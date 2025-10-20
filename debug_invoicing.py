#!/usr/bin/env python3
"""
Debug script to check invoicing quantities and logic
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

def authenticate():
    """Authenticate and return session"""
    session = requests.Session()
    
    response = session.post(f"{API_BASE}/auth/login", json={
        "username": "Callum",
        "password": "Peach7510"
    })
    
    if response.status_code == 200:
        data = response.json()
        auth_token = data.get('access_token')
        session.headers.update({
            'Authorization': f'Bearer {auth_token}'
        })
        print("✅ Authenticated successfully")
        return session
    else:
        print("❌ Authentication failed")
        return None

def check_order_details(session, order_id):
    """Check order details and invoice history"""
    response = session.get(f"{API_BASE}/orders/{order_id}")
    
    if response.status_code == 200:
        order = response.json()
        
        print(f"\n=== ORDER DETAILS ===")
        print(f"Order Number: {order.get('order_number')}")
        print(f"Current Stage: {order.get('current_stage')}")
        print(f"Status: {order.get('status')}")
        print(f"Invoiced: {order.get('invoiced')}")
        print(f"Fully Invoiced: {order.get('fully_invoiced')}")
        print(f"Partially Invoiced: {order.get('partially_invoiced')}")
        
        print(f"\n=== ORIGINAL ORDER ITEMS ===")
        for i, item in enumerate(order.get("items", [])):
            print(f"Item {i+1}: {item.get('product_name')} - Quantity: {item.get('quantity')}")
        
        print(f"\n=== INVOICE HISTORY ({len(order.get('invoice_history', []))}) ===")
        total_invoiced = {}
        
        for i, inv in enumerate(order.get("invoice_history", [])):
            print(f"\nInvoice {i+1}: {inv.get('invoice_number')}")
            for item in inv.get("items", []):
                product_name = item.get("product_name")
                quantity = item.get("quantity", 0)
                print(f"  - {product_name}: {quantity}")
                
                # Track total invoiced
                if product_name:
                    total_invoiced[product_name] = total_invoiced.get(product_name, 0) + quantity
        
        print(f"\n=== TOTAL INVOICED QUANTITIES ===")
        for product_name, total_qty in total_invoiced.items():
            print(f"{product_name}: {total_qty}")
        
        print(f"\n=== REMAINING QUANTITIES ===")
        for item in order.get("items", []):
            product_name = item.get('product_name')
            original_qty = item.get('quantity', 0)
            invoiced_qty = total_invoiced.get(product_name, 0)
            remaining = original_qty - invoiced_qty
            print(f"{product_name}: {remaining} remaining (Original: {original_qty}, Invoiced: {invoiced_qty})")
        
        return order
    else:
        print(f"❌ Failed to get order details: {response.status_code}")
        return None

def main():
    session = authenticate()
    if not session:
        return
    
    # Use the order from the previous test
    order_id = "aad25c84-47ea-4f50-b52d-8998a8c8cea3"  # ADM-2025-0013
    
    order = check_order_details(session, order_id)

if __name__ == "__main__":
    main()