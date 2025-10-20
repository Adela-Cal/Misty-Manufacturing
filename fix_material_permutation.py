#!/usr/bin/env python3
"""
Fix material permutation by creating proper raw material entry
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

def get_material_data(session):
    """Get material data"""
    response = session.get(f"{API_BASE}/materials")
    if response.status_code == 200:
        materials = response.json()
        if materials:
            return materials[0]  # Return first material
    return None

def update_raw_material_with_material_data(session, material):
    """Update raw material entry to include material properties"""
    print(f"\n=== UPDATING RAW MATERIAL WITH MATERIAL DATA ===")
    
    material_id = material.get('id')
    
    # Find existing raw material for this material
    response = session.get(f"{API_BASE}/stock/raw-materials")
    if response.status_code != 200:
        print(f"❌ Failed to get raw materials: {response.status_code}")
        return None
    
    result = response.json()
    raw_materials = result.get("data", []) if isinstance(result, dict) else result
    
    # Find raw material with matching material_id
    target_raw_material = None
    for rm in raw_materials:
        if rm.get('material_id') == material_id:
            target_raw_material = rm
            break
    
    if not target_raw_material:
        print(f"❌ No raw material found for material ID: {material_id}")
        return None
    
    raw_material_id = target_raw_material.get('id')
    print(f"Found raw material ID: {raw_material_id}")
    
    # Update the raw material with material properties
    # Since we can't modify the model, let's work with what we have
    # The calculator should look at the materials collection for GSM, width, etc.
    # and the raw materials collection for quantity
    
    # Let's check if the calculator is working with the current data
    print(f"Material data:")
    print(f"  GSM: {material.get('gsm')}")
    print(f"  Width: {material.get('master_deckle_width_mm')}")
    print(f"  Price: {material.get('price')}")
    
    print(f"Raw material data:")
    print(f"  Quantity on hand: {target_raw_material.get('quantity_on_hand')}")
    print(f"  Unit: {target_raw_material.get('unit_of_measure')}")
    
    return material_id

def test_permutation_calculation(session, material_id):
    """Test the permutation calculation"""
    print(f"\n=== TESTING PERMUTATION CALCULATION ===")
    
    test_data = {
        "material_id": material_id,
        "waste_allowance_mm": 5,
        "desired_slit_widths": [50, 75, 100],
        "quantity_master_rolls": 2
    }
    
    print(f"Testing with material ID: {material_id}")
    
    response = session.post(f"{API_BASE}/calculators/material-permutation", json=test_data)
    
    print(f"Response status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        result = response.json()
        
        if result.get("success"):
            data = result.get("data", {})
            print(f"✅ SUCCESS! Permutation calculation worked!")
            print(f"   Found {data.get('total_permutations_found', 0)} permutations")
            print(f"   Best yield: {data.get('best_yield_percentage', 0)}%")
            return True
        else:
            print(f"❌ Calculation failed: {result.get('message')}")
    else:
        print(f"❌ Request failed: {response.status_code}")
    
    return False

def debug_calculator_logic(session, material_id):
    """Debug what the calculator is seeing"""
    print(f"\n=== DEBUGGING CALCULATOR LOGIC ===")
    
    # Check what the calculator sees when it looks up the material
    print("1. Checking raw_materials collection for material_id...")
    response = session.get(f"{API_BASE}/stock/raw-materials")
    if response.status_code == 200:
        result = response.json()
        raw_materials = result.get("data", []) if isinstance(result, dict) else result
        
        for rm in raw_materials:
            if rm.get('material_id') == material_id:
                print(f"   Found in raw_materials: {rm}")
                break
        else:
            print(f"   Not found in raw_materials with material_id={material_id}")
    
    print("2. Checking materials collection for id...")
    response = session.get(f"{API_BASE}/materials")
    if response.status_code == 200:
        materials = response.json()
        
        for m in materials:
            if m.get('id') == material_id:
                print(f"   Found in materials: {m}")
                
                # Check the specific fields the calculator needs
                width = m.get("width_mm") or m.get("master_deckle_width_mm", 0)
                gsm = m.get("gsm", 0)
                tonnage = m.get("tonnage", 0)
                quantity = m.get("quantity_on_hand", 0)
                cost = m.get("cost_per_tonne") or m.get("price", 0)
                
                print(f"   Calculator fields:")
                print(f"     width_mm or master_deckle_width_mm: {width}")
                print(f"     gsm: {gsm}")
                print(f"     tonnage: {tonnage}")
                print(f"     quantity_on_hand: {quantity}")
                print(f"     cost_per_tonne or price: {cost}")
                
                if width == 0:
                    print(f"   ❌ Missing width data")
                if gsm == 0:
                    print(f"   ❌ Missing GSM data")
                if tonnage == 0 and quantity == 0:
                    print(f"   ❌ Missing tonnage and quantity data")
                if cost == 0:
                    print(f"   ❌ Missing cost data")
                
                break
        else:
            print(f"   Not found in materials with id={material_id}")

if __name__ == "__main__":
    session = authenticate()
    if session:
        material = get_material_data(session)
        if material:
            material_id = update_raw_material_with_material_data(session, material)
            if material_id:
                debug_calculator_logic(session, material_id)
                success = test_permutation_calculation(session, material_id)
                
                if not success:
                    print(f"\n🔧 ATTEMPTING TO FIX THE ISSUE...")
                    # The issue is that materials don't have tonnage or quantity_on_hand
                    # But raw materials have quantity_on_hand but not GSM/width
                    # The calculator needs to combine data from both collections
                    print(f"   The calculator needs to be fixed to properly combine data from materials and raw_materials collections")
        else:
            print(f"❌ No materials found")