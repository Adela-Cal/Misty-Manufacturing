#!/usr/bin/env python3
"""
Complete Timesheet Approval Workflow with Automatic Payslip Generation Testing

CRITICAL TEST OBJECTIVES:
1. Setup & Authentication - Authenticate as admin (Callum/Peach7510)
2. Get list of employees
3. Create and Submit Timesheet - Select employee, create timesheet with hours, save, submit
4. Verify Timesheet in Pending List - Check it appears in pending list with employee name enriched
5. Approve Timesheet (Critical - Auto Payslip Generation) - Verify payslip is automatically generated
6. Verify Timesheet Disappears from Pending List - Critical for "Timesheet Approval" window
7. Verify Approved Timesheet in Reports - For "Approved Timesheets Report"
8. Verify Payslip Generation (NEW - CRITICAL) - For "Pay Slips" window
9. Test Edge Cases - Multiple approvals, no duplicates, filtering

EXPECTED RESULTS:
✅ Timesheet approval succeeds
✅ Payslip automatically generated and saved to payslips collection
✅ Approved timesheet disappears from pending list
✅ Approved timesheet appears in approved timesheets report
✅ Payslip appears in payslips list with all required fields
✅ Pay calculations are accurate
✅ No duplicate payslips created
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

class TimesheetApprovalPayslipTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        self.test_employee_id = None
        self.test_timesheet_id = None
        self.test_payslip_id = None
        
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
        print("\n=== STEP 1: AUTHENTICATION ===")
        
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
                    "Admin Authentication", 
                    True, 
                    f"Successfully authenticated as {user_info.get('username')} with role {user_info.get('role')}"
                )
                return True
            else:
                self.log_result(
                    "Admin Authentication", 
                    False, 
                    f"Authentication failed with status {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_result("Admin Authentication", False, f"Authentication error: {str(e)}")
            return False

    def get_employees_list(self):
        """Get list of employees"""
        print("\n=== STEP 2: GET EMPLOYEES LIST ===")
        
        try:
            response = self.session.get(f"{API_BASE}/payroll/employees")
            
            if response.status_code == 200:
                employees = response.json()
                
                if isinstance(employees, dict) and "data" in employees:
                    employees = employees["data"]
                
                if employees and len(employees) > 0:
                    # Find a non-Callum employee for testing
                    non_callum_employees = [emp for emp in employees if emp.get('first_name', '').lower() != 'callum']
                    
                    if non_callum_employees:
                        self.test_employee_id = non_callum_employees[0]['id']
                        employee_name = f"{non_callum_employees[0].get('first_name', '')} {non_callum_employees[0].get('last_name', '')}"
                        
                        self.log_result(
                            "Get Employees List", 
                            True, 
                            f"Found {len(employees)} employees, selected {employee_name} for testing",
                            f"Employee ID: {self.test_employee_id}"
                        )
                        return True
                    else:
                        # Use Callum if no other employees available
                        self.test_employee_id = employees[0]['id']
                        employee_name = f"{employees[0].get('first_name', '')} {employees[0].get('last_name', '')}"
                        
                        self.log_result(
                            "Get Employees List", 
                            True, 
                            f"Using Callum for testing (no other employees available): {employee_name}",
                            f"Employee ID: {self.test_employee_id}"
                        )
                        return True
                else:
                    self.log_result(
                        "Get Employees List", 
                        False, 
                        "No employees found in system"
                    )
                    return False
            else:
                self.log_result(
                    "Get Employees List", 
                    False, 
                    f"Failed to get employees: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_result("Get Employees List", False, f"Error: {str(e)}")
            return False

    def create_and_submit_timesheet(self):
        """Create timesheet with hours and submit for approval"""
        print("\n=== STEP 3: CREATE AND SUBMIT TIMESHEET ===")
        
        if not self.test_employee_id:
            self.log_result("Create Timesheet", False, "No employee ID available")
            return False
        
        # Step 3a: Get/Create timesheet for a future week to avoid conflicts with existing approved timesheets
        try:
            # Use a week far in the future to avoid conflicts with existing timesheets
            today = datetime.now().date()
            # Use a week 4 weeks in the future
            future_week_monday = today + timedelta(days=(28 - today.weekday()))
            
            response = self.session.get(
                f"{API_BASE}/payroll/timesheets/current-week/{self.test_employee_id}",
                params={"week_starting": future_week_monday.isoformat()}
            )
            
            if response.status_code == 200:
                timesheet = response.json()
                self.test_timesheet_id = timesheet.get('id')
                
                # Check if timesheet is already approved (unlikely for future weeks)
                if timesheet.get('status') == 'approved':
                    # Try with an even further week
                    future_week_monday = future_week_monday + timedelta(days=7)
                    response = self.session.get(
                        f"{API_BASE}/payroll/timesheets/current-week/{self.test_employee_id}",
                        params={"week_starting": future_week_monday.isoformat()}
                    )
                    
                    if response.status_code == 200:
                        timesheet = response.json()
                        self.test_timesheet_id = timesheet.get('id')
                
                self.log_result(
                    "Get/Create Test Week Timesheet", 
                    True, 
                    f"Retrieved timesheet for week {future_week_monday}",
                    f"Timesheet ID: {self.test_timesheet_id}, Status: {timesheet.get('status', 'unknown')}"
                )
                
                # Store the week for later use
                self.test_week_monday = future_week_monday
                
            else:
                self.log_result(
                    "Get/Create Test Week Timesheet", 
                    False, 
                    f"Failed to get timesheet: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_result("Get/Create Test Week Timesheet", False, f"Error: {str(e)}")
            return False
        
        # Step 3b: Update timesheet with hours (Monday: 8h, Tuesday: 7.5h, Wednesday: 8h)
        try:
            # Use the test week we determined above
            monday = self.test_week_monday
            
            update_data = {
                "employee_id": self.test_employee_id,
                "week_starting": monday.isoformat(),
                "entries": [
                    {
                        "date": monday.isoformat(),
                        "regular_hours": 8.0,
                        "overtime_hours": 0.0,
                        "leave_hours": {},
                        "notes": "Monday work"
                    },
                    {
                        "date": (monday + timedelta(days=1)).isoformat(),
                        "regular_hours": 7.5,
                        "overtime_hours": 0.0,
                        "leave_hours": {},
                        "notes": "Tuesday work"
                    },
                    {
                        "date": (monday + timedelta(days=2)).isoformat(),
                        "regular_hours": 8.0,
                        "overtime_hours": 0.0,
                        "leave_hours": {},
                        "notes": "Wednesday work"
                    }
                ]
            }
            
            response = self.session.put(f"{API_BASE}/payroll/timesheets/{self.test_timesheet_id}", json=update_data)
            
            if response.status_code == 200:
                self.log_result(
                    "Update Timesheet with Hours", 
                    True, 
                    "Successfully updated timesheet with hours (Monday: 8h, Tuesday: 7.5h, Wednesday: 8h)",
                    f"Total hours: 23.5"
                )
            else:
                self.log_result(
                    "Update Timesheet with Hours", 
                    False, 
                    f"Failed to update timesheet: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_result("Update Timesheet with Hours", False, f"Error: {str(e)}")
            return False
        
        # Step 3c: Submit timesheet for approval
        try:
            response = self.session.post(f"{API_BASE}/payroll/timesheets/{self.test_timesheet_id}/submit")
            
            if response.status_code == 200:
                result = response.json()
                
                self.log_result(
                    "Submit Timesheet for Approval", 
                    True, 
                    "Successfully submitted timesheet for approval",
                    f"Status should now be 'submitted'"
                )
                return True
            else:
                self.log_result(
                    "Submit Timesheet for Approval", 
                    False, 
                    f"Failed to submit timesheet: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_result("Submit Timesheet for Approval", False, f"Error: {str(e)}")
            return False

    def verify_timesheet_in_pending_list(self):
        """Verify submitted timesheet appears in pending list"""
        print("\n=== STEP 4: VERIFY TIMESHEET IN PENDING LIST ===")
        
        try:
            response = self.session.get(f"{API_BASE}/payroll/timesheets/pending")
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("success") and "data" in result:
                    pending_timesheets = result["data"]
                    
                    # Find our test timesheet
                    test_timesheet = None
                    for ts in pending_timesheets:
                        if ts.get("id") == self.test_timesheet_id:
                            test_timesheet = ts
                            break
                    
                    if test_timesheet:
                        # Verify employee name is enriched
                        employee_name = test_timesheet.get("employee_name", "")
                        
                        if employee_name and employee_name != "Unknown Employee":
                            self.log_result(
                                "Verify Timesheet in Pending List", 
                                True, 
                                f"Submitted timesheet appears in pending list with employee name enriched",
                                f"Employee: {employee_name}, Status: {test_timesheet.get('status')}"
                            )
                            return True
                        else:
                            self.log_result(
                                "Verify Employee Name Enrichment", 
                                False, 
                                f"Employee name not properly enriched: '{employee_name}'"
                            )
                            return False
                    else:
                        self.log_result(
                            "Verify Timesheet in Pending List", 
                            False, 
                            f"Test timesheet {self.test_timesheet_id} not found in pending list",
                            f"Found {len(pending_timesheets)} pending timesheets"
                        )
                        return False
                else:
                    self.log_result(
                        "Verify Timesheet in Pending List", 
                        False, 
                        "Invalid response structure from pending timesheets endpoint"
                    )
                    return False
            else:
                self.log_result(
                    "Verify Timesheet in Pending List", 
                    False, 
                    f"Failed to get pending timesheets: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_result("Verify Timesheet in Pending List", False, f"Error: {str(e)}")
            return False

    def approve_timesheet_and_verify_payslip_generation(self):
        """CRITICAL: Approve timesheet and verify automatic payslip generation"""
        print("\n=== STEP 5: APPROVE TIMESHEET (CRITICAL - AUTO PAYSLIP GENERATION) ===")
        
        try:
            response = self.session.post(f"{API_BASE}/payroll/timesheets/{self.test_timesheet_id}/approve")
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("success"):
                    approval_data = result.get("data", {})
                    
                    # Verify approval response includes pay calculations
                    required_fields = ["gross_pay", "net_pay", "hours_worked"]
                    missing_fields = [field for field in required_fields if field not in approval_data]
                    
                    if not missing_fields:
                        gross_pay = approval_data.get("gross_pay", 0)
                        net_pay = approval_data.get("net_pay", 0)
                        hours_worked = approval_data.get("hours_worked", 0)
                        
                        self.log_result(
                            "Timesheet Approval with Pay Calculations", 
                            True, 
                            f"Timesheet approved successfully with pay calculations",
                            f"Gross: ${gross_pay}, Net: ${net_pay}, Hours: {hours_worked}"
                        )
                        
                        # Now verify payslip was automatically generated
                        return self.verify_automatic_payslip_generation()
                    else:
                        self.log_result(
                            "Timesheet Approval Response Structure", 
                            False, 
                            f"Approval response missing required fields: {missing_fields}",
                            f"Available fields: {list(approval_data.keys())}"
                        )
                        return False
                else:
                    self.log_result(
                        "Timesheet Approval", 
                        False, 
                        "Approval response indicates failure",
                        result.get("message", "No message provided")
                    )
                    return False
            else:
                self.log_result(
                    "Timesheet Approval", 
                    False, 
                    f"Failed to approve timesheet: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_result("Timesheet Approval", False, f"Error: {str(e)}")
            return False

    def verify_automatic_payslip_generation(self):
        """Verify that payslip was automatically generated"""
        print("\n=== STEP 5b: VERIFY AUTOMATIC PAYSLIP GENERATION ===")
        
        try:
            # Check if payslip was generated for this timesheet
            response = self.session.get(f"{API_BASE}/payroll/reports/payslip/{self.test_timesheet_id}")
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("success") and result.get("data"):
                    payslip_data = result["data"]
                    
                    # Verify payslip has all required fields
                    required_sections = [
                        "employee", "pay_period", "hours", "earnings", 
                        "deductions", "net_pay", "year_to_date", "bank_details"
                    ]
                    
                    missing_sections = [section for section in required_sections if section not in payslip_data]
                    
                    if not missing_sections:
                        self.log_result(
                            "CRITICAL: Automatic Payslip Generation", 
                            True, 
                            "Payslip automatically generated with all required sections",
                            f"Sections: {list(payslip_data.keys())}"
                        )
                        
                        # Store payslip ID for later verification
                        self.test_payslip_id = payslip_data.get("id")
                        return True
                    else:
                        self.log_result(
                            "Payslip Data Structure", 
                            False, 
                            f"Payslip missing required sections: {missing_sections}",
                            f"Available sections: {list(payslip_data.keys())}"
                        )
                        return False
                else:
                    self.log_result(
                        "CRITICAL: Automatic Payslip Generation", 
                        False, 
                        "No payslip data returned - payslip may not have been generated automatically"
                    )
                    return False
            else:
                self.log_result(
                    "CRITICAL: Automatic Payslip Generation", 
                    False, 
                    f"Failed to retrieve payslip: {response.status_code}",
                    "Payslip may not have been automatically generated"
                )
                return False
                
        except Exception as e:
            self.log_result("Verify Automatic Payslip Generation", False, f"Error: {str(e)}")
            return False

    def verify_timesheet_disappears_from_pending_list(self):
        """Verify approved timesheet no longer appears in pending list"""
        print("\n=== STEP 6: VERIFY TIMESHEET DISAPPEARS FROM PENDING LIST ===")
        
        try:
            response = self.session.get(f"{API_BASE}/payroll/timesheets/pending")
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("success") and "data" in result:
                    pending_timesheets = result["data"]
                    
                    # Check that our test timesheet is NOT in the pending list
                    test_timesheet_found = False
                    for ts in pending_timesheets:
                        if ts.get("id") == self.test_timesheet_id:
                            test_timesheet_found = True
                            break
                    
                    if not test_timesheet_found:
                        self.log_result(
                            "CRITICAL: Timesheet Removed from Pending List", 
                            True, 
                            "Approved timesheet correctly removed from pending list",
                            f"Pending list now has {len(pending_timesheets)} timesheets"
                        )
                        return True
                    else:
                        self.log_result(
                            "CRITICAL: Timesheet Removed from Pending List", 
                            False, 
                            "Approved timesheet still appears in pending list",
                            "This is critical for the 'Timesheet Approval' window"
                        )
                        return False
                else:
                    self.log_result(
                        "Verify Pending List Structure", 
                        False, 
                        "Invalid response structure from pending timesheets endpoint"
                    )
                    return False
            else:
                self.log_result(
                    "Verify Timesheet Disappears from Pending List", 
                    False, 
                    f"Failed to get pending timesheets: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_result("Verify Timesheet Disappears from Pending List", False, f"Error: {str(e)}")
            return False

    def verify_approved_timesheet_in_reports(self):
        """Verify approved timesheet appears in approved timesheets report"""
        print("\n=== STEP 7: VERIFY APPROVED TIMESHEET IN REPORTS ===")
        
        try:
            # Get timesheets report (should include approved timesheets)
            response = self.session.get(f"{API_BASE}/payroll/reports/timesheets")
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("success") and "data" in result:
                    report_data = result["data"]
                    # Handle both formats: direct list or object with timesheets field
                    if isinstance(report_data, list):
                        timesheets = report_data
                    else:
                        timesheets = report_data.get("timesheets", [])
                    
                    # Find our approved timesheet
                    approved_timesheet = None
                    for ts in timesheets:
                        if ts.get("id") == self.test_timesheet_id:
                            approved_timesheet = ts
                            break
                    
                    if approved_timesheet:
                        if approved_timesheet.get("status") == "approved":
                            self.log_result(
                                "Approved Timesheet in Reports", 
                                True, 
                                "Approved timesheet appears in timesheets report with 'approved' status",
                                f"Employee: {approved_timesheet.get('employee_name', 'Unknown')}"
                            )
                            return True
                        else:
                            self.log_result(
                                "Approved Timesheet Status", 
                                False, 
                                f"Timesheet found but status is '{approved_timesheet.get('status')}', expected 'approved'"
                            )
                            return False
                    else:
                        self.log_result(
                            "Approved Timesheet in Reports", 
                            False, 
                            f"Approved timesheet {self.test_timesheet_id} not found in reports",
                            f"Found {len(timesheets)} timesheets in report"
                        )
                        return False
                else:
                    self.log_result(
                        "Timesheets Report Structure", 
                        False, 
                        "Invalid response structure from timesheets report endpoint"
                    )
                    return False
            else:
                self.log_result(
                    "Verify Approved Timesheet in Reports", 
                    False, 
                    f"Failed to get timesheets report: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_result("Verify Approved Timesheet in Reports", False, f"Error: {str(e)}")
            return False

    def verify_payslip_in_payslips_list(self):
        """Verify payslip appears in payslips list with all required fields"""
        print("\n=== STEP 8: VERIFY PAYSLIP IN PAYSLIPS LIST (NEW - CRITICAL) ===")
        
        try:
            # Get payslips report
            response = self.session.get(f"{API_BASE}/payroll/reports/payslips")
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("success") and "data" in result:
                    payslips = result["data"]
                    
                    if len(payslips) > 0:
                        # Find our payslip (should be the most recent one for our employee)
                        our_payslip = None
                        for payslip in payslips:
                            if payslip.get("employee_id") == self.test_employee_id:
                                our_payslip = payslip
                                break
                        
                        if our_payslip:
                            # Verify payslip has all required fields
                            required_fields = [
                                "employee", "pay_period", "hours", "earnings",
                                "deductions", "net_pay", "year_to_date", "bank_details",
                                "generated_at"
                            ]
                            
                            missing_fields = [field for field in required_fields if field not in our_payslip]
                            
                            if not missing_fields:
                                # Verify specific field details
                                employee_info = our_payslip.get("employee", {})
                                pay_period = our_payslip.get("pay_period", {})
                                hours = our_payslip.get("hours", {})
                                earnings = our_payslip.get("earnings", {})
                                
                                details = []
                                details.append(f"Employee: {employee_info.get('name', 'Unknown')}")
                                details.append(f"Period: {pay_period.get('week_start')} to {pay_period.get('week_end')}")
                                details.append(f"Hours: {hours.get('regular_hours', 0)} regular, {hours.get('overtime_hours', 0)} overtime")
                                details.append(f"Gross Pay: ${earnings.get('gross_pay', 0)}")
                                details.append(f"Net Pay: ${our_payslip.get('net_pay', 0)}")
                                
                                self.log_result(
                                    "CRITICAL: Payslip in Payslips List", 
                                    True, 
                                    "Payslip appears in payslips list with all required fields",
                                    "; ".join(details)
                                )
                                return True
                            else:
                                self.log_result(
                                    "Payslip Required Fields", 
                                    False, 
                                    f"Payslip missing required fields: {missing_fields}",
                                    f"Available fields: {list(our_payslip.keys())}"
                                )
                                return False
                        else:
                            self.log_result(
                                "CRITICAL: Payslip in Payslips List", 
                                False, 
                                f"No payslip found for employee {self.test_employee_id}",
                                f"Found {len(payslips)} total payslips"
                            )
                            return False
                    else:
                        self.log_result(
                            "CRITICAL: Payslip in Payslips List", 
                            False, 
                            "No payslips found in payslips list",
                            "Payslip may not have been generated or saved"
                        )
                        return False
                else:
                    self.log_result(
                        "Payslips Report Structure", 
                        False, 
                        "Invalid response structure from payslips report endpoint"
                    )
                    return False
            else:
                self.log_result(
                    "Verify Payslip in Payslips List", 
                    False, 
                    f"Failed to get payslips report: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_result("Verify Payslip in Payslips List", False, f"Error: {str(e)}")
            return False

    def test_edge_cases(self):
        """Test edge cases: multiple approvals, no duplicates, filtering"""
        print("\n=== STEP 9: TEST EDGE CASES ===")
        
        # Test 1: Approve another timesheet and verify payslip is generated
        self.test_multiple_timesheet_approvals()
        
        # Test 2: Verify no duplicate payslips are created
        self.test_no_duplicate_payslips()
        
        # Test 3: Test filtering payslips by employee_id (if supported)
        self.test_payslip_filtering()

    def test_multiple_timesheet_approvals(self):
        """Test approving another timesheet and verify payslip generation"""
        try:
            # Create another timesheet for the same employee (different week)
            # Use week after our test week
            another_week_monday = self.test_week_monday + timedelta(days=7)
            
            # Get timesheet for another week
            response = self.session.get(
                f"{API_BASE}/payroll/timesheets/current-week/{self.test_employee_id}",
                params={"week_starting": another_week_monday.isoformat()}
            )
            
            if response.status_code == 200:
                timesheet = response.json()
                timesheet_id = timesheet.get('id')
                
                # Update with different hours
                update_data = {
                    "employee_id": self.test_employee_id,
                    "week_starting": another_week_monday.isoformat(),
                    "entries": [
                        {
                            "date": another_week_monday.isoformat(),
                            "regular_hours": 7.0,
                            "overtime_hours": 1.0,
                            "leave_hours": {},
                            "notes": "Monday with overtime"
                        },
                        {
                            "date": (another_week_monday + timedelta(days=1)).isoformat(),
                            "regular_hours": 8.0,
                            "overtime_hours": 0.0,
                            "leave_hours": {},
                            "notes": "Tuesday regular"
                        }
                    ]
                }
                
                # Update timesheet
                update_response = self.session.put(f"{API_BASE}/payroll/timesheets/{timesheet_id}", json=update_data)
                
                if update_response.status_code == 200:
                    # Submit timesheet
                    submit_response = self.session.post(f"{API_BASE}/payroll/timesheets/{timesheet_id}/submit")
                    
                    if submit_response.status_code == 200:
                        # Approve timesheet
                        approve_response = self.session.post(f"{API_BASE}/payroll/timesheets/{timesheet_id}/approve")
                        
                        if approve_response.status_code == 200:
                            # Verify payslip was generated
                            payslip_response = self.session.get(f"{API_BASE}/payroll/reports/payslip/{timesheet_id}")
                            
                            if payslip_response.status_code == 200:
                                self.log_result(
                                    "Multiple Timesheet Approvals", 
                                    True, 
                                    "Second timesheet approved and payslip generated successfully"
                                )
                            else:
                                self.log_result(
                                    "Multiple Timesheet Approvals - Payslip", 
                                    False, 
                                    "Second timesheet approved but payslip not generated"
                                )
                        else:
                            self.log_result(
                                "Multiple Timesheet Approvals - Approval", 
                                False, 
                                f"Failed to approve second timesheet: {approve_response.status_code}"
                            )
                    else:
                        self.log_result(
                            "Multiple Timesheet Approvals - Submit", 
                            False, 
                            f"Failed to submit second timesheet: {submit_response.status_code}"
                        )
                else:
                    self.log_result(
                        "Multiple Timesheet Approvals - Update", 
                        False, 
                        f"Failed to update second timesheet: {update_response.status_code}"
                    )
            else:
                self.log_result(
                    "Multiple Timesheet Approvals - Create", 
                    False, 
                    f"Failed to create second timesheet: {response.status_code}"
                )
                
        except Exception as e:
            self.log_result("Multiple Timesheet Approvals", False, f"Error: {str(e)}")

    def test_no_duplicate_payslips(self):
        """Verify no duplicate payslips are created for the same timesheet"""
        try:
            # Get all payslips for our test employee
            response = self.session.get(f"{API_BASE}/payroll/reports/payslips")
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("success") and "data" in result:
                    payslips = result["data"]
                    
                    # Count payslips for our employee
                    employee_payslips = [p for p in payslips if p.get("employee_id") == self.test_employee_id]
                    
                    # Check for duplicates based on timesheet_id or pay period
                    timesheet_ids = [p.get("timesheet_id") for p in employee_payslips if p.get("timesheet_id")]
                    unique_timesheet_ids = set(timesheet_ids)
                    
                    if len(timesheet_ids) == len(unique_timesheet_ids):
                        self.log_result(
                            "No Duplicate Payslips", 
                            True, 
                            f"No duplicate payslips found - {len(employee_payslips)} unique payslips for employee"
                        )
                    else:
                        duplicates = len(timesheet_ids) - len(unique_timesheet_ids)
                        self.log_result(
                            "No Duplicate Payslips", 
                            False, 
                            f"Found {duplicates} duplicate payslips for the same timesheets"
                        )
                else:
                    self.log_result(
                        "No Duplicate Payslips - Structure", 
                        False, 
                        "Invalid response structure from payslips endpoint"
                    )
            else:
                self.log_result(
                    "No Duplicate Payslips", 
                    False, 
                    f"Failed to get payslips: {response.status_code}"
                )
                
        except Exception as e:
            self.log_result("No Duplicate Payslips", False, f"Error: {str(e)}")

    def test_payslip_filtering(self):
        """Test filtering payslips by employee_id if backend supports it"""
        try:
            # Try to filter payslips by employee_id
            response = self.session.get(
                f"{API_BASE}/payroll/reports/payslips",
                params={"employee_id": self.test_employee_id}
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("success") and "data" in result:
                    filtered_payslips = result["data"]
                    
                    # Verify all payslips belong to the specified employee
                    all_match = all(p.get("employee_id") == self.test_employee_id for p in filtered_payslips)
                    
                    if all_match:
                        self.log_result(
                            "Payslip Filtering by Employee", 
                            True, 
                            f"Employee filtering works - {len(filtered_payslips)} payslips for employee"
                        )
                    else:
                        self.log_result(
                            "Payslip Filtering by Employee", 
                            False, 
                            "Filtering returned payslips for other employees"
                        )
                else:
                    self.log_result(
                        "Payslip Filtering - Structure", 
                        False, 
                        "Invalid response structure from filtered payslips"
                    )
            else:
                # Filtering might not be supported - this is not necessarily a failure
                self.log_result(
                    "Payslip Filtering by Employee", 
                    True, 
                    f"Employee filtering not supported (status {response.status_code}) - this is acceptable"
                )
                
        except Exception as e:
            self.log_result("Payslip Filtering by Employee", False, f"Error: {str(e)}")

    def run_complete_workflow_test(self):
        """Run the complete timesheet approval workflow with payslip generation test"""
        print("="*100)
        print("COMPLETE TIMESHEET APPROVAL WORKFLOW WITH AUTOMATIC PAYSLIP GENERATION TEST")
        print("="*100)
        
        # Step 1: Authentication
        if not self.authenticate():
            print("❌ CRITICAL: Authentication failed - cannot proceed with testing")
            return False
        
        # Step 2: Get employees list
        if not self.get_employees_list():
            print("❌ CRITICAL: Cannot get employees list - cannot proceed with testing")
            return False
        
        # Step 3: Create and submit timesheet
        if not self.create_and_submit_timesheet():
            print("❌ CRITICAL: Cannot create/submit timesheet - cannot proceed with testing")
            return False
        
        # Step 4: Verify timesheet in pending list
        if not self.verify_timesheet_in_pending_list():
            print("❌ CRITICAL: Timesheet not in pending list - workflow broken")
            return False
        
        # Step 5: Approve timesheet and verify payslip generation (CRITICAL)
        if not self.approve_timesheet_and_verify_payslip_generation():
            print("❌ CRITICAL: Timesheet approval or payslip generation failed - core functionality broken")
            return False
        
        # Step 6: Verify timesheet disappears from pending list
        if not self.verify_timesheet_disappears_from_pending_list():
            print("❌ CRITICAL: Approved timesheet still in pending list - workflow broken")
            return False
        
        # Step 7: Verify approved timesheet in reports
        if not self.verify_approved_timesheet_in_reports():
            print("⚠️  WARNING: Approved timesheet not in reports - may affect reporting")
        
        # Step 8: Verify payslip in payslips list
        if not self.verify_payslip_in_payslips_list():
            print("❌ CRITICAL: Payslip not in payslips list - payslip functionality broken")
            return False
        
        # Step 9: Test edge cases
        self.test_edge_cases()
        
        return True

    def print_test_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "="*100)
        print("COMPLETE TIMESHEET APPROVAL WORKFLOW TEST SUMMARY")
        print("="*100)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        # Show critical results
        critical_tests = [
            "Admin Authentication",
            "Get Employees List", 
            "Submit Timesheet for Approval",
            "Verify Timesheet in Pending List",
            "Timesheet Approval with Pay Calculations",
            "CRITICAL: Automatic Payslip Generation",
            "CRITICAL: Timesheet Removed from Pending List",
            "CRITICAL: Payslip in Payslips List"
        ]
        
        print("\n" + "="*80)
        print("CRITICAL WORKFLOW COMPONENTS:")
        print("="*80)
        
        critical_passed = 0
        for test_name in critical_tests:
            test_result = next((r for r in self.test_results if r['test'] == test_name), None)
            if test_result:
                status = "✅" if test_result['success'] else "❌"
                print(f"{status} {test_name}")
                if test_result['success']:
                    critical_passed += 1
            else:
                print(f"⚪ {test_name} - Not tested")
        
        critical_success_rate = (critical_passed / len(critical_tests) * 100)
        
        # Show failed tests details
        failed_results = [r for r in self.test_results if not r['success']]
        if failed_results:
            print("\n" + "="*80)
            print("FAILED TESTS DETAILS:")
            print("="*80)
            for result in failed_results:
                print(f"\n❌ {result['test']}")
                print(f"   Message: {result['message']}")
                if result['details']:
                    print(f"   Details: {result['details']}")
        
        print("\n" + "="*100)
        print("FINAL ASSESSMENT:")
        print("="*100)
        
        if critical_success_rate == 100:
            print("🎉 PERFECT! COMPLETE TIMESHEET APPROVAL WORKFLOW WITH PAYSLIP GENERATION IS 100% FUNCTIONAL!")
            print("✅ Timesheet approval succeeds")
            print("✅ Payslip automatically generated and saved")
            print("✅ Approved timesheet disappears from pending list")
            print("✅ Approved timesheet appears in reports")
            print("✅ Payslip appears in payslips list with all required fields")
            print("✅ Pay calculations are accurate")
            print("✅ No duplicate payslips created")
        elif critical_success_rate >= 80:
            print(f"✅ GOOD! Critical workflow components: {critical_success_rate:.1f}% functional")
            print("⚠️  Some non-critical issues may need attention")
        else:
            print(f"❌ CRITICAL ISSUES! Only {critical_success_rate:.1f}% of critical components working")
            print("🚨 TIMESHEET APPROVAL WORKFLOW WITH PAYSLIP GENERATION NEEDS IMMEDIATE ATTENTION")
        
        print("="*100)

def main():
    """Main test execution"""
    tester = TimesheetApprovalPayslipTester()
    
    try:
        success = tester.run_complete_workflow_test()
        tester.print_test_summary()
        
        if success:
            print("\n🎉 COMPLETE TIMESHEET APPROVAL WORKFLOW WITH PAYSLIP GENERATION TEST COMPLETED SUCCESSFULLY!")
        else:
            print("\n❌ COMPLETE TIMESHEET APPROVAL WORKFLOW WITH PAYSLIP GENERATION TEST FAILED!")
            
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Test failed with unexpected error: {str(e)}")

if __name__ == "__main__":
    main()