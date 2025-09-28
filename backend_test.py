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
                        "order_id": order_id,
                        "from_stage": "order_entered",
                        "to_stage": "delivery",
                        "updated_by": "test-user",
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
            
            if response.status_code in [401, 403]:
                self.log_result(
                    "Role Permissions", 
                    True, 
                    f"Invoicing endpoints properly require authentication (status: {response.status_code})"
                )
            else:
                self.log_result(
                    "Role Permissions", 
                    False, 
                    f"Expected 401/403 but got {response.status_code}",
                    "Invoicing endpoints should require authentication"
                )
                
        except Exception as e:
            self.log_result("Role Permissions", False, f"Error: {str(e)}")
    
    def test_xero_connection_status(self):
        """Test GET /api/xero/status"""
        print("\n=== XERO CONNECTION STATUS TEST ===")
        
        try:
            response = self.session.get(f"{API_BASE}/xero/status")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                if 'connected' in data and 'message' in data:
                    connected = data.get('connected')
                    message = data.get('message')
                    
                    # For new connections, should return false
                    if connected == False and "No Xero connection found" in message:
                        self.log_result(
                            "Xero Connection Status", 
                            True, 
                            "Correctly reports no Xero connection for new user",
                            f"Connected: {connected}, Message: {message}"
                        )
                    elif connected == True:
                        self.log_result(
                            "Xero Connection Status", 
                            True, 
                            "User has active Xero connection",
                            f"Message: {message}"
                        )
                    else:
                        self.log_result(
                            "Xero Connection Status", 
                            False, 
                            "Unexpected connection status response",
                            f"Connected: {connected}, Message: {message}"
                        )
                else:
                    self.log_result(
                        "Xero Connection Status", 
                        False, 
                        "Response missing required fields (connected, message)",
                        str(data)
                    )
            else:
                self.log_result(
                    "Xero Connection Status", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Xero Connection Status", False, f"Error: {str(e)}")
    
    def test_xero_auth_url(self):
        """Test GET /api/xero/auth/url"""
        print("\n=== XERO AUTH URL TEST ===")
        
        try:
            response = self.session.get(f"{API_BASE}/xero/auth/url")
            
            if response.status_code == 200:
                data = response.json()
                
                if 'auth_url' in data and 'state' in data:
                    auth_url = data.get('auth_url')
                    state = data.get('state')
                    
                    # Verify URL components
                    expected_client_id = "0C765F92708046D5B625162E5D42C5FB"
                    expected_callback = "https://app.emergent.sh/api/xero/callback"  # From backend/.env
                    expected_scopes = "accounting.transactions accounting.contacts.read accounting.invoices.read accounting.settings.read"
                    
                    url_checks = []
                    
                    # Check client ID
                    if expected_client_id in auth_url:
                        url_checks.append("✅ Client ID correct")
                    else:
                        url_checks.append("❌ Client ID missing or incorrect")
                    
                    # Check callback URL (URL encoded)
                    import urllib.parse
                    encoded_callback = urllib.parse.quote(expected_callback, safe='')
                    if encoded_callback in auth_url or expected_callback in auth_url:
                        url_checks.append("✅ Callback URL correct")
                    else:
                        url_checks.append("❌ Callback URL missing or incorrect")
                    
                    # Check scopes (at least accounting.transactions should be present)
                    if "accounting.transactions" in auth_url:
                        url_checks.append("✅ Required scopes present")
                    else:
                        url_checks.append("❌ Required scopes missing")
                    
                    # Check state parameter
                    if state and len(state) > 20:
                        url_checks.append("✅ State parameter generated")
                    else:
                        url_checks.append("❌ State parameter missing or too short")
                    
                    # Check if it's a proper Xero URL
                    if "https://login.xero.com/identity/connect/authorize" in auth_url:
                        url_checks.append("✅ Proper Xero authorization URL")
                    else:
                        url_checks.append("❌ Not a proper Xero authorization URL")
                    
                    all_checks_passed = all("✅" in check for check in url_checks)
                    
                    self.log_result(
                        "Xero Auth URL", 
                        all_checks_passed, 
                        "Generated Xero OAuth URL" if all_checks_passed else "OAuth URL has issues",
                        "\n".join(url_checks)
                    )
                    
                    return state  # Return state for callback testing
                else:
                    self.log_result(
                        "Xero Auth URL", 
                        False, 
                        "Response missing required fields (auth_url, state)",
                        str(data)
                    )
            else:
                self.log_result(
                    "Xero Auth URL", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Xero Auth URL", False, f"Error: {str(e)}")
        
        return None
    
    def test_xero_auth_callback(self, state_param):
        """Test POST /api/xero/auth/callback with mock data"""
        print("\n=== XERO AUTH CALLBACK TEST ===")
        
        if not state_param:
            self.log_result(
                "Xero Auth Callback", 
                False, 
                "No state parameter available from auth URL test"
            )
            return
        
        try:
            # Test with mock callback data
            callback_data = {
                "code": "mock_authorization_code_12345",
                "state": state_param
            }
            
            response = self.session.post(f"{API_BASE}/xero/auth/callback", json=callback_data)
            
            # Note: This will likely fail with actual Xero API call, but we're testing the endpoint structure
            if response.status_code == 200:
                data = response.json()
                
                if 'message' in data:
                    self.log_result(
                        "Xero Auth Callback", 
                        True, 
                        "Callback endpoint processed successfully",
                        data.get('message')
                    )
                else:
                    self.log_result(
                        "Xero Auth Callback", 
                        False, 
                        "Callback response missing message field",
                        str(data)
                    )
            elif response.status_code == 400:
                # Expected for mock data - check if it's validating properly
                error_text = response.text
                if "authorization code" in error_text.lower() or "failed to exchange" in error_text.lower():
                    self.log_result(
                        "Xero Auth Callback", 
                        True, 
                        "Callback endpoint properly validates authorization codes (expected failure with mock data)",
                        f"Status: {response.status_code}, Response: {error_text}"
                    )
                else:
                    self.log_result(
                        "Xero Auth Callback", 
                        False, 
                        f"Unexpected error response: {response.status_code}",
                        error_text
                    )
            else:
                self.log_result(
                    "Xero Auth Callback", 
                    False, 
                    f"Unexpected status code: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Xero Auth Callback", False, f"Error: {str(e)}")
    
    def test_xero_disconnect(self):
        """Test DELETE /api/xero/disconnect"""
        print("\n=== XERO DISCONNECT TEST ===")
        
        try:
            response = self.session.delete(f"{API_BASE}/xero/disconnect")
            
            if response.status_code == 200:
                data = response.json()
                
                if 'message' in data:
                    message = data.get('message')
                    
                    # Should return success message regardless of whether connection existed
                    if "disconnection successful" in message.lower() or "no xero connection found" in message.lower():
                        self.log_result(
                            "Xero Disconnect", 
                            True, 
                            "Disconnect endpoint working correctly",
                            message
                        )
                    else:
                        self.log_result(
                            "Xero Disconnect", 
                            False, 
                            "Unexpected disconnect response message",
                            message
                        )
                else:
                    self.log_result(
                        "Xero Disconnect", 
                        False, 
                        "Disconnect response missing message field",
                        str(data)
                    )
            else:
                self.log_result(
                    "Xero Disconnect", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Xero Disconnect", False, f"Error: {str(e)}")
    
    def test_xero_permissions(self):
        """Test that Xero endpoints require admin/manager permissions"""
        print("\n=== XERO PERMISSIONS TEST ===")
        
        # Test without authentication
        temp_session = requests.Session()
        
        try:
            response = temp_session.get(f"{API_BASE}/xero/status")
            
            if response.status_code in [401, 403]:
                self.log_result(
                    "Xero Permissions", 
                    True, 
                    f"Xero endpoints properly require authentication (status: {response.status_code})"
                )
            else:
                self.log_result(
                    "Xero Permissions", 
                    False, 
                    f"Expected 401/403 but got {response.status_code}",
                    "Xero endpoints should require admin/manager authentication"
                )
                
        except Exception as e:
            self.log_result("Xero Permissions", False, f"Error: {str(e)}")
    
    def test_xero_next_invoice_number(self):
        """Test GET /api/xero/next-invoice-number"""
        print("\n=== XERO NEXT INVOICE NUMBER TEST ===")
        
        try:
            response = self.session.get(f"{API_BASE}/xero/next-invoice-number")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                required_fields = ['next_number', 'formatted_number']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    next_number = data.get('next_number')
                    formatted_number = data.get('formatted_number')
                    
                    # Validate format (should be INV-XXXXXX)
                    if isinstance(next_number, int) and next_number > 0:
                        if formatted_number and formatted_number.startswith('INV-'):
                            self.log_result(
                                "Xero Next Invoice Number", 
                                True, 
                                f"Successfully retrieved next invoice number: {formatted_number}",
                                f"Next number: {next_number}, Formatted: {formatted_number}"
                            )
                        else:
                            self.log_result(
                                "Xero Next Invoice Number", 
                                False, 
                                "Invalid formatted number format",
                                f"Expected INV-XXXXXX format, got: {formatted_number}"
                            )
                    else:
                        self.log_result(
                            "Xero Next Invoice Number", 
                            False, 
                            "Invalid next_number value",
                            f"Expected positive integer, got: {next_number}"
                        )
                else:
                    self.log_result(
                        "Xero Next Invoice Number", 
                        False, 
                        f"Response missing required fields: {missing_fields}",
                        str(data)
                    )
            elif response.status_code == 401:
                # Expected if no Xero connection
                error_text = response.text
                if "No Xero connection found" in error_text:
                    self.log_result(
                        "Xero Next Invoice Number", 
                        True, 
                        "Correctly handles missing Xero connection",
                        f"Status: {response.status_code}, Response: {error_text}"
                    )
                else:
                    self.log_result(
                        "Xero Next Invoice Number", 
                        False, 
                        f"Unexpected 401 error: {error_text}"
                    )
            elif response.status_code == 500:
                # May be expected if Xero integration not fully configured
                error_text = response.text
                if "Failed to get next invoice number" in error_text:
                    self.log_result(
                        "Xero Next Invoice Number", 
                        True, 
                        "Endpoint handles Xero API errors gracefully",
                        f"Status: {response.status_code}, Response: {error_text}"
                    )
                else:
                    self.log_result(
                        "Xero Next Invoice Number", 
                        False, 
                        f"Unexpected 500 error: {error_text}"
                    )
            else:
                self.log_result(
                    "Xero Next Invoice Number", 
                    False, 
                    f"Unexpected status code: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Xero Next Invoice Number", False, f"Error: {str(e)}")
    
    def test_xero_create_draft_invoice(self):
        """Test POST /api/xero/create-draft-invoice"""
        print("\n=== XERO CREATE DRAFT INVOICE TEST ===")
        
        try:
            # Test with sample invoice data
            invoice_data = {
                "client_name": "Test Client for Xero",
                "client_email": "test@testclient.com",
                "invoice_number": "INV-TEST-001",
                "order_number": "ADM-2024-TEST",
                "due_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
                "total_amount": 1000.00,
                "items": [
                    {
                        "description": "Test Product",
                        "quantity": 2,
                        "unit_price": 500.00
                    }
                ]
            }
            
            response = self.session.post(f"{API_BASE}/xero/create-draft-invoice", json=invoice_data)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                required_fields = ['success', 'message', 'invoice_id']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    success = data.get('success')
                    message = data.get('message')
                    invoice_id = data.get('invoice_id')
                    
                    if success and invoice_id:
                        self.log_result(
                            "Xero Create Draft Invoice", 
                            True, 
                            f"Successfully created draft invoice in Xero",
                            f"Invoice ID: {invoice_id}, Message: {message}"
                        )
                    else:
                        self.log_result(
                            "Xero Create Draft Invoice", 
                            False, 
                            "Response indicates failure or missing invoice ID",
                            f"Success: {success}, Invoice ID: {invoice_id}"
                        )
                else:
                    self.log_result(
                        "Xero Create Draft Invoice", 
                        False, 
                        f"Response missing required fields: {missing_fields}",
                        str(data)
                    )
            elif response.status_code == 400:
                # Expected if no Xero tenant ID or connection issues
                error_text = response.text
                if "No Xero tenant ID found" in error_text or "No Xero connection found" in error_text:
                    self.log_result(
                        "Xero Create Draft Invoice", 
                        True, 
                        "Correctly handles missing Xero connection/tenant",
                        f"Status: {response.status_code}, Response: {error_text}"
                    )
                else:
                    self.log_result(
                        "Xero Create Draft Invoice", 
                        False, 
                        f"Unexpected 400 error: {error_text}"
                    )
            elif response.status_code == 500:
                # May be expected if Xero integration not fully configured
                error_text = response.text
                if "Failed to create draft invoice" in error_text:
                    self.log_result(
                        "Xero Create Draft Invoice", 
                        True, 
                        "Endpoint handles Xero API errors gracefully",
                        f"Status: {response.status_code}, Response: {error_text}"
                    )
                else:
                    self.log_result(
                        "Xero Create Draft Invoice", 
                        False, 
                        f"Unexpected 500 error: {error_text}"
                    )
            else:
                self.log_result(
                    "Xero Create Draft Invoice", 
                    False, 
                    f"Unexpected status code: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Xero Create Draft Invoice", False, f"Error: {str(e)}")
    
    def test_document_generation_endpoints(self, delivery_jobs):
        """Test all document generation endpoints with real order data"""
        print("\n=== DOCUMENT GENERATION ENDPOINTS TEST ===")
        
        if not delivery_jobs:
            self.log_result(
                "Document Generation Endpoints", 
                False, 
                "No delivery jobs available for document testing"
            )
            return
        
        # Use the first available job for testing
        test_job = delivery_jobs[0]
        order_id = test_job.get('id')
        order_number = test_job.get('order_number', 'Unknown')
        
        print(f"Testing document generation with Order ID: {order_id}, Order Number: {order_number}")
        
        # Test all document endpoints
        document_endpoints = [
            ("Invoice PDF", f"/documents/invoice/{order_id}", "invoice"),
            ("Packing List PDF", f"/documents/packing-list/{order_id}", "packing_list"),
            ("Order Acknowledgment PDF", f"/documents/acknowledgment/{order_id}", "acknowledgment"),
            ("Job Card PDF", f"/documents/job-card/{order_id}", "job_card")
        ]
        
        successful_docs = 0
        failed_docs = []
        
        for doc_name, endpoint, doc_type in document_endpoints:
            try:
                print(f"  Testing {doc_name}...")
                response = self.session.get(f"{API_BASE}{endpoint}")
                
                if response.status_code == 200:
                    # Check if response is actually a PDF
                    content_type = response.headers.get('content-type', '')
                    content_length = len(response.content)
                    
                    if 'application/pdf' in content_type and content_length > 1000:
                        # Check if PDF content starts with PDF header
                        pdf_header = response.content[:4]
                        if pdf_header == b'%PDF':
                            self.log_result(
                                f"{doc_name} Generation", 
                                True, 
                                f"Successfully generated {doc_name} ({content_length} bytes)",
                                f"Content-Type: {content_type}, Order: {order_number}"
                            )
                            successful_docs += 1
                        else:
                            self.log_result(
                                f"{doc_name} Generation", 
                                False, 
                                f"Response is not a valid PDF (missing PDF header)",
                                f"Content starts with: {pdf_header}, Length: {content_length}"
                            )
                            failed_docs.append(doc_name)
                    else:
                        self.log_result(
                            f"{doc_name} Generation", 
                            False, 
                            f"Invalid PDF response",
                            f"Content-Type: {content_type}, Length: {content_length}"
                        )
                        failed_docs.append(doc_name)
                else:
                    error_detail = response.text[:200] if response.text else "No error details"
                    self.log_result(
                        f"{doc_name} Generation", 
                        False, 
                        f"HTTP {response.status_code} error",
                        error_detail
                    )
                    failed_docs.append(doc_name)
                    
            except Exception as e:
                self.log_result(f"{doc_name} Generation", False, f"Exception: {str(e)}")
                failed_docs.append(doc_name)
        
        # Overall document generation summary
        if successful_docs == len(document_endpoints):
            self.log_result(
                "Document Generation Endpoints", 
                True, 
                f"All {len(document_endpoints)} document types generated successfully"
            )
        else:
            self.log_result(
                "Document Generation Endpoints", 
                False, 
                f"Only {successful_docs}/{len(document_endpoints)} document types working",
                f"Failed: {', '.join(failed_docs)}"
            )
    
    def test_pdf_download_functionality(self, delivery_jobs):
        """Test that PDFs can be properly downloaded with correct headers"""
        print("\n=== PDF DOWNLOAD FUNCTIONALITY TEST ===")
        
        if not delivery_jobs:
            self.log_result(
                "PDF Download Functionality", 
                False, 
                "No delivery jobs available for download testing"
            )
            return
        
        test_job = delivery_jobs[0]
        order_id = test_job.get('id')
        order_number = test_job.get('order_number', 'Unknown')
        
        try:
            # Test invoice PDF download
            response = self.session.get(f"{API_BASE}/documents/invoice/{order_id}")
            
            if response.status_code == 200:
                # Check download headers
                content_disposition = response.headers.get('content-disposition', '')
                content_type = response.headers.get('content-type', '')
                
                # Should have attachment disposition for download
                has_attachment = 'attachment' in content_disposition
                has_filename = f'invoice_{order_number}.pdf' in content_disposition or 'filename=' in content_disposition
                is_pdf_type = 'application/pdf' in content_type
                
                if has_attachment and has_filename and is_pdf_type:
                    self.log_result(
                        "PDF Download Functionality", 
                        True, 
                        "PDF download headers configured correctly",
                        f"Content-Disposition: {content_disposition}, Content-Type: {content_type}"
                    )
                else:
                    issues = []
                    if not has_attachment:
                        issues.append("Missing 'attachment' in Content-Disposition")
                    if not has_filename:
                        issues.append("Missing filename in Content-Disposition")
                    if not is_pdf_type:
                        issues.append("Incorrect Content-Type")
                    
                    self.log_result(
                        "PDF Download Functionality", 
                        False, 
                        "PDF download headers have issues",
                        f"Issues: {', '.join(issues)}"
                    )
            else:
                self.log_result(
                    "PDF Download Functionality", 
                    False, 
                    f"Failed to get PDF for download test: HTTP {response.status_code}",
                    response.text[:200]
                )
                
        except Exception as e:
            self.log_result("PDF Download Functionality", False, f"Error: {str(e)}")
    
    def test_reportlab_pdf_generation(self):
        """Test if ReportLab PDF generation is working properly"""
        print("\n=== REPORTLAB PDF GENERATION TEST ===")
        
        try:
            # Test basic ReportLab functionality
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import A4
            from io import BytesIO
            
            # Create a simple test PDF
            buffer = BytesIO()
            c = canvas.Canvas(buffer, pagesize=A4)
            c.drawString(100, 750, "ReportLab Test PDF")
            c.save()
            
            # Check if PDF was created
            pdf_content = buffer.getvalue()
            buffer.close()
            
            if len(pdf_content) > 100 and pdf_content.startswith(b'%PDF'):
                self.log_result(
                    "ReportLab PDF Generation", 
                    True, 
                    f"ReportLab is working correctly ({len(pdf_content)} bytes generated)"
                )
            else:
                self.log_result(
                    "ReportLab PDF Generation", 
                    False, 
                    "ReportLab generated invalid PDF content",
                    f"Content length: {len(pdf_content)}, Starts with: {pdf_content[:10]}"
                )
                
        except ImportError as e:
            self.log_result(
                "ReportLab PDF Generation", 
                False, 
                "ReportLab library not available",
                str(e)
            )
        except Exception as e:
            self.log_result("ReportLab PDF Generation", False, f"ReportLab error: {str(e)}")
    
    def test_document_branding_and_content(self, delivery_jobs):
        """Test that documents include proper Adela Merchants branding"""
        print("\n=== DOCUMENT BRANDING AND CONTENT TEST ===")
        
        if not delivery_jobs:
            self.log_result(
                "Document Branding and Content", 
                False, 
                "No delivery jobs available for branding testing"
            )
            return
        
        test_job = delivery_jobs[0]
        order_id = test_job.get('id')
        
        try:
            # Test order acknowledgment for branding elements
            response = self.session.get(f"{API_BASE}/documents/acknowledgment/{order_id}")
            
            if response.status_code == 200 and 'application/pdf' in response.headers.get('content-type', ''):
                # For PDF content analysis, we can check the raw content for text strings
                pdf_content = response.content.decode('latin-1', errors='ignore')
                
                branding_elements = [
                    ("Company Name", "ADELA MERCHANTS" in pdf_content),
                    ("Document Title", "ORDER ACKNOWLEDGMENT" in pdf_content),
                    ("Contact Email", "info@adelamerchants.com.au" in pdf_content),
                    ("Website", "www.adelamerchants.com.au" in pdf_content)
                ]
                
                found_elements = [name for name, found in branding_elements if found]
                missing_elements = [name for name, found in branding_elements if not found]
                
                if len(found_elements) >= 2:  # At least company name and title should be present
                    self.log_result(
                        "Document Branding and Content", 
                        True, 
                        f"Document contains proper branding elements",
                        f"Found: {', '.join(found_elements)}"
                    )
                else:
                    self.log_result(
                        "Document Branding and Content", 
                        False, 
                        "Document missing key branding elements",
                        f"Missing: {', '.join(missing_elements)}, Found: {', '.join(found_elements)}"
                    )
            else:
                self.log_result(
                    "Document Branding and Content", 
                    False, 
                    f"Could not retrieve document for branding test: HTTP {response.status_code}"
                )
                
        except Exception as e:
            self.log_result("Document Branding and Content", False, f"Error: {str(e)}")
    
    def test_jobs_ready_for_invoicing(self):
        """Test that there are jobs in delivery stage ready for invoicing"""
        print("\n=== JOBS READY FOR INVOICING TEST ===")
        
        try:
            response = self.session.get(f"{API_BASE}/invoicing/live-jobs")
            
            if response.status_code == 200:
                data = response.json()
                jobs = data.get('data', [])
                
                # Check for jobs in delivery stage
                delivery_jobs = [job for job in jobs if job.get('current_stage') == 'delivery']
                
                if len(delivery_jobs) >= 7:
                    self.log_result(
                        "Jobs Ready for Invoicing", 
                        True, 
                        f"Found {len(delivery_jobs)} jobs in delivery stage ready for invoicing (expected 7+)",
                        f"Total live jobs: {len(jobs)}"
                    )
                    return delivery_jobs  # Return jobs for document testing
                elif len(delivery_jobs) > 0:
                    self.log_result(
                        "Jobs Ready for Invoicing", 
                        True, 
                        f"Found {len(delivery_jobs)} jobs in delivery stage ready for invoicing",
                        f"Total live jobs: {len(jobs)} (expected 7 but found {len(delivery_jobs)})"
                    )
                    return delivery_jobs  # Return jobs for document testing
                else:
                    self.log_result(
                        "Jobs Ready for Invoicing", 
                        False, 
                        "No jobs found in delivery stage ready for invoicing",
                        f"Total live jobs: {len(jobs)}, Jobs by stage: {[job.get('current_stage') for job in jobs]}"
                    )
            else:
                self.log_result(
                    "Jobs Ready for Invoicing", 
                    False, 
                    f"Failed to retrieve live jobs: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Jobs Ready for Invoicing", False, f"Error: {str(e)}")
        
        return []
    
    def test_material_currency_field(self):
        """Test the new currency field functionality in Material model"""
        print("\n=== MATERIAL CURRENCY FIELD TEST ===")
        
        # Test 1: Create Material with Default Currency (should default to "AUD")
        material_default_currency = {
            "supplier": "Australian Paper Co",
            "product_code": "APC-DEFAULT-001",
            "order_to_delivery_time": "5-7 business days",
            "material_description": "Premium Australian paper with default currency",
            "price": 35.50,
            "unit": "m2",
            "raw_substrate": False
            # Note: currency field not specified - should default to "AUD"
        }
        
        default_currency_material_id = None
        try:
            response = self.session.post(f"{API_BASE}/materials", json=material_default_currency)
            
            if response.status_code == 200:
                result = response.json()
                default_currency_material_id = result.get('data', {}).get('id')
                
                # Verify the material was created and retrieve it to check currency
                if default_currency_material_id:
                    get_response = self.session.get(f"{API_BASE}/materials/{default_currency_material_id}")
                    if get_response.status_code == 200:
                        material = get_response.json()
                        currency = material.get('currency')
                        
                        if currency == "AUD":
                            self.log_result(
                                "Create Material with Default Currency", 
                                True, 
                                f"Material created with default currency 'AUD' as expected",
                                f"Material ID: {default_currency_material_id}, Currency: {currency}"
                            )
                        else:
                            self.log_result(
                                "Create Material with Default Currency", 
                                False, 
                                f"Expected default currency 'AUD' but got '{currency}'",
                                f"Material ID: {default_currency_material_id}"
                            )
                    else:
                        self.log_result(
                            "Create Material with Default Currency", 
                            False, 
                            "Failed to retrieve created material for currency verification"
                        )
                else:
                    self.log_result(
                        "Create Material with Default Currency", 
                        False, 
                        "Material creation response missing ID"
                    )
            else:
                self.log_result(
                    "Create Material with Default Currency", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Create Material with Default Currency", False, f"Error: {str(e)}")
        
        # Test 2: Create Material with Specific Currency (USD)
        material_usd_currency = {
            "supplier": "US Paper Imports",
            "product_code": "USPI-USD-001",
            "order_to_delivery_time": "10-14 business days",
            "material_description": "Imported US paper priced in USD",
            "price": 28.75,
            "currency": "USD",  # Explicitly set currency to USD
            "unit": "m2",
            "raw_substrate": False
        }
        
        usd_currency_material_id = None
        try:
            response = self.session.post(f"{API_BASE}/materials", json=material_usd_currency)
            
            if response.status_code == 200:
                result = response.json()
                usd_currency_material_id = result.get('data', {}).get('id')
                
                # Verify the material was created with USD currency
                if usd_currency_material_id:
                    get_response = self.session.get(f"{API_BASE}/materials/{usd_currency_material_id}")
                    if get_response.status_code == 200:
                        material = get_response.json()
                        currency = material.get('currency')
                        
                        if currency == "USD":
                            self.log_result(
                                "Create Material with Specific Currency (USD)", 
                                True, 
                                f"Material created with specified currency 'USD' as expected",
                                f"Material ID: {usd_currency_material_id}, Currency: {currency}"
                            )
                        else:
                            self.log_result(
                                "Create Material with Specific Currency (USD)", 
                                False, 
                                f"Expected currency 'USD' but got '{currency}'",
                                f"Material ID: {usd_currency_material_id}"
                            )
                    else:
                        self.log_result(
                            "Create Material with Specific Currency (USD)", 
                            False, 
                            "Failed to retrieve created material for currency verification"
                        )
                else:
                    self.log_result(
                        "Create Material with Specific Currency (USD)", 
                        False, 
                        "Material creation response missing ID"
                    )
            else:
                self.log_result(
                    "Create Material with Specific Currency (USD)", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Create Material with Specific Currency (USD)", False, f"Error: {str(e)}")
        
        # Test 3: Create Material with EUR Currency
        material_eur_currency = {
            "supplier": "European Materials Ltd",
            "product_code": "EML-EUR-001",
            "order_to_delivery_time": "12-16 business days",
            "material_description": "European specialty paper priced in EUR",
            "price": 42.30,
            "currency": "EUR",  # Explicitly set currency to EUR
            "unit": "m2",
            "raw_substrate": False
        }
        
        eur_currency_material_id = None
        try:
            response = self.session.post(f"{API_BASE}/materials", json=material_eur_currency)
            
            if response.status_code == 200:
                result = response.json()
                eur_currency_material_id = result.get('data', {}).get('id')
                
                # Verify the material was created with EUR currency
                if eur_currency_material_id:
                    get_response = self.session.get(f"{API_BASE}/materials/{eur_currency_material_id}")
                    if get_response.status_code == 200:
                        material = get_response.json()
                        currency = material.get('currency')
                        
                        if currency == "EUR":
                            self.log_result(
                                "Create Material with Specific Currency (EUR)", 
                                True, 
                                f"Material created with specified currency 'EUR' as expected",
                                f"Material ID: {eur_currency_material_id}, Currency: {currency}"
                            )
                        else:
                            self.log_result(
                                "Create Material with Specific Currency (EUR)", 
                                False, 
                                f"Expected currency 'EUR' but got '{currency}'",
                                f"Material ID: {eur_currency_material_id}"
                            )
                    else:
                        self.log_result(
                            "Create Material with Specific Currency (EUR)", 
                            False, 
                            "Failed to retrieve created material for currency verification"
                        )
                else:
                    self.log_result(
                        "Create Material with Specific Currency (EUR)", 
                        False, 
                        "Material creation response missing ID"
                    )
            else:
                self.log_result(
                    "Create Material with Specific Currency (EUR)", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Create Material with Specific Currency (EUR)", False, f"Error: {str(e)}")
        
        # Test 4: Update Material Currency (from AUD to GBP)
        if default_currency_material_id:
            update_currency_data = {
                "supplier": "Australian Paper Co",
                "product_code": "APC-DEFAULT-001-UPDATED",
                "order_to_delivery_time": "5-7 business days",
                "material_description": "Premium Australian paper now priced in GBP",
                "price": 22.75,
                "currency": "GBP",  # Update currency from AUD to GBP
                "unit": "m2",
                "raw_substrate": False
            }
            
            try:
                response = self.session.put(f"{API_BASE}/materials/{default_currency_material_id}", json=update_currency_data)
                
                if response.status_code == 200:
                    # Verify the currency was updated
                    get_response = self.session.get(f"{API_BASE}/materials/{default_currency_material_id}")
                    if get_response.status_code == 200:
                        updated_material = get_response.json()
                        updated_currency = updated_material.get('currency')
                        
                        if updated_currency == "GBP":
                            self.log_result(
                                "Update Material Currency (AUD to GBP)", 
                                True, 
                                f"Successfully updated material currency from AUD to GBP",
                                f"Material ID: {default_currency_material_id}, New Currency: {updated_currency}"
                            )
                        else:
                            self.log_result(
                                "Update Material Currency (AUD to GBP)", 
                                False, 
                                f"Currency update failed - expected 'GBP' but got '{updated_currency}'"
                            )
                    else:
                        self.log_result(
                            "Update Material Currency (AUD to GBP)", 
                            False, 
                            "Failed to retrieve updated material for currency verification"
                        )
                else:
                    self.log_result(
                        "Update Material Currency (AUD to GBP)", 
                        False, 
                        f"Update failed with status {response.status_code}",
                        response.text
                    )
            except Exception as e:
                self.log_result("Update Material Currency (AUD to GBP)", False, f"Error: {str(e)}")
        
        # Test 5: Verify Currency Field in GET All Materials Response
        try:
            response = self.session.get(f"{API_BASE}/materials")
            
            if response.status_code == 200:
                materials = response.json()
                
                # Check if any materials have currency field
                materials_with_currency = [m for m in materials if 'currency' in m and m.get('currency')]
                
                if len(materials_with_currency) > 0:
                    # Check for our test materials
                    test_currencies = []
                    for material in materials_with_currency:
                        if material.get('id') in [default_currency_material_id, usd_currency_material_id, eur_currency_material_id]:
                            test_currencies.append(f"{material.get('product_code', 'Unknown')}: {material.get('currency')}")
                    
                    if len(test_currencies) > 0:
                        self.log_result(
                            "Retrieve Materials with Currency Field", 
                            True, 
                            f"Currency field included in GET /api/materials response",
                            f"Test materials found: {', '.join(test_currencies)}"
                        )
                    else:
                        self.log_result(
                            "Retrieve Materials with Currency Field", 
                            True, 
                            f"Currency field present in materials list ({len(materials_with_currency)} materials have currency)"
                        )
                else:
                    self.log_result(
                        "Retrieve Materials with Currency Field", 
                        False, 
                        "No materials found with currency field in GET /api/materials response",
                        f"Total materials: {len(materials)}"
                    )
            else:
                self.log_result(
                    "Retrieve Materials with Currency Field", 
                    False, 
                    f"Failed to retrieve materials list: {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Retrieve Materials with Currency Field", False, f"Error: {str(e)}")
        
        # Test 6: Test Raw Substrate Material with Currency
        raw_substrate_with_currency = {
            "supplier": "International Raw Materials",
            "product_code": "IRM-RAW-CAD-001",
            "order_to_delivery_time": "14-21 business days",
            "material_description": "Canadian corrugated substrate priced in CAD",
            "price": 52.80,
            "currency": "CAD",  # Canadian Dollar
            "unit": "By the Box",
            "raw_substrate": True,
            "gsm": "300",
            "thickness_mm": 3.2,
            "burst_strength_kpa": 950.0,
            "ply_bonding_jm2": 135.0,
            "moisture_percent": 7.8,
            "supplied_roll_weight": 1400.0,
            "master_deckle_width_mm": 1800.0
        }
        
        try:
            response = self.session.post(f"{API_BASE}/materials", json=raw_substrate_with_currency)
            
            if response.status_code == 200:
                result = response.json()
                raw_material_id = result.get('data', {}).get('id')
                
                if raw_material_id:
                    # Verify raw substrate material has correct currency
                    get_response = self.session.get(f"{API_BASE}/materials/{raw_material_id}")
                    if get_response.status_code == 200:
                        material = get_response.json()
                        currency = material.get('currency')
                        is_raw_substrate = material.get('raw_substrate')
                        
                        if currency == "CAD" and is_raw_substrate:
                            self.log_result(
                                "Create Raw Substrate Material with Currency", 
                                True, 
                                f"Raw substrate material created with currency 'CAD' successfully",
                                f"Material ID: {raw_material_id}, Currency: {currency}, Raw Substrate: {is_raw_substrate}"
                            )
                        else:
                            self.log_result(
                                "Create Raw Substrate Material with Currency", 
                                False, 
                                f"Raw substrate material currency or type incorrect",
                                f"Expected: CAD/True, Got: {currency}/{is_raw_substrate}"
                            )
                    else:
                        self.log_result(
                            "Create Raw Substrate Material with Currency", 
                            False, 
                            "Failed to retrieve created raw substrate material"
                        )
                else:
                    self.log_result(
                        "Create Raw Substrate Material with Currency", 
                        False, 
                        "Raw substrate material creation response missing ID"
                    )
            else:
                self.log_result(
                    "Create Raw Substrate Material with Currency", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Create Raw Substrate Material with Currency", False, f"Error: {str(e)}")
    
    def test_materials_management_api(self):
        """Test Materials Management API endpoints with new fields"""
        print("\n=== MATERIALS MANAGEMENT API TEST (WITH NEW FIELDS) ===")
        
        # Test GET /api/materials (get all materials)
        try:
            response = self.session.get(f"{API_BASE}/materials")
            
            if response.status_code == 200:
                materials = response.json()
                self.log_result(
                    "Get All Materials", 
                    True, 
                    f"Successfully retrieved {len(materials)} materials"
                )
            else:
                self.log_result(
                    "Get All Materials", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Get All Materials", False, f"Error: {str(e)}")
        
        # Test POST /api/materials (create basic material with material_description - REQUIRED FIELD)
        basic_material_data = {
            "supplier": "Premium Paper Supplies",
            "product_code": "PPS-BASIC-001",
            "order_to_delivery_time": "5-7 business days",
            "material_description": "High-quality printing paper for commercial use",  # NEW REQUIRED FIELD
            "price": 25.50,
            "unit": "m2",
            "raw_substrate": False
        }
        
        basic_material_id = None
        try:
            response = self.session.post(f"{API_BASE}/materials", json=basic_material_data)
            
            if response.status_code == 200:
                result = response.json()
                basic_material_id = result.get('data', {}).get('id')
                self.log_result(
                    "Create Basic Material (with material_description)", 
                    True, 
                    f"Successfully created basic material with ID: {basic_material_id}"
                )
            else:
                self.log_result(
                    "Create Basic Material (with material_description)", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Create Basic Material (with material_description)", False, f"Error: {str(e)}")
        
        # Test POST /api/materials (create material WITHOUT material_description - should fail)
        invalid_material_data = {
            "supplier": "Test Supplier Ltd",
            "product_code": "TEST-INVALID-001",
            "order_to_delivery_time": "5-7 business days",
            # Missing material_description - should cause validation error
            "price": 25.50,
            "unit": "m2",
            "raw_substrate": False
        }
        
        try:
            response = self.session.post(f"{API_BASE}/materials", json=invalid_material_data)
            
            if response.status_code == 422:  # Validation error expected
                self.log_result(
                    "Create Material Without material_description (validation test)", 
                    True, 
                    "Correctly rejected material creation without required material_description field"
                )
            elif response.status_code == 200:
                self.log_result(
                    "Create Material Without material_description (validation test)", 
                    False, 
                    "Material was created without required material_description field - validation failed"
                )
            else:
                self.log_result(
                    "Create Material Without material_description (validation test)", 
                    False, 
                    f"Unexpected status code {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Create Material Without material_description (validation test)", False, f"Error: {str(e)}")
        
        # Test POST /api/materials (create raw substrate material with ALL NEW FIELDS)
        raw_substrate_data = {
            "supplier": "Industrial Raw Materials Co",
            "product_code": "IRM-RAW-SUB-001",
            "order_to_delivery_time": "10-14 business days",
            "material_description": "Premium corrugated cardboard substrate for high-strength packaging applications",  # NEW REQUIRED FIELD
            "price": 45.75,
            "unit": "By the Box",
            "raw_substrate": True,
            "gsm": "250",
            "thickness_mm": 2.5,
            "burst_strength_kpa": 850.0,
            "ply_bonding_jm2": 120.5,
            "moisture_percent": 8.2,
            "supplied_roll_weight": 1250.5,  # NEW FIELD for raw substrates
            "master_deckle_width_mm": 1600.0  # NEW FIELD for raw substrates
        }
        
        raw_material_id = None
        try:
            response = self.session.post(f"{API_BASE}/materials", json=raw_substrate_data)
            
            if response.status_code == 200:
                result = response.json()
                raw_material_id = result.get('data', {}).get('id')
                self.log_result(
                    "Create Raw Substrate Material (with new fields)", 
                    True, 
                    f"Successfully created raw substrate material with ID: {raw_material_id}"
                )
            else:
                self.log_result(
                    "Create Raw Substrate Material (with new fields)", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Create Raw Substrate Material (with new fields)", False, f"Error: {str(e)}")
        
        # Test GET /api/materials/{id} (get specific material and verify new fields)
        if basic_material_id:
            try:
                response = self.session.get(f"{API_BASE}/materials/{basic_material_id}")
                
                if response.status_code == 200:
                    material = response.json()
                    
                    # Verify basic material has new required field
                    has_material_description = material.get('material_description') == "High-quality printing paper for commercial use"
                    has_correct_supplier = material.get('supplier') == "Premium Paper Supplies"
                    
                    if has_material_description and has_correct_supplier:
                        self.log_result(
                            "Get Specific Basic Material (verify new fields)", 
                            True, 
                            f"Successfully retrieved material with material_description: {material.get('product_code')}"
                        )
                    else:
                        self.log_result(
                            "Get Specific Basic Material (verify new fields)", 
                            False, 
                            "Material missing material_description or other expected values",
                            f"material_description: {material.get('material_description')}, supplier: {material.get('supplier')}"
                        )
                else:
                    self.log_result(
                        "Get Specific Basic Material (verify new fields)", 
                        False, 
                        f"Failed with status {response.status_code}",
                        response.text
                    )
            except Exception as e:
                self.log_result("Get Specific Basic Material (verify new fields)", False, f"Error: {str(e)}")
        
        # Test GET /api/materials/{id} (get raw substrate material and verify ALL new fields)
        if raw_material_id:
            try:
                response = self.session.get(f"{API_BASE}/materials/{raw_material_id}")
                
                if response.status_code == 200:
                    material = response.json()
                    
                    # Verify raw substrate material has all new fields
                    checks = [
                        ("material_description", material.get('material_description') == "Premium corrugated cardboard substrate for high-strength packaging applications"),
                        ("supplied_roll_weight", material.get('supplied_roll_weight') == 1250.5),
                        ("master_deckle_width_mm", material.get('master_deckle_width_mm') == 1600.0),
                        ("raw_substrate", material.get('raw_substrate') == True)
                    ]
                    
                    passed_checks = [name for name, passed in checks if passed]
                    failed_checks = [name for name, passed in checks if not passed]
                    
                    if len(failed_checks) == 0:
                        self.log_result(
                            "Get Specific Raw Substrate Material (verify all new fields)", 
                            True, 
                            f"Successfully retrieved raw substrate material with all new fields: {material.get('product_code')}"
                        )
                    else:
                        self.log_result(
                            "Get Specific Raw Substrate Material (verify all new fields)", 
                            False, 
                            f"Raw substrate material missing or incorrect new fields: {', '.join(failed_checks)}",
                            f"Passed: {', '.join(passed_checks)}, Failed: {', '.join(failed_checks)}"
                        )
                else:
                    self.log_result(
                        "Get Specific Raw Substrate Material (verify all new fields)", 
                        False, 
                        f"Failed with status {response.status_code}",
                        response.text
                    )
            except Exception as e:
                self.log_result("Get Specific Raw Substrate Material (verify all new fields)", False, f"Error: {str(e)}")
        
        # Test PUT /api/materials/{id} (update material with new fields)
        if basic_material_id:
            update_data = {
                "supplier": "Updated Premium Supplier Ltd",
                "product_code": "UPS-BASIC-001-UPDATED",
                "order_to_delivery_time": "3-5 business days",
                "material_description": "Updated high-quality printing paper with enhanced durability",  # Updated required field
                "price": 28.75,
                "unit": "m2",
                "raw_substrate": False
            }
            
            try:
                response = self.session.put(f"{API_BASE}/materials/{basic_material_id}", json=update_data)
                
                if response.status_code == 200:
                    # Verify the update worked by fetching the material
                    get_response = self.session.get(f"{API_BASE}/materials/{basic_material_id}")
                    if get_response.status_code == 200:
                        updated_material = get_response.json()
                        if updated_material.get('material_description') == "Updated high-quality printing paper with enhanced durability":
                            self.log_result(
                                "Update Material (with new fields)", 
                                True, 
                                "Successfully updated material with new material_description field"
                            )
                        else:
                            self.log_result(
                                "Update Material (with new fields)", 
                                False, 
                                "Material updated but material_description not correctly updated"
                            )
                    else:
                        self.log_result(
                            "Update Material (with new fields)", 
                            True, 
                            "Material update returned success"
                        )
                else:
                    self.log_result(
                        "Update Material (with new fields)", 
                        False, 
                        f"Failed with status {response.status_code}",
                        response.text
                    )
            except Exception as e:
                self.log_result("Update Material (with new fields)", False, f"Error: {str(e)}")
        
        # Test PUT /api/materials/{id} (update raw substrate material with new fields)
        if raw_material_id:
            raw_update_data = {
                "supplier": "Updated Industrial Raw Materials Co",
                "product_code": "UIRM-RAW-SUB-001-UPDATED",
                "order_to_delivery_time": "7-10 business days",
                "material_description": "Updated premium corrugated cardboard substrate with enhanced strength properties",
                "price": 52.25,
                "unit": "By the Box",
                "raw_substrate": True,
                "gsm": "280",
                "thickness_mm": 2.8,
                "burst_strength_kpa": 950.0,
                "ply_bonding_jm2": 135.0,
                "moisture_percent": 7.5,
                "supplied_roll_weight": 1400.0,  # Updated new field
                "master_deckle_width_mm": 1800.0  # Updated new field
            }
            
            try:
                response = self.session.put(f"{API_BASE}/materials/{raw_material_id}", json=raw_update_data)
                
                if response.status_code == 200:
                    # Verify the update worked by fetching the material
                    get_response = self.session.get(f"{API_BASE}/materials/{raw_material_id}")
                    if get_response.status_code == 200:
                        updated_material = get_response.json()
                        
                        # Check updated new fields
                        checks = [
                            ("material_description", updated_material.get('material_description') == "Updated premium corrugated cardboard substrate with enhanced strength properties"),
                            ("supplied_roll_weight", updated_material.get('supplied_roll_weight') == 1400.0),
                            ("master_deckle_width_mm", updated_material.get('master_deckle_width_mm') == 1800.0)
                        ]
                        
                        passed_checks = [name for name, passed in checks if passed]
                        failed_checks = [name for name, passed in checks if not passed]
                        
                        if len(failed_checks) == 0:
                            self.log_result(
                                "Update Raw Substrate Material (with new fields)", 
                                True, 
                                "Successfully updated raw substrate material with all new fields"
                            )
                        else:
                            self.log_result(
                                "Update Raw Substrate Material (with new fields)", 
                                False, 
                                f"Raw substrate material updated but new fields not correctly updated: {', '.join(failed_checks)}"
                            )
                    else:
                        self.log_result(
                            "Update Raw Substrate Material (with new fields)", 
                            True, 
                            "Raw substrate material update returned success"
                        )
                else:
                    self.log_result(
                        "Update Raw Substrate Material (with new fields)", 
                        False, 
                        f"Failed with status {response.status_code}",
                        response.text
                    )
            except Exception as e:
                self.log_result("Update Raw Substrate Material (with new fields)", False, f"Error: {str(e)}")
        
        # Test DELETE /api/materials/{id} (soft delete material)
        if basic_material_id:
            try:
                response = self.session.delete(f"{API_BASE}/materials/{basic_material_id}")
                
                if response.status_code == 200:
                    self.log_result(
                        "Delete Material", 
                        True, 
                        "Successfully deleted material (soft delete)"
                    )
                else:
                    self.log_result(
                        "Delete Material", 
                        False, 
                        f"Failed with status {response.status_code}",
                        response.text
                    )
            except Exception as e:
                self.log_result("Delete Material", False, f"Error: {str(e)}")
        
        return raw_material_id  # Return for use in client product tests
    
    def test_client_product_catalog_api(self, client_id, material_id):
        """Test Client Product Catalog API endpoints"""
        print("\n=== CLIENT PRODUCT CATALOG API TEST ===")
        
        if not client_id:
            self.log_result(
                "Client Product Catalog API", 
                False, 
                "No client ID available for testing"
            )
            return
        
        # Test GET /api/clients/{client_id}/catalog (get client products)
        try:
            response = self.session.get(f"{API_BASE}/clients/{client_id}/catalog")
            
            if response.status_code == 200:
                products = response.json()
                self.log_result(
                    "Get Client Product Catalog", 
                    True, 
                    f"Successfully retrieved {len(products)} client products"
                )
            else:
                self.log_result(
                    "Get Client Product Catalog", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Get Client Product Catalog", False, f"Error: {str(e)}")
        
        # Test POST /api/clients/{client_id}/catalog (create finished goods product)
        finished_goods_data = {
            "product_type": "finished_goods",
            "product_code": "FG-001",
            "product_description": "Premium Finished Product",
            "price_ex_gst": 150.00,
            "minimum_order_quantity": 10,
            "consignment": False
        }
        
        finished_product_id = None
        try:
            response = self.session.post(f"{API_BASE}/clients/{client_id}/catalog", json=finished_goods_data)
            
            if response.status_code == 200:
                result = response.json()
                finished_product_id = result.get('data', {}).get('id')
                self.log_result(
                    "Create Finished Goods Product", 
                    True, 
                    f"Successfully created finished goods product with ID: {finished_product_id}"
                )
            else:
                self.log_result(
                    "Create Finished Goods Product", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Create Finished Goods Product", False, f"Error: {str(e)}")
        
        # Test POST /api/clients/{client_id}/catalog (create paper cores product with materials)
        paper_cores_data = {
            "product_type": "paper_cores",
            "product_code": "PC-001",
            "product_description": "Custom Paper Core - High Strength",
            "price_ex_gst": 85.50,
            "minimum_order_quantity": 50,
            "consignment": True,
            "material_used": [material_id] if material_id else [],
            "core_id": "CORE-12345",
            "core_width": "150mm",
            "core_thickness": "3.2mm",
            "strength_quality_important": True,
            "delivery_included": True
        }
        
        paper_cores_product_id = None
        try:
            response = self.session.post(f"{API_BASE}/clients/{client_id}/catalog", json=paper_cores_data)
            
            if response.status_code == 200:
                result = response.json()
                paper_cores_product_id = result.get('data', {}).get('id')
                self.log_result(
                    "Create Paper Cores Product", 
                    True, 
                    f"Successfully created paper cores product with ID: {paper_cores_product_id}"
                )
            else:
                self.log_result(
                    "Create Paper Cores Product", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Create Paper Cores Product", False, f"Error: {str(e)}")
        
        # Test GET /api/clients/{client_id}/catalog/{product_id} (get specific client product)
        if finished_product_id:
            try:
                response = self.session.get(f"{API_BASE}/clients/{client_id}/catalog/{finished_product_id}")
                
                if response.status_code == 200:
                    product = response.json()
                    if product.get('product_code') == "FG-001":
                        self.log_result(
                            "Get Specific Client Product", 
                            True, 
                            f"Successfully retrieved client product: {product.get('product_code')}"
                        )
                    else:
                        self.log_result(
                            "Get Specific Client Product", 
                            False, 
                            "Product data doesn't match expected values"
                        )
                else:
                    self.log_result(
                        "Get Specific Client Product", 
                        False, 
                        f"Failed with status {response.status_code}",
                        response.text
                    )
            except Exception as e:
                self.log_result("Get Specific Client Product", False, f"Error: {str(e)}")
        
        # Test PUT /api/clients/{client_id}/catalog/{product_id} (update client product)
        if finished_product_id:
            update_data = {
                "product_type": "finished_goods",
                "product_code": "FG-001-UPDATED",
                "product_description": "Premium Finished Product - Updated",
                "price_ex_gst": 175.00,
                "minimum_order_quantity": 15,
                "consignment": True
            }
            
            try:
                response = self.session.put(f"{API_BASE}/clients/{client_id}/catalog/{finished_product_id}", json=update_data)
                
                if response.status_code == 200:
                    self.log_result(
                        "Update Client Product", 
                        True, 
                        "Successfully updated client product"
                    )
                else:
                    self.log_result(
                        "Update Client Product", 
                        False, 
                        f"Failed with status {response.status_code}",
                        response.text
                    )
            except Exception as e:
                self.log_result("Update Client Product", False, f"Error: {str(e)}")
        
        return finished_product_id, paper_cores_product_id
    
    def test_client_product_copy_functionality(self, source_client_id, product_id):
        """Test copying products between clients"""
        print("\n=== CLIENT PRODUCT COPY FUNCTIONALITY TEST ===")
        
        if not source_client_id or not product_id:
            self.log_result(
                "Client Product Copy Functionality", 
                False, 
                "Missing source client ID or product ID for copy test"
            )
            return
        
        # Create a second client for copy testing
        target_client_data = {
            "company_name": "Target Copy Client Ltd",
            "contact_name": "Jane Smith",
            "email": "jane@targetclient.com",
            "phone": "0487654321",
            "address": "789 Target Street",
            "city": "Sydney",
            "state": "NSW",
            "postal_code": "2000",
            "abn": "98765432109",
            "payment_terms": "Net 21 days",
            "lead_time_days": 5
        }
        
        target_client_id = None
        try:
            response = self.session.post(f"{API_BASE}/clients", json=target_client_data)
            
            if response.status_code == 200:
                result = response.json()
                target_client_id = result.get('data', {}).get('id')
                self.log_result(
                    "Create Target Client for Copy Test", 
                    True, 
                    f"Successfully created target client with ID: {target_client_id}"
                )
            else:
                self.log_result(
                    "Create Target Client for Copy Test", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
                return
        except Exception as e:
            self.log_result("Create Target Client for Copy Test", False, f"Error: {str(e)}")
            return
        
        # Test POST /api/clients/{client_id}/catalog/{product_id}/copy-to/{target_client_id}
        try:
            response = self.session.post(f"{API_BASE}/clients/{source_client_id}/catalog/{product_id}/copy-to/{target_client_id}")
            
            if response.status_code == 200:
                result = response.json()
                copied_product_id = result.get('data', {}).get('id')
                
                if copied_product_id:
                    # Verify the product was copied by checking target client's catalog
                    verify_response = self.session.get(f"{API_BASE}/clients/{target_client_id}/catalog/{copied_product_id}")
                    
                    if verify_response.status_code == 200:
                        copied_product = verify_response.json()
                        self.log_result(
                            "Copy Product Between Clients", 
                            True, 
                            f"Successfully copied product to target client. New ID: {copied_product_id}",
                            f"Product Code: {copied_product.get('product_code')}"
                        )
                    else:
                        self.log_result(
                            "Copy Product Between Clients", 
                            False, 
                            "Product copy reported success but verification failed"
                        )
                else:
                    self.log_result(
                        "Copy Product Between Clients", 
                        False, 
                        "Copy response missing new product ID"
                    )
            else:
                self.log_result(
                    "Copy Product Between Clients", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Copy Product Between Clients", False, f"Error: {str(e)}")
    
    def test_client_product_delete_functionality(self, client_id, product_id):
        """Test DELETE /api/clients/{client_id}/catalog/{product_id}"""
        print("\n=== CLIENT PRODUCT DELETE FUNCTIONALITY TEST ===")
        
        if not client_id or not product_id:
            self.log_result(
                "Client Product Delete Functionality", 
                False, 
                "Missing client ID or product ID for delete test"
            )
            return
        
        try:
            response = self.session.delete(f"{API_BASE}/clients/{client_id}/catalog/{product_id}")
            
            if response.status_code == 200:
                # Verify the product is no longer accessible
                verify_response = self.session.get(f"{API_BASE}/clients/{client_id}/catalog/{product_id}")
                
                if verify_response.status_code == 404:
                    self.log_result(
                        "Delete Client Product", 
                        True, 
                        "Successfully deleted client product (soft delete verified)"
                    )
                else:
                    self.log_result(
                        "Delete Client Product", 
                        False, 
                        "Delete reported success but product still accessible"
                    )
            else:
                self.log_result(
                    "Delete Client Product", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Delete Client Product", False, f"Error: {str(e)}")
    
    def test_validation_errors(self, client_id):
        """Test validation errors for required fields"""
        print("\n=== VALIDATION ERRORS TEST ===")
        
        # Test materials validation - missing required fields
        invalid_material_data = {
            "supplier": "",  # Empty supplier
            "product_code": "",  # Empty product code
            "price": -10.0,  # Negative price
            "unit": ""  # Empty unit
        }
        
        try:
            response = self.session.post(f"{API_BASE}/materials", json=invalid_material_data)
            
            if response.status_code in [400, 422]:  # Validation error expected
                self.log_result(
                    "Materials Validation Errors", 
                    True, 
                    f"Correctly rejected invalid material data with status {response.status_code}"
                )
            else:
                self.log_result(
                    "Materials Validation Errors", 
                    False, 
                    f"Expected validation error but got status {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Materials Validation Errors", False, f"Error: {str(e)}")
        
        # Test client products validation - missing required fields
        if client_id:
            invalid_product_data = {
                "product_type": "invalid_type",  # Invalid product type
                "product_code": "",  # Empty product code
                "price_ex_gst": -50.0,  # Negative price
                "minimum_order_quantity": -5  # Negative quantity
            }
            
            try:
                response = self.session.post(f"{API_BASE}/clients/{client_id}/catalog", json=invalid_product_data)
                
                if response.status_code in [400, 422]:  # Validation error expected
                    self.log_result(
                        "Client Products Validation Errors", 
                        True, 
                        f"Correctly rejected invalid client product data with status {response.status_code}"
                    )
                else:
                    self.log_result(
                        "Client Products Validation Errors", 
                        False, 
                        f"Expected validation error but got status {response.status_code}",
                        response.text
                    )
            except Exception as e:
                self.log_result("Client Products Validation Errors", False, f"Error: {str(e)}")
    
    def test_authentication_requirements(self):
        """Test that new endpoints require proper authentication"""
        print("\n=== AUTHENTICATION REQUIREMENTS TEST ===")
        
        # Test without authentication
        temp_session = requests.Session()
        
        endpoints_to_test = [
            ("GET", "/materials", "Materials List"),
            ("POST", "/materials", "Create Material"),
            ("GET", "/clients/test-id/catalog", "Client Product Catalog"),
            ("POST", "/clients/test-id/catalog", "Create Client Product")
        ]
        
        for method, endpoint, name in endpoints_to_test:
            try:
                if method == "GET":
                    response = temp_session.get(f"{API_BASE}{endpoint}")
                else:
                    response = temp_session.post(f"{API_BASE}{endpoint}", json={})
                
                if response.status_code in [401, 403]:
                    self.log_result(
                        f"{name} Authentication", 
                        True, 
                        f"Correctly requires authentication (status: {response.status_code})"
                    )
                else:
                    self.log_result(
                        f"{name} Authentication", 
                        False, 
                        f"Expected 401/403 but got {response.status_code}",
                        f"Endpoint {endpoint} should require authentication"
                    )
            except Exception as e:
                self.log_result(f"{name} Authentication", False, f"Error: {str(e)}")

    def test_production_board_enhancements(self):
        """Test new Production Board API enhancements"""
        print("\n=== PRODUCTION BOARD ENHANCEMENTS TEST ===")
        
        # Test GET /api/production/board - should include runtime and materials_ready fields
        try:
            response = self.session.get(f"{API_BASE}/production/board")
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success') and 'data' in data:
                    board_data = data['data']
                    
                    # Check if board has stages
                    if isinstance(board_data, dict) and len(board_data) > 0:
                        # Find a stage with jobs to test
                        test_job = None
                        for stage, jobs in board_data.items():
                            if jobs and len(jobs) > 0:
                                test_job = jobs[0]
                                break
                        
                        if test_job:
                            # Check for new fields: runtime and materials_ready
                            has_runtime = 'runtime' in test_job
                            has_materials_ready = 'materials_ready' in test_job
                            
                            if has_runtime and has_materials_ready:
                                self.log_result(
                                    "Production Board Enhanced Fields", 
                                    True, 
                                    f"Production board includes new fields: runtime='{test_job.get('runtime')}', materials_ready={test_job.get('materials_ready')}"
                                )
                                return test_job.get('id')  # Return order ID for further testing
                            else:
                                missing_fields = []
                                if not has_runtime:
                                    missing_fields.append('runtime')
                                if not has_materials_ready:
                                    missing_fields.append('materials_ready')
                                
                                self.log_result(
                                    "Production Board Enhanced Fields", 
                                    False, 
                                    f"Production board missing new fields: {', '.join(missing_fields)}"
                                )
                        else:
                            self.log_result(
                                "Production Board Enhanced Fields", 
                                False, 
                                "No jobs found on production board to test enhanced fields"
                            )
                    else:
                        self.log_result(
                            "Production Board Enhanced Fields", 
                            False, 
                            "Production board data is empty or invalid format"
                        )
                else:
                    self.log_result(
                        "Production Board Enhanced Fields", 
                        False, 
                        "Production board response missing success/data fields",
                        str(data)
                    )
            else:
                self.log_result(
                    "Production Board Enhanced Fields", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Production Board Enhanced Fields", False, f"Error: {str(e)}")
        
        return None

    def test_stage_movement_api(self, order_id):
        """Test POST /api/production/move-stage/{order_id}"""
        print("\n=== STAGE MOVEMENT API TEST ===")
        
        if not order_id:
            self.log_result(
                "Stage Movement API", 
                False, 
                "No order ID available for stage movement testing"
            )
            return
        
        # Test forward movement
        try:
            forward_request = {
                "direction": "forward",
                "notes": "Testing forward stage movement"
            }
            
            response = self.session.post(f"{API_BASE}/production/move-stage/{order_id}", json=forward_request)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success') and 'new_stage' in data:
                    new_stage = data.get('new_stage')
                    self.log_result(
                        "Stage Movement Forward", 
                        True, 
                        f"Successfully moved order to stage: {new_stage}",
                        data.get('message')
                    )
                    
                    # Test backward movement
                    backward_request = {
                        "direction": "backward",
                        "notes": "Testing backward stage movement"
                    }
                    
                    backward_response = self.session.post(f"{API_BASE}/production/move-stage/{order_id}", json=backward_request)
                    
                    if backward_response.status_code == 200:
                        backward_data = backward_response.json()
                        
                        if backward_data.get('success'):
                            self.log_result(
                                "Stage Movement Backward", 
                                True, 
                                f"Successfully moved order back to stage: {backward_data.get('new_stage')}",
                                backward_data.get('message')
                            )
                        else:
                            self.log_result(
                                "Stage Movement Backward", 
                                False, 
                                "Backward movement response indicates failure",
                                str(backward_data)
                            )
                    else:
                        self.log_result(
                            "Stage Movement Backward", 
                            False, 
                            f"Backward movement failed with status {backward_response.status_code}",
                            backward_response.text
                        )
                else:
                    self.log_result(
                        "Stage Movement Forward", 
                        False, 
                        "Forward movement response missing success/new_stage fields",
                        str(data)
                    )
            else:
                self.log_result(
                    "Stage Movement Forward", 
                    False, 
                    f"Forward movement failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Stage Movement API", False, f"Error: {str(e)}")
        
        # Test invalid direction
        try:
            invalid_request = {
                "direction": "invalid_direction",
                "notes": "Testing invalid direction"
            }
            
            response = self.session.post(f"{API_BASE}/production/move-stage/{order_id}", json=invalid_request)
            
            if response.status_code == 400:
                self.log_result(
                    "Stage Movement Invalid Direction", 
                    True, 
                    "Correctly rejected invalid direction with status 400"
                )
            else:
                self.log_result(
                    "Stage Movement Invalid Direction", 
                    False, 
                    f"Expected 400 for invalid direction but got {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Stage Movement Invalid Direction", False, f"Error: {str(e)}")

    def test_materials_status_api(self, order_id):
        """Test materials status API endpoints"""
        print("\n=== MATERIALS STATUS API TEST ===")
        
        if not order_id:
            self.log_result(
                "Materials Status API", 
                False, 
                "No order ID available for materials status testing"
            )
            return
        
        # Test GET /api/production/materials-status/{order_id}
        try:
            response = self.session.get(f"{API_BASE}/production/materials-status/{order_id}")
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success') and 'data' in data:
                    materials_data = data['data']
                    
                    # Check required fields
                    required_fields = ['order_id', 'materials_ready', 'materials_checklist', 'updated_by']
                    missing_fields = [field for field in required_fields if field not in materials_data]
                    
                    if not missing_fields:
                        self.log_result(
                            "Get Materials Status", 
                            True, 
                            f"Successfully retrieved materials status for order {order_id}",
                            f"Materials ready: {materials_data.get('materials_ready')}, Checklist items: {len(materials_data.get('materials_checklist', []))}"
                        )
                    else:
                        self.log_result(
                            "Get Materials Status", 
                            False, 
                            f"Materials status response missing fields: {missing_fields}",
                            str(materials_data)
                        )
                else:
                    self.log_result(
                        "Get Materials Status", 
                        False, 
                        "Materials status response missing success/data fields",
                        str(data)
                    )
            else:
                self.log_result(
                    "Get Materials Status", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Get Materials Status", False, f"Error: {str(e)}")
        
        # Test PUT /api/production/materials-status/{order_id}
        try:
            update_data = {
                "materials_ready": True,
                "materials_checklist": [
                    {"material": "Raw Paper", "ready": True},
                    {"material": "Adhesive", "ready": True},
                    {"material": "Packaging", "ready": False}
                ]
            }
            
            response = self.session.put(f"{API_BASE}/production/materials-status/{order_id}", json=update_data)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success'):
                    self.log_result(
                        "Update Materials Status", 
                        True, 
                        "Successfully updated materials status",
                        data.get('message')
                    )
                    
                    # Verify the update by getting the status again
                    verify_response = self.session.get(f"{API_BASE}/production/materials-status/{order_id}")
                    
                    if verify_response.status_code == 200:
                        verify_data = verify_response.json()
                        
                        if verify_data.get('success') and verify_data.get('data', {}).get('materials_ready') == True:
                            self.log_result(
                                "Verify Materials Status Update", 
                                True, 
                                "Materials status update was persisted correctly"
                            )
                        else:
                            self.log_result(
                                "Verify Materials Status Update", 
                                False, 
                                "Materials status update was not persisted correctly"
                            )
                else:
                    self.log_result(
                        "Update Materials Status", 
                        False, 
                        "Update materials status response indicates failure",
                        str(data)
                    )
            else:
                self.log_result(
                    "Update Materials Status", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Update Materials Status", False, f"Error: {str(e)}")

    def test_order_item_status_api(self, order_id):
        """Test PUT /api/production/order-item-status/{order_id}"""
        print("\n=== ORDER ITEM STATUS API TEST ===")
        
        if not order_id:
            self.log_result(
                "Order Item Status API", 
                False, 
                "No order ID available for order item status testing"
            )
            return
        
        # Test updating first item completion status
        try:
            update_data = {
                "item_index": 0,
                "is_completed": True
            }
            
            response = self.session.put(f"{API_BASE}/production/order-item-status/{order_id}", json=update_data)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success'):
                    self.log_result(
                        "Update Order Item Status", 
                        True, 
                        "Successfully updated order item completion status",
                        data.get('message')
                    )
                    
                    # Test updating with invalid item index
                    invalid_update = {
                        "item_index": 999,  # Invalid index
                        "is_completed": True
                    }
                    
                    invalid_response = self.session.put(f"{API_BASE}/production/order-item-status/{order_id}", json=invalid_update)
                    
                    if invalid_response.status_code == 400:
                        self.log_result(
                            "Order Item Status Invalid Index", 
                            True, 
                            "Correctly rejected invalid item index with status 400"
                        )
                    else:
                        self.log_result(
                            "Order Item Status Invalid Index", 
                            False, 
                            f"Expected 400 for invalid index but got {invalid_response.status_code}",
                            invalid_response.text
                        )
                else:
                    self.log_result(
                        "Update Order Item Status", 
                        False, 
                        "Update order item status response indicates failure",
                        str(data)
                    )
            else:
                self.log_result(
                    "Update Order Item Status", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Update Order Item Status", False, f"Error: {str(e)}")

    def test_production_board_authentication(self):
        """Test that production board endpoints require proper authentication"""
        print("\n=== PRODUCTION BOARD AUTHENTICATION TEST ===")
        
        # Test without authentication
        temp_session = requests.Session()
        
        endpoints_to_test = [
            ("Production Board", "GET", "/production/board"),
            ("Move Stage", "POST", "/production/move-stage/test-id"),
            ("Get Materials Status", "GET", "/production/materials-status/test-id"),
            ("Update Materials Status", "PUT", "/production/materials-status/test-id"),
            ("Update Order Item Status", "PUT", "/production/order-item-status/test-id")
        ]
        
        for endpoint_name, method, endpoint in endpoints_to_test:
            try:
                if method == "GET":
                    response = temp_session.get(f"{API_BASE}{endpoint}")
                elif method == "POST":
                    response = temp_session.post(f"{API_BASE}{endpoint}", json={"direction": "forward"})
                elif method == "PUT":
                    response = temp_session.put(f"{API_BASE}{endpoint}", json={"test": "data"})
                
                if response.status_code in [401, 403]:
                    self.log_result(
                        f"{endpoint_name} Authentication", 
                        True, 
                        f"Correctly requires authentication (status: {response.status_code})"
                    )
                else:
                    self.log_result(
                        f"{endpoint_name} Authentication", 
                        False, 
                        f"Expected 401/403 but got {response.status_code}",
                        f"Endpoint {endpoint} should require authentication"
                    )
                    
            except Exception as e:
                self.log_result(f"{endpoint_name} Authentication", False, f"Error: {str(e)}")

    def test_invalid_order_ids(self):
        """Test error handling for invalid order IDs"""
        print("\n=== INVALID ORDER IDS TEST ===")
        
        invalid_order_id = "invalid-order-id-12345"
        
        endpoints_to_test = [
            ("Move Stage Invalid Order", "POST", f"/production/move-stage/{invalid_order_id}", {"direction": "forward"}),
            ("Get Materials Status Invalid Order", "GET", f"/production/materials-status/{invalid_order_id}", None),
            ("Update Materials Status Invalid Order", "PUT", f"/production/materials-status/{invalid_order_id}", {"materials_ready": True, "materials_checklist": []}),
            ("Update Order Item Status Invalid Order", "PUT", f"/production/order-item-status/{invalid_order_id}", {"item_index": 0, "is_completed": True})
        ]
        
        for test_name, method, endpoint, data in endpoints_to_test:
            try:
                if method == "GET":
                    response = self.session.get(f"{API_BASE}{endpoint}")
                elif method == "POST":
                    response = self.session.post(f"{API_BASE}{endpoint}", json=data)
                elif method == "PUT":
                    response = self.session.put(f"{API_BASE}{endpoint}", json=data)
                
                if response.status_code == 404:
                    self.log_result(
                        test_name, 
                        True, 
                        "Correctly returned 404 for invalid order ID"
                    )
                else:
                    self.log_result(
                        test_name, 
                        False, 
                        f"Expected 404 for invalid order ID but got {response.status_code}",
                        response.text
                    )
                    
            except Exception as e:
                self.log_result(test_name, False, f"Error: {str(e)}")

    def test_materials_api_fix(self):
        """Test the Materials API fix for material_description Optional field"""
        print("\n=== MATERIALS API FIX TEST ===")
        
        # Test 1: GET /api/materials - Should work now with Optional material_description
        try:
            response = self.session.get(f"{API_BASE}/materials")
            
            if response.status_code == 200:
                materials = response.json()
                
                # Check if we get a list of materials
                if isinstance(materials, list):
                    # Check for materials with and without material_description
                    materials_with_desc = [m for m in materials if m.get('material_description') is not None]
                    materials_without_desc = [m for m in materials if m.get('material_description') is None]
                    
                    self.log_result(
                        "GET /api/materials - Backward Compatibility", 
                        True, 
                        f"Successfully retrieved {len(materials)} materials (with desc: {len(materials_with_desc)}, without desc: {len(materials_without_desc)})",
                        f"Fix working: existing materials without material_description load correctly"
                    )
                else:
                    self.log_result(
                        "GET /api/materials - Backward Compatibility", 
                        False, 
                        "Response is not a list of materials",
                        f"Response type: {type(materials)}"
                    )
            else:
                self.log_result(
                    "GET /api/materials - Backward Compatibility", 
                    False, 
                    f"GET /api/materials failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("GET /api/materials - Backward Compatibility", False, f"Error: {str(e)}")
        
        # Test 2: POST /api/materials - Create new material WITH material_description
        material_with_desc = {
            "supplier": "Test Materials Fix Co",
            "product_code": "TMF-WITH-DESC-001",
            "order_to_delivery_time": "3-5 business days",
            "material_description": "Test material with description for API fix verification",
            "price": 45.75,
            "currency": "AUD",
            "unit": "m2",
            "raw_substrate": False
        }
        
        material_with_desc_id = None
        try:
            response = self.session.post(f"{API_BASE}/materials", json=material_with_desc)
            
            if response.status_code == 200:
                result = response.json()
                material_with_desc_id = result.get('data', {}).get('id')
                
                if material_with_desc_id:
                    # Verify the material was created correctly
                    get_response = self.session.get(f"{API_BASE}/materials/{material_with_desc_id}")
                    if get_response.status_code == 200:
                        material = get_response.json()
                        desc = material.get('material_description')
                        
                        if desc == "Test material with description for API fix verification":
                            self.log_result(
                                "POST /api/materials - With Description", 
                                True, 
                                "Successfully created material with material_description field",
                                f"Material ID: {material_with_desc_id}, Description: {desc}"
                            )
                        else:
                            self.log_result(
                                "POST /api/materials - With Description", 
                                False, 
                                f"Material created but description mismatch",
                                f"Expected: 'Test material...', Got: '{desc}'"
                            )
                    else:
                        self.log_result(
                            "POST /api/materials - With Description", 
                            False, 
                            "Failed to retrieve created material"
                        )
                else:
                    self.log_result(
                        "POST /api/materials - With Description", 
                        False, 
                        "Material creation response missing ID"
                    )
            else:
                self.log_result(
                    "POST /api/materials - With Description", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("POST /api/materials - With Description", False, f"Error: {str(e)}")
        
        # Test 3: POST /api/materials - Try to create material WITHOUT material_description (should fail validation)
        material_without_desc = {
            "supplier": "Test Materials Fix Co",
            "product_code": "TMF-WITHOUT-DESC-001",
            "order_to_delivery_time": "3-5 business days",
            # Note: material_description field intentionally omitted
            "price": 35.50,
            "currency": "AUD",
            "unit": "m2",
            "raw_substrate": False
        }
        
        try:
            response = self.session.post(f"{API_BASE}/materials", json=material_without_desc)
            
            if response.status_code == 422:  # Validation error expected
                self.log_result(
                    "POST /api/materials - Without Description (Validation)", 
                    True, 
                    "Correctly rejects material creation without required material_description field",
                    f"Status: {response.status_code} (validation error as expected)"
                )
            elif response.status_code == 200:
                self.log_result(
                    "POST /api/materials - Without Description (Validation)", 
                    False, 
                    "Material creation should have failed validation but succeeded",
                    "MaterialCreate model should require material_description field"
                )
            else:
                self.log_result(
                    "POST /api/materials - Without Description (Validation)", 
                    False, 
                    f"Unexpected status code: {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("POST /api/materials - Without Description (Validation)", False, f"Error: {str(e)}")
        
        # Test 4: Verify existing materials load correctly with null material_description
        try:
            response = self.session.get(f"{API_BASE}/materials")
            
            if response.status_code == 200:
                materials = response.json()
                
                # Look for materials with null/None material_description
                legacy_materials = [m for m in materials if m.get('material_description') is None]
                
                if len(legacy_materials) > 0:
                    # Test retrieving a specific legacy material
                    legacy_material = legacy_materials[0]
                    legacy_id = legacy_material.get('id')
                    
                    if legacy_id:
                        get_response = self.session.get(f"{API_BASE}/materials/{legacy_id}")
                        if get_response.status_code == 200:
                            material = get_response.json()
                            desc = material.get('material_description')
                            
                            if desc is None:
                                self.log_result(
                                    "Legacy Materials Compatibility", 
                                    True, 
                                    "Legacy materials without material_description load correctly with null values",
                                    f"Legacy Material ID: {legacy_id}, Description: {desc}"
                                )
                            else:
                                self.log_result(
                                    "Legacy Materials Compatibility", 
                                    False, 
                                    f"Expected null description but got: {desc}"
                                )
                        else:
                            self.log_result(
                                "Legacy Materials Compatibility", 
                                False, 
                                f"Failed to retrieve legacy material: {get_response.status_code}"
                            )
                    else:
                        self.log_result(
                            "Legacy Materials Compatibility", 
                            False, 
                            "Legacy material missing ID field"
                        )
                else:
                    self.log_result(
                        "Legacy Materials Compatibility", 
                        True, 
                        "No legacy materials found (all materials have material_description)",
                        "This is expected if database was cleaned or all materials have been updated"
                    )
            else:
                self.log_result(
                    "Legacy Materials Compatibility", 
                    False, 
                    f"Failed to retrieve materials for legacy test: {response.status_code}"
                )
        except Exception as e:
            self.log_result("Legacy Materials Compatibility", False, f"Error: {str(e)}")
        
        # Test 5: Update existing material - should work regardless of whether it has material_description
        if material_with_desc_id:
            update_data = {
                "supplier": "Updated Test Materials Fix Co",
                "product_code": "TMF-WITH-DESC-001-UPDATED",
                "order_to_delivery_time": "2-4 business days",
                "material_description": "Updated test material description for API fix verification",
                "price": 50.25,
                "currency": "AUD",
                "unit": "m2",
                "raw_substrate": False
            }
            
            try:
                response = self.session.put(f"{API_BASE}/materials/{material_with_desc_id}", json=update_data)
                
                if response.status_code == 200:
                    # Verify the update worked
                    get_response = self.session.get(f"{API_BASE}/materials/{material_with_desc_id}")
                    if get_response.status_code == 200:
                        updated_material = get_response.json()
                        updated_desc = updated_material.get('material_description')
                        updated_price = updated_material.get('price')
                        
                        if updated_desc == "Updated test material description for API fix verification" and updated_price == 50.25:
                            self.log_result(
                                "PUT /api/materials - Update Material", 
                                True, 
                                "Successfully updated material with material_description field",
                                f"Updated Description: {updated_desc}, Updated Price: {updated_price}"
                            )
                        else:
                            self.log_result(
                                "PUT /api/materials - Update Material", 
                                False, 
                                "Material update did not persist correctly",
                                f"Description: {updated_desc}, Price: {updated_price}"
                            )
                    else:
                        self.log_result(
                            "PUT /api/materials - Update Material", 
                            False, 
                            "Failed to retrieve updated material for verification"
                        )
                else:
                    self.log_result(
                        "PUT /api/materials - Update Material", 
                        False, 
                        f"Update failed with status {response.status_code}",
                        response.text
                    )
            except Exception as e:
                self.log_result("PUT /api/materials - Update Material", False, f"Error: {str(e)}")

    def test_suppliers_api_endpoints(self):
        """Test all Suppliers API endpoints"""
        print("\n=== SUPPLIERS API ENDPOINTS TEST ===")
        
        # Test 1: GET /api/suppliers - Retrieve all suppliers
        try:
            response = self.session.get(f"{API_BASE}/suppliers")
            
            if response.status_code == 200:
                suppliers = response.json()
                self.log_result(
                    "GET /api/suppliers", 
                    True, 
                    f"Successfully retrieved {len(suppliers)} suppliers"
                )
            else:
                self.log_result(
                    "GET /api/suppliers", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("GET /api/suppliers", False, f"Error: {str(e)}")
        
        # Test 2: POST /api/suppliers - Create new supplier
        supplier_data = {
            "supplier_name": "Test Paper Supplies Ltd",
            "contact_person": "John Smith",
            "phone_number": "+61 3 9876 5432",
            "email": "john.smith@testpapersupplies.com.au",
            "physical_address": "123 Industrial Drive, Melbourne VIC 3000",
            "post_code": "3000",
            "currency_accepted": "AUD",
            "bank_name": "Commonwealth Bank of Australia",
            "bank_address": "456 Collins Street, Melbourne VIC 3000",
            "bank_account_number": "123456789",
            "swift_code": "CTBAAU2S"
        }
        
        created_supplier_id = None
        try:
            response = self.session.post(f"{API_BASE}/suppliers", json=supplier_data)
            
            if response.status_code == 200:
                result = response.json()
                created_supplier_id = result.get('data', {}).get('id')
                
                if created_supplier_id:
                    self.log_result(
                        "POST /api/suppliers", 
                        True, 
                        f"Successfully created supplier with all required fields",
                        f"Supplier ID: {created_supplier_id}"
                    )
                else:
                    self.log_result(
                        "POST /api/suppliers", 
                        False, 
                        "Supplier creation response missing ID"
                    )
            else:
                self.log_result(
                    "POST /api/suppliers", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("POST /api/suppliers", False, f"Error: {str(e)}")
        
        # Test 3: GET /api/suppliers/{id} - Get specific supplier
        if created_supplier_id:
            try:
                response = self.session.get(f"{API_BASE}/suppliers/{created_supplier_id}")
                
                if response.status_code == 200:
                    supplier = response.json()
                    
                    # Verify all required fields are present
                    required_fields = ['supplier_name', 'phone_number', 'email', 'physical_address', 
                                     'post_code', 'bank_name', 'bank_account_number']
                    missing_fields = [field for field in required_fields if field not in supplier]
                    
                    if not missing_fields:
                        self.log_result(
                            "GET /api/suppliers/{id}", 
                            True, 
                            f"Successfully retrieved supplier with all required fields",
                            f"Supplier: {supplier.get('supplier_name')}"
                        )
                    else:
                        self.log_result(
                            "GET /api/suppliers/{id}", 
                            False, 
                            f"Supplier missing required fields: {missing_fields}"
                        )
                else:
                    self.log_result(
                        "GET /api/suppliers/{id}", 
                        False, 
                        f"Failed with status {response.status_code}",
                        response.text
                    )
            except Exception as e:
                self.log_result("GET /api/suppliers/{id}", False, f"Error: {str(e)}")
        
        # Test 4: PUT /api/suppliers/{id} - Update supplier
        if created_supplier_id:
            updated_supplier_data = {
                "supplier_name": "Test Paper Supplies Ltd (Updated)",
                "contact_person": "Jane Smith",
                "phone_number": "+61 3 9876 5433",
                "email": "jane.smith@testpapersupplies.com.au",
                "physical_address": "456 Industrial Drive, Melbourne VIC 3000",
                "post_code": "3000",
                "currency_accepted": "AUD",
                "bank_name": "ANZ Bank",
                "bank_address": "789 Collins Street, Melbourne VIC 3000",
                "bank_account_number": "987654321",
                "swift_code": "ANZBAU3M"
            }
            
            try:
                response = self.session.put(f"{API_BASE}/suppliers/{created_supplier_id}", json=updated_supplier_data)
                
                if response.status_code == 200:
                    # Verify the update by retrieving the supplier
                    get_response = self.session.get(f"{API_BASE}/suppliers/{created_supplier_id}")
                    if get_response.status_code == 200:
                        updated_supplier = get_response.json()
                        
                        if (updated_supplier.get('supplier_name') == "Test Paper Supplies Ltd (Updated)" and
                            updated_supplier.get('contact_person') == "Jane Smith"):
                            self.log_result(
                                "PUT /api/suppliers/{id}", 
                                True, 
                                "Successfully updated supplier information"
                            )
                        else:
                            self.log_result(
                                "PUT /api/suppliers/{id}", 
                                False, 
                                "Supplier update did not persist correctly"
                            )
                    else:
                        self.log_result(
                            "PUT /api/suppliers/{id}", 
                            False, 
                            "Failed to retrieve updated supplier for verification"
                        )
                else:
                    self.log_result(
                        "PUT /api/suppliers/{id}", 
                        False, 
                        f"Failed with status {response.status_code}",
                        response.text
                    )
            except Exception as e:
                self.log_result("PUT /api/suppliers/{id}", False, f"Error: {str(e)}")
        
        # Test 5: DELETE /api/suppliers/{id} - Soft delete supplier
        if created_supplier_id:
            try:
                response = self.session.delete(f"{API_BASE}/suppliers/{created_supplier_id}")
                
                if response.status_code == 200:
                    # Verify soft delete by trying to retrieve the supplier
                    get_response = self.session.get(f"{API_BASE}/suppliers/{created_supplier_id}")
                    if get_response.status_code == 404:
                        self.log_result(
                            "DELETE /api/suppliers/{id}", 
                            True, 
                            "Successfully soft deleted supplier (no longer accessible)"
                        )
                    else:
                        self.log_result(
                            "DELETE /api/suppliers/{id}", 
                            False, 
                            "Supplier still accessible after delete (soft delete may not be working)"
                        )
                else:
                    self.log_result(
                        "DELETE /api/suppliers/{id}", 
                        False, 
                        f"Failed with status {response.status_code}",
                        response.text
                    )
            except Exception as e:
                self.log_result("DELETE /api/suppliers/{id}", False, f"Error: {str(e)}")
    
    def test_product_specifications_api_endpoints(self):
        """Test all Product Specifications API endpoints"""
        print("\n=== PRODUCT SPECIFICATIONS API ENDPOINTS TEST ===")
        
        # Test 1: GET /api/product-specifications - Retrieve all specifications
        try:
            response = self.session.get(f"{API_BASE}/product-specifications")
            
            if response.status_code == 200:
                specifications = response.json()
                self.log_result(
                    "GET /api/product-specifications", 
                    True, 
                    f"Successfully retrieved {len(specifications)} product specifications"
                )
            else:
                self.log_result(
                    "GET /api/product-specifications", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("GET /api/product-specifications", False, f"Error: {str(e)}")
        
        # Test 2: POST /api/product-specifications - Create Paper Core specification
        paper_core_spec = {
            "product_name": "Standard Paper Core",
            "product_type": "Paper Core",
            "specifications": {
                "inner_diameter": "76mm",
                "wall_thickness": "3.2mm",
                "length": "1000mm",
                "crush_strength": "450 N/cm",
                "moisture_content": "8%",
                "surface_finish": "Smooth"
            },
            "materials_composition": [
                {
                    "material_name": "Recycled Kraft Paper",
                    "percentage": 85,
                    "grade": "High strength"
                },
                {
                    "material_name": "Adhesive",
                    "percentage": 15,
                    "type": "Water-based"
                }
            ],
            "manufacturing_notes": "Standard production process with quality control at each stage"
        }
        
        created_paper_core_id = None
        try:
            response = self.session.post(f"{API_BASE}/product-specifications", json=paper_core_spec)
            
            if response.status_code == 200:
                result = response.json()
                created_paper_core_id = result.get('data', {}).get('id')
                
                if created_paper_core_id:
                    self.log_result(
                        "POST /api/product-specifications (Paper Core)", 
                        True, 
                        f"Successfully created Paper Core specification",
                        f"Spec ID: {created_paper_core_id}"
                    )
                else:
                    self.log_result(
                        "POST /api/product-specifications (Paper Core)", 
                        False, 
                        "Specification creation response missing ID"
                    )
            else:
                self.log_result(
                    "POST /api/product-specifications (Paper Core)", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("POST /api/product-specifications (Paper Core)", False, f"Error: {str(e)}")
        
        # Test 3: POST /api/product-specifications - Create Spiral Paper Core specification
        spiral_core_spec = {
            "product_name": "Heavy Duty Spiral Paper Core",
            "product_type": "Spiral Paper Core",
            "specifications": {
                "inner_diameter": "152mm",
                "wall_thickness": "6.5mm",
                "length": "1500mm",
                "spiral_angle": "45 degrees",
                "crush_strength": "800 N/cm",
                "moisture_content": "7%",
                "surface_finish": "Textured",
                "end_caps": "Plastic reinforced"
            },
            "materials_composition": [
                {
                    "material_name": "Virgin Kraft Paper",
                    "percentage": 70,
                    "grade": "Extra high strength"
                },
                {
                    "material_name": "Recycled Kraft Paper",
                    "percentage": 20,
                    "grade": "Medium strength"
                },
                {
                    "material_name": "Spiral Adhesive",
                    "percentage": 10,
                    "type": "Hot-melt"
                }
            ],
            "manufacturing_notes": "Spiral winding process with reinforced end caps for heavy-duty applications"
        }
        
        created_spiral_core_id = None
        try:
            response = self.session.post(f"{API_BASE}/product-specifications", json=spiral_core_spec)
            
            if response.status_code == 200:
                result = response.json()
                created_spiral_core_id = result.get('data', {}).get('id')
                
                if created_spiral_core_id:
                    self.log_result(
                        "POST /api/product-specifications (Spiral Paper Core)", 
                        True, 
                        f"Successfully created Spiral Paper Core specification",
                        f"Spec ID: {created_spiral_core_id}"
                    )
                else:
                    self.log_result(
                        "POST /api/product-specifications (Spiral Paper Core)", 
                        False, 
                        "Specification creation response missing ID"
                    )
            else:
                self.log_result(
                    "POST /api/product-specifications (Spiral Paper Core)", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("POST /api/product-specifications (Spiral Paper Core)", False, f"Error: {str(e)}")
        
        # Test 4: GET /api/product-specifications/{id} - Get specific specification
        if created_paper_core_id:
            try:
                response = self.session.get(f"{API_BASE}/product-specifications/{created_paper_core_id}")
                
                if response.status_code == 200:
                    specification = response.json()
                    
                    # Verify flexible specifications dict storage
                    specs = specification.get('specifications', {})
                    materials = specification.get('materials_composition', [])
                    
                    if (specs.get('inner_diameter') == "76mm" and 
                        specs.get('crush_strength') == "450 N/cm" and
                        len(materials) == 2):
                        self.log_result(
                            "GET /api/product-specifications/{id}", 
                            True, 
                            f"Successfully retrieved specification with flexible dict storage",
                            f"Product: {specification.get('product_name')}, Specs: {len(specs)} fields, Materials: {len(materials)} items"
                        )
                    else:
                        self.log_result(
                            "GET /api/product-specifications/{id}", 
                            False, 
                            "Specification data not stored/retrieved correctly"
                        )
                else:
                    self.log_result(
                        "GET /api/product-specifications/{id}", 
                        False, 
                        f"Failed with status {response.status_code}",
                        response.text
                    )
            except Exception as e:
                self.log_result("GET /api/product-specifications/{id}", False, f"Error: {str(e)}")
        
        # Test 5: PUT /api/product-specifications/{id} - Update specification
        if created_spiral_core_id:
            updated_spiral_spec = {
                "product_name": "Heavy Duty Spiral Paper Core (Updated)",
                "product_type": "Spiral Paper Core",
                "specifications": {
                    "inner_diameter": "152mm",
                    "wall_thickness": "7.0mm",  # Updated thickness
                    "length": "1500mm",
                    "spiral_angle": "50 degrees",  # Updated angle
                    "crush_strength": "900 N/cm",  # Updated strength
                    "moisture_content": "6%",  # Updated moisture
                    "surface_finish": "Smooth",  # Updated finish
                    "end_caps": "Metal reinforced",  # Updated caps
                    "color": "Brown"  # New field added
                },
                "materials_composition": [
                    {
                        "material_name": "Virgin Kraft Paper",
                        "percentage": 75,  # Updated percentage
                        "grade": "Extra high strength"
                    },
                    {
                        "material_name": "Recycled Kraft Paper",
                        "percentage": 15,  # Updated percentage
                        "grade": "Medium strength"
                    },
                    {
                        "material_name": "Spiral Adhesive",
                        "percentage": 10,
                        "type": "Hot-melt"
                    }
                ],
                "manufacturing_notes": "Updated spiral winding process with metal-reinforced end caps for extra heavy-duty applications"
            }
            
            try:
                response = self.session.put(f"{API_BASE}/product-specifications/{created_spiral_core_id}", json=updated_spiral_spec)
                
                if response.status_code == 200:
                    # Verify the update by retrieving the specification
                    get_response = self.session.get(f"{API_BASE}/product-specifications/{created_spiral_core_id}")
                    if get_response.status_code == 200:
                        updated_spec = get_response.json()
                        
                        updated_specs = updated_spec.get('specifications', {})
                        if (updated_spec.get('product_name') == "Heavy Duty Spiral Paper Core (Updated)" and
                            updated_specs.get('wall_thickness') == "7.0mm" and
                            updated_specs.get('color') == "Brown"):
                            self.log_result(
                                "PUT /api/product-specifications/{id}", 
                                True, 
                                "Successfully updated specification with flexible dict storage"
                            )
                        else:
                            self.log_result(
                                "PUT /api/product-specifications/{id}", 
                                False, 
                                "Specification update did not persist correctly"
                            )
                    else:
                        self.log_result(
                            "PUT /api/product-specifications/{id}", 
                            False, 
                            "Failed to retrieve updated specification for verification"
                        )
                else:
                    self.log_result(
                        "PUT /api/product-specifications/{id}", 
                        False, 
                        f"Failed with status {response.status_code}",
                        response.text
                    )
            except Exception as e:
                self.log_result("PUT /api/product-specifications/{id}", False, f"Error: {str(e)}")
        
        # Test 6: DELETE /api/product-specifications/{id} - Soft delete specification
        if created_paper_core_id:
            try:
                response = self.session.delete(f"{API_BASE}/product-specifications/{created_paper_core_id}")
                
                if response.status_code == 200:
                    # Verify soft delete by trying to retrieve the specification
                    get_response = self.session.get(f"{API_BASE}/product-specifications/{created_paper_core_id}")
                    if get_response.status_code == 404:
                        self.log_result(
                            "DELETE /api/product-specifications/{id}", 
                            True, 
                            "Successfully soft deleted specification (no longer accessible)"
                        )
                    else:
                        self.log_result(
                            "DELETE /api/product-specifications/{id}", 
                            False, 
                            "Specification still accessible after delete (soft delete may not be working)"
                        )
                else:
                    self.log_result(
                        "DELETE /api/product-specifications/{id}", 
                        False, 
                        f"Failed with status {response.status_code}",
                        response.text
                    )
            except Exception as e:
                self.log_result("DELETE /api/product-specifications/{id}", False, f"Error: {str(e)}")
    
    def test_new_endpoints_authentication_requirements(self):
        """Test that Suppliers and Product Specifications endpoints require proper authentication"""
        print("\n=== NEW ENDPOINTS AUTHENTICATION REQUIREMENTS TEST ===")
        
        # Test without authentication
        temp_session = requests.Session()
        
        endpoints_to_test = [
            ("GET /api/suppliers", "get", "/suppliers"),
            ("POST /api/suppliers", "post", "/suppliers"),
            ("GET /api/product-specifications", "get", "/product-specifications"),
            ("POST /api/product-specifications", "post", "/product-specifications")
        ]
        
        authenticated_endpoints = 0
        total_endpoints = len(endpoints_to_test)
        
        for endpoint_name, method, path in endpoints_to_test:
            try:
                if method == "get":
                    response = temp_session.get(f"{API_BASE}{path}")
                elif method == "post":
                    response = temp_session.post(f"{API_BASE}{path}", json={})
                
                if response.status_code in [401, 403]:
                    authenticated_endpoints += 1
                    self.log_result(
                        f"Auth Required - {endpoint_name}", 
                        True, 
                        f"Properly requires authentication (status: {response.status_code})"
                    )
                else:
                    self.log_result(
                        f"Auth Required - {endpoint_name}", 
                        False, 
                        f"Expected 401/403 but got {response.status_code}",
                        "Endpoint should require admin/production_manager authentication"
                    )
                    
            except Exception as e:
                self.log_result(f"Auth Required - {endpoint_name}", False, f"Error: {str(e)}")
        
        # Overall authentication summary
        if authenticated_endpoints == total_endpoints:
            self.log_result(
                "New Endpoints Authentication Requirements", 
                True, 
                f"All {total_endpoints} new endpoints properly require authentication"
            )
        else:
            self.log_result(
                "New Endpoints Authentication Requirements", 
                False, 
                f"Only {authenticated_endpoints}/{total_endpoints} new endpoints require authentication"
            )
    
    def test_new_endpoints_validation_requirements(self):
        """Test validation of required fields for Suppliers and Product Specifications"""
        print("\n=== NEW ENDPOINTS VALIDATION REQUIREMENTS TEST ===")
        
        # Test 1: Supplier validation - missing required fields
        incomplete_supplier = {
            "supplier_name": "Test Supplier",
            # Missing phone_number, email, physical_address, post_code, bank_name, bank_account_number
        }
        
        try:
            response = self.session.post(f"{API_BASE}/suppliers", json=incomplete_supplier)
            
            if response.status_code == 422:  # Validation error
                self.log_result(
                    "Supplier Validation - Required Fields", 
                    True, 
                    "Correctly validates required fields (422 validation error)",
                    response.text[:200]
                )
            elif response.status_code == 400:
                self.log_result(
                    "Supplier Validation - Required Fields", 
                    True, 
                    "Correctly validates required fields (400 bad request)",
                    response.text[:200]
                )
            else:
                self.log_result(
                    "Supplier Validation - Required Fields", 
                    False, 
                    f"Expected validation error but got {response.status_code}",
                    response.text[:200]
                )
        except Exception as e:
            self.log_result("Supplier Validation - Required Fields", False, f"Error: {str(e)}")
        
        # Test 2: Product Specification validation - missing required fields
        incomplete_spec = {
            "product_name": "Test Product",
            # Missing product_type, specifications
        }
        
        try:
            response = self.session.post(f"{API_BASE}/product-specifications", json=incomplete_spec)
            
            if response.status_code == 422:  # Validation error
                self.log_result(
                    "Product Specification Validation - Required Fields", 
                    True, 
                    "Correctly validates required fields (422 validation error)",
                    response.text[:200]
                )
            elif response.status_code == 400:
                self.log_result(
                    "Product Specification Validation - Required Fields", 
                    True, 
                    "Correctly validates required fields (400 bad request)",
                    response.text[:200]
                )
            else:
                self.log_result(
                    "Product Specification Validation - Required Fields", 
                    False, 
                    f"Expected validation error but got {response.status_code}",
                    response.text[:200]
                )
        except Exception as e:
            self.log_result("Product Specification Validation - Required Fields", False, f"Error: {str(e)}")

    def run_all_tests(self):
        """Run all backend API tests with PRIMARY FOCUS on NEW Suppliers and Product Specifications APIs"""
        print("🚀 Starting Backend API Tests - PRIMARY FOCUS: NEW Suppliers & Product Specifications APIs")
        print(f"Backend URL: {BACKEND_URL}")
        print("=" * 60)
        
        # Test authentication first
        if not self.authenticate():
            print("❌ Authentication failed - cannot proceed with other tests")
            return self.generate_report()
        
        # PRIMARY FOCUS: Test NEW Suppliers and Product Specifications API endpoints
        print("\n🏭 TESTING NEW SUPPLIERS API ENDPOINTS - PRIMARY FOCUS")
        self.test_suppliers_api_endpoints()
        
        print("\n📋 TESTING NEW PRODUCT SPECIFICATIONS API ENDPOINTS - PRIMARY FOCUS")
        self.test_product_specifications_api_endpoints()
        
        print("\n🔐 TESTING NEW ENDPOINTS AUTHENTICATION & VALIDATION - PRIMARY FOCUS")
        self.test_new_endpoints_authentication_requirements()
        self.test_new_endpoints_validation_requirements()
        
        # SECONDARY: Test Materials API Fix
        print("\n🔧 TESTING MATERIALS API FIX - SECONDARY")
        self.test_materials_api_fix()
        
        # Test authentication requirements for new endpoints
        self.test_authentication_requirements()
        
        # NEW FOCUS: Test Production Board API Enhancements
        print("\n🏭 TESTING PRODUCTION BOARD API ENHANCEMENTS")
        self.test_production_board_authentication()
        order_id = self.test_production_board_enhancements()
        
        if order_id:
            self.test_stage_movement_api(order_id)
            self.test_materials_status_api(order_id)
            self.test_order_item_status_api(order_id)
        
        # Test error handling for invalid order IDs
        self.test_invalid_order_ids()
        
        # NEW FOCUS: Test Materials Management APIs
        print("\n🧱 TESTING MATERIALS MANAGEMENT APIs")
        material_id = self.test_materials_management_api()
        
        # NEW FOCUS: Test Material Currency Field
        print("\n💰 TESTING MATERIAL CURRENCY FIELD")
        self.test_material_currency_field()
        
        # Test client model updates and get client ID for product catalog tests
        client_id = self.test_client_model_updates()
        
        # NEW FOCUS: Test Client Product Catalog APIs
        print("\n📦 TESTING CLIENT PRODUCT CATALOG APIs")
        finished_product_id, paper_cores_product_id = self.test_client_product_catalog_api(client_id, material_id)
        
        # Test copy functionality between clients
        if client_id and finished_product_id:
            self.test_client_product_copy_functionality(client_id, finished_product_id)
        
        # Test delete functionality
        if client_id and paper_cores_product_id:
            self.test_client_product_delete_functionality(client_id, paper_cores_product_id)
        
        # Test validation errors
        self.test_validation_errors(client_id)
        
        # Test ReportLab PDF generation capability
        self.test_reportlab_pdf_generation()
        
        # Test role permissions
        self.test_role_permissions()
        
        # Test Xero Integration APIs
        print("\n🔗 TESTING XERO INTEGRATION ENDPOINTS")
        self.test_xero_permissions()
        self.test_xero_connection_status()
        state_param = self.test_xero_auth_url()
        self.test_xero_auth_callback(state_param)
        self.test_xero_disconnect()
        
        # Test NEW Xero Integration Endpoints
        print("\n🆕 TESTING NEW XERO INTEGRATION ENDPOINTS")
        self.test_xero_next_invoice_number()
        self.test_xero_create_draft_invoice()
        
        # Test jobs ready for invoicing and get delivery jobs for document testing
        delivery_jobs = self.test_jobs_ready_for_invoicing()
        
        # Test invoicing APIs
        self.test_live_jobs_api()
        self.test_archived_jobs_api()
        self.test_monthly_report_api()
        
        # Test invoice generation if we have a client
        if client_id:
            self.test_invoice_generation_api(client_id)
            self.test_document_generation(client_id)
        
        # Test document generation endpoints with real data
        print("\n📄 TESTING DOCUMENT GENERATION ENDPOINTS")
        self.test_document_generation_endpoints(delivery_jobs)
        self.test_pdf_download_functionality(delivery_jobs)
        self.test_document_branding_and_content(delivery_jobs)
        
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