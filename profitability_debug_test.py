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

class ProfitabilityDebugTester:
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

    def test_profitability_report_material_costs_debugging(self):
        """
        PRIORITY TEST 1: Profitability Report Material Costs and Data Sources Debugging
        Debug the Profitability Report material costs and data sources
        """
        print("\n" + "="*80)
        print("PRIORITY TEST 1: PROFITABILITY REPORT MATERIAL COSTS AND DATA SOURCES DEBUGGING")
        print("Debugging material costs and data sources for profitability reports")
        print("="*80)
        
        # Test 1: Check job_cards collection structure
        self.test_job_cards_collection_structure()
        
        # Test 2: Check if client_products endpoint exists and returns data
        self.test_client_products_endpoint()
        
        # Test 3: Verify completed orders have associated job cards
        self.test_completed_orders_job_cards_association()
        
        # Test 4: Identify correct field names for material usage in job cards
        self.test_job_card_material_fields()
        
        # Test 5: Check orders structure and status
        self.test_orders_structure()
        
        # Test 6: Cross-reference job cards with orders
        self.test_job_cards_orders_cross_reference()
        
        # Test 7: Analyze material data sources
        self.test_material_data_sources()

    def test_job_cards_collection_structure(self):
        """Test 1: Check job_cards collection structure - what fields exist for material usage?"""
        print("\n--- Test 1: Job Cards Collection Structure ---")
        try:
            # Try different job card endpoints
            endpoints_to_try = [
                "/production/job-cards/search",
                "/job-cards",
                "/production/job-cards"
            ]
            
            job_cards = []
            successful_endpoint = None
            
            for endpoint in endpoints_to_try:
                try:
                    response = self.session.get(f"{API_BASE}{endpoint}")
                    if response.status_code == 200:
                        data = response.json()
                        if isinstance(data, dict) and 'data' in data:
                            job_cards = data['data']
                        else:
                            job_cards = data
                        successful_endpoint = endpoint
                        break
                except:
                    continue
            
            if not successful_endpoint:
                # Try to get job cards by getting orders first and then their job cards
                orders_response = self.session.get(f"{API_BASE}/orders")
                if orders_response.status_code == 200:
                    orders = orders_response.json()
                    if orders and len(orders) > 0:
                        # Try to get job cards for the first order
                        order_id = orders[0].get('id')
                        response = self.session.get(f"{API_BASE}/production/job-cards/order/{order_id}")
                        if response.status_code == 200:
                            data = response.json()
                            if isinstance(data, dict) and 'data' in data:
                                job_cards = data['data']
                            successful_endpoint = f"/production/job-cards/order/{order_id}"
            
            if successful_endpoint and len(job_cards) > 0:
                    # Analyze first job card structure
                    sample_job_card = job_cards[0]
                    
                    self.log_result(
                        "Job Cards Endpoint Access", 
                        True, 
                        f"Successfully retrieved {len(job_cards)} job cards from {successful_endpoint}"
                    )
                    
                    # Check for material-related fields
                    material_fields = []
                    all_fields = list(sample_job_card.keys())
                    
                    # Look for fields that might contain material usage data
                    for field in all_fields:
                        if any(mat_field in field.lower() for mat_field in ['material', 'stock', 'consumable', 'usage']):
                            material_fields.append(field)
                    
                    self.log_result(
                        "Job Card Material Fields Analysis", 
                        True, 
                        f"Found potential material fields: {material_fields}",
                        f"All fields in job card: {all_fields}"
                    )
                    
                    # Check specific job card details
                    job_card_id = sample_job_card.get('id')
                    order_id = sample_job_card.get('order_id')
                    
                    self.log_result(
                        "Sample Job Card Details", 
                        True, 
                        f"Job Card ID: {job_card_id}, Order ID: {order_id}",
                        f"Sample job card keys: {list(sample_job_card.keys())}"
                    )
                    
                    return job_cards
                    
                elif isinstance(job_cards, list) and len(job_cards) == 0:
                    self.log_result(
                        "Job Cards Collection Structure", 
                        False, 
                        "Job cards collection is empty - no data to analyze"
                    )
                else:
                    self.log_result(
                        "Job Cards Collection Structure", 
                        False, 
                        f"Unexpected response format: {type(job_cards)}"
                    )
            else:
                self.log_result(
                    "Job Cards Endpoint Access", 
                    False, 
                    f"Failed to access job cards endpoint: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Job Cards Collection Structure", False, f"Error: {str(e)}")
        
        return []

    def test_client_products_endpoint(self):
        """Test 2: Check if client_products endpoint exists and returns data"""
        print("\n--- Test 2: Client Products Endpoint ---")
        try:
            # First, get clients to test client-specific products
            clients_response = self.session.get(f"{API_BASE}/clients")
            
            if clients_response.status_code == 200:
                clients = clients_response.json()
                
                if clients and len(clients) > 0:
                    client = clients[0]
                    client_id = client.get('id')
                    
                    # Test client-specific products endpoint
                    response = self.session.get(f"{API_BASE}/clients/{client_id}/catalog")
                    
                    if response.status_code == 200:
                        client_products = response.json()
                        
                        self.log_result(
                            "Client Products Endpoint Access", 
                            True, 
                            f"Successfully retrieved {len(client_products)} client products for client {client.get('company_name')}"
                        )
                        
                        if len(client_products) > 0:
                            sample_product = client_products[0]
                            
                            # Check for material-related fields in client products
                            material_fields = []
                            all_fields = list(sample_product.keys())
                            
                            for field in all_fields:
                                if any(mat_field in field.lower() for mat_field in ['material', 'layer', 'composition', 'cost']):
                                    material_fields.append(field)
                            
                            self.log_result(
                                "Client Product Material Fields", 
                                True, 
                                f"Found material-related fields: {material_fields}",
                                f"All fields: {all_fields}"
                            )
                            
                            # Check if material_layers field exists (important for profitability)
                            if 'material_layers' in sample_product:
                                material_layers = sample_product.get('material_layers', [])
                                self.log_result(
                                    "Material Layers in Client Products", 
                                    True, 
                                    f"Found material_layers field with {len(material_layers)} layers"
                                )
                            else:
                                self.log_result(
                                    "Material Layers in Client Products", 
                                    False, 
                                    "No material_layers field found in client products"
                                )
                        
                        return client_products
                    else:
                        self.log_result(
                            "Client Products Endpoint Access", 
                            False, 
                            f"Failed to access client products: {response.status_code}",
                            response.text
                        )
                else:
                    self.log_result(
                        "Client Products Endpoint Setup", 
                        False, 
                        "No clients found to test client products endpoint"
                    )
            else:
                self.log_result(
                    "Client Products Endpoint Setup", 
                    False, 
                    f"Failed to get clients: {clients_response.status_code}"
                )
                
        except Exception as e:
            self.log_result("Client Products Endpoint", False, f"Error: {str(e)}")
        
        return []

    def test_completed_orders_job_cards_association(self):
        """Test 3: Verify completed orders have associated job cards"""
        print("\n--- Test 3: Completed Orders and Job Cards Association ---")
        try:
            # Get all orders
            orders_response = self.session.get(f"{API_BASE}/orders")
            
            if orders_response.status_code == 200:
                orders = orders_response.json()
                
                # Filter for completed orders
                completed_orders = [order for order in orders if order.get('status') in ['completed', 'delivered', 'invoiced']]
                
                self.log_result(
                    "Completed Orders Analysis", 
                    True, 
                    f"Found {len(completed_orders)} completed orders out of {len(orders)} total orders"
                )
                
                if len(completed_orders) > 0:
                    # Get job cards
                    job_cards_response = self.session.get(f"{API_BASE}/job-cards")
                    
                    if job_cards_response.status_code == 200:
                        job_cards = job_cards_response.json()
                        
                        # Check association between completed orders and job cards
                        orders_with_job_cards = 0
                        orders_without_job_cards = []
                        
                        for order in completed_orders:
                            order_id = order.get('id')
                            order_number = order.get('order_number', 'Unknown')
                            
                            # Find job card for this order
                            matching_job_cards = [jc for jc in job_cards if jc.get('order_id') == order_id]
                            
                            if matching_job_cards:
                                orders_with_job_cards += 1
                            else:
                                orders_without_job_cards.append({
                                    'order_id': order_id,
                                    'order_number': order_number,
                                    'status': order.get('status')
                                })
                        
                        self.log_result(
                            "Orders-Job Cards Association", 
                            orders_with_job_cards > 0, 
                            f"{orders_with_job_cards} completed orders have job cards, {len(orders_without_job_cards)} do not",
                            f"Orders without job cards: {orders_without_job_cards}"
                        )
                        
                        return completed_orders, job_cards
                    else:
                        self.log_result(
                            "Job Cards Retrieval for Association", 
                            False, 
                            f"Failed to get job cards: {job_cards_response.status_code}"
                        )
                else:
                    self.log_result(
                        "Completed Orders Analysis", 
                        False, 
                        "No completed orders found to check job card association"
                    )
            else:
                self.log_result(
                    "Orders Retrieval for Association", 
                    False, 
                    f"Failed to get orders: {orders_response.status_code}"
                )
                
        except Exception as e:
            self.log_result("Completed Orders Job Cards Association", False, f"Error: {str(e)}")
        
        return [], []

    def test_job_card_material_fields(self):
        """Test 4: Identify correct field names for material usage in job cards"""
        print("\n--- Test 4: Job Card Material Fields Deep Analysis ---")
        try:
            response = self.session.get(f"{API_BASE}/job-cards")
            
            if response.status_code == 200:
                job_cards = response.json()
                
                if len(job_cards) > 0:
                    # Analyze multiple job cards to find material usage patterns
                    material_field_analysis = {}
                    
                    for i, job_card in enumerate(job_cards[:5]):  # Check first 5 job cards
                        job_card_id = job_card.get('id', f'job_card_{i}')
                        
                        # Look for any field that might contain material data
                        for field_name, field_value in job_card.items():
                            if any(keyword in field_name.lower() for keyword in ['material', 'stock', 'usage', 'consumption', 'cost']):
                                if field_name not in material_field_analysis:
                                    material_field_analysis[field_name] = {
                                        'count': 0,
                                        'sample_values': [],
                                        'data_types': set()
                                    }
                                
                                material_field_analysis[field_name]['count'] += 1
                                material_field_analysis[field_name]['data_types'].add(type(field_value).__name__)
                                
                                # Store sample values (truncated for readability)
                                if len(material_field_analysis[field_name]['sample_values']) < 3:
                                    if isinstance(field_value, (list, dict)):
                                        material_field_analysis[field_name]['sample_values'].append(str(field_value)[:200])
                                    else:
                                        material_field_analysis[field_name]['sample_values'].append(field_value)
                    
                    self.log_result(
                        "Material Fields Analysis", 
                        True, 
                        f"Analyzed {len(job_cards)} job cards for material fields",
                        f"Material field analysis: {material_field_analysis}"
                    )
                    
                    # Check specific fields that are commonly used for material tracking
                    common_material_fields = [
                        'materials_used', 'material_consumption', 'stock_movements', 
                        'material_cost', 'raw_materials_used', 'consumables_used'
                    ]
                    
                    found_fields = []
                    missing_fields = []
                    
                    sample_job_card = job_cards[0]
                    for field in common_material_fields:
                        if field in sample_job_card:
                            found_fields.append(field)
                        else:
                            missing_fields.append(field)
                    
                    self.log_result(
                        "Common Material Fields Check", 
                        len(found_fields) > 0, 
                        f"Found fields: {found_fields}, Missing fields: {missing_fields}"
                    )
                    
                    return material_field_analysis
                else:
                    self.log_result(
                        "Job Card Material Fields Analysis", 
                        False, 
                        "No job cards available for material fields analysis"
                    )
            else:
                self.log_result(
                    "Job Card Material Fields Analysis", 
                    False, 
                    f"Failed to get job cards: {response.status_code}"
                )
                
        except Exception as e:
            self.log_result("Job Card Material Fields Analysis", False, f"Error: {str(e)}")
        
        return {}

    def test_orders_structure(self):
        """Test 5: Check orders structure and status"""
        print("\n--- Test 5: Orders Structure Analysis ---")
        try:
            response = self.session.get(f"{API_BASE}/orders")
            
            if response.status_code == 200:
                orders = response.json()
                
                if len(orders) > 0:
                    # Analyze order statuses
                    status_counts = {}
                    for order in orders:
                        status = order.get('status', 'unknown')
                        status_counts[status] = status_counts.get(status, 0) + 1
                    
                    self.log_result(
                        "Order Status Distribution", 
                        True, 
                        f"Order status breakdown: {status_counts}",
                        f"Total orders: {len(orders)}"
                    )
                    
                    # Check order structure for material-related fields
                    sample_order = orders[0]
                    order_fields = list(sample_order.keys())
                    
                    # Look for fields that might be relevant to profitability calculation
                    profitability_fields = []
                    for field in order_fields:
                        if any(keyword in field.lower() for keyword in ['cost', 'price', 'material', 'profit', 'margin']):
                            profitability_fields.append(field)
                    
                    self.log_result(
                        "Order Profitability Fields", 
                        True, 
                        f"Found profitability-related fields: {profitability_fields}",
                        f"All order fields: {order_fields}"
                    )
                    
                    # Check if orders have items with material information
                    items = sample_order.get('items', [])
                    if items and len(items) > 0:
                        item_fields = list(items[0].keys())
                        
                        item_material_fields = []
                        for field in item_fields:
                            if any(keyword in field.lower() for keyword in ['material', 'cost', 'specification']):
                                item_material_fields.append(field)
                        
                        self.log_result(
                            "Order Item Material Fields", 
                            True, 
                            f"Found item material fields: {item_material_fields}",
                            f"All item fields: {item_fields}"
                        )
                    
                    return orders
                else:
                    self.log_result(
                        "Orders Structure Analysis", 
                        False, 
                        "No orders found for structure analysis"
                    )
            else:
                self.log_result(
                    "Orders Structure Analysis", 
                    False, 
                    f"Failed to get orders: {response.status_code}"
                )
                
        except Exception as e:
            self.log_result("Orders Structure Analysis", False, f"Error: {str(e)}")
        
        return []

    def test_job_cards_orders_cross_reference(self):
        """Test 6: Cross-reference job cards with orders"""
        print("\n--- Test 6: Job Cards and Orders Cross-Reference ---")
        try:
            # Get both job cards and orders
            job_cards_response = self.session.get(f"{API_BASE}/job-cards")
            orders_response = self.session.get(f"{API_BASE}/orders")
            
            if job_cards_response.status_code == 200 and orders_response.status_code == 200:
                job_cards = job_cards_response.json()
                orders = orders_response.json()
                
                # Create mappings
                orders_by_id = {order.get('id'): order for order in orders}
                job_cards_by_order_id = {}
                
                for job_card in job_cards:
                    order_id = job_card.get('order_id')
                    if order_id:
                        if order_id not in job_cards_by_order_id:
                            job_cards_by_order_id[order_id] = []
                        job_cards_by_order_id[order_id].append(job_card)
                
                # Analyze the relationships
                orders_with_job_cards = len(job_cards_by_order_id)
                job_cards_without_orders = []
                
                for job_card in job_cards:
                    order_id = job_card.get('order_id')
                    if order_id and order_id not in orders_by_id:
                        job_cards_without_orders.append({
                            'job_card_id': job_card.get('id'),
                            'order_id': order_id
                        })
                
                self.log_result(
                    "Job Cards Orders Cross-Reference", 
                    True, 
                    f"{orders_with_job_cards} orders have job cards, {len(job_cards_without_orders)} job cards reference non-existent orders",
                    f"Total orders: {len(orders)}, Total job cards: {len(job_cards)}"
                )
                
                # Find a good example for detailed analysis
                if job_cards_by_order_id:
                    sample_order_id = list(job_cards_by_order_id.keys())[0]
                    sample_order = orders_by_id.get(sample_order_id)
                    sample_job_cards = job_cards_by_order_id[sample_order_id]
                    
                    if sample_order:
                        self.log_result(
                            "Sample Order-Job Card Relationship", 
                            True, 
                            f"Order {sample_order.get('order_number')} has {len(sample_job_cards)} job card(s)",
                            f"Order status: {sample_order.get('status')}, Job card IDs: {[jc.get('id') for jc in sample_job_cards]}"
                        )
                
                return job_cards_by_order_id, orders_by_id
            else:
                self.log_result(
                    "Job Cards Orders Cross-Reference", 
                    False, 
                    f"Failed to get data - Job cards: {job_cards_response.status_code}, Orders: {orders_response.status_code}"
                )
                
        except Exception as e:
            self.log_result("Job Cards Orders Cross-Reference", False, f"Error: {str(e)}")
        
        return {}, {}

    def test_material_data_sources(self):
        """Test 7: Analyze material data sources"""
        print("\n--- Test 7: Material Data Sources Analysis ---")
        try:
            # Check various material-related endpoints
            endpoints_to_check = [
                ('/materials', 'Materials Master Data'),
                ('/stock/raw-materials', 'Raw Materials Stock'),
                ('/stock/raw-substrates', 'Raw Substrates Stock'),
                ('/stock/movements', 'Stock Movements'),
            ]
            
            material_data_sources = {}
            
            for endpoint, description in endpoints_to_check:
                try:
                    response = self.session.get(f"{API_BASE}{endpoint}")
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Handle different response formats
                        if isinstance(data, dict) and 'data' in data:
                            items = data['data']
                        else:
                            items = data
                        
                        material_data_sources[description] = {
                            'status': 'accessible',
                            'count': len(items) if isinstance(items, list) else 1,
                            'sample_fields': list(items[0].keys()) if isinstance(items, list) and len(items) > 0 else []
                        }
                        
                        self.log_result(
                            f"Material Data Source - {description}", 
                            True, 
                            f"Accessible with {len(items) if isinstance(items, list) else 1} items"
                        )
                    else:
                        material_data_sources[description] = {
                            'status': f'error_{response.status_code}',
                            'count': 0,
                            'sample_fields': []
                        }
                        
                        self.log_result(
                            f"Material Data Source - {description}", 
                            False, 
                            f"Not accessible: {response.status_code}"
                        )
                        
                except Exception as e:
                    material_data_sources[description] = {
                        'status': f'exception_{str(e)}',
                        'count': 0,
                        'sample_fields': []
                    }
                    
                    self.log_result(
                        f"Material Data Source - {description}", 
                        False, 
                        f"Exception: {str(e)}"
                    )
            
            # Summary of material data sources
            accessible_sources = [desc for desc, info in material_data_sources.items() if info['status'] == 'accessible']
            
            self.log_result(
                "Material Data Sources Summary", 
                len(accessible_sources) > 0, 
                f"Accessible sources: {accessible_sources}",
                f"All sources analysis: {material_data_sources}"
            )
            
            return material_data_sources
            
        except Exception as e:
            self.log_result("Material Data Sources Analysis", False, f"Error: {str(e)}")
        
        return {}

    def print_test_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "="*80)
        print("PROFITABILITY REPORT DEBUGGING - FINAL SUMMARY")
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

def main():
    """Main test execution"""
    tester = ProfitabilityDebugTester()
    
    print("="*80)
    print("PROFITABILITY REPORT MATERIAL COSTS AND DATA SOURCES DEBUGGING")
    print("="*80)
    
    # Authenticate first
    if not tester.authenticate():
        print("❌ Authentication failed. Cannot proceed with tests.")
        return
    
    # Run profitability report debugging tests
    tester.test_profitability_report_material_costs_debugging()
    
    # Print final summary
    tester.print_test_summary()

if __name__ == "__main__":
    main()