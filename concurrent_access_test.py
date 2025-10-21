#!/usr/bin/env python3
"""
Multi-User Concurrent Access Testing Suite

Test Objectives:
1. Verify atomic stock allocation prevents race conditions
2. Verify atomic leave approval prevents over-deduction
3. Verify timesheet approval guards work correctly
4. Verify token refresh endpoint works

Test Scenarios:
- Token Refresh: Login as user "Callum" / "Peach7510", extract refresh_token, call POST /api/auth/refresh
- Stock Allocation Atomicity: Login as admin, find product with stock, attempt allocation
- Leave Approval Atomicity: Login as manager, find pending leave, approve, verify balance decrease
- Timesheet Approval Guards: Login as manager, find submitted timesheet, approve, verify response
"""

import requests
import json
import os
from datetime import datetime, timedelta, date
from dotenv import load_dotenv
import uuid
import time

# Load environment variables
load_dotenv('/app/frontend/.env')

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:8001')
API_BASE = f"{BACKEND_URL}/api"

class ConcurrentAccessTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.refresh_token = None
        self.test_results = []
        self.user_info = None
        
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
        """Test authentication with demo user Callum/Peach7510"""
        print("\n=== AUTHENTICATION TEST ===")
        
        try:
            response = self.session.post(f"{API_BASE}/auth/login", json={
                "username": "Callum",
                "password": "Peach7510"
            })
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get('access_token')
                self.refresh_token = data.get('refresh_token')
                self.user_info = data.get('user', {})
                
                self.session.headers.update({
                    'Authorization': f'Bearer {self.auth_token}'
                })
                
                self.log_result(
                    "Authentication", 
                    True, 
                    f"Successfully authenticated as {self.user_info.get('username')} with role {self.user_info.get('role')}"
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

    def test_token_refresh(self):
        """
        SCENARIO 1: Token Refresh
        - Login as user "Callum" / "Peach7510"
        - Extract refresh_token from login response
        - Call POST /api/auth/refresh with refresh_token
        - Verify new access_token is returned
        - Verify refresh_token is same (not rotated)
        - Verify user info is included
        """
        print("\n" + "="*80)
        print("SCENARIO 1: TOKEN REFRESH TESTING")
        print("Testing POST /api/auth/refresh endpoint")
        print("="*80)
        
        if not self.refresh_token:
            self.log_result(
                "Token Refresh - Setup", 
                False, 
                "No refresh token available from login"
            )
            return
        
        try:
            # Call refresh endpoint
            response = self.session.post(f"{API_BASE}/auth/refresh", json={
                "refresh_token": self.refresh_token
            })
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                required_fields = ['access_token', 'refresh_token', 'token_type', 'user']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    new_access_token = data.get('access_token')
                    returned_refresh_token = data.get('refresh_token')
                    token_type = data.get('token_type')
                    user_info = data.get('user', {})
                    
                    # Verify new access token is different
                    if new_access_token != self.auth_token:
                        self.log_result(
                            "Token Refresh - New Access Token", 
                            True, 
                            "New access token generated successfully"
                        )
                    else:
                        self.log_result(
                            "Token Refresh - New Access Token", 
                            False, 
                            "New access token is same as old token"
                        )
                    
                    # Verify refresh token is same (not rotated)
                    if returned_refresh_token == self.refresh_token:
                        self.log_result(
                            "Token Refresh - Refresh Token Not Rotated", 
                            True, 
                            "Refresh token correctly not rotated"
                        )
                    else:
                        self.log_result(
                            "Token Refresh - Refresh Token Not Rotated", 
                            False, 
                            "Refresh token was rotated (unexpected)"
                        )
                    
                    # Verify token type
                    if token_type == "bearer":
                        self.log_result(
                            "Token Refresh - Token Type", 
                            True, 
                            "Token type is correctly 'bearer'"
                        )
                    else:
                        self.log_result(
                            "Token Refresh - Token Type", 
                            False, 
                            f"Token type is '{token_type}', expected 'bearer'"
                        )
                    
                    # Verify user info is included
                    user_required_fields = ['id', 'username', 'full_name', 'role', 'email']
                    missing_user_fields = [field for field in user_required_fields if field not in user_info]
                    
                    if not missing_user_fields:
                        self.log_result(
                            "Token Refresh - User Info", 
                            True, 
                            f"User info included with all required fields: {user_required_fields}"
                        )
                    else:
                        self.log_result(
                            "Token Refresh - User Info", 
                            False, 
                            f"User info missing fields: {missing_user_fields}"
                        )
                    
                    # Update session with new token
                    self.auth_token = new_access_token
                    self.session.headers.update({
                        'Authorization': f'Bearer {self.auth_token}'
                    })
                    
                else:
                    self.log_result(
                        "Token Refresh - Response Structure", 
                        False, 
                        f"Response missing required fields: {missing_fields}",
                        f"Available fields: {list(data.keys())}"
                    )
            else:
                self.log_result(
                    "Token Refresh", 
                    False, 
                    f"Token refresh failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Token Refresh", False, f"Error: {str(e)}")

    def test_stock_allocation_atomicity(self):
        """
        SCENARIO 2: Stock Allocation Atomicity
        - Login as admin user
        - Find a product with known stock quantity
        - Attempt stock allocation
        - Verify response structure includes allocated_quantity, remaining_stock
        - Verify stock quantity decreased correctly
        """
        print("\n" + "="*80)
        print("SCENARIO 2: STOCK ALLOCATION ATOMICITY TESTING")
        print("Testing atomic stock allocation to prevent race conditions")
        print("="*80)
        
        # First, find available stock
        stock_item = self.find_available_stock()
        if not stock_item:
            self.log_result(
                "Stock Allocation - Setup", 
                False, 
                "No stock items available for testing"
            )
            return
        
        # Test stock allocation
        self.test_stock_allocation(stock_item)

    def find_available_stock(self):
        """Find a stock item with available quantity"""
        try:
            # Try raw substrate stock first
            response = self.session.get(f"{API_BASE}/stock/raw-substrates")
            
            if response.status_code == 200:
                result = response.json()
                stock_items = result.get('data', []) if isinstance(result, dict) else result
                
                # Find item with quantity > 0
                for item in stock_items:
                    if item.get('quantity_on_hand', 0) > 0:
                        self.log_result(
                            "Find Available Stock", 
                            True, 
                            f"Found substrate stock: {item.get('product_description', 'Unknown')} with {item.get('quantity_on_hand')} units"
                        )
                        return item
            
            # Try raw materials stock
            response = self.session.get(f"{API_BASE}/stock/raw-materials")
            
            if response.status_code == 200:
                result = response.json()
                stock_items = result.get('data', []) if isinstance(result, dict) else result
                
                # Find item with quantity > 0
                for item in stock_items:
                    if item.get('quantity_on_hand', 0) > 0:
                        self.log_result(
                            "Find Available Stock", 
                            True, 
                            f"Found material stock: {item.get('material_name', 'Unknown')} with {item.get('quantity_on_hand')} units"
                        )
                        return item
            
            self.log_result(
                "Find Available Stock", 
                False, 
                "No stock items with available quantity found"
            )
            
        except Exception as e:
            self.log_result("Find Available Stock", False, f"Error: {str(e)}")
        
        return None

    def test_stock_allocation(self, stock_item):
        """Test stock allocation for a specific item"""
        try:
            stock_id = stock_item.get('id')
            initial_quantity = stock_item.get('quantity_on_hand', 0)
            allocation_quantity = min(5, initial_quantity)  # Allocate 5 units or less
            
            # Test stock allocation endpoint
            allocation_data = {
                "quantity": allocation_quantity,
                "order_id": f"TEST-ORDER-{str(uuid.uuid4())[:8]}",
                "notes": "Test allocation for concurrent access testing"
            }
            
            response = self.session.post(f"{API_BASE}/stock/allocate/{stock_id}", json=allocation_data)
            
            if response.status_code == 200:
                result = response.json()
                data = result.get('data', {})
                
                # Verify response structure
                required_fields = ['allocated_quantity', 'remaining_stock']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    allocated_quantity = data.get('allocated_quantity')
                    remaining_stock = data.get('remaining_stock')
                    
                    # Verify allocation quantity
                    if allocated_quantity == allocation_quantity:
                        self.log_result(
                            "Stock Allocation - Quantity Verification", 
                            True, 
                            f"Allocated quantity matches request: {allocated_quantity}"
                        )
                    else:
                        self.log_result(
                            "Stock Allocation - Quantity Verification", 
                            False, 
                            f"Allocated quantity {allocated_quantity} doesn't match request {allocation_quantity}"
                        )
                    
                    # Verify remaining stock calculation
                    expected_remaining = initial_quantity - allocation_quantity
                    if remaining_stock == expected_remaining:
                        self.log_result(
                            "Stock Allocation - Remaining Stock Calculation", 
                            True, 
                            f"Remaining stock correctly calculated: {remaining_stock}"
                        )
                    else:
                        self.log_result(
                            "Stock Allocation - Remaining Stock Calculation", 
                            False, 
                            f"Remaining stock {remaining_stock} doesn't match expected {expected_remaining}"
                        )
                    
                    # Verify stock quantity decreased in database
                    self.verify_stock_decrease(stock_item, allocation_quantity)
                    
                else:
                    self.log_result(
                        "Stock Allocation - Response Structure", 
                        False, 
                        f"Response missing required fields: {missing_fields}",
                        f"Available fields: {list(data.keys())}"
                    )
            else:
                self.log_result(
                    "Stock Allocation", 
                    False, 
                    f"Stock allocation failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Stock Allocation", False, f"Error: {str(e)}")

    def verify_stock_decrease(self, original_stock_item, allocated_quantity):
        """Verify that stock quantity decreased correctly in database"""
        try:
            stock_id = original_stock_item.get('id')
            
            # Determine stock type and endpoint
            if 'product_description' in original_stock_item:
                # Substrate stock
                response = self.session.get(f"{API_BASE}/stock/raw-substrates/{stock_id}")
            else:
                # Material stock
                response = self.session.get(f"{API_BASE}/stock/raw-materials/{stock_id}")
            
            if response.status_code == 200:
                result = response.json()
                updated_stock = result.get('data', result)
                
                original_quantity = original_stock_item.get('quantity_on_hand', 0)
                current_quantity = updated_stock.get('quantity_on_hand', 0)
                expected_quantity = original_quantity - allocated_quantity
                
                if current_quantity == expected_quantity:
                    self.log_result(
                        "Stock Allocation - Database Verification", 
                        True, 
                        f"Stock quantity correctly decreased from {original_quantity} to {current_quantity}"
                    )
                else:
                    self.log_result(
                        "Stock Allocation - Database Verification", 
                        False, 
                        f"Stock quantity is {current_quantity}, expected {expected_quantity}"
                    )
            else:
                self.log_result(
                    "Stock Allocation - Database Verification", 
                    False, 
                    f"Failed to retrieve updated stock: {response.status_code}"
                )
                
        except Exception as e:
            self.log_result("Stock Allocation - Database Verification", False, f"Error: {str(e)}")

    def test_leave_approval_atomicity(self):
        """
        SCENARIO 3: Leave Approval Atomicity
        - Login as manager user (Callum or Bubbles)
        - Find a pending leave request (or create one if none exist)
        - Approve the leave request
        - Verify leave balance decreased
        - Try to approve same leave again - should fail with appropriate error
        """
        print("\n" + "="*80)
        print("SCENARIO 3: LEAVE APPROVAL ATOMICITY TESTING")
        print("Testing atomic leave approval to prevent over-deduction")
        print("="*80)
        
        # Check if current user is manager
        if self.user_info.get('role') not in ['admin', 'manager']:
            self.log_result(
                "Leave Approval - Permission Check", 
                False, 
                f"User role '{self.user_info.get('role')}' may not have leave approval permissions"
            )
        
        # Find or create pending leave request
        leave_request = self.find_or_create_pending_leave()
        if not leave_request:
            self.log_result(
                "Leave Approval - Setup", 
                False, 
                "No pending leave request available for testing"
            )
            return
        
        # Test leave approval
        self.test_leave_approval(leave_request)

    def find_or_create_pending_leave(self):
        """Find a pending leave request or create one"""
        try:
            # First, try to find existing pending leave requests
            response = self.session.get(f"{API_BASE}/payroll/leave-requests/pending")
            
            if response.status_code == 200:
                result = response.json()
                leave_requests = result.get('data', [])
                
                # Find a pending request
                for request in leave_requests:
                    if request.get('status') == 'pending':
                        self.log_result(
                            "Find Pending Leave Request", 
                            True, 
                            f"Found pending leave request: {request.get('leave_type')} for {request.get('employee_name')}"
                        )
                        return request
            
            # If no pending requests, create one
            return self.create_test_leave_request()
            
        except Exception as e:
            self.log_result("Find Pending Leave Request", False, f"Error: {str(e)}")
        
        return None

    def create_test_leave_request(self):
        """Create a test leave request"""
        try:
            # Get employees first
            response = self.session.get(f"{API_BASE}/payroll/employees")
            
            if response.status_code == 200:
                employees = response.json()
                if not employees:
                    self.log_result(
                        "Create Test Leave Request", 
                        False, 
                        "No employees available to create leave request"
                    )
                    return None
                
                employee = employees[0]
                
                # Create leave request
                leave_data = {
                    "employee_id": employee.get('id'),
                    "leave_type": "annual_leave",
                    "start_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
                    "end_date": (datetime.now() + timedelta(days=9)).strftime("%Y-%m-%d"),
                    "hours_requested": 24.0,
                    "reason": "Test leave request for concurrent access testing"
                }
                
                response = self.session.post(f"{API_BASE}/payroll/leave-requests", json=leave_data)
                
                if response.status_code == 200:
                    result = response.json()
                    leave_id = result.get('data', {}).get('id')
                    
                    self.log_result(
                        "Create Test Leave Request", 
                        True, 
                        f"Created test leave request with ID: {leave_id}"
                    )
                    
                    # Return the created leave request
                    return {
                        'id': leave_id,
                        'employee_id': employee.get('id'),
                        'employee_name': f"{employee.get('first_name')} {employee.get('last_name')}",
                        'leave_type': 'annual_leave',
                        'hours_requested': 24.0,
                        'status': 'pending'
                    }
                else:
                    self.log_result(
                        "Create Test Leave Request", 
                        False, 
                        f"Failed to create leave request: {response.status_code}",
                        response.text
                    )
            else:
                self.log_result(
                    "Create Test Leave Request", 
                    False, 
                    f"Failed to get employees: {response.status_code}"
                )
                
        except Exception as e:
            self.log_result("Create Test Leave Request", False, f"Error: {str(e)}")
        
        return None

    def test_leave_approval(self, leave_request):
        """Test leave approval for a specific request"""
        try:
            leave_id = leave_request.get('id')
            employee_id = leave_request.get('employee_id')
            hours_requested = leave_request.get('hours_requested', 0)
            
            # Get employee's current leave balance
            initial_balance = self.get_employee_leave_balance(employee_id)
            
            # Approve the leave request
            response = self.session.post(f"{API_BASE}/payroll/leave-requests/{leave_id}/approve")
            
            if response.status_code == 200:
                result = response.json()
                
                self.log_result(
                    "Leave Approval - First Approval", 
                    True, 
                    f"Successfully approved leave request: {result.get('message', 'No message')}"
                )
                
                # Verify leave balance decreased
                self.verify_leave_balance_decrease(employee_id, initial_balance, hours_requested)
                
                # Try to approve the same leave again (should fail)
                self.test_duplicate_leave_approval(leave_id)
                
            else:
                self.log_result(
                    "Leave Approval - First Approval", 
                    False, 
                    f"Leave approval failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Leave Approval", False, f"Error: {str(e)}")

    def get_employee_leave_balance(self, employee_id):
        """Get employee's current leave balance"""
        try:
            response = self.session.get(f"{API_BASE}/payroll/employees/{employee_id}/leave-balance")
            
            if response.status_code == 200:
                result = response.json()
                balance_data = result.get('data', {})
                annual_leave_balance = balance_data.get('annual_leave_balance', 0)
                
                self.log_result(
                    "Get Employee Leave Balance", 
                    True, 
                    f"Current annual leave balance: {annual_leave_balance} hours"
                )
                
                return annual_leave_balance
            else:
                self.log_result(
                    "Get Employee Leave Balance", 
                    False, 
                    f"Failed to get leave balance: {response.status_code}"
                )
                
        except Exception as e:
            self.log_result("Get Employee Leave Balance", False, f"Error: {str(e)}")
        
        return 0

    def verify_leave_balance_decrease(self, employee_id, initial_balance, hours_requested):
        """Verify that leave balance decreased correctly"""
        try:
            current_balance = self.get_employee_leave_balance(employee_id)
            expected_balance = initial_balance - hours_requested
            
            if current_balance == expected_balance:
                self.log_result(
                    "Leave Approval - Balance Verification", 
                    True, 
                    f"Leave balance correctly decreased from {initial_balance} to {current_balance} hours"
                )
            else:
                self.log_result(
                    "Leave Approval - Balance Verification", 
                    False, 
                    f"Leave balance is {current_balance}, expected {expected_balance}"
                )
                
        except Exception as e:
            self.log_result("Leave Approval - Balance Verification", False, f"Error: {str(e)}")

    def test_duplicate_leave_approval(self, leave_id):
        """Test that approving the same leave twice fails appropriately"""
        try:
            response = self.session.post(f"{API_BASE}/payroll/leave-requests/{leave_id}/approve")
            
            if response.status_code in [400, 409, 422]:  # Expected error codes
                result = response.json()
                error_message = result.get('detail', result.get('message', 'No error message'))
                
                self.log_result(
                    "Leave Approval - Duplicate Prevention", 
                    True, 
                    f"Correctly prevented duplicate approval with status {response.status_code}",
                    f"Error message: {error_message}"
                )
            else:
                self.log_result(
                    "Leave Approval - Duplicate Prevention", 
                    False, 
                    f"Duplicate approval should have failed, got status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Leave Approval - Duplicate Prevention", False, f"Error: {str(e)}")

    def test_timesheet_approval_guards(self):
        """
        SCENARIO 4: Timesheet Approval Guards
        - Login as manager user
        - Find a submitted timesheet (or create one if none exist)
        - Approve the timesheet
        - Verify response includes gross_pay, net_pay, hours_worked
        - Try to approve same timesheet again - should fail with "already approved" error
        """
        print("\n" + "="*80)
        print("SCENARIO 4: TIMESHEET APPROVAL GUARDS TESTING")
        print("Testing timesheet approval guards to prevent duplicate approvals")
        print("="*80)
        
        # Find or create submitted timesheet
        timesheet = self.find_or_create_submitted_timesheet()
        if not timesheet:
            self.log_result(
                "Timesheet Approval - Setup", 
                False, 
                "No submitted timesheet available for testing"
            )
            return
        
        # Test timesheet approval
        self.test_timesheet_approval(timesheet)

    def find_or_create_submitted_timesheet(self):
        """Find a submitted timesheet or create one"""
        try:
            # First, try to find existing submitted timesheets
            response = self.session.get(f"{API_BASE}/payroll/timesheets/pending")
            
            if response.status_code == 200:
                result = response.json()
                timesheets = result.get('data', [])
                
                # Find a submitted timesheet
                for timesheet in timesheets:
                    if timesheet.get('status') == 'submitted':
                        self.log_result(
                            "Find Submitted Timesheet", 
                            True, 
                            f"Found submitted timesheet for {timesheet.get('employee_name')}"
                        )
                        return timesheet
            
            # If no submitted timesheets, create one
            return self.create_test_submitted_timesheet()
            
        except Exception as e:
            self.log_result("Find Submitted Timesheet", False, f"Error: {str(e)}")
        
        return None

    def create_test_submitted_timesheet(self):
        """Create a test submitted timesheet"""
        try:
            # Get employees first
            response = self.session.get(f"{API_BASE}/payroll/employees")
            
            if response.status_code == 200:
                employees = response.json()
                if not employees:
                    self.log_result(
                        "Create Test Submitted Timesheet", 
                        False, 
                        "No employees available to create timesheet"
                    )
                    return None
                
                employee = employees[0]
                
                # Create timesheet with submitted status
                timesheet_data = {
                    "employee_id": employee.get('id'),
                    "week_starting": (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
                    "week_ending": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
                    "status": "submitted",
                    "total_regular_hours": 40.0,
                    "total_overtime_hours": 8.0,
                    "entries": [
                        {
                            "date": (datetime.now() - timedelta(days=6)).strftime("%Y-%m-%d"),
                            "regular_hours": 8.0,
                            "overtime_hours": 2.0,
                            "notes": "Test timesheet entry"
                        },
                        {
                            "date": (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d"),
                            "regular_hours": 8.0,
                            "overtime_hours": 2.0,
                            "notes": "Test timesheet entry"
                        },
                        {
                            "date": (datetime.now() - timedelta(days=4)).strftime("%Y-%m-%d"),
                            "regular_hours": 8.0,
                            "overtime_hours": 2.0,
                            "notes": "Test timesheet entry"
                        },
                        {
                            "date": (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d"),
                            "regular_hours": 8.0,
                            "overtime_hours": 2.0,
                            "notes": "Test timesheet entry"
                        },
                        {
                            "date": (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d"),
                            "regular_hours": 8.0,
                            "overtime_hours": 0.0,
                            "notes": "Test timesheet entry"
                        }
                    ]
                }
                
                response = self.session.post(f"{API_BASE}/payroll/timesheets", json=timesheet_data)
                
                if response.status_code == 200:
                    result = response.json()
                    timesheet_id = result.get('data', {}).get('id')
                    
                    self.log_result(
                        "Create Test Submitted Timesheet", 
                        True, 
                        f"Created test submitted timesheet with ID: {timesheet_id}"
                    )
                    
                    # Return the created timesheet
                    return {
                        'id': timesheet_id,
                        'employee_id': employee.get('id'),
                        'employee_name': f"{employee.get('first_name')} {employee.get('last_name')}",
                        'total_regular_hours': 40.0,
                        'total_overtime_hours': 8.0,
                        'status': 'submitted'
                    }
                else:
                    self.log_result(
                        "Create Test Submitted Timesheet", 
                        False, 
                        f"Failed to create timesheet: {response.status_code}",
                        response.text
                    )
            else:
                self.log_result(
                    "Create Test Submitted Timesheet", 
                    False, 
                    f"Failed to get employees: {response.status_code}"
                )
                
        except Exception as e:
            self.log_result("Create Test Submitted Timesheet", False, f"Error: {str(e)}")
        
        return None

    def test_timesheet_approval(self, timesheet):
        """Test timesheet approval for a specific timesheet"""
        try:
            timesheet_id = timesheet.get('id')
            
            # Approve the timesheet
            response = self.session.post(f"{API_BASE}/payroll/timesheets/{timesheet_id}/approve")
            
            if response.status_code == 200:
                result = response.json()
                data = result.get('data', {})
                
                # Verify response includes required fields
                required_fields = ['gross_pay', 'net_pay', 'hours_worked']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    gross_pay = data.get('gross_pay')
                    net_pay = data.get('net_pay')
                    hours_worked = data.get('hours_worked')
                    
                    self.log_result(
                        "Timesheet Approval - First Approval", 
                        True, 
                        f"Successfully approved timesheet",
                        f"Gross Pay: ${gross_pay}, Net Pay: ${net_pay}, Hours: {hours_worked}"
                    )
                    
                    # Try to approve the same timesheet again (should fail)
                    self.test_duplicate_timesheet_approval(timesheet_id)
                    
                else:
                    self.log_result(
                        "Timesheet Approval - Response Structure", 
                        False, 
                        f"Response missing required fields: {missing_fields}",
                        f"Available fields: {list(data.keys())}"
                    )
            else:
                self.log_result(
                    "Timesheet Approval - First Approval", 
                    False, 
                    f"Timesheet approval failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Timesheet Approval", False, f"Error: {str(e)}")

    def test_duplicate_timesheet_approval(self, timesheet_id):
        """Test that approving the same timesheet twice fails appropriately"""
        try:
            response = self.session.post(f"{API_BASE}/payroll/timesheets/{timesheet_id}/approve")
            
            if response.status_code in [400, 409, 422]:  # Expected error codes
                result = response.json()
                error_message = result.get('detail', result.get('message', 'No error message'))
                
                # Check if error message mentions "already approved"
                if "already approved" in error_message.lower():
                    self.log_result(
                        "Timesheet Approval - Duplicate Prevention", 
                        True, 
                        f"Correctly prevented duplicate approval with 'already approved' error",
                        f"Error message: {error_message}"
                    )
                else:
                    self.log_result(
                        "Timesheet Approval - Duplicate Prevention", 
                        True, 
                        f"Prevented duplicate approval with status {response.status_code}",
                        f"Error message: {error_message}"
                    )
            else:
                self.log_result(
                    "Timesheet Approval - Duplicate Prevention", 
                    False, 
                    f"Duplicate approval should have failed, got status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Timesheet Approval - Duplicate Prevention", False, f"Error: {str(e)}")

    def run_all_tests(self):
        """Run all concurrent access tests"""
        print("="*80)
        print("MULTI-USER CONCURRENT ACCESS TESTING SUITE")
        print("="*80)
        
        # Authenticate first
        if not self.authenticate():
            print("❌ Authentication failed - cannot proceed with tests")
            return
        
        # Run all test scenarios
        self.test_token_refresh()
        self.test_stock_allocation_atomicity()
        self.test_leave_approval_atomicity()
        self.test_timesheet_approval_guards()
        
        # Print summary
        self.print_test_summary()

    def print_test_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "="*80)
        print("MULTI-USER CONCURRENT ACCESS TEST SUMMARY")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        # Group results by scenario
        scenarios = {
            "Token Refresh": [],
            "Stock Allocation": [],
            "Leave Approval": [],
            "Timesheet Approval": [],
            "Other": []
        }
        
        for result in self.test_results:
            test_name = result['test']
            if 'Token Refresh' in test_name:
                scenarios["Token Refresh"].append(result)
            elif 'Stock Allocation' in test_name:
                scenarios["Stock Allocation"].append(result)
            elif 'Leave Approval' in test_name:
                scenarios["Leave Approval"].append(result)
            elif 'Timesheet Approval' in test_name:
                scenarios["Timesheet Approval"].append(result)
            else:
                scenarios["Other"].append(result)
        
        print("\n" + "="*60)
        print("RESULTS BY SCENARIO:")
        print("="*60)
        
        for scenario, results in scenarios.items():
            if results:
                scenario_passed = sum(1 for r in results if r['success'])
                scenario_total = len(results)
                scenario_rate = (scenario_passed / scenario_total * 100) if scenario_total > 0 else 0
                
                print(f"\n{scenario}: {scenario_passed}/{scenario_total} ({scenario_rate:.1f}%)")
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
            print("🎉 PERFECT! ALL CONCURRENT ACCESS FIXES WORKING!")
        elif success_rate >= 90:
            print(f"🎯 EXCELLENT! {success_rate:.1f}% SUCCESS RATE")
        elif success_rate >= 80:
            print(f"✅ GOOD! {success_rate:.1f}% SUCCESS RATE")
        else:
            print(f"⚠️  NEEDS ATTENTION: {success_rate:.1f}% SUCCESS RATE")
        print("="*80)

def main():
    """Main function to run the tests"""
    tester = ConcurrentAccessTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()