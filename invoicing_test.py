#!/usr/bin/env python3
"""
Part Supply Invoicing Workflow Testing Suite
Testing the Part Supply Invoicing workflow for the Misty Manufacturing application.

TEST SCENARIO:
1. Find or create a test job/order in the delivery stage ready for invoicing
2. Test partial invoicing workflow:
   a. First partial invoice: Invoice 50% of the order quantity
   b. Verify invoice created with ~1 suffix
   c. Verify job remains in delivery stage with status=active and partially_invoiced=True
   d. Verify invoice_history is updated with first invoice
   e. Verify remaining quantities are correct
   
   f. Second partial invoice: Invoice another 30% of the original order quantity
   g. Verify invoice created with ~2 suffix
   h. Verify job still remains in delivery stage (20% remaining)
   i. Verify invoice_history has both invoices
   
   j. Third partial invoice: Invoice the final 20%
   k. Verify invoice created with ~3 suffix
   l. Verify job is now fully invoiced and moved to accounting_transaction stage
   m. Verify fully_invoiced=True, invoiced=True
   n. Verify all three invoices are in invoice_history

API ENDPOINTS TO TEST:
- POST /api/invoicing/generate/{job_id} - with invoice_type: "partial"
- GET /api/orders/{job_id} - to verify status updates

EXPECTED BEHAVIOR:
- Partial invoices should have invoice numbers like INV-0001~1, INV-0001~2, INV-0001~3
- Job should remain in delivery stage until fully invoiced
- invoice_history should track all partial invoices
- Once fully invoiced, job should move to accounting_transaction stage

TEST CREDENTIALS:
- Username: Callum
- Password: Peach7510
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

class InvoicingWorkflowTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        self.test_order_id = None
        self.test_order_data = None
        self.invoice_ids = []
        
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

    def find_or_create_delivery_stage_order(self):
        """Find an existing order in delivery stage or create one"""
        print("\n=== FINDING OR CREATING DELIVERY STAGE ORDER ===")
        
        # First, try to find an existing order in delivery stage
        existing_order = self.find_delivery_stage_order()
        if existing_order:
            self.test_order_id = existing_order["id"]
            self.test_order_data = existing_order
            return True
        
        # If no existing order, create a new one
        return self.create_test_order_in_delivery_stage()
    
    def find_delivery_stage_order(self):
        """Find an existing order in delivery stage"""
        try:
            response = self.session.get(f"{API_BASE}/orders")
            
            if response.status_code == 200:
                orders = response.json()
                
                # Look for orders in delivery stage that are not yet invoiced
                delivery_orders = [
                    order for order in orders 
                    if order.get("current_stage") == "delivery" 
                    and not order.get("invoiced", False)
                    and not order.get("fully_invoiced", False)
                ]
                
                if delivery_orders:
                    order = delivery_orders[0]
                    self.log_result(
                        "Find Delivery Stage Order", 
                        True, 
                        f"Found existing order in delivery stage: {order.get('order_number')}",
                        f"Order ID: {order.get('id')}, Items: {len(order.get('items', []))}"
                    )
                    return order
                else:
                    self.log_result(
                        "Find Delivery Stage Order", 
                        False, 
                        "No existing orders in delivery stage found"
                    )
            else:
                self.log_result(
                    "Find Delivery Stage Order", 
                    False, 
                    f"Failed to get orders: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Find Delivery Stage Order", False, f"Error: {str(e)}")
        
        return None
    
    def create_test_order_in_delivery_stage(self):
        """Create a new test order and move it to delivery stage"""
        try:
            # Get clients first
            clients_response = self.session.get(f"{API_BASE}/clients")
            if clients_response.status_code != 200:
                self.log_result(
                    "Create Test Order - Get Clients", 
                    False, 
                    f"Failed to get clients: {clients_response.status_code}"
                )
                return False
            
            clients = clients_response.json()
            if not clients:
                self.log_result(
                    "Create Test Order - Get Clients", 
                    False, 
                    "No clients available"
                )
                return False
            
            client = clients[0]
            
            # Create order with multiple items for partial invoicing
            order_data = {
                "client_id": client["id"],
                "purchase_order_number": f"TEST-INVOICE-PO-{str(uuid.uuid4())[:8]}",
                "items": [
                    {
                        "product_id": str(uuid.uuid4()),
                        "product_name": "Test Paper Core - Large",
                        "quantity": 100,  # Will invoice 50, 30, 20
                        "unit_price": 15.00,
                        "total_price": 1500.00
                    },
                    {
                        "product_id": str(uuid.uuid4()),
                        "product_name": "Test Paper Core - Medium", 
                        "quantity": 200,  # Will invoice 100, 60, 40
                        "unit_price": 10.00,
                        "total_price": 2000.00
                    }
                ],
                "due_date": "2024-12-31",
                "priority": "Normal/Low",
                "notes": "Test order for partial invoicing workflow testing"
            }
            
            # Create the order
            response = self.session.post(f"{API_BASE}/orders", json=order_data)
            
            if response.status_code == 200:
                result = response.json()
                order_id = result.get("data", {}).get("id")
                order_number = result.get("data", {}).get("order_number")
                
                self.log_result(
                    "Create Test Order", 
                    True, 
                    f"Created test order: {order_number}",
                    f"Order ID: {order_id}"
                )
                
                # Move order through stages to delivery
                if self.move_order_to_delivery_stage(order_id):
                    self.test_order_id = order_id
                    # Get the updated order data
                    order_response = self.session.get(f"{API_BASE}/orders/{order_id}")
                    if order_response.status_code == 200:
                        self.test_order_data = order_response.json()
                    return True
                else:
                    return False
            else:
                self.log_result(
                    "Create Test Order", 
                    False, 
                    f"Failed to create order: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_result("Create Test Order", False, f"Error: {str(e)}")
            return False
    
    def move_order_to_delivery_stage(self, order_id):
        """Move order through production stages to delivery"""
        stages = [
            ("order_entered", "pending_material"),
            ("pending_material", "paper_slitting"),
            ("paper_slitting", "winding"),
            ("winding", "finishing"),
            ("finishing", "delivery")
        ]
        
        for from_stage, to_stage in stages:
            try:
                stage_data = {
                    "from_stage": from_stage,
                    "to_stage": to_stage,
                    "notes": f"Moving to {to_stage} for invoicing test"
                }
                
                response = self.session.put(f"{API_BASE}/orders/{order_id}/stage", json=stage_data)
                
                if response.status_code == 200:
                    self.log_result(
                        f"Move Order Stage: {from_stage} → {to_stage}", 
                        True, 
                        f"Successfully moved to {to_stage}"
                    )
                else:
                    self.log_result(
                        f"Move Order Stage: {from_stage} → {to_stage}", 
                        False, 
                        f"Failed to move stage: {response.status_code}",
                        response.text
                    )
                    return False
                    
            except Exception as e:
                self.log_result(f"Move Order Stage: {from_stage} → {to_stage}", False, f"Error: {str(e)}")
                return False
        
        return True
    
    def test_partial_invoicing_workflow(self):
        """Test the complete partial invoicing workflow"""
        print("\n=== PARTIAL INVOICING WORKFLOW TEST ===")
        
        if not self.test_order_id or not self.test_order_data:
            self.log_result(
                "Partial Invoicing Workflow", 
                False, 
                "No test order available for invoicing"
            )
            return
        
        # Test 1: First partial invoice (50% of quantities)
        self.test_first_partial_invoice()
        
        # Test 2: Second partial invoice (30% of original quantities)
        self.test_second_partial_invoice()
        
        # Test 3: Third partial invoice (remaining 20%)
        self.test_third_partial_invoice()
        
        # Test 4: Verify final job status
        self.test_final_job_status()
    
    def test_first_partial_invoice(self):
        """Test first partial invoice - 50% of quantities"""
        print("\n--- First Partial Invoice (50%) ---")
        
        try:
            # Calculate 50% of each item quantity
            partial_items = []
            for item in self.test_order_data["items"]:
                partial_quantity = int(item["quantity"] * 0.5)  # 50%
                partial_items.append({
                    "product_id": item["product_id"],
                    "product_name": item["product_name"],
                    "quantity": partial_quantity,
                    "unit_price": item["unit_price"],
                    "total_price": partial_quantity * item["unit_price"]
                })
            
            # Calculate totals
            subtotal = sum(item["total_price"] for item in partial_items)
            gst = subtotal * 0.1
            total_amount = subtotal + gst
            
            invoice_data = {
                "invoice_type": "partial",
                "items": partial_items,
                "subtotal": subtotal,
                "gst": gst,
                "total_amount": total_amount,
                "due_date": (datetime.now() + timedelta(days=30)).isoformat()
            }
            
            response = self.session.post(f"{API_BASE}/invoicing/generate/{self.test_order_id}", json=invoice_data)
            
            if response.status_code == 200:
                result = response.json()
                invoice_id = result.get("invoice_id")  # Direct access, not nested in data
                invoice_number = result.get("invoice_number")
                
                self.log_result(
                    "First Partial Invoice Generation", 
                    True, 
                    f"Successfully generated first partial invoice",
                    f"Invoice ID: {invoice_id}, Invoice Number: {invoice_number}, Items: {len(partial_items)}"
                )
                
                if invoice_id:
                    self.invoice_ids.append(invoice_id)
                
                # Verify invoice number has ~1 suffix directly from response
                if invoice_number and invoice_number.endswith("~1"):
                    self.log_result(
                        "Invoice Number Suffix Verification ~1", 
                        True, 
                        f"Invoice number correctly has suffix: {invoice_number}"
                    )
                else:
                    self.log_result(
                        "Invoice Number Suffix Verification ~1", 
                        False, 
                        f"Invoice number does not have expected suffix ~1",
                        f"Got: {invoice_number}"
                    )
                
                # Verify job status after first partial invoice
                self.verify_job_status_after_partial_invoice(1)
                
            else:
                self.log_result(
                    "First Partial Invoice Generation", 
                    False, 
                    f"Failed to generate first partial invoice: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("First Partial Invoice Generation", False, f"Error: {str(e)}")
    
    def test_second_partial_invoice(self):
        """Test second partial invoice - 30% of original quantities"""
        print("\n--- Second Partial Invoice (30%) ---")
        
        try:
            # Calculate 30% of each item quantity (from original order)
            partial_items = []
            for item in self.test_order_data["items"]:
                partial_quantity = int(item["quantity"] * 0.3)  # 30%
                partial_items.append({
                    "product_id": item["product_id"],
                    "product_name": item["product_name"],
                    "quantity": partial_quantity,
                    "unit_price": item["unit_price"],
                    "total_price": partial_quantity * item["unit_price"]
                })
            
            # Calculate totals
            subtotal = sum(item["total_price"] for item in partial_items)
            gst = subtotal * 0.1
            total_amount = subtotal + gst
            
            invoice_data = {
                "invoice_type": "partial",
                "items": partial_items,
                "subtotal": subtotal,
                "gst": gst,
                "total_amount": total_amount,
                "due_date": (datetime.now() + timedelta(days=30)).isoformat()
            }
            
            response = self.session.post(f"{API_BASE}/invoicing/generate/{self.test_order_id}", json=invoice_data)
            
            if response.status_code == 200:
                result = response.json()
                invoice_id = result.get("invoice_id")  # Direct access, not nested in data
                invoice_number = result.get("invoice_number")
                
                self.log_result(
                    "Second Partial Invoice Generation", 
                    True, 
                    f"Successfully generated second partial invoice",
                    f"Invoice ID: {invoice_id}, Invoice Number: {invoice_number}, Items: {len(partial_items)}"
                )
                
                if invoice_id:
                    self.invoice_ids.append(invoice_id)
                
                # Verify invoice number has ~2 suffix directly from response
                if invoice_number and invoice_number.endswith("~2"):
                    self.log_result(
                        "Invoice Number Suffix Verification ~2", 
                        True, 
                        f"Invoice number correctly has suffix: {invoice_number}"
                    )
                else:
                    self.log_result(
                        "Invoice Number Suffix Verification ~2", 
                        False, 
                        f"Invoice number does not have expected suffix ~2",
                        f"Got: {invoice_number}"
                    )
                
                # Verify job status after second partial invoice
                self.verify_job_status_after_partial_invoice(2)
                
            else:
                self.log_result(
                    "Second Partial Invoice Generation", 
                    False, 
                    f"Failed to generate second partial invoice: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Second Partial Invoice Generation", False, f"Error: {str(e)}")
    
    def test_third_partial_invoice(self):
        """Test third partial invoice - remaining 20%"""
        print("\n--- Third Partial Invoice (20% - Final) ---")
        
        try:
            # Calculate remaining 20% of each item quantity (from original order)
            partial_items = []
            for item in self.test_order_data["items"]:
                partial_quantity = int(item["quantity"] * 0.2)  # 20%
                partial_items.append({
                    "product_id": item["product_id"],
                    "product_name": item["product_name"],
                    "quantity": partial_quantity,
                    "unit_price": item["unit_price"],
                    "total_price": partial_quantity * item["unit_price"]
                })
            
            # Calculate totals
            subtotal = sum(item["total_price"] for item in partial_items)
            gst = subtotal * 0.1
            total_amount = subtotal + gst
            
            invoice_data = {
                "invoice_type": "partial",
                "items": partial_items,
                "subtotal": subtotal,
                "gst": gst,
                "total_amount": total_amount,
                "due_date": (datetime.now() + timedelta(days=30)).isoformat()
            }
            
            response = self.session.post(f"{API_BASE}/invoicing/generate/{self.test_order_id}", json=invoice_data)
            
            if response.status_code == 200:
                result = response.json()
                invoice_id = result.get("invoice_id")  # Direct access, not nested in data
                invoice_number = result.get("invoice_number")
                
                self.log_result(
                    "Third Partial Invoice Generation", 
                    True, 
                    f"Successfully generated third partial invoice (final)",
                    f"Invoice ID: {invoice_id}, Invoice Number: {invoice_number}, Items: {len(partial_items)}"
                )
                
                if invoice_id:
                    self.invoice_ids.append(invoice_id)
                
                # Verify invoice number has ~3 suffix directly from response
                if invoice_number and invoice_number.endswith("~3"):
                    self.log_result(
                        "Invoice Number Suffix Verification ~3", 
                        True, 
                        f"Invoice number correctly has suffix: {invoice_number}"
                    )
                else:
                    self.log_result(
                        "Invoice Number Suffix Verification ~3", 
                        False, 
                        f"Invoice number does not have expected suffix ~3",
                        f"Got: {invoice_number}"
                    )
                
                # Verify job is now fully invoiced
                self.verify_job_fully_invoiced()
                
            else:
                self.log_result(
                    "Third Partial Invoice Generation", 
                    False, 
                    f"Failed to generate third partial invoice: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Third Partial Invoice Generation", False, f"Error: {str(e)}")
    
    def verify_invoice_number_suffix(self, invoice_id, expected_suffix):
        """Verify invoice has the expected suffix"""
        try:
            # Get invoice details
            response = self.session.get(f"{API_BASE}/invoices/{invoice_id}")
            
            if response.status_code == 200:
                invoice = response.json()
                invoice_number = invoice.get("invoice_number", "")
                
                if invoice_number.endswith(expected_suffix):
                    self.log_result(
                        f"Invoice Number Suffix Verification {expected_suffix}", 
                        True, 
                        f"Invoice number correctly has suffix: {invoice_number}"
                    )
                else:
                    self.log_result(
                        f"Invoice Number Suffix Verification {expected_suffix}", 
                        False, 
                        f"Invoice number does not have expected suffix",
                        f"Expected: {expected_suffix}, Got: {invoice_number}"
                    )
            else:
                # Try alternative approach - check invoices collection
                invoices_response = self.session.get(f"{API_BASE}/invoices")
                if invoices_response.status_code == 200:
                    invoices = invoices_response.json()
                    matching_invoice = next((inv for inv in invoices if inv.get("id") == invoice_id), None)
                    
                    if matching_invoice:
                        invoice_number = matching_invoice.get("invoice_number", "")
                        if invoice_number.endswith(expected_suffix):
                            self.log_result(
                                f"Invoice Number Suffix Verification {expected_suffix}", 
                                True, 
                                f"Invoice number correctly has suffix: {invoice_number}"
                            )
                        else:
                            self.log_result(
                                f"Invoice Number Suffix Verification {expected_suffix}", 
                                False, 
                                f"Invoice number does not have expected suffix",
                                f"Expected: {expected_suffix}, Got: {invoice_number}"
                            )
                    else:
                        self.log_result(
                            f"Invoice Number Suffix Verification {expected_suffix}", 
                            False, 
                            f"Could not find invoice with ID: {invoice_id}"
                        )
                else:
                    self.log_result(
                        f"Invoice Number Suffix Verification {expected_suffix}", 
                        False, 
                        f"Failed to get invoice details: {response.status_code}",
                        response.text
                    )
                
        except Exception as e:
            self.log_result(f"Invoice Number Suffix Verification {expected_suffix}", False, f"Error: {str(e)}")
    
    def verify_job_status_after_partial_invoice(self, invoice_count):
        """Verify job status after partial invoice"""
        try:
            response = self.session.get(f"{API_BASE}/orders/{self.test_order_id}")
            
            if response.status_code == 200:
                job = response.json()
                
                # Check job is still in delivery stage
                current_stage = job.get("current_stage")
                if current_stage == "delivery":
                    self.log_result(
                        f"Job Stage After Partial Invoice {invoice_count}", 
                        True, 
                        f"Job correctly remains in delivery stage"
                    )
                else:
                    self.log_result(
                        f"Job Stage After Partial Invoice {invoice_count}", 
                        False, 
                        f"Job moved to unexpected stage: {current_stage}"
                    )
                
                # Check job status is active
                status = job.get("status")
                if status == "active":
                    self.log_result(
                        f"Job Status After Partial Invoice {invoice_count}", 
                        True, 
                        f"Job status correctly remains active"
                    )
                else:
                    self.log_result(
                        f"Job Status After Partial Invoice {invoice_count}", 
                        False, 
                        f"Job status is not active: {status}"
                    )
                
                # Check partially_invoiced flag
                partially_invoiced = job.get("partially_invoiced", False)
                if partially_invoiced:
                    self.log_result(
                        f"Partially Invoiced Flag After Invoice {invoice_count}", 
                        True, 
                        f"Job correctly marked as partially invoiced"
                    )
                else:
                    self.log_result(
                        f"Partially Invoiced Flag After Invoice {invoice_count}", 
                        False, 
                        f"Job not marked as partially invoiced"
                    )
                
                # Check invoice history
                invoice_history = job.get("invoice_history", [])
                if len(invoice_history) == invoice_count:
                    self.log_result(
                        f"Invoice History Count After Invoice {invoice_count}", 
                        True, 
                        f"Invoice history correctly has {invoice_count} entries"
                    )
                else:
                    self.log_result(
                        f"Invoice History Count After Invoice {invoice_count}", 
                        False, 
                        f"Invoice history has {len(invoice_history)} entries, expected {invoice_count}"
                    )
                
            else:
                self.log_result(
                    f"Job Status Verification After Invoice {invoice_count}", 
                    False, 
                    f"Failed to get job details: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result(f"Job Status Verification After Invoice {invoice_count}", False, f"Error: {str(e)}")
    
    def verify_job_fully_invoiced(self):
        """Verify job is fully invoiced and moved to accounting_transaction stage"""
        try:
            response = self.session.get(f"{API_BASE}/orders/{self.test_order_id}")
            
            if response.status_code == 200:
                job = response.json()
                
                # Check job moved to accounting_transaction stage
                current_stage = job.get("current_stage")
                if current_stage == "accounting_transaction":
                    self.log_result(
                        "Job Stage After Full Invoicing", 
                        True, 
                        f"Job correctly moved to accounting_transaction stage"
                    )
                else:
                    self.log_result(
                        "Job Stage After Full Invoicing", 
                        False, 
                        f"Job in unexpected stage: {current_stage}, expected accounting_transaction"
                    )
                
                # Check fully_invoiced flag
                fully_invoiced = job.get("fully_invoiced", False)
                if fully_invoiced:
                    self.log_result(
                        "Fully Invoiced Flag", 
                        True, 
                        f"Job correctly marked as fully invoiced"
                    )
                else:
                    self.log_result(
                        "Fully Invoiced Flag", 
                        False, 
                        f"Job not marked as fully invoiced"
                    )
                
                # Check invoiced flag
                invoiced = job.get("invoiced", False)
                if invoiced:
                    self.log_result(
                        "Invoiced Flag", 
                        True, 
                        f"Job correctly marked as invoiced"
                    )
                else:
                    self.log_result(
                        "Invoiced Flag", 
                        False, 
                        f"Job not marked as invoiced"
                    )
                
                # Check invoice history has all 3 invoices
                invoice_history = job.get("invoice_history", [])
                if len(invoice_history) == 3:
                    self.log_result(
                        "Final Invoice History Count", 
                        True, 
                        f"Invoice history correctly has all 3 invoices"
                    )
                    
                    # Verify invoice numbers have correct suffixes
                    expected_suffixes = ["~1", "~2", "~3"]
                    for i, invoice_entry in enumerate(invoice_history):
                        invoice_number = invoice_entry.get("invoice_number", "")
                        expected_suffix = expected_suffixes[i]
                        
                        if invoice_number.endswith(expected_suffix):
                            self.log_result(
                                f"Invoice History Entry {i+1} Suffix", 
                                True, 
                                f"Invoice {i+1} has correct suffix: {invoice_number}"
                            )
                        else:
                            self.log_result(
                                f"Invoice History Entry {i+1} Suffix", 
                                False, 
                                f"Invoice {i+1} has incorrect suffix: {invoice_number}"
                            )
                else:
                    self.log_result(
                        "Final Invoice History Count", 
                        False, 
                        f"Invoice history has {len(invoice_history)} entries, expected 3"
                    )
                
            else:
                self.log_result(
                    "Job Fully Invoiced Verification", 
                    False, 
                    f"Failed to get job details: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Job Fully Invoiced Verification", False, f"Error: {str(e)}")
    
    def test_final_job_status(self):
        """Test final job status and verify all requirements are met"""
        print("\n--- Final Job Status Verification ---")
        
        try:
            response = self.session.get(f"{API_BASE}/orders/{self.test_order_id}")
            
            if response.status_code == 200:
                job = response.json()
                
                # Print final job status for review
                print(f"\nFINAL JOB STATUS:")
                print(f"Order Number: {job.get('order_number')}")
                print(f"Current Stage: {job.get('current_stage')}")
                print(f"Status: {job.get('status')}")
                print(f"Invoiced: {job.get('invoiced')}")
                print(f"Fully Invoiced: {job.get('fully_invoiced')}")
                print(f"Partially Invoiced: {job.get('partially_invoiced')}")
                print(f"Invoice History Count: {len(job.get('invoice_history', []))}")
                
                # Verify all requirements
                requirements_met = True
                
                # 1. Job should be in accounting_transaction stage
                if job.get("current_stage") != "accounting_transaction":
                    requirements_met = False
                
                # 2. Job should be fully invoiced
                if not job.get("fully_invoiced"):
                    requirements_met = False
                
                # 3. Job should be invoiced
                if not job.get("invoiced"):
                    requirements_met = False
                
                # 4. Should have 3 invoices in history
                if len(job.get("invoice_history", [])) != 3:
                    requirements_met = False
                
                if requirements_met:
                    self.log_result(
                        "Final Job Status - All Requirements Met", 
                        True, 
                        f"All partial invoicing workflow requirements successfully met"
                    )
                else:
                    self.log_result(
                        "Final Job Status - All Requirements Met", 
                        False, 
                        f"Some requirements not met - see individual test results above"
                    )
                
            else:
                self.log_result(
                    "Final Job Status Verification", 
                    False, 
                    f"Failed to get final job status: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Final Job Status Verification", False, f"Error: {str(e)}")
    
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
        
        # Group results by category
        categories = {
            "Authentication": [],
            "Order Setup": [],
            "First Partial Invoice": [],
            "Second Partial Invoice": [],
            "Third Partial Invoice": [],
            "Job Status Verification": [],
            "Invoice Number Verification": [],
            "Final Status": []
        }
        
        for result in self.test_results:
            test_name = result['test']
            if 'Authentication' in test_name:
                categories["Authentication"].append(result)
            elif any(keyword in test_name for keyword in ['Find', 'Create Test Order', 'Move Order']):
                categories["Order Setup"].append(result)
            elif 'First Partial' in test_name or 'Invoice 1' in test_name:
                categories["First Partial Invoice"].append(result)
            elif 'Second Partial' in test_name or 'Invoice 2' in test_name:
                categories["Second Partial Invoice"].append(result)
            elif 'Third Partial' in test_name or 'Invoice 3' in test_name:
                categories["Third Partial Invoice"].append(result)
            elif 'Job Stage' in test_name or 'Job Status' in test_name or 'Invoiced Flag' in test_name:
                categories["Job Status Verification"].append(result)
            elif 'Invoice Number' in test_name or 'Suffix' in test_name:
                categories["Invoice Number Verification"].append(result)
            elif 'Final' in test_name:
                categories["Final Status"].append(result)
        
        print("\n" + "="*60)
        print("RESULTS BY CATEGORY:")
        print("="*60)
        
        for category, results in categories.items():
            if results:
                category_passed = sum(1 for r in results if r['success'])
                category_total = len(results)
                category_rate = (category_passed / category_total * 100) if category_total > 0 else 0
                
                print(f"\n{category}: {category_passed}/{category_total} ({category_rate:.1f}%)")
                for result in results:
                    status = "✅" if result['success'] else "❌"
                    print(f"  {status} {result['test']}")
        
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
            print("🎉 PERFECT! PARTIAL INVOICING WORKFLOW 100% SUCCESSFUL!")
        elif success_rate >= 90:
            print(f"🎯 EXCELLENT! {success_rate:.1f}% SUCCESS RATE")
        elif success_rate >= 80:
            print(f"✅ GOOD! {success_rate:.1f}% SUCCESS RATE")
        else:
            print(f"⚠️  NEEDS IMPROVEMENT: {success_rate:.1f}% SUCCESS RATE")
        print("="*80)

def main():
    """Main test execution"""
    print("="*80)
    print("PART SUPPLY INVOICING WORKFLOW TESTING")
    print("Testing partial invoicing with 50%, 30%, 20% splits")
    print("="*80)
    
    tester = InvoicingWorkflowTester()
    
    # Step 1: Authenticate
    if not tester.authenticate():
        print("❌ Authentication failed - cannot proceed with tests")
        return
    
    # Step 2: Find or create order in delivery stage
    if not tester.find_or_create_delivery_stage_order():
        print("❌ Failed to set up test order - cannot proceed with invoicing tests")
        return
    
    # Step 3: Test partial invoicing workflow
    tester.test_partial_invoicing_workflow()
    
    # Step 4: Print summary
    tester.print_test_summary()

if __name__ == "__main__":
    main()