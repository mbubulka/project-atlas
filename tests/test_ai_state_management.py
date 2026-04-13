"""
Test script for AI scenario state management and comparison workflow.

Tests:
1. Temp profile creation from AI analysis
2. Comparison statement generation
3. Scenario naming and metadata
4. End-to-end AI analysis → save → compare
"""

import sys
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.ai_layer.ai_scenario_state_manager import AIScenarioStateManager


def test_temp_profile_creation():
    """Test creating temp profile from AI extraction."""
    print("\n✓ TEST 1: Temp Profile Creation")
    print("=" * 60)
    
    # Baseline profile
    baseline = {
        'job_search_timeline_months': 6,
        'csv_optional_expenses': 500,
        'csv_negotiable_expenses': 1000,
        'gi_bill_bah_monthly': 0,
    }
    
    # AI extraction results
    extracted = {
        'job_search_timeline_months': 9,
        'expense_reduction': 200,
    }
    
    # Create temp profile
    analyzed = AIScenarioStateManager.create_temp_analyzed_profile(
        baseline,
        extracted,
        {'test': 'calculation'}
    )
    
    # Verify changes applied
    assert analyzed['job_search_timeline_months'] == 9, "Job search timeline not updated"
    assert analyzed['csv_optional_expenses'] == 300, "Expense reduction not applied"  # 500 - 200
    assert baseline['job_search_timeline_months'] == 6, "Baseline was mutated!"
    assert baseline['csv_optional_expenses'] == 500, "Baseline was mutated!"
    assert '_ai_analysis' in analyzed, "AI metadata not stored"
    
    print(f"✅ Baseline job search: {baseline['job_search_timeline_months']} months")
    print(f"✅ Analyzed job search: {analyzed['job_search_timeline_months']} months")
    print(f"✅ Baseline expenses: ${baseline['csv_optional_expenses']}")
    print(f"✅ Analyzed expenses: ${analyzed['csv_optional_expenses']}")
    print(f"✅ Baseline unchanged (no mutations)")
    return True


def test_comparison_statement():
    """Test generating comparison statements."""
    print("\n✓ TEST 2: Comparison Statement Generation")
    print("=" * 60)
    
    baseline = {
        'job_search_timeline_months': 6,
        'csv_optional_expenses': 500,
        'csv_negotiable_expenses': 1000,
        'gi_bill_bah_monthly': 0,
    }
    
    analyzed = {
        'job_search_timeline_months': 9,
        'csv_optional_expenses': 300,
        'csv_negotiable_expenses': 1000,
        'gi_bill_bah_monthly': 2000,
    }
    
    comparison = AIScenarioStateManager.generate_comparison_statement(
        baseline,
        analyzed,
        'job_search_timeline',
        'What if I take 9 months?'
    )
    
    assert '3 months longer' in comparison, "Timeline delta not detected"
    assert '200' in comparison, "Expense reduction not mentioned"
    # GI Bill should be mentioned since analyzed has 2000 and baseline has 0
    assert '2000' in comparison or '2,000' in comparison, "GI Bill BAH not mentioned (checking both number formats)"
    
    print(f"✅ Comparison Statement Generated:")
    print(f"   {comparison}")
    return True


def test_scenario_creation_for_save():
    """Test creating saved scenario from AI analysis."""
    print("\n✓ TEST 3: Scenario Creation for Dashboard Save")
    print("=" * 60)
    
    baseline = {
        'job_search_timeline_months': 6,
        'csv_optional_expenses': 500,
    }
    
    analyzed = {
        'job_search_timeline_months': 9,
        'csv_optional_expenses': 300,
    }
    
    result = {
        'intent': 'job_search_timeline',
        'analysis': 'Taking 9 months extends your transition timeline.',
        'recommendation': 'Build extra buffer for job search duration.',
    }
    
    question = 'What if my job search takes 9 months?'
    
    scenario = AIScenarioStateManager.create_named_scenario_from_ai(
        baseline,
        analyzed,
        question,
        result
    )
    
    # Verify all required fields
    assert 'name' in scenario, "Name not created"
    assert 'profile' in scenario, "Profile not included"
    assert 'timestamp' in scenario, "Timestamp not added"
    assert scenario['source'] == 'ai_analysis', "Source not marked"
    assert 'comparison_to_baseline' in scenario, "Comparison not generated"
    assert 'baseline_profile' in scenario, "Baseline not stored"
    
    print(f"✅ Scenario Name: {scenario['name']}")
    print(f"✅ Source: {scenario['source']}")
    print(f"✅ Comparison: {scenario['comparison_to_baseline']}")
    print(f"✅ Timestamp: {scenario['timestamp']}")
    print(f"✅ Baseline preserved for comparison")
    return True


def test_workflow_integration():
    """Test complete workflow: analysis → profile creation → comparison → save."""
    print("\n✓ TEST 4: End-to-End Workflow Integration")
    print("=" * 60)
    
    # Simulate user baseline
    baseline_profile = {
        'user_rank': 'O-5',
        'years_of_service': 28,
        'job_search_timeline_months': 6,
        'csv_optional_expenses': 500,
        'csv_negotiable_expenses': 1000,
        'gi_bill_bah_monthly': 0,
        'pension': 5000,
        'va_monthly': 1000,
        'current_savings': 50000,
    }
    
    # Step 1: User asks scenario question
    user_question = 'What if I use the GI Bill and take 8 months to graduate?'
    print(f"\n1️⃣  User Question: {user_question}")
    
    # Step 2: AI extracts parameters
    extracted_params = {
        'degree': 'masters',
        'location': 'Colorado',
        'job_search_timeline_months': 8,
        'gi_bill_bah_monthly': 2000,
    }
    print(f"2️⃣  AI Extracted: {extracted_params}")
    
    # Step 3: Create temp analyzed profile
    analyzed_profile = AIScenarioStateManager.create_temp_analyzed_profile(
        baseline_profile,
        extracted_params,
        {'gi_bill': 'calculated', 'expenses': 'recalculated'}
    )
    print(f"3️⃣  Temp Profile Created (baseline unchanged: {baseline_profile['job_search_timeline_months']} months)")
    
    # Step 4: Generate comparison
    comparison = AIScenarioStateManager.generate_comparison_statement(
        baseline_profile,
        analyzed_profile,
        'gi_bill',
        user_question
    )
    print(f"4️⃣  Comparison Generated: {comparison}")
    
    # Step 5: Create saveable scenario
    result = {
        'intent': 'gi_bill',
        'analysis': 'Using GI Bill extends your timeline but provides BAH income.',
        'recommendation': 'GI Bill is viable with your savings buffer.',
    }
    
    scenario = AIScenarioStateManager.create_named_scenario_from_ai(
        baseline_profile,
        analyzed_profile,
        user_question,
        result
    )
    print(f"5️⃣  Scenario Created: {scenario['name']}")
    
    # Step 6: Verify can be saved to list
    saved_scenarios = []
    saved_scenarios.append(scenario)
    print(f"6️⃣  Saved to list: {len(saved_scenarios)} scenario(s)")
    
    # Step 7: Verify comparison data persists
    assert scenario['comparison_to_baseline'] != '', "Comparison lost"
    assert scenario['baseline_profile']['job_search_timeline_months'] == 6, "Baseline not preserved"
    print(f"7️⃣  Comparison data persists for dashboard display")
    
    print(f"\n✅ WORKFLOW COMPLETE: Question → Extract → Analyze → Compare → Save")
    return True


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("AI SCENARIO STATE MANAGEMENT - COMPREHENSIVE TEST SUITE")
    print("=" * 60)
    
    tests = [
        ("Temp Profile Creation", test_temp_profile_creation),
        ("Comparison Statement", test_comparison_statement),
        ("Scenario Creation", test_scenario_creation_for_save),
        ("Workflow Integration", test_workflow_integration),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except AssertionError as e:
            print(f"❌ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ ERROR: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED - AI STATE MANAGEMENT READY FOR PRODUCTION")
    else:
        print(f"\n⚠️  {failed} test(s) failed - review above for details")
    
    sys.exit(0 if failed == 0 else 1)
