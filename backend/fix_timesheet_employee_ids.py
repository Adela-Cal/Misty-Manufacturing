#!/usr/bin/env python3
"""
Fix Timesheet Employee IDs
Updates timesheets to use correct employee_id instead of user_id
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def fix_timesheet_employee_ids():
    """Fix timesheets that are using user_id instead of employee_id"""
    
    # Connect to MongoDB
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    client = AsyncIOMotorClient(mongo_url)
    db = client.misty_manufacturing
    
    print("Starting timesheet employee_id fix...")
    print("-" * 60)
    
    # Get all timesheets
    timesheets = await db.timesheets.find({}).to_list(1000)
    print(f"Found {len(timesheets)} timesheets in database")
    
    # Get all employee profiles
    employee_profiles = await db.employee_profiles.find({}).to_list(1000)
    print(f"Found {len(employee_profiles)} employee profiles")
    
    # Create lookup map: user_id -> employee_id
    user_to_employee = {}
    for emp in employee_profiles:
        if emp.get("user_id"):
            user_to_employee[emp["user_id"]] = emp["id"]
    
    print(f"\nUser to Employee mapping: {len(user_to_employee)} entries")
    for user_id, emp_id in user_to_employee.items():
        print(f"  {user_id[:8]}... -> {emp_id[:8]}...")
    
    # Check and fix timesheets
    print("\n" + "=" * 60)
    print("Checking timesheets...")
    print("=" * 60)
    
    fixed_count = 0
    already_correct = 0
    cannot_fix = 0
    
    for timesheet in timesheets:
        timesheet_id = timesheet.get("id", "unknown")
        employee_id = timesheet.get("employee_id")
        
        if not employee_id:
            print(f"\n⚠️  Timesheet {timesheet_id[:8]}... has no employee_id")
            cannot_fix += 1
            continue
        
        # Check if employee_id exists in employee_profiles
        employee_exists = any(emp["id"] == employee_id for emp in employee_profiles)
        
        if employee_exists:
            print(f"✅ Timesheet {timesheet_id[:8]}... has correct employee_id")
            already_correct += 1
        else:
            # Check if employee_id is actually a user_id
            if employee_id in user_to_employee:
                correct_employee_id = user_to_employee[employee_id]
                print(f"\n🔧 Fixing timesheet {timesheet_id[:8]}...")
                print(f"   Old employee_id (user_id): {employee_id[:8]}...")
                print(f"   New employee_id: {correct_employee_id[:8]}...")
                
                # Update the timesheet
                result = await db.timesheets.update_one(
                    {"id": timesheet_id},
                    {"$set": {"employee_id": correct_employee_id}}
                )
                
                if result.modified_count > 0:
                    print(f"   ✅ Successfully updated!")
                    fixed_count += 1
                else:
                    print(f"   ❌ Failed to update")
            else:
                print(f"\n⚠️  Timesheet {timesheet_id[:8]}... has orphaned employee_id: {employee_id[:8]}...")
                cannot_fix += 1
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total timesheets: {len(timesheets)}")
    print(f"✅ Already correct: {already_correct}")
    print(f"🔧 Fixed: {fixed_count}")
    print(f"⚠️  Cannot fix: {cannot_fix}")
    
    # Verify the fix
    if fixed_count > 0:
        print("\n" + "=" * 60)
        print("VERIFICATION")
        print("=" * 60)
        
        # Re-check timesheets
        updated_timesheets = await db.timesheets.find({}).to_list(1000)
        all_correct = True
        
        for timesheet in updated_timesheets:
            employee_id = timesheet.get("employee_id")
            if employee_id:
                employee_exists = any(emp["id"] == employee_id for emp in employee_profiles)
                if not employee_exists:
                    print(f"❌ Timesheet {timesheet.get('id', 'unknown')[:8]}... still has invalid employee_id")
                    all_correct = False
        
        if all_correct:
            print("✅ All timesheets now have valid employee_ids!")
        else:
            print("⚠️  Some timesheets still have invalid employee_ids")
    
    # Close connection
    client.close()
    print("\nDone!")

if __name__ == "__main__":
    asyncio.run(fix_timesheet_employee_ids())
