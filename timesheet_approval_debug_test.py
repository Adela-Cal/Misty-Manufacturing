#!/usr/bin/env python3
"""
Timesheet Approval Debug Test
Debug the "Employee not found" error when approving timesheets as requested in review.

SPECIFIC TESTS:
1. Get pending timesheets - GET /api/payroll/timesheets/pending (with admin auth)
2. Check employee profiles - GET /api/payroll/employees to see what employee IDs exist
3. Try to approve a timesheet - POST /api/payroll/timesheets/{timesheet_id}/approve
4. If it fails, check what employee_id is in the timesheet and if it exists in employee_profiles collection
5. Check backend error logs for detailed error message

Admin credentials: Callum / Peach7510
"""

import requests
import json
import os
from datetime import datetime, timedelta, date
from dotenv import load_dotenv
import uuid

# Load environment variables
load_dotenv('/app/frontend/.env')

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:8001')
API_BASE = f"{BACKEND_URL}/api"

class TimesheetApprovalDebugger:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        
    def log_result(self, test_name, success, message, details=None):
        """Log test result"""
        result = {
            'test': test_name,
            'success': success,
            'message': message,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name} - {message}")
        if details and not success:
            print(f"   Details: {details}")
    
    def authenticate(self):
        """Test authentication with admin credentials"""
        print("\n=== AUTHENTICATION TEST ===")
        
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
                self.log_result(
                    "Authentication", 
                    True, 
                    f"Successfully authenticated as {user_info.get('username')} with role {user_info.get('role')}"
                )
                return True
            else:
                self.log_result(
                    "Authentication", 
                    False, 
                    f"Authentication failed with status {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_result("Authentication", False, f"Authentication error: {str(e)}")
            return False

    def debug_timesheet_approval_issue(self):
        """
        Main debug function for timesheet approval issue
        """
        print("\n" + "="*80)
        print("TIMESHEET APPROVAL DEBUG - EMPLOYEE NOT FOUND ERROR")
        print("="*80)
        
        # Step 1: Get pending timesheets
        pending_timesheets = self.get_pending_timesheets()
        
        # Step 2: Get employee profiles
        employee_profiles = self.get_employee_profiles()
        
        # Step 3: Analyze the data mismatch
        self.analyze_employee_data_mismatch(pending_timesheets, employee_profiles)
        
        # Step 4: Try to approve a timesheet and capture the error
        if pending_timesheets:
            self.test_timesheet_approval(pending_timesheets[0], employee_profiles)
        
        # Step 5: Check backend logs
        self.check_backend_logs()
        
        # Step 6: Provide detailed diagnosis
        self.provide_diagnosis(pending_timesheets, employee_profiles)

    def get_pending_timesheets(self):
        """Step 1: Get pending timesheets"""
        print("\n--- STEP 1: GET PENDING TIMESHEETS ---")
        
        try:
            response = self.session.get(f"{API_BASE}/payroll/timesheets/pending")
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("success") and "data" in result:
                    timesheets = result["data"]
                    
                    self.log_result(
                        "Get Pending Timesheets", 
                        True, 
                        f"Successfully retrieved {len(timesheets)} pending timesheets"
                    )
                    
                    # Print detailed timesheet information
                    for i, timesheet in enumerate(timesheets):
                        print(f"\nTimesheet {i+1}:")
                        print(f"  ID: {timesheet.get('id')}")
                        print(f"  Employee ID: {timesheet.get('employee_id')}")
                        print(f"  Employee Name: {timesheet.get('employee_name', 'NOT SET')}")
                        print(f"  Status: {timesheet.get('status')}")
                        print(f"  Week: {timesheet.get('week_start')} to {timesheet.get('week_end')}")
                        print(f"  Total Hours: {timesheet.get('total_regular_hours', 0)} regular + {timesheet.get('total_overtime_hours', 0)} overtime")
                    
                    return timesheets
                else:
                    self.log_result(
                        "Get Pending Timesheets", 
                        False, 
                        "Invalid response structure",
                        f"Response: {result}"
                    )
            else:
                self.log_result(
                    "Get Pending Timesheets", 
                    False, 
                    f"Failed to get pending timesheets: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Get Pending Timesheets", False, f"Error: {str(e)}")
        
        return []

    def get_employee_profiles(self):
        """Step 2: Get employee profiles"""
        print("\n--- STEP 2: GET EMPLOYEE PROFILES ---")
        
        try:
            response = self.session.get(f"{API_BASE}/payroll/employees")
            
            if response.status_code == 200:
                result = response.json()
                
                # Handle both direct array and StandardResponse format
                if isinstance(result, list):
                    employees = result
                elif isinstance(result, dict) and "data" in result:
                    employees = result["data"]
                else:
                    employees = result
                
                self.log_result(
                    "Get Employee Profiles", 
                    True, 
                    f"Successfully retrieved {len(employees)} employee profiles"
                )
                
                # Print detailed employee information
                for i, employee in enumerate(employees):
                    print(f"\nEmployee {i+1}:")
                    print(f"  ID: {employee.get('id')}")
                    print(f"  User ID: {employee.get('user_id')}")
                    print(f"  Employee Number: {employee.get('employee_number')}")
                    print(f"  Name: {employee.get('first_name')} {employee.get('last_name')}")
                    print(f"  Email: {employee.get('email')}")
                    print(f"  Department: {employee.get('department')}")
                    print(f"  Position: {employee.get('position')}")
                
                return employees
            else:
                self.log_result(
                    "Get Employee Profiles", 
                    False, 
                    f"Failed to get employee profiles: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Get Employee Profiles", False, f"Error: {str(e)}")
        
        return []

    def analyze_employee_data_mismatch(self, timesheets, employees):
        """Step 3: Analyze data mismatch between timesheets and employees"""
        print("\n--- STEP 3: ANALYZE EMPLOYEE DATA MISMATCH ---")
        
        if not timesheets or not employees:
            self.log_result(
                "Data Mismatch Analysis", 
                False, 
                "Cannot analyze - missing timesheets or employee data"
            )
            return
        
        # Extract employee IDs from timesheets
        timesheet_employee_ids = set()
        for timesheet in timesheets:
            emp_id = timesheet.get('employee_id')
            if emp_id:
                timesheet_employee_ids.add(emp_id)
        
        # Extract employee IDs from employee profiles
        profile_employee_ids = set()
        profile_user_ids = set()
        for employee in employees:
            emp_id = employee.get('id')
            user_id = employee.get('user_id')
            if emp_id:
                profile_employee_ids.add(emp_id)
            if user_id:
                profile_user_ids.add(user_id)
        
        print(f"\nTimesheet Employee IDs: {timesheet_employee_ids}")
        print(f"Profile Employee IDs: {profile_employee_ids}")
        print(f"Profile User IDs: {profile_user_ids}")
        
        # Check for mismatches
        missing_in_profiles = timesheet_employee_ids - profile_employee_ids
        missing_in_timesheets = profile_employee_ids - timesheet_employee_ids
        
        # Check if timesheet employee_ids match user_ids instead of employee_ids
        timesheet_ids_matching_user_ids = timesheet_employee_ids & profile_user_ids
        
        if missing_in_profiles:
            self.log_result(
                "Employee ID Mismatch - Missing in Profiles", 
                False, 
                f"Timesheet employee IDs not found in employee profiles: {missing_in_profiles}"
            )
        
        if timesheet_ids_matching_user_ids:
            self.log_result(
                "Employee ID Mismatch - Using User IDs", 
                False, 
                f"Timesheets are using USER IDs instead of EMPLOYEE IDs: {timesheet_ids_matching_user_ids}",
                "This is likely the root cause of the 'Employee not found' error"
            )
        
        if not missing_in_profiles and not timesheet_ids_matching_user_ids:
            self.log_result(
                "Employee ID Matching", 
                True, 
                "All timesheet employee IDs match employee profile IDs"
            )

    def test_timesheet_approval(self, timesheet, employees):
        """Step 4: Try to approve a timesheet and capture the error"""
        print("\n--- STEP 4: TEST TIMESHEET APPROVAL ---")
        
        timesheet_id = timesheet.get('id')
        employee_id = timesheet.get('employee_id')
        
        print(f"Attempting to approve timesheet: {timesheet_id}")
        print(f"Timesheet employee_id: {employee_id}")
        
        try:
            response = self.session.post(f"{API_BASE}/payroll/timesheets/{timesheet_id}/approve")
            
            if response.status_code == 200:
                result = response.json()
                self.log_result(
                    "Timesheet Approval", 
                    True, 
                    f"Successfully approved timesheet {timesheet_id}"
                )
            else:
                error_text = response.text
                self.log_result(
                    "Timesheet Approval", 
                    False, 
                    f"Failed to approve timesheet: {response.status_code}",
                    error_text
                )
                
                # Try to parse error details
                try:
                    error_data = response.json()
                    if "detail" in error_data:
                        print(f"Error detail: {error_data['detail']}")
                except:
                    pass
                
        except Exception as e:
            self.log_result("Timesheet Approval", False, f"Error: {str(e)}")

    def check_backend_logs(self):
        """Step 5: Check backend logs for errors"""
        print("\n--- STEP 5: CHECK BACKEND LOGS ---")
        
        try:
            import subprocess
            
            # Check supervisor backend logs
            result = subprocess.run(
                ["tail", "-n", "50", "/var/log/supervisor/backend.err.log"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                log_content = result.stdout
                if log_content.strip():
                    self.log_result(
                        "Backend Error Logs", 
                        True, 
                        "Retrieved backend error logs"
                    )
                    print("\nRecent Backend Error Log Entries:")
                    print("-" * 50)
                    print(log_content)
                    print("-" * 50)
                else:
                    self.log_result(
                        "Backend Error Logs", 
                        True, 
                        "No recent errors in backend logs"
                    )
            else:
                self.log_result(
                    "Backend Error Logs", 
                    False, 
                    "Could not read backend error logs"
                )
                
        except Exception as e:
            self.log_result("Backend Error Logs", False, f"Error reading logs: {str(e)}")

    def provide_diagnosis(self, timesheets, employees):
        """Step 6: Provide detailed diagnosis"""
        print("\n--- STEP 6: DETAILED DIAGNOSIS ---")
        
        print("\n" + "="*60)
        print("DIAGNOSIS SUMMARY")
        print("="*60)
        
        if not timesheets:
            print("❌ No pending timesheets found")
            return
        
        if not employees:
            print("❌ No employee profiles found")
            return
        
        # Check for the specific issue
        timesheet_employee_ids = {ts.get('employee_id') for ts in timesheets if ts.get('employee_id')}
        profile_employee_ids = {emp.get('id') for emp in employees if emp.get('id')}
        profile_user_ids = {emp.get('user_id') for emp in employees if emp.get('user_id')}
        
        print(f"📊 Found {len(timesheets)} pending timesheets")
        print(f"📊 Found {len(employees)} employee profiles")
        
        # Check if timesheets are using user_id instead of employee_id
        using_user_ids = timesheet_employee_ids & profile_user_ids
        missing_employee_ids = timesheet_employee_ids - profile_employee_ids
        
        if using_user_ids:
            print(f"\n🔍 ROOT CAUSE IDENTIFIED:")
            print(f"   Timesheets are using USER_ID instead of EMPLOYEE_ID")
            print(f"   Affected IDs: {using_user_ids}")
            
            # Find the mapping
            for timesheet in timesheets:
                ts_emp_id = timesheet.get('employee_id')
                if ts_emp_id in using_user_ids:
                    # Find the corresponding employee
                    matching_employee = next((emp for emp in employees if emp.get('user_id') == ts_emp_id), None)
                    if matching_employee:
                        print(f"\n   📋 Timesheet ID: {timesheet.get('id')}")
                        print(f"      Using USER_ID: {ts_emp_id}")
                        print(f"      Should use EMPLOYEE_ID: {matching_employee.get('id')}")
                        print(f"      Employee: {matching_employee.get('first_name')} {matching_employee.get('last_name')}")
            
            print(f"\n💡 SOLUTION:")
            print(f"   Update timesheets to use correct employee_id:")
            for timesheet in timesheets:
                ts_emp_id = timesheet.get('employee_id')
                if ts_emp_id in using_user_ids:
                    matching_employee = next((emp for emp in employees if emp.get('user_id') == ts_emp_id), None)
                    if matching_employee:
                        print(f"   UPDATE timesheets SET employee_id = '{matching_employee.get('id')}' WHERE employee_id = '{ts_emp_id}'")
        
        elif missing_employee_ids:
            print(f"\n🔍 ISSUE IDENTIFIED:")
            print(f"   Employee IDs in timesheets not found in employee profiles")
            print(f"   Missing IDs: {missing_employee_ids}")
            
            print(f"\n💡 SOLUTION:")
            print(f"   Run employee synchronization: POST /api/payroll/employees/sync")
        
        else:
            print(f"\n✅ No obvious employee ID mismatch found")
            print(f"   The issue may be in the approval endpoint logic")

    def run_debug(self):
        """Run the complete debug process"""
        print("🔍 TIMESHEET APPROVAL DEBUG STARTED")
        print("Investigating 'Employee not found' error when approving timesheets")
        
        # Authenticate first
        if not self.authenticate():
            print("❌ Authentication failed - cannot proceed with debug")
            return
        
        # Run the debug process
        self.debug_timesheet_approval_issue()
        
        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*80)
        print("DEBUG SUMMARY")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        
        # Show failed tests
        failed_results = [r for r in self.test_results if not r['success']]
        if failed_results:
            print("\n❌ FAILED TESTS:")
            for result in failed_results:
                print(f"   • {result['test']}: {result['message']}")
                if result['details']:
                    print(f"     Details: {result['details']}")
        
        print("\n" + "="*80)

if __name__ == "__main__":
    debugger = TimesheetApprovalDebugger()
    debugger.run_debug()