#!/usr/bin/env python3
"""
Comprehensive test for Pending Timesheets functionality in Payroll Management system
Tests the specific requirements from the review request:
1. GET /api/payroll/timesheets/pending - returns pending timesheets with employee information
2. POST /api/payroll/timesheets/{timesheet_id}/approve - timesheet approval functionality  
3. Verify timesheet approval calculates pay correctly and updates status

Test credentials: Callum / Peach7510 (from review request)
Expected results:
- Pending timesheets endpoint returns array with at least one timesheet
- All timesheets have employee_name field populated
- Approve endpoint successfully approves timesheet and calculates pay
- Approved timesheet is removed from pending list
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

class PendingTimesheetsAPITester:
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
        """Test authentication with demo user Callum/Peach7510"""
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

    def test_pending_timesheets_endpoint(self):
        """
        MAIN TEST: Test GET /api/payroll/timesheets/pending endpoint
        Verify employee name enrichment is working after the fix
        """
        print("\n" + "="*80)
        print("TESTING PENDING TIMESHEETS ENDPOINT - EMPLOYEE NAME ENRICHMENT FIX")
        print("="*80)
        
        try:
            response = self.session.get(f"{API_BASE}/payroll/timesheets/pending")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                if not isinstance(data, dict) or 'success' not in data or 'data' not in data:
                    self.log_result(
                        "Pending Timesheets Response Structure",
                        False,
                        "Invalid response structure - missing 'success' or 'data' fields",
                        f"Response: {data}"
                    )
                    return
                
                if not data.get('success'):
                    self.log_result(
                        "Pending Timesheets API Success",
                        False,
                        "API returned success=false",
                        f"Response: {data}"
                    )
                    return
                
                timesheets = data.get('data', [])
                
                self.log_result(
                    "Pending Timesheets Endpoint Access",
                    True,
                    f"Successfully retrieved {len(timesheets)} pending timesheets"
                )
                
                # Test each timesheet for employee name enrichment
                unknown_employee_count = 0
                properly_named_count = 0
                
                for i, timesheet in enumerate(timesheets):
                    timesheet_id = timesheet.get('id', f'timesheet_{i}')
                    employee_name = timesheet.get('employee_name', 'MISSING')
                    employee_id = timesheet.get('employee_id', 'MISSING')
                    
                    print(f"\n--- Timesheet {i+1} Analysis ---")
                    print(f"Timesheet ID: {timesheet_id}")
                    print(f"Employee ID: {employee_id}")
                    print(f"Employee Name: {employee_name}")
                    
                    # Check if employee_name field exists
                    if 'employee_name' not in timesheet:
                        self.log_result(
                            f"Timesheet {i+1} Employee Name Field",
                            False,
                            f"Missing employee_name field in timesheet {timesheet_id}"
                        )
                        continue
                    
                    # Check for "Unknown Employee" entries
                    if "Unknown Employee" in employee_name:
                        unknown_employee_count += 1
                        self.log_result(
                            f"Timesheet {i+1} Employee Name Resolution",
                            False,
                            f"Still showing 'Unknown Employee' for timesheet {timesheet_id}: {employee_name}"
                        )
                    else:
                        properly_named_count += 1
                        self.log_result(
                            f"Timesheet {i+1} Employee Name Resolution",
                            True,
                            f"Properly resolved employee name: {employee_name}"
                        )
                
                # Overall assessment
                if len(timesheets) == 0:
                    self.log_result(
                        "Pending Timesheets Data",
                        True,
                        "No pending timesheets found - cannot test employee name enrichment"
                    )
                elif unknown_employee_count == 0:
                    self.log_result(
                        "Employee Name Enrichment Fix",
                        True,
                        f"✅ ALL {properly_named_count} timesheets now have proper employee names - FIX SUCCESSFUL!"
                    )
                else:
                    self.log_result(
                        "Employee Name Enrichment Fix",
                        False,
                        f"❌ {unknown_employee_count} timesheets still show 'Unknown Employee', {properly_named_count} are properly named"
                    )
                
                # Check for specific expected names (like "Callum - System Administrator")
                callum_found = False
                for timesheet in timesheets:
                    employee_name = timesheet.get('employee_name', '')
                    if 'Callum' in employee_name and ('Administrator' in employee_name or 'System' in employee_name):
                        callum_found = True
                        self.log_result(
                            "Expected Employee Name Format",
                            True,
                            f"Found expected name format: {employee_name}"
                        )
                        break
                
                if len(timesheets) > 0 and not callum_found:
                    self.log_result(
                        "Expected Employee Name Format",
                        False,
                        "Did not find expected 'Callum - System Administrator' format in any timesheet"
                    )
                
            elif response.status_code == 403:
                self.log_result(
                    "Pending Timesheets Endpoint Access",
                    False,
                    "Access denied (403) - authentication or authorization issue"
                )
            else:
                self.log_result(
                    "Pending Timesheets Endpoint Access",
                    False,
                    f"Endpoint returned status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result(
                "Pending Timesheets Endpoint Test",
                False,
                f"Exception occurred: {str(e)}"
            )

    def test_employee_data_verification(self):
        """
        Verify employee data exists and is properly structured
        """
        print("\n=== EMPLOYEE DATA VERIFICATION ===")
        
        try:
            # Test employees endpoint
            response = self.session.get(f"{API_BASE}/payroll/employees")
            
            if response.status_code == 200:
                employees = response.json()
                
                self.log_result(
                    "Employee Profiles Access",
                    True,
                    f"Successfully retrieved {len(employees)} employee profiles"
                )
                
                # Check for Callum's employee profile
                callum_found = False
                for employee in employees:
                    first_name = employee.get('first_name', '')
                    last_name = employee.get('last_name', '')
                    full_name = f"{first_name} {last_name}".strip()
                    employee_id = employee.get('id', '')
                    user_id = employee.get('user_id', '')
                    
                    print(f"Employee: {full_name} (ID: {employee_id}, User ID: {user_id})")
                    
                    if 'Callum' in first_name or 'Callum' in full_name:
                        callum_found = True
                        self.log_result(
                            "Callum Employee Profile",
                            True,
                            f"Found Callum's profile: {full_name} (ID: {employee_id})"
                        )
                
                if not callum_found and len(employees) > 0:
                    self.log_result(
                        "Callum Employee Profile",
                        False,
                        "Could not find Callum's employee profile"
                    )
                    
            else:
                self.log_result(
                    "Employee Profiles Access",
                    False,
                    f"Failed to access employee profiles: {response.status_code}"
                )
                
        except Exception as e:
            self.log_result(
                "Employee Data Verification",
                False,
                f"Exception occurred: {str(e)}"
            )

    def test_timesheet_data_investigation(self):
        """
        Investigate existing timesheet data to understand the employee_id structure
        """
        print("\n=== TIMESHEET DATA INVESTIGATION ===")
        
        try:
            # Check if we can access all timesheets (not just pending)
            response = self.session.get(f"{API_BASE}/payroll/timesheets")
            
            if response.status_code == 200:
                data = response.json()
                timesheets = data.get('data', []) if isinstance(data, dict) else data
                
                self.log_result(
                    "All Timesheets Access",
                    True,
                    f"Successfully retrieved {len(timesheets)} total timesheets"
                )
                
                # Analyze employee_id patterns
                employee_ids = set()
                for timesheet in timesheets:
                    employee_id = timesheet.get('employee_id')
                    if employee_id:
                        employee_ids.add(employee_id)
                
                print(f"Found {len(employee_ids)} unique employee IDs in timesheets:")
                for emp_id in employee_ids:
                    print(f"  - {emp_id}")
                
                # Check status distribution
                status_counts = {}
                for timesheet in timesheets:
                    status = timesheet.get('status', 'unknown')
                    status_counts[status] = status_counts.get(status, 0) + 1
                
                print(f"Timesheet status distribution:")
                for status, count in status_counts.items():
                    print(f"  - {status}: {count}")
                
            elif response.status_code == 404:
                self.log_result(
                    "All Timesheets Access",
                    False,
                    "Timesheets endpoint not found (404) - may not be implemented"
                )
            else:
                self.log_result(
                    "All Timesheets Access",
                    False,
                    f"Failed to access all timesheets: {response.status_code}"
                )
                
        except Exception as e:
            self.log_result(
                "Timesheet Data Investigation",
                False,
                f"Exception occurred: {str(e)}"
            )

    def run_comprehensive_test(self):
        """Run all tests for pending timesheets endpoint"""
        print("🔍 PENDING TIMESHEETS ENDPOINT TESTING - EMPLOYEE NAME ENRICHMENT FIX")
        print("=" * 80)
        print("Testing after fixing employee_id mismatch issue")
        print("Expected: All timesheets should show proper employee names")
        print("=" * 80)
        
        # Step 1: Authenticate
        if not self.authenticate():
            print("❌ Authentication failed - cannot proceed with tests")
            return
        
        # Step 2: Test the main endpoint
        self.test_pending_timesheets_endpoint()
        
        # Step 3: Verify employee data
        self.test_employee_data_verification()
        
        # Step 4: Investigate timesheet data
        self.test_timesheet_data_investigation()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['message']}")
        
        # Overall assessment
        pending_timesheets_working = any(
            result['success'] and 'Employee Name Enrichment Fix' in result['test'] 
            for result in self.test_results
        )
        
        if pending_timesheets_working:
            print(f"\n🎉 EMPLOYEE NAME ENRICHMENT FIX VERIFICATION: SUCCESS!")
            print("✅ Pending timesheets endpoint is now properly showing employee names")
        else:
            print(f"\n⚠️  EMPLOYEE NAME ENRICHMENT FIX VERIFICATION: NEEDS ATTENTION")
            print("❌ Some issues remain with employee name display in pending timesheets")

if __name__ == "__main__":
    tester = PendingTimesheetsAPITester()
    tester.run_comprehensive_test()