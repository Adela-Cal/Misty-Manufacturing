#!/usr/bin/env python3
"""
Detailed Analysis of Job Cards and Client Products for Profitability Report Debugging
"""

import requests
import json
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:8001')
API_BASE = f"{BACKEND_URL}/api"

class DetailedAnalyzer:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        
    def authenticate(self):
        """Authenticate with admin credentials"""
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

    def analyze_job_cards(self):
        """Detailed analysis of job cards structure"""
        print("\n" + "="*80)
        print("DETAILED JOB CARDS ANALYSIS")
        print("="*80)
        
        try:
            response = self.session.get(f"{API_BASE}/production/job-cards/search")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict) and 'data' in data:
                    job_cards = data['data']
                else:
                    job_cards = data
                
                print(f"Found {len(job_cards)} job cards")
                
                if len(job_cards) > 0:
                    # Analyze first job card in detail
                    sample_job_card = job_cards[0]
                    
                    print(f"\nSample Job Card Structure:")
                    print(json.dumps(sample_job_card, indent=2, default=str))
                    
                    print(f"\nAll fields in job card:")
                    for field in sorted(sample_job_card.keys()):
                        value = sample_job_card[field]
                        value_type = type(value).__name__
                        if isinstance(value, (list, dict)):
                            print(f"  {field}: {value_type} (length: {len(value) if hasattr(value, '__len__') else 'N/A'})")
                        else:
                            print(f"  {field}: {value_type} = {value}")
                    
                    return job_cards
                else:
                    print("No job cards found")
            else:
                print(f"Failed to get job cards: {response.status_code}")
                print(response.text)
                
        except Exception as e:
            print(f"Error analyzing job cards: {str(e)}")
        
        return []

    def analyze_client_products(self):
        """Detailed analysis of client products structure"""
        print("\n" + "="*80)
        print("DETAILED CLIENT PRODUCTS ANALYSIS")
        print("="*80)
        
        try:
            # Get clients first
            clients_response = self.session.get(f"{API_BASE}/clients")
            
            if clients_response.status_code == 200:
                clients = clients_response.json()
                
                if clients and len(clients) > 0:
                    client = clients[0]
                    client_id = client.get('id')
                    
                    print(f"Analyzing products for client: {client.get('company_name')}")
                    
                    # Get client products
                    response = self.session.get(f"{API_BASE}/clients/{client_id}/catalog")
                    
                    if response.status_code == 200:
                        client_products = response.json()
                        
                        print(f"Found {len(client_products)} client products")
                        
                        if len(client_products) > 0:
                            # Analyze first client product in detail
                            sample_product = client_products[0]
                            
                            print(f"\nSample Client Product Structure:")
                            print(json.dumps(sample_product, indent=2, default=str))
                            
                            print(f"\nAll fields in client product:")
                            for field in sorted(sample_product.keys()):
                                value = sample_product[field]
                                value_type = type(value).__name__
                                if isinstance(value, (list, dict)):
                                    print(f"  {field}: {value_type} (length: {len(value) if hasattr(value, '__len__') else 'N/A'})")
                                else:
                                    print(f"  {field}: {value_type} = {value}")
                            
                            return client_products
                        else:
                            print("No client products found")
                    else:
                        print(f"Failed to get client products: {response.status_code}")
                        print(response.text)
                else:
                    print("No clients found")
            else:
                print(f"Failed to get clients: {clients_response.status_code}")
                
        except Exception as e:
            print(f"Error analyzing client products: {str(e)}")
        
        return []

    def analyze_orders(self):
        """Detailed analysis of orders structure"""
        print("\n" + "="*80)
        print("DETAILED ORDERS ANALYSIS")
        print("="*80)
        
        try:
            response = self.session.get(f"{API_BASE}/orders")
            
            if response.status_code == 200:
                orders = response.json()
                
                print(f"Found {len(orders)} orders")
                
                if len(orders) > 0:
                    # Analyze first order in detail
                    sample_order = orders[0]
                    
                    print(f"\nSample Order Structure:")
                    print(json.dumps(sample_order, indent=2, default=str))
                    
                    print(f"\nAll fields in order:")
                    for field in sorted(sample_order.keys()):
                        value = sample_order[field]
                        value_type = type(value).__name__
                        if isinstance(value, (list, dict)):
                            print(f"  {field}: {value_type} (length: {len(value) if hasattr(value, '__len__') else 'N/A'})")
                        else:
                            print(f"  {field}: {value_type} = {value}")
                    
                    # Analyze order items if they exist
                    items = sample_order.get('items', [])
                    if items and len(items) > 0:
                        print(f"\nSample Order Item Structure:")
                        sample_item = items[0]
                        print(json.dumps(sample_item, indent=2, default=str))
                    
                    return orders
                else:
                    print("No orders found")
            else:
                print(f"Failed to get orders: {response.status_code}")
                print(response.text)
                
        except Exception as e:
            print(f"Error analyzing orders: {str(e)}")
        
        return []

    def analyze_materials(self):
        """Detailed analysis of materials structure"""
        print("\n" + "="*80)
        print("DETAILED MATERIALS ANALYSIS")
        print("="*80)
        
        try:
            response = self.session.get(f"{API_BASE}/materials")
            
            if response.status_code == 200:
                materials = response.json()
                
                print(f"Found {len(materials)} materials")
                
                if len(materials) > 0:
                    # Analyze first material in detail
                    sample_material = materials[0]
                    
                    print(f"\nSample Material Structure:")
                    print(json.dumps(sample_material, indent=2, default=str))
                    
                    return materials
                else:
                    print("No materials found")
            else:
                print(f"Failed to get materials: {response.status_code}")
                print(response.text)
                
        except Exception as e:
            print(f"Error analyzing materials: {str(e)}")
        
        return []

def main():
    """Main analysis execution"""
    analyzer = DetailedAnalyzer()
    
    print("="*80)
    print("DETAILED PROFITABILITY REPORT DATA SOURCES ANALYSIS")
    print("="*80)
    
    # Authenticate first
    if not analyzer.authenticate():
        print("❌ Authentication failed. Cannot proceed with analysis.")
        return
    
    # Run detailed analysis
    analyzer.analyze_job_cards()
    analyzer.analyze_client_products()
    analyzer.analyze_orders()
    analyzer.analyze_materials()

if __name__ == "__main__":
    main()