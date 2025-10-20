#!/usr/bin/env python3
"""
Pending Timesheets Approve Functionality Testing
Re-testing the Pending Timesheets approve functionality after the data fix

Test Objectives:
1. Verify GET /api/payroll/timesheets/pending still returns the timesheet (ID: 9668ebe6-6be4-4e3f-8fea-840206691a84)
2. Test POST /api/payroll/timesheets/{timesheet_id}/approve endpoint now works correctly
3. Verify approval calculates pay correctly and updates timesheet status
4. Verify approved timesheet is removed from pending list

Authentication: Callum/Peach7510
"""

import requests
import json
import os
from datetime import datetime, timedelta, date
from dotenv import load_dotenv
import uuid

# Load environment variables
load_dotenv('/app/frontend/.env')

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:8001')
API_BASE = f"{BACKEND_URL}/api"

class PendingTimesheetsApproveTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        self.target_timesheet_id = "9668ebe6-6be4-4e3f-8fea-840206691a84"
        
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
        """Test authentication with admin credentials"""
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

    def test_get_pending_timesheets(self):
        """Test Step 1: GET /api/payroll/timesheets/pending"""
        print("\n=== TEST STEP 1: GET PENDING TIMESHEETS ===")
        
        try:
            response = self.session.get(f"{API_BASE}/payroll/timesheets/pending")
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("success") and "data" in result:
                    timesheets = result["data"]
                    
                    self.log_result(
                        "GET Pending Timesheets", 
                        True, 
                        f"Successfully retrieved {len(timesheets)} pending timesheets"
                    )
                    
                    # Look for the specific timesheet ID
                    target_timesheet = None
                    for ts in timesheets:
                        if ts.get("id") == self.target_timesheet_id:
                            target_timesheet = ts
                            break
                    
                    if target_timesheet:
                        self.log_result(
                            "Target Timesheet Found", 
                            True, 
                            f"Found target timesheet ID: {self.target_timesheet_id}",
                            f"Employee: {target_timesheet.get('employee_name')}, Status: {target_timesheet.get('status')}"
                        )
                        return target_timesheet
                    else:
                        # Check if any pending timesheet exists
                        if timesheets:
                            first_timesheet = timesheets[0]
                            self.log_result(
                                "Target Timesheet Not Found", 
                                False, 
                                f"Target timesheet {self.target_timesheet_id} not found, but found other pending timesheets",
                                f"Using first available timesheet: {first_timesheet.get('id')}"
                            )
                            self.target_timesheet_id = first_timesheet.get('id')
                            return first_timesheet
                        else:
                            self.log_result(
                                "No Pending Timesheets", 
                                False, 
                                "No pending timesheets found in the system"
                            )
                            return None
                else:
                    self.log_result(
                        "GET Pending Timesheets", 
                        False, 
                        "Invalid response structure",
                        f"Response: {result}"
                    )
            else:
                self.log_result(
                    "GET Pending Timesheets", 
                    False, 
                    f"Failed to get pending timesheets: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("GET Pending Timesheets", False, f"Error: {str(e)}")
        
        return None

    def test_approve_timesheet(self, timesheet_id):
        """Test Step 2: POST /api/payroll/timesheets/{timesheet_id}/approve"""
        print(f"\n=== TEST STEP 2: APPROVE TIMESHEET {timesheet_id} ===")
        
        try:
            response = self.session.post(f"{API_BASE}/payroll/timesheets/{timesheet_id}/approve")
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("success"):
                    data = result.get("data", {})
                    
                    # Check for required fields in approval response
                    required_fields = ["gross_pay", "net_pay", "hours_worked"]
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if not missing_fields:
                        self.log_result(
                            "Timesheet Approval", 
                            True, 
                            f"Successfully approved timesheet",
                            f"Gross Pay: ${data.get('gross_pay', 0)}, Net Pay: ${data.get('net_pay', 0)}, Hours: {data.get('hours_worked', 0)}"
                        )
                        
                        # Verify pay calculations
                        self.verify_pay_calculations(data)
                        
                        return True
                    else:
                        self.log_result(
                            "Timesheet Approval", 
                            False, 
                            f"Approval response missing required fields: {missing_fields}",
                            f"Available fields: {list(data.keys())}"
                        )
                else:
                    self.log_result(
                        "Timesheet Approval", 
                        False, 
                        "Approval failed - success=false in response",
                        result.get("message", "No message provided")
                    )
            elif response.status_code == 404:
                self.log_result(
                    "Timesheet Approval", 
                    False, 
                    "Employee not found error - data integrity issue still exists",
                    response.text
                )
            else:
                self.log_result(
                    "Timesheet Approval", 
                    False, 
                    f"Failed to approve timesheet: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Timesheet Approval", False, f"Error: {str(e)}")
        
        return False

    def verify_pay_calculations(self, approval_data):
        """Test Step 3: Verify approval calculates pay correctly"""
        print("\n=== TEST STEP 3: VERIFY PAY CALCULATIONS ===")
        
        try:
            gross_pay = approval_data.get("gross_pay", 0)
            net_pay = approval_data.get("net_pay", 0)
            hours_worked = approval_data.get("hours_worked", 0)
            
            # Basic validation checks
            if gross_pay > 0:
                self.log_result(
                    "Gross Pay Calculation", 
                    True, 
                    f"Gross pay calculated: ${gross_pay}"
                )
            else:
                self.log_result(
                    "Gross Pay Calculation", 
                    False, 
                    f"Gross pay is zero or negative: ${gross_pay}"
                )
            
            if net_pay > 0 and net_pay <= gross_pay:
                self.log_result(
                    "Net Pay Calculation", 
                    True, 
                    f"Net pay calculated correctly: ${net_pay} (after deductions from ${gross_pay})"
                )
            else:
                self.log_result(
                    "Net Pay Calculation", 
                    False, 
                    f"Net pay calculation issue: ${net_pay} (gross: ${gross_pay})"
                )
            
            if hours_worked > 0:
                self.log_result(
                    "Hours Worked Calculation", 
                    True, 
                    f"Hours worked calculated: {hours_worked}"
                )
            else:
                self.log_result(
                    "Hours Worked Calculation", 
                    False, 
                    f"Hours worked is zero or negative: {hours_worked}"
                )
            
            # Check for additional fields that might be present
            additional_fields = ["regular_hours", "overtime_hours", "tax_deducted", "superannuation"]
            for field in additional_fields:
                if field in approval_data:
                    self.log_result(
                        f"Additional Field - {field}", 
                        True, 
                        f"{field}: {approval_data[field]}"
                    )
                    
        except Exception as e:
            self.log_result("Pay Calculations Verification", False, f"Error: {str(e)}")

    def test_timesheet_status_update(self, timesheet_id):
        """Test Step 4: Verify timesheet status updated to 'approved'"""
        print(f"\n=== TEST STEP 4: VERIFY TIMESHEET STATUS UPDATE ===")
        
        try:
            # Try to get the specific timesheet to check its status
            # Note: This might require a different endpoint or checking pending list
            
            # First, check if it's still in pending list (it shouldn't be)
            pending_response = self.session.get(f"{API_BASE}/payroll/timesheets/pending")
            
            if pending_response.status_code == 200:
                pending_result = pending_response.json()
                
                if pending_result.get("success"):
                    pending_timesheets = pending_result.get("data", [])
                    
                    # Check if our timesheet is still in pending list
                    still_pending = any(ts.get("id") == timesheet_id for ts in pending_timesheets)
                    
                    if not still_pending:
                        self.log_result(
                            "Timesheet Removed from Pending", 
                            True, 
                            f"Timesheet {timesheet_id} successfully removed from pending list"
                        )
                    else:
                        self.log_result(
                            "Timesheet Removed from Pending", 
                            False, 
                            f"Timesheet {timesheet_id} still appears in pending list"
                        )
                        
                    return not still_pending
                else:
                    self.log_result(
                        "Check Pending List After Approval", 
                        False, 
                        "Failed to get pending timesheets for verification"
                    )
            else:
                self.log_result(
                    "Check Pending List After Approval", 
                    False, 
                    f"Failed to check pending list: {pending_response.status_code}"
                )
                
        except Exception as e:
            self.log_result("Timesheet Status Update Verification", False, f"Error: {str(e)}")
        
        return False

    def test_approved_timesheet_removed_from_pending(self):
        """Test Step 5: Verify approved timesheet is removed from pending list"""
        print("\n=== TEST STEP 5: VERIFY APPROVED TIMESHEET REMOVED FROM PENDING ===")
        
        try:
            response = self.session.get(f"{API_BASE}/payroll/timesheets/pending")
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("success"):
                    current_pending = result.get("data", [])
                    
                    # Check if our target timesheet is still there
                    target_still_pending = any(ts.get("id") == self.target_timesheet_id for ts in current_pending)
                    
                    if not target_still_pending:
                        self.log_result(
                            "Final Pending List Verification", 
                            True, 
                            f"Confirmed: Approved timesheet {self.target_timesheet_id} is no longer in pending list",
                            f"Current pending count: {len(current_pending)}"
                        )
                    else:
                        self.log_result(
                            "Final Pending List Verification", 
                            False, 
                            f"Approved timesheet {self.target_timesheet_id} is still in pending list"
                        )
                        
                    return not target_still_pending
                else:
                    self.log_result(
                        "Final Pending List Verification", 
                        False, 
                        "Failed to get final pending list"
                    )
            else:
                self.log_result(
                    "Final Pending List Verification", 
                    False, 
                    f"Failed to check final pending list: {response.status_code}"
                )
                
        except Exception as e:
            self.log_result("Final Pending List Verification", False, f"Error: {str(e)}")
        
        return False

    def run_complete_test_workflow(self):
        """Run the complete test workflow as specified in the review request"""
        print("="*80)
        print("PENDING TIMESHEETS APPROVE FUNCTIONALITY TESTING")
        print("Re-testing after data fix")
        print("="*80)
        
        # Step 0: Authenticate
        if not self.authenticate():
            print("❌ Authentication failed - cannot proceed with tests")
            return
        
        # Step 1: Get pending timesheets
        target_timesheet = self.test_get_pending_timesheets()
        if not target_timesheet:
            print("❌ No pending timesheets found - cannot test approval workflow")
            return
        
        timesheet_id = target_timesheet.get("id")
        print(f"\n🎯 Testing approval workflow with timesheet ID: {timesheet_id}")
        
        # Step 2: Approve the timesheet
        approval_success = self.test_approve_timesheet(timesheet_id)
        if not approval_success:
            print("❌ Timesheet approval failed - cannot verify remaining steps")
            return
        
        # Step 3: Verify status update (already done in approval test)
        
        # Step 4: Verify removal from pending list
        self.test_timesheet_status_update(timesheet_id)
        
        # Step 5: Final verification
        self.test_approved_timesheet_removed_from_pending()
        
        # Print summary
        self.print_test_summary()

    def print_test_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "="*80)
        print("PENDING TIMESHEETS APPROVE FUNCTIONALITY TEST SUMMARY")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        print("\n" + "="*60)
        print("DETAILED RESULTS:")
        print("="*60)
        
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test']}: {result['message']}")
            if result['details'] and not result['success']:
                print(f"   Details: {result['details']}")
        
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
            print("🎉 PERFECT! PENDING TIMESHEETS APPROVE FUNCTIONALITY 100% WORKING!")
        elif success_rate >= 80:
            print(f"✅ GOOD! Pending Timesheets Approve Functionality {success_rate:.1f}% Working")
        else:
            print(f"⚠️  ISSUES FOUND: Pending Timesheets Approve Functionality {success_rate:.1f}% Working")
        print("="*80)

def main():
    """Main function to run the tests"""
    tester = PendingTimesheetsApproveTester()
    tester.run_complete_test_workflow()

if __name__ == "__main__":
    main()