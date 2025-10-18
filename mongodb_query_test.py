#!/usr/bin/env python3
"""
Test the exact MongoDB query format used by the endpoint
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

class MongoQueryTester:
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

    def test_exact_endpoint_logic(self):
        """Test the exact logic used by the endpoint"""
        print("="*80)
        print("TESTING EXACT ENDPOINT LOGIC")
        print("="*80)
        
        # Simulate the exact endpoint logic
        start_date = "2020-01-01T00:00:00Z"
        end_date = "2030-12-31T23:59:59Z"
        
        print(f"Input dates:")
        print(f"  start_date: {start_date}")
        print(f"  end_date: {end_date}")
        
        # Parse dates exactly like the endpoint does
        start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        print(f"\nParsed datetime objects:")
        print(f"  start: {start}")
        print(f"  end: {end}")
        
        # Create query exactly like the endpoint does
        query_start_iso = start.isoformat()
        query_end_iso = end.isoformat()
        
        print(f"\nQuery ISO strings (what goes to MongoDB):")
        print(f"  start: {query_start_iso}")
        print(f"  end: {query_end_iso}")
        
        # Get a sample order
        orders_response = self.session.get(f"{API_BASE}/orders")
        if orders_response.status_code == 200:
            orders = orders_response.json()
            if orders:
                sample_order = orders[0]
                order_date = sample_order.get('created_at')
                
                print(f"\nSample order date: {order_date}")
                
                # Test the exact MongoDB query logic
                print(f"\nMongoDB query comparison:")
                print(f"  {query_start_iso} <= {order_date} = {query_start_iso <= order_date}")
                print(f"  {order_date} <= {query_end_iso} = {order_date <= query_end_iso}")
                print(f"  Both conditions: {query_start_iso <= order_date <= query_end_iso}")
                
                # The issue might be in the $gte and $lte operators
                print(f"\nMongoDB operators:")
                print(f"  created_at >= {query_start_iso}: Should match")
                print(f"  created_at <= {query_end_iso}: Should match")
                
                # Check if there's a timezone issue
                if '+' in query_start_iso and '+' not in order_date:
                    print(f"\n🚨 TIMEZONE MISMATCH DETECTED!")
                    print(f"  Query uses timezone: {query_start_iso}")
                    print(f"  Order has no timezone: {order_date}")
                    print(f"  This could cause MongoDB comparison issues")

    def test_with_corrected_dates(self):
        """Test the endpoint with timezone-naive dates"""
        print("\n" + "="*80)
        print("TESTING WITH CORRECTED DATE FORMAT")
        print("="*80)
        
        # Test with timezone-naive dates (remove timezone info)
        start_date = "2020-01-01T00:00:00"  # No Z
        end_date = "2030-12-31T23:59:59"    # No Z
        
        print(f"Testing with timezone-naive dates:")
        print(f"  start_date: {start_date}")
        print(f"  end_date: {end_date}")
        
        # This would require modifying the endpoint, but let's see what happens
        # if we try to call it with these dates
        try:
            response = self.session.get(
                f"{API_BASE}/stock/reports/projected-order-analysis",
                params={
                    "start_date": start_date,
                    "end_date": end_date
                }
            )
            
            print(f"\nResponse status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                data = result.get("data", {})
                summary = data.get("summary", {})
                
                print(f"Orders analyzed: {summary.get('total_orders_analyzed', 0)}")
                print(f"Products found: {summary.get('total_unique_products', 0)}")
            else:
                print(f"Error: {response.text}")
                
        except Exception as e:
            print(f"Error testing corrected dates: {e}")

    def check_order_date_formats_in_detail(self):
        """Check all order date formats in detail"""
        print("\n" + "="*80)
        print("DETAILED ORDER DATE FORMAT ANALYSIS")
        print("="*80)
        
        orders_response = self.session.get(f"{API_BASE}/orders")
        if orders_response.status_code == 200:
            orders = orders_response.json()
            
            print(f"Analyzing {len(orders)} orders:")
            
            for i, order in enumerate(orders):
                created_at = order.get('created_at')
                order_number = order.get('order_number', f'Order {i+1}')
                
                print(f"\n{order_number}:")
                print(f"  Raw: {created_at}")
                print(f"  Type: {type(created_at)}")
                print(f"  Length: {len(str(created_at))}")
                print(f"  Has timezone: {'T' in str(created_at) and ('+' in str(created_at) or 'Z' in str(created_at))}")
                
                # Try to parse it
                try:
                    if isinstance(created_at, str):
                        # Try different parsing methods
                        if created_at.endswith('Z'):
                            parsed = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        elif '+' in created_at:
                            parsed = datetime.fromisoformat(created_at)
                        else:
                            parsed = datetime.fromisoformat(created_at)
                        
                        print(f"  Parsed: {parsed}")
                        print(f"  ISO: {parsed.isoformat()}")
                except Exception as e:
                    print(f"  Parse error: {e}")

    def run_test(self):
        """Run the MongoDB query test"""
        if not self.authenticate():
            print("❌ Authentication failed")
            return
        
        self.test_exact_endpoint_logic()
        self.test_with_corrected_dates()
        self.check_order_date_formats_in_detail()

if __name__ == "__main__":
    tester = MongoQueryTester()
    tester.run_test()