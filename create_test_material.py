#!/usr/bin/env python3
"""
Create a test material with all required fields for permutation calculation
"""

import requests
import json
import os
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
        print("✅ Authentication successful")
        return session
    else:
        print(f"❌ Authentication failed: {response.status_code}")
        return None

def update_existing_material(session):
    """Update existing material to have tonnage data"""
    print("\n=== UPDATING EXISTING MATERIAL ===")
    
    # Get first material
    response = session.get(f"{API_BASE}/materials")
    if response.status_code != 200:
        print(f"❌ Failed to get materials: {response.status_code}")
        return None
    
    materials = response.json()
    if not materials:
        print("❌ No materials found")
        return None
    
    material = materials[0]  # Use first material (Paper.Jin01)
    material_id = material.get('id')
    
    print(f"Updating material: {material.get('product_code')} (ID: {material_id})")
    
    # Update material with tonnage data
    update_data = {
        "supplier": material.get("supplier"),
        "product_code": material.get("product_code"),
        "order_to_delivery_time": material.get("order_to_delivery_time", 14),
        "material_description": material.get("material_description", "Test material for permutation calculation"),
        "price": material.get("price", 380.0),
        "currency": material.get("currency", "AUD"),
        "unit": "Tons",
        "raw_substrate": material.get("raw_substrate", True),
        "gsm": material.get("gsm", 155),
        "thickness_mm": material.get("thickness_mm", 0.155),
        "burst_strength_kpa": material.get("burst_strength_kpa", 200),
        "ply_bonding_jm2": material.get("ply_bonding_jm2", 150),
        "moisture_percent": material.get("moisture_percent", 8.0),
        "supplied_roll_weight": material.get("supplied_roll_weight", 1000),
        "master_deckle_width_mm": material.get("master_deckle_width_mm", 1070.0),
        "tonnage": 10.0,  # Add tonnage data
        "quantity_on_hand": 1000.0,  # Add quantity data
        "cost_per_tonne": 380.0  # Add cost per tonne
    }
    
    response = session.put(f"{API_BASE}/materials/{material_id}", json=update_data)
    
    if response.status_code == 200:
        print(f"✅ Successfully updated material with tonnage: 10.0 tons")
        print(f"   GSM: {update_data['gsm']}")
        print(f"   Width: {update_data['master_deckle_width_mm']}mm")
        print(f"   Cost per tonne: ${update_data['cost_per_tonne']}")
        return material_id
    else:
        print(f"❌ Failed to update material: {response.status_code}")
        print(f"Response: {response.text}")
        return None

def test_permutation_with_updated_material(session, material_id):
    """Test permutation calculation with updated material"""
    print(f"\n=== TESTING PERMUTATION WITH UPDATED MATERIAL ===")
    
    test_data = {
        "material_id": material_id,
        "waste_allowance_mm": 5,
        "desired_slit_widths": [50, 75, 100],
        "quantity_master_rolls": 2
    }
    
    response = session.post(f"{API_BASE}/calculators/material-permutation", json=test_data)
    
    if response.status_code == 200:
        result = response.json()
        
        if result.get("success"):
            data = result.get("data", {})
            permutations_count = data.get("total_permutations_found", 0)
            best_yield = data.get("best_yield_percentage", 0)
            
            print(f"✅ Permutation calculation successful!")
            print(f"   Found {permutations_count} permutations")
            print(f"   Best yield: {best_yield}%")
            
            # Show material info
            material_info = data.get("material_info", {})
            print(f"   Material: {material_info.get('material_name')}")
            print(f"   Width: {material_info.get('master_width_mm')}mm")
            print(f"   GSM: {material_info.get('gsm')}")
            print(f"   Linear meters: {material_info.get('total_linear_meters')}")
            
            # Show first few permutations
            permutations = data.get("permutations", [])
            if permutations:
                print(f"\n   Top 3 permutations:")
                for i, perm in enumerate(permutations[:3]):
                    print(f"   {i+1}. {perm.get('pattern_description')} - Yield: {perm.get('yield_percentage')}%, Waste: {perm.get('waste_mm')}mm")
            
            return True
        else:
            print(f"❌ Permutation calculation failed: {result.get('message')}")
    else:
        print(f"❌ Permutation request failed: {response.status_code}")
        print(f"Response: {response.text}")
    
    return False

if __name__ == "__main__":
    session = authenticate()
    if session:
        material_id = update_existing_material(session)
        if material_id:
            success = test_permutation_with_updated_material(session, material_id)
            if success:
                print(f"\n🎉 MATERIAL PERMUTATION CALCULATOR IS NOW WORKING!")
                print(f"   Use material ID: {material_id}")
            else:
                print(f"\n❌ MATERIAL PERMUTATION CALCULATOR STILL HAS ISSUES")
        else:
            print(f"\n❌ FAILED TO UPDATE MATERIAL")