#!/usr/bin/env python3
"""
Machinery Rates Endpoints Testing Suite
Tests the newly implemented machinery rates CRUD operations, validation, and error handling
"""

import requests
import json
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:8001')
API_BASE = f"{BACKEND_URL}/api"

class MachineryRatesTester:
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
    
    def test_machinery_rates_get_all(self):
        """Test GET /api/machinery-rates (get all rates)"""
        print("\n=== MACHINERY RATES GET ALL TEST ===")
        
        try:
            response = self.session.get(f"{API_BASE}/machinery-rates")
            
            if response.status_code == 200:
                rates = response.json()
                
                if isinstance(rates, list):
                    self.log_result(
                        "Machinery Rates GET All", 
                        True, 
                        f"Successfully retrieved {len(rates)} machinery rates",
                        f"Rates found: {len(rates)}"
                    )
                    return rates
                else:
                    self.log_result(
                        "Machinery Rates GET All", 
                        False, 
                        "Response is not a list",
                        f"Response type: {type(rates)}"
                    )
            else:
                self.log_result(
                    "Machinery Rates GET All", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Machinery Rates GET All", False, f"Error: {str(e)}")
        
        return []
    
    def test_machinery_rates_create(self, function_name, rate_per_hour, description=None):
        """Test POST /api/machinery-rates (create new rate)"""
        print(f"\n=== MACHINERY RATES CREATE TEST ({function_name}) ===")
        
        try:
            rate_data = {
                "function": function_name,
                "rate_per_hour": rate_per_hour
            }
            
            if description:
                rate_data["description"] = description
            
            response = self.session.post(f"{API_BASE}/machinery-rates", json=rate_data)
            
            if response.status_code == 200:
                result = response.json()
                rate_id = result.get('data', {}).get('id')
                
                if rate_id:
                    self.log_result(
                        f"Machinery Rates CREATE ({function_name})", 
                        True, 
                        f"Successfully created rate for {function_name} at ${rate_per_hour}/hour",
                        f"Rate ID: {rate_id}"
                    )
                    return rate_id
                else:
                    self.log_result(
                        f"Machinery Rates CREATE ({function_name})", 
                        False, 
                        "Response missing rate ID",
                        str(result)
                    )
            else:
                self.log_result(
                    f"Machinery Rates CREATE ({function_name})", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result(f"Machinery Rates CREATE ({function_name})", False, f"Error: {str(e)}")
        
        return None
    
    def test_machinery_rates_get_by_id(self, rate_id, expected_function):
        """Test GET /api/machinery-rates/{id} (get specific rate)"""
        print(f"\n=== MACHINERY RATES GET BY ID TEST ({expected_function}) ===")
        
        if not rate_id:
            self.log_result(
                f"Machinery Rates GET By ID ({expected_function})", 
                False, 
                "No rate ID available for test"
            )
            return None
        
        try:
            response = self.session.get(f"{API_BASE}/machinery-rates/{rate_id}")
            
            if response.status_code == 200:
                rate = response.json()
                
                # Verify rate structure
                required_fields = ['id', 'function', 'rate_per_hour', 'is_active', 'created_at']
                missing_fields = [field for field in required_fields if field not in rate]
                
                if not missing_fields:
                    if rate.get('function') == expected_function:
                        self.log_result(
                            f"Machinery Rates GET By ID ({expected_function})", 
                            True, 
                            f"Successfully retrieved rate for {expected_function}",
                            f"Rate: ${rate.get('rate_per_hour')}/hour, Active: {rate.get('is_active')}"
                        )
                        return rate
                    else:
                        self.log_result(
                            f"Machinery Rates GET By ID ({expected_function})", 
                            False, 
                            f"Function mismatch: expected {expected_function}, got {rate.get('function')}"
                        )
                else:
                    self.log_result(
                        f"Machinery Rates GET By ID ({expected_function})", 
                        False, 
                        f"Missing required fields: {missing_fields}"
                    )
            elif response.status_code == 404:
                self.log_result(
                    f"Machinery Rates GET By ID ({expected_function})", 
                    False, 
                    "Rate not found (404)",
                    f"Rate ID: {rate_id}"
                )
            else:
                self.log_result(
                    f"Machinery Rates GET By ID ({expected_function})", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result(f"Machinery Rates GET By ID ({expected_function})", False, f"Error: {str(e)}")
        
        return None
    
    def test_machinery_rates_update(self, rate_id, function_name, new_rate):
        """Test PUT /api/machinery-rates/{id} (update rate)"""
        print(f"\n=== MACHINERY RATES UPDATE TEST ({function_name}) ===")
        
        if not rate_id:
            self.log_result(
                f"Machinery Rates UPDATE ({function_name})", 
                False, 
                "No rate ID available for update test"
            )
            return False
        
        try:
            update_data = {
                "rate_per_hour": new_rate,
                "description": f"Updated rate for {function_name} function"
            }
            
            response = self.session.put(f"{API_BASE}/machinery-rates/{rate_id}", json=update_data)
            
            if response.status_code == 200:
                # Verify the update by retrieving the rate
                get_response = self.session.get(f"{API_BASE}/machinery-rates/{rate_id}")
                
                if get_response.status_code == 200:
                    updated_rate = get_response.json()
                    
                    if updated_rate.get('rate_per_hour') == new_rate:
                        self.log_result(
                            f"Machinery Rates UPDATE ({function_name})", 
                            True, 
                            f"Successfully updated rate to ${new_rate}/hour",
                            f"Description: {updated_rate.get('description')}"
                        )
                        return True
                    else:
                        self.log_result(
                            f"Machinery Rates UPDATE ({function_name})", 
                            False, 
                            f"Rate not updated correctly: expected ${new_rate}, got ${updated_rate.get('rate_per_hour')}"
                        )
                else:
                    self.log_result(
                        f"Machinery Rates UPDATE ({function_name})", 
                        False, 
                        f"Failed to retrieve updated rate: {get_response.status_code}"
                    )
            else:
                self.log_result(
                    f"Machinery Rates UPDATE ({function_name})", 
                    False, 
                    f"Update failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result(f"Machinery Rates UPDATE ({function_name})", False, f"Error: {str(e)}")
        
        return False
    
    def test_machinery_rates_delete(self, rate_id, function_name):
        """Test DELETE /api/machinery-rates/{id} (delete rate)"""
        print(f"\n=== MACHINERY RATES DELETE TEST ({function_name}) ===")
        
        if not rate_id:
            self.log_result(
                f"Machinery Rates DELETE ({function_name})", 
                False, 
                "No rate ID available for delete test"
            )
            return False
        
        try:
            response = self.session.delete(f"{API_BASE}/machinery-rates/{rate_id}")
            
            if response.status_code == 200:
                # Verify the deletion by trying to retrieve the rate
                get_response = self.session.get(f"{API_BASE}/machinery-rates/{rate_id}")
                
                if get_response.status_code == 404:
                    self.log_result(
                        f"Machinery Rates DELETE ({function_name})", 
                        True, 
                        f"Successfully deleted rate for {function_name}",
                        "Rate no longer accessible (404)"
                    )
                    return True
                elif get_response.status_code == 200:
                    # Check if it's soft deleted
                    rate = get_response.json()
                    if rate.get('is_active') == False:
                        self.log_result(
                            f"Machinery Rates DELETE ({function_name})", 
                            True, 
                            f"Successfully soft deleted rate for {function_name}",
                            "Rate marked as inactive"
                        )
                        return True
                    else:
                        self.log_result(
                            f"Machinery Rates DELETE ({function_name})", 
                            False, 
                            "Rate still active after deletion"
                        )
                else:
                    self.log_result(
                        f"Machinery Rates DELETE ({function_name})", 
                        False, 
                        f"Unexpected response after deletion: {get_response.status_code}"
                    )
            else:
                self.log_result(
                    f"Machinery Rates DELETE ({function_name})", 
                    False, 
                    f"Delete failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result(f"Machinery Rates DELETE ({function_name})", False, f"Error: {str(e)}")
        
        return False
    
    def test_machinery_rates_validation(self):
        """Test data validation for machinery rates"""
        print("\n=== MACHINERY RATES VALIDATION TEST ===")
        
        validation_tests = [
            # Test invalid function name
            {
                "name": "Invalid Function Name",
                "data": {"function": "InvalidFunction", "rate_per_hour": 100.0},
                "expected_status": 422,
                "should_fail": True
            },
            # Test negative rate
            {
                "name": "Negative Rate",
                "data": {"function": "Slitting", "rate_per_hour": -50.0},
                "expected_status": 422,
                "should_fail": True
            },
            # Test zero rate
            {
                "name": "Zero Rate",
                "data": {"function": "Slitting", "rate_per_hour": 0.0},
                "expected_status": 422,
                "should_fail": True
            },
            # Test missing function
            {
                "name": "Missing Function",
                "data": {"rate_per_hour": 100.0},
                "expected_status": 422,
                "should_fail": True
            },
            # Test missing rate
            {
                "name": "Missing Rate",
                "data": {"function": "Slitting"},
                "expected_status": 422,
                "should_fail": True
            }
        ]
        
        passed_validations = 0
        total_validations = len(validation_tests)
        
        for test in validation_tests:
            try:
                response = self.session.post(f"{API_BASE}/machinery-rates", json=test["data"])
                
                if test["should_fail"]:
                    if response.status_code == test["expected_status"]:
                        passed_validations += 1
                        print(f"  ✅ {test['name']}: Correctly rejected with {response.status_code}")
                    else:
                        print(f"  ❌ {test['name']}: Expected {test['expected_status']}, got {response.status_code}")
                else:
                    if response.status_code == 200:
                        passed_validations += 1
                        print(f"  ✅ {test['name']}: Correctly accepted")
                    else:
                        print(f"  ❌ {test['name']}: Expected 200, got {response.status_code}")
                        
            except Exception as e:
                print(f"  ❌ {test['name']}: Error - {str(e)}")
        
        success = passed_validations == total_validations
        self.log_result(
            "Machinery Rates Validation", 
            success, 
            f"Validation tests: {passed_validations}/{total_validations} passed",
            f"All validation scenarios {'passed' if success else 'failed'}"
        )
        
        return success
    
    def test_machinery_rates_duplicate_function(self):
        """Test duplicate function validation"""
        print("\n=== MACHINERY RATES DUPLICATE FUNCTION TEST ===")
        
        try:
            # Create first rate
            rate_data = {
                "function": "Slitting",
                "rate_per_hour": 500.0,
                "description": "First Slitting rate"
            }
            
            first_response = self.session.post(f"{API_BASE}/machinery-rates", json=rate_data)
            
            if first_response.status_code == 200:
                first_rate_id = first_response.json().get('data', {}).get('id')
                
                # Try to create duplicate
                duplicate_data = {
                    "function": "Slitting",
                    "rate_per_hour": 600.0,
                    "description": "Duplicate Slitting rate"
                }
                
                duplicate_response = self.session.post(f"{API_BASE}/machinery-rates", json=duplicate_data)
                
                if duplicate_response.status_code == 400:
                    error_text = duplicate_response.text
                    if "already exists" in error_text.lower():
                        self.log_result(
                            "Machinery Rates Duplicate Function", 
                            True, 
                            "Correctly prevented duplicate function creation",
                            f"Error: {error_text}"
                        )
                        
                        # Clean up - delete the first rate
                        if first_rate_id:
                            self.session.delete(f"{API_BASE}/machinery-rates/{first_rate_id}")
                        
                        return True
                    else:
                        self.log_result(
                            "Machinery Rates Duplicate Function", 
                            False, 
                            "Got 400 status but wrong error message",
                            error_text
                        )
                else:
                    self.log_result(
                        "Machinery Rates Duplicate Function", 
                        False, 
                        f"Expected 400 for duplicate, got {duplicate_response.status_code}",
                        duplicate_response.text
                    )
                
                # Clean up
                if first_rate_id:
                    self.session.delete(f"{API_BASE}/machinery-rates/{first_rate_id}")
                    
            else:
                self.log_result(
                    "Machinery Rates Duplicate Function", 
                    False, 
                    f"Failed to create first rate: {first_response.status_code}",
                    first_response.text
                )
                
        except Exception as e:
            self.log_result("Machinery Rates Duplicate Function", False, f"Error: {str(e)}")
        
        return False
    
    def test_machinery_rates_404_errors(self):
        """Test 404 errors for non-existent rates"""
        print("\n=== MACHINERY RATES 404 ERRORS TEST ===")
        
        fake_id = "non-existent-rate-id-12345"
        
        tests = [
            ("GET", f"{API_BASE}/machinery-rates/{fake_id}"),
            ("PUT", f"{API_BASE}/machinery-rates/{fake_id}"),
            ("DELETE", f"{API_BASE}/machinery-rates/{fake_id}")
        ]
        
        passed_tests = 0
        
        for method, url in tests:
            try:
                if method == "GET":
                    response = self.session.get(url)
                elif method == "PUT":
                    response = self.session.put(url, json={"rate_per_hour": 100.0})
                elif method == "DELETE":
                    response = self.session.delete(url)
                
                if response.status_code == 404:
                    passed_tests += 1
                    print(f"  ✅ {method}: Correctly returned 404 for non-existent rate")
                else:
                    print(f"  ❌ {method}: Expected 404, got {response.status_code}")
                    
            except Exception as e:
                print(f"  ❌ {method}: Error - {str(e)}")
        
        success = passed_tests == len(tests)
        self.log_result(
            "Machinery Rates 404 Errors", 
            success, 
            f"404 error tests: {passed_tests}/{len(tests)} passed",
            "All endpoints correctly handle non-existent rates" if success else "Some endpoints failed 404 handling"
        )
        
        return success
    
    def test_function_field_validation(self):
        """Test that only valid function types are accepted"""
        print("\n=== FUNCTION FIELD VALIDATION TEST ===")
        
        valid_functions = ["Slitting", "winding", "Cutting/Indexing", "splitting", "Packing", "Delivery Time"]
        invalid_functions = ["InvalidFunction", "Printing", "Laminating", "Coating", ""]
        
        # Test valid functions
        valid_passed = 0
        for function in valid_functions:
            try:
                response = self.session.post(f"{API_BASE}/machinery-rates", json={
                    "function": function,
                    "rate_per_hour": 100.0
                })
                
                if response.status_code == 200:
                    valid_passed += 1
                    # Clean up - delete the created rate
                    rate_id = response.json().get('data', {}).get('id')
                    if rate_id:
                        self.session.delete(f"{API_BASE}/machinery-rates/{rate_id}")
                    print(f"  ✅ {function}: Correctly accepted")
                else:
                    print(f"  ❌ {function}: Expected 200, got {response.status_code}")
                    
            except Exception as e:
                print(f"  ❌ {function}: Error - {str(e)}")
        
        # Test invalid functions
        invalid_rejected = 0
        for function in invalid_functions:
            try:
                response = self.session.post(f"{API_BASE}/machinery-rates", json={
                    "function": function,
                    "rate_per_hour": 100.0
                })
                
                if response.status_code in [400, 422]:
                    invalid_rejected += 1
                    print(f"  ✅ {function}: Correctly rejected with {response.status_code}")
                else:
                    print(f"  ❌ {function}: Expected 400/422, got {response.status_code}")
                    
            except Exception as e:
                print(f"  ❌ {function}: Error - {str(e)}")
        
        total_valid = len(valid_functions)
        total_invalid = len(invalid_functions)
        success = (valid_passed == total_valid) and (invalid_rejected == total_invalid)
        
        self.log_result(
            "Function Field Validation", 
            success, 
            f"Valid functions: {valid_passed}/{total_valid} accepted, Invalid functions: {invalid_rejected}/{total_invalid} rejected",
            f"All function validation scenarios {'passed' if success else 'failed'}"
        )
        
        return success
    
    def test_rate_per_hour_validation(self):
        """Test rate_per_hour field validation (must be positive number)"""
        print("\n=== RATE PER HOUR VALIDATION TEST ===")
        
        rate_tests = [
            # Valid rates
            {"rate": 100.0, "should_pass": True, "name": "Valid Rate (100.0)"},
            {"rate": 0.01, "should_pass": True, "name": "Valid Small Rate (0.01)"},
            {"rate": 999999.99, "should_pass": True, "name": "Valid Large Rate (999999.99)"},
            
            # Invalid rates
            {"rate": 0.0, "should_pass": False, "name": "Zero Rate"},
            {"rate": -50.0, "should_pass": False, "name": "Negative Rate"},
            {"rate": -0.01, "should_pass": False, "name": "Small Negative Rate"}
        ]
        
        passed_tests = 0
        total_tests = len(rate_tests)
        
        for test in rate_tests:
            try:
                response = self.session.post(f"{API_BASE}/machinery-rates", json={
                    "function": "Slitting",
                    "rate_per_hour": test["rate"]
                })
                
                if test["should_pass"]:
                    if response.status_code == 200:
                        passed_tests += 1
                        # Clean up - delete the created rate
                        rate_id = response.json().get('data', {}).get('id')
                        if rate_id:
                            self.session.delete(f"{API_BASE}/machinery-rates/{rate_id}")
                        print(f"  ✅ {test['name']}: Correctly accepted")
                    else:
                        print(f"  ❌ {test['name']}: Expected 200, got {response.status_code}")
                else:
                    if response.status_code in [400, 422]:
                        passed_tests += 1
                        print(f"  ✅ {test['name']}: Correctly rejected with {response.status_code}")
                    else:
                        print(f"  ❌ {test['name']}: Expected 400/422, got {response.status_code}")
                        
            except Exception as e:
                print(f"  ❌ {test['name']}: Error - {str(e)}")
        
        success = passed_tests == total_tests
        self.log_result(
            "Rate Per Hour Validation", 
            success, 
            f"Rate validation tests: {passed_tests}/{total_tests} passed",
            f"All rate validation scenarios {'passed' if success else 'failed'}"
        )
        
        return success
    
    def run_comprehensive_tests(self):
        """Run comprehensive machinery rates endpoint tests"""
        print("\n" + "="*80)
        print("MACHINERY RATES ENDPOINTS COMPREHENSIVE TESTING")
        print("="*80)
        
        # Step 1: Authenticate
        if not self.authenticate():
            print("❌ Authentication failed - cannot proceed with tests")
            return
        
        # Test data for all 6 function types with realistic rates
        function_rates = [
            ("Slitting", 500.00, "High-speed slitting operations"),
            ("winding", 300.00, "Paper winding and rolling"),
            ("Cutting/Indexing", 400.00, "Precision cutting and indexing"),
            ("splitting", 350.00, "Material splitting operations"),
            ("Packing", 250.00, "Product packing and preparation"),
            ("Delivery Time", 150.00, "Delivery and logistics time")
        ]
        
        created_rates = {}
        
        # Test 1: Get all rates (initially)
        print("\n" + "-"*60)
        print("STEP 1: INITIAL STATE CHECK")
        print("-"*60)
        initial_rates = self.test_machinery_rates_get_all()
        
        # Test 2: Create rates for all 6 function types
        print("\n" + "-"*60)
        print("STEP 2: CREATE MACHINERY RATES FOR ALL FUNCTION TYPES")
        print("-"*60)
        for function, rate, description in function_rates:
            rate_id = self.test_machinery_rates_create(function, rate, description)
            if rate_id:
                created_rates[function] = rate_id
        
        # Test 3: Get all rates (should now have 6 more)
        print("\n" + "-"*60)
        print("STEP 3: VERIFY ALL RATES CREATED")
        print("-"*60)
        all_rates = self.test_machinery_rates_get_all()
        expected_count = len(initial_rates) + len(function_rates)
        if len(all_rates) >= expected_count:
            print(f"✅ Successfully created {len(created_rates)} new machinery rates")
        else:
            print(f"❌ Expected at least {expected_count} rates, found {len(all_rates)}")
        
        # Test 4: Get specific rates by ID
        print("\n" + "-"*60)
        print("STEP 4: RETRIEVE SPECIFIC RATES BY ID")
        print("-"*60)
        for function, rate_id in created_rates.items():
            self.test_machinery_rates_get_by_id(rate_id, function)
        
        # Test 5: Update rates
        print("\n" + "-"*60)
        print("STEP 5: UPDATE SELECTED RATES")
        print("-"*60)
        update_tests = [
            ("Slitting", 550.00),
            ("Packing", 275.00),
            ("Delivery Time", 175.00)
        ]
        
        for function, new_rate in update_tests:
            if function in created_rates:
                self.test_machinery_rates_update(created_rates[function], function, new_rate)
        
        # Test 6: Data validation tests
        print("\n" + "-"*60)
        print("STEP 6: DATA VALIDATION TESTS")
        print("-"*60)
        self.test_machinery_rates_validation()
        
        # Test 7: Function field validation
        print("\n" + "-"*60)
        print("STEP 7: FUNCTION FIELD VALIDATION")
        print("-"*60)
        self.test_function_field_validation()
        
        # Test 8: Rate per hour validation
        print("\n" + "-"*60)
        print("STEP 8: RATE PER HOUR VALIDATION")
        print("-"*60)
        self.test_rate_per_hour_validation()
        
        # Test 9: Duplicate function validation
        print("\n" + "-"*60)
        print("STEP 9: DUPLICATE FUNCTION VALIDATION")
        print("-"*60)
        self.test_machinery_rates_duplicate_function()
        
        # Test 10: 404 error handling
        print("\n" + "-"*60)
        print("STEP 10: 404 ERROR HANDLING")
        print("-"*60)
        self.test_machinery_rates_404_errors()
        
        # Test 11: Delete rates (clean up)
        print("\n" + "-"*60)
        print("STEP 11: DELETE ALL CREATED RATES (CLEANUP)")
        print("-"*60)
        for function, rate_id in created_rates.items():
            self.test_machinery_rates_delete(rate_id, function)
        
        # Test 12: Verify all rates deleted
        print("\n" + "-"*60)
        print("STEP 12: VERIFY CLEANUP COMPLETED")
        print("-"*60)
        final_rates = self.test_machinery_rates_get_all()
        remaining_count = len(final_rates)
        if remaining_count <= len(initial_rates):
            print(f"✅ Successfully cleaned up rates (remaining: {remaining_count})")
        else:
            print(f"❌ Some rates may not have been deleted (remaining: {remaining_count})")
        
        # Print comprehensive summary
        self.print_test_summary()
    
    def print_test_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "="*80)
        print("MACHINERY RATES TESTING SUMMARY")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['success']])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%" if total_tests > 0 else "0%")
        
        print("\n" + "-"*80)
        print("DETAILED RESULTS:")
        print("-"*80)
        
        # Group results by category
        categories = {
            "CRUD Operations": [],
            "Data Validation": [],
            "Error Handling": [],
            "Authentication": []
        }
        
        for result in self.test_results:
            test_name = result['test']
            if "CREATE" in test_name or "GET" in test_name or "UPDATE" in test_name or "DELETE" in test_name:
                categories["CRUD Operations"].append(result)
            elif "Validation" in test_name:
                categories["Data Validation"].append(result)
            elif "404" in test_name or "Duplicate" in test_name:
                categories["Error Handling"].append(result)
            elif "Authentication" in test_name:
                categories["Authentication"].append(result)
            else:
                # Create a miscellaneous category if needed
                if "Miscellaneous" not in categories:
                    categories["Miscellaneous"] = []
                categories["Miscellaneous"].append(result)
        
        for category, results in categories.items():
            if results:  # Only show categories that have results
                print(f"\n{category}:")
                for result in results:
                    status = "✅ PASS" if result['success'] else "❌ FAIL"
                    print(f"  {status}: {result['message']}")
                    if result['details'] and not result['success']:
                        print(f"    Details: {result['details']}")
        
        print("\n" + "="*80)
        print("TESTING ANALYSIS:")
        print("="*80)
        
        # Analyze specific functionality
        crud_tests = [r for r in self.test_results if any(op in r['test'] for op in ['CREATE', 'GET', 'UPDATE', 'DELETE'])]
        validation_tests = [r for r in self.test_results if 'Validation' in r['test']]
        error_tests = [r for r in self.test_results if any(err in r['test'] for err in ['404', 'Duplicate'])]
        
        crud_passed = len([r for r in crud_tests if r['success']])
        validation_passed = len([r for r in validation_tests if r['success']])
        error_passed = len([r for r in error_tests if r['success']])
        
        print(f"CRUD Operations: {crud_passed}/{len(crud_tests)} passed")
        print(f"Data Validation: {validation_passed}/{len(validation_tests)} passed")
        print(f"Error Handling: {error_passed}/{len(error_tests)} passed")
        
        # Check for critical issues
        critical_failures = []
        for result in self.test_results:
            if not result['success'] and any(critical in result['test'] for critical in ['CREATE', 'GET All', 'Authentication']):
                critical_failures.append(result['test'])
        
        if critical_failures:
            print(f"\n🚨 CRITICAL FAILURES:")
            for failure in critical_failures:
                print(f"  - {failure}")
        else:
            print(f"\n✅ NO CRITICAL FAILURES DETECTED")
        
        # Final assessment
        if passed_tests == total_tests:
            print(f"\n🎉 ALL TESTS PASSED! Machinery rates endpoints are fully functional.")
        elif passed_tests >= total_tests * 0.8:  # 80% pass rate
            print(f"\n✅ MOSTLY SUCCESSFUL: {passed_tests}/{total_tests} tests passed. Minor issues may need attention.")
        else:
            print(f"\n⚠️  SIGNIFICANT ISSUES: Only {passed_tests}/{total_tests} tests passed. Major fixes needed.")
        
        print("\n" + "="*80)

def main():
    """Main test execution"""
    print("Starting Machinery Rates Endpoints Testing...")
    print(f"Backend URL: {BACKEND_URL}")
    
    tester = MachineryRatesTester()
    
    # Run the complete machinery rates test suite
    tester.run_comprehensive_tests()

if __name__ == "__main__":
    main()