#!/usr/bin/env python3
"""
Order Creation Issues Investigation
Focus on identifying specific API failures and resolving them
"""

import requests
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:8001')
API_BASE = f"{BACKEND_URL}/api"

class OrderInvestigationTester:
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
    
    def test_existing_orders(self):
        """Test with existing orders ADM-2025-0002 and ADM-2025-0005"""
        print("\n=== EXISTING ORDERS TESTING ===")
        
        existing_orders = ["ADM-2025-0002", "ADM-2025-0005"]
        
        try:
            # First get all orders to find the IDs
            response = self.session.get(f"{API_BASE}/orders")
            
            if response.status_code == 200:
                orders = response.json()
                self.log_result(
                    "Existing Orders - GET /api/orders", 
                    True, 
                    f"Successfully retrieved {len(orders)} orders"
                )
                
                # Find the specific orders
                for target_order_number in existing_orders:
                    found_order = None
                    for order in orders:
                        if order.get('order_number') == target_order_number:
                            found_order = order
                            break
                    
                    if found_order:
                        order_id = found_order['id']
                        self.log_result(
                            f"Existing Orders - {target_order_number}", 
                            True, 
                            f"Found order {target_order_number}",
                            f"ID: {order_id}, Client: {found_order.get('client_name')}, Priority: {found_order.get('priority')}"
                        )
                        
                        # Test individual order retrieval
                        self.test_individual_order_retrieval(order_id, target_order_number)
                        
                    else:
                        self.log_result(
                            f"Existing Orders - {target_order_number}", 
                            False, 
                            f"Order {target_order_number} not found in system"
                        )
                
            else:
                self.log_result(
                    "Existing Orders - GET /api/orders", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Existing Orders Testing", False, f"Error: {str(e)}")
    
    def test_individual_order_retrieval(self, order_id, order_number):
        """Test individual order retrieval"""
        try:
            response = self.session.get(f"{API_BASE}/orders/{order_id}")
            
            if response.status_code == 200:
                order = response.json()
                
                # Check for priority field specifically
                priority = order.get('priority')
                items = order.get('items', [])
                
                self.log_result(
                    f"Individual Order - {order_number}", 
                    True, 
                    f"Successfully retrieved order details",
                    f"Priority: {priority}, Items: {len(items)}, Total: ${order.get('total_amount')}"
                )
                
                # Check if items have required fields for job card system
                if items:
                    first_item = items[0]
                    item_fields = ['product_name', 'quantity', 'unit_price']
                    missing_item_fields = [field for field in item_fields if field not in first_item]
                    
                    if not missing_item_fields:
                        self.log_result(
                            f"Order Items - {order_number}", 
                            True, 
                            "Order items contain required fields for job card system"
                        )
                    else:
                        self.log_result(
                            f"Order Items - {order_number}", 
                            False, 
                            f"Order items missing fields: {missing_item_fields}"
                        )
                
            else:
                self.log_result(
                    f"Individual Order - {order_number}", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result(f"Individual Order Retrieval - {order_number}", False, f"Error: {str(e)}")
    
    def test_order_creation_issues(self):
        """Test order creation with proper complete order data structure"""
        print("\n=== ORDER CREATION ISSUES INVESTIGATION ===")
        
        try:
            # First, get a valid client ID
            clients_response = self.session.get(f"{API_BASE}/clients")
            if clients_response.status_code != 200:
                self.log_result(
                    "Order Creation - Get Clients", 
                    False, 
                    f"Failed to get clients: {clients_response.status_code}",
                    clients_response.text
                )
                return
            
            clients = clients_response.json()
            if not clients:
                self.log_result(
                    "Order Creation - Client Available", 
                    False, 
                    "No clients available for order creation"
                )
                return
            
            # Use Label Makers client if available, otherwise first client
            client = None
            for c in clients:
                if "Label Makers" in c.get('company_name', ''):
                    client = c
                    break
            if not client:
                client = clients[0]
            
            client_id = client['id']
            self.log_result(
                "Order Creation - Client Selection", 
                True, 
                f"Using client: {client.get('company_name')} (ID: {client_id})"
            )
            
            # Create comprehensive order data with all required fields based on the error analysis
            order_data = {
                "client_id": client_id,
                "purchase_order_number": "PO-TEST-2025-001",
                "due_date": (datetime.now() + timedelta(days=14)).isoformat(),
                "priority": "Normal/Low",
                "items": [
                    {
                        "product_id": "test-product-001",  # REQUIRED: This was missing
                        "product_name": "Test Paper Core - 40mm ID x 1.8mmT",
                        "quantity": 1000,
                        "unit_price": 2.50,
                        "total_price": 2500.00,
                        "specifications": {
                            "material_type": "Spiral Paper Core",  # REQUIRED: This was missing
                            "dimensions": {  # REQUIRED: This was missing
                                "internal_diameter": 40,
                                "wall_thickness": 1.8,
                                "length": 1000
                            },
                            "core_id": 40,
                            "wall_thickness_required": 1.8,
                            "material_layers": [
                                {
                                    "material_id": "mat-001",
                                    "layer_type": "Outer Most Layer",
                                    "thickness": 0.6,
                                    "quantity": 1
                                },
                                {
                                    "material_id": "mat-002", 
                                    "layer_type": "Central Layer",
                                    "thickness": 0.6,
                                    "quantity": 1
                                },
                                {
                                    "material_id": "mat-003",
                                    "layer_type": "Inner Most Layer", 
                                    "thickness": 0.6,
                                    "quantity": 1
                                }
                            ]
                        }
                    }
                ],
                "delivery_address": "123 Test Street, Test City, NSW 2000",
                "delivery_instructions": "Standard delivery during business hours",
                "runtime_estimate": "2-3 days",
                "notes": "Test order for API validation",
                "discount_percentage": 0,
                "discount_notes": None
            }
            
            # Test POST /api/orders with complete data
            response = self.session.post(f"{API_BASE}/orders", json=order_data)
            
            if response.status_code == 200:
                result = response.json()
                order_id = result.get('data', {}).get('id')
                order_number = result.get('data', {}).get('order_number')
                
                self.log_result(
                    "Order Creation - POST /api/orders", 
                    True, 
                    f"Successfully created order: {order_number}",
                    f"Order ID: {order_id}, Total: $2500.00"
                )
                
                # Test GET /api/orders/{order_id} with the new order
                if order_id:
                    self.test_order_retrieval(order_id, order_number)
                
            elif response.status_code == 422:
                # Parse validation errors
                error_data = response.json()
                detail = error_data.get('detail', [])
                
                missing_fields = []
                for error in detail:
                    if isinstance(error, dict):
                        field_path = error.get('loc', [])
                        error_msg = error.get('msg', '')
                        missing_fields.append(f"{'.'.join(map(str, field_path))}: {error_msg}")
                
                self.log_result(
                    "Order Creation - POST /api/orders", 
                    False, 
                    "422 Validation Error - Missing required fields identified",
                    f"Missing fields: {missing_fields}"
                )
                
            else:
                self.log_result(
                    "Order Creation - POST /api/orders", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Order Creation Issues", False, f"Error: {str(e)}")
    
    def test_order_retrieval(self, order_id, order_number):
        """Test order retrieval endpoints"""
        print("\n=== ORDER RETRIEVAL TESTING ===")
        
        try:
            # Test GET /api/orders/{order_id}
            response = self.session.get(f"{API_BASE}/orders/{order_id}")
            
            if response.status_code == 200:
                order = response.json()
                self.log_result(
                    "Order Retrieval - GET /api/orders/{order_id}", 
                    True, 
                    f"Successfully retrieved order: {order.get('order_number')}",
                    f"Client: {order.get('client_name')}, Total: ${order.get('total_amount')}"
                )
                
                # Verify order contains all expected fields
                required_fields = ['id', 'order_number', 'client_id', 'client_name', 'items', 'total_amount', 'priority']
                missing_fields = [field for field in required_fields if field not in order]
                
                if not missing_fields:
                    self.log_result(
                        "Order Retrieval - Required Fields", 
                        True, 
                        "All required fields present in order response"
                    )
                else:
                    self.log_result(
                        "Order Retrieval - Required Fields", 
                        False, 
                        f"Missing required fields: {missing_fields}"
                    )
                
            else:
                self.log_result(
                    "Order Retrieval - GET /api/orders/{order_id}", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Order Retrieval", False, f"Error: {str(e)}")
    
    def test_product_specifications_integration(self):
        """Test GET /api/product-specifications and verify material_layers data"""
        print("\n=== PRODUCT SPECIFICATIONS INTEGRATION TESTING ===")
        
        try:
            response = self.session.get(f"{API_BASE}/product-specifications")
            
            if response.status_code == 200:
                specs = response.json()
                self.log_result(
                    "Product Specifications - GET /api/product-specifications", 
                    True, 
                    f"Successfully retrieved {len(specs)} product specifications"
                )
                
                # Check for material_layers data for slitting integration
                specs_with_material_layers = 0
                spiral_core_specs = 0
                
                for spec in specs:
                    if spec.get('product_type') == 'Spiral Paper Core':
                        spiral_core_specs += 1
                    
                    material_layers = spec.get('material_layers', [])
                    if material_layers:
                        specs_with_material_layers += 1
                        
                        # Verify material layer structure
                        first_layer = material_layers[0]
                        required_layer_fields = ['material_id', 'layer_type', 'thickness']
                        missing_layer_fields = [field for field in required_layer_fields if field not in first_layer]
                        
                        if not missing_layer_fields:
                            self.log_result(
                                f"Material Layers - {spec.get('product_name')}", 
                                True, 
                                f"Material layers have required structure ({len(material_layers)} layers)"
                            )
                        else:
                            self.log_result(
                                f"Material Layers - {spec.get('product_name')}", 
                                False, 
                                f"Material layers missing fields: {missing_layer_fields}"
                            )
                
                self.log_result(
                    "Product Specifications - Material Layers Integration", 
                    True, 
                    f"{specs_with_material_layers}/{len(specs)} specifications have material_layers data",
                    f"Spiral Paper Core specs: {spiral_core_specs}"
                )
                
                # Test specific product specification retrieval
                if specs:
                    first_spec = specs[0]
                    spec_id = first_spec['id']
                    self.test_individual_product_specification(spec_id, first_spec.get('product_name'))
                
            else:
                self.log_result(
                    "Product Specifications - GET /api/product-specifications", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Product Specifications Integration", False, f"Error: {str(e)}")
    
    def test_individual_product_specification(self, spec_id, product_name):
        """Test individual product specification retrieval"""
        try:
            response = self.session.get(f"{API_BASE}/product-specifications/{spec_id}")
            
            if response.status_code == 200:
                spec = response.json()
                self.log_result(
                    f"Individual Product Spec - {product_name}", 
                    True, 
                    "Successfully retrieved product specification details",
                    f"Type: {spec.get('product_type')}, Material Layers: {len(spec.get('material_layers', []))}"
                )
            else:
                self.log_result(
                    f"Individual Product Spec - {product_name}", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result(f"Individual Product Specification - {product_name}", False, f"Error: {str(e)}")
    
    def test_system_stability_verification(self):
        """Test all core endpoints for system stability"""
        print("\n=== SYSTEM STABILITY VERIFICATION ===")
        
        core_endpoints = [
            ("/clients", "Clients"),
            ("/materials", "Materials"), 
            ("/product-specifications", "Product Specifications"),
            ("/production/board", "Production Board"),
            ("/invoicing/live-jobs", "Live Jobs"),
            ("/xero/status", "Xero Integration Status")
        ]
        
        for endpoint, name in core_endpoints:
            try:
                response = self.session.get(f"{API_BASE}{endpoint}")
                
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list):
                        count = len(data)
                    elif isinstance(data, dict):
                        count = len(data.get('data', data))
                    else:
                        count = "N/A"
                    
                    self.log_result(
                        f"System Stability - {name}", 
                        True, 
                        f"Endpoint accessible, returned {count} items"
                    )
                elif response.status_code == 403:
                    self.log_result(
                        f"System Stability - {name}", 
                        True, 
                        "Endpoint accessible but requires higher permissions (expected)"
                    )
                else:
                    self.log_result(
                        f"System Stability - {name}", 
                        False, 
                        f"Failed with status {response.status_code}",
                        response.text[:200] if response.text else "No response body"
                    )
                    
            except Exception as e:
                self.log_result(f"System Stability - {name}", False, f"Error: {str(e)}")

    def print_test_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "="*60)
        print("ORDER CREATION ISSUES INVESTIGATION SUMMARY")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS ({failed_tests}):")
            for result in self.test_results:
                if not result['success']:
                    print(f"  • {result['test']}: {result['message']}")
                    if result.get('details'):
                        print(f"    Details: {result['details']}")
        
        print(f"\n✅ PASSED TESTS ({passed_tests}):")
        for result in self.test_results:
            if result['success']:
                print(f"  • {result['test']}: {result['message']}")
        
        print("\n" + "="*60)
        
        # Analyze specific issues
        print("CRITICAL FINDINGS:")
        print("="*60)
        
        order_creation_failures = [r for r in self.test_results if not r['success'] and 'order creation' in r['test'].lower()]
        if order_creation_failures:
            print("🚨 ORDER CREATION ISSUES IDENTIFIED:")
            for failure in order_creation_failures:
                print(f"  ❌ {failure['message']}")
                if failure.get('details'):
                    print(f"     Root Cause: {failure['details']}")
        
        validation_errors = [r for r in self.test_results if '422' in str(r.get('details', ''))]
        if validation_errors:
            print("\n🔍 VALIDATION ERRORS ANALYSIS:")
            for error in validation_errors:
                print(f"  • {error['test']}")
                if 'product_id' in str(error.get('details', '')):
                    print("    - Missing product_id field in items")
                if 'material_type' in str(error.get('details', '')):
                    print("    - Missing material_type field in specifications")
                if 'dimensions' in str(error.get('details', '')):
                    print("    - Missing dimensions field in specifications")
        
        print("\n" + "="*60)

    def run_investigation(self):
        """Run comprehensive order creation and API validation tests"""
        print("\n" + "="*60)
        print("ORDER CREATION ISSUES INVESTIGATION")
        print("Focus on 63.2% test results - identifying specific API failures")
        print("="*60)
        
        # Step 1: Authenticate
        if not self.authenticate():
            print("❌ Authentication failed - cannot proceed with tests")
            return
        
        # Step 2: Test existing orders
        self.test_existing_orders()
        
        # Step 3: Test order creation with complete data
        self.test_order_creation_issues()
        
        # Step 4: Test product specifications integration
        self.test_product_specifications_integration()
        
        # Step 5: Test system stability
        self.test_system_stability_verification()
        
        # Print summary
        self.print_test_summary()

if __name__ == "__main__":
    tester = OrderInvestigationTester()
    tester.run_investigation()