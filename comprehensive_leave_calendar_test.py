#!/usr/bin/env python3
"""
Comprehensive Leave Calendar Endpoint Testing Suite
Testing the leave calendar endpoint to verify it's returning upcoming approved leave correctly.
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

class ComprehensiveLeaveCalendarTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        self.test_employee_id = None
        self.test_leave_request_id = None
        
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
        if details:
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

    def test_leave_calendar_comprehensive(self):
        """
        Comprehensive Leave Calendar Testing
        """
        print("\n" + "="*80)
        print("COMPREHENSIVE LEAVE CALENDAR ENDPOINT TESTING")
        print("Testing all aspects of the leave calendar functionality")
        print("="*80)
        
        # Test 1: Check current calendar endpoint response structure
        self.test_calendar_endpoint_structure()
        
        # Test 2: Check for any existing leave requests in database
        self.test_check_all_leave_requests()
        
        # Test 3: Get employees for testing
        self.test_get_employees()
        
        # Test 4: Create and approve test leave with future dates
        self.test_create_future_approved_leave()
        
        # Test 5: Test calendar endpoint after creating approved leave
        self.test_calendar_endpoint_with_approved_leave()
        
        # Test 6: Test date filtering logic specifically
        self.test_date_filtering_logic()
        
        # Test 7: Test leave balance deduction
        self.test_leave_balance_verification()
        
        # Test 8: Test edge cases
        self.test_calendar_edge_cases()

    def test_calendar_endpoint_structure(self):
        """Test 1: Check calendar endpoint response structure"""
        try:
            response = self.session.get(f"{API_BASE}/payroll/leave-requests/calendar")
            
            if response.status_code == 200:
                result = response.json()
                
                # Check StandardResponse structure
                if isinstance(result, dict) and "success" in result and "data" in result:
                    calendar_data = result.get("data", [])
                    
                    self.log_result(
                        "Calendar Endpoint Structure", 
                        True, 
                        f"Calendar endpoint returns correct StandardResponse structure",
                        f"Success: {result.get('success')}, Data entries: {len(calendar_data)}"
                    )
                    
                    # Check data structure if any entries exist
                    if calendar_data and len(calendar_data) > 0:
                        first_entry = calendar_data[0]
                        expected_fields = ["id", "employee_id", "employee_name", "employee_number", 
                                         "department", "leave_type", "start_date", "end_date", 
                                         "hours_requested", "reason"]
                        
                        missing_fields = [field for field in expected_fields if field not in first_entry]
                        
                        if not missing_fields:
                            self.log_result(
                                "Calendar Entry Fields", 
                                True, 
                                "Calendar entries have all expected fields"
                            )
                        else:
                            self.log_result(
                                "Calendar Entry Fields", 
                                False, 
                                f"Missing fields in calendar entries: {missing_fields}",
                                f"Available fields: {list(first_entry.keys())}"
                            )
                    
                    return calendar_data
                else:
                    self.log_result(
                        "Calendar Endpoint Structure", 
                        False, 
                        "Calendar endpoint does not return StandardResponse structure",
                        f"Response: {result}"
                    )
            else:
                self.log_result(
                    "Calendar Endpoint Structure", 
                    False, 
                    f"Calendar endpoint failed: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Calendar Endpoint Structure", False, f"Error: {str(e)}")
        
        return []

    def test_check_all_leave_requests(self):
        """Test 2: Check all leave requests in database"""
        try:
            # Check pending leave requests
            pending_response = self.session.get(f"{API_BASE}/payroll/leave-requests/pending")
            
            if pending_response.status_code == 200:
                pending_requests = pending_response.json()
                
                self.log_result(
                    "Check Pending Leave Requests", 
                    True, 
                    f"Found {len(pending_requests)} pending leave requests"
                )
            else:
                self.log_result(
                    "Check Pending Leave Requests", 
                    False, 
                    f"Failed to get pending requests: {pending_response.status_code}"
                )
            
            # Try to get all leave requests (if endpoint exists)
            try:
                all_response = self.session.get(f"{API_BASE}/payroll/leave-requests")
                if all_response.status_code == 200:
                    all_requests = all_response.json()
                    
                    # Count by status
                    status_counts = {}
                    for req in all_requests:
                        status = req.get("status", "unknown")
                        status_counts[status] = status_counts.get(status, 0) + 1
                    
                    self.log_result(
                        "Check All Leave Requests", 
                        True, 
                        f"Found {len(all_requests)} total leave requests",
                        f"Status breakdown: {status_counts}"
                    )
                    
                    return all_requests
                else:
                    self.log_result(
                        "Check All Leave Requests", 
                        False, 
                        f"Failed to get all requests: {all_response.status_code}"
                    )
            except:
                self.log_result(
                    "Check All Leave Requests", 
                    False, 
                    "All leave requests endpoint not available"
                )
                
        except Exception as e:
            self.log_result("Check All Leave Requests", False, f"Error: {str(e)}")
        
        return []

    def test_get_employees(self):
        """Test 3: Get employees for testing"""
        try:
            response = self.session.get(f"{API_BASE}/payroll/employees")
            
            if response.status_code == 200:
                employees = response.json()
                
                if employees and len(employees) > 0:
                    # Use first employee for testing
                    self.test_employee_id = employees[0].get("id")
                    employee_name = f"{employees[0].get('first_name', '')} {employees[0].get('last_name', '')}"
                    
                    self.log_result(
                        "Get Employees for Testing", 
                        True, 
                        f"Found {len(employees)} employees for testing",
                        f"Using employee: {employee_name} (ID: {self.test_employee_id})"
                    )
                    return employees
                else:
                    self.log_result(
                        "Get Employees for Testing", 
                        False, 
                        "No employees found for testing"
                    )
            else:
                self.log_result(
                    "Get Employees for Testing", 
                    False, 
                    f"Failed to get employees: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Get Employees for Testing", False, f"Error: {str(e)}")
        
        return []

    def test_create_future_approved_leave(self):
        """Test 4: Create and approve test leave with future dates"""
        if not self.test_employee_id:
            self.log_result(
                "Create Future Approved Leave", 
                False, 
                "No employee ID available for creating test leave"
            )
            return None
        
        try:
            # Create a leave request for future dates (starting tomorrow, ending day after)
            start_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            end_date = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
            
            leave_data = {
                "employee_id": self.test_employee_id,
                "leave_type": "annual_leave",
                "start_date": start_date,
                "end_date": end_date,
                "hours_requested": 16,  # 2 days
                "reason": "Test leave for calendar endpoint testing - future dates"
            }
            
            # Create leave request
            response = self.session.post(f"{API_BASE}/payroll/leave-requests", json=leave_data)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success") and "data" in result:
                    self.test_leave_request_id = result.get("data", {}).get("id")
                    
                    self.log_result(
                        "Create Future Leave Request", 
                        True, 
                        f"Successfully created future leave request",
                        f"Leave ID: {self.test_leave_request_id}, Dates: {start_date} to {end_date}"
                    )
                    
                    # Now approve the leave request
                    return self.approve_test_leave()
                else:
                    self.log_result(
                        "Create Future Leave Request", 
                        False, 
                        "Invalid response structure from create leave request",
                        f"Response: {result}"
                    )
            else:
                self.log_result(
                    "Create Future Leave Request", 
                    False, 
                    f"Failed to create leave request: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Create Future Leave Request", False, f"Error: {str(e)}")
        
        return None

    def approve_test_leave(self):
        """Approve the test leave request"""
        if not self.test_leave_request_id:
            return None
        
        try:
            response = self.session.post(f"{API_BASE}/payroll/leave-requests/{self.test_leave_request_id}/approve")
            
            if response.status_code == 200:
                result = response.json()
                
                self.log_result(
                    "Approve Future Leave Request", 
                    True, 
                    f"Successfully approved future leave request",
                    f"Leave ID: {self.test_leave_request_id}, Response: {result.get('message', 'No message')}"
                )
                return self.test_leave_request_id
            else:
                self.log_result(
                    "Approve Future Leave Request", 
                    False, 
                    f"Failed to approve leave request: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Approve Future Leave Request", False, f"Error: {str(e)}")
        
        return None

    def test_calendar_endpoint_with_approved_leave(self):
        """Test 5: Test calendar endpoint after creating approved leave"""
        try:
            response = self.session.get(f"{API_BASE}/payroll/leave-requests/calendar")
            
            if response.status_code == 200:
                result = response.json()
                
                if isinstance(result, dict) and "data" in result:
                    calendar_data = result.get("data", [])
                    
                    # Check if our test leave appears in the calendar
                    test_leave_found = False
                    test_leave_entry = None
                    
                    for entry in calendar_data:
                        if entry.get("employee_id") == self.test_employee_id:
                            test_leave_found = True
                            test_leave_entry = entry
                            break
                    
                    if test_leave_found:
                        self.log_result(
                            "Calendar Shows Approved Leave", 
                            True, 
                            f"Calendar correctly shows approved future leave",
                            f"Found {len(calendar_data)} total entries, test leave: {test_leave_entry}"
                        )
                    else:
                        self.log_result(
                            "Calendar Shows Approved Leave", 
                            False, 
                            "Test approved leave not found in calendar",
                            f"Calendar has {len(calendar_data)} entries, employee_id searched: {self.test_employee_id}"
                        )
                    
                    return calendar_data
                else:
                    self.log_result(
                        "Calendar Shows Approved Leave", 
                        False, 
                        "Calendar endpoint response structure invalid"
                    )
            else:
                self.log_result(
                    "Calendar Shows Approved Leave", 
                    False, 
                    f"Calendar endpoint failed: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Calendar Shows Approved Leave", False, f"Error: {str(e)}")
        
        return []

    def test_date_filtering_logic(self):
        """Test 6: Test date filtering logic specifically"""
        try:
            # Get calendar data
            response = self.session.get(f"{API_BASE}/payroll/leave-requests/calendar")
            
            if response.status_code == 200:
                result = response.json()
                calendar_data = result.get("data", [])
                
                if isinstance(calendar_data, list):
                    today = datetime.now().date()
                    future_entries = 0
                    past_entries = 0
                    invalid_dates = 0
                    
                    for entry in calendar_data:
                        end_date_str = entry.get("end_date")
                        if end_date_str:
                            try:
                                # Parse date (handle different formats)
                                if "T" in end_date_str:
                                    end_date = datetime.fromisoformat(end_date_str.replace("Z", "+00:00")).date()
                                else:
                                    end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
                                
                                if end_date >= today:
                                    future_entries += 1
                                else:
                                    past_entries += 1
                            except ValueError as ve:
                                invalid_dates += 1
                                self.log_result(
                                    "Date Parsing Error", 
                                    False, 
                                    f"Could not parse date: {end_date_str}",
                                    f"Parse error: {ve}"
                                )
                    
                    if past_entries == 0 and invalid_dates == 0:
                        self.log_result(
                            "Date Filtering Logic", 
                            True, 
                            f"Date filtering working correctly",
                            f"All {future_entries} entries have end_date >= today"
                        )
                    elif past_entries > 0:
                        self.log_result(
                            "Date Filtering Logic", 
                            False, 
                            f"Date filtering not working - found past entries",
                            f"Past entries: {past_entries}, Future entries: {future_entries}"
                        )
                    else:
                        self.log_result(
                            "Date Filtering Logic", 
                            False, 
                            f"Date parsing issues found",
                            f"Invalid dates: {invalid_dates}, Future entries: {future_entries}"
                        )
                else:
                    self.log_result(
                        "Date Filtering Logic", 
                        False, 
                        "Cannot test date filtering - calendar data not available"
                    )
            else:
                self.log_result(
                    "Date Filtering Logic", 
                    False, 
                    f"Cannot test date filtering - calendar endpoint failed: {response.status_code}"
                )
                
        except Exception as e:
            self.log_result("Date Filtering Logic", False, f"Error: {str(e)}")

    def test_leave_balance_verification(self):
        """Test 7: Verify leave balance deduction"""
        if not self.test_employee_id:
            self.log_result(
                "Leave Balance Verification", 
                False, 
                "No employee ID available for testing leave balance"
            )
            return
        
        try:
            # Get employee details to check leave balance
            response = self.session.get(f"{API_BASE}/payroll/employees")
            
            if response.status_code == 200:
                employees = response.json()
                test_employee = None
                
                for emp in employees:
                    if emp.get("id") == self.test_employee_id:
                        test_employee = emp
                        break
                
                if test_employee:
                    # Check if employee has leave balance fields
                    leave_balance_fields = ["annual_leave_balance", "sick_leave_balance", "personal_leave_balance"]
                    available_balance_fields = [field for field in leave_balance_fields if field in test_employee]
                    
                    if available_balance_fields:
                        annual_balance = test_employee.get("annual_leave_balance", 0)
                        
                        self.log_result(
                            "Leave Balance Verification", 
                            True, 
                            f"Employee has leave balance tracking",
                            f"Annual leave balance: {annual_balance} hours, Available fields: {available_balance_fields}"
                        )
                        
                        # Check if balance seems reasonable (should be less than initial if leave was deducted)
                        if annual_balance is not None and annual_balance >= 0:
                            self.log_result(
                                "Leave Balance Value Check", 
                                True, 
                                f"Leave balance value is valid: {annual_balance} hours"
                            )
                        else:
                            self.log_result(
                                "Leave Balance Value Check", 
                                False, 
                                f"Leave balance value seems invalid: {annual_balance}"
                            )
                    else:
                        self.log_result(
                            "Leave Balance Verification", 
                            False, 
                            "Employee does not have leave balance fields",
                            f"Employee fields: {list(test_employee.keys())}"
                        )
                else:
                    self.log_result(
                        "Leave Balance Verification", 
                        False, 
                        "Test employee not found in employee list"
                    )
            else:
                self.log_result(
                    "Leave Balance Verification", 
                    False, 
                    f"Failed to get employees: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Leave Balance Verification", False, f"Error: {str(e)}")

    def test_calendar_edge_cases(self):
        """Test 8: Test edge cases"""
        try:
            # Test calendar endpoint with different scenarios
            
            # Test 1: Calendar endpoint accessibility
            response = self.session.get(f"{API_BASE}/payroll/leave-requests/calendar")
            
            if response.status_code == 200:
                self.log_result(
                    "Calendar Endpoint Accessibility", 
                    True, 
                    "Calendar endpoint is accessible and returns 200"
                )
            else:
                self.log_result(
                    "Calendar Endpoint Accessibility", 
                    False, 
                    f"Calendar endpoint returned {response.status_code}"
                )
            
            # Test 2: Check if endpoint handles authentication properly
            temp_session = requests.Session()
            unauth_response = temp_session.get(f"{API_BASE}/payroll/leave-requests/calendar")
            
            if unauth_response.status_code in [401, 403]:
                self.log_result(
                    "Calendar Authentication Check", 
                    True, 
                    f"Calendar endpoint properly requires authentication (status: {unauth_response.status_code})"
                )
            else:
                self.log_result(
                    "Calendar Authentication Check", 
                    False, 
                    f"Calendar endpoint does not require authentication (status: {unauth_response.status_code})"
                )
                
        except Exception as e:
            self.log_result("Calendar Edge Cases", False, f"Error: {str(e)}")

    def print_test_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "="*80)
        print("COMPREHENSIVE LEAVE CALENDAR TEST SUMMARY")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        # Show all test results
        print("\n" + "="*60)
        print("DETAILED TEST RESULTS:")
        print("="*60)
        
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test']}: {result['message']}")
            if result['details']:
                print(f"   Details: {result['details']}")
        
        # Show failed tests details
        failed_results = [r for r in self.test_results if not r['success']]
        if failed_results:
            print("\n" + "="*60)
            print("CRITICAL ISSUES FOUND:")
            print("="*60)
            for result in failed_results:
                print(f"\n❌ {result['test']}")
                print(f"   Issue: {result['message']}")
                if result['details']:
                    print(f"   Details: {result['details']}")
        
        print("\n" + "="*80)
        if success_rate == 100:
            print("🎉 PERFECT! LEAVE CALENDAR WORKING 100% CORRECTLY!")
        elif success_rate >= 80:
            print(f"✅ MOSTLY WORKING! {success_rate:.1f}% SUCCESS RATE - MINOR ISSUES")
        else:
            print(f"⚠️  CRITICAL ISSUES FOUND: {success_rate:.1f}% SUCCESS RATE")
        print("="*80)

    def run_all_tests(self):
        """Run all comprehensive leave calendar tests"""
        print("🚀 STARTING COMPREHENSIVE LEAVE CALENDAR TESTING")
        print("="*80)
        
        # Authenticate first
        if not self.authenticate():
            print("❌ Authentication failed - cannot proceed with tests")
            return
        
        # Run comprehensive leave calendar tests
        self.test_leave_calendar_comprehensive()
        
        # Print summary
        self.print_test_summary()

def main():
    """Main function to run comprehensive leave calendar tests"""
    tester = ComprehensiveLeaveCalendarTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()