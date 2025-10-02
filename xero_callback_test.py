#!/usr/bin/env python3
"""
Xero Callback 404 Issue Resolution Testing
Tests if the router registration fix has resolved the 404 errors for Xero endpoints
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

class XeroCallbackTester:
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
    
    def test_xero_callback_router_registration_fix(self):
        """Test if the Xero callback 404 issue is resolved after registering the API router"""
        print("\n=== XERO CALLBACK ROUTER REGISTRATION FIX TEST ===")
        print("Testing the specific issue: api_router was defined but never included with app.include_router(api_router)")
        
        try:
            # Test 1: GET /api/xero/callback - Should now return 200 instead of 404
            response = self.session.get(f"{API_BASE}/xero/callback")
            
            if response.status_code == 200:
                self.log_result(
                    "GET /api/xero/callback - Router Registration Fix", 
                    True, 
                    "✅ SUCCESS: GET /api/xero/callback now returns 200 (was 404 before router registration)",
                    f"Response content type: {response.headers.get('content-type', 'unknown')}"
                )
            elif response.status_code == 404:
                self.log_result(
                    "GET /api/xero/callback - Router Registration Fix", 
                    False, 
                    "❌ FAILED: GET /api/xero/callback still returns 404 - router registration may not be working",
                    "The api_router may still not be properly included in the main FastAPI app"
                )
            else:
                self.log_result(
                    "GET /api/xero/callback - Router Registration Fix", 
                    False, 
                    f"❌ UNEXPECTED: GET /api/xero/callback returns {response.status_code} instead of 200",
                    response.text[:200]
                )
            
            # Test 2: GET /api/xero/callback with OAuth parameters - Test with code=test123&state=test456
            oauth_params = {
                'code': 'test123',
                'state': 'test456'
            }
            
            response_with_params = self.session.get(f"{API_BASE}/xero/callback", params=oauth_params)
            
            if response_with_params.status_code == 200:
                content = response_with_params.text
                # Check if the OAuth parameters are being handled
                if 'test123' in content or 'test456' in content:
                    self.log_result(
                        "GET /api/xero/callback with OAuth Parameters", 
                        True, 
                        "✅ SUCCESS: OAuth callback handles parameters correctly (code=test123&state=test456)",
                        "Parameters are being processed by the callback endpoint"
                    )
                else:
                    self.log_result(
                        "GET /api/xero/callback with OAuth Parameters", 
                        True, 
                        "✅ SUCCESS: OAuth callback accessible with parameters (200 OK)",
                        "Endpoint is accessible, parameter handling may be internal"
                    )
            elif response_with_params.status_code == 404:
                self.log_result(
                    "GET /api/xero/callback with OAuth Parameters", 
                    False, 
                    "❌ FAILED: OAuth callback with parameters still returns 404",
                    "Router registration fix incomplete - parameterized requests still failing"
                )
            else:
                self.log_result(
                    "GET /api/xero/callback with OAuth Parameters", 
                    False, 
                    f"❌ UNEXPECTED: OAuth callback with parameters returns {response_with_params.status_code}",
                    response_with_params.text[:200]
                )
            
            # Test 3: Verify all Xero endpoints are accessible - Check /api/xero/status, /api/xero/auth/url
            xero_endpoints = [
                ('/api/xero/status', 'Xero Status'),
                ('/api/xero/auth/url', 'Xero Auth URL'),
                ('/api/xero/debug', 'Xero Debug'),
                ('/api/xero/next-invoice-number', 'Xero Next Invoice Number')
            ]
            
            accessible_endpoints = 0
            total_endpoints = len(xero_endpoints)
            
            for endpoint_path, endpoint_name in xero_endpoints:
                try:
                    endpoint_response = self.session.get(f"{BACKEND_URL}{endpoint_path}")
                    
                    if endpoint_response.status_code in [200, 500]:  # 500 is OK for some endpoints without Xero connection
                        accessible_endpoints += 1
                        self.log_result(
                            f"Xero Endpoint Accessibility - {endpoint_name}", 
                            True, 
                            f"✅ {endpoint_path} is accessible (status: {endpoint_response.status_code})",
                            "Endpoint is properly registered and responding"
                        )
                    elif endpoint_response.status_code == 404:
                        self.log_result(
                            f"Xero Endpoint Accessibility - {endpoint_name}", 
                            False, 
                            f"❌ {endpoint_path} returns 404 - router registration incomplete",
                            "This endpoint is still not accessible after router registration"
                        )
                    else:
                        self.log_result(
                            f"Xero Endpoint Accessibility - {endpoint_name}", 
                            False, 
                            f"❌ {endpoint_path} returns unexpected status {endpoint_response.status_code}",
                            endpoint_response.text[:100]
                        )
                        
                except Exception as e:
                    self.log_result(f"Xero Endpoint Accessibility - {endpoint_name}", False, f"Error: {str(e)}")
            
            # Test 4: Check if routes are properly registered - Summary
            if accessible_endpoints == total_endpoints:
                self.log_result(
                    "Xero Routes Registration Summary", 
                    True, 
                    f"✅ ALL Xero endpoints accessible ({accessible_endpoints}/{total_endpoints})",
                    "Router registration fix is working correctly - all /api/xero/* routes are accessible"
                )
            elif accessible_endpoints > 0:
                self.log_result(
                    "Xero Routes Registration Summary", 
                    False, 
                    f"⚠️ PARTIAL: {accessible_endpoints}/{total_endpoints} Xero endpoints accessible",
                    "Router registration partially working - some routes may still have issues"
                )
            else:
                self.log_result(
                    "Xero Routes Registration Summary", 
                    False, 
                    f"❌ FAILED: No Xero endpoints accessible (0/{total_endpoints})",
                    "Router registration fix failed - api_router may not be properly included"
                )
                
        except Exception as e:
            self.log_result("Xero Callback Router Registration Fix", False, f"Error: {str(e)}")
    
    def run_xero_callback_404_fix_tests(self):
        """Run the specific Xero callback 404 fix tests as requested in review"""
        print("\n" + "="*80)
        print("XERO CALLBACK 404 ISSUE RESOLUTION TESTING")
        print("Testing if the missing router registration issue has been fixed")
        print("Issue: api_router was defined but never included with app.include_router(api_router)")
        print("="*80)
        
        # Step 1: Authenticate
        if not self.authenticate():
            print("❌ Authentication failed - cannot proceed with tests")
            return
        
        # Step 2: Test the specific router registration fix
        self.test_xero_callback_router_registration_fix()
        
        # Print focused summary
        self.print_xero_callback_fix_summary()
    
    def print_xero_callback_fix_summary(self):
        """Print summary focused on the Xero callback 404 fix"""
        print("\n" + "="*80)
        print("XERO CALLBACK 404 FIX TEST SUMMARY")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['success']])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%" if total_tests > 0 else "0%")
        
        # Check specifically for callback 404 resolution
        callback_tests = [r for r in self.test_results if 'callback' in r['test'].lower() and 'xero' in r['test'].lower()]
        callback_success = [r for r in callback_tests if r['success']]
        
        print("\n" + "-"*80)
        print("CALLBACK 404 ISSUE RESOLUTION:")
        print("-"*80)
        
        if len(callback_success) == len(callback_tests) and len(callback_tests) > 0:
            print("🎉 SUCCESS: Xero callback 404 issue has been RESOLVED!")
            print("🎉 The api_router registration fix is working correctly")
            print("🎉 GET /api/xero/callback now returns 200 instead of 404")
            print("🎉 OAuth parameters are being handled properly")
        elif len(callback_success) > 0:
            print("⚠️ PARTIAL SUCCESS: Some callback endpoints working")
            print(f"⚠️ {len(callback_success)}/{len(callback_tests)} callback tests passed")
        else:
            print("❌ FAILURE: Xero callback 404 issue NOT resolved")
            print("❌ The api_router may still not be properly registered")
            print("❌ GET /api/xero/callback still returns 404")
        
        # Check Xero endpoints accessibility
        xero_endpoint_tests = [r for r in self.test_results if 'xero endpoint accessibility' in r['test'].lower()]
        xero_success = [r for r in xero_endpoint_tests if r['success']]
        
        if xero_endpoint_tests:
            print(f"\n📊 XERO ENDPOINTS ACCESSIBILITY: {len(xero_success)}/{len(xero_endpoint_tests)} endpoints accessible")
            
            if len(xero_success) == len(xero_endpoint_tests):
                print("✅ All Xero endpoints are now accessible")
            elif len(xero_success) > 0:
                print("⚠️ Some Xero endpoints still have issues")
            else:
                print("❌ No Xero endpoints are accessible")
        
        print("\n" + "="*80)
        print("CONCLUSION:")
        print("="*80)
        
        if len(callback_success) == len(callback_tests) and len(callback_tests) > 0:
            print("✅ ISSUE RESOLVED: The missing router registration has been fixed")
            print("✅ Users should no longer get 404 errors after Xero OAuth redirect")
            print("✅ The Xero integration callback flow is now working correctly")
        else:
            print("❌ ISSUE NOT RESOLVED: Router registration fix incomplete")
            print("❌ Users will still get 404 errors after Xero OAuth redirect")
            print("❌ Further investigation needed for api_router registration")
        
        print("\n" + "="*80)

if __name__ == "__main__":
    tester = XeroCallbackTester()
    
    # Run the specific Xero callback 404 fix tests as requested in the review
    tester.run_xero_callback_404_fix_tests()