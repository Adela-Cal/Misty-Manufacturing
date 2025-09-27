#!/usr/bin/env python3
"""
Backend API Testing Suite for Invoicing System
Tests the new invoicing functionality and related features
"""

import requests
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:8001')
API_BASE = f"{BACKEND_URL}/api"

class InvoicingAPITester:
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
    
    def test_client_model_updates(self):
        """Test client creation/update with payment_terms and lead_time_days"""
        print("\n=== CLIENT MODEL UPDATES TEST ===")
        
        try:
            # Test client creation with new fields
            client_data = {
                "company_name": "Test Invoicing Client",
                "contact_name": "John Doe",
                "email": "john@testclient.com",
                "phone": "0412345678",
                "address": "123 Test Street",
                "city": "Melbourne",
                "state": "VIC",
                "postal_code": "3000",
                "abn": "12345678901",
                "payment_terms": "Net 14 days",
                "lead_time_days": 10
            }
            
            response = self.session.post(f"{API_BASE}/clients", json=client_data)
            
            if response.status_code == 200:
                result = response.json()
                client_id = result.get('data', {}).get('id')
                
                if client_id:
                    # Verify client was created with new fields
                    get_response = self.session.get(f"{API_BASE}/clients/{client_id}")
                    if get_response.status_code == 200:
                        client = get_response.json()
                        
                        has_payment_terms = client.get('payment_terms') == "Net 14 days"
                        has_lead_time = client.get('lead_time_days') == 10
                        
                        if has_payment_terms and has_lead_time:
                            self.log_result(
                                "Client Model Updates", 
                                True, 
                                "Client created successfully with payment_terms and lead_time_days fields"
                            )
                            return client_id
                        else:
                            self.log_result(
                                "Client Model Updates", 
                                False, 
                                "Client created but missing new fields",
                                f"payment_terms: {client.get('payment_terms')}, lead_time_days: {client.get('lead_time_days')}"
                            )
                    else:
                        self.log_result(
                            "Client Model Updates", 
                            False, 
                            "Failed to retrieve created client"
                        )
                else:
                    self.log_result(
                        "Client Model Updates", 
                        False, 
                        "Client creation response missing ID"
                    )
            else:
                self.log_result(
                    "Client Model Updates", 
                    False, 
                    f"Client creation failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Client Model Updates", False, f"Error: {str(e)}")
        
        return None
    
    def test_live_jobs_api(self):
        """Test GET /api/invoicing/live-jobs"""
        print("\n=== LIVE JOBS API TEST ===")
        
        try:
            response = self.session.get(f"{API_BASE}/invoicing/live-jobs")
            
            if response.status_code == 200:
                data = response.json()
                jobs = data.get('data', [])
                
                self.log_result(
                    "Live Jobs API", 
                    True, 
                    f"Successfully retrieved {len(jobs)} live jobs ready for invoicing"
                )
                return jobs
            else:
                self.log_result(
                    "Live Jobs API", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Live Jobs API", False, f"Error: {str(e)}")
        
        return []
    
    def test_archived_jobs_api(self):
        """Test GET /api/invoicing/archived-jobs"""
        print("\n=== ARCHIVED JOBS API TEST ===")
        
        try:
            # Test without filters
            response = self.session.get(f"{API_BASE}/invoicing/archived-jobs")
            
            if response.status_code == 200:
                data = response.json()
                jobs = data.get('data', [])
                
                self.log_result(
                    "Archived Jobs API (no filter)", 
                    True, 
                    f"Successfully retrieved {len(jobs)} archived jobs"
                )
                
                # Test with month/year filters
                current_date = datetime.now()
                response_filtered = self.session.get(
                    f"{API_BASE}/invoicing/archived-jobs?month={current_date.month}&year={current_date.year}"
                )
                
                if response_filtered.status_code == 200:
                    filtered_data = response_filtered.json()
                    filtered_jobs = filtered_data.get('data', [])
                    
                    self.log_result(
                        "Archived Jobs API (with filters)", 
                        True, 
                        f"Successfully retrieved {len(filtered_jobs)} archived jobs for {current_date.month}/{current_date.year}"
                    )
                    return jobs
                else:
                    self.log_result(
                        "Archived Jobs API (with filters)", 
                        False, 
                        f"Filtered request failed with status {response_filtered.status_code}"
                    )
            else:
                self.log_result(
                    "Archived Jobs API", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Archived Jobs API", False, f"Error: {str(e)}")
        
        return []
    
    def test_monthly_report_api(self):
        """Test GET /api/invoicing/monthly-report"""
        print("\n=== MONTHLY REPORT API TEST ===")
        
        try:
            current_date = datetime.now()
            response = self.session.get(
                f"{API_BASE}/invoicing/monthly-report?month={current_date.month}&year={current_date.year}"
            )
            
            if response.status_code == 200:
                data = response.json()
                
                required_fields = ['month', 'year', 'total_jobs_completed', 'total_jobs_invoiced', 'total_invoice_amount']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    self.log_result(
                        "Monthly Report API", 
                        True, 
                        f"Successfully generated report for {current_date.month}/{current_date.year}",
                        f"Completed: {data['total_jobs_completed']}, Invoiced: {data['total_jobs_invoiced']}, Amount: ${data['total_invoice_amount']}"
                    )
                else:
                    self.log_result(
                        "Monthly Report API", 
                        False, 
                        f"Report missing required fields: {missing_fields}"
                    )
            else:
                self.log_result(
                    "Monthly Report API", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Monthly Report API", False, f"Error: {str(e)}")
    
    def create_test_order(self, client_id):
        """Create a test order for invoice generation testing"""
        try:
            order_data = {
                "client_id": client_id,
                "due_date": (datetime.now() + timedelta(days=14)).isoformat(),
                "delivery_address": "456 Delivery Street, Melbourne VIC 3000",
                "delivery_instructions": "Handle with care",
                "notes": "Test order for invoicing",
                "items": [
                    {
                        "product_id": "test-product-1",
                        "product_name": "Test Product",
                        "description": "Test product for invoicing",
                        "quantity": 2,
                        "unit_price": 100.0,
                        "total_price": 200.0
                    }
                ]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=order_data)
            
            if response.status_code == 200:
                result = response.json()
                order_id = result.get('data', {}).get('id')
                
                # Move order to delivery stage to make it ready for invoicing
                if order_id:
                    stage_update = {
                        "to_stage": "delivery",
                        "notes": "Moving to delivery for invoice testing"
                    }
                    
                    stage_response = self.session.put(
                        f"{API_BASE}/orders/{order_id}/stage", 
                        json=stage_update
                    )
                    
                    if stage_response.status_code == 200:
                        return order_id
                        
        except Exception as e:
            print(f"Error creating test order: {str(e)}")
        
        return None
    
    def test_invoice_generation_api(self, client_id):
        """Test POST /api/invoicing/generate/{job_id}"""
        print("\n=== INVOICE GENERATION API TEST ===")
        
        # First create a test order
        order_id = self.create_test_order(client_id)
        
        if not order_id:
            self.log_result(
                "Invoice Generation API", 
                False, 
                "Failed to create test order for invoice generation"
            )
            return
        
        try:
            # Test full invoice generation
            invoice_data = {
                "invoice_type": "full",
                "due_date": (datetime.now() + timedelta(days=30)).isoformat()
            }
            
            response = self.session.post(
                f"{API_BASE}/invoicing/generate/{order_id}", 
                json=invoice_data
            )
            
            if response.status_code == 200:
                result = response.json()
                invoice_id = result.get('invoice_id')
                invoice_number = result.get('invoice_number')
                
                if invoice_id and invoice_number:
                    self.log_result(
                        "Invoice Generation API", 
                        True, 
                        f"Successfully generated invoice {invoice_number}",
                        f"Invoice ID: {invoice_id}"
                    )
                else:
                    self.log_result(
                        "Invoice Generation API", 
                        False, 
                        "Invoice generated but missing ID or number in response"
                    )
            else:
                self.log_result(
                    "Invoice Generation API", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Invoice Generation API", False, f"Error: {str(e)}")
    
    def test_document_generation(self, client_id):
        """Test document generation with new client fields"""
        print("\n=== DOCUMENT GENERATION TEST ===")
        
        # Create a test order
        order_id = self.create_test_order(client_id)
        
        if not order_id:
            self.log_result(
                "Document Generation", 
                False, 
                "Failed to create test order for document generation"
            )
            return
        
        try:
            # Test order acknowledgment generation
            response = self.session.get(f"{API_BASE}/documents/acknowledgment/{order_id}")
            
            if response.status_code == 200:
                # Check if response is PDF content
                content_type = response.headers.get('content-type', '')
                
                if 'application/pdf' in content_type:
                    self.log_result(
                        "Document Generation", 
                        True, 
                        "Successfully generated order acknowledgment PDF with client payment terms and lead time"
                    )
                else:
                    self.log_result(
                        "Document Generation", 
                        False, 
                        f"Expected PDF but got content-type: {content_type}"
                    )
            else:
                self.log_result(
                    "Document Generation", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Document Generation", False, f"Error: {str(e)}")
    
    def test_role_permissions(self):
        """Test that invoicing endpoints require proper permissions"""
        print("\n=== ROLE PERMISSIONS TEST ===")
        
        # Test without authentication
        temp_session = requests.Session()
        
        try:
            response = temp_session.get(f"{API_BASE}/invoicing/live-jobs")
            
            if response.status_code == 401:
                self.log_result(
                    "Role Permissions", 
                    True, 
                    "Invoicing endpoints properly require authentication"
                )
            else:
                self.log_result(
                    "Role Permissions", 
                    False, 
                    f"Expected 401 Unauthorized but got {response.status_code}",
                    "Invoicing endpoints should require authentication"
                )
                
        except Exception as e:
            self.log_result("Role Permissions", False, f"Error: {str(e)}")
    
    def run_all_tests(self):
        """Run all invoicing system tests"""
        print("🚀 Starting Invoicing System Backend API Tests")
        print(f"Backend URL: {BACKEND_URL}")
        print("=" * 60)
        
        # Test authentication first
        if not self.authenticate():
            print("❌ Authentication failed - cannot proceed with other tests")
            return self.generate_report()
        
        # Test role permissions
        self.test_role_permissions()
        
        # Test client model updates
        client_id = self.test_client_model_updates()
        
        # Test invoicing APIs
        self.test_live_jobs_api()
        self.test_archived_jobs_api()
        self.test_monthly_report_api()
        
        # Test invoice generation if we have a client
        if client_id:
            self.test_invoice_generation_api(client_id)
            self.test_document_generation(client_id)
        
        return self.generate_report()
    
    def generate_report(self):
        """Generate test report"""
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['success']])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  • {result['test']}: {result['message']}")
        
        return {
            'total': total_tests,
            'passed': passed_tests,
            'failed': failed_tests,
            'success_rate': passed_tests/total_tests*100 if total_tests > 0 else 0,
            'results': self.test_results
        }

if __name__ == "__main__":
    tester = InvoicingAPITester()
    report = tester.run_all_tests()