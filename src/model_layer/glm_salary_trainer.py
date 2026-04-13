"""
GLM Salary Model Trainer - Build and validate Python GLM from R training data.

This script:
1. Loads training data from R projects (2,512 records)
2. Trains a GLM model in Python using statsmodels (matches R's glm())
3. Validates on test set (1,077 records)
4. Saves the trained model for use in salary_predictor
5. Outputs coefficients and performance metrics
"""

import os
import pickle
import logging
from pathlib import Path
from typing import Tuple, Dict

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

logger = logging.getLogger(__name__)


class GLMSalaryTrainer:
    """Train GLM salary prediction model from R training data."""

    def __init__(self, training_data_path: str, test_data_path: str):
        """
        Initialize trainer with data paths.

        Args:
            training_data_path: Path to 02_training_set_CLEAN.csv
            test_data_path: Path to 02_test_set_CLEAN.csv
        """
        self.training_data_path = training_data_path
        self.test_data_path = test_data_path
        self.model = None
        self.training_data = None
        self.test_data = None

    def load_data(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Load training and test data from CSV files."""
        logger.info(f"Loading training data from {self.training_data_path}")
        self.training_data = pd.read_csv(self.training_data_path)
        logger.info(f"Training set: {len(self.training_data)} rows")

        logger.info(f"Loading test data from {self.test_data_path}")
        self.test_data = pd.read_csv(self.test_data_path)
        logger.info(f"Test set: {len(self.test_data)} rows")

        return self.training_data, self.test_data

    def prepare_data(self) -> pd.DataFrame:
        """
        Prepare data for GLM training.

        Matches R model specification:
        - Target: military_annual_salary_inflated
        - Features: rank, occupation_name, years_of_service, skill_level, civilian_category
        """
        df = self.training_data.copy()

        # Ensure required columns exist
        required_cols = [
            "rank",
            "occupation_name",
            "years_of_service",
            "skill_level",
            "civilian_category",
            "military_annual_salary_inflated",
        ]

        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        # Convert categoricals to factors (for formula)
        df["rank"] = df["rank"].astype("category")
        df["occupation_name"] = df["occupation_name"].astype("category")
        df["skill_level"] = df["skill_level"].astype("category")
        df["civilian_category"] = df["civilian_category"].astype("category")

        # Remove any rows with missing values in required columns
        df = df.dropna(subset=required_cols)
        logger.info(f"Prepared data: {len(df)} rows (after removing NAs)")

        return df

    def train_glm(self):
        """
        Train GLM model matching R specification.

        Formula: military_annual_salary_inflated ~ rank + occupation_name + years_of_service + skill_level + civilian_category
        Family: Gaussian
        Link: Identity (default for Gaussian)
        """
        logger.info("Training GLM model...")

        prepared_data = self.prepare_data()

        # GLM formula (matches R model)
        formula = (
            "military_annual_salary_inflated ~ C(rank) + C(occupation_name) + "
            "years_of_service + C(skill_level) + C(civilian_category)"
        )

        # Train GLM with Gaussian family (like R)
        self.model = smf.glm(
            formula=formula, data=prepared_data, family=sm.families.Gaussian()
        ).fit()

        logger.info("✓ GLM model trained successfully")
        logger.info(f"  AIC: {self.model.aic:.2f}")
        logger.info(f"  BIC: {self.model.bic:.2f}")

        return self.model

    def evaluate_model(self) -> Dict[str, float]:
        """
        Evaluate model performance on training and test sets.

        Returns dictionary with R², RMSE, MAE for both sets.
        """
        if self.model is None:
            raise ValueError("Model not trained yet. Call train_glm() first.")

        # Prepare test data with same transformations
        test_prepared = self.test_data.copy()
        test_prepared["rank"] = test_prepared["rank"].astype("category")
        test_prepared["occupation_name"] = test_prepared["occupation_name"].astype(
            "category"
        )
        test_prepared["skill_level"] = test_prepared["skill_level"].astype("category")
        test_prepared["civilian_category"] = test_prepared["civilian_category"].astype(
            "category"
        )
        test_prepared = test_prepared.dropna(
            subset=[
                "rank",
                "occupation_name",
                "years_of_service",
                "skill_level",
                "civilian_category",
                "military_annual_salary_inflated",
            ]
        )

        # Get predictions
        train_prepared = self.prepare_data()
        train_pred = self.model.predict(train_prepared)
        test_pred = self.model.predict(test_prepared)

        # Calculate metrics
        train_y = train_prepared["military_annual_salary_inflated"]
        test_y = test_prepared["military_annual_salary_inflated"]

        train_r2 = r2_score(train_y, train_pred)
        train_rmse = np.sqrt(mean_squared_error(train_y, train_pred))
        train_mae = mean_absolute_error(train_y, train_pred)

        test_r2 = r2_score(test_y, test_pred)
        test_rmse = np.sqrt(mean_squared_error(test_y, test_pred))
        test_mae = mean_absolute_error(test_y, test_pred)

        metrics = {
            "train_r2": train_r2,
            "train_rmse": train_rmse,
            "train_mae": train_mae,
            "test_r2": test_r2,
            "test_rmse": test_rmse,
            "test_mae": test_mae,
        }

        logger.info("\n════════════════════════════════════════════════════")
        logger.info("MODEL PERFORMANCE")
        logger.info("════════════════════════════════════════════════════")
        logger.info(f"Training - R²: {train_r2:.4f}, RMSE: ${train_rmse:,.0f}, MAE: ${train_mae:,.0f}")
        logger.info(
            f"Test     - R²: {test_r2:.4f}, RMSE: ${test_rmse:,.0f}, MAE: ${test_mae:,.0f}"
        )
        logger.info(f"Generalization gap: {(train_r2 - test_r2):+.4f}")
        logger.info("════════════════════════════════════════════════════\n")

        return metrics

    def get_coefficients_summary(self) -> Dict:
        """Get human-readable summary of model coefficients."""
        if self.model is None:
            raise ValueError("Model not trained yet. Call train_glm() first.")

        summary_dict = {
            "intercept": float(self.model.params[0]),
            "formula": (
                "military_annual_salary_inflated ~ rank + occupation_name + years_of_service + skill_level + civilian_category"
            ),
            "coefficients": {},
        }

        for param_name, param_value in self.model.params.items():
            summary_dict["coefficients"][param_name] = float(param_value)

        return summary_dict

    def save_model(self, output_path: str):
        """Save trained model to pickle file."""
        if self.model is None:
            raise ValueError("Model not trained yet. Call train_glm() first.")

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "wb") as f:
            pickle.dump(self.model, f)
        logger.info(f"✓ Model saved to {output_path}")

    def print_summary(self):
        """Print model summary."""
        if self.model is None:
            raise ValueError("Model not trained yet. Call train_glm() first.")
        print(self.model.summary())


def train_and_save_glm_model():
    """
    Main function: Train GLM and save for use in production.

    This should be run once to create the trained model.
    """
    # Paths to R training data
    r_data_dir = Path(
        "d:/R projects/week 15/Presentation Folder/ACADEMIC/01_working_notes/04_results"
    )
    training_path = r_data_dir / "02_training_set_CLEAN.csv"
    test_path = r_data_dir / "02_test_set_CLEAN.csv"

    # Verify files exist
    if not training_path.exists():
        raise FileNotFoundError(f"Training data not found: {training_path}")
    if not test_path.exists():
        raise FileNotFoundError(f"Test data not found: {test_path}")

    # Train model
    trainer = GLMSalaryTrainer(str(training_path), str(test_path))
    trainer.load_data()
    trainer.train_glm()
    trainer.evaluate_model()

    # Print summary
    trainer.print_summary()

    # Save model
    model_output = Path("d:/personal2/ProjectAtlas/src/model_layer/glm_salary_model.pkl")
    trainer.save_model(str(model_output))

    # Save coefficients summary
    coef_summary = trainer.get_coefficients_summary()
    coef_output = Path(
        "d:/personal2/ProjectAtlas/src/model_layer/glm_coefficients_summary.json"
    )
    os.makedirs(coef_output.parent, exist_ok=True)

    import json

    with open(coef_output, "w") as f:
        json.dump(coef_summary, f, indent=2)
    logger.info(f"✓ Coefficients summary saved to {coef_output}")

    logger.info("\n✓✓✓ GLM MODEL TRAINING COMPLETE ✓✓✓")
    logger.info(f"Model ready for predictions: {model_output}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    train_and_save_glm_model()
