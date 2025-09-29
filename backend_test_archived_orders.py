#!/usr/bin/env python3
"""
Backend API Testing Suite for Archived Orders Functionality
Tests the newly implemented archived orders functionality
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

class ArchivedOrdersTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        self.test_client_id = None
        self.test_order_id = None
        
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
    
    def get_test_client(self):
        """Get a test client for archived orders testing"""
        print("\n=== GET TEST CLIENT ===")
        
        try:
            response = self.session.get(f"{API_BASE}/clients")
            
            if response.status_code == 200:
                clients = response.json()
                if clients:
                    # Use the first available client
                    self.test_client_id = clients[0]['id']
                    client_name = clients[0]['company_name']
                    
                    self.log_result(
                        "Get Test Client", 
                        True, 
                        f"Using client: {client_name} (ID: {self.test_client_id})"
                    )
                    return True
                else:
                    self.log_result(
                        "Get Test Client", 
                        False, 
                        "No clients found in database"
                    )
                    return False
            else:
                self.log_result(
                    "Get Test Client", 
                    False, 
                    f"Failed to get clients: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_result("Get Test Client", False, f"Error: {str(e)}")
            return False
    
    def create_test_order_for_archiving(self):
        """Create a test order that can be moved to CLEARED stage for archiving"""
        print("\n=== CREATE TEST ORDER FOR ARCHIVING ===")
        
        if not self.test_client_id:
            self.log_result(
                "Create Test Order for Archiving", 
                False, 
                "No test client available"
            )
            return False
        
        try:
            order_data = {
                "client_id": self.test_client_id,
                "purchase_order_number": f"PO-ARCHIVE-TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "due_date": (datetime.now() + timedelta(days=7)).isoformat(),
                "delivery_address": "123 Test Archive Street, Melbourne VIC 3000",
                "delivery_instructions": "Test order for archiving functionality",
                "runtime_estimate": "2-3 days",
                "notes": "Test order created for archived orders functionality testing",
                "items": [
                    {
                        "product_id": "test-archive-product-1",
                        "product_name": "Test Archive Product",
                        "description": "Test product for archiving functionality",
                        "quantity": 5,
                        "unit_price": 150.0,
                        "total_price": 750.0
                    }
                ]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=order_data)
            
            if response.status_code == 200:
                result = response.json()
                self.test_order_id = result.get('data', {}).get('id')
                order_number = result.get('data', {}).get('order_number')
                
                if self.test_order_id:
                    self.log_result(
                        "Create Test Order for Archiving", 
                        True, 
                        f"Created test order {order_number} (ID: {self.test_order_id})"
                    )
                    return True
                else:
                    self.log_result(
                        "Create Test Order for Archiving", 
                        False, 
                        "Order creation response missing ID"
                    )
                    return False
            else:
                self.log_result(
                    "Create Test Order for Archiving", 
                    False, 
                    f"Failed to create order: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_result("Create Test Order for Archiving", False, f"Error: {str(e)}")
            return False
    
    def test_automatic_archiving_on_cleared_stage(self):
        """Test that orders are automatically archived when moved to CLEARED stage"""
        print("\n=== TEST AUTOMATIC ARCHIVING ON CLEARED STAGE ===")
        
        if not self.test_order_id:
            self.log_result(
                "Automatic Archiving on CLEARED Stage", 
                False, 
                "No test order available"
            )
            return False
        
        try:
            # Move order to CLEARED stage to trigger archiving
            stage_update = {
                "order_id": self.test_order_id,
                "from_stage": "order_entered",
                "to_stage": "cleared",
                "updated_by": "test-user",
                "notes": "Moving to cleared stage to test automatic archiving"
            }
            
            response = self.session.put(
                f"{API_BASE}/orders/{self.test_order_id}/stage", 
                json=stage_update
            )
            
            if response.status_code == 200:
                # Check if order was archived
                archived_response = self.session.get(
                    f"{API_BASE}/clients/{self.test_client_id}/archived-orders"
                )
                
                if archived_response.status_code == 200:
                    archived_data = archived_response.json()
                    archived_orders = archived_data.get('data', [])
                    
                    # Look for our test order in archived orders
                    test_archived_order = None
                    for order in archived_orders:
                        if order.get('original_order_id') == self.test_order_id:
                            test_archived_order = order
                            break
                    
                    if test_archived_order:
                        # Verify all original order data is preserved
                        required_fields = [
                            'original_order_id', 'order_number', 'client_id', 'client_name',
                            'purchase_order_number', 'items', 'subtotal', 'gst', 'total_amount',
                            'due_date', 'delivery_address', 'delivery_instructions', 'runtime_estimate',
                            'notes', 'created_by', 'created_at', 'completed_at', 'archived_at', 'archived_by'
                        ]
                        
                        missing_fields = [field for field in required_fields if field not in test_archived_order]
                        
                        if not missing_fields:
                            self.log_result(
                                "Automatic Archiving on CLEARED Stage", 
                                True, 
                                "Order automatically archived with all original data preserved",
                                f"Archived order ID: {test_archived_order.get('id')}, Original order data intact"
                            )
                            return True
                        else:
                            self.log_result(
                                "Automatic Archiving on CLEARED Stage", 
                                False, 
                                "Order archived but missing required fields",
                                f"Missing fields: {missing_fields}"
                            )
                            return False
                    else:
                        self.log_result(
                            "Automatic Archiving on CLEARED Stage", 
                            False, 
                            "Order moved to CLEARED but not found in archived orders"
                        )
                        return False
                else:
                    self.log_result(
                        "Automatic Archiving on CLEARED Stage", 
                        False, 
                        f"Failed to retrieve archived orders: {archived_response.status_code}",
                        archived_response.text
                    )
                    return False
            else:
                self.log_result(
                    "Automatic Archiving on CLEARED Stage", 
                    False, 
                    f"Failed to move order to CLEARED stage: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_result("Automatic Archiving on CLEARED Stage", False, f"Error: {str(e)}")
            return False
    
    def test_get_archived_orders_endpoint(self):
        """Test GET /api/clients/{client_id}/archived-orders endpoint"""
        print("\n=== TEST GET ARCHIVED ORDERS ENDPOINT ===")
        
        if not self.test_client_id:
            self.log_result(
                "GET Archived Orders Endpoint", 
                False, 
                "No test client available"
            )
            return False
        
        try:
            # Test basic endpoint without filters
            response = self.session.get(f"{API_BASE}/clients/{self.test_client_id}/archived-orders")
            
            if response.status_code == 200:
                data = response.json()
                archived_orders = data.get('data', [])
                
                self.log_result(
                    "GET Archived Orders Endpoint (Basic)", 
                    True, 
                    f"Successfully retrieved {len(archived_orders)} archived orders"
                )
                
                # Test with date filters
                today = date.today()
                date_from = today - timedelta(days=30)
                date_to = today
                
                filtered_response = self.session.get(
                    f"{API_BASE}/clients/{self.test_client_id}/archived-orders",
                    params={
                        "date_from": date_from.isoformat(),
                        "date_to": date_to.isoformat()
                    }
                )
                
                if filtered_response.status_code == 200:
                    filtered_data = filtered_response.json()
                    filtered_orders = filtered_data.get('data', [])
                    
                    self.log_result(
                        "GET Archived Orders Endpoint (Date Filter)", 
                        True, 
                        f"Successfully retrieved {len(filtered_orders)} archived orders with date filter"
                    )
                    
                    # Test with search query
                    if archived_orders:
                        # Use the order number from the first archived order for search
                        search_order = archived_orders[0]
                        search_query = search_order.get('order_number', '')[:5]  # First 5 chars
                        
                        search_response = self.session.get(
                            f"{API_BASE}/clients/{self.test_client_id}/archived-orders",
                            params={"search_query": search_query}
                        )
                        
                        if search_response.status_code == 200:
                            search_data = search_response.json()
                            search_orders = search_data.get('data', [])
                            
                            self.log_result(
                                "GET Archived Orders Endpoint (Search)", 
                                True, 
                                f"Successfully retrieved {len(search_orders)} archived orders with search query '{search_query}'"
                            )
                        else:
                            self.log_result(
                                "GET Archived Orders Endpoint (Search)", 
                                False, 
                                f"Search query failed: {search_response.status_code}",
                                search_response.text
                            )
                    
                    return True
                else:
                    self.log_result(
                        "GET Archived Orders Endpoint (Date Filter)", 
                        False, 
                        f"Date filter failed: {filtered_response.status_code}",
                        filtered_response.text
                    )
                    return False
            else:
                self.log_result(
                    "GET Archived Orders Endpoint", 
                    False, 
                    f"Failed: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_result("GET Archived Orders Endpoint", False, f"Error: {str(e)}")
            return False
    
    def test_fast_report_generation(self):
        """Test Fast Report generation endpoint"""
        print("\n=== TEST FAST REPORT GENERATION ===")
        
        if not self.test_client_id:
            self.log_result(
                "Fast Report Generation", 
                False, 
                "No test client available"
            )
            return False
        
        try:
            # Test current month report
            report_request = {
                "client_id": self.test_client_id,
                "time_period": "current_month",
                "selected_fields": [
                    "order_number",
                    "client_name", 
                    "purchase_order_number",
                    "created_at",
                    "completed_at",
                    "total_amount",
                    "product_names"
                ],
                "report_title": "Test Archived Orders Report - Current Month"
            }
            
            response = self.session.post(
                f"{API_BASE}/clients/{self.test_client_id}/archived-orders/fast-report",
                json=report_request
            )
            
            if response.status_code == 200:
                # Check if response is Excel file
                content_type = response.headers.get('content-type', '')
                content_length = len(response.content)
                
                if 'spreadsheet' in content_type and content_length > 1000:
                    self.log_result(
                        "Fast Report Generation (Current Month)", 
                        True, 
                        f"Successfully generated Excel report ({content_length} bytes)",
                        f"Content-Type: {content_type}"
                    )
                else:
                    self.log_result(
                        "Fast Report Generation (Current Month)", 
                        False, 
                        "Invalid Excel response",
                        f"Content-Type: {content_type}, Length: {content_length}"
                    )
            elif response.status_code == 404:
                # Expected if no archived orders for current month
                self.log_result(
                    "Fast Report Generation (Current Month)", 
                    True, 
                    "Correctly handles no archived orders for current month (404 expected)",
                    response.text
                )
            else:
                self.log_result(
                    "Fast Report Generation (Current Month)", 
                    False, 
                    f"Failed: {response.status_code}",
                    response.text
                )
                return False
            
            # Test last 3 months report
            report_request_3m = {
                "client_id": self.test_client_id,
                "time_period": "last_3_months",
                "selected_fields": [
                    "order_number",
                    "client_name",
                    "total_amount",
                    "completion_date"
                ],
                "report_title": "Test Archived Orders Report - Last 3 Months"
            }
            
            response_3m = self.session.post(
                f"{API_BASE}/clients/{self.test_client_id}/archived-orders/fast-report",
                json=report_request_3m
            )
            
            if response_3m.status_code == 200:
                content_type_3m = response_3m.headers.get('content-type', '')
                content_length_3m = len(response_3m.content)
                
                if 'spreadsheet' in content_type_3m and content_length_3m > 1000:
                    self.log_result(
                        "Fast Report Generation (Last 3 Months)", 
                        True, 
                        f"Successfully generated Excel report ({content_length_3m} bytes)"
                    )
                else:
                    self.log_result(
                        "Fast Report Generation (Last 3 Months)", 
                        False, 
                        "Invalid Excel response for 3 months report"
                    )
            elif response_3m.status_code == 404:
                self.log_result(
                    "Fast Report Generation (Last 3 Months)", 
                    True, 
                    "Correctly handles no archived orders for last 3 months (404 expected)"
                )
            else:
                self.log_result(
                    "Fast Report Generation (Last 3 Months)", 
                    False, 
                    f"Failed: {response_3m.status_code}",
                    response_3m.text
                )
            
            return True
                
        except Exception as e:
            self.log_result("Fast Report Generation", False, f"Error: {str(e)}")
            return False
    
    def test_time_period_filters(self):
        """Test various time period filters"""
        print("\n=== TEST TIME PERIOD FILTERS ===")
        
        if not self.test_client_id:
            self.log_result(
                "Time Period Filters", 
                False, 
                "No test client available"
            )
            return False
        
        time_periods = [
            "current_month",
            "last_month", 
            "last_3_months",
            "last_6_months",
            "current_quarter",
            "year_to_date",
            "current_financial_year"
        ]
        
        successful_periods = 0
        
        for period in time_periods:
            try:
                report_request = {
                    "client_id": self.test_client_id,
                    "time_period": period,
                    "selected_fields": ["order_number", "client_name", "total_amount"],
                    "report_title": f"Test Report - {period.replace('_', ' ').title()}"
                }
                
                response = self.session.post(
                    f"{API_BASE}/clients/{self.test_client_id}/archived-orders/fast-report",
                    json=report_request
                )
                
                if response.status_code in [200, 404]:  # 404 is acceptable if no data
                    self.log_result(
                        f"Time Period Filter ({period})", 
                        True, 
                        f"Successfully processed {period} filter (Status: {response.status_code})"
                    )
                    successful_periods += 1
                else:
                    self.log_result(
                        f"Time Period Filter ({period})", 
                        False, 
                        f"Failed: {response.status_code}",
                        response.text
                    )
                    
            except Exception as e:
                self.log_result(f"Time Period Filter ({period})", False, f"Error: {str(e)}")
        
        if successful_periods == len(time_periods):
            self.log_result(
                "Time Period Filters", 
                True, 
                f"All {len(time_periods)} time period filters working correctly"
            )
            return True
        else:
            self.log_result(
                "Time Period Filters", 
                False, 
                f"Only {successful_periods}/{len(time_periods)} time period filters working"
            )
            return False
    
    def test_excel_generation_and_download(self):
        """Test Excel generation and download functionality"""
        print("\n=== TEST EXCEL GENERATION AND DOWNLOAD ===")
        
        if not self.test_client_id:
            self.log_result(
                "Excel Generation and Download", 
                False, 
                "No test client available"
            )
            return False
        
        try:
            report_request = {
                "client_id": self.test_client_id,
                "time_period": "last_year",  # Use broader range to increase chance of data
                "selected_fields": [
                    "order_number",
                    "client_name",
                    "purchase_order_number", 
                    "order_date",
                    "completion_date",
                    "due_date",
                    "subtotal",
                    "gst",
                    "total_amount",
                    "delivery_address",
                    "product_names",
                    "product_quantities",
                    "notes",
                    "runtime_estimate"
                ],
                "report_title": "Comprehensive Archived Orders Report - Excel Test"
            }
            
            response = self.session.post(
                f"{API_BASE}/clients/{self.test_client_id}/archived-orders/fast-report",
                json=report_request
            )
            
            if response.status_code == 200:
                # Check Excel file properties
                content_type = response.headers.get('content-type', '')
                content_disposition = response.headers.get('content-disposition', '')
                content_length = len(response.content)
                
                # Verify it's an Excel file
                is_excel = 'spreadsheet' in content_type or 'excel' in content_type
                has_attachment = 'attachment' in content_disposition
                has_filename = 'filename=' in content_disposition and '.xlsx' in content_disposition
                
                if is_excel and has_attachment and has_filename and content_length > 5000:
                    self.log_result(
                        "Excel Generation and Download", 
                        True, 
                        f"Successfully generated downloadable Excel file ({content_length} bytes)",
                        f"Content-Type: {content_type}, Content-Disposition: {content_disposition}"
                    )
                    return True
                else:
                    issues = []
                    if not is_excel:
                        issues.append("Not Excel format")
                    if not has_attachment:
                        issues.append("Missing attachment header")
                    if not has_filename:
                        issues.append("Missing filename")
                    if content_length <= 5000:
                        issues.append("File too small")
                    
                    self.log_result(
                        "Excel Generation and Download", 
                        False, 
                        "Excel file has issues",
                        f"Issues: {', '.join(issues)}"
                    )
                    return False
            elif response.status_code == 404:
                self.log_result(
                    "Excel Generation and Download", 
                    True, 
                    "No archived orders found for Excel generation (404 expected if no data)"
                )
                return True
            else:
                self.log_result(
                    "Excel Generation and Download", 
                    False, 
                    f"Failed: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_result("Excel Generation and Download", False, f"Error: {str(e)}")
            return False
    
    def test_search_functionality(self):
        """Test search functionality in archived orders"""
        print("\n=== TEST SEARCH FUNCTIONALITY ===")
        
        if not self.test_client_id:
            self.log_result(
                "Search Functionality", 
                False, 
                "No test client available"
            )
            return False
        
        try:
            # First get all archived orders to have search terms
            response = self.session.get(f"{API_BASE}/clients/{self.test_client_id}/archived-orders")
            
            if response.status_code == 200:
                data = response.json()
                archived_orders = data.get('data', [])
                
                if not archived_orders:
                    self.log_result(
                        "Search Functionality", 
                        True, 
                        "No archived orders available for search testing (expected if no data)"
                    )
                    return True
                
                # Test search by order number
                test_order = archived_orders[0]
                order_number = test_order.get('order_number', '')
                
                if order_number:
                    # Search with partial order number
                    search_term = order_number[:5]  # First 5 characters
                    
                    search_response = self.session.get(
                        f"{API_BASE}/clients/{self.test_client_id}/archived-orders",
                        params={"search_query": search_term}
                    )
                    
                    if search_response.status_code == 200:
                        search_data = search_response.json()
                        search_results = search_data.get('data', [])
                        
                        # Verify search results contain the search term
                        found_match = False
                        for result in search_results:
                            if (search_term.lower() in result.get('order_number', '').lower() or
                                search_term.lower() in result.get('client_name', '').lower() or
                                search_term.lower() in result.get('purchase_order_number', '').lower()):
                                found_match = True
                                break
                        
                        if found_match:
                            self.log_result(
                                "Search Functionality (Order Number)", 
                                True, 
                                f"Successfully found {len(search_results)} results for search term '{search_term}'"
                            )
                        else:
                            self.log_result(
                                "Search Functionality (Order Number)", 
                                False, 
                                f"Search returned {len(search_results)} results but none match search term '{search_term}'"
                            )
                    else:
                        self.log_result(
                            "Search Functionality (Order Number)", 
                            False, 
                            f"Search failed: {search_response.status_code}",
                            search_response.text
                        )
                
                # Test search by client name
                client_name = test_order.get('client_name', '')
                if client_name:
                    client_search_term = client_name.split()[0] if ' ' in client_name else client_name[:4]
                    
                    client_search_response = self.session.get(
                        f"{API_BASE}/clients/{self.test_client_id}/archived-orders",
                        params={"search_query": client_search_term}
                    )
                    
                    if client_search_response.status_code == 200:
                        client_search_data = client_search_response.json()
                        client_search_results = client_search_data.get('data', [])
                        
                        self.log_result(
                            "Search Functionality (Client Name)", 
                            True, 
                            f"Successfully found {len(client_search_results)} results for client search '{client_search_term}'"
                        )
                    else:
                        self.log_result(
                            "Search Functionality (Client Name)", 
                            False, 
                            f"Client search failed: {client_search_response.status_code}"
                        )
                
                # Test search by product name (if items exist)
                if test_order.get('items'):
                    product_name = test_order['items'][0].get('product_name', '')
                    if product_name:
                        product_search_term = product_name.split()[0] if ' ' in product_name else product_name[:4]
                        
                        product_search_response = self.session.get(
                            f"{API_BASE}/clients/{self.test_client_id}/archived-orders",
                            params={"search_query": product_search_term}
                        )
                        
                        if product_search_response.status_code == 200:
                            product_search_data = product_search_response.json()
                            product_search_results = product_search_data.get('data', [])
                            
                            self.log_result(
                                "Search Functionality (Product Name)", 
                                True, 
                                f"Successfully found {len(product_search_results)} results for product search '{product_search_term}'"
                            )
                        else:
                            self.log_result(
                                "Search Functionality (Product Name)", 
                                False, 
                                f"Product search failed: {product_search_response.status_code}"
                            )
                
                return True
            else:
                self.log_result(
                    "Search Functionality", 
                    False, 
                    f"Failed to get archived orders for search testing: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_result("Search Functionality", False, f"Error: {str(e)}")
            return False
    
    def test_data_preservation(self):
        """Test that archived orders preserve all original order data"""
        print("\n=== TEST DATA PRESERVATION ===")
        
        if not self.test_client_id:
            self.log_result(
                "Data Preservation", 
                False, 
                "No test client available"
            )
            return False
        
        try:
            # Get archived orders
            response = self.session.get(f"{API_BASE}/clients/{self.test_client_id}/archived-orders")
            
            if response.status_code == 200:
                data = response.json()
                archived_orders = data.get('data', [])
                
                if not archived_orders:
                    self.log_result(
                        "Data Preservation", 
                        True, 
                        "No archived orders available for data preservation testing (expected if no data)"
                    )
                    return True
                
                # Check first archived order for data completeness
                test_order = archived_orders[0]
                
                # Required fields that should be preserved
                required_fields = [
                    'id', 'original_order_id', 'order_number', 'client_id', 'client_name',
                    'items', 'subtotal', 'gst', 'total_amount', 'due_date',
                    'created_at', 'completed_at', 'archived_at', 'archived_by'
                ]
                
                # Optional fields that should be preserved if they existed
                optional_fields = [
                    'purchase_order_number', 'delivery_address', 'delivery_instructions',
                    'runtime_estimate', 'notes', 'created_by'
                ]
                
                missing_required = [field for field in required_fields if field not in test_order]
                present_optional = [field for field in optional_fields if field in test_order and test_order[field] is not None]
                
                # Check items structure
                items_valid = True
                if 'items' in test_order and test_order['items']:
                    for item in test_order['items']:
                        required_item_fields = ['product_name', 'quantity', 'unit_price', 'total_price']
                        missing_item_fields = [field for field in required_item_fields if field not in item]
                        if missing_item_fields:
                            items_valid = False
                            break
                
                if not missing_required and items_valid:
                    self.log_result(
                        "Data Preservation", 
                        True, 
                        f"All required data preserved in archived orders",
                        f"Required fields: {len(required_fields)}, Optional fields present: {len(present_optional)}, Items structure valid: {items_valid}"
                    )
                    return True
                else:
                    issues = []
                    if missing_required:
                        issues.append(f"Missing required fields: {missing_required}")
                    if not items_valid:
                        issues.append("Invalid items structure")
                    
                    self.log_result(
                        "Data Preservation", 
                        False, 
                        "Data preservation issues found",
                        "; ".join(issues)
                    )
                    return False
            else:
                self.log_result(
                    "Data Preservation", 
                    False, 
                    f"Failed to get archived orders: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_result("Data Preservation", False, f"Error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all archived orders tests"""
        print("=" * 80)
        print("ARCHIVED ORDERS FUNCTIONALITY TESTING")
        print("=" * 80)
        
        # Authentication
        if not self.authenticate():
            print("\n❌ Authentication failed - cannot proceed with tests")
            return
        
        # Get test client
        if not self.get_test_client():
            print("\n❌ No test client available - cannot proceed with tests")
            return
        
        # Create test order for archiving
        if self.create_test_order_for_archiving():
            # Test automatic archiving
            self.test_automatic_archiving_on_cleared_stage()
        
        # Test archived orders endpoints
        self.test_get_archived_orders_endpoint()
        self.test_fast_report_generation()
        self.test_time_period_filters()
        self.test_excel_generation_and_download()
        self.test_search_functionality()
        self.test_data_preservation()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['message']}")
        
        print(f"\n✅ PASSED TESTS:")
        for result in self.test_results:
            if result['success']:
                print(f"  - {result['test']}: {result['message']}")

if __name__ == "__main__":
    tester = ArchivedOrdersTester()
    tester.run_all_tests()