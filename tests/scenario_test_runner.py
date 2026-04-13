"""
Static Scenario Test Runner for Military Transition Wizard

Runs pre-generated test scenarios through the wizard programmatically and:
1. Simulates Steps 1-8 by pre-populating session state
2. Generates 3-8 AI questions in Step 11
3. Collects responses and results
4. Saves comprehensive results for analysis
"""

import json
import random
from datetime import datetime
from typing import List, Dict, Any


class TestQuestionGenerator:
    """Generate test questions for a given scenario."""
    
    QUESTION_TEMPLATES = {
        "affordability_baseline": [
            "Based on my profile, can I afford this military-to-civilian transition?",
            "Will my financial situation sustain me through the job search period?",
            "What's my financial runway if I don't find a job immediately?",
            "Am I in a high-risk financial position?",
        ],
        "scenario_planning": [
            "What if my job search takes {job_search_timeline_months} months?",
            "What happens if I need to support {user_dependents} dependents on my savings alone?",
            "Can I maintain my current lifestyle during transition?",
            "What spending categories should I cut first if funds run low?",
        ],
        "comparative": [
            "How does my scenario compare to a typical {paygrade} transition?",
            "What advantages do I have compared to others in my pay grade?",
            "What risks are unique to my situation?",
        ],
        "risk_detection": [
            "What are the red flags in my transition plan?",
            "What could derail my financial plan?",
            "What should I prioritize to reduce risk?",
            "Are there hidden expenses I'm not accounting for?",
        ],
    }
    
    def __init__(self, scenario: Dict):
        """Initialize with a scenario."""
        self.scenario = scenario
    
    def generate_questions(self, count: int = 6) -> List[str]:
        """
        Generate 3-8 contextual questions for this scenario.
        Mix different question types.
        """
        questions = []
        
        # Always start with affordability baseline
        questions.append(random.choice(self.QUESTION_TEMPLATES["affordability_baseline"]))
        
        # Add scenario planning questions
        scenario_q = random.choice(self.QUESTION_TEMPLATES["scenario_planning"])
        scenario_q = scenario_q.format(
            job_search_timeline_months=self.scenario.get("job_search_timeline_months", 6),
            user_dependents=self.scenario.get("user_dependents", 0)
        )
        questions.append(scenario_q)
        
        # Add comparative questions
        if random.random() < 0.7:
            comp_q = random.choice(self.QUESTION_TEMPLATES["comparative"])
            comp_q = comp_q.format(paygrade=self.scenario.get("paygrade", "E-5"))
            questions.append(comp_q)
        
        # Add risk detection
        questions.append(random.choice(self.QUESTION_TEMPLATES["risk_detection"]))
        
        # Add follow-up questions based on scenario risk
        if self.scenario.get("is_edge_case"):
            questions.append("Given my edge case scenario, what's the minimum I need to do to stay viable?")
        
        # Add financial stress-specific questions
        if self.scenario.get("current_savings", 0) < 10000:
            questions.append("What are my emergency options if I run out of savings?")
        
        return questions[:count]


class ScenarioTestRunner:
    """Run test scenarios and collect results."""
    
    def __init__(self, scenarios_file: str = "d:\\Project Atlas\\tests\\static_test_scenarios.json"):
        """Initialize test runner with scenarios file."""
        with open(scenarios_file, "r") as f:
            self.test_suite = json.load(f)
        self.scenarios = self.test_suite["scenarios"]
        self.results = []
    
    def run_all_tests(self) -> Dict[str, Any]:
        """
        Run all test scenarios.
        
        Returns:
            {
                "metadata": {...},
                "results": [
                    {
                        "test_id": "TEST_0001",
                        "paygrade": "E-5",
                        "scenario": {...},
                        "questions": [...],
                        "is_edge_case": bool,
                        "test_status": "ready_for_ai",
                        "timestamp": "2026-04-06T..."
                    },
                    ...
                ]
            }
        """
        
        results = []
        total = 0
        edge_cases = 0
        
        for paygrade in self.scenarios:
            for scenario in self.scenarios[paygrade]:
                test_id = scenario.get("test_id")
                
                # Generate questions for this scenario
                qgen = TestQuestionGenerator(scenario)
                questions = qgen.generate_questions(count=random.randint(3, 8))
                
                # Create result record
                result = {
                    "test_id": test_id,
                    "paygrade": paygrade,
                    "scenario": scenario,
                    "questions": questions,
                    "question_count": len(questions),
                    "is_edge_case": scenario.get("is_edge_case", False),
                    "test_status": "ready_for_ai",
                    "timestamp": datetime.now().isoformat(),
                    "ai_responses": [],  # Will be filled by AI during Step 11
                    "analysis": {},  # Will be filled after AI responses
                }
                
                results.append(result)
                total += 1
                if result["is_edge_case"]:
                    edge_cases += 1
        
        return {
            "metadata": {
                "generated_date": datetime.now().isoformat(),
                "total_tests": total,
                "edge_cases": edge_cases,
                "paygrades": list(self.scenarios.keys()),
            },
            "results": results,
        }


def generate_static_test_suite() -> Dict[str, Any]:
    """
    Main function: Generate scenarios and questions for testing.
    """
    from scenario_test_generator import generate_test_suite as gen_scenarios
    
    print("📊 Generating stratified test scenarios...")
    scenario_suite = gen_scenarios(count_per_paygrade=50)
    
    # Save scenarios
    with open("d:\\Project Atlas\\tests\\static_test_scenarios.json", "w") as f:
        json.dump(scenario_suite, f, indent=2, default=str)
    
    print(f"✓ Generated {scenario_suite['metadata']['total_tests']} scenarios")
    
    print("\n📝 Generating test questions...")
    runner = ScenarioTestRunner("d:\\Project Atlas\\tests\\static_test_scenarios.json")
    test_suite = runner.run_all_tests()
    
    # Save test suite with questions
    with open("d:\\Project Atlas\\tests\\static_test_suite_with_questions.json", "w") as f:
        json.dump(test_suite, f, indent=2, default=str)
    
    print(f"✓ Generated {len(test_suite['results'])} test cases")
    print(f"  - Edge cases: {test_suite['metadata']['edge_cases']}")
    
    # Print summary
    print("\n📋 Test Suite Summary:")
    for paygrade in scenario_suite["metadata"]["paygrades"]:
        count = len(test_suite["results"])
        print(f"   {paygrade}: 50 tests")
    
    print("\n✅ Test suite ready for Step 11!")
    print("   Location: d:\\Project Atlas\\tests\\static_test_suite_with_questions.json")
    
    return test_suite


if __name__ == "__main__":
    test_suite = generate_static_test_suite()
    
    # Show sample
    if test_suite["results"]:
        sample = test_suite["results"][0]
        print(f"\n📌 Sample Test (first):")
        print(f"   ID: {sample['test_id']}")
        print(f"   Paygrade: {sample['paygrade']}")
        print(f"   Dependents: {sample['scenario']['user_dependents']}")
        print(f"   Savings: ${sample['scenario']['current_savings']:,}")
        print(f"   Job Search Timeline: {sample['scenario']['job_search_timeline_months']} months")
        print(f"   Edge Case: {sample['is_edge_case']}")
        print(f"   Questions to ask ({len(sample['questions'])}):")
        for idx, q in enumerate(sample['questions'], 1):
            print(f"      {idx}. {q}")
