#!/usr/bin/env python3
"""
Part Supply Invoicing Workflow Testing Suite
Testing the COMPLETE Part Supply Invoicing workflow for order ADM-2025-0007

COMPLETE WORKFLOW TEST:
1. Verify current state of order ADM-2025-0007
2. Create second partial invoice (500 units) - should get INV-0036~2
3. Create third partial invoice (640 units) - should get INV-0036~3  
4. Create fourth and final invoice (500 units) - should get INV-0036~4
5. Verify order moves to accounting_transaction stage when fully invoiced
6. Test packing slip and invoice document downloads
"""

import requests
import json
import os
from datetime import datetime, timedelta, date
from dotenv import load_dotenv
import uuid

# Load environment variables
load_dotenv('/app/frontend/.env')

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:8001')
API_BASE = f"{BACKEND_URL}/api"

class PartSupplyInvoicingTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        self.target_order_id = "ADM-2025-0007"
        
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

    def test_complete_part_supply_invoicing_workflow(self):
        """
        MAIN TEST: Complete Part Supply Invoicing Workflow for ADM-2025-0007
        """
        print("\n" + "="*80)
        print("COMPLETE PART SUPPLY INVOICING WORKFLOW TEST")
        print("Testing order ADM-2025-0007 with LM Paper Core - 2640 units total")
        print("Already invoiced: 1000 units (INV-0036)")
        print("Remaining to invoice: 1640 units in 3 partial invoices")
        print("="*80)
        
        # Step 1: Verify current state
        order_data = self.verify_current_order_state()
        if not order_data:
            return
        
        # Step 2: Second partial invoice (500 units)
        self.create_partial_invoice(order_data["id"], 500, "Second partial invoice")
        
        # Step 3: Third partial invoice (640 units)  
        self.create_partial_invoice(order_data["id"], 640, "Third partial invoice")
        
        # Step 4: Fourth and final invoice (500 units)
        self.create_final_partial_invoice(order_data["id"], 500, "Fourth and final invoice")
        
        # Step 5: Verify final state
        self.verify_final_order_state(order_data["id"])
        
        # Step 6: Test document downloads
        self.test_document_downloads(order_data["id"])

    def verify_current_order_state(self):
        """Step 1: Verify the current state of order ADM-2025-0007"""
        try:
            # First, find the order by order number
            response = self.session.get(f"{API_BASE}/orders")
            
            if response.status_code != 200:
                self.log_result(
                    "Get Orders List", 
                    False, 
                    f"Failed to get orders: {response.status_code}",
                    response.text
                )
                return None
            
            orders = response.json()
            target_order = None
            
            for order in orders:
                if order.get("order_number") == self.target_order_id:
                    target_order = order
                    break
            
            if not target_order:
                self.log_result(
                    "Find Target Order", 
                    False, 
                    f"Order {self.target_order_id} not found in orders list"
                )
                return None
            
            # Get detailed order information
            order_id = target_order["id"]
            response = self.session.get(f"{API_BASE}/orders/{order_id}")
            
            if response.status_code != 200:
                self.log_result(
                    "Get Order Details", 
                    False, 
                    f"Failed to get order details: {response.status_code}",
                    response.text
                )
                return None
            
            order_data = response.json()
            
            # Verify order details
            self.verify_order_details(order_data)
            
            return order_data
            
        except Exception as e:
            self.log_result("Verify Current Order State", False, f"Error: {str(e)}")
            return None

    def verify_order_details(self, order_data):
        """Verify the order has expected details"""
        try:
            order_number = order_data.get("order_number")
            current_stage = order_data.get("current_stage")
            status = order_data.get("status")
            partially_invoiced = order_data.get("partially_invoiced", False)
            invoiced = order_data.get("invoiced", False)
            invoice_history = order_data.get("invoice_history", [])
            
            # Check order number
            if order_number == self.target_order_id:
                self.log_result(
                    "Verify Order Number", 
                    True, 
                    f"Order number confirmed: {order_number}"
                )
            else:
                self.log_result(
                    "Verify Order Number", 
                    False, 
                    f"Expected {self.target_order_id}, got {order_number}"
                )
            
            # Check current stage (should be delivery or invoicing)
            expected_stages = ["delivery", "invoicing"]
            if current_stage in expected_stages:
                self.log_result(
                    "Verify Order Stage", 
                    True, 
                    f"Order in correct stage: {current_stage}"
                )
            else:
                self.log_result(
                    "Verify Order Stage", 
                    False, 
                    f"Expected stage in {expected_stages}, got {current_stage}"
                )
            
            # Check invoice status
            if partially_invoiced and not invoiced:
                self.log_result(
                    "Verify Invoice Status", 
                    True, 
                    f"Correct invoice status: partially_invoiced={partially_invoiced}, invoiced={invoiced}"
                )
            else:
                self.log_result(
                    "Verify Invoice Status", 
                    False, 
                    f"Unexpected invoice status: partially_invoiced={partially_invoiced}, invoiced={invoiced}"
                )
            
            # Check invoice history
            if len(invoice_history) >= 1:
                first_invoice = invoice_history[0]
                if first_invoice.get("invoice_number") == "INV-0036":
                    self.log_result(
                        "Verify Existing Invoice", 
                        True, 
                        f"Found existing invoice INV-0036 with {first_invoice.get('quantity_invoiced')} units"
                    )
                else:
                    self.log_result(
                        "Verify Existing Invoice", 
                        False, 
                        f"Expected INV-0036, got {first_invoice.get('invoice_number')}"
                    )
            else:
                self.log_result(
                    "Verify Existing Invoice", 
                    False, 
                    "No invoice history found"
                )
            
            # Check product details
            items = order_data.get("items", [])
            if items:
                item = items[0]
                product_name = item.get("product_name", "")
                quantity = item.get("quantity", 0)
                
                if "LM Paper Core" in product_name and quantity == 2640:
                    self.log_result(
                        "Verify Product Details", 
                        True, 
                        f"Product confirmed: {product_name}, Quantity: {quantity}"
                    )
                else:
                    self.log_result(
                        "Verify Product Details", 
                        False, 
                        f"Expected LM Paper Core with 2640 units, got {product_name} with {quantity} units"
                    )
            
        except Exception as e:
            self.log_result("Verify Order Details", False, f"Error: {str(e)}")

    def create_partial_invoice(self, order_id, quantity, description):
        """Create a partial invoice for the specified quantity"""
        try:
            # First get the order to get the item details
            order_response = self.session.get(f"{API_BASE}/orders/{order_id}")
            if order_response.status_code != 200:
                self.log_result(
                    f"Get Order for Invoice - {description}", 
                    False, 
                    f"Failed to get order: {order_response.status_code}"
                )
                return None
            
            order_data = order_response.json()
            original_items = order_data.get("items", [])
            
            if not original_items:
                self.log_result(
                    f"Get Order Items - {description}", 
                    False, 
                    "No items found in order"
                )
                return None
            
            # Create partial items with the specified quantity
            partial_items = []
            for item in original_items:
                partial_item = item.copy()
                partial_item["quantity"] = quantity
                # Recalculate total price based on partial quantity
                unit_price = item.get("unit_price", 0)
                partial_item["total_price"] = quantity * unit_price
                partial_items.append(partial_item)
            
            # Calculate partial totals
            subtotal = sum(item["total_price"] for item in partial_items)
            gst = subtotal * 0.1
            total_amount = subtotal + gst
            
            invoice_data = {
                "invoice_type": "partial",
                "items": partial_items,
                "subtotal": subtotal,
                "gst": gst,
                "total_amount": total_amount
            }
            
            response = self.session.post(f"{API_BASE}/invoicing/generate/{order_id}", json=invoice_data)
            
            if response.status_code == 200:
                result = response.json()
                invoice_number = result.get("data", {}).get("invoice_number")
                
                self.log_result(
                    f"Create Partial Invoice - {description}", 
                    True, 
                    f"Successfully created invoice {invoice_number} for {quantity} units"
                )
                
                # Verify order state after invoice
                self.verify_order_state_after_invoice(order_id, description)
                
                return invoice_number
            else:
                self.log_result(
                    f"Create Partial Invoice - {description}", 
                    False, 
                    f"Failed to create invoice: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result(f"Create Partial Invoice - {description}", False, f"Error: {str(e)}")
        
        return None

    def create_final_partial_invoice(self, order_id, quantity, description):
        """Create the final partial invoice that should complete the order"""
        try:
            # First get the order to get the item details
            order_response = self.session.get(f"{API_BASE}/orders/{order_id}")
            if order_response.status_code != 200:
                self.log_result(
                    f"Get Order for Final Invoice - {description}", 
                    False, 
                    f"Failed to get order: {order_response.status_code}"
                )
                return None
            
            order_data = order_response.json()
            original_items = order_data.get("items", [])
            
            if not original_items:
                self.log_result(
                    f"Get Order Items for Final Invoice - {description}", 
                    False, 
                    "No items found in order"
                )
                return None
            
            # Create partial items with the specified quantity
            partial_items = []
            for item in original_items:
                partial_item = item.copy()
                partial_item["quantity"] = quantity
                # Recalculate total price based on partial quantity
                unit_price = item.get("unit_price", 0)
                partial_item["total_price"] = quantity * unit_price
                partial_items.append(partial_item)
            
            # Calculate partial totals
            subtotal = sum(item["total_price"] for item in partial_items)
            gst = subtotal * 0.1
            total_amount = subtotal + gst
            
            invoice_data = {
                "invoice_type": "partial",
                "items": partial_items,
                "subtotal": subtotal,
                "gst": gst,
                "total_amount": total_amount
            }
            
            response = self.session.post(f"{API_BASE}/invoicing/generate/{order_id}", json=invoice_data)
            
            if response.status_code == 200:
                result = response.json()
                invoice_number = result.get("data", {}).get("invoice_number")
                
                self.log_result(
                    f"Create Final Invoice - {description}", 
                    True, 
                    f"Successfully created final invoice {invoice_number} for {quantity} units"
                )
                
                # Verify order is now fully invoiced
                self.verify_order_fully_invoiced(order_id)
                
                return invoice_number
            else:
                self.log_result(
                    f"Create Final Invoice - {description}", 
                    False, 
                    f"Failed to create final invoice: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result(f"Create Final Invoice - {description}", False, f"Error: {str(e)}")
        
        return None

    def verify_order_state_after_invoice(self, order_id, description):
        """Verify order state after creating a partial invoice"""
        try:
            response = self.session.get(f"{API_BASE}/orders/{order_id}")
            
            if response.status_code == 200:
                order_data = response.json()
                current_stage = order_data.get("current_stage")
                partially_invoiced = order_data.get("partially_invoiced", False)
                invoiced = order_data.get("invoiced", False)
                invoice_history = order_data.get("invoice_history", [])
                
                # Should still be in delivery/invoicing stage
                if current_stage in ["delivery", "invoicing"]:
                    self.log_result(
                        f"Verify Stage After {description}", 
                        True, 
                        f"Order correctly remains in {current_stage} stage"
                    )
                else:
                    self.log_result(
                        f"Verify Stage After {description}", 
                        False, 
                        f"Unexpected stage: {current_stage}"
                    )
                
                # Should still be partially invoiced but not fully invoiced
                if partially_invoiced and not invoiced:
                    self.log_result(
                        f"Verify Invoice Status After {description}", 
                        True, 
                        "Order correctly marked as partially invoiced"
                    )
                else:
                    self.log_result(
                        f"Verify Invoice Status After {description}", 
                        False, 
                        f"Unexpected invoice status: partially_invoiced={partially_invoiced}, invoiced={invoiced}"
                    )
                
                # Check invoice history count
                expected_count = 2 if "Second" in description else 3 if "Third" in description else len(invoice_history)
                if len(invoice_history) == expected_count:
                    self.log_result(
                        f"Verify Invoice History Count After {description}", 
                        True, 
                        f"Invoice history has {len(invoice_history)} entries as expected"
                    )
                else:
                    self.log_result(
                        f"Verify Invoice History Count After {description}", 
                        False, 
                        f"Expected {expected_count} invoices, got {len(invoice_history)}"
                    )
                
            else:
                self.log_result(
                    f"Verify Order State After {description}", 
                    False, 
                    f"Failed to get order: {response.status_code}"
                )
                
        except Exception as e:
            self.log_result(f"Verify Order State After {description}", False, f"Error: {str(e)}")

    def verify_order_fully_invoiced(self, order_id):
        """Verify order is fully invoiced and moved to accounting_transaction stage"""
        try:
            response = self.session.get(f"{API_BASE}/orders/{order_id}")
            
            if response.status_code == 200:
                order_data = response.json()
                current_stage = order_data.get("current_stage")
                partially_invoiced = order_data.get("partially_invoiced", False)
                invoiced = order_data.get("invoiced", False)
                fully_invoiced = order_data.get("fully_invoiced", False)
                invoice_history = order_data.get("invoice_history", [])
                
                # Should be in accounting_transaction stage
                if current_stage == "accounting_transaction":
                    self.log_result(
                        "Verify Final Stage", 
                        True, 
                        f"Order correctly moved to accounting_transaction stage"
                    )
                else:
                    self.log_result(
                        "Verify Final Stage", 
                        False, 
                        f"Expected accounting_transaction, got {current_stage}"
                    )
                
                # Should be fully invoiced
                if invoiced and fully_invoiced:
                    self.log_result(
                        "Verify Fully Invoiced Status", 
                        True, 
                        "Order correctly marked as fully invoiced"
                    )
                else:
                    self.log_result(
                        "Verify Fully Invoiced Status", 
                        False, 
                        f"Expected fully invoiced, got invoiced={invoiced}, fully_invoiced={fully_invoiced}"
                    )
                
                # Should have 4 invoices total
                if len(invoice_history) == 4:
                    self.log_result(
                        "Verify Complete Invoice History", 
                        True, 
                        f"Invoice history has all 4 invoices"
                    )
                    
                    # Verify invoice numbers
                    expected_numbers = ["INV-0036", "INV-0036~2", "INV-0036~3", "INV-0036~4"]
                    actual_numbers = [inv.get("invoice_number") for inv in invoice_history]
                    
                    if actual_numbers == expected_numbers:
                        self.log_result(
                            "Verify Invoice Number Sequence", 
                            True, 
                            f"Invoice numbers correct: {actual_numbers}"
                        )
                    else:
                        self.log_result(
                            "Verify Invoice Number Sequence", 
                            False, 
                            f"Expected {expected_numbers}, got {actual_numbers}"
                        )
                else:
                    self.log_result(
                        "Verify Complete Invoice History", 
                        False, 
                        f"Expected 4 invoices, got {len(invoice_history)}"
                    )
                
            else:
                self.log_result(
                    "Verify Order Fully Invoiced", 
                    False, 
                    f"Failed to get order: {response.status_code}"
                )
                
        except Exception as e:
            self.log_result("Verify Order Fully Invoiced", False, f"Error: {str(e)}")

    def verify_final_order_state(self, order_id):
        """Verify the final state of the order"""
        try:
            response = self.session.get(f"{API_BASE}/orders/{order_id}")
            
            if response.status_code == 200:
                order_data = response.json()
                
                # Check that order no longer appears in "Jobs Ready for Invoicing"
                self.verify_order_not_in_invoicing_list(order_id)
                
                # Verify all quantities add up correctly
                self.verify_invoice_quantities(order_data)
                
            else:
                self.log_result(
                    "Verify Final Order State", 
                    False, 
                    f"Failed to get order: {response.status_code}"
                )
                
        except Exception as e:
            self.log_result("Verify Final Order State", False, f"Error: {str(e)}")

    def verify_order_not_in_invoicing_list(self, order_id):
        """Verify order no longer appears in Jobs Ready for Invoicing"""
        try:
            # Get orders in invoicing stage
            response = self.session.get(f"{API_BASE}/orders?status_filter=invoicing")
            
            if response.status_code == 200:
                invoicing_orders = response.json()
                
                # Check if our order is in the list
                order_found = any(order.get("id") == order_id for order in invoicing_orders)
                
                if not order_found:
                    self.log_result(
                        "Verify Order Not in Invoicing List", 
                        True, 
                        "Order correctly removed from Jobs Ready for Invoicing"
                    )
                else:
                    self.log_result(
                        "Verify Order Not in Invoicing List", 
                        False, 
                        "Order still appears in Jobs Ready for Invoicing"
                    )
            else:
                self.log_result(
                    "Verify Order Not in Invoicing List", 
                    False, 
                    f"Failed to get invoicing orders: {response.status_code}"
                )
                
        except Exception as e:
            self.log_result("Verify Order Not in Invoicing List", False, f"Error: {str(e)}")

    def verify_invoice_quantities(self, order_data):
        """Verify all invoice quantities add up correctly"""
        try:
            items = order_data.get("items", [])
            if not items:
                self.log_result(
                    "Verify Invoice Quantities", 
                    False, 
                    "No items found in order"
                )
                return
            
            total_ordered = items[0].get("quantity", 0)
            invoice_history = order_data.get("invoice_history", [])
            
            total_invoiced = sum(inv.get("quantity_invoiced", 0) for inv in invoice_history)
            
            if total_invoiced == total_ordered:
                self.log_result(
                    "Verify Invoice Quantities", 
                    True, 
                    f"All quantities correctly invoiced: {total_invoiced}/{total_ordered}"
                )
                
                # Verify individual invoice quantities
                expected_quantities = [1000, 500, 640, 500]  # INV-0036, ~2, ~3, ~4
                actual_quantities = [inv.get("quantity_invoiced", 0) for inv in invoice_history]
                
                if actual_quantities == expected_quantities:
                    self.log_result(
                        "Verify Individual Invoice Quantities", 
                        True, 
                        f"Individual quantities correct: {actual_quantities}"
                    )
                else:
                    self.log_result(
                        "Verify Individual Invoice Quantities", 
                        False, 
                        f"Expected {expected_quantities}, got {actual_quantities}"
                    )
            else:
                self.log_result(
                    "Verify Invoice Quantities", 
                    False, 
                    f"Quantity mismatch: invoiced {total_invoiced}, ordered {total_ordered}"
                )
                
        except Exception as e:
            self.log_result("Verify Invoice Quantities", False, f"Error: {str(e)}")

    def test_document_downloads(self, order_id):
        """Test packing slip and invoice document downloads"""
        try:
            # Test packing slip download
            self.test_packing_slip_download(order_id)
            
            # Test invoice PDF download
            self.test_invoice_pdf_download(order_id)
            
        except Exception as e:
            self.log_result("Test Document Downloads", False, f"Error: {str(e)}")

    def test_packing_slip_download(self, order_id):
        """Test packing slip download"""
        try:
            response = self.session.get(f"{API_BASE}/documents/packing-list/{order_id}")
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                content_disposition = response.headers.get('content-disposition', '')
                
                if 'application/pdf' in content_type:
                    pdf_size = len(response.content)
                    self.log_result(
                        "Test Packing Slip Download", 
                        True, 
                        f"Successfully downloaded packing slip PDF ({pdf_size} bytes)"
                    )
                else:
                    self.log_result(
                        "Test Packing Slip Download", 
                        False, 
                        f"Response not a PDF: {content_type}"
                    )
            else:
                self.log_result(
                    "Test Packing Slip Download", 
                    False, 
                    f"Failed to download packing slip: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Test Packing Slip Download", False, f"Error: {str(e)}")

    def test_invoice_pdf_download(self, order_id):
        """Test invoice PDF download"""
        try:
            response = self.session.get(f"{API_BASE}/invoices/download/{order_id}")
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                content_disposition = response.headers.get('content-disposition', '')
                
                if 'application/pdf' in content_type:
                    pdf_size = len(response.content)
                    self.log_result(
                        "Test Invoice PDF Download", 
                        True, 
                        f"Successfully downloaded invoice PDF ({pdf_size} bytes)"
                    )
                else:
                    self.log_result(
                        "Test Invoice PDF Download", 
                        False, 
                        f"Response not a PDF: {content_type}"
                    )
            else:
                self.log_result(
                    "Test Invoice PDF Download", 
                    False, 
                    f"Failed to download invoice PDF: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Test Invoice PDF Download", False, f"Error: {str(e)}")

    def print_test_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "="*80)
        print("PART SUPPLY INVOICING WORKFLOW TEST SUMMARY")
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
            print("🎉 PERFECT! 100% SUCCESS RATE ACHIEVED!")
        elif success_rate >= 90:
            print(f"🎯 EXCELLENT! {success_rate:.1f}% SUCCESS RATE")
        elif success_rate >= 80:
            print(f"✅ GOOD! {success_rate:.1f}% SUCCESS RATE")
        else:
            print(f"⚠️  NEEDS IMPROVEMENT: {success_rate:.1f}% SUCCESS RATE")
        print("="*80)

def main():
    """Main test execution"""
    tester = PartSupplyInvoicingTester()
    
    # Authenticate first
    if not tester.authenticate():
        print("❌ Authentication failed. Cannot proceed with tests.")
        return
    
    # Run the complete workflow test
    tester.test_complete_part_supply_invoicing_workflow()
    
    # Print summary
    tester.print_test_summary()

if __name__ == "__main__":
    main()