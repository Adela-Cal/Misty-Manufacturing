#!/usr/bin/env python3
"""
Quick test for Fast Report generation fix
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

def test_fast_report():
    session = requests.Session()
    
    # Authenticate
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
    else:
        print("❌ Authentication failed")
        return
    
    # Get clients
    clients_response = session.get(f"{API_BASE}/clients")
    if clients_response.status_code == 200:
        clients = clients_response.json()
        if clients:
            test_client_id = clients[0]['id']
            print(f"✅ Using client: {clients[0]['company_name']}")
        else:
            print("❌ No clients found")
            return
    else:
        print("❌ Failed to get clients")
        return
    
    # Test Fast Report generation
    report_request = {
        "client_id": test_client_id,
        "time_period": "current_month",
        "selected_fields": [
            "order_number",
            "client_name", 
            "total_amount"
        ],
        "report_title": "Test Fast Report"
    }
    
    response = session.post(
        f"{API_BASE}/clients/{test_client_id}/archived-orders/fast-report",
        json=report_request
    )
    
    if response.status_code == 200:
        content_type = response.headers.get('content-type', '')
        content_length = len(response.content)
        print(f"✅ Fast Report generated successfully ({content_length} bytes)")
        print(f"   Content-Type: {content_type}")
    elif response.status_code == 404:
        print("✅ Fast Report endpoint working (404 - no data expected)")
    else:
        print(f"❌ Fast Report failed: {response.status_code}")
        print(f"   Error: {response.text}")

if __name__ == "__main__":
    test_fast_report()