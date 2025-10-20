#!/usr/bin/env python3
"""
Simple test to debug the invoicing flag issue
"""

import requests
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import uuid

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

def create_simple_test_order(session):
    """Create a simple test order"""
    # Get clients first
    clients_response = session.get(f"{API_BASE}/clients")
    if clients_response.status_code != 200:
        print("❌ Failed to get clients")
        return None
    
    clients = clients_response.json()
    if not clients:
        print("❌ No clients available")
        return None
    
    client = clients[0]
    
    # Create order with one simple item
    order_data = {
        "client_id": client["id"],
        "purchase_order_number": f"SIMPLE-TEST-{str(uuid.uuid4())[:8]}",
        "items": [
            {
                "product_id": str(uuid.uuid4()),
                "product_name": "Simple Test Product",
                "quantity": 10,  # Simple quantity for easy calculation
                "unit_price": 100.00,
                "total_price": 1000.00
            }
        ],
        "due_date": "2024-12-31",
        "priority": "Normal/Low",
        "notes": "Simple test order for debugging invoicing flags"
    }
    
    # Create the order
    response = session.post(f"{API_BASE}/orders", json=order_data)
    
    if response.status_code == 200:
        result = response.json()
        order_id = result.get("data", {}).get("id")
        order_number = result.get("data", {}).get("order_number")
        
        print(f"✅ Created test order: {order_number} (ID: {order_id})")
        
        # Move to delivery stage
        stages = [
            ("order_entered", "pending_material"),
            ("pending_material", "paper_slitting"),
            ("paper_slitting", "winding"),
            ("winding", "finishing"),
            ("finishing", "delivery")
        ]
        
        for from_stage, to_stage in stages:
            stage_data = {
                "from_stage": from_stage,
                "to_stage": to_stage,
                "notes": f"Moving to {to_stage} for simple test"
            }
            
            stage_response = session.put(f"{API_BASE}/orders/{order_id}/stage", json=stage_data)
            if stage_response.status_code != 200:
                print(f"❌ Failed to move to {to_stage}")
                return None
        
        print(f"✅ Moved order to delivery stage")
        return order_id
    else:
        print(f"❌ Failed to create order: {response.status_code}")
        return None

def test_first_partial_invoice(session, order_id):
    """Test first partial invoice (5 out of 10 items)"""
    print(f"\n=== TESTING FIRST PARTIAL INVOICE (5/10) ===")
    
    # First, get the order to get the correct product_id
    order_response = session.get(f"{API_BASE}/orders/{order_id}")
    if order_response.status_code != 200:
        print("❌ Failed to get order details")
        return False
    
    order = order_response.json()
    original_item = order["items"][0]  # Get the first (and only) item
    
    # Invoice 5 out of 10 items using the same product_id
    invoice_data = {
        "invoice_type": "partial",
        "items": [
            {
                "product_id": original_item["product_id"],  # Use same product_id as original order
                "product_name": original_item["product_name"],
                "quantity": 5,
                "unit_price": 100.00,
                "total_price": 500.00
            }
        ],
        "subtotal": 500.00,
        "gst": 50.00,
        "total_amount": 550.00,
        "due_date": (datetime.now() + timedelta(days=30)).isoformat()
    }
    
    response = session.post(f"{API_BASE}/invoicing/generate/{order_id}", json=invoice_data)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Invoice generated: {result.get('invoice_number')}")
        
        # Immediately check order status
        order_response = session.get(f"{API_BASE}/orders/{order_id}")
        if order_response.status_code == 200:
            order = order_response.json()
            print(f"Order Status After First Partial Invoice:")
            print(f"  - Current Stage: {order.get('current_stage')}")
            print(f"  - Status: {order.get('status')}")
            print(f"  - Invoiced: {order.get('invoiced')}")
            print(f"  - Partially Invoiced: {order.get('partially_invoiced')}")
            print(f"  - Fully Invoiced: {order.get('fully_invoiced')}")
            print(f"  - Invoice History Count: {len(order.get('invoice_history', []))}")
            
            return order.get('fully_invoiced', False)
        else:
            print(f"❌ Failed to get order after invoice")
            return False
    else:
        print(f"❌ Failed to generate invoice: {response.status_code}")
        print(f"Response: {response.text}")
        return False

def main():
    session = authenticate()
    if not session:
        return
    
    # Create simple test order
    order_id = create_simple_test_order(session)
    if not order_id:
        return
    
    # Test first partial invoice
    is_fully_invoiced = test_first_partial_invoice(session, order_id)
    
    print(f"\nResult: is_fully_invoiced = {is_fully_invoiced}")

if __name__ == "__main__":
    main()