#!/usr/bin/env python3
"""
Timesheet Approval Endpoint Testing
Testing the timesheet approval endpoint to identify the error causing "failed to approve timesheet"

SPECIFIC TEST REQUIREMENTS:
1. Authenticate as Callum / Peach7510 (admin)
2. Get pending timesheets from GET /api/payroll/timesheets/pending
3. Try to approve one using POST /api/payroll/timesheets/{timesheet_id}/approve
4. Check backend logs for any errors during the approval process
5. Identify the specific error causing "failed to approve timesheet"
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

class TimesheetApprovalTester:
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
        """Test authentication with Callum / Peach7510 (admin)"""
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

    def get_pending_timesheets(self):
        """Get pending timesheets from GET /api/payroll/timesheets/pending"""
        print("\n=== GETTING PENDING TIMESHEETS ===")
        
        try:
            response = self.session.get(f"{API_BASE}/payroll/timesheets/pending")
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("success") and "data" in result:
                    timesheets = result["data"]
                    
                    self.log_result(
                        "Get Pending Timesheets", 
                        True, 
                        f"Successfully retrieved {len(timesheets)} pending timesheets"
                    )
                    
                    # Log details of each timesheet
                    for i, timesheet in enumerate(timesheets):
                        print(f"   Timesheet {i+1}: ID={timesheet.get('id')}, Employee={timesheet.get('employee_name')}, Status={timesheet.get('status')}")
                    
                    return timesheets
                else:
                    self.log_result(
                        "Get Pending Timesheets", 
                        False, 
                        "Invalid response structure",
                        f"Response: {result}"
                    )
            else:
                self.log_result(
                    "Get Pending Timesheets", 
                    False, 
                    f"Failed to get pending timesheets: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Get Pending Timesheets", False, f"Error: {str(e)}")
        
        return []

    def test_timesheet_approval(self, timesheet_id):
        """Try to approve a timesheet using POST /api/payroll/timesheets/{timesheet_id}/approve"""
        print(f"\n=== TESTING TIMESHEET APPROVAL FOR ID: {timesheet_id} ===")
        
        try:
            # First, let's check if the endpoint exists and what it expects
            response = self.session.post(f"{API_BASE}/payroll/timesheets/{timesheet_id}/approve")
            
            print(f"Response Status Code: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            print(f"Response Text: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                self.log_result(
                    "Timesheet Approval", 
                    True, 
                    f"Successfully approved timesheet {timesheet_id}",
                    f"Response: {result}"
                )
                return True
            elif response.status_code == 404:
                self.log_result(
                    "Timesheet Approval", 
                    False, 
                    f"Timesheet approval endpoint not found (404)",
                    f"URL: {API_BASE}/payroll/timesheets/{timesheet_id}/approve"
                )
            elif response.status_code == 400:
                self.log_result(
                    "Timesheet Approval", 
                    False, 
                    f"Bad request (400) - possible validation error",
                    response.text
                )
            elif response.status_code == 422:
                self.log_result(
                    "Timesheet Approval", 
                    False, 
                    f"Unprocessable entity (422) - validation error",
                    response.text
                )
            elif response.status_code == 500:
                self.log_result(
                    "Timesheet Approval", 
                    False, 
                    f"Internal server error (500) - backend error",
                    response.text
                )
            else:
                self.log_result(
                    "Timesheet Approval", 
                    False, 
                    f"Unexpected status code: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Timesheet Approval", False, f"Error: {str(e)}")
        
        return False

    def check_backend_logs(self):
        """Check backend logs for any errors during the approval process"""
        print("\n=== CHECKING BACKEND LOGS ===")
        
        try:
            # Check supervisor backend logs
            import subprocess
            
            # Get recent backend logs
            result = subprocess.run(
                ["tail", "-n", "100", "/var/log/supervisor/backend.err.log"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                error_logs = result.stdout
                if error_logs.strip():
                    self.log_result(
                        "Backend Error Logs", 
                        True, 
                        f"Found backend error logs",
                        f"Recent errors:\n{error_logs}"
                    )
                else:
                    self.log_result(
                        "Backend Error Logs", 
                        True, 
                        "No recent errors in backend logs"
                    )
            else:
                self.log_result(
                    "Backend Error Logs", 
                    False, 
                    "Could not read backend error logs"
                )
            
            # Also check stdout logs
            result = subprocess.run(
                ["tail", "-n", "100", "/var/log/supervisor/backend.out.log"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                stdout_logs = result.stdout
                if stdout_logs.strip():
                    self.log_result(
                        "Backend Output Logs", 
                        True, 
                        f"Found backend output logs",
                        f"Recent output:\n{stdout_logs}"
                    )
                else:
                    self.log_result(
                        "Backend Output Logs", 
                        True, 
                        "No recent output in backend logs"
                    )
                    
        except Exception as e:
            self.log_result("Check Backend Logs", False, f"Error: {str(e)}")

    def check_payroll_endpoints_file(self):
        """Check if payroll_endpoints.py has the approval endpoint"""
        print("\n=== CHECKING PAYROLL ENDPOINTS FILE ===")
        
        try:
            # Check if the approval endpoint exists in payroll_endpoints.py
            with open('/app/backend/payroll_endpoints.py', 'r') as f:
                content = f.read()
                
            if '/approve' in content:
                self.log_result(
                    "Approval Endpoint Exists", 
                    True, 
                    "Found approval endpoint in payroll_endpoints.py"
                )
                
                # Look for the specific endpoint definition
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if 'approve' in line and ('post' in line.lower() or 'put' in line.lower()):
                        print(f"   Found at line {i+1}: {line.strip()}")
                        
                        # Show surrounding context
                        start = max(0, i-5)
                        end = min(len(lines), i+10)
                        context = '\n'.join(lines[start:end])
                        
                        self.log_result(
                            "Approval Endpoint Context", 
                            True, 
                            f"Found approval endpoint definition",
                            f"Context:\n{context}"
                        )
                        break
            else:
                self.log_result(
                    "Approval Endpoint Exists", 
                    False, 
                    "No approval endpoint found in payroll_endpoints.py"
                )
                
        except Exception as e:
            self.log_result("Check Payroll Endpoints File", False, f"Error: {str(e)}")

    def test_alternative_approval_methods(self, timesheet_id):
        """Test alternative approval methods in case the endpoint is different"""
        print(f"\n=== TESTING ALTERNATIVE APPROVAL METHODS FOR ID: {timesheet_id} ===")
        
        # Method 1: PUT request instead of POST
        try:
            response = self.session.put(f"{API_BASE}/payroll/timesheets/{timesheet_id}/approve")
            print(f"PUT /approve - Status: {response.status_code}, Response: {response.text}")
            
            if response.status_code == 200:
                self.log_result(
                    "Alternative Approval (PUT)", 
                    True, 
                    f"Successfully approved timesheet using PUT method"
                )
                return True
        except Exception as e:
            print(f"PUT /approve error: {str(e)}")
        
        # Method 2: PATCH request with status update
        try:
            response = self.session.patch(
                f"{API_BASE}/payroll/timesheets/{timesheet_id}", 
                json={"status": "approved"}
            )
            print(f"PATCH with status - Status: {response.status_code}, Response: {response.text}")
            
            if response.status_code == 200:
                self.log_result(
                    "Alternative Approval (PATCH)", 
                    True, 
                    f"Successfully approved timesheet using PATCH method"
                )
                return True
        except Exception as e:
            print(f"PATCH with status error: {str(e)}")
        
        # Method 3: PUT request with status update
        try:
            response = self.session.put(
                f"{API_BASE}/payroll/timesheets/{timesheet_id}", 
                json={"status": "approved"}
            )
            print(f"PUT with status - Status: {response.status_code}, Response: {response.text}")
            
            if response.status_code == 200:
                self.log_result(
                    "Alternative Approval (PUT with status)", 
                    True, 
                    f"Successfully approved timesheet using PUT with status"
                )
                return True
        except Exception as e:
            print(f"PUT with status error: {str(e)}")
        
        # Method 4: Check if there's a general approval endpoint
        try:
            response = self.session.post(
                f"{API_BASE}/payroll/approve-timesheet", 
                json={"timesheet_id": timesheet_id}
            )
            print(f"POST /approve-timesheet - Status: {response.status_code}, Response: {response.text}")
            
            if response.status_code == 200:
                self.log_result(
                    "Alternative Approval (General endpoint)", 
                    True, 
                    f"Successfully approved timesheet using general approval endpoint"
                )
                return True
        except Exception as e:
            print(f"POST /approve-timesheet error: {str(e)}")
        
        self.log_result(
            "Alternative Approval Methods", 
            False, 
            "None of the alternative approval methods worked"
        )
        return False

    def run_comprehensive_test(self):
        """Run comprehensive timesheet approval test"""
        print("="*80)
        print("TIMESHEET APPROVAL ENDPOINT TESTING")
        print("="*80)
        
        # Step 1: Authenticate
        if not self.authenticate():
            print("❌ Authentication failed - cannot proceed with tests")
            return
        
        # Step 2: Check if approval endpoint exists in code
        self.check_payroll_endpoints_file()
        
        # Step 3: Get pending timesheets
        pending_timesheets = self.get_pending_timesheets()
        
        if not pending_timesheets:
            print("❌ No pending timesheets found - cannot test approval")
            return
        
        # Step 4: Try to approve the first pending timesheet
        timesheet_to_approve = pending_timesheets[0]
        timesheet_id = timesheet_to_approve.get('id')
        
        print(f"\n🎯 Attempting to approve timesheet: {timesheet_id}")
        print(f"   Employee: {timesheet_to_approve.get('employee_name')}")
        print(f"   Status: {timesheet_to_approve.get('status')}")
        print(f"   Week: {timesheet_to_approve.get('week_start')} to {timesheet_to_approve.get('week_end')}")
        
        # Step 5: Test approval endpoint
        approval_success = self.test_timesheet_approval(timesheet_id)
        
        # Step 6: If primary method fails, try alternatives
        if not approval_success:
            print("\n🔄 Primary approval method failed, trying alternatives...")
            approval_success = self.test_alternative_approval_methods(timesheet_id)
        
        # Step 7: Check backend logs for errors
        self.check_backend_logs()
        
        # Step 8: Print summary
        self.print_test_summary()

    def print_test_summary(self):
        """Print test summary"""
        print("\n" + "="*80)
        print("TIMESHEET APPROVAL TEST SUMMARY")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
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
        
        # Show successful tests
        success_results = [r for r in self.test_results if r['success']]
        if success_results:
            print("\n" + "="*60)
            print("SUCCESSFUL TESTS:")
            print("="*60)
            for result in success_results:
                print(f"✅ {result['test']}: {result['message']}")

if __name__ == "__main__":
    tester = TimesheetApprovalTester()
    tester.run_comprehensive_test()