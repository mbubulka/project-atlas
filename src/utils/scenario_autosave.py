"""
Auto-save scenarios to JSON for analysis and validation.
Tracks all user inputs and calculated results for "common sense" testing.
"""

import json
import os
from datetime import datetime
from pathlib import Path
import streamlit as st


class ScenarioAutoSaver:
    """Manages automatic scenario saving to JSON files."""
    
    def __init__(self, base_dir: str = None):
        """Initialize with scenarios directory."""
        if base_dir is None:
            base_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'scenarios')
        
        self.base_dir = base_dir
        Path(self.base_dir).mkdir(parents=True, exist_ok=True)
        self.run_log_file = os.path.join(self.base_dir, 'scenarios_run_log.json')
    
    def get_scenario_data(self):
        """Extract all relevant scenario data from session state."""
        saveable_keys = [
            # Profile
            'user_rank', 'user_years_of_service', 'user_career_field', 
            'user_separation_date', 'user_marital_status', 'user_dependents',
            'user_service_branch', 'user_locality', 'user_state',
            
            # Income
            'military_pension_gross', 'current_military_takehome_monthly',
            'va_rating', 'va_monthly_custom', 'use_calculated_va',
            'new_job_salary_annual', 'job_start_month',
            'rental_income_monthly', 'spouse_income_monthly', 'other_income_monthly',
            'current_takehome', 'current_annual_pretax', 'other_deductions',
            'filing_status', 'state', 'savings_available',
            
            # Healthcare
            'medical_plan', 'medical_dependents_status',
            'vision_plan', 'dental_plan',
            
            # Education
            'gi_program_type', 'school_location_preset', 'school_custom_bah',
            'gi_months_used', 'ruskin_approved', 'ruskin_additional_months',
            'bah_custom', 'salary_education', 'salary_expectation',
            
            # Calculated Results
            'annual_income_civilian', 'annual_income_military', 'annual_income_total',
            'annual_expenses_essential', 'annual_expenses_discretionary',
            'annual_expenses_investable', 'annual_expenses_total',
            'retirement_runway_months', 'annual_surplus_deficit',
        ]
        
        scenario_data = {}
        for key in saveable_keys:
            if key in st.session_state:
                value = st.session_state[key]
                # Handle date objects
                if hasattr(value, 'isoformat'):
                    scenario_data[key] = value.isoformat()
                else:
                    scenario_data[key] = value
        
        return scenario_data
    
    def save_scenario(self, scenario_name: str = None, override_rank: str = None) -> tuple[bool, str]:
        """
        Save current scenario to JSON file.
        
        Args:
            scenario_name: Name for the scenario. If None, auto-generates timestamp-based name.
            override_rank: Force a specific rank for the filename (bypasses session state)
        
        Returns:
            (success: bool, message: str)
        """
        if scenario_name is None:
            # Auto-generate name with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            # Use override_rank if provided, otherwise read from session state
            rank = override_rank if override_rank else st.session_state.get('user_rank', 'Unknown')
            scenario_name = f"scenario_{rank}_{timestamp}"
        
        scenario_data = self.get_scenario_data()
        scenario_data['_saved_at'] = datetime.now().isoformat()
        scenario_data['_scenario_name'] = scenario_name
        
        filepath = os.path.join(self.base_dir, f'{scenario_name}.json')
        
        try:
            with open(filepath, 'w') as f:
                json.dump(scenario_data, f, indent=2)
            
            # Update run log
            self._update_run_log(scenario_name, filepath, scenario_data)
            
            return True, f"✅ Scenario '{scenario_name}' auto-saved to JSON"
        except Exception as e:
            return False, f"❌ Error saving scenario: {str(e)}"
    
    def _update_run_log(self, scenario_name: str, filepath: str, data: dict):
        """Update the master run log with scenario metadata."""
        log_entry = {
            'scenario_name': scenario_name,
            'filepath': filepath,
            'saved_at': datetime.now().isoformat(),
            'rank': data.get('user_rank', 'Unknown'),
            'yos': data.get('user_years_of_service', 0),
            'state': data.get('user_state', 'Unknown'),
            'annual_income_civilian': data.get('annual_income_civilian', 0),
            'annual_income_military': data.get('annual_income_military', 0),
            'retirement_runway_months': data.get('retirement_runway_months', 0),
        }
        
        try:
            if os.path.exists(self.run_log_file):
                with open(self.run_log_file, 'r') as f:
                    run_log = json.load(f)
            else:
                run_log = {'scenarios': []}
            
            # Ensure 'scenarios' key exists
            if 'scenarios' not in run_log:
                run_log['scenarios'] = []
            
            run_log['scenarios'].append(log_entry)
            run_log['last_updated'] = datetime.now().isoformat()
            
            with open(self.run_log_file, 'w') as f:
                json.dump(run_log, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not update run log: {e}")
    
    def get_all_scenarios(self) -> list:
        """Get list of all saved scenarios."""
        try:
            if os.path.exists(self.run_log_file):
                with open(self.run_log_file, 'r') as f:
                    run_log = json.load(f)
                    return run_log.get('scenarios', [])
        except Exception as e:
            print(f"Error reading run log: {e}")
        return []
    
    def get_scenarios_summary(self) -> dict:
        """Get summary statistics of all saved scenarios."""
        scenarios = self.get_all_scenarios()
        
        if not scenarios:
            return {
                'total_scenarios': 0,
                'by_rank': {},
                'summary': 'No scenarios saved yet'
            }
        
        summary = {
            'total_scenarios': len(scenarios),
            'by_rank': {},
            'by_state': {},
            'average_runway_months': 0,
            'scenarios_with_positive_cashflow': 0,
        }
        
        total_runway = 0
        for scenario in scenarios:
            # By rank
            rank = scenario.get('rank', 'Unknown')
            summary['by_rank'][rank] = summary['by_rank'].get(rank, 0) + 1
            
            # By state
            state = scenario.get('state', 'Unknown')
            summary['by_state'][state] = summary['by_state'].get(state, 0) + 1
            
            # Runway tracking
            runway = scenario.get('retirement_runway_months', 0)
            if runway > 0:
                total_runway += runway
                summary['scenarios_with_positive_cashflow'] += 1
        
        if scenarios:
            summary['average_runway_months'] = round(total_runway / len(scenarios), 1)
        
        return summary
    
    def export_scenarios_csv(self, filepath: str = None) -> tuple[bool, str]:
        """
        Export all scenarios to CSV for analysis.
        
        Args:
            filepath: Path for CSV file. If None, saves to scenarios/ directory.
        
        Returns:
            (success: bool, message: str)
        """
        try:
            import csv
            
            scenarios = self.get_all_scenarios()
            if not scenarios:
                return False, "No scenarios to export"
            
            if filepath is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filepath = os.path.join(self.base_dir, f'scenarios_export_{timestamp}.csv')
            
            # Flatten scenario data for CSV
            with open(filepath, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=scenarios[0].keys())
                writer.writeheader()
                writer.writerows(scenarios)
            
            return True, f"✅ Exported {len(scenarios)} scenarios to {filepath}"
        except Exception as e:
            return False, f"❌ Error exporting CSV: {str(e)}"


def init_autosave():
    """Initialize autosave in session state."""
    if 'autosaver' not in st.session_state:
        st.session_state.autosaver = ScenarioAutoSaver()
    return st.session_state.autosaver
