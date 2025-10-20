#!/usr/bin/env python3
"""
Timesheet Flow Testing Suite
Testing the fixed timesheet flow to verify permission checks are working.

TEST FLOW:
1. Authenticate as Callum / Peach7510
2. Get employee ID for Callum from /api/payroll/employees
3. GET /api/payroll/timesheets/current-week/{employee_id} - Test if timesheet can be retrieved/created without permission errors
4. PUT /api/payroll/timesheets/{timesheet_id} - Test if timesheet can be updated without permission errors
5. POST /api/payroll/timesheets/{timesheet_id}/submit - Test if timesheet can be submitted
6. GET /api/payroll/timesheets/pending - Verify submitted timesheet appears in pending list

Expected result: All operations should succeed without 403 permission errors.
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

class TimesheetFlowTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        self.employee_id = None
        self.timesheet_id = None
        
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
        """Step 1: Authenticate as Callum / Peach7510"""
        print("\n=== STEP 1: AUTHENTICATION ===")
        
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

    def get_employee_id(self):
        """Step 2: Get employee ID for Callum from /api/payroll/employees"""
        print("\n=== STEP 2: GET EMPLOYEE ID ===")
        
        try:
            response = self.session.get(f"{API_BASE}/payroll/employees")
            
            if response.status_code == 200:
                employees = response.json()
                
                # Look for Callum in the employees list
                callum_employee = None
                for emp in employees:
                    if emp.get('first_name', '').lower() == 'callum' or emp.get('username', '').lower() == 'callum':
                        callum_employee = emp
                        break
                
                if callum_employee:
                    self.employee_id = callum_employee['id']
                    self.log_result(
                        "Get Employee ID", 
                        True, 
                        f"Found Callum's employee ID: {self.employee_id}",
                        f"Employee: {callum_employee.get('first_name')} {callum_employee.get('last_name')} ({callum_employee.get('employee_number')})"
                    )
                    return True
                else:
                    self.log_result(
                        "Get Employee ID", 
                        False, 
                        "Could not find Callum in employees list",
                        f"Available employees: {[f\"{emp.get('first_name')} {emp.get('last_name')}\" for emp in employees]}"
                    )
                    return False
            else:
                self.log_result(
                    "Get Employee ID", 
                    False, 
                    f"Failed to get employees: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_result("Get Employee ID", False, f"Error: {str(e)}")
            return False

    def test_get_current_week_timesheet(self):
        """Step 3: GET /api/payroll/timesheets/current-week/{employee_id}"""
        print("\n=== STEP 3: GET CURRENT WEEK TIMESHEET ===")
        
        try:
            response = self.session.get(f"{API_BASE}/payroll/timesheets/current-week/{self.employee_id}")
            
            if response.status_code == 200:
                data = response.json()
                timesheet_data = data.get('data', {})
                
                if timesheet_data and timesheet_data.get('id'):
                    self.timesheet_id = timesheet_data['id']
                    self.log_result(
                        "Get Current Week Timesheet", 
                        True, 
                        f"Successfully retrieved/created current week timesheet",
                        f"Timesheet ID: {self.timesheet_id}, Status: {timesheet_data.get('status')}"
                    )
                    return True
                else:
                    self.log_result(
                        "Get Current Week Timesheet", 
                        False, 
                        "No timesheet data returned",
                        f"Response: {data}"
                    )
                    return False
            elif response.status_code == 403:
                self.log_result(
                    "Get Current Week Timesheet", 
                    False, 
                    "Permission denied (403) - This is the bug we're testing for!",
                    response.text
                )
                return False
            else:
                self.log_result(
                    "Get Current Week Timesheet", 
                    False, 
                    f"Failed to get current week timesheet: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_result("Get Current Week Timesheet", False, f"Error: {str(e)}")
            return False

    def test_update_timesheet(self):
        """Step 4: PUT /api/payroll/timesheets/{timesheet_id}"""
        print("\n=== STEP 4: UPDATE TIMESHEET ===")
        
        if not self.timesheet_id:
            self.log_result(
                "Update Timesheet", 
                False, 
                "No timesheet ID available for update test"
            )
            return False
        
        try:
            # Sample timesheet update data
            update_data = {
                "daily_entries": [
                    {
                        "date": "2024-12-16",
                        "regular_hours": 8.0,
                        "overtime_hours": 0.0,
                        "notes": "Regular work day - testing update"
                    },
                    {
                        "date": "2024-12-17",
                        "regular_hours": 8.0,
                        "overtime_hours": 1.0,
                        "notes": "Overtime for urgent project"
                    },
                    {
                        "date": "2024-12-18",
                        "regular_hours": 7.5,
                        "overtime_hours": 0.5,
                        "notes": "Half day overtime"
                    }
                ],
                "total_regular_hours": 23.5,
                "total_overtime_hours": 1.5
            }
            
            response = self.session.put(f"{API_BASE}/payroll/timesheets/{self.timesheet_id}", json=update_data)
            
            if response.status_code == 200:
                data = response.json()
                self.log_result(
                    "Update Timesheet", 
                    True, 
                    "Successfully updated timesheet with sample entry data",
                    f"Updated entries: 3 days, Total regular: 23.5h, Total overtime: 1.5h"
                )
                return True
            elif response.status_code == 403:
                self.log_result(
                    "Update Timesheet", 
                    False, 
                    "Permission denied (403) - This is the bug we're testing for!",
                    response.text
                )
                return False
            else:
                self.log_result(
                    "Update Timesheet", 
                    False, 
                    f"Failed to update timesheet: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_result("Update Timesheet", False, f"Error: {str(e)}")
            return False

    def test_submit_timesheet(self):
        """Step 5: POST /api/payroll/timesheets/{timesheet_id}/submit"""
        print("\n=== STEP 5: SUBMIT TIMESHEET ===")
        
        if not self.timesheet_id:
            self.log_result(
                "Submit Timesheet", 
                False, 
                "No timesheet ID available for submit test"
            )
            return False
        
        try:
            response = self.session.post(f"{API_BASE}/payroll/timesheets/{self.timesheet_id}/submit")
            
            if response.status_code == 200:
                data = response.json()
                self.log_result(
                    "Submit Timesheet", 
                    True, 
                    "Successfully submitted timesheet",
                    f"Response: {data.get('message', 'Timesheet submitted')}"
                )
                return True
            elif response.status_code == 403:
                self.log_result(
                    "Submit Timesheet", 
                    False, 
                    "Permission denied (403) - This is the bug we're testing for!",
                    response.text
                )
                return False
            else:
                self.log_result(
                    "Submit Timesheet", 
                    False, 
                    f"Failed to submit timesheet: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_result("Submit Timesheet", False, f"Error: {str(e)}")
            return False

    def test_verify_pending_timesheet(self):
        """Step 6: GET /api/payroll/timesheets/pending - Verify submitted timesheet appears"""
        print("\n=== STEP 6: VERIFY SUBMITTED TIMESHEET IN PENDING LIST ===")
        
        try:
            response = self.session.get(f"{API_BASE}/payroll/timesheets/pending")
            
            if response.status_code == 200:
                data = response.json()
                pending_timesheets = data.get('data', [])
                
                # Look for our submitted timesheet
                our_timesheet = None
                for ts in pending_timesheets:
                    if ts.get('id') == self.timesheet_id:
                        our_timesheet = ts
                        break
                
                if our_timesheet:
                    self.log_result(
                        "Verify Pending Timesheet", 
                        True, 
                        f"Successfully found submitted timesheet in pending list",
                        f"Timesheet ID: {our_timesheet.get('id')}, Status: {our_timesheet.get('status')}, Employee: {our_timesheet.get('employee_name')}"
                    )
                    return True
                else:
                    self.log_result(
                        "Verify Pending Timesheet", 
                        False, 
                        f"Submitted timesheet not found in pending list",
                        f"Found {len(pending_timesheets)} pending timesheets, but our timesheet ID {self.timesheet_id} not among them"
                    )
                    return False
            elif response.status_code == 403:
                self.log_result(
                    "Verify Pending Timesheet", 
                    False, 
                    "Permission denied (403) accessing pending timesheets",
                    response.text
                )
                return False
            else:
                self.log_result(
                    "Verify Pending Timesheet", 
                    False, 
                    f"Failed to get pending timesheets: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_result("Verify Pending Timesheet", False, f"Error: {str(e)}")
            return False

    def run_complete_timesheet_flow_test(self):
        """Run the complete timesheet flow test"""
        print("="*80)
        print("TIMESHEET FLOW PERMISSION TESTING")
        print("Testing fixed timesheet flow to verify permission checks are working")
        print("="*80)
        
        # Step 1: Authenticate
        if not self.authenticate():
            print("\n❌ CRITICAL: Authentication failed - cannot proceed with tests")
            return False
        
        # Step 2: Get employee ID
        if not self.get_employee_id():
            print("\n❌ CRITICAL: Could not get employee ID - cannot proceed with tests")
            return False
        
        # Step 3: Get/create current week timesheet
        if not self.test_get_current_week_timesheet():
            print("\n❌ CRITICAL: Could not get current week timesheet - this may be the permission bug")
            # Continue with other tests to see full scope of issue
        
        # Step 4: Update timesheet (if we have one)
        if self.timesheet_id:
            self.test_update_timesheet()
        else:
            self.log_result(
                "Update Timesheet", 
                False, 
                "Skipped - no timesheet ID available"
            )
        
        # Step 5: Submit timesheet (if we have one)
        if self.timesheet_id:
            self.test_submit_timesheet()
        else:
            self.log_result(
                "Submit Timesheet", 
                False, 
                "Skipped - no timesheet ID available"
            )
        
        # Step 6: Verify in pending list
        self.test_verify_pending_timesheet()
        
        return True

    def print_test_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "="*80)
        print("TIMESHEET FLOW TEST SUMMARY")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        print("\n" + "="*60)
        print("DETAILED RESULTS:")
        print("="*60)
        
        for result in self.test_results:
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"{status} {result['test']}")
            print(f"    {result['message']}")
            if result['details'] and not result['success']:
                print(f"    Details: {result['details']}")
        
        # Show failed tests details
        failed_results = [r for r in self.test_results if not r['success']]
        if failed_results:
            print("\n" + "="*60)
            print("FAILED TESTS ANALYSIS:")
            print("="*60)
            
            permission_errors = [r for r in failed_results if '403' in r['message']]
            if permission_errors:
                print(f"\n🚨 PERMISSION ERRORS FOUND: {len(permission_errors)} tests failed with 403 errors")
                for result in permission_errors:
                    print(f"   ❌ {result['test']}: {result['message']}")
                print("\n   This indicates the permission bug is still present!")
            
            other_errors = [r for r in failed_results if '403' not in r['message']]
            if other_errors:
                print(f"\n⚠️  OTHER ERRORS: {len(other_errors)} tests failed with non-permission issues")
                for result in other_errors:
                    print(f"   ❌ {result['test']}: {result['message']}")
        
        print("\n" + "="*80)
        if success_rate == 100:
            print("🎉 PERFECT! All timesheet operations working without permission errors!")
        elif any('403' in r['message'] for r in failed_results):
            print("🚨 PERMISSION BUG DETECTED! Some operations still failing with 403 errors.")
        else:
            print(f"⚠️  {success_rate:.1f}% SUCCESS - Some non-permission issues found.")
        print("="*80)

def main():
    """Main test execution"""
    tester = TimesheetFlowTester()
    
    try:
        tester.run_complete_timesheet_flow_test()
        tester.print_test_summary()
        
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\nUnexpected error during testing: {str(e)}")
        tester.print_test_summary()

if __name__ == "__main__":
    main()