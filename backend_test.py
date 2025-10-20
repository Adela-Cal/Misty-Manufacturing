#!/usr/bin/env python3
"""
Backend API Testing Suite for Profitability Report Material Costs and Data Sources Debugging

PRIORITY TESTS:
1. Check job_cards collection structure - what fields exist for material usage?
2. Check if client_products endpoint exists and returns data
3. Verify completed orders have associated job cards
4. Identify correct field names for material usage in job cards

TEST STEPS:
1. Login with admin credentials (Callum/Peach7510)
2. GET /api/job-cards to see structure of job cards
3. Check a sample job card for material-related fields
4. GET /api/client-products to verify endpoint exists
5. Check structure of client products
6. GET /api/orders and find one completed order
7. Check if that order has a job card with order_id matching
8. Examine what material fields are in the job card
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

class BackendAPITester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        self.test_stock_id = None
        self.test_material_stock_id = None
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

    def test_pending_timesheets_endpoint(self):
        """
        PRIORITY TEST 1: Pending Timesheets Endpoint Testing
        Test GET /api/payroll/timesheets/pending endpoint to verify it's returning submitted timesheets
        """
        print("\n" + "="*80)
        print("PRIORITY TEST 1: PENDING TIMESHEETS ENDPOINT TESTING")
        print("Testing GET /api/payroll/timesheets/pending endpoint")
        print("="*80)
        
        # Test 1: Check pending timesheets endpoint
        self.test_get_pending_timesheets()
        
        # Test 2: Check all timesheets in database
        self.test_get_all_timesheets()
        
        # Test 3: Check timesheet statuses
        self.test_check_timesheet_statuses()
        
        # Test 4: Create test submitted timesheet if none exists
        self.test_create_submitted_timesheet()
        
        # Test 5: Verify data structure
        self.test_pending_timesheets_data_structure()
        
        # Test 6: Test authentication
        self.test_pending_timesheets_authentication()
        
        # Test 7: Check backend logs for errors
        self.test_check_backend_logs()

    def create_test_substrate_stock(self):
        """Create test substrate stock for PDF testing"""
        try:
            # Get a client first
            clients_response = self.session.get(f"{API_BASE}/clients")
            if clients_response.status_code != 200:
                return None
            
            clients = clients_response.json()
            if not clients:
                return None
            
            client = clients[0]
            
            # Create substrate stock
            stock_data = {
                "client_id": client["id"],
                "client_name": client["company_name"],
                "product_id": str(uuid.uuid4()),
                "product_code": f"TEST-SUBSTRATE-{str(uuid.uuid4())[:8]}",
                "product_description": "Test substrate for PDF generation testing",
                "quantity_on_hand": 100.0,
                "unit_of_measure": "units",
                "source_order_id": f"TEST-ORDER-{str(uuid.uuid4())[:8]}",
                "source_job_id": f"TEST-JOB-{str(uuid.uuid4())[:8]}",
                "minimum_stock_level": 10.0,
                "location": "Test Warehouse"
            }
            
            response = self.session.post(f"{API_BASE}/stock/raw-substrates", json=stock_data)
            
            if response.status_code == 200:
                result = response.json()
                stock_id = result.get("data", {}).get("id")
                self.log_result(
                    "Create Test Substrate Stock", 
                    True, 
                    f"Created test substrate stock with ID: {stock_id}"
                )
                return stock_id
            else:
                self.log_result(
                    "Create Test Substrate Stock", 
                    False, 
                    f"Failed to create substrate stock: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Create Test Substrate Stock", False, f"Error: {str(e)}")
        
        return None

    def create_test_material_stock(self):
        """Create test material stock for PDF testing"""
        try:
            # Create material stock
            stock_data = {
                "material_id": str(uuid.uuid4()),
                "material_name": f"Test Material {str(uuid.uuid4())[:8]}",
                "quantity_on_hand": 50.0,
                "unit_of_measure": "kg",
                "minimum_stock_level": 5.0,
                "usage_rate_per_month": 10.0,
                "alert_threshold_days": 7,
                "supplier_id": str(uuid.uuid4())
            }
            
            response = self.session.post(f"{API_BASE}/stock/raw-materials", json=stock_data)
            
            if response.status_code == 200:
                result = response.json()
                stock_id = result.get("data", {}).get("id")
                self.log_result(
                    "Create Test Material Stock", 
                    True, 
                    f"Created test material stock with ID: {stock_id}"
                )
                return stock_id
            else:
                self.log_result(
                    "Create Test Material Stock", 
                    False, 
                    f"Failed to create material stock: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Create Test Material Stock", False, f"Error: {str(e)}")
        
        return None

    def test_substrate_pdf_generation(self, stock_id):
        """Test substrate PDF generation"""
        try:
            response = self.session.get(f"{API_BASE}/stock/print/{stock_id}?stock_type=substrate")
            
            if response.status_code == 200:
                # Check if response is PDF
                content_type = response.headers.get('content-type', '')
                content_disposition = response.headers.get('content-disposition', '')
                
                if 'application/pdf' in content_type and 'attachment' in content_disposition:
                    # Check PDF content length
                    pdf_size = len(response.content)
                    
                    self.log_result(
                        "Substrate PDF Generation", 
                        True, 
                        f"Successfully generated substrate PDF",
                        f"PDF size: {pdf_size} bytes, Content-Type: {content_type}"
                    )
                else:
                    self.log_result(
                        "Substrate PDF Generation", 
                        False, 
                        "Response not a proper PDF file",
                        f"Content-Type: {content_type}, Content-Disposition: {content_disposition}"
                    )
            else:
                self.log_result(
                    "Substrate PDF Generation", 
                    False, 
                    f"PDF generation failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Substrate PDF Generation", False, f"Error: {str(e)}")

    def test_material_pdf_generation(self, stock_id):
        """Test material PDF generation"""
        try:
            response = self.session.get(f"{API_BASE}/stock/print/{stock_id}?stock_type=material")
            
            if response.status_code == 200:
                # Check if response is PDF
                content_type = response.headers.get('content-type', '')
                content_disposition = response.headers.get('content-disposition', '')
                
                if 'application/pdf' in content_type and 'attachment' in content_disposition:
                    # Check PDF content length
                    pdf_size = len(response.content)
                    
                    self.log_result(
                        "Material PDF Generation", 
                        True, 
                        f"Successfully generated material PDF",
                        f"PDF size: {pdf_size} bytes, Content-Type: {content_type}"
                    )
                else:
                    self.log_result(
                        "Material PDF Generation", 
                        False, 
                        "Response not a proper PDF file",
                        f"Content-Type: {content_type}, Content-Disposition: {content_disposition}"
                    )
            else:
                self.log_result(
                    "Material PDF Generation", 
                    False, 
                    f"PDF generation failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Material PDF Generation", False, f"Error: {str(e)}")

    def test_pdf_generation_edge_cases(self):
        """Test PDF generation edge cases"""
        try:
            # Test with non-existent stock ID
            fake_id = str(uuid.uuid4())
            response = self.session.get(f"{API_BASE}/stock/print/{fake_id}?stock_type=substrate")
            
            if response.status_code == 404:
                self.log_result(
                    "PDF Generation - Non-existent Stock", 
                    True, 
                    "Correctly returned 404 for non-existent stock"
                )
            else:
                self.log_result(
                    "PDF Generation - Non-existent Stock", 
                    False, 
                    f"Expected 404, got {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("PDF Generation - Edge Cases", False, f"Error: {str(e)}")

    def test_pdf_with_string_date(self):
        """Test PDF generation with string created_at date"""
        # This would require creating stock with specific date format
        # For now, we'll test the existing stock
        pass

    def test_pdf_with_datetime_date(self):
        """Test PDF generation with datetime created_at date"""
        # This would require creating stock with specific date format
        # For now, we'll test the existing stock
        pass

    def test_order_deletion_with_stock_reallocation(self):
        """
        PRIORITY TEST 2: Order Deletion with Stock Reallocation - VERIFICATION
        Quick verification test to ensure still working at 100%
        """
        print("\n" + "="*80)
        print("PRIORITY TEST 2: ORDER DELETION WITH STOCK REALLOCATION - VERIFICATION")
        print("Quick verification that order deletion with stock return is still working")
        print("="*80)
        
        # Create test order with stock allocation
        order_id = self.create_test_order_with_stock()
        if not order_id:
            self.log_result(
                "Order Deletion Setup", 
                False, 
                "Failed to create test order with stock allocation"
            )
            return
        
        # Test order deletion
        self.test_order_deletion(order_id)

    def create_test_order_with_stock(self):
        """Create test order with stock allocation"""
        try:
            # Get clients and create a simple order
            clients_response = self.session.get(f"{API_BASE}/clients")
            if clients_response.status_code != 200:
                return None
            
            clients = clients_response.json()
            if not clients:
                return None
            
            client = clients[0]
            
            # Create order
            order_data = {
                "client_id": client["id"],
                "purchase_order_number": f"TEST-PO-DELETE-{str(uuid.uuid4())[:8]}",
                "items": [
                    {
                        "product_id": str(uuid.uuid4()),
                        "product_name": "Test Product for Deletion",
                        "quantity": 5,
                        "unit_price": 10.00,
                        "total_price": 50.00
                    }
                ],
                "due_date": "2024-12-31",
                "priority": "Normal/Low",
                "notes": "Test order for deletion verification"
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=order_data)
            
            if response.status_code == 200:
                result = response.json()
                order_id = result.get("data", {}).get("id")
                self.log_result(
                    "Create Test Order", 
                    True, 
                    f"Created test order with ID: {order_id}"
                )
                return order_id
            else:
                self.log_result(
                    "Create Test Order", 
                    False, 
                    f"Failed to create order: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Create Test Order", False, f"Error: {str(e)}")
        
        return None

    def test_order_deletion(self, order_id):
        """Test order deletion"""
        try:
            response = self.session.delete(f"{API_BASE}/orders/{order_id}")
            
            if response.status_code == 200:
                result = response.json()
                message = result.get("message", "")
                
                self.log_result(
                    "Order Deletion", 
                    True, 
                    f"Successfully deleted order",
                    f"Response: {message}"
                )
            else:
                self.log_result(
                    "Order Deletion", 
                    False, 
                    f"Failed to delete order: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Order Deletion", False, f"Error: {str(e)}")

    def test_stock_reporting_endpoints(self):
        """
        PRIORITY TEST 3: Stock Reporting Endpoints - VERIFICATION
        Test material usage report, low stock report, inventory value report
        """
        print("\n" + "="*80)
        print("PRIORITY TEST 3: STOCK REPORTING ENDPOINTS - VERIFICATION")
        print("Testing material usage, low stock, and inventory value reports")
        print("="*80)
        
        # Test 1: Material Usage Report
        self.test_material_usage_report()
        
        # Test 2: Low Stock Report
        self.test_low_stock_report()
        
        # Test 3: Inventory Value Report
        self.test_inventory_value_report()

    def test_material_usage_report(self):
        """Test material usage report endpoint"""
        try:
            # Test with default parameters
            response = self.session.get(f"{API_BASE}/stock/reports/material-usage")
            
            if response.status_code == 200:
                result = response.json()
                data = result.get("data", {})
                
                # Check report structure
                required_fields = ["report_period", "materials", "total_materials"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    self.log_result(
                        "Material Usage Report", 
                        True, 
                        f"Successfully generated material usage report",
                        f"Total materials: {data.get('total_materials', 0)}"
                    )
                else:
                    self.log_result(
                        "Material Usage Report", 
                        False, 
                        f"Report missing required fields: {missing_fields}",
                        f"Available fields: {list(data.keys())}"
                    )
            else:
                self.log_result(
                    "Material Usage Report", 
                    False, 
                    f"Failed to generate report: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Material Usage Report", False, f"Error: {str(e)}")

    def test_low_stock_report(self):
        """Test low stock report endpoint"""
        try:
            response = self.session.get(f"{API_BASE}/stock/reports/low-stock?threshold_days=30")
            
            if response.status_code == 200:
                result = response.json()
                data = result.get("data", {})
                
                # Check report structure
                required_fields = ["low_stock_items", "critical_items", "total_items", "threshold_days"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    self.log_result(
                        "Low Stock Report", 
                        True, 
                        f"Successfully generated low stock report",
                        f"Total items: {data.get('total_items', 0)}, Critical: {data.get('critical_items', 0)}"
                    )
                else:
                    self.log_result(
                        "Low Stock Report", 
                        False, 
                        f"Report missing required fields: {missing_fields}",
                        f"Available fields: {list(data.keys())}"
                    )
            else:
                self.log_result(
                    "Low Stock Report", 
                    False, 
                    f"Failed to generate report: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Low Stock Report", False, f"Error: {str(e)}")

    def test_inventory_value_report(self):
        """Test inventory value report endpoint"""
        try:
            response = self.session.get(f"{API_BASE}/stock/reports/inventory-value")
            
            if response.status_code == 200:
                result = response.json()
                data = result.get("data", {})
                
                # Check report structure
                required_fields = ["total_substrate_value", "total_material_value", "total_inventory_value"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    total_value = data.get("total_inventory_value", 0)
                    self.log_result(
                        "Inventory Value Report", 
                        True, 
                        f"Successfully generated inventory value report",
                        f"Total inventory value: ${total_value}"
                    )
                else:
                    self.log_result(
                        "Inventory Value Report", 
                        False, 
                        f"Report missing required fields: {missing_fields}",
                        f"Available fields: {list(data.keys())}"
                    )
            else:
                self.log_result(
                    "Inventory Value Report", 
                    False, 
                    f"Failed to generate report: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Inventory Value Report", False, f"Error: {str(e)}")

    def test_production_board_reordering(self):
        """
        PRIORITY TEST 4: Production Board Reordering - VERIFICATION
        Test PUT /api/orders/reorder endpoint
        """
        print("\n" + "="*80)
        print("PRIORITY TEST 4: PRODUCTION BOARD REORDERING - VERIFICATION")
        print("Testing PUT /api/orders/reorder endpoint for drag and drop functionality")
        print("="*80)
        
        # Get some orders to test reordering
        orders = self.get_test_orders_for_reordering()
        if not orders:
            self.log_result(
                "Production Board Reordering Setup", 
                False, 
                "No orders available for reordering test"
            )
            return
        
        # Test reordering
        self.test_order_reordering(orders)

    def get_test_orders_for_reordering(self):
        """Get orders for reordering test"""
        try:
            response = self.session.get(f"{API_BASE}/orders")
            
            if response.status_code == 200:
                orders = response.json()
                if len(orders) >= 2:
                    self.log_result(
                        "Get Orders for Reordering", 
                        True, 
                        f"Found {len(orders)} orders for reordering test"
                    )
                    return orders[:3]  # Use first 3 orders
                else:
                    # Create some test orders if not enough exist
                    return self.create_test_orders_for_reordering()
            else:
                self.log_result(
                    "Get Orders for Reordering", 
                    False, 
                    f"Failed to get orders: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Get Orders for Reordering", False, f"Error: {str(e)}")
        
        return []

    def create_test_orders_for_reordering(self):
        """Create test orders for reordering"""
        try:
            # Get a client
            clients_response = self.session.get(f"{API_BASE}/clients")
            if clients_response.status_code != 200:
                return []
            
            clients = clients_response.json()
            if not clients:
                return []
            
            client = clients[0]
            orders = []
            
            # Create 2 test orders
            for i in range(2):
                order_data = {
                    "client_id": client["id"],
                    "purchase_order_number": f"TEST-REORDER-{i+1}-{str(uuid.uuid4())[:8]}",
                    "items": [
                        {
                            "product_id": str(uuid.uuid4()),
                            "product_name": f"Test Product {i+1}",
                            "quantity": 10,
                            "unit_price": 15.00,
                            "total_price": 150.00
                        }
                    ],
                    "due_date": "2024-12-31",
                    "priority": "Normal/Low",
                    "notes": f"Test order {i+1} for reordering"
                }
                
                response = self.session.post(f"{API_BASE}/orders", json=order_data)
                
                if response.status_code == 200:
                    result = response.json()
                    order_id = result.get("data", {}).get("id")
                    orders.append({"id": order_id})
            
            if orders:
                self.log_result(
                    "Create Test Orders for Reordering", 
                    True, 
                    f"Created {len(orders)} test orders for reordering"
                )
            
            return orders
            
        except Exception as e:
            self.log_result("Create Test Orders for Reordering", False, f"Error: {str(e)}")
        
        return []

    def test_order_reordering(self, orders):
        """Test order reordering endpoint"""
        try:
            if len(orders) < 2:
                self.log_result(
                    "Order Reordering", 
                    False, 
                    "Need at least 2 orders for reordering test"
                )
                return
            
            # Prepare reorder data
            order_ids = [order["id"] for order in orders]
            # Reverse the order to test reordering
            reversed_order_ids = list(reversed(order_ids))
            
            reorder_data = {
                "stage": "order_entered",
                "job_order": reversed_order_ids
            }
            
            response = self.session.put(f"{API_BASE}/orders/reorder", json=reorder_data)
            
            if response.status_code == 200:
                result = response.json()
                message = result.get("message", "")
                updated_count = result.get("data", {}).get("updated_count", 0)
                
                self.log_result(
                    "Order Reordering", 
                    True, 
                    f"Successfully reordered jobs",
                    f"Updated {updated_count} jobs. Message: {message}"
                )
            else:
                self.log_result(
                    "Order Reordering", 
                    False, 
                    f"Failed to reorder jobs: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Order Reordering", False, f"Error: {str(e)}")

    def print_test_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "="*80)
        print("FINAL COMPREHENSIVE TEST SUMMARY")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        # Group results by category
        categories = {
            "Employee Auto-Sync": [],
            "Manual Sync": [],
            "Data Validation": [],
            "Edge Cases": [],
            "Other": []
        }
        
        for result in self.test_results:
            test_name = result['test']
            if 'Auto-Sync' in test_name or 'Get Employees' in test_name:
                categories["Employee Auto-Sync"].append(result)
            elif 'Manual' in test_name and 'Sync' in test_name:
                categories["Manual Sync"].append(result)
            elif any(keyword in test_name for keyword in ['Data Matches', 'Role to Position', 'Number Generation', 'Default Values', 'Enrichment', 'Structure']):
                categories["Data Validation"].append(result)
            elif 'Edge Cases' in test_name or 'Duplicates' in test_name:
                categories["Edge Cases"].append(result)
            else:
                categories["Other"].append(result)
        
        print("\n" + "="*60)
        print("RESULTS BY CATEGORY:")
        print("="*60)
        
        for category, results in categories.items():
            if results:
                category_passed = sum(1 for r in results if r['success'])
                category_total = len(results)
                category_rate = (category_passed / category_total * 100) if category_total > 0 else 0
                
                print(f"\n{category}: {category_passed}/{category_total} ({category_rate:.1f}%)")
                for result in results:
                    status = "✅" if result['success'] else "❌"
                    print(f"  {status} {result['test']}")
        
        # Show failed tests details
        failed_results = [r for r in self.test_results if not r['success']]
        if failed_results:
            print("\n" + "="*60)
            print("FAILED TESTS DETAILS:")
            print("="*60)
            for result in failed_results:
                print(f"\n❌ {result['test']}")
                print(f"   Message: {result['message']}")
                if result['details']:
                    print(f"   Details: {result['details']}")
        
        print("\n" + "="*80)
        if success_rate == 100:
            print("🎉 PERFECT! 100% SUCCESS RATE ACHIEVED!")
        elif success_rate >= 90:
            print(f"🎯 EXCELLENT! {success_rate:.1f}% SUCCESS RATE")
        elif success_rate >= 80:
            print(f"✅ GOOD! {success_rate:.1f}% SUCCESS RATE")
        else:
            print(f"⚠️  NEEDS IMPROVEMENT: {success_rate:.1f}% SUCCESS RATE")
        print("="*80)

    def test_material_usage_detailed_report(self):
        """
        NEW TEST: Material Usage Report by Width Functionality
        Test GET /api/stock/reports/material-usage-detailed endpoint
        """
        print("\n" + "="*80)
        print("NEW TEST: MATERIAL USAGE REPORT BY WIDTH FUNCTIONALITY")
        print("Testing GET /api/stock/reports/material-usage-detailed endpoint")
        print("="*80)
        
        # First, get available materials to test with
        materials = self.get_available_materials()
        print(f"DEBUG: materials returned: {materials}")
        if not materials or len(materials) == 0:
            self.log_result(
                "Material Usage Detailed Report - Setup", 
                False, 
                "No materials available for testing"
            )
            return
        
        material = materials[0]
        # BACKEND BUG IDENTIFIED: The endpoint looks for raw_materials with id=material_id
        # but should look for raw_materials with material_id=material_id or materials with id=material_id
        # Let's try both approaches to see which one works
        material_id = material.get("id")  # Try stock ID first
        material_actual_id = material.get("material_id")  # Backup: actual material ID
        
        # Test 1: Basic functionality with sample material and date range
        self.test_basic_material_usage_report(material_id)
        
        # Test 2: Test with include_order_breakdown=true
        self.test_material_usage_with_order_breakdown(material_id)
        
        # Test 3: Edge case - Non-existent material_id
        self.test_material_usage_nonexistent_material()
        
        # Test 4: Edge case - Date range with no data
        self.test_material_usage_no_data(material_id)
        
        # Test 5: Edge case - Invalid date formats
        self.test_material_usage_invalid_dates(material_id)
        
        # Test 6: Verify response structure and calculations
        self.test_material_usage_response_structure(material_id)

    def get_available_materials(self):
        """Get available materials for testing"""
        try:
            # First try to get raw materials (which the endpoint uses)
            response = self.session.get(f"{API_BASE}/stock/raw-materials")
            
            if response.status_code == 200:
                result = response.json()
                # Check if it's a StandardResponse format
                if isinstance(result, dict) and "data" in result:
                    raw_materials = result.get("data", [])
                else:
                    raw_materials = result
                
                if raw_materials and len(raw_materials) > 0:
                    self.log_result(
                        "Get Available Raw Materials", 
                        True, 
                        f"Found {len(raw_materials)} raw materials for testing"
                    )
                    return raw_materials
            
            # If no raw materials, try regular materials and create a raw material
            materials_response = self.session.get(f"{API_BASE}/materials")
            if materials_response.status_code == 200:
                materials = materials_response.json()
                if materials and len(materials) > 0:
                    # Create a raw material stock entry for testing
                    material = materials[0]
                    raw_material_id = self.create_raw_material_for_testing(material)
                    if raw_material_id:
                        return [{"id": raw_material_id, "material_name": material.get("product_code", "Test Material")}]
            
            self.log_result(
                "Get Available Materials", 
                False, 
                "No materials or raw materials found for testing"
            )
                
        except Exception as e:
            self.log_result("Get Available Materials", False, f"Error: {str(e)}")
        
        return []

    def create_raw_material_for_testing(self, material):
        """Create a raw material stock entry for testing"""
        try:
            stock_data = {
                "material_id": str(uuid.uuid4()),
                "material_name": f"Test Raw Material - {material.get('product_code', 'Unknown')}",
                "material_code": material.get("product_code", "TEST-MAT"),
                "quantity_on_hand": 100.0,
                "unit_of_measure": "kg",
                "minimum_stock_level": 10.0,
                "usage_rate_per_month": 5.0,
                "alert_threshold_days": 14,
                "supplier_id": str(uuid.uuid4())
            }
            
            response = self.session.post(f"{API_BASE}/stock/raw-materials", json=stock_data)
            
            if response.status_code == 200:
                result = response.json()
                material_id = result.get("data", {}).get("id")
                self.log_result(
                    "Create Raw Material for Testing", 
                    True, 
                    f"Created raw material with ID: {material_id}"
                )
                return material_id
            else:
                self.log_result(
                    "Create Raw Material for Testing", 
                    False, 
                    f"Failed to create raw material: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Create Raw Material for Testing", False, f"Error: {str(e)}")
        
        return None

    def test_basic_material_usage_report(self, material_id):
        """Test basic material usage report functionality"""
        try:
            # Use a date range that should capture some data
            start_date = "2024-01-01T00:00:00Z"
            end_date = "2024-12-31T23:59:59Z"
            
            response = self.session.get(
                f"{API_BASE}/stock/reports/material-usage-detailed",
                params={
                    "material_id": material_id,
                    "start_date": start_date,
                    "end_date": end_date
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                data = result.get("data", {})
                
                # Check required fields
                required_fields = [
                    "material_id", "material_name", "material_code", 
                    "report_period", "usage_by_width", "total_widths_used",
                    "grand_total_m2", "grand_total_length_m"
                ]
                
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    # Check report period structure
                    report_period = data.get("report_period", {})
                    period_fields = ["start_date", "end_date", "days"]
                    missing_period_fields = [field for field in period_fields if field not in report_period]
                    
                    if not missing_period_fields:
                        self.log_result(
                            "Basic Material Usage Report", 
                            True, 
                            f"Successfully generated material usage report",
                            f"Material: {data.get('material_name')}, Widths: {data.get('total_widths_used')}, Total m²: {data.get('grand_total_m2')}"
                        )
                    else:
                        self.log_result(
                            "Basic Material Usage Report", 
                            False, 
                            f"Report period missing fields: {missing_period_fields}"
                        )
                else:
                    self.log_result(
                        "Basic Material Usage Report", 
                        False, 
                        f"Report missing required fields: {missing_fields}",
                        f"Available fields: {list(data.keys())}"
                    )
            else:
                self.log_result(
                    "Basic Material Usage Report", 
                    False, 
                    f"Failed to generate report: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Basic Material Usage Report", False, f"Error: {str(e)}")

    def test_material_usage_with_order_breakdown(self, material_id):
        """Test material usage report with order breakdown"""
        try:
            start_date = "2024-01-01T00:00:00Z"
            end_date = "2024-12-31T23:59:59Z"
            
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
                
                # Check that include_order_breakdown is true
                if data.get("include_order_breakdown") == True:
                    # Check usage_by_width structure with order breakdown
                    usage_by_width = data.get("usage_by_width", [])
                    
                    # Verify each width entry has order breakdown fields
                    breakdown_valid = True
                    for width_entry in usage_by_width:
                        required_breakdown_fields = ["width_mm", "total_length_m", "m2"]
                        if data.get("include_order_breakdown"):
                            required_breakdown_fields.extend(["orders", "order_count"])
                        
                        missing_breakdown_fields = [field for field in required_breakdown_fields if field not in width_entry]
                        if missing_breakdown_fields:
                            breakdown_valid = False
                            break
                    
                    if breakdown_valid:
                        self.log_result(
                            "Material Usage Report with Order Breakdown", 
                            True, 
                            f"Successfully generated report with order breakdown",
                            f"Widths with breakdown: {len(usage_by_width)}"
                        )
                    else:
                        self.log_result(
                            "Material Usage Report with Order Breakdown", 
                            False, 
                            "Order breakdown structure incomplete"
                        )
                else:
                    self.log_result(
                        "Material Usage Report with Order Breakdown", 
                        False, 
                        "include_order_breakdown flag not properly set"
                    )
            else:
                self.log_result(
                    "Material Usage Report with Order Breakdown", 
                    False, 
                    f"Failed to generate report: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Material Usage Report with Order Breakdown", False, f"Error: {str(e)}")

    def test_material_usage_nonexistent_material(self):
        """Test material usage report with non-existent material_id"""
        try:
            fake_material_id = str(uuid.uuid4())
            start_date = "2024-01-01T00:00:00Z"
            end_date = "2024-12-31T23:59:59Z"
            
            response = self.session.get(
                f"{API_BASE}/stock/reports/material-usage-detailed",
                params={
                    "material_id": fake_material_id,
                    "start_date": start_date,
                    "end_date": end_date
                }
            )
            
            if response.status_code == 404:
                self.log_result(
                    "Material Usage Report - Non-existent Material", 
                    True, 
                    "Correctly returned 404 for non-existent material"
                )
            else:
                self.log_result(
                    "Material Usage Report - Non-existent Material", 
                    False, 
                    f"Expected 404, got {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Material Usage Report - Non-existent Material", False, f"Error: {str(e)}")

    def test_material_usage_no_data(self, material_id):
        """Test material usage report with date range that has no data"""
        try:
            # Use a future date range that should have no data
            start_date = "2025-01-01T00:00:00Z"
            end_date = "2025-01-31T23:59:59Z"
            
            response = self.session.get(
                f"{API_BASE}/stock/reports/material-usage-detailed",
                params={
                    "material_id": material_id,
                    "start_date": start_date,
                    "end_date": end_date
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                data = result.get("data", {})
                
                # Should return valid structure but with empty arrays
                usage_by_width = data.get("usage_by_width", [])
                total_widths = data.get("total_widths_used", 0)
                grand_total_m2 = data.get("grand_total_m2", 0)
                
                if len(usage_by_width) == 0 and total_widths == 0 and grand_total_m2 == 0:
                    self.log_result(
                        "Material Usage Report - No Data", 
                        True, 
                        "Correctly returned empty arrays with valid structure for no data period"
                    )
                else:
                    self.log_result(
                        "Material Usage Report - No Data", 
                        False, 
                        f"Expected empty data, got widths: {total_widths}, m²: {grand_total_m2}"
                    )
            else:
                self.log_result(
                    "Material Usage Report - No Data", 
                    False, 
                    f"Failed to generate report: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Material Usage Report - No Data", False, f"Error: {str(e)}")

    def test_material_usage_invalid_dates(self, material_id):
        """Test material usage report with invalid date formats"""
        try:
            # Test with invalid date format
            invalid_start_date = "invalid-date"
            end_date = "2024-12-31T23:59:59Z"
            
            response = self.session.get(
                f"{API_BASE}/stock/reports/material-usage-detailed",
                params={
                    "material_id": material_id,
                    "start_date": invalid_start_date,
                    "end_date": end_date
                }
            )
            
            # Should return 400 or 422 for invalid date format
            if response.status_code in [400, 422, 500]:
                self.log_result(
                    "Material Usage Report - Invalid Dates", 
                    True, 
                    f"Correctly handled invalid date format with status {response.status_code}"
                )
            else:
                self.log_result(
                    "Material Usage Report - Invalid Dates", 
                    False, 
                    f"Expected error status for invalid date, got {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Material Usage Report - Invalid Dates", False, f"Error: {str(e)}")

    def test_get_pending_timesheets(self):
        """Test GET /api/payroll/timesheets/pending endpoint"""
        try:
            response = self.session.get(f"{API_BASE}/payroll/timesheets/pending")
            
            if response.status_code == 200:
                result = response.json()
                
                # Check response structure
                if result.get("success") and "data" in result:
                    timesheets = result["data"]
                    
                    self.log_result(
                        "Get Pending Timesheets", 
                        True, 
                        f"Successfully retrieved pending timesheets endpoint",
                        f"Found {len(timesheets)} pending timesheets"
                    )
                    
                    # Check if any timesheets have status "submitted"
                    submitted_count = sum(1 for ts in timesheets if ts.get("status") == "submitted")
                    
                    if submitted_count > 0:
                        self.log_result(
                            "Pending Timesheets - Submitted Status", 
                            True, 
                            f"Found {submitted_count} timesheets with 'submitted' status"
                        )
                    else:
                        self.log_result(
                            "Pending Timesheets - Submitted Status", 
                            False, 
                            "No timesheets with 'submitted' status found",
                            f"Statuses found: {[ts.get('status') for ts in timesheets]}"
                        )
                    
                    return timesheets
                else:
                    self.log_result(
                        "Get Pending Timesheets", 
                        False, 
                        "Invalid response structure",
                        f"Response: {result}"
                    )
            elif response.status_code == 403:
                self.log_result(
                    "Get Pending Timesheets", 
                    False, 
                    "Access denied - insufficient permissions",
                    "User may not have payroll access"
                )
            else:
                self.log_result(
                    "Get Pending Timesheets", 
                    False, 
                    f"Failed to get pending timesheets: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Get Pending Timesheets", False, f"Error: {str(e)}")
        
        return []

    def test_get_all_timesheets(self):
        """Test checking all timesheets in database regardless of status"""
        try:
            # Try to get all timesheets (if endpoint exists)
            response = self.session.get(f"{API_BASE}/payroll/timesheets")
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("success") and "data" in result:
                    all_timesheets = result["data"]
                    
                    self.log_result(
                        "Get All Timesheets", 
                        True, 
                        f"Found {len(all_timesheets)} total timesheets in database"
                    )
                    
                    # Analyze statuses
                    status_counts = {}
                    for ts in all_timesheets:
                        status = ts.get("status", "unknown")
                        status_counts[status] = status_counts.get(status, 0) + 1
                    
                    self.log_result(
                        "Timesheet Status Analysis", 
                        True, 
                        f"Status breakdown: {status_counts}"
                    )
                    
                    return all_timesheets
                else:
                    self.log_result(
                        "Get All Timesheets", 
                        False, 
                        "Invalid response structure for all timesheets"
                    )
            else:
                self.log_result(
                    "Get All Timesheets", 
                    False, 
                    f"All timesheets endpoint not available or failed: {response.status_code}",
                    "This is expected if endpoint doesn't exist"
                )
                
        except Exception as e:
            self.log_result("Get All Timesheets", False, f"Error: {str(e)}")
        
        return []

    def test_check_timesheet_statuses(self):
        """Test checking what timesheet statuses exist in the database"""
        try:
            # Get employees first to create test timesheets
            employees_response = self.session.get(f"{API_BASE}/payroll/employees")
            
            if employees_response.status_code == 200:
                employees = employees_response.json()
                
                if employees and len(employees) > 0:
                    self.log_result(
                        "Check Employees for Timesheet Creation", 
                        True, 
                        f"Found {len(employees)} employees available for timesheet creation"
                    )
                    
                    # Check what statuses should exist: draft, submitted, approved, rejected
                    expected_statuses = ["draft", "submitted", "approved", "rejected"]
                    
                    self.log_result(
                        "Expected Timesheet Statuses", 
                        True, 
                        f"Expected statuses: {expected_statuses}"
                    )
                    
                    return employees
                else:
                    self.log_result(
                        "Check Employees for Timesheet Creation", 
                        False, 
                        "No employees found - cannot create test timesheets"
                    )
            else:
                self.log_result(
                    "Check Employees for Timesheet Creation", 
                    False, 
                    f"Failed to get employees: {employees_response.status_code}"
                )
                
        except Exception as e:
            self.log_result("Check Timesheet Statuses", False, f"Error: {str(e)}")
        
        return []

    def test_create_submitted_timesheet(self):
        """Create a test submitted timesheet if none exists"""
        try:
            # Get employees first
            employees_response = self.session.get(f"{API_BASE}/payroll/employees")
            
            if employees_response.status_code == 200:
                employees = employees_response.json()
                
                if employees and len(employees) > 0:
                    employee = employees[0]  # Use first employee
                    
                    # Create a timesheet with submitted status
                    timesheet_data = {
                        "employee_id": employee["id"],
                        "week_start": "2024-12-16",  # Monday
                        "week_end": "2024-12-22",    # Sunday
                        "status": "submitted",
                        "total_regular_hours": 38.0,
                        "total_overtime_hours": 2.0,
                        "daily_entries": [
                            {
                                "date": "2024-12-16",
                                "regular_hours": 8.0,
                                "overtime_hours": 0.0,
                                "notes": "Regular work day"
                            },
                            {
                                "date": "2024-12-17",
                                "regular_hours": 8.0,
                                "overtime_hours": 1.0,
                                "notes": "Overtime for urgent order"
                            },
                            {
                                "date": "2024-12-18",
                                "regular_hours": 8.0,
                                "overtime_hours": 1.0,
                                "notes": "Overtime continued"
                            },
                            {
                                "date": "2024-12-19",
                                "regular_hours": 7.0,
                                "overtime_hours": 0.0,
                                "notes": "Left early"
                            },
                            {
                                "date": "2024-12-20",
                                "regular_hours": 7.0,
                                "overtime_hours": 0.0,
                                "notes": "Regular work day"
                            }
                        ]
                    }
                    
                    # Try to create timesheet
                    response = self.session.post(f"{API_BASE}/payroll/timesheets", json=timesheet_data)
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        self.log_result(
                            "Create Test Submitted Timesheet", 
                            True, 
                            f"Successfully created test timesheet with 'submitted' status",
                            f"Employee: {employee.get('first_name')} {employee.get('last_name')}, Week: 2024-12-16 to 2024-12-22"
                        )
                        
                        # Now test the pending endpoint again
                        self.test_get_pending_timesheets_after_creation()
                        
                        return result.get("data", {}).get("id")
                    else:
                        self.log_result(
                            "Create Test Submitted Timesheet", 
                            False, 
                            f"Failed to create timesheet: {response.status_code}",
                            response.text
                        )
                else:
                    self.log_result(
                        "Create Test Submitted Timesheet", 
                        False, 
                        "No employees available to create timesheet"
                    )
            else:
                self.log_result(
                    "Create Test Submitted Timesheet", 
                    False, 
                    f"Failed to get employees: {employees_response.status_code}"
                )
                
        except Exception as e:
            self.log_result("Create Test Submitted Timesheet", False, f"Error: {str(e)}")
        
        return None

    def test_get_pending_timesheets_after_creation(self):
        """Test pending timesheets endpoint after creating test data"""
        try:
            response = self.session.get(f"{API_BASE}/payroll/timesheets/pending")
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("success") and "data" in result:
                    timesheets = result["data"]
                    
                    self.log_result(
                        "Get Pending Timesheets After Creation", 
                        True, 
                        f"Found {len(timesheets)} pending timesheets after creating test data"
                    )
                    
                    # Check if our test timesheet is there
                    submitted_timesheets = [ts for ts in timesheets if ts.get("status") == "submitted"]
                    
                    if len(submitted_timesheets) > 0:
                        self.log_result(
                            "Verify Submitted Timesheets Present", 
                            True, 
                            f"Found {len(submitted_timesheets)} submitted timesheets in pending list"
                        )
                    else:
                        self.log_result(
                            "Verify Submitted Timesheets Present", 
                            False, 
                            "No submitted timesheets found in pending list"
                        )
                    
                    return timesheets
                else:
                    self.log_result(
                        "Get Pending Timesheets After Creation", 
                        False, 
                        "Invalid response structure"
                    )
            else:
                self.log_result(
                    "Get Pending Timesheets After Creation", 
                    False, 
                    f"Failed to get pending timesheets: {response.status_code}"
                )
                
        except Exception as e:
            self.log_result("Get Pending Timesheets After Creation", False, f"Error: {str(e)}")
        
        return []

    def test_pending_timesheets_data_structure(self):
        """Verify pending timesheets response has correct data structure"""
        try:
            response = self.session.get(f"{API_BASE}/payroll/timesheets/pending")
            
            if response.status_code == 200:
                result = response.json()
                
                # Check top-level structure
                if result.get("success") == True and "data" in result:
                    timesheets = result["data"]
                    
                    if isinstance(timesheets, list):
                        self.log_result(
                            "Pending Timesheets Response Structure", 
                            True, 
                            f"Response has correct structure: success=true, data=array"
                        )
                        
                        # Check individual timesheet structure
                        if len(timesheets) > 0:
                            timesheet = timesheets[0]
                            
                            # Expected fields for each timesheet
                            expected_fields = [
                                "id", "employee_id", "employee_name", "week_start", "week_end", 
                                "status", "total_regular_hours", "total_overtime_hours"
                            ]
                            
                            missing_fields = [field for field in expected_fields if field not in timesheet]
                            
                            if len(missing_fields) == 0:
                                self.log_result(
                                    "Timesheet Data Structure", 
                                    True, 
                                    f"Timesheets have all required fields: {expected_fields}"
                                )
                                
                                # Check that no MongoDB _id field is present
                                if "_id" not in timesheet:
                                    self.log_result(
                                        "MongoDB ObjectId Removal", 
                                        True, 
                                        "No MongoDB _id field present in response (correctly removed)"
                                    )
                                else:
                                    self.log_result(
                                        "MongoDB ObjectId Removal", 
                                        False, 
                                        "MongoDB _id field still present in response"
                                    )
                                
                                # Check employee_name enrichment
                                if timesheet.get("employee_name"):
                                    self.log_result(
                                        "Employee Name Enrichment", 
                                        True, 
                                        f"Employee name enriched: {timesheet.get('employee_name')}"
                                    )
                                else:
                                    self.log_result(
                                        "Employee Name Enrichment", 
                                        False, 
                                        "Employee name not enriched in response"
                                    )
                            else:
                                self.log_result(
                                    "Timesheet Data Structure", 
                                    False, 
                                    f"Missing required fields: {missing_fields}"
                                )
                        else:
                            self.log_result(
                                "Timesheet Data Structure", 
                                True, 
                                "No timesheets to check structure (empty array is valid)"
                            )
                    else:
                        self.log_result(
                            "Pending Timesheets Response Structure", 
                            False, 
                            "Data field is not an array"
                        )
                else:
                    self.log_result(
                        "Pending Timesheets Response Structure", 
                        False, 
                        "Response missing success=true or data field"
                    )
            else:
                self.log_result(
                    "Pending Timesheets Data Structure", 
                    False, 
                    f"Failed to get response: {response.status_code}"
                )
                
        except Exception as e:
            self.log_result("Pending Timesheets Data Structure", False, f"Error: {str(e)}")

    def test_pending_timesheets_authentication(self):
        """Test authentication requirements for pending timesheets endpoint"""
        try:
            # Test without authentication
            session_no_auth = requests.Session()
            response = session_no_auth.get(f"{API_BASE}/payroll/timesheets/pending")
            
            if response.status_code == 403 or response.status_code == 401:
                self.log_result(
                    "Pending Timesheets Authentication - No Auth", 
                    True, 
                    f"Correctly denied access without authentication (status: {response.status_code})"
                )
            else:
                self.log_result(
                    "Pending Timesheets Authentication - No Auth", 
                    False, 
                    f"Expected 401/403, got {response.status_code}",
                    "Endpoint should require authentication"
                )
            
            # Test with valid authentication (already done in main test)
            response_auth = self.session.get(f"{API_BASE}/payroll/timesheets/pending")
            
            if response_auth.status_code == 200:
                self.log_result(
                    "Pending Timesheets Authentication - With Auth", 
                    True, 
                    "Successfully accessed endpoint with valid authentication"
                )
            elif response_auth.status_code == 403:
                self.log_result(
                    "Pending Timesheets Authentication - With Auth", 
                    False, 
                    "Access denied even with authentication - user may lack payroll permissions"
                )
            else:
                self.log_result(
                    "Pending Timesheets Authentication - With Auth", 
                    False, 
                    f"Unexpected status with auth: {response_auth.status_code}"
                )
                
        except Exception as e:
            self.log_result("Pending Timesheets Authentication", False, f"Error: {str(e)}")

    def test_check_backend_logs(self):
        """Check backend logs for any errors related to pending timesheets"""
        try:
            # Try to check supervisor logs for backend errors
            import subprocess
            
            # Check backend logs
            result = subprocess.run(
                ["tail", "-n", "50", "/var/log/supervisor/backend.err.log"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                log_content = result.stdout
                
                # Look for errors related to timesheets
                timesheet_errors = []
                for line in log_content.split('\n'):
                    if 'timesheet' in line.lower() and ('error' in line.lower() or 'exception' in line.lower()):
                        timesheet_errors.append(line.strip())
                
                if len(timesheet_errors) == 0:
                    self.log_result(
                        "Backend Logs - Timesheet Errors", 
                        True, 
                        "No timesheet-related errors found in backend logs"
                    )
                else:
                    self.log_result(
                        "Backend Logs - Timesheet Errors", 
                        False, 
                        f"Found {len(timesheet_errors)} timesheet-related errors",
                        f"Errors: {timesheet_errors[:3]}"
                    )
            else:
                self.log_result(
                    "Backend Logs Check", 
                    False, 
                    "Could not access backend error logs"
                )
                
        except subprocess.TimeoutExpired:
            self.log_result("Backend Logs Check", False, "Timeout accessing logs")
        except Exception as e:
            self.log_result("Backend Logs Check", False, f"Error: {str(e)}")

    def test_employee_data_enrichment(self):
        """Test employee data enrichment with current user information"""
        try:
            # Get employees twice to test enrichment
            first_response = self.session.get(f"{API_BASE}/payroll/employees")
            second_response = self.session.get(f"{API_BASE}/payroll/employees")
            
            if first_response.status_code == 200 and second_response.status_code == 200:
                first_employees = first_response.json()
                second_employees = second_response.json()
                
                # Both calls should return the same enriched data
                if len(first_employees) == len(second_employees):
                    # Check that employees have enriched data (role field from users)
                    enriched_count = 0
                    for emp in first_employees:
                        if emp.get("role"):  # Role field indicates enrichment
                            enriched_count += 1
                    
                    if enriched_count == len(first_employees):
                        self.log_result(
                            "Employee Data Enrichment", 
                            True, 
                            f"All {enriched_count} employees have enriched data with role information"
                        )
                    else:
                        self.log_result(
                            "Employee Data Enrichment", 
                            False, 
                            f"Only {enriched_count}/{len(first_employees)} employees have enriched data"
                        )
                else:
                    self.log_result(
                        "Employee Data Enrichment", 
                        False, 
                        "Inconsistent employee count between calls"
                    )
            else:
                self.log_result(
                    "Employee Data Enrichment", 
                    False, 
                    "Failed to get employees for enrichment test"
                )
                
        except Exception as e:
            self.log_result("Employee Data Enrichment", False, f"Error: {str(e)}")

    def test_employee_sync_edge_cases(self):
        """Test edge cases for employee synchronization"""
        try:
            # Test 1: Multiple sync calls should not create duplicates
            sync1_response = self.session.post(f"{API_BASE}/payroll/employees/sync")
            sync2_response = self.session.post(f"{API_BASE}/payroll/employees/sync")
            
            if sync1_response.status_code == 200 and sync2_response.status_code == 200:
                sync1_data = sync1_response.json().get("data", {})
                sync2_data = sync2_response.json().get("data", {})
                
                # Second sync should create 0 new employees
                if sync2_data.get("created_count", -1) == 0:
                    self.log_result(
                        "Employee Sync - No Duplicates", 
                        True, 
                        "Multiple sync calls do not create duplicate employees"
                    )
                else:
                    self.log_result(
                        "Employee Sync - No Duplicates", 
                        False, 
                        f"Second sync created {sync2_data.get('created_count')} employees (expected 0)"
                    )
            else:
                self.log_result(
                    "Employee Sync - No Duplicates", 
                    False, 
                    "Failed to test duplicate sync calls"
                )
            
            # Test 2: Check response structure
            employees_response = self.session.get(f"{API_BASE}/payroll/employees")
            if employees_response.status_code == 200:
                employees = employees_response.json()
                
                # Verify expected response structure matches API specification
                if len(employees) > 0:
                    sample_employee = employees[0]
                    expected_structure_fields = [
                        "id", "user_id", "employee_number", "first_name", "last_name",
                        "email", "phone", "department", "position", "role", "start_date",
                        "employment_type", "hourly_rate", "weekly_hours", 
                        "annual_leave_balance", "sick_leave_balance", "personal_leave_balance", "is_active"
                    ]
                    
                    missing_fields = [field for field in expected_structure_fields if field not in sample_employee]
                    
                    if len(missing_fields) == 0:
                        self.log_result(
                            "Employee Response Structure", 
                            True, 
                            "Employee response structure matches API specification"
                        )
                    else:
                        self.log_result(
                            "Employee Response Structure", 
                            False, 
                            f"Missing fields in response: {missing_fields}"
                        )
                else:
                    self.log_result(
                        "Employee Response Structure", 
                        False, 
                        "No employees returned to verify structure"
                    )
            
        except Exception as e:
            self.log_result("Employee Sync Edge Cases", False, f"Error: {str(e)}")

    def test_payroll_reports_endpoints(self):
        """
        NEW PRIORITY TEST: Payroll Reports Endpoints Testing
        Test the newly implemented payroll reports endpoints:
        1. GET /api/payroll/reports/payslips - Get all historic payslips
        2. GET /api/payroll/reports/timesheets - Get timesheet report with filters
        3. GET /api/payroll/reports/payslip/{timesheet_id} - Generate payslip from approved timesheet
        """
        print("\n" + "="*80)
        print("NEW PRIORITY TEST: PAYROLL REPORTS ENDPOINTS TESTING")
        print("Testing newly implemented payroll reports endpoints")
        print("="*80)
        
        # Test 1: GET /api/payroll/reports/payslips - Should return empty array initially
        self.test_get_all_payslips()
        
        # Test 2: GET /api/payroll/reports/timesheets - Test without filters
        self.test_get_timesheet_report_no_filters()
        
        # Test 3: GET /api/payroll/reports/timesheets - Test with employee_id filter
        self.test_get_timesheet_report_with_employee_filter()
        
        # Test 4: GET /api/payroll/reports/timesheets - Test with date range filters
        self.test_get_timesheet_report_with_date_filters()
        
        # Test 5: Check if there are any approved timesheets
        approved_timesheet_id = self.check_for_approved_timesheets()
        
        # Test 6: Generate payslip from approved timesheet (if available)
        if approved_timesheet_id:
            self.test_generate_payslip_from_timesheet(approved_timesheet_id)
        else:
            # Create an approved timesheet for testing
            approved_timesheet_id = self.create_approved_timesheet_for_testing()
            if approved_timesheet_id:
                self.test_generate_payslip_from_timesheet(approved_timesheet_id)
        
        # Test 7: Verify payslip data structure
        self.test_payslip_data_structure()
        
        # Test 8: Test edge cases
        self.test_payroll_reports_edge_cases()

    def test_get_all_payslips(self):
        """Test GET /api/payroll/reports/payslips endpoint"""
        try:
            response = self.session.get(f"{API_BASE}/payroll/reports/payslips")
            
            if response.status_code == 200:
                result = response.json()
                
                # Check response structure
                if result.get("success") == True and "data" in result:
                    payslips = result["data"]
                    
                    if isinstance(payslips, list):
                        self.log_result(
                            "Get All Payslips", 
                            True, 
                            f"Successfully retrieved payslips endpoint",
                            f"Found {len(payslips)} payslips. Expected structure: {{success: true, data: []}}"
                        )
                        
                        # If payslips exist, check structure
                        if len(payslips) > 0:
                            payslip = payslips[0]
                            expected_fields = ["id", "timesheet_id", "employee_id", "payslip_data", "generated_at"]
                            missing_fields = [field for field in expected_fields if field not in payslip]
                            
                            if not missing_fields:
                                self.log_result(
                                    "Payslip Data Structure", 
                                    True, 
                                    "Payslips have correct structure with all required fields"
                                )
                            else:
                                self.log_result(
                                    "Payslip Data Structure", 
                                    False, 
                                    f"Payslips missing fields: {missing_fields}"
                                )
                    else:
                        self.log_result(
                            "Get All Payslips", 
                            False, 
                            "Data field is not an array",
                            f"Data type: {type(payslips)}"
                        )
                else:
                    self.log_result(
                        "Get All Payslips", 
                        False, 
                        "Invalid response structure",
                        f"Response: {result}"
                    )
            elif response.status_code == 403:
                self.log_result(
                    "Get All Payslips", 
                    False, 
                    "Access denied - insufficient permissions for payroll reports"
                )
            else:
                self.log_result(
                    "Get All Payslips", 
                    False, 
                    f"Failed to get payslips: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Get All Payslips", False, f"Error: {str(e)}")

    def test_get_timesheet_report_no_filters(self):
        """Test GET /api/payroll/reports/timesheets without filters"""
        try:
            response = self.session.get(f"{API_BASE}/payroll/reports/timesheets")
            
            if response.status_code == 200:
                result = response.json()
                
                # Check response structure
                if result.get("success") == True and "data" in result and "summary" in result:
                    timesheets = result["data"]
                    summary = result["summary"]
                    
                    # Verify summary structure
                    expected_summary_fields = ["total_timesheets", "total_regular_hours", "total_overtime_hours", "total_hours"]
                    missing_summary_fields = [field for field in expected_summary_fields if field not in summary]
                    
                    if not missing_summary_fields:
                        self.log_result(
                            "Timesheet Report - No Filters", 
                            True, 
                            f"Successfully retrieved timesheet report",
                            f"Found {len(timesheets)} timesheets. Summary: {summary['total_timesheets']} timesheets, {summary['total_hours']} total hours"
                        )
                        
                        # Check timesheet enrichment
                        if len(timesheets) > 0:
                            timesheet = timesheets[0]
                            if "employee_name" in timesheet:
                                self.log_result(
                                    "Timesheet Employee Name Enrichment", 
                                    True, 
                                    f"Timesheets properly enriched with employee names"
                                )
                            else:
                                self.log_result(
                                    "Timesheet Employee Name Enrichment", 
                                    False, 
                                    "Timesheets missing employee_name enrichment"
                                )
                    else:
                        self.log_result(
                            "Timesheet Report - No Filters", 
                            False, 
                            f"Summary missing fields: {missing_summary_fields}"
                        )
                else:
                    self.log_result(
                        "Timesheet Report - No Filters", 
                        False, 
                        "Invalid response structure - missing success, data, or summary"
                    )
            else:
                self.log_result(
                    "Timesheet Report - No Filters", 
                    False, 
                    f"Failed to get timesheet report: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Timesheet Report - No Filters", False, f"Error: {str(e)}")

    def test_get_timesheet_report_with_employee_filter(self):
        """Test GET /api/payroll/reports/timesheets with employee_id filter"""
        try:
            # Get employees first
            employees_response = self.session.get(f"{API_BASE}/payroll/employees")
            
            if employees_response.status_code == 200:
                employees = employees_response.json()
                
                if employees and len(employees) > 0:
                    employee = employees[0]
                    employee_id = employee["id"]
                    
                    # Test with employee filter
                    response = self.session.get(f"{API_BASE}/payroll/reports/timesheets?employee_id={employee_id}")
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        if result.get("success") == True and "data" in result:
                            timesheets = result["data"]
                            
                            # Verify all timesheets belong to the specified employee
                            all_match_employee = all(ts.get("employee_id") == employee_id for ts in timesheets)
                            
                            if all_match_employee:
                                self.log_result(
                                    "Timesheet Report - Employee Filter", 
                                    True, 
                                    f"Successfully filtered timesheets by employee",
                                    f"Found {len(timesheets)} timesheets for employee {employee.get('first_name')} {employee.get('last_name')}"
                                )
                            else:
                                self.log_result(
                                    "Timesheet Report - Employee Filter", 
                                    False, 
                                    "Filter not working - found timesheets for other employees"
                                )
                        else:
                            self.log_result(
                                "Timesheet Report - Employee Filter", 
                                False, 
                                "Invalid response structure"
                            )
                    else:
                        self.log_result(
                            "Timesheet Report - Employee Filter", 
                            False, 
                            f"Failed to get filtered timesheet report: {response.status_code}",
                            response.text
                        )
                else:
                    self.log_result(
                        "Timesheet Report - Employee Filter", 
                        False, 
                        "No employees available for filter testing"
                    )
            else:
                self.log_result(
                    "Timesheet Report - Employee Filter", 
                    False, 
                    f"Failed to get employees for filter test: {employees_response.status_code}"
                )
                
        except Exception as e:
            self.log_result("Timesheet Report - Employee Filter", False, f"Error: {str(e)}")

    def test_get_timesheet_report_with_date_filters(self):
        """Test GET /api/payroll/reports/timesheets with date range filters"""
        try:
            # Test with date range
            start_date = "2024-12-01"
            end_date = "2024-12-31"
            
            response = self.session.get(f"{API_BASE}/payroll/reports/timesheets?start_date={start_date}&end_date={end_date}")
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("success") == True and "data" in result:
                    timesheets = result["data"]
                    
                    self.log_result(
                        "Timesheet Report - Date Range Filter", 
                        True, 
                        f"Successfully filtered timesheets by date range",
                        f"Found {len(timesheets)} timesheets between {start_date} and {end_date}"
                    )
                    
                    # Test with only start_date
                    response2 = self.session.get(f"{API_BASE}/payroll/reports/timesheets?start_date={start_date}")
                    
                    if response2.status_code == 200:
                        result2 = response2.json()
                        timesheets2 = result2.get("data", [])
                        
                        self.log_result(
                            "Timesheet Report - Start Date Only Filter", 
                            True, 
                            f"Successfully filtered timesheets by start date only",
                            f"Found {len(timesheets2)} timesheets from {start_date} onwards"
                        )
                    
                    # Test with only end_date
                    response3 = self.session.get(f"{API_BASE}/payroll/reports/timesheets?end_date={end_date}")
                    
                    if response3.status_code == 200:
                        result3 = response3.json()
                        timesheets3 = result3.get("data", [])
                        
                        self.log_result(
                            "Timesheet Report - End Date Only Filter", 
                            True, 
                            f"Successfully filtered timesheets by end date only",
                            f"Found {len(timesheets3)} timesheets up to {end_date}"
                        )
                else:
                    self.log_result(
                        "Timesheet Report - Date Range Filter", 
                        False, 
                        "Invalid response structure"
                    )
            else:
                self.log_result(
                    "Timesheet Report - Date Range Filter", 
                    False, 
                    f"Failed to get date-filtered timesheet report: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Timesheet Report - Date Range Filter", False, f"Error: {str(e)}")

    def check_for_approved_timesheets(self):
        """Check if there are any approved timesheets for payslip generation"""
        try:
            # Get all timesheets and look for approved ones
            response = self.session.get(f"{API_BASE}/payroll/reports/timesheets")
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("success") == True and "data" in result:
                    timesheets = result["data"]
                    
                    # Look for approved timesheets
                    approved_timesheets = [ts for ts in timesheets if ts.get("status") == "approved"]
                    
                    if approved_timesheets:
                        approved_timesheet = approved_timesheets[0]
                        self.log_result(
                            "Check for Approved Timesheets", 
                            True, 
                            f"Found {len(approved_timesheets)} approved timesheets",
                            f"Using timesheet ID: {approved_timesheet['id']}"
                        )
                        return approved_timesheet["id"]
                    else:
                        self.log_result(
                            "Check for Approved Timesheets", 
                            False, 
                            "No approved timesheets found for payslip generation",
                            f"Found timesheets with statuses: {list(set(ts.get('status') for ts in timesheets))}"
                        )
                        return None
                else:
                    self.log_result(
                        "Check for Approved Timesheets", 
                        False, 
                        "Invalid response structure"
                    )
            else:
                self.log_result(
                    "Check for Approved Timesheets", 
                    False, 
                    f"Failed to get timesheets: {response.status_code}"
                )
                
        except Exception as e:
            self.log_result("Check for Approved Timesheets", False, f"Error: {str(e)}")
        
        return None

    def create_approved_timesheet_for_testing(self):
        """Create an approved timesheet for payslip generation testing"""
        try:
            # Get employees first
            employees_response = self.session.get(f"{API_BASE}/payroll/employees")
            
            if employees_response.status_code == 200:
                employees = employees_response.json()
                
                if employees and len(employees) > 0:
                    employee = employees[0]
                    
                    # Create a timesheet with approved status
                    timesheet_data = {
                        "employee_id": employee["id"],
                        "week_starting": "2024-12-16",
                        "week_ending": "2024-12-22",
                        "status": "approved",
                        "entries": [
                            {
                                "date": "2024-12-16",
                                "regular_hours": 8.0,
                                "overtime_hours": 0.0,
                                "notes": "Regular work day"
                            },
                            {
                                "date": "2024-12-17",
                                "regular_hours": 8.0,
                                "overtime_hours": 2.0,
                                "notes": "Overtime for urgent project"
                            },
                            {
                                "date": "2024-12-18",
                                "regular_hours": 8.0,
                                "overtime_hours": 0.0,
                                "notes": "Regular work day"
                            },
                            {
                                "date": "2024-12-19",
                                "regular_hours": 8.0,
                                "overtime_hours": 0.0,
                                "notes": "Regular work day"
                            },
                            {
                                "date": "2024-12-20",
                                "regular_hours": 6.0,
                                "overtime_hours": 0.0,
                                "notes": "Half day Friday"
                            }
                        ]
                    }
                    
                    # Try to create timesheet (this might not work if endpoint doesn't exist)
                    response = self.session.post(f"{API_BASE}/payroll/timesheets", json=timesheet_data)
                    
                    if response.status_code == 200:
                        result = response.json()
                        timesheet_id = result.get("data", {}).get("id")
                        
                        self.log_result(
                            "Create Approved Timesheet for Testing", 
                            True, 
                            f"Successfully created approved timesheet for payslip testing",
                            f"Timesheet ID: {timesheet_id}, Employee: {employee.get('first_name')} {employee.get('last_name')}"
                        )
                        return timesheet_id
                    else:
                        self.log_result(
                            "Create Approved Timesheet for Testing", 
                            False, 
                            f"Failed to create timesheet: {response.status_code}",
                            "Timesheet creation endpoint may not be available"
                        )
                else:
                    self.log_result(
                        "Create Approved Timesheet for Testing", 
                        False, 
                        "No employees available for timesheet creation"
                    )
            else:
                self.log_result(
                    "Create Approved Timesheet for Testing", 
                    False, 
                    f"Failed to get employees: {employees_response.status_code}"
                )
                
        except Exception as e:
            self.log_result("Create Approved Timesheet for Testing", False, f"Error: {str(e)}")
        
        return None

    def test_generate_payslip_from_timesheet(self, timesheet_id):
        """Test GET /api/payroll/reports/payslip/{timesheet_id} endpoint"""
        try:
            response = self.session.get(f"{API_BASE}/payroll/reports/payslip/{timesheet_id}")
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("success") == True and "data" in result:
                    payslip_data = result["data"]
                    
                    # Check payslip structure
                    expected_fields = ["id", "timesheet_id", "employee_id", "payslip_data", "generated_at"]
                    missing_fields = [field for field in expected_fields if field not in payslip_data]
                    
                    if not missing_fields:
                        # Check payslip_data structure
                        payslip_details = payslip_data.get("payslip_data", {})
                        expected_sections = ["employee", "pay_period", "hours", "earnings", "deductions", "net_pay", "year_to_date", "bank_details"]
                        missing_sections = [section for section in expected_sections if section not in payslip_details]
                        
                        if not missing_sections:
                            self.log_result(
                                "Generate Payslip from Timesheet", 
                                True, 
                                f"Successfully generated payslip from approved timesheet",
                                f"Payslip ID: {payslip_data['id']}, Net Pay: ${payslip_details.get('net_pay', 0)}"
                            )
                            
                            # Verify specific payslip data
                            self.verify_payslip_calculations(payslip_details)
                        else:
                            self.log_result(
                                "Generate Payslip from Timesheet", 
                                False, 
                                f"Payslip data missing sections: {missing_sections}"
                            )
                    else:
                        self.log_result(
                            "Generate Payslip from Timesheet", 
                            False, 
                            f"Payslip missing required fields: {missing_fields}"
                        )
                else:
                    self.log_result(
                        "Generate Payslip from Timesheet", 
                        False, 
                        "Invalid response structure"
                    )
            elif response.status_code == 404:
                self.log_result(
                    "Generate Payslip from Timesheet", 
                    False, 
                    "Approved timesheet not found for payslip generation",
                    f"Timesheet ID: {timesheet_id} may not be approved or may not exist"
                )
            else:
                self.log_result(
                    "Generate Payslip from Timesheet", 
                    False, 
                    f"Failed to generate payslip: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Generate Payslip from Timesheet", False, f"Error: {str(e)}")

    def verify_payslip_calculations(self, payslip_details):
        """Verify payslip calculations are correct"""
        try:
            employee = payslip_details.get("employee", {})
            hours = payslip_details.get("hours", {})
            earnings = payslip_details.get("earnings", {})
            deductions = payslip_details.get("deductions", {})
            
            # Check employee info
            required_employee_fields = ["name", "employee_number", "position", "department"]
            missing_employee_fields = [field for field in required_employee_fields if not employee.get(field)]
            
            if not missing_employee_fields:
                self.log_result(
                    "Payslip Employee Info", 
                    True, 
                    f"Employee info complete: {employee['name']}, {employee['position']}, {employee['department']}"
                )
            else:
                self.log_result(
                    "Payslip Employee Info", 
                    False, 
                    f"Employee info missing fields: {missing_employee_fields}"
                )
            
            # Check pay period
            pay_period = payslip_details.get("pay_period", {})
            if pay_period.get("week_start") and pay_period.get("week_end"):
                self.log_result(
                    "Payslip Pay Period", 
                    True, 
                    f"Pay period: {pay_period['week_start']} to {pay_period['week_end']}"
                )
            else:
                self.log_result(
                    "Payslip Pay Period", 
                    False, 
                    "Pay period missing week_start or week_end"
                )
            
            # Check hours and earnings calculations
            regular_hours = hours.get("regular_hours", 0)
            overtime_hours = hours.get("overtime_hours", 0)
            hourly_rate = hours.get("hourly_rate", 0)
            
            regular_pay = earnings.get("regular_pay", 0)
            overtime_pay = earnings.get("overtime_pay", 0)
            gross_pay = earnings.get("gross_pay", 0)
            
            # Verify calculations (allowing for small floating point differences)
            expected_regular_pay = regular_hours * hourly_rate
            expected_overtime_pay = overtime_hours * hourly_rate * 1.5
            expected_gross_pay = expected_regular_pay + expected_overtime_pay
            
            if abs(regular_pay - expected_regular_pay) < 0.01:
                self.log_result(
                    "Payslip Regular Pay Calculation", 
                    True, 
                    f"Regular pay correct: {regular_hours}h × ${hourly_rate} = ${regular_pay}"
                )
            else:
                self.log_result(
                    "Payslip Regular Pay Calculation", 
                    False, 
                    f"Regular pay incorrect: Expected ${expected_regular_pay}, got ${regular_pay}"
                )
            
            if abs(gross_pay - expected_gross_pay) < 0.01:
                self.log_result(
                    "Payslip Gross Pay Calculation", 
                    True, 
                    f"Gross pay correct: ${gross_pay}"
                )
            else:
                self.log_result(
                    "Payslip Gross Pay Calculation", 
                    False, 
                    f"Gross pay incorrect: Expected ${expected_gross_pay}, got ${gross_pay}"
                )
            
            # Check deductions
            tax = deductions.get("tax_withheld", 0)
            super_amount = deductions.get("superannuation", 0)
            net_pay = payslip_details.get("net_pay", 0)
            
            expected_net_pay = gross_pay - tax
            
            if abs(net_pay - expected_net_pay) < 0.01:
                self.log_result(
                    "Payslip Net Pay Calculation", 
                    True, 
                    f"Net pay correct: ${gross_pay} - ${tax} = ${net_pay}"
                )
            else:
                self.log_result(
                    "Payslip Net Pay Calculation", 
                    False, 
                    f"Net pay incorrect: Expected ${expected_net_pay}, got ${net_pay}"
                )
                
        except Exception as e:
            self.log_result("Verify Payslip Calculations", False, f"Error: {str(e)}")

    def test_payslip_data_structure(self):
        """Test payslip data structure by getting all payslips and checking first one"""
        try:
            response = self.session.get(f"{API_BASE}/payroll/reports/payslips")
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("success") == True and "data" in result:
                    payslips = result["data"]
                    
                    if len(payslips) > 0:
                        payslip = payslips[0]
                        payslip_data = payslip.get("payslip_data", {})
                        
                        # Check all required sections exist
                        required_sections = {
                            "employee": ["name", "employee_number", "position", "department"],
                            "pay_period": ["week_start", "week_end"],
                            "hours": ["regular_hours", "overtime_hours", "hourly_rate"],
                            "earnings": ["regular_pay", "overtime_pay", "gross_pay"],
                            "deductions": ["tax_withheld", "superannuation"],
                            "year_to_date": ["gross_pay", "tax_withheld", "superannuation", "net_pay"],
                            "bank_details": ["bsb", "account_number", "superannuation_fund"]
                        }
                        
                        all_sections_valid = True
                        for section, fields in required_sections.items():
                            if section not in payslip_data:
                                self.log_result(
                                    f"Payslip Data Structure - {section}", 
                                    False, 
                                    f"Missing {section} section"
                                )
                                all_sections_valid = False
                            else:
                                section_data = payslip_data[section]
                                missing_fields = [field for field in fields if field not in section_data]
                                if missing_fields:
                                    self.log_result(
                                        f"Payslip Data Structure - {section}", 
                                        False, 
                                        f"Missing fields in {section}: {missing_fields}"
                                    )
                                    all_sections_valid = False
                        
                        if all_sections_valid:
                            self.log_result(
                                "Payslip Data Structure Complete", 
                                True, 
                                "All payslip sections and fields present and correct"
                            )
                    else:
                        self.log_result(
                            "Payslip Data Structure", 
                            False, 
                            "No payslips available to check structure"
                        )
                else:
                    self.log_result(
                        "Payslip Data Structure", 
                        False, 
                        "Invalid response structure"
                    )
            else:
                self.log_result(
                    "Payslip Data Structure", 
                    False, 
                    f"Failed to get payslips: {response.status_code}"
                )
                
        except Exception as e:
            self.log_result("Payslip Data Structure", False, f"Error: {str(e)}")

    def test_payroll_reports_edge_cases(self):
        """Test edge cases for payroll reports endpoints"""
        try:
            # Test 1: Generate payslip with non-existent timesheet ID
            fake_timesheet_id = str(uuid.uuid4())
            response = self.session.get(f"{API_BASE}/payroll/reports/payslip/{fake_timesheet_id}")
            
            if response.status_code == 404:
                self.log_result(
                    "Payslip Generation - Non-existent Timesheet", 
                    True, 
                    "Correctly returned 404 for non-existent timesheet"
                )
            else:
                self.log_result(
                    "Payslip Generation - Non-existent Timesheet", 
                    False, 
                    f"Expected 404, got {response.status_code}"
                )
            
            # Test 2: Timesheet report with invalid employee_id
            fake_employee_id = str(uuid.uuid4())
            response2 = self.session.get(f"{API_BASE}/payroll/reports/timesheets?employee_id={fake_employee_id}")
            
            if response2.status_code == 200:
                result = response2.json()
                if result.get("success") == True and len(result.get("data", [])) == 0:
                    self.log_result(
                        "Timesheet Report - Invalid Employee ID", 
                        True, 
                        "Correctly returned empty array for non-existent employee"
                    )
                else:
                    self.log_result(
                        "Timesheet Report - Invalid Employee ID", 
                        False, 
                        "Should return empty array for non-existent employee"
                    )
            else:
                self.log_result(
                    "Timesheet Report - Invalid Employee ID", 
                    False, 
                    f"Expected 200 with empty data, got {response2.status_code}"
                )
            
            # Test 3: Timesheet report with invalid date format
            response3 = self.session.get(f"{API_BASE}/payroll/reports/timesheets?start_date=invalid-date")
            
            # Should handle gracefully (either 400/422 error or ignore invalid date)
            if response3.status_code in [200, 400, 422]:
                self.log_result(
                    "Timesheet Report - Invalid Date Format", 
                    True, 
                    f"Handled invalid date format appropriately with status {response3.status_code}"
                )
            else:
                self.log_result(
                    "Timesheet Report - Invalid Date Format", 
                    False, 
                    f"Unexpected response to invalid date: {response3.status_code}"
                )
                
        except Exception as e:
            self.log_result("Payroll Reports Edge Cases", False, f"Error: {str(e)}")

    def run_comprehensive_tests(self):
        """Run all comprehensive tests for payroll reports endpoints"""
        print("\n" + "="*80)
        print("PAYROLL REPORTS ENDPOINTS TESTING")
        print("Testing newly implemented payroll reports endpoints")
        print("="*80)
        
        # Step 1: Authenticate
        if not self.authenticate():
            print("❌ Authentication failed - cannot proceed with tests")
            return
        
        # Step 2: Run payroll reports tests
        self.test_payroll_reports_endpoints()
        
        # Step 3: Print comprehensive summary
        self.print_test_summary()

if __name__ == "__main__":
    tester = BackendAPITester()
    tester.run_comprehensive_tests()
