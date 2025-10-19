#!/usr/bin/env python3
"""
Detailed GSM Verification Test
Verify the specific calculations mentioned in the review request
"""

import requests
import json
import os
from datetime import datetime, timedelta
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

def test_specific_gsm_calculations():
    """Test the specific GSM calculations mentioned in the review request"""
    session = authenticate()
    if not session:
        print("❌ Authentication failed")
        return
    
    print("\n" + "="*80)
    print("DETAILED GSM CALCULATION VERIFICATION")
    print("Testing specific examples from review request")
    print("="*80)
    
    # Get projected order analysis
    response = session.get(f"{API_BASE}/stock/reports/projected-order-analysis")
    
    if response.status_code != 200:
        print(f"❌ Failed to get projected order analysis: {response.status_code}")
        return
    
    result = response.json()
    data = result.get("data", {})
    products = data.get("products", [])
    
    print(f"\n📊 ANALYSIS RESULTS:")
    print(f"Found {len(products)} products with projections")
    
    # Look for specific GSM values and verify calculations
    gsm_155_examples = []
    gsm_360_examples = []
    
    for product in products:
        product_name = product.get("product_info", {}).get("product_description", "Unknown")
        material_requirements = product.get("material_requirements", {})
        
        print(f"\n🔍 Product: {product_name}")
        
        for period, layers in material_requirements.items():
            if isinstance(layers, list):
                print(f"  📅 {period.replace('_', ' ').title()}:")
                
                for layer in layers:
                    if layer.get("is_total", False):
                        # Summary row
                        total_cost = layer.get("total_cost", 0)
                        projected_qty = layer.get("projected_quantity", 0)
                        cost_per_core = layer.get("cost_per_core", 0)
                        cost_per_metre_of_core = layer.get("cost_per_metre_of_core", 0)
                        
                        print(f"    💰 SUMMARY: Total Cost: ${total_cost:,.2f}, Qty: {projected_qty:,} cores")
                        print(f"    💰 Cost per core: ${cost_per_core:.4f}, Cost per metre: ${cost_per_metre_of_core:.4f}")
                    else:
                        # Material layer
                        gsm = layer.get("gsm", 0)
                        width_mm = layer.get("width_mm", 0)
                        linear_metres_per_tonne = layer.get("linear_metres_per_tonne", 0)
                        cost_per_meter = layer.get("cost_per_meter", 0)
                        price_per_tonne = layer.get("price_per_tonne", 0)
                        material_name = layer.get("material_name", "Unknown")
                        layer_type = layer.get("layer_type", "Unknown")
                        
                        if gsm > 0:
                            print(f"    📋 {layer_type} ({material_name})")
                            print(f"        GSM: {gsm}, Width: {width_mm}mm")
                            print(f"        Linear metres/tonne: {linear_metres_per_tonne:,.2f}")
                            print(f"        Price/tonne: ${price_per_tonne:,.2f}")
                            print(f"        Cost/meter: ${cost_per_meter:.4f}")
                            
                            # Verify the formula: linear_metres_per_tonne = 1,000,000 / (GSM × width_metres)
                            if width_mm > 0:
                                width_metres = width_mm / 1000
                                expected_linear_metres = 1000000 / (gsm * width_metres)
                                formula_correct = abs(linear_metres_per_tonne - expected_linear_metres) < 1
                                
                                print(f"        ✅ Formula check: Expected {expected_linear_metres:,.2f}, Got {linear_metres_per_tonne:,.2f} {'✅' if formula_correct else '❌'}")
                                
                                # Verify cost calculation: cost_per_meter = price_per_tonne / linear_metres_per_tonne
                                if linear_metres_per_tonne > 0:
                                    expected_cost_per_meter = price_per_tonne / linear_metres_per_tonne
                                    cost_correct = abs(cost_per_meter - expected_cost_per_meter) < 0.0001
                                    
                                    print(f"        ✅ Cost check: Expected ${expected_cost_per_meter:.4f}, Got ${cost_per_meter:.4f} {'✅' if cost_correct else '❌'}")
                                
                                # Collect examples for specific GSM values
                                if gsm == 155:
                                    gsm_155_examples.append({
                                        "width_mm": width_mm,
                                        "width_metres": width_metres,
                                        "linear_metres_per_tonne": linear_metres_per_tonne,
                                        "expected": expected_linear_metres,
                                        "price_per_tonne": price_per_tonne,
                                        "cost_per_meter": cost_per_meter
                                    })
                                elif gsm == 360:
                                    gsm_360_examples.append({
                                        "width_mm": width_mm,
                                        "width_metres": width_metres,
                                        "linear_metres_per_tonne": linear_metres_per_tonne,
                                        "expected": expected_linear_metres,
                                        "price_per_tonne": price_per_tonne,
                                        "cost_per_meter": cost_per_meter
                                    })
    
    # Test specific examples from review request
    print(f"\n" + "="*80)
    print("SPECIFIC EXAMPLES FROM REVIEW REQUEST")
    print("="*80)
    
    if gsm_155_examples:
        print(f"\n🔍 GSM 155 Examples Found: {len(gsm_155_examples)}")
        for i, example in enumerate(gsm_155_examples[:3]):  # Show first 3
            print(f"  Example {i+1}:")
            print(f"    GSM: 155, Width: {example['width_mm']}mm ({example['width_metres']}m)")
            print(f"    Formula: 1,000,000 / (155 × {example['width_metres']}) = {example['expected']:,.2f}")
            print(f"    Actual: {example['linear_metres_per_tonne']:,.2f}")
            print(f"    Price/tonne: ${example['price_per_tonne']:,.2f}")
            print(f"    Cost/meter: ${example['cost_per_meter']:.4f}")
            
            # Check if this matches the review request example (GSM=155, Width=50mm)
            if abs(example['width_mm'] - 50) < 5:  # Allow some tolerance
                print(f"    🎯 MATCHES REVIEW EXAMPLE (GSM=155, Width≈50mm)")
                expected_for_50mm = 1000000 / (155 * 0.05)  # 129,032.26
                print(f"    Expected for 50mm width: {expected_for_50mm:,.2f} metres/tonne")
    
    if gsm_360_examples:
        print(f"\n🔍 GSM 360 Examples Found: {len(gsm_360_examples)}")
        for i, example in enumerate(gsm_360_examples[:3]):  # Show first 3
            print(f"  Example {i+1}:")
            print(f"    GSM: 360, Width: {example['width_mm']}mm ({example['width_metres']}m)")
            print(f"    Formula: 1,000,000 / (360 × {example['width_metres']}) = {example['expected']:,.2f}")
            print(f"    Actual: {example['linear_metres_per_tonne']:,.2f}")
            print(f"    Price/tonne: ${example['price_per_tonne']:,.2f}")
            print(f"    Cost/meter: ${example['cost_per_meter']:.4f}")
    
    # Verify the relationship: Higher GSM = fewer metres per tonne
    if gsm_155_examples and gsm_360_examples:
        avg_155 = sum(ex['linear_metres_per_tonne'] for ex in gsm_155_examples) / len(gsm_155_examples)
        avg_360 = sum(ex['linear_metres_per_tonne'] for ex in gsm_360_examples) / len(gsm_360_examples)
        
        print(f"\n📊 GSM RELATIONSHIP VERIFICATION:")
        print(f"  Average metres/tonne for GSM 155: {avg_155:,.2f}")
        print(f"  Average metres/tonne for GSM 360: {avg_360:,.2f}")
        print(f"  Relationship correct (360 < 155): {'✅' if avg_360 < avg_155 else '❌'}")
        print(f"  Higher GSM = heavier paper = fewer metres per tonne ✅")

if __name__ == "__main__":
    test_specific_gsm_calculations()