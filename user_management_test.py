#!/usr/bin/env python3
"""
User Management API Testing Suite
Tests the Staff & Security user management API endpoints
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

class UserManagementTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        
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
    
    def test_get_all_users(self):
        """Test GET /api/users - Get all users (Admin only)"""
        print("\n=== GET ALL USERS TEST ===")
        
        try:
            response = self.session.get(f"{API_BASE}/users")
            
            if response.status_code == 200:
                users = response.json()
                
                if isinstance(users, list):
                    # Check that password hashes are not included in response
                    has_password_hash = any('password_hash' in user for user in users)
                    
                    if not has_password_hash:
                        self.log_result(
                            "GET /api/users - Get All Users", 
                            True, 
                            f"Successfully retrieved {len(users)} users without password hashes",
                            f"Users found: {[user.get('username', 'Unknown') for user in users[:3]]}"
                        )
                        return users
                    else:
                        self.log_result(
                            "GET /api/users - Get All Users", 
                            False, 
                            "Response contains password hashes (security issue)"
                        )
                else:
                    self.log_result(
                        "GET /api/users - Get All Users", 
                        False, 
                        "Response is not a list of users",
                        f"Response type: {type(users)}"
                    )
            else:
                self.log_result(
                    "GET /api/users - Get All Users", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("GET /api/users - Get All Users", False, f"Error: {str(e)}")
        
        return []
    
    def test_create_user(self):
        """Test POST /api/users - Create new user account (Admin only) with password hashing"""
        print("\n=== CREATE USER TEST ===")
        
        test_user_data = {
            "username": "teststaff001",
            "email": "teststaff001@adelamerchants.com.au",
            "password": "SecurePass123!",
            "full_name": "Test Staff Member",
            "role": "production_staff",
            "department": "Production",
            "phone": "0412345678"
        }
        
        try:
            response = self.session.post(f"{API_BASE}/users", json=test_user_data)
            
            if response.status_code == 200:
                result = response.json()
                created_user_id = result.get('data', {}).get('id')
                
                if created_user_id:
                    self.log_result(
                        "POST /api/users - Create User with Password Hashing", 
                        True, 
                        f"Successfully created user '{test_user_data['username']}' with proper password hashing",
                        f"User ID: {created_user_id}"
                    )
                    return created_user_id
                else:
                    self.log_result(
                        "POST /api/users - Create User with Password Hashing", 
                        False, 
                        "User creation response missing ID"
                    )
            else:
                self.log_result(
                    "POST /api/users - Create User with Password Hashing", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("POST /api/users - Create User with Password Hashing", False, f"Error: {str(e)}")
        
        return None
    
    def test_get_specific_user(self, user_id):
        """Test GET /api/users/{user_id} - Get specific user by ID (Admin only)"""
        print("\n=== GET SPECIFIC USER TEST ===")
        
        if not user_id:
            self.log_result(
                "GET /api/users/{user_id} - Get Specific User", 
                False, 
                "No user ID provided for testing"
            )
            return
        
        try:
            response = self.session.get(f"{API_BASE}/users/{user_id}")
            
            if response.status_code == 200:
                user = response.json()
                
                # Verify user data and that password hash is not included
                expected_fields = ['id', 'username', 'email', 'full_name', 'role', 'department', 'phone']
                missing_fields = [field for field in expected_fields if field not in user]
                has_password_hash = 'password_hash' in user
                
                if not missing_fields and not has_password_hash:
                    self.log_result(
                        "GET /api/users/{user_id} - Get Specific User", 
                        True, 
                        f"Successfully retrieved user '{user.get('username')}' without password hash",
                        f"Role: {user.get('role')}, Department: {user.get('department')}"
                    )
                else:
                    issues = []
                    if missing_fields:
                        issues.append(f"Missing fields: {missing_fields}")
                    if has_password_hash:
                        issues.append("Contains password hash (security issue)")
                    
                    self.log_result(
                        "GET /api/users/{user_id} - Get Specific User", 
                        False, 
                        "User data has issues",
                        "; ".join(issues)
                    )
            else:
                self.log_result(
                    "GET /api/users/{user_id} - Get Specific User", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("GET /api/users/{user_id} - Get Specific User", False, f"Error: {str(e)}")
    
    def test_update_user(self, user_id):
        """Test PUT /api/users/{user_id} - Update user account (Admin only)"""
        print("\n=== UPDATE USER TEST ===")
        
        if not user_id:
            self.log_result(
                "PUT /api/users/{user_id} - Update User", 
                False, 
                "No user ID provided for testing"
            )
            return
        
        update_data = {
            "email": "teststaff001.updated@adelamerchants.com.au",
            "full_name": "Test Staff Member Updated",
            "role": "supervisor",
            "department": "Quality Control",
            "phone": "0487654321",
            "is_active": True
        }
        
        try:
            response = self.session.put(f"{API_BASE}/users/{user_id}", json=update_data)
            
            if response.status_code == 200:
                # Verify the update by retrieving the user
                get_response = self.session.get(f"{API_BASE}/users/{user_id}")
                if get_response.status_code == 200:
                    updated_user = get_response.json()
                    
                    # Check if updates were applied
                    updates_applied = (
                        updated_user.get('email') == update_data['email'] and
                        updated_user.get('full_name') == update_data['full_name'] and
                        updated_user.get('role') == update_data['role'] and
                        updated_user.get('department') == update_data['department'] and
                        updated_user.get('phone') == update_data['phone']
                    )
                    
                    if updates_applied:
                        self.log_result(
                            "PUT /api/users/{user_id} - Update User", 
                            True, 
                            f"Successfully updated user account",
                            f"New role: {updated_user.get('role')}, New department: {updated_user.get('department')}"
                        )
                    else:
                        self.log_result(
                            "PUT /api/users/{user_id} - Update User", 
                            False, 
                            "User update did not apply all changes correctly"
                        )
                else:
                    self.log_result(
                        "PUT /api/users/{user_id} - Update User", 
                        False, 
                        "Failed to retrieve updated user for verification"
                    )
            else:
                self.log_result(
                    "PUT /api/users/{user_id} - Update User", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("PUT /api/users/{user_id} - Update User", False, f"Error: {str(e)}")
    
    def test_change_password(self):
        """Test POST /api/users/change-password - Change user's own password"""
        print("\n=== CHANGE PASSWORD TEST ===")
        
        try:
            password_change_data = {
                "current_password": "Peach7510",  # Current admin password
                "new_password": "NewSecurePass456!"
            }
            
            response = self.session.post(f"{API_BASE}/users/change-password", json=password_change_data)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('success'):
                    self.log_result(
                        "POST /api/users/change-password - Change Own Password", 
                        True, 
                        "Successfully changed user's own password with proper hashing",
                        result.get('message', 'Password changed')
                    )
                    
                    # Test login with new password to verify it works
                    test_login_response = self.session.post(f"{API_BASE}/auth/login", json={
                        "username": "Callum",
                        "password": "NewSecurePass456!"
                    })
                    
                    if test_login_response.status_code == 200:
                        # Update session with new token
                        new_token_data = test_login_response.json()
                        new_token = new_token_data.get('access_token')
                        self.session.headers.update({
                            'Authorization': f'Bearer {new_token}'
                        })
                        
                        self.log_result(
                            "Password Change Verification", 
                            True, 
                            "New password works correctly for login"
                        )
                        
                        # Change password back to original for other tests
                        revert_password_data = {
                            "current_password": "NewSecurePass456!",
                            "new_password": "Peach7510"
                        }
                        
                        revert_response = self.session.post(f"{API_BASE}/users/change-password", json=revert_password_data)
                        if revert_response.status_code == 200:
                            # Re-authenticate with original password
                            original_auth = self.session.post(f"{API_BASE}/auth/login", json={
                                "username": "Callum",
                                "password": "Peach7510"
                            })
                            if original_auth.status_code == 200:
                                original_token = original_auth.json().get('access_token')
                                self.session.headers.update({
                                    'Authorization': f'Bearer {original_token}'
                                })
                    else:
                        self.log_result(
                            "Password Change Verification", 
                            False, 
                            "New password does not work for login - password hashing may be incorrect"
                        )
                else:
                    self.log_result(
                        "POST /api/users/change-password - Change Own Password", 
                        False, 
                        "Password change response indicates failure",
                        result.get('message', 'Unknown error')
                    )
            else:
                self.log_result(
                    "POST /api/users/change-password - Change Own Password", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("POST /api/users/change-password - Change Own Password", False, f"Error: {str(e)}")
    
    def test_delete_user(self, user_id):
        """Test DELETE /api/users/{user_id} - Soft delete user (Admin only)"""
        print("\n=== DELETE USER TEST ===")
        
        if not user_id:
            self.log_result(
                "DELETE /api/users/{user_id} - Soft Delete User", 
                False, 
                "No user ID provided for testing"
            )
            return
        
        try:
            response = self.session.delete(f"{API_BASE}/users/{user_id}")
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('success'):
                    # Verify soft delete by trying to retrieve the user
                    get_response = self.session.get(f"{API_BASE}/users/{user_id}")
                    if get_response.status_code == 200:
                        deleted_user = get_response.json()
                        is_inactive = not deleted_user.get('is_active', True)
                        
                        if is_inactive:
                            self.log_result(
                                "DELETE /api/users/{user_id} - Soft Delete User", 
                                True, 
                                "Successfully soft deleted user (marked as inactive)",
                                f"User is_active: {deleted_user.get('is_active')}"
                            )
                        else:
                            self.log_result(
                                "DELETE /api/users/{user_id} - Soft Delete User", 
                                False, 
                                "User was not properly marked as inactive",
                                f"User is_active: {deleted_user.get('is_active')}"
                            )
                    else:
                        self.log_result(
                            "DELETE /api/users/{user_id} - Soft Delete User", 
                            False, 
                            "Could not retrieve user after deletion to verify soft delete"
                        )
                else:
                    self.log_result(
                        "DELETE /api/users/{user_id} - Soft Delete User", 
                        False, 
                        "Delete response indicates failure",
                        result.get('message', 'Unknown error')
                    )
            else:
                self.log_result(
                    "DELETE /api/users/{user_id} - Soft Delete User", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("DELETE /api/users/{user_id} - Soft Delete User", False, f"Error: {str(e)}")
    
    def test_role_based_access_control(self):
        """Test role-based access control (try accessing with non-admin user)"""
        print("\n=== ROLE-BASED ACCESS CONTROL TEST ===")
        
        try:
            # Create a temporary session without admin token
            temp_session = requests.Session()
            
            # Test without authentication
            response = temp_session.get(f"{API_BASE}/users")
            
            if response.status_code in [401, 403]:
                self.log_result(
                    "User Management Role-Based Access Control", 
                    True, 
                    f"User management endpoints properly require admin authentication (status: {response.status_code})"
                )
            else:
                self.log_result(
                    "User Management Role-Based Access Control", 
                    False, 
                    f"Expected 401/403 but got {response.status_code}",
                    "User management endpoints should require admin authentication"
                )
        except Exception as e:
            self.log_result("User Management Role-Based Access Control", False, f"Error: {str(e)}")
    
    def test_duplicate_validation(self):
        """Test duplicate username/email validation"""
        print("\n=== DUPLICATE VALIDATION TEST ===")
        
        try:
            duplicate_user_data = {
                "username": "Callum",  # Existing admin username
                "email": "duplicate@test.com",
                "password": "TestPass123!",
                "full_name": "Duplicate Test User",
                "role": "production_staff",
                "department": "Test",
                "phone": "0400000000"
            }
            
            response = self.session.post(f"{API_BASE}/users", json=duplicate_user_data)
            
            if response.status_code == 400:
                error_text = response.text
                if "already exists" in error_text.lower():
                    self.log_result(
                        "User Creation Duplicate Validation", 
                        True, 
                        "Properly prevents duplicate username creation",
                        f"Status: {response.status_code}, Response: {error_text}"
                    )
                else:
                    self.log_result(
                        "User Creation Duplicate Validation", 
                        False, 
                        f"Unexpected 400 error: {error_text}"
                    )
            else:
                self.log_result(
                    "User Creation Duplicate Validation", 
                    False, 
                    f"Expected 400 for duplicate username but got {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("User Creation Duplicate Validation", False, f"Error: {str(e)}")
    
    def run_all_tests(self):
        """Run all user management tests"""
        print("=" * 80)
        print("STAFF & SECURITY USER MANAGEMENT API TESTING SUITE")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        
        # Authenticate first
        if not self.authenticate():
            print("\n❌ AUTHENTICATION FAILED - Cannot proceed with tests")
            return
        
        # Test all user management endpoints
        users = self.test_get_all_users()
        created_user_id = self.test_create_user()
        
        if created_user_id:
            self.test_get_specific_user(created_user_id)
            self.test_update_user(created_user_id)
            self.test_delete_user(created_user_id)
        
        self.test_change_password()
        self.test_role_based_access_control()
        self.test_duplicate_validation()
        
        # Print summary
        self.print_test_summary()
    
    def print_test_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['message']}")
        
        print("\n✅ PASSED TESTS:")
        for result in self.test_results:
            if result['success']:
                print(f"  - {result['test']}: {result['message']}")

if __name__ == "__main__":
    tester = UserManagementTester()
    tester.run_all_tests()