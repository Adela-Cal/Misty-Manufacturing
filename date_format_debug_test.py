#!/usr/bin/env python3
"""
Specific test to confirm the date format mismatch issue
and check client_products for the orders
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

class DateFormatDebugTester:
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

    def test_date_format_issue(self):
        """Test the specific date format issue"""
        print("="*80)
        print("DATE FORMAT MISMATCH CONFIRMATION TEST")
        print("="*80)
        
        # Get orders to check their dates
        orders_response = self.session.get(f"{API_BASE}/orders")
        if orders_response.status_code != 200:
            print("❌ Could not get orders")
            return
        
        orders = orders_response.json()
        if not orders:
            print("❌ No orders found")
            return
        
        sample_order = orders[0]
        order_date = sample_order.get('created_at')
        
        print(f"📅 SAMPLE ORDER DATE: {order_date}")
        print(f"📅 TYPE: {type(order_date)}")
        
        # Test string comparison (what MongoDB does)
        test_cases = [
            ("2020-01-01T00:00:00+00:00", "Query start with timezone"),
            ("2030-12-31T23:59:59+00:00", "Query end with timezone"),
            ("2020-01-01T00:00:00", "Query start without timezone"),
            ("2030-12-31T23:59:59", "Query end without timezone"),
        ]
        
        print(f"\n🔍 STRING COMPARISON TESTS:")
        for test_date, description in test_cases:
            if test_date <= order_date:
                result = "✅ WOULD MATCH (<=)"
            else:
                result = "❌ WOULD NOT MATCH (>)"
            
            print(f"  {description}: {test_date}")
            print(f"    vs Order date: {order_date}")
            print(f"    Result: {result}")
            print()
        
        # Test the actual issue
        print(f"🎯 ROOT CAUSE ANALYSIS:")
        timezone_query_start = "2020-01-01T00:00:00+00:00"
        no_timezone_query_start = "2020-01-01T00:00:00"
        
        print(f"With timezone (+00:00): '{timezone_query_start}' <= '{order_date}' = {timezone_query_start <= order_date}")
        print(f"Without timezone: '{no_timezone_query_start}' <= '{order_date}' = {no_timezone_query_start <= order_date}")
        
        if timezone_query_start > order_date:
            print(f"\n🚨 CONFIRMED: The '+00:00' timezone suffix causes string comparison to fail!")
            print(f"   In ASCII: '+' (43) > '1' (49) is False, but '+' (43) > '2' (50) is False")
            print(f"   Actually: '+' (43) < '2' (50), so the comparison fails because of string sorting")

    def check_client_products(self):
        """Check if client products exist for the orders"""
        print("\n" + "="*80)
        print("CLIENT PRODUCTS CHECK")
        print("="*80)
        
        # Get orders
        orders_response = self.session.get(f"{API_BASE}/orders")
        if orders_response.status_code != 200:
            print("❌ Could not get orders")
            return
        
        orders = orders_response.json()
        
        # Get unique product IDs from orders
        product_ids = set()
        client_ids = set()
        
        for order in orders:
            client_ids.add(order.get('client_id'))
            for item in order.get('items', []):
                product_id = item.get('product_id')
                if product_id:
                    product_ids.add(product_id)
        
        print(f"📦 Found {len(product_ids)} unique product IDs in orders")
        print(f"🏢 Found {len(client_ids)} unique client IDs in orders")
        
        # Check client products for each client
        products_found = 0
        for client_id in client_ids:
            try:
                client_products_response = self.session.get(f"{API_BASE}/clients/{client_id}/catalog")
                if client_products_response.status_code == 200:
                    client_products = client_products_response.json()
                    print(f"\n🏢 Client {client_id}: {len(client_products)} products in catalog")
                    
                    # Check if any order product IDs match client catalog
                    matching_products = []
                    for product in client_products:
                        if product.get('id') in product_ids:
                            matching_products.append(product)
                            products_found += 1
                    
                    print(f"   📦 {len(matching_products)} products match order items")
                    
                    if matching_products:
                        for product in matching_products[:3]:  # Show first 3
                            print(f"     - {product.get('product_description', 'N/A')} (ID: {product.get('id')})")
                else:
                    print(f"\n🏢 Client {client_id}: Could not get catalog (status {client_products_response.status_code})")
            except Exception as e:
                print(f"\n🏢 Client {client_id}: Error getting catalog - {e}")
        
        print(f"\n📊 SUMMARY:")
        print(f"   Total product IDs in orders: {len(product_ids)}")
        print(f"   Matching products in client catalogs: {products_found}")
        
        if products_found == 0:
            print(f"\n🚨 SECOND ISSUE FOUND: No client products match the product IDs in orders!")
            print(f"   This means even if the date issue is fixed, no products would be found")
            print(f"   because the endpoint looks for products in client_products collection")

    def suggest_fixes(self):
        """Suggest fixes for the identified issues"""
        print("\n" + "="*80)
        print("SUGGESTED FIXES")
        print("="*80)
        
        print("🔧 FIX 1: Date Format Issue")
        print("   Problem: Endpoint uses timezone-aware dates in query, but orders have timezone-naive dates")
        print("   Solution: Remove timezone from query dates or ensure consistent date formats")
        print("   Code change needed in server.py around line 5139:")
        print('   Change: order_query = {"created_at": {"$gte": start.isoformat(), "$lte": end.isoformat()}}')
        print('   To: order_query = {"created_at": {"$gte": start.replace(tzinfo=None).isoformat(), "$lte": end.replace(tzinfo=None).isoformat()}}')
        
        print("\n🔧 FIX 2: Client Products Issue")
        print("   Problem: Orders reference product IDs that don't exist in client_products collection")
        print("   Solution: Either:")
        print("   A) Create matching client_products entries for the order items")
        print("   B) Modify endpoint to handle missing client_products gracefully")
        print("   C) Use a different product lookup strategy")
        
        print("\n🔧 FIX 3: Default Date Range")
        print("   Problem: Endpoint fails when no dates provided")
        print("   Solution: Add default date range (e.g., last 90 days) when dates are None")
        print("   Code change needed in server.py around line 5131:")
        print("   Add: if not start_date: start_date = (datetime.now() - timedelta(days=90)).isoformat() + 'Z'")
        print("        if not end_date: end_date = datetime.now().isoformat() + 'Z'")

    def run_debug_test(self):
        """Run the debug test"""
        if not self.authenticate():
            print("❌ Authentication failed")
            return
        
        self.test_date_format_issue()
        self.check_client_products()
        self.suggest_fixes()

if __name__ == "__main__":
    tester = DateFormatDebugTester()
    tester.run_debug_test()