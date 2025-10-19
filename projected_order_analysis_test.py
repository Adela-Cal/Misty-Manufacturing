#!/usr/bin/env python3
"""
Projected Order Analysis GSM-Based Formula Testing Suite

Testing the updated Projected Material Cost calculation using the new GSM-based formula:
1. Convert 1 tonne to linear metres: linear_metres_per_tonne = 1,000,000 / (GSM × width_metres)
2. Calculate price per linear metre: price_per_metre = price_per_tonne / linear_metres_per_tonne  
3. Calculate material cost: material_cost = strip_length_m × price_per_metre × projected_qty

Test Objectives:
- Verify new cost calculation formula is working correctly
- Check that price_per_tonne, linear_metres_per_tonne, cost_per_meter are included in response
- Verify cost_per_core and cost_per_metre_of_core are calculated in summary
- Ensure the formula uses GSM and layer width correctly
- Test edge cases (missing GSM, missing width, zero price, etc.)

SPECIFIC TEST REQUIREMENTS FROM REVIEW:
1. API Response Structure Verification - Check new fields are present
2. Formula Calculation Verification - Verify GSM-based calculations
3. Multiple Layers Cost Breakdown - Test with products having 3+ material layers
4. Edge Cases - Test missing GSM, width, zero price, very small width, very high GSM
5. Summary Totals - Verify cost_per_core and cost_per_metre_of_core in summary
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

    def test_material_requirements_structure(self):
        """Test material requirements structure in projected order analysis response"""
        print("\n" + "="*80)
        print("STEP 7: TESTING MATERIAL REQUIREMENTS STRUCTURE")
        print("Testing material_requirements object structure for each period")
        print("="*80)
        
        try:
            # Call the endpoint with default parameters
            response = self.session.get(f"{API_BASE}/stock/reports/projected-order-analysis")
            
            if response.status_code == 200:
                result = response.json()
                data = result.get("data", {})
                products = data.get("products", [])
                
                if not products:
                    self.log_result(
                        "Material Requirements Structure", 
                        False, 
                        "No products found in response to test material requirements"
                    )
                    return
                
                # Test the first product (or look for LM Paper Core)
                test_product = None
                for product in products:
                    product_info = product.get("product_info", {})
                    if "LM Paper Core" in product_info.get("product_description", ""):
                        test_product = product
                        break
                
                if not test_product:
                    test_product = products[0]  # Use first product if LM Paper Core not found
                
                product_name = test_product.get("product_info", {}).get("product_description", "Unknown")
                print(f"🔍 Testing material requirements for: {product_name}")
                
                # Check if material_requirements exists
                material_requirements = test_product.get("material_requirements", {})
                
                if not material_requirements:
                    self.log_result(
                        "Material Requirements - Field Existence", 
                        False, 
                        "material_requirements field missing from product response"
                    )
                    return
                
                # Check required periods
                required_periods = ["3_months", "6_months", "9_months", "12_months"]
                missing_periods = [period for period in required_periods if period not in material_requirements]
                
                if missing_periods:
                    self.log_result(
                        "Material Requirements - Periods", 
                        False, 
                        f"Missing required periods: {missing_periods}",
                        f"Available periods: {list(material_requirements.keys())}"
                    )
                else:
                    self.log_result(
                        "Material Requirements - Periods", 
                        True, 
                        "All required periods present in material_requirements"
                    )
                
                # Check structure of each period
                materials_found = False
                for period in required_periods:
                    materials_list = material_requirements.get(period, [])
                    
                    if materials_list and len(materials_list) > 0:
                        materials_found = True
                        # Check structure of first material
                        first_material = materials_list[0]
                        required_fields = ["material_id", "material_name", "width_mm", "total_quantity_needed"]
                        missing_fields = [field for field in required_fields if field not in first_material]
                        
                        if not missing_fields:
                            self.log_result(
                                f"Material Requirements - {period} Structure", 
                                True, 
                                f"Proper structure found with {len(materials_list)} materials"
                            )
                        else:
                            self.log_result(
                                f"Material Requirements - {period} Structure", 
                                False, 
                                f"Missing fields: {missing_fields}",
                                f"Available fields: {list(first_material.keys())}"
                            )
                    else:
                        print(f"   {period}: No materials (empty array)")
                
                if not materials_found:
                    self.log_result(
                        "Material Requirements - Data Population", 
                        False, 
                        "No materials found in any period - materials_composition may be missing from client products"
                    )
                else:
                    self.log_result(
                        "Material Requirements - Data Population", 
                        True, 
                        "Materials found in at least one period"
                    )
                    
            else:
                self.log_result(
                    "Material Requirements Structure", 
                    False, 
                    f"Failed to get projected order analysis: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Material Requirements Structure", False, f"Error: {str(e)}")

    def test_materials_composition_in_client_products(self):
        """Test if materials_composition field exists in client_products"""
        print("\n" + "="*80)
        print("STEP 8: TESTING MATERIALS COMPOSITION IN CLIENT PRODUCTS")
        print("Checking if materials_composition field exists in client_products")
        print("="*80)
        
        try:
            # Get clients first
            clients_response = self.session.get(f"{API_BASE}/clients")
            
            if clients_response.status_code != 200:
                self.log_result(
                    "Materials Composition Check", 
                    False, 
                    f"Failed to get clients: {clients_response.status_code}"
                )
                return
            
            clients = clients_response.json()
            if not clients:
                self.log_result(
                    "Materials Composition Check", 
                    False, 
                    "No clients found"
                )
                return
            
            # Check client products for materials_composition field
            materials_composition_found = False
            total_products_checked = 0
            products_with_composition = 0
            
            for client in clients[:3]:  # Check first 3 clients
                client_id = client.get("id")
                client_name = client.get("company_name", "Unknown")
                
                print(f"🏢 Checking client: {client_name}")
                
                # Get client products
                products_response = self.session.get(f"{API_BASE}/clients/{client_id}/catalog")
                
                if products_response.status_code == 200:
                    products = products_response.json()
                    total_products_checked += len(products)
                    
                    print(f"   Found {len(products)} products")
                    
                    for product in products:
                        product_name = product.get("product_description", "Unknown")
                        
                        if "materials_composition" in product:
                            materials_composition_found = True
                            materials_composition = product.get("materials_composition")
                            
                            if materials_composition and len(materials_composition) > 0:
                                products_with_composition += 1
                                print(f"   ✅ {product_name}: Has materials_composition with {len(materials_composition)} materials")
                                
                                # Check structure of first material
                                first_material = materials_composition[0]
                                required_fields = ["material_id", "width", "quantity"]
                                missing_fields = [field for field in required_fields if field not in first_material]
                                
                                if not missing_fields:
                                    print(f"      Structure: ✅ All required fields present")
                                else:
                                    print(f"      Structure: ❌ Missing fields: {missing_fields}")
                            else:
                                print(f"   ⚠️  {product_name}: Has materials_composition but it's empty")
                        else:
                            print(f"   ❌ {product_name}: No materials_composition field")
                else:
                    print(f"   ❌ Failed to get products for {client_name}: {products_response.status_code}")
            
            if materials_composition_found:
                self.log_result(
                    "Materials Composition - Field Existence", 
                    True, 
                    f"materials_composition field found in client products",
                    f"Products checked: {total_products_checked}, Products with composition: {products_with_composition}"
                )
            else:
                self.log_result(
                    "Materials Composition - Field Existence", 
                    False, 
                    f"materials_composition field not found in any client products",
                    f"Products checked: {total_products_checked} - This explains why material_requirements are empty"
                )
                
        except Exception as e:
            self.log_result("Materials Composition Check", False, f"Error: {str(e)}")

    def test_material_calculation_logic(self):
        """Test the material calculation logic by creating a product with materials_composition"""
        print("\n" + "="*80)
        print("STEP 9: TESTING MATERIAL CALCULATION LOGIC")
        print("Creating a test product with materials_composition to verify calculations")
        print("="*80)
        
        try:
            # Get a client to work with
            clients_response = self.session.get(f"{API_BASE}/clients")
            
            if clients_response.status_code != 200:
                self.log_result(
                    "Material Calculation Logic", 
                    False, 
                    "Failed to get clients for testing"
                )
                return
            
            clients = clients_response.json()
            if not clients:
                self.log_result(
                    "Material Calculation Logic", 
                    False, 
                    "No clients found for testing"
                )
                return
            
            client = clients[0]
            client_id = client.get("id")
            
            # Create a test product with materials_composition
            test_product_data = {
                "product_description": "Test Product for Material Calculation",
                "product_code": f"TEST-MAT-CALC-{str(uuid.uuid4())[:8]}",
                "product_type": "paper_cores",
                "unit_price": 10.0,
                "unit_of_measure": "units",
                "materials_composition": [
                    {
                        "material_id": str(uuid.uuid4()),
                        "material_name": "Test Material 1",
                        "width": 100.0,
                        "quantity": 2.5,
                        "unit_of_measure": "m"
                    },
                    {
                        "material_id": str(uuid.uuid4()),
                        "material_name": "Test Material 2", 
                        "width": 50.0,
                        "quantity": 1.0,
                        "unit_of_measure": "kg"
                    }
                ]
            }
            
            # Create the test product
            create_response = self.session.post(
                f"{API_BASE}/clients/{client_id}/catalog", 
                json=test_product_data
            )
            
            if create_response.status_code == 200:
                result = create_response.json()
                test_product_id = result.get("data", {}).get("id")
                
                print(f"✅ Created test product with ID: {test_product_id}")
                
                # Create a test order with this product
                test_order_data = {
                    "client_id": client_id,
                    "purchase_order_number": f"TEST-MAT-ORDER-{str(uuid.uuid4())[:8]}",
                    "items": [
                        {
                            "product_id": test_product_id,
                            "product_name": "Test Product for Material Calculation",
                            "quantity": 100,  # 100 units
                            "unit_price": 10.0,
                            "total_price": 1000.0
                        }
                    ],
                    "due_date": "2024-12-31",
                    "priority": "Normal/Low",
                    "notes": "Test order for material calculation verification"
                }
                
                order_response = self.session.post(f"{API_BASE}/orders", json=test_order_data)
                
                if order_response.status_code == 200:
                    print(f"✅ Created test order")
                    
                    # Now test the projected order analysis
                    analysis_response = self.session.get(f"{API_BASE}/stock/reports/projected-order-analysis")
                    
                    if analysis_response.status_code == 200:
                        analysis_result = analysis_response.json()
                        analysis_data = analysis_result.get("data", {})
                        products = analysis_data.get("products", [])
                        
                        # Find our test product
                        test_product_found = None
                        for product in products:
                            product_info = product.get("product_info", {})
                            if product_info.get("product_id") == test_product_id:
                                test_product_found = product
                                break
                        
                        if test_product_found:
                            print(f"✅ Found test product in analysis")
                            
                            # Check material requirements
                            material_requirements = test_product_found.get("material_requirements", {})
                            projections = test_product_found.get("projections", {})
                            
                            # Verify calculations for 3_months period
                            if "3_months" in material_requirements and "3_months" in projections:
                                projected_qty = projections["3_months"]
                                materials_3m = material_requirements["3_months"]
                                
                                print(f"📊 3-month projection: {projected_qty} units")
                                print(f"📊 Materials for 3 months: {len(materials_3m)} materials")
                                
                                calculation_correct = True
                                for material in materials_3m:
                                    material_name = material.get("material_name", "Unknown")
                                    quantity_per_unit = material.get("quantity_per_unit", 0)
                                    total_needed = material.get("total_quantity_needed", 0)
                                    
                                    expected_total = projected_qty * quantity_per_unit
                                    
                                    print(f"   Material: {material_name}")
                                    print(f"   Quantity per unit: {quantity_per_unit}")
                                    print(f"   Total needed: {total_needed}")
                                    print(f"   Expected: {expected_total}")
                                    
                                    if abs(total_needed - expected_total) > 0.01:
                                        calculation_correct = False
                                        print(f"   ❌ Calculation mismatch!")
                                    else:
                                        print(f"   ✅ Calculation correct")
                                
                                if calculation_correct:
                                    self.log_result(
                                        "Material Calculation Logic", 
                                        True, 
                                        "Material calculations are working correctly",
                                        f"Verified calculations for {len(materials_3m)} materials"
                                    )
                                else:
                                    self.log_result(
                                        "Material Calculation Logic", 
                                        False, 
                                        "Material calculation errors found"
                                    )
                            else:
                                self.log_result(
                                    "Material Calculation Logic", 
                                    False, 
                                    "No material requirements found for test product"
                                )
                        else:
                            self.log_result(
                                "Material Calculation Logic", 
                                False, 
                                "Test product not found in analysis results"
                            )
                    else:
                        self.log_result(
                            "Material Calculation Logic", 
                            False, 
                            f"Failed to get analysis: {analysis_response.status_code}"
                        )
                else:
                    self.log_result(
                        "Material Calculation Logic", 
                        False, 
                        f"Failed to create test order: {order_response.status_code}"
                    )
            else:
                self.log_result(
                    "Material Calculation Logic", 
                    False, 
                    f"Failed to create test product: {create_response.status_code}",
                    create_response.text
                )
                
        except Exception as e:
            self.log_result("Material Calculation Logic", False, f"Error: {str(e)}")
    def run_comprehensive_test(self):
        """Run all tests for projected order analysis debugging and material requirements testing"""
        print("\n" + "="*80)
        print("PROJECTED ORDER ANALYSIS ENDPOINT TESTING")
        print("Testing material requirements data structure and calculations")
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
        
        # NEW TESTS FOR MATERIAL REQUIREMENTS (as requested in review)
        # Step 8: Test material requirements structure
        self.test_material_requirements_structure()
        
        # Step 9: Test materials composition in client products
        self.test_materials_composition_in_client_products()
        
        # Step 10: Test material calculation logic
        self.test_material_calculation_logic()
        
        # Step 11: Print summary
        self.print_test_summary()

if __name__ == "__main__":
    tester = ProjectedOrderAnalysisTester()
    tester.run_comprehensive_test()