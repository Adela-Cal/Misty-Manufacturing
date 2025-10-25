#!/usr/bin/env python3
"""
Pending Timesheets Data Mismatch Investigation
Investigating the data mismatch between employees, timesheets, and users as requested
"""

import requests
import json
from datetime import datetime
import sys

# Configuration
BACKEND_URL = "https://misty-ato-payroll.preview.emergentagent.com/api"
ADMIN_USERNAME = "Callum"
ADMIN_PASSWORD = "Peach7510"

class TimesheetsInvestigator:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        
    def log_result(self, test_name, success, message, data=None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅" if success else "❌"
        print(f"{status} {test_name}: {message}")
        if data and isinstance(data, dict):
            for key, value in data.items():
                print(f"   {key}: {value}")
        print()

    def authenticate(self):
        """Authenticate with admin credentials"""
        try:
            response = self.session.post(f"{BACKEND_URL}/auth/login", json={
                "username": ADMIN_USERNAME,
                "password": ADMIN_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data["access_token"]
                self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                self.log_result("Authentication", True, f"Successfully authenticated as {ADMIN_USERNAME}")
                return True
            else:
                self.log_result("Authentication", False, f"Failed to authenticate: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Authentication", False, f"Authentication error: {str(e)}")
            return False

    def get_current_employees(self):
        """Get all current employees from payroll system"""
        try:
            response = self.session.get(f"{BACKEND_URL}/payroll/employees")
            
            if response.status_code == 200:
                result = response.json()
                employees = result.get("data", []) if isinstance(result, dict) else result
                employee_ids = [emp.get("id") for emp in employees if emp.get("id")]
                employee_details = []
                
                for emp in employees:
                    employee_details.append({
                        "id": emp.get("id"),
                        "employee_number": emp.get("employee_number"),
                        "first_name": emp.get("first_name"),
                        "last_name": emp.get("last_name"),
                        "email": emp.get("email"),
                        "user_id": emp.get("user_id")
                    })
                
                self.log_result("Get Current Employees", True, 
                              f"Found {len(employees)} employees", 
                              {"employee_count": len(employees), "employee_ids": employee_ids})
                
                print("📋 EMPLOYEE DETAILS:")
                for emp in employee_details:
                    print(f"   ID: {emp['id']}")
                    print(f"   Number: {emp['employee_number']}")
                    print(f"   Name: {emp['first_name']} {emp['last_name']}")
                    print(f"   Email: {emp['email']}")
                    print(f"   User ID: {emp['user_id']}")
                    print("   ---")
                print()
                
                return employee_ids, employee_details
                
            else:
                self.log_result("Get Current Employees", False, 
                              f"Failed to get employees: {response.status_code} - {response.text}")
                return [], []
                
        except Exception as e:
            self.log_result("Get Current Employees", False, f"Error getting employees: {str(e)}")
            return [], []

    def get_pending_timesheets(self):
        """Get pending timesheets to see employee_id values"""
        try:
            response = self.session.get(f"{BACKEND_URL}/payroll/timesheets/pending")
            
            if response.status_code == 200:
                result = response.json()
                timesheets = result.get("data", []) if isinstance(result, dict) else result
                timesheet_employee_ids = []
                timesheet_details = []
                
                for ts in timesheets:
                    employee_id = ts.get("employee_id")
                    if employee_id:
                        timesheet_employee_ids.append(employee_id)
                        timesheet_details.append({
                            "id": ts.get("id"),
                            "employee_id": employee_id,
                            "employee_name": ts.get("employee_name", "NOT_FOUND"),
                            "week_starting": ts.get("week_starting") or ts.get("week_start"),
                            "week_ending": ts.get("week_ending") or ts.get("week_end"),
                            "status": ts.get("status"),
                            "total_hours": ts.get("total_hours") or (ts.get("total_regular_hours", 0) + ts.get("total_overtime_hours", 0))
                        })
                
                self.log_result("Get Pending Timesheets", True, 
                              f"Found {len(timesheets)} pending timesheets", 
                              {"timesheet_count": len(timesheets), "unique_employee_ids": list(set(timesheet_employee_ids))})
                
                print("📋 TIMESHEET DETAILS:")
                for ts in timesheet_details:
                    print(f"   Timesheet ID: {ts['id']}")
                    print(f"   Employee ID: {ts['employee_id']}")
                    print(f"   Employee Name: {ts['employee_name']}")
                    print(f"   Week: {ts['week_starting']} to {ts['week_ending']}")
                    print(f"   Status: {ts['status']}")
                    print(f"   Total Hours: {ts['total_hours']}")
                    print("   ---")
                print()
                
                return timesheet_employee_ids, timesheet_details
                
            else:
                self.log_result("Get Pending Timesheets", False, 
                              f"Failed to get timesheets: {response.status_code} - {response.text}")
                return [], []
                
        except Exception as e:
            self.log_result("Get Pending Timesheets", False, f"Error getting timesheets: {str(e)}")
            return [], []

    def get_all_users(self):
        """Get all users from the system"""
        try:
            response = self.session.get(f"{BACKEND_URL}/users")
            
            if response.status_code == 200:
                users = response.json()
                user_details = []
                
                for user in users:
                    user_details.append({
                        "id": user.get("id"),
                        "username": user.get("username"),
                        "full_name": user.get("full_name"),
                        "email": user.get("email"),
                        "role": user.get("role"),
                        "department": user.get("department"),
                        "is_active": user.get("is_active")
                    })
                
                self.log_result("Get All Users", True, 
                              f"Found {len(users)} users", 
                              {"user_count": len(users)})
                
                print("📋 USER DETAILS:")
                for user in user_details:
                    print(f"   ID: {user['id']}")
                    print(f"   Username: {user['username']}")
                    print(f"   Full Name: {user['full_name']}")
                    print(f"   Email: {user['email']}")
                    print(f"   Role: {user['role']}")
                    print(f"   Department: {user['department']}")
                    print(f"   Active: {user['is_active']}")
                    print("   ---")
                print()
                
                return user_details
                
            else:
                self.log_result("Get All Users", False, 
                              f"Failed to get users: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            self.log_result("Get All Users", False, f"Error getting users: {str(e)}")
            return []

    def analyze_data_mismatch(self, employee_ids, timesheet_employee_ids, user_details, employee_details, timesheet_details):
        """Analyze the data mismatch between employees, timesheets, and users"""
        print("🔍 DATA MISMATCH ANALYSIS:")
        print("=" * 50)
        
        # Find orphaned timesheet employee IDs
        orphaned_timesheet_ids = [tid for tid in timesheet_employee_ids if tid not in employee_ids]
        matched_timesheet_ids = [tid for tid in timesheet_employee_ids if tid in employee_ids]
        
        print(f"📊 SUMMARY:")
        print(f"   Total Employees in System: {len(employee_ids)}")
        print(f"   Total Pending Timesheets: {len(timesheet_employee_ids)}")
        print(f"   Total Users: {len(user_details)}")
        print(f"   Matched Timesheet Employee IDs: {len(matched_timesheet_ids)}")
        print(f"   Orphaned Timesheet Employee IDs: {len(orphaned_timesheet_ids)}")
        print()
        
        if orphaned_timesheet_ids:
            print("❌ ORPHANED TIMESHEET EMPLOYEE IDs:")
            for orphaned_id in orphaned_timesheet_ids:
                print(f"   {orphaned_id}")
                # Find corresponding timesheet details
                for ts in timesheet_details:
                    if ts['employee_id'] == orphaned_id:
                        print(f"      Week: {ts['week_starting']} to {ts['week_ending']}")
                        print(f"      Hours: {ts['total_hours']}")
                        break
            print()
        
        if matched_timesheet_ids:
            print("✅ MATCHED TIMESHEET EMPLOYEE IDs:")
            for matched_id in matched_timesheet_ids:
                print(f"   {matched_id}")
                # Find employee name
                for emp in employee_details:
                    if emp['id'] == matched_id:
                        print(f"      Employee: {emp['first_name']} {emp['last_name']}")
                        break
            print()
        
        # Try to match orphaned timesheets to users by email or name
        print("🔗 POTENTIAL MATCHES FOR ORPHANED TIMESHEETS:")
        for orphaned_id in orphaned_timesheet_ids:
            print(f"   Orphaned ID: {orphaned_id}")
            
            # Check if this ID matches any user ID
            matching_users = [user for user in user_details if user['id'] == orphaned_id]
            if matching_users:
                user = matching_users[0]
                print(f"      ✅ DIRECT USER MATCH FOUND:")
                print(f"         User: {user['full_name']} ({user['email']})")
                print(f"         Role: {user['role']}")
                print(f"         Active: {user['is_active']}")
                
                # Check if there's an employee with matching email
                matching_employees = [emp for emp in employee_details if emp['email'] == user['email']]
                if matching_employees:
                    emp = matching_employees[0]
                    print(f"      🔗 SUGGESTED LINK TO EMPLOYEE:")
                    print(f"         Employee ID: {emp['id']}")
                    print(f"         Employee: {emp['first_name']} {emp['last_name']}")
                    print(f"         Employee Number: {emp['employee_number']}")
                else:
                    print(f"      ⚠️  No matching employee found for this user")
            else:
                print(f"      ❌ No direct user match found")
            print()
        
        # Suggestions for fixing the issue
        print("💡 SUGGESTIONS FOR FIXING ORPHANED TIMESHEETS:")
        print("=" * 50)
        
        if orphaned_timesheet_ids:
            print("1. UPDATE TIMESHEET EMPLOYEE_IDs:")
            for orphaned_id in orphaned_timesheet_ids:
                # Find user with this ID
                matching_users = [user for user in user_details if user['id'] == orphaned_id]
                if matching_users:
                    user = matching_users[0]
                    # Find employee with matching email
                    matching_employees = [emp for emp in employee_details if emp['email'] == user['email']]
                    if matching_employees:
                        emp = matching_employees[0]
                        print(f"   UPDATE timesheets SET employee_id = '{emp['id']}' WHERE employee_id = '{orphaned_id}';")
                        print(f"   -- This links {user['full_name']}'s timesheets to employee {emp['employee_number']}")
            print()
            
            print("2. ALTERNATIVE - CREATE MISSING EMPLOYEE PROFILES:")
            for orphaned_id in orphaned_timesheet_ids:
                matching_users = [user for user in user_details if user['id'] == orphaned_id]
                if matching_users:
                    user = matching_users[0]
                    if not any(emp['email'] == user['email'] for emp in employee_details):
                        print(f"   Create employee profile for: {user['full_name']} ({user['email']})")
                        print(f"   User ID: {user['id']}")
            print()
            
            print("3. SYNC EMPLOYEE PROFILES:")
            print("   Run the employee synchronization endpoint to ensure all active users have employee profiles:")
            print("   POST /api/payroll/employees/sync")
            print()

    def run_investigation(self):
        """Run the complete investigation"""
        print("🔍 PENDING TIMESHEETS DATA MISMATCH INVESTIGATION")
        print("=" * 60)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Admin User: {ADMIN_USERNAME}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print()
        
        # Step 1: Authenticate
        if not self.authenticate():
            return False
        
        # Step 2: Get current employees
        employee_ids, employee_details = self.get_current_employees()
        
        # Step 3: Get pending timesheets
        timesheet_employee_ids, timesheet_details = self.get_pending_timesheets()
        
        # Step 4: Get all users
        user_details = self.get_all_users()
        
        # Step 5: Analyze data mismatch
        self.analyze_data_mismatch(employee_ids, timesheet_employee_ids, user_details, employee_details, timesheet_details)
        
        # Summary
        success_count = sum(1 for result in self.test_results if result["success"])
        total_count = len(self.test_results)
        
        print("📊 INVESTIGATION SUMMARY:")
        print("=" * 30)
        print(f"Total Tests: {total_count}")
        print(f"Successful: {success_count}")
        print(f"Failed: {total_count - success_count}")
        print(f"Success Rate: {(success_count/total_count)*100:.1f}%")
        
        return success_count == total_count

def main():
    """Main function"""
    investigator = TimesheetsInvestigator()
    success = investigator.run_investigation()
    
    if success:
        print("\n✅ Investigation completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Investigation completed with some failures!")
        sys.exit(1)

if __name__ == "__main__":
    main()