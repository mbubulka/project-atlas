"""
Production Salary Predictor using trained GLM model.

Loads the trained Python GLM model and makes salary predictions based on military profile.
"""

import pickle
import logging
from pathlib import Path
from typing import Dict, Optional

import pandas as pd

logger = logging.getLogger(__name__)

# Global model cache
_GLM_MODEL_CACHE = None

# Rank mapping from abbreviations to full names (training data format)
RANK_MAPPING = {
    "E-1": "Private",
    "E-2": "PFC",
    "E-3": "Specialist",
    "E-4": "Sergeant",
    "E-5": "Staff Sergeant",
    "E-6": "Sgt First Class",
    "E-7": "Senior Sergeant",
    "E-8": "Master Sergeant",
    "E-9": "Sergeant Major",
    "O-1": "1st Lieutenant",
    "O-2": "2nd Lieutenant",
    "O-3": "Captain",
    "O-4": "Major",
    "O-5": "Lt Colonel",
    "O-6": "Colonel",
}

# Occupation mapping for common variations/similar roles
# Maps user-entered occupations to valid training set occupations
OCCUPATION_MAPPING = {
    "Operations Research": "Cyber Operational Intelligence Analyst",
    "Operations Research Analyst": "Cyber Operational Intelligence Analyst",
    "Data Analyst": "Data Network Technician",
    "Data Analytics": "Data Network Technician",
    "Data Scientist": "Intelligence Analyst",
    "Software Engineer": "Information Technology Specialist",
    "IT Specialist": "Information Technology Specialist",
    "Communications": "Communications Technician",
    "Supply Officer": "Supply Systems Technician",
    "Logistics Officer": "Logistics Readiness Officer",
    "Medical Officer": "Hospital Corpsman",
    "Healthcare": "Hospital Corpsman",
    "Cybersecurity": "Cyber Warfare Operator",
    "Cyber": "Cyber Operations Specialist",
    "Intelligence": "Intelligence Analyst",
    "HR": "Human Resources Specialist",
    "Human Resources": "Human Resources Specialist",
    # Trades and technical roles
    "Welder": "Maintenance Technician",
    "Mechanic": "Maintenance Technician",
    "Maintenance": "Maintenance Technician",
    "Electrician": "Electronics Technician",
    "HVAC": "Maintenance Technician",
    "Plumbing": "Maintenance Technician",
    "Construction": "Construction Equipment Operator",
    "Carpenter": "Construction Equipment Operator",
    # Additional common titles
    "Analyst": "Intelligence Analyst",
    "Engineer": "Information Technology Specialist",
    "Technician": "Electronics Technician",
    "Specialist": "Information Technology Specialist",
    "Officer": "Logistics Readiness Officer",
    "Manager": "Logistics Readiness Officer",
    "Supervisor": "Logistics Readiness Officer",
    "Administrator": "Human Resources Specialist",
}

# Skill level mapping - maps education levels, experience levels, and other inputs to valid skill
# levels
# Valid skill levels in training data: Administrative, Analytical, Management, Medical, Operations,
# Technical
SKILL_LEVEL_MAPPING = {
    # Education levels
    "High School": "Administrative",
    "HS": "Administrative",
    "Bachelor's": "Analytical",
    "Bachelor": "Analytical",
    "BS": "Analytical",
    "BA": "Analytical",
    "Master's": "Analytical",
    "Master": "Analytical",
    "MS": "Analytical",
    "MA": "Analytical",
    "PhD": "Technical",
    "Doctorate": "Technical",
    # Experience levels
    "Beginner": "Administrative",
    "Junior": "Administrative",
    "Intermediate": "Analytical",
    "Senior": "Technical",
    "Advanced": "Technical",
    "Expert": "Technical",
    "Leadership": "Management",
    "Manager": "Management",
}

# Civilian category mapping - maps common job titles/types to valid training categories
# Valid categories: Communications, Cybersecurity, Engineering, Healthcare, HR/Administration,
# Intelligence, IT/Tech, Leadership, Logistics, Operations, Technical, Transportation
CIVILIAN_CATEGORY_MAPPING = {
    "Analyst": "Intelligence",
    "Analytics": "Intelligence",
    "Data Analyst": "IT/Tech",
    "Data Science": "IT/Tech",
    "Data Scientist": "IT/Tech",
    "Engineer": "Engineering",
    "Software Engineer": "IT/Tech",
    "IT": "IT/Tech",
    "Technology": "IT/Tech",
    "Tech": "IT/Tech",
    "Cybersecurity": "Cybersecurity",
    "Security": "Cybersecurity",
    "Intelligence": "Intelligence",
    "Leadership": "Leadership",
    "Management": "Leadership",
    "Manager": "Leadership",
    "HR": "HR/Administration",
    "Human Resources": "HR/Administration",
    "Administration": "HR/Administration",
    "Healthcare": "Healthcare",
    "Medical": "Healthcare",
    "Health": "Healthcare",
    "Logistics": "Logistics",
    "Supply Chain": "Logistics",
    "Operations": "Operations",
    "Communications": "Communications",
    "Transport": "Transportation",
    "Transportation": "Transportation",
}


def normalize_rank(rank: str) -> str:
    """
    Convert rank abbreviation to full name used in training data.
    
    Args:
        rank: Rank in either format ('O-5', 'O5', 'Lt Colonel', etc.)
    
    Returns:
        Rank in full name format matching training data
    """
    # Try direct lookup first (handles 'O-5', 'E-7', etc.)
    if rank in RANK_MAPPING:
        return RANK_MAPPING[rank]
    
    # Try without dash (handles 'O5', 'E7', etc.)
    rank_with_dash = rank[0] + "-" + rank[1:] if len(rank) > 1 else rank
    if rank_with_dash in RANK_MAPPING:
        return RANK_MAPPING[rank_with_dash]
    
    # If not found, assume it's already in full name format
    if rank in ["Private", "PFC", "Specialist", "Sergeant", "Staff Sergeant", 
                "Sgt First Class", "Senior Sergeant", "Master Sergeant", "Sergeant Major",
                "1st Lieutenant", "2nd Lieutenant", "Captain", "Major", "Lt Colonel", "Colonel"]:
        return rank
    
    # Default: return as-is (will cause error if not in training data)
    logger.warning(f"Unknown rank format: {rank}. Attempting direct usage.")
    return rank


def normalize_occupation(occupation: str) -> str:
    """
    Map user-entered occupation to a valid training set occupation.
    
    Handles variations and similar role names. If not found in mapping,
    returns the occupation as-is (will use exact match from training set).
    
    Args:
        occupation: Occupation name (may not match training set exactly)
    
    Returns:
        Occupation name that exists in training set
    """
    # Direct match - occupation is already valid
    if occupation in [
        "Aerospace Medical Technician", "Air Battle Manager", "Ammunition Specialist",
        "Automated Logistical Specialist", "Avionics Flight Test Technician",
        "Combat Medic", "Communications and Information Officer", "Communications Technician",
        "Cyber Operational Intelligence Analyst", "Cyber Operations Specialist",
        "Cyber Warfare Operations Specialist", "Cyber Warfare Operator",
        "Data Network Technician", "Engineman", "Hospital Corpsman",
        "Human Resources Officer", "Human Resources Specialist",
        "Information Technology Specialist", "Intelligence Analyst", "Intelligence Officer",
        "Intelligence Specialist", "Inventory Management Specialist",
        "Logistics Readiness Officer", "Machinery Repairman", "Medical Laboratory Specialist",
        "Motor Transport Operator", "Operating Room Technician", "Personnel Specialist",
        "Radar Repairer", "Rifleman/Infantry", "Signal Support Specialist",
        "Signals Intelligence Technician", "Strike Warfare Officer", "Supply Systems Technician",
        "Surface Warfare Officer (SWO)", "Unit Supply Specialist"
    ]:
        return occupation
    
    # Check mapping dictionary
    if occupation in OCCUPATION_MAPPING:
        mapped = OCCUPATION_MAPPING[occupation]
        logger.info(f"Mapped occupation '{occupation}' → '{mapped}'")
        return mapped
    
    # Check partial matches in mapping (case-insensitive)
    occupation_lower = occupation.lower()
    for key, value in OCCUPATION_MAPPING.items():
        if key.lower() in occupation_lower or occupation_lower in key.lower():
            logger.info(f"Fuzzy matched occupation '{occupation}' → '{value}'")
            return value
    
    # No match found - use a sensible default based on the input
    # Try to infer from keywords in the occupation name
    occupation_lower = occupation.lower()
    
    if any(word in occupation_lower for word in ["tech", "engineer", "software", "it", "coding", "developer"]):
        logger.warning(f"Occupation '{occupation}' → defaulting to 'Information Technology Specialist'")
        return "Information Technology Specialist"
    elif any(word in occupation_lower for word in ["analyst", "data", "analytics", "intel", "analysis"]):
        logger.warning(f"Occupation '{occupation}' → defaulting to 'Intelligence Analyst'")
        return "Intelligence Analyst"
    elif any(word in occupation_lower for word in ["mechanic", "repair", "maintain", "weld", "hvac", "electric"]):
        logger.warning(f"Occupation '{occupation}' → defaulting to 'Maintenance Technician'")
        return "Maintenance Technician"
    elif any(word in occupation_lower for word in ["health", "medical", "nurse", "doctor", "hospital"]):
        logger.warning(f"Occupation '{occupation}' → defaulting to 'Hospital Corpsman'")
        return "Hospital Corpsman"
    elif any(word in occupation_lower for word in ["supply", "logistics", "warehouse", "inventory"]):
        logger.warning(f"Occupation '{occupation}' → defaulting to 'Supply Systems Technician'")
        return "Supply Systems Technician"
    elif any(word in occupation_lower for word in ["hr", "human resource", "admin", "office"]):
        logger.warning(f"Occupation '{occupation}' → defaulting to 'Human Resources Specialist'")
        return "Human Resources Specialist"
    else:
        # Final fallback to a neutral technical role
        logger.warning(
            f"Occupation '{occupation}' not recognized. "
            f"Using 'Information Technology Specialist' as default."
        )
        return "Information Technology Specialist"


def normalize_skill_level(skill_level: str) -> str:
    """
    Map user-entered skill level to a valid training set skill level.
    
    Valid levels in training data: Administrative, Analytical, Management, Medical, Operations, Technical
    
    Handles education levels, experience levels, and other inputs.
    
    Args:
        skill_level: Skill level (may be education level like "Master's" or experience level like "Senior")
    
    Returns:
        Skill level that exists in training set
    """
    # Direct match - already valid
    if skill_level in ["Administrative", "Analytical", "Management", "Medical", "Operations", "Technical"]:
        return skill_level
    
    # Check mapping dictionary (case-insensitive)
    skill_level_lower = skill_level.lower()
    
    if skill_level in SKILL_LEVEL_MAPPING:
        mapped = SKILL_LEVEL_MAPPING[skill_level]
        logger.info(f"Mapped skill level '{skill_level}' → '{mapped}'")
        return mapped
    
    # Check case-insensitive match
    for key, value in SKILL_LEVEL_MAPPING.items():
        if key.lower() == skill_level_lower:
            logger.info(f"Mapped skill level '{skill_level}' → '{value}'")
            return value
    
    # Check partial matches
    for key, value in SKILL_LEVEL_MAPPING.items():
        if key.lower() in skill_level_lower or skill_level_lower in key.lower():
            logger.info(f"Fuzzy matched skill level '{skill_level}' → '{value}'")
            return value
    
    # Default to Analytical if no match found
    logger.warning(
        f"Skill level '{skill_level}' not in mapping. Defaulting to 'Analytical'."
    )
    return "Analytical"


def normalize_civilian_category(civilian_category: str) -> str:
    """
    Map user-entered civilian category to a valid training set category.
    
    Valid categories in training data: Communications, Cybersecurity, Engineering, Healthcare, 
    HR/Administration, Intelligence, IT/Tech, Leadership, Logistics, Operations, Technical, Transportation
    
    Args:
        civilian_category: Job category or title (e.g., 'Analyst', 'Engineer', 'IT')
    
    Returns:
        Civilian category that exists in training set
    """
    # Direct match - already valid
    if civilian_category in [
        "Communications", "Cybersecurity", "Engineering", "Healthcare",
        "HR/Administration", "Intelligence", "IT/Tech", "Leadership",
        "Logistics", "Operations", "Technical", "Transportation"
    ]:
        return civilian_category
    
    # Check mapping dictionary (case-insensitive)
    category_lower = civilian_category.lower()
    
    if civilian_category in CIVILIAN_CATEGORY_MAPPING:
        mapped = CIVILIAN_CATEGORY_MAPPING[civilian_category]
        logger.info(f"Mapped civilian category '{civilian_category}' → '{mapped}'")
        return mapped
    
    # Check case-insensitive match
    for key, value in CIVILIAN_CATEGORY_MAPPING.items():
        if key.lower() == category_lower:
            logger.info(f"Mapped civilian category '{civilian_category}' → '{value}'")
            return value
    
    # Check partial matches
    for key, value in CIVILIAN_CATEGORY_MAPPING.items():
        if key.lower() in category_lower or category_lower in key.lower():
            logger.info(f"Fuzzy matched civilian category '{civilian_category}' → '{value}'")
            return value
    
    # Default to Intelligence if no match found
    logger.warning(
        f"Civilian category '{civilian_category}' not in mapping. Defaulting to 'Intelligence'."
    )
    return "Intelligence"


def load_glm_model():
    """Load the trained GLM model from pickle file."""
    global _GLM_MODEL_CACHE

    if _GLM_MODEL_CACHE is not None:
        return _GLM_MODEL_CACHE

    model_path = Path(__file__).parent / "glm_salary_model.pkl"

    if not model_path.exists():
        raise FileNotFoundError(
            f"Trained GLM model not found at {model_path}. "
            f"Run glm_salary_trainer.py to train the model first."
        )

    try:
        with open(model_path, "rb") as f:
            _GLM_MODEL_CACHE = pickle.load(f)
        logger.info(f"✓ Loaded trained GLM model")
        return _GLM_MODEL_CACHE
    except Exception as e:
        logger.error(f"Failed to load GLM model: {e}")
        raise


def predict_salary_glm(
    rank: str,
    occupation: str,
    years_of_service: int,
    skill_level: str = "Intermediate",
    civilian_category: str = "Analyst",
) -> Dict[str, float]:
    """
    Predict civilian salary using trained GLM model.

    Args:
        rank: Military rank (e.g., 'O-5', 'O5', 'Lt Colonel')
        occupation: Occupation name (e.g., 'Intelligence Officer', 'Data Analyst')
        years_of_service: Years of military service (0-40)
        skill_level: Skill level ('Beginner', 'Intermediate', 'Advanced', 'Expert')
        civilian_category: Civilian job category (e.g., 'Analyst', 'Engineer', 'Manager')

    Returns:
        Dictionary with predicted salary and confidence interval
    """
    try:
        model = load_glm_model()

        # Normalize rank to full name format
        rank_normalized = normalize_rank(rank)
        
        # Normalize occupation to match training set
        occupation_normalized = normalize_occupation(occupation)
        
        # Normalize skill level to match training set
        skill_level_normalized = normalize_skill_level(skill_level)
        
        # Normalize civilian category to match training set
        civilian_category_normalized = normalize_civilian_category(civilian_category)

        # Create prediction input dataframe (must match training format)
        prediction_data = pd.DataFrame(
            {
                "rank": [rank_normalized],
                "occupation_name": [occupation_normalized],
                "years_of_service": [years_of_service],
                "skill_level": [skill_level_normalized],
                "civilian_category": [civilian_category_normalized],
            }
        )

        # Ensure categorical dtypes match training
        prediction_data["rank"] = prediction_data["rank"].astype("category")
        prediction_data["occupation_name"] = prediction_data["occupation_name"].astype(
            "category"
        )
        prediction_data["skill_level"] = prediction_data["skill_level"].astype(
            "category"
        )
        prediction_data["civilian_category"] = prediction_data[
            "civilian_category"
        ].astype("category")

        # Make prediction
        predicted_salary = float(model.predict(prediction_data)[0])

        # Get standard error for confidence interval estimation
        predictions = model.get_prediction(prediction_data)
        prediction_summary = predictions.summary_frame(alpha=0.05)
        std_err = float(prediction_summary["mean_se"][0])

        # Calculate 95% CI (±1.96 * std_err)
        ci_lower = predicted_salary - 1.96 * std_err
        ci_upper = predicted_salary + 1.96 * std_err

        logger.info(
            f"Predicted salary for {rank_normalized} {occupation_normalized} (mapped from '{occupation}', skill: '{skill_level_normalized}'): ${predicted_salary:,.0f}"
        )

        return {
            "salary": max(0, predicted_salary),  # Ensure non-negative
            "ci_lower": max(0, ci_lower),
            "ci_upper": ci_upper,
            "std_error": std_err,
        }

    except Exception as e:
        logger.error(f"Error predicting salary: {e}")
        raise


def get_salary_range(
    rank: str,
    occupation: str,
    years_of_service: int,
    skill_level: str = "Intermediate",
    civilian_category: str = "Analyst",
    percentile_low: float = 0.15,
    percentile_high: float = 0.15,
) -> Dict[str, float]:
    """
    Get salary range using GLM prediction with confidence interval.

    Args:
        rank: Military rank
        occupation: Occupation name
        years_of_service: Years of service
        skill_level: Skill level
        civilian_category: Civilian category
        percentile_low: Percentage below predicted (default 15% = conservative)
        percentile_high: Percentage above predicted (default 15% = optimistic)

    Returns:
        Dictionary with low, mid, high salary estimates based on prediction ± percentages
    """
    prediction = predict_salary_glm(
        rank, occupation, years_of_service, skill_level, civilian_category
    )

    mid_salary = prediction["salary"]
    low_salary = mid_salary * (1 - percentile_low)  # Conservative: 15% below
    high_salary = mid_salary * (1 + percentile_high)  # Optimistic: 15% above

    return {
        "low": low_salary,
        "mid": mid_salary,
        "high": high_salary,
        "ci_lower": prediction["ci_lower"],
        "ci_upper": prediction["ci_upper"],
    }


if __name__ == "__main__":
    # Test predictions
    logging.basicConfig(level=logging.INFO)

    # Example: O-5 Intelligence Officer with 20 YOS
    # Using valid categorical values from training data:
    # Skill levels: 'Administrative', 'Analytical', 'Management', 'Medical', 'Operations',
    # 'Technical'
    # Categories: 'Communications', 'Cybersecurity', 'Engineering', 'HR/Administration',
    # 'Healthcare',
    # 'IT/Tech', 'Intelligence', 'Leadership', 'Logistics', 'Operations', 'Technical',
    # 'Transportation'
    
    result = predict_salary_glm(
        rank="O-5",
        occupation="Intelligence Officer",
        years_of_service=20,
        skill_level="Analytical",  # Use valid value from training data
        civilian_category="Intelligence",  # Use valid value from training data
    )

    print(f"\nPredicted salary: ${result['salary']:,.0f}")
    print(f"95% CI: ${result['ci_lower']:,.0f} - ${result['ci_upper']:,.0f}")

    # Get range
    range_result = get_salary_range("O-5", "Intelligence Officer", 20, 
                                     skill_level="Analytical", 
                                     civilian_category="Intelligence")
    print(f"\nSalary Range:")
    print(f"  Conservative (25%): ${range_result['low']:,.0f}")
    print(f"  Predicted (Mid): ${range_result['mid']:,.0f}")
    print(f"  Optimistic (75%): ${range_result['high']:,.0f}")
