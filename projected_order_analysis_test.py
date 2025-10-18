#!/usr/bin/env python3
"""
Projected Order Analysis Endpoint Testing
Testing GET /api/stock/reports/projected-order-analysis to identify why it's returning 0 orders

Test Scenarios:
1. Check if there are any orders in the database at all
2. Check the date format of created_at field
3. Check the status values
4. Test the endpoint with default date range (last 90 days)
5. Test with no client filter
6. Debug the date comparison
7. Test with a very wide date range
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

class ProjectedOrderAnalysisTester:
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
        """Check if there are any orders in the database at all"""
        print("\n" + "="*80)
        print("STEP 1: CHECKING ORDERS IN DATABASE")
        print("="*80)
        
        try:
            # Get all orders
            response = self.session.get(f"{API_BASE}/orders")
            
            if response.status_code == 200:
                orders = response.json()
                
                if isinstance(orders, list):
                    total_orders = len(orders)
                    
                    if total_orders > 0:
                        # Analyze first few orders
                        sample_orders = orders[:3] if len(orders) >= 3 else orders
                        
                        print(f"\n📊 FOUND {total_orders} ORDERS IN DATABASE")
                        print("\n🔍 SAMPLE ORDER ANALYSIS:")
                        
                        for i, order in enumerate(sample_orders, 1):
                            print(f"\n--- Order {i} ---")
                            print(f"Order ID: {order.get('id', 'N/A')}")
                            print(f"Order Number: {order.get('order_number', 'N/A')}")
                            print(f"Client ID: {order.get('client_id', 'N/A')}")
                            print(f"Client Name: {order.get('client_name', 'N/A')}")
                            print(f"Status: {order.get('status', 'N/A')}")
                            print(f"Created At: {order.get('created_at', 'N/A')}")
                            print(f"Created At Type: {type(order.get('created_at'))}")
                            
                            # Check items
                            items = order.get('items', [])
                            print(f"Items Count: {len(items)}")
                            if items:
                                item = items[0]
                                print(f"First Item - Product ID: {item.get('product_id', 'N/A')}")
                                print(f"First Item - Product Name: {item.get('product_name', 'N/A')}")
                                print(f"First Item - Quantity: {item.get('quantity', 'N/A')}")
                        
                        # Check date formats and status values
                        self.analyze_order_dates_and_status(orders)
                        
                        self.log_result(
                            "Database Orders Check", 
                            True, 
                            f"Found {total_orders} orders in database",
                            f"Sample orders analyzed for date format and status"
                        )
                    else:
                        self.log_result(
                            "Database Orders Check", 
                            False, 
                            "No orders found in database - this explains why projected analysis returns 0 orders"
                        )
                else:
                    self.log_result(
                        "Database Orders Check", 
                        False, 
                        f"Unexpected response format: {type(orders)}",
                        str(orders)
                    )
            else:
                self.log_result(
                    "Database Orders Check", 
                    False, 
                    f"Failed to get orders: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Database Orders Check", False, f"Error: {str(e)}")

    def analyze_order_dates_and_status(self, orders):
        """Analyze order date formats and status values"""
        print(f"\n📅 DATE FORMAT ANALYSIS:")
        
        date_formats = {}
        status_values = {}
        
        for order in orders:
            created_at = order.get('created_at')
            status = order.get('status', 'unknown')
            
            # Analyze date format
            if created_at:
                date_type = type(created_at).__name__
                if date_type not in date_formats:
                    date_formats[date_type] = []
                date_formats[date_type].append(str(created_at))
            
            # Count status values
            status_values[status] = status_values.get(status, 0) + 1
        
        print("Date Formats Found:")
        for date_type, examples in date_formats.items():
            print(f"  - {date_type}: {len(examples)} orders")
            print(f"    Examples: {examples[:2]}")  # Show first 2 examples
        
        print(f"\nStatus Values Found:")
        for status, count in status_values.items():
            print(f"  - '{status}': {count} orders")

    def test_projected_order_analysis_default(self):
        """Test the endpoint with default date range (last 90 days)"""
        print("\n" + "="*80)
        print("STEP 2: TESTING PROJECTED ORDER ANALYSIS - DEFAULT DATE RANGE")
        print("="*80)
        
        try:
            # Calculate default date range (last 90 days)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=90)
            
            # Format dates as ISO strings
            start_date_str = start_date.isoformat() + "Z"
            end_date_str = end_date.isoformat() + "Z"
            
            print(f"📅 Testing with date range:")
            print(f"   Start: {start_date_str}")
            print(f"   End: {end_date_str}")
            
            response = self.session.get(
                f"{API_BASE}/stock/reports/projected-order-analysis",
                params={
                    "start_date": start_date_str,
                    "end_date": end_date_str
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                data = result.get("data", {})
                
                print(f"\n📊 RESPONSE ANALYSIS:")
                print(f"Success: {result.get('success', False)}")
                print(f"Message: {result.get('message', 'N/A')}")
                
                # Analyze the data
                report_period = data.get("report_period", {})
                products = data.get("products", [])
                summary = data.get("summary", {})
                
                print(f"\nReport Period: {report_period}")
                print(f"Total Products: {data.get('total_products', 0)}")
                print(f"Total Orders Analyzed: {summary.get('total_orders_analyzed', 0)}")
                print(f"Total Unique Products: {summary.get('total_unique_products', 0)}")
                
                if len(products) > 0:
                    print(f"\n🎯 FOUND {len(products)} PRODUCTS WITH PROJECTIONS")
                    for i, product in enumerate(products[:3], 1):  # Show first 3
                        product_info = product.get("product_info", {})
                        historical = product.get("historical_data", {})
                        print(f"\n--- Product {i} ---")
                        print(f"Product: {product_info.get('product_description', 'N/A')}")
                        print(f"Client: {product_info.get('client_name', 'N/A')}")
                        print(f"Total Quantity: {historical.get('total_quantity', 0)}")
                        print(f"Order Count: {historical.get('order_count', 0)}")
                else:
                    print(f"\n⚠️  NO PRODUCTS FOUND IN ANALYSIS")
                
                self.log_result(
                    "Projected Order Analysis - Default Range", 
                    True, 
                    f"Endpoint responded successfully",
                    f"Orders analyzed: {summary.get('total_orders_analyzed', 0)}, Products: {len(products)}"
                )
            else:
                self.log_result(
                    "Projected Order Analysis - Default Range", 
                    False, 
                    f"Endpoint failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Projected Order Analysis - Default Range", False, f"Error: {str(e)}")

    def test_projected_order_analysis_no_dates(self):
        """Test the endpoint without providing dates (should fail)"""
        print("\n" + "="*80)
        print("STEP 3: TESTING PROJECTED ORDER ANALYSIS - NO DATES PROVIDED")
        print("="*80)
        
        try:
            response = self.session.get(f"{API_BASE}/stock/reports/projected-order-analysis")
            
            print(f"📊 RESPONSE WITHOUT DATES:")
            print(f"Status Code: {response.status_code}")
            
            if response.status_code != 200:
                print(f"Response Text: {response.text}")
                self.log_result(
                    "Projected Order Analysis - No Dates", 
                    True, 
                    f"Correctly failed when no dates provided (status {response.status_code})",
                    "This confirms the endpoint requires date parameters"
                )
            else:
                result = response.json()
                self.log_result(
                    "Projected Order Analysis - No Dates", 
                    False, 
                    "Endpoint should have failed without dates but returned 200",
                    str(result)
                )
                
        except Exception as e:
            self.log_result("Projected Order Analysis - No Dates", False, f"Error: {str(e)}")

    def test_projected_order_analysis_wide_range(self):
        """Test with a very wide date range to capture any orders"""
        print("\n" + "="*80)
        print("STEP 4: TESTING PROJECTED ORDER ANALYSIS - WIDE DATE RANGE")
        print("="*80)
        
        try:
            # Use very wide date range
            start_date_str = "2020-01-01T00:00:00Z"
            end_date_str = "2030-12-31T23:59:59Z"
            
            print(f"📅 Testing with WIDE date range:")
            print(f"   Start: {start_date_str}")
            print(f"   End: {end_date_str}")
            
            response = self.session.get(
                f"{API_BASE}/stock/reports/projected-order-analysis",
                params={
                    "start_date": start_date_str,
                    "end_date": end_date_str
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                data = result.get("data", {})
                
                print(f"\n📊 WIDE RANGE RESPONSE ANALYSIS:")
                
                summary = data.get("summary", {})
                products = data.get("products", [])
                
                print(f"Total Orders Analyzed: {summary.get('total_orders_analyzed', 0)}")
                print(f"Total Unique Products: {summary.get('total_unique_products', 0)}")
                print(f"Products with Projections: {len(products)}")
                
                if summary.get('total_orders_analyzed', 0) > 0:
                    print(f"\n🎯 SUCCESS! Found {summary.get('total_orders_analyzed')} orders in wide range")
                    
                    # Show some product details
                    if products:
                        print(f"\n📦 PRODUCT ANALYSIS:")
                        for i, product in enumerate(products[:3], 1):
                            product_info = product.get("product_info", {})
                            historical = product.get("historical_data", {})
                            projections = product.get("projections", {})
                            
                            print(f"\n--- Product {i} ---")
                            print(f"Product: {product_info.get('product_description', 'N/A')}")
                            print(f"Client: {product_info.get('client_name', 'N/A')}")
                            print(f"Historical Total: {historical.get('total_quantity', 0)}")
                            print(f"3-Month Projection: {projections.get('3_months', 0)}")
                            print(f"12-Month Projection: {projections.get('12_months', 0)}")
                else:
                    print(f"\n⚠️  STILL NO ORDERS FOUND EVEN WITH WIDE DATE RANGE")
                    print("This suggests either:")
                    print("1. No orders exist in database")
                    print("2. Date format mismatch in query")
                    print("3. Status filtering excluding all orders")
                
                self.log_result(
                    "Projected Order Analysis - Wide Range", 
                    True, 
                    f"Wide range test completed",
                    f"Orders found: {summary.get('total_orders_analyzed', 0)}"
                )
            else:
                self.log_result(
                    "Projected Order Analysis - Wide Range", 
                    False, 
                    f"Wide range test failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Projected Order Analysis - Wide Range", False, f"Error: {str(e)}")

    def debug_date_comparison_issue(self):
        """Debug the date comparison by examining the actual query logic"""
        print("\n" + "="*80)
        print("STEP 5: DEBUGGING DATE COMPARISON ISSUE")
        print("="*80)
        
        try:
            # Get a sample order to check its date format
            response = self.session.get(f"{API_BASE}/orders")
            
            if response.status_code == 200:
                orders = response.json()
                
                if orders and len(orders) > 0:
                    sample_order = orders[0]
                    created_at = sample_order.get('created_at')
                    
                    print(f"📅 SAMPLE ORDER DATE ANALYSIS:")
                    print(f"Raw created_at value: {created_at}")
                    print(f"Type: {type(created_at)}")
                    
                    # Try to parse the date in different ways
                    if isinstance(created_at, str):
                        print(f"\n🔍 PARSING ATTEMPTS:")
                        
                        # Try ISO format parsing (what the endpoint uses)
                        try:
                            parsed_iso = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                            print(f"✅ ISO parsing successful: {parsed_iso}")
                            print(f"   ISO string: {parsed_iso.isoformat()}")
                        except Exception as e:
                            print(f"❌ ISO parsing failed: {e}")
                        
                        # Try direct datetime parsing
                        try:
                            if created_at.endswith('Z'):
                                # Remove Z and add timezone
                                clean_date = created_at.replace('Z', '+00:00')
                                parsed_direct = datetime.fromisoformat(clean_date)
                                print(f"✅ Direct parsing successful: {parsed_direct}")
                            else:
                                parsed_direct = datetime.fromisoformat(created_at)
                                print(f"✅ Direct parsing successful: {parsed_direct}")
                        except Exception as e:
                            print(f"❌ Direct parsing failed: {e}")
                    
                    # Test the actual query format used by the endpoint
                    print(f"\n🔍 TESTING ENDPOINT QUERY FORMAT:")
                    
                    # Simulate the endpoint's date parsing
                    test_start = "2020-01-01T00:00:00Z"
                    test_end = "2030-12-31T23:59:59Z"
                    
                    try:
                        start = datetime.fromisoformat(test_start.replace('Z', '+00:00'))
                        end = datetime.fromisoformat(test_end.replace('Z', '+00:00'))
                        
                        print(f"Endpoint start date: {start.isoformat()}")
                        print(f"Endpoint end date: {end.isoformat()}")
                        print(f"Sample order date: {created_at}")
                        
                        # Check if the sample order date would match the query
                        if isinstance(created_at, str):
                            # The endpoint uses: "created_at": {"$gte": start.isoformat(), "$lte": end.isoformat()}
                            query_start = start.isoformat()
                            query_end = end.isoformat()
                            
                            print(f"\n📊 QUERY COMPARISON:")
                            print(f"Query start: {query_start}")
                            print(f"Query end: {query_end}")
                            print(f"Order date: {created_at}")
                            
                            # String comparison (what MongoDB will do)
                            if query_start <= created_at <= query_end:
                                print(f"✅ Order date WOULD match query (string comparison)")
                            else:
                                print(f"❌ Order date would NOT match query (string comparison)")
                                print(f"   This could be the issue!")
                        
                    except Exception as e:
                        print(f"❌ Date parsing simulation failed: {e}")
                
                self.log_result(
                    "Date Comparison Debug", 
                    True, 
                    "Date format analysis completed",
                    f"Sample order date format analyzed"
                )
            else:
                self.log_result(
                    "Date Comparison Debug", 
                    False, 
                    "Could not get orders for date analysis"
                )
                
        except Exception as e:
            self.log_result("Date Comparison Debug", False, f"Error: {str(e)}")

    def test_with_specific_client(self):
        """Test the endpoint with a specific client filter"""
        print("\n" + "="*80)
        print("STEP 6: TESTING WITH SPECIFIC CLIENT FILTER")
        print("="*80)
        
        try:
            # Get available clients
            clients_response = self.session.get(f"{API_BASE}/clients")
            
            if clients_response.status_code == 200:
                clients = clients_response.json()
                
                if clients and len(clients) > 0:
                    test_client = clients[0]
                    client_id = test_client.get('id')
                    client_name = test_client.get('company_name', 'Unknown')
                    
                    print(f"🏢 Testing with client: {client_name} (ID: {client_id})")
                    
                    # Test with wide date range and specific client
                    start_date_str = "2020-01-01T00:00:00Z"
                    end_date_str = "2030-12-31T23:59:59Z"
                    
                    response = self.session.get(
                        f"{API_BASE}/stock/reports/projected-order-analysis",
                        params={
                            "client_id": client_id,
                            "start_date": start_date_str,
                            "end_date": end_date_str
                        }
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        data = result.get("data", {})
                        summary = data.get("summary", {})
                        
                        print(f"\n📊 CLIENT-SPECIFIC ANALYSIS:")
                        print(f"Client Filter: {data.get('client_filter')}")
                        print(f"Orders Analyzed: {summary.get('total_orders_analyzed', 0)}")
                        print(f"Products Found: {summary.get('total_unique_products', 0)}")
                        
                        self.log_result(
                            "Projected Order Analysis - Client Filter", 
                            True, 
                            f"Client-specific test completed for {client_name}",
                            f"Orders: {summary.get('total_orders_analyzed', 0)}"
                        )
                    else:
                        self.log_result(
                            "Projected Order Analysis - Client Filter", 
                            False, 
                            f"Client-specific test failed: {response.status_code}",
                            response.text
                        )
                else:
                    self.log_result(
                        "Projected Order Analysis - Client Filter", 
                        False, 
                        "No clients available for testing"
                    )
            else:
                self.log_result(
                    "Projected Order Analysis - Client Filter", 
                    False, 
                    f"Could not get clients: {clients_response.status_code}"
                )
                
        except Exception as e:
            self.log_result("Projected Order Analysis - Client Filter", False, f"Error: {str(e)}")

    def print_test_summary(self):
        """Print comprehensive test summary with findings"""
        print("\n" + "="*80)
        print("PROJECTED ORDER ANALYSIS TEST SUMMARY")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        
        print(f"\n📋 TEST RESULTS:")
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test']}: {result['message']}")
            if result['details'] and not result['success']:
                print(f"    Details: {result['details']}")
        
        print(f"\n🔍 KEY FINDINGS:")
        print("1. Check if orders exist in database")
        print("2. Verify date format compatibility between orders and endpoint query")
        print("3. Check if status filtering is excluding orders")
        print("4. Confirm endpoint parameter requirements")
        
        print(f"\n💡 RECOMMENDATIONS:")
        print("1. If no orders found: Create test orders with proper date format")
        print("2. If date format mismatch: Fix endpoint date comparison logic")
        print("3. If status filtering issue: Review order status values and filtering logic")
        print("4. Add default date range handling in endpoint for better UX")

    def run_comprehensive_test(self):
        """Run all tests for projected order analysis debugging"""
        print("\n" + "="*80)
        print("PROJECTED ORDER ANALYSIS ENDPOINT DEBUGGING")
        print("Investigating why the endpoint returns 0 orders")
        print("="*80)
        
        # Step 1: Authenticate
        if not self.authenticate():
            print("❌ Authentication failed - cannot proceed with tests")
            return
        
        # Step 2: Check orders in database
        self.check_orders_in_database()
        
        # Step 3: Test endpoint with default date range
        self.test_projected_order_analysis_default()
        
        # Step 4: Test endpoint without dates
        self.test_projected_order_analysis_no_dates()
        
        # Step 5: Test with wide date range
        self.test_projected_order_analysis_wide_range()
        
        # Step 6: Debug date comparison
        self.debug_date_comparison_issue()
        
        # Step 7: Test with specific client
        self.test_with_specific_client()
        
        # Step 8: Print summary
        self.print_test_summary()

if __name__ == "__main__":
    tester = ProjectedOrderAnalysisTester()
    tester.run_comprehensive_test()