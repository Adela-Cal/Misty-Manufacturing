# User Accounts and Role-Based Access Control

## Overview
The Misty Manufacturing application implements role-based access control (RBAC) to ensure users only have access to features relevant to their role.

## User Accounts

### 1. Admin User
- **Username:** Callum
- **Password:** Peach7510
- **Full Name:** Callum - System Administrator
- **Role:** admin
- **Email:** Callum@adelamerchants.com.au

### 2. Manager Users
#### Bubbles (Zach JJ Sanders)
- **Username:** Bubbles
- **Password:** Fugger
- **Full Name:** Zach JJ Sanders
- **Role:** manager
- **Email:** Zach@adelamerchants.com.au

#### Fuzzy (Callum Hughes)
- **Username:** Fuzzy
- **Password:** Coldcuts
- **Full Name:** Callum Hughes
- **Role:** manager
- **Email:** Staff@adelamerchants.com.au

### 3. Production Staff
- **Username:** ProductionStaff
- **Password:** TestStaff123
- **Full Name:** Production Staff Test
- **Role:** production_staff
- **Email:** staff@adelamerchants.com.au

---

## Role-Based Access Matrix

### Admin (Full Access)
**Access to ALL features:**
- ✅ Dashboard
- ✅ Clients
- ✅ Orders
- ✅ Production (Production Board)
- ✅ Invoicing
- ✅ Payroll (all features)
- ✅ Reports
- ✅ Raw Materials
- ✅ Suppliers List
- ✅ Products & Specifications
- ✅ Machinery Specifications
- ✅ Calculators
- ✅ Stocktake
- ✅ Label Designer
- ✅ **Staff & Security** (Admin Only)

### Manager (Everything Except Staff & Security)
**Access to almost all features:**
- ✅ Dashboard
- ✅ Clients
- ✅ Orders
- ✅ Production (Production Board)
- ✅ Invoicing
- ✅ Payroll (all features including approvals)
- ✅ Reports
- ✅ Raw Materials
- ✅ Suppliers List
- ✅ Products & Specifications
- ✅ Machinery Specifications
- ✅ Calculators
- ✅ Stocktake
- ✅ Label Designer
- ❌ **Staff & Security** (Admin Only)

### Production Staff (Limited Access)
**Access to only essential production features:**
- ✅ Dashboard
- ✅ Production (Production Board)
- ✅ Payroll (own timesheets only)
- ✅ Calculators
- ✅ Label Designer
- ❌ Clients
- ❌ Orders
- ❌ Invoicing
- ❌ Reports
- ❌ Raw Materials
- ❌ Suppliers List
- ❌ Products & Specifications
- ❌ Machinery Specifications
- ❌ Stocktake
- ❌ Staff & Security

---

## Permission Details

### Frontend Permissions (AuthContext.js)
The following permissions control access to features:

| Permission | Roles with Access |
|------------|-------------------|
| `admin` | admin |
| `manage_clients` | admin, manager, sales |
| `create_orders` | admin, manager, production_manager, sales |
| `update_production` | admin, manager, production_manager, production_staff |
| `invoice` | admin, manager, production_manager |
| `view_reports` | admin, manager, production_manager, sales |
| `manage_payroll` | admin, manager |
| `view_all_timesheets` | admin, manager, production_manager |
| `submit_timesheet` | admin, manager, production_manager, production_staff, employee |
| `access_payroll` | All authenticated users (for own timesheets) |
| `view_production_board` | admin, manager, production_manager, production_staff |
| `use_calculators` | admin, manager, production_manager, production_staff, sales |
| `use_label_designer` | admin, manager, production_manager, production_staff |

### Backend Permissions (auth.py)
The backend uses the following role-based dependencies:

- `require_admin` - Admin only
- `require_manager` - Admin and Manager
- `require_any_role` - All authenticated users with valid roles
- `require_production_access` - Admin, Production Manager, Manager, Production Staff
- `require_payroll_access` - Admin and Manager

---

## Adding New Users

### Steps to Add a New Staff Member:

1. **Create User Account** in Staff & Security (Admin only)
2. **Assign Appropriate Role:**
   - `admin` - Full system access
   - `manager` - All features except Staff & Security
   - `production_staff` - Dashboard, Production Board, Payroll, Calculators, Label Designer only
   - `sales` - Sales-focused access
   - `production_manager` - Production management access

3. **Create Employee Profile** in Payroll (for timesheet access)
4. **Test Login** to verify correct access level

### Important Notes:
- All users must have `is_active: true` to log in
- Users must have a password set (hashed_password field)
- Employee profiles are separate from user accounts
- Payroll access requires both user account and employee profile

---

## Security Best Practices

1. **Never share admin credentials**
2. **Use strong passwords** for all accounts
3. **Regularly review user access** in Staff & Security
4. **Deactivate users** when they leave (don't delete)
5. **Monitor login activity** through the system logs
6. **Update passwords** periodically

---

## Troubleshooting

### User Cannot Log In
- Verify `is_active` is set to `true`
- Confirm password is set correctly
- Check role is assigned
- Ensure no typos in username

### User Cannot See Expected Features
- Verify role is correct
- Check permission mappings in AuthContext.js
- Ensure user has logged out and back in after role changes
- Clear browser cache/cookies

### Timesheet Issues
- User must have an employee_profile record
- Employee profile must link to user account via user_id
- Check employee profile has required fields (hourly_rate, etc.)

---

**Last Updated:** October 21, 2025
**System Version:** Production v1.0
