#!/usr/bin/env python3
"""
Material Usage Report Endpoint Testing Suite
Testing the Material Usage Report endpoint to identify why it returns no data.

PRIORITY TESTS:
1. Login with admin credentials (Callum/Peach7510)
2. GET /api/materials to list all available materials
3. Select the first material and note its ID
4. GET /api/orders to see what orders exist and their statuses
5. Check if any orders have associated job_specifications
6. Test GET /api/stock/reports/material-usage-detailed with:
   - material_id from step 3
   - start_date: "2020-01-01T00:00:00Z" (wide date range)
   - end_date: "2030-12-31T23:59:59Z"
   - include_order_breakdown: true
7. Analyze why the report returns empty results
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
        self.materials = []
        self.orders = []
        self.selected_material = None
        
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
        print("\n=== STEP 1: AUTHENTICATION TEST ===")
        
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
        """Step 2: GET /api/materials to list all available materials"""
        print("\n=== STEP 2: GET AVAILABLE MATERIALS ===")
        
        try:
            response = self.session.get(f"{API_BASE}/materials")
            
            if response.status_code == 200:
                self.materials = response.json()
                
                if self.materials and len(self.materials) > 0:
                    self.log_result(
                        "Get Materials", 
                        True, 
                        f"Found {len(self.materials)} materials available"
                    )
                    
                    # Display first few materials for reference
                    print("\nFirst 3 materials found:")
                    for i, material in enumerate(self.materials[:3]):
                        print(f"  {i+1}. ID: {material.get('id')}, Code: {material.get('product_code')}, Supplier: {material.get('supplier')}")
                    
                    return True
                else:
                    self.log_result(
                        "Get Materials", 
                        False, 
                        "No materials found in database"
                    )
                    return False
            else:
                self.log_result(
                    "Get Materials", 
                    False, 
                    f"Failed to get materials: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_result("Get Materials", False, f"Error: {str(e)}")
            return False

    def select_material(self):
        """Step 3: Select the first material and note its ID"""
        print("\n=== STEP 3: SELECT MATERIAL FOR TESTING ===")
        
        if not self.materials:
            self.log_result(
                "Select Material", 
                False, 
                "No materials available to select"
            )
            return False
        
        self.selected_material = self.materials[0]
        material_id = self.selected_material.get('id')
        material_code = self.selected_material.get('product_code')
        supplier = self.selected_material.get('supplier')
        
        self.log_result(
            "Select Material", 
            True, 
            f"Selected material: {supplier} - {material_code} (ID: {material_id})"
        )
        
        print(f"Selected Material Details:")
        print(f"  ID: {material_id}")
        print(f"  Code: {material_code}")
        print(f"  Supplier: {supplier}")
        print(f"  GSM: {self.selected_material.get('gsm', 'N/A')}")
        print(f"  Thickness: {self.selected_material.get('thickness_mm', 'N/A')} mm")
        print(f"  Unit: {self.selected_material.get('unit', 'N/A')}")
        
        return True

    def get_orders(self):
        """Step 4: GET /api/orders to see what orders exist and their statuses"""
        print("\n=== STEP 4: GET ORDERS AND ANALYZE STATUSES ===")
        
        try:
            response = self.session.get(f"{API_BASE}/orders")
            
            if response.status_code == 200:
                self.orders = response.json()
                
                if self.orders and len(self.orders) > 0:
                    self.log_result(
                        "Get Orders", 
                        True, 
                        f"Found {len(self.orders)} orders in database"
                    )
                    
                    # Analyze order statuses
                    status_counts = {}
                    for order in self.orders:
                        status = order.get('status', 'unknown')
                        status_counts[status] = status_counts.get(status, 0) + 1
                    
                    print(f"\nOrder Status Breakdown:")
                    for status, count in status_counts.items():
                        print(f"  {status}: {count} orders")
                    
                    # Show first few orders
                    print(f"\nFirst 3 orders:")
                    for i, order in enumerate(self.orders[:3]):
                        print(f"  {i+1}. Order: {order.get('order_number')}, Status: {order.get('status')}, Client: {order.get('client_name')}")
                        print(f"      Created: {order.get('created_at')}, Items: {len(order.get('items', []))}")
                    
                    return True
                else:
                    self.log_result(
                        "Get Orders", 
                        False, 
                        "No orders found in database"
                    )
                    return False
            else:
                self.log_result(
                    "Get Orders", 
                    False, 
                    f"Failed to get orders: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_result("Get Orders", False, f"Error: {str(e)}")
            return False

    def check_job_specifications(self):
        """Step 5: Check if any orders have associated job_specifications"""
        print("\n=== STEP 5: CHECK JOB SPECIFICATIONS AND MATERIALS COMPOSITION ===")
        
        # Check if there's a job_specifications collection or materials_composition in orders
        try:
            # First, check if orders have materials_composition or job_specifications
            orders_with_materials = []
            orders_with_job_specs = []
            
            for order in self.orders:
                if order.get('materials_composition'):
                    orders_with_materials.append(order)
                if order.get('job_specifications'):
                    orders_with_job_specs.append(order)
            
            self.log_result(
                "Check Materials Composition in Orders", 
                len(orders_with_materials) > 0, 
                f"Found {len(orders_with_materials)} orders with materials_composition data"
            )
            
            self.log_result(
                "Check Job Specifications in Orders", 
                len(orders_with_job_specs) > 0, 
                f"Found {len(orders_with_job_specs)} orders with job_specifications data"
            )
            
            # Try to access job_specifications collection directly
            try:
                # This might not exist as an endpoint, but let's try
                response = self.session.get(f"{API_BASE}/job-specifications")
                
                if response.status_code == 200:
                    job_specs = response.json()
                    self.log_result(
                        "Get Job Specifications Collection", 
                        True, 
                        f"Found {len(job_specs)} job specifications in collection"
                    )
                elif response.status_code == 404:
                    self.log_result(
                        "Get Job Specifications Collection", 
                        False, 
                        "Job specifications endpoint not found (404)"
                    )
                else:
                    self.log_result(
                        "Get Job Specifications Collection", 
                        False, 
                        f"Job specifications endpoint returned {response.status_code}"
                    )
            except Exception as e:
                self.log_result("Get Job Specifications Collection", False, f"Error: {str(e)}")
            
            # Check client products for materials_composition
            try:
                # Get clients first
                clients_response = self.session.get(f"{API_BASE}/clients")
                if clients_response.status_code == 200:
                    clients = clients_response.json()
                    
                    products_with_materials = 0
                    total_products = 0
                    
                    for client in clients[:3]:  # Check first 3 clients
                        client_id = client.get('id')
                        products_response = self.session.get(f"{API_BASE}/clients/{client_id}/catalog")
                        
                        if products_response.status_code == 200:
                            products = products_response.json()
                            total_products += len(products)
                            
                            for product in products:
                                if product.get('materials_composition') or product.get('material_layers'):
                                    products_with_materials += 1
                    
                    self.log_result(
                        "Check Client Products Materials Composition", 
                        products_with_materials > 0, 
                        f"Found {products_with_materials}/{total_products} client products with materials data"
                    )
                    
            except Exception as e:
                self.log_result("Check Client Products Materials Composition", False, f"Error: {str(e)}")
            
            return True
            
        except Exception as e:
            self.log_result("Check Job Specifications", False, f"Error: {str(e)}")
            return False

    def test_material_usage_report(self):
        """Step 6: Test GET /api/stock/reports/material-usage-detailed endpoint"""
        print("\n=== STEP 6: TEST MATERIAL USAGE REPORT ENDPOINT ===")
        
        if not self.selected_material:
            self.log_result(
                "Material Usage Report Test", 
                False, 
                "No material selected for testing"
            )
            return False
        
        material_id = self.selected_material.get('id')
        
        # Test with wide date range as specified
        start_date = "2020-01-01T00:00:00Z"
        end_date = "2030-12-31T23:59:59Z"
        
        try:
            print(f"Testing with material_id: {material_id}")
            print(f"Date range: {start_date} to {end_date}")
            print(f"Include order breakdown: true")
            
            response = self.session.get(
                f"{API_BASE}/stock/reports/material-usage-detailed",
                params={
                    "material_id": material_id,
                    "start_date": start_date,
                    "end_date": end_date,
                    "include_order_breakdown": True
                }
            )
            
            print(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                data = result.get("data", {})
                
                # Analyze the response
                print(f"\nResponse structure analysis:")
                print(f"  Success: {result.get('success')}")
                print(f"  Data keys: {list(data.keys()) if data else 'No data'}")
                
                if data:
                    print(f"  Material ID: {data.get('material_id')}")
                    print(f"  Material Name: {data.get('material_name')}")
                    print(f"  Total Widths Used: {data.get('total_widths_used', 0)}")
                    print(f"  Grand Total m²: {data.get('grand_total_m2', 0)}")
                    print(f"  Usage by Width entries: {len(data.get('usage_by_width', []))}")
                
                # Check if report returns empty results
                usage_by_width = data.get('usage_by_width', [])
                total_widths = data.get('total_widths_used', 0)
                grand_total_m2 = data.get('grand_total_m2', 0)
                
                if len(usage_by_width) == 0 and total_widths == 0 and grand_total_m2 == 0:
                    self.log_result(
                        "Material Usage Report - Empty Results", 
                        False, 
                        "Report returns empty results - this is the issue we need to investigate"
                    )
                    
                    # This is the main issue - let's analyze why
                    self.analyze_empty_results(material_id, start_date, end_date)
                    
                else:
                    self.log_result(
                        "Material Usage Report - Has Data", 
                        True, 
                        f"Report contains data: {total_widths} widths, {grand_total_m2} m² total"
                    )
                
                return True
                
            elif response.status_code == 404:
                self.log_result(
                    "Material Usage Report Test", 
                    False, 
                    "Material not found (404) - this could be the issue",
                    f"Material ID {material_id} not found in system"
                )
                return False
                
            else:
                self.log_result(
                    "Material Usage Report Test", 
                    False, 
                    f"Report endpoint failed with status {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_result("Material Usage Report Test", False, f"Error: {str(e)}")
            return False

    def analyze_empty_results(self, material_id, start_date, end_date):
        """Step 7: Analyze why the report returns empty results"""
        print("\n=== STEP 7: ANALYZE WHY REPORT RETURNS EMPTY RESULTS ===")
        
        # Check 1: Does the material exist in raw_materials collection?
        self.check_raw_materials_collection(material_id)
        
        # Check 2: Are there any stock movements for this material?
        self.check_stock_movements(material_id)
        
        # Check 3: Check order items for material usage
        self.check_order_items_for_material(material_id)
        
        # Check 4: Check if there are any job specifications with this material
        self.check_job_specs_for_material(material_id)
        
        # Check 5: Check date filtering issues
        self.check_date_filtering_issues(start_date, end_date)
        
        # Check 6: Check status filtering
        self.check_status_filtering()

    def check_raw_materials_collection(self, material_id):
        """Check if material exists in raw_materials collection"""
        try:
            response = self.session.get(f"{API_BASE}/stock/raw-materials")
            
            if response.status_code == 200:
                result = response.json()
                raw_materials = result.get("data", []) if isinstance(result, dict) else result
                
                # Look for our material
                found_material = None
                for raw_mat in raw_materials:
                    if raw_mat.get('material_id') == material_id or raw_mat.get('id') == material_id:
                        found_material = raw_mat
                        break
                
                if found_material:
                    self.log_result(
                        "Check Raw Materials Collection", 
                        True, 
                        f"Material found in raw_materials collection",
                        f"Raw material: {found_material.get('material_name')}, Quantity: {found_material.get('quantity_on_hand')}"
                    )
                else:
                    self.log_result(
                        "Check Raw Materials Collection", 
                        False, 
                        f"Material ID {material_id} NOT found in raw_materials collection",
                        f"This could be why the report returns no data. Found {len(raw_materials)} raw materials total."
                    )
                    
                    # Show what raw materials do exist
                    if raw_materials:
                        print("Available raw materials:")
                        for i, rm in enumerate(raw_materials[:5]):
                            print(f"  {i+1}. ID: {rm.get('id')}, Material ID: {rm.get('material_id')}, Name: {rm.get('material_name')}")
            else:
                self.log_result(
                    "Check Raw Materials Collection", 
                    False, 
                    f"Failed to get raw materials: {response.status_code}"
                )
                
        except Exception as e:
            self.log_result("Check Raw Materials Collection", False, f"Error: {str(e)}")

    def check_stock_movements(self, material_id):
        """Check if there are stock movements for this material"""
        try:
            # Try to get stock movements (this endpoint might not exist)
            response = self.session.get(f"{API_BASE}/stock/movements")
            
            if response.status_code == 200:
                movements = response.json()
                
                # Look for movements with our material
                material_movements = []
                for movement in movements:
                    if movement.get('material_id') == material_id:
                        material_movements.append(movement)
                
                self.log_result(
                    "Check Stock Movements", 
                    len(material_movements) > 0, 
                    f"Found {len(material_movements)} stock movements for material {material_id}"
                )
                
            elif response.status_code == 404:
                self.log_result(
                    "Check Stock Movements", 
                    False, 
                    "Stock movements endpoint not found (404)"
                )
            else:
                self.log_result(
                    "Check Stock Movements", 
                    False, 
                    f"Stock movements endpoint returned {response.status_code}"
                )
                
        except Exception as e:
            self.log_result("Check Stock Movements", False, f"Error: {str(e)}")

    def check_order_items_for_material(self, material_id):
        """Check if any order items reference this material"""
        material_usage_count = 0
        orders_with_material = []
        
        for order in self.orders:
            items = order.get('items', [])
            for item in items:
                # Check if item has material references
                if (item.get('material_id') == material_id or 
                    item.get('product_id') == material_id):
                    material_usage_count += 1
                    orders_with_material.append(order.get('order_number'))
        
        self.log_result(
            "Check Order Items for Material", 
            material_usage_count > 0, 
            f"Found {material_usage_count} order items referencing material {material_id}",
            f"Orders: {orders_with_material[:5]}" if orders_with_material else "No orders found"
        )

    def check_job_specs_for_material(self, material_id):
        """Check if job specifications reference this material"""
        # This is speculative since we don't know the exact structure
        self.log_result(
            "Check Job Specifications for Material", 
            False, 
            "Cannot check job specifications - endpoint structure unknown",
            "The report might depend on job_specifications collection having materials_composition data"
        )

    def check_date_filtering_issues(self, start_date, end_date):
        """Check for potential date filtering issues"""
        # Check if orders fall within date range
        orders_in_range = 0
        
        for order in self.orders:
            created_at = order.get('created_at')
            if created_at:
                try:
                    # Parse the date (might be string or datetime)
                    if isinstance(created_at, str):
                        order_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    else:
                        order_date = created_at
                    
                    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                    
                    if start_dt <= order_date <= end_dt:
                        orders_in_range += 1
                        
                except Exception:
                    pass  # Skip date parsing errors
        
        self.log_result(
            "Check Date Filtering", 
            orders_in_range > 0, 
            f"Found {orders_in_range}/{len(self.orders)} orders within date range {start_date} to {end_date}",
            "Date format mismatch could cause filtering issues"
        )

    def check_status_filtering(self):
        """Check if status filtering is too restrictive"""
        # Analyze order statuses
        status_counts = {}
        for order in self.orders:
            status = order.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Check if report only looks for completed/archived orders
        completed_orders = status_counts.get('completed', 0)
        archived_orders = status_counts.get('archived', 0)
        active_orders = status_counts.get('active', 0)
        
        self.log_result(
            "Check Status Filtering", 
            completed_orders > 0 or archived_orders > 0, 
            f"Status analysis: {completed_orders} completed, {archived_orders} archived, {active_orders} active",
            "Report might only include completed/archived orders, excluding active orders"
        )

    def provide_recommendations(self):
        """Provide recommendations for fixing the issue"""
        print("\n=== RECOMMENDATIONS FOR FIXING THE ISSUE ===")
        
        failed_tests = [r for r in self.test_results if not r['success']]
        
        print("\nBased on the test results, here are the likely causes and solutions:")
        
        # Analyze failed tests to provide specific recommendations
        raw_materials_issue = any("Raw Materials Collection" in test['test'] and not test['success'] for test in self.test_results)
        empty_results_issue = any("Empty Results" in test['test'] and not test['success'] for test in self.test_results)
        
        if raw_materials_issue:
            print("\n🔍 ISSUE 1: Material not found in raw_materials collection")
            print("   SOLUTION: The endpoint looks for materials in raw_materials collection,")
            print("   but the material exists only in materials collection.")
            print("   Fix: Update endpoint to look in materials collection OR create raw_materials entries.")
        
        if empty_results_issue:
            print("\n🔍 ISSUE 2: Report returns empty results")
            print("   POSSIBLE CAUSES:")
            print("   - Status filtering too restrictive (only completed/archived orders)")
            print("   - Date format mismatch in MongoDB queries")
            print("   - Missing materials_composition data in job_specifications")
            print("   - No stock movements recorded for the material")
            
        print("\n🛠️  RECOMMENDED FIXES:")
        print("1. Update status filter to include active orders")
        print("2. Fix date format in MongoDB queries (use datetime objects, not ISO strings)")
        print("3. Ensure job_specifications have materials_composition data")
        print("4. Create raw_materials entries for materials in the materials collection")
        print("5. Verify stock movements are being recorded properly")

    def run_comprehensive_test(self):
        """Run the complete test suite"""
        print("="*80)
        print("MATERIAL USAGE REPORT ENDPOINT COMPREHENSIVE TESTING")
        print("Testing why GET /api/stock/reports/material-usage-detailed returns no data")
        print("="*80)
        
        # Step 1: Authentication
        if not self.authenticate():
            print("❌ Authentication failed - cannot continue testing")
            return
        
        # Step 2: Get materials
        if not self.get_materials():
            print("❌ No materials found - cannot continue testing")
            return
        
        # Step 3: Select material
        if not self.select_material():
            print("❌ Could not select material - cannot continue testing")
            return
        
        # Step 4: Get orders
        if not self.get_orders():
            print("❌ No orders found - this might be part of the issue")
        
        # Step 5: Check job specifications
        self.check_job_specifications()
        
        # Step 6: Test the material usage report
        self.test_material_usage_report()
        
        # Step 7: Provide recommendations
        self.provide_recommendations()
        
        # Print final summary
        self.print_test_summary()

    def print_test_summary(self):
        """Print comprehensive test summary"""
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
        
        # Show failed tests details
        failed_results = [r for r in self.test_results if not r['success']]
        if failed_results:
            print("\n" + "="*60)
            print("FAILED TESTS (ISSUES IDENTIFIED):")
            print("="*60)
            for result in failed_results:
                print(f"\n❌ {result['test']}")
                print(f"   Issue: {result['message']}")
                if result['details']:
                    print(f"   Details: {result['details']}")
        
        print("\n" + "="*80)
        if failed_tests == 0:
            print("🎉 ALL TESTS PASSED - No issues found!")
        else:
            print(f"⚠️  {failed_tests} ISSUES IDENTIFIED - See recommendations above")
        print("="*80)

def main():
    """Main function to run the material usage report test"""
    tester = MaterialUsageReportTester()
    tester.run_comprehensive_test()

if __name__ == "__main__":
    main()