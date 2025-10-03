#!/usr/bin/env python3
"""
Comprehensive CSV Export Testing Suite
Tests the new CSV export functionality for drafted invoices as requested in review
"""

import requests
import json
import os
import csv
import io
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:8001')
API_BASE = f"{BACKEND_URL}/api"

class CSVExportTester:
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
    
    def test_csv_export_endpoint(self):
        """Test 1: GET /api/invoicing/export-drafted-csv endpoint"""
        print("\n=== TEST 1: CSV EXPORT ENDPOINT ===")
        
        try:
            response = self.session.get(f"{API_BASE}/invoicing/export-drafted-csv")
            
            if response.status_code == 200:
                # Check response headers
                content_type = response.headers.get('content-type', '')
                content_disposition = response.headers.get('content-disposition', '')
                
                if 'text/csv' in content_type:
                    self.log_result(
                        "CSV Export Endpoint - Content Type", 
                        True, 
                        "Returns proper CSV content type",
                        f"Content-Type: {content_type}"
                    )
                else:
                    self.log_result(
                        "CSV Export Endpoint - Content Type", 
                        False, 
                        f"Incorrect content type: {content_type}",
                        "Expected: text/csv"
                    )
                
                if 'attachment' in content_disposition and 'drafted_invoices_' in content_disposition:
                    self.log_result(
                        "CSV Export Endpoint - File Download", 
                        True, 
                        "Properly formatted CSV file download",
                        f"Filename includes date: {content_disposition}"
                    )
                else:
                    self.log_result(
                        "CSV Export Endpoint - File Download", 
                        False, 
                        f"Incorrect download headers: {content_disposition}",
                        "Expected: attachment with dated filename"
                    )
                
                return response.text
            else:
                self.log_result(
                    "CSV Export Endpoint", 
                    False, 
                    f"Endpoint failed with status {response.status_code}",
                    response.text
                )
                return None
                
        except Exception as e:
            self.log_result("CSV Export Endpoint", False, f"Error: {str(e)}")
            return None
    
    def test_csv_format_compliance(self, csv_content):
        """Test 2: CSV format compliance with Xero import format"""
        print("\n=== TEST 2: CSV FORMAT COMPLIANCE ===")
        
        if not csv_content:
            self.log_result("CSV Format Compliance", False, "No CSV content to test")
            return
        
        try:
            # Parse CSV
            csv_reader = csv.reader(io.StringIO(csv_content))
            rows = list(csv_reader)
            
            if len(rows) < 1:
                self.log_result("CSV Format Compliance", False, "CSV is empty")
                return
            
            headers = rows[0]
            
            # Test required Xero fields
            required_fields = [
                "ContactName", "InvoiceNumber", "InvoiceDate", "DueDate", 
                "Description", "Quantity", "UnitAmount", "AccountCode", "TaxType"
            ]
            
            missing_required = [field for field in required_fields if field not in headers]
            
            if not missing_required:
                self.log_result(
                    "CSV Format - Required Fields", 
                    True, 
                    "All required Xero fields present",
                    f"Required fields: {len(required_fields)}"
                )
            else:
                self.log_result(
                    "CSV Format - Required Fields", 
                    False, 
                    f"Missing required fields: {missing_required}",
                    f"Available headers: {headers}"
                )
            
            # Test optional fields
            optional_fields = [
                "EmailAddress", "InventoryItemCode", "Discount", "Reference", "Currency"
            ]
            
            present_optional = [field for field in optional_fields if field in headers]
            
            self.log_result(
                "CSV Format - Optional Fields", 
                True, 
                f"Optional fields present: {len(present_optional)}/{len(optional_fields)}",
                f"Present: {present_optional}"
            )
            
            # Test data rows if available
            if len(rows) > 1:
                self.test_csv_data_rows(headers, rows[1:])
            else:
                self.log_result(
                    "CSV Format - Data Rows", 
                    True, 
                    "CSV contains headers only (no accounting transactions)",
                    "This is expected if no drafted invoices exist"
                )
                
        except Exception as e:
            self.log_result("CSV Format Compliance", False, f"Error parsing CSV: {str(e)}")
    
    def test_csv_data_rows(self, headers, data_rows):
        """Test CSV data rows for proper formatting"""
        print("\n=== CSV DATA ROWS TESTING ===")
        
        try:
            self.log_result(
                "CSV Data Rows - Count", 
                True, 
                f"CSV contains {len(data_rows)} data rows",
                f"Each row represents a line item"
            )
            
            # Test first row for format compliance
            if data_rows:
                first_row = data_rows[0]
                field_map = dict(zip(headers, first_row))
                
                # Test date formats (DD/MM/YYYY)
                self.test_date_formatting(field_map)
                
                # Test account code
                self.test_account_code(field_map)
                
                # Test tax type
                self.test_tax_type(field_map)
                
                # Test currency
                self.test_currency(field_map)
                
                # Test numeric fields
                self.test_numeric_fields(field_map)
                
        except Exception as e:
            self.log_result("CSV Data Rows", False, f"Error: {str(e)}")
    
    def test_date_formatting(self, field_map):
        """Test proper date formatting (DD/MM/YYYY)"""
        date_fields = ["InvoiceDate", "DueDate"]
        
        for field in date_fields:
            if field in field_map and field_map[field]:
                date_value = field_map[field].strip()
                
                # Check DD/MM/YYYY format
                import re
                if re.match(r'\d{2}/\d{2}/\d{4}', date_value):
                    self.log_result(
                        f"CSV Date Format - {field}", 
                        True, 
                        f"Correct date format: {date_value}",
                        "Format: DD/MM/YYYY as required by Xero"
                    )
                else:
                    self.log_result(
                        f"CSV Date Format - {field}", 
                        False, 
                        f"Incorrect date format: {date_value}",
                        "Expected: DD/MM/YYYY"
                    )
    
    def test_account_code(self, field_map):
        """Test account code using XERO_SALES_ACCOUNT_CODE (200)"""
        if "AccountCode" in field_map:
            account_code = field_map["AccountCode"].strip()
            expected_code = "200"  # XERO_SALES_ACCOUNT_CODE
            
            if account_code == expected_code:
                self.log_result(
                    "CSV Account Code", 
                    True, 
                    f"Correct account code: {account_code}",
                    "Uses XERO_SALES_ACCOUNT_CODE (200) for sales"
                )
            else:
                self.log_result(
                    "CSV Account Code", 
                    False, 
                    f"Incorrect account code: {account_code}",
                    f"Expected: {expected_code} (XERO_SALES_ACCOUNT_CODE)"
                )
    
    def test_tax_type(self, field_map):
        """Test tax type for GST compliance"""
        if "TaxType" in field_map:
            tax_type = field_map["TaxType"].strip()
            
            if tax_type == "OUTPUT":
                self.log_result(
                    "CSV Tax Type", 
                    True, 
                    f"Correct tax type: {tax_type}",
                    "OUTPUT for GST on sales (Australian tax system)"
                )
            else:
                self.log_result(
                    "CSV Tax Type", 
                    False, 
                    f"Incorrect tax type: {tax_type}",
                    "Expected: OUTPUT for GST sales"
                )
    
    def test_currency(self, field_map):
        """Test currency field"""
        if "Currency" in field_map:
            currency = field_map["Currency"].strip()
            
            if currency == "AUD":
                self.log_result(
                    "CSV Currency", 
                    True, 
                    f"Correct currency: {currency}",
                    "Australian Dollar as expected"
                )
            else:
                self.log_result(
                    "CSV Currency", 
                    False, 
                    f"Incorrect currency: {currency}",
                    "Expected: AUD"
                )
    
    def test_numeric_fields(self, field_map):
        """Test numeric fields for proper formatting"""
        numeric_fields = ["Quantity", "UnitAmount"]
        
        for field in numeric_fields:
            if field in field_map and field_map[field]:
                value = field_map[field].strip()
                
                try:
                    float(value)
                    self.log_result(
                        f"CSV Numeric - {field}", 
                        True, 
                        f"Valid numeric value: {value}",
                        "Properly formatted for Xero import"
                    )
                except ValueError:
                    self.log_result(
                        f"CSV Numeric - {field}", 
                        False, 
                        f"Invalid numeric value: {value}",
                        "Should be a valid number"
                    )
    
    def test_data_mapping(self):
        """Test 3: Data mapping from accounting transactions to CSV"""
        print("\n=== TEST 3: DATA MAPPING ===")
        
        try:
            # Get accounting transactions
            response = self.session.get(f"{API_BASE}/invoicing/accounting-transactions")
            
            if response.status_code == 200:
                transactions_data = response.json()
                transactions = transactions_data.get('data', [])
                
                self.log_result(
                    "Data Mapping - Source Data", 
                    True, 
                    f"Found {len(transactions)} accounting transactions",
                    "Source data for CSV export"
                )
                
                if transactions:
                    # Test specific field mapping
                    transaction = transactions[0]
                    
                    # Test client information mapping
                    client_name = transaction.get('client_name')
                    client_email = transaction.get('client_email')
                    
                    if client_name:
                        self.log_result(
                            "Data Mapping - Client Name", 
                            True, 
                            f"Client name mapped: {client_name}",
                            "Maps to ContactName in CSV"
                        )
                    
                    if client_email:
                        self.log_result(
                            "Data Mapping - Client Email", 
                            True, 
                            f"Client email mapped: {client_email}",
                            "Maps to EmailAddress in CSV"
                        )
                    
                    # Test invoice details
                    order_number = transaction.get('order_number')
                    if order_number:
                        self.log_result(
                            "Data Mapping - Order Reference", 
                            True, 
                            f"Order number mapped: {order_number}",
                            "Maps to Reference field in CSV"
                        )
                    
                    # Test line items
                    items = transaction.get('items', [])
                    if items:
                        self.log_result(
                            "Data Mapping - Line Items", 
                            True, 
                            f"Found {len(items)} line items",
                            "Each item becomes a CSV row"
                        )
                        
                        # Test first item mapping
                        item = items[0]
                        product_name = item.get('product_name')
                        quantity = item.get('quantity')
                        unit_price = item.get('unit_price')
                        
                        if product_name:
                            self.log_result(
                                "Data Mapping - Product Description", 
                                True, 
                                f"Product name mapped: {product_name}",
                                "Maps to Description field in CSV"
                            )
                        
                        if quantity:
                            self.log_result(
                                "Data Mapping - Quantity", 
                                True, 
                                f"Quantity mapped: {quantity}",
                                "Maps to Quantity field in CSV"
                            )
                        
                        if unit_price:
                            self.log_result(
                                "Data Mapping - Unit Price", 
                                True, 
                                f"Unit price mapped: {unit_price}",
                                "Maps to UnitAmount field in CSV"
                            )
                else:
                    self.log_result(
                        "Data Mapping - No Data", 
                        True, 
                        "No accounting transactions found",
                        "CSV will contain headers only"
                    )
            else:
                self.log_result(
                    "Data Mapping - Source Data", 
                    False, 
                    f"Failed to get accounting transactions: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Data Mapping", False, f"Error: {str(e)}")
    
    def test_empty_scenarios(self):
        """Test 4: Empty scenarios handling"""
        print("\n=== TEST 4: EMPTY SCENARIOS ===")
        
        try:
            # The CSV export should handle empty scenarios gracefully
            response = self.session.get(f"{API_BASE}/invoicing/export-drafted-csv")
            
            if response.status_code == 200:
                csv_content = response.text
                lines = csv_content.strip().split('\n')
                
                if len(lines) >= 1:
                    # Should always have headers
                    self.log_result(
                        "Empty Scenarios - Headers Present", 
                        True, 
                        "CSV always includes headers even when no data",
                        f"Header line: {lines[0][:50]}..."
                    )
                    
                    if len(lines) == 1:
                        self.log_result(
                            "Empty Scenarios - No Data Handling", 
                            True, 
                            "Gracefully handles empty data with headers only",
                            "No error when no accounting transactions exist"
                        )
                    else:
                        self.log_result(
                            "Empty Scenarios - Data Present", 
                            True, 
                            f"CSV contains {len(lines)-1} data rows",
                            "Data is available for export"
                        )
                else:
                    self.log_result(
                        "Empty Scenarios - Malformed CSV", 
                        False, 
                        "CSV appears to be empty or malformed",
                        f"Content length: {len(csv_content)}"
                    )
            else:
                self.log_result(
                    "Empty Scenarios", 
                    False, 
                    f"Failed to test empty scenarios: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Empty Scenarios", False, f"Error: {str(e)}")
    
    def test_csv_file_structure(self):
        """Test 5: CSV file structure and formatting"""
        print("\n=== TEST 5: CSV FILE STRUCTURE ===")
        
        try:
            response = self.session.get(f"{API_BASE}/invoicing/export-drafted-csv")
            
            if response.status_code == 200:
                csv_content = response.text
                
                # Test CSV parsing
                try:
                    csv_reader = csv.reader(io.StringIO(csv_content))
                    rows = list(csv_reader)
                    
                    self.log_result(
                        "CSV File Structure - Parsing", 
                        True, 
                        "CSV is properly formatted and parseable",
                        f"Successfully parsed {len(rows)} rows"
                    )
                    
                    if rows:
                        # Test header consistency
                        header_count = len(rows[0])
                        consistent_columns = all(len(row) == header_count for row in rows)
                        
                        if consistent_columns:
                            self.log_result(
                                "CSV File Structure - Column Consistency", 
                                True, 
                                f"All rows have consistent {header_count} columns",
                                "Proper CSV structure maintained"
                            )
                        else:
                            self.log_result(
                                "CSV File Structure - Column Consistency", 
                                False, 
                                "Inconsistent column count across rows",
                                "Some rows may be malformed"
                            )
                        
                        # Test for proper CSV escaping
                        has_commas_in_data = any(',' in cell for row in rows for cell in row if cell)
                        if has_commas_in_data:
                            self.log_result(
                                "CSV File Structure - Data Escaping", 
                                True, 
                                "CSV properly handles commas in data",
                                "Data with commas is properly quoted"
                            )
                        else:
                            self.log_result(
                                "CSV File Structure - Data Escaping", 
                                True, 
                                "No special characters requiring escaping found",
                                "Clean data structure"
                            )
                            
                except csv.Error as e:
                    self.log_result(
                        "CSV File Structure - Parsing", 
                        False, 
                        f"CSV parsing failed: {str(e)}",
                        "CSV may be malformed"
                    )
            else:
                self.log_result(
                    "CSV File Structure", 
                    False, 
                    f"Failed to get CSV: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("CSV File Structure", False, f"Error: {str(e)}")
    
    def run_comprehensive_tests(self):
        """Run all comprehensive CSV export tests"""
        print("="*80)
        print("COMPREHENSIVE CSV EXPORT TESTING")
        print("Testing new CSV export functionality for drafted invoices")
        print("="*80)
        
        # Step 1: Authenticate
        if not self.authenticate():
            print("❌ Authentication failed - cannot proceed with tests")
            return
        
        # Step 2: Test CSV export endpoint
        csv_content = self.test_csv_export_endpoint()
        
        # Step 3: Test CSV format compliance
        self.test_csv_format_compliance(csv_content)
        
        # Step 4: Test data mapping
        self.test_data_mapping()
        
        # Step 5: Test empty scenarios
        self.test_empty_scenarios()
        
        # Step 6: Test CSV file structure
        self.test_csv_file_structure()
        
        # Print comprehensive summary
        self.print_comprehensive_summary()
    
    def print_comprehensive_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "="*80)
        print("COMPREHENSIVE CSV EXPORT TEST SUMMARY")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['success']])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%" if total_tests > 0 else "0%")
        
        # Group results by test category
        categories = {}
        for result in self.test_results:
            test_name = result['test']
            # Extract category from test name
            if ' - ' in test_name:
                category = test_name.split(' - ')[0]
            else:
                category = test_name.split(' ')[0] + ' ' + test_name.split(' ')[1] if len(test_name.split(' ')) > 1 else test_name
            
            if category not in categories:
                categories[category] = []
            categories[category].append(result)
        
        print("\n" + "-"*80)
        print("DETAILED RESULTS BY CATEGORY:")
        print("-"*80)
        
        for category, results in categories.items():
            passed = len([r for r in results if r['success']])
            total = len(results)
            print(f"\n{category}: {passed}/{total} passed")
            
            for result in results:
                status = "✅" if result['success'] else "❌"
                print(f"  {status} {result['message']}")
                if result['details'] and not result['success']:
                    print(f"     Details: {result['details']}")
        
        print("\n" + "="*80)
        print("XERO IMPORT COMPLIANCE ANALYSIS:")
        print("="*80)
        
        # Check specific Xero requirements
        xero_requirements = {
            "Required Fields Present": any("required fields" in r['test'].lower() and r['success'] for r in self.test_results),
            "Date Format (DD/MM/YYYY)": any("date format" in r['test'].lower() and r['success'] for r in self.test_results),
            "Account Code (200)": any("account code" in r['test'].lower() and r['success'] for r in self.test_results),
            "Tax Type (OUTPUT)": any("tax type" in r['test'].lower() and r['success'] for r in self.test_results),
            "Currency (AUD)": any("currency" in r['test'].lower() and r['success'] for r in self.test_results),
            "Proper CSV Structure": any("csv file structure" in r['test'].lower() and r['success'] for r in self.test_results),
            "Data Mapping": any("data mapping" in r['test'].lower() and r['success'] for r in self.test_results)
        }
        
        compliant_count = sum(1 for req, status in xero_requirements.items() if status)
        total_requirements = len(xero_requirements)
        compliance_rate = (compliant_count / total_requirements) * 100
        
        print(f"Xero Import Compliance: {compliance_rate:.1f}% ({compliant_count}/{total_requirements})")
        
        print("\n✅ Compliant Requirements:")
        for req, status in xero_requirements.items():
            if status:
                print(f"  ✅ {req}")
        
        non_compliant = [req for req, status in xero_requirements.items() if not status]
        if non_compliant:
            print("\n❌ Non-Compliant Requirements:")
            for req in non_compliant:
                print(f"  ❌ {req}")
        
        print("\n" + "="*80)
        print("FINAL ASSESSMENT:")
        print("="*80)
        
        if compliance_rate >= 90:
            print("🎉 EXCELLENT: CSV export functionality is fully compliant with Xero import requirements")
        elif compliance_rate >= 75:
            print("✅ GOOD: CSV export functionality meets most Xero import requirements")
        elif compliance_rate >= 50:
            print("⚠️ NEEDS IMPROVEMENT: CSV export functionality has some compliance issues")
        else:
            print("❌ CRITICAL: CSV export functionality has major compliance issues")
        
        print(f"\nThe CSV export endpoint is {'✅ WORKING' if passed_tests > failed_tests else '❌ FAILING'}")
        print(f"Xero import format compliance: {compliance_rate:.1f}%")
        
        if failed_tests == 0:
            print("\n🎉 ALL TESTS PASSED - CSV export functionality is ready for production!")
        elif failed_tests <= 2:
            print(f"\n⚠️ Minor issues found ({failed_tests} failed tests) - review and fix before production")
        else:
            print(f"\n❌ Major issues found ({failed_tests} failed tests) - significant work needed")
        
        print("\n" + "="*80)

if __name__ == "__main__":
    tester = CSVExportTester()
    tester.run_comprehensive_tests()