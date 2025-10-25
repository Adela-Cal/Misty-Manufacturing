"""
Australian Taxation Office (ATO) Payroll Calculator
Implements 2025-26 tax year rules including:
- Schedule 1: Regular PAYG withholding
- Schedule 8: HELP/HECS withholding (effective 24 September 2025)
- Medicare Levy: 2% of taxable income
- Superannuation Guarantee: 12% from 1 July 2025
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class ATOPayrollCalculator:
    """
    Calculate Australian payroll with ATO 2025-26 rules
    """
    
    # Superannuation Guarantee rate from 1 July 2025
    SG_RATE = Decimal('0.12')  # 12%
    
    # Maximum contribution base (per quarter)
    SG_QUARTERLY_CAP = Decimal('62500')
    SG_WEEKLY_CAP = Decimal('4807.69')
    SG_FORTNIGHTLY_CAP = Decimal('9615.38')
    SG_MONTHLY_CAP = Decimal('20833.33')
    
    # Medicare Levy
    MEDICARE_LEVY_RATE = Decimal('0.02')  # 2%
    MEDICARE_LOW_INCOME_THRESHOLD_SINGLE = Decimal('27222')
    MEDICARE_LOW_INCOME_THRESHOLD_FAMILY = Decimal('45907')
    MEDICARE_DEPENDENT_CHILD_AMOUNT = Decimal('4216')
    
    # 2025-26 Resident income tax rates (annual)
    TAX_BRACKETS_ANNUAL = [
        (Decimal('18200'), Decimal('0')),          # $0 - $18,200 → 0%
        (Decimal('45000'), Decimal('0.16')),       # $18,201 - $45,000 → 16%
        (Decimal('135000'), Decimal('0.30')),      # $45,001 - $135,000 → 30%
        (Decimal('190000'), Decimal('0.37')),      # $135,001 - $190,000 → 37%
        (Decimal('999999999'), Decimal('0.45'))    # $190,001+ → 45%
    ]
    
    # Schedule 1 - Weekly tax table with tax-free threshold (2025-26)
    # Format: (weekly_earnings_up_to, tax_a, tax_b)
    # Tax = (earnings × tax_a) - tax_b
    SCHEDULE_1_WEEKLY_WITH_TFN_THRESHOLD = [
        (Decimal('371'), Decimal('0'), Decimal('0')),
        (Decimal('515'), Decimal('0.16'), Decimal('59.36')),
        (Decimal('932'), Decimal('0.219'), Decimal('89.74')),
        (Decimal('1957'), Decimal('0.3477'), Decimal('209.58')),
        (Decimal('3111'), Decimal('0.39'), Decimal('292.48')),
        (Decimal('999999'), Decimal('0.47'), Decimal('541.36'))
    ]
    
    # Schedule 1 - Weekly tax table WITHOUT tax-free threshold (2025-26)
    SCHEDULE_1_WEEKLY_NO_TFN_THRESHOLD = [
        (Decimal('88'), Decimal('0.19'), Decimal('0')),
        (Decimal('371'), Decimal('0.29'), Decimal('8.80')),
        (Decimal('515'), Decimal('0.219'), Decimal('17.15')),
        (Decimal('932'), Decimal('0.3477'), Decimal('83.54')),
        (Decimal('1957'), Decimal('0.39'), Decimal('123.14')),
        (Decimal('3111'), Decimal('0.47'), Decimal('279.74')),
        (Decimal('999999'), Decimal('0.47'), Decimal('279.74'))
    ]
    
    # Schedule 8 - HELP/HECS withholding rates (effective 24 September 2025)
    # Format: (annual_threshold, weekly_threshold, rate)
    SCHEDULE_8_HELP_WEEKLY = [
        (Decimal('54435'), Decimal('1047'), Decimal('0')),
        (Decimal('62851'), Decimal('1209'), Decimal('0.01')),
        (Decimal('66621'), Decimal('1281'), Decimal('0.02')),
        (Decimal('70619'), Decimal('1358'), Decimal('0.025')),
        (Decimal('74855'), Decimal('1440'), Decimal('0.03')),
        (Decimal('79346'), Decimal('1526'), Decimal('0.035')),
        (Decimal('84108'), Decimal('1617'), Decimal('0.04')),
        (Decimal('89154'), Decimal('1715'), Decimal('0.045')),
        (Decimal('94503'), Decimal('1817'), Decimal('0.05')),
        (Decimal('100174'), Decimal('1926'), Decimal('0.055')),
        (Decimal('106185'), Decimal('2042'), Decimal('0.06')),
        (Decimal('112556'), Decimal('2165'), Decimal('0.065')),
        (Decimal('119310'), Decimal('2294'), Decimal('0.07')),
        (Decimal('126468'), Decimal('2432'), Decimal('0.075')),
        (Decimal('134056'), Decimal('2578'), Decimal('0.08')),
        (Decimal('142099'), Decimal('2733'), Decimal('0.085')),
        (Decimal('150626'), Decimal('2897'), Decimal('0.09')),
        (Decimal('159663'), Decimal('3070'), Decimal('0.095')),
        (Decimal('999999999'), Decimal('999999'), Decimal('0.10'))
    ]
    
    def __init__(self):
        pass
    
    def round_currency(self, value: Decimal) -> Decimal:
        """Round to 2 decimal places for currency"""
        return value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def calculate_superannuation(self, ote: Decimal, pay_period: str = 'weekly') -> Decimal:
        """
        Calculate Superannuation Guarantee (12% from 1 July 2025)
        SG is paid by employer, not deducted from employee pay
        
        Args:
            ote: Ordinary Time Earnings (base pay + allowances, excludes overtime)
            pay_period: 'weekly', 'fortnightly', or 'monthly'
        
        Returns:
            Superannuation amount
        """
        # Apply period cap
        if pay_period == 'weekly':
            cap = self.SG_WEEKLY_CAP
        elif pay_period == 'fortnightly':
            cap = self.SG_FORTNIGHTLY_CAP
        elif pay_period == 'monthly':
            cap = self.SG_MONTHLY_CAP
        else:
            cap = self.SG_WEEKLY_CAP
        
        capped_ote = min(ote, cap)
        sg = capped_ote * self.SG_RATE
        
        return self.round_currency(sg)
    
    def calculate_payg_tax(
        self,
        taxable_income: Decimal,
        pay_period: str = 'weekly',
        claims_tax_free_threshold: bool = True,
        is_resident: bool = True,
        tfn_provided: bool = True
    ) -> Decimal:
        """
        Calculate PAYG tax withholding using Schedule 1 (2025-26)
        
        Args:
            taxable_income: Taxable income for the period
            pay_period: 'weekly', 'fortnightly', or 'monthly'
            claims_tax_free_threshold: Whether employee claims tax-free threshold
            is_resident: Whether employee is Australian resident for tax
            tfn_provided: Whether TFN is provided
        
        Returns:
            Tax amount to withhold
        """
        if not tfn_provided:
            # No TFN: withhold at highest rate (47%)
            return self.round_currency(taxable_income * Decimal('0.47'))
        
        if not is_resident:
            # Non-resident: flat 32.5% on all income (no tax-free threshold)
            return self.round_currency(taxable_income * Decimal('0.325'))
        
        # Use appropriate tax table
        if pay_period == 'weekly':
            if claims_tax_free_threshold:
                tax_table = self.SCHEDULE_1_WEEKLY_WITH_TFN_THRESHOLD
            else:
                tax_table = self.SCHEDULE_1_WEEKLY_NO_TFN_THRESHOLD
        else:
            # For now, convert to weekly equivalent
            # TODO: Add fortnightly and monthly tables
            if pay_period == 'fortnightly':
                taxable_income = taxable_income / Decimal('2')
            elif pay_period == 'monthly':
                taxable_income = taxable_income * Decimal('12') / Decimal('52')
            
            if claims_tax_free_threshold:
                tax_table = self.SCHEDULE_1_WEEKLY_WITH_TFN_THRESHOLD
            else:
                tax_table = self.SCHEDULE_1_WEEKLY_NO_TFN_THRESHOLD
        
        # Find applicable bracket
        tax = Decimal('0')
        for threshold, tax_a, tax_b in tax_table:
            if taxable_income <= threshold:
                tax = (taxable_income * tax_a) - tax_b
                break
        
        # Convert back if needed
        if pay_period == 'fortnightly':
            tax = tax * Decimal('2')
        elif pay_period == 'monthly':
            tax = tax * Decimal('52') / Decimal('12')
        
        return self.round_currency(max(tax, Decimal('0')))
    
    def calculate_medicare_levy(
        self,
        taxable_income: Decimal,
        pay_period: str = 'weekly',
        is_single: bool = True,
        num_dependents: int = 0
    ) -> Decimal:
        """
        Calculate Medicare Levy (2% of taxable income)
        
        Args:
            taxable_income: Taxable income for the period
            pay_period: 'weekly', 'fortnightly', or 'monthly'
            is_single: Whether employee is single or has family
            num_dependents: Number of dependent children
        
        Returns:
            Medicare levy amount
        """
        # Convert to annual for threshold comparison
        if pay_period == 'weekly':
            annual_income = taxable_income * Decimal('52')
        elif pay_period == 'fortnightly':
            annual_income = taxable_income * Decimal('26')
        elif pay_period == 'monthly':
            annual_income = taxable_income * Decimal('12')
        else:
            annual_income = taxable_income * Decimal('52')
        
        # Determine threshold
        if is_single:
            threshold = self.MEDICARE_LOW_INCOME_THRESHOLD_SINGLE
        else:
            threshold = self.MEDICARE_LOW_INCOME_THRESHOLD_FAMILY
            threshold += (self.MEDICARE_DEPENDENT_CHILD_AMOUNT * Decimal(str(num_dependents)))
        
        # Below threshold: no levy
        if annual_income <= threshold:
            return Decimal('0')
        
        # Calculate 2% levy
        levy = taxable_income * self.MEDICARE_LEVY_RATE
        
        return self.round_currency(levy)
    
    def calculate_help_withholding(
        self,
        taxable_income: Decimal,
        pay_period: str = 'weekly'
    ) -> Decimal:
        """
        Calculate HELP/HECS withholding using Schedule 8 (effective 24 Sept 2025)
        
        Args:
            taxable_income: Taxable income for the period
            pay_period: 'weekly', 'fortnightly', or 'monthly'
        
        Returns:
            HELP withholding amount
        """
        # Convert to weekly for table lookup
        if pay_period == 'fortnightly':
            weekly_income = taxable_income / Decimal('2')
        elif pay_period == 'monthly':
            weekly_income = taxable_income * Decimal('12') / Decimal('52')
        else:
            weekly_income = taxable_income
        
        # Find applicable rate
        rate = Decimal('0')
        for annual_threshold, weekly_threshold, help_rate in self.SCHEDULE_8_HELP_WEEKLY:
            if weekly_income <= weekly_threshold:
                rate = help_rate
                break
        
        # Calculate withholding
        help_amount = weekly_income * rate
        
        # Convert back if needed
        if pay_period == 'fortnightly':
            help_amount = help_amount * Decimal('2')
        elif pay_period == 'monthly':
            help_amount = help_amount * Decimal('52') / Decimal('12')
        
        return self.round_currency(help_amount)
    
    def calculate_payroll(
        self,
        base_pay: Decimal,
        allowances: Decimal = Decimal('0'),
        overtime: Decimal = Decimal('0'),
        bonuses: Decimal = Decimal('0'),
        salary_sacrifice_super: Decimal = Decimal('0'),
        other_pre_tax_deductions: Decimal = Decimal('0'),
        post_tax_deductions: Decimal = Decimal('0'),
        pay_period: str = 'weekly',
        claims_tax_free_threshold: bool = True,
        is_resident: bool = True,
        has_help_debt: bool = False,
        tfn_provided: bool = True,
        has_private_health: bool = False,
        is_single: bool = True,
        num_dependents: int = 0
    ) -> Dict[str, any]:
        """
        Complete payroll calculation with ATO 2025-26 rules
        
        Returns dictionary with all payroll components
        """
        # Step 1: Calculate OTE and Gross
        ote = base_pay + allowances
        gross_pay = base_pay + allowances + overtime + bonuses
        
        # Step 2: Calculate Superannuation (paid by employer, not deducted)
        sg_contribution = self.calculate_superannuation(ote, pay_period)
        
        # Step 3: Calculate Taxable Income
        taxable_income = gross_pay - salary_sacrifice_super - other_pre_tax_deductions
        
        # Step 4: Calculate PAYG Tax
        payg_tax = self.calculate_payg_tax(
            taxable_income,
            pay_period,
            claims_tax_free_threshold,
            is_resident,
            tfn_provided
        )
        
        # Step 5: Calculate Medicare Levy
        medicare_levy = self.calculate_medicare_levy(
            taxable_income,
            pay_period,
            is_single,
            num_dependents
        )
        
        # Step 6: Calculate HELP/HECS withholding
        help_withholding = Decimal('0')
        if has_help_debt:
            help_withholding = self.calculate_help_withholding(taxable_income, pay_period)
        
        # Step 7: Calculate Total Tax
        total_tax_withheld = payg_tax + medicare_levy + help_withholding
        
        # Step 8: Calculate Net Pay
        net_pay = taxable_income - total_tax_withheld - post_tax_deductions
        
        # Prepare notes
        notes = []
        if claims_tax_free_threshold:
            notes.append("Tax-free threshold applied")
        if has_help_debt:
            notes.append("HELP debt withholding active")
        if has_private_health:
            notes.append("Private health cover noted")
        if not tfn_provided:
            notes.append("No TFN - maximum withholding rate applied")
        if not is_resident:
            notes.append("Non-resident tax rates applied")
        
        return {
            'ote': self.round_currency(ote),
            'gross_pay': self.round_currency(gross_pay),
            'pre_tax_deductions': {
                'salary_sacrifice_super': self.round_currency(salary_sacrifice_super),
                'other': self.round_currency(other_pre_tax_deductions),
                'total': self.round_currency(salary_sacrifice_super + other_pre_tax_deductions)
            },
            'taxable_income': self.round_currency(taxable_income),
            'tax_withholdings': {
                'payg_tax': self.round_currency(payg_tax),
                'medicare_levy': self.round_currency(medicare_levy),
                'help_withholding': self.round_currency(help_withholding),
                'total': self.round_currency(total_tax_withheld)
            },
            'post_tax_deductions': self.round_currency(post_tax_deductions),
            'net_pay': self.round_currency(net_pay),
            'employer_contributions': {
                'superannuation': self.round_currency(sg_contribution)
            },
            'notes': notes,
            'breakdown': {
                'base_pay': self.round_currency(base_pay),
                'allowances': self.round_currency(allowances),
                'overtime': self.round_currency(overtime),
                'bonuses': self.round_currency(bonuses)
            }
        }


# Global instance
ato_calculator = ATOPayrollCalculator()
