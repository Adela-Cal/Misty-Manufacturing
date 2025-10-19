#!/usr/bin/env python3
"""
Payroll Employee Synchronization Investigation
Investigating why some users from Staff and Security are not appearing in the Payroll employees list.

Test Objectives:
1. Check how many users exist in Staff and Security
2. Check how many employee profiles exist in Payroll
3. Identify which users don't have employee profiles
4. Verify the sync logic is working correctly
"""

import requests
import json
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:8001')
API_BASE = f"{BACKEND_URL}/api"

class PayrollSyncInvestigator:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        
    def authenticate(self):
        """Authenticate with demo user"""
        print("🔐 Authenticating...")
        
        try:
            response = self.session.post(f"{API_BASE}/auth/login", json={
                "username": "Callum",
                "password": "Peach7510"
            })
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get('access_token')
                self.session.headers.update({
                    'Authorization': f'Bearer {self.auth_token}'
                })
                
                user_info = data.get('user', {})
                print(f"✅ Authenticated as {user_info.get('username')} with role {user_info.get('role')}")
                return True
            else:
                print(f"❌ Authentication failed with status {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication error: {str(e)}")
            return False

    def investigate_user_employee_discrepancy(self):
        """Main investigation function"""
        print("\n" + "="*80)
        print("🔍 PAYROLL EMPLOYEE SYNCHRONIZATION INVESTIGATION")
        print("Investigating why some users are missing from payroll employees list")
        print("="*80)
        
        # Step 1: Get all users from Staff and Security
        print("\n📋 STEP 1: Getting all users from Staff and Security...")
        users = self.get_all_users()
        if not users:
            print("❌ Failed to get users. Cannot continue investigation.")
            return
        
        # Step 2: Get all employee profiles from Payroll
        print("\n💼 STEP 2: Getting all employee profiles from Payroll...")
        employees = self.get_all_employees()
        if employees is None:
            print("❌ Failed to get employees. Cannot continue investigation.")
            return
        
        # Step 3: Analyze the discrepancy
        print("\n🔍 STEP 3: Analyzing user vs employee discrepancy...")
        self.analyze_discrepancy(users, employees)
        
        # Step 4: Test manual sync
        print("\n🔄 STEP 4: Testing manual sync functionality...")
        self.test_manual_sync()
        
        # Step 5: Re-check after sync
        print("\n📊 STEP 5: Re-checking after manual sync...")
        employees_after_sync = self.get_all_employees()
        if employees_after_sync is not None:
            self.analyze_discrepancy(users, employees_after_sync, after_sync=True)
        
        # Step 6: Check for specific issues
        print("\n🔧 STEP 6: Checking for specific sync issues...")
        self.check_sync_issues(users, employees_after_sync or employees)

    def get_all_users(self):
        """Get all users from Staff and Security"""
        try:
            response = self.session.get(f"{API_BASE}/users")
            
            if response.status_code == 200:
                users = response.json()
                active_users = [user for user in users if user.get("is_active", True)]
                
                print(f"📊 Total users in Staff and Security: {len(users)}")
                print(f"📊 Active users: {len(active_users)}")
                
                # Show user details
                print("\n👥 User Details:")
                for i, user in enumerate(active_users, 1):
                    print(f"  {i}. {user.get('full_name', 'N/A')} ({user.get('username')}) - {user.get('role')} - {user.get('department', 'N/A')}")
                
                return active_users
            else:
                print(f"❌ Failed to get users: {response.status_code}")
                print(f"Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error getting users: {str(e)}")
            return None

    def get_all_employees(self):
        """Get all employee profiles from Payroll"""
        try:
            response = self.session.get(f"{API_BASE}/payroll/employees")
            
            if response.status_code == 200:
                employees = response.json()
                
                print(f"📊 Total employee profiles in Payroll: {len(employees)}")
                
                # Show employee details
                print("\n💼 Employee Details:")
                for i, emp in enumerate(employees, 1):
                    print(f"  {i}. {emp.get('first_name')} {emp.get('last_name')} ({emp.get('employee_number')}) - {emp.get('position')} - User ID: {emp.get('user_id')}")
                
                return employees
            else:
                print(f"❌ Failed to get employees: {response.status_code}")
                print(f"Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error getting employees: {str(e)}")
            return None

    def analyze_discrepancy(self, users, employees, after_sync=False):
        """Analyze discrepancy between users and employees"""
        prefix = "🔄 AFTER SYNC" if after_sync else "🔍 BEFORE SYNC"
        print(f"\n{prefix} - DISCREPANCY ANALYSIS:")
        print("-" * 60)
        
        # Create lookup dictionaries
        user_lookup = {user.get("id"): user for user in users}
        employee_user_ids = {emp.get("user_id") for emp in employees if emp.get("user_id")}
        
        # Find users without employee profiles
        missing_employees = []
        for user in users:
            user_id = user.get("id")
            if user_id not in employee_user_ids:
                missing_employees.append(user)
        
        # Find employees without corresponding users
        orphaned_employees = []
        for emp in employees:
            user_id = emp.get("user_id")
            if user_id and user_id not in user_lookup:
                orphaned_employees.append(emp)
        
        print(f"📊 Users in Staff & Security: {len(users)}")
        print(f"📊 Employee profiles in Payroll: {len(employees)}")
        print(f"📊 Users missing employee profiles: {len(missing_employees)}")
        print(f"📊 Orphaned employee profiles: {len(orphaned_employees)}")
        
        if missing_employees:
            print(f"\n❌ USERS MISSING FROM PAYROLL ({len(missing_employees)}):")
            for i, user in enumerate(missing_employees, 1):
                print(f"  {i}. {user.get('full_name', 'N/A')} ({user.get('username')}) - {user.get('role')} - ID: {user.get('id')}")
                print(f"     Department: {user.get('department', 'N/A')}, Active: {user.get('is_active', 'N/A')}")
        
        if orphaned_employees:
            print(f"\n⚠️  ORPHANED EMPLOYEE PROFILES ({len(orphaned_employees)}):")
            for i, emp in enumerate(orphaned_employees, 1):
                print(f"  {i}. {emp.get('first_name')} {emp.get('last_name')} - User ID: {emp.get('user_id')}")
        
        if not missing_employees and not orphaned_employees:
            print("✅ Perfect sync! All users have corresponding employee profiles.")
        
        return missing_employees, orphaned_employees

    def test_manual_sync(self):
        """Test manual sync endpoint"""
        try:
            print("🔄 Triggering manual sync...")
            response = self.session.post(f"{API_BASE}/payroll/employees/sync")
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("success"):
                    data = result.get("data", {})
                    created_count = data.get("created_count", 0)
                    total_employees = data.get("total_employees", 0)
                    
                    print(f"✅ Manual sync completed successfully")
                    print(f"📊 New employee profiles created: {created_count}")
                    print(f"📊 Total employee profiles after sync: {total_employees}")
                    
                    return True
                else:
                    print(f"❌ Manual sync failed: {result.get('message', 'Unknown error')}")
                    return False
            else:
                print(f"❌ Manual sync failed with status {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error during manual sync: {str(e)}")
            return False

    def check_sync_issues(self, users, employees):
        """Check for specific sync issues"""
        print("\n🔧 CHECKING FOR SPECIFIC SYNC ISSUES:")
        print("-" * 50)
        
        # Check 1: User ID format issues
        print("1. Checking user ID formats...")
        uuid_users = 0
        non_uuid_users = 0
        
        for user in users:
            user_id = user.get("id", "")
            if len(user_id) == 36 and user_id.count("-") == 4:  # UUID format
                uuid_users += 1
            else:
                non_uuid_users += 1
                print(f"   ⚠️  Non-UUID user ID: {user.get('username')} - ID: {user_id}")
        
        print(f"   📊 UUID format users: {uuid_users}")
        print(f"   📊 Non-UUID format users: {non_uuid_users}")
        
        # Check 2: Active status issues
        print("\n2. Checking user active status...")
        active_users = [u for u in users if u.get("is_active", True)]
        inactive_users = [u for u in users if not u.get("is_active", True)]
        
        print(f"   📊 Active users: {len(active_users)}")
        print(f"   📊 Inactive users: {len(inactive_users)}")
        
        if inactive_users:
            print("   ⚠️  Inactive users (should not sync to payroll):")
            for user in inactive_users:
                print(f"      - {user.get('full_name')} ({user.get('username')})")
        
        # Check 3: Required field issues
        print("\n3. Checking required fields...")
        users_missing_fields = []
        
        for user in users:
            missing_fields = []
            if not user.get("username"):
                missing_fields.append("username")
            if not user.get("full_name"):
                missing_fields.append("full_name")
            if not user.get("email"):
                missing_fields.append("email")
            
            if missing_fields:
                users_missing_fields.append((user, missing_fields))
        
        if users_missing_fields:
            print(f"   ⚠️  Users missing required fields: {len(users_missing_fields)}")
            for user, missing in users_missing_fields:
                print(f"      - {user.get('username', 'N/A')}: missing {', '.join(missing)}")
        else:
            print("   ✅ All users have required fields")
        
        # Check 4: Employee number conflicts
        print("\n4. Checking employee number conflicts...")
        employee_numbers = [emp.get("employee_number") for emp in employees if emp.get("employee_number")]
        duplicate_numbers = []
        
        for num in set(employee_numbers):
            if employee_numbers.count(num) > 1:
                duplicate_numbers.append(num)
        
        if duplicate_numbers:
            print(f"   ⚠️  Duplicate employee numbers: {duplicate_numbers}")
        else:
            print("   ✅ No duplicate employee numbers found")

    def check_backend_logs(self):
        """Check backend logs for sync errors"""
        print("\n📋 CHECKING BACKEND LOGS:")
        print("-" * 30)
        
        try:
            # This would require access to backend logs
            # For now, we'll just indicate what to check
            print("To check backend logs, run:")
            print("  tail -n 100 /var/log/supervisor/backend.*.log")
            print("\nLook for:")
            print("  - Employee sync errors")
            print("  - Database connection issues")
            print("  - User validation failures")
            print("  - Employee creation errors")
            
        except Exception as e:
            print(f"❌ Error checking logs: {str(e)}")

def main():
    """Main investigation function"""
    investigator = PayrollSyncInvestigator()
    
    # Authenticate
    if not investigator.authenticate():
        print("❌ Authentication failed. Cannot proceed with investigation.")
        return
    
    # Run investigation
    investigator.investigate_user_employee_discrepancy()
    
    # Check backend logs
    investigator.check_backend_logs()
    
    print("\n" + "="*80)
    print("🎯 INVESTIGATION COMPLETE")
    print("="*80)
    print("If users are still missing from payroll after manual sync:")
    print("1. Check backend logs for specific error messages")
    print("2. Verify user data integrity (required fields)")
    print("3. Check for database connection issues")
    print("4. Verify sync logic handles all user ID formats")
    print("5. Test with specific problematic user IDs")

if __name__ == "__main__":
    main()