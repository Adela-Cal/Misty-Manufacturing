# This file shows the additions needed to the main server.py file
# Add these imports at the top of server.py:

from payroll_endpoints import payroll_router
from payroll_models import UserRole  # Update the existing import

# Add this line after creating the api_router:
api_router.include_router(payroll_router)

# Update the startup event to create additional collections:

@app.on_event("startup")
async def startup_event():
    """Initialize system on startup"""
    logger.info("Starting Misty Manufacturing Management System...")
    
    # Create default admin user if not exists
    admin_user = await db.users.find_one({"username": "Callum"})
    if not admin_user:
        logger.info("Creating default admin user...")
        default_admin = User(
            username="Callum",
            email="admin@adelamerchants.com.au",
            hashed_password=get_password_hash("Peach7510"),
            role=UserRole.ADMIN,
            full_name="Callum - System Administrator"
        )
        await db.users.insert_one(default_admin.dict())
        logger.info("Default admin user created successfully")
    
    # Create indexes for payroll collections
    try:
        await db.employee_profiles.create_index("employee_number", unique=True)
        await db.employee_profiles.create_index("user_id")
        await db.timesheets.create_index([("employee_id", 1), ("week_starting", 1)], unique=True)
        await db.leave_requests.create_index("employee_id")
        await db.leave_requests.create_index("status")
        await db.payroll_calculations.create_index("employee_id")
        await db.payroll_calculations.create_index("pay_period_start")
        logger.info("Payroll database indexes created successfully")
    except Exception as e:
        logger.warning(f"Some indexes may already exist: {e}")
    
    logger.info("Misty Manufacturing Management System started successfully!")

# Additional endpoint to create employee users:

@api_router.post("/auth/create-employee-user", response_model=StandardResponse)
async def create_employee_user(user_data: UserCreate, current_user: dict = Depends(require_admin)):
    """Create new employee user account (Admin only)"""
    
    # Check if username already exists
    existing_user = await db.users.find_one({"username": user_data.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Check if email already exists
    existing_email = await db.users.find_one({"email": user_data.email})
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already exists")
    
    # Create new user with employee or manager role
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        role=user_data.role,
        full_name=user_data.full_name
    )
    
    await db.users.insert_one(new_user.dict())
    
    return StandardResponse(success=True, message="Employee user created successfully", data={"id": new_user.id, "user_id": new_user.id})