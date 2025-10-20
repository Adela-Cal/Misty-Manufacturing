#!/usr/bin/env python3
"""
Raw Material Permutation and Yield Calculator Testing Suite
Re-testing after field mapping fixes as requested in review.

TEST OBJECTIVES:
1. Verify POST /api/calculators/material-permutation now works after field name fixes
2. Validate all calculations are accurate
3. Test complete workflow with real data

TEST STEPS:
1. Login with admin credentials (Callum/Peach7510)
2. GET /api/materials to get first material
3. POST /api/calculators/material-permutation with test data
4. Verify response includes all required fields
5. Validate calculation accuracy
6. Test edge cases

EXPECTED RESULTS:
- Endpoint returns valid permutations with all required fields
- Calculations are mathematically correct
- Patterns sorted by highest yield
- Export-ready data structure
"""

import requests
import json
import os
from datetime import datetime
from dotenv import load_dotenv
import uuid

# Load environment variables
load_dotenv('/app/frontend/.env')

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:8001')
API_BASE = f"{BACKEND_URL}/api"

class MaterialPermutationTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        self.material_id = None
        
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

    def get_first_material(self):
        """Get first material from materials collection"""
        print("\n=== GETTING FIRST MATERIAL ===")
        
        try:
            response = self.session.get(f"{API_BASE}/materials")
            
            if response.status_code == 200:
                materials = response.json()
                
                if materials and len(materials) > 0:
                    material = materials[0]
                    self.material_id = material.get('id')
                    
                    self.log_result(
                        "Get First Material", 
                        True, 
                        f"Retrieved material: {material.get('product_code', 'Unknown')}",
                        f"Material ID: {self.material_id}, GSM: {material.get('gsm')}, Width: {material.get('width_mm')}"
                    )
                    return material
                else:
                    self.log_result(
                        "Get First Material", 
                        False, 
                        "No materials found in database"
                    )
            else:
                self.log_result(
                    "Get First Material", 
                    False, 
                    f"Failed to get materials: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Get First Material", False, f"Error: {str(e)}")
        
        return None

    def test_material_permutation_basic(self):
        """Test basic material permutation calculation"""
        print("\n=== TESTING BASIC MATERIAL PERMUTATION ===")
        
        if not self.material_id:
            self.log_result(
                "Material Permutation Basic Test", 
                False, 
                "No material ID available for testing"
            )
            return
        
        try:
            # Test data as specified in review request
            test_data = {
                "material_id": self.material_id,
                "waste_allowance_mm": 5,
                "desired_slit_widths": [50, 75, 100],
                "quantity_master_rolls": 2
            }
            
            response = self.session.post(
                f"{API_BASE}/calculators/material-permutation", 
                json=test_data
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Check if it's a StandardResponse format
                if result.get("success"):
                    data = result.get("data", {})
                    
                    # Verify required fields in response
                    required_fields = [
                        "material_info", "input_parameters", "permutations", 
                        "total_permutations_found", "best_yield_percentage", "lowest_waste_mm"
                    ]
                    
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if not missing_fields:
                        self.log_result(
                            "Material Permutation Basic Test", 
                            True, 
                            f"Successfully calculated permutations",
                            f"Found {data.get('total_permutations_found', 0)} permutations, Best yield: {data.get('best_yield_percentage', 0)}%"
                        )
                        
                        # Verify material_info structure
                        self.verify_material_info(data.get("material_info", {}))
                        
                        # Verify permutations structure
                        self.verify_permutations(data.get("permutations", []))
                        
                        return data
                    else:
                        self.log_result(
                            "Material Permutation Basic Test", 
                            False, 
                            f"Response missing required fields: {missing_fields}",
                            f"Available fields: {list(data.keys())}"
                        )
                else:
                    self.log_result(
                        "Material Permutation Basic Test", 
                        False, 
                        "Response indicates failure",
                        result.get("message", "No error message")
                    )
            else:
                self.log_result(
                    "Material Permutation Basic Test", 
                    False, 
                    f"Request failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Material Permutation Basic Test", False, f"Error: {str(e)}")
        
        return None

    def verify_material_info(self, material_info):
        """Verify material_info structure has all required properties"""
        try:
            required_fields = [
                "material_id", "material_name", "material_code", 
                "master_width_mm", "gsm", "total_linear_meters", "cost_per_tonne_aud"
            ]
            
            missing_fields = [field for field in required_fields if field not in material_info]
            
            if not missing_fields:
                self.log_result(
                    "Material Info Structure", 
                    True, 
                    "Material info contains all required fields",
                    f"Width: {material_info.get('master_width_mm')}mm, GSM: {material_info.get('gsm')}, Linear meters: {material_info.get('total_linear_meters')}"
                )
            else:
                self.log_result(
                    "Material Info Structure", 
                    False, 
                    f"Material info missing fields: {missing_fields}",
                    f"Available fields: {list(material_info.keys())}"
                )
                
        except Exception as e:
            self.log_result("Material Info Structure", False, f"Error: {str(e)}")

    def verify_permutations(self, permutations):
        """Verify permutations array structure and sorting"""
        try:
            if not permutations:
                self.log_result(
                    "Permutations Structure", 
                    False, 
                    "No permutations found in response"
                )
                return
            
            # Check first permutation structure
            first_perm = permutations[0]
            required_fields = [
                "pattern", "pattern_description", "used_width_mm", "waste_mm",
                "yield_percentage", "slits_per_master_roll", "total_finished_rolls",
                "linear_meters_per_slit", "slit_details", "total_pattern_weight_kg",
                "total_pattern_cost_aud", "total_cost_all_rolls_aud"
            ]
            
            missing_fields = [field for field in required_fields if field not in first_perm]
            
            if not missing_fields:
                self.log_result(
                    "Permutations Structure", 
                    True, 
                    f"Permutations have correct structure ({len(permutations)} permutations)",
                    f"First pattern: {first_perm.get('pattern_description')}, Yield: {first_perm.get('yield_percentage')}%"
                )
                
                # Verify sorting by yield (descending)
                self.verify_yield_sorting(permutations)
                
                # Verify calculations
                self.verify_calculations(first_perm)
                
            else:
                self.log_result(
                    "Permutations Structure", 
                    False, 
                    f"Permutations missing fields: {missing_fields}",
                    f"Available fields: {list(first_perm.keys())}"
                )
                
        except Exception as e:
            self.log_result("Permutations Structure", False, f"Error: {str(e)}")

    def verify_yield_sorting(self, permutations):
        """Verify permutations are sorted by highest yield"""
        try:
            if len(permutations) < 2:
                self.log_result(
                    "Yield Sorting", 
                    True, 
                    "Only one permutation - sorting not applicable"
                )
                return
            
            # Check if yields are in descending order
            yields = [perm.get('yield_percentage', 0) for perm in permutations]
            is_sorted = all(yields[i] >= yields[i+1] for i in range(len(yields)-1))
            
            if is_sorted:
                self.log_result(
                    "Yield Sorting", 
                    True, 
                    f"Permutations correctly sorted by yield (highest first)",
                    f"Yields: {yields[:5]}..." if len(yields) > 5 else f"Yields: {yields}"
                )
            else:
                self.log_result(
                    "Yield Sorting", 
                    False, 
                    "Permutations not sorted by yield percentage",
                    f"Yields: {yields[:5]}..." if len(yields) > 5 else f"Yields: {yields}"
                )
                
        except Exception as e:
            self.log_result("Yield Sorting", False, f"Error: {str(e)}")

    def verify_calculations(self, permutation):
        """Verify mathematical accuracy of calculations"""
        try:
            # Get calculation values
            pattern = permutation.get('pattern', [])
            used_width = permutation.get('used_width_mm', 0)
            waste_mm = permutation.get('waste_mm', 0)
            yield_pct = permutation.get('yield_percentage', 0)
            slit_details = permutation.get('slit_details', [])
            
            # Verify used width calculation
            pattern_widths = []
            for p in pattern:
                if isinstance(p, str) and p.endswith('mm'):
                    width = float(p.replace('mm', ''))
                    pattern_widths.append(width)
            
            calculated_used_width = sum(pattern_widths)
            
            if abs(calculated_used_width - used_width) < 0.01:  # Allow small floating point differences
                self.log_result(
                    "Used Width Calculation", 
                    True, 
                    f"Used width calculation correct: {used_width}mm"
                )
            else:
                self.log_result(
                    "Used Width Calculation", 
                    False, 
                    f"Used width mismatch: calculated {calculated_used_width}mm, reported {used_width}mm"
                )
            
            # Verify slit details structure
            if slit_details:
                detail = slit_details[0]
                required_detail_fields = [
                    "slit_width_mm", "count", "linear_meters", 
                    "weight_per_slit_kg", "cost_per_slit_aud"
                ]
                
                missing_detail_fields = [field for field in required_detail_fields if field not in detail]
                
                if not missing_detail_fields:
                    self.log_result(
                        "Slit Details Structure", 
                        True, 
                        f"Slit details have correct structure ({len(slit_details)} details)"
                    )
                else:
                    self.log_result(
                        "Slit Details Structure", 
                        False, 
                        f"Slit details missing fields: {missing_detail_fields}"
                    )
            
        except Exception as e:
            self.log_result("Calculations Verification", False, f"Error: {str(e)}")

    def test_edge_cases(self):
        """Test edge cases with different slit widths and waste allowances"""
        print("\n=== TESTING EDGE CASES ===")
        
        if not self.material_id:
            self.log_result(
                "Edge Cases Setup", 
                False, 
                "No material ID available for edge case testing"
            )
            return
        
        # Test Case 1: Different slit widths
        self.test_different_slit_widths()
        
        # Test Case 2: Different waste allowances
        self.test_different_waste_allowances()
        
        # Test Case 3: Invalid inputs
        self.test_invalid_inputs()

    def test_different_slit_widths(self):
        """Test with different slit width combinations"""
        try:
            test_data = {
                "material_id": self.material_id,
                "waste_allowance_mm": 10,
                "desired_slit_widths": [25, 50, 75, 100, 150],
                "quantity_master_rolls": 1
            }
            
            response = self.session.post(
                f"{API_BASE}/calculators/material-permutation", 
                json=test_data
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("success"):
                    data = result.get("data", {})
                    permutations_count = data.get("total_permutations_found", 0)
                    
                    self.log_result(
                        "Different Slit Widths Test", 
                        True, 
                        f"Successfully calculated with 5 different slit widths",
                        f"Found {permutations_count} permutations"
                    )
                else:
                    self.log_result(
                        "Different Slit Widths Test", 
                        False, 
                        "Calculation failed",
                        result.get("message", "No error message")
                    )
            else:
                self.log_result(
                    "Different Slit Widths Test", 
                    False, 
                    f"Request failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Different Slit Widths Test", False, f"Error: {str(e)}")

    def test_different_waste_allowances(self):
        """Test with different waste allowance values"""
        try:
            test_data = {
                "material_id": self.material_id,
                "waste_allowance_mm": 20,  # Higher waste allowance
                "desired_slit_widths": [50, 75, 100],
                "quantity_master_rolls": 3
            }
            
            response = self.session.post(
                f"{API_BASE}/calculators/material-permutation", 
                json=test_data
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("success"):
                    data = result.get("data", {})
                    permutations_count = data.get("total_permutations_found", 0)
                    
                    self.log_result(
                        "Different Waste Allowances Test", 
                        True, 
                        f"Successfully calculated with 20mm waste allowance",
                        f"Found {permutations_count} permutations"
                    )
                else:
                    self.log_result(
                        "Different Waste Allowances Test", 
                        False, 
                        "Calculation failed",
                        result.get("message", "No error message")
                    )
            else:
                self.log_result(
                    "Different Waste Allowances Test", 
                    False, 
                    f"Request failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Different Waste Allowances Test", False, f"Error: {str(e)}")

    def test_invalid_inputs(self):
        """Test with invalid input parameters"""
        try:
            # Test with non-existent material ID
            test_data = {
                "material_id": str(uuid.uuid4()),  # Random UUID
                "waste_allowance_mm": 5,
                "desired_slit_widths": [50, 75, 100],
                "quantity_master_rolls": 2
            }
            
            response = self.session.post(
                f"{API_BASE}/calculators/material-permutation", 
                json=test_data
            )
            
            if response.status_code == 404:
                self.log_result(
                    "Invalid Material ID Test", 
                    True, 
                    "Correctly returned 404 for non-existent material"
                )
            else:
                self.log_result(
                    "Invalid Material ID Test", 
                    False, 
                    f"Expected 404, got {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Invalid Inputs Test", False, f"Error: {str(e)}")

    def run_all_tests(self):
        """Run all material permutation tests"""
        print("="*80)
        print("RAW MATERIAL PERMUTATION AND YIELD CALCULATOR TESTING")
        print("Re-testing after field mapping fixes")
        print("="*80)
        
        # Step 1: Authenticate
        if not self.authenticate():
            print("❌ Authentication failed - cannot proceed with tests")
            return
        
        # Step 2: Get first material
        material = self.get_first_material()
        if not material:
            print("❌ No materials available - cannot proceed with tests")
            return
        
        # Step 3: Test basic functionality
        self.test_material_permutation_basic()
        
        # Step 4: Test edge cases
        self.test_edge_cases()
        
        # Step 5: Print summary
        self.print_test_summary()

    def print_test_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "="*80)
        print("MATERIAL PERMUTATION CALCULATOR TEST SUMMARY")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        # Show all test results
        print("\n" + "="*60)
        print("DETAILED TEST RESULTS:")
        print("="*60)
        
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test']}: {result['message']}")
            if result['details'] and not result['success']:
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
            print("✅ Raw Material Permutation Calculator is working correctly")
        elif success_rate >= 90:
            print(f"🎯 EXCELLENT! {success_rate:.1f}% SUCCESS RATE")
            print("✅ Raw Material Permutation Calculator is mostly working")
        elif success_rate >= 80:
            print(f"✅ GOOD! {success_rate:.1f}% SUCCESS RATE")
            print("⚠️  Some issues found in Raw Material Permutation Calculator")
        else:
            print(f"⚠️  NEEDS IMPROVEMENT: {success_rate:.1f}% SUCCESS RATE")
            print("❌ Significant issues found in Raw Material Permutation Calculator")
        print("="*80)

if __name__ == "__main__":
    tester = MaterialPermutationTester()
    tester.run_all_tests()