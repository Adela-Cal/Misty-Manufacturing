#!/usr/bin/env python3
"""
Job Card Performance Report Backend Testing Suite
Testing the Enhanced Job Card Performance Report endpoints as requested in review

ENDPOINTS TO TEST:
1. GET /api/stock/reports/job-card-performance - Main report endpoint
2. GET /api/stock/reports/job-card-performance/export-csv - CSV export endpoint

TEST SCENARIOS:
- Default date range (no params) - should default to last 30 days
- Custom date range with start_date and end_date parameters
- Response structure validation for all required fields
- CSV export functionality with proper headers and format
- Edge cases: empty results, invalid dates, etc.
"""

import requests
import json
import os
from datetime import datetime, timedelta, date
from dotenv import load_dotenv
import uuid
import csv
from io import StringIO

# Load environment variables
load_dotenv('/app/frontend/.env')

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:8001')
API_BASE = f"{BACKEND_URL}/api"

class JobCardPerformanceTester:
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

    def test_job_card_performance_default_date_range(self):
        """Test job card performance report with default date range (no params)"""
        print("\n" + "="*80)
        print("TEST 1: JOB CARD PERFORMANCE REPORT - DEFAULT DATE RANGE")
        print("Testing GET /api/stock/reports/job-card-performance with no date parameters")
        print("Should default to last 30 days")
        print("="*80)
        
        try:
            response = self.session.get(f"{API_BASE}/stock/reports/job-card-performance")
            
            if response.status_code == 200:
                result = response.json()
                
                # Verify it's a StandardResponse format
                if not result.get("success"):
                    self.log_result(
                        "Job Card Performance - Default Range", 
                        False, 
                        "Response success field is not True",
                        f"Response: {result}"
                    )
                    return
                
                data = result.get("data", {})
                
                # Check required top-level fields
                required_fields = ["report_period", "job_cards", "averages", "job_type_breakdown", "client_performance"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_result(
                        "Job Card Performance - Default Range", 
                        False, 
                        f"Missing required fields: {missing_fields}",
                        f"Available fields: {list(data.keys())}"
                    )
                    return
                
                # Verify report_period structure
                report_period = data.get("report_period", {})
                period_fields = ["start_date", "end_date", "days"]
                missing_period_fields = [field for field in period_fields if field not in report_period]
                
                if missing_period_fields:
                    self.log_result(
                        "Job Card Performance - Default Range", 
                        False, 
                        f"Report period missing fields: {missing_period_fields}"
                    )
                    return
                
                # Verify default date range is approximately 30 days
                days = report_period.get("days", 0)
                if days < 28 or days > 32:  # Allow some flexibility
                    self.log_result(
                        "Job Card Performance - Default Range", 
                        False, 
                        f"Default date range should be ~30 days, got {days} days"
                    )
                    return
                
                # Check data structure
                job_cards = data.get("job_cards", [])
                averages = data.get("averages", {})
                job_type_breakdown = data.get("job_type_breakdown", [])
                client_performance = data.get("client_performance", [])
                
                self.log_result(
                    "Job Card Performance - Default Range", 
                    True, 
                    f"Successfully generated report with default 30-day range",
                    f"Period: {days} days, Job cards: {len(job_cards)}, Job types: {len(job_type_breakdown)}, Clients: {len(client_performance)}"
                )
                
                # Store data for further validation
                self.validate_job_cards_structure(job_cards)
                self.validate_averages_structure(averages)
                self.validate_job_type_breakdown_structure(job_type_breakdown)
                self.validate_client_performance_structure(client_performance)
                
            else:
                self.log_result(
                    "Job Card Performance - Default Range", 
                    False, 
                    f"Failed to generate report: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Job Card Performance - Default Range", False, f"Error: {str(e)}")

    def test_job_card_performance_custom_date_range(self):
        """Test job card performance report with custom date range"""
        print("\n" + "="*80)
        print("TEST 2: JOB CARD PERFORMANCE REPORT - CUSTOM DATE RANGE")
        print("Testing GET /api/stock/reports/job-card-performance with start_date and end_date")
        print("="*80)
        
        try:
            # Use a specific date range
            start_date = "2024-01-01T00:00:00Z"
            end_date = "2024-12-31T23:59:59Z"
            
            response = self.session.get(
                f"{API_BASE}/stock/reports/job-card-performance",
                params={
                    "start_date": start_date,
                    "end_date": end_date
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                data = result.get("data", {})
                
                # Verify the date range matches what we requested
                report_period = data.get("report_period", {})
                returned_start = report_period.get("start_date")
                returned_end = report_period.get("end_date")
                
                if returned_start != start_date or returned_end != end_date:
                    self.log_result(
                        "Job Card Performance - Custom Range", 
                        False, 
                        f"Date range mismatch. Expected: {start_date} to {end_date}, Got: {returned_start} to {returned_end}"
                    )
                    return
                
                # Verify days calculation
                expected_days = (datetime(2024, 12, 31) - datetime(2024, 1, 1)).days
                actual_days = report_period.get("days", 0)
                
                if abs(actual_days - expected_days) > 1:  # Allow 1 day difference for calculation variations
                    self.log_result(
                        "Job Card Performance - Custom Range", 
                        False, 
                        f"Days calculation incorrect. Expected ~{expected_days}, got {actual_days}"
                    )
                    return
                
                job_cards = data.get("job_cards", [])
                
                self.log_result(
                    "Job Card Performance - Custom Range", 
                    True, 
                    f"Successfully generated report with custom date range",
                    f"Period: {actual_days} days ({returned_start} to {returned_end}), Job cards: {len(job_cards)}"
                )
                
            else:
                self.log_result(
                    "Job Card Performance - Custom Range", 
                    False, 
                    f"Failed to generate report: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Job Card Performance - Custom Range", False, f"Error: {str(e)}")

    def validate_job_cards_structure(self, job_cards):
        """Validate job cards array structure"""
        try:
            if not isinstance(job_cards, list):
                self.log_result(
                    "Job Cards Structure Validation", 
                    False, 
                    "job_cards should be an array"
                )
                return
            
            if len(job_cards) == 0:
                self.log_result(
                    "Job Cards Structure Validation", 
                    True, 
                    "No job cards in date range (empty result is valid)"
                )
                return
            
            # Check first job card structure
            job_card = job_cards[0]
            required_job_fields = [
                "order_number", "order_id", "client_id", "client_name", "product_types",
                "created_at", "due_date", "completed_at", "is_on_time",
                "total_time_hours", "time_by_stage",
                "material_used_kg", "expected_material_kg", "material_excess_kg", "waste_percentage",
                "material_details", "stock_entries", "total_stock_produced", "ordered_quantity", "stock_entry_count"
            ]
            
            missing_job_fields = [field for field in required_job_fields if field not in job_card]
            
            if missing_job_fields:
                self.log_result(
                    "Job Cards Structure Validation", 
                    False, 
                    f"Job card missing required fields: {missing_job_fields}",
                    f"Available fields: {list(job_card.keys())}"
                )
                return
            
            # Validate data types
            validation_errors = []
            
            if not isinstance(job_card.get("product_types"), list):
                validation_errors.append("product_types should be array")
            
            if not isinstance(job_card.get("time_by_stage"), dict):
                validation_errors.append("time_by_stage should be object")
            
            if not isinstance(job_card.get("material_details"), list):
                validation_errors.append("material_details should be array")
            
            if not isinstance(job_card.get("stock_entries"), list):
                validation_errors.append("stock_entries should be array")
            
            if not isinstance(job_card.get("is_on_time"), bool):
                validation_errors.append("is_on_time should be boolean")
            
            if validation_errors:
                self.log_result(
                    "Job Cards Structure Validation", 
                    False, 
                    f"Data type validation errors: {', '.join(validation_errors)}"
                )
                return
            
            self.log_result(
                "Job Cards Structure Validation", 
                True, 
                f"Job cards structure is valid",
                f"Validated {len(job_cards)} job cards with all required fields"
            )
            
        except Exception as e:
            self.log_result("Job Cards Structure Validation", False, f"Error: {str(e)}")

    def validate_averages_structure(self, averages):
        """Validate averages object structure"""
        try:
            required_avg_fields = [
                "total_jobs_completed", "jobs_on_time", "jobs_delayed",
                "efficiency_score_percentage",
                "total_time_all_jobs_hours", "average_time_per_job_hours",
                "total_material_used_kg", "total_material_excess_kg", "overall_waste_percentage",
                "average_material_used_per_job_kg", "average_waste_per_job_kg",
                "total_stock_produced", "average_stock_entries_per_job", "average_stock_quantity_per_job"
            ]
            
            missing_avg_fields = [field for field in required_avg_fields if field not in averages]
            
            if missing_avg_fields:
                self.log_result(
                    "Averages Structure Validation", 
                    False, 
                    f"Averages missing required fields: {missing_avg_fields}",
                    f"Available fields: {list(averages.keys())}"
                )
                return
            
            # Validate numeric fields
            numeric_fields = [
                "total_jobs_completed", "jobs_on_time", "jobs_delayed",
                "efficiency_score_percentage", "total_time_all_jobs_hours", "average_time_per_job_hours",
                "total_material_used_kg", "total_material_excess_kg", "overall_waste_percentage",
                "average_material_used_per_job_kg", "average_waste_per_job_kg",
                "total_stock_produced", "average_stock_entries_per_job", "average_stock_quantity_per_job"
            ]
            
            non_numeric_errors = []
            for field in numeric_fields:
                value = averages.get(field)
                if not isinstance(value, (int, float)):
                    non_numeric_errors.append(f"{field}: {type(value)}")
            
            if non_numeric_errors:
                self.log_result(
                    "Averages Structure Validation", 
                    False, 
                    f"Non-numeric values in averages: {', '.join(non_numeric_errors)}"
                )
                return
            
            self.log_result(
                "Averages Structure Validation", 
                True, 
                f"Averages structure is valid with all required numeric fields"
            )
            
        except Exception as e:
            self.log_result("Averages Structure Validation", False, f"Error: {str(e)}")

    def validate_job_type_breakdown_structure(self, job_type_breakdown):
        """Validate job type breakdown array structure"""
        try:
            if not isinstance(job_type_breakdown, list):
                self.log_result(
                    "Job Type Breakdown Validation", 
                    False, 
                    "job_type_breakdown should be an array"
                )
                return
            
            if len(job_type_breakdown) == 0:
                self.log_result(
                    "Job Type Breakdown Validation", 
                    True, 
                    "No job types in breakdown (empty result is valid)"
                )
                return
            
            # Check first breakdown entry structure
            breakdown = job_type_breakdown[0]
            required_breakdown_fields = [
                "product_type", "job_count", "total_time_hours", "average_time_per_job",
                "total_material_used_kg", "total_excess_kg", "waste_percentage",
                "jobs_on_time", "jobs_delayed", "efficiency_percentage"
            ]
            
            missing_breakdown_fields = [field for field in required_breakdown_fields if field not in breakdown]
            
            if missing_breakdown_fields:
                self.log_result(
                    "Job Type Breakdown Validation", 
                    False, 
                    f"Job type breakdown missing fields: {missing_breakdown_fields}",
                    f"Available fields: {list(breakdown.keys())}"
                )
                return
            
            self.log_result(
                "Job Type Breakdown Validation", 
                True, 
                f"Job type breakdown structure is valid",
                f"Validated {len(job_type_breakdown)} job type entries"
            )
            
        except Exception as e:
            self.log_result("Job Type Breakdown Validation", False, f"Error: {str(e)}")

    def validate_client_performance_structure(self, client_performance):
        """Validate client performance array structure"""
        try:
            if not isinstance(client_performance, list):
                self.log_result(
                    "Client Performance Validation", 
                    False, 
                    "client_performance should be an array"
                )
                return
            
            if len(client_performance) == 0:
                self.log_result(
                    "Client Performance Validation", 
                    True, 
                    "No clients in performance data (empty result is valid)"
                )
                return
            
            # Check first client performance entry structure
            client = client_performance[0]
            required_client_fields = [
                "client_id", "client_name", "job_count", "total_time_hours", "average_time_per_job",
                "total_material_used_kg", "total_excess_kg", "waste_percentage",
                "jobs_on_time", "jobs_delayed", "efficiency_percentage"
            ]
            
            missing_client_fields = [field for field in required_client_fields if field not in client]
            
            if missing_client_fields:
                self.log_result(
                    "Client Performance Validation", 
                    False, 
                    f"Client performance missing fields: {missing_client_fields}",
                    f"Available fields: {list(client.keys())}"
                )
                return
            
            self.log_result(
                "Client Performance Validation", 
                True, 
                f"Client performance structure is valid",
                f"Validated {len(client_performance)} client entries"
            )
            
        except Exception as e:
            self.log_result("Client Performance Validation", False, f"Error: {str(e)}")

    def test_csv_export_functionality(self):
        """Test CSV export endpoint"""
        print("\n" + "="*80)
        print("TEST 3: CSV EXPORT FUNCTIONALITY")
        print("Testing GET /api/stock/reports/job-card-performance/export-csv")
        print("="*80)
        
        try:
            # Test CSV export with date range
            start_date = "2024-01-01T00:00:00Z"
            end_date = "2024-12-31T23:59:59Z"
            
            response = self.session.get(
                f"{API_BASE}/stock/reports/job-card-performance/export-csv",
                params={
                    "start_date": start_date,
                    "end_date": end_date
                }
            )
            
            if response.status_code == 200:
                # Check response headers
                content_type = response.headers.get('content-type', '')
                content_disposition = response.headers.get('content-disposition', '')
                
                if 'text/csv' not in content_type:
                    self.log_result(
                        "CSV Export - Content Type", 
                        False, 
                        f"Expected text/csv content type, got: {content_type}"
                    )
                    return
                
                if 'attachment' not in content_disposition or 'filename=' not in content_disposition:
                    self.log_result(
                        "CSV Export - Headers", 
                        False, 
                        f"Invalid content disposition header: {content_disposition}"
                    )
                    return
                
                # Validate CSV content
                csv_content = response.text
                self.validate_csv_content(csv_content)
                
            else:
                self.log_result(
                    "CSV Export Functionality", 
                    False, 
                    f"CSV export failed: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("CSV Export Functionality", False, f"Error: {str(e)}")

    def validate_csv_content(self, csv_content):
        """Validate CSV file content and structure"""
        try:
            lines = csv_content.strip().split('\n')
            
            if len(lines) < 10:  # Should have headers and some content
                self.log_result(
                    "CSV Content Validation", 
                    False, 
                    f"CSV content too short: {len(lines)} lines"
                )
                return
            
            # Check for required sections
            required_sections = [
                "Job Card Performance Report",
                "SUMMARY METRICS", 
                "JOB TYPE BREAKDOWN",
                "CLIENT PERFORMANCE",
                "DETAILED JOB CARDS"
            ]
            
            missing_sections = []
            for section in required_sections:
                if section not in csv_content:
                    missing_sections.append(section)
            
            if missing_sections:
                self.log_result(
                    "CSV Content Validation", 
                    False, 
                    f"CSV missing required sections: {missing_sections}"
                )
                return
            
            # Try to parse as CSV to ensure it's valid
            try:
                csv_reader = csv.reader(StringIO(csv_content))
                rows = list(csv_reader)
                
                if len(rows) < 5:
                    self.log_result(
                        "CSV Content Validation", 
                        False, 
                        f"CSV has too few rows: {len(rows)}"
                    )
                    return
                
            except csv.Error as e:
                self.log_result(
                    "CSV Content Validation", 
                    False, 
                    f"CSV parsing error: {str(e)}"
                )
                return
            
            self.log_result(
                "CSV Content Validation", 
                True, 
                f"CSV content is valid and parseable",
                f"Total lines: {len(lines)}, Total rows: {len(rows)}, All required sections present"
            )
            
        except Exception as e:
            self.log_result("CSV Content Validation", False, f"Error: {str(e)}")

    def test_empty_result_scenario(self):
        """Test with date range that should have no completed orders"""
        print("\n" + "="*80)
        print("TEST 4: EMPTY RESULT SCENARIO")
        print("Testing with future date range that should have no data")
        print("="*80)
        
        try:
            # Use future date range
            start_date = "2025-01-01T00:00:00Z"
            end_date = "2025-01-31T23:59:59Z"
            
            response = self.session.get(
                f"{API_BASE}/stock/reports/job-card-performance",
                params={
                    "start_date": start_date,
                    "end_date": end_date
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                data = result.get("data", {})
                
                # Should return valid structure but with empty arrays
                job_cards = data.get("job_cards", [])
                averages = data.get("averages", {})
                job_type_breakdown = data.get("job_type_breakdown", [])
                client_performance = data.get("client_performance", [])
                
                # Check that arrays are empty
                if len(job_cards) != 0:
                    self.log_result(
                        "Empty Result Scenario", 
                        False, 
                        f"Expected empty job_cards, got {len(job_cards)} entries"
                    )
                    return
                
                if len(job_type_breakdown) != 0:
                    self.log_result(
                        "Empty Result Scenario", 
                        False, 
                        f"Expected empty job_type_breakdown, got {len(job_type_breakdown)} entries"
                    )
                    return
                
                if len(client_performance) != 0:
                    self.log_result(
                        "Empty Result Scenario", 
                        False, 
                        f"Expected empty client_performance, got {len(client_performance)} entries"
                    )
                    return
                
                # Check that averages show zero values
                total_jobs = averages.get("total_jobs_completed", -1)
                if total_jobs != 0:
                    self.log_result(
                        "Empty Result Scenario", 
                        False, 
                        f"Expected 0 total jobs, got {total_jobs}"
                    )
                    return
                
                self.log_result(
                    "Empty Result Scenario", 
                    True, 
                    f"Correctly handled empty result scenario",
                    f"All arrays empty, total jobs: {total_jobs}"
                )
                
            else:
                self.log_result(
                    "Empty Result Scenario", 
                    False, 
                    f"Failed to handle empty scenario: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Empty Result Scenario", False, f"Error: {str(e)}")

    def test_invalid_date_formats(self):
        """Test with invalid date formats"""
        print("\n" + "="*80)
        print("TEST 5: INVALID DATE FORMATS")
        print("Testing error handling for invalid date parameters")
        print("="*80)
        
        try:
            # Test with invalid date format
            response = self.session.get(
                f"{API_BASE}/stock/reports/job-card-performance",
                params={
                    "start_date": "invalid-date",
                    "end_date": "2024-12-31T23:59:59Z"
                }
            )
            
            # Should return error status (400, 422, or 500)
            if response.status_code in [400, 422, 500]:
                self.log_result(
                    "Invalid Date Formats", 
                    True, 
                    f"Correctly handled invalid date format with status {response.status_code}"
                )
            else:
                self.log_result(
                    "Invalid Date Formats", 
                    False, 
                    f"Expected error status for invalid date, got {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Invalid Date Formats", False, f"Error: {str(e)}")

    def print_test_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "="*80)
        print("JOB CARD PERFORMANCE REPORT TEST SUMMARY")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        # Show individual test results
        print("\n" + "="*60)
        print("DETAILED TEST RESULTS:")
        print("="*60)
        
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test']}")
            if not result['success'] and result['details']:
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
            print("🎉 PERFECT! 100% SUCCESS RATE ACHIEVED!")
        elif success_rate >= 90:
            print(f"🎯 EXCELLENT! {success_rate:.1f}% SUCCESS RATE")
        elif success_rate >= 80:
            print(f"✅ GOOD! {success_rate:.1f}% SUCCESS RATE")
        else:
            print(f"⚠️  NEEDS IMPROVEMENT: {success_rate:.1f}% SUCCESS RATE")
        print("="*80)

    def run_comprehensive_tests(self):
        """Run all job card performance report tests"""
        print("\n" + "="*80)
        print("ENHANCED JOB CARD PERFORMANCE REPORT TESTING")
        print("Testing backend endpoints for comprehensive metrics")
        print("="*80)
        
        # Step 1: Authenticate
        if not self.authenticate():
            print("❌ Authentication failed - cannot proceed with tests")
            return
        
        # Step 2: Run all tests
        self.test_job_card_performance_default_date_range()
        self.test_job_card_performance_custom_date_range()
        self.test_csv_export_functionality()
        self.test_empty_result_scenario()
        self.test_invalid_date_formats()
        
        # Step 3: Print comprehensive summary
        self.print_test_summary()

if __name__ == "__main__":
    tester = JobCardPerformanceTester()
    tester.run_comprehensive_tests()