#!/usr/bin/env python3
"""
Debug script to investigate the calendar endpoint response structure
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

def debug_calendar_endpoint():
    session = requests.Session()
    
    # Authenticate
    auth_response = session.post(f"{API_BASE}/auth/login", json={
        "username": "Callum",
        "password": "Peach7510"
    })
    
    if auth_response.status_code == 200:
        data = auth_response.json()
        auth_token = data.get('access_token')
        session.headers.update({
            'Authorization': f'Bearer {auth_token}'
        })
        print("✅ Authentication successful")
    else:
        print("❌ Authentication failed")
        return
    
    # Test calendar endpoint
    print("\n=== TESTING CALENDAR ENDPOINT ===")
    response = session.get(f"{API_BASE}/payroll/leave-requests/calendar")
    
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    
    if response.status_code == 200:
        try:
            data = response.json()
            print(f"Response Type: {type(data)}")
            print(f"Response Structure:")
            print(json.dumps(data, indent=2, default=str))
        except Exception as e:
            print(f"Error parsing JSON: {e}")
            print(f"Raw Response: {response.text}")
    else:
        print(f"Error Response: {response.text}")

if __name__ == "__main__":
    debug_calendar_endpoint()