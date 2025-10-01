#!/usr/bin/env python3
"""
Product Specifications API Validation Testing Suite
Tests the Product Specifications endpoints to identify validation errors that cause React child errors
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

class ProductSpecsAPITester:
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
    
    def test_product_specifications_validation_errors(self):
        """Test Product Specifications API endpoints for validation errors that cause React child errors"""
        print("\n=== PRODUCT SPECIFICATIONS VALIDATION ERRORS TEST ===")
        
        # Test 1: POST with valid complete data
        valid_spec_data = {
            "product_name": "Test Paper Core - Complete",
            "product_type": "Spiral Paper Core",
            "specifications": {
                "internal_diameter": 76.0,
                "wall_thickness_required": 3.0,
                "core_length": 1000.0
            },
            "materials_composition": [
                {
                    "material_name": "Premium Kraft Paper",
                    "percentage": 100.0,
                    "gsm": 180
                }
            ],
            "material_layers": [
                {
                    "material_id": "test-material-1",
                    "material_name": "Kraft Paper Layer",
                    "layer_type": "Outer Most Layer",
                    "thickness": 0.18,
                    "quantity": 1.0
                }
            ],
            "manufacturing_notes": "Standard production process",
            "selected_thickness": 3.0
        }
        
        try:
            response = self.session.post(f"{API_BASE}/product-specifications", json=valid_spec_data)
            
            if response.status_code == 200:
                result = response.json()
                spec_id = result.get('data', {}).get('id')
                self.log_result(
                    "POST Valid Complete Data", 
                    True, 
                    "Successfully created product specification with complete valid data",
                    f"Spec ID: {spec_id}"
                )
                return spec_id
            else:
                self.log_result(
                    "POST Valid Complete Data", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("POST Valid Complete Data", False, f"Error: {str(e)}")
        
        # Test 2: POST with missing required fields
        missing_fields_data = {
            "product_type": "Spiral Paper Core",
            "specifications": {},
            # Missing product_name (required field)
        }
        
        try:
            response = self.session.post(f"{API_BASE}/product-specifications", json=missing_fields_data)
            
            if response.status_code == 422:
                error_data = response.json()
                # Check if this returns the FastAPI validation error format
                if 'detail' in error_data and isinstance(error_data['detail'], list):
                    error_detail = error_data['detail'][0] if error_data['detail'] else {}
                    has_fastapi_format = all(key in error_detail for key in ['type', 'loc', 'msg'])
                    
                    self.log_result(
                        "POST Missing Required Fields", 
                        True, 
                        f"Correctly returned 422 validation error for missing product_name",
                        f"FastAPI format detected: {has_fastapi_format}, Error: {error_detail}"
                    )
                else:
                    self.log_result(
                        "POST Missing Required Fields", 
                        False, 
                        "422 error but unexpected format",
                        str(error_data)
                    )
            else:
                self.log_result(
                    "POST Missing Required Fields", 
                    False, 
                    f"Expected 422 but got {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("POST Missing Required Fields", False, f"Error: {str(e)}")
        
        # Test 3: POST with invalid field types
        invalid_types_data = {
            "product_name": "Test Invalid Types",
            "product_type": "Spiral Paper Core",
            "specifications": "invalid_dict_should_be_object",  # Should be dict/object
            "material_layers": "invalid_array_should_be_list",  # Should be list
            "selected_thickness": "invalid_float_should_be_number"  # Should be float
        }
        
        try:
            response = self.session.post(f"{API_BASE}/product-specifications", json=invalid_types_data)
            
            if response.status_code == 422:
                error_data = response.json()
                if 'detail' in error_data and isinstance(error_data['detail'], list):
                    validation_errors = error_data['detail']
                    fastapi_errors = []
                    
                    for error in validation_errors:
                        if all(key in error for key in ['type', 'loc', 'msg', 'input']):
                            fastapi_errors.append({
                                'field': error['loc'][-1] if error['loc'] else 'unknown',
                                'type': error['type'],
                                'message': error['msg']
                            })
                    
                    self.log_result(
                        "POST Invalid Field Types", 
                        True, 
                        f"Correctly returned 422 with {len(fastapi_errors)} FastAPI validation errors",
                        f"Errors: {fastapi_errors}"
                    )
                else:
                    self.log_result(
                        "POST Invalid Field Types", 
                        False, 
                        "422 error but unexpected format",
                        str(error_data)
                    )
            else:
                self.log_result(
                    "POST Invalid Field Types", 
                    False, 
                    f"Expected 422 but got {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("POST Invalid Field Types", False, f"Error: {str(e)}")
        
        # Test 4: POST with empty/null values in required fields
        empty_values_data = {
            "product_name": "",  # Empty string
            "product_type": None,  # Null value
            "specifications": {},
            "material_layers": []
        }
        
        try:
            response = self.session.post(f"{API_BASE}/product-specifications", json=empty_values_data)
            
            if response.status_code == 422:
                error_data = response.json()
                if 'detail' in error_data:
                    self.log_result(
                        "POST Empty/Null Required Fields", 
                        True, 
                        "Correctly returned 422 for empty/null required fields",
                        f"Error details: {error_data['detail']}"
                    )
                else:
                    self.log_result(
                        "POST Empty/Null Required Fields", 
                        False, 
                        "422 error but missing detail field",
                        str(error_data)
                    )
            else:
                self.log_result(
                    "POST Empty/Null Required Fields", 
                    False, 
                    f"Expected 422 but got {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("POST Empty/Null Required Fields", False, f"Error: {str(e)}")
        
        # Test 5: POST with invalid material_layers structure
        invalid_layers_data = {
            "product_name": "Test Invalid Layers",
            "product_type": "Spiral Paper Core",
            "specifications": {"test": "value"},
            "material_layers": [
                {
                    "material_id": 123,  # Should be string
                    "material_name": None,  # Should be string
                    "layer_type": "Invalid Layer Type",  # Should be valid enum
                    "thickness": "not_a_number",  # Should be float
                    "quantity": []  # Should be float or None
                }
            ]
        }
        
        try:
            response = self.session.post(f"{API_BASE}/product-specifications", json=invalid_layers_data)
            
            if response.status_code == 422:
                error_data = response.json()
                if 'detail' in error_data and isinstance(error_data['detail'], list):
                    layer_errors = [err for err in error_data['detail'] if 'material_layers' in str(err.get('loc', []))]
                    
                    self.log_result(
                        "POST Invalid Material Layers", 
                        True, 
                        f"Correctly returned 422 with {len(layer_errors)} material layer validation errors",
                        f"Layer errors: {layer_errors}"
                    )
                else:
                    self.log_result(
                        "POST Invalid Material Layers", 
                        False, 
                        "422 error but unexpected format",
                        str(error_data)
                    )
            else:
                self.log_result(
                    "POST Invalid Material Layers", 
                    False, 
                    f"Expected 422 but got {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("POST Invalid Material Layers", False, f"Error: {str(e)}")
        
        return None
    
    def test_product_specifications_put_validation(self):
        """Test PUT endpoint validation errors"""
        print("\n=== PRODUCT SPECIFICATIONS PUT VALIDATION TEST ===")
        
        # First create a valid specification to update
        valid_spec_data = {
            "product_name": "Test Spec for Update",
            "product_type": "Paper Core",
            "specifications": {"diameter": 50.0},
            "material_layers": []
        }
        
        spec_id = None
        try:
            response = self.session.post(f"{API_BASE}/product-specifications", json=valid_spec_data)
            if response.status_code == 200:
                result = response.json()
                spec_id = result.get('data', {}).get('id')
        except Exception as e:
            self.log_result("PUT Setup - Create Spec", False, f"Failed to create spec for PUT testing: {str(e)}")
            return
        
        if not spec_id:
            self.log_result("PUT Setup - Create Spec", False, "Failed to get spec ID for PUT testing")
            return
        
        # Test 1: PUT with valid data
        valid_update_data = {
            "product_name": "Updated Test Spec",
            "product_type": "Spiral Paper Core",
            "specifications": {"diameter": 76.0, "length": 1000.0},
            "material_layers": [
                {
                    "material_id": "test-material-update",
                    "material_name": "Updated Material",
                    "layer_type": "Central Layer",
                    "thickness": 0.25,
                    "quantity": 2.0
                }
            ]
        }
        
        try:
            response = self.session.put(f"{API_BASE}/product-specifications/{spec_id}", json=valid_update_data)
            
            if response.status_code == 200:
                self.log_result(
                    "PUT Valid Update Data", 
                    True, 
                    "Successfully updated product specification with valid data"
                )
            else:
                self.log_result(
                    "PUT Valid Update Data", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("PUT Valid Update Data", False, f"Error: {str(e)}")
        
        # Test 2: PUT with missing required fields
        missing_fields_update = {
            "product_type": "Paper Core",
            # Missing product_name
        }
        
        try:
            response = self.session.put(f"{API_BASE}/product-specifications/{spec_id}", json=missing_fields_update)
            
            if response.status_code == 422:
                error_data = response.json()
                if 'detail' in error_data and isinstance(error_data['detail'], list):
                    fastapi_errors = [err for err in error_data['detail'] if all(key in err for key in ['type', 'loc', 'msg'])]
                    
                    self.log_result(
                        "PUT Missing Required Fields", 
                        True, 
                        f"Correctly returned 422 with {len(fastapi_errors)} FastAPI validation errors",
                        f"Errors: {fastapi_errors}"
                    )
                else:
                    self.log_result(
                        "PUT Missing Required Fields", 
                        False, 
                        "422 error but unexpected format",
                        str(error_data)
                    )
            else:
                self.log_result(
                    "PUT Missing Required Fields", 
                    False, 
                    f"Expected 422 but got {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("PUT Missing Required Fields", False, f"Error: {str(e)}")
        
        # Test 3: PUT with invalid field types
        invalid_types_update = {
            "product_name": 12345,  # Should be string
            "product_type": ["invalid", "array"],  # Should be string
            "specifications": "not_an_object",  # Should be dict
            "selected_thickness": {"invalid": "object"}  # Should be float
        }
        
        try:
            response = self.session.put(f"{API_BASE}/product-specifications/{spec_id}", json=invalid_types_update)
            
            if response.status_code == 422:
                error_data = response.json()
                if 'detail' in error_data and isinstance(error_data['detail'], list):
                    type_errors = []
                    for error in error_data['detail']:
                        if 'type' in error and 'loc' in error and 'msg' in error:
                            type_errors.append({
                                'field': error['loc'][-1] if error['loc'] else 'unknown',
                                'expected_type': error['type'],
                                'message': error['msg']
                            })
                    
                    self.log_result(
                        "PUT Invalid Field Types", 
                        True, 
                        f"Correctly returned 422 with {len(type_errors)} type validation errors",
                        f"Type errors: {type_errors}"
                    )
                else:
                    self.log_result(
                        "PUT Invalid Field Types", 
                        False, 
                        "422 error but unexpected format",
                        str(error_data)
                    )
            else:
                self.log_result(
                    "PUT Invalid Field Types", 
                    False, 
                    f"Expected 422 but got {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("PUT Invalid Field Types", False, f"Error: {str(e)}")
        
        # Test 4: PUT with non-existent ID
        fake_id = "non-existent-spec-id-12345"
        
        try:
            response = self.session.put(f"{API_BASE}/product-specifications/{fake_id}", json=valid_update_data)
            
            if response.status_code == 404:
                self.log_result(
                    "PUT Non-existent ID", 
                    True, 
                    "Correctly returned 404 for non-existent specification ID"
                )
            else:
                self.log_result(
                    "PUT Non-existent ID", 
                    False, 
                    f"Expected 404 but got {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("PUT Non-existent ID", False, f"Error: {str(e)}")
    
    def test_fastapi_error_format_analysis(self):
        """Analyze the exact format of FastAPI validation errors"""
        print("\n=== FASTAPI ERROR FORMAT ANALYSIS ===")
        
        # Create a request that will definitely trigger multiple validation errors
        problematic_data = {
            "product_name": None,  # Required field as null
            "product_type": 123,   # Wrong type
            "specifications": "not_a_dict",  # Wrong type
            "material_layers": [
                {
                    "material_id": None,  # Required field as null
                    "material_name": 456,  # Wrong type
                    "layer_type": "Invalid Type",  # Invalid enum value
                    "thickness": "not_a_number",  # Wrong type
                    "quantity": {"invalid": "object"}  # Wrong type
                }
            ],
            "selected_thickness": ["not", "a", "number"],  # Wrong type
            "manufacturing_notes": 789  # Wrong type
        }
        
        try:
            response = self.session.post(f"{API_BASE}/product-specifications", json=problematic_data)
            
            if response.status_code == 422:
                error_data = response.json()
                
                # Analyze the error structure
                analysis = {
                    "status_code": response.status_code,
                    "has_detail_field": 'detail' in error_data,
                    "detail_is_list": isinstance(error_data.get('detail'), list),
                    "total_errors": len(error_data.get('detail', [])) if isinstance(error_data.get('detail'), list) else 0,
                    "error_structure_sample": None,
                    "contains_fastapi_keys": False
                }
                
                if analysis["detail_is_list"] and analysis["total_errors"] > 0:
                    first_error = error_data['detail'][0]
                    analysis["error_structure_sample"] = first_error
                    
                    # Check for FastAPI validation error keys
                    fastapi_keys = ['type', 'loc', 'msg', 'input']
                    analysis["contains_fastapi_keys"] = all(key in first_error for key in fastapi_keys)
                    analysis["fastapi_keys_present"] = [key for key in fastapi_keys if key in first_error]
                    
                    # Check if 'url' key is present (mentioned in the React error)
                    analysis["has_url_key"] = 'url' in first_error
                
                # This is the exact error format that causes React child errors
                if analysis["contains_fastapi_keys"]:
                    self.log_result(
                        "FastAPI Error Format Analysis", 
                        True, 
                        f"🚨 IDENTIFIED REACT CHILD ERROR SOURCE: FastAPI returns validation errors with {analysis['fastapi_keys_present']} keys",
                        f"Full analysis: {analysis}"
                    )
                    
                    # Show sample errors that would cause React issues
                    sample_errors = error_data['detail'][:3]  # First 3 errors
                    print(f"   🔍 SAMPLE ERRORS CAUSING REACT ISSUES:")
                    for i, error in enumerate(sample_errors, 1):
                        print(f"   Error {i}: {error}")
                        
                    # Show the exact object structure that React can't render
                    print(f"\n   🚨 REACT ERROR CAUSE: When frontend tries to render these error objects directly in JSX:")
                    print(f"   - Objects with keys: {list(first_error.keys())}")
                    print(f"   - React sees: 'Objects are not valid as a React child (found: object with keys {{type, loc, msg, input, url}})'")
                    
                else:
                    self.log_result(
                        "FastAPI Error Format Analysis", 
                        False, 
                        "Unexpected error format - not standard FastAPI validation",
                        f"Analysis: {analysis}"
                    )
            else:
                self.log_result(
                    "FastAPI Error Format Analysis", 
                    False, 
                    f"Expected 422 validation error but got {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("FastAPI Error Format Analysis", False, f"Error: {str(e)}")

    def run_all_tests(self):
        """Run all tests in sequence"""
        print("🚀 Starting Product Specifications Validation Error Testing")
        print(f"Backend URL: {API_BASE}")
        print("=" * 80)
        
        # Authenticate first
        if not self.authenticate():
            print("❌ Authentication failed - cannot proceed with tests")
            return
        
        # Run Product Specifications validation tests
        self.test_product_specifications_validation_errors()
        self.test_product_specifications_put_validation()
        self.test_fastapi_error_format_analysis()
        
        # Print summary
        self.print_test_summary()
    
    def print_test_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("📊 PRODUCT SPECIFICATIONS VALIDATION TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for result in self.test_results if result['success'])
        failed = len(self.test_results) - passed
        
        print(f"Total Tests: {len(self.test_results)}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"Success Rate: {(passed/len(self.test_results)*100):.1f}%" if self.test_results else "0%")
        
        if failed > 0:
            print(f"\n🚨 FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   - {result['test']}: {result['message']}")
        
        # Highlight key findings
        print(f"\n🔍 KEY FINDINGS:")
        fastapi_errors_found = any("REACT CHILD ERROR SOURCE" in result['message'] for result in self.test_results)
        if fastapi_errors_found:
            print(f"   ✅ Successfully identified FastAPI validation error format causing React child errors")
            print(f"   📋 Solution: Frontend needs to extract error messages from FastAPI validation objects")
            print(f"   💡 Instead of rendering error objects directly, extract 'msg' field from each error")
        else:
            print(f"   ❓ FastAPI error format analysis inconclusive")

if __name__ == "__main__":
    tester = ProductSpecsAPITester()
    tester.run_all_tests()