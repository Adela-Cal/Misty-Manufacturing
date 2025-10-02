#!/usr/bin/env python3
"""
Xero Webhook Endpoints Testing Suite
Tests newly added webhook endpoints to resolve 'Response not 2XX' issue
"""

import requests
import json
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:8001')
API_BASE = f"{BACKEND_URL}/api"

class XeroWebhookTester:
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
    
    def test_xero_webhook_intent_to_receive(self):
        """Test GET /api/xero/webhook - Intent to receive verification"""
        print("\n=== XERO WEBHOOK INTENT TO RECEIVE TEST ===")
        
        try:
            response = self.session.get(f"{API_BASE}/xero/webhook")
            
            if response.status_code == 200:
                data = response.json()
                status = data.get('status')
                message = data.get('message')
                
                if status == 'ready':
                    self.log_result(
                        "Xero Webhook Intent to Receive", 
                        True, 
                        "✅ GET /api/xero/webhook returns 200 OK - Intent to receive satisfied",
                        f"Status: {status}, Message: {message}"
                    )
                else:
                    self.log_result(
                        "Xero Webhook Intent to Receive", 
                        False, 
                        f"❌ Unexpected status in response: {status}",
                        f"Expected 'ready', got: {status}"
                    )
            else:
                self.log_result(
                    "Xero Webhook Intent to Receive", 
                    False, 
                    f"❌ GET /api/xero/webhook failed with status {response.status_code}",
                    f"Expected 200 OK for 'Intent to receive', got: {response.status_code}"
                )
                
        except Exception as e:
            self.log_result("Xero Webhook Intent to Receive", False, f"Error: {str(e)}")
    
    def test_xero_webhook_post_endpoint(self):
        """Test POST /api/xero/webhook - Webhook notification acceptance"""
        print("\n=== XERO WEBHOOK POST ENDPOINT TEST ===")
        
        try:
            # Simulate a Xero webhook notification payload
            webhook_payload = {
                "events": [
                    {
                        "resourceUrl": "https://api.xero.com/api.xro/2.0/Invoices/12345",
                        "resourceId": "12345",
                        "eventDateUtc": "2024-01-15T10:30:00.000Z",
                        "eventType": "CREATE",
                        "eventCategory": "INVOICE",
                        "tenantId": "test-tenant-id",
                        "tenantType": "ORGANISATION"
                    }
                ],
                "lastEventSequence": 1,
                "firstEventSequence": 1,
                "entropy": "test-entropy-value"
            }
            
            # Add webhook signature header (Xero uses this for verification)
            headers = {
                'X-Xero-Signature': 'test-signature-value',
                'Content-Type': 'application/json'
            }
            
            response = self.session.post(
                f"{API_BASE}/xero/webhook", 
                json=webhook_payload,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_result(
                    "Xero Webhook POST Endpoint", 
                    True, 
                    "✅ POST /api/xero/webhook accepts webhook notifications successfully",
                    f"Response: {data}"
                )
            elif response.status_code == 202:
                # 202 Accepted is also valid for webhook endpoints
                self.log_result(
                    "Xero Webhook POST Endpoint", 
                    True, 
                    "✅ POST /api/xero/webhook accepts webhook notifications (202 Accepted)",
                    "Webhook accepted for processing"
                )
            else:
                self.log_result(
                    "Xero Webhook POST Endpoint", 
                    False, 
                    f"❌ POST /api/xero/webhook failed with status {response.status_code}",
                    f"Expected 200 or 202, got: {response.status_code}, Response: {response.text}"
                )
                
        except Exception as e:
            self.log_result("Xero Webhook POST Endpoint", False, f"Error: {str(e)}")
    
    def test_xero_callback_endpoint_accessibility(self):
        """Test GET /api/xero/callback - Callback endpoint accessibility"""
        print("\n=== XERO CALLBACK ENDPOINT ACCESSIBILITY TEST ===")
        
        try:
            # Test callback endpoint without parameters (should handle gracefully)
            response = self.session.get(f"{API_BASE}/xero/callback")
            
            # The callback endpoint should be accessible and handle the request
            # It might return an error for missing parameters, but should not return 404
            if response.status_code in [200, 400, 422]:
                self.log_result(
                    "Xero Callback Endpoint Accessibility", 
                    True, 
                    f"✅ GET /api/xero/callback is accessible (status: {response.status_code})",
                    "Callback endpoint is properly configured and reachable"
                )
            elif response.status_code == 404:
                self.log_result(
                    "Xero Callback Endpoint Accessibility", 
                    False, 
                    "❌ GET /api/xero/callback returns 404 - endpoint not found",
                    "Callback URL configuration issue - endpoint not properly registered"
                )
            else:
                self.log_result(
                    "Xero Callback Endpoint Accessibility", 
                    True, 
                    f"✅ GET /api/xero/callback is accessible (status: {response.status_code})",
                    f"Endpoint responds with status: {response.status_code}"
                )
            
            # Test callback endpoint with sample OAuth parameters
            test_params = {
                'code': 'test-auth-code',
                'state': 'test-state-value',
                'scope': 'accounting.transactions'
            }
            
            response_with_params = self.session.get(f"{API_BASE}/xero/callback", params=test_params)
            
            if response_with_params.status_code in [200, 302, 400, 422]:
                self.log_result(
                    "Xero Callback Endpoint with Parameters", 
                    True, 
                    f"✅ GET /api/xero/callback handles OAuth parameters (status: {response_with_params.status_code})",
                    "Callback endpoint properly processes OAuth flow parameters"
                )
            else:
                self.log_result(
                    "Xero Callback Endpoint with Parameters", 
                    False, 
                    f"❌ GET /api/xero/callback failed with OAuth parameters: {response_with_params.status_code}",
                    response_with_params.text
                )
                
        except Exception as e:
            self.log_result("Xero Callback Endpoint Accessibility", False, f"Error: {str(e)}")
    
    def test_xero_webhook_url_configuration(self):
        """Test that webhook URLs are correctly configured for the production domain"""
        print("\n=== XERO WEBHOOK URL CONFIGURATION TEST ===")
        
        try:
            # Test the debug endpoint to verify URL configuration
            response = self.session.get(f"{API_BASE}/xero/debug")
            
            if response.status_code == 200:
                debug_data = response.json()
                callback_url = debug_data.get('callback_url')
                frontend_url = debug_data.get('frontend_url')
                
                expected_domain = 'manufactxero.preview.emergentagent.com'
                expected_callback = f'https://{expected_domain}/api/xero/callback'
                expected_frontend = f'https://{expected_domain}'
                
                # Check callback URL
                if callback_url == expected_callback:
                    self.log_result(
                        "Xero Webhook URL Configuration - Callback URL", 
                        True, 
                        f"✅ Callback URL correctly configured: {callback_url}",
                        f"Matches expected domain: {expected_domain}"
                    )
                else:
                    self.log_result(
                        "Xero Webhook URL Configuration - Callback URL", 
                        False, 
                        f"❌ Incorrect callback URL: {callback_url}",
                        f"Expected: {expected_callback}, Got: {callback_url}"
                    )
                
                # Check frontend URL
                if frontend_url == expected_frontend:
                    self.log_result(
                        "Xero Webhook URL Configuration - Frontend URL", 
                        True, 
                        f"✅ Frontend URL correctly configured: {frontend_url}",
                        f"Matches expected domain: {expected_domain}"
                    )
                else:
                    self.log_result(
                        "Xero Webhook URL Configuration - Frontend URL", 
                        False, 
                        f"❌ Incorrect frontend URL: {frontend_url}",
                        f"Expected: {expected_frontend}, Got: {frontend_url}"
                    )
                
                # Verify no old domain references
                old_domain = 'machinery-timesheet.preview.emergentagent.com'
                if old_domain not in str(debug_data):
                    self.log_result(
                        "Xero Webhook URL Configuration - Old Domain Check", 
                        True, 
                        f"✅ No references to old domain found",
                        f"Old domain '{old_domain}' successfully removed from configuration"
                    )
                else:
                    self.log_result(
                        "Xero Webhook URL Configuration - Old Domain Check", 
                        False, 
                        f"❌ Old domain still referenced in configuration",
                        f"Found references to old domain: {old_domain}"
                    )
                    
            else:
                self.log_result(
                    "Xero Webhook URL Configuration", 
                    False, 
                    f"Failed to access debug endpoint: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Xero Webhook URL Configuration", False, f"Error: {str(e)}")
    
    def run_xero_webhook_tests(self):
        """Run comprehensive Xero webhook endpoint tests"""
        print("\n" + "="*60)
        print("XERO WEBHOOK ENDPOINTS TESTING")
        print("Testing newly added webhook endpoints to resolve 'Response not 2XX' issue")
        print("="*60)
        
        # Step 1: Authenticate
        if not self.authenticate():
            print("❌ Authentication failed - cannot proceed with tests")
            return
        
        # Step 2: Test webhook intent to receive (GET endpoint)
        self.test_xero_webhook_intent_to_receive()
        
        # Step 3: Test webhook notification acceptance (POST endpoint)
        self.test_xero_webhook_post_endpoint()
        
        # Step 4: Test callback endpoint accessibility
        self.test_xero_callback_endpoint_accessibility()
        
        # Step 5: Test URL configuration
        self.test_xero_webhook_url_configuration()
        
        # Print summary
        self.print_xero_webhook_summary()
    
    def print_xero_webhook_summary(self):
        """Print summary focused on Xero webhook testing"""
        print("\n" + "="*60)
        print("XERO WEBHOOK ENDPOINTS TEST SUMMARY")
        print("="*60)
        
        webhook_tests = [r for r in self.test_results if 'webhook' in r['test'].lower() or 'callback' in r['test'].lower()]
        
        if not webhook_tests:
            print("No webhook tests found in results")
            return
        
        total_tests = len(webhook_tests)
        passed_tests = len([r for r in webhook_tests if r['success']])
        failed_tests = total_tests - passed_tests
        
        print(f"Webhook Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%" if total_tests > 0 else "0%")
        
        print("\n" + "-"*60)
        print("WEBHOOK ENDPOINT RESULTS:")
        print("-"*60)
        
        for result in webhook_tests:
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"{status}: {result['message']}")
            if result['details'] and not result['success']:
                print(f"    Details: {result['details']}")
        
        print("\n" + "="*60)
        print("XERO DEVELOPER CONSOLE RESOLUTION:")
        print("="*60)
        
        # Check specific issues mentioned in review request
        intent_test = next((r for r in webhook_tests if 'intent to receive' in r['test'].lower()), None)
        post_test = next((r for r in webhook_tests if 'post endpoint' in r['test'].lower()), None)
        callback_test = next((r for r in webhook_tests if 'callback' in r['test'].lower()), None)
        
        if intent_test and intent_test['success']:
            print("✅ GET /api/xero/webhook returns 200 OK - 'Intent to receive' requirement satisfied")
        else:
            print("❌ GET /api/xero/webhook failing - 'Intent to receive' requirement NOT satisfied")
        
        if post_test and post_test['success']:
            print("✅ POST /api/xero/webhook accepts notifications - webhook delivery should work")
        else:
            print("❌ POST /api/xero/webhook failing - webhook notifications may be rejected")
        
        if callback_test and callback_test['success']:
            print("✅ /api/xero/callback endpoint accessible - OAuth flow should work")
        else:
            print("❌ /api/xero/callback endpoint issues - OAuth flow may fail")
        
        # Overall assessment
        if passed_tests == total_tests:
            print("\n🎉 SUCCESS: All webhook endpoints working correctly!")
            print("🎉 The 'Response not 2XX' issue in Xero Developer console should be RESOLVED")
            print("🎉 Webhook Status should change from 'Intent to receive required' to active")
        elif passed_tests >= total_tests * 0.75:
            print("\n⚠️  PARTIAL SUCCESS: Most webhook endpoints working")
            print("⚠️  Some issues may remain in Xero Developer console")
        else:
            print("\n❌ FAILURE: Major webhook endpoint issues detected")
            print("❌ 'Response not 2XX' issue likely NOT resolved")
            print("❌ Xero Developer console will continue showing errors")
        
        print("\n" + "="*60)

if __name__ == "__main__":
    tester = XeroWebhookTester()
    tester.run_xero_webhook_tests()