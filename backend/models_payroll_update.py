# Update to the existing models.py file
# Replace the existing UserRole enum with this expanded version:

class UserRole(str, Enum):
    ADMIN = "admin"
    PRODUCTION_MANAGER = "production_manager"
    SALES = "sales"
    PRODUCTION_TEAM = "production_team"
    MANAGER = "manager"          # New: Department/Team managers
    EMPLOYEE = "employee"        # New: Regular employees

# Add these new imports at the top of models.py:
from decimal import Decimal

# Update the User model to support employee linking:
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: EmailStr
    hashed_password: str
    role: UserRole
    full_name: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    employee_profile_id: Optional[str] = None  # New: Link to employee profile

# Update UserCreate to support new roles:
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: UserRole
    full_name: str
    
    @validator('role')
    def validate_role(cls, v):
        if v not in [role.value for role in UserRole]:
            raise ValueError('Invalid user role')
        return v