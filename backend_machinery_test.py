#!/usr/bin/env python3
"""
Backend API Testing Suite for Machinery Section in Product Specifications
Tests the recently implemented machinery functionality and system stability
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

class MachineryBackendTester:
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
    
    def test_machinery_product_specifications_create(self):
        """Test POST /api/product-specifications with machinery data"""
        print("\n=== MACHINERY PRODUCT SPECIFICATIONS CREATE TEST ===")
        
        try:
            # Test data with comprehensive machinery section
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
                                "function": "Slitting",
                                "rate_per_hour": 500.0
                            },
                            {
                                "function": "winding",
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
                                "function": "Cutting/Indexing",
                                "rate_per_hour": 400.0
                            },
                            {
                                "function": "splitting",
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
                                "function": "Packing",
                                "rate_per_hour": 250.0
                            },
                            {
                                "function": "Delivery Time",
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
    
    def test_system_stability(self):
        """Test overall system stability and key endpoints"""
        print("\n=== SYSTEM STABILITY TESTING ===")
        
        # Test key CRUD operations
        self.test_clients_endpoint()
        self.test_materials_endpoint()
        self.test_product_specifications_basic()
        self.test_production_board()
        self.test_invoicing_endpoints()
    
    def test_clients_endpoint(self):
        """Test GET /api/clients endpoint"""
        print("\n=== CLIENTS ENDPOINT TEST ===")
        
        try:
            response = self.session.get(f"{API_BASE}/clients")
            
            if response.status_code == 200:
                clients = response.json()
                
                if isinstance(clients, list) and len(clients) > 0:
                    # Check client structure
                    client = clients[0]
                    required_fields = ['id', 'company_name', 'email']
                    missing_fields = [field for field in required_fields if field not in client]
                    
                    if not missing_fields:
                        self.log_result(
                            "Clients Endpoint", 
                            True, 
                            f"Successfully retrieved {len(clients)} clients with proper structure"
                        )
                    else:
                        self.log_result(
                            "Clients Endpoint", 
                            False, 
                            f"Client structure missing fields: {missing_fields}"
                        )
                else:
                    self.log_result(
                        "Clients Endpoint", 
                        False, 
                        "No clients found or invalid response format"
                    )
            else:
                self.log_result(
                    "Clients Endpoint", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Clients Endpoint", False, f"Error: {str(e)}")
    
    def test_materials_endpoint(self):
        """Test GET /api/materials endpoint"""
        print("\n=== MATERIALS ENDPOINT TEST ===")
        
        try:
            response = self.session.get(f"{API_BASE}/materials")
            
            if response.status_code == 200:
                materials = response.json()
                
                if isinstance(materials, list) and len(materials) > 0:
                    # Check material structure
                    material = materials[0]
                    required_fields = ['id', 'product_code', 'supplier', 'unit']
                    missing_fields = [field for field in required_fields if field not in material]
                    
                    if not missing_fields:
                        self.log_result(
                            "Materials Endpoint", 
                            True, 
                            f"Successfully retrieved {len(materials)} materials with proper structure"
                        )
                    else:
                        self.log_result(
                            "Materials Endpoint", 
                            False, 
                            f"Material structure missing fields: {missing_fields}"
                        )
                else:
                    self.log_result(
                        "Materials Endpoint", 
                        False, 
                        "No materials found or invalid response format"
                    )
            else:
                self.log_result(
                    "Materials Endpoint", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Materials Endpoint", False, f"Error: {str(e)}")
    
    def test_product_specifications_basic(self):
        """Test basic GET /api/product-specifications endpoint"""
        print("\n=== PRODUCT SPECIFICATIONS BASIC TEST ===")
        
        try:
            response = self.session.get(f"{API_BASE}/product-specifications")
            
            if response.status_code == 200:
                specs = response.json()
                
                if isinstance(specs, list):
                    self.log_result(
                        "Product Specifications Basic", 
                        True, 
                        f"Successfully retrieved {len(specs)} product specifications"
                    )
                else:
                    self.log_result(
                        "Product Specifications Basic", 
                        False, 
                        "Invalid response format - expected list"
                    )
            else:
                self.log_result(
                    "Product Specifications Basic", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Product Specifications Basic", False, f"Error: {str(e)}")
    
    def test_production_board(self):
        """Test GET /api/production/board endpoint"""
        print("\n=== PRODUCTION BOARD TEST ===")
        
        try:
            response = self.session.get(f"{API_BASE}/production/board")
            
            if response.status_code == 200:
                data = response.json()
                
                if 'success' in data and 'data' in data:
                    board_data = data.get('data', {})
                    
                    # Check for expected production stages
                    expected_stages = ['order_entered', 'pending_material', 'paper_slitting', 'winding', 'finishing', 'delivery', 'invoicing']
                    found_stages = [stage for stage in expected_stages if stage in board_data]
                    
                    if len(found_stages) >= 5:  # At least 5 stages should be present
                        self.log_result(
                            "Production Board", 
                            True, 
                            f"Production board working with {len(found_stages)} stages",
                            f"Stages: {', '.join(found_stages)}"
                        )
                    else:
                        self.log_result(
                            "Production Board", 
                            False, 
                            f"Missing production stages - only found {len(found_stages)}",
                            f"Found: {found_stages}, Expected: {expected_stages}"
                        )
                else:
                    self.log_result(
                        "Production Board", 
                        False, 
                        "Invalid response structure - missing success/data fields"
                    )
            else:
                self.log_result(
                    "Production Board", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Production Board", False, f"Error: {str(e)}")
    
    def test_invoicing_endpoints(self):
        """Test invoicing workflow endpoints"""
        print("\n=== INVOICING ENDPOINTS TEST ===")
        
        try:
            # Test live jobs endpoint
            response = self.session.get(f"{API_BASE}/invoicing/live-jobs")
            
            if response.status_code == 200:
                data = response.json()
                jobs = data.get('data', [])
                
                self.log_result(
                    "Invoicing Live Jobs", 
                    True, 
                    f"Successfully retrieved {len(jobs)} live jobs for invoicing"
                )
                
                # Test Xero status
                xero_response = self.session.get(f"{API_BASE}/xero/status")
                
                if xero_response.status_code == 200:
                    xero_data = xero_response.json()
                    connected = xero_data.get('connected', False)
                    
                    self.log_result(
                        "Xero Integration Status", 
                        True, 
                        f"Xero connection status: {'Connected' if connected else 'Not Connected'}",
                        xero_data.get('message', '')
                    )
                else:
                    self.log_result(
                        "Xero Integration Status", 
                        False, 
                        f"Failed to get Xero status: {xero_response.status_code}"
                    )
                    
            else:
                self.log_result(
                    "Invoicing Live Jobs", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Invoicing Endpoints", False, f"Error: {str(e)}")
    
    def run_comprehensive_backend_tests(self):
        """Run all backend tests including machinery and system stability"""
        print("\n" + "="*80)
        print("COMPREHENSIVE BACKEND API TESTING")
        print("="*80)
        
        # Step 1: Authenticate
        if not self.authenticate():
            print("❌ Authentication failed - cannot proceed with tests")
            return
        
        # Step 2: Test Machinery Functionality (Primary Focus)
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
        
        # Step 3: Test System Stability - Key Endpoints
        print("\n" + "="*60)
        print("SYSTEM STABILITY TESTING")
        print("="*60)
        
        self.test_system_stability()
        
        # Print comprehensive summary
        self.print_comprehensive_test_summary()
    
    def print_comprehensive_test_summary(self):
        """Print comprehensive test summary with focus on machinery"""
        print("\n" + "="*80)
        print("COMPREHENSIVE BACKEND TEST SUMMARY")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['success']])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%" if total_tests > 0 else "0%")
        
        # Machinery-specific summary
        machinery_results = [r for r in self.test_results if 'Machinery' in r['test']]
        if machinery_results:
            machinery_passed = len([r for r in machinery_results if r['success']])
            print(f"\n🔧 MACHINERY FUNCTIONALITY: {machinery_passed}/{len(machinery_results)} tests passed")
            
            for result in machinery_results:
                status = "✅ PASS" if result['success'] else "❌ FAIL"
                print(f"  {status}: {result['message']}")
                if result['details'] and not result['success']:
                    print(f"    Details: {result['details']}")
        
        # System stability summary
        stability_results = [r for r in self.test_results if any(keyword in r['test'] for keyword in ['Endpoint', 'Board', 'Invoicing', 'Permissions'])]
        if stability_results:
            stability_passed = len([r for r in stability_results if r['success']])
            print(f"\n🏗️ SYSTEM STABILITY: {stability_passed}/{len(stability_results)} tests passed")
            
            for result in stability_results:
                status = "✅ PASS" if result['success'] else "❌ FAIL"
                print(f"  {status}: {result['message']}")
                if result['details'] and not result['success']:
                    print(f"    Details: {result['details']}")
        
        # Critical issues
        critical_issues = [r for r in self.test_results if not r['success'] and 'Machinery' in r['test']]
        if critical_issues:
            print(f"\n🚨 CRITICAL MACHINERY ISSUES:")
            for issue in critical_issues:
                print(f"  - {issue['test']}: {issue['message']}")
        
        print("\n" + "="*80)

if __name__ == "__main__":
    tester = MachineryBackendTester()
    tester.run_comprehensive_backend_tests()