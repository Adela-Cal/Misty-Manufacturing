#!/usr/bin/env python3
"""
Debug script to check the date format in leave requests database
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

def debug_leave_dates():
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
    
    # Get pending leave requests to see date format
    print("\n=== CHECKING PENDING LEAVE REQUESTS ===")
    response = session.get(f"{API_BASE}/payroll/leave-requests/pending")
    
    if response.status_code == 200:
        response_data = response.json()
        print(f"Response structure: {type(response_data)}")
        print(f"Response keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'Not a dict'}")
        
        # Handle StandardResponse format
        if isinstance(response_data, dict) and "data" in response_data:
            pending_requests = response_data["data"]
        else:
            pending_requests = response_data
            
        print(f"Found {len(pending_requests)} pending leave requests")
        
        for i, req in enumerate(pending_requests):
            print(f"\nRequest {i+1}:")
            if isinstance(req, dict):
                print(f"  ID: {req.get('id')}")
                print(f"  Status: {req.get('status')}")
                print(f"  Start Date: {req.get('start_date')} (type: {type(req.get('start_date'))})")
                print(f"  End Date: {req.get('end_date')} (type: {type(req.get('end_date'))})")
                print(f"  Employee ID: {req.get('employee_id')}")
                
                # Check if this is our test request
                if req.get('id') == '21e7e913-b17c-469a-b1d0-e94fd1a68fa9':
                    print("  *** THIS IS OUR TEST REQUEST ***")
            else:
                print(f"  Request data: {req} (type: {type(req)})")
    else:
        print(f"Failed to get pending requests: {response.status_code}")
    
    # Check today's date format
    today = datetime.utcnow().date()
    print(f"\n=== DATE COMPARISON ===")
    print(f"Today (datetime.utcnow().date()): {today}")
    print(f"Today isoformat(): {today.isoformat()}")
    print(f"Today type: {type(today)}")
    
    # Test different date formats
    test_date_str = "2025-10-22"
    test_date_obj = datetime.strptime(test_date_str, "%Y-%m-%d").date()
    
    print(f"\nTest date string: {test_date_str}")
    print(f"Test date object: {test_date_obj}")
    print(f"String >= Today isoformat: {test_date_str >= today.isoformat()}")
    print(f"Date object >= Today: {test_date_obj >= today}")

if __name__ == "__main__":
    debug_leave_dates()