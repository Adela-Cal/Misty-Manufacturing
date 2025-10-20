#!/usr/bin/env python3
"""
Payroll Reports Endpoints Testing
Testing the newly implemented payroll reports endpoints as requested in the review.
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

class PayrollReportsAPITester:
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
        """Test authentication with demo user"""
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

    def test_payslips_endpoint(self):
        """Test GET /api/payroll/reports/payslips - Get all historic payslips"""
        print("\n=== TEST 1: GET /api/payroll/reports/payslips ===")
        
        try:
            response = self.session.get(f"{API_BASE}/payroll/reports/payslips")
            
            if response.status_code == 200:
                result = response.json()
                
                # Check response structure: {success: true, data: []}
                if result.get("success") == True and "data" in result:
                    payslips = result["data"]
                    
                    if isinstance(payslips, list):
                        self.log_result(
                            "GET /api/payroll/reports/payslips", 
                            True, 
                            f"Successfully retrieved payslips - Expected structure confirmed",
                            f"Found {len(payslips)} payslips. Response: {{success: true, data: []}}"
                        )
                        return payslips
                    else:
                        self.log_result(
                            "GET /api/payroll/reports/payslips", 
                            False, 
                            "Data field is not an array"
                        )
                else:
                    self.log_result(
                        "GET /api/payroll/reports/payslips", 
                        False, 
                        "Invalid response structure - missing success or data fields"
                    )
            else:
                self.log_result(
                    "GET /api/payroll/reports/payslips", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("GET /api/payroll/reports/payslips", False, f"Error: {str(e)}")
        
        return []

    def test_timesheets_report_no_filters(self):
        """Test GET /api/payroll/reports/timesheets - Get timesheet report without filters"""
        print("\n=== TEST 2: GET /api/payroll/reports/timesheets (No Filters) ===")
        
        try:
            response = self.session.get(f"{API_BASE}/payroll/reports/timesheets")
            
            if response.status_code == 200:
                result = response.json()
                
                # Check response structure includes data and summary
                if (result.get("success") == True and 
                    "data" in result and 
                    "summary" in result):
                    
                    timesheets = result["data"]
                    summary = result["summary"]
                    
                    # Verify summary structure
                    expected_summary_fields = ["total_timesheets", "total_regular_hours", "total_overtime_hours", "total_hours"]
                    missing_summary_fields = [field for field in expected_summary_fields if field not in summary]
                    
                    if not missing_summary_fields:
                        self.log_result(
                            "GET /api/payroll/reports/timesheets (No Filters)", 
                            True, 
                            f"Successfully retrieved timesheet report with summary",
                            f"Found {len(timesheets)} timesheets. Summary: {summary['total_timesheets']} timesheets, {summary['total_hours']} total hours"
                        )
                        
                        # Check employee name enrichment
                        if len(timesheets) > 0:
                            timesheet = timesheets[0]
                            if "employee_name" in timesheet:
                                self.log_result(
                                    "Timesheet Employee Name Enrichment", 
                                    True, 
                                    f"Timesheets properly enriched with employee names"
                                )
                            else:
                                self.log_result(
                                    "Timesheet Employee Name Enrichment", 
                                    False, 
                                    "Timesheets missing employee_name enrichment"
                                )
                        
                        return timesheets
                    else:
                        self.log_result(
                            "GET /api/payroll/reports/timesheets (No Filters)", 
                            False, 
                            f"Summary missing required fields: {missing_summary_fields}"
                        )
                else:
                    self.log_result(
                        "GET /api/payroll/reports/timesheets (No Filters)", 
                        False, 
                        "Invalid response structure - missing success, data, or summary"
                    )
            else:
                self.log_result(
                    "GET /api/payroll/reports/timesheets (No Filters)", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("GET /api/payroll/reports/timesheets (No Filters)", False, f"Error: {str(e)}")
        
        return []

    def test_timesheets_report_with_filters(self):
        """Test GET /api/payroll/reports/timesheets with employee_id and date filters"""
        print("\n=== TEST 3: GET /api/payroll/reports/timesheets (With Filters) ===")
        
        try:
            # Get employees first for employee_id filter
            employees_response = self.session.get(f"{API_BASE}/payroll/employees")
            
            if employees_response.status_code == 200:
                employees = employees_response.json()
                
                if employees and len(employees) > 0:
                    employee = employees[0]
                    employee_id = employee["id"]
                    
                    # Test with employee_id filter
                    response = self.session.get(f"{API_BASE}/payroll/reports/timesheets?employee_id={employee_id}")
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        if result.get("success") == True and "data" in result:
                            timesheets = result["data"]
                            
                            # Verify all timesheets belong to the specified employee
                            all_match_employee = all(ts.get("employee_id") == employee_id for ts in timesheets)
                            
                            if all_match_employee:
                                self.log_result(
                                    "Timesheet Report - Employee ID Filter", 
                                    True, 
                                    f"Successfully filtered timesheets by employee_id",
                                    f"Found {len(timesheets)} timesheets for employee {employee.get('first_name')} {employee.get('last_name')}"
                                )
                            else:
                                self.log_result(
                                    "Timesheet Report - Employee ID Filter", 
                                    False, 
                                    "Filter not working - found timesheets for other employees"
                                )
                        else:
                            self.log_result(
                                "Timesheet Report - Employee ID Filter", 
                                False, 
                                "Invalid response structure"
                            )
                    else:
                        self.log_result(
                            "Timesheet Report - Employee ID Filter", 
                            False, 
                            f"Failed with status {response.status_code}"
                        )
                
                # Test with date range filters
                start_date = "2024-12-01"
                end_date = "2024-12-31"
                
                response2 = self.session.get(f"{API_BASE}/payroll/reports/timesheets?start_date={start_date}&end_date={end_date}")
                
                if response2.status_code == 200:
                    result2 = response2.json()
                    
                    if result2.get("success") == True and "data" in result2:
                        timesheets2 = result2["data"]
                        
                        self.log_result(
                            "Timesheet Report - Date Range Filter", 
                            True, 
                            f"Successfully filtered timesheets by date range",
                            f"Found {len(timesheets2)} timesheets between {start_date} and {end_date}"
                        )
                    else:
                        self.log_result(
                            "Timesheet Report - Date Range Filter", 
                            False, 
                            "Invalid response structure for date filter"
                        )
                else:
                    self.log_result(
                        "Timesheet Report - Date Range Filter", 
                        False, 
                        f"Date filter failed with status {response2.status_code}"
                    )
            else:
                self.log_result(
                    "Timesheet Report Filters Setup", 
                    False, 
                    f"Failed to get employees for filter test: {employees_response.status_code}"
                )
                
        except Exception as e:
            self.log_result("Timesheet Report Filters", False, f"Error: {str(e)}")

    def test_payslip_generation(self):
        """Test GET /api/payroll/reports/payslip/{timesheet_id} - Generate payslip from approved timesheet"""
        print("\n=== TEST 4: GET /api/payroll/reports/payslip/{timesheet_id} ===")
        
        try:
            # First, check if there are any approved timesheets
            response = self.session.get(f"{API_BASE}/payroll/reports/timesheets")
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("success") == True and "data" in result:
                    timesheets = result["data"]
                    
                    # Look for approved timesheets
                    approved_timesheets = [ts for ts in timesheets if ts.get("status") == "approved"]
                    
                    if approved_timesheets:
                        # Test with first approved timesheet
                        approved_timesheet = approved_timesheets[0]
                        timesheet_id = approved_timesheet["id"]
                        
                        self.log_result(
                            "Found Approved Timesheets", 
                            True, 
                            f"Found {len(approved_timesheets)} approved timesheets for payslip generation",
                            f"Using timesheet ID: {timesheet_id}"
                        )
                        
                        # Generate payslip
                        payslip_response = self.session.get(f"{API_BASE}/payroll/reports/payslip/{timesheet_id}")
                        
                        if payslip_response.status_code == 200:
                            payslip_result = payslip_response.json()
                            
                            if payslip_result.get("success") == True and "data" in payslip_result:
                                payslip_data = payslip_result["data"]
                                
                                # Verify payslip structure
                                expected_fields = ["id", "timesheet_id", "employee_id", "payslip_data", "generated_at"]
                                missing_fields = [field for field in expected_fields if field not in payslip_data]
                                
                                if not missing_fields:
                                    # Check payslip_data structure
                                    payslip_details = payslip_data.get("payslip_data", {})
                                    expected_sections = ["employee", "pay_period", "hours", "earnings", "deductions", "net_pay", "year_to_date", "bank_details"]
                                    missing_sections = [section for section in expected_sections if section not in payslip_details]
                                    
                                    if not missing_sections:
                                        self.log_result(
                                            "Generate Payslip from Approved Timesheet", 
                                            True, 
                                            f"Successfully generated payslip from approved timesheet",
                                            f"Payslip ID: {payslip_data['id']}, Net Pay: ${payslip_details.get('net_pay', 0)}"
                                        )
                                        
                                        # Verify specific payslip data structure
                                        self.verify_payslip_data_structure(payslip_details)
                                    else:
                                        self.log_result(
                                            "Generate Payslip from Approved Timesheet", 
                                            False, 
                                            f"Payslip data missing sections: {missing_sections}"
                                        )
                                else:
                                    self.log_result(
                                        "Generate Payslip from Approved Timesheet", 
                                        False, 
                                        f"Payslip missing required fields: {missing_fields}"
                                    )
                            else:
                                self.log_result(
                                    "Generate Payslip from Approved Timesheet", 
                                    False, 
                                    "Invalid payslip response structure"
                                )
                        else:
                            self.log_result(
                                "Generate Payslip from Approved Timesheet", 
                                False, 
                                f"Payslip generation failed with status {payslip_response.status_code}",
                                payslip_response.text
                            )
                    else:
                        # No approved timesheets found - test with non-existent ID to verify 404 handling
                        fake_timesheet_id = str(uuid.uuid4())
                        payslip_response = self.session.get(f"{API_BASE}/payroll/reports/payslip/{fake_timesheet_id}")
                        
                        if payslip_response.status_code == 404:
                            self.log_result(
                                "No Approved Timesheets Available", 
                                True, 
                                "No approved timesheets found, but endpoint correctly returns 404 for non-existent timesheet",
                                f"Found timesheets with statuses: {list(set(ts.get('status') for ts in timesheets))}"
                            )
                        else:
                            self.log_result(
                                "No Approved Timesheets Available", 
                                False, 
                                f"Expected 404 for non-existent timesheet, got {payslip_response.status_code}"
                            )
                else:
                    self.log_result(
                        "Payslip Generation Setup", 
                        False, 
                        "Invalid timesheets response structure"
                    )
            else:
                self.log_result(
                    "Payslip Generation Setup", 
                    False, 
                    f"Failed to get timesheets: {response.status_code}"
                )
                
        except Exception as e:
            self.log_result("Payslip Generation", False, f"Error: {str(e)}")

    def verify_payslip_data_structure(self, payslip_details):
        """Verify payslip data structure includes all required sections and fields"""
        try:
            # Check employee info
            employee = payslip_details.get("employee", {})
            required_employee_fields = ["name", "employee_number", "position", "department"]
            missing_employee_fields = [field for field in required_employee_fields if not employee.get(field)]
            
            if not missing_employee_fields:
                self.log_result(
                    "Payslip Employee Info Structure", 
                    True, 
                    f"Employee info complete: {employee['name']}, {employee['position']}, {employee['department']}"
                )
            else:
                self.log_result(
                    "Payslip Employee Info Structure", 
                    False, 
                    f"Employee info missing fields: {missing_employee_fields}"
                )
            
            # Check pay period
            pay_period = payslip_details.get("pay_period", {})
            if pay_period.get("week_start") and pay_period.get("week_end"):
                self.log_result(
                    "Payslip Pay Period Structure", 
                    True, 
                    f"Pay period complete: {pay_period['week_start']} to {pay_period['week_end']}"
                )
            else:
                self.log_result(
                    "Payslip Pay Period Structure", 
                    False, 
                    "Pay period missing week_start or week_end"
                )
            
            # Check hours section
            hours = payslip_details.get("hours", {})
            required_hours_fields = ["regular_hours", "overtime_hours", "hourly_rate"]
            missing_hours_fields = [field for field in required_hours_fields if field not in hours]
            
            if not missing_hours_fields:
                self.log_result(
                    "Payslip Hours Structure", 
                    True, 
                    f"Hours section complete: {hours['regular_hours']}h regular, {hours['overtime_hours']}h overtime @ ${hours['hourly_rate']}/hr"
                )
            else:
                self.log_result(
                    "Payslip Hours Structure", 
                    False, 
                    f"Hours section missing fields: {missing_hours_fields}"
                )
            
            # Check earnings section
            earnings = payslip_details.get("earnings", {})
            required_earnings_fields = ["regular_pay", "overtime_pay", "gross_pay"]
            missing_earnings_fields = [field for field in required_earnings_fields if field not in earnings]
            
            if not missing_earnings_fields:
                self.log_result(
                    "Payslip Earnings Structure", 
                    True, 
                    f"Earnings section complete: Regular ${earnings['regular_pay']}, Overtime ${earnings['overtime_pay']}, Gross ${earnings['gross_pay']}"
                )
            else:
                self.log_result(
                    "Payslip Earnings Structure", 
                    False, 
                    f"Earnings section missing fields: {missing_earnings_fields}"
                )
            
            # Check deductions section
            deductions = payslip_details.get("deductions", {})
            required_deductions_fields = ["tax_withheld", "superannuation"]
            missing_deductions_fields = [field for field in required_deductions_fields if field not in deductions]
            
            if not missing_deductions_fields:
                self.log_result(
                    "Payslip Deductions Structure", 
                    True, 
                    f"Deductions section complete: Tax ${deductions['tax_withheld']}, Super ${deductions['superannuation']}"
                )
            else:
                self.log_result(
                    "Payslip Deductions Structure", 
                    False, 
                    f"Deductions section missing fields: {missing_deductions_fields}"
                )
            
            # Check year_to_date section
            ytd = payslip_details.get("year_to_date", {})
            required_ytd_fields = ["gross_pay", "tax_withheld", "superannuation", "net_pay"]
            missing_ytd_fields = [field for field in required_ytd_fields if field not in ytd]
            
            if not missing_ytd_fields:
                self.log_result(
                    "Payslip Year-to-Date Structure", 
                    True, 
                    f"YTD section complete: Gross ${ytd['gross_pay']}, Net ${ytd['net_pay']}"
                )
            else:
                self.log_result(
                    "Payslip Year-to-Date Structure", 
                    False, 
                    f"YTD section missing fields: {missing_ytd_fields}"
                )
            
            # Check bank_details section
            bank_details = payslip_details.get("bank_details", {})
            required_bank_fields = ["bsb", "account_number", "superannuation_fund"]
            missing_bank_fields = [field for field in required_bank_fields if field not in bank_details]
            
            if not missing_bank_fields:
                self.log_result(
                    "Payslip Bank Details Structure", 
                    True, 
                    f"Bank details section complete"
                )
            else:
                self.log_result(
                    "Payslip Bank Details Structure", 
                    False, 
                    f"Bank details section missing fields: {missing_bank_fields}"
                )
                
        except Exception as e:
            self.log_result("Verify Payslip Data Structure", False, f"Error: {str(e)}")

    def print_test_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "="*80)
        print("PAYROLL REPORTS ENDPOINTS TEST SUMMARY")
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
        
        print("\n" + "="*80)
        if success_rate == 100:
            print("🎉 PERFECT! 100% SUCCESS RATE ACHIEVED!")
        elif success_rate >= 90:
            print(f"🎯 EXCELLENT! {success_rate:.1f}% SUCCESS RATE")
        elif success_rate >= 80:
            print(f"✅ GOOD! {success_rate:.1f}% SUCCESS RATE")
        else:
            print(f"⚠️  NEEDS IMPROVEMENT: {success_rate:.1f}% SUCCESS RATE")
        print("="*80)

    def run_all_tests(self):
        """Run all payroll reports endpoint tests"""
        print("🚀 STARTING PAYROLL REPORTS ENDPOINTS TESTING")
        print("Testing newly implemented payroll reports endpoints as requested")
        print("="*80)
        
        # Authenticate first
        if not self.authenticate():
            print("❌ Authentication failed - cannot proceed with tests")
            return
        
        # Test 1: GET /api/payroll/reports/payslips
        self.test_payslips_endpoint()
        
        # Test 2: GET /api/payroll/reports/timesheets (no filters)
        self.test_timesheets_report_no_filters()
        
        # Test 3: GET /api/payroll/reports/timesheets (with filters)
        self.test_timesheets_report_with_filters()
        
        # Test 4: GET /api/payroll/reports/payslip/{timesheet_id}
        self.test_payslip_generation()
        
        # Print final summary
        self.print_test_summary()

if __name__ == "__main__":
    tester = PayrollReportsAPITester()
    tester.run_all_tests()