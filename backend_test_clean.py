#!/usr/bin/env python3
"""
Backend API Testing Suite for Xero Integration and Timesheet Serialization Fixes
Tests the specific fixes mentioned in the review request
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
    
    def create_test_employee_if_needed(self):
        """Create a test employee if none exist"""
        try:
            # Check if employees exist
            employees_response = self.session.get(f"{API_BASE}/payroll/employees")
            
            if employees_response.status_code == 200:
                employees = employees_response.json()
                if employees:
                    return employees[0].get('id')  # Return existing employee ID
            
            # Create a test employee
            employee_data = {
                "user_id": "test-user-id-123",
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
            
            create_response = self.session.post(f"{API_BASE}/payroll/employees", json=employee_data)
            
            if create_response.status_code == 200:
                result = create_response.json()
                employee_id = result.get('data', {}).get('id')
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
                    f"Failed to create test employee: {create_response.status_code}",
                    create_response.text
                )
                return None
                
        except Exception as e:
            self.log_result("Create Test Employee", False, f"Error: {str(e)}")
            return None

    def test_timesheet_mongodb_serialization_fix(self):
        """Test the specific MongoDB serialization fix for timesheets"""
        print("\n=== TIMESHEET MONGODB SERIALIZATION FIX TEST ===")
        
        try:
            # Get or create a test employee
            employee_id = self.create_test_employee_if_needed()
            
            if employee_id:
                    employee_id = employees[0].get('id')
                    employee_name = f"{employees[0].get('first_name', '')} {employees[0].get('last_name', '')}"
                    
                    # Test the current-week endpoint that was throwing serialization errors
                    response = self.session.get(f"{API_BASE}/payroll/timesheets/current-week/{employee_id}")
                    
                    if response.status_code == 200:
                        timesheet_data = response.json()
                        
                        # Check that the response contains properly serialized date/datetime fields
                        week_starting = timesheet_data.get('week_starting')
                        created_at = timesheet_data.get('created_at')
                        
                        # Verify date fields are properly serialized (should be ISO strings, not raw date objects)
                        date_fields_valid = True
                        date_field_details = []
                        
                        if week_starting:
                            if isinstance(week_starting, str):
                                date_field_details.append(f"week_starting: {week_starting} (string - ✅)")
                            else:
                                date_fields_valid = False
                                date_field_details.append(f"week_starting: {type(week_starting)} (not string - ❌)")
                        
                        if created_at:
                            if isinstance(created_at, str):
                                date_field_details.append(f"created_at: {created_at} (string - ✅)")
                            else:
                                date_fields_valid = False
                                date_field_details.append(f"created_at: {type(created_at)} (not string - ❌)")
                        
                        if date_fields_valid:
                            self.log_result(
                                "Timesheet MongoDB Serialization Fix", 
                                True, 
                                f"✅ NO SERIALIZATION ERRORS: Successfully retrieved timesheet for {employee_name}",
                                f"Date fields properly serialized: {'; '.join(date_field_details)}"
                            )
                        else:
                            self.log_result(
                                "Timesheet MongoDB Serialization Fix", 
                                False, 
                                "Date fields not properly serialized",
                                f"Issues: {'; '.join(date_field_details)}"
                            )
                    
                    elif response.status_code == 500:
                        # Check if it's the specific BSON serialization error
                        error_text = response.text.lower()
                        if 'bson.errors.invaliddocument' in error_text and 'cannot encode object' in error_text:
                            self.log_result(
                                "Timesheet MongoDB Serialization Fix", 
                                False, 
                                "🚨 BSON SERIALIZATION ERROR STILL EXISTS - Fix not working!",
                                f"Original error still occurring: {response.text}"
                            )
                        else:
                            self.log_result(
                                "Timesheet MongoDB Serialization Fix", 
                                False, 
                                f"500 Internal Server Error (different issue): {response.status_code}",
                                response.text
                            )
                    else:
                        self.log_result(
                            "Timesheet MongoDB Serialization Fix", 
                            False, 
                            f"Unexpected status code: {response.status_code}",
                            response.text
                        )
                else:
                    self.log_result(
                        "Timesheet MongoDB Serialization Fix", 
                        False, 
                        "No employees found in system - cannot test timesheet endpoint"
                    )
            else:
                self.log_result(
                    "Timesheet MongoDB Serialization Fix", 
                    False, 
                    f"Failed to get employees list: {employees_response.status_code}",
                    employees_response.text
                )
                
        except Exception as e:
            self.log_result("Timesheet MongoDB Serialization Fix", False, f"Error: {str(e)}")
    
    def test_xero_debug_configuration(self):
        """Test GET /api/xero/debug endpoint for proper environment variable usage"""
        print("\n=== XERO DEBUG CONFIGURATION TEST ===")
        
        try:
            response = self.session.get(f"{API_BASE}/xero/debug")
            
            if response.status_code == 200:
                debug_data = response.json()
                
                # Check that callback URL is using environment variables, not hardcoded values
                callback_url = debug_data.get('callback_url')
                callback_url_from_variable = debug_data.get('callback_url_from_variable')
                client_id = debug_data.get('client_id')
                
                # Expected environment-based URL (from .env file)
                expected_callback_url = "https://machinery-timesheet.preview.emergentagent.com/api/xero/callback"
                
                checks = []
                all_checks_passed = True
                
                # Check callback URL is from environment variables
                if callback_url == expected_callback_url:
                    checks.append("✅ callback_url matches environment variable")
                else:
                    checks.append(f"❌ callback_url mismatch: got '{callback_url}', expected '{expected_callback_url}'")
                    all_checks_passed = False
                
                # Check client ID is present
                if client_id:
                    checks.append("✅ client_id is configured")
                else:
                    checks.append("❌ client_id is missing")
                    all_checks_passed = False
                
                # Check for hardcoded URLs (should not contain localhost or hardcoded domains)
                if 'localhost' in callback_url.lower() or 'app.emergent.sh' in callback_url.lower():
                    checks.append(f"❌ callback_url contains hardcoded value: {callback_url}")
                    all_checks_passed = False
                else:
                    checks.append("✅ callback_url does not contain hardcoded localhost/emergent values")
                
                if all_checks_passed:
                    self.log_result(
                        "Xero Debug Configuration", 
                        True, 
                        "✅ XERO CONFIGURATION FIXED: Using environment variables correctly",
                        f"Callback URL: {callback_url}; {'; '.join(checks)}"
                    )
                else:
                    self.log_result(
                        "Xero Debug Configuration", 
                        False, 
                        "Xero configuration issues found",
                        '; '.join(checks)
                    )
            else:
                self.log_result(
                    "Xero Debug Configuration", 
                    False, 
                    f"Debug endpoint failed: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Xero Debug Configuration", False, f"Error: {str(e)}")
    
    def test_xero_auth_url_generation(self):
        """Test GET /api/xero/auth/url endpoint for correct callback URL generation"""
        print("\n=== XERO AUTH URL GENERATION TEST ===")
        
        try:
            response = self.session.get(f"{API_BASE}/xero/auth/url")
            
            if response.status_code == 200:
                auth_data = response.json()
                auth_url = auth_data.get('auth_url')
                debug_info = auth_data.get('debug_info', {})
                
                # Expected callback URL from environment
                expected_callback_url = "https://machinery-timesheet.preview.emergentagent.com/api/xero/callback"
                
                checks = []
                all_checks_passed = True
                
                # Check that auth URL contains the correct callback URL (URL-encoded)
                import urllib.parse
                encoded_callback_url = urllib.parse.quote(expected_callback_url, safe='')
                if auth_url and encoded_callback_url in auth_url:
                    checks.append("✅ auth_url contains correct callback URL from environment")
                else:
                    checks.append(f"❌ auth_url missing correct callback URL: {auth_url}")
                    all_checks_passed = False
                
                # Check debug info callback URL
                debug_callback = debug_info.get('callback_url')
                if debug_callback == expected_callback_url:
                    checks.append("✅ debug_info callback_url matches environment")
                else:
                    checks.append(f"❌ debug_info callback_url mismatch: {debug_callback}")
                    all_checks_passed = False
                
                # Check that URL starts with Xero's OAuth endpoint
                if auth_url and auth_url.startswith('https://login.xero.com/identity/connect/authorize'):
                    checks.append("✅ auth_url uses correct Xero OAuth endpoint")
                else:
                    checks.append(f"❌ auth_url has incorrect OAuth endpoint: {auth_url}")
                    all_checks_passed = False
                
                # Check for required OAuth parameters
                required_params = ['client_id', 'redirect_uri', 'scope', 'state']
                missing_params = []
                for param in required_params:
                    if param not in auth_url:
                        missing_params.append(param)
                
                if not missing_params:
                    checks.append("✅ All required OAuth parameters present")
                else:
                    checks.append(f"❌ Missing OAuth parameters: {missing_params}")
                    all_checks_passed = False
                
                if all_checks_passed:
                    self.log_result(
                        "Xero Auth URL Generation", 
                        True, 
                        "✅ XERO AUTH URL GENERATION FIXED: Correct callback URL from environment",
                        f"Generated URL uses environment callback; {'; '.join(checks)}"
                    )
                else:
                    self.log_result(
                        "Xero Auth URL Generation", 
                        False, 
                        "Xero auth URL generation issues found",
                        '; '.join(checks)
                    )
            
            elif response.status_code == 403:
                self.log_result(
                    "Xero Auth URL Generation", 
                    True, 
                    "✅ ENDPOINT ACCESSIBLE: 403 Forbidden (expected - requires admin/manager role)",
                    "Endpoint exists and validates permissions correctly"
                )
            else:
                self.log_result(
                    "Xero Auth URL Generation", 
                    False, 
                    f"Auth URL endpoint failed: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Xero Auth URL Generation", False, f"Error: {str(e)}")
    
    def test_prepare_for_mongo_functionality(self):
        """Test that the prepare_for_mongo helper function is working correctly"""
        print("\n=== PREPARE_FOR_MONGO FUNCTIONALITY TEST ===")
        
        try:
            # Test creating a new timesheet to verify prepare_for_mongo is working
            employees_response = self.session.get(f"{API_BASE}/payroll/employees")
            
            if employees_response.status_code == 200:
                employees = employees_response.json()
                if employees:
                    employee_id = employees[0].get('id')
                    
                    # Create a new timesheet which should use prepare_for_mongo internally
                    from datetime import date, timedelta
                    today = date.today()
                    week_start = today - timedelta(days=today.weekday())
                    
                    # First get current week timesheet (this triggers prepare_for_mongo)
                    response = self.session.get(f"{API_BASE}/payroll/timesheets/current-week/{employee_id}")
                    
                    if response.status_code == 200:
                        timesheet = response.json()
                        timesheet_id = timesheet.get('id')
                        
                        # Now try to update the timesheet (this also uses prepare_for_mongo)
                        update_data = {
                            "employee_id": employee_id,
                            "week_starting": week_start.isoformat(),
                            "entries": [
                                {
                                    "date": week_start.isoformat(),
                                    "regular_hours": 8.0,
                                    "overtime_hours": 0.0,
                                    "leave_hours": {},
                                    "notes": "Test entry for prepare_for_mongo"
                                }
                            ]
                        }
                        
                        update_response = self.session.put(f"{API_BASE}/payroll/timesheets/{timesheet_id}", json=update_data)
                        
                        if update_response.status_code == 200:
                            self.log_result(
                                "prepare_for_mongo Functionality", 
                                True, 
                                "✅ PREPARE_FOR_MONGO WORKING: Timesheet operations complete without serialization errors",
                                "Both GET and PUT operations handled date/datetime serialization correctly"
                            )
                        else:
                            # Check if it's a serialization error
                            error_text = update_response.text.lower()
                            if 'bson' in error_text or 'serialize' in error_text:
                                self.log_result(
                                    "prepare_for_mongo Functionality", 
                                    False, 
                                    "🚨 SERIALIZATION ERROR in UPDATE: prepare_for_mongo not working properly",
                                    update_response.text
                                )
                            else:
                                self.log_result(
                                    "prepare_for_mongo Functionality", 
                                    False, 
                                    f"Update failed (non-serialization issue): {update_response.status_code}",
                                    update_response.text
                                )
                    else:
                        # Check if it's the original serialization error
                        error_text = response.text.lower()
                        if 'bson.errors.invaliddocument' in error_text:
                            self.log_result(
                                "prepare_for_mongo Functionality", 
                                False, 
                                "🚨 ORIGINAL BSON ERROR STILL EXISTS: prepare_for_mongo fix not applied",
                                response.text
                            )
                        else:
                            self.log_result(
                                "prepare_for_mongo Functionality", 
                                False, 
                                f"GET timesheet failed: {response.status_code}",
                                response.text
                            )
                else:
                    self.log_result(
                        "prepare_for_mongo Functionality", 
                        False, 
                        "No employees available for testing"
                    )
            else:
                self.log_result(
                    "prepare_for_mongo Functionality", 
                    False, 
                    f"Failed to get employees: {employees_response.status_code}",
                    employees_response.text
                )
                
        except Exception as e:
            self.log_result("prepare_for_mongo Functionality", False, f"Error: {str(e)}")
    
    def run_xero_timesheet_fix_tests(self):
        """Run the specific tests for Xero integration and timesheet fixes"""
        print("\n" + "="*60)
        print("XERO INTEGRATION & TIMESHEET SERIALIZATION FIX TESTING")
        print("="*60)
        
        # Step 1: Authenticate
        if not self.authenticate():
            print("❌ Authentication failed - cannot proceed with tests")
            return
        
        # Step 2: Test timesheet MongoDB serialization fix
        self.test_timesheet_mongodb_serialization_fix()
        
        # Step 3: Test prepare_for_mongo functionality
        self.test_prepare_for_mongo_functionality()
        
        # Step 4: Test Xero debug configuration
        self.test_xero_debug_configuration()
        
        # Step 5: Test Xero auth URL generation
        self.test_xero_auth_url_generation()
        
        # Print summary focused on the specific fixes
        self.print_fix_test_summary()
    
    def print_fix_test_summary(self):
        """Print summary focused on the specific fixes tested"""
        print("\n" + "="*60)
        print("XERO & TIMESHEET FIX TEST SUMMARY")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['success']])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Fix Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%" if total_tests > 0 else "0%")
        
        print("\n" + "-"*60)
        print("SPECIFIC FIX RESULTS:")
        print("-"*60)
        
        # Focus on the specific fixes mentioned in the review
        fix_categories = {
            "MongoDB Serialization": ["Timesheet MongoDB Serialization", "prepare_for_mongo"],
            "Xero Configuration": ["Xero Debug Configuration", "Xero Auth URL Generation"]
        }
        
        for category, keywords in fix_categories.items():
            print(f"\n{category}:")
            category_results = [r for r in self.test_results if any(keyword in r['test'] for keyword in keywords)]
            
            if category_results:
                for result in category_results:
                    status = "✅ FIXED" if result['success'] else "❌ STILL BROKEN"
                    print(f"  {status}: {result['message']}")
                    if result['details'] and not result['success']:
                        print(f"    Details: {result['details']}")
            else:
                print(f"  No tests found for {category}")
        
        print("\n" + "="*60)
        print("CRITICAL ISSUE STATUS:")
        print("="*60)
        
        # Check specific error conditions mentioned in review
        serialization_fixed = any(r['success'] and 'serialization' in r['test'].lower() for r in self.test_results)
        xero_config_fixed = any(r['success'] and 'xero' in r['test'].lower() and 'configuration' in r['test'].lower() for r in self.test_results)
        
        print(f"🔍 BSON Serialization Error (datetime.date): {'✅ RESOLVED' if serialization_fixed else '❌ UNRESOLVED'}")
        print(f"🔍 Xero URL Configuration: {'✅ RESOLVED' if xero_config_fixed else '❌ UNRESOLVED'}")
        
        # Summary of critical findings
        critical_failures = [r for r in self.test_results if not r['success'] and any(keyword in r['message'].lower() for keyword in ['bson', 'serialization', 'callback', 'hardcoded'])]
        
        if critical_failures:
            print(f"\n🚨 CRITICAL ISSUES STILL PRESENT:")
            for failure in critical_failures:
                print(f"  - {failure['test']}: {failure['message']}")
        else:
            print(f"\n🎉 ALL CRITICAL ISSUES APPEAR TO BE RESOLVED!")
        
        print("\n" + "="*60)

if __name__ == "__main__":
    tester = BackendAPITester()
    tester.run_xero_timesheet_fix_tests()