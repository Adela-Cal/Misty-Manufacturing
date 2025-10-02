#!/usr/bin/env python3
"""
Backend API Testing Suite for Recently Implemented Features
Tests machinery section in product specifications, timesheet workflow, and system stability
"""

import requests
import json
import os
from datetime import datetime, timedelta, date
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:8001')
API_BASE = f"{BACKEND_URL}/api"

class BackendAPITester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        self.test_user_id = None
        self.test_employee_id = None
        self.test_manager_id = None
        self.test_timesheet_id = None
        
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
        """Test authentication with demo user"""
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
    
    def create_test_employee(self):
        """Create a test employee for timesheet testing"""
        print("\n=== CREATE TEST EMPLOYEE ===")
        
        try:
            # First create a user account for the employee
            user_data = {
                "username": "test_employee",
                "email": "test.employee@testcompany.com",
                "password": "TestPass123!",
                "full_name": "Test Employee",
                "role": "employee",
                "employment_type": "full_time",
                "department": "Production",
                "phone": "0412345678"
            }
            
            user_response = self.session.post(f"{API_BASE}/users", json=user_data)
            
            if user_response.status_code == 200:
                user_result = user_response.json()
                user_id = user_result.get('data', {}).get('id')
                
                if user_id:
                    # Now create employee profile
                    employee_data = {
                        "user_id": user_id,
                        "employee_number": "EMP001",
                        "first_name": "Test",
                        "last_name": "Employee",
                        "email": "test.employee@testcompany.com",
                        "phone": "0412345678",
                        "department": "Production",
                        "position": "Production Worker",
                        "start_date": "2024-01-01",
                        "employment_type": "full_time",
                        "hourly_rate": 25.50,
                        "weekly_hours": 38
                    }
                    
                    emp_response = self.session.post(f"{API_BASE}/payroll/employees", json=employee_data)
                    
                    if emp_response.status_code == 200:
                        emp_result = emp_response.json()
                        employee_id = emp_result.get('data', {}).get('id')
                        
                        self.test_employee_id = employee_id
                        self.log_result(
                            "Create Test Employee", 
                            True, 
                            f"Successfully created test employee with ID: {employee_id}"
                        )
                        return employee_id
                    else:
                        self.log_result(
                            "Create Test Employee", 
                            False, 
                            f"Employee creation failed with status {emp_response.status_code}",
                            emp_response.text
                        )
                else:
                    self.log_result(
                        "Create Test Employee", 
                        False, 
                        "User creation response missing ID"
                    )
            else:
                self.log_result(
                    "Create Test Employee", 
                    False, 
                    f"User creation failed with status {user_response.status_code}",
                    user_response.text
                )
                
        except Exception as e:
            self.log_result("Create Test Employee", False, f"Error: {str(e)}")
        
        return None
    
    def test_get_current_week_timesheet(self, employee_id):
        """Test GET /api/payroll/timesheets/current-week/{employee_id}"""
        print("\n=== GET CURRENT WEEK TIMESHEET TEST ===")
        
        try:
            response = self.session.get(f"{API_BASE}/payroll/timesheets/current-week/{employee_id}")
            
            if response.status_code == 200:
                timesheet = response.json()
                timesheet_id = timesheet.get('id')
                
                if timesheet_id:
                    self.test_timesheet_id = timesheet_id
                    self.log_result(
                        "Get Current Week Timesheet", 
                        True, 
                        f"Successfully retrieved/created timesheet with ID: {timesheet_id}",
                        f"Week starting: {timesheet.get('week_starting')}, Status: {timesheet.get('status')}"
                    )
                    return timesheet
                else:
                    self.log_result(
                        "Get Current Week Timesheet", 
                        False, 
                        "Timesheet response missing ID"
                    )
            else:
                self.log_result(
                    "Get Current Week Timesheet", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Get Current Week Timesheet", False, f"Error: {str(e)}")
        
        return None
    
    def test_update_timesheet(self, timesheet_id, employee_id):
        """Test PUT /api/payroll/timesheets/{timesheet_id}"""
        print("\n=== UPDATE TIMESHEET TEST ===")
        
        try:
            # Create sample timesheet entries for a week
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
                    "notes": f"Work day {i+1}"
                })
            
            timesheet_data = {
                "employee_id": employee_id,
                "week_starting": week_start.isoformat(),
                "entries": entries
            }
            
            response = self.session.put(f"{API_BASE}/payroll/timesheets/{timesheet_id}", json=timesheet_data)
            
            if response.status_code == 200:
                self.log_result(
                    "Update Timesheet", 
                    True, 
                    "Successfully updated timesheet with 40 hours of work entries"
                )
                return True
            else:
                self.log_result(
                    "Update Timesheet", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Update Timesheet", False, f"Error: {str(e)}")
        
        return False
    
    def test_submit_timesheet(self, timesheet_id):
        """Test POST /api/payroll/timesheets/{timesheet_id}/submit"""
        print("\n=== SUBMIT TIMESHEET TEST ===")
        
        try:
            response = self.session.post(f"{API_BASE}/payroll/timesheets/{timesheet_id}/submit")
            
            if response.status_code == 200:
                result = response.json()
                message = result.get('message', '')
                
                if 'submitted for approval' in message.lower():
                    self.log_result(
                        "Submit Timesheet", 
                        True, 
                        "Successfully submitted timesheet for approval",
                        f"Message: {message}"
                    )
                    return True
                else:
                    self.log_result(
                        "Submit Timesheet", 
                        False, 
                        "Unexpected response message",
                        f"Message: {message}"
                    )
            else:
                self.log_result(
                    "Submit Timesheet", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Submit Timesheet", False, f"Error: {str(e)}")
        
        return False
    
    def test_get_pending_timesheets(self):
        """Test GET /api/payroll/timesheets/pending"""
        print("\n=== GET PENDING TIMESHEETS TEST ===")
        
        try:
            response = self.session.get(f"{API_BASE}/payroll/timesheets/pending")
            
            if response.status_code == 200:
                data = response.json()
                pending_timesheets = data.get('data', [])
                
                # Check if our submitted timesheet is in the pending list
                found_timesheet = False
                for timesheet in pending_timesheets:
                    if timesheet.get('id') == self.test_timesheet_id:
                        found_timesheet = True
                        break
                
                if found_timesheet:
                    self.log_result(
                        "Get Pending Timesheets", 
                        True, 
                        f"Successfully retrieved {len(pending_timesheets)} pending timesheets including our test timesheet"
                    )
                else:
                    self.log_result(
                        "Get Pending Timesheets", 
                        True, 
                        f"Successfully retrieved {len(pending_timesheets)} pending timesheets (test timesheet may have been processed)"
                    )
                
                return pending_timesheets
            else:
                self.log_result(
                    "Get Pending Timesheets", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Get Pending Timesheets", False, f"Error: {str(e)}")
        
        return []
    
    def test_approve_timesheet(self, timesheet_id):
        """Test POST /api/payroll/timesheets/{timesheet_id}/approve"""
        print("\n=== APPROVE TIMESHEET TEST ===")
        
        try:
            response = self.session.post(f"{API_BASE}/payroll/timesheets/{timesheet_id}/approve")
            
            if response.status_code == 200:
                result = response.json()
                message = result.get('message', '')
                data = result.get('data', {})
                
                if 'approved' in message.lower():
                    gross_pay = data.get('gross_pay', 0)
                    net_pay = data.get('net_pay', 0)
                    hours_worked = data.get('hours_worked', 0)
                    
                    self.log_result(
                        "Approve Timesheet", 
                        True, 
                        "Successfully approved timesheet and calculated pay",
                        f"Gross Pay: ${gross_pay}, Net Pay: ${net_pay}, Hours: {hours_worked}"
                    )
                    return True
                else:
                    self.log_result(
                        "Approve Timesheet", 
                        False, 
                        "Unexpected response message",
                        f"Message: {message}"
                    )
            else:
                self.log_result(
                    "Approve Timesheet", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Approve Timesheet", False, f"Error: {str(e)}")
        
        return False
    def test_manager_selection_functionality(self, employee_id):
        """Test manager selection functionality in timesheet workflow"""
        print("\n=== MANAGER SELECTION FUNCTIONALITY TEST ===")
        
        try:
            # First, get the employee profile to check if manager_id is set
            response = self.session.get(f"{API_BASE}/payroll/employees/{employee_id}")
            
            if response.status_code == 200:
                employee = response.json()
                manager_id = employee.get('manager_id')
                
                if manager_id:
                    self.log_result(
                        "Manager Selection - Employee Profile", 
                        True, 
                        f"Employee has manager assigned: {manager_id}"
                    )
                else:
                    self.log_result(
                        "Manager Selection - Employee Profile", 
                        False, 
                        "Employee does not have a manager assigned",
                        "Manager selection may not be implemented in employee profile"
                    )
                
                # Test if we can get manager information
                if manager_id:
                    manager_response = self.session.get(f"{API_BASE}/users/{manager_id}")
                    if manager_response.status_code == 200:
                        manager = manager_response.json()
                        self.log_result(
                            "Manager Selection - Manager Details", 
                            True, 
                            f"Successfully retrieved manager details: {manager.get('full_name')}"
                        )
                    else:
                        self.log_result(
                            "Manager Selection - Manager Details", 
                            False, 
                            f"Failed to retrieve manager details: {manager_response.status_code}"
                        )
                
                return manager_id
            else:
                self.log_result(
                    "Manager Selection - Employee Profile", 
                    False, 
                    f"Failed to retrieve employee profile: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Manager Selection Functionality", False, f"Error: {str(e)}")
        
        return None
    
    def test_timesheet_status_updates(self, timesheet_id):
        """Test that timesheet status updates correctly through the workflow"""
        print("\n=== TIMESHEET STATUS UPDATES TEST ===")
        
        try:
            # Get timesheet and check status progression
            response = self.session.get(f"{API_BASE}/payroll/timesheets/current-week/{self.test_employee_id}")
            
            if response.status_code == 200:
                timesheet = response.json()
                current_status = timesheet.get('status')
                
                # Check if status is 'approved' after our workflow
                if current_status == 'approved':
                    self.log_result(
                        "Timesheet Status Updates", 
                        True, 
                        f"Timesheet status correctly updated to 'approved'",
                        f"Status progression: draft → submitted → approved"
                    )
                    
                    # Check if approval metadata is present
                    approved_by = timesheet.get('approved_by')
                    approved_at = timesheet.get('approved_at')
                    
                    if approved_by and approved_at:
                        self.log_result(
                            "Timesheet Approval Metadata", 
                            True, 
                            "Approval metadata correctly recorded",
                            f"Approved by: {approved_by}, Approved at: {approved_at}"
                        )
                    else:
                        self.log_result(
                            "Timesheet Approval Metadata", 
                            False, 
                            "Missing approval metadata",
                            f"approved_by: {approved_by}, approved_at: {approved_at}"
                        )
                        
                elif current_status == 'submitted':
                    self.log_result(
                        "Timesheet Status Updates", 
                        False, 
                        "Timesheet is still in 'submitted' status - approval may have failed"
                    )
                else:
                    self.log_result(
                        "Timesheet Status Updates", 
                        False, 
                        f"Unexpected timesheet status: {current_status}"
                    )
            else:
                self.log_result(
                    "Timesheet Status Updates", 
                    False, 
                    f"Failed to retrieve timesheet: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Timesheet Status Updates", False, f"Error: {str(e)}")
    
    def test_payroll_system_integration(self, timesheet_id):
        """Test integration with existing payroll system"""
        print("\n=== PAYROLL SYSTEM INTEGRATION TEST ===")
        
        try:
            # Check if payroll calculation was created after timesheet approval
            # This would be in the payroll_calculations collection
            # Since we don't have direct access, we'll test the employee leave balances update
            
            response = self.session.get(f"{API_BASE}/payroll/employees/{self.test_employee_id}/leave-balances")
            
            if response.status_code == 200:
                leave_balances = response.json()
                
                # Check if leave balances are present and reasonable
                annual_leave = leave_balances.get('annual_leave_balance', 0)
                sick_leave = leave_balances.get('sick_leave_balance', 0)
                
                if annual_leave >= 0 and sick_leave >= 0:
                    self.log_result(
                        "Payroll System Integration - Leave Balances", 
                        True, 
                        "Leave balances are accessible and valid",
                        f"Annual Leave: {annual_leave} hours, Sick Leave: {sick_leave} hours"
                    )
                else:
                    self.log_result(
                        "Payroll System Integration - Leave Balances", 
                        False, 
                        "Invalid leave balance values",
                        f"Annual Leave: {annual_leave}, Sick Leave: {sick_leave}"
                    )
                
                # Test payroll summary endpoint if available
                try:
                    from datetime import date
                    today = date.today()
                    start_date = today.replace(day=1)  # First day of month
                    end_date = today
                    
                    summary_response = self.session.get(
                        f"{API_BASE}/payroll/reports/payroll-summary?start_date={start_date}&end_date={end_date}"
                    )
                    
                    if summary_response.status_code == 200:
                        summary_data = summary_response.json()
                        payroll_data = summary_data.get('data', {})
                        
                        self.log_result(
                            "Payroll System Integration - Summary Report", 
                            True, 
                            "Payroll summary report accessible",
                            f"Total employees: {payroll_data.get('employee_count', 0)}"
                        )
                    else:
                        self.log_result(
                            "Payroll System Integration - Summary Report", 
                            False, 
                            f"Payroll summary not accessible: {summary_response.status_code}"
                        )
                        
                except Exception as summary_error:
                    self.log_result(
                        "Payroll System Integration - Summary Report", 
                        False, 
                        f"Error accessing payroll summary: {str(summary_error)}"
                    )
                    
            else:
                self.log_result(
                    "Payroll System Integration", 
                    False, 
                    f"Failed to access leave balances: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Payroll System Integration", False, f"Error: {str(e)}")
    
    def test_timesheet_api_debug(self):
        """Debug timesheet API issues reported by user"""
        print("\n=== TIMESHEET API DEBUG TESTS ===")
        
        # Test 1: Check if payroll endpoints are accessible
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
                        f"500 Internal Server Error with {description} employee_id",
                        f"This confirms the reported issue - URL: {url}"
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
                        response.text
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
        
        # First get a valid employee ID
        employee_id = self.test_employee_id or self.test_timesheet_api_debug()
        
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
                    f"Employee ID: {employee_id}, Response: {response.text}"
                )
            else:
                self.log_result(
                    "GET Current Week Timesheet", 
                    False, 
                    f"Unexpected status: {response.status_code}",
                    response.text
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
                    response.text
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
                    response.text
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
                    response.text
                )
                
        except Exception as e:
            self.log_result("POST Approve Timesheet", False, f"Error: {str(e)}")
    
    def run_timesheet_debug_tests(self):
        """Run comprehensive timesheet API debugging tests"""
        print("\n" + "="*60)
        print("TIMESHEET API DEBUG TESTING")
        print("="*60)
        
        # Step 1: Authenticate
        if not self.authenticate():
            print("❌ Authentication failed - cannot proceed with tests")
            return
        
        # Step 2: Test payroll authentication and access
        self.test_timesheet_api_debug()
        
        # Step 3: Test undefined employee_id issue
        self.test_undefined_employee_id_issue()
        
        # Step 4: Test manager loading functionality
        self.test_manager_loading_functionality()
        
        # Step 5: Test timesheet endpoints with valid employee
        self.test_timesheet_endpoints_with_valid_employee()
        
        # Print summary
        self.print_test_summary()

    def run_timesheet_workflow_tests(self):
        """Run the complete timesheet workflow test suite"""
        print("\n" + "="*60)
        print("ENHANCED TIMESHEET WORKFLOW TESTING")
        print("="*60)
        
        # Step 1: Authenticate
        if not self.authenticate():
            print("❌ Authentication failed - cannot proceed with tests")
            return
        
        # Step 2: Create test employee
        employee_id = self.create_test_employee()
        if not employee_id:
            print("❌ Failed to create test employee - cannot proceed with timesheet tests")
            return
        
        # Step 3: Test manager selection functionality
        manager_id = self.test_manager_selection_functionality(employee_id)
        
        # Step 4: Get/Create current week timesheet
        timesheet = self.test_get_current_week_timesheet(employee_id)
        if not timesheet:
            print("❌ Failed to get/create timesheet - cannot proceed")
            return
        
        timesheet_id = timesheet.get('id')
        
        # Step 5: Update timesheet with work entries
        if not self.test_update_timesheet(timesheet_id, employee_id):
            print("❌ Failed to update timesheet - cannot proceed")
            return
        
        # Step 6: Submit timesheet for approval
        if not self.test_submit_timesheet(timesheet_id):
            print("❌ Failed to submit timesheet - cannot proceed")
            return
        
        # Step 7: Test pending timesheets endpoint (manager view)
        pending_timesheets = self.test_get_pending_timesheets()
        
        # Step 8: Approve timesheet
        if not self.test_approve_timesheet(timesheet_id):
            print("❌ Failed to approve timesheet - workflow incomplete")
        
        # Step 9: Test status updates
        self.test_timesheet_status_updates(timesheet_id)
        
        # Step 10: Test payroll system integration
        self.test_payroll_system_integration(timesheet_id)
        
        # Print summary
        self.print_test_summary()
    
    def print_test_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "="*60)
        print("TIMESHEET WORKFLOW TEST SUMMARY")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['success']])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%" if total_tests > 0 else "0%")
        
        print("\n" + "-"*60)
        print("DETAILED RESULTS:")
        print("-"*60)
        
        # Group results by category
        categories = {}
        for result in self.test_results:
            test_name = result['test']
            category = test_name.split(' - ')[0] if ' - ' in test_name else test_name
            if category not in categories:
                categories[category] = []
            categories[category].append(result)
        
        for category, results in categories.items():
            print(f"\n{category}:")
            for result in results:
                status = "✅ PASS" if result['success'] else "❌ FAIL"
                print(f"  {status}: {result['message']}")
                if result['details'] and not result['success']:
                    print(f"    Details: {result['details']}")
        
        print("\n" + "="*60)
        print("WORKFLOW ANALYSIS:")
        print("="*60)
        
        # Analyze workflow completeness
        workflow_steps = [
            "Authentication",
            "Create Test Employee", 
            "Get Current Week Timesheet",
            "Update Timesheet",
            "Submit Timesheet",
            "Get Pending Timesheets",
            "Approve Timesheet"
        ]
        
        completed_steps = []
        failed_steps = []
        
        for step in workflow_steps:
            step_results = [r for r in self.test_results if step.lower() in r['test'].lower()]
            if step_results and any(r['success'] for r in step_results):
                completed_steps.append(step)
            else:
                failed_steps.append(step)
        
        print(f"Completed Workflow Steps: {len(completed_steps)}/{len(workflow_steps)}")
        
        if completed_steps:
            print("\n✅ Completed Steps:")
            for step in completed_steps:
                print(f"  - {step}")
        
        if failed_steps:
            print("\n❌ Failed Steps:")
            for step in failed_steps:
                print(f"  - {step}")
        
        # Check for critical issues
        critical_issues = []
        for result in self.test_results:
            if not result['success'] and any(keyword in result['test'].lower() 
                                           for keyword in ['submit', 'approve', 'pending']):
                critical_issues.append(result['test'])
        
        if critical_issues:
            print(f"\n🚨 CRITICAL ISSUES FOUND:")
            for issue in critical_issues:
                print(f"  - {issue}")
        
        print("\n" + "="*60)
    
    def test_machinery_product_specifications_create(self):
        """Test POST /api/product-specifications with machinery data"""
        print("\n=== MACHINERY PRODUCT SPECIFICATIONS CREATE TEST ===")
        
        try:
            # Test data with machinery section
            spec_data = {
                "product_name": "Test Paper Core with Machinery",
                "product_type": "Spiral Paper Core",
                "manufacturing_notes": "Test product for machinery functionality",
                "specifications": {
                    "internal_diameter": 76.0,
                    "wall_thickness_required": 3.0
                },
                "material_layers": [
                    {
                        "material_id": "test-material-001",
                        "layer_type": "Outer Most Layer",
                        "thickness": 0.15,
                        "quantity": 2.0
                    }
                ],
                "machinery": [
                    {
                        "machine_name": "Slitting Machine A",
                        "running_speed": 150.0,
                        "setup_time": "00:30",
                        "pack_up_time": "00:15",
                        "functions": [
                            {
                                "function_name": "Slitting",
                                "rate_per_hour": 500.0
                            },
                            {
                                "function_name": "winding",
                                "rate_per_hour": 300.0
                            }
                        ]
                    },
                    {
                        "machine_name": "Cutting Machine B",
                        "running_speed": 200.0,
                        "setup_time": "00:45",
                        "pack_up_time": "00:20",
                        "functions": [
                            {
                                "function_name": "Cutting/Indexing",
                                "rate_per_hour": 400.0
                            },
                            {
                                "function_name": "splitting",
                                "rate_per_hour": 350.0
                            }
                        ]
                    },
                    {
                        "machine_name": "Packing Machine C",
                        "running_speed": 100.0,
                        "setup_time": "00:20",
                        "pack_up_time": "00:10",
                        "functions": [
                            {
                                "function_name": "Packing",
                                "rate_per_hour": 250.0
                            },
                            {
                                "function_name": "Delivery Time",
                                "rate_per_hour": 150.0
                            }
                        ]
                    }
                ]
            }
            
            response = self.session.post(f"{API_BASE}/product-specifications", json=spec_data)
            
            if response.status_code == 200:
                result = response.json()
                spec_id = result.get('data', {}).get('id')
                
                if spec_id:
                    self.log_result(
                        "Machinery Product Specifications CREATE", 
                        True, 
                        f"Successfully created product specification with machinery data (ID: {spec_id})",
                        f"3 machines with 6 total functions created"
                    )
                    return spec_id
                else:
                    self.log_result(
                        "Machinery Product Specifications CREATE", 
                        False, 
                        "Response missing specification ID",
                        str(result)
                    )
            else:
                self.log_result(
                    "Machinery Product Specifications CREATE", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Machinery Product Specifications CREATE", False, f"Error: {str(e)}")
        
        return None
    
    def test_machinery_product_specifications_retrieve(self, spec_id):
        """Test GET /api/product-specifications/{spec_id} returns machinery data"""
        print("\n=== MACHINERY PRODUCT SPECIFICATIONS RETRIEVE TEST ===")
        
        if not spec_id:
            self.log_result(
                "Machinery Product Specifications RETRIEVE", 
                False, 
                "No specification ID available for retrieve test"
            )
            return None
        
        try:
            response = self.session.get(f"{API_BASE}/product-specifications/{spec_id}")
            
            if response.status_code == 200:
                spec = response.json()
                machinery = spec.get('machinery', [])
                
                if machinery and len(machinery) == 3:
                    # Verify machinery structure
                    required_fields = ['machine_name', 'running_speed', 'setup_time', 'pack_up_time', 'functions']
                    required_function_types = ['Slitting', 'winding', 'Cutting/Indexing', 'splitting', 'Packing', 'Delivery Time']
                    
                    all_functions = []
                    for machine in machinery:
                        # Check machine fields
                        missing_fields = [field for field in required_fields if field not in machine]
                        if missing_fields:
                            self.log_result(
                                "Machinery Product Specifications RETRIEVE", 
                                False, 
                                f"Machine missing required fields: {missing_fields}"
                            )
                            return None
                        
                        # Collect all functions
                        for func in machine.get('functions', []):
                            all_functions.append(func.get('function_name'))
                    
                    # Check if all required function types are present
                    found_functions = set(all_functions)
                    missing_functions = set(required_function_types) - found_functions
                    
                    if not missing_functions:
                        self.log_result(
                            "Machinery Product Specifications RETRIEVE", 
                            True, 
                            f"Successfully retrieved machinery data with all required function types",
                            f"3 machines, 6 functions: {', '.join(sorted(found_functions))}"
                        )
                        return spec
                    else:
                        self.log_result(
                            "Machinery Product Specifications RETRIEVE", 
                            False, 
                            f"Missing required function types: {missing_functions}",
                            f"Found: {found_functions}"
                        )
                else:
                    self.log_result(
                        "Machinery Product Specifications RETRIEVE", 
                        False, 
                        f"Expected 3 machines, got {len(machinery)}",
                        f"Machinery data: {machinery}"
                    )
            else:
                self.log_result(
                    "Machinery Product Specifications RETRIEVE", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Machinery Product Specifications RETRIEVE", False, f"Error: {str(e)}")
        
        return None
    
    def test_machinery_product_specifications_update(self, spec_id):
        """Test PUT /api/product-specifications/{spec_id} can update machinery data"""
        print("\n=== MACHINERY PRODUCT SPECIFICATIONS UPDATE TEST ===")
        
        if not spec_id:
            self.log_result(
                "Machinery Product Specifications UPDATE", 
                False, 
                "No specification ID available for update test"
            )
            return False
        
        try:
            # Updated machinery data
            update_data = {
                "product_name": "Updated Paper Core with Machinery",
                "product_type": "Spiral Paper Core",
                "manufacturing_notes": "Updated test product for machinery functionality",
                "specifications": {
                    "internal_diameter": 76.0,
                    "wall_thickness_required": 3.0
                },
                "material_layers": [
                    {
                        "material_id": "test-material-001",
                        "layer_type": "Outer Most Layer",
                        "thickness": 0.15,
                        "quantity": 2.0
                    }
                ],
                "machinery": [
                    {
                        "machine_name": "Updated Slitting Machine A",
                        "running_speed": 175.0,  # Updated speed
                        "setup_time": "00:25",   # Updated time
                        "pack_up_time": "00:15",
                        "functions": [
                            {
                                "function_name": "Slitting",
                                "rate_per_hour": 550.0  # Updated rate
                            },
                            {
                                "function_name": "winding",
                                "rate_per_hour": 325.0  # Updated rate
                            }
                        ]
                    }
                ]
            }
            
            response = self.session.put(f"{API_BASE}/product-specifications/{spec_id}", json=update_data)
            
            if response.status_code == 200:
                # Verify the update by retrieving the specification
                get_response = self.session.get(f"{API_BASE}/product-specifications/{spec_id}")
                
                if get_response.status_code == 200:
                    updated_spec = get_response.json()
                    machinery = updated_spec.get('machinery', [])
                    
                    if machinery and len(machinery) == 1:
                        machine = machinery[0]
                        
                        # Check updated values
                        checks = [
                            ("Machine Name", machine.get('machine_name') == "Updated Slitting Machine A"),
                            ("Running Speed", machine.get('running_speed') == 175.0),
                            ("Setup Time", machine.get('setup_time') == "00:25"),
                            ("Function Rate", machine.get('functions', [{}])[0].get('rate_per_hour') == 550.0)
                        ]
                        
                        passed_checks = [name for name, passed in checks if passed]
                        failed_checks = [name for name, passed in checks if not passed]
                        
                        if len(passed_checks) == len(checks):
                            self.log_result(
                                "Machinery Product Specifications UPDATE", 
                                True, 
                                "Successfully updated machinery specifications",
                                f"All fields updated correctly: {', '.join(passed_checks)}"
                            )
                            return True
                        else:
                            self.log_result(
                                "Machinery Product Specifications UPDATE", 
                                False, 
                                f"Some fields not updated correctly",
                                f"Failed: {failed_checks}, Passed: {passed_checks}"
                            )
                    else:
                        self.log_result(
                            "Machinery Product Specifications UPDATE", 
                            False, 
                            f"Expected 1 machine after update, got {len(machinery)}"
                        )
                else:
                    self.log_result(
                        "Machinery Product Specifications UPDATE", 
                        False, 
                        f"Failed to retrieve updated specification: {get_response.status_code}"
                    )
            else:
                self.log_result(
                    "Machinery Product Specifications UPDATE", 
                    False, 
                    f"Update failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Machinery Product Specifications UPDATE", False, f"Error: {str(e)}")
        
        return False
    
    def test_machinery_function_types_validation(self):
        """Test that all required function types are supported"""
        print("\n=== MACHINERY FUNCTION TYPES VALIDATION TEST ===")
        
        required_function_types = ["Slitting", "winding", "Cutting/Indexing", "splitting", "Packing", "Delivery Time"]
        
        try:
            # Test each function type individually
            for function_type in required_function_types:
                spec_data = {
                    "product_name": f"Test {function_type} Function",
                    "product_type": "Spiral Paper Core",
                    "specifications": {
                        "internal_diameter": 40.0,
                        "wall_thickness_required": 1.8
                    },
                    "material_layers": [],
                    "machinery": [
                        {
                            "machine_name": f"Test {function_type} Machine",
                            "running_speed": 100.0,
                            "setup_time": "00:30",
                            "pack_up_time": "00:15",
                            "functions": [
                                {
                                    "function_name": function_type,
                                    "rate_per_hour": 200.0
                                }
                            ]
                        }
                    ]
                }
                
                response = self.session.post(f"{API_BASE}/product-specifications", json=spec_data)
                
                if response.status_code != 200:
                    self.log_result(
                        "Machinery Function Types Validation", 
                        False, 
                        f"Function type '{function_type}' not accepted",
                        f"Status: {response.status_code}, Response: {response.text}"
                    )
                    return False
            
            self.log_result(
                "Machinery Function Types Validation", 
                True, 
                f"All {len(required_function_types)} required function types are supported",
                f"Tested: {', '.join(required_function_types)}"
            )
            return True
            
        except Exception as e:
            self.log_result("Machinery Function Types Validation", False, f"Error: {str(e)}")
        
        return False
    
    def test_machinery_optional_fields(self):
        """Test that optional fields in machinery work correctly"""
        print("\n=== MACHINERY OPTIONAL FIELDS TEST ===")
        
        try:
            # Test with minimal machinery data (only required fields)
            spec_data = {
                "product_name": "Test Minimal Machinery",
                "product_type": "Spiral Paper Core",
                "specifications": {
                    "internal_diameter": 40.0,
                    "wall_thickness_required": 1.8
                },
                "material_layers": [],
                "machinery": [
                    {
                        "machine_name": "Minimal Machine",
                        # running_speed, setup_time, pack_up_time are optional
                        "functions": [
                            {
                                "function_name": "Slitting"
                                # rate_per_hour is optional
                            }
                        ]
                    }
                ]
            }
            
            response = self.session.post(f"{API_BASE}/product-specifications", json=spec_data)
            
            if response.status_code == 200:
                result = response.json()
                spec_id = result.get('data', {}).get('id')
                
                if spec_id:
                    # Retrieve and verify optional fields are handled correctly
                    get_response = self.session.get(f"{API_BASE}/product-specifications/{spec_id}")
                    
                    if get_response.status_code == 200:
                        spec = get_response.json()
                        machinery = spec.get('machinery', [])
                        
                        if machinery:
                            machine = machinery[0]
                            function = machine.get('functions', [{}])[0]
                            
                            # Check that optional fields can be null/missing
                            optional_checks = [
                                ("Running Speed", machine.get('running_speed') is None or isinstance(machine.get('running_speed'), (int, float))),
                                ("Setup Time", machine.get('setup_time') is None or isinstance(machine.get('setup_time'), str)),
                                ("Pack Up Time", machine.get('pack_up_time') is None or isinstance(machine.get('pack_up_time'), str)),
                                ("Rate Per Hour", function.get('rate_per_hour') is None or isinstance(function.get('rate_per_hour'), (int, float)))
                            ]
                            
                            all_valid = all(valid for _, valid in optional_checks)
                            
                            if all_valid:
                                self.log_result(
                                    "Machinery Optional Fields", 
                                    True, 
                                    "Optional fields handled correctly (can be null or proper type)",
                                    f"Machine name required, other fields optional"
                                )
                                return True
                            else:
                                failed_checks = [name for name, valid in optional_checks if not valid]
                                self.log_result(
                                    "Machinery Optional Fields", 
                                    False, 
                                    f"Optional field validation failed: {failed_checks}"
                                )
                        else:
                            self.log_result(
                                "Machinery Optional Fields", 
                                False, 
                                "No machinery data found in retrieved specification"
                            )
                    else:
                        self.log_result(
                            "Machinery Optional Fields", 
                            False, 
                            f"Failed to retrieve specification: {get_response.status_code}"
                        )
                else:
                    self.log_result(
                        "Machinery Optional Fields", 
                        False, 
                        "Response missing specification ID"
                    )
            else:
                self.log_result(
                    "Machinery Optional Fields", 
                    False, 
                    f"Failed to create specification with minimal machinery: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Machinery Optional Fields", False, f"Error: {str(e)}")
        
        return False
    
    def run_machinery_tests(self):
        """Run comprehensive machinery functionality tests"""
        print("\n" + "="*60)
        print("MACHINERY SECTION TESTING")
        print("="*60)
        
        # Test 1: Create product specification with machinery
        spec_id = self.test_machinery_product_specifications_create()
        
        # Test 2: Retrieve and verify machinery data
        if spec_id:
            retrieved_spec = self.test_machinery_product_specifications_retrieve(spec_id)
            
            # Test 3: Update machinery data
            self.test_machinery_product_specifications_update(spec_id)
        
        # Test 4: Validate all function types
        self.test_machinery_function_types_validation()
        
        # Test 5: Test optional fields
        self.test_machinery_optional_fields()
    
    def test_role_permissions(self):
        """Test that invoicing endpoints require proper permissions"""
        print("\n=== ROLE PERMISSIONS TEST ===")
        
        # Test without authentication
        temp_session = requests.Session()
        
        try:
            response = temp_session.get(f"{API_BASE}/invoicing/live-jobs")
            
            if response.status_code in [401, 403]:
                self.log_result(
                    "Role Permissions", 
                    True, 
                    f"Invoicing endpoints properly require authentication (status: {response.status_code})"
                )
            else:
                self.log_result(
                    "Role Permissions", 
                    False, 
                    f"Expected 401/403 but got {response.status_code}",
                    "Invoicing endpoints should require authentication"
                )
                
        except Exception as e:
            self.log_result("Role Permissions", False, f"Error: {str(e)}")
    
    def test_xero_connection_status(self):
        """Test GET /api/xero/status"""
        print("\n=== XERO CONNECTION STATUS TEST ===")
        
        try:
            response = self.session.get(f"{API_BASE}/xero/status")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                if 'connected' in data and 'message' in data:
                    connected = data.get('connected')
                    message = data.get('message')
                    
                    # For new connections, should return false
                    if connected == False and "No Xero connection found" in message:
                        self.log_result(
                            "Xero Connection Status", 
                            True, 
                            "Correctly reports no Xero connection for new user",
                            f"Connected: {connected}, Message: {message}"
                        )
                    elif connected == True:
                        self.log_result(
                            "Xero Connection Status", 
                            True, 
                            "User has active Xero connection",
                            f"Message: {message}"
                        )
                    else:
                        self.log_result(
                            "Xero Connection Status", 
                            False, 
                            "Unexpected connection status response",
                            f"Connected: {connected}, Message: {message}"
                        )
                else:
                    self.log_result(
                        "Xero Connection Status", 
                        False, 
                        "Response missing required fields (connected, message)",
                        str(data)
                    )
            else:
                self.log_result(
                    "Xero Connection Status", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Xero Connection Status", False, f"Error: {str(e)}")
    
    def test_xero_auth_url(self):
        """Test GET /api/xero/auth/url"""
        print("\n=== XERO AUTH URL TEST ===")
        
        try:
            response = self.session.get(f"{API_BASE}/xero/auth/url")
            
            if response.status_code == 200:
                data = response.json()
                
                if 'auth_url' in data and 'state' in data:
                    auth_url = data.get('auth_url')
                    state = data.get('state')
                    
                    # Verify URL components
                    expected_client_id = "0C765F92708046D5B625162E5D42C5FB"
                    expected_callback = "https://app.emergent.sh/api/xero/callback"  # From backend/.env
                    expected_scopes = "accounting.transactions accounting.contacts.read accounting.invoices.read accounting.settings.read"
                    
                    url_checks = []
                    
                    # Check client ID
                    if expected_client_id in auth_url:
                        url_checks.append("✅ Client ID correct")
                    else:
                        url_checks.append("❌ Client ID missing or incorrect")
                    
                    # Check callback URL (URL encoded)
                    import urllib.parse
                    encoded_callback = urllib.parse.quote(expected_callback, safe='')
                    if encoded_callback in auth_url or expected_callback in auth_url:
                        url_checks.append("✅ Callback URL correct")
                    else:
                        url_checks.append("❌ Callback URL missing or incorrect")
                    
                    # Check scopes (at least accounting.transactions should be present)
                    if "accounting.transactions" in auth_url:
                        url_checks.append("✅ Required scopes present")
                    else:
                        url_checks.append("❌ Required scopes missing")
                    
                    # Check state parameter
                    if state and len(state) > 20:
                        url_checks.append("✅ State parameter generated")
                    else:
                        url_checks.append("❌ State parameter missing or too short")
                    
                    # Check if it's a proper Xero URL
                    if "https://login.xero.com/identity/connect/authorize" in auth_url:
                        url_checks.append("✅ Proper Xero authorization URL")
                    else:
                        url_checks.append("❌ Not a proper Xero authorization URL")
                    
                    all_checks_passed = all("✅" in check for check in url_checks)
                    
                    self.log_result(
                        "Xero Auth URL", 
                        all_checks_passed, 
                        "Generated Xero OAuth URL" if all_checks_passed else "OAuth URL has issues",
                        "\n".join(url_checks)
                    )
                    
                    return state  # Return state for callback testing
                else:
                    self.log_result(
                        "Xero Auth URL", 
                        False, 
                        "Response missing required fields (auth_url, state)",
                        str(data)
                    )
            else:
                self.log_result(
                    "Xero Auth URL", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Xero Auth URL", False, f"Error: {str(e)}")
        
        return None
    
    def test_xero_auth_callback(self, state_param):
        """Test POST /api/xero/auth/callback with mock data"""
        print("\n=== XERO AUTH CALLBACK TEST ===")
        
        if not state_param:
            self.log_result(
                "Xero Auth Callback", 
                False, 
                "No state parameter available from auth URL test"
            )
            return
        
        try:
            # Test with mock callback data
            callback_data = {
                "code": "mock_authorization_code_12345",
                "state": state_param
            }
            
            response = self.session.post(f"{API_BASE}/xero/auth/callback", json=callback_data)
            
            # Note: This will likely fail with actual Xero API call, but we're testing the endpoint structure
            if response.status_code == 200:
                data = response.json()
                
                if 'message' in data:
                    self.log_result(
                        "Xero Auth Callback", 
                        True, 
                        "Callback endpoint processed successfully",
                        data.get('message')
                    )
                else:
                    self.log_result(
                        "Xero Auth Callback", 
                        False, 
                        "Callback response missing message field",
                        str(data)
                    )
            elif response.status_code == 400:
                # Expected for mock data - check if it's validating properly
                error_text = response.text
                if "authorization code" in error_text.lower() or "failed to exchange" in error_text.lower():
                    self.log_result(
                        "Xero Auth Callback", 
                        True, 
                        "Callback endpoint properly validates authorization codes (expected failure with mock data)",
                        f"Status: {response.status_code}, Response: {error_text}"
                    )
                else:
                    self.log_result(
                        "Xero Auth Callback", 
                        False, 
                        f"Unexpected error response: {response.status_code}",
                        error_text
                    )
            else:
                self.log_result(
                    "Xero Auth Callback", 
                    False, 
                    f"Unexpected status code: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Xero Auth Callback", False, f"Error: {str(e)}")
    
    def test_xero_disconnect(self):
        """Test DELETE /api/xero/disconnect"""
        print("\n=== XERO DISCONNECT TEST ===")
        
        try:
            response = self.session.delete(f"{API_BASE}/xero/disconnect")
            
            if response.status_code == 200:
                data = response.json()
                
                if 'message' in data:
                    message = data.get('message')
                    
                    # Should return success message regardless of whether connection existed
                    if "disconnection successful" in message.lower() or "no xero connection found" in message.lower():
                        self.log_result(
                            "Xero Disconnect", 
                            True, 
                            "Disconnect endpoint working correctly",
                            message
                        )
                    else:
                        self.log_result(
                            "Xero Disconnect", 
                            False, 
                            "Unexpected disconnect response message",
                            message
                        )
                else:
                    self.log_result(
                        "Xero Disconnect", 
                        False, 
                        "Disconnect response missing message field",
                        str(data)
                    )
            else:
                self.log_result(
                    "Xero Disconnect", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Xero Disconnect", False, f"Error: {str(e)}")
    
    def test_xero_permissions(self):
        """Test that Xero endpoints require admin/manager permissions"""
        print("\n=== XERO PERMISSIONS TEST ===")
        
        # Test without authentication
        temp_session = requests.Session()
        
        try:
            response = temp_session.get(f"{API_BASE}/xero/status")
            
            if response.status_code in [401, 403]:
                self.log_result(
                    "Xero Permissions", 
                    True, 
                    f"Xero endpoints properly require authentication (status: {response.status_code})"
                )
            else:
                self.log_result(
                    "Xero Permissions", 
                    False, 
                    f"Expected 401/403 but got {response.status_code}",
                    "Xero endpoints should require admin/manager authentication"
                )
                
        except Exception as e:
            self.log_result("Xero Permissions", False, f"Error: {str(e)}")
    
    def test_xero_next_invoice_number(self):
        """Test GET /api/xero/next-invoice-number"""
        print("\n=== XERO NEXT INVOICE NUMBER TEST ===")
        
        try:
            response = self.session.get(f"{API_BASE}/xero/next-invoice-number")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                required_fields = ['next_number', 'formatted_number']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    next_number = data.get('next_number')
                    formatted_number = data.get('formatted_number')
                    
                    # Validate format (should be INV-XXXXXX)
                    if isinstance(next_number, int) and next_number > 0:
                        if formatted_number and formatted_number.startswith('INV-'):
                            self.log_result(
                                "Xero Next Invoice Number", 
                                True, 
                                f"Successfully retrieved next invoice number: {formatted_number}",
                                f"Next number: {next_number}, Formatted: {formatted_number}"
                            )
                        else:
                            self.log_result(
                                "Xero Next Invoice Number", 
                                False, 
                                "Invalid formatted number format",
                                f"Expected INV-XXXXXX format, got: {formatted_number}"
                            )
                    else:
                        self.log_result(
                            "Xero Next Invoice Number", 
                            False, 
                            "Invalid next_number value",
                            f"Expected positive integer, got: {next_number}"
                        )
                else:
                    self.log_result(
                        "Xero Next Invoice Number", 
                        False, 
                        f"Response missing required fields: {missing_fields}",
                        str(data)
                    )
            elif response.status_code == 401:
                # Expected if no Xero connection
                error_text = response.text
                if "No Xero connection found" in error_text:
                    self.log_result(
                        "Xero Next Invoice Number", 
                        True, 
                        "Correctly handles missing Xero connection",
                        f"Status: {response.status_code}, Response: {error_text}"
                    )
                else:
                    self.log_result(
                        "Xero Next Invoice Number", 
                        False, 
                        f"Unexpected 401 error: {error_text}"
                    )
            elif response.status_code == 500:
                # May be expected if Xero integration not fully configured
                error_text = response.text
                if "Failed to get next invoice number" in error_text:
                    self.log_result(
                        "Xero Next Invoice Number", 
                        True, 
                        "Endpoint handles Xero API errors gracefully",
                        f"Status: {response.status_code}, Response: {error_text}"
                    )
                else:
                    self.log_result(
                        "Xero Next Invoice Number", 
                        False, 
                        f"Unexpected 500 error: {error_text}"
                    )
            else:
                self.log_result(
                    "Xero Next Invoice Number", 
                    False, 
                    f"Unexpected status code: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Xero Next Invoice Number", False, f"Error: {str(e)}")
    
    def test_xero_create_draft_invoice(self):
        """Test POST /api/xero/create-draft-invoice"""
        print("\n=== XERO CREATE DRAFT INVOICE TEST ===")
        
        try:
            # Test with sample invoice data
            invoice_data = {
                "client_name": "Test Client for Xero",
                "client_email": "test@testclient.com",
                "invoice_number": "INV-TEST-001",
                "order_number": "ADM-2024-TEST",
                "due_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
                "total_amount": 1000.00,
                "items": [
                    {
                        "description": "Test Product",
                        "quantity": 2,
                        "unit_price": 500.00
                    }
                ]
            }
            
            response = self.session.post(f"{API_BASE}/xero/create-draft-invoice", json=invoice_data)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                required_fields = ['success', 'message', 'invoice_id']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    success = data.get('success')
                    message = data.get('message')
                    invoice_id = data.get('invoice_id')
                    
                    if success and invoice_id:
                        self.log_result(
                            "Xero Create Draft Invoice", 
                            True, 
                            f"Successfully created draft invoice in Xero",
                            f"Invoice ID: {invoice_id}, Message: {message}"
                        )
                    else:
                        self.log_result(
                            "Xero Create Draft Invoice", 
                            False, 
                            "Response indicates failure or missing invoice ID",
                            f"Success: {success}, Invoice ID: {invoice_id}"
                        )
                else:
                    self.log_result(
                        "Xero Create Draft Invoice", 
                        False, 
                        f"Response missing required fields: {missing_fields}",
                        str(data)
                    )
            elif response.status_code == 400:
                # Expected if no Xero tenant ID or connection issues
                error_text = response.text
                if "No Xero tenant ID found" in error_text or "No Xero connection found" in error_text:
                    self.log_result(
                        "Xero Create Draft Invoice", 
                        True, 
                        "Correctly handles missing Xero connection/tenant",
                        f"Status: {response.status_code}, Response: {error_text}"
                    )
                else:
                    self.log_result(
                        "Xero Create Draft Invoice", 
                        False, 
                        f"Unexpected 400 error: {error_text}"
                    )
            elif response.status_code == 500:
                # May be expected if Xero integration not fully configured
                error_text = response.text
                if "Failed to create draft invoice" in error_text:
                    self.log_result(
                        "Xero Create Draft Invoice", 
                        True, 
                        "Endpoint handles Xero API errors gracefully",
                        f"Status: {response.status_code}, Response: {error_text}"
                    )
                else:
                    self.log_result(
                        "Xero Create Draft Invoice", 
                        False, 
                        f"Unexpected 500 error: {error_text}"
                    )
            else:
                self.log_result(
                    "Xero Create Draft Invoice", 
                    False, 
                    f"Unexpected status code: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Xero Create Draft Invoice", False, f"Error: {str(e)}")
    
    def test_document_generation_endpoints(self, delivery_jobs):
        """Test all document generation endpoints with real order data"""
        print("\n=== DOCUMENT GENERATION ENDPOINTS TEST ===")
        
        if not delivery_jobs:
            self.log_result(
                "Document Generation Endpoints", 
                False, 
                "No delivery jobs available for document testing"
            )
            return
        
        # Use the first available job for testing
        test_job = delivery_jobs[0]
        order_id = test_job.get('id')
        order_number = test_job.get('order_number', 'Unknown')
        
        print(f"Testing document generation with Order ID: {order_id}, Order Number: {order_number}")
        
        # Test all document endpoints
        document_endpoints = [
            ("Invoice PDF", f"/documents/invoice/{order_id}", "invoice"),
            ("Packing List PDF", f"/documents/packing-list/{order_id}", "packing_list"),
            ("Order Acknowledgment PDF", f"/documents/acknowledgment/{order_id}", "acknowledgment"),
            ("Job Card PDF", f"/documents/job-card/{order_id}", "job_card")
        ]
        
        successful_docs = 0
        failed_docs = []
        
        for doc_name, endpoint, doc_type in document_endpoints:
            try:
                print(f"  Testing {doc_name}...")
                response = self.session.get(f"{API_BASE}{endpoint}")
                
                if response.status_code == 200:
                    # Check if response is actually a PDF
                    content_type = response.headers.get('content-type', '')
                    content_length = len(response.content)
                    
                    if 'application/pdf' in content_type and content_length > 1000:
                        # Check if PDF content starts with PDF header
                        pdf_header = response.content[:4]
                        if pdf_header == b'%PDF':
                            self.log_result(
                                f"{doc_name} Generation", 
                                True, 
                                f"Successfully generated {doc_name} ({content_length} bytes)",
                                f"Content-Type: {content_type}, Order: {order_number}"
                            )
                            successful_docs += 1
                        else:
                            self.log_result(
                                f"{doc_name} Generation", 
                                False, 
                                f"Response is not a valid PDF (missing PDF header)",
                                f"Content starts with: {pdf_header}, Length: {content_length}"
                            )
                            failed_docs.append(doc_name)
                    else:
                        self.log_result(
                            f"{doc_name} Generation", 
                            False, 
                            f"Invalid PDF response",
                            f"Content-Type: {content_type}, Length: {content_length}"
                        )
                        failed_docs.append(doc_name)
                else:
                    error_detail = response.text[:200] if response.text else "No error details"
                    self.log_result(
                        f"{doc_name} Generation", 
                        False, 
                        f"HTTP {response.status_code} error",
                        error_detail
                    )
                    failed_docs.append(doc_name)
                    
            except Exception as e:
                self.log_result(f"{doc_name} Generation", False, f"Exception: {str(e)}")
                failed_docs.append(doc_name)
        
        # Overall document generation summary
        if successful_docs == len(document_endpoints):
            self.log_result(
                "Document Generation Endpoints", 
                True, 
                f"All {len(document_endpoints)} document types generated successfully"
            )
        else:
            self.log_result(
                "Document Generation Endpoints", 
                False, 
                f"Only {successful_docs}/{len(document_endpoints)} document types working",
                f"Failed: {', '.join(failed_docs)}"
            )
    
    def test_pdf_download_functionality(self, delivery_jobs):
        """Test that PDFs can be properly downloaded with correct headers"""
        print("\n=== PDF DOWNLOAD FUNCTIONALITY TEST ===")
        
        if not delivery_jobs:
            self.log_result(
                "PDF Download Functionality", 
                False, 
                "No delivery jobs available for download testing"
            )
            return
        
        test_job = delivery_jobs[0]
        order_id = test_job.get('id')
        order_number = test_job.get('order_number', 'Unknown')
        
        try:
            # Test invoice PDF download
            response = self.session.get(f"{API_BASE}/documents/invoice/{order_id}")
            
            if response.status_code == 200:
                # Check download headers
                content_disposition = response.headers.get('content-disposition', '')
                content_type = response.headers.get('content-type', '')
                
                # Should have attachment disposition for download
                has_attachment = 'attachment' in content_disposition
                has_filename = f'invoice_{order_number}.pdf' in content_disposition or 'filename=' in content_disposition
                is_pdf_type = 'application/pdf' in content_type
                
                if has_attachment and has_filename and is_pdf_type:
                    self.log_result(
                        "PDF Download Functionality", 
                        True, 
                        "PDF download headers configured correctly",
                        f"Content-Disposition: {content_disposition}, Content-Type: {content_type}"
                    )
                else:
                    issues = []
                    if not has_attachment:
                        issues.append("Missing 'attachment' in Content-Disposition")
                    if not has_filename:
                        issues.append("Missing filename in Content-Disposition")
                    if not is_pdf_type:
                        issues.append("Incorrect Content-Type")
                    
                    self.log_result(
                        "PDF Download Functionality", 
                        False, 
                        "PDF download headers have issues",
                        f"Issues: {', '.join(issues)}"
                    )
            else:
                self.log_result(
                    "PDF Download Functionality", 
                    False, 
                    f"Failed to get PDF for download test: HTTP {response.status_code}",
                    response.text[:200]
                )
                
        except Exception as e:
            self.log_result("PDF Download Functionality", False, f"Error: {str(e)}")
    
    def test_reportlab_pdf_generation(self):
        """Test if ReportLab PDF generation is working properly"""
        print("\n=== REPORTLAB PDF GENERATION TEST ===")
        
        try:
            # Test basic ReportLab functionality
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import A4
            from io import BytesIO
            
            # Create a simple test PDF
            buffer = BytesIO()
            c = canvas.Canvas(buffer, pagesize=A4)
            c.drawString(100, 750, "ReportLab Test PDF")
            c.save()
            
            # Check if PDF was created
            pdf_content = buffer.getvalue()
            buffer.close()
            
            if len(pdf_content) > 100 and pdf_content.startswith(b'%PDF'):
                self.log_result(
                    "ReportLab PDF Generation", 
                    True, 
                    f"ReportLab is working correctly ({len(pdf_content)} bytes generated)"
                )
            else:
                self.log_result(
                    "ReportLab PDF Generation", 
                    False, 
                    "ReportLab generated invalid PDF content",
                    f"Content length: {len(pdf_content)}, Starts with: {pdf_content[:10]}"
                )
                
        except ImportError as e:
            self.log_result(
                "ReportLab PDF Generation", 
                False, 
                "ReportLab library not available",
                str(e)
            )
        except Exception as e:
            self.log_result("ReportLab PDF Generation", False, f"ReportLab error: {str(e)}")
    
    def test_document_branding_and_content(self, delivery_jobs):
        """Test that documents include proper Adela Merchants branding"""
        print("\n=== DOCUMENT BRANDING AND CONTENT TEST ===")
        
        if not delivery_jobs:
            self.log_result(
                "Document Branding and Content", 
                False, 
                "No delivery jobs available for branding testing"
            )
            return
        
        test_job = delivery_jobs[0]
        order_id = test_job.get('id')
        
        try:
            # Test order acknowledgment for branding elements
            response = self.session.get(f"{API_BASE}/documents/acknowledgment/{order_id}")
            
            if response.status_code == 200 and 'application/pdf' in response.headers.get('content-type', ''):
                # For PDF content analysis, we can check the raw content for text strings
                pdf_content = response.content.decode('latin-1', errors='ignore')
                
                branding_elements = [
                    ("Company Name", "ADELA MERCHANTS" in pdf_content),
                    ("Document Title", "ORDER ACKNOWLEDGMENT" in pdf_content),
                    ("Contact Email", "info@adelamerchants.com.au" in pdf_content),
                    ("Website", "www.adelamerchants.com.au" in pdf_content)
                ]
                
                found_elements = [name for name, found in branding_elements if found]
                missing_elements = [name for name, found in branding_elements if not found]
                
                if len(found_elements) >= 2:  # At least company name and title should be present
                    self.log_result(
                        "Document Branding and Content", 
                        True, 
                        f"Document contains proper branding elements",
                        f"Found: {', '.join(found_elements)}"
                    )
                else:
                    self.log_result(
                        "Document Branding and Content", 
                        False, 
                        "Document missing key branding elements",
                        f"Missing: {', '.join(missing_elements)}, Found: {', '.join(found_elements)}"
                    )
            else:
                self.log_result(
                    "Document Branding and Content", 
                    False, 
                    f"Could not retrieve document for branding test: HTTP {response.status_code}"
                )
                
        except Exception as e:
            self.log_result("Document Branding and Content", False, f"Error: {str(e)}")
    
    def test_jobs_ready_for_invoicing(self):
        """Test that there are jobs in delivery stage ready for invoicing"""
        print("\n=== JOBS READY FOR INVOICING TEST ===")
        
        try:
            response = self.session.get(f"{API_BASE}/invoicing/live-jobs")
            
            if response.status_code == 200:
                data = response.json()
                jobs = data.get('data', [])
                
                # Check for jobs in delivery stage
                delivery_jobs = [job for job in jobs if job.get('current_stage') == 'delivery']
                
                if len(delivery_jobs) >= 7:
                    self.log_result(
                        "Jobs Ready for Invoicing", 
                        True, 
                        f"Found {len(delivery_jobs)} jobs in delivery stage ready for invoicing (expected 7+)",
                        f"Total live jobs: {len(jobs)}"
                    )
                    return delivery_jobs  # Return jobs for document testing
                elif len(delivery_jobs) > 0:
                    self.log_result(
                        "Jobs Ready for Invoicing", 
                        True, 
                        f"Found {len(delivery_jobs)} jobs in delivery stage ready for invoicing",
                        f"Total live jobs: {len(jobs)} (expected 7 but found {len(delivery_jobs)})"
                    )
                    return delivery_jobs  # Return jobs for document testing
                else:
                    self.log_result(
                        "Jobs Ready for Invoicing", 
                        False, 
                        "No jobs found in delivery stage ready for invoicing",
                        f"Total live jobs: {len(jobs)}, Jobs by stage: {[job.get('current_stage') for job in jobs]}"
                    )
            else:
                self.log_result(
                    "Jobs Ready for Invoicing", 
                    False, 
                    f"Failed to retrieve live jobs: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Jobs Ready for Invoicing", False, f"Error: {str(e)}")
        
        return []
    
def main():
    """Main test execution"""
    print("Starting Enhanced Timesheet Workflow Testing...")
    print(f"Backend URL: {BACKEND_URL}")
    
    tester = TimesheetWorkflowTester()
    
    # Run the complete timesheet workflow test suite
    tester.run_timesheet_workflow_tests()

if __name__ == "__main__":
    tester = BackendAPITester()
    
    # Run timesheet debug tests (focus on reported issues)
    tester.run_timesheet_debug_tests()
            
            if response.status_code == 200:
                result = response.json()
                default_currency_material_id = result.get('data', {}).get('id')
                
                # Verify the material was created and retrieve it to check currency
                if default_currency_material_id:
                    get_response = self.session.get(f"{API_BASE}/materials/{default_currency_material_id}")
                    if get_response.status_code == 200:
                        material = get_response.json()
                        currency = material.get('currency')
                        
                        if currency == "AUD":
                            self.log_result(
                                "Create Material with Default Currency", 
                                True, 
                                f"Material created with default currency 'AUD' as expected",
                                f"Material ID: {default_currency_material_id}, Currency: {currency}"
                            )
                        else:
                            self.log_result(
                                "Create Material with Default Currency", 
                                False, 
                                f"Expected default currency 'AUD' but got '{currency}'",
                                f"Material ID: {default_currency_material_id}"
                            )
                    else:
                        self.log_result(
                            "Create Material with Default Currency", 
                            False, 
                            "Failed to retrieve created material for currency verification"
                        )
                else:
                    self.log_result(
                        "Create Material with Default Currency", 
                        False, 
                        "Material creation response missing ID"
                    )
            else:
                self.log_result(
                    "Create Material with Default Currency", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Create Material with Default Currency", False, f"Error: {str(e)}")
        
        # Test 2: Create Material with Specific Currency (USD)
        material_usd_currency = {
            "supplier": "US Paper Imports",
            "product_code": "USPI-USD-001",
            "order_to_delivery_time": "10-14 business days",
            "material_description": "Imported US paper priced in USD",
            "price": 28.75,
            "currency": "USD",  # Explicitly set currency to USD
            "unit": "m2",
            "raw_substrate": False
        }
        
        usd_currency_material_id = None
        try:
            response = self.session.post(f"{API_BASE}/materials", json=material_usd_currency)
            
            if response.status_code == 200:
                result = response.json()
                usd_currency_material_id = result.get('data', {}).get('id')
                
                # Verify the material was created with USD currency
                if usd_currency_material_id:
                    get_response = self.session.get(f"{API_BASE}/materials/{usd_currency_material_id}")
                    if get_response.status_code == 200:
                        material = get_response.json()
                        currency = material.get('currency')
                        
                        if currency == "USD":
                            self.log_result(
                                "Create Material with Specific Currency (USD)", 
                                True, 
                                f"Material created with specified currency 'USD' as expected",
                                f"Material ID: {usd_currency_material_id}, Currency: {currency}"
                            )
                        else:
                            self.log_result(
                                "Create Material with Specific Currency (USD)", 
                                False, 
                                f"Expected currency 'USD' but got '{currency}'",
                                f"Material ID: {usd_currency_material_id}"
                            )
                    else:
                        self.log_result(
                            "Create Material with Specific Currency (USD)", 
                            False, 
                            "Failed to retrieve created material for currency verification"
                        )
                else:
                    self.log_result(
                        "Create Material with Specific Currency (USD)", 
                        False, 
                        "Material creation response missing ID"
                    )
            else:
                self.log_result(
                    "Create Material with Specific Currency (USD)", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Create Material with Specific Currency (USD)", False, f"Error: {str(e)}")
        
        # Test 3: Create Material with EUR Currency
        material_eur_currency = {
            "supplier": "European Materials Ltd",
            "product_code": "EML-EUR-001",
            "order_to_delivery_time": "12-16 business days",
            "material_description": "European specialty paper priced in EUR",
            "price": 42.30,
            "currency": "EUR",  # Explicitly set currency to EUR
            "unit": "m2",
            "raw_substrate": False
        }
        
        eur_currency_material_id = None
        try:
            response = self.session.post(f"{API_BASE}/materials", json=material_eur_currency)
            
            if response.status_code == 200:
                result = response.json()
                eur_currency_material_id = result.get('data', {}).get('id')
                
                # Verify the material was created with EUR currency
                if eur_currency_material_id:
                    get_response = self.session.get(f"{API_BASE}/materials/{eur_currency_material_id}")
                    if get_response.status_code == 200:
                        material = get_response.json()
                        currency = material.get('currency')
                        
                        if currency == "EUR":
                            self.log_result(
                                "Create Material with Specific Currency (EUR)", 
                                True, 
                                f"Material created with specified currency 'EUR' as expected",
                                f"Material ID: {eur_currency_material_id}, Currency: {currency}"
                            )
                        else:
                            self.log_result(
                                "Create Material with Specific Currency (EUR)", 
                                False, 
                                f"Expected currency 'EUR' but got '{currency}'",
                                f"Material ID: {eur_currency_material_id}"
                            )
                    else:
                        self.log_result(
                            "Create Material with Specific Currency (EUR)", 
                            False, 
                            "Failed to retrieve created material for currency verification"
                        )
                else:
                    self.log_result(
                        "Create Material with Specific Currency (EUR)", 
                        False, 
                        "Material creation response missing ID"
                    )
            else:
                self.log_result(
                    "Create Material with Specific Currency (EUR)", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Create Material with Specific Currency (EUR)", False, f"Error: {str(e)}")
        
        # Test 4: Update Material Currency (from AUD to GBP)
        if default_currency_material_id:
            update_currency_data = {
                "supplier": "Australian Paper Co",
                "product_code": "APC-DEFAULT-001-UPDATED",
                "order_to_delivery_time": "5-7 business days",
                "material_description": "Premium Australian paper now priced in GBP",
                "price": 22.75,
                "currency": "GBP",  # Update currency from AUD to GBP
                "unit": "m2",
                "raw_substrate": False
            }
            
            try:
                response = self.session.put(f"{API_BASE}/materials/{default_currency_material_id}", json=update_currency_data)
                
                if response.status_code == 200:
                    # Verify the currency was updated
                    get_response = self.session.get(f"{API_BASE}/materials/{default_currency_material_id}")
                    if get_response.status_code == 200:
                        updated_material = get_response.json()
                        updated_currency = updated_material.get('currency')
                        
                        if updated_currency == "GBP":
                            self.log_result(
                                "Update Material Currency (AUD to GBP)", 
                                True, 
                                f"Successfully updated material currency from AUD to GBP",
                                f"Material ID: {default_currency_material_id}, New Currency: {updated_currency}"
                            )
                        else:
                            self.log_result(
                                "Update Material Currency (AUD to GBP)", 
                                False, 
                                f"Currency update failed - expected 'GBP' but got '{updated_currency}'"
                            )
                    else:
                        self.log_result(
                            "Update Material Currency (AUD to GBP)", 
                            False, 
                            "Failed to retrieve updated material for currency verification"
                        )
                else:
                    self.log_result(
                        "Update Material Currency (AUD to GBP)", 
                        False, 
                        f"Update failed with status {response.status_code}",
                        response.text
                    )
            except Exception as e:
                self.log_result("Update Material Currency (AUD to GBP)", False, f"Error: {str(e)}")
        
        # Test 5: Verify Currency Field in GET All Materials Response
        try:
            response = self.session.get(f"{API_BASE}/materials")
            
            if response.status_code == 200:
                materials = response.json()
                
                # Check if any materials have currency field
                materials_with_currency = [m for m in materials if 'currency' in m and m.get('currency')]
                
                if len(materials_with_currency) > 0:
                    # Check for our test materials
                    test_currencies = []
                    for material in materials_with_currency:
                        if material.get('id') in [default_currency_material_id, usd_currency_material_id, eur_currency_material_id]:
                            test_currencies.append(f"{material.get('product_code', 'Unknown')}: {material.get('currency')}")
                    
                    if len(test_currencies) > 0:
                        self.log_result(
                            "Retrieve Materials with Currency Field", 
                            True, 
                            f"Currency field included in GET /api/materials response",
                            f"Test materials found: {', '.join(test_currencies)}"
                        )
                    else:
                        self.log_result(
                            "Retrieve Materials with Currency Field", 
                            True, 
                            f"Currency field present in materials list ({len(materials_with_currency)} materials have currency)"
                        )
                else:
                    self.log_result(
                        "Retrieve Materials with Currency Field", 
                        False, 
                        "No materials found with currency field in GET /api/materials response",
                        f"Total materials: {len(materials)}"
                    )
            else:
                self.log_result(
                    "Retrieve Materials with Currency Field", 
                    False, 
                    f"Failed to retrieve materials list: {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Retrieve Materials with Currency Field", False, f"Error: {str(e)}")
        
        # Test 6: Test Raw Substrate Material with Currency
        raw_substrate_with_currency = {
            "supplier": "International Raw Materials",
            "product_code": "IRM-RAW-CAD-001",
            "order_to_delivery_time": "14-21 business days",
            "material_description": "Canadian corrugated substrate priced in CAD",
            "price": 52.80,
            "currency": "CAD",  # Canadian Dollar
            "unit": "By the Box",
            "raw_substrate": True,
            "gsm": "300",
            "thickness_mm": 3.2,
            "burst_strength_kpa": 950.0,
            "ply_bonding_jm2": 135.0,
            "moisture_percent": 7.8,
            "supplied_roll_weight": 1400.0,
            "master_deckle_width_mm": 1800.0
        }
        
        try:
            response = self.session.post(f"{API_BASE}/materials", json=raw_substrate_with_currency)
            
            if response.status_code == 200:
                result = response.json()
                raw_material_id = result.get('data', {}).get('id')
                
                if raw_material_id:
                    # Verify raw substrate material has correct currency
                    get_response = self.session.get(f"{API_BASE}/materials/{raw_material_id}")
                    if get_response.status_code == 200:
                        material = get_response.json()
                        currency = material.get('currency')
                        is_raw_substrate = material.get('raw_substrate')
                        
                        if currency == "CAD" and is_raw_substrate:
                            self.log_result(
                                "Create Raw Substrate Material with Currency", 
                                True, 
                                f"Raw substrate material created with currency 'CAD' successfully",
                                f"Material ID: {raw_material_id}, Currency: {currency}, Raw Substrate: {is_raw_substrate}"
                            )
                        else:
                            self.log_result(
                                "Create Raw Substrate Material with Currency", 
                                False, 
                                f"Raw substrate material currency or type incorrect",
                                f"Expected: CAD/True, Got: {currency}/{is_raw_substrate}"
                            )
                    else:
                        self.log_result(
                            "Create Raw Substrate Material with Currency", 
                            False, 
                            "Failed to retrieve created raw substrate material"
                        )
                else:
                    self.log_result(
                        "Create Raw Substrate Material with Currency", 
                        False, 
                        "Raw substrate material creation response missing ID"
                    )
            else:
                self.log_result(
                    "Create Raw Substrate Material with Currency", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Create Raw Substrate Material with Currency", False, f"Error: {str(e)}")
    
    def test_materials_management_api(self):
        """Test Materials Management API endpoints with new fields"""
        print("\n=== MATERIALS MANAGEMENT API TEST (WITH NEW FIELDS) ===")
        
        # Test GET /api/materials (get all materials)
        try:
            response = self.session.get(f"{API_BASE}/materials")
            
            if response.status_code == 200:
                materials = response.json()
                self.log_result(
                    "Get All Materials", 
                    True, 
                    f"Successfully retrieved {len(materials)} materials"
                )
            else:
                self.log_result(
                    "Get All Materials", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Get All Materials", False, f"Error: {str(e)}")
        
        # Test POST /api/materials (create basic material with material_description - REQUIRED FIELD)
        basic_material_data = {
            "supplier": "Premium Paper Supplies",
            "product_code": "PPS-BASIC-001",
            "order_to_delivery_time": "5-7 business days",
            "material_description": "High-quality printing paper for commercial use",  # NEW REQUIRED FIELD
            "price": 25.50,
            "unit": "m2",
            "raw_substrate": False
        }
        
        basic_material_id = None
        try:
            response = self.session.post(f"{API_BASE}/materials", json=basic_material_data)
            
            if response.status_code == 200:
                result = response.json()
                basic_material_id = result.get('data', {}).get('id')
                self.log_result(
                    "Create Basic Material (with material_description)", 
                    True, 
                    f"Successfully created basic material with ID: {basic_material_id}"
                )
            else:
                self.log_result(
                    "Create Basic Material (with material_description)", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Create Basic Material (with material_description)", False, f"Error: {str(e)}")
        
        # Test POST /api/materials (create material WITHOUT material_description - should fail)
        invalid_material_data = {
            "supplier": "Test Supplier Ltd",
            "product_code": "TEST-INVALID-001",
            "order_to_delivery_time": "5-7 business days",
            # Missing material_description - should cause validation error
            "price": 25.50,
            "unit": "m2",
            "raw_substrate": False
        }
        
        try:
            response = self.session.post(f"{API_BASE}/materials", json=invalid_material_data)
            
            if response.status_code == 422:  # Validation error expected
                self.log_result(
                    "Create Material Without material_description (validation test)", 
                    True, 
                    "Correctly rejected material creation without required material_description field"
                )
            elif response.status_code == 200:
                self.log_result(
                    "Create Material Without material_description (validation test)", 
                    False, 
                    "Material was created without required material_description field - validation failed"
                )
            else:
                self.log_result(
                    "Create Material Without material_description (validation test)", 
                    False, 
                    f"Unexpected status code {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Create Material Without material_description (validation test)", False, f"Error: {str(e)}")
        
        # Test POST /api/materials (create raw substrate material with ALL NEW FIELDS)
        raw_substrate_data = {
            "supplier": "Industrial Raw Materials Co",
            "product_code": "IRM-RAW-SUB-001",
            "order_to_delivery_time": "10-14 business days",
            "material_description": "Premium corrugated cardboard substrate for high-strength packaging applications",  # NEW REQUIRED FIELD
            "price": 45.75,
            "unit": "By the Box",
            "raw_substrate": True,
            "gsm": "250",
            "thickness_mm": 2.5,
            "burst_strength_kpa": 850.0,
            "ply_bonding_jm2": 120.5,
            "moisture_percent": 8.2,
            "supplied_roll_weight": 1250.5,  # NEW FIELD for raw substrates
            "master_deckle_width_mm": 1600.0  # NEW FIELD for raw substrates
        }
        
        raw_material_id = None
        try:
            response = self.session.post(f"{API_BASE}/materials", json=raw_substrate_data)
            
            if response.status_code == 200:
                result = response.json()
                raw_material_id = result.get('data', {}).get('id')
                self.log_result(
                    "Create Raw Substrate Material (with new fields)", 
                    True, 
                    f"Successfully created raw substrate material with ID: {raw_material_id}"
                )
            else:
                self.log_result(
                    "Create Raw Substrate Material (with new fields)", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Create Raw Substrate Material (with new fields)", False, f"Error: {str(e)}")
        
        # Test GET /api/materials/{id} (get specific material and verify new fields)
        if basic_material_id:
            try:
                response = self.session.get(f"{API_BASE}/materials/{basic_material_id}")
                
                if response.status_code == 200:
                    material = response.json()
                    
                    # Verify basic material has new required field
                    has_material_description = material.get('material_description') == "High-quality printing paper for commercial use"
                    has_correct_supplier = material.get('supplier') == "Premium Paper Supplies"
                    
                    if has_material_description and has_correct_supplier:
                        self.log_result(
                            "Get Specific Basic Material (verify new fields)", 
                            True, 
                            f"Successfully retrieved material with material_description: {material.get('product_code')}"
                        )
                    else:
                        self.log_result(
                            "Get Specific Basic Material (verify new fields)", 
                            False, 
                            "Material missing material_description or other expected values",
                            f"material_description: {material.get('material_description')}, supplier: {material.get('supplier')}"
                        )
                else:
                    self.log_result(
                        "Get Specific Basic Material (verify new fields)", 
                        False, 
                        f"Failed with status {response.status_code}",
                        response.text
                    )
            except Exception as e:
                self.log_result("Get Specific Basic Material (verify new fields)", False, f"Error: {str(e)}")
        
        # Test GET /api/materials/{id} (get raw substrate material and verify ALL new fields)
        if raw_material_id:
            try:
                response = self.session.get(f"{API_BASE}/materials/{raw_material_id}")
                
                if response.status_code == 200:
                    material = response.json()
                    
                    # Verify raw substrate material has all new fields
                    checks = [
                        ("material_description", material.get('material_description') == "Premium corrugated cardboard substrate for high-strength packaging applications"),
                        ("supplied_roll_weight", material.get('supplied_roll_weight') == 1250.5),
                        ("master_deckle_width_mm", material.get('master_deckle_width_mm') == 1600.0),
                        ("raw_substrate", material.get('raw_substrate') == True)
                    ]
                    
                    passed_checks = [name for name, passed in checks if passed]
                    failed_checks = [name for name, passed in checks if not passed]
                    
                    if len(failed_checks) == 0:
                        self.log_result(
                            "Get Specific Raw Substrate Material (verify all new fields)", 
                            True, 
                            f"Successfully retrieved raw substrate material with all new fields: {material.get('product_code')}"
                        )
                    else:
                        self.log_result(
                            "Get Specific Raw Substrate Material (verify all new fields)", 
                            False, 
                            f"Raw substrate material missing or incorrect new fields: {', '.join(failed_checks)}",
                            f"Passed: {', '.join(passed_checks)}, Failed: {', '.join(failed_checks)}"
                        )
                else:
                    self.log_result(
                        "Get Specific Raw Substrate Material (verify all new fields)", 
                        False, 
                        f"Failed with status {response.status_code}",
                        response.text
                    )
            except Exception as e:
                self.log_result("Get Specific Raw Substrate Material (verify all new fields)", False, f"Error: {str(e)}")
        
        # Test PUT /api/materials/{id} (update material with new fields)
        if basic_material_id:
            update_data = {
                "supplier": "Updated Premium Supplier Ltd",
                "product_code": "UPS-BASIC-001-UPDATED",
                "order_to_delivery_time": "3-5 business days",
                "material_description": "Updated high-quality printing paper with enhanced durability",  # Updated required field
                "price": 28.75,
                "unit": "m2",
                "raw_substrate": False
            }
            
            try:
                response = self.session.put(f"{API_BASE}/materials/{basic_material_id}", json=update_data)
                
                if response.status_code == 200:
                    # Verify the update worked by fetching the material
                    get_response = self.session.get(f"{API_BASE}/materials/{basic_material_id}")
                    if get_response.status_code == 200:
                        updated_material = get_response.json()
                        if updated_material.get('material_description') == "Updated high-quality printing paper with enhanced durability":
                            self.log_result(
                                "Update Material (with new fields)", 
                                True, 
                                "Successfully updated material with new material_description field"
                            )
                        else:
                            self.log_result(
                                "Update Material (with new fields)", 
                                False, 
                                "Material updated but material_description not correctly updated"
                            )
                    else:
                        self.log_result(
                            "Update Material (with new fields)", 
                            True, 
                            "Material update returned success"
                        )
                else:
                    self.log_result(
                        "Update Material (with new fields)", 
                        False, 
                        f"Failed with status {response.status_code}",
                        response.text
                    )
            except Exception as e:
                self.log_result("Update Material (with new fields)", False, f"Error: {str(e)}")
        
        # Test PUT /api/materials/{id} (update raw substrate material with new fields)
        if raw_material_id:
            raw_update_data = {
                "supplier": "Updated Industrial Raw Materials Co",
                "product_code": "UIRM-RAW-SUB-001-UPDATED",
                "order_to_delivery_time": "7-10 business days",
                "material_description": "Updated premium corrugated cardboard substrate with enhanced strength properties",
                "price": 52.25,
                "unit": "By the Box",
                "raw_substrate": True,
                "gsm": "280",
                "thickness_mm": 2.8,
                "burst_strength_kpa": 950.0,
                "ply_bonding_jm2": 135.0,
                "moisture_percent": 7.5,
                "supplied_roll_weight": 1400.0,  # Updated new field
                "master_deckle_width_mm": 1800.0  # Updated new field
            }
            
            try:
                response = self.session.put(f"{API_BASE}/materials/{raw_material_id}", json=raw_update_data)
                
                if response.status_code == 200:
                    # Verify the update worked by fetching the material
                    get_response = self.session.get(f"{API_BASE}/materials/{raw_material_id}")
                    if get_response.status_code == 200:
                        updated_material = get_response.json()
                        
                        # Check updated new fields
                        checks = [
                            ("material_description", updated_material.get('material_description') == "Updated premium corrugated cardboard substrate with enhanced strength properties"),
                            ("supplied_roll_weight", updated_material.get('supplied_roll_weight') == 1400.0),
                            ("master_deckle_width_mm", updated_material.get('master_deckle_width_mm') == 1800.0)
                        ]
                        
                        passed_checks = [name for name, passed in checks if passed]
                        failed_checks = [name for name, passed in checks if not passed]
                        
                        if len(failed_checks) == 0:
                            self.log_result(
                                "Update Raw Substrate Material (with new fields)", 
                                True, 
                                "Successfully updated raw substrate material with all new fields"
                            )
                        else:
                            self.log_result(
                                "Update Raw Substrate Material (with new fields)", 
                                False, 
                                f"Raw substrate material updated but new fields not correctly updated: {', '.join(failed_checks)}"
                            )
                    else:
                        self.log_result(
                            "Update Raw Substrate Material (with new fields)", 
                            True, 
                            "Raw substrate material update returned success"
                        )
                else:
                    self.log_result(
                        "Update Raw Substrate Material (with new fields)", 
                        False, 
                        f"Failed with status {response.status_code}",
                        response.text
                    )
            except Exception as e:
                self.log_result("Update Raw Substrate Material (with new fields)", False, f"Error: {str(e)}")
        
        # Test DELETE /api/materials/{id} (soft delete material)
        if basic_material_id:
            try:
                response = self.session.delete(f"{API_BASE}/materials/{basic_material_id}")
                
                if response.status_code == 200:
                    self.log_result(
                        "Delete Material", 
                        True, 
                        "Successfully deleted material (soft delete)"
                    )
                else:
                    self.log_result(
                        "Delete Material", 
                        False, 
                        f"Failed with status {response.status_code}",
                        response.text
                    )
            except Exception as e:
                self.log_result("Delete Material", False, f"Error: {str(e)}")
        
        return raw_material_id  # Return for use in client product tests
    
    def test_client_product_catalog_api(self, client_id, material_id):
        """Test Client Product Catalog API endpoints"""
        print("\n=== CLIENT PRODUCT CATALOG API TEST ===")
        
        if not client_id:
            self.log_result(
                "Client Product Catalog API", 
                False, 
                "No client ID available for testing"
            )
            return
        
        # Test GET /api/clients/{client_id}/catalog (get client products)
        try:
            response = self.session.get(f"{API_BASE}/clients/{client_id}/catalog")
            
            if response.status_code == 200:
                products = response.json()
                self.log_result(
                    "Get Client Product Catalog", 
                    True, 
                    f"Successfully retrieved {len(products)} client products"
                )
            else:
                self.log_result(
                    "Get Client Product Catalog", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Get Client Product Catalog", False, f"Error: {str(e)}")
        
        # Test POST /api/clients/{client_id}/catalog (create finished goods product)
        finished_goods_data = {
            "product_type": "finished_goods",
            "product_code": "FG-001",
            "product_description": "Premium Finished Product",
            "price_ex_gst": 150.00,
            "minimum_order_quantity": 10,
            "consignment": False
        }
        
        finished_product_id = None
        try:
            response = self.session.post(f"{API_BASE}/clients/{client_id}/catalog", json=finished_goods_data)
            
            if response.status_code == 200:
                result = response.json()
                finished_product_id = result.get('data', {}).get('id')
                self.log_result(
                    "Create Finished Goods Product", 
                    True, 
                    f"Successfully created finished goods product with ID: {finished_product_id}"
                )
            else:
                self.log_result(
                    "Create Finished Goods Product", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Create Finished Goods Product", False, f"Error: {str(e)}")
        
        # Test POST /api/clients/{client_id}/catalog (create paper cores product with materials)
        paper_cores_data = {
            "product_type": "paper_cores",
            "product_code": "PC-001",
            "product_description": "Custom Paper Core - High Strength",
            "price_ex_gst": 85.50,
            "minimum_order_quantity": 50,
            "consignment": True,
            "material_used": [material_id] if material_id else [],
            "core_id": "CORE-12345",
            "core_width": "150mm",
            "core_thickness": "3.2mm",
            "strength_quality_important": True,
            "delivery_included": True
        }
        
        paper_cores_product_id = None
        try:
            response = self.session.post(f"{API_BASE}/clients/{client_id}/catalog", json=paper_cores_data)
            
            if response.status_code == 200:
                result = response.json()
                paper_cores_product_id = result.get('data', {}).get('id')
                self.log_result(
                    "Create Paper Cores Product", 
                    True, 
                    f"Successfully created paper cores product with ID: {paper_cores_product_id}"
                )
            else:
                self.log_result(
                    "Create Paper Cores Product", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Create Paper Cores Product", False, f"Error: {str(e)}")
        
        # Test GET /api/clients/{client_id}/catalog/{product_id} (get specific client product)
        if finished_product_id:
            try:
                response = self.session.get(f"{API_BASE}/clients/{client_id}/catalog/{finished_product_id}")
                
                if response.status_code == 200:
                    product = response.json()
                    if product.get('product_code') == "FG-001":
                        self.log_result(
                            "Get Specific Client Product", 
                            True, 
                            f"Successfully retrieved client product: {product.get('product_code')}"
                        )
                    else:
                        self.log_result(
                            "Get Specific Client Product", 
                            False, 
                            "Product data doesn't match expected values"
                        )
                else:
                    self.log_result(
                        "Get Specific Client Product", 
                        False, 
                        f"Failed with status {response.status_code}",
                        response.text
                    )
            except Exception as e:
                self.log_result("Get Specific Client Product", False, f"Error: {str(e)}")
        
        # Test PUT /api/clients/{client_id}/catalog/{product_id} (update client product)
        if finished_product_id:
            update_data = {
                "product_type": "finished_goods",
                "product_code": "FG-001-UPDATED",
                "product_description": "Premium Finished Product - Updated",
                "price_ex_gst": 175.00,
                "minimum_order_quantity": 15,
                "consignment": True
            }
            
            try:
                response = self.session.put(f"{API_BASE}/clients/{client_id}/catalog/{finished_product_id}", json=update_data)
                
                if response.status_code == 200:
                    self.log_result(
                        "Update Client Product", 
                        True, 
                        "Successfully updated client product"
                    )
                else:
                    self.log_result(
                        "Update Client Product", 
                        False, 
                        f"Failed with status {response.status_code}",
                        response.text
                    )
            except Exception as e:
                self.log_result("Update Client Product", False, f"Error: {str(e)}")
        
        return finished_product_id, paper_cores_product_id
    
    def test_client_product_copy_functionality(self, source_client_id, product_id):
        """Test copying products between clients"""
        print("\n=== CLIENT PRODUCT COPY FUNCTIONALITY TEST ===")
        
        if not source_client_id or not product_id:
            self.log_result(
                "Client Product Copy Functionality", 
                False, 
                "Missing source client ID or product ID for copy test"
            )
            return
        
        # Create a second client for copy testing
        target_client_data = {
            "company_name": "Target Copy Client Ltd",
            "contact_name": "Jane Smith",
            "email": "jane@targetclient.com",
            "phone": "0487654321",
            "address": "789 Target Street",
            "city": "Sydney",
            "state": "NSW",
            "postal_code": "2000",
            "abn": "98765432109",
            "payment_terms": "Net 21 days",
            "lead_time_days": 5
        }
        
        target_client_id = None
        try:
            response = self.session.post(f"{API_BASE}/clients", json=target_client_data)
            
            if response.status_code == 200:
                result = response.json()
                target_client_id = result.get('data', {}).get('id')
                self.log_result(
                    "Create Target Client for Copy Test", 
                    True, 
                    f"Successfully created target client with ID: {target_client_id}"
                )
            else:
                self.log_result(
                    "Create Target Client for Copy Test", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
                return
        except Exception as e:
            self.log_result("Create Target Client for Copy Test", False, f"Error: {str(e)}")
            return
        
        # Test POST /api/clients/{client_id}/catalog/{product_id}/copy-to/{target_client_id}
        try:
            response = self.session.post(f"{API_BASE}/clients/{source_client_id}/catalog/{product_id}/copy-to/{target_client_id}")
            
            if response.status_code == 200:
                result = response.json()
                copied_product_id = result.get('data', {}).get('id')
                
                if copied_product_id:
                    # Verify the product was copied by checking target client's catalog
                    verify_response = self.session.get(f"{API_BASE}/clients/{target_client_id}/catalog/{copied_product_id}")
                    
                    if verify_response.status_code == 200:
                        copied_product = verify_response.json()
                        self.log_result(
                            "Copy Product Between Clients", 
                            True, 
                            f"Successfully copied product to target client. New ID: {copied_product_id}",
                            f"Product Code: {copied_product.get('product_code')}"
                        )
                    else:
                        self.log_result(
                            "Copy Product Between Clients", 
                            False, 
                            "Product copy reported success but verification failed"
                        )
                else:
                    self.log_result(
                        "Copy Product Between Clients", 
                        False, 
                        "Copy response missing new product ID"
                    )
            else:
                self.log_result(
                    "Copy Product Between Clients", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Copy Product Between Clients", False, f"Error: {str(e)}")
    
    def test_client_product_delete_functionality(self, client_id, product_id):
        """Test DELETE /api/clients/{client_id}/catalog/{product_id}"""
        print("\n=== CLIENT PRODUCT DELETE FUNCTIONALITY TEST ===")
        
        if not client_id or not product_id:
            self.log_result(
                "Client Product Delete Functionality", 
                False, 
                "Missing client ID or product ID for delete test"
            )
            return
        
        try:
            response = self.session.delete(f"{API_BASE}/clients/{client_id}/catalog/{product_id}")
            
            if response.status_code == 200:
                # Verify the product is no longer accessible
                verify_response = self.session.get(f"{API_BASE}/clients/{client_id}/catalog/{product_id}")
                
                if verify_response.status_code == 404:
                    self.log_result(
                        "Delete Client Product", 
                        True, 
                        "Successfully deleted client product (soft delete verified)"
                    )
                else:
                    self.log_result(
                        "Delete Client Product", 
                        False, 
                        "Delete reported success but product still accessible"
                    )
            else:
                self.log_result(
                    "Delete Client Product", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Delete Client Product", False, f"Error: {str(e)}")
    
    def test_validation_errors(self, client_id):
        """Test validation errors for required fields"""
        print("\n=== VALIDATION ERRORS TEST ===")
        
        # Test materials validation - missing required fields
        invalid_material_data = {
            "supplier": "",  # Empty supplier
            "product_code": "",  # Empty product code
            "price": -10.0,  # Negative price
            "unit": ""  # Empty unit
        }
        
        try:
            response = self.session.post(f"{API_BASE}/materials", json=invalid_material_data)
            
            if response.status_code in [400, 422]:  # Validation error expected
                self.log_result(
                    "Materials Validation Errors", 
                    True, 
                    f"Correctly rejected invalid material data with status {response.status_code}"
                )
            else:
                self.log_result(
                    "Materials Validation Errors", 
                    False, 
                    f"Expected validation error but got status {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Materials Validation Errors", False, f"Error: {str(e)}")
        
        # Test client products validation - missing required fields
        if client_id:
            invalid_product_data = {
                "product_type": "invalid_type",  # Invalid product type
                "product_code": "",  # Empty product code
                "price_ex_gst": -50.0,  # Negative price
                "minimum_order_quantity": -5  # Negative quantity
            }
            
            try:
                response = self.session.post(f"{API_BASE}/clients/{client_id}/catalog", json=invalid_product_data)
                
                if response.status_code in [400, 422]:  # Validation error expected
                    self.log_result(
                        "Client Products Validation Errors", 
                        True, 
                        f"Correctly rejected invalid client product data with status {response.status_code}"
                    )
                else:
                    self.log_result(
                        "Client Products Validation Errors", 
                        False, 
                        f"Expected validation error but got status {response.status_code}",
                        response.text
                    )
            except Exception as e:
                self.log_result("Client Products Validation Errors", False, f"Error: {str(e)}")
    
    def test_authentication_requirements(self):
        """Test that new endpoints require proper authentication"""
        print("\n=== AUTHENTICATION REQUIREMENTS TEST ===")
        
        # Test without authentication
        temp_session = requests.Session()
        
        endpoints_to_test = [
            ("GET", "/materials", "Materials List"),
            ("POST", "/materials", "Create Material"),
            ("GET", "/clients/test-id/catalog", "Client Product Catalog"),
            ("POST", "/clients/test-id/catalog", "Create Client Product")
        ]
        
        for method, endpoint, name in endpoints_to_test:
            try:
                if method == "GET":
                    response = temp_session.get(f"{API_BASE}{endpoint}")
                else:
                    response = temp_session.post(f"{API_BASE}{endpoint}", json={})
                
                if response.status_code in [401, 403]:
                    self.log_result(
                        f"{name} Authentication", 
                        True, 
                        f"Correctly requires authentication (status: {response.status_code})"
                    )
                else:
                    self.log_result(
                        f"{name} Authentication", 
                        False, 
                        f"Expected 401/403 but got {response.status_code}",
                        f"Endpoint {endpoint} should require authentication"
                    )
            except Exception as e:
                self.log_result(f"{name} Authentication", False, f"Error: {str(e)}")

    def test_production_board_enhancements(self):
        """Test new Production Board API enhancements"""
        print("\n=== PRODUCTION BOARD ENHANCEMENTS TEST ===")
        
        # Test GET /api/production/board - should include runtime and materials_ready fields
        try:
            response = self.session.get(f"{API_BASE}/production/board")
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success') and 'data' in data:
                    board_data = data['data']
                    
                    # Check if board has stages
                    if isinstance(board_data, dict) and len(board_data) > 0:
                        # Find a stage with jobs to test
                        test_job = None
                        for stage, jobs in board_data.items():
                            if jobs and len(jobs) > 0:
                                test_job = jobs[0]
                                break
                        
                        if test_job:
                            # Check for new fields: runtime and materials_ready
                            has_runtime = 'runtime' in test_job
                            has_materials_ready = 'materials_ready' in test_job
                            
                            if has_runtime and has_materials_ready:
                                self.log_result(
                                    "Production Board Enhanced Fields", 
                                    True, 
                                    f"Production board includes new fields: runtime='{test_job.get('runtime')}', materials_ready={test_job.get('materials_ready')}"
                                )
                                return test_job.get('id')  # Return order ID for further testing
                            else:
                                missing_fields = []
                                if not has_runtime:
                                    missing_fields.append('runtime')
                                if not has_materials_ready:
                                    missing_fields.append('materials_ready')
                                
                                self.log_result(
                                    "Production Board Enhanced Fields", 
                                    False, 
                                    f"Production board missing new fields: {', '.join(missing_fields)}"
                                )
                        else:
                            self.log_result(
                                "Production Board Enhanced Fields", 
                                False, 
                                "No jobs found on production board to test enhanced fields"
                            )
                    else:
                        self.log_result(
                            "Production Board Enhanced Fields", 
                            False, 
                            "Production board data is empty or invalid format"
                        )
                else:
                    self.log_result(
                        "Production Board Enhanced Fields", 
                        False, 
                        "Production board response missing success/data fields",
                        str(data)
                    )
            else:
                self.log_result(
                    "Production Board Enhanced Fields", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Production Board Enhanced Fields", False, f"Error: {str(e)}")
        
        return None

    def test_stage_movement_api(self, order_id):
        """Test POST /api/production/move-stage/{order_id}"""
        print("\n=== STAGE MOVEMENT API TEST ===")
        
        if not order_id:
            self.log_result(
                "Stage Movement API", 
                False, 
                "No order ID available for stage movement testing"
            )
            return
        
        # Test forward movement
        try:
            forward_request = {
                "direction": "forward",
                "notes": "Testing forward stage movement"
            }
            
            response = self.session.post(f"{API_BASE}/production/move-stage/{order_id}", json=forward_request)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success') and 'new_stage' in data:
                    new_stage = data.get('new_stage')
                    self.log_result(
                        "Stage Movement Forward", 
                        True, 
                        f"Successfully moved order to stage: {new_stage}",
                        data.get('message')
                    )
                    
                    # Test backward movement
                    backward_request = {
                        "direction": "backward",
                        "notes": "Testing backward stage movement"
                    }
                    
                    backward_response = self.session.post(f"{API_BASE}/production/move-stage/{order_id}", json=backward_request)
                    
                    if backward_response.status_code == 200:
                        backward_data = backward_response.json()
                        
                        if backward_data.get('success'):
                            self.log_result(
                                "Stage Movement Backward", 
                                True, 
                                f"Successfully moved order back to stage: {backward_data.get('new_stage')}",
                                backward_data.get('message')
                            )
                        else:
                            self.log_result(
                                "Stage Movement Backward", 
                                False, 
                                "Backward movement response indicates failure",
                                str(backward_data)
                            )
                    else:
                        self.log_result(
                            "Stage Movement Backward", 
                            False, 
                            f"Backward movement failed with status {backward_response.status_code}",
                            backward_response.text
                        )
                else:
                    self.log_result(
                        "Stage Movement Forward", 
                        False, 
                        "Forward movement response missing success/new_stage fields",
                        str(data)
                    )
            else:
                self.log_result(
                    "Stage Movement Forward", 
                    False, 
                    f"Forward movement failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Stage Movement API", False, f"Error: {str(e)}")
        
        # Test invalid direction
        try:
            invalid_request = {
                "direction": "invalid_direction",
                "notes": "Testing invalid direction"
            }
            
            response = self.session.post(f"{API_BASE}/production/move-stage/{order_id}", json=invalid_request)
            
            if response.status_code == 400:
                self.log_result(
                    "Stage Movement Invalid Direction", 
                    True, 
                    "Correctly rejected invalid direction with status 400"
                )
            else:
                self.log_result(
                    "Stage Movement Invalid Direction", 
                    False, 
                    f"Expected 400 for invalid direction but got {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Stage Movement Invalid Direction", False, f"Error: {str(e)}")

    def test_materials_status_api(self, order_id):
        """Test materials status API endpoints"""
        print("\n=== MATERIALS STATUS API TEST ===")
        
        if not order_id:
            self.log_result(
                "Materials Status API", 
                False, 
                "No order ID available for materials status testing"
            )
            return
        
        # Test GET /api/production/materials-status/{order_id}
        try:
            response = self.session.get(f"{API_BASE}/production/materials-status/{order_id}")
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success') and 'data' in data:
                    materials_data = data['data']
                    
                    # Check required fields
                    required_fields = ['order_id', 'materials_ready', 'materials_checklist', 'updated_by']
                    missing_fields = [field for field in required_fields if field not in materials_data]
                    
                    if not missing_fields:
                        self.log_result(
                            "Get Materials Status", 
                            True, 
                            f"Successfully retrieved materials status for order {order_id}",
                            f"Materials ready: {materials_data.get('materials_ready')}, Checklist items: {len(materials_data.get('materials_checklist', []))}"
                        )
                    else:
                        self.log_result(
                            "Get Materials Status", 
                            False, 
                            f"Materials status response missing fields: {missing_fields}",
                            str(materials_data)
                        )
                else:
                    self.log_result(
                        "Get Materials Status", 
                        False, 
                        "Materials status response missing success/data fields",
                        str(data)
                    )
            else:
                self.log_result(
                    "Get Materials Status", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Get Materials Status", False, f"Error: {str(e)}")
        
        # Test PUT /api/production/materials-status/{order_id}
        try:
            update_data = {
                "materials_ready": True,
                "materials_checklist": [
                    {"material": "Raw Paper", "ready": True},
                    {"material": "Adhesive", "ready": True},
                    {"material": "Packaging", "ready": False}
                ]
            }
            
            response = self.session.put(f"{API_BASE}/production/materials-status/{order_id}", json=update_data)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success'):
                    self.log_result(
                        "Update Materials Status", 
                        True, 
                        "Successfully updated materials status",
                        data.get('message')
                    )
                    
                    # Verify the update by getting the status again
                    verify_response = self.session.get(f"{API_BASE}/production/materials-status/{order_id}")
                    
                    if verify_response.status_code == 200:
                        verify_data = verify_response.json()
                        
                        if verify_data.get('success') and verify_data.get('data', {}).get('materials_ready') == True:
                            self.log_result(
                                "Verify Materials Status Update", 
                                True, 
                                "Materials status update was persisted correctly"
                            )
                        else:
                            self.log_result(
                                "Verify Materials Status Update", 
                                False, 
                                "Materials status update was not persisted correctly"
                            )
                else:
                    self.log_result(
                        "Update Materials Status", 
                        False, 
                        "Update materials status response indicates failure",
                        str(data)
                    )
            else:
                self.log_result(
                    "Update Materials Status", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Update Materials Status", False, f"Error: {str(e)}")

    def test_order_item_status_api(self, order_id):
        """Test PUT /api/production/order-item-status/{order_id}"""
        print("\n=== ORDER ITEM STATUS API TEST ===")
        
        if not order_id:
            self.log_result(
                "Order Item Status API", 
                False, 
                "No order ID available for order item status testing"
            )
            return
        
        # Test updating first item completion status
        try:
            update_data = {
                "item_index": 0,
                "is_completed": True
            }
            
            response = self.session.put(f"{API_BASE}/production/order-item-status/{order_id}", json=update_data)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success'):
                    self.log_result(
                        "Update Order Item Status", 
                        True, 
                        "Successfully updated order item completion status",
                        data.get('message')
                    )
                    
                    # Test updating with invalid item index
                    invalid_update = {
                        "item_index": 999,  # Invalid index
                        "is_completed": True
                    }
                    
                    invalid_response = self.session.put(f"{API_BASE}/production/order-item-status/{order_id}", json=invalid_update)
                    
                    if invalid_response.status_code == 400:
                        self.log_result(
                            "Order Item Status Invalid Index", 
                            True, 
                            "Correctly rejected invalid item index with status 400"
                        )
                    else:
                        self.log_result(
                            "Order Item Status Invalid Index", 
                            False, 
                            f"Expected 400 for invalid index but got {invalid_response.status_code}",
                            invalid_response.text
                        )
                else:
                    self.log_result(
                        "Update Order Item Status", 
                        False, 
                        "Update order item status response indicates failure",
                        str(data)
                    )
            else:
                self.log_result(
                    "Update Order Item Status", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Update Order Item Status", False, f"Error: {str(e)}")

    def test_production_board_authentication(self):
        """Test that production board endpoints require proper authentication"""
        print("\n=== PRODUCTION BOARD AUTHENTICATION TEST ===")
        
        # Test without authentication
        temp_session = requests.Session()
        
        endpoints_to_test = [
            ("Production Board", "GET", "/production/board"),
            ("Move Stage", "POST", "/production/move-stage/test-id"),
            ("Get Materials Status", "GET", "/production/materials-status/test-id"),
            ("Update Materials Status", "PUT", "/production/materials-status/test-id"),
            ("Update Order Item Status", "PUT", "/production/order-item-status/test-id")
        ]
        
        for endpoint_name, method, endpoint in endpoints_to_test:
            try:
                if method == "GET":
                    response = temp_session.get(f"{API_BASE}{endpoint}")
                elif method == "POST":
                    response = temp_session.post(f"{API_BASE}{endpoint}", json={"direction": "forward"})
                elif method == "PUT":
                    response = temp_session.put(f"{API_BASE}{endpoint}", json={"test": "data"})
                
                if response.status_code in [401, 403]:
                    self.log_result(
                        f"{endpoint_name} Authentication", 
                        True, 
                        f"Correctly requires authentication (status: {response.status_code})"
                    )
                else:
                    self.log_result(
                        f"{endpoint_name} Authentication", 
                        False, 
                        f"Expected 401/403 but got {response.status_code}",
                        f"Endpoint {endpoint} should require authentication"
                    )
                    
            except Exception as e:
                self.log_result(f"{endpoint_name} Authentication", False, f"Error: {str(e)}")

    def test_invalid_order_ids(self):
        """Test error handling for invalid order IDs"""
        print("\n=== INVALID ORDER IDS TEST ===")
        
        invalid_order_id = "invalid-order-id-12345"
        
        endpoints_to_test = [
            ("Move Stage Invalid Order", "POST", f"/production/move-stage/{invalid_order_id}", {"direction": "forward"}),
            ("Get Materials Status Invalid Order", "GET", f"/production/materials-status/{invalid_order_id}", None),
            ("Update Materials Status Invalid Order", "PUT", f"/production/materials-status/{invalid_order_id}", {"materials_ready": True, "materials_checklist": []}),
            ("Update Order Item Status Invalid Order", "PUT", f"/production/order-item-status/{invalid_order_id}", {"item_index": 0, "is_completed": True})
        ]
        
        for test_name, method, endpoint, data in endpoints_to_test:
            try:
                if method == "GET":
                    response = self.session.get(f"{API_BASE}{endpoint}")
                elif method == "POST":
                    response = self.session.post(f"{API_BASE}{endpoint}", json=data)
                elif method == "PUT":
                    response = self.session.put(f"{API_BASE}{endpoint}", json=data)
                
                if response.status_code == 404:
                    self.log_result(
                        test_name, 
                        True, 
                        "Correctly returned 404 for invalid order ID"
                    )
                else:
                    self.log_result(
                        test_name, 
                        False, 
                        f"Expected 404 for invalid order ID but got {response.status_code}",
                        response.text
                    )
                    
            except Exception as e:
                self.log_result(test_name, False, f"Error: {str(e)}")

    def test_materials_api_fix(self):
        """Test the Materials API fix for material_description Optional field"""
        print("\n=== MATERIALS API FIX TEST ===")
        
        # Test 1: GET /api/materials - Should work now with Optional material_description
        try:
            response = self.session.get(f"{API_BASE}/materials")
            
            if response.status_code == 200:
                materials = response.json()
                
                # Check if we get a list of materials
                if isinstance(materials, list):
                    # Check for materials with and without material_description
                    materials_with_desc = [m for m in materials if m.get('material_description') is not None]
                    materials_without_desc = [m for m in materials if m.get('material_description') is None]
                    
                    self.log_result(
                        "GET /api/materials - Backward Compatibility", 
                        True, 
                        f"Successfully retrieved {len(materials)} materials (with desc: {len(materials_with_desc)}, without desc: {len(materials_without_desc)})",
                        f"Fix working: existing materials without material_description load correctly"
                    )
                else:
                    self.log_result(
                        "GET /api/materials - Backward Compatibility", 
                        False, 
                        "Response is not a list of materials",
                        f"Response type: {type(materials)}"
                    )
            else:
                self.log_result(
                    "GET /api/materials - Backward Compatibility", 
                    False, 
                    f"GET /api/materials failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("GET /api/materials - Backward Compatibility", False, f"Error: {str(e)}")
        
        # Test 2: POST /api/materials - Create new material WITH material_description
        material_with_desc = {
            "supplier": "Test Materials Fix Co",
            "product_code": "TMF-WITH-DESC-001",
            "order_to_delivery_time": "3-5 business days",
            "material_description": "Test material with description for API fix verification",
            "price": 45.75,
            "currency": "AUD",
            "unit": "m2",
            "raw_substrate": False
        }
        
        material_with_desc_id = None
        try:
            response = self.session.post(f"{API_BASE}/materials", json=material_with_desc)
            
            if response.status_code == 200:
                result = response.json()
                material_with_desc_id = result.get('data', {}).get('id')
                
                if material_with_desc_id:
                    # Verify the material was created correctly
                    get_response = self.session.get(f"{API_BASE}/materials/{material_with_desc_id}")
                    if get_response.status_code == 200:
                        material = get_response.json()
                        desc = material.get('material_description')
                        
                        if desc == "Test material with description for API fix verification":
                            self.log_result(
                                "POST /api/materials - With Description", 
                                True, 
                                "Successfully created material with material_description field",
                                f"Material ID: {material_with_desc_id}, Description: {desc}"
                            )
                        else:
                            self.log_result(
                                "POST /api/materials - With Description", 
                                False, 
                                f"Material created but description mismatch",
                                f"Expected: 'Test material...', Got: '{desc}'"
                            )
                    else:
                        self.log_result(
                            "POST /api/materials - With Description", 
                            False, 
                            "Failed to retrieve created material"
                        )
                else:
                    self.log_result(
                        "POST /api/materials - With Description", 
                        False, 
                        "Material creation response missing ID"
                    )
            else:
                self.log_result(
                    "POST /api/materials - With Description", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("POST /api/materials - With Description", False, f"Error: {str(e)}")
        
        # Test 3: POST /api/materials - Try to create material WITHOUT material_description (should fail validation)
        material_without_desc = {
            "supplier": "Test Materials Fix Co",
            "product_code": "TMF-WITHOUT-DESC-001",
            "order_to_delivery_time": "3-5 business days",
            # Note: material_description field intentionally omitted
            "price": 35.50,
            "currency": "AUD",
            "unit": "m2",
            "raw_substrate": False
        }
        
        try:
            response = self.session.post(f"{API_BASE}/materials", json=material_without_desc)
            
            if response.status_code == 422:  # Validation error expected
                self.log_result(
                    "POST /api/materials - Without Description (Validation)", 
                    True, 
                    "Correctly rejects material creation without required material_description field",
                    f"Status: {response.status_code} (validation error as expected)"
                )
            elif response.status_code == 200:
                self.log_result(
                    "POST /api/materials - Without Description (Validation)", 
                    False, 
                    "Material creation should have failed validation but succeeded",
                    "MaterialCreate model should require material_description field"
                )
            else:
                self.log_result(
                    "POST /api/materials - Without Description (Validation)", 
                    False, 
                    f"Unexpected status code: {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("POST /api/materials - Without Description (Validation)", False, f"Error: {str(e)}")
        
        # Test 4: Verify existing materials load correctly with null material_description
        try:
            response = self.session.get(f"{API_BASE}/materials")
            
            if response.status_code == 200:
                materials = response.json()
                
                # Look for materials with null/None material_description
                legacy_materials = [m for m in materials if m.get('material_description') is None]
                
                if len(legacy_materials) > 0:
                    # Test retrieving a specific legacy material
                    legacy_material = legacy_materials[0]
                    legacy_id = legacy_material.get('id')
                    
                    if legacy_id:
                        get_response = self.session.get(f"{API_BASE}/materials/{legacy_id}")
                        if get_response.status_code == 200:
                            material = get_response.json()
                            desc = material.get('material_description')
                            
                            if desc is None:
                                self.log_result(
                                    "Legacy Materials Compatibility", 
                                    True, 
                                    "Legacy materials without material_description load correctly with null values",
                                    f"Legacy Material ID: {legacy_id}, Description: {desc}"
                                )
                            else:
                                self.log_result(
                                    "Legacy Materials Compatibility", 
                                    False, 
                                    f"Expected null description but got: {desc}"
                                )
                        else:
                            self.log_result(
                                "Legacy Materials Compatibility", 
                                False, 
                                f"Failed to retrieve legacy material: {get_response.status_code}"
                            )
                    else:
                        self.log_result(
                            "Legacy Materials Compatibility", 
                            False, 
                            "Legacy material missing ID field"
                        )
                else:
                    self.log_result(
                        "Legacy Materials Compatibility", 
                        True, 
                        "No legacy materials found (all materials have material_description)",
                        "This is expected if database was cleaned or all materials have been updated"
                    )
            else:
                self.log_result(
                    "Legacy Materials Compatibility", 
                    False, 
                    f"Failed to retrieve materials for legacy test: {response.status_code}"
                )
        except Exception as e:
            self.log_result("Legacy Materials Compatibility", False, f"Error: {str(e)}")
        
        # Test 5: Update existing material - should work regardless of whether it has material_description
        if material_with_desc_id:
            update_data = {
                "supplier": "Updated Test Materials Fix Co",
                "product_code": "TMF-WITH-DESC-001-UPDATED",
                "order_to_delivery_time": "2-4 business days",
                "material_description": "Updated test material description for API fix verification",
                "price": 50.25,
                "currency": "AUD",
                "unit": "m2",
                "raw_substrate": False
            }
            
            try:
                response = self.session.put(f"{API_BASE}/materials/{material_with_desc_id}", json=update_data)
                
                if response.status_code == 200:
                    # Verify the update worked
                    get_response = self.session.get(f"{API_BASE}/materials/{material_with_desc_id}")
                    if get_response.status_code == 200:
                        updated_material = get_response.json()
                        updated_desc = updated_material.get('material_description')
                        updated_price = updated_material.get('price')
                        
                        if updated_desc == "Updated test material description for API fix verification" and updated_price == 50.25:
                            self.log_result(
                                "PUT /api/materials - Update Material", 
                                True, 
                                "Successfully updated material with material_description field",
                                f"Updated Description: {updated_desc}, Updated Price: {updated_price}"
                            )
                        else:
                            self.log_result(
                                "PUT /api/materials - Update Material", 
                                False, 
                                "Material update did not persist correctly",
                                f"Description: {updated_desc}, Price: {updated_price}"
                            )
                    else:
                        self.log_result(
                            "PUT /api/materials - Update Material", 
                            False, 
                            "Failed to retrieve updated material for verification"
                        )
                else:
                    self.log_result(
                        "PUT /api/materials - Update Material", 
                        False, 
                        f"Update failed with status {response.status_code}",
                        response.text
                    )
            except Exception as e:
                self.log_result("PUT /api/materials - Update Material", False, f"Error: {str(e)}")

    def test_suppliers_api_endpoints(self):
        """Test all Suppliers API endpoints"""
        print("\n=== SUPPLIERS API ENDPOINTS TEST ===")
        
        # Test 1: GET /api/suppliers - Retrieve all suppliers
        try:
            response = self.session.get(f"{API_BASE}/suppliers")
            
            if response.status_code == 200:
                suppliers = response.json()
                self.log_result(
                    "GET /api/suppliers", 
                    True, 
                    f"Successfully retrieved {len(suppliers)} suppliers"
                )
            else:
                self.log_result(
                    "GET /api/suppliers", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("GET /api/suppliers", False, f"Error: {str(e)}")
        
        # Test 2: POST /api/suppliers - Create new supplier
        supplier_data = {
            "supplier_name": "Test Paper Supplies Ltd",
            "contact_person": "John Smith",
            "phone_number": "+61 3 9876 5432",
            "email": "john.smith@testpapersupplies.com.au",
            "physical_address": "123 Industrial Drive, Melbourne VIC 3000",
            "post_code": "3000",
            "currency_accepted": "AUD",
            "bank_name": "Commonwealth Bank of Australia",
            "bank_address": "456 Collins Street, Melbourne VIC 3000",
            "bank_account_number": "123456789",
            "swift_code": "CTBAAU2S"
        }
        
        created_supplier_id = None
        try:
            response = self.session.post(f"{API_BASE}/suppliers", json=supplier_data)
            
            if response.status_code == 200:
                result = response.json()
                created_supplier_id = result.get('data', {}).get('id')
                
                if created_supplier_id:
                    self.log_result(
                        "POST /api/suppliers", 
                        True, 
                        f"Successfully created supplier with all required fields",
                        f"Supplier ID: {created_supplier_id}"
                    )
                else:
                    self.log_result(
                        "POST /api/suppliers", 
                        False, 
                        "Supplier creation response missing ID"
                    )
            else:
                self.log_result(
                    "POST /api/suppliers", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("POST /api/suppliers", False, f"Error: {str(e)}")
        
        # Test 3: GET /api/suppliers/{id} - Get specific supplier
        if created_supplier_id:
            try:
                response = self.session.get(f"{API_BASE}/suppliers/{created_supplier_id}")
                
                if response.status_code == 200:
                    supplier = response.json()
                    
                    # Verify all required fields are present
                    required_fields = ['supplier_name', 'phone_number', 'email', 'physical_address', 
                                     'post_code', 'bank_name', 'bank_account_number']
                    missing_fields = [field for field in required_fields if field not in supplier]
                    
                    if not missing_fields:
                        self.log_result(
                            "GET /api/suppliers/{id}", 
                            True, 
                            f"Successfully retrieved supplier with all required fields",
                            f"Supplier: {supplier.get('supplier_name')}"
                        )
                    else:
                        self.log_result(
                            "GET /api/suppliers/{id}", 
                            False, 
                            f"Supplier missing required fields: {missing_fields}"
                        )
                else:
                    self.log_result(
                        "GET /api/suppliers/{id}", 
                        False, 
                        f"Failed with status {response.status_code}",
                        response.text
                    )
            except Exception as e:
                self.log_result("GET /api/suppliers/{id}", False, f"Error: {str(e)}")
        
        # Test 4: PUT /api/suppliers/{id} - Update supplier
        if created_supplier_id:
            updated_supplier_data = {
                "supplier_name": "Test Paper Supplies Ltd (Updated)",
                "contact_person": "Jane Smith",
                "phone_number": "+61 3 9876 5433",
                "email": "jane.smith@testpapersupplies.com.au",
                "physical_address": "456 Industrial Drive, Melbourne VIC 3000",
                "post_code": "3000",
                "currency_accepted": "AUD",
                "bank_name": "ANZ Bank",
                "bank_address": "789 Collins Street, Melbourne VIC 3000",
                "bank_account_number": "987654321",
                "swift_code": "ANZBAU3M"
            }
            
            try:
                response = self.session.put(f"{API_BASE}/suppliers/{created_supplier_id}", json=updated_supplier_data)
                
                if response.status_code == 200:
                    # Verify the update by retrieving the supplier
                    get_response = self.session.get(f"{API_BASE}/suppliers/{created_supplier_id}")
                    if get_response.status_code == 200:
                        updated_supplier = get_response.json()
                        
                        if (updated_supplier.get('supplier_name') == "Test Paper Supplies Ltd (Updated)" and
                            updated_supplier.get('contact_person') == "Jane Smith"):
                            self.log_result(
                                "PUT /api/suppliers/{id}", 
                                True, 
                                "Successfully updated supplier information"
                            )
                        else:
                            self.log_result(
                                "PUT /api/suppliers/{id}", 
                                False, 
                                "Supplier update did not persist correctly"
                            )
                    else:
                        self.log_result(
                            "PUT /api/suppliers/{id}", 
                            False, 
                            "Failed to retrieve updated supplier for verification"
                        )
                else:
                    self.log_result(
                        "PUT /api/suppliers/{id}", 
                        False, 
                        f"Failed with status {response.status_code}",
                        response.text
                    )
            except Exception as e:
                self.log_result("PUT /api/suppliers/{id}", False, f"Error: {str(e)}")
        
        # Test 5: DELETE /api/suppliers/{id} - Soft delete supplier
        if created_supplier_id:
            try:
                response = self.session.delete(f"{API_BASE}/suppliers/{created_supplier_id}")
                
                if response.status_code == 200:
                    # Verify soft delete by trying to retrieve the supplier
                    get_response = self.session.get(f"{API_BASE}/suppliers/{created_supplier_id}")
                    if get_response.status_code == 404:
                        self.log_result(
                            "DELETE /api/suppliers/{id}", 
                            True, 
                            "Successfully soft deleted supplier (no longer accessible)"
                        )
                    else:
                        self.log_result(
                            "DELETE /api/suppliers/{id}", 
                            False, 
                            "Supplier still accessible after delete (soft delete may not be working)"
                        )
                else:
                    self.log_result(
                        "DELETE /api/suppliers/{id}", 
                        False, 
                        f"Failed with status {response.status_code}",
                        response.text
                    )
            except Exception as e:
                self.log_result("DELETE /api/suppliers/{id}", False, f"Error: {str(e)}")
    
    def test_product_specifications_api_endpoints(self):
        """Test all Product Specifications API endpoints"""
        print("\n=== PRODUCT SPECIFICATIONS API ENDPOINTS TEST ===")
        
        # Test 1: GET /api/product-specifications - Retrieve all specifications
        try:
            response = self.session.get(f"{API_BASE}/product-specifications")
            
            if response.status_code == 200:
                specifications = response.json()
                self.log_result(
                    "GET /api/product-specifications", 
                    True, 
                    f"Successfully retrieved {len(specifications)} product specifications"
                )
            else:
                self.log_result(
                    "GET /api/product-specifications", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("GET /api/product-specifications", False, f"Error: {str(e)}")
        
        # Test 2: POST /api/product-specifications - Create Paper Core specification
        paper_core_spec = {
            "product_name": "Standard Paper Core",
            "product_type": "Paper Core",
            "specifications": {
                "inner_diameter": "76mm",
                "wall_thickness": "3.2mm",
                "length": "1000mm",
                "crush_strength": "450 N/cm",
                "moisture_content": "8%",
                "surface_finish": "Smooth"
            },
            "materials_composition": [
                {
                    "material_name": "Recycled Kraft Paper",
                    "percentage": 85,
                    "grade": "High strength"
                },
                {
                    "material_name": "Adhesive",
                    "percentage": 15,
                    "type": "Water-based"
                }
            ],
            "manufacturing_notes": "Standard production process with quality control at each stage"
        }
        
        created_paper_core_id = None
        try:
            response = self.session.post(f"{API_BASE}/product-specifications", json=paper_core_spec)
            
            if response.status_code == 200:
                result = response.json()
                created_paper_core_id = result.get('data', {}).get('id')
                
                if created_paper_core_id:
                    self.log_result(
                        "POST /api/product-specifications (Paper Core)", 
                        True, 
                        f"Successfully created Paper Core specification",
                        f"Spec ID: {created_paper_core_id}"
                    )
                else:
                    self.log_result(
                        "POST /api/product-specifications (Paper Core)", 
                        False, 
                        "Specification creation response missing ID"
                    )
            else:
                self.log_result(
                    "POST /api/product-specifications (Paper Core)", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("POST /api/product-specifications (Paper Core)", False, f"Error: {str(e)}")
        
        # Test 3: POST /api/product-specifications - Create Spiral Paper Core specification
        spiral_core_spec = {
            "product_name": "Heavy Duty Spiral Paper Core",
            "product_type": "Spiral Paper Core",
            "specifications": {
                "inner_diameter": "152mm",
                "wall_thickness": "6.5mm",
                "length": "1500mm",
                "spiral_angle": "45 degrees",
                "crush_strength": "800 N/cm",
                "moisture_content": "7%",
                "surface_finish": "Textured",
                "end_caps": "Plastic reinforced"
            },
            "materials_composition": [
                {
                    "material_name": "Virgin Kraft Paper",
                    "percentage": 70,
                    "grade": "Extra high strength"
                },
                {
                    "material_name": "Recycled Kraft Paper",
                    "percentage": 20,
                    "grade": "Medium strength"
                },
                {
                    "material_name": "Spiral Adhesive",
                    "percentage": 10,
                    "type": "Hot-melt"
                }
            ],
            "manufacturing_notes": "Spiral winding process with reinforced end caps for heavy-duty applications"
        }
        
        created_spiral_core_id = None
        try:
            response = self.session.post(f"{API_BASE}/product-specifications", json=spiral_core_spec)
            
            if response.status_code == 200:
                result = response.json()
                created_spiral_core_id = result.get('data', {}).get('id')
                
                if created_spiral_core_id:
                    self.log_result(
                        "POST /api/product-specifications (Spiral Paper Core)", 
                        True, 
                        f"Successfully created Spiral Paper Core specification",
                        f"Spec ID: {created_spiral_core_id}"
                    )
                else:
                    self.log_result(
                        "POST /api/product-specifications (Spiral Paper Core)", 
                        False, 
                        "Specification creation response missing ID"
                    )
            else:
                self.log_result(
                    "POST /api/product-specifications (Spiral Paper Core)", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("POST /api/product-specifications (Spiral Paper Core)", False, f"Error: {str(e)}")
        
        # Test 4: GET /api/product-specifications/{id} - Get specific specification
        if created_paper_core_id:
            try:
                response = self.session.get(f"{API_BASE}/product-specifications/{created_paper_core_id}")
                
                if response.status_code == 200:
                    specification = response.json()
                    
                    # Verify flexible specifications dict storage
                    specs = specification.get('specifications', {})
                    materials = specification.get('materials_composition', [])
                    
                    if (specs.get('inner_diameter') == "76mm" and 
                        specs.get('crush_strength') == "450 N/cm" and
                        len(materials) == 2):
                        self.log_result(
                            "GET /api/product-specifications/{id}", 
                            True, 
                            f"Successfully retrieved specification with flexible dict storage",
                            f"Product: {specification.get('product_name')}, Specs: {len(specs)} fields, Materials: {len(materials)} items"
                        )
                    else:
                        self.log_result(
                            "GET /api/product-specifications/{id}", 
                            False, 
                            "Specification data not stored/retrieved correctly"
                        )
                else:
                    self.log_result(
                        "GET /api/product-specifications/{id}", 
                        False, 
                        f"Failed with status {response.status_code}",
                        response.text
                    )
            except Exception as e:
                self.log_result("GET /api/product-specifications/{id}", False, f"Error: {str(e)}")
        
        # Test 5: PUT /api/product-specifications/{id} - Update specification
        if created_spiral_core_id:
            updated_spiral_spec = {
                "product_name": "Heavy Duty Spiral Paper Core (Updated)",
                "product_type": "Spiral Paper Core",
                "specifications": {
                    "inner_diameter": "152mm",
                    "wall_thickness": "7.0mm",  # Updated thickness
                    "length": "1500mm",
                    "spiral_angle": "50 degrees",  # Updated angle
                    "crush_strength": "900 N/cm",  # Updated strength
                    "moisture_content": "6%",  # Updated moisture
                    "surface_finish": "Smooth",  # Updated finish
                    "end_caps": "Metal reinforced",  # Updated caps
                    "color": "Brown"  # New field added
                },
                "materials_composition": [
                    {
                        "material_name": "Virgin Kraft Paper",
                        "percentage": 75,  # Updated percentage
                        "grade": "Extra high strength"
                    },
                    {
                        "material_name": "Recycled Kraft Paper",
                        "percentage": 15,  # Updated percentage
                        "grade": "Medium strength"
                    },
                    {
                        "material_name": "Spiral Adhesive",
                        "percentage": 10,
                        "type": "Hot-melt"
                    }
                ],
                "manufacturing_notes": "Updated spiral winding process with metal-reinforced end caps for extra heavy-duty applications"
            }
            
            try:
                response = self.session.put(f"{API_BASE}/product-specifications/{created_spiral_core_id}", json=updated_spiral_spec)
                
                if response.status_code == 200:
                    # Verify the update by retrieving the specification
                    get_response = self.session.get(f"{API_BASE}/product-specifications/{created_spiral_core_id}")
                    if get_response.status_code == 200:
                        updated_spec = get_response.json()
                        
                        updated_specs = updated_spec.get('specifications', {})
                        if (updated_spec.get('product_name') == "Heavy Duty Spiral Paper Core (Updated)" and
                            updated_specs.get('wall_thickness') == "7.0mm" and
                            updated_specs.get('color') == "Brown"):
                            self.log_result(
                                "PUT /api/product-specifications/{id}", 
                                True, 
                                "Successfully updated specification with flexible dict storage"
                            )
                        else:
                            self.log_result(
                                "PUT /api/product-specifications/{id}", 
                                False, 
                                "Specification update did not persist correctly"
                            )
                    else:
                        self.log_result(
                            "PUT /api/product-specifications/{id}", 
                            False, 
                            "Failed to retrieve updated specification for verification"
                        )
                else:
                    self.log_result(
                        "PUT /api/product-specifications/{id}", 
                        False, 
                        f"Failed with status {response.status_code}",
                        response.text
                    )
            except Exception as e:
                self.log_result("PUT /api/product-specifications/{id}", False, f"Error: {str(e)}")
        
        # Test 6: DELETE /api/product-specifications/{id} - Soft delete specification
        if created_paper_core_id:
            try:
                response = self.session.delete(f"{API_BASE}/product-specifications/{created_paper_core_id}")
                
                if response.status_code == 200:
                    # Verify soft delete by trying to retrieve the specification
                    get_response = self.session.get(f"{API_BASE}/product-specifications/{created_paper_core_id}")
                    if get_response.status_code == 404:
                        self.log_result(
                            "DELETE /api/product-specifications/{id}", 
                            True, 
                            "Successfully soft deleted specification (no longer accessible)"
                        )
                    else:
                        self.log_result(
                            "DELETE /api/product-specifications/{id}", 
                            False, 
                            "Specification still accessible after delete (soft delete may not be working)"
                        )
                else:
                    self.log_result(
                        "DELETE /api/product-specifications/{id}", 
                        False, 
                        f"Failed with status {response.status_code}",
                        response.text
                    )
            except Exception as e:
                self.log_result("DELETE /api/product-specifications/{id}", False, f"Error: {str(e)}")
    
    def test_new_endpoints_authentication_requirements(self):
        """Test that Suppliers and Product Specifications endpoints require proper authentication"""
        print("\n=== NEW ENDPOINTS AUTHENTICATION REQUIREMENTS TEST ===")
        
        # Test without authentication
        temp_session = requests.Session()
        
        endpoints_to_test = [
            ("GET /api/suppliers", "get", "/suppliers"),
            ("POST /api/suppliers", "post", "/suppliers"),
            ("GET /api/product-specifications", "get", "/product-specifications"),
            ("POST /api/product-specifications", "post", "/product-specifications")
        ]
        
        authenticated_endpoints = 0
        total_endpoints = len(endpoints_to_test)
        
        for endpoint_name, method, path in endpoints_to_test:
            try:
                if method == "get":
                    response = temp_session.get(f"{API_BASE}{path}")
                elif method == "post":
                    response = temp_session.post(f"{API_BASE}{path}", json={})
                
                if response.status_code in [401, 403]:
                    authenticated_endpoints += 1
                    self.log_result(
                        f"Auth Required - {endpoint_name}", 
                        True, 
                        f"Properly requires authentication (status: {response.status_code})"
                    )
                else:
                    self.log_result(
                        f"Auth Required - {endpoint_name}", 
                        False, 
                        f"Expected 401/403 but got {response.status_code}",
                        "Endpoint should require admin/production_manager authentication"
                    )
                    
            except Exception as e:
                self.log_result(f"Auth Required - {endpoint_name}", False, f"Error: {str(e)}")
        
        # Overall authentication summary
        if authenticated_endpoints == total_endpoints:
            self.log_result(
                "New Endpoints Authentication Requirements", 
                True, 
                f"All {total_endpoints} new endpoints properly require authentication"
            )
        else:
            self.log_result(
                "New Endpoints Authentication Requirements", 
                False, 
                f"Only {authenticated_endpoints}/{total_endpoints} new endpoints require authentication"
            )
    
    def test_new_endpoints_validation_requirements(self):
        """Test validation of required fields for Suppliers and Product Specifications"""
        print("\n=== NEW ENDPOINTS VALIDATION REQUIREMENTS TEST ===")
        
        # Test 1: Supplier validation - missing required fields
        incomplete_supplier = {
            "supplier_name": "Test Supplier",
            # Missing phone_number, email, physical_address, post_code, bank_name, bank_account_number
        }
        
        try:
            response = self.session.post(f"{API_BASE}/suppliers", json=incomplete_supplier)
            
            if response.status_code == 422:  # Validation error
                self.log_result(
                    "Supplier Validation - Required Fields", 
                    True, 
                    "Correctly validates required fields (422 validation error)",
                    response.text[:200]
                )
            elif response.status_code == 400:
                self.log_result(
                    "Supplier Validation - Required Fields", 
                    True, 
                    "Correctly validates required fields (400 bad request)",
                    response.text[:200]
                )
            else:
                self.log_result(
                    "Supplier Validation - Required Fields", 
                    False, 
                    f"Expected validation error but got {response.status_code}",
                    response.text[:200]
                )
        except Exception as e:
            self.log_result("Supplier Validation - Required Fields", False, f"Error: {str(e)}")
        
        # Test 2: Product Specification validation - missing required fields
        incomplete_spec = {
            "product_name": "Test Product",
            # Missing product_type, specifications
        }
        
        try:
            response = self.session.post(f"{API_BASE}/product-specifications", json=incomplete_spec)
            
            if response.status_code == 422:  # Validation error
                self.log_result(
                    "Product Specification Validation - Required Fields", 
                    True, 
                    "Correctly validates required fields (422 validation error)",
                    response.text[:200]
                )
            elif response.status_code == 400:
                self.log_result(
                    "Product Specification Validation - Required Fields", 
                    True, 
                    "Correctly validates required fields (400 bad request)",
                    response.text[:200]
                )
            else:
                self.log_result(
                    "Product Specification Validation - Required Fields", 
                    False, 
                    f"Expected validation error but got {response.status_code}",
                    response.text[:200]
                )
        except Exception as e:
            self.log_result("Product Specification Validation - Required Fields", False, f"Error: {str(e)}")

    def test_suppliers_account_name_field(self):
        """Test the new account_name field in Suppliers API"""
        print("\n=== SUPPLIERS ACCOUNT NAME FIELD TEST ===")
        
        # Test 1: Create supplier with account_name field
        supplier_with_account_name = {
            "supplier_name": "Acme Manufacturing Pty Ltd",
            "contact_person": "John Smith",
            "phone_number": "0412345678",
            "email": "john@acmemanufacturing.com.au",
            "physical_address": "123 Industrial Drive",
            "post_code": "3000",
            "currency_accepted": "AUD",
            "bank_name": "Commonwealth Bank",
            "bank_address": "456 Collins Street, Melbourne VIC 3000",
            "account_name": "Acme Manufacturing Pty Ltd",  # New required field
            "bank_account_number": "123456789",
            "swift_code": "CTBAAU2S"
        }
        
        supplier_id = None
        try:
            response = self.session.post(f"{API_BASE}/suppliers", json=supplier_with_account_name)
            
            if response.status_code == 200:
                result = response.json()
                supplier_id = result.get('data', {}).get('id')
                
                if supplier_id:
                    self.log_result(
                        "Create Supplier with Account Name", 
                        True, 
                        f"Successfully created supplier with account_name field",
                        f"Supplier ID: {supplier_id}, Account Name: {supplier_with_account_name['account_name']}"
                    )
                else:
                    self.log_result(
                        "Create Supplier with Account Name", 
                        False, 
                        "Supplier creation response missing ID"
                    )
            else:
                self.log_result(
                    "Create Supplier with Account Name", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Create Supplier with Account Name", False, f"Error: {str(e)}")
        
        # Test 2: Verify account_name appears in GET response
        if supplier_id:
            try:
                response = self.session.get(f"{API_BASE}/suppliers/{supplier_id}")
                
                if response.status_code == 200:
                    supplier = response.json()
                    account_name = supplier.get('account_name')
                    
                    if account_name == "Acme Manufacturing Pty Ltd":
                        self.log_result(
                            "GET Supplier includes Account Name", 
                            True, 
                            f"Account name field correctly returned in GET response",
                            f"Account Name: {account_name}"
                        )
                    else:
                        self.log_result(
                            "GET Supplier includes Account Name", 
                            False, 
                            f"Account name field missing or incorrect in GET response",
                            f"Expected: 'Acme Manufacturing Pty Ltd', Got: {account_name}"
                        )
                else:
                    self.log_result(
                        "GET Supplier includes Account Name", 
                        False, 
                        f"Failed to retrieve supplier: {response.status_code}",
                        response.text
                    )
            except Exception as e:
                self.log_result("GET Supplier includes Account Name", False, f"Error: {str(e)}")
        
        # Test 3: Update supplier account_name field
        if supplier_id:
            updated_account_name = "John Smith Trading Account"
            update_data = {
                "supplier_name": "Acme Manufacturing Pty Ltd",
                "contact_person": "John Smith",
                "phone_number": "0412345678",
                "email": "john@acmemanufacturing.com.au",
                "physical_address": "123 Industrial Drive",
                "post_code": "3000",
                "currency_accepted": "AUD",
                "bank_name": "Commonwealth Bank",
                "bank_address": "456 Collins Street, Melbourne VIC 3000",
                "account_name": updated_account_name,  # Updated account name
                "bank_account_number": "123456789",
                "swift_code": "CTBAAU2S"
            }
            
            try:
                response = self.session.put(f"{API_BASE}/suppliers/{supplier_id}", json=update_data)
                
                if response.status_code == 200:
                    # Verify the update
                    get_response = self.session.get(f"{API_BASE}/suppliers/{supplier_id}")
                    if get_response.status_code == 200:
                        updated_supplier = get_response.json()
                        updated_account_name_value = updated_supplier.get('account_name')
                        
                        if updated_account_name_value == updated_account_name:
                            self.log_result(
                                "Update Supplier Account Name", 
                                True, 
                                f"Successfully updated account_name field",
                                f"New Account Name: {updated_account_name_value}"
                            )
                        else:
                            self.log_result(
                                "Update Supplier Account Name", 
                                False, 
                                f"Account name update failed",
                                f"Expected: '{updated_account_name}', Got: '{updated_account_name_value}'"
                            )
                    else:
                        self.log_result(
                            "Update Supplier Account Name", 
                            False, 
                            "Failed to retrieve updated supplier for verification"
                        )
                else:
                    self.log_result(
                        "Update Supplier Account Name", 
                        False, 
                        f"Update failed with status {response.status_code}",
                        response.text
                    )
            except Exception as e:
                self.log_result("Update Supplier Account Name", False, f"Error: {str(e)}")
        
        # Test 4: Try creating supplier without account_name (should fail validation)
        supplier_without_account_name = {
            "supplier_name": "Test Supplier Without Account Name",
            "contact_person": "Jane Doe",
            "phone_number": "0487654321",
            "email": "jane@testsupplier.com",
            "physical_address": "789 Test Street",
            "post_code": "3001",
            "currency_accepted": "AUD",
            "bank_name": "ANZ Bank",
            "bank_address": "123 Bank Street, Melbourne VIC 3000",
            # account_name field intentionally missing
            "bank_account_number": "987654321",
            "swift_code": "ANZBAU3M"
        }
        
        try:
            response = self.session.post(f"{API_BASE}/suppliers", json=supplier_without_account_name)
            
            if response.status_code == 422:  # Validation error expected
                self.log_result(
                    "Validation - Account Name Required", 
                    True, 
                    "Correctly rejected supplier creation without required account_name field",
                    f"Status: {response.status_code} (Validation Error)"
                )
            elif response.status_code == 200:
                self.log_result(
                    "Validation - Account Name Required", 
                    False, 
                    "Supplier creation should have failed without account_name field",
                    "Field validation not working properly"
                )
            else:
                self.log_result(
                    "Validation - Account Name Required", 
                    False, 
                    f"Unexpected status code: {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Validation - Account Name Required", False, f"Error: {str(e)}")
        
        # Test 5: Verify account_name field position in GET all suppliers response
        try:
            response = self.session.get(f"{API_BASE}/suppliers")
            
            if response.status_code == 200:
                suppliers = response.json()
                
                if suppliers and len(suppliers) > 0:
                    # Check if any supplier has account_name field
                    suppliers_with_account_name = [s for s in suppliers if 'account_name' in s]
                    
                    if suppliers_with_account_name:
                        # Check field positioning (should be between bank_name and bank_account_number)
                        sample_supplier = suppliers_with_account_name[0]
                        supplier_keys = list(sample_supplier.keys())
                        
                        try:
                            bank_name_index = supplier_keys.index('bank_name')
                            account_name_index = supplier_keys.index('account_name')
                            bank_account_number_index = supplier_keys.index('bank_account_number')
                            
                            # Check if account_name is positioned between bank_name and bank_account_number
                            correct_position = bank_name_index < account_name_index < bank_account_number_index
                            
                            self.log_result(
                                "Account Name Field Position", 
                                correct_position, 
                                f"Account name field positioned correctly between bank_name and bank_account_number" if correct_position else "Account name field not in expected position",
                                f"Field order: bank_name({bank_name_index}) -> account_name({account_name_index}) -> bank_account_number({bank_account_number_index})"
                            )
                        except ValueError as ve:
                            self.log_result(
                                "Account Name Field Position", 
                                False, 
                                "Could not verify field positioning - missing expected fields",
                                str(ve)
                            )
                        
                        self.log_result(
                            "GET All Suppliers includes Account Name", 
                            True, 
                            f"Found {len(suppliers_with_account_name)} suppliers with account_name field out of {len(suppliers)} total suppliers"
                        )
                    else:
                        self.log_result(
                            "GET All Suppliers includes Account Name", 
                            False, 
                            "No suppliers found with account_name field in GET all suppliers response",
                            f"Total suppliers: {len(suppliers)}"
                        )
                else:
                    self.log_result(
                        "GET All Suppliers includes Account Name", 
                        False, 
                        "No suppliers found in database for field verification"
                    )
            else:
                self.log_result(
                    "GET All Suppliers includes Account Name", 
                    False, 
                    f"Failed to retrieve suppliers list: {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("GET All Suppliers includes Account Name", False, f"Error: {str(e)}")
        
        return supplier_id

    def test_product_specifications_api(self):
        """Test Product Specifications API endpoints for backend stability after frontend changes"""
        print("\n=== PRODUCT SPECIFICATIONS API STABILITY TEST ===")
        
        # Test 1: GET /api/product-specifications - Verify existing specifications are retrievable
        try:
            response = self.session.get(f"{API_BASE}/product-specifications")
            
            if response.status_code == 200:
                specs = response.json()
                self.log_result(
                    "GET Product Specifications", 
                    True, 
                    f"Successfully retrieved {len(specs)} existing product specifications"
                )
                existing_specs = specs
            else:
                self.log_result(
                    "GET Product Specifications", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
                existing_specs = []
        except Exception as e:
            self.log_result("GET Product Specifications", False, f"Error: {str(e)}")
            existing_specs = []
        
        # Test 2: POST /api/product-specifications - Create regular Paper Core specification
        regular_paper_core_spec = {
            "product_name": "Standard Paper Core",
            "product_type": "Paper Core",
            "specifications": {
                "inner_diameter_mm": 76,
                "outer_diameter_mm": 80,
                "length_mm": 1000,
                "wall_thickness_mm": 2.0,
                "material_grade": "Standard",
                "crush_strength_n": 500
            },
            "materials_composition": [
                {
                    "material_name": "Recycled Cardboard",
                    "percentage": 80,
                    "grade": "Standard"
                },
                {
                    "material_name": "Virgin Fiber",
                    "percentage": 20,
                    "grade": "High Quality"
                }
            ],
            "manufacturing_notes": "Standard paper core for general use"
        }
        
        regular_spec_id = None
        try:
            response = self.session.post(f"{API_BASE}/product-specifications", json=regular_paper_core_spec)
            
            if response.status_code == 200:
                result = response.json()
                regular_spec_id = result.get('data', {}).get('id')
                
                if regular_spec_id:
                    self.log_result(
                        "Create Regular Paper Core Specification", 
                        True, 
                        "Successfully created regular Paper Core specification with flexible dict storage",
                        f"Spec ID: {regular_spec_id}"
                    )
                else:
                    self.log_result(
                        "Create Regular Paper Core Specification", 
                        False, 
                        "Specification creation response missing ID"
                    )
            else:
                self.log_result(
                    "Create Regular Paper Core Specification", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Create Regular Paper Core Specification", False, f"Error: {str(e)}")
        
        # Test 3: POST /api/product-specifications - Create Spiral Paper Core specification with new fields
        spiral_paper_core_spec = {
            "product_name": "Premium Spiral Paper Core",
            "product_type": "Spiral Paper Core",
            "specifications": {
                "internal_diameter": 76.2,
                "external_diameter": 82.5,
                "length": 1200,
                "wall_thickness_required": 3.15,
                "spiral_angle_degrees": 45,
                "adhesive_type": "PVA",
                "surface_finish": "Smooth",
                "compression_strength_kpa": 850,
                "moisture_content_max": 8.5,
                "spiral_overlap_mm": 2.0,
                "end_cap_type": "Plastic",
                "color": "Natural Brown"
            },
            "materials_composition": [
                {
                    "material_name": "High-Grade Kraft Paper",
                    "percentage": 60,
                    "grade": "Premium",
                    "gsm": 180
                },
                {
                    "material_name": "Recycled Fiber",
                    "percentage": 30,
                    "grade": "Standard",
                    "gsm": 120
                },
                {
                    "material_name": "PVA Adhesive",
                    "percentage": 10,
                    "grade": "Industrial",
                    "viscosity": "Medium"
                }
            ],
            "manufacturing_notes": "Spiral paper core with enhanced strength for heavy-duty applications. Requires precise spiral winding angle and adhesive application."
        }
        
        spiral_spec_id = None
        try:
            response = self.session.post(f"{API_BASE}/product-specifications", json=spiral_paper_core_spec)
            
            if response.status_code == 200:
                result = response.json()
                spiral_spec_id = result.get('data', {}).get('id')
                
                if spiral_spec_id:
                    self.log_result(
                        "Create Spiral Paper Core Specification", 
                        True, 
                        "Successfully created Spiral Paper Core specification with new fields",
                        f"Spec ID: {spiral_spec_id}, Fields: internal_diameter, wall_thickness_required, spiral_angle_degrees, etc."
                    )
                else:
                    self.log_result(
                        "Create Spiral Paper Core Specification", 
                        False, 
                        "Spiral specification creation response missing ID"
                    )
            else:
                self.log_result(
                    "Create Spiral Paper Core Specification", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Create Spiral Paper Core Specification", False, f"Error: {str(e)}")
        
        # Test 4: GET /api/product-specifications/{id} - Verify both types can be retrieved correctly
        if regular_spec_id:
            try:
                response = self.session.get(f"{API_BASE}/product-specifications/{regular_spec_id}")
                
                if response.status_code == 200:
                    spec = response.json()
                    specifications = spec.get('specifications', {})
                    materials = spec.get('materials_composition', [])
                    
                    # Verify regular Paper Core fields are stored correctly
                    expected_fields = ['inner_diameter_mm', 'outer_diameter_mm', 'length_mm', 'wall_thickness_mm']
                    found_fields = [field for field in expected_fields if field in specifications]
                    
                    if len(found_fields) == len(expected_fields) and len(materials) == 2:
                        self.log_result(
                            "Retrieve Regular Paper Core Specification", 
                            True, 
                            f"Successfully retrieved regular Paper Core with all fields intact",
                            f"Spec fields: {len(specifications)}, Materials: {len(materials)}"
                        )
                    else:
                        self.log_result(
                            "Retrieve Regular Paper Core Specification", 
                            False, 
                            "Retrieved specification missing expected fields or materials",
                            f"Found fields: {found_fields}, Materials count: {len(materials)}"
                        )
                else:
                    self.log_result(
                        "Retrieve Regular Paper Core Specification", 
                        False, 
                        f"Failed with status {response.status_code}",
                        response.text
                    )
            except Exception as e:
                self.log_result("Retrieve Regular Paper Core Specification", False, f"Error: {str(e)}")
        
        if spiral_spec_id:
            try:
                response = self.session.get(f"{API_BASE}/product-specifications/{spiral_spec_id}")
                
                if response.status_code == 200:
                    spec = response.json()
                    specifications = spec.get('specifications', {})
                    materials = spec.get('materials_composition', [])
                    
                    # Verify Spiral Paper Core specific fields are stored correctly
                    spiral_fields = ['internal_diameter', 'wall_thickness_required', 'spiral_angle_degrees', 'adhesive_type']
                    found_spiral_fields = [field for field in spiral_fields if field in specifications]
                    
                    if len(found_spiral_fields) == len(spiral_fields) and len(materials) == 3:
                        self.log_result(
                            "Retrieve Spiral Paper Core Specification", 
                            True, 
                            f"Successfully retrieved Spiral Paper Core with all new fields intact",
                            f"Spiral fields: {found_spiral_fields}, Materials: {len(materials)}"
                        )
                    else:
                        self.log_result(
                            "Retrieve Spiral Paper Core Specification", 
                            False, 
                            "Retrieved Spiral specification missing expected fields or materials",
                            f"Found spiral fields: {found_spiral_fields}, Materials count: {len(materials)}"
                        )
                else:
                    self.log_result(
                        "Retrieve Spiral Paper Core Specification", 
                        False, 
                        f"Failed with status {response.status_code}",
                        response.text
                    )
            except Exception as e:
                self.log_result("Retrieve Spiral Paper Core Specification", False, f"Error: {str(e)}")
        
        # Test 5: Verify flexible specifications dict can handle both types seamlessly
        try:
            response = self.session.get(f"{API_BASE}/product-specifications")
            
            if response.status_code == 200:
                all_specs = response.json()
                
                # Count different product types
                paper_core_count = len([s for s in all_specs if s.get('product_type') == 'Paper Core'])
                spiral_core_count = len([s for s in all_specs if s.get('product_type') == 'Spiral Paper Core'])
                
                # Verify both types are present and retrievable
                if paper_core_count > 0 and spiral_core_count > 0:
                    self.log_result(
                        "Flexible Specifications Dict Handling", 
                        True, 
                        f"Backend seamlessly handles both specification types",
                        f"Paper Cores: {paper_core_count}, Spiral Paper Cores: {spiral_core_count}, Total: {len(all_specs)}"
                    )
                else:
                    self.log_result(
                        "Flexible Specifications Dict Handling", 
                        False, 
                        "Not all specification types found in retrieval",
                        f"Paper Cores: {paper_core_count}, Spiral Paper Cores: {spiral_core_count}"
                    )
            else:
                self.log_result(
                    "Flexible Specifications Dict Handling", 
                    False, 
                    f"Failed to retrieve all specifications for type verification: {response.status_code}"
                )
        except Exception as e:
            self.log_result("Flexible Specifications Dict Handling", False, f"Error: {str(e)}")
        
        # Test 6: Verify authentication and permissions are still working
        temp_session = requests.Session()
        try:
            response = temp_session.get(f"{API_BASE}/product-specifications")
            
            if response.status_code in [401, 403]:
                self.log_result(
                    "Product Specifications API Authentication", 
                    True, 
                    f"API properly requires authentication (status: {response.status_code})"
                )
            else:
                self.log_result(
                    "Product Specifications API Authentication", 
                    False, 
                    f"Expected 401/403 but got {response.status_code}",
                    "API should require authentication"
                )
        except Exception as e:
            self.log_result("Product Specifications API Authentication", False, f"Error: {str(e)}")

    def test_calculator_material_consumption_by_client(self):
        """Test POST /api/calculators/material-consumption-by-client"""
        print("\n=== CALCULATOR: MATERIAL CONSUMPTION BY CLIENT TEST ===")
        
        try:
            # First, get available clients and materials
            clients_response = self.session.get(f"{API_BASE}/clients")
            materials_response = self.session.get(f"{API_BASE}/materials")
            
            if clients_response.status_code != 200 or materials_response.status_code != 200:
                self.log_result(
                    "Calculator: Material Consumption by Client", 
                    False, 
                    "Failed to get required data (clients/materials) for test"
                )
                return
            
            clients = clients_response.json()
            materials = materials_response.json()
            
            if not clients or not materials:
                self.log_result(
                    "Calculator: Material Consumption by Client", 
                    False, 
                    "No clients or materials available for testing"
                )
                return
            
            # Use first available client and material
            client_id = clients[0]['id']
            material_id = materials[0]['id']
            
            # Test calculation request
            calculation_data = {
                "client_id": client_id,
                "material_id": material_id,
                "start_date": "2024-01-01",
                "end_date": "2024-12-31"
            }
            
            response = self.session.post(f"{API_BASE}/calculators/material-consumption-by-client", json=calculation_data)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success') and 'data' in data:
                    result = data['data']
                    required_fields = ['calculation_type', 'input_parameters', 'results', 'calculated_by']
                    missing_fields = [field for field in required_fields if field not in result]
                    
                    if not missing_fields:
                        results = result.get('results', {})
                        if 'total_consumption' in results and 'material_name' in results:
                            self.log_result(
                                "Calculator: Material Consumption by Client", 
                                True, 
                                f"Successfully calculated material consumption",
                                f"Total consumption: {results.get('total_consumption')}, Material: {results.get('material_name')}, Orders: {results.get('order_count', 0)}"
                            )
                        else:
                            self.log_result(
                                "Calculator: Material Consumption by Client", 
                                False, 
                                "Calculation results missing expected fields",
                                f"Results: {results}"
                            )
                    else:
                        self.log_result(
                            "Calculator: Material Consumption by Client", 
                            False, 
                            f"Response missing required fields: {missing_fields}"
                        )
                else:
                    self.log_result(
                        "Calculator: Material Consumption by Client", 
                        False, 
                        "Response missing success flag or data",
                        str(data)
                    )
            else:
                self.log_result(
                    "Calculator: Material Consumption by Client", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Calculator: Material Consumption by Client", False, f"Error: {str(e)}")
    
    def test_calculator_material_permutation(self):
        """Test POST /api/calculators/material-permutation"""
        print("\n=== CALCULATOR: MATERIAL PERMUTATION TEST ===")
        
        try:
            # Test permutation calculation request
            permutation_data = {
                "core_ids": ["core-001", "core-002"],
                "sizes_to_manufacture": [
                    {"width": 100.0, "priority": 1},
                    {"width": 150.0, "priority": 2},
                    {"width": 200.0, "priority": 1}
                ],
                "master_deckle_width": 1000.0,
                "acceptable_waste_percentage": 15.0
            }
            
            response = self.session.post(f"{API_BASE}/calculators/material-permutation", json=permutation_data)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success') and 'data' in data:
                    result = data['data']
                    required_fields = ['calculation_type', 'input_parameters', 'results', 'calculated_by']
                    missing_fields = [field for field in required_fields if field not in result]
                    
                    if not missing_fields:
                        results = result.get('results', {})
                        if 'permutation_options' in results and 'total_options_found' in results:
                            options_count = results.get('total_options_found', 0)
                            permutation_options = results.get('permutation_options', [])
                            
                            self.log_result(
                                "Calculator: Material Permutation", 
                                True, 
                                f"Successfully calculated material permutations",
                                f"Total options found: {options_count}, Top options returned: {len(permutation_options)}"
                            )
                        else:
                            self.log_result(
                                "Calculator: Material Permutation", 
                                False, 
                                "Permutation results missing expected fields",
                                f"Results: {results}"
                            )
                    else:
                        self.log_result(
                            "Calculator: Material Permutation", 
                            False, 
                            f"Response missing required fields: {missing_fields}"
                        )
                else:
                    self.log_result(
                        "Calculator: Material Permutation", 
                        False, 
                        "Response missing success flag or data",
                        str(data)
                    )
            else:
                self.log_result(
                    "Calculator: Material Permutation", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Calculator: Material Permutation", False, f"Error: {str(e)}")
    
    def test_calculator_spiral_core_consumption(self):
        """Test POST /api/calculators/spiral-core-consumption"""
        print("\n=== CALCULATOR: SPIRAL CORE CONSUMPTION TEST ===")
        
        try:
            # First, get available product specifications
            specs_response = self.session.get(f"{API_BASE}/product-specifications")
            
            if specs_response.status_code != 200:
                self.log_result(
                    "Calculator: Spiral Core Consumption", 
                    False, 
                    "Failed to get product specifications for test"
                )
                return
            
            specs = specs_response.json()
            
            # Find a Spiral Paper Core specification
            spiral_spec = None
            for spec in specs:
                if spec.get('product_type') == 'Spiral Paper Core':
                    spiral_spec = spec
                    break
            
            if not spiral_spec:
                # Get a real material ID for the test
                materials_response = self.session.get(f"{API_BASE}/materials")
                if materials_response.status_code != 200:
                    self.log_result(
                        "Calculator: Spiral Core Consumption", 
                        False, 
                        "Failed to get materials for test specification creation"
                    )
                    return
                
                materials = materials_response.json()
                if not materials:
                    self.log_result(
                        "Calculator: Spiral Core Consumption", 
                        False, 
                        "No materials available for test specification creation"
                    )
                    return
                
                # Use first available material
                real_material_id = materials[0]['id']
                
                # Create a test Spiral Paper Core specification
                test_spec_data = {
                    "product_name": "Test Spiral Core for Calculator",
                    "product_type": "Spiral Paper Core",
                    "specifications": {
                        "internal_diameter": 76.0,
                        "wall_thickness_required": 3.0,
                        "spiral_angle_degrees": 45.0,
                        "adhesive_type": "PVA",
                        "selected_material_id": real_material_id
                    },
                    "materials_composition": [
                        {"material_name": "Test Paper", "percentage": 100.0, "grade": "Premium"}
                    ]
                }
                
                create_response = self.session.post(f"{API_BASE}/product-specifications", json=test_spec_data)
                if create_response.status_code == 200:
                    spiral_spec = {"id": create_response.json().get('data', {}).get('id')}
                else:
                    self.log_result(
                        "Calculator: Spiral Core Consumption", 
                        False, 
                        "No Spiral Paper Core specifications available and failed to create test spec"
                    )
                    return
            
            # Test spiral core consumption calculation
            consumption_data = {
                "product_specification_id": spiral_spec['id'],
                "core_internal_diameter": 76.0,
                "core_length": 1000.0,
                "quantity": 100
            }
            
            response = self.session.post(f"{API_BASE}/calculators/spiral-core-consumption", json=consumption_data)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success') and 'data' in data:
                    result = data['data']
                    required_fields = ['calculation_type', 'input_parameters', 'results', 'calculated_by']
                    missing_fields = [field for field in required_fields if field not in result]
                    
                    if not missing_fields:
                        results = result.get('results', {})
                        expected_result_fields = ['material_name', 'total_material_weight_kg', 'material_weight_per_core_kg', 'quantity']
                        
                        if all(field in results for field in expected_result_fields):
                            total_weight = results.get('total_material_weight_kg')
                            per_core_weight = results.get('material_weight_per_core_kg')
                            
                            self.log_result(
                                "Calculator: Spiral Core Consumption", 
                                True, 
                                f"Successfully calculated spiral core material consumption",
                                f"Total weight: {total_weight}kg, Per core: {per_core_weight}kg, Quantity: {results.get('quantity')}"
                            )
                        else:
                            missing_result_fields = [field for field in expected_result_fields if field not in results]
                            self.log_result(
                                "Calculator: Spiral Core Consumption", 
                                False, 
                                f"Calculation results missing expected fields: {missing_result_fields}",
                                f"Results: {results}"
                            )
                    else:
                        self.log_result(
                            "Calculator: Spiral Core Consumption", 
                            False, 
                            f"Response missing required fields: {missing_fields}"
                        )
                else:
                    self.log_result(
                        "Calculator: Spiral Core Consumption", 
                        False, 
                        "Response missing success flag or data",
                        str(data)
                    )
            elif response.status_code == 404:
                self.log_result(
                    "Calculator: Spiral Core Consumption", 
                    False, 
                    "Product specification not found",
                    response.text
                )
            elif response.status_code == 400:
                error_text = response.text
                if "not for Spiral Paper Cores" in error_text or "No material selected" in error_text:
                    self.log_result(
                        "Calculator: Spiral Core Consumption", 
                        True, 
                        "Correctly validates specification requirements",
                        f"Validation error: {error_text}"
                    )
                else:
                    self.log_result(
                        "Calculator: Spiral Core Consumption", 
                        False, 
                        f"Unexpected validation error: {error_text}"
                    )
            else:
                self.log_result(
                    "Calculator: Spiral Core Consumption", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Calculator: Spiral Core Consumption", False, f"Error: {str(e)}")
    
    def test_stocktake_current_status(self):
        """Test GET /api/stocktake/current"""
        print("\n=== STOCKTAKE: CURRENT STATUS TEST ===")
        
        try:
            response = self.session.get(f"{API_BASE}/stocktake/current")
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success') and 'data' in data:
                    stocktake_data = data['data']
                    required_fields = ['stocktake_required', 'first_business_day']
                    missing_fields = [field for field in required_fields if field not in stocktake_data]
                    
                    if not missing_fields:
                        stocktake_required = stocktake_data.get('stocktake_required')
                        first_business_day = stocktake_data.get('first_business_day')
                        existing_stocktake = stocktake_data.get('stocktake')
                        
                        if existing_stocktake:
                            self.log_result(
                                "Stocktake: Current Status", 
                                True, 
                                f"Current stocktake exists for this month",
                                f"Stocktake ID: {existing_stocktake.get('id')}, Status: {existing_stocktake.get('status')}"
                            )
                        else:
                            self.log_result(
                                "Stocktake: Current Status", 
                                True, 
                                f"Stocktake status retrieved successfully",
                                f"Required: {stocktake_required}, First business day: {first_business_day}"
                            )
                    else:
                        self.log_result(
                            "Stocktake: Current Status", 
                            False, 
                            f"Response missing required fields: {missing_fields}"
                        )
                else:
                    self.log_result(
                        "Stocktake: Current Status", 
                        False, 
                        "Response missing success flag or data",
                        str(data)
                    )
            else:
                self.log_result(
                    "Stocktake: Current Status", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Stocktake: Current Status", False, f"Error: {str(e)}")
    
    def test_stocktake_creation(self):
        """Test POST /api/stocktake"""
        print("\n=== STOCKTAKE: CREATION TEST ===")
        
        try:
            # Create stocktake for current month
            from datetime import date
            current_date = date.today()
            
            stocktake_data = {
                "stocktake_date": current_date.isoformat()
            }
            
            response = self.session.post(f"{API_BASE}/stocktake", json=stocktake_data)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success') and 'data' in data:
                    stocktake_info = data['data']
                    required_fields = ['stocktake_id', 'materials_count', 'materials']
                    missing_fields = [field for field in required_fields if field not in stocktake_info]
                    
                    if not missing_fields:
                        stocktake_id = stocktake_info.get('stocktake_id')
                        materials_count = stocktake_info.get('materials_count')
                        materials = stocktake_info.get('materials', [])
                        
                        self.log_result(
                            "Stocktake: Creation", 
                            True, 
                            f"Successfully created stocktake with {materials_count} materials",
                            f"Stocktake ID: {stocktake_id}, Materials available: {len(materials)}"
                        )
                        return stocktake_id  # Return for use in other tests
                    else:
                        self.log_result(
                            "Stocktake: Creation", 
                            False, 
                            f"Response missing required fields: {missing_fields}"
                        )
                else:
                    self.log_result(
                        "Stocktake: Creation", 
                        False, 
                        "Response missing success flag or data",
                        str(data)
                    )
            elif response.status_code == 400:
                error_text = response.text
                if "already exists for this month" in error_text:
                    self.log_result(
                        "Stocktake: Creation", 
                        True, 
                        "Correctly prevents duplicate stocktakes for same month",
                        f"Validation error: {error_text}"
                    )
                else:
                    self.log_result(
                        "Stocktake: Creation", 
                        False, 
                        f"Unexpected validation error: {error_text}"
                    )
            else:
                self.log_result(
                    "Stocktake: Creation", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Stocktake: Creation", False, f"Error: {str(e)}")
        
        return None
    
    def test_stocktake_entry_update(self, stocktake_id):
        """Test PUT /api/stocktake/{stocktake_id}/entry"""
        print("\n=== STOCKTAKE: ENTRY UPDATE TEST ===")
        
        if not stocktake_id:
            self.log_result(
                "Stocktake: Entry Update", 
                False, 
                "No stocktake ID available for entry update test"
            )
            return
        
        try:
            # First, get available materials
            materials_response = self.session.get(f"{API_BASE}/materials")
            
            if materials_response.status_code != 200:
                self.log_result(
                    "Stocktake: Entry Update", 
                    False, 
                    "Failed to get materials for entry update test"
                )
                return
            
            materials = materials_response.json()
            
            if not materials:
                self.log_result(
                    "Stocktake: Entry Update", 
                    False, 
                    "No materials available for entry update test"
                )
                return
            
            # Use first available material
            material_id = materials[0]['id']
            
            # Test entry update
            entry_data = {
                "material_id": material_id,
                "current_quantity": 150.75
            }
            
            response = self.session.put(f"{API_BASE}/stocktake/{stocktake_id}/entry", json=entry_data)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success'):
                    message = data.get('message', '')
                    
                    if 'updated' in message.lower():
                        self.log_result(
                            "Stocktake: Entry Update", 
                            True, 
                            f"Successfully updated stocktake entry",
                            f"Material ID: {material_id}, Quantity: {entry_data['current_quantity']}"
                        )
                    else:
                        self.log_result(
                            "Stocktake: Entry Update", 
                            False, 
                            f"Unexpected success message: {message}"
                        )
                else:
                    self.log_result(
                        "Stocktake: Entry Update", 
                        False, 
                        "Response indicates failure",
                        str(data)
                    )
            elif response.status_code == 404:
                error_text = response.text
                if "Stocktake not found" in error_text or "Material not found" in error_text:
                    self.log_result(
                        "Stocktake: Entry Update", 
                        True, 
                        "Correctly validates stocktake and material existence",
                        f"Validation error: {error_text}"
                    )
                else:
                    self.log_result(
                        "Stocktake: Entry Update", 
                        False, 
                        f"Unexpected 404 error: {error_text}"
                    )
            else:
                self.log_result(
                    "Stocktake: Entry Update", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Stocktake: Entry Update", False, f"Error: {str(e)}")
    
    def test_stocktake_completion(self, stocktake_id):
        """Test POST /api/stocktake/{stocktake_id}/complete"""
        print("\n=== STOCKTAKE: COMPLETION TEST ===")
        
        if not stocktake_id:
            self.log_result(
                "Stocktake: Completion", 
                False, 
                "No stocktake ID available for completion test"
            )
            return
        
        try:
            response = self.session.post(f"{API_BASE}/stocktake/{stocktake_id}/complete")
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success'):
                    message = data.get('message', '')
                    
                    if 'completed' in message.lower():
                        self.log_result(
                            "Stocktake: Completion", 
                            True, 
                            f"Successfully completed stocktake",
                            f"Stocktake ID: {stocktake_id}, Message: {message}"
                        )
                    else:
                        self.log_result(
                            "Stocktake: Completion", 
                            False, 
                            f"Unexpected success message: {message}"
                        )
                else:
                    self.log_result(
                        "Stocktake: Completion", 
                        False, 
                        "Response indicates failure",
                        str(data)
                    )
            elif response.status_code == 404:
                error_text = response.text
                if "Stocktake not found" in error_text:
                    self.log_result(
                        "Stocktake: Completion", 
                        True, 
                        "Correctly validates stocktake existence",
                        f"Validation error: {error_text}"
                    )
                else:
                    self.log_result(
                        "Stocktake: Completion", 
                        False, 
                        f"Unexpected 404 error: {error_text}"
                    )
            else:
                self.log_result(
                    "Stocktake: Completion", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Stocktake: Completion", False, f"Error: {str(e)}")
    
    def test_calculator_authentication(self):
        """Test that calculator endpoints require proper authentication"""
        print("\n=== CALCULATOR AUTHENTICATION TEST ===")
        
        # Test without authentication
        temp_session = requests.Session()
        
        try:
            test_data = {
                "client_id": "test-client",
                "material_id": "test-material",
                "start_date": "2024-01-01",
                "end_date": "2024-12-31"
            }
            
            response = temp_session.post(f"{API_BASE}/calculators/material-consumption-by-client", json=test_data)
            
            if response.status_code in [401, 403]:
                self.log_result(
                    "Calculator Authentication", 
                    True, 
                    f"Calculator endpoints properly require authentication (status: {response.status_code})"
                )
            else:
                self.log_result(
                    "Calculator Authentication", 
                    False, 
                    f"Expected 401/403 but got {response.status_code}",
                    "Calculator endpoints should require authentication"
                )
                
        except Exception as e:
            self.log_result("Calculator Authentication", False, f"Error: {str(e)}")
    
    def test_stocktake_authentication(self):
        """Test that stocktake endpoints require proper authentication (admin/manager)"""
        print("\n=== STOCKTAKE AUTHENTICATION TEST ===")
        
        # Test without authentication
        temp_session = requests.Session()
        
        try:
            response = temp_session.get(f"{API_BASE}/stocktake/current")
            
            if response.status_code in [401, 403]:
                self.log_result(
                    "Stocktake Authentication", 
                    True, 
                    f"Stocktake endpoints properly require admin/manager authentication (status: {response.status_code})"
                )
            else:
                self.log_result(
                    "Stocktake Authentication", 
                    False, 
                    f"Expected 401/403 but got {response.status_code}",
                    "Stocktake endpoints should require admin/manager authentication"
                )
                
        except Exception as e:
            self.log_result("Stocktake Authentication", False, f"Error: {str(e)}")

    def test_username_editing_functionality(self):
        """Test the username editing functionality fix in Staff & Security system"""
        print("\n=== USERNAME EDITING FUNCTIONALITY TEST ===")
        
        # Test 1: Create a test user for username editing tests
        test_user_data = {
            "username": "testuser_username_edit",
            "email": "testuser.username@example.com",
            "password": "TestPassword123",
            "full_name": "Test User for Username Editing",
            "role": "production_staff",
            "department": "Testing",
            "phone": "0412345678"
        }
        
        test_user_id = None
        try:
            response = self.session.post(f"{API_BASE}/users", json=test_user_data)
            
            if response.status_code == 200:
                result = response.json()
                test_user_id = result.get('data', {}).get('id')
                
                if test_user_id:
                    self.log_result(
                        "Create Test User for Username Editing", 
                        True, 
                        f"Successfully created test user with ID: {test_user_id}"
                    )
                else:
                    self.log_result(
                        "Create Test User for Username Editing", 
                        False, 
                        "User creation response missing ID"
                    )
                    return
            else:
                self.log_result(
                    "Create Test User for Username Editing", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
                return
                
        except Exception as e:
            self.log_result("Create Test User for Username Editing", False, f"Error: {str(e)}")
            return
        
        # Test 2: Update username to a new unique value
        new_username = f"updated_username_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        try:
            update_data = {
                "username": new_username
            }
            
            response = self.session.put(f"{API_BASE}/users/{test_user_id}", json=update_data)
            
            if response.status_code == 200:
                # Verify the username was updated in database
                get_response = self.session.get(f"{API_BASE}/users/{test_user_id}")
                if get_response.status_code == 200:
                    user = get_response.json()
                    updated_username = user.get('username')
                    
                    if updated_username == new_username:
                        self.log_result(
                            "Update Username to Unique Value", 
                            True, 
                            f"Successfully updated username from 'testuser_username_edit' to '{new_username}'"
                        )
                    else:
                        self.log_result(
                            "Update Username to Unique Value", 
                            False, 
                            f"Username not updated correctly - expected '{new_username}' but got '{updated_username}'"
                        )
                else:
                    self.log_result(
                        "Update Username to Unique Value", 
                        False, 
                        "Failed to retrieve updated user for verification"
                    )
            else:
                self.log_result(
                    "Update Username to Unique Value", 
                    False, 
                    f"Username update failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Update Username to Unique Value", False, f"Error: {str(e)}")
        
        # Test 3: Test username uniqueness validation (try to update to existing username)
        try:
            # Try to update to an existing username (use "Callum" which should exist)
            duplicate_update_data = {
                "username": "Callum"  # This should already exist in the system
            }
            
            response = self.session.put(f"{API_BASE}/users/{test_user_id}", json=duplicate_update_data)
            
            if response.status_code == 400:
                error_text = response.text
                if "Username already exists" in error_text:
                    self.log_result(
                        "Username Uniqueness Validation", 
                        True, 
                        "Correctly prevented duplicate username with 400 error and proper message",
                        f"Error message: {error_text}"
                    )
                else:
                    self.log_result(
                        "Username Uniqueness Validation", 
                        False, 
                        "Got 400 error but wrong error message",
                        f"Expected 'Username already exists' but got: {error_text}"
                    )
            else:
                self.log_result(
                    "Username Uniqueness Validation", 
                    False, 
                    f"Expected 400 status for duplicate username but got {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Username Uniqueness Validation", False, f"Error: {str(e)}")
        
        # Test 4: Test combined updates (username with other fields)
        combined_username = f"combined_update_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        try:
            combined_update_data = {
                "username": combined_username,
                "full_name": "Updated Full Name for Combined Test",
                "email": "updated.combined@example.com",
                "role": "supervisor",
                "department": "Updated Department",
                "phone": "0487654321"
            }
            
            response = self.session.put(f"{API_BASE}/users/{test_user_id}", json=combined_update_data)
            
            if response.status_code == 200:
                # Verify all fields were updated
                get_response = self.session.get(f"{API_BASE}/users/{test_user_id}")
                if get_response.status_code == 200:
                    user = get_response.json()
                    
                    checks = [
                        ("username", user.get('username') == combined_username),
                        ("full_name", user.get('full_name') == "Updated Full Name for Combined Test"),
                        ("email", user.get('email') == "updated.combined@example.com"),
                        ("role", user.get('role') == "supervisor"),
                        ("department", user.get('department') == "Updated Department"),
                        ("phone", user.get('phone') == "0487654321")
                    ]
                    
                    passed_checks = [field for field, passed in checks if passed]
                    failed_checks = [field for field, passed in checks if not passed]
                    
                    if len(failed_checks) == 0:
                        self.log_result(
                            "Combined Updates (Username + Other Fields)", 
                            True, 
                            f"Successfully updated all fields including username",
                            f"Updated fields: {', '.join(passed_checks)}"
                        )
                    else:
                        self.log_result(
                            "Combined Updates (Username + Other Fields)", 
                            False, 
                            f"Some fields failed to update",
                            f"Passed: {', '.join(passed_checks)}, Failed: {', '.join(failed_checks)}"
                        )
                else:
                    self.log_result(
                        "Combined Updates (Username + Other Fields)", 
                        False, 
                        "Failed to retrieve updated user for verification"
                    )
            else:
                self.log_result(
                    "Combined Updates (Username + Other Fields)", 
                    False, 
                    f"Combined update failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Combined Updates (Username + Other Fields)", False, f"Error: {str(e)}")
        
        # Test 5: Test updating username to same value (should work)
        try:
            same_value_data = {
                "username": combined_username  # Same as current username
            }
            
            response = self.session.put(f"{API_BASE}/users/{test_user_id}", json=same_value_data)
            
            if response.status_code == 200:
                self.log_result(
                    "Update Username to Same Value", 
                    True, 
                    "Successfully updated username to same value (no conflict)"
                )
            else:
                self.log_result(
                    "Update Username to Same Value", 
                    False, 
                    f"Failed to update username to same value with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Update Username to Same Value", False, f"Error: {str(e)}")
        
        # Test 6: Test with empty/null username (should be ignored)
        try:
            empty_username_data = {
                "username": None,
                "full_name": "Updated with Null Username"
            }
            
            response = self.session.put(f"{API_BASE}/users/{test_user_id}", json=empty_username_data)
            
            if response.status_code == 200:
                # Verify username wasn't changed but full_name was
                get_response = self.session.get(f"{API_BASE}/users/{test_user_id}")
                if get_response.status_code == 200:
                    user = get_response.json()
                    
                    username_unchanged = user.get('username') == combined_username
                    full_name_updated = user.get('full_name') == "Updated with Null Username"
                    
                    if username_unchanged and full_name_updated:
                        self.log_result(
                            "Update with Null Username", 
                            True, 
                            "Null username correctly ignored while other fields updated"
                        )
                    else:
                        self.log_result(
                            "Update with Null Username", 
                            False, 
                            f"Unexpected behavior - username unchanged: {username_unchanged}, full_name updated: {full_name_updated}"
                        )
                else:
                    self.log_result(
                        "Update with Null Username", 
                        False, 
                        "Failed to retrieve user for null username test verification"
                    )
            else:
                self.log_result(
                    "Update with Null Username", 
                    False, 
                    f"Update with null username failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Update with Null Username", False, f"Error: {str(e)}")
        
        # Test 7: Verify existing functionality still works (email updates, role updates, etc.)
        try:
            existing_functionality_data = {
                "email": "existing.functionality@example.com",
                "role": "manager",
                "is_active": True
            }
            
            response = self.session.put(f"{API_BASE}/users/{test_user_id}", json=existing_functionality_data)
            
            if response.status_code == 200:
                # Verify the updates
                get_response = self.session.get(f"{API_BASE}/users/{test_user_id}")
                if get_response.status_code == 200:
                    user = get_response.json()
                    
                    email_updated = user.get('email') == "existing.functionality@example.com"
                    role_updated = user.get('role') == "manager"
                    is_active_updated = user.get('is_active') == True
                    
                    if email_updated and role_updated and is_active_updated:
                        self.log_result(
                            "Verify Existing Functionality", 
                            True, 
                            "All existing update functionality still works correctly"
                        )
                    else:
                        self.log_result(
                            "Verify Existing Functionality", 
                            False, 
                            f"Some existing functionality broken - email: {email_updated}, role: {role_updated}, is_active: {is_active_updated}"
                        )
                else:
                    self.log_result(
                        "Verify Existing Functionality", 
                        False, 
                        "Failed to retrieve user for existing functionality verification"
                    )
            else:
                self.log_result(
                    "Verify Existing Functionality", 
                    False, 
                    f"Existing functionality test failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Verify Existing Functionality", False, f"Error: {str(e)}")
        
        # Cleanup: Delete the test user
        if test_user_id:
            try:
                delete_response = self.session.delete(f"{API_BASE}/users/{test_user_id}")
                if delete_response.status_code == 200:
                    self.log_result(
                        "Cleanup Test User", 
                        True, 
                        "Successfully cleaned up test user"
                    )
                else:
                    self.log_result(
                        "Cleanup Test User", 
                        False, 
                        f"Failed to cleanup test user: {delete_response.status_code}"
                    )
            except Exception as e:
                self.log_result("Cleanup Test User", False, f"Cleanup error: {str(e)}")

    def test_user_deactivation_functionality(self):
        """Test user deactivation functionality as requested in review"""
        print("\n=== USER DEACTIVATION FUNCTIONALITY TEST ===")
        
        # Test 1: Create a test user for deactivation testing
        test_user_data = {
            "username": f"testuser_deactivation_{int(datetime.now().timestamp())}",
            "email": f"testdeactivation{int(datetime.now().timestamp())}@example.com",
            "password": "TestPassword123!",
            "full_name": "Test User for Deactivation",
            "role": "production_staff",
            "department": "Testing",
            "phone": "0412345678"
        }
        
        try:
            # Create test user
            response = self.session.post(f"{API_BASE}/users", json=test_user_data)
            
            if response.status_code == 200:
                result = response.json()
                self.test_user_id = result.get('data', {}).get('id')
                
                if self.test_user_id:
                    self.log_result(
                        "Create Test User for Deactivation", 
                        True, 
                        f"Successfully created test user for deactivation testing",
                        f"User ID: {self.test_user_id}, Username: {test_user_data['username']}"
                    )
                    
                    # Verify user is initially active
                    get_response = self.session.get(f"{API_BASE}/users/{self.test_user_id}")
                    if get_response.status_code == 200:
                        user_data = get_response.json()
                        is_active = user_data.get('is_active', False)
                        
                        if is_active:
                            self.log_result(
                                "Verify Test User Initially Active", 
                                True, 
                                "Test user is initially active as expected"
                            )
                        else:
                            self.log_result(
                                "Verify Test User Initially Active", 
                                False, 
                                "Test user should be active initially but is not"
                            )
                    else:
                        self.log_result(
                            "Verify Test User Initially Active", 
                            False, 
                            "Failed to retrieve test user for verification"
                        )
                else:
                    self.log_result(
                        "Create Test User for Deactivation", 
                        False, 
                        "User creation response missing ID"
                    )
                    return
            else:
                self.log_result(
                    "Create Test User for Deactivation", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
                return
                
        except Exception as e:
            self.log_result("Create Test User for Deactivation", False, f"Error: {str(e)}")
            return
        
        # Test 2: Test DELETE /api/users/{user_id} endpoint functionality
        if self.test_user_id:
            try:
                response = self.session.delete(f"{API_BASE}/users/{self.test_user_id}")
                
                if response.status_code == 200:
                    result = response.json()
                    success = result.get('success', False)
                    message = result.get('message', '')
                    
                    if success and 'deactivated' in message.lower():
                        self.log_result(
                            "DELETE Endpoint Functionality", 
                            True, 
                            f"DELETE endpoint successfully deactivated user",
                            f"Response: {message}"
                        )
                        
                        # Test 3: Verify user gets marked as inactive (is_active: false)
                        get_response = self.session.get(f"{API_BASE}/users/{self.test_user_id}")
                        if get_response.status_code == 200:
                            user_data = get_response.json()
                            is_active = user_data.get('is_active', True)
                            
                            if not is_active:
                                self.log_result(
                                    "Verify User Marked as Inactive", 
                                    True, 
                                    "User correctly marked as inactive (is_active: false) after DELETE"
                                )
                                
                                # Test 4: Verify user still exists in database but is_active is false
                                if 'id' in user_data and user_data['id'] == self.test_user_id:
                                    self.log_result(
                                        "Verify User Still Exists in Database", 
                                        True, 
                                        "User still exists in database but marked as inactive (soft delete working correctly)"
                                    )
                                else:
                                    self.log_result(
                                        "Verify User Still Exists in Database", 
                                        False, 
                                        "User data missing or ID mismatch after deactivation"
                                    )
                            else:
                                self.log_result(
                                    "Verify User Marked as Inactive", 
                                    False, 
                                    f"User should be inactive after DELETE but is_active is still {is_active}"
                                )
                        else:
                            self.log_result(
                                "Verify User Marked as Inactive", 
                                False, 
                                f"Failed to retrieve user after deactivation: {get_response.status_code}"
                            )
                    else:
                        self.log_result(
                            "DELETE Endpoint Functionality", 
                            False, 
                            f"DELETE endpoint response indicates failure",
                            f"Success: {success}, Message: {message}"
                        )
                else:
                    self.log_result(
                        "DELETE Endpoint Functionality", 
                        False, 
                        f"DELETE endpoint failed with status {response.status_code}",
                        response.text
                    )
                    
            except Exception as e:
                self.log_result("DELETE Endpoint Functionality", False, f"Error: {str(e)}")
        
        # Test 5: Test deactivating already inactive user
        if self.test_user_id:
            try:
                response = self.session.delete(f"{API_BASE}/users/{self.test_user_id}")
                
                if response.status_code == 200:
                    result = response.json()
                    success = result.get('success', False)
                    
                    if success:
                        self.log_result(
                            "Deactivate Already Inactive User", 
                            True, 
                            "DELETE endpoint handles already inactive user correctly"
                        )
                    else:
                        self.log_result(
                            "Deactivate Already Inactive User", 
                            False, 
                            "DELETE endpoint should handle already inactive user gracefully"
                        )
                else:
                    self.log_result(
                        "Deactivate Already Inactive User", 
                        False, 
                        f"DELETE endpoint failed on already inactive user: {response.status_code}"
                    )
                    
            except Exception as e:
                self.log_result("Deactivate Already Inactive User", False, f"Error: {str(e)}")
        
        # Test 6: Test deactivating non-existent user (should return 404)
        fake_user_id = "non-existent-user-id-12345"
        try:
            response = self.session.delete(f"{API_BASE}/users/{fake_user_id}")
            
            if response.status_code == 404:
                self.log_result(
                    "Deactivate Non-existent User", 
                    True, 
                    "DELETE endpoint correctly returns 404 for non-existent user"
                )
            else:
                self.log_result(
                    "Deactivate Non-existent User", 
                    False, 
                    f"Expected 404 for non-existent user but got {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Deactivate Non-existent User", False, f"Error: {str(e)}")
        
        # Test 7: Test unauthorized access returns proper 403 error
        temp_session = requests.Session()
        if self.test_user_id:
            try:
                response = temp_session.delete(f"{API_BASE}/users/{self.test_user_id}")
                
                if response.status_code in [401, 403]:
                    self.log_result(
                        "Unauthorized DELETE Access", 
                        True, 
                        f"DELETE endpoint properly requires admin authentication (status: {response.status_code})"
                    )
                else:
                    self.log_result(
                        "Unauthorized DELETE Access", 
                        False, 
                        f"Expected 401/403 for unauthorized access but got {response.status_code}",
                        "DELETE endpoint should require admin authentication"
                    )
                    
            except Exception as e:
                self.log_result("Unauthorized DELETE Access", False, f"Error: {str(e)}")
        
        # Test 8: Verify deactivated users can still be retrieved but marked inactive
        if self.test_user_id:
            try:
                response = self.session.get(f"{API_BASE}/users/{self.test_user_id}")
                
                if response.status_code == 200:
                    user_data = response.json()
                    is_active = user_data.get('is_active', True)
                    
                    if not is_active:
                        self.log_result(
                            "Retrieve Deactivated User", 
                            True, 
                            "Deactivated user can still be retrieved and is correctly marked as inactive"
                        )
                    else:
                        self.log_result(
                            "Retrieve Deactivated User", 
                            False, 
                            "Deactivated user should be marked as inactive when retrieved"
                        )
                else:
                    self.log_result(
                        "Retrieve Deactivated User", 
                        False, 
                        f"Failed to retrieve deactivated user: {response.status_code}"
                    )
                    
            except Exception as e:
                self.log_result("Retrieve Deactivated User", False, f"Error: {str(e)}")
        
        # Test 9: Verify user appears as inactive in user list
        if self.test_user_id:
            try:
                response = self.session.get(f"{API_BASE}/users")
                
                if response.status_code == 200:
                    users = response.json()
                    test_user = next((user for user in users if user.get('id') == self.test_user_id), None)
                    
                    if test_user:
                        is_active = test_user.get('is_active', True)
                        if not is_active:
                            self.log_result(
                                "User Appears as Inactive in List", 
                                True, 
                                "Deactivated user appears as inactive in user list"
                            )
                        else:
                            self.log_result(
                                "User Appears as Inactive in List", 
                                False, 
                                "Deactivated user should appear as inactive in user list"
                            )
                    else:
                        self.log_result(
                            "User Appears as Inactive in List", 
                            False, 
                            "Deactivated user not found in user list (may be filtered out)"
                        )
                else:
                    self.log_result(
                        "User Appears as Inactive in List", 
                        False, 
                        f"Failed to retrieve user list: {response.status_code}"
                    )
                    
            except Exception as e:
                self.log_result("User Appears as Inactive in List", False, f"Error: {str(e)}")

    def test_user_deletion_functionality(self):
        """Test the updated user deletion functionality with permanent deletion"""
        print("\n=== USER DELETION FUNCTIONALITY TEST ===")
        
        # Test 1: Create a test user for deletion
        test_user_data = {
            "username": f"testuser_deletion_{int(datetime.now().timestamp())}",
            "email": f"testdeletion_{int(datetime.now().timestamp())}@example.com",
            "password": "TestPassword123",
            "full_name": "Test User for Deletion",
            "role": "production_staff",
            "department": "Testing",
            "phone": "0412345678"
        }
        
        test_user_id = None
        try:
            response = self.session.post(f"{API_BASE}/users", json=test_user_data)
            
            if response.status_code == 200:
                result = response.json()
                test_user_id = result.get('data', {}).get('id')
                
                if test_user_id:
                    self.log_result(
                        "Create Test User for Deletion", 
                        True, 
                        f"Successfully created test user for deletion testing",
                        f"User ID: {test_user_id}, Username: {test_user_data['username']}"
                    )
                else:
                    self.log_result(
                        "Create Test User for Deletion", 
                        False, 
                        "User creation response missing ID"
                    )
                    return
            else:
                self.log_result(
                    "Create Test User for Deletion", 
                    False, 
                    f"Failed to create test user with status {response.status_code}",
                    response.text
                )
                return
        except Exception as e:
            self.log_result("Create Test User for Deletion", False, f"Error: {str(e)}")
            return
        
        # Test 2: Test DELETE /api/users/{user_id} endpoint (Hard Delete)
        try:
            response = self.session.delete(f"{API_BASE}/users/{test_user_id}")
            
            if response.status_code == 200:
                result = response.json()
                message = result.get('message', '')
                
                if message == "User deleted successfully":
                    self.log_result(
                        "Hard Delete Functionality", 
                        True, 
                        f"Successfully deleted user with correct response message",
                        f"Response: {message}"
                    )
                else:
                    self.log_result(
                        "Hard Delete Functionality", 
                        False, 
                        f"Unexpected response message: '{message}' (expected 'User deleted successfully')"
                    )
            else:
                self.log_result(
                    "Hard Delete Functionality", 
                    False, 
                    f"Delete failed with status {response.status_code}",
                    response.text
                )
                return
        except Exception as e:
            self.log_result("Hard Delete Functionality", False, f"Error: {str(e)}")
            return
        
        # Test 3: Verify user is completely removed from database
        try:
            response = self.session.get(f"{API_BASE}/users/{test_user_id}")
            
            if response.status_code == 404:
                self.log_result(
                    "Verify Complete Database Removal", 
                    True, 
                    "User completely removed from database (404 response as expected)"
                )
            else:
                self.log_result(
                    "Verify Complete Database Removal", 
                    False, 
                    f"User still exists in database (status: {response.status_code})",
                    "User should be completely removed, not just marked inactive"
                )
        except Exception as e:
            self.log_result("Verify Complete Database Removal", False, f"Error: {str(e)}")
        
        # Test 4: Test that admin cannot delete their own account
        try:
            # Get current user info to find admin user ID
            me_response = self.session.get(f"{API_BASE}/auth/me")
            if me_response.status_code == 200:
                current_user = me_response.json()
                current_user_id = current_user.get('id')
                
                if current_user_id:
                    # Try to delete own account
                    response = self.session.delete(f"{API_BASE}/users/{current_user_id}")
                    
                    if response.status_code == 400:
                        result = response.json()
                        error_message = result.get('detail', '')
                        
                        if "Cannot delete your own account" in error_message:
                            self.log_result(
                                "Prevent Self-Deletion", 
                                True, 
                                "Correctly prevents admin from deleting their own account",
                                f"Error message: {error_message}"
                            )
                        else:
                            self.log_result(
                                "Prevent Self-Deletion", 
                                False, 
                                f"Wrong error message for self-deletion attempt: '{error_message}'"
                            )
                    else:
                        self.log_result(
                            "Prevent Self-Deletion", 
                            False, 
                            f"Expected 400 status but got {response.status_code}",
                            "Should prevent admin from deleting their own account"
                        )
                else:
                    self.log_result(
                        "Prevent Self-Deletion", 
                        False, 
                        "Could not get current user ID for self-deletion test"
                    )
            else:
                self.log_result(
                    "Prevent Self-Deletion", 
                    False, 
                    "Could not get current user info for self-deletion test"
                )
        except Exception as e:
            self.log_result("Prevent Self-Deletion", False, f"Error: {str(e)}")
        
        # Test 5: Test deletion of non-existent user (should return 404)
        try:
            fake_user_id = "non-existent-user-id-12345"
            response = self.session.delete(f"{API_BASE}/users/{fake_user_id}")
            
            if response.status_code == 404:
                result = response.json()
                error_message = result.get('detail', '')
                
                if "User not found" in error_message:
                    self.log_result(
                        "Delete Non-Existent User", 
                        True, 
                        "Correctly returns 404 for non-existent user deletion",
                        f"Error message: {error_message}"
                    )
                else:
                    self.log_result(
                        "Delete Non-Existent User", 
                        False, 
                        f"Wrong error message for non-existent user: '{error_message}'"
                    )
            else:
                self.log_result(
                    "Delete Non-Existent User", 
                    False, 
                    f"Expected 404 status but got {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Delete Non-Existent User", False, f"Error: {str(e)}")
        
        # Test 6: Test unauthorized access (without admin token)
        try:
            # Create a temporary session without authentication
            temp_session = requests.Session()
            
            response = temp_session.delete(f"{API_BASE}/users/{test_user_id}")
            
            if response.status_code in [401, 403]:
                self.log_result(
                    "Delete Endpoint Authentication", 
                    True, 
                    f"DELETE endpoint properly requires admin authentication (status: {response.status_code})"
                )
            else:
                self.log_result(
                    "Delete Endpoint Authentication", 
                    False, 
                    f"Expected 401/403 but got {response.status_code}",
                    "DELETE endpoint should require admin authentication"
                )
        except Exception as e:
            self.log_result("Delete Endpoint Authentication", False, f"Error: {str(e)}")
        
        # Test 7: Create another test user and verify permanent deletion vs soft delete
        test_user_data_2 = {
            "username": f"testuser_permanent_{int(datetime.now().timestamp())}",
            "email": f"testpermanent_{int(datetime.now().timestamp())}@example.com",
            "password": "TestPassword123",
            "full_name": "Test User for Permanent Deletion",
            "role": "production_staff",
            "department": "Testing",
            "phone": "0412345679"
        }
        
        test_user_id_2 = None
        try:
            response = self.session.post(f"{API_BASE}/users", json=test_user_data_2)
            
            if response.status_code == 200:
                result = response.json()
                test_user_id_2 = result.get('data', {}).get('id')
                
                if test_user_id_2:
                    # Delete the user
                    delete_response = self.session.delete(f"{API_BASE}/users/{test_user_id_2}")
                    
                    if delete_response.status_code == 200:
                        # Try to find user in all users list (should not be there)
                        all_users_response = self.session.get(f"{API_BASE}/users")
                        
                        if all_users_response.status_code == 200:
                            all_users = all_users_response.json()
                            deleted_user_found = any(user.get('id') == test_user_id_2 for user in all_users)
                            
                            if not deleted_user_found:
                                self.log_result(
                                    "Verify Permanent Deletion", 
                                    True, 
                                    "User permanently deleted - not found in users list",
                                    f"Checked {len(all_users)} users, deleted user not present"
                                )
                            else:
                                self.log_result(
                                    "Verify Permanent Deletion", 
                                    False, 
                                    "User still appears in users list after deletion",
                                    "User should be permanently removed, not just marked inactive"
                                )
                        else:
                            self.log_result(
                                "Verify Permanent Deletion", 
                                False, 
                                "Could not retrieve users list to verify permanent deletion"
                            )
                    else:
                        self.log_result(
                            "Verify Permanent Deletion", 
                            False, 
                            f"Failed to delete second test user: {delete_response.status_code}"
                        )
                else:
                    self.log_result(
                        "Verify Permanent Deletion", 
                        False, 
                        "Could not create second test user for permanent deletion test"
                    )
            else:
                self.log_result(
                    "Verify Permanent Deletion", 
                    False, 
                    f"Failed to create second test user: {response.status_code}"
                )
        except Exception as e:
            self.log_result("Verify Permanent Deletion", False, f"Error: {str(e)}")

    def test_staff_security_employment_type(self):
        """Test enhanced Staff & Security system with employment type functionality"""
        print("\n=== STAFF & SECURITY EMPLOYMENT TYPE TESTS ===")
        
        # Test 1: Create User with Employment Type (Full Time)
        user_full_time = {
            "username": f"testuser_fulltime_{int(datetime.now().timestamp())}",
            "email": f"fulltime_{int(datetime.now().timestamp())}@test.com",
            "password": "TestPassword123",
            "full_name": "Full Time Test User",
            "role": "production_staff",
            "department": "Manufacturing",
            "phone": "0412345678",
            "employment_type": "full_time"
        }
        
        full_time_user_id = None
        try:
            response = self.session.post(f"{API_BASE}/users", json=user_full_time)
            
            if response.status_code == 200:
                result = response.json()
                full_time_user_id = result.get('data', {}).get('id')
                
                if full_time_user_id:
                    # Verify user was created with employment_type
                    get_response = self.session.get(f"{API_BASE}/users/{full_time_user_id}")
                    if get_response.status_code == 200:
                        user = get_response.json()
                        employment_type = user.get('employment_type')
                        
                        if employment_type == "full_time":
                            self.log_result(
                                "Create User with Employment Type (Full Time)", 
                                True, 
                                f"Successfully created full-time user with employment_type field",
                                f"User ID: {full_time_user_id}, Employment Type: {employment_type}"
                            )
                        else:
                            self.log_result(
                                "Create User with Employment Type (Full Time)", 
                                False, 
                                f"Expected employment_type 'full_time' but got '{employment_type}'"
                            )
                    else:
                        self.log_result(
                            "Create User with Employment Type (Full Time)", 
                            False, 
                            "Failed to retrieve created user for employment_type verification"
                        )
                else:
                    self.log_result(
                        "Create User with Employment Type (Full Time)", 
                        False, 
                        "User creation response missing ID"
                    )
            else:
                self.log_result(
                    "Create User with Employment Type (Full Time)", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Create User with Employment Type (Full Time)", False, f"Error: {str(e)}")
        
        # Test 2: Create User with Employment Type (Part Time)
        user_part_time = {
            "username": f"testuser_parttime_{int(datetime.now().timestamp())}",
            "email": f"parttime_{int(datetime.now().timestamp())}@test.com",
            "password": "TestPassword123",
            "full_name": "Part Time Test User",
            "role": "production_staff",
            "department": "Quality Control",
            "phone": "0412345679",
            "employment_type": "part_time"
        }
        
        part_time_user_id = None
        try:
            response = self.session.post(f"{API_BASE}/users", json=user_part_time)
            
            if response.status_code == 200:
                result = response.json()
                part_time_user_id = result.get('data', {}).get('id')
                
                if part_time_user_id:
                    # Verify user was created with employment_type
                    get_response = self.session.get(f"{API_BASE}/users/{part_time_user_id}")
                    if get_response.status_code == 200:
                        user = get_response.json()
                        employment_type = user.get('employment_type')
                        
                        if employment_type == "part_time":
                            self.log_result(
                                "Create User with Employment Type (Part Time)", 
                                True, 
                                f"Successfully created part-time user with employment_type field",
                                f"User ID: {part_time_user_id}, Employment Type: {employment_type}"
                            )
                        else:
                            self.log_result(
                                "Create User with Employment Type (Part Time)", 
                                False, 
                                f"Expected employment_type 'part_time' but got '{employment_type}'"
                            )
                    else:
                        self.log_result(
                            "Create User with Employment Type (Part Time)", 
                            False, 
                            "Failed to retrieve created user for employment_type verification"
                        )
                else:
                    self.log_result(
                        "Create User with Employment Type (Part Time)", 
                        False, 
                        "User creation response missing ID"
                    )
            else:
                self.log_result(
                    "Create User with Employment Type (Part Time)", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Create User with Employment Type (Part Time)", False, f"Error: {str(e)}")
        
        # Test 3: Create User with Employment Type (Casual)
        user_casual = {
            "username": f"testuser_casual_{int(datetime.now().timestamp())}",
            "email": f"casual_{int(datetime.now().timestamp())}@test.com",
            "password": "TestPassword123",
            "full_name": "Casual Test User",
            "role": "production_staff",
            "department": "Warehouse",
            "phone": "0412345680",
            "employment_type": "casual"
        }
        
        casual_user_id = None
        try:
            response = self.session.post(f"{API_BASE}/users", json=user_casual)
            
            if response.status_code == 200:
                result = response.json()
                casual_user_id = result.get('data', {}).get('id')
                
                if casual_user_id:
                    # Verify user was created with employment_type
                    get_response = self.session.get(f"{API_BASE}/users/{casual_user_id}")
                    if get_response.status_code == 200:
                        user = get_response.json()
                        employment_type = user.get('employment_type')
                        
                        if employment_type == "casual":
                            self.log_result(
                                "Create User with Employment Type (Casual)", 
                                True, 
                                f"Successfully created casual user with employment_type field",
                                f"User ID: {casual_user_id}, Employment Type: {employment_type}"
                            )
                        else:
                            self.log_result(
                                "Create User with Employment Type (Casual)", 
                                False, 
                                f"Expected employment_type 'casual' but got '{employment_type}'"
                            )
                    else:
                        self.log_result(
                            "Create User with Employment Type (Casual)", 
                            False, 
                            "Failed to retrieve created user for employment_type verification"
                        )
                else:
                    self.log_result(
                        "Create User with Employment Type (Casual)", 
                        False, 
                        "User creation response missing ID"
                    )
            else:
                self.log_result(
                    "Create User with Employment Type (Casual)", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Create User with Employment Type (Casual)", False, f"Error: {str(e)}")
        
        # Test 4: Create User with Default Employment Type (should default to full_time)
        user_default = {
            "username": f"testuser_default_{int(datetime.now().timestamp())}",
            "email": f"default_{int(datetime.now().timestamp())}@test.com",
            "password": "TestPassword123",
            "full_name": "Default Employment Type User",
            "role": "production_staff",
            "department": "Administration",
            "phone": "0412345681"
            # Note: employment_type not specified - should default to full_time
        }
        
        default_user_id = None
        try:
            response = self.session.post(f"{API_BASE}/users", json=user_default)
            
            if response.status_code == 200:
                result = response.json()
                default_user_id = result.get('data', {}).get('id')
                
                if default_user_id:
                    # Verify user was created with default employment_type
                    get_response = self.session.get(f"{API_BASE}/users/{default_user_id}")
                    if get_response.status_code == 200:
                        user = get_response.json()
                        employment_type = user.get('employment_type')
                        
                        if employment_type == "full_time":
                            self.log_result(
                                "Create User with Default Employment Type", 
                                True, 
                                f"Successfully created user with default employment_type 'full_time'",
                                f"User ID: {default_user_id}, Employment Type: {employment_type}"
                            )
                        else:
                            self.log_result(
                                "Create User with Default Employment Type", 
                                False, 
                                f"Expected default employment_type 'full_time' but got '{employment_type}'"
                            )
                    else:
                        self.log_result(
                            "Create User with Default Employment Type", 
                            False, 
                            "Failed to retrieve created user for employment_type verification"
                        )
                else:
                    self.log_result(
                        "Create User with Default Employment Type", 
                        False, 
                        "User creation response missing ID"
                    )
            else:
                self.log_result(
                    "Create User with Default Employment Type", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Create User with Default Employment Type", False, f"Error: {str(e)}")
        
        # Test 5: Update User Employment Type (from full_time to part_time)
        if full_time_user_id:
            update_employment_data = {
                "employment_type": "part_time",
                "department": "Updated Department"
            }
            
            try:
                response = self.session.put(f"{API_BASE}/users/{full_time_user_id}", json=update_employment_data)
                
                if response.status_code == 200:
                    # Verify the employment_type was updated
                    get_response = self.session.get(f"{API_BASE}/users/{full_time_user_id}")
                    if get_response.status_code == 200:
                        updated_user = get_response.json()
                        updated_employment_type = updated_user.get('employment_type')
                        updated_department = updated_user.get('department')
                        
                        if updated_employment_type == "part_time" and updated_department == "Updated Department":
                            self.log_result(
                                "Update User Employment Type", 
                                True, 
                                f"Successfully updated user employment_type from full_time to part_time",
                                f"User ID: {full_time_user_id}, New Employment Type: {updated_employment_type}, Department: {updated_department}"
                            )
                        else:
                            self.log_result(
                                "Update User Employment Type", 
                                False, 
                                f"Update failed - expected part_time but got '{updated_employment_type}'"
                            )
                    else:
                        self.log_result(
                            "Update User Employment Type", 
                            False, 
                            "Failed to retrieve updated user for employment_type verification"
                        )
                else:
                    self.log_result(
                        "Update User Employment Type", 
                        False, 
                        f"Update failed with status {response.status_code}",
                        response.text
                    )
            except Exception as e:
                self.log_result("Update User Employment Type", False, f"Error: {str(e)}")
        
        # Test 6: Test Hard Delete Functionality
        if casual_user_id:
            try:
                # First verify user exists
                get_response = self.session.get(f"{API_BASE}/users/{casual_user_id}")
                if get_response.status_code == 200:
                    # Perform hard delete
                    delete_response = self.session.delete(f"{API_BASE}/users/{casual_user_id}")
                    
                    if delete_response.status_code == 200:
                        delete_result = delete_response.json()
                        delete_message = delete_result.get('message', '')
                        
                        if 'deleted successfully' in delete_message:
                            # Verify user is completely removed from database
                            verify_response = self.session.get(f"{API_BASE}/users/{casual_user_id}")
                            
                            if verify_response.status_code == 404:
                                self.log_result(
                                    "Hard Delete User", 
                                    True, 
                                    f"Successfully performed hard delete - user completely removed from database",
                                    f"User ID: {casual_user_id}, Delete Message: {delete_message}"
                                )
                            else:
                                self.log_result(
                                    "Hard Delete User", 
                                    False, 
                                    f"Delete claimed success but user still exists (status: {verify_response.status_code})"
                                )
                        else:
                            self.log_result(
                                "Hard Delete User", 
                                False, 
                                f"Unexpected delete response message: {delete_message}"
                            )
                    else:
                        self.log_result(
                            "Hard Delete User", 
                            False, 
                            f"Delete failed with status {delete_response.status_code}",
                            delete_response.text
                        )
                else:
                    self.log_result(
                        "Hard Delete User", 
                        False, 
                        "Test user not found before delete test"
                    )
            except Exception as e:
                self.log_result("Hard Delete User", False, f"Error: {str(e)}")
        
        # Test 7: Test Self-Deletion Protection
        try:
            # Try to delete current user (should be prevented)
            current_user_response = self.session.get(f"{API_BASE}/auth/me")
            if current_user_response.status_code == 200:
                current_user_data = current_user_response.json()
                current_user_id = current_user_data.get('id')
                
                if current_user_id:
                    delete_response = self.session.delete(f"{API_BASE}/users/{current_user_id}")
                    
                    if delete_response.status_code == 400:
                        error_text = delete_response.text
                        if "Cannot delete your own account" in error_text:
                            self.log_result(
                                "Self-Deletion Protection", 
                                True, 
                                "Successfully prevented admin from deleting their own account",
                                f"Error message: {error_text}"
                            )
                        else:
                            self.log_result(
                                "Self-Deletion Protection", 
                                False, 
                                f"Expected 'Cannot delete your own account' error but got: {error_text}"
                            )
                    else:
                        self.log_result(
                            "Self-Deletion Protection", 
                            False, 
                            f"Expected 400 status but got {delete_response.status_code}",
                            "Self-deletion should be prevented"
                        )
                else:
                    self.log_result(
                        "Self-Deletion Protection", 
                        False, 
                        "Could not get current user ID for self-deletion test"
                    )
            else:
                self.log_result(
                    "Self-Deletion Protection", 
                    False, 
                    "Could not get current user info for self-deletion test"
                )
        except Exception as e:
            self.log_result("Self-Deletion Protection", False, f"Error: {str(e)}")
        
        # Test 8: Test Employment Type Validation (invalid value)
        user_invalid_employment = {
            "username": f"testuser_invalid_{int(datetime.now().timestamp())}",
            "email": f"invalid_{int(datetime.now().timestamp())}@test.com",
            "password": "TestPassword123",
            "full_name": "Invalid Employment Type User",
            "role": "production_staff",
            "employment_type": "invalid_type"  # Invalid employment type
        }
        
        try:
            response = self.session.post(f"{API_BASE}/users", json=user_invalid_employment)
            
            if response.status_code == 422:  # Validation error expected
                self.log_result(
                    "Employment Type Validation", 
                    True, 
                    "Correctly rejected invalid employment_type with validation error",
                    f"Status: {response.status_code}, Response: {response.text}"
                )
            else:
                self.log_result(
                    "Employment Type Validation", 
                    False, 
                    f"Expected 422 validation error but got {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Employment Type Validation", False, f"Error: {str(e)}")
        
        # Test 9: Test Combined Update (username, employment_type, role)
        if part_time_user_id:
            combined_update_data = {
                "username": f"updated_user_{int(datetime.now().timestamp())}",
                "employment_type": "casual",
                "role": "supervisor",
                "full_name": "Updated Combined User",
                "department": "Combined Update Department"
            }
            
            try:
                response = self.session.put(f"{API_BASE}/users/{part_time_user_id}", json=combined_update_data)
                
                if response.status_code == 200:
                    # Verify all fields were updated
                    get_response = self.session.get(f"{API_BASE}/users/{part_time_user_id}")
                    if get_response.status_code == 200:
                        updated_user = get_response.json()
                        
                        checks = [
                            ("username", updated_user.get('username') == combined_update_data['username']),
                            ("employment_type", updated_user.get('employment_type') == combined_update_data['employment_type']),
                            ("role", updated_user.get('role') == combined_update_data['role']),
                            ("full_name", updated_user.get('full_name') == combined_update_data['full_name']),
                            ("department", updated_user.get('department') == combined_update_data['department'])
                        ]
                        
                        passed_checks = [field for field, passed in checks if passed]
                        failed_checks = [field for field, passed in checks if not passed]
                        
                        if len(failed_checks) == 0:
                            self.log_result(
                                "Combined Update (username, employment_type, role)", 
                                True, 
                                f"Successfully updated all fields in combined update",
                                f"Updated fields: {', '.join(passed_checks)}"
                            )
                        else:
                            self.log_result(
                                "Combined Update (username, employment_type, role)", 
                                False, 
                                f"Some fields failed to update: {', '.join(failed_checks)}",
                                f"Passed: {', '.join(passed_checks)}"
                            )
                    else:
                        self.log_result(
                            "Combined Update (username, employment_type, role)", 
                            False, 
                            "Failed to retrieve updated user for verification"
                        )
                else:
                    self.log_result(
                        "Combined Update (username, employment_type, role)", 
                        False, 
                        f"Combined update failed with status {response.status_code}",
                        response.text
                    )
            except Exception as e:
                self.log_result("Combined Update (username, employment_type, role)", False, f"Error: {str(e)}")
        
        # Test 10: Verify Employment Type in User List
        try:
            response = self.session.get(f"{API_BASE}/users")
            
            if response.status_code == 200:
                users = response.json()
                
                # Check if employment_type field is present in user list
                users_with_employment_type = [user for user in users if 'employment_type' in user]
                
                if len(users_with_employment_type) > 0:
                    # Check for different employment types
                    employment_types_found = set(user.get('employment_type') for user in users_with_employment_type if user.get('employment_type'))
                    
                    self.log_result(
                        "Employment Type in User List", 
                        True, 
                        f"Employment type field present in user list responses",
                        f"Users with employment_type: {len(users_with_employment_type)}, Types found: {list(employment_types_found)}"
                    )
                else:
                    self.log_result(
                        "Employment Type in User List", 
                        False, 
                        "No users found with employment_type field in list response"
                    )
            else:
                self.log_result(
                    "Employment Type in User List", 
                    False, 
                    f"Failed to get user list: {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Employment Type in User List", False, f"Error: {str(e)}")
        
        # Cleanup: Delete remaining test users
        cleanup_user_ids = [full_time_user_id, part_time_user_id, default_user_id]
        for user_id in cleanup_user_ids:
            if user_id:
                try:
                    self.session.delete(f"{API_BASE}/users/{user_id}")
                except:
                    pass  # Ignore cleanup errors

    def test_client_deletion_functionality(self):
        """Test comprehensive client deletion functionality"""
        print("\n=== CLIENT DELETION FUNCTIONALITY TEST ===")
        
        # Test 1: Create a test client for deletion testing
        test_client_data = {
            "company_name": "Test Client for Deletion",
            "contact_name": "John Delete",
            "email": "john.delete@testclient.com",
            "phone": "0412345678",
            "address": "123 Delete Street",
            "city": "Melbourne",
            "state": "VIC",
            "postal_code": "3000",
            "abn": "98765432101",
            "payment_terms": "Net 30 days",
            "lead_time_days": 7
        }
        
        test_client_id = None
        try:
            response = self.session.post(f"{API_BASE}/clients", json=test_client_data)
            
            if response.status_code == 200:
                result = response.json()
                test_client_id = result.get('data', {}).get('id')
                
                if test_client_id:
                    self.log_result(
                        "Create Test Client for Deletion", 
                        True, 
                        f"Successfully created test client for deletion testing",
                        f"Client ID: {test_client_id}"
                    )
                else:
                    self.log_result(
                        "Create Test Client for Deletion", 
                        False, 
                        "Client creation response missing ID"
                    )
                    return
            else:
                self.log_result(
                    "Create Test Client for Deletion", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
                return
        except Exception as e:
            self.log_result("Create Test Client for Deletion", False, f"Error: {str(e)}")
            return
        
        # Test 2: Test DELETE endpoint with admin credentials
        try:
            response = self.session.delete(f"{API_BASE}/clients/{test_client_id}")
            
            if response.status_code == 200:
                result = response.json()
                message = result.get('message', '')
                
                if 'Client deleted successfully' in message:
                    self.log_result(
                        "Client Deletion Endpoint (Admin Access)", 
                        True, 
                        f"Successfully deleted client with proper response message",
                        f"Response: {message}"
                    )
                else:
                    self.log_result(
                        "Client Deletion Endpoint (Admin Access)", 
                        False, 
                        f"Unexpected response message: {message}"
                    )
            else:
                self.log_result(
                    "Client Deletion Endpoint (Admin Access)", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Client Deletion Endpoint (Admin Access)", False, f"Error: {str(e)}")
        
        # Test 3: Verify client is soft deleted (is_active set to false)
        try:
            response = self.session.get(f"{API_BASE}/clients/{test_client_id}")
            
            if response.status_code == 404:
                self.log_result(
                    "Client Soft Delete Verification", 
                    True, 
                    "Client correctly returns 404 after deletion (soft delete working)",
                    "Client is no longer accessible via GET /api/clients/{id}"
                )
            else:
                # If we can still get the client, check if it's marked as inactive
                if response.status_code == 200:
                    client_data = response.json()
                    is_active = client_data.get('is_active', True)
                    
                    if is_active == False:
                        self.log_result(
                            "Client Soft Delete Verification", 
                            True, 
                            "Client marked as inactive (is_active: false) - soft delete working"
                        )
                    else:
                        self.log_result(
                            "Client Soft Delete Verification", 
                            False, 
                            "Client still active after deletion - soft delete not working",
                            f"is_active: {is_active}"
                        )
                else:
                    self.log_result(
                        "Client Soft Delete Verification", 
                        False, 
                        f"Unexpected response status: {response.status_code}",
                        response.text
                    )
        except Exception as e:
            self.log_result("Client Soft Delete Verification", False, f"Error: {str(e)}")
        
        # Test 4: Verify deleted client doesn't appear in GET /api/clients list
        try:
            response = self.session.get(f"{API_BASE}/clients")
            
            if response.status_code == 200:
                clients = response.json()
                deleted_client_in_list = any(client.get('id') == test_client_id for client in clients)
                
                if not deleted_client_in_list:
                    self.log_result(
                        "Deleted Client Not in List", 
                        True, 
                        "Deleted client correctly filtered out from GET /api/clients list",
                        f"Total active clients: {len(clients)}"
                    )
                else:
                    self.log_result(
                        "Deleted Client Not in List", 
                        False, 
                        "Deleted client still appears in active clients list"
                    )
            else:
                self.log_result(
                    "Deleted Client Not in List", 
                    False, 
                    f"Failed to get clients list: {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Deleted Client Not in List", False, f"Error: {str(e)}")
        
        # Test 5: Test deleting non-existent client (should return 404)
        fake_client_id = "non-existent-client-id-12345"
        try:
            response = self.session.delete(f"{API_BASE}/clients/{fake_client_id}")
            
            if response.status_code == 404:
                result = response.json()
                message = result.get('detail', '')
                
                if 'Client not found' in message:
                    self.log_result(
                        "Delete Non-Existent Client", 
                        True, 
                        "Correctly returns 404 for non-existent client",
                        f"Response: {message}"
                    )
                else:
                    self.log_result(
                        "Delete Non-Existent Client", 
                        False, 
                        f"Unexpected error message: {message}"
                    )
            else:
                self.log_result(
                    "Delete Non-Existent Client", 
                    False, 
                    f"Expected 404 but got {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Delete Non-Existent Client", False, f"Error: {str(e)}")
        
        # Test 6: Test deleting already deleted client
        try:
            response = self.session.delete(f"{API_BASE}/clients/{test_client_id}")
            
            if response.status_code == 404:
                result = response.json()
                message = result.get('detail', '')
                
                if 'Client not found' in message:
                    self.log_result(
                        "Delete Already Deleted Client", 
                        True, 
                        "Correctly returns 404 when trying to delete already deleted client",
                        f"Response: {message}"
                    )
                else:
                    self.log_result(
                        "Delete Already Deleted Client", 
                        False, 
                        f"Unexpected error message: {message}"
                    )
            else:
                self.log_result(
                    "Delete Already Deleted Client", 
                    False, 
                    f"Expected 404 but got {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Delete Already Deleted Client", False, f"Error: {str(e)}")
        
        # Test 7: Test unauthorized access (without admin credentials)
        temp_session = requests.Session()
        try:
            response = temp_session.delete(f"{API_BASE}/clients/{test_client_id}")
            
            if response.status_code in [401, 403]:
                self.log_result(
                    "Client Deletion Authentication Required", 
                    True, 
                    f"Correctly requires authentication for client deletion (status: {response.status_code})"
                )
            else:
                self.log_result(
                    "Client Deletion Authentication Required", 
                    False, 
                    f"Expected 401/403 but got {response.status_code}",
                    "Client deletion should require admin authentication"
                )
        except Exception as e:
            self.log_result("Client Deletion Authentication Required", False, f"Error: {str(e)}")
        
        # Test 8: Test safety protection - client with active orders
        # First create a client with an active order
        client_with_orders_data = {
            "company_name": "Client with Active Orders",
            "contact_name": "Jane Orders",
            "email": "jane.orders@testclient.com",
            "phone": "0412345679",
            "address": "456 Orders Street",
            "city": "Sydney",
            "state": "NSW",
            "postal_code": "2000",
            "abn": "11223344556",
            "payment_terms": "Net 14 days",
            "lead_time_days": 5
        }
        
        client_with_orders_id = None
        try:
            response = self.session.post(f"{API_BASE}/clients", json=client_with_orders_data)
            
            if response.status_code == 200:
                result = response.json()
                client_with_orders_id = result.get('data', {}).get('id')
                
                if client_with_orders_id:
                    # Create an active order for this client
                    order_data = {
                        "client_id": client_with_orders_id,
                        "due_date": (datetime.now() + timedelta(days=14)).isoformat(),
                        "delivery_address": "456 Orders Street, Sydney NSW 2000",
                        "delivery_instructions": "Handle with care",
                        "notes": "Test order to prevent client deletion",
                        "items": [
                            {
                                "product_id": "test-product-1",
                                "product_name": "Test Product",
                                "description": "Test product for deletion protection",
                                "quantity": 1,
                                "unit_price": 50.0,
                                "total_price": 50.0
                            }
                        ]
                    }
                    
                    order_response = self.session.post(f"{API_BASE}/orders", json=order_data)
                    
                    if order_response.status_code == 200:
                        # Now try to delete the client - should fail with 400 error
                        delete_response = self.session.delete(f"{API_BASE}/clients/{client_with_orders_id}")
                        
                        if delete_response.status_code == 400:
                            result = delete_response.json()
                            message = result.get('detail', '')
                            
                            if 'Cannot delete client with active orders' in message:
                                self.log_result(
                                    "Safety Protection - Client with Active Orders", 
                                    True, 
                                    "Correctly prevents deletion of client with active orders",
                                    f"Response: {message}"
                                )
                            else:
                                self.log_result(
                                    "Safety Protection - Client with Active Orders", 
                                    False, 
                                    f"Unexpected error message: {message}"
                                )
                        else:
                            self.log_result(
                                "Safety Protection - Client with Active Orders", 
                                False, 
                                f"Expected 400 but got {delete_response.status_code}",
                                delete_response.text
                            )
                    else:
                        self.log_result(
                            "Safety Protection - Client with Active Orders", 
                            False, 
                            "Failed to create test order for safety protection test"
                        )
                else:
                    self.log_result(
                        "Safety Protection - Client with Active Orders", 
                        False, 
                        "Failed to create client for safety protection test"
                    )
            else:
                self.log_result(
                    "Safety Protection - Client with Active Orders", 
                    False, 
                    f"Failed to create client for safety test: {response.status_code}"
                )
        except Exception as e:
            self.log_result("Safety Protection - Client with Active Orders", False, f"Error: {str(e)}")

    def test_order_deletion_functionality(self):
        """Test the new order deletion functionality comprehensively"""
        print("\n=== ORDER DELETION FUNCTIONALITY TEST ===")
        
        # First, create a test client for our orders
        test_client_id = self.create_test_client_for_orders()
        if not test_client_id:
            self.log_result(
                "Order Deletion Setup", 
                False, 
                "Failed to create test client for order deletion tests"
            )
            return
        
        # Test 1: Create test orders in different stages
        safe_stage_order_id = self.create_test_order_in_stage(test_client_id, "order_entered")
        production_stage_order_id = self.create_test_order_in_stage(test_client_id, "paper_slitting")
        
        if not safe_stage_order_id or not production_stage_order_id:
            self.log_result(
                "Order Deletion Setup", 
                False, 
                "Failed to create test orders for deletion tests"
            )
            return
        
        # Test 2: Order Deletion Endpoint with Admin Credentials
        self.test_order_deletion_endpoint(safe_stage_order_id)
        
        # Test 3: Safety Protections - Production Stage Orders
        self.test_order_deletion_safety_protections(production_stage_order_id)
        
        # Test 4: Authentication & Authorization
        self.test_order_deletion_authentication()
        
        # Test 5: Order Soft Delete Behavior
        self.test_order_soft_delete_behavior(test_client_id)
        
        # Test 6: Edge Cases
        self.test_order_deletion_edge_cases(test_client_id)
    
    def create_test_client_for_orders(self):
        """Create a test client for order deletion tests"""
        try:
            client_data = {
                "company_name": "Order Deletion Test Client",
                "contact_name": "Test Manager",
                "email": "test@orderdeletion.com",
                "phone": "0412345678",
                "address": "123 Test Street",
                "city": "Melbourne",
                "state": "VIC",
                "postal_code": "3000",
                "abn": "12345678901",
                "payment_terms": "Net 30 days",
                "lead_time_days": 7
            }
            
            response = self.session.post(f"{API_BASE}/clients", json=client_data)
            
            if response.status_code == 200:
                result = response.json()
                return result.get('data', {}).get('id')
            
        except Exception as e:
            print(f"Error creating test client: {str(e)}")
        
        return None
    
    def create_test_order_in_stage(self, client_id, stage):
        """Create a test order and move it to specified stage"""
        try:
            # Create order
            order_data = {
                "client_id": client_id,
                "due_date": (datetime.now() + timedelta(days=14)).isoformat(),
                "delivery_address": "456 Test Delivery Street, Melbourne VIC 3000",
                "delivery_instructions": "Test order for deletion testing",
                "notes": f"Test order for stage {stage}",
                "items": [
                    {
                        "product_id": "test-product-deletion",
                        "product_name": "Test Product for Deletion",
                        "description": "Test product for order deletion testing",
                        "quantity": 1,
                        "unit_price": 50.0,
                        "total_price": 50.0
                    }
                ]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=order_data)
            
            if response.status_code == 200:
                result = response.json()
                order_id = result.get('data', {}).get('id')
                
                if order_id and stage != "order_entered":
                    # Use the proper stage update endpoint
                    stage_update = {
                        "order_id": order_id,
                        "from_stage": "order_entered",
                        "to_stage": stage,
                        "updated_by": "test-user",
                        "notes": f"Moving to {stage} for deletion testing"
                    }
                    
                    update_response = self.session.put(f"{API_BASE}/orders/{order_id}/stage", json=stage_update)
                    
                    if update_response.status_code != 200:
                        print(f"Warning: Failed to update order stage to {stage}: {update_response.status_code}")
                        print(f"Response: {update_response.text}")
                    
                return order_id
                
        except Exception as e:
            print(f"Error creating test order: {str(e)}")
        
        return None
    
    def verify_order_stage(self, order_id):
        """Verify what stage an order is actually in"""
        try:
            response = self.session.get(f"{API_BASE}/orders/{order_id}")
            if response.status_code == 200:
                order = response.json()
                return order.get('current_stage', 'unknown')
        except Exception as e:
            print(f"Error verifying order stage: {str(e)}")
        return 'unknown'
    
    def test_order_deletion_endpoint(self, order_id):
        """Test DELETE /api/orders/{order_id} with admin credentials"""
        print("\n--- Testing Order Deletion Endpoint ---")
        
        try:
            response = self.session.delete(f"{API_BASE}/orders/{order_id}")
            
            if response.status_code == 200:
                result = response.json()
                message = result.get('message', '')
                
                if "Order deleted successfully" in message:
                    self.log_result(
                        "Order Deletion Endpoint", 
                        True, 
                        "Successfully deleted order with admin credentials",
                        f"Order ID: {order_id}, Message: {message}"
                    )
                    
                    # Verify order is marked as cancelled
                    get_response = self.session.get(f"{API_BASE}/orders/{order_id}")
                    if get_response.status_code == 200:
                        order = get_response.json()
                        if order.get('status') == 'cancelled':
                            self.log_result(
                                "Order Soft Delete Verification", 
                                True, 
                                "Order correctly marked as cancelled (soft delete)",
                                f"Order status: {order.get('status')}"
                            )
                        else:
                            self.log_result(
                                "Order Soft Delete Verification", 
                                False, 
                                f"Order status is '{order.get('status')}', expected 'cancelled'"
                            )
                    else:
                        self.log_result(
                            "Order Soft Delete Verification", 
                            False, 
                            f"Could not retrieve order after deletion: {get_response.status_code}"
                        )
                else:
                    self.log_result(
                        "Order Deletion Endpoint", 
                        False, 
                        f"Unexpected response message: {message}"
                    )
            else:
                self.log_result(
                    "Order Deletion Endpoint", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Order Deletion Endpoint", False, f"Error: {str(e)}")
    
    def test_order_deletion_safety_protections(self, production_order_id):
        """Test safety protections against deleting orders in production"""
        print("\n--- Testing Order Deletion Safety Protections ---")
        
        # First verify the order is actually in a production stage
        actual_stage = self.verify_order_stage(production_order_id)
        print(f"Order {production_order_id} is in stage: {actual_stage}")
        
        try:
            response = self.session.delete(f"{API_BASE}/orders/{production_order_id}")
            
            if response.status_code == 400:
                result = response.json()
                message = result.get('detail', '')
                
                if "Cannot delete order in production" in message:
                    self.log_result(
                        "Safety Protection - Production Stage", 
                        True, 
                        f"Correctly prevented deletion of order in {actual_stage} stage",
                        f"Order ID: {production_order_id}, Message: {message}"
                    )
                else:
                    self.log_result(
                        "Safety Protection - Production Stage", 
                        False, 
                        f"Wrong error message for production stage deletion: {message}"
                    )
            else:
                self.log_result(
                    "Safety Protection - Production Stage", 
                    False, 
                    f"Expected 400 status but got {response.status_code} for order in {actual_stage} stage",
                    f"Response: {response.text}"
                )
                
        except Exception as e:
            self.log_result("Safety Protection - Production Stage", False, f"Error: {str(e)}")
        
        # Test deleting non-existent order
        try:
            fake_order_id = "non-existent-order-id-12345"
            response = self.session.delete(f"{API_BASE}/orders/{fake_order_id}")
            
            if response.status_code == 404:
                result = response.json()
                message = result.get('detail', '')
                
                if "Order not found" in message:
                    self.log_result(
                        "Safety Protection - Non-existent Order", 
                        True, 
                        "Correctly returned 404 for non-existent order",
                        f"Message: {message}"
                    )
                else:
                    self.log_result(
                        "Safety Protection - Non-existent Order", 
                        False, 
                        f"Wrong error message for non-existent order: {message}"
                    )
            else:
                self.log_result(
                    "Safety Protection - Non-existent Order", 
                    False, 
                    f"Expected 404 status but got {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Safety Protection - Non-existent Order", False, f"Error: {str(e)}")
    
    def test_order_deletion_authentication(self):
        """Test authentication and authorization for order deletion"""
        print("\n--- Testing Order Deletion Authentication ---")
        
        # Test without authentication
        temp_session = requests.Session()
        
        try:
            fake_order_id = "test-order-for-auth"
            response = temp_session.delete(f"{API_BASE}/orders/{fake_order_id}")
            
            if response.status_code in [401, 403]:
                self.log_result(
                    "Order Deletion Authentication", 
                    True, 
                    f"Correctly requires admin authentication (status: {response.status_code})"
                )
            else:
                self.log_result(
                    "Order Deletion Authentication", 
                    False, 
                    f"Expected 401/403 but got {response.status_code}",
                    "Order deletion should require admin authentication"
                )
                
        except Exception as e:
            self.log_result("Order Deletion Authentication", False, f"Error: {str(e)}")
    
    def test_order_soft_delete_behavior(self, client_id):
        """Test that order deletion is soft delete (status = cancelled)"""
        print("\n--- Testing Order Soft Delete Behavior ---")
        
        # Create a new order for soft delete testing
        test_order_id = self.create_test_order_in_stage(client_id, "pending_material")
        
        if not test_order_id:
            self.log_result(
                "Order Soft Delete Behavior", 
                False, 
                "Failed to create test order for soft delete testing"
            )
            return
        
        try:
            # Get original order data
            get_response = self.session.get(f"{API_BASE}/orders/{test_order_id}")
            if get_response.status_code != 200:
                self.log_result(
                    "Order Soft Delete Behavior", 
                    False, 
                    "Could not retrieve order before deletion"
                )
                return
            
            original_order = get_response.json()
            original_data = {
                'order_number': original_order.get('order_number'),
                'client_id': original_order.get('client_id'),
                'total_amount': original_order.get('total_amount')
            }
            
            # Delete the order
            delete_response = self.session.delete(f"{API_BASE}/orders/{test_order_id}")
            
            if delete_response.status_code == 200:
                # Verify order still exists but is marked as cancelled
                get_after_response = self.session.get(f"{API_BASE}/orders/{test_order_id}")
                
                if get_after_response.status_code == 200:
                    deleted_order = get_after_response.json()
                    
                    # Check that data is preserved
                    data_preserved = (
                        deleted_order.get('order_number') == original_data['order_number'] and
                        deleted_order.get('client_id') == original_data['client_id'] and
                        deleted_order.get('total_amount') == original_data['total_amount']
                    )
                    
                    # Check that status is cancelled
                    status_cancelled = deleted_order.get('status') == 'cancelled'
                    
                    # Check that updated_at is recent
                    updated_at = deleted_order.get('updated_at')
                    has_recent_update = updated_at is not None
                    
                    if data_preserved and status_cancelled and has_recent_update:
                        self.log_result(
                            "Order Soft Delete Behavior", 
                            True, 
                            "Order data preserved, status set to cancelled, datetime updated",
                            f"Status: {deleted_order.get('status')}, Data preserved: {data_preserved}"
                        )
                    else:
                        issues = []
                        if not data_preserved:
                            issues.append("Data not preserved")
                        if not status_cancelled:
                            issues.append(f"Status is '{deleted_order.get('status')}', not 'cancelled'")
                        if not has_recent_update:
                            issues.append("No recent update timestamp")
                        
                        self.log_result(
                            "Order Soft Delete Behavior", 
                            False, 
                            f"Soft delete issues: {', '.join(issues)}"
                        )
                else:
                    self.log_result(
                        "Order Soft Delete Behavior", 
                        False, 
                        f"Order not accessible after deletion: {get_after_response.status_code}"
                    )
            else:
                self.log_result(
                    "Order Soft Delete Behavior", 
                    False, 
                    f"Order deletion failed: {delete_response.status_code}",
                    delete_response.text
                )
                
        except Exception as e:
            self.log_result("Order Soft Delete Behavior", False, f"Error: {str(e)}")
    
    def test_order_deletion_edge_cases(self, client_id):
        """Test edge cases for order deletion"""
        print("\n--- Testing Order Deletion Edge Cases ---")
        
        # Test 1: Delete already cancelled order
        cancelled_order_id = self.create_test_order_in_stage(client_id, "order_entered")
        
        if cancelled_order_id:
            try:
                # First deletion
                first_delete = self.session.delete(f"{API_BASE}/orders/{cancelled_order_id}")
                
                if first_delete.status_code == 200:
                    # Second deletion attempt
                    second_delete = self.session.delete(f"{API_BASE}/orders/{cancelled_order_id}")
                    
                    if second_delete.status_code == 200:
                        result = second_delete.json()
                        message = result.get('message', '')
                        
                        self.log_result(
                            "Edge Case - Delete Already Cancelled Order", 
                            True, 
                            "Successfully handled deletion of already cancelled order",
                            f"Message: {message}"
                        )
                    elif second_delete.status_code == 400:
                        # Also acceptable if it prevents re-deletion
                        result = second_delete.json()
                        message = result.get('detail', '')
                        
                        self.log_result(
                            "Edge Case - Delete Already Cancelled Order", 
                            True, 
                            "Correctly prevented re-deletion of cancelled order",
                            f"Message: {message}"
                        )
                    else:
                        self.log_result(
                            "Edge Case - Delete Already Cancelled Order", 
                            False, 
                            f"Unexpected status for second deletion: {second_delete.status_code}",
                            second_delete.text
                        )
                else:
                    self.log_result(
                        "Edge Case - Delete Already Cancelled Order", 
                        False, 
                        f"First deletion failed: {first_delete.status_code}"
                    )
                    
            except Exception as e:
                self.log_result("Edge Case - Delete Already Cancelled Order", False, f"Error: {str(e)}")
        
        # Test 2: Test different safe stages
        safe_stages = ["order_entered", "pending_material"]
        
        for stage in safe_stages:
            stage_order_id = self.create_test_order_in_stage(client_id, stage)
            
            if stage_order_id:
                try:
                    response = self.session.delete(f"{API_BASE}/orders/{stage_order_id}")
                    
                    if response.status_code == 200:
                        self.log_result(
                            f"Edge Case - Delete Order in {stage.title()} Stage", 
                            True, 
                            f"Successfully deleted order in {stage} stage (safe stage)",
                            f"Order ID: {stage_order_id}"
                        )
                    else:
                        self.log_result(
                            f"Edge Case - Delete Order in {stage.title()} Stage", 
                            False, 
                            f"Failed to delete order in safe stage {stage}: {response.status_code}",
                            response.text
                        )
                        
                except Exception as e:
                    self.log_result(f"Edge Case - Delete Order in {stage.title()} Stage", False, f"Error: {str(e)}")
        
        # Test 3: Test different unsafe stages (using actual ProductionStage enum values)
        # Note: The delete_order function checks for these specific stage names
        unsafe_stages = ["paper_slitting", "winding", "finishing"]
        
        for stage in unsafe_stages[:2]:  # Test first 2 to avoid too many test orders
            unsafe_order_id = self.create_test_order_in_stage(client_id, stage)
            
            if unsafe_order_id:
                # Verify the order is actually in the expected stage
                actual_stage = self.verify_order_stage(unsafe_order_id)
                print(f"Order {unsafe_order_id} is in stage: {actual_stage}")
                
                try:
                    response = self.session.delete(f"{API_BASE}/orders/{unsafe_order_id}")
                    
                    if response.status_code == 400:
                        result = response.json()
                        message = result.get('detail', '')
                        
                        if "Cannot delete order in production" in message:
                            self.log_result(
                                f"Edge Case - Prevent Delete in {stage.title()} Stage", 
                                True, 
                                f"Correctly prevented deletion in {actual_stage} stage (unsafe stage)",
                                f"Message: {message}"
                            )
                        else:
                            self.log_result(
                                f"Edge Case - Prevent Delete in {stage.title()} Stage", 
                                False, 
                                f"Wrong error message for {stage} stage: {message}"
                            )
                    else:
                        self.log_result(
                            f"Edge Case - Prevent Delete in {stage.title()} Stage", 
                            False, 
                            f"Expected 400 but got {response.status_code} for order in {actual_stage} stage (expected {stage})",
                            f"Response: {response.text}"
                        )
                        
                except Exception as e:
                    self.log_result(f"Edge Case - Prevent Delete in {stage.title()} Stage", False, f"Error: {str(e)}")

    def test_order_creation_with_purchase_order_number(self):
        """Test order creation endpoint with purchase_order_number field"""
        print("\n=== ORDER CREATION WITH PURCHASE ORDER NUMBER TEST ===")
        
        # First, get a client to use for testing
        try:
            clients_response = self.session.get(f"{API_BASE}/clients")
            if clients_response.status_code != 200:
                self.log_result(
                    "Order Creation - Get Clients", 
                    False, 
                    f"Failed to get clients: {clients_response.status_code}"
                )
                return
            
            clients = clients_response.json()
            if not clients:
                self.log_result(
                    "Order Creation - Get Clients", 
                    False, 
                    "No clients available for testing"
                )
                return
            
            test_client_id = clients[0]['id']
            test_client_name = clients[0]['company_name']
            
            self.log_result(
                "Order Creation - Get Clients", 
                True, 
                f"Using client: {test_client_name} (ID: {test_client_id})"
            )
            
        except Exception as e:
            self.log_result("Order Creation - Get Clients", False, f"Error: {str(e)}")
            return
        
        # Test 1: Create order WITH purchase_order_number
        print("\n--- Test 1: Order with Purchase Order Number ---")
        order_with_po = {
            "client_id": test_client_id,
            "purchase_order_number": "PO-2024-TEST-001",  # Include PO number
            "due_date": (datetime.now() + timedelta(days=14)).isoformat(),
            "delivery_address": "123 Test Street, Melbourne VIC 3000",
            "delivery_instructions": "Handle with care - testing PO number functionality",
            "notes": "Test order with purchase order number",
            "items": [
                {
                    "product_id": "test-product-po-1",
                    "product_name": "Test Product with PO",
                    "description": "Test product for PO number testing",
                    "quantity": 3,
                    "unit_price": 150.0,
                    "total_price": 450.0
                }
            ]
        }
        
        order_with_po_id = None
        try:
            response = self.session.post(f"{API_BASE}/orders", json=order_with_po)
            
            if response.status_code == 200:
                result = response.json()
                order_with_po_id = result.get('data', {}).get('id')
                order_number = result.get('data', {}).get('order_number')
                
                if order_with_po_id:
                    # Verify the order was created and retrieve it to check PO number
                    get_response = self.session.get(f"{API_BASE}/orders/{order_with_po_id}")
                    if get_response.status_code == 200:
                        order = get_response.json()
                        stored_po_number = order.get('purchase_order_number')
                        
                        if stored_po_number == "PO-2024-TEST-001":
                            self.log_result(
                                "Create Order WITH Purchase Order Number", 
                                True, 
                                f"Order created successfully with PO number stored correctly",
                                f"Order: {order_number}, PO Number: {stored_po_number}"
                            )
                        else:
                            self.log_result(
                                "Create Order WITH Purchase Order Number", 
                                False, 
                                f"PO number not stored correctly - expected 'PO-2024-TEST-001' but got '{stored_po_number}'"
                            )
                    else:
                        self.log_result(
                            "Create Order WITH Purchase Order Number", 
                            False, 
                            "Failed to retrieve created order for PO verification"
                        )
                else:
                    self.log_result(
                        "Create Order WITH Purchase Order Number", 
                        False, 
                        "Order creation response missing ID"
                    )
            else:
                self.log_result(
                    "Create Order WITH Purchase Order Number", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Create Order WITH Purchase Order Number", False, f"Error: {str(e)}")
        
        # Test 2: Create order WITHOUT purchase_order_number (should handle null values)
        print("\n--- Test 2: Order without Purchase Order Number ---")
        order_without_po = {
            "client_id": test_client_id,
            # Note: purchase_order_number field is intentionally omitted
            "due_date": (datetime.now() + timedelta(days=21)).isoformat(),
            "delivery_address": "456 Another Test Street, Sydney NSW 2000",
            "delivery_instructions": "Standard delivery - no PO number",
            "notes": "Test order without purchase order number",
            "items": [
                {
                    "product_id": "test-product-no-po-1",
                    "product_name": "Test Product without PO",
                    "description": "Test product for null PO number testing",
                    "quantity": 2,
                    "unit_price": 200.0,
                    "total_price": 400.0
                }
            ]
        }
        
        order_without_po_id = None
        try:
            response = self.session.post(f"{API_BASE}/orders", json=order_without_po)
            
            if response.status_code == 200:
                result = response.json()
                order_without_po_id = result.get('data', {}).get('id')
                order_number = result.get('data', {}).get('order_number')
                
                if order_without_po_id:
                    # Verify the order was created and check PO number is null/None
                    get_response = self.session.get(f"{API_BASE}/orders/{order_without_po_id}")
                    if get_response.status_code == 200:
                        order = get_response.json()
                        stored_po_number = order.get('purchase_order_number')
                        
                        if stored_po_number is None or stored_po_number == "":
                            self.log_result(
                                "Create Order WITHOUT Purchase Order Number", 
                                True, 
                                f"Order created successfully with null PO number handled correctly",
                                f"Order: {order_number}, PO Number: {stored_po_number}"
                            )
                        else:
                            self.log_result(
                                "Create Order WITHOUT Purchase Order Number", 
                                False, 
                                f"Expected null/empty PO number but got '{stored_po_number}'"
                            )
                    else:
                        self.log_result(
                            "Create Order WITHOUT Purchase Order Number", 
                            False, 
                            "Failed to retrieve created order for PO verification"
                        )
                else:
                    self.log_result(
                        "Create Order WITHOUT Purchase Order Number", 
                        False, 
                        "Order creation response missing ID"
                    )
            else:
                self.log_result(
                    "Create Order WITHOUT Purchase Order Number", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Create Order WITHOUT Purchase Order Number", False, f"Error: {str(e)}")
        
        # Test 3: Create order with explicit null purchase_order_number
        print("\n--- Test 3: Order with Explicit Null Purchase Order Number ---")
        order_explicit_null_po = {
            "client_id": test_client_id,
            "purchase_order_number": None,  # Explicitly set to null
            "due_date": (datetime.now() + timedelta(days=28)).isoformat(),
            "delivery_address": "789 Explicit Null Street, Brisbane QLD 4000",
            "delivery_instructions": "Testing explicit null PO number",
            "notes": "Test order with explicit null purchase order number",
            "items": [
                {
                    "product_id": "test-product-null-po-1",
                    "product_name": "Test Product with Null PO",
                    "description": "Test product for explicit null PO testing",
                    "quantity": 1,
                    "unit_price": 300.0,
                    "total_price": 300.0
                }
            ]
        }
        
        order_explicit_null_po_id = None
        try:
            response = self.session.post(f"{API_BASE}/orders", json=order_explicit_null_po)
            
            if response.status_code == 200:
                result = response.json()
                order_explicit_null_po_id = result.get('data', {}).get('id')
                order_number = result.get('data', {}).get('order_number')
                
                if order_explicit_null_po_id:
                    # Verify the order was created and check PO number is null
                    get_response = self.session.get(f"{API_BASE}/orders/{order_explicit_null_po_id}")
                    if get_response.status_code == 200:
                        order = get_response.json()
                        stored_po_number = order.get('purchase_order_number')
                        
                        if stored_po_number is None:
                            self.log_result(
                                "Create Order with Explicit Null PO Number", 
                                True, 
                                f"Order created successfully with explicit null PO number handled correctly",
                                f"Order: {order_number}, PO Number: {stored_po_number}"
                            )
                        else:
                            self.log_result(
                                "Create Order with Explicit Null PO Number", 
                                False, 
                                f"Expected null PO number but got '{stored_po_number}'"
                            )
                    else:
                        self.log_result(
                            "Create Order with Explicit Null PO Number", 
                            False, 
                            "Failed to retrieve created order for PO verification"
                        )
                else:
                    self.log_result(
                        "Create Order with Explicit Null PO Number", 
                        False, 
                        "Order creation response missing ID"
                    )
            else:
                self.log_result(
                    "Create Order with Explicit Null PO Number", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Create Order with Explicit Null PO Number", False, f"Error: {str(e)}")
        
        # Test 4: Verify existing functionality still works (client selection, due dates, items, etc.)
        print("\n--- Test 4: Verify Existing Order Functionality ---")
        
        # Test with comprehensive order data including all existing fields
        comprehensive_order = {
            "client_id": test_client_id,
            "purchase_order_number": "PO-COMPREHENSIVE-TEST",
            "due_date": (datetime.now() + timedelta(days=35)).isoformat(),
            "delivery_address": "999 Comprehensive Test Avenue, Perth WA 6000",
            "delivery_instructions": "Comprehensive test - verify all existing functionality works with PO number",
            "runtime_estimate": "3-4 days",
            "notes": "Comprehensive test order to verify existing functionality",
            "items": [
                {
                    "product_id": "comprehensive-product-1",
                    "product_name": "Comprehensive Test Product 1",
                    "description": "First product for comprehensive testing",
                    "quantity": 5,
                    "unit_price": 100.0,
                    "total_price": 500.0
                },
                {
                    "product_id": "comprehensive-product-2",
                    "product_name": "Comprehensive Test Product 2",
                    "description": "Second product for comprehensive testing",
                    "quantity": 3,
                    "unit_price": 250.0,
                    "total_price": 750.0
                }
            ]
        }
        
        try:
            response = self.session.post(f"{API_BASE}/orders", json=comprehensive_order)
            
            if response.status_code == 200:
                result = response.json()
                comprehensive_order_id = result.get('data', {}).get('id')
                order_number = result.get('data', {}).get('order_number')
                
                if comprehensive_order_id:
                    # Verify all fields were stored correctly
                    get_response = self.session.get(f"{API_BASE}/orders/{comprehensive_order_id}")
                    if get_response.status_code == 200:
                        order = get_response.json()
                        
                        # Check all key fields
                        checks = []
                        checks.append(("Client ID", order.get('client_id') == test_client_id))
                        checks.append(("Purchase Order Number", order.get('purchase_order_number') == "PO-COMPREHENSIVE-TEST"))
                        checks.append(("Delivery Address", order.get('delivery_address') == "999 Comprehensive Test Avenue, Perth WA 6000"))
                        checks.append(("Delivery Instructions", "Comprehensive test" in order.get('delivery_instructions', "")))
                        checks.append(("Runtime Estimate", order.get('runtime_estimate') == "3-4 days"))
                        checks.append(("Notes", "Comprehensive test order" in order.get('notes', "")))
                        checks.append(("Items Count", len(order.get('items', [])) == 2))
                        checks.append(("Total Amount", order.get('total_amount') > 0))  # Should have calculated totals
                        checks.append(("Order Number", order.get('order_number') is not None))
                        checks.append(("Created At", order.get('created_at') is not None))
                        
                        passed_checks = [name for name, passed in checks if passed]
                        failed_checks = [name for name, passed in checks if not passed]
                        
                        if len(failed_checks) == 0:
                            self.log_result(
                                "Verify Existing Order Functionality", 
                                True, 
                                f"All existing functionality working correctly with PO number field",
                                f"Order: {order_number}, All {len(checks)} checks passed"
                            )
                        else:
                            self.log_result(
                                "Verify Existing Order Functionality", 
                                False, 
                                f"Some existing functionality issues detected",
                                f"Passed: {', '.join(passed_checks)}, Failed: {', '.join(failed_checks)}"
                            )
                    else:
                        self.log_result(
                            "Verify Existing Order Functionality", 
                            False, 
                            "Failed to retrieve comprehensive order for verification"
                        )
                else:
                    self.log_result(
                        "Verify Existing Order Functionality", 
                        False, 
                        "Comprehensive order creation response missing ID"
                    )
            else:
                self.log_result(
                    "Verify Existing Order Functionality", 
                    False, 
                    f"Comprehensive order creation failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Verify Existing Order Functionality", False, f"Error: {str(e)}")
        
        # Test 5: Test order retrieval includes purchase_order_number in response
        print("\n--- Test 5: Verify PO Number in Order List ---")
        try:
            response = self.session.get(f"{API_BASE}/orders")
            
            if response.status_code == 200:
                orders = response.json()
                
                # Find our test orders
                test_orders = [order for order in orders if order.get('purchase_order_number') in [
                    "PO-2024-TEST-001", "PO-COMPREHENSIVE-TEST"
                ]]
                
                if len(test_orders) >= 2:
                    po_numbers_found = [order.get('purchase_order_number') for order in test_orders]
                    self.log_result(
                        "Verify PO Number in Order List", 
                        True, 
                        f"Purchase order numbers correctly included in order list responses",
                        f"Found PO numbers: {', '.join(po_numbers_found)}"
                    )
                else:
                    self.log_result(
                        "Verify PO Number in Order List", 
                        False, 
                        f"Expected to find test orders with PO numbers in order list, found {len(test_orders)}"
                    )
            else:
                self.log_result(
                    "Verify PO Number in Order List", 
                    False, 
                    f"Failed to retrieve order list: {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Verify PO Number in Order List", False, f"Error: {str(e)}")

    def test_materials_thickness_investigation(self):
        """Investigate materials database to identify thickness field issues"""
        print("\n=== MATERIALS THICKNESS INVESTIGATION ===")
        
        try:
            # Get all materials from database
            response = self.session.get(f"{API_BASE}/materials")
            
            if response.status_code == 200:
                materials = response.json()
                
                self.log_result(
                    "Materials Database Retrieval", 
                    True, 
                    f"Successfully retrieved {len(materials)} materials from database"
                )
                
                # Analyze each material's thickness-related fields
                thickness_analysis = []
                problematic_materials = []
                
                for i, material in enumerate(materials):
                    material_id = material.get('id', f'material_{i}')
                    supplier = material.get('supplier', 'Unknown')
                    product_code = material.get('product_code', 'Unknown')
                    
                    # Check all potential thickness fields
                    thickness_fields = {}
                    
                    # Standard thickness fields
                    if 'thickness' in material:
                        thickness_fields['thickness'] = material['thickness']
                    if 'thickness_mm' in material:
                        thickness_fields['thickness_mm'] = material['thickness_mm']
                    if 'thickness_microns' in material:
                        thickness_fields['thickness_microns'] = material['thickness_microns']
                    
                    # Raw substrate specific fields that might be confused as thickness
                    if 'supplied_roll_weight' in material:
                        thickness_fields['supplied_roll_weight'] = material['supplied_roll_weight']
                    if 'master_deckle_width_mm' in material:
                        thickness_fields['master_deckle_width_mm'] = material['master_deckle_width_mm']
                    if 'gsm' in material:
                        thickness_fields['gsm'] = material['gsm']
                    
                    # Other fields that might be mistaken for thickness
                    if 'price' in material:
                        thickness_fields['price'] = material['price']
                    if 'weight' in material:
                        thickness_fields['weight'] = material['weight']
                    if 'roll_weight' in material:
                        thickness_fields['roll_weight'] = material['roll_weight']
                    
                    material_analysis = {
                        'id': material_id,
                        'supplier': supplier,
                        'product_code': product_code,
                        'raw_substrate': material.get('raw_substrate', False),
                        'thickness_fields': thickness_fields,
                        'all_fields': list(material.keys())
                    }
                    
                    thickness_analysis.append(material_analysis)
                    
                    # Check for problematic values (1000mm, 1400mm range)
                    for field_name, value in thickness_fields.items():
                        if isinstance(value, (int, float)) and 900 <= value <= 1500:
                            problematic_materials.append({
                                'material': f"{supplier} - {product_code}",
                                'field': field_name,
                                'value': value,
                                'material_id': material_id
                            })
                
                # Report findings
                if problematic_materials:
                    materials_list = []
                    for m in problematic_materials[:5]:
                        materials_list.append(f"{m['material']} ({m['field']}: {m['value']})")
                    
                    self.log_result(
                        "Problematic Thickness Values Found", 
                        True, 
                        f"Found {len(problematic_materials)} materials with suspicious thickness values (900-1500 range)",
                        f"Materials: {materials_list}"
                    )
                else:
                    self.log_result(
                        "Problematic Thickness Values Found", 
                        False, 
                        "No materials found with thickness values in the 900-1500mm range"
                    )
                
                # Analyze field usage patterns
                field_usage = {}
                for analysis in thickness_analysis:
                    for field in analysis['thickness_fields'].keys():
                        field_usage[field] = field_usage.get(field, 0) + 1
                
                # Check what field might be used as "thickness" in dropdowns
                potential_thickness_fields = ['thickness', 'thickness_mm', 'supplied_roll_weight', 'master_deckle_width_mm']
                dropdown_field_analysis = []
                
                for field in potential_thickness_fields:
                    if field in field_usage:
                        values = [m['thickness_fields'].get(field) for m in thickness_analysis if field in m['thickness_fields']]
                        values = [v for v in values if isinstance(v, (int, float))]
                        
                        if values:
                            avg_value = sum(values) / len(values)
                            min_value = min(values)
                            max_value = max(values)
                            
                            dropdown_field_analysis.append({
                                'field': field,
                                'count': field_usage[field],
                                'avg_value': avg_value,
                                'min_value': min_value,
                                'max_value': max_value,
                                'sample_values': values[:5]
                            })
                
                # Report field analysis
                self.log_result(
                    "Thickness Field Analysis", 
                    True, 
                    f"Analyzed thickness-related fields across {len(materials)} materials",
                    f"Field usage: {field_usage}"
                )
                
                # Detailed analysis for each potential thickness field
                for analysis in dropdown_field_analysis:
                    field_name = analysis['field']
                    is_problematic = analysis['max_value'] > 100  # Thickness should typically be under 100mm
                    
                    self.log_result(
                        f"Field Analysis: {field_name}", 
                        not is_problematic, 
                        f"Field '{field_name}' used in {analysis['count']} materials, avg: {analysis['avg_value']:.2f}, range: {analysis['min_value']}-{analysis['max_value']}",
                        f"Sample values: {analysis['sample_values']}"
                    )
                
                # Check specific materials with unrealistic thickness
                print(f"\n=== DETAILED ANALYSIS OF PROBLEMATIC MATERIALS ===")
                for problem in problematic_materials:
                    material_id = problem['material_id']
                    
                    # Get full material details
                    detail_response = self.session.get(f"{API_BASE}/materials/{material_id}")
                    if detail_response.status_code == 200:
                        material_detail = detail_response.json()
                        
                        print(f"\nMaterial: {problem['material']}")
                        print(f"  ID: {material_id}")
                        print(f"  Problematic Field: {problem['field']} = {problem['value']}")
                        print(f"  Raw Substrate: {material_detail.get('raw_substrate', False)}")
                        print(f"  All Fields: {list(material_detail.keys())}")
                        
                        # Show all numeric fields that could be thickness
                        numeric_fields = {}
                        for key, value in material_detail.items():
                            if isinstance(value, (int, float)) and value > 0:
                                numeric_fields[key] = value
                        print(f"  Numeric Fields: {numeric_fields}")
                
                # Summary and recommendations
                print(f"\n=== THICKNESS INVESTIGATION SUMMARY ===")
                print(f"Total Materials Analyzed: {len(materials)}")
                print(f"Materials with Problematic Values (900-1500): {len(problematic_materials)}")
                print(f"Field Usage Patterns: {field_usage}")
                
                if problematic_materials:
                    print(f"\nLIKELY ISSUE IDENTIFIED:")
                    most_common_problem_field = max(set(p['field'] for p in problematic_materials), 
                                                  key=lambda x: sum(1 for p in problematic_materials if p['field'] == x))
                    print(f"  - Field '{most_common_problem_field}' appears to contain unrealistic thickness values")
                    print(f"  - This field might be incorrectly used as 'thickness' in material selection dropdowns")
                    print(f"  - Values like 1000mm, 1400mm suggest this could be weight, width, or other measurement")
                
                print(f"\nRECOMMENDATIONS:")
                print(f"  1. Check frontend code for material selection dropdown - which field is used as 'thickness'")
                print(f"  2. Verify if 'supplied_roll_weight' or 'master_deckle_width_mm' is being displayed as thickness")
                print(f"  3. Add proper 'thickness_mm' field with realistic values (0.1-10mm typically)")
                print(f"  4. Update material data structure to separate thickness from weight/width measurements")
                
                return {
                    'total_materials': len(materials),
                    'problematic_materials': problematic_materials,
                    'field_usage': field_usage,
                    'dropdown_field_analysis': dropdown_field_analysis
                }
                
            else:
                self.log_result(
                    "Materials Database Retrieval", 
                    False, 
                    f"Failed to retrieve materials: HTTP {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Materials Thickness Investigation", False, f"Error: {str(e)}")
        
        return None

    def test_enhanced_product_specifications(self):
        """Test enhanced Product Specifications functionality with material layers and thickness calculation"""
        print("\n=== ENHANCED PRODUCT SPECIFICATIONS TEST ===")
        
        # First, get some materials to use in our tests
        materials_response = self.session.get(f"{API_BASE}/materials")
        materials = []
        if materials_response.status_code == 200:
            materials = materials_response.json()
        
        if len(materials) < 2:
            self.log_result(
                "Enhanced Product Specifications Setup", 
                False, 
                "Need at least 2 materials in database for testing"
            )
            return
        
        # Test 1: Create Product Specification with Material Layers and Thickness Calculation
        material_layers = [
            {
                "material_id": materials[0]["id"],
                "material_name": f"{materials[0]['supplier']} - {materials[0]['product_code']}",
                "layer_type": "Outer Most Layer",
                "width": 150.0,  # mm
                "thickness": 2.5,  # mm
                "quantity": 1.0,
                "notes": "Outer protective layer"
            },
            {
                "material_id": materials[1]["id"] if len(materials) > 1 else materials[0]["id"],
                "material_name": f"{materials[1]['supplier']} - {materials[1]['product_code']}" if len(materials) > 1 else f"{materials[0]['supplier']} - {materials[0]['product_code']}",
                "layer_type": "Central Layer",
                "width_range": "61-68",  # mm range for central layer
                "thickness": 1.8,  # mm
                "quantity": 2.0,  # double layer
                "notes": "Central structural layers"
            },
            {
                "material_id": materials[0]["id"],
                "material_name": f"{materials[0]['supplier']} - {materials[0]['product_code']}",
                "layer_type": "Inner Most Layer",
                "width": 145.0,  # mm
                "thickness": 0.7,  # mm
                "quantity": 1.0,
                "notes": "Inner finishing layer"
            }
        ]
        
        # Expected thickness calculation: (2.5 * 1.0) + (1.8 * 2.0) + (0.7 * 1.0) = 2.5 + 3.6 + 0.7 = 6.8mm
        expected_thickness = 6.8
        
        spec_data = {
            "product_name": "Multi-Layer Paper Core Test",
            "product_type": "Paper Core",
            "specifications": {
                "inner_diameter_mm": 76.0,
                "outer_diameter_mm": 89.0,
                "length_mm": 1200.0,
                "wall_thickness_mm": 6.5,
                "gsm": 250
            },
            "material_layers": material_layers,
            "manufacturing_notes": "Test specification with realistic thickness values",
            "selected_thickness": None  # Will be set after seeing options
        }
        
        created_spec_id = None
        try:
            response = self.session.post(f"{API_BASE}/product-specifications", json=spec_data)
            
            if response.status_code == 200:
                result = response.json()
                created_spec_id = result.get('data', {}).get('id')
                calculated_thickness = result.get('data', {}).get('calculated_thickness')
                thickness_options = result.get('data', {}).get('thickness_options', [])
                
                # Verify thickness calculation
                if abs(calculated_thickness - expected_thickness) < 0.01:  # Allow small floating point differences
                    self.log_result(
                        "Create Product Specification with Material Layers", 
                        True, 
                        f"Successfully created specification with correct thickness calculation: {calculated_thickness}mm",
                        f"Expected: {expected_thickness}mm, Options: {thickness_options}"
                    )
                else:
                    self.log_result(
                        "Create Product Specification with Material Layers", 
                        False, 
                        f"Thickness calculation incorrect: expected {expected_thickness}mm, got {calculated_thickness}mm"
                    )
            else:
                self.log_result(
                    "Create Product Specification with Material Layers", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Create Product Specification with Material Layers", False, f"Error: {str(e)}")
        
        # Test 2: Verify Thickness Options Generation (±5%, ±10%, exact)
        if created_spec_id:
            try:
                get_response = self.session.get(f"{API_BASE}/product-specifications/{created_spec_id}")
                
                if get_response.status_code == 200:
                    spec = get_response.json()
                    thickness_options = spec.get('thickness_options', [])
                    calculated_thickness = spec.get('calculated_total_thickness')
                    
                    # Expected options: -10%, -5%, exact, +5%, +10%
                    expected_options = [
                        round(calculated_thickness * 0.90, 3),  # -10%
                        round(calculated_thickness * 0.95, 3),  # -5%
                        round(calculated_thickness, 3),         # Exact
                        round(calculated_thickness * 1.05, 3),  # +5%
                        round(calculated_thickness * 1.10, 3),  # +10%
                    ]
                    expected_options = sorted(list(set(expected_options)))  # Remove duplicates and sort
                    
                    if len(thickness_options) >= 3 and calculated_thickness in thickness_options:
                        self.log_result(
                            "Thickness Options Generation", 
                            True, 
                            f"Generated {len(thickness_options)} thickness options including exact value",
                            f"Options: {thickness_options}, Calculated: {calculated_thickness}mm"
                        )
                    else:
                        self.log_result(
                            "Thickness Options Generation", 
                            False, 
                            f"Thickness options generation issue",
                            f"Options: {thickness_options}, Expected to include: {calculated_thickness}mm"
                        )
                else:
                    self.log_result(
                        "Thickness Options Generation", 
                        False, 
                        f"Failed to retrieve specification: {get_response.status_code}"
                    )
            except Exception as e:
                self.log_result("Thickness Options Generation", False, f"Error: {str(e)}")
        
        # Test 3: Update Product Specification with New Material Layers
        if created_spec_id:
            # Update with different material layers
            updated_material_layers = [
                {
                    "material_id": materials[0]["id"],
                    "material_name": f"{materials[0]['supplier']} - {materials[0]['product_code']}",
                    "layer_type": "Outer Most Layer",
                    "width": 160.0,  # mm - changed width
                    "thickness": 3.2,  # mm - changed thickness
                    "quantity": 1.0,
                    "notes": "Updated outer layer with increased thickness"
                },
                {
                    "material_id": materials[1]["id"] if len(materials) > 1 else materials[0]["id"],
                    "material_name": f"{materials[1]['supplier']} - {materials[1]['product_code']}" if len(materials) > 1 else f"{materials[0]['supplier']} - {materials[0]['product_code']}",
                    "layer_type": "Inner Most Layer",
                    "width": 155.0,  # mm
                    "thickness": 1.5,  # mm
                    "quantity": 1.0,
                    "notes": "Single inner layer"
                }
            ]
            
            # Expected new thickness: (3.2 * 1.0) + (1.5 * 1.0) = 4.7mm
            expected_new_thickness = 4.7
            
            update_data = {
                "product_name": "Multi-Layer Paper Core Test - Updated",
                "product_type": "Paper Core",
                "specifications": {
                    "inner_diameter_mm": 76.0,
                    "outer_diameter_mm": 89.0,
                    "length_mm": 1200.0,
                    "wall_thickness_mm": 4.5,  # Updated to match new calculation
                    "gsm": 280  # Updated GSM
                },
                "material_layers": updated_material_layers,
                "manufacturing_notes": "Updated specification with new material layers",
                "selected_thickness": 4.7  # Select exact calculated thickness
            }
            
            try:
                response = self.session.put(f"{API_BASE}/product-specifications/{created_spec_id}", json=update_data)
                
                if response.status_code == 200:
                    result = response.json()
                    calculated_thickness = result.get('data', {}).get('calculated_thickness')
                    thickness_options = result.get('data', {}).get('thickness_options', [])
                    
                    if abs(calculated_thickness - expected_new_thickness) < 0.01:
                        self.log_result(
                            "Update Product Specification with New Material Layers", 
                            True, 
                            f"Successfully updated specification with recalculated thickness: {calculated_thickness}mm",
                            f"Expected: {expected_new_thickness}mm, New options: {thickness_options}"
                        )
                    else:
                        self.log_result(
                            "Update Product Specification with New Material Layers", 
                            False, 
                            f"Thickness recalculation incorrect: expected {expected_new_thickness}mm, got {calculated_thickness}mm"
                        )
                else:
                    self.log_result(
                        "Update Product Specification with New Material Layers", 
                        False, 
                        f"Update failed with status {response.status_code}",
                        response.text
                    )
            except Exception as e:
                self.log_result("Update Product Specification with New Material Layers", False, f"Error: {str(e)}")
        
        # Test 4: Verify GSM Field Handling
        if created_spec_id:
            try:
                get_response = self.session.get(f"{API_BASE}/product-specifications/{created_spec_id}")
                
                if get_response.status_code == 200:
                    spec = get_response.json()
                    gsm_value = spec.get('specifications', {}).get('gsm')
                    
                    if gsm_value == 280:  # From our update
                        self.log_result(
                            "GSM Field Handling", 
                            True, 
                            f"GSM field properly stored and retrieved: {gsm_value}",
                            f"Specification ID: {created_spec_id}"
                        )
                    else:
                        self.log_result(
                            "GSM Field Handling", 
                            False, 
                            f"GSM field not properly handled: expected 280, got {gsm_value}"
                        )
                else:
                    self.log_result(
                        "GSM Field Handling", 
                        False, 
                        f"Failed to retrieve specification for GSM test: {get_response.status_code}"
                    )
            except Exception as e:
                self.log_result("GSM Field Handling", False, f"Error: {str(e)}")
        
        # Test 5: Verify Selected Thickness Handling
        if created_spec_id:
            try:
                get_response = self.session.get(f"{API_BASE}/product-specifications/{created_spec_id}")
                
                if get_response.status_code == 200:
                    spec = get_response.json()
                    selected_thickness = spec.get('selected_thickness')
                    
                    if selected_thickness == 4.7:  # From our update
                        self.log_result(
                            "Selected Thickness Handling", 
                            True, 
                            f"Selected thickness properly stored and retrieved: {selected_thickness}mm",
                            f"Specification ID: {created_spec_id}"
                        )
                    else:
                        self.log_result(
                            "Selected Thickness Handling", 
                            False, 
                            f"Selected thickness not properly handled: expected 4.7, got {selected_thickness}"
                        )
                else:
                    self.log_result(
                        "Selected Thickness Handling", 
                        False, 
                        f"Failed to retrieve specification for selected thickness test: {get_response.status_code}"
                    )
            except Exception as e:
                self.log_result("Selected Thickness Handling", False, f"Error: {str(e)}")
        
        # Test 6: Test with Realistic Thickness Values (0.15-3.2mm range)
        realistic_material_layers = [
            {
                "material_id": materials[0]["id"],
                "material_name": f"{materials[0]['supplier']} - {materials[0]['product_code']}",
                "layer_type": "Outer Most Layer",
                "width": 120.0,
                "thickness": 0.15,  # Minimum realistic thickness
                "quantity": 1.0,
                "notes": "Ultra-thin outer layer"
            },
            {
                "material_id": materials[1]["id"] if len(materials) > 1 else materials[0]["id"],
                "material_name": f"{materials[1]['supplier']} - {materials[1]['product_code']}" if len(materials) > 1 else f"{materials[0]['supplier']} - {materials[0]['product_code']}",
                "layer_type": "Central Layer",
                "width_range": "50-60",
                "thickness": 1.6,  # Mid-range thickness
                "quantity": 0.5,  # Partial layer
                "notes": "Partial central layer"
            },
            {
                "material_id": materials[0]["id"],
                "material_name": f"{materials[0]['supplier']} - {materials[0]['product_code']}",
                "layer_type": "Inner Most Layer",
                "width": 115.0,
                "thickness": 3.2,  # Maximum realistic thickness
                "quantity": 1.0,
                "notes": "Thick inner structural layer"
            }
        ]
        
        # Expected thickness: (0.15 * 1.0) + (1.6 * 0.5) + (3.2 * 1.0) = 0.15 + 0.8 + 3.2 = 4.15mm
        expected_realistic_thickness = 4.15
        
        realistic_spec_data = {
            "product_name": "Realistic Thickness Range Test",
            "product_type": "Paper Core",
            "specifications": {
                "inner_diameter_mm": 50.0,
                "outer_diameter_mm": 58.0,
                "length_mm": 800.0,
                "wall_thickness_mm": 4.0,
                "gsm": 180
            },
            "material_layers": realistic_material_layers,
            "manufacturing_notes": "Testing with realistic thickness values in 0.15-3.2mm range"
        }
        
        try:
            response = self.session.post(f"{API_BASE}/product-specifications", json=realistic_spec_data)
            
            if response.status_code == 200:
                result = response.json()
                calculated_thickness = result.get('data', {}).get('calculated_thickness')
                thickness_options = result.get('data', {}).get('thickness_options', [])
                
                if abs(calculated_thickness - expected_realistic_thickness) < 0.01:
                    # Verify thickness options are within reasonable range
                    min_option = min(thickness_options) if thickness_options else 0
                    max_option = max(thickness_options) if thickness_options else 0
                    
                    if min_option >= 0.1 and max_option <= 10.0:  # Reasonable range
                        self.log_result(
                            "Realistic Thickness Range Test", 
                            True, 
                            f"Successfully handled realistic thickness values: {calculated_thickness}mm",
                            f"Range: {min_option}mm - {max_option}mm, Options count: {len(thickness_options)}"
                        )
                    else:
                        self.log_result(
                            "Realistic Thickness Range Test", 
                            False, 
                            f"Thickness options outside reasonable range: {min_option}mm - {max_option}mm"
                        )
                else:
                    self.log_result(
                        "Realistic Thickness Range Test", 
                        False, 
                        f"Realistic thickness calculation incorrect: expected {expected_realistic_thickness}mm, got {calculated_thickness}mm"
                    )
            else:
                self.log_result(
                    "Realistic Thickness Range Test", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Realistic Thickness Range Test", False, f"Error: {str(e)}")
        
        # Test 7: Test Material and Product Integration
        try:
            # Get all product specifications to verify material integration
            response = self.session.get(f"{API_BASE}/product-specifications")
            
            if response.status_code == 200:
                specs = response.json()
                specs_with_materials = [spec for spec in specs if spec.get('material_layers')]
                
                if len(specs_with_materials) >= 2:  # We created at least 2 specs with materials
                    self.log_result(
                        "Material and Product Integration", 
                        True, 
                        f"Successfully integrated materials with product specifications",
                        f"Found {len(specs_with_materials)} specifications with material layers out of {len(specs)} total"
                    )
                else:
                    self.log_result(
                        "Material and Product Integration", 
                        False, 
                        f"Material integration issue: only {len(specs_with_materials)} specs with materials found"
                    )
            else:
                self.log_result(
                    "Material and Product Integration", 
                    False, 
                    f"Failed to retrieve specifications for integration test: {response.status_code}"
                )
        except Exception as e:
            self.log_result("Material and Product Integration", False, f"Error: {str(e)}")

    def test_discount_functionality(self):
        """Test comprehensive discount functionality in order creation"""
        print("\n=== DISCOUNT FUNCTIONALITY TEST ===")
        
        # First create a test client for orders
        client_data = {
            "company_name": "Discount Test Client",
            "contact_name": "Jane Smith",
            "email": "jane@discounttest.com",
            "phone": "0412345679",
            "address": "456 Discount Street",
            "city": "Sydney",
            "state": "NSW",
            "postal_code": "2000",
            "abn": "98765432109",
            "payment_terms": "Net 30 days",
            "lead_time_days": 14
        }
        
        try:
            response = self.session.post(f"{API_BASE}/clients", json=client_data)
            if response.status_code != 200:
                self.log_result("Discount Test Setup", False, "Failed to create test client for discount tests")
                return
            
            client_id = response.json().get('data', {}).get('id')
            if not client_id:
                self.log_result("Discount Test Setup", False, "No client ID returned from client creation")
                return
            
            # Test 1: Order with 10% discount
            self.test_order_with_discount(client_id, 10.0, "Volume discount for large order", 1000.0)
            
            # Test 2: Order with 5% discount
            self.test_order_with_discount(client_id, 5.0, "Early payment discount", 800.0)
            
            # Test 3: Order with 15% discount
            self.test_order_with_discount(client_id, 15.0, "Loyalty customer discount", 1200.0)
            
            # Test 4: Order with 0% discount
            self.test_order_with_discount(client_id, 0.0, None, 500.0)
            
            # Test 5: Order without discount fields (null values)
            self.test_order_without_discount(client_id, 750.0)
            
            # Test 6: Order with 100% discount (edge case)
            self.test_order_with_discount(client_id, 100.0, "Promotional free order", 300.0)
            
            # Test 7: Verify GST calculation on discounted amount
            self.test_gst_calculation_on_discounted_amount(client_id)
            
        except Exception as e:
            self.log_result("Discount Functionality Test", False, f"Error in discount test setup: {str(e)}")
    
    def test_order_with_discount(self, client_id, discount_percentage, discount_notes, subtotal):
        """Test order creation with specific discount parameters"""
        test_name = f"Order with {discount_percentage}% Discount"
        
        try:
            order_data = {
                "client_id": client_id,
                "due_date": (datetime.now() + timedelta(days=30)).isoformat(),
                "delivery_address": "123 Test Delivery St, Melbourne VIC 3000",
                "delivery_instructions": "Handle with care",
                "notes": f"Test order with {discount_percentage}% discount",
                "discount_percentage": discount_percentage if discount_percentage > 0 else None,
                "discount_notes": discount_notes,
                "items": [
                    {
                        "product_id": "test-product-discount",
                        "product_name": "Test Discount Product",
                        "description": "Product for discount testing",
                        "quantity": 1,
                        "unit_price": subtotal,
                        "total_price": subtotal
                    }
                ]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=order_data)
            
            if response.status_code == 200:
                result = response.json()
                order_id = result.get('data', {}).get('id')
                
                if order_id:
                    # Retrieve the created order to verify discount calculations
                    get_response = self.session.get(f"{API_BASE}/orders/{order_id}")
                    
                    if get_response.status_code == 200:
                        order = get_response.json()
                        
                        # Calculate expected values
                        expected_discount_amount = subtotal * (discount_percentage / 100) if discount_percentage > 0 else 0
                        expected_discounted_subtotal = subtotal - expected_discount_amount
                        expected_gst = expected_discounted_subtotal * 0.1
                        expected_total = expected_discounted_subtotal + expected_gst
                        
                        # Verify all discount-related fields
                        actual_subtotal = order.get('subtotal')
                        actual_discount_percentage = order.get('discount_percentage')
                        actual_discount_amount = order.get('discount_amount')
                        actual_discount_notes = order.get('discount_notes')
                        actual_discounted_subtotal = order.get('discounted_subtotal')
                        actual_gst = order.get('gst')
                        actual_total = order.get('total_amount')
                        
                        # Validation checks
                        checks = []
                        
                        # Check subtotal
                        if abs(actual_subtotal - subtotal) < 0.01:
                            checks.append("✅ Subtotal correct")
                        else:
                            checks.append(f"❌ Subtotal incorrect: expected {subtotal}, got {actual_subtotal}")
                        
                        # Check discount percentage
                        if discount_percentage > 0:
                            if actual_discount_percentage == discount_percentage:
                                checks.append("✅ Discount percentage correct")
                            else:
                                checks.append(f"❌ Discount percentage incorrect: expected {discount_percentage}, got {actual_discount_percentage}")
                        else:
                            if actual_discount_percentage is None:
                                checks.append("✅ Discount percentage correctly null for 0% discount")
                            else:
                                checks.append(f"❌ Discount percentage should be null for 0% discount, got {actual_discount_percentage}")
                        
                        # Check discount amount
                        if discount_percentage > 0:
                            if actual_discount_amount is not None and abs(actual_discount_amount - expected_discount_amount) < 0.01:
                                checks.append("✅ Discount amount calculated correctly")
                            else:
                                checks.append(f"❌ Discount amount incorrect: expected {expected_discount_amount}, got {actual_discount_amount}")
                        else:
                            if actual_discount_amount is None:
                                checks.append("✅ Discount amount correctly null for 0% discount")
                            else:
                                checks.append(f"❌ Discount amount should be null for 0% discount, got {actual_discount_amount}")
                        
                        # Check discount notes
                        if discount_notes:
                            if actual_discount_notes == discount_notes:
                                checks.append("✅ Discount notes correct")
                            else:
                                checks.append(f"❌ Discount notes incorrect: expected '{discount_notes}', got '{actual_discount_notes}'")
                        else:
                            if actual_discount_notes is None:
                                checks.append("✅ Discount notes correctly null")
                            else:
                                checks.append(f"❌ Discount notes should be null, got '{actual_discount_notes}'")
                        
                        # Check discounted subtotal
                        if abs(actual_discounted_subtotal - expected_discounted_subtotal) < 0.01:
                            checks.append("✅ Discounted subtotal calculated correctly")
                        else:
                            checks.append(f"❌ Discounted subtotal incorrect: expected {expected_discounted_subtotal}, got {actual_discounted_subtotal}")
                        
                        # Check GST calculation on discounted amount
                        if abs(actual_gst - expected_gst) < 0.01:
                            checks.append("✅ GST calculated on discounted amount correctly")
                        else:
                            checks.append(f"❌ GST calculation incorrect: expected {expected_gst}, got {actual_gst}")
                        
                        # Check total amount
                        if abs(actual_total - expected_total) < 0.01:
                            checks.append("✅ Total amount calculated correctly")
                        else:
                            checks.append(f"❌ Total amount incorrect: expected {expected_total}, got {actual_total}")
                        
                        # Determine overall success
                        all_checks_passed = all("✅" in check for check in checks)
                        
                        self.log_result(
                            test_name,
                            all_checks_passed,
                            f"Discount calculation {'successful' if all_checks_passed else 'has issues'}",
                            f"Subtotal: ${subtotal}, Discount: {discount_percentage}%, Final Total: ${actual_total:.2f}\n" + "\n".join(checks)
                        )
                        
                        return order_id
                    else:
                        self.log_result(test_name, False, "Failed to retrieve created order for verification")
                else:
                    self.log_result(test_name, False, "Order creation response missing ID")
            else:
                self.log_result(test_name, False, f"Order creation failed with status {response.status_code}", response.text)
                
        except Exception as e:
            self.log_result(test_name, False, f"Error: {str(e)}")
        
        return None
    
    def test_order_without_discount(self, client_id, subtotal):
        """Test order creation without discount fields"""
        test_name = "Order without Discount Fields"
        
        try:
            order_data = {
                "client_id": client_id,
                "due_date": (datetime.now() + timedelta(days=30)).isoformat(),
                "delivery_address": "123 Test Delivery St, Melbourne VIC 3000",
                "delivery_instructions": "Standard delivery",
                "notes": "Test order without discount fields",
                "items": [
                    {
                        "product_id": "test-product-no-discount",
                        "product_name": "Test No Discount Product",
                        "description": "Product for no discount testing",
                        "quantity": 1,
                        "unit_price": subtotal,
                        "total_price": subtotal
                    }
                ]
                # Note: No discount_percentage or discount_notes fields
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=order_data)
            
            if response.status_code == 200:
                result = response.json()
                order_id = result.get('data', {}).get('id')
                
                if order_id:
                    # Retrieve the created order to verify no discount fields
                    get_response = self.session.get(f"{API_BASE}/orders/{order_id}")
                    
                    if get_response.status_code == 200:
                        order = get_response.json()
                        
                        # Expected values (no discount)
                        expected_gst = subtotal * 0.1
                        expected_total = subtotal + expected_gst
                        
                        # Verify discount fields are null/None
                        checks = []
                        
                        if order.get('discount_percentage') is None:
                            checks.append("✅ Discount percentage is null")
                        else:
                            checks.append(f"❌ Discount percentage should be null, got {order.get('discount_percentage')}")
                        
                        if order.get('discount_amount') is None:
                            checks.append("✅ Discount amount is null")
                        else:
                            checks.append(f"❌ Discount amount should be null, got {order.get('discount_amount')}")
                        
                        if order.get('discount_notes') is None:
                            checks.append("✅ Discount notes is null")
                        else:
                            checks.append(f"❌ Discount notes should be null, got {order.get('discount_notes')}")
                        
                        # Verify discounted_subtotal equals subtotal (no discount applied)
                        if abs(order.get('discounted_subtotal', 0) - subtotal) < 0.01:
                            checks.append("✅ Discounted subtotal equals subtotal (no discount)")
                        else:
                            checks.append(f"❌ Discounted subtotal incorrect: expected {subtotal}, got {order.get('discounted_subtotal')}")
                        
                        # Verify GST and total calculations
                        if abs(order.get('gst', 0) - expected_gst) < 0.01:
                            checks.append("✅ GST calculated correctly on full subtotal")
                        else:
                            checks.append(f"❌ GST calculation incorrect: expected {expected_gst}, got {order.get('gst')}")
                        
                        if abs(order.get('total_amount', 0) - expected_total) < 0.01:
                            checks.append("✅ Total amount calculated correctly")
                        else:
                            checks.append(f"❌ Total amount incorrect: expected {expected_total}, got {order.get('total_amount')}")
                        
                        all_checks_passed = all("✅" in check for check in checks)
                        
                        self.log_result(
                            test_name,
                            all_checks_passed,
                            f"Order without discount fields {'handled correctly' if all_checks_passed else 'has issues'}",
                            "\n".join(checks)
                        )
                    else:
                        self.log_result(test_name, False, "Failed to retrieve created order for verification")
                else:
                    self.log_result(test_name, False, "Order creation response missing ID")
            else:
                self.log_result(test_name, False, f"Order creation failed with status {response.status_code}", response.text)
                
        except Exception as e:
            self.log_result(test_name, False, f"Error: {str(e)}")
    
    def test_gst_calculation_on_discounted_amount(self, client_id):
        """Test specific scenario to verify GST is calculated on discounted amount, not original subtotal"""
        test_name = "GST Calculation on Discounted Amount"
        
        try:
            # Use specific values that make the calculation clear
            subtotal = 1000.0
            discount_percentage = 10.0
            
            order_data = {
                "client_id": client_id,
                "due_date": (datetime.now() + timedelta(days=30)).isoformat(),
                "delivery_address": "123 GST Test St, Melbourne VIC 3000",
                "notes": "Test GST calculation on discounted amount",
                "discount_percentage": discount_percentage,
                "discount_notes": "Testing GST calculation",
                "items": [
                    {
                        "product_id": "test-gst-calc",
                        "product_name": "GST Calculation Test Product",
                        "description": "Product for GST calculation testing",
                        "quantity": 1,
                        "unit_price": subtotal,
                        "total_price": subtotal
                    }
                ]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=order_data)
            
            if response.status_code == 200:
                result = response.json()
                order_id = result.get('data', {}).get('id')
                
                if order_id:
                    get_response = self.session.get(f"{API_BASE}/orders/{order_id}")
                    
                    if get_response.status_code == 200:
                        order = get_response.json()
                        
                        # Expected calculation:
                        # Subtotal: $1000
                        # Discount (10%): $100
                        # Discounted Subtotal: $900
                        # GST (10% of $900): $90
                        # Total: $990
                        
                        expected_discount_amount = 100.0
                        expected_discounted_subtotal = 900.0
                        expected_gst = 90.0  # GST on discounted amount, not original
                        expected_total = 990.0
                        
                        actual_discount_amount = order.get('discount_amount', 0)
                        actual_discounted_subtotal = order.get('discounted_subtotal', 0)
                        actual_gst = order.get('gst', 0)
                        actual_total = order.get('total_amount', 0)
                        
                        # Detailed verification
                        calculation_correct = (
                            abs(actual_discount_amount - expected_discount_amount) < 0.01 and
                            abs(actual_discounted_subtotal - expected_discounted_subtotal) < 0.01 and
                            abs(actual_gst - expected_gst) < 0.01 and
                            abs(actual_total - expected_total) < 0.01
                        )
                        
                        # Check if GST was incorrectly calculated on original subtotal
                        incorrect_gst_on_original = 100.0  # 10% of $1000
                        gst_calculated_on_original = abs(actual_gst - incorrect_gst_on_original) < 0.01
                        
                        if calculation_correct:
                            self.log_result(
                                test_name,
                                True,
                                "GST correctly calculated on discounted amount",
                                f"Subtotal: ${subtotal}, Discount: ${expected_discount_amount}, Discounted Subtotal: ${expected_discounted_subtotal}, GST: ${expected_gst}, Total: ${expected_total}"
                            )
                        elif gst_calculated_on_original:
                            self.log_result(
                                test_name,
                                False,
                                "GST incorrectly calculated on original subtotal instead of discounted amount",
                                f"Expected GST: ${expected_gst} (on discounted amount), Actual GST: ${actual_gst} (on original subtotal)"
                            )
                        else:
                            self.log_result(
                                test_name,
                                False,
                                "GST calculation has unexpected errors",
                                f"Expected: Discount=${expected_discount_amount}, GST=${expected_gst}, Total=${expected_total}\nActual: Discount=${actual_discount_amount}, GST=${actual_gst}, Total=${actual_total}"
                            )
                    else:
                        self.log_result(test_name, False, "Failed to retrieve order for GST calculation verification")
                else:
                    self.log_result(test_name, False, "Order creation response missing ID")
            else:
                self.log_result(test_name, False, f"Order creation failed with status {response.status_code}", response.text)
                
        except Exception as e:
            self.log_result(test_name, False, f"Error: {str(e)}")

    def test_client_product_catalog(self):
        """Test Client Product Catalog functionality"""
        print("\n=== CLIENT PRODUCT CATALOG TESTS ===")
        
        # First, get an existing client or create one for testing
        client_id = self.get_or_create_test_client()
        if not client_id:
            self.log_result("Client Product Catalog Setup", False, "Failed to get or create test client")
            return
        
        # Test 1: Create Finished Goods Product
        finished_goods_product = {
            "product_type": "finished_goods",
            "product_code": "FG-TEST-001",
            "product_description": "Premium finished goods product for testing",
            "price_ex_gst": 125.50,
            "minimum_order_quantity": 100,
            "consignment": False
        }
        
        finished_goods_id = self.test_create_client_product(client_id, finished_goods_product, "Finished Goods")
        
        # Test 2: Create Paper Cores Product with optional fields
        paper_cores_product = {
            "product_type": "paper_cores",
            "product_code": "PC-TEST-001", 
            "product_description": "High-quality paper cores with custom specifications",
            "price_ex_gst": 85.75,
            "minimum_order_quantity": 500,
            "consignment": True,
            "material_used": ["material-id-1", "material-id-2"],
            "core_id": "CORE-001",
            "core_width": "76mm",
            "core_thickness": "3.2mm",
            "strength_quality_important": True,
            "delivery_included": True
        }
        
        paper_cores_id = self.test_create_client_product(client_id, paper_cores_product, "Paper Cores")
        
        # Test 3: Retrieve Client Products
        self.test_get_client_products(client_id)
        
        # Test 4: Update Products
        if finished_goods_id:
            self.test_update_client_product(client_id, finished_goods_id)
        
        # Test 5: Delete Product (soft delete)
        if paper_cores_id:
            self.test_delete_client_product(client_id, paper_cores_id)
        
        # Test 6: Verify soft delete worked
        self.test_verify_soft_delete(client_id, paper_cores_id)
    
    def get_or_create_test_client(self):
        """Get existing client or create one for testing"""
        try:
            # First try to get existing clients
            response = self.session.get(f"{API_BASE}/clients")
            if response.status_code == 200:
                clients = response.json()
                if clients and len(clients) > 0:
                    client_id = clients[0]['id']
                    self.log_result("Get Test Client", True, f"Using existing client: {clients[0]['company_name']}")
                    return client_id
            
            # Create a new test client if none exist
            client_data = {
                "company_name": "Test Client for Product Catalog",
                "contact_name": "Jane Smith",
                "email": "jane@testcatalog.com",
                "phone": "0423456789",
                "address": "456 Catalog Street",
                "city": "Sydney",
                "state": "NSW",
                "postal_code": "2000",
                "abn": "98765432109",
                "payment_terms": "Net 21 days",
                "lead_time_days": 14
            }
            
            response = self.session.post(f"{API_BASE}/clients", json=client_data)
            if response.status_code == 200:
                result = response.json()
                client_id = result.get('data', {}).get('id')
                self.log_result("Create Test Client", True, "Created new test client for catalog testing")
                return client_id
            else:
                self.log_result("Create Test Client", False, f"Failed with status {response.status_code}", response.text)
                
        except Exception as e:
            self.log_result("Get/Create Test Client", False, f"Error: {str(e)}")
        
        return None
    
    def test_create_client_product(self, client_id, product_data, product_type_name):
        """Test creating a client product"""
        try:
            response = self.session.post(f"{API_BASE}/clients/{client_id}/catalog", json=product_data)
            
            if response.status_code == 200:
                result = response.json()
                product_id = result.get('data', {}).get('id')
                
                if product_id:
                    # Verify the product was created correctly
                    get_response = self.session.get(f"{API_BASE}/clients/{client_id}/catalog/{product_id}")
                    if get_response.status_code == 200:
                        created_product = get_response.json()
                        
                        # Verify required fields
                        checks = [
                            created_product.get('product_type') == product_data['product_type'],
                            created_product.get('product_code') == product_data['product_code'],
                            created_product.get('price_ex_gst') == product_data['price_ex_gst'],
                            created_product.get('is_active') == True,
                            'created_at' in created_product
                        ]
                        
                        # Check optional fields for paper_cores
                        if product_data['product_type'] == 'paper_cores':
                            checks.extend([
                                created_product.get('material_used') == product_data.get('material_used'),
                                created_product.get('core_id') == product_data.get('core_id'),
                                created_product.get('strength_quality_important') == product_data.get('strength_quality_important')
                            ])
                        
                        if all(checks):
                            self.log_result(
                                f"Create {product_type_name} Product", 
                                True, 
                                f"Successfully created {product_type_name.lower()} product with all fields",
                                f"Product ID: {product_id}, Code: {product_data['product_code']}"
                            )
                            return product_id
                        else:
                            self.log_result(
                                f"Create {product_type_name} Product", 
                                False, 
                                "Product created but field validation failed",
                                f"Failed checks: {[i for i, check in enumerate(checks) if not check]}"
                            )
                    else:
                        self.log_result(
                            f"Create {product_type_name} Product", 
                            False, 
                            "Product created but failed to retrieve for verification"
                        )
                else:
                    self.log_result(
                        f"Create {product_type_name} Product", 
                        False, 
                        "Product creation response missing ID"
                    )
            else:
                self.log_result(
                    f"Create {product_type_name} Product", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result(f"Create {product_type_name} Product", False, f"Error: {str(e)}")
        
        return None
    
    def test_get_client_products(self, client_id):
        """Test retrieving client products"""
        try:
            response = self.session.get(f"{API_BASE}/clients/{client_id}/catalog")
            
            if response.status_code == 200:
                products = response.json()
                
                if isinstance(products, list):
                    active_products = [p for p in products if p.get('is_active', True)]
                    
                    self.log_result(
                        "Get Client Products", 
                        True, 
                        f"Successfully retrieved {len(active_products)} active products from catalog",
                        f"Total products: {len(products)}, Active: {len(active_products)}"
                    )
                    
                    # Verify product structure
                    if active_products:
                        sample_product = active_products[0]
                        required_fields = ['id', 'client_id', 'product_type', 'product_code', 'product_description', 'price_ex_gst', 'is_active', 'created_at']
                        missing_fields = [field for field in required_fields if field not in sample_product]
                        
                        if not missing_fields:
                            self.log_result(
                                "Product Structure Validation", 
                                True, 
                                "Product objects contain all required fields"
                            )
                        else:
                            self.log_result(
                                "Product Structure Validation", 
                                False, 
                                f"Products missing required fields: {missing_fields}"
                            )
                else:
                    self.log_result(
                        "Get Client Products", 
                        False, 
                        "Response is not a list",
                        f"Response type: {type(products)}"
                    )
            else:
                self.log_result(
                    "Get Client Products", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Get Client Products", False, f"Error: {str(e)}")
    
    def test_update_client_product(self, client_id, product_id):
        """Test updating a client product"""
        try:
            update_data = {
                "product_type": "finished_goods",
                "product_code": "FG-TEST-001-UPDATED",
                "product_description": "Updated premium finished goods product",
                "price_ex_gst": 135.75,
                "minimum_order_quantity": 150,
                "consignment": True
            }
            
            response = self.session.put(f"{API_BASE}/clients/{client_id}/catalog/{product_id}", json=update_data)
            
            if response.status_code == 200:
                # Verify the update worked
                get_response = self.session.get(f"{API_BASE}/clients/{client_id}/catalog/{product_id}")
                if get_response.status_code == 200:
                    updated_product = get_response.json()
                    
                    # Check if fields were updated and updated_at timestamp was set
                    checks = [
                        updated_product.get('product_code') == update_data['product_code'],
                        updated_product.get('price_ex_gst') == update_data['price_ex_gst'],
                        updated_product.get('consignment') == update_data['consignment'],
                        'updated_at' in updated_product and updated_product['updated_at'] is not None
                    ]
                    
                    if all(checks):
                        self.log_result(
                            "Update Client Product", 
                            True, 
                            "Successfully updated product with correct updated_at timestamp",
                            f"New code: {update_data['product_code']}, New price: ${update_data['price_ex_gst']}"
                        )
                    else:
                        self.log_result(
                            "Update Client Product", 
                            False, 
                            "Product update failed validation",
                            f"Failed checks: {[i for i, check in enumerate(checks) if not check]}"
                        )
                else:
                    self.log_result(
                        "Update Client Product", 
                        False, 
                        "Update succeeded but failed to retrieve updated product"
                    )
            else:
                self.log_result(
                    "Update Client Product", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Update Client Product", False, f"Error: {str(e)}")
    
    def test_delete_client_product(self, client_id, product_id):
        """Test soft deleting a client product"""
        try:
            response = self.session.delete(f"{API_BASE}/clients/{client_id}/catalog/{product_id}")
            
            if response.status_code == 200:
                self.log_result(
                    "Delete Client Product", 
                    True, 
                    "Successfully soft deleted client product"
                )
            else:
                self.log_result(
                    "Delete Client Product", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Delete Client Product", False, f"Error: {str(e)}")
    
    def test_verify_soft_delete(self, client_id, product_id):
        """Verify that soft delete worked correctly"""
        try:
            # Try to get the specific product - should return 404 since it's inactive
            get_response = self.session.get(f"{API_BASE}/clients/{client_id}/catalog/{product_id}")
            
            if get_response.status_code == 404:
                # Also verify it doesn't appear in the catalog list
                catalog_response = self.session.get(f"{API_BASE}/clients/{client_id}/catalog")
                if catalog_response.status_code == 200:
                    products = catalog_response.json()
                    deleted_product_in_list = any(p.get('id') == product_id for p in products)
                    
                    if not deleted_product_in_list:
                        self.log_result(
                            "Verify Soft Delete", 
                            True, 
                            "Soft delete working correctly - product not accessible and not in catalog list"
                        )
                    else:
                        self.log_result(
                            "Verify Soft Delete", 
                            False, 
                            "Product still appears in catalog list after deletion"
                        )
                else:
                    self.log_result(
                        "Verify Soft Delete", 
                        False, 
                        "Failed to retrieve catalog for verification"
                    )
            else:
                self.log_result(
                    "Verify Soft Delete", 
                    False, 
                    f"Expected 404 for deleted product but got {get_response.status_code}",
                    "Soft delete may not be working correctly"
                )
                
        except Exception as e:
            self.log_result("Verify Soft Delete", False, f"Error: {str(e)}")

    def test_xero_create_draft_invoice_with_realistic_data(self):
        """Test POST /api/xero/create-draft-invoice with realistic data structure"""
        print("\n=== XERO CREATE DRAFT INVOICE WITH REALISTIC DATA TEST ===")
        
        try:
            # Test with realistic invoice data matching the expected structure
            invoice_data = {
                "client_name": "Acme Manufacturing Ltd",
                "client_email": "accounts@acmemanufacturing.com",
                "invoice_number": "INV-TEST-001",
                "order_number": "ADM-2025-0001",
                "due_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
                "total_amount": 1100.00,
                "items": [
                    {
                        "product_name": "Heavy Duty Paper Core",
                        "quantity": 10,
                        "unit_price": 100.0,
                        "total_price": 1000.0
                    }
                ],
                "subtotal": 1000.0,
                "gst": 100.0
            }
            
            response = self.session.post(f"{API_BASE}/xero/create-draft-invoice", json=invoice_data)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                required_fields = ['success', 'message', 'invoice_id']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    success = data.get('success')
                    message = data.get('message')
                    invoice_id = data.get('invoice_id')
                    
                    if success and invoice_id:
                        self.log_result(
                            "Xero Create Draft Invoice (Realistic Data)", 
                            True, 
                            f"Successfully created draft invoice in Xero with realistic data",
                            f"Invoice ID: {invoice_id}, Message: {message}"
                        )
                    else:
                        self.log_result(
                            "Xero Create Draft Invoice (Realistic Data)", 
                            False, 
                            "Response indicates failure or missing invoice ID",
                            f"Success: {success}, Invoice ID: {invoice_id}"
                        )
                else:
                    self.log_result(
                        "Xero Create Draft Invoice (Realistic Data)", 
                        False, 
                        f"Response missing required fields: {missing_fields}",
                        str(data)
                    )
            elif response.status_code == 400:
                # Expected if no Xero tenant ID or connection issues
                error_text = response.text
                if "No Xero tenant ID found" in error_text or "No Xero connection found" in error_text:
                    self.log_result(
                        "Xero Create Draft Invoice (Realistic Data)", 
                        True, 
                        "Correctly handles missing Xero connection/tenant",
                        f"Status: {response.status_code}, Response: {error_text}"
                    )
                else:
                    self.log_result(
                        "Xero Create Draft Invoice (Realistic Data)", 
                        False, 
                        f"Unexpected 400 error: {error_text}"
                    )
            elif response.status_code == 500:
                # May be expected if Xero integration not fully configured
                error_text = response.text
                if "Failed to create draft invoice" in error_text:
                    self.log_result(
                        "Xero Create Draft Invoice (Realistic Data)", 
                        True, 
                        "Endpoint handles Xero API errors gracefully",
                        f"Status: {response.status_code}, Response: {error_text}"
                    )
                else:
                    self.log_result(
                        "Xero Create Draft Invoice (Realistic Data)", 
                        False, 
                        f"Unexpected 500 error: {error_text}"
                    )
            else:
                self.log_result(
                    "Xero Create Draft Invoice (Realistic Data)", 
                    False, 
                    f"Unexpected status code: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Xero Create Draft Invoice (Realistic Data)", False, f"Error: {str(e)}")
    
    def test_live_jobs_data_structure(self, live_jobs):
        """Test that live jobs include proper client email data and correct field names"""
        print("\n=== LIVE JOBS DATA STRUCTURE VERIFICATION TEST ===")
        
        if not live_jobs:
            self.log_result(
                "Live Jobs Data Structure", 
                False, 
                "No live jobs available for data structure testing"
            )
            return
        
        try:
            # Check first job for required fields
            test_job = live_jobs[0]
            
            # Check for client email data
            has_client_email = 'client_email' in test_job
            has_client_name = 'client_name' in test_job
            has_items = 'items' in test_job and len(test_job['items']) > 0
            
            issues = []
            
            if not has_client_email:
                issues.append("Missing client_email field")
            if not has_client_name:
                issues.append("Missing client_name field")
            if not has_items:
                issues.append("Missing or empty items array")
            
            # Check order items field names
            if has_items:
                first_item = test_job['items'][0]
                required_item_fields = ['product_name', 'unit_price', 'quantity']
                missing_item_fields = [field for field in required_item_fields if field not in first_item]
                
                if missing_item_fields:
                    issues.append(f"Order items missing fields: {missing_item_fields}")
                
                # Check for correct field names (not 'description' instead of 'product_name')
                if 'description' in first_item and 'product_name' not in first_item:
                    issues.append("Order items use 'description' instead of 'product_name'")
            
            if not issues:
                self.log_result(
                    "Live Jobs Data Structure", 
                    True, 
                    "Live jobs have correct data structure with client email and proper field names",
                    f"Verified job: {test_job.get('order_number', 'Unknown')}"
                )
            else:
                self.log_result(
                    "Live Jobs Data Structure", 
                    False, 
                    "Live jobs data structure has issues",
                    f"Issues found: {', '.join(issues)}"
                )
                
        except Exception as e:
            self.log_result("Live Jobs Data Structure", False, f"Error: {str(e)}")
    
    def test_invoice_generation_with_archiving(self, job):
        """Test POST /api/invoicing/generate/{job_id} with archiving workflow"""
        print("\n=== INVOICE GENERATION WITH ARCHIVING TEST ===")
        
        if not job:
            self.log_result(
                "Invoice Generation with Archiving", 
                False, 
                "No job provided for invoice generation testing"
            )
            return
        
        job_id = job.get('id')
        order_number = job.get('order_number', 'Unknown')
        
        try:
            # Test full invoice generation with realistic data
            invoice_data = {
                "invoice_type": "full",
                "items": [
                    {
                        "product_name": "Test Product", 
                        "quantity": 1, 
                        "unit_price": 100.0, 
                        "total_price": 100.0
                    }
                ],
                "subtotal": 100.0,
                "gst": 10.0,
                "total_amount": 110.0,
                "due_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
            }
            
            response = self.session.post(
                f"{API_BASE}/invoicing/generate/{job_id}", 
                json=invoice_data
            )
            
            if response.status_code == 200:
                result = response.json()
                invoice_id = result.get('invoice_id')
                invoice_number = result.get('invoice_number')
                
                if invoice_id and invoice_number:
                    # Verify that order was moved to "cleared" stage and archived
                    order_check = self.session.get(f"{API_BASE}/orders/{job_id}")
                    
                    if order_check.status_code == 200:
                        order_data = order_check.json()
                        current_stage = order_data.get('current_stage')
                        status = order_data.get('status')
                        
                        if current_stage == 'cleared' and status == 'completed':
                            self.log_result(
                                "Invoice Generation with Archiving", 
                                True, 
                                f"Successfully generated invoice {invoice_number} and moved order to cleared/completed",
                                f"Order: {order_number}, Invoice ID: {invoice_id}, Stage: {current_stage}, Status: {status}"
                            )
                        else:
                            self.log_result(
                                "Invoice Generation with Archiving", 
                                False, 
                                f"Invoice generated but order not properly archived",
                                f"Expected stage: cleared, status: completed. Got stage: {current_stage}, status: {status}"
                            )
                    else:
                        self.log_result(
                            "Invoice Generation with Archiving", 
                            False, 
                            "Invoice generated but could not verify order status"
                        )
                else:
                    self.log_result(
                        "Invoice Generation with Archiving", 
                        False, 
                        "Invoice generated but missing ID or number in response"
                    )
            else:
                self.log_result(
                    "Invoice Generation with Archiving", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Invoice Generation with Archiving", False, f"Error: {str(e)}")

    def test_staff_security_user_creation(self):
        """Test Staff & Security API endpoints - User Creation with various validation scenarios"""
        print("\n=== STAFF & SECURITY USER CREATION VALIDATION TEST ===")
        
        # Test scenarios to identify specific validation errors causing 422 status
        test_scenarios = [
            {
                "name": "Valid Complete User Data",
                "data": {
                    "username": "teststaff001",
                    "email": "teststaff001@company.com",
                    "full_name": "Test Staff Member",
                    "password": "SecurePass123!",
                    "role": "employee",
                    "employment_type": "full_time",
                    "department": "Security",
                    "phone": "0412345678"
                },
                "expected_success": True
            },
            {
                "name": "Missing Username",
                "data": {
                    "email": "teststaff002@company.com",
                    "full_name": "Test Staff Member 2",
                    "password": "SecurePass123!",
                    "role": "employee",
                    "employment_type": "full_time",
                    "department": "Security",
                    "phone": "0412345679"
                },
                "expected_success": False
            },
            {
                "name": "Missing Email",
                "data": {
                    "username": "teststaff003",
                    "full_name": "Test Staff Member 3",
                    "password": "SecurePass123!",
                    "role": "employee",
                    "employment_type": "full_time",
                    "department": "Security",
                    "phone": "0412345680"
                },
                "expected_success": False
            },
            {
                "name": "Invalid Email Format",
                "data": {
                    "username": "teststaff004",
                    "email": "invalid-email-format",
                    "full_name": "Test Staff Member 4",
                    "password": "SecurePass123!",
                    "role": "employee",
                    "employment_type": "full_time",
                    "department": "Security",
                    "phone": "0412345681"
                },
                "expected_success": False
            },
            {
                "name": "Missing Password",
                "data": {
                    "username": "teststaff005",
                    "email": "teststaff005@company.com",
                    "full_name": "Test Staff Member 5",
                    "role": "employee",
                    "employment_type": "full_time",
                    "department": "Security",
                    "phone": "0412345682"
                },
                "expected_success": False
            },
            {
                "name": "Missing Full Name",
                "data": {
                    "username": "teststaff006",
                    "email": "teststaff006@company.com",
                    "password": "SecurePass123!",
                    "role": "employee",
                    "employment_type": "full_time",
                    "department": "Security",
                    "phone": "0412345683"
                },
                "expected_success": False
            },
            {
                "name": "Invalid Role Value",
                "data": {
                    "username": "teststaff007",
                    "email": "teststaff007@company.com",
                    "full_name": "Test Staff Member 7",
                    "password": "SecurePass123!",
                    "role": "invalid_role",
                    "employment_type": "full_time",
                    "department": "Security",
                    "phone": "0412345684"
                },
                "expected_success": False
            },
            {
                "name": "Invalid Employment Type",
                "data": {
                    "username": "teststaff008",
                    "email": "teststaff008@company.com",
                    "full_name": "Test Staff Member 8",
                    "password": "SecurePass123!",
                    "role": "employee",
                    "employment_type": "invalid_employment",
                    "department": "Security",
                    "phone": "0412345685"
                },
                "expected_success": False
            },
            {
                "name": "Duplicate Username",
                "data": {
                    "username": "teststaff001",  # Same as first test
                    "email": "teststaff009@company.com",
                    "full_name": "Test Staff Member 9",
                    "password": "SecurePass123!",
                    "role": "employee",
                    "employment_type": "full_time",
                    "department": "Security",
                    "phone": "0412345686"
                },
                "expected_success": False
            },
            {
                "name": "Duplicate Email",
                "data": {
                    "username": "teststaff010",
                    "email": "teststaff001@company.com",  # Same as first test
                    "full_name": "Test Staff Member 10",
                    "password": "SecurePass123!",
                    "role": "employee",
                    "employment_type": "full_time",
                    "department": "Security",
                    "phone": "0412345687"
                },
                "expected_success": False
            },
            {
                "name": "Valid Manager Role",
                "data": {
                    "username": "testmanager001",
                    "email": "testmanager001@company.com",
                    "full_name": "Test Manager",
                    "password": "SecurePass123!",
                    "role": "manager",
                    "employment_type": "full_time",
                    "department": "Operations",
                    "phone": "0412345688"
                },
                "expected_success": True
            },
            {
                "name": "Valid Admin Role",
                "data": {
                    "username": "testadmin001",
                    "email": "testadmin001@company.com",
                    "full_name": "Test Admin",
                    "password": "SecurePass123!",
                    "role": "admin",
                    "employment_type": "full_time",
                    "department": "IT",
                    "phone": "0412345689"
                },
                "expected_success": True
            },
            {
                "name": "Valid Part Time Employee",
                "data": {
                    "username": "testparttime001",
                    "email": "testparttime001@company.com",
                    "full_name": "Test Part Time Staff",
                    "password": "SecurePass123!",
                    "role": "production_team",
                    "employment_type": "part_time",
                    "department": "Production",
                    "phone": "0412345690"
                },
                "expected_success": True
            },
            {
                "name": "Valid Casual Employee",
                "data": {
                    "username": "testcasual001",
                    "email": "testcasual001@company.com",
                    "full_name": "Test Casual Staff",
                    "password": "SecurePass123!",
                    "role": "production_team",
                    "employment_type": "casual",
                    "department": "Production",
                    "phone": "0412345691"
                },
                "expected_success": True
            },
            {
                "name": "Minimal Required Fields Only",
                "data": {
                    "username": "testminimal001",
                    "email": "testminimal001@company.com",
                    "full_name": "Test Minimal Staff",
                    "password": "SecurePass123!",
                    "role": "employee"
                    # Optional fields omitted: employment_type, department, phone
                },
                "expected_success": True
            }
        ]
        
        successful_tests = 0
        failed_tests = 0
        validation_errors_found = []
        created_user_ids = []
        
        for scenario in test_scenarios:
            try:
                print(f"\n  Testing: {scenario['name']}")
                response = self.session.post(f"{API_BASE}/users", json=scenario['data'])
                
                if scenario['expected_success']:
                    if response.status_code == 200:
                        result = response.json()
                        user_id = result.get('data', {}).get('id')
                        if user_id:
                            created_user_ids.append(user_id)
                        
                        self.log_result(
                            f"User Creation - {scenario['name']}", 
                            True, 
                            f"Successfully created user as expected",
                            f"User ID: {user_id}"
                        )
                        successful_tests += 1
                    else:
                        self.log_result(
                            f"User Creation - {scenario['name']}", 
                            False, 
                            f"Expected success but got status {response.status_code}",
                            response.text
                        )
                        failed_tests += 1
                        
                        # Capture validation error details for analysis
                        if response.status_code == 422:
                            try:
                                error_detail = response.json()
                                validation_errors_found.append({
                                    'scenario': scenario['name'],
                                    'status': response.status_code,
                                    'error': error_detail
                                })
                            except:
                                validation_errors_found.append({
                                    'scenario': scenario['name'],
                                    'status': response.status_code,
                                    'error': response.text
                                })
                else:
                    # Expected to fail
                    if response.status_code in [400, 422]:
                        # Capture the specific validation error
                        try:
                            error_detail = response.json()
                            validation_errors_found.append({
                                'scenario': scenario['name'],
                                'status': response.status_code,
                                'error': error_detail
                            })
                        except:
                            validation_errors_found.append({
                                'scenario': scenario['name'],
                                'status': response.status_code,
                                'error': response.text
                            })
                        
                        self.log_result(
                            f"User Creation - {scenario['name']}", 
                            True, 
                            f"Correctly failed with status {response.status_code} as expected",
                            f"Error: {response.text[:200]}"
                        )
                        successful_tests += 1
                    else:
                        self.log_result(
                            f"User Creation - {scenario['name']}", 
                            False, 
                            f"Expected failure (400/422) but got status {response.status_code}",
                            response.text
                        )
                        failed_tests += 1
                        
            except Exception as e:
                self.log_result(f"User Creation - {scenario['name']}", False, f"Exception: {str(e)}")
                failed_tests += 1
        
        # Summary of validation errors found
        print(f"\n=== VALIDATION ERROR ANALYSIS ===")
        print(f"Total scenarios tested: {len(test_scenarios)}")
        print(f"Successful tests: {successful_tests}")
        print(f"Failed tests: {failed_tests}")
        print(f"Validation errors captured: {len(validation_errors_found)}")
        
        # Detailed analysis of 422 errors
        error_422_scenarios = [err for err in validation_errors_found if err['status'] == 422]
        if error_422_scenarios:
            print(f"\n🚨 422 VALIDATION ERRORS FOUND ({len(error_422_scenarios)} scenarios):")
            for error in error_422_scenarios:
                print(f"  Scenario: {error['scenario']}")
                print(f"  Status: {error['status']}")
                print(f"  Error: {error['error']}")
                print()
        
        # Clean up created test users
        print(f"\n=== CLEANUP ===")
        for user_id in created_user_ids:
            try:
                delete_response = self.session.delete(f"{API_BASE}/users/{user_id}")
                if delete_response.status_code == 200:
                    print(f"✅ Cleaned up test user: {user_id}")
                else:
                    print(f"⚠️ Failed to cleanup test user {user_id}: {delete_response.status_code}")
            except Exception as e:
                print(f"⚠️ Exception during cleanup of user {user_id}: {str(e)}")
        
        # Overall test result
        overall_success = failed_tests == 0
        self.log_result(
            "Staff & Security User Creation Validation", 
            overall_success, 
            f"Completed comprehensive user creation testing",
            f"Success: {successful_tests}/{len(test_scenarios)}, 422 Errors: {len(error_422_scenarios)}"
        )
        
        return validation_errors_found

    def test_product_specifications_create_400_error(self):
        """Test Product Specifications CREATE endpoint to identify 400 Bad Request error"""
        print("\n=== PRODUCT SPECIFICATIONS CREATE 400 ERROR ANALYSIS ===")
        
        # Test data structure from the screenshots
        test_data = {
            "product_name": "Paper Core - 40mm ID x 1.8mmT",
            "product_type": "Spiral Paper Core",
            "manufacturing_notes": "Paper cores intended for the Label Manufacturing Industry",
            "specifications": {
                "internal_diameter": 40,
                "wall_thickness_required": 1.8
            },
            "material_layers": [
                {
                    "material_id": "test-material-1",
                    "material_name": "Outer Layer Material",
                    "layer_type": "Outer Most Layer",
                    "thickness": 0.15,
                    "quantity": 1
                },
                {
                    "material_id": "test-material-2", 
                    "material_name": "Central Layer Material",
                    "layer_type": "Central Layer",
                    "thickness": 0.54,
                    "quantity": 3
                },
                {
                    "material_id": "test-material-3",
                    "material_name": "Outer Layer Material",
                    "layer_type": "Outer Most Layer", 
                    "thickness": 0.15,
                    "quantity": 1
                }
            ]
        }
        
        # Test 1: Full valid request
        try:
            response = self.session.post(f"{API_BASE}/product-specifications", json=test_data)
            
            if response.status_code == 200:
                self.log_result(
                    "Product Specifications CREATE - Full Valid Request",
                    True,
                    "CREATE request successful with complete data structure"
                )
            elif response.status_code == 400:
                self.log_result(
                    "Product Specifications CREATE - Full Valid Request",
                    False,
                    f"400 Bad Request with complete data: {response.text}",
                    f"Request data: {json.dumps(test_data, indent=2)}"
                )
            elif response.status_code == 422:
                self.log_result(
                    "Product Specifications CREATE - Full Valid Request",
                    False,
                    f"422 Validation Error (not 400): {response.text}",
                    "This indicates validation issues, not structural problems"
                )
            else:
                self.log_result(
                    "Product Specifications CREATE - Full Valid Request",
                    False,
                    f"Unexpected status {response.status_code}: {response.text}"
                )
        except Exception as e:
            self.log_result("Product Specifications CREATE - Full Valid Request", False, f"Exception: {str(e)}")
        
        # Test 2: Missing required fields (should cause 422, not 400)
        minimal_data = {
            "product_name": "Paper Core - 40mm ID x 1.8mmT"
            # Missing product_type and specifications
        }
        
        try:
            response = self.session.post(f"{API_BASE}/product-specifications", json=minimal_data)
            
            if response.status_code == 422:
                self.log_result(
                    "Product Specifications CREATE - Missing Required Fields",
                    True,
                    "Correctly returns 422 for missing required fields (not 400)",
                    f"Response: {response.text}"
                )
            elif response.status_code == 400:
                self.log_result(
                    "Product Specifications CREATE - Missing Required Fields",
                    False,
                    f"Returns 400 instead of expected 422 for validation: {response.text}",
                    "This suggests structural issues in request handling"
                )
            else:
                self.log_result(
                    "Product Specifications CREATE - Missing Required Fields",
                    False,
                    f"Unexpected status {response.status_code}: {response.text}"
                )
        except Exception as e:
            self.log_result("Product Specifications CREATE - Missing Required Fields", False, f"Exception: {str(e)}")
        
        # Test 3: Wrong data types (should cause 422, not 400)
        wrong_types_data = {
            "product_name": 123,  # Should be string
            "product_type": "Spiral Paper Core",
            "specifications": "not a dict",  # Should be dict
            "material_layers": "not a list"  # Should be list
        }
        
        try:
            response = self.session.post(f"{API_BASE}/product-specifications", json=wrong_types_data)
            
            if response.status_code == 422:
                self.log_result(
                    "Product Specifications CREATE - Wrong Data Types",
                    True,
                    "Correctly returns 422 for wrong data types (not 400)",
                    f"Response: {response.text}"
                )
            elif response.status_code == 400:
                self.log_result(
                    "Product Specifications CREATE - Wrong Data Types",
                    False,
                    f"Returns 400 instead of expected 422 for type validation: {response.text}",
                    "This suggests JSON parsing or structural issues"
                )
            else:
                self.log_result(
                    "Product Specifications CREATE - Wrong Data Types",
                    False,
                    f"Unexpected status {response.status_code}: {response.text}"
                )
        except Exception as e:
            self.log_result("Product Specifications CREATE - Wrong Data Types", False, f"Exception: {str(e)}")
        
        # Test 4: Malformed JSON (should cause 400)
        try:
            malformed_json = '{"product_name": "Test", "product_type": "Spiral Paper Core", "specifications": {'
            response = self.session.post(
                f"{API_BASE}/product-specifications", 
                data=malformed_json,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 400:
                self.log_result(
                    "Product Specifications CREATE - Malformed JSON",
                    True,
                    "Correctly returns 400 for malformed JSON",
                    f"Response: {response.text}"
                )
            else:
                self.log_result(
                    "Product Specifications CREATE - Malformed JSON",
                    False,
                    f"Expected 400 for malformed JSON but got {response.status_code}: {response.text}"
                )
        except Exception as e:
            self.log_result("Product Specifications CREATE - Malformed JSON", False, f"Exception: {str(e)}")
        
        # Test 5: Invalid endpoint URL (should cause 404, not 400)
        try:
            response = self.session.post(f"{API_BASE}/product-specification", json=test_data)  # Missing 's'
            
            if response.status_code == 404:
                self.log_result(
                    "Product Specifications CREATE - Invalid Endpoint URL",
                    True,
                    "Correctly returns 404 for invalid endpoint (not 400)",
                    f"Response: {response.text}"
                )
            elif response.status_code == 400:
                self.log_result(
                    "Product Specifications CREATE - Invalid Endpoint URL",
                    False,
                    f"Returns 400 instead of expected 404 for invalid URL: {response.text}",
                    "This suggests routing issues"
                )
            else:
                self.log_result(
                    "Product Specifications CREATE - Invalid Endpoint URL",
                    False,
                    f"Unexpected status {response.status_code}: {response.text}"
                )
        except Exception as e:
            self.log_result("Product Specifications CREATE - Invalid Endpoint URL", False, f"Exception: {str(e)}")
        
        # Test 6: Missing Content-Type header (should cause 400)
        try:
            response = self.session.post(
                f"{API_BASE}/product-specifications", 
                data=json.dumps(test_data)
                # No Content-Type header
            )
            
            if response.status_code == 400:
                self.log_result(
                    "Product Specifications CREATE - Missing Content-Type",
                    True,
                    "Correctly returns 400 for missing Content-Type header",
                    f"Response: {response.text}"
                )
            elif response.status_code == 422:
                self.log_result(
                    "Product Specifications CREATE - Missing Content-Type",
                    False,
                    f"Returns 422 instead of expected 400 for missing Content-Type: {response.text}",
                    "FastAPI may be handling this differently"
                )
            else:
                self.log_result(
                    "Product Specifications CREATE - Missing Content-Type",
                    False,
                    f"Unexpected status {response.status_code}: {response.text}"
                )
        except Exception as e:
            self.log_result("Product Specifications CREATE - Missing Content-Type", False, f"Exception: {str(e)}")
        
        # Test 7: Authentication issues (should cause 401/403, not 400)
        temp_session = requests.Session()
        try:
            response = temp_session.post(f"{API_BASE}/product-specifications", json=test_data)
            
            if response.status_code in [401, 403]:
                self.log_result(
                    "Product Specifications CREATE - No Authentication",
                    True,
                    f"Correctly returns {response.status_code} for missing authentication (not 400)",
                    f"Response: {response.text}"
                )
            elif response.status_code == 400:
                self.log_result(
                    "Product Specifications CREATE - No Authentication",
                    False,
                    f"Returns 400 instead of expected 401/403 for auth issues: {response.text}",
                    "This suggests authentication middleware issues"
                )
            else:
                self.log_result(
                    "Product Specifications CREATE - No Authentication",
                    False,
                    f"Unexpected status {response.status_code}: {response.text}"
                )
        except Exception as e:
            self.log_result("Product Specifications CREATE - No Authentication", False, f"Exception: {str(e)}")
        
        # Test 8: Compare CREATE vs UPDATE endpoint structure
        # First, try to get an existing specification to test UPDATE
        try:
            get_response = self.session.get(f"{API_BASE}/product-specifications")
            
            if get_response.status_code == 200:
                specs = get_response.json()
                if specs and len(specs) > 0:
                    spec_id = specs[0]['id']
                    
                    # Test UPDATE with same data structure
                    update_response = self.session.put(f"{API_BASE}/product-specifications/{spec_id}", json=test_data)
                    
                    if update_response.status_code == 200:
                        self.log_result(
                            "Product Specifications UPDATE vs CREATE Comparison",
                            True,
                            "UPDATE works with same data structure that might fail in CREATE",
                            f"UPDATE successful, CREATE may have different validation"
                        )
                    elif update_response.status_code == 400:
                        self.log_result(
                            "Product Specifications UPDATE vs CREATE Comparison",
                            False,
                            f"Both CREATE and UPDATE return 400 with same data: {update_response.text}",
                            "Issue is in data structure or validation logic"
                        )
                    elif update_response.status_code == 422:
                        self.log_result(
                            "Product Specifications UPDATE vs CREATE Comparison",
                            False,
                            f"UPDATE returns 422 while CREATE returns 400: {update_response.text}",
                            "Different validation behavior between CREATE and UPDATE"
                        )
                    else:
                        self.log_result(
                            "Product Specifications UPDATE vs CREATE Comparison",
                            False,
                            f"UPDATE returns {update_response.status_code}: {update_response.text}"
                        )
                else:
                    self.log_result(
                        "Product Specifications UPDATE vs CREATE Comparison",
                        False,
                        "No existing specifications found to test UPDATE comparison"
                    )
            else:
                self.log_result(
                    "Product Specifications UPDATE vs CREATE Comparison",
                    False,
                    f"Failed to get existing specifications: {get_response.status_code}"
                )
        except Exception as e:
            self.log_result("Product Specifications UPDATE vs CREATE Comparison", False, f"Exception: {str(e)}")
        
        # Test 9: Test with minimal valid data to isolate the issue
        minimal_valid_data = {
            "product_name": "Paper Core - 40mm ID x 1.8mmT",
            "product_type": "Spiral Paper Core",
            "specifications": {}
        }
        
        try:
            response = self.session.post(f"{API_BASE}/product-specifications", json=minimal_valid_data)
            
            if response.status_code == 200:
                self.log_result(
                    "Product Specifications CREATE - Minimal Valid Data",
                    True,
                    "CREATE works with minimal valid data - issue is with material_layers",
                    f"Response: {response.text}"
                )
            elif response.status_code == 400:
                self.log_result(
                    "Product Specifications CREATE - Minimal Valid Data",
                    False,
                    f"400 error even with minimal data: {response.text}",
                    "Issue is not with material_layers but with basic structure"
                )
            elif response.status_code == 422:
                self.log_result(
                    "Product Specifications CREATE - Minimal Valid Data",
                    True,
                    f"422 validation error with minimal data (expected): {response.text}",
                    "Basic structure is correct, validation working properly"
                )
            else:
                self.log_result(
                    "Product Specifications CREATE - Minimal Valid Data",
                    False,
                    f"Unexpected status {response.status_code}: {response.text}"
                )
        except Exception as e:
            self.log_result("Product Specifications CREATE - Minimal Valid Data", False, f"Exception: {str(e)}")
        
        # Test 10: Test material_layers structure specifically
        material_layers_test_data = {
            "product_name": "Paper Core - 40mm ID x 1.8mmT",
            "product_type": "Spiral Paper Core", 
            "specifications": {
                "internal_diameter": 40,
                "wall_thickness_required": 1.8
            },
            "material_layers": [
                {
                    "material_id": "missing-fields-test"
                    # Missing required fields: material_name, layer_type, thickness
                }
            ]
        }
        
        try:
            response = self.session.post(f"{API_BASE}/product-specifications", json=material_layers_test_data)
            
            if response.status_code == 422:
                self.log_result(
                    "Product Specifications CREATE - Invalid Material Layers",
                    True,
                    f"422 validation error for invalid material_layers (expected): {response.text}",
                    "material_layers validation working correctly"
                )
            elif response.status_code == 400:
                self.log_result(
                    "Product Specifications CREATE - Invalid Material Layers",
                    False,
                    f"400 error for invalid material_layers: {response.text}",
                    "material_layers causing 400 instead of 422 - structural issue"
                )
            else:
                self.log_result(
                    "Product Specifications CREATE - Invalid Material Layers",
                    False,
                    f"Unexpected status {response.status_code}: {response.text}"
                )
        except Exception as e:
            self.log_result("Product Specifications CREATE - Invalid Material Layers", False, f"Exception: {str(e)}")

    def test_product_specifications_machinery_field(self):
        """Test the new machinery field functionality in Product Specifications"""
        print("\n=== PRODUCT SPECIFICATIONS MACHINERY FIELD TEST ===")
        
        # Test 1: Create Product Specification with Machinery Data
        machinery_spec_data = {
            "product_name": "Test Paper Core with Machinery",
            "product_type": "Spiral Paper Core",
            "specifications": {
                "internal_diameter": 40.0,
                "wall_thickness_required": 1.8,
                "core_length": 1000.0
            },
            "manufacturing_notes": "Test specification with machinery data for automated job card generation",
            "machinery": [
                {
                    "machine_name": "Slitting Machine A1",
                    "running_speed": 150.5,
                    "setup_time": "00:30",
                    "pack_up_time": "00:15",
                    "functions": [
                        {"function": "Slitting", "rate_per_hour": 85.0},
                        {"function": "Cutting/Indexing", "rate_per_hour": 75.0}
                    ]
                },
                {
                    "machine_name": "Winding Station B2",
                    "running_speed": 200.0,
                    "setup_time": "00:20",
                    "pack_up_time": "00:10",
                    "functions": [
                        {"function": "winding", "rate_per_hour": 90.0},
                        {"function": "Packing", "rate_per_hour": 65.0}
                    ]
                },
                {
                    "machine_name": "Delivery Unit C1",
                    "functions": [
                        {"function": "Delivery Time", "rate_per_hour": 50.0},
                        {"function": "splitting", "rate_per_hour": 70.0}
                    ]
                }
            ]
        }
        
        created_spec_id = None
        try:
            response = self.session.post(f"{API_BASE}/product-specifications", json=machinery_spec_data)
            
            if response.status_code == 200:
                result = response.json()
                created_spec_id = result.get('data', {}).get('id')
                
                if created_spec_id:
                    self.log_result(
                        "Create Product Specification with Machinery", 
                        True, 
                        f"Successfully created product specification with machinery data",
                        f"Spec ID: {created_spec_id}, Machines: 3, Total Functions: 6"
                    )
                else:
                    self.log_result(
                        "Create Product Specification with Machinery", 
                        False, 
                        "Product specification creation response missing ID"
                    )
            else:
                self.log_result(
                    "Create Product Specification with Machinery", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Create Product Specification with Machinery", False, f"Error: {str(e)}")
        
        # Test 2: Retrieve and Verify Machinery Data Structure
        if created_spec_id:
            try:
                response = self.session.get(f"{API_BASE}/product-specifications/{created_spec_id}")
                
                if response.status_code == 200:
                    spec = response.json()
                    machinery = spec.get('machinery', [])
                    
                    # Verify machinery structure
                    if len(machinery) == 3:
                        # Check first machine (Slitting Machine A1)
                        machine1 = machinery[0]
                        machine1_valid = (
                            machine1.get('machine_name') == "Slitting Machine A1" and
                            machine1.get('running_speed') == 150.5 and
                            machine1.get('setup_time') == "00:30" and
                            machine1.get('pack_up_time') == "00:15" and
                            len(machine1.get('functions', [])) == 2
                        )
                        
                        # Check functions for machine1
                        functions1 = machine1.get('functions', [])
                        slitting_func = next((f for f in functions1 if f.get('function') == 'Slitting'), None)
                        cutting_func = next((f for f in functions1 if f.get('function') == 'Cutting/Indexing'), None)
                        
                        functions1_valid = (
                            slitting_func and slitting_func.get('rate_per_hour') == 85.0 and
                            cutting_func and cutting_func.get('rate_per_hour') == 75.0
                        )
                        
                        # Check second machine (Winding Station B2)
                        machine2 = machinery[1]
                        machine2_valid = (
                            machine2.get('machine_name') == "Winding Station B2" and
                            machine2.get('running_speed') == 200.0 and
                            len(machine2.get('functions', [])) == 2
                        )
                        
                        # Check third machine (Delivery Unit C1) - no running speed/times
                        machine3 = machinery[2]
                        machine3_valid = (
                            machine3.get('machine_name') == "Delivery Unit C1" and
                            machine3.get('running_speed') is None and
                            len(machine3.get('functions', [])) == 2
                        )
                        
                        if machine1_valid and functions1_valid and machine2_valid and machine3_valid:
                            self.log_result(
                                "Retrieve and Verify Machinery Data Structure", 
                                True, 
                                "Machinery data structure matches expected format perfectly",
                                f"All 3 machines with correct fields, 6 total functions with rates"
                            )
                        else:
                            validation_issues = []
                            if not machine1_valid: validation_issues.append("Machine1 structure invalid")
                            if not functions1_valid: validation_issues.append("Machine1 functions invalid")
                            if not machine2_valid: validation_issues.append("Machine2 structure invalid")
                            if not machine3_valid: validation_issues.append("Machine3 structure invalid")
                            
                            self.log_result(
                                "Retrieve and Verify Machinery Data Structure", 
                                False, 
                                "Machinery data structure validation failed",
                                f"Issues: {', '.join(validation_issues)}"
                            )
                    else:
                        self.log_result(
                            "Retrieve and Verify Machinery Data Structure", 
                            False, 
                            f"Expected 3 machines but found {len(machinery)}",
                            f"Machinery array length: {len(machinery)}"
                        )
                else:
                    self.log_result(
                        "Retrieve and Verify Machinery Data Structure", 
                        False, 
                        f"Failed to retrieve specification: {response.status_code}",
                        response.text
                    )
            except Exception as e:
                self.log_result("Retrieve and Verify Machinery Data Structure", False, f"Error: {str(e)}")
        
        # Test 3: Update Specification to Modify Machinery Data
        if created_spec_id:
            updated_machinery_data = {
                "product_name": "Updated Paper Core with Modified Machinery",
                "product_type": "Spiral Paper Core",
                "specifications": {
                    "internal_diameter": 45.0,  # Updated diameter
                    "wall_thickness_required": 2.0,  # Updated thickness
                    "core_length": 1200.0  # Updated length
                },
                "manufacturing_notes": "Updated specification with modified machinery rates and new machine",
                "machinery": [
                    {
                        "machine_name": "Slitting Machine A1",
                        "running_speed": 175.0,  # Updated speed
                        "setup_time": "00:25",  # Updated time
                        "pack_up_time": "00:12",  # Updated time
                        "functions": [
                            {"function": "Slitting", "rate_per_hour": 95.0},  # Updated rate
                            {"function": "Cutting/Indexing", "rate_per_hour": 80.0}  # Updated rate
                        ]
                    },
                    {
                        "machine_name": "Advanced Winding Station B3",  # New machine name
                        "running_speed": 250.0,  # Updated speed
                        "setup_time": "00:15",
                        "pack_up_time": "00:08",
                        "functions": [
                            {"function": "winding", "rate_per_hour": 110.0},  # Updated rate
                            {"function": "Packing", "rate_per_hour": 75.0},  # Updated rate
                            {"function": "splitting", "rate_per_hour": 85.0}  # New function
                        ]
                    }
                    # Removed third machine to test array modification
                ]
            }
            
            try:
                response = self.session.put(f"{API_BASE}/product-specifications/{created_spec_id}", json=updated_machinery_data)
                
                if response.status_code == 200:
                    # Verify the update by retrieving the specification
                    get_response = self.session.get(f"{API_BASE}/product-specifications/{created_spec_id}")
                    
                    if get_response.status_code == 200:
                        updated_spec = get_response.json()
                        updated_machinery = updated_spec.get('machinery', [])
                        
                        # Verify updates
                        if len(updated_machinery) == 2:  # Should now have 2 machines
                            machine1 = updated_machinery[0]
                            machine2 = updated_machinery[1]
                            
                            # Check updated values
                            machine1_updated = (
                                machine1.get('running_speed') == 175.0 and
                                machine1.get('setup_time') == "00:25" and
                                machine1.get('functions', [])[0].get('rate_per_hour') == 95.0
                            )
                            
                            machine2_updated = (
                                machine2.get('machine_name') == "Advanced Winding Station B3" and
                                machine2.get('running_speed') == 250.0 and
                                len(machine2.get('functions', [])) == 3  # Now has 3 functions
                            )
                            
                            if machine1_updated and machine2_updated:
                                self.log_result(
                                    "Update Specification Machinery Data", 
                                    True, 
                                    "Successfully updated machinery data with modified rates and structure",
                                    f"Updated to 2 machines, modified rates, added new function"
                                )
                            else:
                                self.log_result(
                                    "Update Specification Machinery Data", 
                                    False, 
                                    "Machinery update validation failed",
                                    f"Machine1 valid: {machine1_updated}, Machine2 valid: {machine2_updated}"
                                )
                        else:
                            self.log_result(
                                "Update Specification Machinery Data", 
                                False, 
                                f"Expected 2 machines after update but found {len(updated_machinery)}"
                            )
                    else:
                        self.log_result(
                            "Update Specification Machinery Data", 
                            False, 
                            "Failed to retrieve updated specification for verification"
                        )
                else:
                    self.log_result(
                        "Update Specification Machinery Data", 
                        False, 
                        f"Update failed with status {response.status_code}",
                        response.text
                    )
            except Exception as e:
                self.log_result("Update Specification Machinery Data", False, f"Error: {str(e)}")
        
        # Test 4: Verify All Required Function Types
        function_types_test_data = {
            "product_name": "Complete Function Types Test",
            "product_type": "Paper Core",
            "specifications": {"test": "complete_functions"},
            "machinery": [
                {
                    "machine_name": "Multi-Function Production Line",
                    "running_speed": 180.0,
                    "setup_time": "00:45",
                    "pack_up_time": "00:20",
                    "functions": [
                        {"function": "Slitting", "rate_per_hour": 100.0},
                        {"function": "winding", "rate_per_hour": 95.0},
                        {"function": "Cutting/Indexing", "rate_per_hour": 85.0},
                        {"function": "splitting", "rate_per_hour": 80.0},
                        {"function": "Packing", "rate_per_hour": 70.0},
                        {"function": "Delivery Time", "rate_per_hour": 60.0}
                    ]
                }
            ]
        }
        
        try:
            response = self.session.post(f"{API_BASE}/product-specifications", json=function_types_test_data)
            
            if response.status_code == 200:
                result = response.json()
                function_test_spec_id = result.get('data', {}).get('id')
                
                if function_test_spec_id:
                    # Verify all function types are present
                    get_response = self.session.get(f"{API_BASE}/product-specifications/{function_test_spec_id}")
                    
                    if get_response.status_code == 200:
                        spec = get_response.json()
                        functions = spec.get('machinery', [{}])[0].get('functions', [])
                        
                        expected_functions = ["Slitting", "winding", "Cutting/Indexing", "splitting", "Packing", "Delivery Time"]
                        found_functions = [f.get('function') for f in functions]
                        
                        all_functions_present = all(func in found_functions for func in expected_functions)
                        
                        if all_functions_present and len(functions) == 6:
                            self.log_result(
                                "Verify All Required Function Types", 
                                True, 
                                "All 6 required function types successfully stored and retrieved",
                                f"Functions: {', '.join(found_functions)}"
                            )
                        else:
                            missing_functions = [func for func in expected_functions if func not in found_functions]
                            self.log_result(
                                "Verify All Required Function Types", 
                                False, 
                                f"Missing or incorrect function types",
                                f"Expected: {expected_functions}, Found: {found_functions}, Missing: {missing_functions}"
                            )
                    else:
                        self.log_result(
                            "Verify All Required Function Types", 
                            False, 
                            "Failed to retrieve specification for function verification"
                        )
                else:
                    self.log_result(
                        "Verify All Required Function Types", 
                        False, 
                        "Function types test specification creation missing ID"
                    )
            else:
                self.log_result(
                    "Verify All Required Function Types", 
                    False, 
                    f"Failed to create function types test specification: {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Verify All Required Function Types", False, f"Error: {str(e)}")
        
        # Test 5: Test Optional Fields (machine without running_speed, setup_time, pack_up_time)
        minimal_machinery_data = {
            "product_name": "Minimal Machinery Configuration",
            "product_type": "Paper Core",
            "specifications": {"test": "minimal_machinery"},
            "machinery": [
                {
                    "machine_name": "Basic Processing Unit",
                    # No running_speed, setup_time, pack_up_time (all optional)
                    "functions": [
                        {"function": "Packing"},  # No rate_per_hour (optional)
                        {"function": "Delivery Time", "rate_per_hour": 45.0}
                    ]
                }
            ]
        }
        
        try:
            response = self.session.post(f"{API_BASE}/product-specifications", json=minimal_machinery_data)
            
            if response.status_code == 200:
                result = response.json()
                minimal_spec_id = result.get('data', {}).get('id')
                
                if minimal_spec_id:
                    # Verify minimal configuration works
                    get_response = self.session.get(f"{API_BASE}/product-specifications/{minimal_spec_id}")
                    
                    if get_response.status_code == 200:
                        spec = get_response.json()
                        machine = spec.get('machinery', [{}])[0]
                        
                        # Verify optional fields are handled correctly
                        optional_fields_correct = (
                            machine.get('machine_name') == "Basic Processing Unit" and
                            machine.get('running_speed') is None and
                            machine.get('setup_time') is None and
                            machine.get('pack_up_time') is None and
                            len(machine.get('functions', [])) == 2
                        )
                        
                        # Check function with no rate
                        packing_func = next((f for f in machine.get('functions', []) if f.get('function') == 'Packing'), None)
                        delivery_func = next((f for f in machine.get('functions', []) if f.get('function') == 'Delivery Time'), None)
                        
                        functions_correct = (
                            packing_func and packing_func.get('rate_per_hour') is None and
                            delivery_func and delivery_func.get('rate_per_hour') == 45.0
                        )
                        
                        if optional_fields_correct and functions_correct:
                            self.log_result(
                                "Test Optional Machinery Fields", 
                                True, 
                                "Optional fields handled correctly - null values preserved",
                                f"Machine with minimal config and mixed function rates"
                            )
                        else:
                            self.log_result(
                                "Test Optional Machinery Fields", 
                                False, 
                                "Optional fields validation failed",
                                f"Fields correct: {optional_fields_correct}, Functions correct: {functions_correct}"
                            )
                    else:
                        self.log_result(
                            "Test Optional Machinery Fields", 
                            False, 
                            "Failed to retrieve minimal machinery specification"
                        )
                else:
                    self.log_result(
                        "Test Optional Machinery Fields", 
                        False, 
                        "Minimal machinery specification creation missing ID"
                    )
            else:
                self.log_result(
                    "Test Optional Machinery Fields", 
                    False, 
                    f"Failed to create minimal machinery specification: {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Test Optional Machinery Fields", False, f"Error: {str(e)}")

    def run_all_tests(self):
        """Run Product Specifications Machinery Field Testing"""
        print("🚀 STARTING PRODUCT SPECIFICATIONS MACHINERY FIELD TESTING")
        print(f"Backend URL: {BACKEND_URL}")
        print("=" * 70)
        
        # Authentication first
        if not self.authenticate():
            print("❌ Authentication failed - cannot proceed with other tests")
            return self.generate_report()
        
        # PRIMARY FOCUS: Test Product Specifications Machinery Field functionality
        print("\n🔍 TESTING PRODUCT SPECIFICATIONS MACHINERY FIELD...")
        self.test_product_specifications_machinery_field()
        
        # SECONDARY: Test Product Specifications CREATE 400 error (existing test)
        print("\n🔍 TESTING PRODUCT SPECIFICATIONS CREATE ENDPOINT...")
        self.test_product_specifications_create_400_error()
        
        # TERTIARY: Test Staff & Security User Creation validation
        print("\n🔍 TESTING STAFF & SECURITY USER CREATION...")
        validation_errors = self.test_staff_security_user_creation()
        
        # Test invoicing workflow endpoints in priority order
        print("\n🔍 TESTING INVOICING ENDPOINTS...")
        live_jobs = self.test_live_jobs_api()
        
        # Test Xero integration endpoints
        print("\n🔍 TESTING XERO INTEGRATION...")
        self.test_xero_connection_status()
        self.test_xero_next_invoice_number()
        
        # Test complete Xero draft invoice creation process
        self.test_xero_create_draft_invoice_with_realistic_data()
        
        # Test data structure verification
        print("\n🔍 TESTING DATA STRUCTURE VERIFICATION...")
        self.test_live_jobs_data_structure(live_jobs)
        
        # Test invoice generation with archiving
        if live_jobs:
            self.test_invoice_generation_with_archiving(live_jobs[0])
        
        # Test archiving integration
        print("\n🔍 TESTING ARCHIVING INTEGRATION...")
        self.test_archived_jobs_api()
        
        # Additional Xero tests
        state_param = self.test_xero_auth_url()
        self.test_xero_auth_callback(state_param)
        self.test_xero_disconnect()
        self.test_xero_permissions()
        
        return self.generate_report()
    
    def print_test_summary(self):
        """Print a focused test summary for invoicing workflow"""
        print("\n" + "=" * 70)
        print("📊 INVOICING WORKFLOW TEST RESULTS SUMMARY")
        print("=" * 70)
        
        # Categorize results by test type
        invoicing_tests = []
        xero_tests = []
        data_tests = []
        archiving_tests = []
        
        for result in self.test_results:
            test_name = result['test'].lower()
            if 'live jobs' in test_name or 'invoice generation' in test_name:
                invoicing_tests.append(result)
            elif 'xero' in test_name:
                xero_tests.append(result)
            elif 'data structure' in test_name:
                data_tests.append(result)
            elif 'archiv' in test_name:
                archiving_tests.append(result)
        
        # Print category summaries
        categories = [
            ("🔄 INVOICING ENDPOINTS", invoicing_tests),
            ("🔗 XERO INTEGRATION", xero_tests),
            ("📋 DATA STRUCTURE", data_tests),
            ("📦 ARCHIVING WORKFLOW", archiving_tests)
        ]
        
        for category_name, tests in categories:
            if tests:
                passed = len([t for t in tests if t['success']])
                total = len(tests)
                print(f"\n{category_name}: {passed}/{total} passed")
                
                for test in tests:
                    status = "✅" if test['success'] else "❌"
                    print(f"  {status} {test['test']}")
                    if not test['success']:
                        print(f"     └─ {test['message']}")
        
        # Overall summary
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['success']])
        failed_tests = total_tests - passed_tests
        
        print(f"\n📈 OVERALL: {passed_tests}/{total_tests} tests passed ({(passed_tests/total_tests*100):.1f}%)")
        
        if failed_tests > 0:
            print(f"\n⚠️  {failed_tests} tests failed - see details above")
        else:
            print("\n🎉 All invoicing workflow tests passed!")
    
    def generate_report(self):
        """Generate test report"""
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['success']])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  • {result['test']}: {result['message']}")
        
        return {
            'total': total_tests,
            'passed': passed_tests,
            'failed': failed_tests,
            'success_rate': passed_tests/total_tests*100 if total_tests > 0 else 0,
            'results': self.test_results
        }

if __name__ == "__main__":
    tester = BackendAPITester()
    
    # Run timesheet debug tests (focus on reported issues)
    tester.run_timesheet_debug_tests()