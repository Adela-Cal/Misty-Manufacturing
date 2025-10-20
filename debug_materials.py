#!/usr/bin/env python3
"""
Debug script to check materials data structure
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

def check_materials(session):
    """Check materials data structure"""
    print("\n=== CHECKING MATERIALS DATA ===")
    
    response = session.get(f"{API_BASE}/materials")
    
    if response.status_code == 200:
        materials = response.json()
        print(f"Found {len(materials)} materials")
        
        for i, material in enumerate(materials[:3]):  # Check first 3 materials
            print(f"\nMaterial {i+1}:")
            print(f"  ID: {material.get('id')}")
            print(f"  Product Code: {material.get('product_code')}")
            print(f"  Supplier: {material.get('supplier')}")
            print(f"  GSM: {material.get('gsm')}")
            print(f"  Width MM: {material.get('width_mm')}")
            print(f"  Master Deckle Width MM: {material.get('master_deckle_width_mm')}")
            print(f"  Tonnage: {material.get('tonnage')}")
            print(f"  Quantity on Hand: {material.get('quantity_on_hand')}")
            print(f"  Cost per Tonne: {material.get('cost_per_tonne')}")
            print(f"  Price: {material.get('price')}")
            print(f"  Unit: {material.get('unit')}")
            print(f"  All fields: {list(material.keys())}")
            
            # Check if this material has the required fields for calculation
            has_width = material.get('width_mm') or material.get('master_deckle_width_mm')
            has_gsm = material.get('gsm')
            has_tonnage = material.get('tonnage')
            has_quantity = material.get('quantity_on_hand')
            has_cost = material.get('cost_per_tonne') or material.get('price')
            
            print(f"  ✅ Has Width: {bool(has_width)} ({has_width})")
            print(f"  ✅ Has GSM: {bool(has_gsm)} ({has_gsm})")
            print(f"  ✅ Has Tonnage: {bool(has_tonnage)} ({has_tonnage})")
            print(f"  ✅ Has Quantity: {bool(has_quantity)} ({has_quantity})")
            print(f"  ✅ Has Cost: {bool(has_cost)} ({has_cost})")
            
            if has_width and has_gsm and (has_tonnage or has_quantity) and has_cost:
                print(f"  🎉 Material {i+1} is SUITABLE for permutation calculation!")
                return material
            else:
                print(f"  ⚠️  Material {i+1} is missing required fields")
    else:
        print(f"❌ Failed to get materials: {response.status_code}")
    
    return None

def check_raw_materials(session):
    """Check raw materials data structure"""
    print("\n=== CHECKING RAW MATERIALS DATA ===")
    
    response = session.get(f"{API_BASE}/stock/raw-materials")
    
    if response.status_code == 200:
        result = response.json()
        
        # Handle StandardResponse format
        if isinstance(result, dict) and "data" in result:
            raw_materials = result.get("data", [])
        else:
            raw_materials = result
        
        print(f"Found {len(raw_materials)} raw materials")
        
        for i, material in enumerate(raw_materials[:3]):  # Check first 3 raw materials
            print(f"\nRaw Material {i+1}:")
            print(f"  ID: {material.get('id')}")
            print(f"  Material ID: {material.get('material_id')}")
            print(f"  Material Name: {material.get('material_name')}")
            print(f"  Material Code: {material.get('material_code')}")
            print(f"  Width MM: {material.get('width_mm')}")
            print(f"  Master Deckle Width MM: {material.get('master_deckle_width_mm')}")
            print(f"  GSM: {material.get('gsm')}")
            print(f"  Tonnage: {material.get('tonnage')}")
            print(f"  Quantity on Hand: {material.get('quantity_on_hand')}")
            print(f"  Cost per Tonne: {material.get('cost_per_tonne')}")
            print(f"  Price: {material.get('price')}")
            print(f"  All fields: {list(material.keys())}")
    else:
        print(f"❌ Failed to get raw materials: {response.status_code}")
        print(f"Response: {response.text}")

if __name__ == "__main__":
    session = authenticate()
    if session:
        suitable_material = check_materials(session)
        check_raw_materials(session)
        
        if suitable_material:
            print(f"\n🎯 RECOMMENDED MATERIAL FOR TESTING:")
            print(f"   ID: {suitable_material.get('id')}")
            print(f"   Product Code: {suitable_material.get('product_code')}")
            print(f"   Supplier: {suitable_material.get('supplier')}")
        else:
            print(f"\n⚠️  NO SUITABLE MATERIALS FOUND FOR PERMUTATION CALCULATION")
            print(f"   Materials need: width_mm, gsm, tonnage/quantity_on_hand, cost_per_tonne/price")