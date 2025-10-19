#!/usr/bin/env python3
"""
GSM Bug Fix Testing Suite for Projected Material Cost Calculation
Testing the fix where GSM was being retrieved from layer data instead of materials database

CRITICAL BUG FIX TESTED:
- GSM was being retrieved from layer.get("gsm") which doesn't exist
- Fixed to retrieve from material.get("gsm") from materials database
- GSM is stored as string in database, needs conversion to float

TEST OBJECTIVES:
1. Verify GSM values are now populated correctly from materials database (not 0.0)
2. Verify GSM-based formula: linear_metres_per_tonne = 1,000,000 / (GSM × width_metres)
3. Verify cost_per_meter calculation: cost_per_meter = price_per_tonne / linear_metres_per_tonne
4. Verify final material costs are realistic and accurate
"""

import requests
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import uuid

# Load environment variables
load_dotenv('/app/frontend/.env')

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:8001')
API_BASE = f"{BACKEND_URL}/api"

class GSMBugFixTester:
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

    def test_projected_order_analysis_gsm_fix(self):
        """
        MAIN TEST: Projected Order Analysis GSM Bug Fix
        Test GET /api/stock/reports/projected-order-analysis
        Verify GSM values are populated correctly and calculations are accurate
        """
        print("\n" + "="*80)
        print("MAIN TEST: PROJECTED ORDER ANALYSIS GSM BUG FIX")
        print("Testing GSM retrieval from materials database and cost calculations")
        print("="*80)
        
        # Test 1: Basic GSM Values Verification
        self.test_gsm_values_populated()
        
        # Test 2: GSM-based Formula Verification
        self.test_gsm_formula_calculations()
        
        # Test 3: Cost Calculation Accuracy
        self.test_cost_calculation_accuracy()
        
        # Test 4: Multiple GSM Values Testing
        self.test_multiple_gsm_values()
        
        # Test 5: Total Cost Accuracy
        self.test_total_cost_accuracy()

    def test_gsm_values_populated(self):
        """Test 1: Verify GSM values are now populated correctly from materials database"""
        try:
            response = self.session.get(f"{API_BASE}/stock/reports/projected-order-analysis")
            
            if response.status_code == 200:
                result = response.json()
                data = result.get("data", {})
                products = data.get("products", [])
                
                gsm_found_count = 0
                zero_gsm_count = 0
                gsm_values = []
                
                for product in products:
                    material_requirements = product.get("material_requirements", {})
                    
                    for period, layers in material_requirements.items():
                        if isinstance(layers, list):
                            for layer in layers:
                                if not layer.get("is_total", False):  # Skip summary rows
                                    gsm = layer.get("gsm", 0)
                                    if gsm > 0:
                                        gsm_found_count += 1
                                        gsm_values.append(gsm)
                                    else:
                                        zero_gsm_count += 1
                
                if gsm_found_count > 0:
                    unique_gsm_values = list(set(gsm_values))
                    self.log_result(
                        "GSM Values Populated", 
                        True, 
                        f"Found {gsm_found_count} layers with GSM values > 0",
                        f"Unique GSM values: {unique_gsm_values}, Zero GSM count: {zero_gsm_count}"
                    )
                    
                    # Verify specific GSM values match expected values (155, 360, etc.)
                    expected_gsm_values = [155, 360]  # Common GSM values from materials database
                    found_expected = [gsm for gsm in unique_gsm_values if gsm in expected_gsm_values]
                    
                    if found_expected:
                        self.log_result(
                            "Expected GSM Values Found", 
                            True, 
                            f"Found expected GSM values: {found_expected}"
                        )
                    else:
                        self.log_result(
                            "Expected GSM Values Found", 
                            False, 
                            f"Expected GSM values {expected_gsm_values} not found in {unique_gsm_values}"
                        )
                else:
                    self.log_result(
                        "GSM Values Populated", 
                        False, 
                        f"No GSM values > 0 found. Zero GSM count: {zero_gsm_count}",
                        f"Products analyzed: {len(products)}"
                    )
            else:
                self.log_result(
                    "GSM Values Populated", 
                    False, 
                    f"Failed to get projected order analysis: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("GSM Values Populated", False, f"Error: {str(e)}")

    def test_gsm_formula_calculations(self):
        """Test 2: Verify GSM-based formula calculations"""
        try:
            response = self.session.get(f"{API_BASE}/stock/reports/projected-order-analysis")
            
            if response.status_code == 200:
                result = response.json()
                data = result.get("data", {})
                products = data.get("products", [])
                
                formula_correct_count = 0
                formula_incorrect_count = 0
                calculation_examples = []
                
                for product in products:
                    material_requirements = product.get("material_requirements", {})
                    
                    for period, layers in material_requirements.items():
                        if isinstance(layers, list):
                            for layer in layers:
                                if not layer.get("is_total", False):  # Skip summary rows
                                    gsm = layer.get("gsm", 0)
                                    width_mm = layer.get("width_mm", 0)
                                    linear_metres_per_tonne = layer.get("linear_metres_per_tonne", 0)
                                    
                                    if gsm > 0 and width_mm > 0 and linear_metres_per_tonne > 0:
                                        # Calculate expected linear_metres_per_tonne
                                        width_metres = width_mm / 1000
                                        expected_linear_metres = 1000000 / (gsm * width_metres)
                                        
                                        # Allow small rounding differences (within 1%)
                                        tolerance = expected_linear_metres * 0.01
                                        if abs(linear_metres_per_tonne - expected_linear_metres) <= tolerance:
                                            formula_correct_count += 1
                                        else:
                                            formula_incorrect_count += 1
                                        
                                        calculation_examples.append({
                                            "gsm": gsm,
                                            "width_mm": width_mm,
                                            "width_metres": width_metres,
                                            "expected_linear_metres": round(expected_linear_metres, 2),
                                            "actual_linear_metres": linear_metres_per_tonne,
                                            "correct": abs(linear_metres_per_tonne - expected_linear_metres) <= tolerance
                                        })
                
                if formula_correct_count > 0:
                    self.log_result(
                        "GSM Formula Calculations", 
                        True, 
                        f"Formula correct for {formula_correct_count} layers",
                        f"Incorrect: {formula_incorrect_count}, Examples: {calculation_examples[:3]}"
                    )
                    
                    # Test specific examples
                    gsm_155_examples = [ex for ex in calculation_examples if ex["gsm"] == 155]
                    if gsm_155_examples:
                        example = gsm_155_examples[0]
                        self.log_result(
                            "GSM 155 Formula Verification", 
                            example["correct"], 
                            f"GSM=155, Width={example['width_mm']}mm: Expected {example['expected_linear_metres']}, Got {example['actual_linear_metres']}"
                        )
                else:
                    self.log_result(
                        "GSM Formula Calculations", 
                        False, 
                        "No valid GSM formula calculations found",
                        f"Products analyzed: {len(products)}"
                    )
            else:
                self.log_result(
                    "GSM Formula Calculations", 
                    False, 
                    f"Failed to get projected order analysis: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("GSM Formula Calculations", False, f"Error: {str(e)}")

    def test_cost_calculation_accuracy(self):
        """Test 3: Verify cost_per_meter calculation accuracy"""
        try:
            response = self.session.get(f"{API_BASE}/stock/reports/projected-order-analysis")
            
            if response.status_code == 200:
                result = response.json()
                data = result.get("data", {})
                products = data.get("products", [])
                
                cost_correct_count = 0
                cost_incorrect_count = 0
                cost_examples = []
                
                for product in products:
                    material_requirements = product.get("material_requirements", {})
                    
                    for period, layers in material_requirements.items():
                        if isinstance(layers, list):
                            for layer in layers:
                                if not layer.get("is_total", False):  # Skip summary rows
                                    price_per_tonne = layer.get("price_per_tonne", 0)
                                    linear_metres_per_tonne = layer.get("linear_metres_per_tonne", 0)
                                    cost_per_meter = layer.get("cost_per_meter", 0)
                                    
                                    if price_per_tonne > 0 and linear_metres_per_tonne > 0 and cost_per_meter > 0:
                                        # Calculate expected cost_per_meter
                                        expected_cost_per_meter = price_per_tonne / linear_metres_per_tonne
                                        
                                        # Allow small rounding differences (within 1%)
                                        tolerance = expected_cost_per_meter * 0.01
                                        if abs(cost_per_meter - expected_cost_per_meter) <= tolerance:
                                            cost_correct_count += 1
                                        else:
                                            cost_incorrect_count += 1
                                        
                                        cost_examples.append({
                                            "price_per_tonne": price_per_tonne,
                                            "linear_metres_per_tonne": linear_metres_per_tonne,
                                            "expected_cost_per_meter": round(expected_cost_per_meter, 4),
                                            "actual_cost_per_meter": cost_per_meter,
                                            "correct": abs(cost_per_meter - expected_cost_per_meter) <= tolerance
                                        })
                
                if cost_correct_count > 0:
                    self.log_result(
                        "Cost Per Meter Calculations", 
                        True, 
                        f"Cost calculation correct for {cost_correct_count} layers",
                        f"Incorrect: {cost_incorrect_count}, Examples: {cost_examples[:3]}"
                    )
                else:
                    self.log_result(
                        "Cost Per Meter Calculations", 
                        False, 
                        "No valid cost calculations found",
                        f"Products analyzed: {len(products)}"
                    )
            else:
                self.log_result(
                    "Cost Per Meter Calculations", 
                    False, 
                    f"Failed to get projected order analysis: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Cost Per Meter Calculations", False, f"Error: {str(e)}")

    def test_multiple_gsm_values(self):
        """Test 4: Test different materials with different GSM values"""
        try:
            response = self.session.get(f"{API_BASE}/stock/reports/projected-order-analysis")
            
            if response.status_code == 200:
                result = response.json()
                data = result.get("data", {})
                products = data.get("products", [])
                
                gsm_analysis = {}  # {gsm: [linear_metres_per_tonne_values]}
                
                for product in products:
                    material_requirements = product.get("material_requirements", {})
                    
                    for period, layers in material_requirements.items():
                        if isinstance(layers, list):
                            for layer in layers:
                                if not layer.get("is_total", False):  # Skip summary rows
                                    gsm = layer.get("gsm", 0)
                                    linear_metres_per_tonne = layer.get("linear_metres_per_tonne", 0)
                                    
                                    if gsm > 0 and linear_metres_per_tonne > 0:
                                        if gsm not in gsm_analysis:
                                            gsm_analysis[gsm] = []
                                        gsm_analysis[gsm].append(linear_metres_per_tonne)
                
                # Verify that higher GSM = fewer metres per tonne (heavier paper)
                gsm_values = sorted(gsm_analysis.keys())
                relationship_correct = True
                
                if len(gsm_values) >= 2:
                    for i in range(len(gsm_values) - 1):
                        lower_gsm = gsm_values[i]
                        higher_gsm = gsm_values[i + 1]
                        
                        avg_lower = sum(gsm_analysis[lower_gsm]) / len(gsm_analysis[lower_gsm])
                        avg_higher = sum(gsm_analysis[higher_gsm]) / len(gsm_analysis[higher_gsm])
                        
                        # Higher GSM should have fewer metres per tonne
                        if avg_higher >= avg_lower:
                            relationship_correct = False
                    
                    self.log_result(
                        "Multiple GSM Values Relationship", 
                        relationship_correct, 
                        f"GSM vs metres/tonne relationship {'correct' if relationship_correct else 'incorrect'}",
                        f"GSM analysis: {dict((k, round(sum(v)/len(v), 0)) for k, v in gsm_analysis.items())}"
                    )
                else:
                    self.log_result(
                        "Multiple GSM Values Relationship", 
                        False, 
                        f"Need at least 2 different GSM values for comparison, found {len(gsm_values)}",
                        f"GSM values found: {gsm_values}"
                    )
            else:
                self.log_result(
                    "Multiple GSM Values Relationship", 
                    False, 
                    f"Failed to get projected order analysis: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Multiple GSM Values Relationship", False, f"Error: {str(e)}")

    def test_total_cost_accuracy(self):
        """Test 5: Verify total cost accuracy for projected quantities"""
        try:
            response = self.session.get(f"{API_BASE}/stock/reports/projected-order-analysis")
            
            if response.status_code == 200:
                result = response.json()
                data = result.get("data", {})
                products = data.get("products", [])
                
                total_cost_examples = []
                cost_verification_passed = 0
                cost_verification_failed = 0
                
                for product in products:
                    product_name = product.get("product_info", {}).get("product_description", "Unknown")
                    material_requirements = product.get("material_requirements", {})
                    
                    for period, layers in material_requirements.items():
                        if isinstance(layers, list):
                            period_total_cost = 0
                            projected_quantity = 0
                            
                            # Find the summary row to get projected quantity and total cost
                            summary_row = None
                            for layer in layers:
                                if layer.get("is_total", False):
                                    summary_row = layer
                                    break
                            
                            if summary_row:
                                projected_quantity = summary_row.get("projected_quantity", 0)
                                reported_total_cost = summary_row.get("total_cost", 0)
                                
                                # Calculate expected total cost by summing individual layer costs
                                calculated_total_cost = 0
                                for layer in layers:
                                    if not layer.get("is_total", False):
                                        layer_total_cost = layer.get("total_cost", 0)
                                        calculated_total_cost += layer_total_cost
                                
                                # Verify total cost matches sum of layer costs
                                tolerance = max(1.0, calculated_total_cost * 0.01)  # 1% tolerance or $1 minimum
                                if abs(reported_total_cost - calculated_total_cost) <= tolerance:
                                    cost_verification_passed += 1
                                else:
                                    cost_verification_failed += 1
                                
                                total_cost_examples.append({
                                    "product": product_name,
                                    "period": period,
                                    "projected_quantity": projected_quantity,
                                    "reported_total_cost": reported_total_cost,
                                    "calculated_total_cost": round(calculated_total_cost, 2),
                                    "cost_per_core": round(reported_total_cost / projected_quantity, 4) if projected_quantity > 0 else 0,
                                    "correct": abs(reported_total_cost - calculated_total_cost) <= tolerance
                                })
                
                if cost_verification_passed > 0:
                    self.log_result(
                        "Total Cost Accuracy", 
                        True, 
                        f"Total cost verification passed for {cost_verification_passed} periods",
                        f"Failed: {cost_verification_failed}, Examples: {total_cost_examples[:2]}"
                    )
                    
                    # Check for realistic cost values
                    realistic_costs = [ex for ex in total_cost_examples if 100 <= ex["reported_total_cost"] <= 1000000]
                    if realistic_costs:
                        self.log_result(
                            "Realistic Cost Values", 
                            True, 
                            f"Found {len(realistic_costs)} periods with realistic costs ($100-$1M)",
                            f"Cost range: ${min(ex['reported_total_cost'] for ex in realistic_costs):.2f} - ${max(ex['reported_total_cost'] for ex in realistic_costs):.2f}"
                        )
                    else:
                        self.log_result(
                            "Realistic Cost Values", 
                            False, 
                            "No realistic cost values found",
                            f"All costs: {[ex['reported_total_cost'] for ex in total_cost_examples[:5]]}"
                        )
                else:
                    self.log_result(
                        "Total Cost Accuracy", 
                        False, 
                        "No valid total cost calculations found",
                        f"Products analyzed: {len(products)}"
                    )
            else:
                self.log_result(
                    "Total Cost Accuracy", 
                    False, 
                    f"Failed to get projected order analysis: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Total Cost Accuracy", False, f"Error: {str(e)}")

    def test_materials_database_gsm_values(self):
        """Verify GSM values exist in materials database"""
        try:
            response = self.session.get(f"{API_BASE}/materials")
            
            if response.status_code == 200:
                materials = response.json()
                
                gsm_materials = []
                for material in materials:
                    gsm = material.get("gsm")
                    if gsm and gsm != "0":
                        try:
                            gsm_float = float(gsm)
                            if gsm_float > 0:
                                gsm_materials.append({
                                    "id": material.get("id"),
                                    "product_code": material.get("product_code"),
                                    "gsm": gsm_float,
                                    "price": material.get("price", 0)
                                })
                        except (ValueError, TypeError):
                            pass
                
                if gsm_materials:
                    self.log_result(
                        "Materials Database GSM Values", 
                        True, 
                        f"Found {len(gsm_materials)} materials with GSM values",
                        f"GSM values: {[m['gsm'] for m in gsm_materials[:5]]}"
                    )
                else:
                    self.log_result(
                        "Materials Database GSM Values", 
                        False, 
                        "No materials with GSM values found in database",
                        f"Total materials: {len(materials)}"
                    )
            else:
                self.log_result(
                    "Materials Database GSM Values", 
                    False, 
                    f"Failed to get materials: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Materials Database GSM Values", False, f"Error: {str(e)}")

    def print_test_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "="*80)
        print("GSM BUG FIX TEST SUMMARY")
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
        
        print("\n" + "="*80)
        if success_rate == 100:
            print("🎉 PERFECT! GSM BUG FIX WORKING 100%!")
        elif success_rate >= 80:
            print(f"✅ GSM BUG FIX MOSTLY WORKING: {success_rate:.1f}% SUCCESS RATE")
        else:
            print(f"⚠️  GSM BUG FIX NEEDS ATTENTION: {success_rate:.1f}% SUCCESS RATE")
        print("="*80)

    def run_gsm_bug_fix_tests(self):
        """Run all GSM bug fix tests"""
        print("\n" + "="*80)
        print("GSM BUG FIX TESTING SUITE")
        print("Testing Projected Material Cost Calculation after GSM bug fix")
        print("="*80)
        
        # Step 1: Authenticate
        if not self.authenticate():
            print("❌ Authentication failed - cannot proceed with tests")
            return
        
        # Step 2: Verify materials database has GSM values
        self.test_materials_database_gsm_values()
        
        # Step 3: Run main GSM bug fix tests
        self.test_projected_order_analysis_gsm_fix()
        
        # Step 4: Print comprehensive summary
        self.print_test_summary()

if __name__ == "__main__":
    tester = GSMBugFixTester()
    tester.run_gsm_bug_fix_tests()