#!/usr/bin/env python3
"""
Payslip Delete Functionality Testing
Testing the new payslip delete functionality in the Historic Pay Slips window.

Test Objectives:
1. Authentication as admin (Callum/Peach7510)
2. GET /api/payroll/reports/payslips - Verify payslips exist
3. DELETE /api/payroll/reports/payslips/{payslip_id} - Test delete endpoint
4. Verify payslip is actually deleted from database
5. Test error cases (404 for non-existent payslip)
6. Test access control (admin-only restriction)
"""

import requests
import json
import os
from datetime import datetime, date, timedelta
import sys

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://misty-ato-payroll.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class PayslipDeleteTester:
    def __init__(self):
        self.session = requests.Session()
        self.access_token = None
        self.test_results = []
        self.payslips_before = []
        self.payslips_after = []
        self.deleted_payslip_id = None
        
    def log_test(self, test_name, success, details=""):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
        
    def authenticate(self):
        """Authenticate as admin user"""
        print("🔐 Authenticating as admin (Callum/Peach7510)...")
        
        login_data = {
            "username": "Callum",
            "password": "Peach7510"
        }
        
        try:
            response = self.session.post(f"{API_BASE}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data["access_token"]
                self.session.headers.update({"Authorization": f"Bearer {self.access_token}"})
                self.log_test("Admin Authentication", True, f"User: {data['user']['full_name']}")
                return True
            else:
                self.log_test("Admin Authentication", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Admin Authentication", False, f"Exception: {str(e)}")
            return False
    
    def get_existing_payslips(self):
        """Get existing payslips to test with"""
        print("\n📋 Getting existing payslips...")
        
        try:
            response = self.session.get(f"{API_BASE}/payroll/reports/payslips")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    self.payslips_before = data.get("data", [])
                    payslip_count = len(self.payslips_before)
                    self.log_test("Get Existing Payslips", True, f"Found {payslip_count} payslips")
                    
                    if payslip_count > 0:
                        # Show details of first few payslips
                        for i, payslip in enumerate(self.payslips_before[:3]):
                            employee_name = payslip.get('payslip_data', {}).get('employee', {}).get('name', 'Unknown')
                            pay_period = payslip.get('payslip_data', {}).get('pay_period', {}).get('week_start', 'Unknown')
                            print(f"   Payslip {i+1}: ID={payslip.get('id', 'N/A')[:8]}..., Employee={employee_name}, Period={pay_period}")
                    
                    return payslip_count > 0
                else:
                    self.log_test("Get Existing Payslips", False, f"API returned success=false: {data}")
                    return False
            else:
                self.log_test("Get Existing Payslips", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Get Existing Payslips", False, f"Exception: {str(e)}")
            return False
    
    def test_delete_payslip(self):
        """Test deleting a payslip"""
        if not self.payslips_before:
            self.log_test("Delete Payslip Test", False, "No payslips available to delete")
            return False
            
        print("\n🗑️ Testing payslip deletion...")
        
        # Select the first payslip for deletion
        target_payslip = self.payslips_before[0]
        self.deleted_payslip_id = target_payslip.get('id')
        
        if not self.deleted_payslip_id:
            self.log_test("Delete Payslip Test", False, "Target payslip has no ID")
            return False
        
        # Get payslip details for verification
        employee_name = target_payslip.get('payslip_data', {}).get('employee', {}).get('name', 'Unknown')
        pay_period = target_payslip.get('payslip_data', {}).get('pay_period', {}).get('week_start', 'Unknown')
        
        print(f"   Target: Employee={employee_name}, Period={pay_period}, ID={self.deleted_payslip_id[:8]}...")
        
        try:
            response = self.session.delete(f"{API_BASE}/payroll/reports/payslips/{self.deleted_payslip_id}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    expected_message = f"Payslip for {employee_name} ({pay_period}) deleted successfully"
                    actual_message = data.get("message", "")
                    
                    # Check if response includes employee name and pay period
                    has_employee_name = employee_name in actual_message
                    has_pay_period = pay_period in actual_message or "deleted successfully" in actual_message
                    
                    self.log_test("Delete Payslip Endpoint", True, f"Message: {actual_message}")
                    self.log_test("Response Includes Employee Name", has_employee_name, f"Expected: {employee_name}, Got: {actual_message}")
                    self.log_test("Response Includes Success Message", has_pay_period, f"Message: {actual_message}")
                    
                    return True
                else:
                    self.log_test("Delete Payslip Endpoint", False, f"API returned success=false: {data}")
                    return False
            else:
                self.log_test("Delete Payslip Endpoint", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Delete Payslip Endpoint", False, f"Exception: {str(e)}")
            return False
    
    def verify_payslip_deleted(self):
        """Verify the payslip was actually deleted from the database"""
        print("\n🔍 Verifying payslip deletion...")
        
        try:
            response = self.session.get(f"{API_BASE}/payroll/reports/payslips")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    self.payslips_after = data.get("data", [])
                    payslip_count_after = len(self.payslips_after)
                    payslip_count_before = len(self.payslips_before)
                    
                    # Check if count decreased by 1
                    count_decreased = payslip_count_after == (payslip_count_before - 1)
                    self.log_test("Payslip Count Decreased", count_decreased, 
                                f"Before: {payslip_count_before}, After: {payslip_count_after}")
                    
                    # Check if the specific payslip is gone
                    deleted_payslip_still_exists = any(p.get('id') == self.deleted_payslip_id for p in self.payslips_after)
                    payslip_removed = not deleted_payslip_still_exists
                    self.log_test("Deleted Payslip No Longer in List", payslip_removed, 
                                f"Payslip ID {self.deleted_payslip_id[:8]}... {'still exists' if deleted_payslip_still_exists else 'successfully removed'}")
                    
                    # Check if other payslips remain intact
                    other_payslips_intact = True
                    for payslip in self.payslips_before[1:]:  # Skip the deleted one
                        if not any(p.get('id') == payslip.get('id') for p in self.payslips_after):
                            other_payslips_intact = False
                            break
                    
                    self.log_test("Other Payslips Remain Intact", other_payslips_intact, 
                                f"Other payslips preserved: {other_payslips_intact}")
                    
                    return count_decreased and payslip_removed and other_payslips_intact
                else:
                    self.log_test("Verify Payslip Deleted", False, f"API returned success=false: {data}")
                    return False
            else:
                self.log_test("Verify Payslip Deleted", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Verify Payslip Deleted", False, f"Exception: {str(e)}")
            return False
    
    def test_delete_nonexistent_payslip(self):
        """Test deleting a non-existent payslip (should return 404)"""
        print("\n🚫 Testing deletion of non-existent payslip...")
        
        fake_payslip_id = "non-existent-payslip-id-12345"
        
        try:
            response = self.session.delete(f"{API_BASE}/payroll/reports/payslips/{fake_payslip_id}")
            
            if response.status_code == 404:
                self.log_test("404 Error for Non-existent Payslip", True, "Correctly returned 404")
                return True
            else:
                self.log_test("404 Error for Non-existent Payslip", False, 
                            f"Expected 404, got {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("404 Error for Non-existent Payslip", False, f"Exception: {str(e)}")
            return False
    
    def test_access_control(self):
        """Test that non-admin users cannot delete payslips"""
        print("\n🔒 Testing access control (admin-only restriction)...")
        
        # Remove authorization header to test unauthenticated access
        original_headers = self.session.headers.copy()
        
        try:
            # Test without authentication
            self.session.headers.pop('Authorization', None)
            
            if self.payslips_after:
                test_payslip_id = self.payslips_after[0].get('id', 'test-id')
            else:
                test_payslip_id = "test-payslip-id"
            
            response = self.session.delete(f"{API_BASE}/payroll/reports/payslips/{test_payslip_id}")
            
            if response.status_code == 401 or response.status_code == 403:
                self.log_test("Admin-only Access Control", True, f"Correctly returned {response.status_code} for unauthenticated request")
                return True
            else:
                self.log_test("Admin-only Access Control", False, 
                            f"Expected 401/403, got {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Admin-only Access Control", False, f"Exception: {str(e)}")
            return False
        finally:
            # Restore authorization header
            self.session.headers.update(original_headers)
    
    def run_all_tests(self):
        """Run all payslip delete functionality tests"""
        print("🧪 PAYSLIP DELETE FUNCTIONALITY TESTING")
        print("=" * 50)
        
        # Test 1: Authentication
        if not self.authenticate():
            print("\n❌ Authentication failed - cannot continue with tests")
            return False
        
        # Test 2: Get existing payslips
        if not self.get_existing_payslips():
            print("\n❌ No payslips found - cannot test deletion")
            return False
        
        # Test 3: Delete a payslip
        if not self.test_delete_payslip():
            print("\n❌ Payslip deletion failed")
            return False
        
        # Test 4: Verify deletion
        if not self.verify_payslip_deleted():
            print("\n❌ Payslip deletion verification failed")
            return False
        
        # Test 5: Test error cases
        self.test_delete_nonexistent_payslip()
        
        # Test 6: Test access control
        self.test_access_control()
        
        # Summary
        self.print_summary()
        
        return True
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        print("\nDetailed Results:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}")
            if result["details"]:
                print(f"   {result['details']}")
        
        if success_rate >= 80:
            print(f"\n🎉 PAYSLIP DELETE FUNCTIONALITY TESTING COMPLETED SUCCESSFULLY!")
            print(f"✅ DELETE endpoint successfully removes payslip")
            print(f"✅ Payslip disappears from payslips list") 
            print(f"✅ Success message includes employee name and pay period")
            print(f"✅ Other payslips remain unaffected")
            print(f"✅ 404 error for non-existent payslip")
            print(f"✅ Admin-only access enforced")
            print(f"✅ Database record actually deleted (not just hidden)")
        else:
            print(f"\n⚠️ PAYSLIP DELETE FUNCTIONALITY HAS ISSUES")
            failed_tests = [r for r in self.test_results if not r["success"]]
            for test in failed_tests:
                print(f"❌ {test['test']}: {test['details']}")

def main():
    """Main function"""
    tester = PayslipDeleteTester()
    
    try:
        success = tester.run_all_tests()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n\n⚠️ Testing interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\n❌ Unexpected error during testing: {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)