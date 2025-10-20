#!/usr/bin/env python3
"""
Stage Update Endpoint Testing Suite
Testing the stage update endpoint to debug the 422 error as requested in review.

TEST PLAN:
1. Get an order from production board - GET /api/production/board
2. Try to update the stage - PUT /api/orders/{order_id}/stage
3. If it fails with 422, capture the full error response including validation details
4. Check ProductionStage enum values to ensure they match
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

class StageUpdateTester:
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
        """Test authentication with admin credentials"""
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

    def test_stage_update_endpoint(self):
        """
        MAIN TEST: Stage Update Endpoint Debugging
        Following the exact steps from the review request
        """
        print("\n" + "="*80)
        print("STAGE UPDATE ENDPOINT DEBUGGING")
        print("Testing PUT /api/orders/{order_id}/stage to debug 422 error")
        print("="*80)
        
        # Step 1: Get an order from production board
        order = self.get_order_from_production_board()
        if not order:
            print("❌ Cannot proceed without an order from production board")
            return
        
        # Step 2: Try to update the stage with the specific body from review
        self.test_stage_update_with_specific_body(order)
        
        # Step 3: Check ProductionStage enum values
        self.check_production_stage_enum_values()
        
        # Additional debugging tests
        self.test_stage_update_variations(order)

    def get_order_from_production_board(self):
        """Step 1: Get an order from production board - GET /api/production/board"""
        try:
            print("\n--- Step 1: Getting order from production board ---")
            
            # First try the production board endpoint
            response = self.session.get(f"{API_BASE}/production/board")
            
            print(f"Production board response status: {response.status_code}")
            if response.status_code != 200:
                print(f"Production board failed: {response.text}")
                
                # Fallback: try getting orders directly
                print("Trying fallback: GET /api/orders")
                response = self.session.get(f"{API_BASE}/orders")
            
            if response.status_code == 200:
                result = response.json()
                
                # Check if it's a StandardResponse format
                if isinstance(result, dict) and "data" in result:
                    orders = result.get("data", [])
                else:
                    orders = result if isinstance(result, list) else []
                
                if orders and len(orders) > 0:
                    order = orders[0]  # Get first order
                    current_stage = order.get('current_stage', 'unknown')
                    
                    self.log_result(
                        "Get Order from Production Board", 
                        True, 
                        f"Found order {order.get('order_number', 'N/A')} with current_stage: {current_stage}",
                        f"Order ID: {order.get('id')}, Total orders: {len(orders)}"
                    )
                    
                    print(f"📋 Selected Order Details:")
                    print(f"   Order ID: {order.get('id')}")
                    print(f"   Order Number: {order.get('order_number')}")
                    print(f"   Current Stage: {current_stage}")
                    print(f"   Client: {order.get('client_name', 'N/A')}")
                    
                    return order
                else:
                    self.log_result(
                        "Get Order from Production Board", 
                        False, 
                        "No orders found in production board"
                    )
            else:
                self.log_result(
                    "Get Order from Production Board", 
                    False, 
                    f"Failed to get orders: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Get Order from Production Board", False, f"Error: {str(e)}")
        
        return None

    def test_stage_update_with_specific_body(self, order):
        """Step 2: Try to update the stage with exact body from review request"""
        try:
            print("\n--- Step 2: Testing stage update with specific body ---")
            
            order_id = order.get('id')
            if not order_id:
                self.log_result(
                    "Stage Update - Specific Body", 
                    False, 
                    "Order ID not found"
                )
                return
            
            # Exact body from review request
            stage_update_body = {
                "from_stage": "paper_slitting",
                "to_stage": "core_winding"
            }
            
            print(f"🔄 Attempting stage update:")
            print(f"   URL: PUT {API_BASE}/orders/{order_id}/stage")
            print(f"   Body: {json.dumps(stage_update_body, indent=2)}")
            print(f"   Auth: Bearer token (Callum admin)")
            
            response = self.session.put(
                f"{API_BASE}/orders/{order_id}/stage", 
                json=stage_update_body
            )
            
            print(f"📊 Response Status: {response.status_code}")
            print(f"📊 Response Headers: {dict(response.headers)}")
            
            if response.status_code == 422:
                # This is the expected error we're debugging
                try:
                    error_data = response.json()
                    self.log_result(
                        "Stage Update - 422 Error Captured", 
                        True, 
                        "Successfully captured 422 validation error",
                        f"Full error response: {json.dumps(error_data, indent=2)}"
                    )
                    
                    print(f"🚨 422 VALIDATION ERROR DETAILS:")
                    print(f"   Full Response: {json.dumps(error_data, indent=2)}")
                    
                    # Extract specific validation details
                    if isinstance(error_data, dict):
                        if "detail" in error_data:
                            print(f"   Error Detail: {error_data['detail']}")
                        if "errors" in error_data:
                            print(f"   Validation Errors: {error_data['errors']}")
                        if "message" in error_data:
                            print(f"   Error Message: {error_data['message']}")
                    
                except json.JSONDecodeError:
                    self.log_result(
                        "Stage Update - 422 Error Captured", 
                        True, 
                        "422 error captured but response is not JSON",
                        f"Raw response: {response.text}"
                    )
                    print(f"🚨 422 ERROR (Non-JSON): {response.text}")
                    
            elif response.status_code == 200:
                result = response.json()
                self.log_result(
                    "Stage Update - Unexpected Success", 
                    True, 
                    "Stage update succeeded (unexpected - should investigate why no 422)",
                    f"Response: {json.dumps(result, indent=2)}"
                )
                print(f"✅ UNEXPECTED SUCCESS: {json.dumps(result, indent=2)}")
                
            else:
                # Other error codes
                try:
                    error_data = response.json()
                    error_details = json.dumps(error_data, indent=2)
                except:
                    error_details = response.text
                
                self.log_result(
                    "Stage Update - Other Error", 
                    False, 
                    f"Unexpected status code {response.status_code}",
                    error_details
                )
                print(f"❓ UNEXPECTED STATUS {response.status_code}: {error_details}")
                
        except Exception as e:
            self.log_result("Stage Update - Specific Body", False, f"Error: {str(e)}")

    def check_production_stage_enum_values(self):
        """Step 4: Check ProductionStage enum values to ensure they match"""
        try:
            print("\n--- Step 4: Checking ProductionStage enum values ---")
            
            # Try to get enum values from a models endpoint or check what values are accepted
            # First, let's check what stages are currently in use
            response = self.session.get(f"{API_BASE}/production/board")
            
            if response.status_code == 200:
                result = response.json()
                orders = result.get("data", []) if isinstance(result, dict) else result
                
                # Collect all current_stage values
                current_stages = set()
                for order in orders:
                    stage = order.get('current_stage')
                    if stage:
                        current_stages.add(stage)
                
                self.log_result(
                    "Production Stage Values in Use", 
                    True, 
                    f"Found stages currently in use: {sorted(list(current_stages))}",
                    f"Total unique stages: {len(current_stages)}"
                )
                
                print(f"📋 PRODUCTION STAGES CURRENTLY IN USE:")
                for stage in sorted(current_stages):
                    print(f"   - {stage}")
                
                # Check if the stages from our test are valid
                test_stages = ["paper_slitting", "core_winding"]
                print(f"\n🔍 CHECKING TEST STAGES:")
                for stage in test_stages:
                    if stage in current_stages:
                        print(f"   ✅ {stage} - FOUND in current stages")
                    else:
                        print(f"   ❌ {stage} - NOT FOUND in current stages")
                
                # Try to find the complete enum by checking backend code or documentation
                self.check_backend_stage_definitions()
                
            else:
                self.log_result(
                    "Production Stage Values Check", 
                    False, 
                    f"Failed to get production board: {response.status_code}"
                )
                
        except Exception as e:
            self.log_result("Production Stage Values Check", False, f"Error: {str(e)}")

    def check_backend_stage_definitions(self):
        """Try to determine the correct ProductionStage enum values"""
        try:
            print(f"\n🔍 ANALYZING STAGE DEFINITIONS:")
            
            # Common production stages that might be expected
            expected_stages = [
                "order_entered", "order_entry", "ORDER_ENTERED",
                "paper_slitting", "PAPER_SLITTING", 
                "core_winding", "CORE_WINDING",
                "cutting", "CUTTING",
                "quality_control", "QUALITY_CONTROL",
                "packaging", "PACKAGING", 
                "shipping", "SHIPPING",
                "completed", "COMPLETED",
                "cleared", "CLEARED",
                "invoicing", "INVOICING"
            ]
            
            print(f"   Expected possible stages: {expected_stages}")
            
            # The issue might be:
            # 1. Case sensitivity (paper_slitting vs PAPER_SLITTING)
            # 2. Underscore vs camelCase (paper_slitting vs paperSlitting)
            # 3. Different naming convention
            
            possible_issues = [
                "Case sensitivity: backend expects UPPERCASE",
                "Naming convention: backend uses different names",
                "Missing enum values: stages not defined in backend",
                "Field validation: from_stage/to_stage field names incorrect"
            ]
            
            print(f"\n🚨 POSSIBLE ISSUES:")
            for i, issue in enumerate(possible_issues, 1):
                print(f"   {i}. {issue}")
                
        except Exception as e:
            self.log_result("Backend Stage Definitions Check", False, f"Error: {str(e)}")

    def test_stage_update_variations(self, order):
        """Test different variations to identify the exact issue"""
        try:
            print("\n--- Additional Debugging: Testing Stage Update Variations ---")
            
            order_id = order.get('id')
            if not order_id:
                return
            
            # Test different case variations
            test_variations = [
                {
                    "name": "UPPERCASE stages",
                    "body": {"from_stage": "PAPER_SLITTING", "to_stage": "CORE_WINDING"}
                },
                {
                    "name": "camelCase stages", 
                    "body": {"from_stage": "paperSlitting", "to_stage": "coreWinding"}
                },
                {
                    "name": "Different field names",
                    "body": {"from": "paper_slitting", "to": "core_winding"}
                },
                {
                    "name": "Single stage field",
                    "body": {"stage": "core_winding"}
                },
                {
                    "name": "Common stage names",
                    "body": {"from_stage": "order_entered", "to_stage": "cutting"}
                }
            ]
            
            for variation in test_variations:
                print(f"\n🧪 Testing: {variation['name']}")
                print(f"   Body: {json.dumps(variation['body'], indent=2)}")
                
                try:
                    response = self.session.put(
                        f"{API_BASE}/orders/{order_id}/stage", 
                        json=variation['body']
                    )
                    
                    print(f"   Status: {response.status_code}")
                    
                    if response.status_code == 422:
                        try:
                            error_data = response.json()
                            print(f"   422 Error: {json.dumps(error_data, indent=4)}")
                        except:
                            print(f"   422 Error (raw): {response.text}")
                    elif response.status_code == 200:
                        print(f"   ✅ SUCCESS with {variation['name']}")
                        result = response.json()
                        print(f"   Response: {json.dumps(result, indent=4)}")
                    else:
                        print(f"   Other status: {response.text}")
                        
                except Exception as e:
                    print(f"   Error: {str(e)}")
                    
        except Exception as e:
            self.log_result("Stage Update Variations", False, f"Error: {str(e)}")

    def print_test_summary(self):
        """Print test summary"""
        print("\n" + "="*80)
        print("STAGE UPDATE ENDPOINT DEBUGGING SUMMARY")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        
        print("\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test']}: {result['message']}")
            if result['details'] and not result['success']:
                print(f"   Details: {result['details']}")
        
        print("\n" + "="*80)

def main():
    """Main test execution"""
    print("🚀 Starting Stage Update Endpoint Debugging")
    print("Following exact steps from review request...")
    
    tester = StageUpdateTester()
    
    # Authenticate first
    if not tester.authenticate():
        print("❌ Authentication failed. Cannot proceed with tests.")
        return
    
    # Run the main test
    tester.test_stage_update_endpoint()
    
    # Print summary
    tester.print_test_summary()

if __name__ == "__main__":
    main()