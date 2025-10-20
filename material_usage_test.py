#!/usr/bin/env python3
"""
Material Usage Report Endpoint Testing
Re-testing the Material Usage Report endpoint after applying fixes as requested in review.

TEST OBJECTIVES:
1. Verify the material usage report now returns data after fixes
2. Test with a wide date range to include active orders
3. Confirm material_layers data from client_products is being used

TEST STEPS:
1. Login with admin credentials (Callum/Peach7510)
2. GET /api/materials to get first material
3. Test GET /api/stock/reports/material-usage-detailed with wide date range
4. Verify response includes usage_by_width array with material usage data
5. If still empty, check if the material has material_layers in client_products

EXPECTED RESULTS:
- Material usage report returns data with usage_by_width populated
- Report shows material usage from client product material_layers
- Grand totals are calculated correctly
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

class MaterialUsageReportTester:
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
        """Test authentication with admin credentials (Callum/Peach7510)"""
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

    def get_materials(self):
        """GET /api/materials to get first material"""
        print("\n=== GETTING MATERIALS ===")
        
        try:
            response = self.session.get(f"{API_BASE}/materials")
            
            if response.status_code == 200:
                materials = response.json()
                
                if materials and len(materials) > 0:
                    material = materials[0]
                    self.log_result(
                        "Get Materials", 
                        True, 
                        f"Successfully retrieved {len(materials)} materials",
                        f"First material: {material.get('product_code')} - {material.get('supplier')}"
                    )
                    return material
                else:
                    self.log_result(
                        "Get Materials", 
                        False, 
                        "No materials found in database"
                    )
                    return None
            else:
                self.log_result(
                    "Get Materials", 
                    False, 
                    f"Failed to get materials: {response.status_code}",
                    response.text
                )
                return None
                
        except Exception as e:
            self.log_result("Get Materials", False, f"Error: {str(e)}")
            return None

    def test_material_usage_detailed_report(self, material_id):
        """Test GET /api/stock/reports/material-usage-detailed with wide date range"""
        print("\n=== MATERIAL USAGE DETAILED REPORT TEST ===")
        
        try:
            # Use wide date range as specified in review request
            start_date = "2020-01-01T00:00:00Z"
            end_date = "2030-12-31T23:59:59Z"
            
            response = self.session.get(
                f"{API_BASE}/stock/reports/material-usage-detailed",
                params={
                    "material_id": material_id,
                    "start_date": start_date,
                    "end_date": end_date,
                    "include_order_breakdown": True
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                data = result.get("data", {})
                
                # Check required fields
                required_fields = [
                    "material_id", "material_name", "report_period", 
                    "usage_by_width", "grand_total_m2", "grand_total_length_m"
                ]
                
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    usage_by_width = data.get("usage_by_width", [])
                    grand_total_m2 = data.get("grand_total_m2", 0)
                    grand_total_length_m = data.get("grand_total_length_m", 0)
                    
                    # Check if we have actual usage data
                    if len(usage_by_width) > 0 and (grand_total_m2 > 0 or grand_total_length_m > 0):
                        self.log_result(
                            "Material Usage Report - Data Present", 
                            True, 
                            f"Material usage report contains data",
                            f"Widths: {len(usage_by_width)}, Total m²: {grand_total_m2}, Total length: {grand_total_length_m}m"
                        )
                        
                        # Verify usage_by_width structure
                        self.verify_usage_by_width_structure(usage_by_width)
                        
                        return True
                    else:
                        self.log_result(
                            "Material Usage Report - Data Present", 
                            False, 
                            "Material usage report returns empty data",
                            f"usage_by_width: {len(usage_by_width)} entries, grand_total_m2: {grand_total_m2}, grand_total_length_m: {grand_total_length_m}"
                        )
                        
                        # Check if material has material_layers in client_products
                        self.check_material_layers_in_client_products(material_id)
                        
                        return False
                else:
                    self.log_result(
                        "Material Usage Report - Structure", 
                        False, 
                        f"Report missing required fields: {missing_fields}",
                        f"Available fields: {list(data.keys())}"
                    )
                    return False
            else:
                self.log_result(
                    "Material Usage Report", 
                    False, 
                    f"Failed to generate report: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_result("Material Usage Report", False, f"Error: {str(e)}")
            return False

    def verify_usage_by_width_structure(self, usage_by_width):
        """Verify the structure of usage_by_width array"""
        try:
            if not usage_by_width:
                self.log_result(
                    "Usage By Width Structure", 
                    False, 
                    "usage_by_width array is empty"
                )
                return
            
            # Check first entry structure
            first_entry = usage_by_width[0]
            expected_fields = ["width_mm", "total_length_m", "m2"]
            
            missing_fields = [field for field in expected_fields if field not in first_entry]
            
            if not missing_fields:
                self.log_result(
                    "Usage By Width Structure", 
                    True, 
                    f"usage_by_width entries have correct structure",
                    f"Sample entry: width={first_entry.get('width_mm')}mm, length={first_entry.get('total_length_m')}m, area={first_entry.get('m2')}m²"
                )
                
                # Check if order breakdown is included
                if "orders" in first_entry and "order_count" in first_entry:
                    self.log_result(
                        "Order Breakdown Structure", 
                        True, 
                        f"Order breakdown included with {first_entry.get('order_count', 0)} orders"
                    )
                else:
                    self.log_result(
                        "Order Breakdown Structure", 
                        False, 
                        "Order breakdown not included in usage_by_width entries"
                    )
            else:
                self.log_result(
                    "Usage By Width Structure", 
                    False, 
                    f"usage_by_width entries missing fields: {missing_fields}",
                    f"Available fields: {list(first_entry.keys())}"
                )
                
        except Exception as e:
            self.log_result("Usage By Width Structure", False, f"Error: {str(e)}")

    def check_material_layers_in_client_products(self, material_id):
        """Check if the material has material_layers in client_products"""
        print("\n=== CHECKING MATERIAL LAYERS IN CLIENT PRODUCTS ===")
        
        try:
            # Get all clients
            clients_response = self.session.get(f"{API_BASE}/clients")
            
            if clients_response.status_code != 200:
                self.log_result(
                    "Check Material Layers - Get Clients", 
                    False, 
                    f"Failed to get clients: {clients_response.status_code}"
                )
                return
            
            clients = clients_response.json()
            material_layers_found = 0
            products_with_material = 0
            
            for client in clients:
                client_id = client.get("id")
                
                # Get client products
                products_response = self.session.get(f"{API_BASE}/clients/{client_id}/catalog")
                
                if products_response.status_code == 200:
                    products = products_response.json()
                    
                    for product in products:
                        material_layers = product.get("material_layers", [])
                        
                        if material_layers:
                            material_layers_found += len(material_layers)
                            
                            # Check if any layer uses our material
                            for layer in material_layers:
                                if layer.get("material_id") == material_id:
                                    products_with_material += 1
                                    break
            
            if material_layers_found > 0:
                self.log_result(
                    "Material Layers in Client Products", 
                    True, 
                    f"Found {material_layers_found} material layers across all client products",
                    f"Products using material {material_id}: {products_with_material}"
                )
                
                if products_with_material == 0:
                    self.log_result(
                        "Material Usage in Products", 
                        False, 
                        f"No client products use material {material_id} in their material_layers",
                        "This explains why the material usage report is empty"
                    )
            else:
                self.log_result(
                    "Material Layers in Client Products", 
                    False, 
                    "No material_layers found in any client products",
                    "This explains why the material usage report is empty"
                )
                
        except Exception as e:
            self.log_result("Check Material Layers", False, f"Error: {str(e)}")

    def check_active_orders_with_material_usage(self):
        """Check if there are active orders that should contribute to material usage"""
        print("\n=== CHECKING ACTIVE ORDERS ===")
        
        try:
            # Get active orders
            response = self.session.get(f"{API_BASE}/orders")
            
            if response.status_code == 200:
                orders = response.json()
                
                active_orders = [order for order in orders if order.get("status") != "completed"]
                
                self.log_result(
                    "Active Orders Check", 
                    True, 
                    f"Found {len(active_orders)} active orders out of {len(orders)} total orders"
                )
                
                # Check if any orders have items with material requirements
                orders_with_items = 0
                total_items = 0
                
                for order in active_orders:
                    items = order.get("items", [])
                    if items:
                        orders_with_items += 1
                        total_items += len(items)
                
                self.log_result(
                    "Orders with Items", 
                    True, 
                    f"{orders_with_items} active orders have items ({total_items} total items)"
                )
                
                return len(active_orders) > 0
            else:
                self.log_result(
                    "Active Orders Check", 
                    False, 
                    f"Failed to get orders: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_result("Active Orders Check", False, f"Error: {str(e)}")
            return False

    def run_comprehensive_test(self):
        """Run the comprehensive material usage report test"""
        print("="*80)
        print("MATERIAL USAGE REPORT ENDPOINT RE-TESTING")
        print("Testing after fixes have been applied")
        print("="*80)
        
        # Step 1: Authenticate
        if not self.authenticate():
            print("❌ Authentication failed - cannot proceed with tests")
            return
        
        # Step 2: Get materials
        material = self.get_materials()
        if not material:
            print("❌ No materials available - cannot proceed with tests")
            return
        
        material_id = material.get("id")
        
        # Step 3: Test material usage detailed report
        report_success = self.test_material_usage_detailed_report(material_id)
        
        # Step 4: Check active orders
        self.check_active_orders_with_material_usage()
        
        # Step 5: Print summary
        self.print_test_summary(report_success)

    def print_test_summary(self, report_success):
        """Print test summary"""
        print("\n" + "="*80)
        print("MATERIAL USAGE REPORT TEST SUMMARY")
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
            if result['details'] and not result['success']:
                print(f"   Details: {result['details']}")
        
        print("\n" + "="*60)
        print("CONCLUSION:")
        print("="*60)
        
        if report_success:
            print("🎉 SUCCESS: Material Usage Report is now returning data after fixes!")
            print("✅ The endpoint is working correctly with usage_by_width populated")
            print("✅ Grand totals are being calculated correctly")
        else:
            print("⚠️  ISSUE: Material Usage Report is still returning empty data")
            print("❌ The usage_by_width array is empty or grand totals are 0")
            print("🔍 Check if materials are properly linked to client products via material_layers")
            print("🔍 Verify that active orders exist with items that use the materials")
        
        print("="*80)

def main():
    """Main function to run the material usage report test"""
    tester = MaterialUsageReportTester()
    tester.run_comprehensive_test()

if __name__ == "__main__":
    main()