#!/usr/bin/env python3
"""
Debug Employee ID Mismatch Issue
Check what employee_id is in the pending timesheet vs what employee profiles exist
"""

import requests
import json
import os

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://misty-ato-payroll.preview.emergentagent.com')
BASE_URL = f"{BACKEND_URL}/api"

# Test credentials
USERNAME = "Callum"
PASSWORD = "Peach7510"

class EmployeeMismatchDebugger:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        
    def authenticate(self):
        """Authenticate with admin credentials"""
        try:
            response = self.session.post(f"{BASE_URL}/auth/login", json={
                "username": USERNAME,
                "password": PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                print(f"✅ Authenticated as {data.get('user', {}).get('username')}")
                return True
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication exception: {str(e)}")
            return False
    
    def get_pending_timesheets(self):
        """Get pending timesheets"""
        try:
            response = self.session.get(f"{BASE_URL}/payroll/timesheets/pending")
            
            if response.status_code == 200:
                data = response.json()
                timesheets = data.get("data", [])
                print(f"✅ Found {len(timesheets)} pending timesheets")
                return timesheets
            else:
                print(f"❌ Failed to get pending timesheets: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Exception getting pending timesheets: {str(e)}")
            return []
    
    def get_employee_profiles(self):
        """Get employee profiles"""
        try:
            response = self.session.get(f"{BASE_URL}/payroll/employees")
            
            if response.status_code == 200:
                data = response.json()
                # Handle both direct list and data wrapper
                if isinstance(data, list):
                    employees = data
                else:
                    employees = data.get("data", [])
                print(f"✅ Found {len(employees)} employee profiles")
                return employees
            else:
                print(f"❌ Failed to get employee profiles: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Exception getting employee profiles: {str(e)}")
            return []
    
    def debug_mismatch(self):
        """Debug the employee ID mismatch"""
        print("🔍 DEBUGGING EMPLOYEE ID MISMATCH")
        print("=" * 60)
        
        if not self.authenticate():
            return
        
        # Get pending timesheets
        timesheets = self.get_pending_timesheets()
        if not timesheets:
            print("No pending timesheets to debug")
            return
        
        # Get employee profiles
        employees = self.get_employee_profiles()
        if not employees:
            print("No employee profiles found")
            return
        
        print("\n📋 PENDING TIMESHEETS:")
        for i, timesheet in enumerate(timesheets):
            print(f"  Timesheet {i+1}:")
            print(f"    ID: {timesheet.get('id')}")
            print(f"    Employee ID: {timesheet.get('employee_id')}")
            print(f"    Employee Name: {timesheet.get('employee_name')}")
            print(f"    Status: {timesheet.get('status')}")
        
        print("\n👥 EMPLOYEE PROFILES:")
        for i, employee in enumerate(employees):
            print(f"  Employee {i+1}:")
            print(f"    ID: {employee.get('id')}")
            print(f"    User ID: {employee.get('user_id')}")
            print(f"    Name: {employee.get('first_name')} {employee.get('last_name')}")
            print(f"    Employee Number: {employee.get('employee_number')}")
        
        print("\n🔍 MISMATCH ANALYSIS:")
        for timesheet in timesheets:
            timesheet_employee_id = timesheet.get('employee_id')
            print(f"\nTimesheet {timesheet.get('id')}:")
            print(f"  Looking for employee_id: {timesheet_employee_id}")
            
            # Check if this employee_id exists in employee profiles
            matching_employee = None
            for employee in employees:
                if employee.get('id') == timesheet_employee_id:
                    matching_employee = employee
                    break
            
            if matching_employee:
                print(f"  ✅ MATCH FOUND: {matching_employee.get('first_name')} {matching_employee.get('last_name')}")
            else:
                print(f"  ❌ NO MATCH FOUND in employee profiles")
                
                # Check if timesheet employee_id matches any user_id
                user_id_match = None
                for employee in employees:
                    if employee.get('user_id') == timesheet_employee_id:
                        user_id_match = employee
                        break
                
                if user_id_match:
                    print(f"  🔄 FOUND AS USER_ID: {user_id_match.get('first_name')} {user_id_match.get('last_name')}")
                    print(f"     Timesheet has user_id ({timesheet_employee_id}) instead of employee_id ({user_id_match.get('id')})")
                    print(f"     SOLUTION: Update timesheet employee_id from {timesheet_employee_id} to {user_id_match.get('id')}")
                else:
                    print(f"  ❌ NOT FOUND as user_id either")
        
        print("\n💡 RECOMMENDED ACTION:")
        print("If timesheet employee_id matches user_id instead of employee_id,")
        print("update the timesheet record to use the correct employee_id.")

if __name__ == "__main__":
    debugger = EmployeeMismatchDebugger()
    debugger.debug_mismatch()