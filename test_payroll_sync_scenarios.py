#!/usr/bin/env python3
"""
Test Payroll Sync Scenarios
Testing various scenarios that could cause users to be missing from payroll
"""

import requests
import json
import os
from datetime import datetime
from dotenv import load_dotenv
import uuid

# Load environment variables
load_dotenv('/app/frontend/.env')

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:8001')
API_BASE = f"{BACKEND_URL}/api"

class PayrollSyncTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_users = []
        
    def authenticate(self):
        """Authenticate with demo user"""
        print("🔐 Authenticating...")
        
        try:
            response = self.session.post(f"{API_BASE}/auth/login", json={
                "username": "Callum",
                "password": "Peach7510"
            })
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get('access_token')
                self.session.headers.update({
                    'Authorization': f'Bearer {self.auth_token}'
                })
                
                user_info = data.get('user', {})
                print(f"✅ Authenticated as {user_info.get('username')} with role {user_info.get('role')}")
                return True
            else:
                print(f"❌ Authentication failed with status {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication error: {str(e)}")
            return False

    def test_scenario_1_reactivate_inactive_user(self):
        """Test Scenario 1: Reactivate inactive user and check if sync picks them up"""
        print("\n" + "="*80)
        print("🧪 TEST SCENARIO 1: Reactivate Inactive User")
        print("Testing if reactivating an inactive user creates employee profile")
        print("="*80)
        
        # Get the inactive user (Bubbles)
        inactive_user_id = "11c8ee97-1177-4f9c-bb6a-d0e9833e0e74"
        
        print("1. Checking current status of inactive user...")
        user_response = self.session.get(f"{API_BASE}/users/{inactive_user_id}")
        if user_response.status_code == 200:
            user = user_response.json()
            print(f"   User: {user.get('full_name')} - Active: {user.get('is_active')}")
        
        # Check if they have employee profile
        employees_response = self.session.get(f"{API_BASE}/payroll/employees")
        if employees_response.status_code == 200:
            employees = employees_response.json()
            has_profile = any(emp.get('user_id') == inactive_user_id for emp in employees)
            print(f"   Has employee profile: {has_profile}")
        
        # Reactivate the user
        print("\n2. Reactivating the user...")
        update_response = self.session.put(f"{API_BASE}/users/{inactive_user_id}", json={
            "is_active": True
        })
        
        if update_response.status_code == 200:
            print("   ✅ User reactivated successfully")
        else:
            print(f"   ❌ Failed to reactivate user: {update_response.status_code}")
            print(f"   Response: {update_response.text}")
            return
        
        # Trigger manual sync
        print("\n3. Triggering manual sync...")
        sync_response = self.session.post(f"{API_BASE}/payroll/employees/sync")
        if sync_response.status_code == 200:
            result = sync_response.json()
            data = result.get("data", {})
            created_count = data.get("created_count", 0)
            print(f"   ✅ Sync completed - Created {created_count} new employee profiles")
        else:
            print(f"   ❌ Sync failed: {sync_response.status_code}")
        
        # Check if employee profile was created
        print("\n4. Checking if employee profile was created...")
        employees_response = self.session.get(f"{API_BASE}/payroll/employees")
        if employees_response.status_code == 200:
            employees = employees_response.json()
            new_employee = next((emp for emp in employees if emp.get('user_id') == inactive_user_id), None)
            
            if new_employee:
                print(f"   ✅ Employee profile created: {new_employee.get('first_name')} {new_employee.get('last_name')} ({new_employee.get('employee_number')})")
            else:
                print("   ❌ No employee profile found for reactivated user")
        
        # Deactivate user again to restore original state
        print("\n5. Restoring original state (deactivating user)...")
        restore_response = self.session.put(f"{API_BASE}/users/{inactive_user_id}", json={
            "is_active": False
        })
        
        if restore_response.status_code == 200:
            print("   ✅ User deactivated (original state restored)")
        else:
            print(f"   ⚠️  Failed to restore original state: {restore_response.status_code}")

    def test_scenario_2_create_new_user_and_sync(self):
        """Test Scenario 2: Create new user and check if sync picks them up"""
        print("\n" + "="*80)
        print("🧪 TEST SCENARIO 2: Create New User and Test Sync")
        print("Testing if newly created users get employee profiles")
        print("="*80)
        
        # Create a new test user
        test_user_data = {
            "username": f"testuser_{str(uuid.uuid4())[:8]}",
            "email": f"test_{str(uuid.uuid4())[:8]}@test.com",
            "password": "TestPassword123!",
            "full_name": "Test User for Payroll Sync",
            "role": "employee",
            "department": "Testing",
            "phone": "0400000000",
            "employment_type": "full_time"
        }
        
        print("1. Creating new test user...")
        create_response = self.session.post(f"{API_BASE}/users", json=test_user_data)
        
        if create_response.status_code == 200:
            result = create_response.json()
            test_user_id = result.get("data", {}).get("id")
            self.test_users.append(test_user_id)
            print(f"   ✅ Test user created with ID: {test_user_id}")
        else:
            print(f"   ❌ Failed to create test user: {create_response.status_code}")
            print(f"   Response: {create_response.text}")
            return
        
        # Check if employee profile exists (should not exist yet)
        print("\n2. Checking if employee profile exists before sync...")
        employees_response = self.session.get(f"{API_BASE}/payroll/employees")
        if employees_response.status_code == 200:
            employees = employees_response.json()
            has_profile = any(emp.get('user_id') == test_user_id for emp in employees)
            print(f"   Has employee profile before sync: {has_profile}")
        
        # Trigger manual sync
        print("\n3. Triggering manual sync...")
        sync_response = self.session.post(f"{API_BASE}/payroll/employees/sync")
        if sync_response.status_code == 200:
            result = sync_response.json()
            data = result.get("data", {})
            created_count = data.get("created_count", 0)
            print(f"   ✅ Sync completed - Created {created_count} new employee profiles")
        else:
            print(f"   ❌ Sync failed: {sync_response.status_code}")
        
        # Check if employee profile was created
        print("\n4. Checking if employee profile was created after sync...")
        employees_response = self.session.get(f"{API_BASE}/payroll/employees")
        if employees_response.status_code == 200:
            employees = employees_response.json()
            new_employee = next((emp for emp in employees if emp.get('user_id') == test_user_id), None)
            
            if new_employee:
                print(f"   ✅ Employee profile created: {new_employee.get('first_name')} {new_employee.get('last_name')} ({new_employee.get('employee_number')})")
                print(f"   Position: {new_employee.get('position')}")
                print(f"   Department: {new_employee.get('department')}")
                print(f"   Hourly Rate: ${new_employee.get('hourly_rate')}")
            else:
                print("   ❌ No employee profile found for new user")

    def test_scenario_3_auto_sync_on_get_employees(self):
        """Test Scenario 3: Test auto-sync when getting employees"""
        print("\n" + "="*80)
        print("🧪 TEST SCENARIO 3: Auto-Sync on GET /api/payroll/employees")
        print("Testing if GET endpoint automatically syncs missing users")
        print("="*80)
        
        # Create another test user
        test_user_data = {
            "username": f"autosync_{str(uuid.uuid4())[:8]}",
            "email": f"autosync_{str(uuid.uuid4())[:8]}@test.com",
            "password": "TestPassword123!",
            "full_name": "Auto Sync Test User",
            "role": "production_team",
            "department": "Production",
            "phone": "0400000001",
            "employment_type": "part_time"
        }
        
        print("1. Creating new test user for auto-sync test...")
        create_response = self.session.post(f"{API_BASE}/users", json=test_user_data)
        
        if create_response.status_code == 200:
            result = create_response.json()
            test_user_id = result.get("data", {}).get("id")
            self.test_users.append(test_user_id)
            print(f"   ✅ Test user created with ID: {test_user_id}")
        else:
            print(f"   ❌ Failed to create test user: {create_response.status_code}")
            return
        
        # Call GET /api/payroll/employees (should trigger auto-sync)
        print("\n2. Calling GET /api/payroll/employees (should auto-sync)...")
        employees_response = self.session.get(f"{API_BASE}/payroll/employees")
        
        if employees_response.status_code == 200:
            employees = employees_response.json()
            auto_synced_employee = next((emp for emp in employees if emp.get('user_id') == test_user_id), None)
            
            if auto_synced_employee:
                print(f"   ✅ Auto-sync worked! Employee profile found: {auto_synced_employee.get('first_name')} {auto_synced_employee.get('last_name')}")
                print(f"   Employee Number: {auto_synced_employee.get('employee_number')}")
                print(f"   Position: {auto_synced_employee.get('position')}")
            else:
                print("   ❌ Auto-sync failed - no employee profile found")
        else:
            print(f"   ❌ Failed to get employees: {employees_response.status_code}")

    def test_scenario_4_edge_cases(self):
        """Test Scenario 4: Edge cases that might cause sync issues"""
        print("\n" + "="*80)
        print("🧪 TEST SCENARIO 4: Edge Cases")
        print("Testing edge cases that might cause sync issues")
        print("="*80)
        
        # Test with user missing required fields
        print("1. Testing user with missing email...")
        test_user_data = {
            "username": f"nomail_{str(uuid.uuid4())[:8]}",
            "email": "",  # Empty email
            "password": "TestPassword123!",
            "full_name": "User With No Email",
            "role": "employee",
            "department": "Testing",
            "phone": "0400000002",
            "employment_type": "casual"
        }
        
        create_response = self.session.post(f"{API_BASE}/users", json=test_user_data)
        if create_response.status_code == 200:
            result = create_response.json()
            test_user_id = result.get("data", {}).get("id")
            self.test_users.append(test_user_id)
            print(f"   ✅ User with empty email created: {test_user_id}")
            
            # Try to sync
            sync_response = self.session.post(f"{API_BASE}/payroll/employees/sync")
            if sync_response.status_code == 200:
                # Check if employee was created
                employees_response = self.session.get(f"{API_BASE}/payroll/employees")
                if employees_response.status_code == 200:
                    employees = employees_response.json()
                    has_profile = any(emp.get('user_id') == test_user_id for emp in employees)
                    print(f"   Employee profile created for user with empty email: {has_profile}")
        else:
            print(f"   ❌ Failed to create user with empty email: {create_response.status_code}")

    def cleanup_test_users(self):
        """Clean up test users created during testing"""
        print("\n🧹 CLEANING UP TEST USERS...")
        
        for user_id in self.test_users:
            try:
                delete_response = self.session.delete(f"{API_BASE}/users/{user_id}")
                if delete_response.status_code == 200:
                    print(f"   ✅ Deleted test user: {user_id}")
                else:
                    print(f"   ⚠️  Failed to delete test user {user_id}: {delete_response.status_code}")
            except Exception as e:
                print(f"   ⚠️  Error deleting test user {user_id}: {str(e)}")

    def run_all_tests(self):
        """Run all test scenarios"""
        print("🚀 STARTING PAYROLL SYNC SCENARIO TESTS")
        print("="*80)
        
        # Authenticate
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return
        
        try:
            # Run test scenarios
            self.test_scenario_1_reactivate_inactive_user()
            self.test_scenario_2_create_new_user_and_sync()
            self.test_scenario_3_auto_sync_on_get_employees()
            self.test_scenario_4_edge_cases()
            
        finally:
            # Always clean up
            self.cleanup_test_users()
        
        print("\n" + "="*80)
        print("🎯 ALL PAYROLL SYNC SCENARIO TESTS COMPLETE")
        print("="*80)

def main():
    """Main test function"""
    tester = PayrollSyncTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()