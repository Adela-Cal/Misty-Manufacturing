from pydantic import BaseModel, Field, EmailStr, validator
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from enum import Enum
import uuid
from decimal import Decimal

# Enhanced User Roles for Payroll System
class UserRole(str, Enum):
    ADMIN = "admin"
    PRODUCTION_MANAGER = "production_manager"
    SALES = "sales"
    PRODUCTION_TEAM = "production_team"
    MANAGER = "manager"
    EMPLOYEE = "employee"

# Leave Types
class LeaveType(str, Enum):
    ANNUAL_LEAVE = "annual_leave"
    SICK_LEAVE = "sick_leave"
    PERSONAL_LEAVE = "personal_leave"
    MATERNITY_LEAVE = "maternity_leave"
    PATERNITY_LEAVE = "paternity_leave"
    TRAINING_LEAVE = "training_leave"
    CONFERENCE_LEAVE = "conference_leave"
    COMPASSIONATE_LEAVE = "compassionate_leave"
    UNPAID_LEAVE = "unpaid_leave"

# Leave Request Status
class LeaveStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"

# Timesheet Status
class TimesheetStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"

# Employee Models
class EmployeeProfile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str  # Links to existing user system
    employee_number: str
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None
    department: Optional[str] = None
    position: str
    manager_id: Optional[str] = None
    
    # Employment Details
    start_date: date
    employment_type: str = "full_time"  # full_time, part_time, casual, contract
    hourly_rate: Decimal
    weekly_hours: int = 38
    
    # Leave Entitlements (hours per year)
    annual_leave_entitlement: int = 152  # 4 weeks for full-time
    sick_leave_entitlement: int = 76     # 2 weeks for full-time
    personal_leave_entitlement: int = 38  # 1 week for full-time
    
    # Current Leave Balances (hours)
    annual_leave_balance: Decimal = Decimal('0')
    sick_leave_balance: Decimal = Decimal('0')
    personal_leave_balance: Decimal = Decimal('0')
    
    # Payroll Settings
    tax_file_number: Optional[str] = None
    superannuation_fund: Optional[str] = None
    bank_account_bsb: Optional[str] = None
    bank_account_number: Optional[str] = None
    
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

class EmployeeProfileCreate(BaseModel):
    user_id: str
    employee_number: str
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None
    department: Optional[str] = None
    position: str
    manager_id: Optional[str] = None
    start_date: date
    employment_type: str = "full_time"
    hourly_rate: Decimal
    weekly_hours: int = 38
    annual_leave_entitlement: int = 152
    sick_leave_entitlement: int = 76
    personal_leave_entitlement: int = 38
    tax_file_number: Optional[str] = None
    superannuation_fund: Optional[str] = None
    bank_account_bsb: Optional[str] = None
    bank_account_number: Optional[str] = None
    
    @validator('hourly_rate')
    def validate_hourly_rate(cls, v):
        if v <= 0:
            raise ValueError('Hourly rate must be positive')
        return v

# Leave Request Models
class LeaveRequest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    employee_id: str
    leave_type: LeaveType
    start_date: date
    end_date: date
    hours_requested: Decimal
    reason: Optional[str] = None
    status: LeaveStatus = LeaveStatus.PENDING
    requested_by: str
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

class LeaveRequestCreate(BaseModel):
    employee_id: str
    leave_type: LeaveType
    start_date: date
    end_date: date
    hours_requested: Decimal
    reason: Optional[str] = None
    
    @validator('end_date')
    def validate_end_date(cls, v, values):
        if 'start_date' in values and v < values['start_date']:
            raise ValueError('End date must be after start date')
        return v
    
    @validator('hours_requested')
    def validate_hours_requested(cls, v):
        if v <= 0:
            raise ValueError('Hours requested must be positive')
        return v

# Timesheet Models
class TimesheetEntry(BaseModel):
    date: datetime  # Changed to datetime for MongoDB compatibility
    regular_hours: float = 0.0
    overtime_hours: float = 0.0
    leave_hours: Dict[LeaveType, float] = {}
    notes: Optional[str] = None

class Timesheet(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    employee_id: str
    week_starting: datetime  # Monday of the week (as datetime for MongoDB compatibility)
    week_ending: datetime    # Sunday of the week (as datetime for MongoDB compatibility)
    entries: List[TimesheetEntry] = []
    
    # Calculated totals
    total_regular_hours: float = 0.0
    total_overtime_hours: float = 0.0
    total_leave_hours: Dict[LeaveType, float] = {}
    
    status: TimesheetStatus = TimesheetStatus.DRAFT
    submitted_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

class TimesheetCreate(BaseModel):
    employee_id: str
    week_starting: datetime
    entries: List[TimesheetEntry]

# Payroll Calculation Models
class PayrollCalculation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    employee_id: str
    timesheet_id: str
    pay_period_start: date
    pay_period_end: date
    
    # Hours
    regular_hours: Decimal
    overtime_hours: Decimal
    total_hours: Decimal
    
    # Pay Calculations
    regular_pay: Decimal
    overtime_pay: Decimal  # Usually 1.5x or 2x rate
    gross_pay: Decimal
    
    # Deductions
    tax_withheld: Decimal
    superannuation: Decimal  # Usually 11% of gross pay
    
    # Net Pay
    net_pay: Decimal
    
    # Leave Accruals (hours earned this period)
    annual_leave_accrued: Decimal
    sick_leave_accrued: Decimal
    personal_leave_accrued: Decimal
    
    # Leave Used (hours taken this period)
    leave_taken: Dict[LeaveType, Decimal] = {}
    
    calculated_at: datetime = Field(default_factory=datetime.utcnow)
    calculated_by: str

# Response Models
class EmployeeLeaveBalance(BaseModel):
    employee_id: str
    employee_name: str
    annual_leave_balance: Decimal
    sick_leave_balance: Decimal
    personal_leave_balance: Decimal
    annual_leave_entitlement: int
    sick_leave_entitlement: int
    personal_leave_entitlement: int

class PayrollSummary(BaseModel):
    employee_id: str
    employee_name: str
    pay_period: str
    gross_pay: Decimal
    net_pay: Decimal
    hours_worked: Decimal
    leave_taken: Dict[LeaveType, Decimal]
    leave_accrued: Dict[str, Decimal]

class TeamLeaveCalendar(BaseModel):
    date: date
    employees_on_leave: List[Dict[str, Any]]
    total_employees: int
    employees_available: int
    coverage_percentage: float

# Settings Models
class PayrollSettings(BaseModel):
    overtime_multiplier: Decimal = Decimal('1.5')
    superannuation_rate: Decimal = Decimal('0.11')  # 11%
    tax_free_threshold: Decimal = Decimal('18200')  # Annual
    leave_accrual_frequency: str = "weekly"  # weekly, fortnightly, monthly
    timesheet_reminder_day: str = "thursday"
    auto_approve_timesheets: bool = False
    max_daily_hours: Decimal = Decimal('12')
    standard_work_week: int = 5  # days

class StandardResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None