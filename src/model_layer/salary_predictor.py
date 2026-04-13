"""
Salary prediction model for Project Atlas.

This module provides salary prediction functionality. For the MVP, it accepts
the user's input directly. Long-term: This is where we integrate the GLM model
or subprocess calls to R.
"""

import json
import logging
import os
import subprocess
import tempfile
from pathlib import Path

from src.data_models import TransitionProfile

logger = logging.getLogger(__name__)


def predict_salary(profile: TransitionProfile) -> TransitionProfile:
    """
    Predict the user's post-military salary.

    MVP approach: Uses the user's input (estimated_annual_salary) directly.

    Long-term approaches:
    1. Integrate a local GLM model trained on military-to-civilian salary data.
    2. Use subprocess to call an R script with the user's profile details.
    3. Connect to an external API or database.

    Args:
        profile (TransitionProfile): User's transition profile.

    Returns:
        TransitionProfile: Updated profile with predicted_salary filled in.
                          For MVP, this equals estimated_annual_salary.

    Raises:
        ValueError: If the estimated_annual_salary is invalid.
    """

    if profile.estimated_annual_salary < 0:
        raise ValueError(f"Estimated annual salary must be non-negative, " f"got {profile.estimated_annual_salary}")

    # MVP: Simply accept the user's estimate
    predicted_salary = profile.estimated_annual_salary

    logger.info(f"Salary prediction for {profile.user_name}: ${predicted_salary:,.2f}/year")

    # Store in profile metadata for future debugging
    if not hasattr(profile, "metadata"):
        profile.metadata = {}
    profile.metadata["salary_prediction_method"] = "user_estimate"

    return profile


def predict_salary_with_r_model(profile: TransitionProfile, r_script_path: str) -> TransitionProfile:
    """
    Predict salary using an external R GLM model.

    This function demonstrates how to integrate your R model:
    1. Serialize the profile to a temp CSV
    2. Call the R script as a subprocess
    3. Read the result back

    Args:
        profile (TransitionProfile): User's profile.
        r_script_path (str): Path to the R script that performs prediction.
                            The script should:
                            - Read a CSV from a temp location
                            - Output a JSON file with 'predicted_salary' key

    Returns:
        TransitionProfile: Updated profile with prediction result.

    Raises:
        FileNotFoundError: If R script not found.
        RuntimeError: If R execution fails.
    """

    if not os.path.exists(r_script_path):
        raise FileNotFoundError(f"R script not found: {r_script_path}")

    # Check if R is available
    try:
        subprocess.run(["Rscript", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        raise RuntimeError("Rscript not found. Ensure R is installed and in PATH.")

    try:
        # Create temporary directory for data exchange
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "profile_input.csv"
            output_path = Path(tmpdir) / "prediction_output.json"

            # Write profile to CSV
            profile_data = {
                "rank": profile.rank,
                "years_of_service": profile.years_of_service,
                "target_city": profile.target_city,
                "service_branch": profile.service_branch,
            }

            import csv

            with open(input_path, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=profile_data.keys())
                writer.writeheader()
                writer.writerow(profile_data)

            logger.info(f"Wrote profile input to {input_path}")

            # Call R script
            cmd = ["Rscript", r_script_path, str(input_path), str(output_path)]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                raise RuntimeError(f"R script failed: {result.stderr}")

            # Read result
            if not output_path.exists():
                raise RuntimeError("R script did not produce output file")

            with open(output_path, "r") as f:
                output = json.load(f)

            predicted_salary = output.get("predicted_salary", profile.estimated_annual_salary)

            logger.info(f"R model prediction: ${predicted_salary:,.2f}/year")

            profile.estimated_annual_salary = predicted_salary
            profile.metadata["salary_prediction_method"] = "r_glm_model"

            return profile

    except subprocess.TimeoutExpired:
        logger.warning("R script timed out; using user estimate.")
        return profile
    except Exception as e:
        logger.error(f"Error calling R model: {e}. Using user estimate.")
        return profile


def estimate_salary_range(
    profile: TransitionProfile, low_percentile: float = 0.25, high_percentile: float = 0.75
) -> dict:
    """
    Estimate a salary range (low/mid/high scenarios).

    Useful for sensitivity analysis.

    Args:
        profile (TransitionProfile): User's profile.
        low_percentile (float): Multiplier for conservative estimate.
        high_percentile (float): Multiplier for optimistic estimate.

    Returns:
        dict: Contains 'low', 'mid', 'high' salary estimates.
    """

    mid = profile.estimated_annual_salary
    low = mid * low_percentile
    high = mid * high_percentile

    return {
        "low": low,
        "mid": mid,
        "high": high,
    }
