#!/usr/bin/env python3
"""
Database Migration Script - Add Version Fields
For Multi-User Concurrent Access - Optimistic Locking

This script adds version fields to critical collections to support
optimistic locking and prevent concurrent modification conflicts.

Collections to update:
- orders: Add version field (default: 1)
- timesheets: Add version field (default: 1)  
- employee_profiles: Add version field (default: 1)

Usage:
    python add_version_fields.py

Note: This script is idempotent - safe to run multiple times.
"""

import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv('/app/backend/.env')

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME')

if not MONGO_URL or not DB_NAME:
    print("❌ Error: MONGO_URL or DB_NAME not found in environment")
    sys.exit(1)

async def add_version_to_collection(db, collection_name):
    """Add version field to documents in a collection"""
    collection = db[collection_name]
    
    # Count documents without version field
    count_without_version = await collection.count_documents({"version": {"$exists": False}})
    
    if count_without_version == 0:
        print(f"✅ {collection_name}: All documents already have version field")
        return 0
    
    print(f"📝 {collection_name}: Adding version field to {count_without_version} documents...")
    
    # Update all documents without version field
    result = await collection.update_many(
        {"version": {"$exists": False}},
        {
            "$set": {
                "version": 1,
                "version_updated_at": datetime.utcnow().isoformat()
            }
        }
    )
    
    print(f"✅ {collection_name}: Updated {result.modified_count} documents")
    return result.modified_count

async def create_indexes(db):
    """Create compound indexes for optimistic locking queries"""
    
    # Index on orders for version checking during updates
    await db.orders.create_index([("id", 1), ("version", 1)])
    print("✅ Created compound index on orders (id, version)")
    
    # Index on timesheets for version checking
    await db.timesheets.create_index([("id", 1), ("version", 1)])
    print("✅ Created compound index on timesheets (id, version)")
    
    # Index on employee_profiles for version checking
    await db.employee_profiles.create_index([("id", 1), ("version", 1)])
    print("✅ Created compound index on employee_profiles (id, version)")

async def verify_migration(db):
    """Verify that migration was successful"""
    collections = ['orders', 'timesheets', 'employee_profiles']
    
    print("\n" + "="*60)
    print("MIGRATION VERIFICATION")
    print("="*60)
    
    for collection_name in collections:
        collection = db[collection_name]
        
        total_count = await collection.count_documents({})
        with_version = await collection.count_documents({"version": {"$exists": True}})
        without_version = await collection.count_documents({"version": {"$exists": False}})
        
        status = "✅ PASS" if without_version == 0 else "❌ FAIL"
        print(f"{status} {collection_name}:")
        print(f"  Total documents: {total_count}")
        print(f"  With version field: {with_version}")
        print(f"  Without version field: {without_version}")
        
        if total_count > 0 and without_version == 0:
            # Sample one document to show version field
            sample = await collection.find_one({"version": {"$exists": True}})
            if sample:
                print(f"  Sample version value: {sample.get('version')}")

async def main():
    """Main migration function"""
    print("\n" + "="*60)
    print("DATABASE MIGRATION: Add Version Fields for Optimistic Locking")
    print("="*60)
    print(f"Database: {DB_NAME}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("="*60 + "\n")
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    try:
        # Test connection
        await db.command('ping')
        print("✅ Connected to MongoDB successfully\n")
        
        # Add version fields to collections
        collections = ['orders', 'timesheets', 'employee_profiles']
        total_updated = 0
        
        for collection_name in collections:
            updated = await add_version_to_collection(db, collection_name)
            total_updated += updated
        
        print(f"\n📊 Total documents updated: {total_updated}")
        
        # Create indexes
        print("\n📇 Creating compound indexes...")
        await create_indexes(db)
        
        # Verify migration
        await verify_migration(db)
        
        print("\n" + "="*60)
        print("✅ MIGRATION COMPLETED SUCCESSFULLY")
        print("="*60)
        print("\nNext steps:")
        print("1. ✅ Version fields added to all documents")
        print("2. ✅ Compound indexes created for optimistic locking")
        print("3. ⏳ Update backend endpoints to use version checking")
        print("4. ⏳ Update frontend to include version in update requests")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(main())
