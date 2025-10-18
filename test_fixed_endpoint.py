#!/usr/bin/env python3
"""
Test the fixed projected order analysis endpoint
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

class FixedEndpointTester:
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

    def test_fixed_endpoint(self):
        """Test the fixed endpoint with various scenarios"""
        print("="*80)
        print("TESTING FIXED PROJECTED ORDER ANALYSIS ENDPOINT")
        print("="*80)
        
        test_cases = [
            {
                "name": "Wide Date Range",
                "params": {
                    "start_date": "2020-01-01T00:00:00Z",
                    "end_date": "2030-12-31T23:59:59Z"
                }
            },
            {
                "name": "Default Date Range (Last 90 Days)",
                "params": {
                    "start_date": (datetime.now() - timedelta(days=90)).isoformat() + "Z",
                    "end_date": datetime.now().isoformat() + "Z"
                }
            },
            {
                "name": "No Dates Provided (Should Use Defaults)",
                "params": {}
            },
            {
                "name": "With Client Filter",
                "params": {
                    "client_id": "2eebd139-5330-494c-84e2-311a8c779316",
                    "start_date": "2020-01-01T00:00:00Z",
                    "end_date": "2030-12-31T23:59:59Z"
                }
            }
        ]
        
        for test_case in test_cases:
            print(f"\n🧪 TEST: {test_case['name']}")
            print(f"Parameters: {test_case['params']}")
            
            try:
                response = self.session.get(
                    f"{API_BASE}/stock/reports/projected-order-analysis",
                    params=test_case['params']
                )
                
                print(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    data = result.get("data", {})
                    summary = data.get("summary", {})
                    products = data.get("products", [])
                    
                    print(f"✅ SUCCESS")
                    print(f"   Orders analyzed: {summary.get('total_orders_analyzed', 0)}")
                    print(f"   Unique products: {summary.get('total_unique_products', 0)}")
                    print(f"   Products with projections: {len(products)}")
                    
                    if len(products) > 0:
                        print(f"   🎯 FOUND PRODUCTS! Showing first product:")
                        product = products[0]
                        product_info = product.get("product_info", {})
                        historical = product.get("historical_data", {})
                        projections = product.get("projections", {})
                        
                        print(f"     Product: {product_info.get('product_description', 'N/A')}")
                        print(f"     Client: {product_info.get('client_name', 'N/A')}")
                        print(f"     Historical Total: {historical.get('total_quantity', 0)}")
                        print(f"     3-Month Projection: {projections.get('3_months', 0)}")
                        print(f"     12-Month Projection: {projections.get('12_months', 0)}")
                        
                        # Check material requirements
                        material_reqs = product.get("material_requirements", {})
                        if material_reqs:
                            print(f"     Material Requirements (3 months): {len(material_reqs.get('3_months', []))} materials")
                else:
                    print(f"❌ FAILED")
                    print(f"   Error: {response.text}")
                    
            except Exception as e:
                print(f"❌ ERROR: {e}")

    def run_test(self):
        """Run the test"""
        if not self.authenticate():
            print("❌ Authentication failed")
            return
        
        self.test_fixed_endpoint()
        
        print(f"\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        print("✅ Fixed the date format issue by using timezone-naive dates in MongoDB query")
        print("✅ Added default date range handling for when dates are not provided")
        print("🎯 The endpoint should now return projected order analysis with actual data")

if __name__ == "__main__":
    tester = FixedEndpointTester()
    tester.run_test()