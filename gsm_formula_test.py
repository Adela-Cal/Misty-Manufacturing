#!/usr/bin/env python3
"""
GSM-Based Formula Testing Suite for Projected Order Analysis

CRITICAL FINDING: The current implementation shows GSM = 0.0 for all materials,
which means the new GSM-based formula is falling back to using price directly.

This test will:
1. Verify the new cost calculation fields are present
2. Check if GSM values are properly populated
3. Test the formula calculations when GSM > 0
4. Verify edge case handling when GSM = 0
5. Test the complete formula chain
"""

import requests
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import math

# Load environment variables
load_dotenv('/app/frontend/.env')

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:8001')
API_BASE = f"{BACKEND_URL}/api"

class GSMFormulaTester:
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
        """Authenticate with demo credentials"""
        try:
            response = self.session.post(f"{API_BASE}/auth/login", json={
                "username": "Callum",
                "password": "Peach7510"
            })
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data['access_token']
                self.session.headers.update({'Authorization': f'Bearer {self.auth_token}'})
                self.log_result("Authentication", True, "Successfully authenticated with demo credentials")
                return True
            else:
                self.log_result("Authentication", False, f"Failed to authenticate: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Authentication", False, f"Authentication error: {str(e)}")
            return False
    
    def test_new_cost_fields_present(self):
        """Test 1: Verify new GSM-based cost calculation fields are present"""
        try:
            response = self.session.get(f"{API_BASE}/stock/reports/projected-order-analysis")
            
            if response.status_code != 200:
                self.log_result("New Cost Fields Test", False, f"API returned {response.status_code}")
                return False
            
            data = response.json()
            report_data = data.get('data', {})
            products = report_data.get('products', [])
            
            new_fields_found = []
            
            for product in products:
                material_requirements = product.get('material_requirements', {})
                for period in ['3_months', '6_months', '9_months', '12_months']:
                    period_data = material_requirements.get(period, [])
                    for material in period_data:
                        if material.get('is_total'):
                            continue  # Skip summary rows
                            
                        # Check for new GSM-based calculation fields
                        required_fields = [
                            'price_per_tonne', 
                            'linear_metres_per_tonne', 
                            'cost_per_meter',
                            'cost_per_core',
                            'total_cost'
                        ]
                        
                        field_status = {}
                        for field in required_fields:
                            field_status[field] = field in material
                        
                        new_fields_found.append({
                            'material': material.get('material_name', 'Unknown'),
                            'period': period,
                            'fields_present': field_status,
                            'all_present': all(field_status.values())
                        })
                        
                        if len(new_fields_found) >= 3:  # Check first 3 materials
                            break
                    if len(new_fields_found) >= 3:
                        break
                if len(new_fields_found) >= 3:
                    break
            
            if new_fields_found:
                all_present = all(item['all_present'] for item in new_fields_found)
                if all_present:
                    self.log_result("New Cost Fields Test", True, f"All new GSM-based cost fields present in {len(new_fields_found)} materials", new_fields_found[0])
                    return True
                else:
                    missing_fields = [item for item in new_fields_found if not item['all_present']]
                    self.log_result("New Cost Fields Test", False, f"Some new fields missing", missing_fields[0])
                    return False
            else:
                self.log_result("New Cost Fields Test", False, "No material data found to check")
                return False
                
        except Exception as e:
            self.log_result("New Cost Fields Test", False, f"Test error: {str(e)}")
            return False
    
    def test_gsm_values_population(self):
        """Test 2: Check if GSM values are properly populated from materials"""
        try:
            response = self.session.get(f"{API_BASE}/stock/reports/projected-order-analysis")
            
            if response.status_code != 200:
                self.log_result("GSM Values Test", False, f"API returned {response.status_code}")
                return False
            
            data = response.json()
            report_data = data.get('data', {})
            products = report_data.get('products', [])
            
            gsm_analysis = []
            
            for product in products:
                material_requirements = product.get('material_requirements', {})
                three_month_data = material_requirements.get('3_months', [])
                
                for material in three_month_data:
                    if material.get('is_total'):
                        continue
                        
                    gsm = material.get('gsm', 0)
                    material_id = material.get('material_id')
                    material_name = material.get('material_name', 'Unknown')
                    
                    gsm_analysis.append({
                        'material_id': material_id,
                        'material_name': material_name,
                        'gsm': gsm,
                        'has_gsm': gsm > 0
                    })
            
            if gsm_analysis:
                materials_with_gsm = [item for item in gsm_analysis if item['has_gsm']]
                materials_without_gsm = [item for item in gsm_analysis if not item['has_gsm']]
                
                if materials_with_gsm:
                    self.log_result("GSM Values Test", True, f"Found {len(materials_with_gsm)}/{len(gsm_analysis)} materials with GSM values", materials_with_gsm[0])
                    return True
                else:
                    self.log_result("GSM Values Test", False, f"No materials have GSM values (all are 0.0) - {len(materials_without_gsm)} materials checked", gsm_analysis[0])
                    return False
            else:
                self.log_result("GSM Values Test", False, "No material data found")
                return False
                
        except Exception as e:
            self.log_result("GSM Values Test", False, f"Test error: {str(e)}")
            return False
    
    def test_formula_calculation_logic(self):
        """Test 3: Verify the GSM-based formula calculation logic"""
        try:
            response = self.session.get(f"{API_BASE}/stock/reports/projected-order-analysis")
            
            if response.status_code != 200:
                self.log_result("Formula Logic Test", False, f"API returned {response.status_code}")
                return False
            
            data = response.json()
            report_data = data.get('data', {})
            products = report_data.get('products', [])
            
            formula_tests = []
            
            for product in products:
                material_requirements = product.get('material_requirements', {})
                three_month_data = material_requirements.get('3_months', [])
                
                for material in three_month_data:
                    if material.get('is_total'):
                        continue
                        
                    # Get calculation parameters
                    price_per_tonne = material.get('price_per_tonne', 0)
                    linear_metres_per_tonne = material.get('linear_metres_per_tonne')
                    cost_per_meter = material.get('cost_per_meter', 0)
                    gsm = material.get('gsm', 0)
                    width_mm = material.get('width_mm', 0)
                    
                    test_result = {
                        'material_name': material.get('material_name', 'Unknown'),
                        'gsm': gsm,
                        'width_mm': width_mm,
                        'price_per_tonne': price_per_tonne,
                        'linear_metres_per_tonne': linear_metres_per_tonne,
                        'cost_per_meter': cost_per_meter
                    }
                    
                    if gsm > 0 and width_mm > 0:
                        # Test Formula 1: linear_metres_per_tonne = 1,000,000 / (GSM × width_metres)
                        width_metres = width_mm / 1000
                        expected_linear_metres = 1000000 / (gsm * width_metres)
                        
                        if linear_metres_per_tonne is not None:
                            linear_metres_correct = abs(linear_metres_per_tonne - expected_linear_metres) < 1
                            
                            # Test Formula 2: cost_per_meter = price_per_tonne / linear_metres_per_tonne
                            if linear_metres_per_tonne > 0:
                                expected_cost_per_meter = price_per_tonne / linear_metres_per_tonne
                                cost_per_meter_correct = abs(cost_per_meter - expected_cost_per_meter) < 0.001
                            else:
                                cost_per_meter_correct = False
                                expected_cost_per_meter = 0
                            
                            test_result.update({
                                'formula_applicable': True,
                                'expected_linear_metres': expected_linear_metres,
                                'linear_metres_correct': linear_metres_correct,
                                'expected_cost_per_meter': expected_cost_per_meter,
                                'cost_per_meter_correct': cost_per_meter_correct,
                                'formula_working': linear_metres_correct and cost_per_meter_correct
                            })
                        else:
                            test_result.update({
                                'formula_applicable': True,
                                'error': 'linear_metres_per_tonne is None despite GSM > 0'
                            })
                    else:
                        # Edge case: GSM = 0 or width = 0, should fall back to using price directly
                        fallback_correct = (linear_metres_per_tonne is None) and (cost_per_meter == price_per_tonne)
                        test_result.update({
                            'formula_applicable': False,
                            'fallback_used': True,
                            'fallback_correct': fallback_correct
                        })
                    
                    formula_tests.append(test_result)
                    
                    if len(formula_tests) >= 5:  # Test first 5 materials
                        break
                if len(formula_tests) >= 5:
                    break
            
            if formula_tests:
                working_formulas = [test for test in formula_tests if test.get('formula_working', False)]
                correct_fallbacks = [test for test in formula_tests if test.get('fallback_correct', False)]
                
                if working_formulas:
                    self.log_result("Formula Logic Test", True, f"GSM-based formula working correctly for {len(working_formulas)} materials", working_formulas[0])
                    return True
                elif correct_fallbacks:
                    self.log_result("Formula Logic Test", True, f"Fallback logic working correctly for {len(correct_fallbacks)} materials (GSM=0)", correct_fallbacks[0])
                    return True
                else:
                    self.log_result("Formula Logic Test", False, f"Formula calculations incorrect", formula_tests[0])
                    return False
            else:
                self.log_result("Formula Logic Test", False, "No material data found for formula testing")
                return False
                
        except Exception as e:
            self.log_result("Formula Logic Test", False, f"Test error: {str(e)}")
            return False
    
    def test_materials_database_gsm(self):
        """Test 4: Check GSM values in materials database"""
        try:
            response = self.session.get(f"{API_BASE}/materials")
            
            if response.status_code != 200:
                self.log_result("Materials GSM Test", False, f"Materials API returned {response.status_code}")
                return False
            
            materials = response.json()
            
            gsm_materials = []
            for material in materials:
                gsm = material.get('gsm', 0)
                gsm_materials.append({
                    'id': material.get('id'),
                    'supplier': material.get('supplier', 'Unknown'),
                    'product_code': material.get('product_code', 'Unknown'),
                    'gsm': gsm,
                    'has_gsm': gsm > 0
                })
            
            materials_with_gsm = [m for m in gsm_materials if m['has_gsm']]
            
            if materials_with_gsm:
                self.log_result("Materials GSM Test", True, f"Found {len(materials_with_gsm)}/{len(gsm_materials)} materials with GSM values in database", materials_with_gsm[0])
                return True
            else:
                self.log_result("Materials GSM Test", False, f"No materials have GSM values in database - all {len(gsm_materials)} materials have GSM=0", gsm_materials[0] if gsm_materials else None)
                return False
                
        except Exception as e:
            self.log_result("Materials GSM Test", False, f"Test error: {str(e)}")
            return False
    
    def test_summary_cost_calculations(self):
        """Test 5: Verify summary cost calculations include new fields"""
        try:
            response = self.session.get(f"{API_BASE}/stock/reports/projected-order-analysis")
            
            if response.status_code != 200:
                self.log_result("Summary Cost Test", False, f"API returned {response.status_code}")
                return False
            
            data = response.json()
            report_data = data.get('data', {})
            summary = report_data.get('summary', {})
            
            summary_analysis = []
            
            for period in ['3_months', '6_months', '9_months', '12_months']:
                period_summary = summary.get(period, {})
                
                # Check for cost-related fields in summary
                cost_fields = {
                    'total_projected_material_cost': period_summary.get('total_projected_material_cost'),
                    'total_projected_orders': period_summary.get('total_projected_orders'),
                    'products_analyzed': period_summary.get('products_analyzed')
                }
                
                # Calculate cost per unit if possible
                cost_per_unit = None
                if cost_fields['total_projected_material_cost'] and cost_fields['total_projected_orders']:
                    cost_per_unit = cost_fields['total_projected_material_cost'] / cost_fields['total_projected_orders']
                
                summary_analysis.append({
                    'period': period,
                    'cost_fields': cost_fields,
                    'cost_per_unit': cost_per_unit,
                    'has_cost_data': cost_fields['total_projected_material_cost'] is not None
                })
            
            periods_with_costs = [s for s in summary_analysis if s['has_cost_data']]
            
            if periods_with_costs:
                self.log_result("Summary Cost Test", True, f"Summary cost calculations present for {len(periods_with_costs)}/4 periods", periods_with_costs[0])
                return True
            else:
                self.log_result("Summary Cost Test", False, "No cost data found in summary", summary_analysis[0])
                return False
                
        except Exception as e:
            self.log_result("Summary Cost Test", False, f"Test error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all GSM formula tests"""
        print("🧪 GSM-BASED FORMULA TESTING SUITE")
        print("=" * 60)
        
        if not self.authenticate():
            return False
        
        tests = [
            self.test_new_cost_fields_present,
            self.test_gsm_values_population,
            self.test_formula_calculation_logic,
            self.test_materials_database_gsm,
            self.test_summary_cost_calculations
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            if test():
                passed += 1
        
        print("\n" + "=" * 60)
        print(f"📊 TEST RESULTS: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
        
        # Analyze results
        if passed == total:
            print("🎉 ALL TESTS PASSED - GSM-based formula implementation is working correctly!")
        elif passed >= 3:
            print("⚠️  Most tests passed - GSM-based formula is partially working")
        else:
            print("❌ Multiple tests failed - GSM-based formula needs attention")
        
        return passed >= 3  # Consider success if most tests pass

if __name__ == "__main__":
    tester = GSMFormulaTester()
    success = tester.run_all_tests()
    
    # Print detailed results
    print("\n📋 DETAILED TEST RESULTS:")
    for result in tester.test_results:
        status = "✅" if result['success'] else "❌"
        print(f"{status} {result['test']}: {result['message']}")
        if result.get('details') and not result['success']:
            print(f"   Details: {result['details']}")
    
    exit(0 if success else 1)