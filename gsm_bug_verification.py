#!/usr/bin/env python3
"""
GSM Bug Verification Test

This test verifies the specific bug in the Projected Order Analysis endpoint:
- GSM values are being retrieved from layer data (which doesn't have GSM)
- Instead of being retrieved from the materials database (which has GSM as strings like "155", "360")

Expected Fix:
- Line 5436: gsm = float(layer.get("gsm") or 0)  # WRONG - layer doesn't have GSM
- Should be: gsm = float(material.get("gsm", 0)) if material else 0  # CORRECT - get from material DB
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
    """Get auth token"""
    response = requests.post(f"{API_BASE}/auth/login", json={
        "username": "Callum",
        "password": "Peach7510"
    })
    
    if response.status_code == 200:
        return response.json()['access_token']
    return None

def main():
    print("🔍 GSM BUG VERIFICATION TEST")
    print("=" * 50)
    
    token = authenticate()
    if not token:
        print("❌ Authentication failed")
        return
    
    headers = {'Authorization': f'Bearer {token}'}
    
    # 1. Check materials database for GSM values
    print("\n1. Checking materials database for GSM values...")
    materials_response = requests.get(f"{API_BASE}/materials", headers=headers)
    
    if materials_response.status_code == 200:
        materials = materials_response.json()
        print(f"Found {len(materials)} materials:")
        
        for material in materials[:3]:  # Check first 3
            gsm = material.get('gsm', 'Not set')
            print(f"  - {material.get('supplier', 'Unknown')} {material.get('product_code', 'Unknown')}: GSM = {gsm} (type: {type(gsm)})")
    
    # 2. Check projected order analysis response
    print("\n2. Checking Projected Order Analysis response...")
    analysis_response = requests.get(f"{API_BASE}/stock/reports/projected-order-analysis", headers=headers)
    
    if analysis_response.status_code == 200:
        data = analysis_response.json()
        products = data.get('data', {}).get('products', [])
        
        if products:
            product = products[0]  # Check first product
            material_requirements = product.get('material_requirements', {})
            three_month_data = material_requirements.get('3_months', [])
            
            print(f"Product: {product.get('product_info', {}).get('product_description', 'Unknown')}")
            print(f"Found {len(three_month_data)} material layers:")
            
            for i, material in enumerate(three_month_data[:3]):  # Check first 3 layers
                if material.get('is_total'):
                    continue
                    
                gsm = material.get('gsm', 'Not set')
                material_id = material.get('material_id', 'Unknown')
                material_name = material.get('material_name', 'Unknown')
                linear_metres_per_tonne = material.get('linear_metres_per_tonne')
                
                print(f"  Layer {i+1}: {material_name}")
                print(f"    Material ID: {material_id}")
                print(f"    GSM in response: {gsm} (type: {type(gsm)})")
                print(f"    Linear metres per tonne: {linear_metres_per_tonne}")
                print(f"    Formula working: {'Yes' if linear_metres_per_tonne and linear_metres_per_tonne > 0 else 'No - GSM is 0'}")
                print()
    
    # 3. Summary
    print("🔍 BUG ANALYSIS:")
    print("1. Materials database has GSM as strings: '155', '360'")
    print("2. Projected Order Analysis shows GSM as 0.0 for all materials")
    print("3. This means GSM is being retrieved from layer data (which doesn't have GSM)")
    print("4. Instead of being retrieved from materials database (which has GSM)")
    print()
    print("🛠️  REQUIRED FIX:")
    print("In /app/backend/server.py around line 5436:")
    print("CURRENT: gsm = float(layer.get('gsm') or 0)  # WRONG")
    print("SHOULD BE: gsm = float(material.get('gsm', 0)) if material else 0  # CORRECT")
    print()
    print("This fix should be applied AFTER the material is fetched from database (around line 5502)")

if __name__ == "__main__":
    main()