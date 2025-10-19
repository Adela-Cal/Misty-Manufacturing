#!/usr/bin/env python3
"""
Backend API Testing Suite for Payroll Employee Synchronization
Testing new employee synchronization with Staff and Security users

PRIORITY TESTS:
1. Employee Auto-Sync with Staff and Security Users
2. Manual Sync Endpoint Testing
3. Employee Data Enrichment Verification
4. Employee Profile Creation with Default Values
5. Role to Position Mapping Verification
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

class PayrollBackendTester:
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

    def test_payroll_employee_synchronization(self):
        """
        PRIORITY TEST 1: Payroll Employee Synchronization
        Test GET /api/payroll/employees and POST /api/payroll/employees/sync
        Verify employee auto-sync with Staff and Security users
        """
        print("\n" + "="*80)
        print("PRIORITY TEST 1: PAYROLL EMPLOYEE SYNCHRONIZATION")
        print("Testing employee synchronization with Staff and Security users")
        print("="*80)
        
        # Test 1: Get current users from Staff and Security
        self.test_get_staff_security_users()
        
        # Test 2: Test GET /api/payroll/employees (auto-sync)
        self.test_get_employees_with_auto_sync()
        
        # Test 3: Test POST /api/payroll/employees/sync (manual sync)
        self.test_manual_employee_sync()
        
        # Test 4: Verify employee data matches user data
        self.test_employee_data_matches_user_data()
        
        # Test 5: Test role to position mapping
        self.test_role_to_position_mapping()
        
        # Test 6: Test employee number generation
        self.test_employee_number_generation()
        
        # Test 7: Test default values
        self.test_employee_default_values()
        
        # Test 8: Test data enrichment
        self.test_employee_data_enrichment()
        
        # Test 9: Test edge cases
        self.test_employee_sync_edge_cases()

    def test_get_staff_security_users(self):
        """Test getting users from Staff and Security system"""
        try:
            response = self.session.get(f"{API_BASE}/users")
            
            if response.status_code == 200:
                users = response.json()
                active_users = [user for user in users if user.get("is_active", True)]
                
                self.log_result(
                    "Get Staff & Security Users", 
                    True, 
                    f"Successfully retrieved {len(active_users)} active users from Staff and Security",
                    f"Total users: {len(users)}, Active users: {len(active_users)}"
                )
                return active_users
            else:
                self.log_result(
                    "Get Staff & Security Users", 
                    False, 
                    f"Failed to get users: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Get Staff & Security Users", False, f"Error: {str(e)}")
        
        return []

    def test_get_employees_with_auto_sync(self):
        """Test GET /api/payroll/employees with auto-sync functionality"""
        try:
            response = self.session.get(f"{API_BASE}/payroll/employees")
            
            if response.status_code == 200:
                employees = response.json()
                
                # Verify response structure
                if isinstance(employees, list):
                    # Check required fields for each employee
                    required_fields = [
                        "id", "user_id", "employee_number", "first_name", "last_name",
                        "email", "department", "position", "employment_type", 
                        "hourly_rate", "weekly_hours", "is_active"
                    ]
                    
                    all_valid = True
                    missing_fields_list = []
                    for emp in employees:
                        missing_fields = [field for field in required_fields if field not in emp]
                        if missing_fields:
                            all_valid = False
                            missing_fields_list.extend(missing_fields)
                    
                    if all_valid:
                        self.log_result(
                            "Get Employees with Auto-Sync", 
                            True, 
                            f"Successfully retrieved {len(employees)} employees with auto-sync",
                            f"All employees have required fields"
                        )
                        return employees
                    else:
                        self.log_result(
                            "Get Employees with Auto-Sync", 
                            False, 
                            f"Some employees missing required fields: {set(missing_fields_list)}"
                        )
                else:
                    self.log_result(
                        "Get Employees with Auto-Sync", 
                        False, 
                        "Response is not a list of employees"
                    )
            else:
                self.log_result(
                    "Get Employees with Auto-Sync", 
                    False, 
                    f"Failed to get employees: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Get Employees with Auto-Sync", False, f"Error: {str(e)}")
        
        return []

    def test_manual_employee_sync(self):
        """Test POST /api/payroll/employees/sync manual sync endpoint"""
        try:
            response = self.session.post(f"{API_BASE}/payroll/employees/sync")
            
            if response.status_code == 200:
                result = response.json()
                
                # Check response structure
                if result.get("success") and "data" in result:
                    data = result["data"]
                    created_count = data.get("created_count", 0)
                    total_employees = data.get("total_employees", 0)
                    
                    self.log_result(
                        "Manual Employee Sync", 
                        True, 
                        f"Successfully synced employees",
                        f"Created: {created_count}, Total employees: {total_employees}"
                    )
                    return data
                else:
                    self.log_result(
                        "Manual Employee Sync", 
                        False, 
                        "Invalid response structure",
                        f"Response: {result}"
                    )
            else:
                self.log_result(
                    "Manual Employee Sync", 
                    False, 
                    f"Failed to sync employees: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Manual Employee Sync", False, f"Error: {str(e)}")
        
        return {}

    def test_employee_data_matches_user_data(self):
        """Test that employee data matches user data from Staff and Security"""
        try:
            # Get users and employees
            users_response = self.session.get(f"{API_BASE}/users")
            employees_response = self.session.get(f"{API_BASE}/payroll/employees")
            
            if users_response.status_code == 200 and employees_response.status_code == 200:
                users = users_response.json()
                employees = employees_response.json()
                
                # Create user lookup by ID
                user_lookup = {user.get("id"): user for user in users if user.get("is_active", True)}
                
                matches_verified = 0
                mismatches = []
                
                for emp in employees:
                    user_id = emp.get("user_id")
                    if user_id and user_id in user_lookup:
                        user = user_lookup[user_id]
                        
                        # Verify data matches
                        checks = [
                            ("email", emp.get("email"), user.get("email")),
                            ("department", emp.get("department"), user.get("department")),
                            ("employment_type", emp.get("employment_type"), user.get("employment_type"))
                        ]
                        
                        # Check name matching
                        user_full_name = user.get("full_name", "")
                        if user_full_name:
                            name_parts = user_full_name.split(" ", 1)
                            expected_first = name_parts[0]
                            expected_last = name_parts[1] if len(name_parts) > 1 else ""
                            
                            checks.extend([
                                ("first_name", emp.get("first_name"), expected_first),
                                ("last_name", emp.get("last_name"), expected_last)
                            ])
                        
                        # Verify all checks
                        employee_valid = True
                        for field_name, emp_value, user_value in checks:
                            if emp_value != user_value and user_value:  # Only check if user has value
                                mismatches.append(f"Employee {emp.get('employee_number')}: {field_name} mismatch")
                                employee_valid = False
                        
                        if employee_valid:
                            matches_verified += 1
                
                if len(mismatches) == 0:
                    self.log_result(
                        "Employee Data Matches User Data", 
                        True, 
                        f"All {matches_verified} employees have matching user data"
                    )
                else:
                    self.log_result(
                        "Employee Data Matches User Data", 
                        False, 
                        f"Found {len(mismatches)} data mismatches",
                        f"Mismatches: {mismatches[:5]}"  # Show first 5
                    )
            else:
                self.log_result(
                    "Employee Data Matches User Data", 
                    False, 
                    "Failed to get users or employees for comparison"
                )
                
        except Exception as e:
            self.log_result("Employee Data Matches User Data", False, f"Error: {str(e)}")

    def test_role_to_position_mapping(self):
        """Test role to position mapping functionality"""
        try:
            employees_response = self.session.get(f"{API_BASE}/payroll/employees")
            
            if employees_response.status_code == 200:
                employees = employees_response.json()
                
                # Expected role to position mapping
                expected_mapping = {
                    "admin": "Administrator",
                    "manager": "Manager", 
                    "production_manager": "Production Manager",
                    "supervisor": "Supervisor",
                    "production_staff": "Production Staff",
                    "production_team": "Production Team Member"
                }
                
                mapping_correct = True
                mapping_issues = []
                
                for emp in employees:
                    role = emp.get("role")
                    position = emp.get("position")
                    
                    if role and role in expected_mapping:
                        expected_position = expected_mapping[role]
                        if position != expected_position:
                            mapping_correct = False
                            mapping_issues.append(f"Role '{role}' mapped to '{position}', expected '{expected_position}'")
                
                if mapping_correct:
                    self.log_result(
                        "Role to Position Mapping", 
                        True, 
                        f"All role to position mappings are correct for {len(employees)} employees"
                    )
                else:
                    self.log_result(
                        "Role to Position Mapping", 
                        False, 
                        f"Found {len(mapping_issues)} mapping issues",
                        f"Issues: {mapping_issues[:3]}"  # Show first 3
                    )
            else:
                self.log_result(
                    "Role to Position Mapping", 
                    False, 
                    f"Failed to get employees: {employees_response.status_code}"
                )
                
        except Exception as e:
            self.log_result("Role to Position Mapping", False, f"Error: {str(e)}")

    def test_employee_number_generation(self):
        """Test employee number generation (EMP0001, EMP0002, etc.)"""
        try:
            employees_response = self.session.get(f"{API_BASE}/payroll/employees")
            
            if employees_response.status_code == 200:
                employees = employees_response.json()
                
                # Check employee number format
                valid_numbers = 0
                invalid_numbers = []
                
                for emp in employees:
                    emp_number = emp.get("employee_number", "")
                    
                    # Check format: EMP followed by 4 digits
                    if emp_number.startswith("EMP") and len(emp_number) == 7:
                        try:
                            number_part = int(emp_number[3:])
                            if 1 <= number_part <= 9999:
                                valid_numbers += 1
                            else:
                                invalid_numbers.append(f"Number out of range: {emp_number}")
                        except ValueError:
                            invalid_numbers.append(f"Invalid number format: {emp_number}")
                    else:
                        invalid_numbers.append(f"Invalid format: {emp_number}")
                
                if len(invalid_numbers) == 0:
                    self.log_result(
                        "Employee Number Generation", 
                        True, 
                        f"All {valid_numbers} employee numbers have correct format (EMP####)"
                    )
                else:
                    self.log_result(
                        "Employee Number Generation", 
                        False, 
                        f"Found {len(invalid_numbers)} invalid employee numbers",
                        f"Invalid: {invalid_numbers[:3]}"  # Show first 3
                    )
            else:
                self.log_result(
                    "Employee Number Generation", 
                    False, 
                    f"Failed to get employees: {employees_response.status_code}"
                )
                
        except Exception as e:
            self.log_result("Employee Number Generation", False, f"Error: {str(e)}")

    def test_employee_default_values(self):
        """Test employee default values (hourly_rate=$25.00, weekly_hours=38)"""
        try:
            employees_response = self.session.get(f"{API_BASE}/payroll/employees")
            
            if employees_response.status_code == 200:
                employees = employees_response.json()
                
                correct_defaults = 0
                incorrect_defaults = []
                
                for emp in employees:
                    hourly_rate = emp.get("hourly_rate")
                    weekly_hours = emp.get("weekly_hours")
                    
                    # Check default values
                    rate_correct = hourly_rate == 25.0 or hourly_rate == "25.00"
                    hours_correct = weekly_hours == 38
                    
                    if rate_correct and hours_correct:
                        correct_defaults += 1
                    else:
                        issues = []
                        if not rate_correct:
                            issues.append(f"hourly_rate={hourly_rate} (expected 25.00)")
                        if not hours_correct:
                            issues.append(f"weekly_hours={weekly_hours} (expected 38)")
                        
                        incorrect_defaults.append(f"Employee {emp.get('employee_number')}: {', '.join(issues)}")
                
                if len(incorrect_defaults) == 0:
                    self.log_result(
                        "Employee Default Values", 
                        True, 
                        f"All {correct_defaults} employees have correct default values (hourly_rate=$25.00, weekly_hours=38)"
                    )
                else:
                    self.log_result(
                        "Employee Default Values", 
                        False, 
                        f"Found {len(incorrect_defaults)} employees with incorrect defaults",
                        f"Issues: {incorrect_defaults[:3]}"  # Show first 3
                    )
            else:
                self.log_result(
                    "Employee Default Values", 
                    False, 
                    f"Failed to get employees: {employees_response.status_code}"
                )
                
        except Exception as e:
            self.log_result("Employee Default Values", False, f"Error: {str(e)}")

    def test_employee_data_enrichment(self):
        """Test employee data enrichment with current user information"""
        try:
            # Get employees twice to test enrichment
            first_response = self.session.get(f"{API_BASE}/payroll/employees")
            second_response = self.session.get(f"{API_BASE}/payroll/employees")
            
            if first_response.status_code == 200 and second_response.status_code == 200:
                first_employees = first_response.json()
                second_employees = second_response.json()
                
                # Both calls should return the same enriched data
                if len(first_employees) == len(second_employees):
                    # Check that employees have enriched data (role field from users)
                    enriched_count = 0
                    for emp in first_employees:
                        if emp.get("role"):  # Role field indicates enrichment
                            enriched_count += 1
                    
                    if enriched_count == len(first_employees):
                        self.log_result(
                            "Employee Data Enrichment", 
                            True, 
                            f"All {enriched_count} employees have enriched data with role information"
                        )
                    else:
                        self.log_result(
                            "Employee Data Enrichment", 
                            False, 
                            f"Only {enriched_count}/{len(first_employees)} employees have enriched data"
                        )
                else:
                    self.log_result(
                        "Employee Data Enrichment", 
                        False, 
                        "Inconsistent employee count between calls"
                    )
            else:
                self.log_result(
                    "Employee Data Enrichment", 
                    False, 
                    "Failed to get employees for enrichment test"
                )
                
        except Exception as e:
            self.log_result("Employee Data Enrichment", False, f"Error: {str(e)}")

    def test_employee_sync_edge_cases(self):
        """Test edge cases for employee synchronization"""
        try:
            # Test 1: Multiple sync calls should not create duplicates
            sync1_response = self.session.post(f"{API_BASE}/payroll/employees/sync")
            sync2_response = self.session.post(f"{API_BASE}/payroll/employees/sync")
            
            if sync1_response.status_code == 200 and sync2_response.status_code == 200:
                sync1_data = sync1_response.json().get("data", {})
                sync2_data = sync2_response.json().get("data", {})
                
                # Second sync should create 0 new employees
                if sync2_data.get("created_count", -1) == 0:
                    self.log_result(
                        "Employee Sync - No Duplicates", 
                        True, 
                        "Multiple sync calls do not create duplicate employees"
                    )
                else:
                    self.log_result(
                        "Employee Sync - No Duplicates", 
                        False, 
                        f"Second sync created {sync2_data.get('created_count')} employees (expected 0)"
                    )
            else:
                self.log_result(
                    "Employee Sync - No Duplicates", 
                    False, 
                    "Failed to test duplicate sync calls"
                )
            
            # Test 2: Check response structure
            employees_response = self.session.get(f"{API_BASE}/payroll/employees")
            if employees_response.status_code == 200:
                employees = employees_response.json()
                
                # Verify expected response structure matches API specification
                if len(employees) > 0:
                    sample_employee = employees[0]
                    expected_structure_fields = [
                        "id", "user_id", "employee_number", "first_name", "last_name",
                        "email", "phone", "department", "position", "role", "start_date",
                        "employment_type", "hourly_rate", "weekly_hours", 
                        "annual_leave_balance", "sick_leave_balance", "personal_leave_balance", "is_active"
                    ]
                    
                    missing_fields = [field for field in expected_structure_fields if field not in sample_employee]
                    
                    if len(missing_fields) == 0:
                        self.log_result(
                            "Employee Response Structure", 
                            True, 
                            "Employee response structure matches API specification"
                        )
                    else:
                        self.log_result(
                            "Employee Response Structure", 
                            False, 
                            f"Missing fields in response: {missing_fields}"
                        )
                else:
                    self.log_result(
                        "Employee Response Structure", 
                        False, 
                        "No employees returned to verify structure"
                    )
            
        except Exception as e:
            self.log_result("Employee Sync Edge Cases", False, f"Error: {str(e)}")

    def print_test_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "="*80)
        print("PAYROLL EMPLOYEE SYNCHRONIZATION TEST SUMMARY")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        # Group results by category
        categories = {
            "Employee Auto-Sync": [],
            "Manual Sync": [],
            "Data Validation": [],
            "Edge Cases": [],
            "Other": []
        }
        
        for result in self.test_results:
            test_name = result['test']
            if 'Auto-Sync' in test_name or 'Get Employees' in test_name:
                categories["Employee Auto-Sync"].append(result)
            elif 'Manual' in test_name and 'Sync' in test_name:
                categories["Manual Sync"].append(result)
            elif any(keyword in test_name for keyword in ['Data Matches', 'Role to Position', 'Number Generation', 'Default Values', 'Enrichment', 'Structure']):
                categories["Data Validation"].append(result)
            elif 'Edge Cases' in test_name or 'Duplicates' in test_name:
                categories["Edge Cases"].append(result)
            else:
                categories["Other"].append(result)
        
        print("\n" + "="*60)
        print("RESULTS BY CATEGORY:")
        print("="*60)
        
        for category, results in categories.items():
            if results:
                category_passed = sum(1 for r in results if r['success'])
                category_total = len(results)
                category_rate = (category_passed / category_total * 100) if category_total > 0 else 0
                
                print(f"\n{category}: {category_passed}/{category_total} ({category_rate:.1f}%)")
                for result in results:
                    status = "✅" if result['success'] else "❌"
                    print(f"  {status} {result['test']}")
        
        # Show failed tests details
        failed_results = [r for r in self.test_results if not r['success']]
        if failed_results:
            print("\n" + "="*60)
            print("FAILED TESTS DETAILS:")
            print("="*60)
            for result in failed_results:
                print(f"\n❌ {result['test']}")
                print(f"   Message: {result['message']}")
                if result['details']:
                    print(f"   Details: {result['details']}")
        
        print("\n" + "="*80)
        if success_rate == 100:
            print("🎉 PERFECT! 100% SUCCESS RATE ACHIEVED!")
        elif success_rate >= 90:
            print(f"🎯 EXCELLENT! {success_rate:.1f}% SUCCESS RATE")
        elif success_rate >= 80:
            print(f"✅ GOOD! {success_rate:.1f}% SUCCESS RATE")
        else:
            print(f"⚠️  NEEDS IMPROVEMENT: {success_rate:.1f}% SUCCESS RATE")
        print("="*80)

    def run_comprehensive_tests(self):
        """Run all comprehensive tests for payroll employee synchronization"""
        print("\n" + "="*80)
        print("PAYROLL EMPLOYEE SYNCHRONIZATION TESTING")
        print("Testing new employee synchronization with Staff and Security users")
        print("="*80)
        
        # Step 1: Authenticate
        if not self.authenticate():
            print("❌ Authentication failed - cannot proceed with tests")
            return
        
        # Step 2: Run payroll synchronization tests
        self.test_payroll_employee_synchronization()
        
        # Step 3: Print comprehensive summary
        self.print_test_summary()

if __name__ == "__main__":
    tester = PayrollBackendTester()
    tester.run_comprehensive_tests()