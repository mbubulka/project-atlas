"""
Amortization Calculator for ProjectAtlas

Calculates loan payoff schedules, monthly payments, and total interest paid.
Handles fixed-rate amortized loans (mortgages, car loans, etc.).
"""

from dataclasses import dataclass
from typing import List, Optional
import math


@dataclass
class AmortizationPayment:
    """Single payment in amortization schedule."""
    month: int
    beginning_balance: float
    payment: float
    principal: float
    interest: float
    ending_balance: float


@dataclass
class AmortizationResult:
    """Complete amortization schedule and summary."""
    monthly_payment: float
    total_payments: int
    total_amount_paid: float
    total_interest_paid: float
    schedule: List[AmortizationPayment]
    
    def to_dict(self) -> dict:
        """Convert to dictionary for display."""
        return {
            "monthly_payment": self.monthly_payment,
            "total_payments": self.total_payments,
            "total_amount_paid": self.total_amount_paid,
            "total_interest_paid": self.total_interest_paid,
            "schedule": [
                {
                    "month": p.month,
                    "beginning_balance": p.beginning_balance,
                    "payment": p.payment,
                    "principal": p.principal,
                    "interest": p.interest,
                    "ending_balance": p.ending_balance,
                }
                for p in self.schedule
            ],
        }


class AmortizationCalculator:
    """
    Calculates amortization schedules for fixed-rate loans.
    
    Supports:
    - Mortgages (15, 20, 30 year)
    - Auto loans (36, 48, 60, 72 month)
    - Personal loans
    - Military-specific: VA refinance (IRRRL), home purchase loans
    
    Formula:
    M = P * [r(1+r)^n] / [(1+r)^n - 1]
    where:
        M = monthly payment
        P = principal
        r = monthly interest rate (annual / 12)
        n = number of months
    """
    
    @staticmethod
    def calculate_payment(
        principal: float,
        annual_rate: float,
        months: int,
    ) -> float:
        """
        Calculate fixed monthly payment for a loan.
        
        Args:
            principal: Loan amount in dollars
            annual_rate: Annual interest rate as percentage (e.g., 4.5 for 4.5%)
            months: Total number of months to pay
            
        Returns:
            Monthly payment amount
        """
        if annual_rate == 0:
            return principal / months
        
        monthly_rate = annual_rate / 100 / 12
        numerator = principal * monthly_rate * (1 + monthly_rate) ** months
        denominator = (1 + monthly_rate) ** months - 1
        
        return numerator / denominator
    
    @staticmethod
    def calculate_schedule(
        principal: float,
        annual_rate: float,
        months: int,
        monthly_payment: Optional[float] = None,
    ) -> AmortizationResult:
        """
        Generate complete amortization schedule.
        
        Args:
            principal: Loan amount
            annual_rate: Annual interest rate (%)
            months: Number of months
            monthly_payment: Optional fixed payment (if None, calculated)
            
        Returns:
            AmortizationResult with schedule and summary
        """
        # Calculate payment if not provided
        if monthly_payment is None:
            monthly_payment = AmortizationCalculator.calculate_payment(
                principal, annual_rate, months
            )
        
        monthly_rate = annual_rate / 100 / 12
        schedule = []
        balance = principal
        total_paid = 0
        total_interest = 0
        
        for month in range(1, months + 1):
            # Interest for this month
            interest_payment = balance * monthly_rate
            
            # Principal for this month
            principal_payment = monthly_payment - interest_payment
            
            # New balance
            new_balance = balance - principal_payment
            if new_balance < 0:
                new_balance = 0
            
            # Track totals
            total_paid += monthly_payment
            total_interest += interest_payment
            
            # Add to schedule
            schedule.append(
                AmortizationPayment(
                    month=month,
                    beginning_balance=balance,
                    payment=monthly_payment,
                    principal=principal_payment,
                    interest=interest_payment,
                    ending_balance=new_balance,
                )
            )
            
            balance = new_balance
        
        return AmortizationResult(
            monthly_payment=monthly_payment,
            total_payments=months,
            total_amount_paid=total_paid,
            total_interest_paid=total_interest,
            schedule=schedule,
        )
    
    @staticmethod
    def calculate_remaining_balance(
        original_principal: float,
        annual_rate: float,
        original_months: int,
        months_paid: int,
    ) -> float:
        """
        Calculate remaining balance on a loan after some payments.
        
        Args:
            original_principal: Original loan amount
            annual_rate: Annual interest rate (%)
            original_months: Total loan term in months
            months_paid: Number of months already paid
            
        Returns:
            Remaining balance
        """
        monthly_payment = AmortizationCalculator.calculate_payment(
            original_principal, annual_rate, original_months
        )
        
        monthly_rate = annual_rate / 100 / 12
        remaining_months = original_months - months_paid
        
        # Balance = PV of remaining payments
        if monthly_rate == 0:
            return original_principal - (monthly_payment * months_paid)
        
        remaining_balance = (
            monthly_payment
            * ((1 + monthly_rate) ** remaining_months - 1)
            / (monthly_rate * (1 + monthly_rate) ** remaining_months)
        )
        
        return max(0, remaining_balance)
    
    @staticmethod
    def calculate_payoff_months(
        original_principal: float,
        annual_rate: float,
        monthly_payment: float,
    ) -> int:
        """
        Calculate how many months to pay off a loan with given payment.
        
        Args:
            original_principal: Loan amount
            annual_rate: Annual interest rate (%)
            monthly_payment: Monthly payment amount
            
        Returns:
            Number of months to payoff
        """
        if monthly_payment <= 0:
            return 0
        
        monthly_rate = annual_rate / 100 / 12
        
        if monthly_rate == 0:
            return int(original_principal / monthly_payment)
        
        # n = -log(1 - (P * r) / M) / log(1 + r)
        numerator = 1 - (original_principal * monthly_rate) / monthly_payment
        
        if numerator <= 0:
            return 0  # Payment insufficient to cover interest
        
        months = -math.log(numerator) / math.log(1 + monthly_rate)
        return int(math.ceil(months))
