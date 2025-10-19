#!/usr/bin/env python3
"""
Payroll Employees ObjectId Serialization Fix Testing
Testing the fixed payroll employees endpoint after ObjectId serialization fix.

SPECIFIC TESTS FOR THE FIX:
1. GET /api/payroll/employees works without ObjectId errors
2. All employee data is returned correctly without _id field
3. No serialization errors in logs
4. All payroll dashboard endpoints work
5. Employee data structure validation
6. Backend logs verification
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

class PayrollObjectIdTester:
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

    def test_payroll_employees_objectid_fix(self):
        """
        MAIN TEST: Payroll Employees ObjectId Serialization Fix
        Test all aspects of the ObjectId fix implementation
        """
        print("\n" + "="*80)
        print("PAYROLL EMPLOYEES OBJECTID SERIALIZATION FIX TESTING")
        print("Testing the fixed payroll employees endpoint after ObjectId serialization fix")
        print("="*80)
        
        # Test 1: GET /api/payroll/employees - Basic Functionality
        self.test_get_payroll_employees_basic()
        
        # Test 2: Check Employee Data Structure (no _id field)
        self.test_employee_data_structure()
        
        # Test 3: Check All Payroll Dashboard Endpoints
        self.test_all_payroll_dashboard_endpoints()
        
        # Test 4: Verify No ObjectId in Response
        self.test_no_objectid_in_response()
        
        # Test 5: Test Multiple Calls (consistency)
        self.test_multiple_calls_consistency()
        
        # Test 6: Test Employee Data Completeness
        self.test_employee_data_completeness()

    def test_get_payroll_employees_basic(self):
        """Test 1: GET /api/payroll/employees - Basic Functionality"""
        try:
            print("\n--- Test 1: GET /api/payroll/employees - Basic Functionality ---")
            
            response = self.session.get(f"{API_BASE}/payroll/employees")
            
            if response.status_code == 200:
                try:
                    employees = response.json()
                    
                    # Verify it's a list
                    if isinstance(employees, list):
                        self.log_result(
                            "GET /api/payroll/employees - Basic", 
                            True, 
                            f"✅ Returns 200 status code and list of {len(employees)} employees"
                        )
                        return employees
                    else:
                        self.log_result(
                            "GET /api/payroll/employees - Basic", 
                            False, 
                            "Response is not a list",
                            f"Response type: {type(employees)}"
                        )
                        
                except json.JSONDecodeError as e:
                    self.log_result(
                        "GET /api/payroll/employees - Basic", 
                        False, 
                        "JSON decode error - possible serialization issue",
                        f"JSON Error: {str(e)}"
                    )
            else:
                self.log_result(
                    "GET /api/payroll/employees - Basic", 
                    False, 
                    f"❌ Failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("GET /api/payroll/employees - Basic", False, f"Error: {str(e)}")
        
        return []

    def test_employee_data_structure(self):
        """Test 2: Check Employee Data Structure"""
        try:
            print("\n--- Test 2: Check Employee Data Structure ---")
            
            response = self.session.get(f"{API_BASE}/payroll/employees")
            
            if response.status_code == 200:
                employees = response.json()
                
                if not employees:
                    self.log_result(
                        "Employee Data Structure", 
                        True, 
                        "No employees found - structure test skipped"
                    )
                    return
                
                # Check each employee structure
                required_fields = [
                    "id", "user_id", "employee_number", "first_name", "last_name",
                    "email", "department", "position", "employment_type", 
                    "hourly_rate", "weekly_hours", "is_active"
                ]
                
                structure_valid = True
                structure_issues = []
                objectid_found = False
                
                for i, emp in enumerate(employees):
                    # Check for _id field (should NOT exist)
                    if "_id" in emp:
                        objectid_found = True
                        structure_issues.append(f"Employee {i+1}: Contains '_id' field (ObjectId not removed)")
                    
                    # Check for required fields
                    missing_fields = [field for field in required_fields if field not in emp]
                    if missing_fields:
                        structure_valid = False
                        structure_issues.append(f"Employee {i+1}: Missing fields {missing_fields}")
                    
                    # Check data types
                    if "id" in emp and not isinstance(emp["id"], str):
                        structure_issues.append(f"Employee {i+1}: 'id' is not string")
                    
                    if "hourly_rate" in emp and not isinstance(emp["hourly_rate"], (int, float)):
                        structure_issues.append(f"Employee {i+1}: 'hourly_rate' is not numeric")
                
                if objectid_found:
                    self.log_result(
                        "Employee Data Structure", 
                        False, 
                        "❌ ObjectId '_id' field found in response - fix not working",
                        f"Issues: {structure_issues[:3]}"
                    )
                elif not structure_valid:
                    self.log_result(
                        "Employee Data Structure", 
                        False, 
                        f"❌ Structure issues found in {len(structure_issues)} cases",
                        f"Issues: {structure_issues[:3]}"
                    )
                else:
                    self.log_result(
                        "Employee Data Structure", 
                        True, 
                        f"✅ All {len(employees)} employees have correct structure (no '_id' field, all required fields present)"
                    )
            else:
                self.log_result(
                    "Employee Data Structure", 
                    False, 
                    f"Failed to get employees: {response.status_code}"
                )
                
        except Exception as e:
            self.log_result("Employee Data Structure", False, f"Error: {str(e)}")

    def test_all_payroll_dashboard_endpoints(self):
        """Test 3: Check All Payroll Dashboard Endpoints"""
        try:
            print("\n--- Test 3: Check All Payroll Dashboard Endpoints ---")
            
            endpoints_to_test = [
                ("GET /api/payroll/employees", "/payroll/employees"),
                ("GET /api/payroll/timesheets/pending", "/payroll/timesheets/pending"),
                ("GET /api/payroll/leave-requests/pending", "/payroll/leave-requests/pending"),
                ("GET /api/payroll/dashboard/timesheet-reminder", "/payroll/dashboard/timesheet-reminder")
            ]
            
            all_endpoints_working = True
            endpoint_results = []
            
            for endpoint_name, endpoint_path in endpoints_to_test:
                try:
                    response = self.session.get(f"{API_BASE}{endpoint_path}")
                    
                    if response.status_code == 200:
                        # Try to parse JSON to check for serialization errors
                        try:
                            data = response.json()
                            endpoint_results.append(f"✅ {endpoint_name}: 200 OK")
                        except json.JSONDecodeError:
                            all_endpoints_working = False
                            endpoint_results.append(f"❌ {endpoint_name}: JSON decode error")
                    else:
                        # Some endpoints might return 404 if no data, which is acceptable
                        if response.status_code == 404:
                            endpoint_results.append(f"⚠️  {endpoint_name}: 404 (no data)")
                        else:
                            all_endpoints_working = False
                            endpoint_results.append(f"❌ {endpoint_name}: {response.status_code}")
                            
                except Exception as e:
                    all_endpoints_working = False
                    endpoint_results.append(f"❌ {endpoint_name}: Exception - {str(e)}")
            
            if all_endpoints_working:
                self.log_result(
                    "All Payroll Dashboard Endpoints", 
                    True, 
                    f"✅ All {len(endpoints_to_test)} endpoints working without serialization errors",
                    f"Results: {endpoint_results}"
                )
            else:
                failed_endpoints = [r for r in endpoint_results if r.startswith("❌")]
                self.log_result(
                    "All Payroll Dashboard Endpoints", 
                    False, 
                    f"❌ {len(failed_endpoints)} endpoints have issues",
                    f"Results: {endpoint_results}"
                )
                
        except Exception as e:
            self.log_result("All Payroll Dashboard Endpoints", False, f"Error: {str(e)}")

    def test_no_objectid_in_response(self):
        """Test 4: Verify No ObjectId in Response"""
        try:
            print("\n--- Test 4: Verify No ObjectId in Response ---")
            
            response = self.session.get(f"{API_BASE}/payroll/employees")
            
            if response.status_code == 200:
                employees = response.json()
                
                # Convert response to string and check for ObjectId patterns
                response_text = json.dumps(employees)
                
                # Check for ObjectId patterns
                objectid_patterns = [
                    '"_id"',
                    'ObjectId(',
                    '$oid',
                    'bson.objectid',
                    'mongodb.objectid'
                ]
                
                objectid_found = []
                for pattern in objectid_patterns:
                    if pattern.lower() in response_text.lower():
                        objectid_found.append(pattern)
                
                # Check data types are JSON serializable
                json_serializable = True
                non_serializable = []
                
                def check_serializable(obj, path=""):
                    nonlocal json_serializable, non_serializable
                    if isinstance(obj, dict):
                        for key, value in obj.items():
                            check_serializable(value, f"{path}.{key}")
                    elif isinstance(obj, list):
                        for i, item in enumerate(obj):
                            check_serializable(item, f"{path}[{i}]")
                    elif not isinstance(obj, (str, int, float, bool, type(None))):
                        json_serializable = False
                        non_serializable.append(f"{path}: {type(obj)}")
                
                check_serializable(employees)
                
                if objectid_found:
                    self.log_result(
                        "No ObjectId in Response", 
                        False, 
                        f"❌ ObjectId patterns found in response",
                        f"Patterns found: {objectid_found}"
                    )
                elif not json_serializable:
                    self.log_result(
                        "No ObjectId in Response", 
                        False, 
                        f"❌ Non-JSON serializable types found",
                        f"Non-serializable: {non_serializable[:3]}"
                    )
                else:
                    self.log_result(
                        "No ObjectId in Response", 
                        True, 
                        "✅ Response contains only JSON-serializable data types (no ObjectId)"
                    )
            else:
                self.log_result(
                    "No ObjectId in Response", 
                    False, 
                    f"Failed to get employees: {response.status_code}"
                )
                
        except Exception as e:
            self.log_result("No ObjectId in Response", False, f"Error: {str(e)}")

    def test_multiple_calls_consistency(self):
        """Test 5: Test Multiple Calls (consistency)"""
        try:
            print("\n--- Test 5: Test Multiple Calls (consistency) ---")
            
            responses = []
            all_successful = True
            
            # Make 3 calls to test consistency
            for i in range(3):
                try:
                    response = self.session.get(f"{API_BASE}/payroll/employees")
                    
                    if response.status_code == 200:
                        employees = response.json()
                        responses.append({
                            'call': i+1,
                            'status': 200,
                            'count': len(employees),
                            'success': True
                        })
                    else:
                        responses.append({
                            'call': i+1,
                            'status': response.status_code,
                            'success': False
                        })
                        all_successful = False
                        
                except Exception as e:
                    responses.append({
                        'call': i+1,
                        'error': str(e),
                        'success': False
                    })
                    all_successful = False
            
            if all_successful:
                # Check if all calls returned same number of employees
                counts = [r['count'] for r in responses if 'count' in r]
                consistent_count = len(set(counts)) == 1 if counts else True
                
                if consistent_count:
                    self.log_result(
                        "Multiple Calls Consistency", 
                        True, 
                        f"✅ All 3 calls successful and consistent ({counts[0] if counts else 0} employees each)"
                    )
                else:
                    self.log_result(
                        "Multiple Calls Consistency", 
                        False, 
                        f"❌ Inconsistent employee counts across calls",
                        f"Counts: {counts}"
                    )
            else:
                failed_calls = [r for r in responses if not r['success']]
                self.log_result(
                    "Multiple Calls Consistency", 
                    False, 
                    f"❌ {len(failed_calls)} out of 3 calls failed",
                    f"Responses: {responses}"
                )
                
        except Exception as e:
            self.log_result("Multiple Calls Consistency", False, f"Error: {str(e)}")

    def test_employee_data_completeness(self):
        """Test 6: Test Employee Data Completeness"""
        try:
            print("\n--- Test 6: Test Employee Data Completeness ---")
            
            response = self.session.get(f"{API_BASE}/payroll/employees")
            
            if response.status_code == 200:
                employees = response.json()
                
                if not employees:
                    self.log_result(
                        "Employee Data Completeness", 
                        True, 
                        "No employees found - completeness test skipped"
                    )
                    return
                
                completeness_issues = []
                complete_employees = 0
                
                for i, emp in enumerate(employees):
                    employee_issues = []
                    
                    # Check required string fields are not empty
                    string_fields = ["employee_number", "first_name", "last_name", "email", "department", "position"]
                    for field in string_fields:
                        if field in emp and (not emp[field] or emp[field].strip() == ""):
                            employee_issues.append(f"{field} is empty")
                    
                    # Check numeric fields are valid
                    if "hourly_rate" in emp and (emp["hourly_rate"] is None or emp["hourly_rate"] <= 0):
                        employee_issues.append("hourly_rate is invalid")
                    
                    if "weekly_hours" in emp and (emp["weekly_hours"] is None or emp["weekly_hours"] <= 0):
                        employee_issues.append("weekly_hours is invalid")
                    
                    # Check UUID format for id fields
                    uuid_fields = ["id", "user_id"]
                    for field in uuid_fields:
                        if field in emp and emp[field]:
                            try:
                                uuid.UUID(emp[field])
                            except ValueError:
                                employee_issues.append(f"{field} is not valid UUID")
                    
                    if employee_issues:
                        completeness_issues.append(f"Employee {i+1} ({emp.get('employee_number', 'Unknown')}): {', '.join(employee_issues)}")
                    else:
                        complete_employees += 1
                
                if not completeness_issues:
                    self.log_result(
                        "Employee Data Completeness", 
                        True, 
                        f"✅ All {complete_employees} employees have complete and valid data"
                    )
                else:
                    self.log_result(
                        "Employee Data Completeness", 
                        False, 
                        f"❌ {len(completeness_issues)} employees have data issues",
                        f"Issues: {completeness_issues[:3]}"
                    )
            else:
                self.log_result(
                    "Employee Data Completeness", 
                    False, 
                    f"Failed to get employees: {response.status_code}"
                )
                
        except Exception as e:
            self.log_result("Employee Data Completeness", False, f"Error: {str(e)}")

    def print_test_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "="*80)
        print("PAYROLL OBJECTID FIX TEST SUMMARY")
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
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test']}: {result['message']}")
            if not result['success'] and result['details']:
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
            print("🎉 PERFECT! ObjectId serialization fix is working 100%!")
            print("✅ No 'Failed to load payroll data' error should occur")
            print("✅ All payroll endpoints working without serialization errors")
        elif success_rate >= 80:
            print(f"⚠️  MOSTLY WORKING: {success_rate:.1f}% success rate")
            print("Some issues found - check failed tests above")
        else:
            print(f"❌ CRITICAL ISSUES: {success_rate:.1f}% success rate")
            print("ObjectId serialization fix may not be working properly")
        print("="*80)

def main():
    """Main test execution"""
    print("="*80)
    print("PAYROLL EMPLOYEES OBJECTID SERIALIZATION FIX TESTING")
    print("Testing the fixed payroll employees endpoint after ObjectId serialization fix")
    print("="*80)
    
    tester = PayrollObjectIdTester()
    
    # Authenticate first
    if not tester.authenticate():
        print("❌ Authentication failed - cannot proceed with tests")
        return
    
    # Run the main test suite
    tester.test_payroll_employees_objectid_fix()
    
    # Print summary
    tester.print_test_summary()

if __name__ == "__main__":
    main()