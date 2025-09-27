from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, status
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os
from auth import require_admin, require_admin_or_production_manager, get_current_user, require_any_role, require_manager, require_payroll_access
from payroll_models import *
from payroll_service import PayrollCalculationService, TimesheetService, LeaveManagementService, PayrollReportingService
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

# ============= EMPLOYEE MANAGEMENT ENDPOINTS =============

@payroll_router.get("/employees", response_model=List[EmployeeProfile])
async def get_employees(current_user: dict = Depends(require_payroll_access)):
    """Get all employees (Admin/Manager only)"""
    employees = await db.employee_profiles.find({"is_active": True}).to_list(1000)
    return [EmployeeProfile(**emp) for emp in employees]

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
    
    await db.employee_profiles.insert_one(new_employee.dict())
    
    logger.info(f"Created employee profile for {new_employee.first_name} {new_employee.last_name}")
    
    return StandardResponse(success=True, message="Employee created successfully", data={"id": new_employee.id})

@payroll_router.get("/employees/{employee_id}", response_model=EmployeeProfile)
async def get_employee(employee_id: str, current_user: dict = Depends(require_payroll_access)):
    """Get specific employee (Admin/Manager only)"""
    employee = await db.employee_profiles.find_one({"id": employee_id, "is_active": True})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
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
    
    # Check access permissions
    if current_user["role"] not in ["admin", "manager", "production_manager"] and current_user["user_id"] != employee_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    week_starting = timesheet_service.get_current_week_starting()
    
    # Try to find existing timesheet
    existing_timesheet = await db.timesheets.find_one({
        "employee_id": employee_id,
        "week_starting": week_starting
    })
    
    if existing_timesheet:
        return Timesheet(**existing_timesheet)
    
    # Create new timesheet if it doesn't exist
    new_timesheet = timesheet_service.generate_weekly_timesheet(employee_id, week_starting)
    await db.timesheets.insert_one(new_timesheet.dict())
    
    return new_timesheet

@payroll_router.put("/timesheets/{timesheet_id}", response_model=StandardResponse)
async def update_timesheet(timesheet_id: str, timesheet_data: TimesheetCreate, current_user: dict = Depends(require_any_role)):
    """Update timesheet entries"""
    
    # Get existing timesheet
    existing_timesheet = await db.timesheets.find_one({"id": timesheet_id})
    if not existing_timesheet:
        raise HTTPException(status_code=404, detail="Timesheet not found")
    
    # Check access permissions
    if current_user["role"] not in ["admin", "manager", "production_manager"] and current_user["user_id"] != existing_timesheet["employee_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Update timesheet
    timesheet = Timesheet(**existing_timesheet)
    timesheet.entries = timesheet_data.entries
    timesheet.updated_at = datetime.utcnow()
    
    # Calculate totals
    timesheet = timesheet_service.calculate_timesheet_totals(timesheet)
    
    # Save updated timesheet
    await db.timesheets.update_one(
        {"id": timesheet_id},
        {"$set": timesheet.dict()}
    )
    
    return StandardResponse(success=True, message="Timesheet updated successfully")

@payroll_router.post("/timesheets/{timesheet_id}/submit", response_model=StandardResponse)
async def submit_timesheet(timesheet_id: str, current_user: dict = Depends(require_any_role)):
    """Submit timesheet for approval"""
    
    timesheet = await db.timesheets.find_one({"id": timesheet_id})
    if not timesheet:
        raise HTTPException(status_code=404, detail="Timesheet not found")
    
    # Check access permissions
    if current_user["role"] not in ["admin", "manager", "production_manager"] and current_user["user_id"] != timesheet["employee_id"]:
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

@payroll_router.post("/timesheets/{timesheet_id}/approve", response_model=StandardResponse)
async def approve_timesheet(timesheet_id: str, current_user: dict = Depends(require_admin_or_production_manager), db: Session = Depends(get_db)):
    """Approve timesheet and calculate pay (Manager only)"""
    
    timesheet_doc = await db.timesheets.find_one({"id": timesheet_id})
    if not timesheet_doc:
        raise HTTPException(status_code=404, detail="Timesheet not found")
    
    timesheet = Timesheet(**timesheet_doc)
    
    # Get employee profile
    employee_doc = await db.employee_profiles.find_one({"id": timesheet.employee_id})
    if not employee_doc:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    employee = EmployeeProfile(**employee_doc)
    
    # Calculate payroll
    payroll_calculation = payroll_calc_service.calculate_weekly_pay(employee, timesheet)
    
    # Save payroll calculation
    await db.payroll_calculations.insert_one(payroll_calculation.dict())
    
    # Update timesheet status
    await db.timesheets.update_one(
        {"id": timesheet_id},
        {"$set": {
            "status": TimesheetStatus.APPROVED,
            "approved_by": current_user["user_id"],
            "approved_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }}
    )
    
    # Update employee leave balances
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
        {"$set": leave_updates}
    )
    
    logger.info(f"Approved timesheet {timesheet_id} and calculated pay: ${payroll_calculation.gross_pay}")
    
    return StandardResponse(
        success=True, 
        message="Timesheet approved and pay calculated", 
        data={
            "gross_pay": float(payroll_calculation.gross_pay),
            "net_pay": float(payroll_calculation.net_pay),
            "hours_worked": float(payroll_calculation.total_hours)
        }
    )

@payroll_router.get("/timesheets/pending")
async def get_pending_timesheets(current_user: dict = Depends(require_admin_or_production_manager), db: Session = Depends(get_db)):
    """Get all pending timesheets for approval"""
    
    pending_timesheets = await db.timesheets.find({"status": TimesheetStatus.SUBMITTED}).to_list(1000)
    
    # Enrich with employee names
    for timesheet in pending_timesheets:
        employee = await db.employee_profiles.find_one({"id": timesheet["employee_id"]})
        if employee:
            timesheet["employee_name"] = f"{employee['first_name']} {employee['last_name']}"
    
    return {"success": True, "data": pending_timesheets}

# ============= LEAVE REQUEST ENDPOINTS =============

@payroll_router.post("/leave-requests", response_model=StandardResponse)
async def create_leave_request(leave_data: LeaveRequestCreate, current_user: dict = Depends(require_any_role), db: Session = Depends(get_db)):
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
    leave_request = LeaveRequest(
        **leave_data.dict(),
        requested_by=current_user["user_id"]
    )
    
    await db.leave_requests.insert_one(leave_request.dict())
    
    return StandardResponse(success=True, message="Leave request created successfully", data={"id": leave_request.id})

@payroll_router.get("/leave-requests/pending")
async def get_pending_leave_requests(current_user: dict = Depends(require_admin_or_production_manager), db: Session = Depends(get_db)):
    """Get all pending leave requests"""
    
    pending_requests = await db.leave_requests.find({"status": LeaveStatus.PENDING}).to_list(1000)
    
    # Enrich with employee names
    for request in pending_requests:
        employee = await db.employee_profiles.find_one({"id": request["employee_id"]})
        if employee:
            request["employee_name"] = f"{employee['first_name']} {employee['last_name']}"
    
    return {"success": True, "data": pending_requests}

@payroll_router.post("/leave-requests/{request_id}/approve", response_model=StandardResponse)
async def approve_leave_request(request_id: str, current_user: dict = Depends(require_admin_or_production_manager), db: Session = Depends(get_db)):
    """Approve leave request"""
    
    result = await db.leave_requests.update_one(
        {"id": request_id, "status": LeaveStatus.PENDING},
        {"$set": {
            "status": LeaveStatus.APPROVED,
            "approved_by": current_user["user_id"],
            "approved_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Leave request not found or already processed")
    
    return StandardResponse(success=True, message="Leave request approved")

@payroll_router.post("/leave-requests/{request_id}/reject", response_model=StandardResponse)
async def reject_leave_request(request_id: str, rejection_reason: str, current_user: dict = Depends(require_admin_or_production_manager), db: Session = Depends(get_db)):
    """Reject leave request"""
    
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
    
    return StandardResponse(success=True, message="Leave request rejected")

# ============= REPORTING ENDPOINTS =============

@payroll_router.get("/reports/payroll-summary")
async def get_payroll_summary(start_date: date, end_date: date, current_user: dict = Depends(require_admin_or_production_manager), db: Session = Depends(get_db)):
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
async def get_leave_balances_report(current_user: dict = Depends(require_admin_or_production_manager), db: Session = Depends(get_db)):
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