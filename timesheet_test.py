#!/usr/bin/env python3
"""
Timesheet Creation and Submission Flow Testing
Testing the specific timesheet workflow as requested in the review:

1. GET /api/payroll/timesheets/current-week/{employee_id} - Test getting/creating current week timesheet
2. PUT /api/payroll/timesheets/{timesheet_id} - Test updating timesheet
3. POST /api/payroll/timesheets/{timesheet_id}/submit - Test submitting timesheet
4. GET /api/payroll/timesheets/pending - Check if submitted timesheet appears

Expected issues to identify:
- Permission check failure (user_id vs employee_id mismatch)
- Timesheet not appearing in pending after submission
- Any other errors in the flow

Using credentials: Callum / Peach7510
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
        self.current_user_id = None
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
        """Test authentication with Callum / Peach7510"""
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
                self.current_user_id = user_info.get('id')
                
                self.log_result(
                    "Authentication", 
                    True, 
                    f"Successfully authenticated as {user_info.get('username')} with role {user_info.get('role')}",
                    f"User ID: {self.current_user_id}"
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

    def get_employee_id_for_callum(self):
        """Get the employee_id for Callum from /api/payroll/employees"""
        print("\n=== GETTING EMPLOYEE ID FOR CALLUM ===")
        
        try:
            response = self.session.get(f"{API_BASE}/payroll/employees")
            
            if response.status_code == 200:
                employees = response.json()
                
                # Look for Callum in the employees list
                callum_employee = None
                for emp in employees:
                    if 'callum' in emp.get('first_name', '').lower() or 'callum' in emp.get('full_name', '').lower():
                        callum_employee = emp
                        break
                
                if callum_employee:
                    self.employee_id = callum_employee['id']
                    self.log_result(
                        "Get Employee ID for Callum", 
                        True, 
                        f"Found Callum's employee ID: {self.employee_id}",
                        f"Employee: {callum_employee.get('first_name')} {callum_employee.get('last_name')}, Number: {callum_employee.get('employee_number')}"
                    )
                    return True
                else:
                    self.log_result(
                        "Get Employee ID for Callum", 
                        False, 
                        "Could not find Callum in employees list",
                        f"Available employees: {[emp.get('first_name') + ' ' + emp.get('last_name') for emp in employees]}"
                    )
                    return False
            else:
                self.log_result(
                    "Get Employee ID for Callum", 
                    False, 
                    f"Failed to get employees: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_result("Get Employee ID for Callum", False, f"Error: {str(e)}")
            return False
    
    def test_payroll_endpoints_access(self):
        """Test if payroll endpoints are accessible"""
        print("\n=== PAYROLL ENDPOINTS ACCESS TEST ===")
        
        try:
            response = self.session.get(f"{API_BASE}/payroll/employees")
            
            if response.status_code == 200:
                employees = response.json()
                self.log_result(
                    "Payroll Endpoints Access", 
                    True, 
                    f"Successfully accessed payroll endpoints - found {len(employees)} employees"
                )
                
                # Use first employee for testing if available
                if employees:
                    first_employee = employees[0]
                    employee_id = first_employee.get('id')
                    self.test_employee_id = employee_id
                    
                    self.log_result(
                        "Employee ID Available", 
                        True, 
                        f"Using existing employee ID: {employee_id}",
                        f"Employee: {first_employee.get('first_name')} {first_employee.get('last_name')}"
                    )
                    
                    return employee_id
                else:
                    self.log_result(
                        "Employee ID Available", 
                        False, 
                        "No employees found in system - need to create test employee"
                    )
            else:
                self.log_result(
                    "Payroll Endpoints Access", 
                    False, 
                    f"Failed to access payroll endpoints: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Payroll Endpoints Access", False, f"Error: {str(e)}")
        
        return None
    
    def test_undefined_employee_id_issue(self):
        """Test the specific issue where employee_id comes as undefined"""
        print("\n=== UNDEFINED EMPLOYEE_ID ISSUE TEST ===")
        
        # Test with undefined/null employee_id
        test_cases = [
            ("undefined", "undefined"),
            ("null", "null"),
            ("", "empty string"),
            (None, "None/null")
        ]
        
        for employee_id, description in test_cases:
            try:
                if employee_id is None:
                    url = f"{API_BASE}/payroll/timesheets/current-week/None"
                else:
                    url = f"{API_BASE}/payroll/timesheets/current-week/{employee_id}"
                
                response = self.session.get(url)
                
                if response.status_code == 500:
                    self.log_result(
                        f"Undefined Employee ID - {description}", 
                        False, 
                        f"500 Internal Server Error with {description} employee_id - THIS IS THE REPORTED ISSUE!",
                        f"URL: {url}, Response: {response.text[:200]}"
                    )
                elif response.status_code == 404:
                    self.log_result(
                        f"Undefined Employee ID - {description}", 
                        True, 
                        f"Properly returns 404 for {description} employee_id (expected behavior)"
                    )
                elif response.status_code == 422:
                    self.log_result(
                        f"Undefined Employee ID - {description}", 
                        True, 
                        f"Properly returns 422 validation error for {description} employee_id"
                    )
                else:
                    self.log_result(
                        f"Undefined Employee ID - {description}", 
                        False, 
                        f"Unexpected status {response.status_code} for {description} employee_id",
                        response.text[:200]
                    )
                    
            except Exception as e:
                self.log_result(f"Undefined Employee ID - {description}", False, f"Error: {str(e)}")
    
    def test_manager_loading_functionality(self):
        """Test manager loading for timesheet approval"""
        print("\n=== MANAGER LOADING FUNCTIONALITY TEST ===")
        
        try:
            # Test GET /api/users to verify manager loading
            response = self.session.get(f"{API_BASE}/users")
            
            if response.status_code == 200:
                users = response.json()
                managers = [user for user in users if user.get('role') in ['admin', 'manager', 'production_manager']]
                
                if managers:
                    self.log_result(
                        "Manager Loading - Users Endpoint", 
                        True, 
                        f"Successfully loaded {len(managers)} managers from {len(users)} total users",
                        f"Manager roles found: {[m.get('role') for m in managers]}"
                    )
                    
                    # Test specific manager details
                    for manager in managers[:2]:  # Test first 2 managers
                        manager_id = manager.get('id')
                        manager_response = self.session.get(f"{API_BASE}/users/{manager_id}")
                        
                        if manager_response.status_code == 200:
                            manager_details = manager_response.json()
                            self.log_result(
                                f"Manager Details - {manager.get('full_name')}", 
                                True, 
                                f"Successfully retrieved manager details",
                                f"Role: {manager_details.get('role')}, Email: {manager_details.get('email')}"
                            )
                        else:
                            self.log_result(
                                f"Manager Details - {manager.get('full_name')}", 
                                False, 
                                f"Failed to retrieve manager details: {manager_response.status_code}"
                            )
                else:
                    self.log_result(
                        "Manager Loading - Users Endpoint", 
                        False, 
                        f"No managers found in {len(users)} users",
                        "Manager loading will fail - no managers available for timesheet approval"
                    )
            else:
                self.log_result(
                    "Manager Loading - Users Endpoint", 
                    False, 
                    f"Failed to load users: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Manager Loading Functionality", False, f"Error: {str(e)}")
    
    def test_timesheet_endpoints_with_valid_employee(self):
        """Test all timesheet endpoints with a valid employee ID"""
        print("\n=== TIMESHEET ENDPOINTS WITH VALID EMPLOYEE TEST ===")
        
        employee_id = self.test_employee_id
        
        if not employee_id:
            self.log_result(
                "Valid Employee ID Required", 
                False, 
                "No valid employee ID available for testing timesheet endpoints"
            )
            return
        
        # Test 1: GET current week timesheet
        try:
            response = self.session.get(f"{API_BASE}/payroll/timesheets/current-week/{employee_id}")
            
            if response.status_code == 200:
                timesheet = response.json()
                timesheet_id = timesheet.get('id')
                
                self.log_result(
                    "GET Current Week Timesheet", 
                    True, 
                    f"Successfully retrieved/created timesheet",
                    f"ID: {timesheet_id}, Status: {timesheet.get('status')}, Week: {timesheet.get('week_starting')}"
                )
                
                # Test 2: PUT update timesheet
                if timesheet_id:
                    self.test_update_timesheet_with_valid_data(timesheet_id, employee_id)
                    
                    # Test 3: POST submit timesheet
                    self.test_submit_timesheet_endpoint(timesheet_id)
                    
                    # Test 4: POST approve timesheet
                    self.test_approve_timesheet_endpoint(timesheet_id)
                    
            elif response.status_code == 500:
                self.log_result(
                    "GET Current Week Timesheet", 
                    False, 
                    "500 Internal Server Error - this is the reported issue!",
                    f"Employee ID: {employee_id}, Response: {response.text[:500]}"
                )
            else:
                self.log_result(
                    "GET Current Week Timesheet", 
                    False, 
                    f"Unexpected status: {response.status_code}",
                    response.text[:200]
                )
                
        except Exception as e:
            self.log_result("GET Current Week Timesheet", False, f"Error: {str(e)}")
    
    def test_update_timesheet_with_valid_data(self, timesheet_id, employee_id):
        """Test PUT /api/payroll/timesheets/{timesheet_id} with valid data"""
        try:
            from datetime import date, timedelta
            
            # Create realistic timesheet data
            today = date.today()
            week_start = today - timedelta(days=today.weekday())  # Monday
            
            entries = []
            for i in range(5):  # Monday to Friday
                entry_date = week_start + timedelta(days=i)
                entries.append({
                    "date": entry_date.isoformat(),
                    "regular_hours": 8.0,
                    "overtime_hours": 0.0,
                    "leave_hours": {},
                    "notes": f"Regular work day {i+1}"
                })
            
            timesheet_data = {
                "employee_id": employee_id,
                "week_starting": week_start.isoformat(),
                "entries": entries
            }
            
            response = self.session.put(f"{API_BASE}/payroll/timesheets/{timesheet_id}", json=timesheet_data)
            
            if response.status_code == 200:
                self.log_result(
                    "PUT Update Timesheet", 
                    True, 
                    "Successfully updated timesheet with 40 hours of work"
                )
            else:
                self.log_result(
                    "PUT Update Timesheet", 
                    False, 
                    f"Failed to update timesheet: {response.status_code}",
                    response.text[:200]
                )
                
        except Exception as e:
            self.log_result("PUT Update Timesheet", False, f"Error: {str(e)}")
    
    def test_submit_timesheet_endpoint(self, timesheet_id):
        """Test POST /api/payroll/timesheets/{timesheet_id}/submit"""
        try:
            response = self.session.post(f"{API_BASE}/payroll/timesheets/{timesheet_id}/submit")
            
            if response.status_code == 200:
                result = response.json()
                self.log_result(
                    "POST Submit Timesheet", 
                    True, 
                    "Successfully submitted timesheet for approval",
                    result.get('message', '')
                )
            else:
                self.log_result(
                    "POST Submit Timesheet", 
                    False, 
                    f"Failed to submit timesheet: {response.status_code}",
                    response.text[:200]
                )
                
        except Exception as e:
            self.log_result("POST Submit Timesheet", False, f"Error: {str(e)}")
    
    def test_approve_timesheet_endpoint(self, timesheet_id):
        """Test POST /api/payroll/timesheets/{timesheet_id}/approve"""
        try:
            response = self.session.post(f"{API_BASE}/payroll/timesheets/{timesheet_id}/approve")
            
            if response.status_code == 200:
                result = response.json()
                data = result.get('data', {})
                self.log_result(
                    "POST Approve Timesheet", 
                    True, 
                    "Successfully approved timesheet and calculated pay",
                    f"Gross Pay: ${data.get('gross_pay', 0)}, Hours: {data.get('hours_worked', 0)}"
                )
            else:
                self.log_result(
                    "POST Approve Timesheet", 
                    False, 
                    f"Failed to approve timesheet: {response.status_code}",
                    response.text[:200]
                )
                
        except Exception as e:
            self.log_result("POST Approve Timesheet", False, f"Error: {str(e)}")
    
    def run_timesheet_debug_tests(self):
        """Run comprehensive timesheet API debugging tests"""
        print("\n" + "="*60)
        print("TIMESHEET API DEBUG TESTING")
        print("="*60)
        print(f"Backend URL: {BACKEND_URL}")
        
        # Step 1: Authenticate
        if not self.authenticate():
            print("❌ Authentication failed - cannot proceed with tests")
            return
        
        # Step 2: Test payroll authentication and access
        self.test_payroll_endpoints_access()
        
        # Step 3: Test undefined employee_id issue
        self.test_undefined_employee_id_issue()
        
        # Step 4: Test manager loading functionality
        self.test_manager_loading_functionality()
        
        # Step 5: Test timesheet endpoints with valid employee
        self.test_timesheet_endpoints_with_valid_employee()
        
        # Print summary
        self.print_test_summary()
    
    def print_test_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "="*60)
        print("TIMESHEET API DEBUG TEST SUMMARY")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['success']])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%" if total_tests > 0 else "0%")
        
        print("\n" + "-"*60)
        print("CRITICAL ISSUES FOUND:")
        print("-"*60)
        
        critical_issues = []
        for result in self.test_results:
            if not result['success'] and any(keyword in result['test'].lower() 
                                           for keyword in ['500', 'undefined', 'manager loading']):
                critical_issues.append(result)
        
        if critical_issues:
            for issue in critical_issues:
                print(f"🚨 {issue['test']}: {issue['message']}")
                if issue['details']:
                    print(f"   Details: {issue['details']}")
        else:
            print("✅ No critical issues found")
        
        print("\n" + "-"*60)
        print("DETAILED RESULTS:")
        print("-"*60)
        
        for result in self.test_results:
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"{status}: {result['test']} - {result['message']}")
            if result['details'] and not result['success']:
                print(f"    Details: {result['details']}")
        
        print("\n" + "="*60)

if __name__ == "__main__":
    tester = TimesheetAPITester()
    tester.run_timesheet_debug_tests()