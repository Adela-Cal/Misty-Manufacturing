#!/usr/bin/env python3
"""
Debug script to check the current state of order ADM-2025-0007
"""

import requests
import json
import os
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
        print("✅ Authentication successful")
        return session
    else:
        print(f"❌ Authentication failed: {response.status_code}")
        return None

def debug_order_state():
    """Debug the current state of order ADM-2025-0007"""
    session = authenticate()
    if not session:
        return
    
    # Find the order
    response = session.get(f"{API_BASE}/orders")
    if response.status_code != 200:
        print(f"❌ Failed to get orders: {response.status_code}")
        return
    
    orders = response.json()
    target_order = None
    
    for order in orders:
        if order.get("order_number") == "ADM-2025-0007":
            target_order = order
            break
    
    if not target_order:
        print("❌ Order ADM-2025-0007 not found")
        return
    
    # Get detailed order information
    order_id = target_order["id"]
    response = session.get(f"{API_BASE}/orders/{order_id}")
    
    if response.status_code != 200:
        print(f"❌ Failed to get order details: {response.status_code}")
        return
    
    order_data = response.json()
    
    print("\n" + "="*80)
    print("ORDER ADM-2025-0007 CURRENT STATE")
    print("="*80)
    
    print(f"Order ID: {order_data.get('id')}")
    print(f"Order Number: {order_data.get('order_number')}")
    print(f"Current Stage: {order_data.get('current_stage')}")
    print(f"Status: {order_data.get('status')}")
    print(f"Partially Invoiced: {order_data.get('partially_invoiced', False)}")
    print(f"Invoiced: {order_data.get('invoiced', False)}")
    print(f"Fully Invoiced: {order_data.get('fully_invoiced', False)}")
    
    # Show items
    items = order_data.get("items", [])
    print(f"\nItems ({len(items)}):")
    for i, item in enumerate(items):
        print(f"  {i+1}. {item.get('product_name')} - Quantity: {item.get('quantity')}")
    
    # Show invoice history
    invoice_history = order_data.get("invoice_history", [])
    print(f"\nInvoice History ({len(invoice_history)} entries):")
    
    total_invoiced = 0
    for i, inv in enumerate(invoice_history):
        inv_items = inv.get("items", [])
        inv_quantity = sum(item.get("quantity", 0) for item in inv_items)
        total_invoiced += inv_quantity
        
        print(f"  {i+1}. {inv.get('invoice_number')} - Date: {inv.get('date')} - Quantity: {inv_quantity}")
        
        # Show items in this invoice
        for j, item in enumerate(inv_items):
            print(f"     Item {j+1}: {item.get('product_name', 'Unknown')} - Qty: {item.get('quantity', 0)}")
    
    print(f"\nTotal Invoiced Quantity: {total_invoiced}")
    
    if items:
        total_ordered = items[0].get("quantity", 0)
        print(f"Total Ordered Quantity: {total_ordered}")
        print(f"Remaining to Invoice: {total_ordered - total_invoiced}")

if __name__ == "__main__":
    debug_order_state()