#!/usr/bin/env python3
"""
User-Specific Product Specifications UPDATE Validation Testing
Tests the exact scenario the user is experiencing with "Field required, Field required, Field required" errors
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

class UserSpecificValidationTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        
    def authenticate(self):
        """Test authentication with demo user"""
        print("=== AUTHENTICATION ===")
        
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
                print(f"✅ Authenticated as {user_info.get('username')} with role {user_info.get('role')}")
                return True
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication error: {str(e)}")
            return False
    
    def get_existing_specification(self):
        """Get an existing specification to test updates"""
        print("\n=== GETTING EXISTING SPECIFICATION ===")
        
        try:
            response = self.session.get(f"{API_BASE}/product-specifications")
            
            if response.status_code == 200:
                specs = response.json()
                if specs and len(specs) > 0:
                    spec = specs[0]  # Get the first specification
                    print(f"✅ Found existing specification: {spec.get('product_name')} (ID: {spec.get('id')})")
                    return spec
                else:
                    print("❌ No existing specifications found")
                    return None
            else:
                print(f"❌ Failed to get specifications: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error getting specifications: {str(e)}")
            return None
    
    def test_user_scenario_update(self, spec_id):
        """Test the exact scenario the user is experiencing"""
        print(f"\n=== TESTING USER SCENARIO UPDATE ===")
        print(f"Testing UPDATE on specification ID: {spec_id}")
        
        # Test data structure as mentioned by user
        user_data_structure = {
            "product_name": "Paper Core - 76mm ID x 3mmT - Updated",
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
        }
        
        print("📤 Sending UPDATE request with user data structure...")
        print(f"Data: {json.dumps(user_data_structure, indent=2)}")
        
        try:
            response = self.session.put(f"{API_BASE}/product-specifications/{spec_id}", json=user_data_structure)
            
            print(f"\n📥 Response Status: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            
            if response.status_code == 422:
                print("🚨 VALIDATION ERROR DETECTED!")
                try:
                    error_data = response.json()
                    print(f"Error Response: {json.dumps(error_data, indent=2)}")
                    
                    if "detail" in error_data and isinstance(error_data["detail"], list):
                        print(f"\n📋 SPECIFIC VALIDATION ERRORS ({len(error_data['detail'])} total):")
                        for i, error in enumerate(error_data["detail"], 1):
                            print(f"  {i}. Field: {error.get('loc', ['unknown'])[-1] if error.get('loc') else 'unknown'}")
                            print(f"     Location: {error.get('loc', [])}")
                            print(f"     Message: {error.get('msg', 'Unknown error')}")
                            print(f"     Type: {error.get('type', 'unknown')}")
                            print(f"     Input: {error.get('input', 'unknown')}")
                            print()
                        
                        # Check if this matches the user's "Field required, Field required, Field required" pattern
                        field_required_errors = [e for e in error_data["detail"] if e.get("msg") == "Field required"]
                        if len(field_required_errors) >= 3:
                            print("🎯 MATCHES USER'S ISSUE: Multiple 'Field required' errors found!")
                            print(f"   Required fields: {[e.get('loc', ['unknown'])[-1] for e in field_required_errors]}")
                        
                except Exception as parse_error:
                    print(f"❌ Failed to parse error response: {parse_error}")
                    print(f"Raw response: {response.text}")
                    
            elif response.status_code == 200:
                print("✅ UPDATE SUCCESSFUL!")
                try:
                    success_data = response.json()
                    print(f"Success Response: {json.dumps(success_data, indent=2)}")
                except:
                    print(f"Raw success response: {response.text}")
            else:
                print(f"❌ Unexpected status code: {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Request error: {str(e)}")
    
    def test_minimal_update_scenarios(self, spec_id):
        """Test various minimal update scenarios to identify required fields"""
        print(f"\n=== TESTING MINIMAL UPDATE SCENARIOS ===")
        
        test_scenarios = [
            {
                "name": "Only product_name",
                "data": {
                    "product_name": "Updated Product Name Only"
                }
            },
            {
                "name": "Only product_name and product_type",
                "data": {
                    "product_name": "Updated Product Name",
                    "product_type": "Spiral Paper Core"
                }
            },
            {
                "name": "Only product_name, product_type, and empty specifications",
                "data": {
                    "product_name": "Updated Product Name",
                    "product_type": "Spiral Paper Core",
                    "specifications": {}
                }
            },
            {
                "name": "Missing materials_composition and material_layers",
                "data": {
                    "product_name": "Updated Product Name",
                    "product_type": "Spiral Paper Core",
                    "specifications": {"internal_diameter": 76.0}
                }
            },
            {
                "name": "With empty arrays for optional fields",
                "data": {
                    "product_name": "Updated Product Name",
                    "product_type": "Spiral Paper Core",
                    "specifications": {"internal_diameter": 76.0},
                    "materials_composition": [],
                    "material_layers": []
                }
            }
        ]
        
        for scenario in test_scenarios:
            print(f"\n🧪 Testing: {scenario['name']}")
            print(f"   Data: {json.dumps(scenario['data'], indent=2)}")
            
            try:
                response = self.session.put(f"{API_BASE}/product-specifications/{spec_id}", json=scenario["data"])
                print(f"   Status: {response.status_code}")
                
                if response.status_code == 422:
                    try:
                        error_data = response.json()
                        required_fields = [e.get('loc', ['unknown'])[-1] for e in error_data.get("detail", []) if e.get("msg") == "Field required"]
                        if required_fields:
                            print(f"   ❌ Required fields missing: {required_fields}")
                        else:
                            print(f"   ❌ Other validation errors: {len(error_data.get('detail', []))}")
                    except:
                        print(f"   ❌ Validation error (unparseable)")
                elif response.status_code == 200:
                    print(f"   ✅ Success")
                else:
                    print(f"   ❓ Unexpected status: {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ Error: {str(e)}")
    
    def test_frontend_form_data_simulation(self, spec_id):
        """Simulate what the frontend form might be sending"""
        print(f"\n=== TESTING FRONTEND FORM DATA SIMULATION ===")
        
        # Simulate incomplete form data that might cause the user's issue
        incomplete_form_scenarios = [
            {
                "name": "Form with undefined/null values",
                "data": {
                    "product_name": "Test Product",
                    "product_type": "Spiral Paper Core",
                    "specifications": None,  # This might happen if form field is empty
                    "materials_composition": None,
                    "material_layers": None,
                    "manufacturing_notes": None,
                    "selected_thickness": None
                }
            },
            {
                "name": "Form with missing nested required fields",
                "data": {
                    "product_name": "Test Product",
                    "product_type": "Spiral Paper Core",
                    "specifications": {},  # Empty object
                    "materials_composition": [],
                    "material_layers": [
                        {
                            # Missing required fields in material layer
                            "material_name": "Test Material"
                            # Missing: material_id, layer_type, thickness
                        }
                    ],
                    "manufacturing_notes": "",
                    "selected_thickness": 0
                }
            },
            {
                "name": "Form with string numbers (common frontend issue)",
                "data": {
                    "product_name": "Test Product",
                    "product_type": "Spiral Paper Core",
                    "specifications": {
                        "internal_diameter": "76.0",  # String instead of number
                        "wall_thickness_required": "3.0"
                    },
                    "materials_composition": [],
                    "material_layers": [],
                    "manufacturing_notes": "",
                    "selected_thickness": "3.0"  # String instead of number
                }
            }
        ]
        
        for scenario in incomplete_form_scenarios:
            print(f"\n🎭 Testing: {scenario['name']}")
            
            try:
                response = self.session.put(f"{API_BASE}/product-specifications/{spec_id}", json=scenario["data"])
                print(f"   Status: {response.status_code}")
                
                if response.status_code == 422:
                    try:
                        error_data = response.json()
                        print(f"   📋 Validation errors found: {len(error_data.get('detail', []))}")
                        
                        field_required_count = len([e for e in error_data.get("detail", []) if e.get("msg") == "Field required"])
                        if field_required_count >= 3:
                            print(f"   🎯 POTENTIAL MATCH: {field_required_count} 'Field required' errors!")
                            for error in error_data.get("detail", []):
                                if error.get("msg") == "Field required":
                                    field_name = error.get('loc', ['unknown'])[-1]
                                    print(f"      - {field_name}: Field required")
                        
                        # Show all errors for this scenario
                        for i, error in enumerate(error_data.get("detail", []), 1):
                            field_name = error.get('loc', ['unknown'])[-1]
                            message = error.get('msg', 'Unknown error')
                            print(f"      {i}. {field_name}: {message}")
                            
                    except Exception as parse_error:
                        print(f"   ❌ Parse error: {parse_error}")
                        print(f"   Raw response: {response.text}")
                        
                elif response.status_code == 200:
                    print(f"   ✅ Unexpected success")
                else:
                    print(f"   ❓ Status: {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ Request error: {str(e)}")

    def run_tests(self):
        """Run all user-specific validation tests"""
        print("🚀 USER-SPECIFIC PRODUCT SPECIFICATIONS UPDATE VALIDATION TESTING")
        print(f"Backend URL: {API_BASE}")
        print("=" * 80)
        
        # Authentication
        if not self.authenticate():
            print("❌ Cannot proceed without authentication")
            return
        
        # Get existing specification to test with
        existing_spec = self.get_existing_specification()
        if not existing_spec:
            print("❌ Cannot proceed without existing specification")
            return
        
        spec_id = existing_spec.get('id')
        
        # Test the user's specific scenario
        self.test_user_scenario_update(spec_id)
        
        # Test minimal update scenarios
        self.test_minimal_update_scenarios(spec_id)
        
        # Test frontend form data simulation
        self.test_frontend_form_data_simulation(spec_id)
        
        print("\n" + "=" * 80)
        print("🎯 TESTING COMPLETE")
        print("=" * 80)

def main():
    """Main function to run the tests"""
    tester = UserSpecificValidationTester()
    tester.run_tests()

if __name__ == "__main__":
    main()