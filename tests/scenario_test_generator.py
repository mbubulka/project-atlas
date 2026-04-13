"""
Stratified Scenario Test Generator for Military Transition Wizard

Generates realistic test scenarios using stratified sampling across:
- Paygrades (E-5, E-6, O-3, E-9)
- Financial stress levels (Low, Medium, High)
- Healthcare complexity (Simple, Complex)
- Family situations (Single, Married, +Kids)
- Edge cases (deliberately included for AI testing)

Produces 50 scenarios per paygrade for total of 200 test cases.
"""

import json
import random
import uuid
from datetime import date, timedelta
from typing import List, Dict, Any


class ScenarioTestGenerator:
    """Generate stratified test scenarios for wizard testing."""
    
    PAYGRADES = {
        "E-5": {"title": "Staff Sergeant", "base_yos": 20, "key": "E-5"},
        "E-6": {"title": "Technical Sergeant", "base_yos": 22, "key": "E-6"},
        "O-3": {"title": "Captain", "base_yos": 18, "key": "O-3"},
        "E-9": {"title": "Chief Master Sergeant", "base_yos": 28, "key": "E-9"},
    }
    
    STRATA = {
        "financial_stress": ["low", "medium", "high"],
        "healthcare_complexity": ["simple", "complex"],
        "family_situation": ["single", "married", "married_kids"],
    }
    
    def __init__(self, seed=42):
        """Initialize generator with optional seed for reproducibility."""
        random.seed(seed)
    
    def generate_all_scenarios(self) -> Dict[str, List[Dict]]:
        """
        Generate stratified scenarios for all paygrades.
        
        Returns:
            {
                "E-5": [scenario1, scenario2, ...],
                "E-6": [...],
                ...
            }
        """
        all_scenarios = {}
        
        for paygrade in self.PAYGRADES.keys():
            all_scenarios[paygrade] = self.generate_paygrade_scenarios(paygrade, count=50)
            print(f"✓ Generated 50 scenarios for {paygrade}")
        
        return all_scenarios
    
    def generate_paygrade_scenarios(self, paygrade: str, count: int = 50) -> List[Dict]:
        """Generate stratified scenarios for a specific paygrade."""
        
        scenarios = []
        strata_combinations = []
        
        # Generate strata combinations (ensures coverage)
        for stress in self.STRATA["financial_stress"]:
            for healthcare in self.STRATA["healthcare_complexity"]:
                for family in self.STRATA["family_situation"]:
                    strata_combinations.append({
                        "financial_stress": stress,
                        "healthcare_complexity": healthcare,
                        "family_situation": family,
                    })
        
        # Distribute scenarios across strata (roughly equal per stratum)
        scenarios_per_stratum = count // len(strata_combinations)
        remainder = count % len(strata_combinations)
        
        for idx, stratum in enumerate(strata_combinations):
            # Add scenarios to this stratum
            num_scenarios = scenarios_per_stratum + (1 if idx < remainder else 0)
            for _ in range(num_scenarios):
                scenario = self._generate_scenario_in_stratum(paygrade, stratum)
                scenarios.append(scenario)
        
        # Shuffle for more realistic distribution
        random.shuffle(scenarios)
        return scenarios[:count]
    
    def _generate_scenario_in_stratum(self, paygrade: str, stratum: Dict) -> Dict:
        """Generate a single scenario within a stratum."""
        
        pg_info = self.PAYGRADES[paygrade]
        
        # Base parameters from paygrade
        scenario = {
            "paygrade": paygrade,
            "rank_title": pg_info["title"],
        }
        
        # === Step 1: Military Profile ===
        scenario["user_years_of_service"] = self._generate_yos(pg_info["base_yos"])
        scenario["user_separation_date"] = self._generate_separation_date()
        scenario["user_marital_status"] = self._generate_marital_status(stratum["family_situation"])
        scenario["user_dependents"] = self._generate_dependents(
            stratum["family_situation"],
            scenario["user_marital_status"]
        )
        scenario["user_service_branch"] = random.choice(["Army", "Navy", "Air Force", "Marines", "Coast Guard"])
        scenario["user_career_field"] = random.choice([
            "Operations Research Analyst", "Cyber Analyst", "Software Engineer",
            "Strategic Planner", "Data Analyst", "Project Manager", "Financial Analyst"
        ])
        scenario["career_education"] = random.choice(["Bachelor's", "Master's"])
        scenario["career_clearance"] = random.choice(["None", "Secret", "Top Secret", "Top Secret/SCI"])
        scenario["user_locality"] = random.choice(["Arlington", "San Diego", "Washington", "Fort Bragg"])
        scenario["user_state"] = random.choice(["VA", "CA", "DC", "NC"])
        
        # === Step 2a: Healthcare ===
        if stratum["healthcare_complexity"] == "simple":
            scenario["medical_plan"] = "Tricare Prime"
            scenario["medical_coverage_type"] = "Self Only"
            scenario["tricare_monthly_cost"] = 100
        else:
            scenario["medical_plan"] = random.choice(["Tricare Prime", "Tricare Select"])
            scenario["medical_coverage_type"] = random.choice(["Self + Family", "Self + 1 person"])
            scenario["tricare_monthly_cost"] = random.randint(200, 400)
        scenario["medical_custom_cost"] = 0
        
        # === Step 2b: SBP ===
        if stratum["healthcare_complexity"] == "complex" and scenario["user_dependents"] > 0:
            scenario["sbp_election"] = random.choice(["spouse_only", "spouse_and_children", "off"])
            scenario["sbp_monthly_cost"] = random.randint(50, 200) if scenario["sbp_election"] != "off" else 0
            scenario["sbp_monthly_benefit"] = scenario["sbp_monthly_cost"] * 12 if scenario["sbp_election"] != "off" else 0
        else:
            scenario["sbp_election"] = "off"
            scenario["sbp_monthly_cost"] = 0
            scenario["sbp_monthly_benefit"] = 0
        
        scenario["life_insurance_monthly_cost"] = 0
        scenario["life_insurance_monthly_benefit"] = 0
        
        # === Step 2c: GI Bill ===
        scenario["gi_bill_choice"] = random.choice(["Yes, for degree completion", "Yes, for additional training", "No, focused on immediate transition"])
        scenario["gi_bill_months_remaining"] = random.randint(0, 36) if "Yes" in scenario["gi_bill_choice"] else 0
        scenario["gi_bill_bah_monthly"] = 0
        
        # === Step 3: Pension & VA ===
        scenario["va_rating_slider"] = self._generate_va_rating(stratum["financial_stress"])
        scenario["tricare_deduction_pension"] = 90
        scenario["pension_take_home"] = 0  # Will be calculated
        scenario["military_pension_gross"] = 0  # Will be calculated
        scenario["current_military_takehome_monthly"] = self._generate_military_takehome(paygrade)
        scenario["va_monthly_amount"] = 0  # Will be calculated
        
        # === Step 4: Financial Resources ===
        scenario["current_savings"] = self._generate_savings(stratum["financial_stress"])
        scenario["available_savings"] = scenario["current_savings"]
        scenario["available_credit"] = self._generate_credit(stratum["financial_stress"])
        scenario["job_search_timeline_months"] = self._generate_job_search_timeline(stratum["financial_stress"])
        scenario["estimated_civilian_salary"] = 0  # Will be calculated by AI
        
        # === Test metadata ===
        scenario["stratum"] = stratum
        scenario["is_edge_case"] = self._is_edge_case(scenario, stratum)
        
        return scenario
    
    def _generate_yos(self, base_yos: int) -> int:
        """Generate Years of Service around base_yos with some variation."""
        # Bimodal: tendency toward 20 (retirement cutoff) and 28+ (full career)
        if random.random() < 0.5:
            return base_yos + random.randint(-2, 2)
        else:
            return base_yos + random.randint(3, 8)
    
    def _generate_separation_date(self) -> date:
        """Generate realistic future separation date."""
        days_offset = random.randint(30, 365)  # 1-12 months out
        sep_date = date.today() + timedelta(days=days_offset)
        return sep_date
    
    def _generate_marital_status(self, family_situation: str) -> str:
        """Generate marital status based on family situation."""
        if family_situation == "single":
            return "Single"
        elif family_situation == "married":
            return "Married"
        else:  # married_kids
            return "Married"
    
    def _generate_dependents(self, family_situation: str, marital_status: str) -> int:
        """Generate number of dependents."""
        if family_situation == "single":
            return random.choice([0, 0, 0, 1])  # Mostly 0, sometimes 1 (elderly parent, etc)
        elif family_situation == "married":
            return 0
        else:  # married_kids
            return random.randint(1, 3)
    
    def _generate_va_rating(self, financial_stress: str) -> int:
        """Generate VA rating (skewed left for realism)."""
        if financial_stress == "high":
            # Higher ratings more likely in high-stress scenarios
            return random.choice([0, 0, 10, 20, 30, 30, 40, 50])
        else:
            # Lower ratings more typical
            return random.choice([0, 0, 0, 10, 20, 30])
    
    def _generate_savings(self, financial_stress: str) -> int:
        """Generate savings amount (log-normal distribution)."""
        if financial_stress == "low":
            return random.randint(50000, 200000)
        elif financial_stress == "medium":
            return random.randint(15000, 50000)
        else:  # high stress
            return random.randint(0, 15000)
    
    def _generate_credit(self, financial_stress: str) -> int:
        """Generate available credit."""
        if financial_stress == "low":
            return random.randint(10000, 50000)
        elif financial_stress == "medium":
            return random.randint(5000, 20000)
        else:  # high stress
            return random.randint(0, 10000)
    
    def _generate_job_search_timeline(self, financial_stress: str) -> int:
        """Generate expected job search timeline (months)."""
        if financial_stress == "low":
            return random.randint(1, 4)
        elif financial_stress == "medium":
            return random.randint(3, 8)
        else:  # high stress
            return random.randint(6, 12)
    
    def _generate_military_takehome(self, paygrade: str) -> int:
        """Generate realistic military take-home pay by paygrade."""
        takehome_map = {
            "E-5": random.randint(5000, 5500),
            "E-6": random.randint(5800, 6500),
            "O-3": random.randint(8000, 9000),
            "E-9": random.randint(9500, 10500),
        }
        return takehome_map.get(paygrade, 6000)
    
    def _is_edge_case(self, scenario: Dict, stratum: Dict) -> bool:
        """Identify edge cases that could break the system."""
        # Edge case: High dependents + Low savings + High job search time
        if (scenario["user_dependents"] >= 2 and 
            scenario["current_savings"] < 10000 and 
            scenario["job_search_timeline_months"] >= 8):
            return True
        
        # Edge case: Low VA rating + Zero savings
        if scenario["va_rating_slider"] == 0 and scenario["current_savings"] < 5000:
            return True
        
        # Edge case: Married + 2+ kids + Needs complex healthcare
        if (scenario["user_marital_status"] == "Married" and 
            scenario["user_dependents"] >= 2 and 
            stratum["healthcare_complexity"] == "complex"):
            return True
        
        return False


def generate_test_suite(count_per_paygrade: int = 50) -> Dict[str, Any]:
    """Generate complete test suite and save to file."""
    
    generator = ScenarioTestGenerator()
    scenarios = generator.generate_all_scenarios()
    
    # Assign test IDs
    test_id = 1
    for paygrade in scenarios:
        for scenario in scenarios[paygrade]:
            scenario["test_id"] = f"TEST_{test_id:04d}"
            test_id += 1
    
    # Create test suite object
    test_suite = {
        "metadata": {
            "generated_date": date.today().isoformat(),
            "total_tests": sum(len(s) for s in scenarios.values()),
            "tests_per_paygrade": count_per_paygrade,
            "paygrades": list(generator.PAYGRADES.keys()),
            "strata": generator.STRATA,
        },
        "scenarios": scenarios,
    }
    
    return test_suite


if __name__ == "__main__":
    # Generate and save test suite
    test_suite = generate_test_suite(count_per_paygrade=50)
    
    # Save to file
    output_file = "d:\\Project Atlas\\tests\\static_test_scenarios.json"
    with open(output_file, "w") as f:
        json.dump(test_suite, f, indent=2, default=str)
    
    print(f"\n✅ Test suite generated!")
    print(f"   Total scenarios: {test_suite['metadata']['total_tests']}")
    print(f"   Paygrades: {', '.join(test_suite['metadata']['paygrades'])}")
    print(f"   Saved to: {output_file}")
    
    # Print sample scenario
    print(f"\n📋 Sample scenario (E-5):")
    sample = test_suite['scenarios']['E-5'][0]
    for key in ['test_id', 'paygrade', 'user_years_of_service', 'user_dependents', 
                'current_savings', 'job_search_timeline_months', 'is_edge_case']:
        print(f"   {key}: {sample.get(key)}")
