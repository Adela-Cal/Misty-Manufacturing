#!/usr/bin/env python3
"""
Fix Timesheet Employee ID Data Integrity Issue
Update timesheets to use correct employee_id instead of user_id
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

class TimesheetEmployeeIdFixer:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        
    def authenticate(self):
        """Authenticate with admin credentials"""
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
                print("✅ Authentication successful")
                return True
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication error: {str(e)}")
            return False

    def get_employee_mapping(self):
        """Get mapping of user_id to employee_id"""
        try:
            response = self.session.get(f"{API_BASE}/payroll/employees")
            
            if response.status_code == 200:
                result = response.json()
                
                # Handle both direct array and StandardResponse format
                if isinstance(result, list):
                    employees = result
                elif isinstance(result, dict) and "data" in result:
                    employees = result["data"]
                else:
                    employees = result
                
                # Create mapping: user_id -> employee_id
                mapping = {}
                for employee in employees:
                    user_id = employee.get('user_id')
                    employee_id = employee.get('id')
                    if user_id and employee_id:
                        mapping[user_id] = {
                            'employee_id': employee_id,
                            'name': f"{employee.get('first_name', '')} {employee.get('last_name', '')}".strip(),
                            'employee_number': employee.get('employee_number')
                        }
                
                print(f"✅ Retrieved mapping for {len(mapping)} employees")
                return mapping
            else:
                print(f"❌ Failed to get employees: {response.status_code}")
                return {}
                
        except Exception as e:
            print(f"❌ Error getting employees: {str(e)}")
            return {}

    def get_pending_timesheets(self):
        """Get all pending timesheets"""
        try:
            response = self.session.get(f"{API_BASE}/payroll/timesheets/pending")
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("success") and "data" in result:
                    timesheets = result["data"]
                    print(f"✅ Retrieved {len(timesheets)} pending timesheets")
                    return timesheets
                else:
                    print("❌ Invalid response structure")
                    return []
            else:
                print(f"❌ Failed to get pending timesheets: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Error getting pending timesheets: {str(e)}")
            return []

    def fix_timesheet_employee_ids(self):
        """Fix the employee_id issue in timesheets"""
        print("🔧 Starting timesheet employee_id fix...")
        
        # Get employee mapping
        employee_mapping = self.get_employee_mapping()
        if not employee_mapping:
            print("❌ Cannot proceed without employee mapping")
            return
        
        # Get pending timesheets
        timesheets = self.get_pending_timesheets()
        if not timesheets:
            print("❌ No pending timesheets to fix")
            return
        
        print(f"\n📋 Analyzing {len(timesheets)} timesheets...")
        
        fixes_needed = []
        for timesheet in timesheets:
            timesheet_id = timesheet.get('id')
            current_employee_id = timesheet.get('employee_id')
            
            # Check if current employee_id is actually a user_id
            if current_employee_id in employee_mapping:
                correct_employee_id = employee_mapping[current_employee_id]['employee_id']
                employee_name = employee_mapping[current_employee_id]['name']
                
                fixes_needed.append({
                    'timesheet_id': timesheet_id,
                    'current_employee_id': current_employee_id,
                    'correct_employee_id': correct_employee_id,
                    'employee_name': employee_name
                })
                
                print(f"   🔍 Timesheet {timesheet_id}")
                print(f"      Current (USER_ID): {current_employee_id}")
                print(f"      Correct (EMPLOYEE_ID): {correct_employee_id}")
                print(f"      Employee: {employee_name}")
        
        if not fixes_needed:
            print("✅ No fixes needed - all timesheets have correct employee_ids")
            return
        
        print(f"\n🔧 Found {len(fixes_needed)} timesheets that need fixing")
        
        # Apply fixes using direct MongoDB update (since we don't have a PUT endpoint)
        print("\n⚠️  NOTE: This would require direct database access to fix.")
        print("The following MongoDB updates are needed:")
        
        for fix in fixes_needed:
            print(f"\ndb.timesheets.updateOne(")
            print(f"  {{\"id\": \"{fix['timesheet_id']}\"}},")
            print(f"  {{\"$set\": {{\"employee_id\": \"{fix['correct_employee_id']}\"}}}}")
            print(f")")
        
        # For now, let's try to test the approval after showing the issue
        print(f"\n🧪 Testing approval with current (incorrect) data...")
        if fixes_needed:
            test_timesheet = fixes_needed[0]
            self.test_approval_before_fix(test_timesheet['timesheet_id'])

    def test_approval_before_fix(self, timesheet_id):
        """Test timesheet approval before fix to confirm the error"""
        try:
            print(f"🧪 Testing approval of timesheet {timesheet_id}...")
            response = self.session.post(f"{API_BASE}/payroll/timesheets/{timesheet_id}/approve")
            
            if response.status_code == 200:
                print("✅ Approval successful (unexpected)")
            else:
                error_text = response.text
                print(f"❌ Approval failed as expected: {response.status_code}")
                try:
                    error_data = response.json()
                    if "detail" in error_data:
                        print(f"   Error: {error_data['detail']}")
                except:
                    pass
                
        except Exception as e:
            print(f"❌ Error testing approval: {str(e)}")

    def run_fix(self):
        """Run the complete fix process"""
        print("🔧 TIMESHEET EMPLOYEE_ID FIX UTILITY")
        print("Fixing 'Employee not found' error in timesheet approval")
        
        # Authenticate first
        if not self.authenticate():
            print("❌ Authentication failed - cannot proceed")
            return
        
        # Run the fix process
        self.fix_timesheet_employee_ids()

if __name__ == "__main__":
    fixer = TimesheetEmployeeIdFixer()
    fixer.run_fix()