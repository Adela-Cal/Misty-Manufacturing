#!/usr/bin/env python3
"""
Fix duplicate order numbers using pymongo (synchronous)
"""

from pymongo import MongoClient
import os
from dotenv import load_dotenv
from collections import defaultdict

# Load environment variables
load_dotenv('/app/backend/.env')

MONGO_URL = os.getenv('MONGO_URL', 'mongodb://localhost:27017')
client = MongoClient(MONGO_URL)
db = client.misty_manufacturing

def fix_duplicate_order_numbers():
    """Find and fix duplicate order numbers"""
    
    print("\n=== SCANNING FOR DUPLICATE ORDER NUMBERS ===")
    
    # Get all orders
    orders = list(db.orders.find({}))
    
    # Group orders by order_number
    orders_by_number = defaultdict(list)
    for order in orders:
        order_number = order.get("order_number")
        if order_number:
            orders_by_number[order_number].append(order)
    
    # Find duplicates
    duplicates = {num: orders for num, orders in orders_by_number.items() if len(orders) > 1}
    
    if not duplicates:
        print("✅ No duplicate order numbers found!")
        return
    
    print(f"\n⚠️  Found {len(duplicates)} duplicate order numbers:")
    for order_number, orders in duplicates.items():
        print(f"\n  {order_number} ({len(orders)} orders):")
        for order in orders:
            print(f"    - ID: {order['id']}")
            print(f"      Client: {order.get('client_name')}")
            print(f"      Stage: {order.get('current_stage')}")
            print(f"      Items: {len(order.get('items', []))}")
            if order.get('items'):
                for item in order.get('items', [])[:2]:  # Show first 2 items
                    print(f"        * {item.get('product_name')}: {item.get('quantity')} units")
    
    print("\n=== FIXING DUPLICATE ORDER NUMBERS ===")
    
    # Fix each set of duplicates
    fixed_count = 0
    for order_number, duplicate_orders in duplicates.items():
        # Sort by created_at to keep the oldest one with original number
        duplicate_orders.sort(key=lambda x: x.get('created_at', ''))
        
        print(f"\nProcessing {order_number}:")
        
        for i, order in enumerate(duplicate_orders):
            if i == 0:
                print(f"  ✓ Keeping original (oldest): {order['id']}")
                print(f"    Stage: {order.get('current_stage')}, Items: {', '.join([item.get('product_name', 'Unknown')[:30] for item in order.get('items', [])])}")
                continue
            
            # Generate new unique order number
            year = int(order_number.split("-")[1])
            
            # Find the highest existing order number for this year
            existing_orders = list(db.orders.find(
                {"order_number": {"$regex": f"^ADM-{year}-"}}
            ))
            
            if existing_orders:
                highest_num = max([int(o["order_number"].split("-")[-1]) for o in existing_orders])
                next_number = highest_num + 1
            else:
                next_number = 1
            
            # Generate new order number with uniqueness check
            for attempt in range(100):
                new_order_number = f"ADM-{year}-{next_number:04d}"
                
                # Check if this order number already exists
                existing = db.orders.find_one({"order_number": new_order_number})
                if not existing:
                    break
                
                next_number += 1
            
            # Update the order
            result = db.orders.update_one(
                {"id": order["id"]},
                {"$set": {"order_number": new_order_number}}
            )
            
            if result.modified_count > 0:
                print(f"  ✓ Renumbered: {order['id']} -> {new_order_number}")
                print(f"    Stage: {order.get('current_stage')}, Items: {', '.join([item.get('product_name', 'Unknown')[:30] for item in order.get('items', [])])}")
                fixed_count += 1
            else:
                print(f"  ✗ Failed to renumber: {order['id']}")
    
    print(f"\n✅ Fixed {fixed_count} duplicate order numbers")
    
    # Verify no duplicates remain
    print("\n=== VERIFYING FIX ===")
    orders = list(db.orders.find({}))
    orders_by_number = defaultdict(list)
    for order in orders:
        order_number = order.get("order_number")
        if order_number:
            orders_by_number[order_number].append(order)
    
    remaining_duplicates = {num: orders for num, orders in orders_by_number.items() if len(orders) > 1}
    
    if remaining_duplicates:
        print(f"⚠️  Still {len(remaining_duplicates)} duplicates remaining!")
        for order_number, orders in remaining_duplicates.items():
            print(f"  {order_number}: {len(orders)} orders")
    else:
        print("✅ All duplicate order numbers have been fixed!")

if __name__ == "__main__":
    try:
        fix_duplicate_order_numbers()
    finally:
        client.close()
