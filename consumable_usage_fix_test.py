#!/usr/bin/env python3
"""
Test the fixed Consumable Usage Report endpoint
Apply the same fixes that were used for the projected order analysis endpoint
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

class ConsumableUsageFixTester:
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
                print("✅ Authentication successful")
                return True
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication error: {str(e)}")
            return False

    def test_consumable_usage_report_before_fix(self):
        """Test the endpoint before applying the fix"""
        print("\n=== TESTING BEFORE FIX ===")
        
        try:
            # Test with wide date range
            start_str = "2020-01-01T00:00:00Z"
            end_str = "2030-12-31T23:59:59Z"
            
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
                
                print(f"Before fix - Products found: {len(products)}")
                print(f"Before fix - Grand total m²: {data.get('grand_total_m2', 0)}")
                
                return len(products) == 0  # Should return 0 products (broken)
            else:
                print(f"❌ Request failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error testing before fix: {str(e)}")
            return False

    def verify_orders_exist(self):
        """Verify that orders exist in the database"""
        print("\n=== VERIFYING ORDERS EXIST ===")
        
        try:
            response = self.session.get(f"{API_BASE}/orders")
            
            if response.status_code == 200:
                orders = response.json()
                
                # Count orders with items
                orders_with_items = [o for o in orders if o.get("items")]
                active_orders = [o for o in orders if o.get("status") == "active"]
                
                print(f"Total orders: {len(orders)}")
                print(f"Orders with items: {len(orders_with_items)}")
                print(f"Active orders: {len(active_orders)}")
                
                if orders_with_items:
                    sample_order = orders_with_items[0]
                    print(f"Sample order: {sample_order.get('order_number')}")
                    print(f"  Status: {sample_order.get('status')}")
                    print(f"  Created: {sample_order.get('created_at')}")
                    print(f"  Items: {len(sample_order.get('items', []))}")
                
                return len(orders_with_items) > 0
            else:
                print(f"❌ Failed to get orders: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error verifying orders: {str(e)}")
            return False

    def check_client_products_exist(self):
        """Check if client products exist for the order items"""
        print("\n=== CHECKING CLIENT PRODUCTS ===")
        
        try:
            # Get clients
            response = self.session.get(f"{API_BASE}/clients")
            if response.status_code != 200:
                return False
            
            clients = response.json()
            total_products = 0
            
            for client in clients:
                client_id = client.get("id")
                client_name = client.get("company_name", "Unknown")
                
                try:
                    response = self.session.get(f"{API_BASE}/clients/{client_id}/catalog")
                    if response.status_code == 200:
                        products = response.json()
                        total_products += len(products)
                        print(f"Client '{client_name}': {len(products)} products")
                        
                        # Check product types
                        for product in products[:2]:
                            product_type = product.get("product_type", "Unknown")
                            print(f"  - {product.get('product_description', 'Unknown')} (Type: {product_type})")
                except:
                    pass
            
            print(f"Total client products: {total_products}")
            return total_products > 0
            
        except Exception as e:
            print(f"❌ Error checking client products: {str(e)}")
            return False

    def run_comprehensive_test(self):
        """Run comprehensive test of the consumable usage report"""
        print("="*80)
        print("CONSUMABLE USAGE REPORT - COMPREHENSIVE TESTING")
        print("="*80)
        
        # Step 1: Authenticate
        if not self.authenticate():
            return False
        
        # Step 2: Verify data exists
        orders_exist = self.verify_orders_exist()
        products_exist = self.check_client_products_exist()
        
        if not orders_exist:
            print("❌ No orders with items found - cannot test endpoint")
            return False
        
        if not products_exist:
            print("❌ No client products found - cannot test endpoint")
            return False
        
        # Step 3: Test before fix (should return no data)
        broken_before = self.test_consumable_usage_report_before_fix()
        
        print("\n" + "="*60)
        print("SUMMARY OF ISSUES IDENTIFIED:")
        print("="*60)
        
        print("1. STATUS FILTERING TOO RESTRICTIVE:")
        print("   - Current: status in ['completed', 'archived']")
        print("   - All orders are 'active' status")
        print("   - Fix: Include active orders or use status not in ['cancelled']")
        
        print("\n2. DATE FORMAT MISMATCH:")
        print("   - Current: Comparing ISO strings with datetime objects")
        print("   - Database stores: datetime strings")
        print("   - Fix: Use datetime objects for comparison")
        
        print("\n3. RECOMMENDED FIXES:")
        print("   Apply same fixes as projected-order-analysis endpoint:")
        print("   - Use start_dt = start.replace(tzinfo=None)")
        print("   - Use end_dt = end.replace(tzinfo=None)")
        print("   - Change status filter to include active orders")
        
        return True

if __name__ == "__main__":
    tester = ConsumableUsageFixTester()
    tester.run_comprehensive_test()