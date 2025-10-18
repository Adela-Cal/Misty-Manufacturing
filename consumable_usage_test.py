#!/usr/bin/env python3
"""
Consumable Usage Report Endpoint Testing
Focus on GET /api/stock/reports/product-usage-detailed endpoint

Testing based on review request:
1. Check if there are orders in the database with items
2. Test the endpoint with different date ranges
3. Check the query structure for date comparison issues
4. Debug the query and check what orders match
5. Verify if it should include orders on hand (not just completed)
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

class ConsumableUsageReportTester:
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

    def check_orders_in_database(self):
        """Check if there are orders in the database with items"""
        print("\n=== CHECKING ORDERS IN DATABASE ===")
        
        try:
            response = self.session.get(f"{API_BASE}/orders")
            
            if response.status_code == 200:
                orders = response.json()
                
                if not orders:
                    self.log_result(
                        "Check Orders in Database", 
                        False, 
                        "No orders found in database"
                    )
                    return []
                
                # Check orders with items
                orders_with_items = []
                for order in orders:
                    items = order.get("items", [])
                    if items:
                        orders_with_items.append(order)
                        print(f"   Order {order.get('order_number', 'Unknown')}: {len(items)} items")
                        for item in items[:2]:  # Show first 2 items
                            print(f"     - {item.get('product_name', 'Unknown')} (ID: {item.get('product_id', 'N/A')})")
                
                self.log_result(
                    "Check Orders in Database", 
                    True, 
                    f"Found {len(orders)} total orders, {len(orders_with_items)} with items",
                    f"Sample orders: {[o.get('order_number') for o in orders_with_items[:3]]}"
                )
                return orders_with_items
            else:
                self.log_result(
                    "Check Orders in Database", 
                    False, 
                    f"Failed to get orders: {response.status_code}",
                    response.text
                )
                return []
                
        except Exception as e:
            self.log_result("Check Orders in Database", False, f"Error: {str(e)}")
            return []

    def test_endpoint_with_default_date_range(self):
        """Test endpoint with default date range (last 30 days)"""
        print("\n=== TESTING WITH DEFAULT DATE RANGE (LAST 30 DAYS) ===")
        
        try:
            # Calculate last 30 days
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            start_str = start_date.isoformat() + 'Z'
            end_str = end_date.isoformat() + 'Z'
            
            print(f"Testing date range: {start_str} to {end_str}")
            
            response = self.session.get(
                f"{API_BASE}/stock/reports/product-usage-detailed",
                params={
                    "start_date": start_str,
                    "end_date": end_str
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                data = result.get("data", {})
                
                products = data.get("products", [])
                total_products = data.get("total_products", 0)
                grand_total_m2 = data.get("grand_total_m2", 0)
                
                self.log_result(
                    "Default Date Range Test", 
                    True, 
                    f"Successfully retrieved report",
                    f"Products: {total_products}, Total m²: {grand_total_m2}"
                )
                
                # Print detailed results
                print(f"   Report Period: {data.get('report_period', {})}")
                print(f"   Products Found: {total_products}")
                print(f"   Grand Total m²: {grand_total_m2}")
                print(f"   Grand Total Length: {data.get('grand_total_length_m', 0)} m")
                
                if products:
                    print("   Sample Products:")
                    for product in products[:3]:
                        product_info = product.get("product_info", {})
                        print(f"     - {product_info.get('product_description', 'Unknown')}")
                        print(f"       Widths: {product.get('total_widths_used', 0)}, m²: {product.get('product_total_m2', 0)}")
                else:
                    print("   ⚠️  NO PRODUCTS FOUND - This indicates the issue!")
                
                return data
            else:
                self.log_result(
                    "Default Date Range Test", 
                    False, 
                    f"Failed to get report: {response.status_code}",
                    response.text
                )
                return None
                
        except Exception as e:
            self.log_result("Default Date Range Test", False, f"Error: {str(e)}")
            return None

    def test_endpoint_with_wide_date_range(self):
        """Test endpoint with wide date range (2020-01-01 to 2030-12-31)"""
        print("\n=== TESTING WITH WIDE DATE RANGE (2020-2030) ===")
        
        try:
            start_str = "2020-01-01T00:00:00Z"
            end_str = "2030-12-31T23:59:59Z"
            
            print(f"Testing wide date range: {start_str} to {end_str}")
            
            response = self.session.get(
                f"{API_BASE}/stock/reports/product-usage-detailed",
                params={
                    "start_date": start_str,
                    "end_date": end_str
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                data = result.get("data", {})
                
                products = data.get("products", [])
                total_products = data.get("total_products", 0)
                grand_total_m2 = data.get("grand_total_m2", 0)
                
                self.log_result(
                    "Wide Date Range Test", 
                    True, 
                    f"Successfully retrieved report",
                    f"Products: {total_products}, Total m²: {grand_total_m2}"
                )
                
                print(f"   Products Found: {total_products}")
                print(f"   Grand Total m²: {grand_total_m2}")
                
                if products:
                    print("   Sample Products:")
                    for product in products[:3]:
                        product_info = product.get("product_info", {})
                        print(f"     - {product_info.get('product_description', 'Unknown')}")
                else:
                    print("   ⚠️  NO PRODUCTS FOUND - Issue confirmed with wide date range!")
                
                return data
            else:
                self.log_result(
                    "Wide Date Range Test", 
                    False, 
                    f"Failed to get report: {response.status_code}",
                    response.text
                )
                return None
                
        except Exception as e:
            self.log_result("Wide Date Range Test", False, f"Error: {str(e)}")
            return None

    def debug_query_structure(self, orders_with_items):
        """Debug the query structure and check what orders match"""
        print("\n=== DEBUGGING QUERY STRUCTURE ===")
        
        if not orders_with_items:
            print("No orders available for debugging")
            return
        
        # Analyze order structure
        print("Analyzing order structure:")
        sample_order = orders_with_items[0]
        
        print(f"Sample Order: {sample_order.get('order_number', 'Unknown')}")
        print(f"  Status: {sample_order.get('status', 'Unknown')}")
        print(f"  Created At: {sample_order.get('created_at', 'Unknown')}")
        print(f"  Created At Type: {type(sample_order.get('created_at'))}")
        print(f"  Client ID: {sample_order.get('client_id', 'Unknown')}")
        print(f"  Items Count: {len(sample_order.get('items', []))}")
        
        # Check item structure
        items = sample_order.get("items", [])
        if items:
            sample_item = items[0]
            print(f"  Sample Item:")
            print(f"    Product ID: {sample_item.get('product_id', 'Unknown')}")
            print(f"    Product Name: {sample_item.get('product_name', 'Unknown')}")
            print(f"    Quantity: {sample_item.get('quantity', 'Unknown')}")
            print(f"    Width: {sample_item.get('width', 'Unknown')}")
            print(f"    Length: {sample_item.get('length', 'Unknown')}")
        
        # Check order statuses
        statuses = {}
        for order in orders_with_items:
            status = order.get("status", "unknown")
            statuses[status] = statuses.get(status, 0) + 1
        
        print(f"\nOrder Status Distribution:")
        for status, count in statuses.items():
            print(f"  {status}: {count} orders")
        
        # Check date formats
        print(f"\nDate Format Analysis:")
        for i, order in enumerate(orders_with_items[:3]):
            created_at = order.get("created_at")
            print(f"  Order {i+1} created_at: {created_at} (type: {type(created_at)})")
        
        # Check if orders have product_id in items that exist in client_products
        print(f"\nChecking Product ID Existence:")
        product_ids_found = set()
        for order in orders_with_items[:3]:
            for item in order.get("items", []):
                product_id = item.get("product_id")
                if product_id:
                    product_ids_found.add(product_id)
        
        print(f"  Unique Product IDs in orders: {len(product_ids_found)}")
        
        # Check if these products exist in client_products
        for product_id in list(product_ids_found)[:3]:
            try:
                # Try to get the product
                response = self.session.get(f"{API_BASE}/clients/*/catalog")  # This won't work, need specific client
                print(f"  Product ID {product_id}: Need to check client_products collection")
            except:
                pass

    def check_client_products(self, orders_with_items):
        """Check if products exist in client_products collection"""
        print("\n=== CHECKING CLIENT PRODUCTS ===")
        
        if not orders_with_items:
            return
        
        # Get clients first
        try:
            response = self.session.get(f"{API_BASE}/clients")
            if response.status_code != 200:
                print("Failed to get clients")
                return
            
            clients = response.json()
            print(f"Found {len(clients)} clients")
            
            # Check products for each client
            total_products = 0
            for client in clients[:3]:  # Check first 3 clients
                client_id = client.get("id")
                client_name = client.get("company_name", "Unknown")
                
                try:
                    response = self.session.get(f"{API_BASE}/clients/{client_id}/catalog")
                    if response.status_code == 200:
                        products = response.json()
                        total_products += len(products)
                        print(f"  Client '{client_name}': {len(products)} products")
                        
                        # Show sample products
                        for product in products[:2]:
                            print(f"    - {product.get('product_description', 'Unknown')} (Type: {product.get('product_type', 'Unknown')})")
                    else:
                        print(f"  Client '{client_name}': Failed to get catalog")
                except Exception as e:
                    print(f"  Client '{client_name}': Error - {str(e)}")
            
            print(f"Total products across clients: {total_products}")
            
        except Exception as e:
            print(f"Error checking client products: {str(e)}")

    def test_status_filtering(self):
        """Test if status filtering is too restrictive"""
        print("\n=== TESTING STATUS FILTERING ===")
        
        # The endpoint currently filters for status: {"$in": ["completed", "archived"]}
        # Let's check what happens if we include orders on hand
        
        print("Current endpoint filters for status: ['completed', 'archived']")
        print("Testing if this is too restrictive...")
        
        # Get all orders and check their statuses
        try:
            response = self.session.get(f"{API_BASE}/orders")
            if response.status_code == 200:
                orders = response.json()
                
                status_counts = {}
                for order in orders:
                    status = order.get("status", "unknown")
                    status_counts[status] = status_counts.get(status, 0) + 1
                
                print("All order statuses in database:")
                for status, count in status_counts.items():
                    print(f"  {status}: {count} orders")
                
                # Check how many orders would be included with different filters
                completed_archived = [o for o in orders if o.get("status") in ["completed", "archived"]]
                all_except_cancelled = [o for o in orders if o.get("status") not in ["cancelled", "deleted"]]
                
                print(f"\nFiltering Results:")
                print(f"  Current filter (completed, archived): {len(completed_archived)} orders")
                print(f"  If including orders on hand (all except cancelled): {len(all_except_cancelled)} orders")
                
                if len(all_except_cancelled) > len(completed_archived):
                    print("  ⚠️  STATUS FILTERING IS TOO RESTRICTIVE!")
                    print("  ⚠️  Should include orders on hand (not just completed/archived)")
                    
                    self.log_result(
                        "Status Filtering Analysis", 
                        False, 
                        "Status filtering too restrictive - excluding orders on hand",
                        f"Current: {len(completed_archived)}, Should include: {len(all_except_cancelled)}"
                    )
                else:
                    self.log_result(
                        "Status Filtering Analysis", 
                        True, 
                        "Status filtering appears appropriate"
                    )
                
            else:
                print("Failed to get orders for status analysis")
                
        except Exception as e:
            print(f"Error in status filtering test: {str(e)}")

    def test_date_format_issues(self):
        """Test for date format mismatch issues"""
        print("\n=== TESTING DATE FORMAT ISSUES ===")
        
        # The endpoint uses: "created_at": {"$gte": start.isoformat(), "$lte": end.isoformat()}
        # This compares ISO strings with whatever format is stored in the database
        
        print("Checking date format compatibility...")
        
        try:
            # Get a sample order to check date format
            response = self.session.get(f"{API_BASE}/orders")
            if response.status_code == 200:
                orders = response.json()
                if orders:
                    sample_order = orders[0]
                    created_at = sample_order.get("created_at")
                    
                    print(f"Sample order created_at: {created_at}")
                    print(f"Type: {type(created_at)}")
                    
                    # Try to parse it
                    if isinstance(created_at, str):
                        try:
                            parsed_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                            print(f"Successfully parsed as datetime: {parsed_date}")
                            print(f"ISO format: {parsed_date.isoformat()}")
                            
                            # This is the issue! The endpoint compares:
                            # Database: datetime object or ISO string
                            # Query: ISO string from start.isoformat()
                            
                            print("\n⚠️  POTENTIAL DATE FORMAT ISSUE IDENTIFIED:")
                            print("   Endpoint query uses: start.isoformat() (string)")
                            print("   Database might store: datetime objects")
                            print("   MongoDB comparison might fail!")
                            
                            self.log_result(
                                "Date Format Analysis", 
                                False, 
                                "Date format mismatch - comparing ISO strings with datetime objects",
                                f"DB format: {type(created_at)}, Query format: ISO string"
                            )
                            
                        except Exception as e:
                            print(f"Failed to parse date: {str(e)}")
                    else:
                        print("Date is not a string - might be datetime object")
                        print("\n⚠️  DATE FORMAT ISSUE CONFIRMED:")
                        print("   Database stores datetime objects")
                        print("   Endpoint query uses ISO strings")
                        print("   This will cause MongoDB query to fail!")
                        
                        self.log_result(
                            "Date Format Analysis", 
                            False, 
                            "Date format mismatch confirmed - datetime vs ISO string",
                            f"DB stores: {type(created_at)}, Query uses: ISO string"
                        )
                else:
                    print("No orders found for date format analysis")
            else:
                print("Failed to get orders for date format analysis")
                
        except Exception as e:
            print(f"Error in date format test: {str(e)}")

    def test_product_type_exclusions(self):
        """Test if product type exclusions are working correctly"""
        print("\n=== TESTING PRODUCT TYPE EXCLUSIONS ===")
        
        # The endpoint excludes: ["Spiral Paper Cores", "Composite Cores"]
        
        try:
            # Get all client products to see what types exist
            response = self.session.get(f"{API_BASE}/clients")
            if response.status_code == 200:
                clients = response.json()
                
                all_product_types = set()
                excluded_count = 0
                total_products = 0
                
                for client in clients:
                    client_id = client.get("id")
                    try:
                        response = self.session.get(f"{API_BASE}/clients/{client_id}/catalog")
                        if response.status_code == 200:
                            products = response.json()
                            total_products += len(products)
                            
                            for product in products:
                                product_type = product.get("product_type", "")
                                all_product_types.add(product_type)
                                
                                if product_type in ["Spiral Paper Cores", "Composite Cores"]:
                                    excluded_count += 1
                    except:
                        pass
                
                print(f"Product type analysis:")
                print(f"  Total products: {total_products}")
                print(f"  Excluded products: {excluded_count}")
                print(f"  Included products: {total_products - excluded_count}")
                
                print(f"\nAll product types found:")
                for product_type in sorted(all_product_types):
                    print(f"  - {product_type}")
                
                if excluded_count == total_products:
                    print("\n⚠️  ALL PRODUCTS ARE BEING EXCLUDED!")
                    print("   Product type exclusions might be too broad")
                    
                    self.log_result(
                        "Product Type Exclusions", 
                        False, 
                        "All products excluded by type filtering",
                        f"Excluded: {excluded_count}, Total: {total_products}"
                    )
                elif excluded_count > 0:
                    self.log_result(
                        "Product Type Exclusions", 
                        True, 
                        f"Product type exclusions working - {excluded_count} excluded, {total_products - excluded_count} included"
                    )
                else:
                    print("No products found with excluded types")
                    
        except Exception as e:
            print(f"Error in product type exclusions test: {str(e)}")

    def run_comprehensive_debug(self):
        """Run comprehensive debugging of the consumable usage report endpoint"""
        print("\n" + "="*80)
        print("CONSUMABLE USAGE REPORT ENDPOINT DEBUGGING")
        print("Testing GET /api/stock/reports/product-usage-detailed")
        print("="*80)
        
        # Step 1: Authenticate
        if not self.authenticate():
            print("❌ Authentication failed - cannot proceed with tests")
            return
        
        # Step 2: Check orders in database
        orders_with_items = self.check_orders_in_database()
        
        # Step 3: Test endpoint with different date ranges
        default_result = self.test_endpoint_with_default_date_range()
        wide_result = self.test_endpoint_with_wide_date_range()
        
        # Step 4: Debug query structure
        self.debug_query_structure(orders_with_items)
        
        # Step 5: Check client products
        self.check_client_products(orders_with_items)
        
        # Step 6: Test status filtering
        self.test_status_filtering()
        
        # Step 7: Test date format issues
        self.test_date_format_issues()
        
        # Step 8: Test product type exclusions
        self.test_product_type_exclusions()
        
        # Step 9: Print summary
        self.print_debug_summary()

    def print_debug_summary(self):
        """Print debugging summary with identified issues"""
        print("\n" + "="*80)
        print("DEBUGGING SUMMARY - CONSUMABLE USAGE REPORT")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        
        # Show failed tests (these indicate issues)
        failed_results = [r for r in self.test_results if not r['success']]
        if failed_results:
            print("\n" + "="*60)
            print("IDENTIFIED ISSUES:")
            print("="*60)
            for result in failed_results:
                print(f"\n❌ {result['test']}")
                print(f"   Issue: {result['message']}")
                if result['details']:
                    print(f"   Details: {result['details']}")
        
        print("\n" + "="*60)
        print("RECOMMENDATIONS:")
        print("="*60)
        
        # Analyze results and provide recommendations
        issue_found = False
        
        for result in failed_results:
            if "Date format mismatch" in result['message']:
                print("🔧 FIX DATE FORMAT ISSUE:")
                print("   Change query from ISO string comparison to datetime object comparison")
                print("   Use: start_dt = start.replace(tzinfo=None)")
                print("   Query: {'created_at': {'$gte': start_dt, '$lte': end_dt}}")
                issue_found = True
                
            if "Status filtering too restrictive" in result['message']:
                print("🔧 FIX STATUS FILTERING:")
                print("   Include orders on hand, not just completed/archived")
                print("   Change: {'status': {'$nin': ['cancelled', 'deleted']}}")
                print("   Or: {'status': {'$in': ['completed', 'archived', 'on_hand', 'in_progress']}}")
                issue_found = True
                
            if "excluded by type filtering" in result['message']:
                print("🔧 FIX PRODUCT TYPE EXCLUSIONS:")
                print("   Review excluded types - might be excluding everything")
                print("   Consider more specific exclusions or different criteria")
                issue_found = True
        
        if not issue_found:
            print("✅ No major issues identified in endpoint logic")
            print("   Issue might be in data availability or query execution")
        
        print("\n" + "="*80)

if __name__ == "__main__":
    tester = ConsumableUsageReportTester()
    tester.run_comprehensive_debug()