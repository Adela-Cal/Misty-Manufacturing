from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, status
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ReturnDocument
from dotenv import load_dotenv
from uuid import uuid4
import os
from auth import require_admin, require_admin_or_manager, get_current_user, require_any_role, require_manager, require_payroll_access
from payroll_models import *
from payroll_service import PayrollCalculationService, TimesheetService, LeaveManagementService, PayrollReportingService, prepare_for_mongo
import logging

# MongoDB connection for payroll endpoints
ROOT_DIR = os.path.dirname(__file__)
load_dotenv(os.path.join(ROOT_DIR, '.env'))

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create router for payroll endpoints
payroll_router = APIRouter(prefix="/api/payroll", tags=["payroll"])

# Initialize services
payroll_calc_service = PayrollCalculationService()
timesheet_service = TimesheetService()
leave_service = LeaveManagementService()
reporting_service = PayrollReportingService()

logger = logging.getLogger(__name__)

# ============= HELPER FUNCTIONS =============


async def get_next_employee_number() -> str:
    """
    Get the next unique employee number by finding the highest existing number
    """
    # Get all employee profiles (including archived)
    all_profiles = await db.employee_profiles.find({}).to_list(1000)
    
    if not all_profiles:
        return "EMP0001"
    
    # Extract all employee numbers and find the highest
    max_number = 0
    for profile in all_profiles:
        emp_num = profile.get("employee_number", "EMP0000")
        if emp_num.startswith("EMP"):
            try:
                num = int(emp_num[3:])  # Extract number part after "EMP"
                if num > max_number:
                    max_number = num
            except ValueError:
                continue
    
    # Return next number
    return f"EMP{max_number + 1:04d}"

async def check_timesheet_access(current_user: dict, timesheet_employee_id: str) -> bool:
    """
    Check if current user has access to a timesheet.
    Handles user_id to employee_id mapping for permission checks.
    """
    # Admins and managers always have access
    if current_user["role"] in ["admin", "manager", "production_manager"]:
        return True
    
    # Check if user's employee profile matches the timesheet's employee_id
    user_id = current_user.get("user_id") or current_user.get("sub")
    
    # First try direct match
    if user_id == timesheet_employee_id:
        return True
    
    # Then check if user_id maps to this employee via employee_profiles
    employee_profile = await db.employee_profiles.find_one({"user_id": user_id})
    if employee_profile and employee_profile["id"] == timesheet_employee_id:
        return True
    
    return False

# ============= EMPLOYEE MANAGEMENT ENDPOINTS =============

@payroll_router.get("/employees", response_model=List[EmployeeProfile])
async def get_employees(current_user: dict = Depends(require_payroll_access)):
    """
    Get all employees synchronized with Staff and Security users.
    Automatically creates employee profiles for users that don't have them yet.
    """
    # Get all active users from Staff and Security
    all_users = await db.users.find({"is_active": True}).to_list(1000)
    
    # Get existing employee profiles
    existing_employees = await db.employee_profiles.find({"is_active": True}).to_list(1000)
    existing_employee_user_ids = {emp.get("user_id") for emp in existing_employees}
    
    # Auto-create employee profiles for users that don't have them
    for user in all_users:
        user_id = user.get("id") or user.get("_id")
        if user_id and user_id not in existing_employee_user_ids:
            # Create default employee profile from user data
            employee_number = await get_next_employee_number()
            
            # Extract name parts
            full_name = user.get("full_name", "")
            name_parts = full_name.split(" ", 1) if full_name else ["", ""]
            first_name = name_parts[0] or user.get("username", "Unknown")
            last_name = name_parts[1] if len(name_parts) > 1 else ""
            
            # Determine position from role
            role = user.get("role", "production_staff")
            position_map = {
                "admin": "Administrator",
                "manager": "Manager",
                "production_manager": "Production Manager",
                "supervisor": "Supervisor",
                "production_staff": "Production Staff",
                "production_team": "Production Team Member"
            }
            position = position_map.get(role, "Staff Member")
            
            # Create new employee profile
            new_employee = EmployeeProfile(
                user_id=user_id,
                employee_number=employee_number,
                first_name=first_name,
                last_name=last_name,
                email=user.get("email", f"{user.get('username')}@example.com"),
                phone=user.get("phone", ""),
                department=user.get("department", "Production"),
                position=position,
                start_date=datetime.utcnow().date(),
                employment_type=user.get("employment_type", "full_time"),
                hourly_rate=Decimal("25.00"),  # Default hourly rate
                weekly_hours=38,
                annual_leave_entitlement=152,
                sick_leave_entitlement=76,
                personal_leave_entitlement=38,
                annual_leave_balance=Decimal("0"),
                sick_leave_balance=Decimal("0"),
                personal_leave_balance=Decimal("0"),
                is_active=True
            )
            
            employee_dict = prepare_for_mongo(new_employee.dict())
            await db.employee_profiles.insert_one(employee_dict)
            existing_employees.append(employee_dict)
            existing_employee_user_ids.add(user_id)
            
            logger.info(f"Auto-created employee profile for user {user_id}: {first_name} {last_name}")
    
    # Fetch updated employee profiles
    employees = await db.employee_profiles.find({"is_active": True}).to_list(1000)
    
    # Enrich employee data with current user information from Staff and Security
    enriched_employees = []
    for emp in employees:
        # Remove MongoDB _id field to avoid serialization issues
        if "_id" in emp:
            del emp["_id"]
        
        user_id = emp.get("user_id")
        if user_id:
            user = await db.users.find_one({"id": user_id, "is_active": True})
            if user:
                # Update employee data with latest user information
                full_name = user.get("full_name", "")
                if full_name:
                    name_parts = full_name.split(" ", 1)
                    emp["first_name"] = name_parts[0]
                    emp["last_name"] = name_parts[1] if len(name_parts) > 1 else ""
                
                emp["email"] = user.get("email", emp.get("email"))
                emp["phone"] = user.get("phone", emp.get("phone"))
                emp["department"] = user.get("department", emp.get("department"))
                emp["employment_type"] = user.get("employment_type", emp.get("employment_type"))
        
        try:
            enriched_employees.append(EmployeeProfile(**emp))
        except Exception as e:
            logger.error(f"Error creating EmployeeProfile for user {user_id}: {e}, emp data keys: {emp.keys()}")
            continue
    
    return enriched_employees

@payroll_router.post("/employees/sync", response_model=StandardResponse)
async def sync_employees_from_users(current_user: dict = Depends(require_admin)):
    """
    Manually trigger synchronization of employee profiles with Staff and Security users.
    This creates employee profiles for any users that don't have them yet.
    """
    # Get all active users
    all_users = await db.users.find({"is_active": True}).to_list(1000)
    
    # Get existing employee profiles
    existing_employees = await db.employee_profiles.find({"is_active": True}).to_list(1000)
    existing_employee_user_ids = {emp.get("user_id") for emp in existing_employees}
    
    created_count = 0
    
    # Create employee profiles for users that don't have them
    for user in all_users:
        user_id = user.get("id") or user.get("_id")
        if user_id and user_id not in existing_employee_user_ids:
            # Create default employee profile from user data
            employee_number = await get_next_employee_number()
            
            # Extract name parts
            full_name = user.get("full_name", "")
            name_parts = full_name.split(" ", 1) if full_name else ["", ""]
            first_name = name_parts[0] or user.get("username", "Unknown")
            last_name = name_parts[1] if len(name_parts) > 1 else ""
            
            # Determine position from role
            role = user.get("role", "production_staff")
            position_map = {
                "admin": "Administrator",
                "manager": "Manager",
                "production_manager": "Production Manager",
                "supervisor": "Supervisor",
                "production_staff": "Production Staff",
                "production_team": "Production Team Member"
            }
            position = position_map.get(role, "Staff Member")
            
            # Create new employee profile
            new_employee = EmployeeProfile(
                user_id=user_id,
                employee_number=employee_number,
                first_name=first_name,
                last_name=last_name,
                email=user.get("email", f"{user.get('username')}@example.com"),
                phone=user.get("phone", ""),
                department=user.get("department", "Production"),
                position=position,
                start_date=datetime.utcnow().date(),
                employment_type=user.get("employment_type", "full_time"),
                hourly_rate=Decimal("25.00"),  # Default hourly rate
                weekly_hours=38,
                annual_leave_entitlement=152,
                sick_leave_entitlement=76,
                personal_leave_entitlement=38,
                annual_leave_balance=Decimal("0"),
                sick_leave_balance=Decimal("0"),
                personal_leave_balance=Decimal("0"),
                is_active=True
            )
            
            employee_dict = prepare_for_mongo(new_employee.dict())
            await db.employee_profiles.insert_one(employee_dict)
            created_count += 1
            
            logger.info(f"Synced employee profile for user {user_id}: {first_name} {last_name}")
    
    return StandardResponse(
        success=True,
        message=f"Successfully synchronized {created_count} employee profiles from Staff and Security users",
        data={"created_count": created_count, "total_employees": len(existing_employees) + created_count}
    )

@payroll_router.post("/employees", response_model=StandardResponse)
async def create_employee(employee_data: EmployeeProfileCreate, current_user: dict = Depends(require_admin)):
    """Create new employee profile (Admin only)"""
    
    # Check if employee number already exists
    existing_emp = await db.employee_profiles.find_one({"employee_number": employee_data.employee_number})
    if existing_emp:
        raise HTTPException(status_code=400, detail="Employee number already exists")
    
    # Create employee profile
    new_employee = EmployeeProfile(**employee_data.dict())
    
    # Set initial leave balances based on start date and current date
    months_employed = max(1, (datetime.utcnow().date() - employee_data.start_date).days // 30)
    accrual_rate = min(1.0, months_employed / 12)  # Pro-rata for first year
    
    new_employee.annual_leave_balance = Decimal(str(employee_data.annual_leave_entitlement * accrual_rate))
    new_employee.sick_leave_balance = Decimal(str(employee_data.sick_leave_entitlement * accrual_rate))
    new_employee.personal_leave_balance = Decimal(str(employee_data.personal_leave_entitlement * accrual_rate))
    
    employee_dict = prepare_for_mongo(new_employee.dict())
    await db.employee_profiles.insert_one(employee_dict)
    
    logger.info(f"Created employee profile for {new_employee.first_name} {new_employee.last_name}")
    
    return StandardResponse(success=True, message="Employee created successfully", data={"id": new_employee.id})

@payroll_router.get("/employees/{employee_id}", response_model=EmployeeProfile)
async def get_employee(employee_id: str, current_user: dict = Depends(require_payroll_access)):
    """Get specific employee (Admin/Manager only)"""
    employee = await db.employee_profiles.find_one({"id": employee_id, "is_active": True})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    return EmployeeProfile(**employee)

@payroll_router.get("/employees/me/profile", response_model=EmployeeProfile)
async def get_my_employee_profile(current_user: dict = Depends(require_any_role)):
    """Get current user's employee profile"""
    user_id = current_user.get("user_id") or current_user.get("sub")
    
    # Find employee profile by user_id
    employee = await db.employee_profiles.find_one({"user_id": user_id, "is_active": True})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee profile not found for current user")
    
    return EmployeeProfile(**employee)

@payroll_router.put("/employees/{employee_id}", response_model=StandardResponse)
async def update_employee(employee_id: str, employee_data: EmployeeProfileCreate, current_user: dict = Depends(require_admin)):
    """Update employee profile (Admin only)"""
    
    update_data = employee_data.dict()
    update_data["updated_at"] = datetime.utcnow()
    
    result = await db.employee_profiles.update_one(
        {"id": employee_id, "is_active": True},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    return StandardResponse(success=True, message="Employee updated successfully")

@payroll_router.delete("/employees/{employee_id}", response_model=StandardResponse)
async def archive_employee(employee_id: str, current_user: dict = Depends(require_admin)):
    """
    Archive (soft delete) employee profile (Admin only)
    Sets is_active=False to preserve historic data while hiding from active employee list
    """
    result = await db.employee_profiles.update_one(
        {"id": employee_id, "is_active": True},
        {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Employee not found or already archived")
    
    logger.info(f"Archived employee {employee_id}")
    
    return StandardResponse(success=True, message="Employee archived successfully")

@payroll_router.get("/employees/archived/list", response_model=List[EmployeeProfile])
async def get_archived_employees(current_user: dict = Depends(require_payroll_access)):
    """
    Get all archived employees (Admin/Manager only)
    Returns employees that have been soft-deleted but their data is preserved for historic review
    """
    employees = await db.employee_profiles.find({"is_active": False}).to_list(1000)
    
    # Enrich employee data with current user information from Staff and Security
    enriched_employees = []
    for emp in employees:
        # Remove MongoDB _id field to avoid serialization issues
        if "_id" in emp:
            del emp["_id"]
        
        user_id = emp.get("user_id")
        if user_id:
            user = await db.users.find_one({"id": user_id})
            if user:
                # Update employee data with latest user information
                full_name = user.get("full_name", "")
                if full_name:
                    name_parts = full_name.split(" ", 1)
                    emp["first_name"] = name_parts[0]
                    emp["last_name"] = name_parts[1] if len(name_parts) > 1 else ""
                
                emp["email"] = user.get("email", emp.get("email"))
                emp["phone"] = user.get("phone", emp.get("phone"))
                emp["department"] = user.get("department", emp.get("department"))
                emp["employment_type"] = user.get("employment_type", emp.get("employment_type"))
        
        try:
            enriched_employees.append(EmployeeProfile(**emp))
        except Exception as e:
            logger.error(f"Error creating EmployeeProfile for user {user_id}: {e}, emp data keys: {emp.keys()}")
            continue
    
    return enriched_employees

@payroll_router.post("/employees/{employee_id}/restore", response_model=StandardResponse)
async def restore_employee(employee_id: str, current_user: dict = Depends(require_admin)):
    """
    Restore archived employee profile (Admin only)
    Sets is_active=True to re-activate an archived employee
    """
    result = await db.employee_profiles.update_one(
        {"id": employee_id, "is_active": False},
        {"$set": {"is_active": True, "updated_at": datetime.utcnow()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Archived employee not found")
    
    logger.info(f"Restored archived employee {employee_id}")
    
    return StandardResponse(success=True, message="Employee restored successfully")

@payroll_router.delete("/employees/{employee_id}/permanent", response_model=StandardResponse)
async def permanently_delete_employee(employee_id: str, current_user: dict = Depends(require_admin)):
    """
    Permanently delete archived employee profile (Admin only)
    WARNING: This is irreversible and will delete ALL associated data including:
    - Employee profile
    - All timesheets
    - All leave requests
    - All payroll history
    Only archived employees can be permanently deleted
    """
    # Check if employee is archived
    employee = await db.employee_profiles.find_one({"id": employee_id, "is_active": False})
    if not employee:
        raise HTTPException(status_code=404, detail="Archived employee not found. Only archived employees can be permanently deleted.")
    
    # Delete all associated data
    # Delete timesheets
    await db.timesheets.delete_many({"employee_id": employee_id})
    
    # Delete leave requests
    await db.leave_requests.delete_many({"employee_id": employee_id})
    
    # Delete employee profile
    result = await db.employee_profiles.delete_one({"id": employee_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=500, detail="Failed to delete employee")
    
    logger.warning(f"PERMANENTLY DELETED employee {employee_id} and all associated data")
    
    return StandardResponse(success=True, message="Employee and all associated data permanently deleted")

@payroll_router.put("/employees/{employee_id}/bank-details", response_model=StandardResponse)
async def update_employee_bank_details(
    employee_id: str,
    bank_account_bsb: str,
    bank_account_number: str,
    tax_file_number: Optional[str] = None,
    superannuation_fund: Optional[str] = None,
    current_user: dict = Depends(require_admin)
):
    """Update employee bank details and tax information (Admin only)"""
    
    result = await db.employee_profiles.update_one(
        {"id": employee_id},
        {"$set": {
            "bank_account_bsb": bank_account_bsb,
            "bank_account_number": bank_account_number,
            "tax_file_number": tax_file_number,
            "superannuation_fund": superannuation_fund,
            "updated_at": datetime.utcnow()
        }}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    logger.info(f"Updated bank details for employee {employee_id}")
    
    return StandardResponse(success=True, message="Bank details updated successfully")

@payroll_router.post("/leave-adjustments", response_model=StandardResponse)
async def create_leave_adjustment(adjustment: LeaveAdjustmentCreate, current_user: dict = Depends(require_admin)):
    """Create manual leave adjustment with reason (Admin only)"""
    
    # Get employee
    employee = await db.employee_profiles.find_one({"id": adjustment.employee_id})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    employee_profile = EmployeeProfile(**employee)
    
    # Get current balance based on leave type
    balance_field = f"{adjustment.leave_type.value}_balance"
    current_balance = getattr(employee_profile, balance_field, Decimal("0"))
    
    # Calculate new balance
    new_balance = current_balance + adjustment.adjustment_hours
    
    if new_balance < 0:
        raise HTTPException(status_code=400, detail="Adjustment would result in negative balance")
    
    # Create adjustment record
    leave_adjustment = LeaveAdjustment(
        **adjustment.dict(),
        previous_balance=current_balance,
        new_balance=new_balance,
        adjusted_by=current_user["user_id"]
    )
    
    adjustment_dict = prepare_for_mongo(leave_adjustment.dict())
    await db.leave_adjustments.insert_one(adjustment_dict)
    
    # Update employee balance
    await db.employee_profiles.update_one(
        {"id": adjustment.employee_id},
        {"$set": {balance_field: float(new_balance), "updated_at": datetime.utcnow()}}
    )
    
    logger.info(f"Created leave adjustment for employee {adjustment.employee_id}: {adjustment.adjustment_hours}h")
    
    return StandardResponse(
        success=True,
        message=f"Leave adjustment recorded. New balance: {new_balance}h",
        data={"new_balance": float(new_balance)}
    )

@payroll_router.get("/leave-adjustments/{employee_id}")
async def get_leave_adjustment_history(employee_id: str, current_user: dict = Depends(require_payroll_access)):
    """Get leave adjustment history for an employee"""
    
    adjustments = await db.leave_adjustments.find({"employee_id": employee_id}).sort("created_at", -1).to_list(100)
    
    for adj in adjustments:
        if "_id" in adj:
            del adj["_id"]
    
    return {"success": True, "data": adjustments}

@payroll_router.get("/employees/{employee_id}/leave-balances", response_model=EmployeeLeaveBalance)
async def get_employee_leave_balances(employee_id: str, current_user: dict = Depends(require_any_role)):
    """Get employee leave balances (Employee can view own, Managers can view all)"""
    
    # Check if user can access this employee's data
    if current_user["role"] not in ["admin", "manager", "production_manager"] and current_user["user_id"] != employee_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    employee = await db.employee_profiles.find_one({"id": employee_id, "is_active": True})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    return EmployeeLeaveBalance(
        employee_id=employee["id"],
        employee_name=f"{employee['first_name']} {employee['last_name']}",
        annual_leave_balance=employee["annual_leave_balance"],
        sick_leave_balance=employee["sick_leave_balance"],
        personal_leave_balance=employee["personal_leave_balance"],
        annual_leave_entitlement=employee["annual_leave_entitlement"],
        sick_leave_entitlement=employee["sick_leave_entitlement"],
        personal_leave_entitlement=employee["personal_leave_entitlement"]
    )

# ============= TIMESHEET ENDPOINTS =============

@payroll_router.get("/timesheets/current-week/{employee_id}")
async def get_current_week_timesheet(employee_id: str, current_user: dict = Depends(require_any_role)):
    """Get or create current week timesheet"""
    
    # Validate employee_id parameter
    if not employee_id or employee_id in ['undefined', 'null', 'None']:
        raise HTTPException(status_code=400, detail="Valid employee ID is required")
    
    # Check access permissions using the helper function
    if not await check_timesheet_access(current_user, employee_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    week_starting = timesheet_service.get_current_week_starting()
    
    # Convert date to datetime for MongoDB compatibility
    week_starting_dt = datetime.combine(week_starting, datetime.min.time()).replace(tzinfo=timezone.utc)
    
    # Try to find existing timesheet
    existing_timesheet = await db.timesheets.find_one({
        "employee_id": employee_id,
        "week_starting": week_starting_dt
    })
    
    if existing_timesheet:
        return Timesheet(**existing_timesheet)
    
    # Create new timesheet if it doesn't exist
    new_timesheet = timesheet_service.generate_weekly_timesheet(employee_id, week_starting)
    timesheet_dict = prepare_for_mongo(new_timesheet.dict())
    await db.timesheets.insert_one(timesheet_dict)
    
    return new_timesheet

@payroll_router.get("/timesheets/employee/{employee_id}")
async def get_employee_timesheets(employee_id: str, current_user: dict = Depends(require_any_role)):
    """Get all timesheets for an employee"""
    
    # Validate employee_id parameter
    if not employee_id or employee_id in ['undefined', 'null', 'None']:
        raise HTTPException(status_code=400, detail="Valid employee ID is required")
    
    # Check access permissions using the helper function
    if not await check_timesheet_access(current_user, employee_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get all timesheets for this employee, sorted by week_starting descending
    timesheets = await db.timesheets.find({"employee_id": employee_id}).sort("week_starting", -1).to_list(100)
    
    # Remove MongoDB _id and return
    for timesheet in timesheets:
        if "_id" in timesheet:
            del timesheet["_id"]
    
    return {
        "success": True,
        "data": timesheets
    }

@payroll_router.put("/timesheets/{timesheet_id}", response_model=StandardResponse)
async def update_timesheet(timesheet_id: str, timesheet_data: TimesheetCreate, current_user: dict = Depends(require_any_role)):
    """Update timesheet entries"""
    
    # Get existing timesheet
    existing_timesheet = await db.timesheets.find_one({"id": timesheet_id})
    if not existing_timesheet:
        raise HTTPException(status_code=404, detail="Timesheet not found")
    
    # Check if timesheet is already approved (can't edit approved timesheets)
    if existing_timesheet.get("status") == TimesheetStatus.APPROVED:
        raise HTTPException(status_code=400, detail="Cannot edit approved timesheet")
    
    # Check access permissions using the helper function
    if not await check_timesheet_access(current_user, existing_timesheet["employee_id"]):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Update timesheet
    timesheet = Timesheet(**existing_timesheet)
    timesheet.entries = timesheet_data.entries
    timesheet.updated_at = datetime.utcnow()
    
    # Calculate totals
    timesheet = timesheet_service.calculate_timesheet_totals(timesheet)
    
    # Save updated timesheet
    timesheet_dict = prepare_for_mongo(timesheet.dict())
    await db.timesheets.update_one(
        {"id": timesheet_id},
        {"$set": timesheet_dict}
    )
    
    return StandardResponse(success=True, message="Timesheet updated successfully")

@payroll_router.post("/timesheets/{timesheet_id}/submit", response_model=StandardResponse)
async def submit_timesheet(timesheet_id: str, current_user: dict = Depends(require_any_role)):
    """Submit timesheet for approval"""
    
    timesheet = await db.timesheets.find_one({"id": timesheet_id})
    if not timesheet:
        raise HTTPException(status_code=404, detail="Timesheet not found")
    
    # Check access permissions using the helper function
    if not await check_timesheet_access(current_user, timesheet["employee_id"]):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Update status
    await db.timesheets.update_one(
        {"id": timesheet_id},
        {"$set": {
            "status": TimesheetStatus.SUBMITTED,
            "submitted_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }}
    )
    
    return StandardResponse(success=True, message="Timesheet submitted for approval")

@payroll_router.post("/timesheets/{timesheet_id}/reset-to-draft", response_model=StandardResponse)
async def reset_timesheet_to_draft(timesheet_id: str, current_user: dict = Depends(require_any_role)):
    """Reset submitted/approved timesheet back to draft for re-editing and resubmission"""
    
    timesheet = await db.timesheets.find_one({"id": timesheet_id})
    if not timesheet:
        raise HTTPException(status_code=404, detail="Timesheet not found")
    
    # Check access permissions - only the timesheet owner can reset it
    if not await check_timesheet_access(current_user, timesheet["employee_id"]):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Reset status to draft and clear approval data
    await db.timesheets.update_one(
        {"id": timesheet_id},
        {"$set": {
            "status": TimesheetStatus.DRAFT,
            "approved_by": None,
            "approved_at": None,
            "submitted_at": None,
            "updated_at": datetime.utcnow()
        }}
    )
    
    logger.info(f"Timesheet {timesheet_id} reset to draft by user {current_user.get('sub')}")
    
    return StandardResponse(success=True, message="Timesheet reset to draft. You can now edit and resubmit.")

@payroll_router.post("/timesheets/{timesheet_id}/approve", response_model=StandardResponse)
async def approve_timesheet(timesheet_id: str, current_user: dict = Depends(require_payroll_access)):
    """Approve timesheet and calculate pay (Manager only) - ATOMIC OPERATION for concurrent access"""
    
    logger.info(f"Attempting to approve timesheet {timesheet_id} by user {current_user.get('sub')}")
    
    # ATOMIC OPERATION: Update timesheet status only if still in submitted status
    # This prevents concurrent approvals by multiple managers
    timesheet_doc = await db.timesheets.find_one_and_update(
        {
            "id": timesheet_id,
            "status": TimesheetStatus.SUBMITTED  # Only approve if currently submitted
        },
        {
            "$set": {
                "status": TimesheetStatus.APPROVED,
                "approved_by": current_user.get("user_id", current_user.get("sub")),
                "approved_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        },
        return_document=ReturnDocument.BEFORE  # Return original document for processing
    )
    
    if not timesheet_doc:
        logger.warning(f"Timesheet {timesheet_id} not found or not in submitted status")
        raise HTTPException(
            status_code=404, 
            detail="Timesheet not found, not in submitted status, or already approved by another manager"
        )
    
    timesheet = Timesheet(**timesheet_doc)
    
    # Get employee profile
    employee_doc = await db.employee_profiles.find_one({"id": timesheet.employee_id})
    if not employee_doc:
        # Rollback timesheet approval
        await db.timesheets.update_one(
            {"id": timesheet_id},
            {"$set": {
                "status": TimesheetStatus.SUBMITTED,
                "approved_by": None,
                "approved_at": None,
                "updated_at": datetime.utcnow()
            }}
        )
        raise HTTPException(status_code=404, detail="Employee not found")
    
    employee = EmployeeProfile(**employee_doc)
    
    try:
        # Calculate payroll
        payroll_calculation = payroll_calc_service.calculate_weekly_pay(employee, timesheet)
        
        # Save payroll calculation
        payroll_dict = prepare_for_mongo(payroll_calculation.dict())
        await db.payroll_calculations.insert_one(payroll_dict)
        
        # Update employee leave balances atomically
        leave_updates = {
            "annual_leave_balance": employee.annual_leave_balance + payroll_calculation.annual_leave_accrued,
            "sick_leave_balance": employee.sick_leave_balance + payroll_calculation.sick_leave_accrued,
            "personal_leave_balance": employee.personal_leave_balance + payroll_calculation.personal_leave_accrued,
            "updated_at": datetime.utcnow()
        }
        
        # Subtract any leave taken
        for leave_type, hours_taken in payroll_calculation.leave_taken.items():
            if leave_type == LeaveType.ANNUAL_LEAVE:
                leave_updates["annual_leave_balance"] -= hours_taken
            elif leave_type == LeaveType.SICK_LEAVE:
                leave_updates["sick_leave_balance"] -= hours_taken
            elif leave_type == LeaveType.PERSONAL_LEAVE:
                leave_updates["personal_leave_balance"] -= hours_taken
        
        await db.employee_profiles.update_one(
            {"id": employee.id},
            {"$set": prepare_for_mongo(leave_updates)}
        )
        
        logger.info(f"Approved timesheet {timesheet_id} by user {current_user.get('sub')} and calculated pay: ${payroll_calculation.gross_pay}")
        
        return StandardResponse(
            success=True, 
            message="Timesheet approved and pay calculated", 
            data={
                "gross_pay": float(payroll_calculation.gross_pay),
                "net_pay": float(payroll_calculation.net_pay),
                "hours_worked": float(payroll_calculation.total_hours)
            }
        )
        
    except Exception as e:
        # Rollback timesheet approval if calculation fails
        await db.timesheets.update_one(
            {"id": timesheet_id},
            {"$set": {
                "status": TimesheetStatus.SUBMITTED,
                "approved_by": None,
                "approved_at": None,
                "updated_at": datetime.utcnow()
            }}
        )
        logger.error(f"Failed to approve timesheet {timesheet_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to calculate pay: {str(e)}")

@payroll_router.get("/timesheets/pending")
async def get_pending_timesheets(current_user: dict = Depends(require_payroll_access)):
    """Get all pending timesheets for approval"""
    
    pending_timesheets = await db.timesheets.find({"status": TimesheetStatus.SUBMITTED}).to_list(1000)
    
    # Remove MongoDB ObjectId and enrich with employee names
    for timesheet in pending_timesheets:
        # Remove MongoDB ObjectId to prevent serialization errors
        if "_id" in timesheet:
            del timesheet["_id"]
        
        # Try to find employee by id first, then by user_id as fallback
        employee_id = timesheet.get("employee_id")
        employee = None
        
        if employee_id:
            # First try: Find by employee_id in employee_profiles
            employee = await db.employee_profiles.find_one({"id": employee_id})
            
            # Second try: Find by user_id in employee_profiles (in case employee_id is actually a user_id)
            if not employee:
                employee = await db.employee_profiles.find_one({"user_id": employee_id})
            
            # Third try: Find user and get their employee profile
            if not employee:
                user = await db.users.find_one({"id": employee_id})
                if user:
                    employee = await db.employee_profiles.find_one({"user_id": user["id"]})
        
        # Set employee name if found, otherwise use ID
        if employee:
            timesheet["employee_name"] = f"{employee['first_name']} {employee['last_name']}"
        else:
            timesheet["employee_name"] = f"Unknown Employee (ID: {employee_id[:8]}...)"
            logger.warning(f"Could not find employee for timesheet {timesheet.get('id')} with employee_id {employee_id}")
    
    return {"success": True, "data": pending_timesheets}

# ============= LEAVE REQUEST ENDPOINTS =============

@payroll_router.post("/leave-requests", response_model=StandardResponse)
async def create_leave_request(leave_data: LeaveRequestCreate, current_user: dict = Depends(require_any_role)):
    """Create new leave request"""
    
    # Check if user can create leave for this employee
    if current_user["role"] not in ["admin", "manager", "production_manager"] and current_user["user_id"] != leave_data.employee_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get employee to check leave balance
    employee = await db.employee_profiles.find_one({"id": leave_data.employee_id})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    employee_profile = EmployeeProfile(**employee)
    
    # Check leave balance
    if not leave_service.check_leave_balance(employee_profile, leave_data.leave_type, leave_data.hours_requested):
        raise HTTPException(status_code=400, detail="Insufficient leave balance")
    
    # Create leave request
    leave_request_data = leave_data.dict()
    leave_request_data['requested_by'] = current_user["user_id"]
    
    leave_request = LeaveRequest(**leave_request_data)
    
    leave_dict = prepare_for_mongo(leave_request.dict())
    await db.leave_requests.insert_one(leave_dict)
    
    return StandardResponse(success=True, message="Leave request created successfully", data={"id": leave_request.id})

@payroll_router.get("/leave-requests/pending")
async def get_pending_leave_requests(current_user: dict = Depends(require_payroll_access)):
    """Get all pending leave requests"""
    
    pending_requests = await db.leave_requests.find({"status": LeaveStatus.PENDING}).to_list(1000)
    
    # Remove MongoDB ObjectId and enrich with employee names
    for request in pending_requests:
        # Remove MongoDB ObjectId to prevent serialization errors
        if "_id" in request:
            del request["_id"]
            
        employee = await db.employee_profiles.find_one({"id": request["employee_id"]})
        if employee:
            request["employee_name"] = f"{employee['first_name']} {employee['last_name']}"
    
    return {"success": True, "data": pending_requests}

@payroll_router.get("/leave-requests/my-approvals")
async def get_my_approval_requests(current_user: dict = Depends(require_any_role)):
    """Get leave requests assigned to current user for approval"""
    
    # Get requests where current user is the assigned approver
    my_requests = await db.leave_requests.find({
        "approver_id": current_user["user_id"],
        "status": LeaveStatus.PENDING
    }).to_list(1000)
    
    # Remove MongoDB ObjectId and enrich with employee names
    for request in my_requests:
        if "_id" in request:
            del request["_id"]
            
        employee = await db.employee_profiles.find_one({"id": request["employee_id"]})
        if employee:
            request["employee_name"] = f"{employee['first_name']} {employee['last_name']}"
    
    return {"success": True, "data": my_requests}

@payroll_router.get("/leave-requests/archived")
async def get_archived_leave_requests(current_user: dict = Depends(require_payroll_access)):
    """Get all archived (approved/declined) leave requests"""
    
    archived_requests = await db.leave_requests.find({
        "status": {"$in": [LeaveStatus.APPROVED, LeaveStatus.REJECTED]}
    }).sort("created_at", -1).to_list(1000)
    
    # Remove MongoDB ObjectId and enrich with employee names
    for request in archived_requests:
        if "_id" in request:
            del request["_id"]
            
        employee = await db.employee_profiles.find_one({"id": request["employee_id"]})
        if employee:
            request["employee_name"] = f"{employee['first_name']} {employee['last_name']}"
        
        # Get approver name
        if request.get("approved_by"):
            approver = await db.users.find_one({"id": request["approved_by"]})
            if approver:
                request["approver_name"] = approver.get("full_name", "Unknown")
    
    return {"success": True, "data": archived_requests}

@payroll_router.get("/leave-requests/calendar")
async def get_leave_calendar(current_user: dict = Depends(require_any_role)):
    """Get all upcoming approved leave for calendar view"""
    
    today = datetime.utcnow().date()
    
    # Fix date format issue - use datetime object for MongoDB comparison
    today_dt = datetime.combine(today, datetime.min.time())
    
    # Get approved leave requests with end_date >= today
    upcoming_leave = await db.leave_requests.find({
        "status": LeaveStatus.APPROVED,
        "end_date": {"$gte": today_dt}
    }).sort("start_date", 1).to_list(1000)
    
    # Enrich with employee details
    calendar_events = []
    for request in upcoming_leave:
        if "_id" in request:
            del request["_id"]
            
        employee = await db.employee_profiles.find_one({"id": request["employee_id"]})
        if employee:
            calendar_events.append({
                "id": request["id"],
                "employee_id": request["employee_id"],
                "employee_name": f"{employee['first_name']} {employee['last_name']}",
                "employee_number": employee["employee_number"],
                "department": employee.get("department", "N/A"),
                "leave_type": request["leave_type"],
                "start_date": request["start_date"],
                "end_date": request["end_date"],
                "hours_requested": float(request["hours_requested"]),
                "reason": request.get("reason", "")
            })
    
    return {"success": True, "data": calendar_events}

@payroll_router.get("/leave-requests/reminders")
async def get_leave_reminders(current_user: dict = Depends(require_any_role)):
    """Get leave reminders for upcoming approved leave (1 week and 1 day before)"""
    
    today = datetime.utcnow().date()
    one_week_from_now = today + timedelta(days=7)
    tomorrow = today + timedelta(days=1)
    
    # Get approved leave starting in 1 week or 1 day
    upcoming_leave = await db.leave_requests.find({
        "status": LeaveStatus.APPROVED,
        "start_date": {"$in": [one_week_from_now.isoformat(), tomorrow.isoformat()]}
    }).to_list(100)
    
    reminders = []
    for request in upcoming_leave:
        if "_id" in request:
            del request["_id"]
            
        employee = await db.employee_profiles.find_one({"id": request["employee_id"]})
        if employee:
            start_date = datetime.fromisoformat(request["start_date"]).date()
            days_until = (start_date - today).days
            
            reminder_type = "1_week" if days_until == 7 else "1_day"
            
            reminders.append({
                "id": request["id"],
                "employee_name": f"{employee['first_name']} {employee['last_name']}",
                "employee_number": employee["employee_number"],
                "department": employee.get("department", "N/A"),
                "leave_type": request["leave_type"],
                "start_date": request["start_date"],
                "end_date": request["end_date"],
                "hours_requested": float(request["hours_requested"]),
                "days_until": days_until,
                "reminder_type": reminder_type,
                "message": f"{employee['first_name']} {employee['last_name']} has approved {request['leave_type'].replace('_', ' ')} starting in {days_until} {'day' if days_until == 1 else 'days'}"
            })
    
    return {"success": True, "data": reminders}

@payroll_router.post("/leave-requests/{request_id}/approve", response_model=StandardResponse)
async def approve_leave_request(request_id: str, current_user: dict = Depends(require_payroll_access)):
    """Approve leave request and deduct from employee balance - ATOMIC OPERATION for concurrent access"""
    
    # Get the leave request and mark as processing atomically
    leave_request = await db.leave_requests.find_one_and_update(
        {
            "id": request_id, 
            "status": LeaveStatus.PENDING  # Only process if still pending
        },
        {
            "$set": {
                "status": LeaveStatus.APPROVED,
                "approved_by": current_user.get("user_id", current_user.get("sub")),
                "approved_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        },
        return_document=ReturnDocument.AFTER
    )
    
    if not leave_request:
        raise HTTPException(
            status_code=404, 
            detail="Leave request not found, already processed, or concurrent approval occurred"
        )
    
    # Determine balance field based on leave type
    leave_type = leave_request["leave_type"]
    balance_field = f"{leave_type}_balance"
    hours_requested = float(leave_request["hours_requested"])
    
    # ATOMIC OPERATION: Deduct leave balance only if sufficient balance exists
    # This prevents race condition where two concurrent approvals could over-deduct balance
    employee = await db.employee_profiles.find_one_and_update(
        {
            "id": leave_request["employee_id"],
            balance_field: {"$gte": hours_requested}  # Only update if sufficient balance
        },
        {
            "$inc": {balance_field: -hours_requested},  # Atomic decrement
            "$set": {"updated_at": datetime.utcnow()}
        },
        return_document=ReturnDocument.AFTER
    )
    
    if employee is None:
        # Insufficient balance - rollback leave approval
        await db.leave_requests.update_one(
            {"id": request_id},
            {"$set": {
                "status": LeaveStatus.PENDING,
                "approved_by": None,
                "approved_at": None,
                "updated_at": datetime.utcnow()
            }}
        )
        
        # Get current balance for error message
        emp = await db.employee_profiles.find_one({"id": leave_request["employee_id"]})
        current_balance = float(emp.get(balance_field, 0)) if emp else 0
        
        raise HTTPException(
            status_code=400, 
            detail=f"Insufficient {leave_type.replace('_', ' ')} balance. Available: {current_balance}h, Requested: {hours_requested}h"
        )
    
    new_balance = float(employee.get(balance_field, 0))
    
    logger.info(f"Approved leave request {request_id} by user {current_user.get('sub')}. Deducted {hours_requested}h from {leave_type}. New balance: {new_balance}h")
    
    return StandardResponse(
        success=True, 
        message=f"Leave request approved. Deducted {hours_requested}h from {leave_type.replace('_', ' ')}. New balance: {new_balance}h"
    )

@payroll_router.post("/leave-requests/{request_id}/reject", response_model=StandardResponse)
async def reject_leave_request(request_id: str, rejection_reason: str, current_user: dict = Depends(require_payroll_access)):
    """Reject leave request (no balance deduction)"""
    
    result = await db.leave_requests.update_one(
        {"id": request_id, "status": LeaveStatus.PENDING},
        {"$set": {
            "status": LeaveStatus.REJECTED,
            "rejection_reason": rejection_reason,
            "approved_by": current_user["user_id"],
            "approved_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Leave request not found or already processed")
    
    logger.info(f"Rejected leave request {request_id}")
    
    return StandardResponse(success=True, message="Leave request rejected")

@payroll_router.post("/leave-requests/{request_id}/cancel", response_model=StandardResponse)
async def cancel_leave_request(request_id: str, current_user: dict = Depends(require_any_role)):
    """Cancel approved leave request and restore balance to employee"""
    
    # Get the leave request
    leave_request = await db.leave_requests.find_one({"id": request_id, "status": LeaveStatus.APPROVED})
    if not leave_request:
        raise HTTPException(status_code=404, detail="Approved leave request not found")
    
    # Check if user has permission to cancel (admin/manager or the employee themselves)
    if current_user["role"] not in ["admin", "manager", "production_manager"] and current_user["user_id"] != leave_request["employee_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get employee profile
    employee = await db.employee_profiles.find_one({"id": leave_request["employee_id"]})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Determine balance field based on leave type
    leave_type = leave_request["leave_type"]
    balance_field = f"{leave_type}_balance"
    hours_requested = float(leave_request["hours_requested"])
    
    # Get current balance
    current_balance = float(employee.get(balance_field, 0))
    
    # Calculate new balance (restore the hours)
    new_balance = current_balance + hours_requested
    
    # Update leave request status to cancelled
    await db.leave_requests.update_one(
        {"id": request_id},
        {"$set": {
            "status": LeaveStatus.REJECTED,  # Use REJECTED status to indicate cancelled
            "rejection_reason": f"Cancelled by {current_user.get('full_name', 'user')}",
            "updated_at": datetime.utcnow()
        }}
    )
    
    # Restore leave balance to employee
    await db.employee_profiles.update_one(
        {"id": leave_request["employee_id"]},
        {"$set": {balance_field: new_balance, "updated_at": datetime.utcnow()}}
    )
    
    logger.info(f"Cancelled leave request {request_id}. Restored {hours_requested}h to {leave_type}. New balance: {new_balance}h")
    
    return StandardResponse(
        success=True, 
        message=f"Leave cancelled. Restored {hours_requested}h to {leave_type.replace('_', ' ')}. New balance: {new_balance}h"
    )

# ============= REPORTING ENDPOINTS =============

@payroll_router.get("/reports/timesheets")
async def get_timesheet_report(
    employee_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(require_payroll_access)
):
    """Get timesheet report with filtering"""
    
    query = {}
    if employee_id:
        query["employee_id"] = employee_id
    if start_date:
        query["week_start"] = {"$gte": start_date}
    if end_date:
        if "week_start" in query:
            query["week_start"]["$lte"] = end_date
        else:
            query["week_start"] = {"$lte": end_date}
    
    timesheets = await db.timesheets.find(query).sort("week_start", -1).to_list(1000)
    
    # Enrich with employee and approver names
    for timesheet in timesheets:
        if "_id" in timesheet:
            del timesheet["_id"]
        
        # Get employee name
        employee = await db.employee_profiles.find_one({"id": timesheet["employee_id"]})
        if employee:
            timesheet["employee_name"] = f"{employee['first_name']} {employee['last_name']}"
        
        # Get approver name
        if timesheet.get("approved_by"):
            approver = await db.users.find_one({"id": timesheet["approved_by"]})
            if approver:
                timesheet["approver_name"] = approver.get("full_name", "Unknown")
    
    # Calculate summary
    total_regular = sum(float(ts.get("total_regular_hours", 0)) for ts in timesheets)
    total_overtime = sum(float(ts.get("total_overtime_hours", 0)) for ts in timesheets)
    
    return {
        "success": True,
        "data": timesheets,
        "summary": {
            "total_timesheets": len(timesheets),
            "total_regular_hours": round(total_regular, 2),
            "total_overtime_hours": round(total_overtime, 2),
            "total_hours": round(total_regular + total_overtime, 2)
        }
    }

@payroll_router.get("/reports/payslip/{timesheet_id}")
async def generate_payslip(timesheet_id: str, current_user: dict = Depends(require_payroll_access)):
    """Generate payslip for a submitted timesheet"""
    
    # Get timesheet
    timesheet = await db.timesheets.find_one({"id": timesheet_id})
    if not timesheet:
        raise HTTPException(status_code=404, detail="Timesheet not found")
    
    # Get employee
    employee = await db.employee_profiles.find_one({"id": timesheet["employee_id"]})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    employee_profile = EmployeeProfile(**employee)
    
    # Calculate pay
    regular_hours = float(timesheet.get("total_regular_hours", 0))
    overtime_hours = float(timesheet.get("total_overtime_hours", 0))
    hourly_rate = float(employee_profile.hourly_rate)
    
    # Basic calculations
    regular_pay = regular_hours * hourly_rate
    overtime_pay = overtime_hours * hourly_rate * 1.5  # 1.5x for overtime
    gross_pay = regular_pay + overtime_pay
    
    # Tax calculation (simplified - 15% flat rate for demo)
    tax_withheld = gross_pay * 0.15
    
    # Superannuation (11% of gross pay in Australia)
    superannuation = gross_pay * 0.11
    
    # Net pay
    net_pay = gross_pay - tax_withheld
    
    # Get YTD totals (sum all approved timesheets for this employee this financial year)
    # Financial year in Australia: July 1 to June 30
    current_date = datetime.utcnow()
    if current_date.month >= 7:
        fy_start = datetime(current_date.year, 7, 1)
    else:
        fy_start = datetime(current_date.year - 1, 7, 1)
    
    ytd_timesheets = await db.timesheets.find({
        "employee_id": timesheet["employee_id"],
        "status": TimesheetStatus.APPROVED,
        "week_start": {"$gte": fy_start.date().isoformat()}
    }).to_list(1000)
    
    ytd_gross = sum(
        (float(ts.get("total_regular_hours", 0)) * hourly_rate) +
        (float(ts.get("total_overtime_hours", 0)) * hourly_rate * 1.5)
        for ts in ytd_timesheets
    )
    ytd_tax = ytd_gross * 0.15
    ytd_super = ytd_gross * 0.11
    ytd_net = ytd_gross - ytd_tax
    
    payslip = {
        "timesheet_id": timesheet_id,
        "employee": {
            "name": f"{employee_profile.first_name} {employee_profile.last_name}",
            "employee_number": employee_profile.employee_number,
            "position": employee_profile.position,
            "department": employee_profile.department,
            "email": employee_profile.email,
            "tax_file_number": employee_profile.tax_file_number or "Not provided"
        },
        "bank_details": {
            "bsb": employee_profile.bank_account_bsb or "Not provided",
            "account_number": employee_profile.bank_account_number or "Not provided",
            "superannuation_fund": employee_profile.superannuation_fund or "Not provided"
        },
        "pay_period": {
            "week_start": timesheet["week_start"],
            "week_end": timesheet["week_end"]
        },
        "hours": {
            "regular_hours": round(regular_hours, 2),
            "overtime_hours": round(overtime_hours, 2),
            "hourly_rate": round(hourly_rate, 2)
        },
        "earnings": {
            "regular_pay": round(regular_pay, 2),
            "overtime_pay": round(overtime_pay, 2),
            "gross_pay": round(gross_pay, 2)
        },
        "deductions": {
            "tax_withheld": round(tax_withheld, 2),
            "superannuation": round(superannuation, 2)
        },
        "net_pay": round(net_pay, 2),
        "year_to_date": {
            "gross_pay": round(ytd_gross, 2),
            "tax_withheld": round(ytd_tax, 2),
            "superannuation": round(ytd_super, 2),
            "net_pay": round(ytd_net, 2)
        },
        "generated_at": datetime.utcnow().isoformat()
    }
    
    # Store payslip in database
    await db.payslips.insert_one({
        "id": str(uuid.uuid4()),
        "timesheet_id": timesheet_id,
        "employee_id": timesheet["employee_id"],
        "payslip_data": payslip,
        "created_at": datetime.utcnow()
    })
    
    return {"success": True, "data": payslip}

@payroll_router.get("/reports/payslips")
async def get_all_payslips(
    employee_id: Optional[str] = None,
    current_user: dict = Depends(require_payroll_access)
):
    """Get all historic payslips"""
    
    query = {}
    if employee_id:
        query["employee_id"] = employee_id
    
    payslips = await db.payslips.find(query).sort("created_at", -1).to_list(1000)
    
    for payslip in payslips:
        if "_id" in payslip:
            del payslip["_id"]
    
    return {"success": True, "data": payslips}

# ============= REPORTING ENDPOINTS =============

@payroll_router.get("/reports/payroll-summary")
async def get_payroll_summary(start_date: date, end_date: date, current_user: dict = Depends(require_payroll_access)):
    """Get payroll summary for date range"""
    
    # Get all payroll calculations in date range
    calculations = await db.payroll_calculations.find({
        "pay_period_start": {"$gte": start_date},
        "pay_period_end": {"$lte": end_date}
    }).to_list(1000)
    
    # Calculate totals
    total_gross_pay = sum(Decimal(str(calc["gross_pay"])) for calc in calculations)
    total_net_pay = sum(Decimal(str(calc["net_pay"])) for calc in calculations)
    total_hours = sum(Decimal(str(calc["total_hours"])) for calc in calculations)
    total_tax = sum(Decimal(str(calc["tax_withheld"])) for calc in calculations)
    total_super = sum(Decimal(str(calc["superannuation"])) for calc in calculations)
    
    return {
        "success": True,
        "data": {
            "period": f"{start_date} to {end_date}",
            "total_gross_pay": float(total_gross_pay),
            "total_net_pay": float(total_net_pay),
            "total_hours_worked": float(total_hours),
            "total_tax_withheld": float(total_tax),
            "total_superannuation": float(total_super),
            "employee_count": len(set(calc["employee_id"] for calc in calculations))
        }
    }

@payroll_router.get("/reports/leave-balances")
async def get_leave_balances_report(current_user: dict = Depends(require_payroll_access)):
    """Get leave balances for all employees"""
    
    employees = await db.employee_profiles.find({"is_active": True}).to_list(1000)
    
    balances = []
    for emp in employees:
        balances.append(EmployeeLeaveBalance(
            employee_id=emp["id"],
            employee_name=f"{emp['first_name']} {emp['last_name']}",
            annual_leave_balance=emp["annual_leave_balance"],
            sick_leave_balance=emp["sick_leave_balance"],
            personal_leave_balance=emp["personal_leave_balance"],
            annual_leave_entitlement=emp["annual_leave_entitlement"],
            sick_leave_entitlement=emp["sick_leave_entitlement"],
            personal_leave_entitlement=emp["personal_leave_entitlement"]
        ))
    
    return {"success": True, "data": balances}

@payroll_router.get("/dashboard/timesheet-reminder")
async def check_timesheet_reminder(current_user: dict = Depends(require_any_role)):
    """Check if timesheet reminder should be shown"""
    
    should_show = timesheet_service.should_show_timesheet_reminder()
    
    return {
        "success": True,
        "data": {
            "show_reminder": should_show,
            "message": "Don't forget to submit your timesheet!" if should_show else None,
            "current_day": date.today().strftime("%A")
        }
    }

# ============= PAYROLL REPORTS ENDPOINTS =============

@payroll_router.get("/reports/payslips")
async def get_all_payslips(current_user: dict = Depends(require_payroll_access)):
    """Get all historic payslips"""
    
    try:
        # Get all payslips
        payslips = await db.payslips.find({}).sort("generated_at", -1).to_list(1000)
        
        # Remove MongoDB ObjectId
        for payslip in payslips:
            if "_id" in payslip:
                del payslip["_id"]
        
        return {
            "success": True,
            "data": payslips
        }
    except Exception as e:
        logger.error(f"Failed to load payslips: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load payslips: {str(e)}")


@payroll_router.get("/reports/payslip/{timesheet_id}")
async def generate_payslip(timesheet_id: str, current_user: dict = Depends(require_payroll_access)):
    """Generate a payslip from an approved timesheet"""
    
    try:
        # Get the timesheet
        timesheet = await db.timesheets.find_one({"id": timesheet_id, "status": TimesheetStatus.APPROVED})
        if not timesheet:
            raise HTTPException(status_code=404, detail="Approved timesheet not found")
        
        # Get employee profile
        employee = await db.employee_profiles.find_one({"id": timesheet["employee_id"]})
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")
        
        # Calculate regular and overtime hours
        entries = timesheet.get("entries", [])
        total_regular_hours = Decimal("0")
        total_overtime_hours = Decimal("0")
        
        for entry in entries:
            regular_hours = Decimal(str(entry.get("regular_hours", 0)))
            overtime_hours = Decimal(str(entry.get("overtime_hours", 0)))
            total_regular_hours += regular_hours
            total_overtime_hours += overtime_hours
        
        # Get hourly rate
        hourly_rate = Decimal(str(employee.get("hourly_rate", 25.00)))
        overtime_rate = hourly_rate * Decimal("1.5")
        
        # Calculate earnings
        regular_pay = total_regular_hours * hourly_rate
        overtime_pay = total_overtime_hours * overtime_rate
        gross_pay = regular_pay + overtime_pay
        
        # Calculate deductions (simplified - 15% tax, 10.5% super)
        tax_withheld = gross_pay * Decimal("0.15")
        superannuation = gross_pay * Decimal("0.105")
        net_pay = gross_pay - tax_withheld
        
        # Get YTD data (simplified - just use current values for MVP)
        ytd_gross = gross_pay
        ytd_tax = tax_withheld
        ytd_super = superannuation
        ytd_net = net_pay
        
        # Create payslip data
        payslip_data = {
            "employee": {
                "name": f"{employee['first_name']} {employee['last_name']}",
                "employee_number": employee["employee_number"],
                "position": employee["position"],
                "department": employee["department"],
                "tax_file_number": employee.get("tax_file_number", "Not provided")
            },
            "pay_period": {
                "week_start": timesheet.get("week_starting", ""),
                "week_end": timesheet.get("week_ending", "")
            },
            "hours": {
                "regular_hours": float(total_regular_hours),
                "overtime_hours": float(total_overtime_hours),
                "hourly_rate": float(hourly_rate)
            },
            "earnings": {
                "regular_pay": float(regular_pay),
                "overtime_pay": float(overtime_pay),
                "gross_pay": float(gross_pay)
            },
            "deductions": {
                "tax_withheld": float(tax_withheld),
                "superannuation": float(superannuation)
            },
            "net_pay": float(net_pay),
            "year_to_date": {
                "gross_pay": float(ytd_gross),
                "tax_withheld": float(ytd_tax),
                "superannuation": float(ytd_super),
                "net_pay": float(ytd_net)
            },
            "bank_details": {
                "bsb": employee.get("bsb", "Not provided"),
                "account_number": employee.get("account_number", "Not provided"),
                "superannuation_fund": employee.get("superannuation_fund", "Not provided")
            },
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Check if payslip already exists for this timesheet
        existing_payslip = await db.payslips.find_one({"timesheet_id": timesheet_id})
        
        if existing_payslip:
            # Return existing payslip
            if "_id" in existing_payslip:
                del existing_payslip["_id"]
            return {
                "success": True,
                "message": "Payslip already exists for this timesheet",
                "data": existing_payslip
            }
        
        # Save payslip to database
        payslip_record = {
            "id": str(uuid4()),
            "timesheet_id": timesheet_id,
            "employee_id": employee["id"],
            "payslip_data": payslip_data,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "generated_by": current_user["user_id"]
        }
        
        await db.payslips.insert_one(payslip_record)
        
        if "_id" in payslip_record:
            del payslip_record["_id"]
        
        return {
            "success": True,
            "message": "Payslip generated successfully",
            "data": payslip_record
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate payslip: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate payslip: {str(e)}")


@payroll_router.get("/reports/timesheets")
async def get_timesheet_report(
    employee_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(require_payroll_access)
):
    """Get timesheet report with filters"""
    
    try:
        # Build query - only show approved timesheets
        query = {"status": TimesheetStatus.APPROVED}
        
        if employee_id:
            query["employee_id"] = employee_id
        
        if start_date or end_date:
            date_query = {}
            if start_date:
                date_query["$gte"] = start_date
            if end_date:
                date_query["$lte"] = end_date
            query["week_starting"] = date_query
        
        # Get approved timesheets
        timesheets = await db.timesheets.find(query).sort("week_starting", -1).to_list(1000)
        
        # Calculate summary
        total_regular_hours = 0
        total_overtime_hours = 0
        
        for timesheet in timesheets:
            # Remove MongoDB ObjectId
            if "_id" in timesheet:
                del timesheet["_id"]
            
            # Enrich with employee name
            employee = await db.employee_profiles.find_one({"id": timesheet["employee_id"]})
            if employee:
                timesheet["employee_name"] = f"{employee['first_name']} {employee['last_name']}"
            else:
                timesheet["employee_name"] = "Unknown"
            
            # Get approver name if approved
            if timesheet.get("approved_by"):
                approver = await db.users.find_one({"id": timesheet["approved_by"]})
                if approver:
                    timesheet["approver_name"] = approver.get("full_name", "Unknown")
            
            # Calculate hours
            entries = timesheet.get("entries", [])
            for entry in entries:
                total_regular_hours += entry.get("regular_hours", 0)
                total_overtime_hours += entry.get("overtime_hours", 0)
            
            # Add fields for display
            timesheet["total_regular_hours"] = sum(e.get("regular_hours", 0) for e in entries)
            timesheet["total_overtime_hours"] = sum(e.get("overtime_hours", 0) for e in entries)
            timesheet["week_start"] = timesheet.get("week_starting", "")
            timesheet["week_end"] = timesheet.get("week_ending", "")
        
        summary = {
            "total_timesheets": len(timesheets),
            "total_regular_hours": round(total_regular_hours, 2),
            "total_overtime_hours": round(total_overtime_hours, 2),
            "total_hours": round(total_regular_hours + total_overtime_hours, 2)
        }
        
        return {
            "success": True,
            "data": timesheets,
            "summary": summary
        }
        
    except Exception as e:
        logger.error(f"Failed to load timesheet report: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load timesheet report: {str(e)}")
