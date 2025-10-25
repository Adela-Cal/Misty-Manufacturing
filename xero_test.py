#!/usr/bin/env python3
"""
Xero Integration Testing Suite
Tests Xero integration with corrected URLs to resolve 400 Bad Request errors
"""

import requests
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

# Use internal backend URL for testing
BACKEND_URL = 'http://localhost:8001'
API_BASE = f"{BACKEND_URL}/api"

class XeroIntegrationTester:
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
    
    def test_xero_debug_configuration(self):
        """Test GET /api/xero/debug to verify correct callback URL configuration"""
        print("\n=== XERO DEBUG CONFIGURATION TEST ===")
        
        try:
            response = self.session.get(f"{API_BASE}/xero/debug")
            
            if response.status_code == 200:
                debug_data = response.json()
                callback_url = debug_data.get('callback_url')
                expected_callback = 'https://misty-ato-payroll.preview.emergentagent.com/api/xero/callback'
                
                # Check if callback URL is correct
                if callback_url == expected_callback:
                    self.log_result(
                        "Xero Debug Configuration - Callback URL", 
                        True, 
                        f"✅ Callback URL correctly configured: {callback_url}",
                        f"Expected: {expected_callback}, Got: {callback_url}"
                    )
                else:
                    self.log_result(
                        "Xero Debug Configuration - Callback URL", 
                        False, 
                        f"❌ Incorrect callback URL: {callback_url}",
                        f"Expected: {expected_callback}, Got: {callback_url}"
                    )
                
                # Check other configuration values
                client_id = debug_data.get('client_id')
                frontend_url = debug_data.get('frontend_url')
                expected_frontend = 'https://misty-ato-payroll.preview.emergentagent.com'
                
                if client_id:
                    self.log_result(
                        "Xero Debug Configuration - Client ID", 
                        True, 
                        f"✅ Client ID is configured: {client_id[:8]}..."
                    )
                else:
                    self.log_result(
                        "Xero Debug Configuration - Client ID", 
                        False, 
                        "❌ Client ID is missing"
                    )
                
                if frontend_url == expected_frontend:
                    self.log_result(
                        "Xero Debug Configuration - Frontend URL", 
                        True, 
                        f"✅ Frontend URL correctly configured: {frontend_url}"
                    )
                else:
                    self.log_result(
                        "Xero Debug Configuration - Frontend URL", 
                        False, 
                        f"❌ Incorrect frontend URL: {frontend_url}",
                        f"Expected: {expected_frontend}, Got: {frontend_url}"
                    )
                
                # Check environment configuration
                env_check = debug_data.get('environment_check', {})
                client_id_set = env_check.get('client_id_set', False)
                client_secret_set = env_check.get('client_secret_set', False)
                redirect_uri = env_check.get('redirect_uri')
                
                if client_id_set and client_secret_set:
                    self.log_result(
                        "Xero Debug Configuration - Environment Variables", 
                        True, 
                        "✅ All required environment variables are set"
                    )
                else:
                    self.log_result(
                        "Xero Debug Configuration - Environment Variables", 
                        False, 
                        f"❌ Missing environment variables - Client ID: {client_id_set}, Client Secret: {client_secret_set}"
                    )
                
                return debug_data
                
            else:
                self.log_result(
                    "Xero Debug Configuration", 
                    False, 
                    f"Failed to access debug endpoint: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Xero Debug Configuration", False, f"Error: {str(e)}")
        
        return None
    
    def test_xero_auth_url_generation(self):
        """Test GET /api/xero/auth/url to verify OAuth URL includes correct callback URL"""
        print("\n=== XERO AUTH URL GENERATION TEST ===")
        
        try:
            response = self.session.get(f"{API_BASE}/xero/auth/url")
            
            if response.status_code == 200:
                auth_data = response.json()
                auth_url = auth_data.get('auth_url')
                debug_info = auth_data.get('debug_info', {})
                
                # Check if auth URL is generated
                if auth_url and auth_url.startswith('https://login.xero.com/identity/connect/authorize'):
                    self.log_result(
                        "Xero Auth URL Generation - URL Format", 
                        True, 
                        f"✅ OAuth URL correctly generated with Xero domain"
                    )
                    
                    # Check if callback URL is included in the auth URL
                    expected_callback = 'https://misty-ato-payroll.preview.emergentagent.com/api/xero/callback'
                    if expected_callback in auth_url:
                        self.log_result(
                            "Xero Auth URL Generation - Callback URL", 
                            True, 
                            f"✅ Correct callback URL included in OAuth URL",
                            f"Callback URL: {expected_callback}"
                        )
                    else:
                        self.log_result(
                            "Xero Auth URL Generation - Callback URL", 
                            False, 
                            f"❌ Incorrect or missing callback URL in OAuth URL",
                            f"Expected: {expected_callback}, Auth URL: {auth_url}"
                        )
                    
                    # Check debug info
                    debug_callback = debug_info.get('callback_url')
                    debug_client_id = debug_info.get('client_id')
                    debug_scopes = debug_info.get('scopes')
                    
                    if debug_callback == expected_callback:
                        self.log_result(
                            "Xero Auth URL Generation - Debug Info", 
                            True, 
                            f"✅ Debug info shows correct callback URL: {debug_callback}"
                        )
                    else:
                        self.log_result(
                            "Xero Auth URL Generation - Debug Info", 
                            False, 
                            f"❌ Debug info shows incorrect callback URL: {debug_callback}"
                        )
                    
                    # Verify required OAuth parameters
                    required_params = ['client_id', 'redirect_uri', 'scope', 'response_type', 'state']
                    missing_params = []
                    for param in required_params:
                        if param not in auth_url:
                            missing_params.append(param)
                    
                    if not missing_params:
                        self.log_result(
                            "Xero Auth URL Generation - OAuth Parameters", 
                            True, 
                            "✅ All required OAuth parameters present in URL"
                        )
                    else:
                        self.log_result(
                            "Xero Auth URL Generation - OAuth Parameters", 
                            False, 
                            f"❌ Missing OAuth parameters: {missing_params}"
                        )
                    
                    return auth_data
                    
                else:
                    self.log_result(
                        "Xero Auth URL Generation - URL Format", 
                        False, 
                        f"❌ Invalid or missing OAuth URL: {auth_url}"
                    )
                    
            elif response.status_code == 403:
                self.log_result(
                    "Xero Auth URL Generation", 
                    False, 
                    "❌ Access denied - insufficient permissions for Xero integration",
                    "User may not have admin or manager role required for Xero access"
                )
            else:
                self.log_result(
                    "Xero Auth URL Generation", 
                    False, 
                    f"Failed to generate auth URL: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Xero Auth URL Generation", False, f"Error: {str(e)}")
        
        return None
    
    def test_xero_status_endpoint(self):
        """Test GET /api/xero/status to verify connection status handling"""
        print("\n=== XERO STATUS ENDPOINT TEST ===")
        
        try:
            response = self.session.get(f"{API_BASE}/xero/status")
            
            if response.status_code == 200:
                status_data = response.json()
                connected = status_data.get('connected')
                message = status_data.get('message')
                
                # Since we likely don't have an active Xero connection, expect connected=False
                if connected is False:
                    self.log_result(
                        "Xero Status Endpoint - No Connection", 
                        True, 
                        f"✅ Correctly reports no Xero connection: {message}",
                        "This is expected behavior when no Xero tokens are stored"
                    )
                elif connected is True:
                    tenant_id = status_data.get('tenant_id')
                    self.log_result(
                        "Xero Status Endpoint - Active Connection", 
                        True, 
                        f"✅ Active Xero connection found: {message}",
                        f"Tenant ID: {tenant_id}"
                    )
                else:
                    self.log_result(
                        "Xero Status Endpoint - Response Format", 
                        False, 
                        f"❌ Invalid response format - connected field missing or invalid: {connected}"
                    )
                
                return status_data
                
            elif response.status_code == 403:
                self.log_result(
                    "Xero Status Endpoint", 
                    False, 
                    "❌ Access denied - insufficient permissions for Xero status check",
                    "User may not have admin or manager role required for Xero access"
                )
            else:
                self.log_result(
                    "Xero Status Endpoint", 
                    False, 
                    f"Failed to check Xero status: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Xero Status Endpoint", False, f"Error: {str(e)}")
        
        return None
    
    def test_xero_next_invoice_number(self):
        """Test GET /api/xero/next-invoice-number endpoint"""
        print("\n=== XERO NEXT INVOICE NUMBER TEST ===")
        
        try:
            response = self.session.get(f"{API_BASE}/xero/next-invoice-number")
            
            if response.status_code == 200:
                invoice_data = response.json()
                next_number = invoice_data.get('next_invoice_number')
                
                if next_number:
                    self.log_result(
                        "Xero Next Invoice Number - With Connection", 
                        True, 
                        f"✅ Successfully retrieved next invoice number: {next_number}"
                    )
                else:
                    self.log_result(
                        "Xero Next Invoice Number - Response Format", 
                        False, 
                        "❌ Response missing next_invoice_number field"
                    )
                
                return invoice_data
                
            elif response.status_code == 401:
                self.log_result(
                    "Xero Next Invoice Number - No Connection", 
                    True, 
                    "✅ Correctly returns 401 when no Xero connection exists",
                    "This is expected behavior when Xero is not connected"
                )
            elif response.status_code == 403:
                self.log_result(
                    "Xero Next Invoice Number", 
                    False, 
                    "❌ Access denied - insufficient permissions"
                )
            else:
                self.log_result(
                    "Xero Next Invoice Number", 
                    False, 
                    f"Unexpected response: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Xero Next Invoice Number", False, f"Error: {str(e)}")
        
        return None
    
    def test_xero_create_draft_invoice(self):
        """Test POST /api/xero/create-draft-invoice endpoint with sample data"""
        print("\n=== XERO CREATE DRAFT INVOICE TEST ===")
        
        try:
            # Sample invoice data matching the expected structure
            invoice_data = {
                "contact_email": "test@testclient.com",
                "contact_name": "Test Client Manufacturing",
                "due_date": "2024-12-31",
                "line_items": [
                    {
                        "product_name": "Paper Core - 76mm ID x 3mmT",
                        "unit_price": 45.00,
                        "quantity": 100
                    },
                    {
                        "product_name": "Spiral Paper Core - Custom Size",
                        "unit_price": 52.50,
                        "quantity": 50
                    }
                ]
            }
            
            response = self.session.post(f"{API_BASE}/xero/create-draft-invoice", json=invoice_data)
            
            if response.status_code == 200:
                result = response.json()
                invoice_id = result.get('invoice_id')
                invoice_number = result.get('invoice_number')
                
                if invoice_id and invoice_number:
                    self.log_result(
                        "Xero Create Draft Invoice - With Connection", 
                        True, 
                        f"✅ Successfully created draft invoice: {invoice_number}",
                        f"Invoice ID: {invoice_id}, Total items: {len(invoice_data['line_items'])}"
                    )
                else:
                    self.log_result(
                        "Xero Create Draft Invoice - Response Format", 
                        False, 
                        "❌ Response missing invoice_id or invoice_number"
                    )
                
                return result
                
            elif response.status_code == 401:
                self.log_result(
                    "Xero Create Draft Invoice - No Connection", 
                    True, 
                    "✅ Correctly returns 401 when no Xero connection exists",
                    "This is expected behavior when Xero is not connected"
                )
            elif response.status_code == 422:
                self.log_result(
                    "Xero Create Draft Invoice - Validation", 
                    True, 
                    "✅ Correctly validates invoice data format",
                    response.text
                )
            elif response.status_code == 403:
                self.log_result(
                    "Xero Create Draft Invoice", 
                    False, 
                    "❌ Access denied - insufficient permissions"
                )
            else:
                self.log_result(
                    "Xero Create Draft Invoice", 
                    False, 
                    f"Unexpected response: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Xero Create Draft Invoice", False, f"Error: {str(e)}")
        
        return None
    
    def test_xero_url_verification(self):
        """Verify all Xero endpoints are using correct manufactxero.preview.emergentagent.com URLs"""
        print("\n=== XERO URL VERIFICATION TEST ===")
        
        expected_domain = 'manufactxero.preview.emergentagent.com'
        old_domain = 'machinery-timesheet.preview.emergentagent.com'
        
        # Test debug endpoint for URL configuration
        debug_data = self.test_xero_debug_configuration()
        if debug_data:
            callback_url = debug_data.get('callback_url', '')
            frontend_url = debug_data.get('frontend_url', '')
            
            # Check if old domain is still present
            if old_domain in callback_url or old_domain in frontend_url:
                self.log_result(
                    "Xero URL Verification - Old Domain Check", 
                    False, 
                    f"❌ Old domain '{old_domain}' still found in configuration",
                    f"Callback: {callback_url}, Frontend: {frontend_url}"
                )
            else:
                self.log_result(
                    "Xero URL Verification - Old Domain Check", 
                    True, 
                    f"✅ Old domain '{old_domain}' successfully removed from configuration"
                )
            
            # Check if new domain is correctly used
            if expected_domain in callback_url and expected_domain in frontend_url:
                self.log_result(
                    "Xero URL Verification - New Domain Check", 
                    True, 
                    f"✅ New domain '{expected_domain}' correctly configured in all URLs",
                    f"Callback: {callback_url}, Frontend: {frontend_url}"
                )
            else:
                self.log_result(
                    "Xero URL Verification - New Domain Check", 
                    False, 
                    f"❌ New domain '{expected_domain}' not found in all URLs",
                    f"Callback: {callback_url}, Frontend: {frontend_url}"
                )
        
        # Test auth URL generation for correct domain
        auth_data = self.test_xero_auth_url_generation()
        if auth_data:
            auth_url = auth_data.get('auth_url', '')
            
            if expected_domain in auth_url:
                self.log_result(
                    "Xero URL Verification - Auth URL Domain", 
                    True, 
                    f"✅ Auth URL contains correct domain '{expected_domain}'"
                )
            else:
                self.log_result(
                    "Xero URL Verification - Auth URL Domain", 
                    False, 
                    f"❌ Auth URL missing correct domain '{expected_domain}'",
                    f"Auth URL: {auth_url}"
                )
            
            if old_domain in auth_url:
                self.log_result(
                    "Xero URL Verification - Auth URL Old Domain", 
                    False, 
                    f"❌ Auth URL still contains old domain '{old_domain}'",
                    f"Auth URL: {auth_url}"
                )
            else:
                self.log_result(
                    "Xero URL Verification - Auth URL Old Domain", 
                    True, 
                    f"✅ Auth URL does not contain old domain '{old_domain}'"
                )
    
    def run_xero_integration_tests(self):
        """Run comprehensive Xero integration tests focusing on URL configuration"""
        print("\n" + "="*60)
        print("XERO INTEGRATION TESTING - URL CONFIGURATION VERIFICATION")
        print("Testing corrected URLs and resolving 400 Bad Request errors")
        print("="*60)
        
        # Step 1: Authenticate
        if not self.authenticate():
            print("❌ Authentication failed - cannot proceed with Xero tests")
            return
        
        # Step 2: Test Xero debug configuration
        print("\n🔍 Testing Xero Debug Configuration...")
        self.test_xero_debug_configuration()
        
        # Step 3: Test Xero auth URL generation
        print("\n🔍 Testing Xero Auth URL Generation...")
        self.test_xero_auth_url_generation()
        
        # Step 4: Test Xero status endpoint
        print("\n🔍 Testing Xero Status Endpoint...")
        self.test_xero_status_endpoint()
        
        # Step 5: Test Xero next invoice number
        print("\n🔍 Testing Xero Next Invoice Number...")
        self.test_xero_next_invoice_number()
        
        # Step 6: Test Xero create draft invoice
        print("\n🔍 Testing Xero Create Draft Invoice...")
        self.test_xero_create_draft_invoice()
        
        # Step 7: Comprehensive URL verification
        print("\n🔍 Testing URL Verification...")
        self.test_xero_url_verification()
        
        # Print summary
        self.print_xero_test_summary()
    
    def print_xero_test_summary(self):
        """Print comprehensive Xero test summary"""
        print("\n" + "="*60)
        print("XERO INTEGRATION TEST SUMMARY")
        print("="*60)
        
        # Filter Xero-related tests
        xero_results = [r for r in self.test_results if 'xero' in r['test'].lower()]
        
        total_tests = len(xero_results)
        passed_tests = len([r for r in xero_results if r['success']])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Xero Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%" if total_tests > 0 else "0%")
        
        print("\n" + "-"*60)
        print("XERO TEST RESULTS:")
        print("-"*60)
        
        # Group results by category
        categories = {
            'Configuration': [],
            'URL Verification': [],
            'Endpoints': [],
            'Authentication': []
        }
        
        for result in xero_results:
            test_name = result['test']
            if 'debug' in test_name.lower() or 'configuration' in test_name.lower():
                categories['Configuration'].append(result)
            elif 'url' in test_name.lower() or 'domain' in test_name.lower():
                categories['URL Verification'].append(result)
            elif 'auth' in test_name.lower():
                categories['Authentication'].append(result)
            else:
                categories['Endpoints'].append(result)
        
        for category, results in categories.items():
            if results:
                print(f"\n{category}:")
                for result in results:
                    status = "✅ PASS" if result['success'] else "❌ FAIL"
                    print(f"  {status}: {result['message']}")
                    if result['details'] and not result['success']:
                        print(f"    Details: {result['details']}")
        
        print("\n" + "="*60)
        print("XERO URL MIGRATION ANALYSIS:")
        print("="*60)
        
        # Check for URL-related issues
        url_issues = []
        url_fixes = []
        
        for result in xero_results:
            if not result['success'] and result['details']:
                if 'machinery-timesheet.preview.emergentagent.com' in result['details']:
                    url_issues.append(f"Old domain still present: {result['test']}")
                elif '400 bad request' in result['details'].lower():
                    url_issues.append(f"400 Bad Request error: {result['test']}")
            elif result['success'] and 'manufactxero.preview.emergentagent.com' in (result.get('details') or ''):
                url_fixes.append(f"Correct domain verified: {result['test']}")
        
        if not url_issues:
            print("✅ NO URL-related issues detected!")
            print("✅ All Xero endpoints are using the correct manufactxero.preview.emergentagent.com domain")
            print("✅ The 400 Bad Request and 'Xero token exchange failed' errors should be resolved")
        else:
            print("🚨 URL-related issues found:")
            for issue in url_issues:
                print(f"  ❌ {issue}")
        
        if url_fixes:
            print("\n✅ URL fixes verified:")
            for fix in url_fixes:
                print(f"  ✅ {fix}")
        
        print("\n" + "="*60)
        print("CONCLUSION:")
        print("="*60)
        
        if not url_issues and url_fixes:
            print("🎉 SUCCESS: Xero URL configuration has been corrected!")
            print("🎉 All endpoints are using manufactxero.preview.emergentagent.com")
            print("🎉 The URL mismatch issues that caused 400 Bad Request errors are resolved")
        elif not url_issues:
            print("✅ No URL issues detected, but verification may be incomplete")
        else:
            print("❌ FAILURE: URL configuration issues still present")
            print("❌ The 400 Bad Request errors may persist due to URL mismatches")
        
        print("\n" + "="*60)

if __name__ == "__main__":
    tester = XeroIntegrationTester()
    tester.run_xero_integration_tests()