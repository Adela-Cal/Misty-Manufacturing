#!/usr/bin/env python3
"""
Test the FIXED Consumable Usage Report endpoint
Testing GET /api/stock/reports/product-usage-detailed

SPECIFIC TEST REQUIREMENTS FROM REVIEW REQUEST:
1. Call GET /api/stock/reports/product-usage-detailed with default date range
2. Verify it now returns data with products
3. Check that it includes orders with "active" status (orders on hand)
4. Verify product type exclusions work correctly (should exclude Spiral Paper Cores and Composite Cores)

Expected Results After Fix:
- Should return products from orders
- Should include active orders (orders on hand)
- Should show usage by width
- Should calculate m² correctly
- Should exclude Spiral Paper Cores and Composite Cores
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

class FixedConsumableUsageReportTester:
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
        if details:
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

    def test_fixed_endpoint_default_range(self):
        """Test 1: Call GET /api/stock/reports/product-usage-detailed with default date range"""
        print("\n=== TEST 1: FIXED ENDPOINT WITH DEFAULT DATE RANGE ===")
        
        try:
            response = self.session.get(f"{API_BASE}/stock/reports/product-usage-detailed")
            
            print(f"Response Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                data = result.get("data", {})
                
                # Check response structure
                required_fields = [
                    "report_period", "products", "total_products", 
                    "grand_total_m2", "grand_total_length_m", "excluded_types"
                ]
                
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    products = data.get("products", [])
                    total_products = data.get("total_products", 0)
                    excluded_types = data.get("excluded_types", [])
                    grand_total_m2 = data.get("grand_total_m2", 0)
                    
                    self.log_result(
                        "Fixed Endpoint - Default Range", 
                        True, 
                        f"Successfully generated report with {total_products} products",
                        f"Products: {len(products)}, Total m²: {grand_total_m2}, Excluded: {excluded_types}"
                    )
                    
                    return data
                else:
                    self.log_result(
                        "Fixed Endpoint - Default Range", 
                        False, 
                        f"Report missing required fields: {missing_fields}",
                        f"Available fields: {list(data.keys())}"
                    )
            else:
                self.log_result(
                    "Fixed Endpoint - Default Range", 
                    False, 
                    f"Failed to generate report: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Fixed Endpoint - Default Range", False, f"Error: {str(e)}")
        
        return None

    def test_active_orders_analysis(self):
        """Test 2: Analyze if active orders are being included"""
        print("\n=== TEST 2: ACTIVE ORDERS ANALYSIS ===")
        
        try:
            # Get all orders to check status distribution
            orders_response = self.session.get(f"{API_BASE}/orders")
            if orders_response.status_code != 200:
                self.log_result(
                    "Active Orders Analysis", 
                    False, 
                    "Failed to get orders for analysis"
                )
                return
            
            orders = orders_response.json()
            
            # Analyze order statuses
            status_counts = {}
            active_orders = []
            orders_with_items = 0
            
            for order in orders:
                status = order.get('status', 'unknown')
                status_counts[status] = status_counts.get(status, 0) + 1
                
                if status == 'active':
                    active_orders.append(order)
                
                if order.get('items', []):
                    orders_with_items += 1
            
            print(f"Order Status Distribution: {status_counts}")
            print(f"Active Orders: {len(active_orders)}")
            print(f"Orders with Items: {orders_with_items}")
            
            # Now test the endpoint with wide date range to capture all data
            response = self.session.get(
                f"{API_BASE}/stock/reports/product-usage-detailed",
                params={
                    "start_date": "2020-01-01T00:00:00Z",
                    "end_date": "2030-12-31T23:59:59Z"
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                data = result.get("data", {})
                products = data.get("products", [])
                
                if len(products) > 0:
                    self.log_result(
                        "Active Orders Analysis", 
                        True, 
                        f"Report includes {len(products)} products (active orders likely included)",
                        f"Active orders in DB: {len(active_orders)}, Products in report: {len(products)}"
                    )
                else:
                    if len(active_orders) > 0:
                        self.log_result(
                            "Active Orders Analysis", 
                            False, 
                            f"No products in report despite {len(active_orders)} active orders",
                            f"This suggests active orders are still not being included or products not found"
                        )
                    else:
                        self.log_result(
                            "Active Orders Analysis", 
                            True, 
                            "No active orders in database, empty report is correct"
                        )
            else:
                self.log_result(
                    "Active Orders Analysis", 
                    False, 
                    f"Failed to get report: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Active Orders Analysis", False, f"Error: {str(e)}")

    def test_product_type_exclusions(self):
        """Test 3: Verify product type exclusions work correctly"""
        print("\n=== TEST 3: PRODUCT TYPE EXCLUSIONS ===")
        
        try:
            response = self.session.get(
                f"{API_BASE}/stock/reports/product-usage-detailed",
                params={
                    "start_date": "2020-01-01T00:00:00Z",
                    "end_date": "2030-12-31T23:59:59Z"
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                data = result.get("data", {})
                
                excluded_types = data.get("excluded_types", [])
                expected_excluded = ["Spiral Paper Cores", "Composite Cores"]
                
                # Check that excluded types are properly configured
                if set(excluded_types) == set(expected_excluded):
                    self.log_result(
                        "Product Type Exclusions - Configuration", 
                        True, 
                        f"Excluded types correctly configured: {excluded_types}"
                    )
                else:
                    self.log_result(
                        "Product Type Exclusions - Configuration", 
                        False, 
                        f"Excluded types mismatch. Expected: {expected_excluded}, Got: {excluded_types}"
                    )
                
                # Check that no products in the report have excluded types
                products = data.get("products", [])
                excluded_products_found = []
                
                for product in products:
                    product_info = product.get("product_info", {})
                    product_type = product_info.get("product_type", "")
                    
                    if product_type in expected_excluded:
                        excluded_products_found.append({
                            "product_id": product_info.get("product_id"),
                            "product_type": product_type,
                            "description": product_info.get("product_description")
                        })
                
                if len(excluded_products_found) == 0:
                    self.log_result(
                        "Product Type Exclusions - Verification", 
                        True, 
                        f"No excluded product types found in report (correct behavior)"
                    )
                else:
                    self.log_result(
                        "Product Type Exclusions - Verification", 
                        False, 
                        f"Found {len(excluded_products_found)} excluded products in report",
                        f"Excluded products: {excluded_products_found}"
                    )
            else:
                self.log_result(
                    "Product Type Exclusions", 
                    False, 
                    f"Failed to get report: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Product Type Exclusions", False, f"Error: {str(e)}")

    def test_width_and_m2_calculations(self):
        """Test 4: Verify width usage and m² calculations are correct"""
        print("\n=== TEST 4: WIDTH AND M² CALCULATIONS ===")
        
        try:
            response = self.session.get(
                f"{API_BASE}/stock/reports/product-usage-detailed",
                params={
                    "start_date": "2020-01-01T00:00:00Z",
                    "end_date": "2030-12-31T23:59:59Z",
                    "include_order_breakdown": True
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                data = result.get("data", {})
                
                products = data.get("products", [])
                grand_total_m2 = data.get("grand_total_m2", 0)
                
                if len(products) == 0:
                    self.log_result(
                        "Width and M² Calculations", 
                        True, 
                        "No products in report, calculations not applicable"
                    )
                    return
                
                calculated_grand_total = 0.0
                calculation_errors = []
                
                for product in products:
                    usage_by_width = product.get("usage_by_width", [])
                    
                    for width_entry in usage_by_width:
                        width_mm = width_entry.get("width_mm", 0)
                        total_length_m = width_entry.get("total_length_m", 0)
                        reported_m2 = width_entry.get("m2", 0)
                        
                        # Calculate expected m²: (width_mm / 1000) * length_m
                        expected_m2 = (width_mm / 1000.0) * total_length_m
                        
                        # Allow small rounding differences
                        if abs(reported_m2 - expected_m2) > 0.01:
                            calculation_errors.append({
                                "product": product.get("product_info", {}).get("product_description", "Unknown"),
                                "width_mm": width_mm,
                                "length_m": total_length_m,
                                "reported_m2": reported_m2,
                                "expected_m2": expected_m2,
                                "difference": abs(reported_m2 - expected_m2)
                            })
                        
                        calculated_grand_total += expected_m2
                
                # Check grand total calculation
                grand_total_correct = abs(grand_total_m2 - calculated_grand_total) < 0.01
                
                if len(calculation_errors) == 0 and grand_total_correct:
                    self.log_result(
                        "Width and M² Calculations", 
                        True, 
                        f"All m² calculations are correct",
                        f"Grand total m²: {grand_total_m2}, Products: {len(products)}"
                    )
                else:
                    error_details = []
                    if calculation_errors:
                        error_details.append(f"{len(calculation_errors)} calculation errors")
                    if not grand_total_correct:
                        error_details.append(f"Grand total mismatch: reported {grand_total_m2}, calculated {calculated_grand_total}")
                    
                    self.log_result(
                        "Width and M² Calculations", 
                        False, 
                        f"Calculation issues found: {', '.join(error_details)}",
                        f"First few errors: {calculation_errors[:3]}"
                    )
            else:
                self.log_result(
                    "Width and M² Calculations", 
                    False, 
                    f"Failed to get report: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Width and M² Calculations", False, f"Error: {str(e)}")

    def debug_product_matching(self):
        """Debug why products might not be found"""
        print("\n=== DEBUG: PRODUCT MATCHING ANALYSIS ===")
        
        try:
            # Get orders
            orders_response = self.session.get(f"{API_BASE}/orders")
            if orders_response.status_code != 200:
                return
            
            orders = orders_response.json()
            
            # Get all client products
            clients_response = self.session.get(f"{API_BASE}/clients")
            if clients_response.status_code != 200:
                return
            
            clients = clients_response.json()
            all_client_products = {}
            
            for client in clients:
                client_id = client.get('id')
                products_response = self.session.get(f"{API_BASE}/clients/{client_id}/catalog")
                
                if products_response.status_code == 200:
                    products = products_response.json()
                    for product in products:
                        all_client_products[product.get('id')] = product
            
            print(f"Total client products: {len(all_client_products)}")
            
            # Check product matching
            product_ids_in_orders = set()
            matched_products = 0
            
            for order in orders:
                for item in order.get('items', []):
                    product_id = item.get('product_id')
                    if product_id:
                        product_ids_in_orders.add(product_id)
                        if product_id in all_client_products:
                            matched_products += 1
                            product = all_client_products[product_id]
                            print(f"  Matched Product: {product.get('product_description', 'Unknown')} (Type: {product.get('product_type', 'Unknown')})")
            
            print(f"Product IDs in orders: {len(product_ids_in_orders)}")
            print(f"Matched products: {matched_products}")
            
            if matched_products == 0:
                print("⚠️  NO PRODUCT MATCHES FOUND - This explains why report is empty!")
                print("   Orders reference product IDs that don't exist in client_products collection")
            
            self.log_result(
                "Product Matching Debug", 
                matched_products > 0, 
                f"Found {matched_products} matching products out of {len(product_ids_in_orders)} product IDs in orders"
            )
                
        except Exception as e:
            self.log_result("Product Matching Debug", False, f"Error: {str(e)}")

    def print_test_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "="*80)
        print("FIXED CONSUMABLE USAGE REPORT TEST SUMMARY")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        # Show all test results
        print("\n" + "="*60)
        print("DETAILED RESULTS:")
        print("="*60)
        
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test']}: {result['message']}")
            if result['details']:
                print(f"   Details: {result['details']}")
        
        # Show failed tests details
        failed_results = [r for r in self.test_results if not r['success']]
        if failed_results:
            print("\n" + "="*60)
            print("FAILED TESTS ANALYSIS:")
            print("="*60)
            for result in failed_results:
                print(f"\n❌ {result['test']}")
                print(f"   Message: {result['message']}")
                if result['details']:
                    print(f"   Details: {result['details']}")
        
        print("\n" + "="*80)
        if success_rate == 100:
            print("🎉 PERFECT! CONSUMABLE USAGE REPORT FIX VERIFIED!")
        elif success_rate >= 80:
            print(f"✅ GOOD! {success_rate:.1f}% SUCCESS RATE - MOSTLY WORKING")
        else:
            print(f"⚠️  ISSUES FOUND: {success_rate:.1f}% SUCCESS RATE")
        print("="*80)

    def run_fixed_consumable_usage_tests(self):
        """Run all tests for the FIXED consumable usage report"""
        print("\n" + "="*80)
        print("TESTING FIXED CONSUMABLE USAGE REPORT ENDPOINT")
        print("GET /api/stock/reports/product-usage-detailed")
        print("="*80)
        
        # Step 1: Authenticate
        if not self.authenticate():
            print("❌ Authentication failed - cannot proceed with tests")
            return
        
        # Step 2: Test the fixed endpoint with default range
        report_data = self.test_fixed_endpoint_default_range()
        
        # Step 3: Test active orders inclusion
        self.test_active_orders_analysis()
        
        # Step 4: Test product type exclusions
        self.test_product_type_exclusions()
        
        # Step 5: Test width and m² calculations
        self.test_width_and_m2_calculations()
        
        # Step 6: Debug product matching if needed
        self.debug_product_matching()
        
        # Step 7: Print comprehensive summary
        self.print_test_summary()

if __name__ == "__main__":
    tester = FixedConsumableUsageReportTester()
    tester.run_fixed_consumable_usage_tests()