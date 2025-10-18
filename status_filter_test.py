#!/usr/bin/env python3
"""
Test the status filtering logic in the projected order analysis endpoint
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

class StatusFilterTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        
    def authenticate(self):
        """Authenticate with demo user"""
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
                return True
            return False
        except Exception as e:
            print(f"Authentication error: {e}")
            return False

    def analyze_status_filtering_logic(self):
        """Analyze the status filtering logic issue"""
        print("="*80)
        print("STATUS FILTERING LOGIC ANALYSIS")
        print("="*80)
        
        # Get all orders and check their status
        orders_response = self.session.get(f"{API_BASE}/orders")
        if orders_response.status_code != 200:
            print("❌ Could not get orders")
            return
        
        orders = orders_response.json()
        
        # Analyze status values
        status_counts = {}
        for order in orders:
            status = order.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        print(f"📊 ORDER STATUS ANALYSIS:")
        print(f"Total orders: {len(orders)}")
        for status, count in status_counts.items():
            print(f"  Status '{status}': {count} orders")
        
        # Check if there are any cancelled orders
        has_cancelled = any(order.get('status') == 'cancelled' for order in orders)
        print(f"\n🔍 CANCELLED ORDERS CHECK:")
        print(f"Has cancelled orders: {has_cancelled}")
        
        if has_cancelled:
            print("✅ Status filter will be applied: {'status': {'$ne': 'cancelled'}}")
            print("   This should include orders with status 'active'")
        else:
            print("✅ No status filter will be applied")
            print("   All orders should be included regardless of status")
        
        # Simulate the endpoint's query logic
        print(f"\n🔍 SIMULATING ENDPOINT QUERY LOGIC:")
        
        # Test date range
        start_date = "2020-01-01T00:00:00"
        end_date = "2030-12-31T23:59:59"
        
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
        
        # Build query like the endpoint does
        order_query = {
            "created_at": {"$gte": start.isoformat(), "$lte": end.isoformat()}
        }
        
        print(f"Base query: {order_query}")
        
        # Check if cancelled orders exist (like the endpoint does)
        if has_cancelled:
            order_query["status"] = {"$ne": "cancelled"}
            print(f"With status filter: {order_query}")
        
        # Manually filter orders to see what would match
        matching_orders = []
        for order in orders:
            created_at = order.get('created_at')
            status = order.get('status')
            
            # Check date range
            if start.isoformat() <= created_at <= end.isoformat():
                # Check status filter
                if not has_cancelled or status != 'cancelled':
                    matching_orders.append(order)
        
        print(f"\n📊 MANUAL FILTERING RESULTS:")
        print(f"Orders matching date range: {len([o for o in orders if start.isoformat() <= o.get('created_at', '') <= end.isoformat()])}")
        print(f"Orders matching full query: {len(matching_orders)}")
        
        if len(matching_orders) > 0:
            print(f"✅ {len(matching_orders)} orders should be found by the endpoint")
            
            # Check if these orders have valid product IDs
            product_ids = set()
            for order in matching_orders:
                for item in order.get('items', []):
                    product_id = item.get('product_id')
                    if product_id:
                        product_ids.add(product_id)
            
            print(f"📦 Unique product IDs in matching orders: {len(product_ids)}")
            
            # Check client products for these product IDs
            self.check_client_products_for_orders(matching_orders)
        else:
            print(f"❌ No orders match the query - this explains the 0 results")

    def check_client_products_for_orders(self, orders):
        """Check if client products exist for the matching orders"""
        print(f"\n🔍 CLIENT PRODUCTS VERIFICATION:")
        
        # Get unique client IDs and product IDs
        client_ids = set()
        product_ids = set()
        
        for order in orders:
            client_ids.add(order.get('client_id'))
            for item in order.get('items', []):
                product_id = item.get('product_id')
                if product_id:
                    product_ids.add(product_id)
        
        print(f"Clients to check: {len(client_ids)}")
        print(f"Product IDs to verify: {len(product_ids)}")
        
        total_matching_products = 0
        
        for client_id in client_ids:
            try:
                response = self.session.get(f"{API_BASE}/clients/{client_id}/catalog")
                if response.status_code == 200:
                    client_products = response.json()
                    
                    # Check which product IDs match
                    matching_products = [p for p in client_products if p.get('id') in product_ids]
                    total_matching_products += len(matching_products)
                    
                    print(f"\nClient {client_id}:")
                    print(f"  Total products in catalog: {len(client_products)}")
                    print(f"  Products matching orders: {len(matching_products)}")
                    
                    if matching_products:
                        for product in matching_products[:3]:  # Show first 3
                            print(f"    - {product.get('product_description', 'N/A')}")
                else:
                    print(f"\nClient {client_id}: Could not get catalog (status {response.status_code})")
            except Exception as e:
                print(f"\nClient {client_id}: Error - {e}")
        
        print(f"\n📊 CLIENT PRODUCTS SUMMARY:")
        print(f"Total matching products found: {total_matching_products}")
        
        if total_matching_products == 0:
            print(f"🚨 ISSUE FOUND: No client products match the order product IDs!")
            print(f"   This means the endpoint finds orders but can't find corresponding products")
            print(f"   The endpoint skips orders where product lookup fails")

    def test_endpoint_with_debug_info(self):
        """Test the endpoint and provide debug information"""
        print(f"\n" + "="*80)
        print("ENDPOINT TEST WITH DEBUG INFO")
        print("="*80)
        
        # Test with wide date range
        start_date = "2020-01-01T00:00:00"
        end_date = "2030-12-31T23:59:59"
        
        print(f"Testing endpoint with:")
        print(f"  start_date: {start_date}")
        print(f"  end_date: {end_date}")
        
        try:
            response = self.session.get(
                f"{API_BASE}/stock/reports/projected-order-analysis",
                params={
                    "start_date": start_date,
                    "end_date": end_date
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                data = result.get("data", {})
                summary = data.get("summary", {})
                
                print(f"\n📊 ENDPOINT RESPONSE:")
                print(f"Success: {result.get('success')}")
                print(f"Message: {result.get('message')}")
                print(f"Orders analyzed: {summary.get('total_orders_analyzed', 0)}")
                print(f"Unique products: {summary.get('total_unique_products', 0)}")
                
                if summary.get('total_orders_analyzed', 0) == 0:
                    print(f"\n🚨 CONFIRMED: Endpoint finds 0 orders")
                    print(f"   This suggests either:")
                    print(f"   1. Date filtering is excluding all orders")
                    print(f"   2. Status filtering is excluding all orders") 
                    print(f"   3. There's a bug in the MongoDB query")
                else:
                    print(f"\n✅ Endpoint found orders but no products")
                    print(f"   This suggests client product lookup is failing")
            else:
                print(f"❌ Endpoint failed: {response.status_code}")
                print(f"Error: {response.text}")
                
        except Exception as e:
            print(f"❌ Error testing endpoint: {e}")

    def run_test(self):
        """Run the status filter test"""
        if not self.authenticate():
            print("❌ Authentication failed")
            return
        
        self.analyze_status_filtering_logic()
        self.test_endpoint_with_debug_info()

if __name__ == "__main__":
    tester = StatusFilterTester()
    tester.run_test()