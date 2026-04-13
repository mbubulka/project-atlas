"""
Debt Reduction Optimizer for ProjectAtlas

Calculates optimal debt payoff strategy using snowball and avalanche methods.
Helps military transitioners plan debt elimination during job search period.
"""

from dataclasses import dataclass
from typing import List, Optional
from enum import Enum


class DebtStrategy(Enum):
    """Debt payoff strategies."""
    SNOWBALL = "snowball"  # Pay smallest balance first
    AVALANCHE = "avalanche"  # Pay highest interest rate first


@dataclass
class Debt:
    """Single debt liability."""
    name: str
    balance: float
    annual_rate: float
    minimum_payment: float
    priority: int = 0  # For custom ordering


@dataclass
class DebtPaymentMonth:
    """Single month in debt payoff schedule."""
    month: int
    debts: List[dict]  # Each debt: {name, balance, payment, interest, principal}
    total_payment: float
    total_interest: float
    total_balance: float
    payoff_progress: float  # Percent of debts paid off


@dataclass
class DebtOptimizationResult:
    """Complete debt optimization analysis."""
    strategy: str
    monthly_surplus: float
    total_months_to_payoff: int
    total_interest_paid: float
    total_amount_paid: float
    monthly_schedule: List[DebtPaymentMonth]
    debt_order: List[str]  # Order to pay off debts
    savings_vs_minimum: float  # Interest saved vs minimum payments
    
    def to_dict(self) -> dict:
        """Convert to dictionary for display."""
        return {
            "strategy": self.strategy,
            "monthly_surplus": self.monthly_surplus,
            "total_months_to_payoff": self.total_months_to_payoff,
            "total_interest_paid": self.total_interest_paid,
            "total_amount_paid": self.total_amount_paid,
            "debt_order": self.debt_order,
            "savings_vs_minimum": self.savings_vs_minimum,
            "monthly_schedule": [
                {
                    "month": m.month,
                    "debts": m.debts,
                    "total_payment": m.total_payment,
                    "total_interest": m.total_interest,
                    "total_balance": m.total_balance,
                    "payoff_progress": m.payoff_progress,
                }
                for m in self.monthly_schedule[:12]  # First 12 months for display
            ],
        }


class DebtOptimizer:
    """
    Calculates optimal debt payoff strategies for military transitioners.
    
    Supports:
    - Snowball method (psychological wins - pay smallest balance first)
    - Avalanche method (interest optimization - pay highest rate first)
    - Custom debt ordering
    - Scenario analysis (what if extra $500/month available?)
    
    Context: Military transitioner with temporary cash flow (pension + job search)
    """
    
    @staticmethod
    def calculate_debt_payoff(
        debts: List[Debt],
        monthly_surplus: float,
        strategy: DebtStrategy = DebtStrategy.SNOWBALL,
        max_months: int = 360,  # 30 years max
    ) -> DebtOptimizationResult:
        """
        Calculate debt payoff schedule using specified strategy.
        
        Args:
            debts: List of Debt objects
            monthly_surplus: Monthly amount available for debt payment (beyond minimums)
            strategy: SNOWBALL or AVALANCHE
            max_months: Maximum months to simulate
            
        Returns:
            DebtOptimizationResult with full schedule and analysis
        """
        if not debts or monthly_surplus < 0:
            return None
        
        # Calculate initial total interest (minimum payments only)
        min_interest_baseline = DebtOptimizer._calculate_interest_on_minimums(
            debts, max_months
        )
        
        # Order debts per strategy
        if strategy == DebtStrategy.SNOWBALL:
            debt_order = DebtOptimizer._snowball_order(debts)
        else:
            debt_order = DebtOptimizer._avalanche_order(debts)
        
        # Reorder the debt list
        debts_dict = {d.name: d for d in debts}
        ordered_debts = [debts_dict[name] for name in debt_order]
        
        # Simulate payoff month by month
        schedule = []
        month = 0
        total_interest_paid = 0
        total_amount_paid = 0
        
        # Track working balances
        balances = {d.name: d.balance for d in ordered_debts}
        monthly_rates = {d.name: d.annual_rate / 100 / 12 for d in ordered_debts}
        min_payments = {d.name: d.minimum_payment for d in ordered_debts}
        
        # Remaining surplus to allocate
        remaining_surplus = monthly_surplus
        
        while month < max_months:
            month += 1
            month_data = []
            month_interest = 0
            month_total_balance = 0
            month_total_payment = 0
            
            # Calculate interest on all debts
            for d in ordered_debts:
                if balances[d.name] <= 0:
                    continue
                
                # Interest accrual
                interest = balances[d.name] * monthly_rates[d.name]
                month_interest += interest
                total_interest_paid += interest
                
                # Minimum payment
                min_payment = min_payments[d.name]
                
                # Principal reduction
                principal = min_payment - interest
                principal = max(0, principal)
                
                # Update balance
                balances[d.name] = max(0, balances[d.name] - principal)
                month_total_balance += balances[d.name]
                
                month_data.append({
                    "name": d.name,
                    "balance": balances[d.name],
                    "payment": min_payment,
                    "interest": interest,
                    "principal": principal,
                })
                
                month_total_payment += min_payment
                total_amount_paid += min_payment
            
            # Apply extra surplus strategically
            remaining_surplus = monthly_surplus
            for d in ordered_debts:
                if balances[d.name] <= 0 or remaining_surplus <= 0:
                    continue
                
                # Extra payment to this debt
                extra_payment = min(remaining_surplus, balances[d.name])
                balances[d.name] -= extra_payment
                remaining_surplus -= extra_payment
                month_total_payment += extra_payment
                total_amount_paid += extra_payment
                
                # Update month data
                for debt_month in month_data:
                    if debt_month["name"] == d.name:
                        debt_month["payment"] += extra_payment
                        debt_month["balance"] = balances[d.name]
            
            # Calculate payoff progress
            paid_off = sum(1 for b in balances.values() if b <= 0)
            progress = paid_off / len(ordered_debts)
            
            schedule.append(
                DebtPaymentMonth(
                    month=month,
                    debts=month_data,
                    total_payment=month_total_payment,
                    total_interest=month_interest,
                    total_balance=month_total_balance,
                    payoff_progress=progress,
                )
            )
            
            # Check if all debts paid off
            if all(b <= 0 for b in balances.values()):
                break
        
        # Calculate savings vs minimum payments
        savings = min_interest_baseline - total_interest_paid
        
        return DebtOptimizationResult(
            strategy=strategy.value,
            monthly_surplus=monthly_surplus,
            total_months_to_payoff=month,
            total_interest_paid=total_interest_paid,
            total_amount_paid=total_amount_paid,
            monthly_schedule=schedule,
            debt_order=debt_order,
            savings_vs_minimum=savings,
        )
    
    @staticmethod
    def compare_strategies(
        debts: List[Debt],
        monthly_surplus: float,
    ) -> dict:
        """
        Compare snowball vs avalanche strategies.
        
        Args:
            debts: List of debts
            monthly_surplus: Monthly payment capacity
            
        Returns:
            Dictionary with both strategies' results
        """
        snowball = DebtOptimizer.calculate_debt_payoff(
            debts, monthly_surplus, DebtStrategy.SNOWBALL
        )
        avalanche = DebtOptimizer.calculate_debt_payoff(
            debts, monthly_surplus, DebtStrategy.AVALANCHE
        )
        
        return {
            "snowball": snowball,
            "avalanche": avalanche,
            "interest_difference": avalanche.total_interest_paid - snowball.total_interest_paid,
            "time_difference": avalanche.total_months_to_payoff - snowball.total_months_to_payoff,
            "recommendation": DebtOptimizer._recommend_strategy(snowball, avalanche),
        }
    
    @staticmethod
    def _snowball_order(debts: List[Debt]) -> List[str]:
        """Order debts by balance (smallest first)."""
        return [d.name for d in sorted(debts, key=lambda x: x.balance)]
    
    @staticmethod
    def _avalanche_order(debts: List[Debt]) -> List[str]:
        """Order debts by interest rate (highest first)."""
        return [d.name for d in sorted(debts, key=lambda x: -x.annual_rate)]
    
    @staticmethod
    def _calculate_interest_on_minimums(
        debts: List[Debt],
        max_months: int,
    ) -> float:
        """Calculate total interest if paying minimums only."""
        total_interest = 0
        balances = {d.name: d.balance for d in debts}
        monthly_rates = {d.name: d.annual_rate / 100 / 12 for d in debts}
        
        for _ in range(max_months):
            for d in debts:
                if balances[d.name] <= 0:
                    continue
                
                interest = balances[d.name] * monthly_rates[d.name]
                total_interest += interest
                
                principal = d.minimum_payment - interest
                principal = max(0, principal)
                balances[d.name] = max(0, balances[d.name] - principal)
            
            if all(b <= 0 for b in balances.values()):
                break
        
        return total_interest
    
    @staticmethod
    def _recommend_strategy(snowball_result, avalanche_result) -> str:
        """Recommend best strategy based on results."""
        # If avalanche saves < $500 interest, recommend snowball (psychological wins matter)
        if avalanche_result.total_interest_paid - snowball_result.total_interest_paid < 500:
            return "SNOWBALL - Similar interest savings, but better for motivation"
        
        # If time difference > 12 months, recommend avalanche
        if avalanche_result.total_months_to_payoff - snowball_result.total_months_to_payoff < -12:
            return "AVALANCHE - Saves significant interest and time"
        
        return "SNOWBALL - Recommended for psychological momentum during transition"
