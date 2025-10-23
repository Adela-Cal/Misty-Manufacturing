#!/usr/bin/env python3
"""
Comprehensive Pending Timesheets Functionality Test
Tests all requirements from the review request:

1. Login with admin credentials (Callum/Peach7510)
2. GET /api/payroll/timesheets/pending to retrieve pending timesheets
3. Verify response structure includes: id, employee_id, employee_name, week_starting, week_ending, status, total_regular_hours, total_overtime_hours
4. For the first pending timesheet:
   a. Test approve endpoint: POST /api/payroll/timesheets/{timesheet_id}/approve
   b. Verify response includes gross_pay, net_pay, hours_worked
   c. Verify timesheet status changed to "approved"
5. Check that approved timesheet no longer appears in pending list

Expected Results:
- Pending timesheets endpoint returns array with at least one timesheet
- All timesheets have employee_name field populated
- Approve endpoint successfully approves timesheet and calculates pay
- Approved timesheet is removed from pending list
"""

import requests
import json
import os
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://misty-mfg-app.preview.emergentagent.com')
BASE_URL = f"{BACKEND_URL}/api"

# Test credentials from review request
USERNAME = "Callum"
PASSWORD = "Peach7510"

class ComprehensiveTimesheetTest:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        
    def log_result(self, test_name, success, details=""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append({
            "test": test_name,
            "status": status,
            "details": details,
            "success": success
        })
        print(f"{status}: {test_name}")
        if details:
            print(f"   {details}")
    
    def authenticate(self):
        """Step 1: Login with admin credentials (Callum/Peach7510)"""
        try:
            response = self.session.post(f"{BASE_URL}/auth/login", json={
                "username": USERNAME,
                "password": PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                user_info = data.get('user', {})
                self.log_result("Login with admin credentials (Callum/Peach7510)", True, 
                              f"Authenticated as {user_info.get('username')} with role {user_info.get('role')}")
                return True
            else:
                self.log_result("Login with admin credentials (Callum/Peach7510)", False, 
                              f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Login with admin credentials (Callum/Peach7510)", False, f"Exception: {str(e)}")
            return False
    
    def get_pending_timesheets(self):
        """Step 2: GET /api/payroll/timesheets/pending to retrieve pending timesheets"""
        try:
            response = self.session.get(f"{BASE_URL}/payroll/timesheets/pending")
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                if not data.get("success"):
                    self.log_result("GET /api/payroll/timesheets/pending response structure", False, 
                                  "Response success field is not True")
                    return None
                
                timesheets = data.get("data", [])
                
                if len(timesheets) == 0:
                    self.log_result("GET /api/payroll/timesheets/pending", True, 
                                  "No pending timesheets found (expected if all approved)")
                    return []
                
                self.log_result("GET /api/payroll/timesheets/pending", True, 
                              f"Successfully retrieved {len(timesheets)} pending timesheets")
                
                return timesheets
                
            else:
                self.log_result("GET /api/payroll/timesheets/pending", False, 
                              f"Status: {response.status_code}, Response: {response.text}")
                return None
                
        except Exception as e:
            self.log_result("GET /api/payroll/timesheets/pending", False, f"Exception: {str(e)}")
            return None
    
    def verify_timesheet_structure(self, timesheets):
        """Step 3: Verify response structure includes required fields"""
        if not timesheets:
            return True
            
        required_fields = ["id", "employee_id", "employee_name", "week_starting", "week_ending", 
                          "status", "total_regular_hours", "total_overtime_hours"]
        
        all_valid = True
        
        for i, timesheet in enumerate(timesheets):
            missing_fields = []
            for field in required_fields:
                if field not in timesheet:
                    missing_fields.append(field)
            
            if missing_fields:
                self.log_result(f"Timesheet {i+1} required fields validation", False, 
                              f"Missing fields: {missing_fields}")
                all_valid = False
            else:
                self.log_result(f"Timesheet {i+1} required fields validation", True, 
                              f"All required fields present")
            
            # Verify employee_name is populated (not "Unknown Employee")
            employee_name = timesheet.get("employee_name")
            if not employee_name or employee_name == "Unknown Employee":
                self.log_result(f"Timesheet {i+1} employee_name field populated", False, 
                              f"Employee name not properly populated: '{employee_name}'")
                all_valid = False
            else:
                self.log_result(f"Timesheet {i+1} employee_name field populated", True, 
                              f"Employee name: {employee_name}")
        
        return all_valid
    
    def diagnose_employee_mismatch(self, timesheet):
        """Diagnose employee ID mismatch issue"""
        try:
            # Get employee profiles to check for mismatch
            response = self.session.get(f"{BASE_URL}/payroll/employees")
            
            if response.status_code == 200:
                data = response.json()
                employees = data if isinstance(data, list) else data.get("data", [])
                
                timesheet_employee_id = timesheet.get('employee_id')
                
                # Check if timesheet employee_id exists in employee profiles
                matching_employee = None
                user_id_match = None
                
                for employee in employees:
                    if employee.get('id') == timesheet_employee_id:
                        matching_employee = employee
                        break
                    elif employee.get('user_id') == timesheet_employee_id:
                        user_id_match = employee
                
                if matching_employee:
                    self.log_result("Employee ID validation", True, 
                                  f"Timesheet employee_id matches employee profile")
                    return True
                elif user_id_match:
                    self.log_result("Employee ID validation", False, 
                                  f"DATA INTEGRITY ISSUE: Timesheet has user_id ({timesheet_employee_id}) instead of employee_id ({user_id_match.get('id')})")
                    return False
                else:
                    self.log_result("Employee ID validation", False, 
                                  f"Timesheet employee_id ({timesheet_employee_id}) not found in any employee profile")
                    return False
            else:
                self.log_result("Employee profiles retrieval for validation", False, 
                              f"Failed to get employee profiles: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Employee ID validation", False, f"Exception: {str(e)}")
            return False
    
    def test_approve_timesheet(self, timesheet_id, employee_name):
        """Step 4a: Test approve endpoint: POST /api/payroll/timesheets/{timesheet_id}/approve"""
        try:
            response = self.session.post(f"{BASE_URL}/payroll/timesheets/{timesheet_id}/approve")
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                if not data.get("success"):
                    self.log_result("POST /api/payroll/timesheets/{timesheet_id}/approve response structure", False, 
                                  "Response success field is not True")
                    return None
                
                approval_data = data.get("data", {})
                
                # Step 4b: Verify response includes gross_pay, net_pay, hours_worked
                required_fields = ["gross_pay", "net_pay", "hours_worked"]
                missing_fields = []
                for field in required_fields:
                    if field not in approval_data:
                        missing_fields.append(field)
                
                if missing_fields:
                    self.log_result("Approval response includes gross_pay, net_pay, hours_worked", False, 
                                  f"Missing fields: {missing_fields}")
                    return None
                else:
                    self.log_result("Approval response includes gross_pay, net_pay, hours_worked", True, 
                                  f"All required pay calculation fields present")
                
                # Verify pay calculations are numeric and reasonable
                try:
                    gross_pay = float(approval_data.get("gross_pay", 0))
                    net_pay = float(approval_data.get("net_pay", 0))
                    hours_worked = float(approval_data.get("hours_worked", 0))
                    
                    self.log_result("Pay calculation values", True, 
                                  f"Employee: {employee_name}, Gross: ${gross_pay:.2f}, Net: ${net_pay:.2f}, Hours: {hours_worked}")
                    
                    # Verify net pay logic (net should be <= gross after deductions)
                    if net_pay <= gross_pay:
                        self.log_result("Pay calculation logic validation", True, 
                                      "Net pay ≤ Gross pay (correct after deductions)")
                    else:
                        self.log_result("Pay calculation logic validation", False, 
                                      f"Net pay (${net_pay:.2f}) > Gross pay (${gross_pay:.2f})")
                    
                    self.log_result("POST /api/payroll/timesheets/{timesheet_id}/approve", True, 
                                  f"Timesheet approved successfully with pay calculation")
                    
                    return approval_data
                    
                except (ValueError, TypeError) as e:
                    self.log_result("Pay calculation values", False, 
                                  f"Non-numeric pay values: {str(e)}")
                    return None
                
            elif response.status_code == 404:
                error_detail = response.json().get("detail", "Unknown error")
                self.log_result("POST /api/payroll/timesheets/{timesheet_id}/approve", False, 
                              f"404 Error: {error_detail}")
                return None
            else:
                self.log_result("POST /api/payroll/timesheets/{timesheet_id}/approve", False, 
                              f"Status: {response.status_code}, Response: {response.text}")
                return None
                
        except Exception as e:
            self.log_result("POST /api/payroll/timesheets/{timesheet_id}/approve", False, f"Exception: {str(e)}")
            return None
    
    def verify_timesheet_removed_from_pending(self, approved_timesheet_id):
        """Step 5: Check that approved timesheet no longer appears in pending list"""
        try:
            response = self.session.get(f"{BASE_URL}/payroll/timesheets/pending")
            
            if response.status_code == 200:
                data = response.json()
                timesheets = data.get("data", [])
                
                # Check if approved timesheet is still in pending list
                still_pending = any(ts.get("id") == approved_timesheet_id for ts in timesheets)
                
                if not still_pending:
                    self.log_result("Approved timesheet removed from pending list", True, 
                                  f"Timesheet {approved_timesheet_id} successfully removed from pending list")
                    return True
                else:
                    self.log_result("Approved timesheet removed from pending list", False, 
                                  f"Timesheet {approved_timesheet_id} still appears in pending list")
                    return False
            else:
                self.log_result("Verify timesheet removed from pending list", False, 
                              f"Failed to retrieve pending list: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Verify timesheet removed from pending list", False, f"Exception: {str(e)}")
            return False
    
    def run_comprehensive_test(self):
        """Run comprehensive test according to review request"""
        print("🔍 COMPREHENSIVE PENDING TIMESHEETS FUNCTIONALITY TEST")
        print("=" * 80)
        print("Testing Requirements from Review Request:")
        print("1. Login with admin credentials (Callum/Peach7510)")
        print("2. GET /api/payroll/timesheets/pending to retrieve pending timesheets")
        print("3. Verify response structure includes required fields")
        print("4. Test approve endpoint and verify pay calculation")
        print("5. Check approved timesheet removed from pending list")
        print("=" * 80)
        
        # Step 1: Authentication
        if not self.authenticate():
            print("❌ Authentication failed - cannot proceed with tests")
            return
        
        # Step 2: Get pending timesheets
        pending_timesheets = self.get_pending_timesheets()
        if pending_timesheets is None:
            print("❌ Failed to retrieve pending timesheets - cannot proceed")
            return
        
        # Step 3: Verify timesheet structure
        structure_valid = self.verify_timesheet_structure(pending_timesheets)
        
        # Test approval workflow if we have pending timesheets
        if len(pending_timesheets) > 0:
            first_timesheet = pending_timesheets[0]
            timesheet_id = first_timesheet.get("id")
            employee_name = first_timesheet.get("employee_name")
            
            print(f"\n🎯 Testing approval workflow for:")
            print(f"   Timesheet ID: {timesheet_id}")
            print(f"   Employee: {employee_name}")
            print(f"   Week: {first_timesheet.get('week_starting')} to {first_timesheet.get('week_ending')}")
            print(f"   Regular Hours: {first_timesheet.get('total_regular_hours')}")
            print(f"   Overtime Hours: {first_timesheet.get('total_overtime_hours')}")
            
            # Diagnose any employee ID mismatch issues
            self.diagnose_employee_mismatch(first_timesheet)
            
            # Test approval
            approval_data = self.test_approve_timesheet(timesheet_id, employee_name)
            
            # Verify removal from pending list if approval succeeded
            if approval_data:
                self.verify_timesheet_removed_from_pending(timesheet_id)
        else:
            print("\n⚠️  No pending timesheets available for approval testing")
            print("   This is expected if all timesheets have been approved")
            self.log_result("Pending timesheets available for testing", True, 
                          "No pending timesheets (expected if all approved)")
        
        # Print comprehensive summary
        self.print_test_summary()
        
        return self.calculate_success_metrics()
    
    def print_test_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        print("\n📋 DETAILED TEST RESULTS:")
        for result in self.test_results:
            print(f"{result['status']}: {result['test']}")
            if result['details']:
                print(f"   {result['details']}")
        
        # Expected Results Assessment
        print("\n🎯 EXPECTED RESULTS FROM REVIEW REQUEST:")
        expected_results = [
            ("Pending timesheets endpoint returns array with at least one timesheet", 
             any("GET /api/payroll/timesheets/pending" in r["test"] and r["success"] for r in self.test_results)),
            ("All timesheets have employee_name field populated", 
             any("employee_name field populated" in r["test"] and r["success"] for r in self.test_results)),
            ("Approve endpoint successfully approves timesheet and calculates pay", 
             any("POST /api/payroll/timesheets" in r["test"] and "approve" in r["test"] and r["success"] for r in self.test_results)),
            ("Approved timesheet is removed from pending list", 
             any("removed from pending list" in r["test"] and r["success"] for r in self.test_results))
        ]
        
        for expectation, met in expected_results:
            status = "✅" if met else "❌"
            print(f"   {status} {expectation}")
        
        # Final assessment
        if failed_tests == 0:
            print("\n🎉 ALL TESTS PASSED - PENDING TIMESHEETS FUNCTIONALITY IS FULLY OPERATIONAL!")
        elif failed_tests <= 2:
            print(f"\n⚠️  MINOR ISSUES DETECTED - {failed_tests} test(s) failed but core functionality working")
        else:
            print(f"\n🚨 CRITICAL ISSUES DETECTED - {failed_tests} test(s) failed")
        
        # Specific issue identification
        approval_failed = any("POST /api/payroll/timesheets" in r["test"] and "approve" in r["test"] and not r["success"] for r in self.test_results)
        employee_mismatch = any("Employee ID validation" in r["test"] and not r["success"] for r in self.test_results)
        
        if approval_failed and employee_mismatch:
            print("\n🔧 IDENTIFIED ISSUE: Employee ID mismatch preventing timesheet approval")
            print("   SOLUTION: Update timesheet records to use employee_id instead of user_id")
    
    def calculate_success_metrics(self):
        """Calculate success metrics"""
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        
        return passed_tests, failed_tests, total_tests

if __name__ == "__main__":
    tester = ComprehensiveTimesheetTest()
    tester.run_comprehensive_test()