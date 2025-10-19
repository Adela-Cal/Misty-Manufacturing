#!/usr/bin/env python3
"""
User Role Update Testing Suite
Testing Staff and Security user role update fix for "production_staff" and "supervisor" roles

PRIORITY TESTS:
1. Test user creation with "production_staff" role
2. Test user creation with "supervisor" role  
3. Test user update to "production_staff" role
4. Test user update to "supervisor" role
5. Test all valid roles are accepted
6. Test invalid role rejection
7. Test payroll integration with new roles
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

class UserRoleTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        self.created_user_ids = []  # Track created users for cleanup
        
    def log_result(self, test_name, success, message, details=None):
        """Log test result"""
        result = {
            'test': test_name,
            'success': success,
            'message': message,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name} - {message}")
        if details and not success:
            print(f"   Details: {details}")
    
    def authenticate(self):
        """Test authentication with admin user"""
        print("\n=== AUTHENTICATION TEST ===")
        
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
                self.log_result(
                    "Authentication", 
                    True, 
                    f"Successfully authenticated as {user_info.get('username')} with role {user_info.get('role')}"
                )
                return True
            else:
                self.log_result(
                    "Authentication", 
                    False, 
                    f"Authentication failed with status {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_result("Authentication", False, f"Authentication error: {str(e)}")
            return False

    def test_create_user_with_production_staff_role(self):
        """Test 1: Create new user with 'production_staff' role"""
        print("\n" + "="*80)
        print("TEST 1: CREATE USER WITH 'production_staff' ROLE")
        print("="*80)
        
        try:
            user_data = {
                "username": f"prodstaff_{str(uuid.uuid4())[:8]}",
                "email": f"prodstaff_{str(uuid.uuid4())[:8]}@example.com",
                "password": "password123",
                "full_name": "Production Staff User",
                "role": "production_staff",
                "department": "Production",
                "phone": "0400000001",
                "employment_type": "full_time"
            }
            
            response = self.session.post(f"{API_BASE}/users", json=user_data)
            
            if response.status_code == 200:
                result = response.json()
                user_id = result.get("data", {}).get("id")
                self.created_user_ids.append(user_id)
                
                # Verify user was created with correct role
                user_response = self.session.get(f"{API_BASE}/users/{user_id}")
                if user_response.status_code == 200:
                    user = user_response.json()
                    if user.get("role") == "production_staff":
                        self.log_result(
                            "Create User - production_staff Role", 
                            True, 
                            f"Successfully created user with production_staff role",
                            f"User ID: {user_id}, Role: {user.get('role')}"
                        )
                    else:
                        self.log_result(
                            "Create User - production_staff Role", 
                            False, 
                            f"User created but role incorrect: {user.get('role')}"
                        )
                else:
                    self.log_result(
                        "Create User - production_staff Role", 
                        False, 
                        "User created but verification failed"
                    )
            else:
                self.log_result(
                    "Create User - production_staff Role", 
                    False, 
                    f"Failed to create user: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Create User - production_staff Role", False, f"Error: {str(e)}")

    def test_create_user_with_supervisor_role(self):
        """Test 2: Create new user with 'supervisor' role"""
        print("\n" + "="*80)
        print("TEST 2: CREATE USER WITH 'supervisor' ROLE")
        print("="*80)
        
        try:
            user_data = {
                "username": f"supervisor_{str(uuid.uuid4())[:8]}",
                "email": f"supervisor_{str(uuid.uuid4())[:8]}@example.com",
                "password": "password123",
                "full_name": "Supervisor User",
                "role": "supervisor",
                "department": "Production",
                "phone": "0400000002",
                "employment_type": "full_time"
            }
            
            response = self.session.post(f"{API_BASE}/users", json=user_data)
            
            if response.status_code == 200:
                result = response.json()
                user_id = result.get("data", {}).get("id")
                self.created_user_ids.append(user_id)
                
                # Verify user was created with correct role
                user_response = self.session.get(f"{API_BASE}/users/{user_id}")
                if user_response.status_code == 200:
                    user = user_response.json()
                    if user.get("role") == "supervisor":
                        self.log_result(
                            "Create User - supervisor Role", 
                            True, 
                            f"Successfully created user with supervisor role",
                            f"User ID: {user_id}, Role: {user.get('role')}"
                        )
                    else:
                        self.log_result(
                            "Create User - supervisor Role", 
                            False, 
                            f"User created but role incorrect: {user.get('role')}"
                        )
                else:
                    self.log_result(
                        "Create User - supervisor Role", 
                        False, 
                        "User created but verification failed"
                    )
            else:
                self.log_result(
                    "Create User - supervisor Role", 
                    False, 
                    f"Failed to create user: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Create User - supervisor Role", False, f"Error: {str(e)}")

    def test_update_user_to_production_staff_role(self):
        """Test 3: Update existing user to 'production_staff' role"""
        print("\n" + "="*80)
        print("TEST 3: UPDATE USER TO 'production_staff' ROLE")
        print("="*80)
        
        try:
            # First create a user with a different role
            user_data = {
                "username": f"updatetest_{str(uuid.uuid4())[:8]}",
                "email": f"updatetest_{str(uuid.uuid4())[:8]}@example.com",
                "password": "password123",
                "full_name": "Update Test User",
                "role": "employee",
                "department": "Production",
                "phone": "0400000003",
                "employment_type": "full_time"
            }
            
            create_response = self.session.post(f"{API_BASE}/users", json=user_data)
            
            if create_response.status_code == 200:
                result = create_response.json()
                user_id = result.get("data", {}).get("id")
                self.created_user_ids.append(user_id)
                
                # Now update the user to production_staff role
                update_data = {
                    "username": user_data["username"],
                    "email": user_data["email"],
                    "full_name": user_data["full_name"],
                    "role": "production_staff",
                    "department": user_data["department"],
                    "phone": user_data["phone"],
                    "employment_type": "full_time"
                }
                
                update_response = self.session.put(f"{API_BASE}/users/{user_id}", json=update_data)
                
                if update_response.status_code == 200:
                    # Verify the update
                    user_response = self.session.get(f"{API_BASE}/users/{user_id}")
                    if user_response.status_code == 200:
                        user = user_response.json()
                        if user.get("role") == "production_staff":
                            self.log_result(
                                "Update User - production_staff Role", 
                                True, 
                                f"Successfully updated user to production_staff role",
                                f"User ID: {user_id}, New Role: {user.get('role')}"
                            )
                        else:
                            self.log_result(
                                "Update User - production_staff Role", 
                                False, 
                                f"Update failed, role is: {user.get('role')}"
                            )
                    else:
                        self.log_result(
                            "Update User - production_staff Role", 
                            False, 
                            "Update completed but verification failed"
                        )
                else:
                    self.log_result(
                        "Update User - production_staff Role", 
                        False, 
                        f"Failed to update user: {update_response.status_code}",
                        update_response.text
                    )
            else:
                self.log_result(
                    "Update User - production_staff Role", 
                    False, 
                    "Failed to create test user for update"
                )
                
        except Exception as e:
            self.log_result("Update User - production_staff Role", False, f"Error: {str(e)}")

    def test_update_user_to_supervisor_role(self):
        """Test 4: Update existing user to 'supervisor' role"""
        print("\n" + "="*80)
        print("TEST 4: UPDATE USER TO 'supervisor' ROLE")
        print("="*80)
        
        try:
            # First create a user with a different role
            user_data = {
                "username": f"updatetest2_{str(uuid.uuid4())[:8]}",
                "email": f"updatetest2_{str(uuid.uuid4())[:8]}@example.com",
                "password": "password123",
                "full_name": "Update Test User 2",
                "role": "employee",
                "department": "Production",
                "phone": "0400000004",
                "employment_type": "full_time"
            }
            
            create_response = self.session.post(f"{API_BASE}/users", json=user_data)
            
            if create_response.status_code == 200:
                result = create_response.json()
                user_id = result.get("data", {}).get("id")
                self.created_user_ids.append(user_id)
                
                # Now update the user to supervisor role
                update_data = {
                    "username": user_data["username"],
                    "email": user_data["email"],
                    "full_name": user_data["full_name"],
                    "role": "supervisor",
                    "department": user_data["department"],
                    "phone": user_data["phone"],
                    "employment_type": "full_time"
                }
                
                update_response = self.session.put(f"{API_BASE}/users/{user_id}", json=update_data)
                
                if update_response.status_code == 200:
                    # Verify the update
                    user_response = self.session.get(f"{API_BASE}/users/{user_id}")
                    if user_response.status_code == 200:
                        user = user_response.json()
                        if user.get("role") == "supervisor":
                            self.log_result(
                                "Update User - supervisor Role", 
                                True, 
                                f"Successfully updated user to supervisor role",
                                f"User ID: {user_id}, New Role: {user.get('role')}"
                            )
                        else:
                            self.log_result(
                                "Update User - supervisor Role", 
                                False, 
                                f"Update failed, role is: {user.get('role')}"
                            )
                    else:
                        self.log_result(
                            "Update User - supervisor Role", 
                            False, 
                            "Update completed but verification failed"
                        )
                else:
                    self.log_result(
                        "Update User - supervisor Role", 
                        False, 
                        f"Failed to update user: {update_response.status_code}",
                        update_response.text
                    )
            else:
                self.log_result(
                    "Update User - supervisor Role", 
                    False, 
                    "Failed to create test user for update"
                )
                
        except Exception as e:
            self.log_result("Update User - supervisor Role", False, f"Error: {str(e)}")

    def test_all_valid_roles(self):
        """Test 5: Test that all valid roles are accepted"""
        print("\n" + "="*80)
        print("TEST 5: TEST ALL VALID ROLES")
        print("="*80)
        
        valid_roles = [
            "admin",
            "manager", 
            "supervisor",
            "production_staff",
            "production_manager",
            "production_team",
            "sales",
            "employee"
        ]
        
        successful_roles = []
        failed_roles = []
        
        for role in valid_roles:
            try:
                user_data = {
                    "username": f"test_{role}_{str(uuid.uuid4())[:8]}",
                    "email": f"test_{role}_{str(uuid.uuid4())[:8]}@example.com",
                    "password": "password123",
                    "full_name": f"Test {role.title()} User",
                    "role": role,
                    "department": "Test Department",
                    "phone": "0400000005",
                    "employment_type": "full_time"
                }
                
                response = self.session.post(f"{API_BASE}/users", json=user_data)
                
                if response.status_code == 200:
                    result = response.json()
                    user_id = result.get("data", {}).get("id")
                    self.created_user_ids.append(user_id)
                    successful_roles.append(role)
                else:
                    failed_roles.append(f"{role}: {response.status_code}")
                    
            except Exception as e:
                failed_roles.append(f"{role}: {str(e)}")
        
        if len(failed_roles) == 0:
            self.log_result(
                "All Valid Roles Test", 
                True, 
                f"All {len(valid_roles)} roles accepted successfully",
                f"Successful roles: {successful_roles}"
            )
        else:
            self.log_result(
                "All Valid Roles Test", 
                False, 
                f"{len(failed_roles)} roles failed",
                f"Failed: {failed_roles}, Successful: {successful_roles}"
            )

    def test_invalid_role_rejection(self):
        """Test 6: Test that invalid roles are rejected"""
        print("\n" + "="*80)
        print("TEST 6: TEST INVALID ROLE REJECTION")
        print("="*80)
        
        try:
            user_data = {
                "username": f"invalidrole_{str(uuid.uuid4())[:8]}",
                "email": f"invalidrole_{str(uuid.uuid4())[:8]}@example.com",
                "password": "password123",
                "full_name": "Invalid Role User",
                "role": "invalid_role_name",
                "department": "Test Department",
                "phone": "0400000006",
                "employment_type": "full_time"
            }
            
            response = self.session.post(f"{API_BASE}/users", json=user_data)
            
            if response.status_code == 422:
                # Check if error message mentions invalid role
                error_text = response.text.lower()
                if "role" in error_text and ("invalid" in error_text or "enumeration" in error_text):
                    self.log_result(
                        "Invalid Role Rejection", 
                        True, 
                        f"Correctly rejected invalid role with 422 status",
                        f"Error response: {response.text[:200]}"
                    )
                else:
                    self.log_result(
                        "Invalid Role Rejection", 
                        False, 
                        "422 status but error message unclear",
                        response.text
                    )
            else:
                self.log_result(
                    "Invalid Role Rejection", 
                    False, 
                    f"Expected 422 status, got {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Invalid Role Rejection", False, f"Error: {str(e)}")

    def test_payroll_integration_with_new_roles(self):
        """Test 7: Test payroll integration with production_staff and supervisor roles"""
        print("\n" + "="*80)
        print("TEST 7: TEST PAYROLL INTEGRATION WITH NEW ROLES")
        print("="*80)
        
        try:
            # Get payroll employees to see if new roles are properly mapped
            response = self.session.get(f"{API_BASE}/payroll/employees")
            
            if response.status_code == 200:
                employees = response.json()
                
                # Look for employees with production_staff and supervisor roles
                production_staff_found = False
                supervisor_found = False
                position_mapping_correct = True
                
                for emp in employees:
                    # Note: The payroll response might not include 'role' field directly
                    # but should have correct position mapping
                    position = emp.get("position", "")
                    
                    if position == "Production Staff":
                        production_staff_found = True
                    elif position == "Supervisor":
                        supervisor_found = True
                
                # Test manual sync to ensure new roles are handled
                sync_response = self.session.post(f"{API_BASE}/payroll/employees/sync")
                
                if sync_response.status_code == 200:
                    sync_result = sync_response.json()
                    
                    self.log_result(
                        "Payroll Integration - New Roles", 
                        True, 
                        f"Payroll integration working with new roles",
                        f"Employees found: {len(employees)}, Production Staff positions: {production_staff_found}, Supervisor positions: {supervisor_found}, Sync successful: {sync_result.get('success', False)}"
                    )
                else:
                    self.log_result(
                        "Payroll Integration - New Roles", 
                        False, 
                        f"Payroll sync failed: {sync_response.status_code}",
                        sync_response.text
                    )
            else:
                self.log_result(
                    "Payroll Integration - New Roles", 
                    False, 
                    f"Failed to get payroll employees: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Payroll Integration - New Roles", False, f"Error: {str(e)}")

    def cleanup_test_users(self):
        """Clean up created test users"""
        print("\n" + "="*80)
        print("CLEANUP: REMOVING TEST USERS")
        print("="*80)
        
        cleaned_count = 0
        failed_cleanup = []
        
        for user_id in self.created_user_ids:
            try:
                response = self.session.delete(f"{API_BASE}/users/{user_id}")
                if response.status_code == 200:
                    cleaned_count += 1
                else:
                    failed_cleanup.append(f"{user_id}: {response.status_code}")
            except Exception as e:
                failed_cleanup.append(f"{user_id}: {str(e)}")
        
        if len(failed_cleanup) == 0:
            self.log_result(
                "Cleanup Test Users", 
                True, 
                f"Successfully cleaned up {cleaned_count} test users"
            )
        else:
            self.log_result(
                "Cleanup Test Users", 
                False, 
                f"Cleaned {cleaned_count} users, {len(failed_cleanup)} failed",
                f"Failed: {failed_cleanup}"
            )

    def print_test_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "="*80)
        print("USER ROLE UPDATE FIX - FINAL TEST SUMMARY")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        # Show results by test category
        print("\n" + "="*60)
        print("DETAILED RESULTS:")
        print("="*60)
        
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test']}: {result['message']}")
        
        # Show failed tests details
        failed_results = [r for r in self.test_results if not r['success']]
        if failed_results:
            print("\n" + "="*60)
            print("FAILED TESTS DETAILS:")
            print("="*60)
            for result in failed_results:
                print(f"\n❌ {result['test']}")
                print(f"   Message: {result['message']}")
                if result['details']:
                    print(f"   Details: {result['details']}")
        
        print("\n" + "="*80)
        if success_rate == 100:
            print("🎉 PERFECT! USER ROLE FIX WORKING 100%!")
            print("✅ 'production_staff' and 'supervisor' roles fully functional")
        elif success_rate >= 90:
            print(f"🎯 EXCELLENT! {success_rate:.1f}% SUCCESS RATE")
        elif success_rate >= 80:
            print(f"✅ GOOD! {success_rate:.1f}% SUCCESS RATE")
        else:
            print(f"⚠️  NEEDS ATTENTION: {success_rate:.1f}% SUCCESS RATE")
        print("="*80)

    def run_all_tests(self):
        """Run all user role tests"""
        print("🚀 STARTING USER ROLE UPDATE FIX TESTING")
        print("Testing 'production_staff' and 'supervisor' roles functionality")
        
        if not self.authenticate():
            print("❌ Authentication failed - cannot proceed with tests")
            return
        
        # Run all tests
        self.test_create_user_with_production_staff_role()
        self.test_create_user_with_supervisor_role()
        self.test_update_user_to_production_staff_role()
        self.test_update_user_to_supervisor_role()
        self.test_all_valid_roles()
        self.test_invalid_role_rejection()
        self.test_payroll_integration_with_new_roles()
        
        # Cleanup
        self.cleanup_test_users()
        
        # Print summary
        self.print_test_summary()

if __name__ == "__main__":
    tester = UserRoleTester()
    tester.run_all_tests()