#!/usr/bin/env python3
"""
Profitability Report Testing Suite
Testing the Profitability Report functionality end-to-end as requested in review.

TEST OBJECTIVES:
1. Verify completed/archived orders exist in the database
2. Test POST /api/reports/profitability endpoint with sample data
3. Verify all data sources are accessible (orders, job_cards, timesheets, materials, etc.)
4. Check if calculations are working correctly

TEST STEPS:
1. Login with admin credentials (Callum/Peach7510)
2. GET /api/orders to check for completed/archived orders
3. Verify at least one order has:
   - status="completed" OR current_stage="cleared"
   - Has associated job card
   - Has timesheet entries
   - Has material usage data
4. Test POST /api/reports/profitability with:
   - Multiple jobs mode (no filters, get all completed jobs)
   - profit_threshold: 0
5. If no data exists, identify what's missing
6. Test with specific order_ids if available
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

class ProfitabilityReportTester:
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
        """Test authentication with admin credentials (Callum/Peach7510)"""
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

    def test_profitability_report_end_to_end(self):
        """
        MAIN TEST: Profitability Report End-to-End Testing
        """
        print("\n" + "="*80)
        print("PROFITABILITY REPORT END-TO-END TESTING")
        print("Testing the complete profitability report functionality")
        print("="*80)
        
        # Step 1: Check for completed/archived orders
        completed_orders = self.check_completed_archived_orders()
        
        # Step 1b: If no completed orders, try to move some orders to completed status
        if not completed_orders:
            completed_orders = self.create_completed_orders_for_testing()
        
        # Step 2: Verify data sources are accessible
        self.verify_data_sources()
        
        # Step 3: Test profitability report endpoint - Multiple jobs mode
        self.test_profitability_report_multiple_jobs()
        
        # Step 4: Test profitability report with specific order IDs if available
        if completed_orders:
            self.test_profitability_report_specific_orders(completed_orders)
        
        # Step 5: Analyze what data is missing if no results
        self.analyze_missing_data()

    def check_completed_archived_orders(self):
        """Check for completed/archived orders in the database"""
        print("\n--- STEP 1: Checking for Completed/Archived Orders ---")
        
        try:
            response = self.session.get(f"{API_BASE}/orders")
            
            if response.status_code == 200:
                orders = response.json()
                
                # Filter for completed or archived orders
                completed_orders = []
                cleared_orders = []
                
                for order in orders:
                    status = order.get('status', '').lower()
                    current_stage = order.get('current_stage', '').lower()
                    
                    if status == 'completed':
                        completed_orders.append(order)
                    elif current_stage == 'cleared':
                        cleared_orders.append(order)
                
                total_eligible = len(completed_orders) + len(cleared_orders)
                
                self.log_result(
                    "Check Completed Orders", 
                    total_eligible > 0, 
                    f"Found {len(completed_orders)} completed orders and {len(cleared_orders)} cleared orders",
                    f"Total orders in database: {len(orders)}, Eligible for profitability: {total_eligible}"
                )
                
                # Log details of eligible orders
                eligible_orders = completed_orders + cleared_orders
                if eligible_orders:
                    for i, order in enumerate(eligible_orders[:5]):  # Show first 5
                        order_info = f"Order {order.get('order_number', 'N/A')} - Status: {order.get('status')}, Stage: {order.get('current_stage')}"
                        self.log_result(
                            f"Eligible Order {i+1}", 
                            True, 
                            order_info
                        )
                
                return eligible_orders
                
            else:
                self.log_result(
                    "Check Completed Orders", 
                    False, 
                    f"Failed to get orders: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Check Completed Orders", False, f"Error: {str(e)}")
        
        return []

    def verify_data_sources(self):
        """Verify all data sources are accessible"""
        print("\n--- STEP 2: Verifying Data Sources ---")
        
        # Check job cards
        self.check_job_cards()
        
        # Check timesheets
        self.check_timesheets()
        
        # Check materials
        self.check_materials()
        
        # Check stock movements
        self.check_stock_movements()

    def check_job_cards(self):
        """Check if job cards exist"""
        try:
            # Try to get job cards - this might be part of orders or separate endpoint
            response = self.session.get(f"{API_BASE}/job-cards")
            
            if response.status_code == 200:
                job_cards = response.json()
                self.log_result(
                    "Check Job Cards", 
                    True, 
                    f"Found {len(job_cards)} job cards in database"
                )
            elif response.status_code == 404:
                # Try alternative endpoint
                response = self.session.get(f"{API_BASE}/orders")
                if response.status_code == 200:
                    orders = response.json()
                    orders_with_job_cards = [o for o in orders if o.get('job_card_id') or o.get('current_stage') != 'order_entered']
                    self.log_result(
                        "Check Job Cards (via Orders)", 
                        len(orders_with_job_cards) > 0, 
                        f"Found {len(orders_with_job_cards)} orders with job card data"
                    )
                else:
                    self.log_result(
                        "Check Job Cards", 
                        False, 
                        "Job cards endpoint not found and orders endpoint failed"
                    )
            else:
                self.log_result(
                    "Check Job Cards", 
                    False, 
                    f"Job cards check failed: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Check Job Cards", False, f"Error: {str(e)}")

    def check_timesheets(self):
        """Check if timesheets exist"""
        try:
            response = self.session.get(f"{API_BASE}/payroll/timesheets")
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, dict) and 'data' in result:
                    timesheets = result['data']
                else:
                    timesheets = result
                
                approved_timesheets = [ts for ts in timesheets if ts.get('status') == 'approved']
                
                self.log_result(
                    "Check Timesheets", 
                    len(timesheets) > 0, 
                    f"Found {len(timesheets)} total timesheets, {len(approved_timesheets)} approved"
                )
            elif response.status_code == 404:
                # Try alternative endpoint
                response = self.session.get(f"{API_BASE}/payroll/timesheets/pending")
                if response.status_code == 200:
                    result = response.json()
                    timesheets = result.get('data', [])
                    self.log_result(
                        "Check Timesheets (Pending Only)", 
                        True, 
                        f"Found {len(timesheets)} pending timesheets (approved timesheets endpoint not accessible)"
                    )
                else:
                    self.log_result(
                        "Check Timesheets", 
                        False, 
                        "No timesheet endpoints accessible"
                    )
            else:
                self.log_result(
                    "Check Timesheets", 
                    False, 
                    f"Timesheets check failed: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Check Timesheets", False, f"Error: {str(e)}")

    def check_materials(self):
        """Check if materials exist"""
        try:
            response = self.session.get(f"{API_BASE}/materials")
            
            if response.status_code == 200:
                materials = response.json()
                self.log_result(
                    "Check Materials", 
                    len(materials) > 0, 
                    f"Found {len(materials)} materials in database"
                )
            else:
                self.log_result(
                    "Check Materials", 
                    False, 
                    f"Materials check failed: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Check Materials", False, f"Error: {str(e)}")

    def check_stock_movements(self):
        """Check if stock movements exist"""
        try:
            # Try different possible endpoints for stock movements
            endpoints_to_try = [
                "/stock/movements",
                "/stock/raw-materials",
                "/stock/raw-substrates"
            ]
            
            found_stock_data = False
            
            for endpoint in endpoints_to_try:
                try:
                    response = self.session.get(f"{API_BASE}{endpoint}")
                    
                    if response.status_code == 200:
                        result = response.json()
                        if isinstance(result, dict) and 'data' in result:
                            stock_data = result['data']
                        else:
                            stock_data = result
                        
                        if len(stock_data) > 0:
                            self.log_result(
                                f"Check Stock Data ({endpoint})", 
                                True, 
                                f"Found {len(stock_data)} stock records"
                            )
                            found_stock_data = True
                            break
                except:
                    continue
            
            if not found_stock_data:
                self.log_result(
                    "Check Stock Movements", 
                    False, 
                    "No stock movement data found in any endpoint"
                )
                
        except Exception as e:
            self.log_result("Check Stock Movements", False, f"Error: {str(e)}")

    def test_profitability_report_multiple_jobs(self):
        """Test POST /api/reports/profitability with multiple jobs mode"""
        print("\n--- STEP 3: Testing Profitability Report - Multiple Jobs Mode ---")
        
        try:
            # Test with multiple jobs mode (no filters, get all completed jobs)
            report_data = {
                "report_type": "multiple_jobs",
                "profit_threshold": 0,
                "include_all_completed": True
            }
            
            response = self.session.post(f"{API_BASE}/reports/profitability", json=report_data)
            
            if response.status_code == 200:
                result = response.json()
                
                # Check response structure
                if result.get('success'):
                    data = result.get('data', {})
                    
                    # Check for required fields (correct field names from backend)
                    required_fields = ['profitability_data', 'summary']
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if not missing_fields:
                        jobs = data.get('profitability_data', [])
                        summary = data.get('summary', {})
                        
                        self.log_result(
                            "Profitability Report - Multiple Jobs", 
                            True, 
                            f"Successfully generated profitability report",
                            f"Jobs analyzed: {len(jobs)}, Total revenue: ${summary.get('total_revenue', 0)}, Total net profit: ${summary.get('total_net_profit', 0)}"
                        )
                        
                        # Check individual job structure
                        if jobs:
                            job = jobs[0]
                            job_fields = ['order_id', 'order_number', 'job_revenue', 'total_production_cost', 'net_profit', 'np_percentage']
                            missing_job_fields = [field for field in job_fields if field not in job]
                            
                            if not missing_job_fields:
                                self.log_result(
                                    "Job Data Structure", 
                                    True, 
                                    "Job records have all required fields"
                                )
                            else:
                                self.log_result(
                                    "Job Data Structure", 
                                    False, 
                                    f"Job records missing fields: {missing_job_fields}"
                                )
                        
                        return data
                    else:
                        self.log_result(
                            "Profitability Report - Multiple Jobs", 
                            False, 
                            f"Report missing required fields: {missing_fields}",
                            f"Available fields: {list(data.keys())}"
                        )
                else:
                    self.log_result(
                        "Profitability Report - Multiple Jobs", 
                        False, 
                        "Report generation failed",
                        result.get('message', 'No error message')
                    )
            else:
                self.log_result(
                    "Profitability Report - Multiple Jobs", 
                    False, 
                    f"Report request failed: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Profitability Report - Multiple Jobs", False, f"Error: {str(e)}")
        
        return None

    def test_profitability_report_specific_orders(self, completed_orders):
        """Test profitability report with specific order IDs"""
        print("\n--- STEP 4: Testing Profitability Report - Specific Orders ---")
        
        if not completed_orders:
            self.log_result(
                "Profitability Report - Specific Orders", 
                False, 
                "No completed orders available for testing"
            )
            return
        
        try:
            # Use first few completed orders
            order_ids = [order.get('id') for order in completed_orders[:3] if order.get('id')]
            
            if not order_ids:
                self.log_result(
                    "Profitability Report - Specific Orders", 
                    False, 
                    "No valid order IDs found in completed orders"
                )
                return
            
            report_data = {
                "report_type": "specific_jobs",
                "order_ids": order_ids,
                "profit_threshold": 0
            }
            
            response = self.session.post(f"{API_BASE}/reports/profitability", json=report_data)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('success'):
                    data = result.get('data', {})
                    jobs = data.get('profitability_data', [])
                    
                    self.log_result(
                        "Profitability Report - Specific Orders", 
                        True, 
                        f"Successfully generated report for specific orders",
                        f"Requested {len(order_ids)} orders, got {len(jobs)} job records"
                    )
                    
                    # Verify we got data for the requested orders
                    returned_order_ids = [job.get('order_id') for job in jobs]
                    matched_orders = [oid for oid in order_ids if oid in returned_order_ids]
                    
                    self.log_result(
                        "Order ID Matching", 
                        len(matched_orders) > 0, 
                        f"Matched {len(matched_orders)} out of {len(order_ids)} requested orders"
                    )
                    
                else:
                    self.log_result(
                        "Profitability Report - Specific Orders", 
                        False, 
                        "Report generation failed for specific orders",
                        result.get('message', 'No error message')
                    )
            else:
                self.log_result(
                    "Profitability Report - Specific Orders", 
                    False, 
                    f"Specific orders report failed: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Profitability Report - Specific Orders", False, f"Error: {str(e)}")

    def analyze_missing_data(self):
        """Analyze what data might be missing for profitability calculations"""
        print("\n--- STEP 5: Analyzing Missing Data ---")
        
        # Check if we have the minimum data needed for profitability calculations
        missing_components = []
        
        # Check orders
        try:
            response = self.session.get(f"{API_BASE}/orders")
            if response.status_code == 200:
                orders = response.json()
                completed_orders = [o for o in orders if o.get('status') == 'completed' or o.get('current_stage') == 'cleared']
                if not completed_orders:
                    missing_components.append("No completed/cleared orders")
            else:
                missing_components.append("Cannot access orders")
        except:
            missing_components.append("Orders endpoint error")
        
        # Check if orders have required financial data
        try:
            response = self.session.get(f"{API_BASE}/orders")
            if response.status_code == 200:
                orders = response.json()
                if orders:
                    sample_order = orders[0]
                    financial_fields = ['total_amount', 'items']
                    missing_financial = [field for field in financial_fields if field not in sample_order]
                    if missing_financial:
                        missing_components.append(f"Orders missing financial fields: {missing_financial}")
        except:
            pass
        
        # Summary
        if missing_components:
            self.log_result(
                "Data Completeness Analysis", 
                False, 
                "Found missing data components for profitability calculations",
                "; ".join(missing_components)
            )
        else:
            self.log_result(
                "Data Completeness Analysis", 
                True, 
                "All basic data components appear to be available"
            )

    def print_test_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "="*80)
        print("PROFITABILITY REPORT TEST SUMMARY")
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
        successful_results = [r for r in self.test_results if r['success']]
        if successful_results:
            print("\n" + "="*60)
            print("SUCCESSFUL TESTS:")
            print("="*60)
            for result in successful_results:
                print(f"✅ {result['test']} - {result['message']}")
        
        print("\n" + "="*80)
        if success_rate == 100:
            print("🎉 PERFECT! 100% SUCCESS RATE ACHIEVED!")
        elif success_rate >= 80:
            print(f"✅ GOOD! {success_rate:.1f}% SUCCESS RATE")
        else:
            print(f"⚠️  NEEDS IMPROVEMENT: {success_rate:.1f}% SUCCESS RATE")
        print("="*80)

    def run_all_tests(self):
        """Run all profitability report tests"""
        print("Starting Profitability Report Testing Suite...")
        print(f"Backend URL: {BACKEND_URL}")
        
        # Authenticate first
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return
        
        # Run main test suite
        self.test_profitability_report_end_to_end()
        
        # Print summary
        self.print_test_summary()

if __name__ == "__main__":
    tester = ProfitabilityReportTester()
    tester.run_all_tests()