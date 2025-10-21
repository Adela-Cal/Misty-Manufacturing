from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from models import User, UserRole
import os

# Security configuration
SECRET_KEY = os.environ.get("SECRET_KEY", "misty-manufacturing-secret-key-2024")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 8 * 60  # 8 hours
REFRESH_TOKEN_EXPIRE_DAYS = 30  # 30 days for refresh tokens

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
security = HTTPBearer()

# Password hashing
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def hash_password(password: str) -> str:
    """Alias for get_password_hash for consistency"""
    return get_password_hash(password)

# JWT token functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        return payload
    except JWTError:
        return None

# Authentication dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = credentials.credentials
    payload = verify_token(token)
    if payload is None:
        raise credentials_exception
    
    return payload

# Role-based permission decorators
def require_role(allowed_roles: list[UserRole]):
    def role_checker(current_user: dict = Depends(get_current_user)):
        user_role = current_user.get("role")
        if user_role not in [role.value for role in allowed_roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker

# Pre-defined permission dependencies
require_admin = require_role([UserRole.ADMIN])
require_admin_or_manager = require_role([UserRole.ADMIN, UserRole.MANAGER])
require_manager_or_admin = require_role([UserRole.ADMIN, UserRole.MANAGER])
require_admin_or_sales = require_role([UserRole.ADMIN, UserRole.SALES])  # Added
require_production_access = require_role([UserRole.ADMIN, UserRole.PRODUCTION_MANAGER, UserRole.MANAGER, UserRole.PRODUCTION_TEAM])
require_any_role = require_role([UserRole.ADMIN, UserRole.PRODUCTION_MANAGER, UserRole.MANAGER, UserRole.PRODUCTION_TEAM, UserRole.SALES])

# Updated permission dependencies for new roles
require_supervisor_or_higher = require_role([UserRole.ADMIN, UserRole.PRODUCTION_MANAGER, UserRole.MANAGER])
require_production_staff_or_higher = require_role([UserRole.ADMIN, UserRole.PRODUCTION_MANAGER, UserRole.MANAGER, UserRole.PRODUCTION_TEAM])

# New payroll permission dependencies
require_manager = require_role([UserRole.ADMIN, UserRole.MANAGER])
require_payroll_access = require_role([UserRole.ADMIN, UserRole.PRODUCTION_MANAGER, UserRole.MANAGER])
require_payroll_management = require_role([UserRole.ADMIN, UserRole.MANAGER])
require_employee_or_manager = require_role([UserRole.ADMIN, UserRole.PRODUCTION_MANAGER, UserRole.MANAGER, UserRole.PRODUCTION_TEAM])

# Permission checking functions
def can_create_orders(user_role: str) -> bool:
    return user_role in [UserRole.ADMIN.value, UserRole.PRODUCTION_MANAGER.value, UserRole.SALES.value]

def can_update_production_stage(user_role: str) -> bool:
    return user_role in [UserRole.ADMIN.value, UserRole.PRODUCTION_MANAGER.value, UserRole.PRODUCTION_TEAM.value]

def can_invoice(user_role: str) -> bool:
    return user_role in [UserRole.ADMIN.value, UserRole.PRODUCTION_MANAGER.value]

def can_delete_orders(user_role: str) -> bool:
    return user_role in [UserRole.ADMIN.value, UserRole.PRODUCTION_MANAGER.value]

def can_manage_clients(user_role: str) -> bool:
    return user_role in [UserRole.ADMIN.value, UserRole.SALES.value]

def can_view_reports(user_role: str) -> bool:
    return user_role in [UserRole.ADMIN.value, UserRole.PRODUCTION_MANAGER.value, UserRole.SALES.value]

def can_manage_payroll(user_role: str) -> bool:
    """Check if user can manage payroll functions"""
    return user_role in [UserRole.ADMIN.value, UserRole.MANAGER.value]

def can_view_all_timesheets(user_role: str) -> bool:
    """Check if user can view all employee timesheets"""
    return user_role in [UserRole.ADMIN.value, UserRole.PRODUCTION_MANAGER.value, UserRole.MANAGER.value]

def can_approve_leave(user_role: str) -> bool:
    """Check if user can approve leave requests"""
    return user_role in [UserRole.ADMIN.value, UserRole.PRODUCTION_MANAGER.value, UserRole.MANAGER.value]

def can_view_payroll_reports(user_role: str) -> bool:
    """Check if user can view payroll reports"""
    return user_role in [UserRole.ADMIN.value, UserRole.MANAGER.value]