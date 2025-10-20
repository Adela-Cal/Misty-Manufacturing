#!/usr/bin/env python3
"""
Test material permutation with slit widths that will generate permutations
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
        return session
    return None

def test_permutations_with_good_widths():
    """Test with slit widths that will generate permutations"""
    session = authenticate()
    if not session:
        print("❌ Authentication failed")
        return
    
    # Get first material
    response = session.get(f"{API_BASE}/materials")
    if response.status_code != 200:
        print("❌ Failed to get materials")
        return
    
    materials = response.json()
    if not materials:
        print("❌ No materials found")
        return
    
    material_id = materials[0].get('id')
    master_width = 1070.0  # From the material data
    
    print(f"Testing with material: {materials[0].get('product_code')}")
    print(f"Master width: {master_width}mm")
    
    # Test with slit widths that will fit nicely
    # For 1070mm width, let's try widths that divide well
    test_cases = [
        {
            "name": "Small widths that fit well",
            "slit_widths": [200, 300, 400],  # These should fit: 200+300+400=900mm < 1070mm
            "waste_allowance": 50
        },
        {
            "name": "Medium widths",
            "slit_widths": [350, 500],  # 350+500=850mm < 1070mm
            "waste_allowance": 100
        },
        {
            "name": "Large single width",
            "slit_widths": [1000],  # Single 1000mm width < 1070mm
            "waste_allowance": 50
        }
    ]
    
    for test_case in test_cases:
        print(f"\n=== Testing: {test_case['name']} ===")
        
        test_data = {
            "material_id": material_id,
            "waste_allowance_mm": test_case["waste_allowance"],
            "desired_slit_widths": test_case["slit_widths"],
            "quantity_master_rolls": 2
        }
        
        response = session.post(f"{API_BASE}/calculators/material-permutation", json=test_data)
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get("success"):
                data = result.get("data", {})
                permutations_count = data.get("total_permutations_found", 0)
                best_yield = data.get("best_yield_percentage", 0)
                
                print(f"✅ SUCCESS: Found {permutations_count} permutations")
                print(f"   Best yield: {best_yield}%")
                
                # Show first few permutations
                permutations = data.get("permutations", [])
                if permutations:
                    print(f"   Top permutations:")
                    for i, perm in enumerate(permutations[:3]):
                        print(f"   {i+1}. {perm.get('pattern_description')} - Yield: {perm.get('yield_percentage')}%, Waste: {perm.get('waste_mm')}mm")
                else:
                    print(f"   No permutations found (slit widths may not fit)")
            else:
                print(f"❌ Calculation failed: {result.get('message')}")
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"   Response: {response.text}")

if __name__ == "__main__":
    test_permutations_with_good_widths()