from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from decimal import Decimal
import calendar
from payroll_models import *
from models import User
import logging

class PayrollCalculationService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Australian tax brackets for 2024-25 (simplified)
        self.tax_brackets = [
            (18200, 0.0),      # Tax-free threshold
            (45000, 0.19),     # 19% tax rate
            (120000, 0.325),   # 32.5% tax rate
            (180000, 0.37),    # 37% tax rate
            (float('inf'), 0.45) # 45% tax rate
        ]
    
    def calculate_weekly_pay(self, employee: EmployeeProfile, timesheet: Timesheet) -> PayrollCalculation:
        """Calculate weekly pay from timesheet"""
        
        # Calculate total hours
        regular_hours = timesheet.total_regular_hours
        overtime_hours = timesheet.total_overtime_hours
        total_hours = regular_hours + overtime_hours
        
        # Calculate pay
        regular_pay = regular_hours * employee.hourly_rate
        overtime_pay = overtime_hours * employee.hourly_rate * Decimal('1.5')  # 1.5x overtime
        gross_pay = regular_pay + overtime_pay
        
        # Calculate annual equivalent for tax purposes
        annual_gross = gross_pay * 52
        
        # Calculate tax withholding
        weekly_tax = self.calculate_weekly_tax(annual_gross)
        
        # Calculate superannuation (11% of gross pay)
        superannuation = gross_pay * Decimal('0.11')
        
        # Calculate net pay
        net_pay = gross_pay - weekly_tax
        
        # Calculate leave accruals
        leave_accruals = self.calculate_leave_accruals(employee, regular_hours)
        
        return PayrollCalculation(
            employee_id=employee.id,
            timesheet_id=timesheet.id,
            pay_period_start=timesheet.week_starting,
            pay_period_end=timesheet.week_ending,
            regular_hours=regular_hours,
            overtime_hours=overtime_hours,
            total_hours=total_hours,
            regular_pay=regular_pay,
            overtime_pay=overtime_pay,
            gross_pay=gross_pay,
            tax_withheld=weekly_tax,
            superannuation=superannuation,
            net_pay=net_pay,
            annual_leave_accrued=leave_accruals['annual_leave'],
            sick_leave_accrued=leave_accruals['sick_leave'],
            personal_leave_accrued=leave_accruals['personal_leave'],
            leave_taken=timesheet.total_leave_hours,
            calculated_by="system"
        )
    
    def calculate_weekly_tax(self, annual_gross: Decimal) -> Decimal:
        """Calculate weekly tax withholding based on annual gross"""
        annual_tax = Decimal('0')
        remaining_income = annual_gross
        
        for i, (threshold, rate) in enumerate(self.tax_brackets):
            if remaining_income <= 0:
                break
                
            if i == 0:
                # Tax-free threshold
                taxable_in_bracket = min(remaining_income, Decimal(str(threshold)))
            else:
                prev_threshold = Decimal(str(self.tax_brackets[i-1][0]))
                if remaining_income > threshold - prev_threshold:
                    taxable_in_bracket = threshold - prev_threshold
                else:
                    taxable_in_bracket = remaining_income
            
            annual_tax += taxable_in_bracket * Decimal(str(rate))
            remaining_income -= taxable_in_bracket
        
        # Convert to weekly
        return annual_tax / 52
    
    def calculate_leave_accruals(self, employee: EmployeeProfile, hours_worked: Decimal) -> Dict[str, Decimal]:
        """Calculate leave accruals based on hours worked"""
        # Full-time equivalent is 38 hours per week
        full_time_hours = Decimal('38')
        work_fraction = hours_worked / full_time_hours
        
        # Annual entitlements divided by 52 weeks
        weekly_annual_leave = Decimal(str(employee.annual_leave_entitlement)) / 52
        weekly_sick_leave = Decimal(str(employee.sick_leave_entitlement)) / 52
        weekly_personal_leave = Decimal(str(employee.personal_leave_entitlement)) / 52
        
        return {
            'annual_leave': weekly_annual_leave * work_fraction,
            'sick_leave': weekly_sick_leave * work_fraction,
            'personal_leave': weekly_personal_leave * work_fraction
        }
    
    def update_leave_balances(self, employee_id: str, calculation: PayrollCalculation) -> Dict[str, Decimal]:
        """Update employee leave balances based on payroll calculation"""
        # This would update the database with new leave balances
        # Implementation would add accrued leave and subtract taken leave
        pass

class TimesheetService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def generate_weekly_timesheet(self, employee_id: str, week_starting: date) -> Timesheet:
        """Generate blank timesheet for the week"""
        
        # Calculate week ending (Sunday)
        week_ending = week_starting + timedelta(days=6)
        
        # Create entries for each day of the week
        entries = []
        for i in range(7):
            entry_date = week_starting + timedelta(days=i)
            entries.append(TimesheetEntry(
                date=entry_date,
                regular_hours=Decimal('0'),
                overtime_hours=Decimal('0'),
                leave_hours={},
                notes=None
            ))
        
        return Timesheet(
            employee_id=employee_id,
            week_starting=week_starting,
            week_ending=week_ending,
            entries=entries,
            status=TimesheetStatus.DRAFT
        )
    
    def calculate_timesheet_totals(self, timesheet: Timesheet) -> Timesheet:
        """Calculate totals for timesheet"""
        total_regular = Decimal('0')
        total_overtime = Decimal('0')
        total_leave = {}
        
        for entry in timesheet.entries:
            total_regular += entry.regular_hours
            total_overtime += entry.overtime_hours
            
            # Sum leave hours by type
            for leave_type, hours in entry.leave_hours.items():
                if leave_type not in total_leave:
                    total_leave[leave_type] = Decimal('0')
                total_leave[leave_type] += hours
        
        timesheet.total_regular_hours = total_regular
        timesheet.total_overtime_hours = total_overtime
        timesheet.total_leave_hours = total_leave
        
        return timesheet
    
    def get_current_week_starting(self) -> date:
        """Get Monday of current week"""
        today = date.today()
        days_since_monday = today.weekday()
        monday = today - timedelta(days=days_since_monday)
        return monday
    
    def should_show_timesheet_reminder(self) -> bool:
        """Check if today is Thursday (timesheet reminder day)"""
        return date.today().weekday() == 3  # Thursday is 3 (Monday is 0)

class LeaveManagementService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def calculate_leave_hours(self, start_date: date, end_date: date, daily_hours: Decimal = Decimal('7.6')) -> Decimal:
        """Calculate total leave hours between dates (excluding weekends)"""
        total_hours = Decimal('0')
        current_date = start_date
        
        while current_date <= end_date:
            # Skip weekends (Saturday = 5, Sunday = 6)
            if current_date.weekday() < 5:
                total_hours += daily_hours
            current_date += timedelta(days=1)
        
        return total_hours
    
    def check_leave_balance(self, employee: EmployeeProfile, leave_type: LeaveType, hours_requested: Decimal) -> bool:
        """Check if employee has sufficient leave balance"""
        balance_field_map = {
            LeaveType.ANNUAL_LEAVE: employee.annual_leave_balance,
            LeaveType.SICK_LEAVE: employee.sick_leave_balance,
            LeaveType.PERSONAL_LEAVE: employee.personal_leave_balance
        }
        
        # Some leave types don't require balance check
        if leave_type in [LeaveType.MATERNITY_LEAVE, LeaveType.PATERNITY_LEAVE, LeaveType.UNPAID_LEAVE]:
            return True
        
        current_balance = balance_field_map.get(leave_type, Decimal('0'))
        return current_balance >= hours_requested
    
    def get_team_leave_calendar(self, team_employee_ids: List[str], start_date: date, end_date: date) -> List[TeamLeaveCalendar]:
        """Generate team leave calendar for date range"""
        calendar_days = []
        current_date = start_date
        
        while current_date <= end_date:
            # This would query database for approved leave on this date
            employees_on_leave = []  # Would be populated from database
            
            calendar_days.append(TeamLeaveCalendar(
                date=current_date,
                employees_on_leave=employees_on_leave,
                total_employees=len(team_employee_ids),
                employees_available=len(team_employee_ids) - len(employees_on_leave),
                coverage_percentage=(len(team_employee_ids) - len(employees_on_leave)) / len(team_employee_ids) * 100
            ))
            
            current_date += timedelta(days=1)
        
        return calendar_days

class PayrollReportingService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def generate_payroll_summary(self, employee_ids: List[str], start_date: date, end_date: date) -> List[PayrollSummary]:
        """Generate payroll summary for multiple employees"""
        summaries = []
        
        # This would query database for payroll calculations in date range
        # and generate summary for each employee
        
        return summaries
    
    def generate_leave_balance_report(self, employee_ids: List[str]) -> List[EmployeeLeaveBalance]:
        """Generate current leave balance report"""
        balances = []
        
        # This would query database for current employee leave balances
        
        return balances
    
    def calculate_monthly_payroll_costs(self, month: int, year: int) -> Dict[str, Any]:
        """Calculate total payroll costs for a month"""
        # This would aggregate payroll calculations for the month
        return {
            'total_gross_pay': Decimal('0'),
            'total_net_pay': Decimal('0'),
            'total_tax_withheld': Decimal('0'),
            'total_superannuation': Decimal('0'),
            'total_hours_worked': Decimal('0'),
            'employee_count': 0
        }