#!/usr/bin/env python3
"""
Enhanced PDF Payslip Generation Testing
Testing the enhanced PDF payslip generation with all new fields including leave information and leave balances.
"""

import requests
import json
import os
from datetime import datetime, date, timedelta
import sys

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://timesheet-manager-33.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class PayslipTester:
    def __init__(self):
        self.session = requests.Session()
        self.access_token = None
        self.employee_id = None
        self.timesheet_id = None
        self.payslip_id = None
        
    def authenticate(self):
        """Authenticate as admin user"""
        print("🔐 Authenticating as admin (Callum/Peach7510)...")
        
        login_data = {
            "username": "Callum",
            "password": "Peach7510"
        }
        
        response = self.session.post(f"{API_BASE}/auth/login", json=login_data)
        
        if response.status_code == 200:
            data = response.json()
            self.access_token = data["access_token"]
            self.session.headers.update({"Authorization": f"Bearer {self.access_token}"})
            print(f"✅ Authentication successful - User: {data['user']['full_name']}")
            return True
        else:
            print(f"❌ Authentication failed: {response.status_code} - {response.text}")
            return False
    
    def get_employees(self):
        """Get list of employees"""
        print("\n👥 Getting employee list...")
        
        response = self.session.get(f"{API_BASE}/payroll/employees")
        
        if response.status_code == 200:
            data = response.json()
            # Handle both list and dict response formats
            if isinstance(data, list):
                employees = data
            else:
                employees = data.get("data", [])
            print(f"✅ Found {len(employees)} employees")
            
            if employees:
                # Use first employee for testing
                self.employee_id = employees[0]["id"]
                print(f"📋 Selected employee: {employees[0]['first_name']} {employees[0]['last_name']} (ID: {self.employee_id})")
                return True
            else:
                print("❌ No employees found")
                return False
        else:
            print(f"❌ Failed to get employees: {response.status_code} - {response.text}")
            return False
    
    def create_test_timesheet(self):
        """Create a comprehensive test timesheet with regular, overtime, and leave hours"""
        print(f"\n📝 Creating test timesheet for employee {self.employee_id}...")
        
        # Calculate week starting date (current week)
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        
        # Create timesheet entries for the week
        entries = []
        for i in range(7):
            entry_date = week_start + timedelta(days=i)
            
            if i == 0:  # Monday - 8 regular hours
                entry = {
                    "date": entry_date.isoformat(),
                    "regular_hours": 8.0,
                    "overtime_hours": 0.0,
                    "leave_hours": {},
                    "notes": "Regular work day"
                }
            elif i == 1:  # Tuesday - 8 regular hours
                entry = {
                    "date": entry_date.isoformat(),
                    "regular_hours": 8.0,
                    "overtime_hours": 0.0,
                    "leave_hours": {},
                    "notes": "Regular work day"
                }
            elif i == 2:  # Wednesday - 8 regular hours
                entry = {
                    "date": entry_date.isoformat(),
                    "regular_hours": 8.0,
                    "overtime_hours": 0.0,
                    "leave_hours": {},
                    "notes": "Regular work day"
                }
            elif i == 3:  # Thursday - 8 regular + 2 overtime hours
                entry = {
                    "date": entry_date.isoformat(),
                    "regular_hours": 8.0,
                    "overtime_hours": 2.0,
                    "leave_hours": {},
                    "notes": "Overtime work day"
                }
            elif i == 4:  # Friday - 7.6 hours annual leave
                entry = {
                    "date": entry_date.isoformat(),
                    "regular_hours": 0.0,
                    "overtime_hours": 0.0,
                    "leave_hours": {"annual_leave": 7.6},
                    "notes": "Annual leave day"
                }
            else:  # Weekend - no hours
                entry = {
                    "date": entry_date.isoformat(),
                    "regular_hours": 0.0,
                    "overtime_hours": 0.0,
                    "leave_hours": {},
                    "notes": "Weekend"
                }
            
            entries.append(entry)
        
        # Get current week timesheet
        response = self.session.get(f"{API_BASE}/payroll/timesheets/current-week/{self.employee_id}")
        
        if response.status_code == 200:
            timesheet_data = response.json()
            self.timesheet_id = timesheet_data["id"]
            
            # Update timesheet with our test data
            update_data = {
                "employee_id": self.employee_id,
                "week_starting": week_start.isoformat(),
                "entries": entries,
                "status": "draft"
            }
            
            update_response = self.session.put(f"{API_BASE}/payroll/timesheets/{self.timesheet_id}", json=update_data)
            
            if update_response.status_code == 200:
                print("✅ Test timesheet created successfully")
                print(f"   📊 Regular hours: 32.0h (Mon-Thu)")
                print(f"   ⏰ Overtime hours: 2.0h (Thu)")
                print(f"   🏖️ Leave hours: 7.6h annual leave (Fri)")
                print(f"   📈 Total hours: 41.6h")
                return True
            else:
                print(f"❌ Failed to update timesheet: {update_response.status_code} - {update_response.text}")
                return False
        else:
            print(f"❌ Failed to get current week timesheet: {response.status_code} - {response.text}")
            return False
    
    def submit_timesheet(self):
        """Submit the timesheet for approval"""
        print(f"\n📤 Submitting timesheet {self.timesheet_id}...")
        
        response = self.session.post(f"{API_BASE}/payroll/timesheets/{self.timesheet_id}/submit")
        
        if response.status_code == 200:
            print("✅ Timesheet submitted successfully")
            return True
        else:
            print(f"❌ Failed to submit timesheet: {response.status_code} - {response.text}")
            return False
    
    def approve_timesheet(self):
        """Approve the timesheet to generate payslip"""
        print(f"\n✅ Approving timesheet {self.timesheet_id}...")
        
        response = self.session.post(f"{API_BASE}/payroll/timesheets/{self.timesheet_id}/approve")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Timesheet approved successfully")
            print(f"   💰 Gross Pay: ${data.get('gross_pay', 0):.2f}")
            print(f"   💵 Net Pay: ${data.get('net_pay', 0):.2f}")
            print(f"   ⏱️ Hours Worked: {data.get('hours_worked', 0):.1f}h")
            return True
        else:
            print(f"❌ Failed to approve timesheet: {response.status_code} - {response.text}")
            return False
    
    def verify_payslip_data_structure(self):
        """Verify the payslip includes all new fields"""
        print(f"\n🔍 Verifying payslip data structure...")
        
        response = self.session.get(f"{API_BASE}/payroll/reports/payslips")
        
        if response.status_code == 200:
            data = response.json()
            payslips = data.get("data", [])
            
            if not payslips:
                print("❌ No payslips found")
                return False
            
            # Get the most recent payslip
            payslip = payslips[0]
            self.payslip_id = payslip["id"]
            payslip_data = payslip.get("payslip_data", {})
            
            print("✅ Payslip data structure verification:")
            
            # Check hours structure
            hours = payslip_data.get("hours", {})
            print(f"   📊 Regular hours: {hours.get('regular_hours', 'MISSING')}")
            print(f"   ⏰ Overtime hours: {hours.get('overtime_hours', 'MISSING')}")
            
            # NEW FIELD: leave_hours
            leave_hours = hours.get('leave_hours', 'MISSING')
            print(f"   🏖️ Leave hours: {leave_hours}")
            
            # NEW FIELD: total_hours
            total_hours = hours.get('total_hours', 'MISSING')
            print(f"   📈 Total hours: {total_hours}")
            
            # NEW FIELD: leave_used
            leave_used = payslip_data.get('leave_used', 'MISSING')
            print(f"   📋 Leave used: {leave_used}")
            
            # NEW FIELD: leave_balances
            leave_balances = payslip_data.get('leave_balances', 'MISSING')
            print(f"   💼 Leave balances: {leave_balances}")
            
            if isinstance(leave_balances, dict):
                print(f"      - Annual leave: {leave_balances.get('annual_leave', 'MISSING')}")
                print(f"      - Sick leave: {leave_balances.get('sick_leave', 'MISSING')}")
                print(f"      - Personal leave: {leave_balances.get('personal_leave', 'MISSING')}")
            
            # Verify all required fields are present
            required_fields = ['leave_hours', 'total_hours']
            missing_fields = []
            
            for field in required_fields:
                if field not in hours or hours[field] == 'MISSING':
                    missing_fields.append(f"hours.{field}")
            
            if 'leave_used' not in payslip_data:
                missing_fields.append('leave_used')
            
            if 'leave_balances' not in payslip_data:
                missing_fields.append('leave_balances')
            
            if missing_fields:
                print(f"❌ Missing required fields: {', '.join(missing_fields)}")
                return False
            else:
                print("✅ All new payslip fields are present")
                return True
        else:
            print(f"❌ Failed to get payslips: {response.status_code} - {response.text}")
            return False
    
    def test_pdf_generation(self):
        """Test PDF generation endpoint"""
        print(f"\n📄 Testing PDF generation for payslip {self.payslip_id}...")
        
        if not self.payslip_id:
            print("❌ No payslip ID available for PDF generation")
            return False
        
        response = self.session.get(f"{API_BASE}/payroll/reports/payslip/{self.payslip_id}/pdf")
        
        if response.status_code == 200:
            print("✅ PDF generation successful")
            
            # Verify Content-Type
            content_type = response.headers.get('Content-Type', '')
            print(f"   📋 Content-Type: {content_type}")
            
            if content_type == 'application/pdf':
                print("✅ Correct Content-Type: application/pdf")
            else:
                print(f"❌ Incorrect Content-Type: expected 'application/pdf', got '{content_type}'")
                return False
            
            # Verify Content-Disposition
            content_disposition = response.headers.get('Content-Disposition', '')
            print(f"   📎 Content-Disposition: {content_disposition}")
            
            if 'attachment' in content_disposition and 'payslip_' in content_disposition:
                print("✅ Correct Content-Disposition with attachment and filename")
            else:
                print(f"❌ Incorrect Content-Disposition: {content_disposition}")
                return False
            
            # Verify PDF file size
            pdf_size = len(response.content)
            print(f"   📏 PDF file size: {pdf_size} bytes")
            
            if pdf_size > 0:
                print("✅ PDF file has content (size > 0 bytes)")
            else:
                print("❌ PDF file is empty")
                return False
            
            # Verify filename format
            if 'payslip_EMP' in content_disposition and '.pdf' in content_disposition:
                print("✅ Filename format correct: payslip_{employee_number}_{week_start}.pdf")
            else:
                print(f"❌ Filename format incorrect: {content_disposition}")
                return False
            
            return True
        else:
            print(f"❌ PDF generation failed: {response.status_code} - {response.text}")
            return False
    
    def test_edge_cases(self):
        """Test edge cases for payslip generation"""
        print(f"\n🧪 Testing edge cases...")
        
        # Test payslip with no leave used
        print("   📋 Testing payslip with no leave used...")
        
        # Create a simple timesheet with only regular hours
        today = date.today()
        week_start = today - timedelta(days=today.weekday() + 7)  # Previous week
        
        entries = []
        for i in range(7):
            entry_date = week_start + timedelta(days=i)
            
            if i < 5:  # Monday to Friday - regular hours only
                entry = {
                    "date": entry_date.isoformat(),
                    "regular_hours": 8.0,
                    "overtime_hours": 0.0,
                    "leave_hours": {},
                    "notes": "Regular work day"
                }
            else:  # Weekend - no hours
                entry = {
                    "date": entry_date.isoformat(),
                    "regular_hours": 0.0,
                    "overtime_hours": 0.0,
                    "leave_hours": {},
                    "notes": "Weekend"
                }
            
            entries.append(entry)
        
        # Get timesheet for previous week
        week_param = week_start.isoformat()
        response = self.session.get(f"{API_BASE}/payroll/timesheets/current-week/{self.employee_id}?week_starting={week_param}")
        
        if response.status_code == 200:
            timesheet_data = response.json()
            test_timesheet_id = timesheet_data["id"]
            
            # Update with regular hours only
            update_data = {"entries": entries, "status": "draft"}
            update_response = self.session.put(f"{API_BASE}/payroll/timesheets/{test_timesheet_id}", json=update_data)
            
            if update_response.status_code == 200:
                # Submit and approve
                self.session.post(f"{API_BASE}/payroll/timesheets/{test_timesheet_id}/submit")
                approve_response = self.session.post(f"{API_BASE}/payroll/timesheets/{test_timesheet_id}/approve")
                
                if approve_response.status_code == 200:
                    print("   ✅ Edge case timesheet (no leave) created and approved")
                    
                    # Verify payslip structure
                    payslips_response = self.session.get(f"{API_BASE}/payroll/reports/payslips")
                    if payslips_response.status_code == 200:
                        payslips = payslips_response.json().get("data", [])
                        if payslips:
                            edge_payslip = payslips[0]  # Most recent
                            payslip_data = edge_payslip.get("payslip_data", {})
                            
                            leave_used = payslip_data.get('leave_used', {})
                            if not leave_used or len(leave_used) == 0:
                                print("   ✅ Leave used is empty/null for no-leave payslip")
                            else:
                                print(f"   ❌ Leave used should be empty but got: {leave_used}")
                                return False
                            
                            hours = payslip_data.get("hours", {})
                            if hours.get('leave_hours', 0) == 0:
                                print("   ✅ Leave hours is 0 for no-leave payslip")
                            else:
                                print(f"   ❌ Leave hours should be 0 but got: {hours.get('leave_hours')}")
                                return False
                            
                            total_hours = hours.get('total_hours', 0)
                            expected_total = hours.get('regular_hours', 0) + hours.get('overtime_hours', 0)
                            if total_hours == expected_total:
                                print(f"   ✅ Total hours calculation correct: {total_hours}h")
                            else:
                                print(f"   ❌ Total hours calculation incorrect: got {total_hours}, expected {expected_total}")
                                return False
                        else:
                            print("   ❌ No payslips found for edge case test")
                            return False
                    else:
                        print("   ❌ Failed to get payslips for edge case verification")
                        return False
                else:
                    print("   ❌ Failed to approve edge case timesheet")
                    return False
            else:
                print("   ❌ Failed to update edge case timesheet")
                return False
        else:
            print("   ❌ Failed to get timesheet for edge case test")
            return False
        
        return True
    
    def run_comprehensive_test(self):
        """Run the complete test scenario"""
        print("🚀 Starting Enhanced PDF Payslip Generation Testing")
        print("=" * 60)
        
        test_results = []
        
        # Test 1: Authentication
        if self.authenticate():
            test_results.append(("Authentication", True))
        else:
            test_results.append(("Authentication", False))
            return self.print_results(test_results)
        
        # Test 2: Get employees
        if self.get_employees():
            test_results.append(("Employee Selection", True))
        else:
            test_results.append(("Employee Selection", False))
            return self.print_results(test_results)
        
        # Test 3: Create comprehensive timesheet
        if self.create_test_timesheet():
            test_results.append(("Timesheet Creation", True))
        else:
            test_results.append(("Timesheet Creation", False))
            return self.print_results(test_results)
        
        # Test 4: Submit timesheet
        if self.submit_timesheet():
            test_results.append(("Timesheet Submission", True))
        else:
            test_results.append(("Timesheet Submission", False))
            return self.print_results(test_results)
        
        # Test 5: Approve timesheet
        if self.approve_timesheet():
            test_results.append(("Timesheet Approval", True))
        else:
            test_results.append(("Timesheet Approval", False))
            return self.print_results(test_results)
        
        # Test 6: Verify payslip data structure
        if self.verify_payslip_data_structure():
            test_results.append(("Payslip Data Structure", True))
        else:
            test_results.append(("Payslip Data Structure", False))
            return self.print_results(test_results)
        
        # Test 7: PDF generation
        if self.test_pdf_generation():
            test_results.append(("PDF Generation", True))
        else:
            test_results.append(("PDF Generation", False))
            return self.print_results(test_results)
        
        # Test 8: Edge cases
        if self.test_edge_cases():
            test_results.append(("Edge Cases", True))
        else:
            test_results.append(("Edge Cases", False))
            return self.print_results(test_results)
        
        return self.print_results(test_results)
    
    def print_results(self, test_results):
        """Print final test results"""
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        passed = 0
        total = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} - {test_name}")
            if result:
                passed += 1
        
        print("-" * 60)
        print(f"📈 Overall Success Rate: {passed}/{total} ({(passed/total)*100:.1f}%)")
        
        if passed == total:
            print("🎉 ALL TESTS PASSED - Enhanced PDF Payslip Generation is fully functional!")
            return True
        else:
            print(f"⚠️  {total - passed} test(s) failed - Issues need to be addressed")
            return False

def main():
    """Main test execution"""
    tester = PayslipTester()
    success = tester.run_comprehensive_test()
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()