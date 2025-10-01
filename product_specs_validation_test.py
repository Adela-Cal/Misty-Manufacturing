#!/usr/bin/env python3
"""
Product Specifications UPDATE Validation Testing
Tests the PUT /api/product-specifications/{id} endpoint to identify specific validation errors
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

class ProductSpecsValidationTester:
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
    
    def test_product_specifications_update_validation(self):
        """Test PUT /api/product-specifications/{id} endpoint validation errors"""
        print("\n=== PRODUCT SPECIFICATIONS UPDATE VALIDATION TEST ===")
        
        # First, create a product specification to update
        test_spec_data = {
            "product_name": "Test Product for Update Validation",
            "product_type": "Spiral Paper Core",
            "specifications": {
                "internal_diameter": 76.0,
                "wall_thickness_required": 3.0,
                "core_length": 1000.0
            },
            "materials_composition": [],
            "material_layers": [
                {
                    "material_id": "test-material-1",
                    "material_name": "Test Material",
                    "layer_type": "Outer Most Layer",
                    "thickness": 2.5,
                    "quantity": 1.0
                }
            ],
            "manufacturing_notes": "Test manufacturing notes",
            "selected_thickness": 2.5
        }
        
        # Create the specification first
        try:
            create_response = self.session.post(f"{API_BASE}/product-specifications", json=test_spec_data)
            
            if create_response.status_code != 200:
                self.log_result(
                    "Product Specifications Update Validation - Create Test Spec", 
                    False, 
                    f"Failed to create test specification: {create_response.status_code}",
                    create_response.text
                )
                return
            
            spec_id = create_response.json().get('data', {}).get('id')
            if not spec_id:
                self.log_result(
                    "Product Specifications Update Validation - Create Test Spec", 
                    False, 
                    "No specification ID returned from create"
                )
                return
            
            self.log_result(
                "Product Specifications Update Validation - Create Test Spec", 
                True, 
                f"Successfully created test specification with ID: {spec_id}"
            )
            
            # Test scenarios for UPDATE validation
            test_scenarios = [
                {
                    "name": "Valid Complete Update",
                    "data": {
                        "product_name": "Updated Test Product",
                        "product_type": "Spiral Paper Core",
                        "specifications": {
                            "internal_diameter": 80.0,
                            "wall_thickness_required": 3.5,
                            "core_length": 1200.0
                        },
                        "materials_composition": [],
                        "material_layers": [
                            {
                                "material_id": "test-material-2",
                                "material_name": "Updated Test Material",
                                "layer_type": "Central Layer",
                                "thickness": 3.0,
                                "quantity": 1.0
                            }
                        ],
                        "manufacturing_notes": "Updated manufacturing notes",
                        "selected_thickness": 3.0
                    },
                    "expected_status": 200
                },
                {
                    "name": "Missing product_name",
                    "data": {
                        "product_type": "Spiral Paper Core",
                        "specifications": {"internal_diameter": 76.0},
                        "materials_composition": [],
                        "material_layers": [],
                        "manufacturing_notes": "Test notes",
                        "selected_thickness": 2.5
                    },
                    "expected_status": 422
                },
                {
                    "name": "Missing product_type",
                    "data": {
                        "product_name": "Test Product",
                        "specifications": {"internal_diameter": 76.0},
                        "materials_composition": [],
                        "material_layers": [],
                        "manufacturing_notes": "Test notes",
                        "selected_thickness": 2.5
                    },
                    "expected_status": 422
                },
                {
                    "name": "Missing specifications",
                    "data": {
                        "product_name": "Test Product",
                        "product_type": "Spiral Paper Core",
                        "materials_composition": [],
                        "material_layers": [],
                        "manufacturing_notes": "Test notes",
                        "selected_thickness": 2.5
                    },
                    "expected_status": 422
                },
                {
                    "name": "Empty product_name",
                    "data": {
                        "product_name": "",
                        "product_type": "Spiral Paper Core",
                        "specifications": {"internal_diameter": 76.0},
                        "materials_composition": [],
                        "material_layers": [],
                        "manufacturing_notes": "Test notes",
                        "selected_thickness": 2.5
                    },
                    "expected_status": 422
                },
                {
                    "name": "Null product_name",
                    "data": {
                        "product_name": None,
                        "product_type": "Spiral Paper Core",
                        "specifications": {"internal_diameter": 76.0},
                        "materials_composition": [],
                        "material_layers": [],
                        "manufacturing_notes": "Test notes",
                        "selected_thickness": 2.5
                    },
                    "expected_status": 422
                },
                {
                    "name": "Invalid product_type (not string)",
                    "data": {
                        "product_name": "Test Product",
                        "product_type": 123,
                        "specifications": {"internal_diameter": 76.0},
                        "materials_composition": [],
                        "material_layers": [],
                        "manufacturing_notes": "Test notes",
                        "selected_thickness": 2.5
                    },
                    "expected_status": 422
                },
                {
                    "name": "Invalid specifications (not dict)",
                    "data": {
                        "product_name": "Test Product",
                        "product_type": "Spiral Paper Core",
                        "specifications": "invalid_string",
                        "materials_composition": [],
                        "material_layers": [],
                        "manufacturing_notes": "Test notes",
                        "selected_thickness": 2.5
                    },
                    "expected_status": 422
                },
                {
                    "name": "Invalid material_layers (not array)",
                    "data": {
                        "product_name": "Test Product",
                        "product_type": "Spiral Paper Core",
                        "specifications": {"internal_diameter": 76.0},
                        "materials_composition": [],
                        "material_layers": "invalid_string",
                        "manufacturing_notes": "Test notes",
                        "selected_thickness": 2.5
                    },
                    "expected_status": 422
                },
                {
                    "name": "Invalid selected_thickness (string instead of float)",
                    "data": {
                        "product_name": "Test Product",
                        "product_type": "Spiral Paper Core",
                        "specifications": {"internal_diameter": 76.0},
                        "materials_composition": [],
                        "material_layers": [],
                        "manufacturing_notes": "Test notes",
                        "selected_thickness": "invalid_string"
                    },
                    "expected_status": 422
                },
                {
                    "name": "Minimal Required Fields Only",
                    "data": {
                        "product_name": "Minimal Test Product",
                        "product_type": "Paper Core",
                        "specifications": {"basic_spec": "test"}
                    },
                    "expected_status": 200
                },
                {
                    "name": "Test with User Data Structure",
                    "data": {
                        "product_name": "Paper Core - 76mm ID x 3mmT",
                        "product_type": "Spiral Paper Core",
                        "specifications": {
                            "internal_diameter": 76.0,
                            "wall_thickness_required": 3.0,
                            "core_length": 1000.0,
                            "adhesive_type": "Water-based",
                            "surface_finish": "Smooth"
                        },
                        "materials_composition": [
                            {
                                "material": "Kraft Paper",
                                "percentage": 80,
                                "gsm": 120
                            }
                        ],
                        "material_layers": [
                            {
                                "material_id": "kraft-paper-120gsm",
                                "material_name": "Kraft Paper 120GSM",
                                "layer_type": "Outer Most Layer",
                                "thickness": 0.12,
                                "quantity": 25.0
                            }
                        ],
                        "manufacturing_notes": "Handle with care during winding process",
                        "selected_thickness": 3.0
                    },
                    "expected_status": 200
                }
            ]
            
            validation_errors_found = []
            successful_updates = 0
            
            for scenario in test_scenarios:
                try:
                    print(f"\n  Testing: {scenario['name']}")
                    response = self.session.put(f"{API_BASE}/product-specifications/{spec_id}", json=scenario["data"])
                    
                    print(f"    Status: {response.status_code} (expected: {scenario['expected_status']})")
                    
                    if response.status_code == scenario["expected_status"]:
                        if response.status_code == 422:
                            # Parse validation errors
                            try:
                                error_data = response.json()
                                print(f"    Response: {json.dumps(error_data, indent=2)}")
                                
                                if "detail" in error_data and isinstance(error_data["detail"], list):
                                    for error in error_data["detail"]:
                                        if isinstance(error, dict):
                                            error_info = {
                                                "scenario": scenario["name"],
                                                "field": error.get("loc", ["unknown"])[-1] if error.get("loc") else "unknown",
                                                "full_location": error.get("loc", []),
                                                "message": error.get("msg", "Unknown error"),
                                                "type": error.get("type", "unknown"),
                                                "input": error.get("input", "unknown")
                                            }
                                            validation_errors_found.append(error_info)
                                
                                self.log_result(
                                    f"Update Validation - {scenario['name']}", 
                                    True, 
                                    f"Expected 422 validation error received",
                                    f"Errors: {len(error_data.get('detail', []))}"
                                )
                            except Exception as parse_error:
                                print(f"    Parse error: {parse_error}")
                                print(f"    Raw response: {response.text}")
                                self.log_result(
                                    f"Update Validation - {scenario['name']}", 
                                    True, 
                                    f"Expected 422 validation error received (unparseable response)",
                                    response.text[:200]
                                )
                        else:
                            successful_updates += 1
                            self.log_result(
                                f"Update Validation - {scenario['name']}", 
                                True, 
                                f"Update successful as expected"
                            )
                    else:
                        print(f"    Unexpected status! Response: {response.text[:300]}")
                        self.log_result(
                            f"Update Validation - {scenario['name']}", 
                            False, 
                            f"Expected status {scenario['expected_status']} but got {response.status_code}",
                            response.text[:200]
                        )
                        
                except Exception as e:
                    print(f"    Exception: {str(e)}")
                    self.log_result(f"Update Validation - {scenario['name']}", False, f"Error: {str(e)}")
            
            # Summary of validation errors found
            if validation_errors_found:
                print(f"\n📋 VALIDATION ERRORS IDENTIFIED ({len(validation_errors_found)} total):")
                for i, error in enumerate(validation_errors_found, 1):
                    print(f"  {i}. Scenario: {error['scenario']}")
                    print(f"     Field: {error['field']}")
                    print(f"     Full Location: {error['full_location']}")
                    print(f"     Message: {error['message']}")
                    print(f"     Type: {error['type']}")
                    print(f"     Input: {error['input']}")
                    print()
                
                self.log_result(
                    "Product Specifications Update Validation Summary", 
                    True, 
                    f"Identified {len(validation_errors_found)} specific validation errors across {len(test_scenarios)} test scenarios",
                    f"Successful updates: {successful_updates}, Failed validations: {len(validation_errors_found)}"
                )
            else:
                self.log_result(
                    "Product Specifications Update Validation Summary", 
                    False, 
                    "No validation errors captured - this may indicate an issue with error handling"
                )
            
            # Test CREATE vs UPDATE differences
            print(f"\n🔍 TESTING CREATE vs UPDATE VALIDATION DIFFERENCES:")
            
            # Test same data with CREATE endpoint
            create_test_data = {
                "product_name": "",  # Empty name to trigger validation
                "product_type": "Spiral Paper Core",
                "specifications": {"internal_diameter": 76.0},
                "materials_composition": [],
                "material_layers": [],
                "manufacturing_notes": "Test notes",
                "selected_thickness": 2.5
            }
            
            print("  Testing CREATE endpoint with empty product_name...")
            create_response = self.session.post(f"{API_BASE}/product-specifications", json=create_test_data)
            print(f"    CREATE Status: {create_response.status_code}")
            
            print("  Testing UPDATE endpoint with empty product_name...")
            update_response = self.session.put(f"{API_BASE}/product-specifications/{spec_id}", json=create_test_data)
            print(f"    UPDATE Status: {update_response.status_code}")
            
            if create_response.status_code == update_response.status_code:
                self.log_result(
                    "CREATE vs UPDATE Validation Consistency", 
                    True, 
                    f"Both CREATE and UPDATE return same status code ({create_response.status_code}) for identical invalid data"
                )
            else:
                self.log_result(
                    "CREATE vs UPDATE Validation Consistency", 
                    False, 
                    f"CREATE returned {create_response.status_code} but UPDATE returned {update_response.status_code} for same data",
                    f"CREATE: {create_response.text[:100]}, UPDATE: {update_response.text[:100]}"
                )
            
            # Test with existing specification data to see what works
            print(f"\n🔍 TESTING UPDATE WITH EXISTING SPECIFICATION DATA:")
            
            # Get the existing specification
            get_response = self.session.get(f"{API_BASE}/product-specifications/{spec_id}")
            if get_response.status_code == 200:
                existing_spec = get_response.json()
                print(f"  Existing specification structure:")
                print(f"    Keys: {list(existing_spec.keys())}")
                
                # Try updating with the exact same data
                update_same_response = self.session.put(f"{API_BASE}/product-specifications/{spec_id}", json={
                    "product_name": existing_spec.get("product_name"),
                    "product_type": existing_spec.get("product_type"),
                    "specifications": existing_spec.get("specifications", {}),
                    "materials_composition": existing_spec.get("materials_composition", []),
                    "material_layers": existing_spec.get("material_layers", []),
                    "manufacturing_notes": existing_spec.get("manufacturing_notes"),
                    "selected_thickness": existing_spec.get("selected_thickness")
                })
                
                print(f"  UPDATE with same data status: {update_same_response.status_code}")
                if update_same_response.status_code != 200:
                    print(f"  Error: {update_same_response.text}")
                    
                self.log_result(
                    "UPDATE with Existing Data", 
                    update_same_response.status_code == 200, 
                    f"Update with existing data returned {update_same_response.status_code}",
                    update_same_response.text[:200] if update_same_response.status_code != 200 else None
                )
            
        except Exception as e:
            self.log_result("Product Specifications Update Validation", False, f"Test setup error: {str(e)}")

    def print_test_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 80)
        print("🎯 PRODUCT SPECIFICATIONS UPDATE VALIDATION TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['success']])
        failed_tests = total_tests - passed_tests
        
        print(f"📊 OVERALL RESULTS:")
        print(f"   Total Tests: {total_tests}")
        print(f"   ✅ Passed: {passed_tests}")
        print(f"   ❌ Failed: {failed_tests}")
        print(f"   Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   • {result['test']}: {result['message']}")
                    if result['details']:
                        print(f"     Details: {result['details']}")
        
        print(f"\n🔍 KEY FINDINGS:")
        validation_tests = [r for r in self.test_results if 'Update Validation -' in r['test']]
        if validation_tests:
            validation_passed = len([r for r in validation_tests if r['success']])
            print(f"   • Validation Tests: {validation_passed}/{len(validation_tests)} passed")
        
        print(f"\n📝 RECOMMENDATIONS:")
        print(f"   • Check FastAPI validation error structure in backend")
        print(f"   • Verify required fields for UPDATE vs CREATE operations")
        print(f"   • Test with actual frontend form data structure")
        print(f"   • Implement proper error handling for 422 responses")

    def run_all_tests(self):
        """Run all tests in sequence"""
        print("🚀 Starting Product Specifications UPDATE Validation Testing")
        print(f"Backend URL: {API_BASE}")
        print("=" * 80)
        
        # Authentication is required for all tests
        if not self.authenticate():
            print("❌ Authentication failed - cannot proceed with tests")
            return
        
        # Focus on Product Specifications UPDATE validation testing
        self.test_product_specifications_update_validation()
        
        # Print summary
        self.print_test_summary()

def main():
    """Main function to run the tests"""
    tester = ProductSpecsValidationTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()