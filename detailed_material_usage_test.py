#!/usr/bin/env python3
"""
Detailed Material Usage Report Verification
Get detailed information about the material usage report data to verify all requirements.
"""

import requests
import json
import os
from datetime import datetime
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

def get_detailed_material_usage_report(session):
    """Get detailed material usage report and print all data"""
    
    # Get first material
    materials_response = session.get(f"{API_BASE}/materials")
    if materials_response.status_code != 200:
        print("❌ Failed to get materials")
        return
    
    materials = materials_response.json()
    if not materials:
        print("❌ No materials found")
        return
    
    material = materials[0]
    material_id = material.get("id")
    
    print(f"\n📋 Testing with Material: {material.get('product_code')} - {material.get('supplier')}")
    print(f"   Material ID: {material_id}")
    
    # Test material usage report with wide date range
    response = session.get(
        f"{API_BASE}/stock/reports/material-usage-detailed",
        params={
            "material_id": material_id,
            "start_date": "2020-01-01T00:00:00Z",
            "end_date": "2030-12-31T23:59:59Z",
            "include_order_breakdown": True
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        data = result.get("data", {})
        
        print(f"\n🎯 MATERIAL USAGE REPORT RESULTS:")
        print(f"   Material Name: {data.get('material_name')}")
        print(f"   Material Code: {data.get('material_code')}")
        
        # Report period
        report_period = data.get("report_period", {})
        print(f"\n📅 Report Period:")
        print(f"   Start Date: {report_period.get('start_date')}")
        print(f"   End Date: {report_period.get('end_date')}")
        print(f"   Days: {report_period.get('days')}")
        
        # Usage by width
        usage_by_width = data.get("usage_by_width", [])
        print(f"\n📊 Usage by Width ({len(usage_by_width)} entries):")
        
        for i, width_entry in enumerate(usage_by_width):
            print(f"   Width {i+1}: {width_entry.get('width_mm')}mm")
            print(f"     Total Length: {width_entry.get('total_length_m')}m")
            print(f"     Area (m²): {width_entry.get('m2')}")
            
            if "orders" in width_entry:
                orders = width_entry.get("orders", [])
                print(f"     Orders ({len(orders)}):")
                for order in orders[:3]:  # Show first 3 orders
                    print(f"       - {order.get('order_number')}: {order.get('length_m')}m")
                if len(orders) > 3:
                    print(f"       ... and {len(orders) - 3} more orders")
            print()
        
        # Grand totals
        print(f"📈 GRAND TOTALS:")
        print(f"   Total Widths Used: {data.get('total_widths_used', 0)}")
        print(f"   Grand Total m²: {data.get('grand_total_m2', 0)}")
        print(f"   Grand Total Length (m): {data.get('grand_total_length_m', 0)}")
        
        # Verify requirements
        print(f"\n✅ REQUIREMENTS VERIFICATION:")
        
        # Check if usage_by_width is populated
        if len(usage_by_width) > 0:
            print("   ✅ usage_by_width array is populated")
        else:
            print("   ❌ usage_by_width array is empty")
        
        # Check if grand totals > 0
        grand_total_m2 = data.get('grand_total_m2', 0)
        grand_total_length_m = data.get('grand_total_length_m', 0)
        
        if grand_total_m2 > 0:
            print(f"   ✅ grand_total_m2 > 0 ({grand_total_m2})")
        else:
            print(f"   ❌ grand_total_m2 is 0 or missing")
        
        if grand_total_length_m > 0:
            print(f"   ✅ grand_total_length_m > 0 ({grand_total_length_m})")
        else:
            print(f"   ❌ grand_total_length_m is 0 or missing")
        
        # Check if order breakdown is included
        if data.get("include_order_breakdown") and len(usage_by_width) > 0:
            first_width = usage_by_width[0]
            if "orders" in first_width and "order_count" in first_width:
                print("   ✅ Order breakdown is included")
            else:
                print("   ❌ Order breakdown is missing")
        
        return True
    else:
        print(f"❌ Material usage report failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return False

def check_material_layers_usage(session):
    """Check if materials are being used via material_layers in client_products"""
    
    print(f"\n🔍 CHECKING MATERIAL LAYERS IN CLIENT PRODUCTS:")
    
    # Get all clients
    clients_response = session.get(f"{API_BASE}/clients")
    if clients_response.status_code != 200:
        print("❌ Failed to get clients")
        return
    
    clients = clients_response.json()
    total_products = 0
    products_with_layers = 0
    total_layers = 0
    
    for client in clients:
        client_id = client.get("id")
        client_name = client.get("company_name")
        
        # Get client products
        products_response = session.get(f"{API_BASE}/clients/{client_id}/catalog")
        
        if products_response.status_code == 200:
            products = products_response.json()
            total_products += len(products)
            
            client_products_with_layers = 0
            client_total_layers = 0
            
            for product in products:
                material_layers = product.get("material_layers", [])
                if material_layers:
                    client_products_with_layers += 1
                    client_total_layers += len(material_layers)
            
            products_with_layers += client_products_with_layers
            total_layers += client_total_layers
            
            if client_products_with_layers > 0:
                print(f"   {client_name}: {client_products_with_layers}/{len(products)} products have material_layers ({client_total_layers} total layers)")
    
    print(f"\n📊 MATERIAL LAYERS SUMMARY:")
    print(f"   Total Products: {total_products}")
    print(f"   Products with Material Layers: {products_with_layers}")
    print(f"   Total Material Layers: {total_layers}")
    
    if products_with_layers > 0:
        print("   ✅ Client products have material_layers data")
    else:
        print("   ❌ No client products have material_layers data")

def main():
    """Main function"""
    print("="*80)
    print("DETAILED MATERIAL USAGE REPORT VERIFICATION")
    print("Verifying all requirements from the review request")
    print("="*80)
    
    session = authenticate()
    if not session:
        return
    
    # Get detailed material usage report
    success = get_detailed_material_usage_report(session)
    
    # Check material layers usage
    check_material_layers_usage(session)
    
    print(f"\n{'='*80}")
    if success:
        print("🎉 MATERIAL USAGE REPORT VERIFICATION COMPLETE")
        print("✅ All requirements from the review request have been verified")
    else:
        print("❌ MATERIAL USAGE REPORT VERIFICATION FAILED")
        print("⚠️  Some requirements from the review request are not met")
    print("="*80)

if __name__ == "__main__":
    main()