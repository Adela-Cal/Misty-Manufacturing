# Updates needed for auth.py to support payroll roles

# Update the UserRole enum in models.py to include new roles:
class UserRole(str, Enum):
    ADMIN = "admin"
    PRODUCTION_MANAGER = "production_manager"
    SALES = "sales"
    PRODUCTION_TEAM = "production_team"
    MANAGER = "manager"          # New role for department managers
    EMPLOYEE = "employee"        # New role for regular employees

# Add new permission checking functions to auth.py:

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

# Add new role-based permission dependencies:
require_manager = require_role([UserRole.ADMIN, UserRole.MANAGER])
require_payroll_access = require_role([UserRole.ADMIN, UserRole.MANAGER, UserRole.PRODUCTION_MANAGER])
require_employee_or_manager = require_role([UserRole.ADMIN, UserRole.MANAGER, UserRole.PRODUCTION_MANAGER, UserRole.EMPLOYEE])

# Update the hasPermission function in AuthContext to include payroll permissions:

def hasPermission(permission):
    if not user:
        return False
    
    role = user.role
    
    # Existing permissions...
    
    # New payroll permissions
    case 'manage_payroll':
        return ['admin', 'manager'].includes(role)
    case 'view_all_timesheets':
        return ['admin', 'production_manager', 'manager'].includes(role)
    case 'approve_leave':
        return ['admin', 'production_manager', 'manager'].includes(role)
    case 'view_payroll_reports':
        return ['admin', 'manager'].includes(role)
    case 'submit_timesheet':
        return ['admin', 'manager', 'production_manager', 'employee'].includes(role)
    default:
        return True