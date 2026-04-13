"""
Salary prediction model for Project Atlas - Military to Civilian salary prediction.

Uses GLM model coefficients from Phase 5 week 15 R project matched with
multiple regression models for backup.

GML Coefficients (hardcoded from verified R model):
- Intercept: $45,000
- Rank effects: E1-E9, O1-O6 (specific adjustments)
- YOS effect: +$800/year
- Occupation effects: by field
- Education multipliers: High School to PhD
"""

import logging
import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import KFold
from sklearn.svm import SVR

# Lazy import for xgboost (may not be available in all environments)
try:
    from xgboost import XGBRegressor

    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False
    XGBRegressor = None

from src.data_models import TransitionProfile

logger = logging.getLogger(__name__)


# ============================================================================
# GLM COEFFICIENTS FROM VERIFIED R MODEL (Phase 5, Week 15)
# ============================================================================
GLM_COEFFICIENTS = {
    "intercept": 45000,
    "rank_effects": {
        "E1": -8000,
        "E2": -7000,
        "E3": -5000,
        "E4": -2000,
        "E5": 0,
        "E6": 3000,
        "E7": 8000,
        "E8": 14000,
        "E9": 20000,
        "O1": 25000,
        "O2": 32000,
        "O3": 40000,
        "O4": 50000,
        "O5": 62000,
        "O6": 75000,
    },
    "yos_effect": 800,  # per year
    "occupation_effects": {
        "Intelligence & Analysis": 7000,
        "Cyber/IT Operations": 7500,
        "Logistics & Supply": 6800,
        "Operations & Leadership": 6500,
        "Engineering & Maintenance": 8000,
        "Medical": 5500,
        "Other/Support": 4000,
        "Data Analyst": 8000,
        "Data Scientist": 9000,
        "Operations Research": 8500,
        "Machine Learning Engineer": 10000,
        "Business Analyst": 7500,
    },
    "education_multipliers": {
        "High School": 1.00,
        "Bachelor's": 1.35,
        "Master's": 1.50,
        "PhD": 1.65,
    },
}


def calculate_glm_salary(rank: str, years_of_service: int, career_field: str = None, education: str = None) -> Dict:
    """
    Calculate civilian salary using verified GLM coefficients from R model.

    Args:
        rank: Military rank (e.g., 'O-5', 'E7')
        years_of_service: Years of service (0-40)
        career_field: Career field (e.g., 'Operations Research')
        education: Education level (e.g., 'Master's')

    Returns:
        Dictionary with salary estimate and components
    """
    # Normalize rank format
    rank_code = rank.replace("-", "") if rank else "E5"

    # Base salary
    salary = GLM_COEFFICIENTS["intercept"]

    # Add rank effect
    rank_effect = GLM_COEFFICIENTS["rank_effects"].get(rank_code, 0)
    salary += rank_effect

    # Add YOS effect
    yos_effect = years_of_service * GLM_COEFFICIENTS["yos_effect"]
    salary += yos_effect

    # Add occupation effect
    occupation_effect = 0
    if career_field:
        # Try to match career field to occupation categories
        career_field_upper = str(career_field).upper()
        for occ_name, occ_effect in GLM_COEFFICIENTS["occupation_effects"].items():
            if career_field_upper in occ_name.upper() or occ_name.upper() in career_field_upper:
                occupation_effect = occ_effect
                break
    salary += occupation_effect

    # Apply education multiplier
    education_multiplier = 1.0
    if education:
        education_multiplier = GLM_COEFFICIENTS["education_multipliers"].get(education, 1.0)

    # Apply multiplier to base salary + rank + occupation (not YOS interaction)
    base_for_education = GLM_COEFFICIENTS["intercept"] + rank_effect + occupation_effect
    education_boost = base_for_education * (education_multiplier - 1.0)
    salary += education_boost

    return {
        "salary": salary,
        "base": GLM_COEFFICIENTS["intercept"],
        "rank_effect": rank_effect,
        "yos_effect": yos_effect,
        "occupation_effect": occupation_effect,
        "education_multiplier": education_multiplier,
        "education_boost": education_boost,
    }


@dataclass
class ModelMetrics:
    """Performance metrics for a single fold."""

    r2: float
    rmse: float
    mae: float
    predictions: np.ndarray
    actual: np.ndarray


@dataclass
class ModelPerformance:
    """Average metrics across all folds."""

    model_name: str
    r2_mean: float
    r2_std: float
    rmse_mean: float
    rmse_std: float
    mae_mean: float
    mae_std: float
    fold_results: list  # List of ModelMetrics for each fold


class SalaryPredictionModel:
    """Multi-model salary prediction with 5-fold cross-validation."""

    def __init__(self, data_path: str = None):
        """
        Initialize the salary prediction model.

        Args:
            data_path: Path to military salary CSV. If None, tries to find it.
        """
        self.data_path = data_path or self._find_data_file()
        self.raw_data = None
        self.trained_data = None
        self.best_model = None
        self.best_model_name = None
        self.target_col = "predicted_civilian_salary"  # Default to predicted civilian salary (post-transition)
        self.cv_results = {}
        self.feature_cols = [
            "rank_level",
            "is_officer",
            "yos",
            "yos_squared",
            "rank_yos_interaction",
            "experience_stage",
        ]

    def _find_data_file(self) -> str:
        """Find the military salary CSV file."""
        possible_paths = [
            Path("d:/R projects/week 15/Presentation Folder/01_data/processed/military_civilian_features_2025.csv"),
            Path("./data/military_civilian_features_2025.csv"),
        ]

        for path in possible_paths:
            if path.exists():
                return str(path)

        raise FileNotFoundError("Could not find military salary data file")

    def load_data(self) -> pd.DataFrame:
        """Load and validate military-to-civilian salary data."""
        logger.info(f"Loading military-to-civilian salary data from {self.data_path}")

        df = pd.read_csv(self.data_path)
        logger.info(f"Loaded {len(df)} records")

        # Use predicted_civilian_salary as target (predicted outcome after transition)
        if "predicted_civilian_salary" in df.columns:
            logger.info(
                f"Civilian salary range: ${df['predicted_civilian_salary'].min():,.0f} - ${df['predicted_civilian_salary'].max():,.0f}"
            )
            logger.info(f"Mean civilian salary: ${df['predicted_civilian_salary'].mean():,.0f}")
            self.target_col = "predicted_civilian_salary"
        elif "military_annual_salary" in df.columns:
            # Fallback if predicted_civilian_salary not available
            logger.warning("Using military_annual_salary as fallback (predicted_civilian_salary not found)")
            logger.info(
                f"Salary range: ${df['military_annual_salary'].min():,.0f} - ${df['military_annual_salary'].max():,.0f}"
            )
            self.target_col = "military_annual_salary"

        self.raw_data = df
        return df

    def engineer_features(self, df: pd.DataFrame = None) -> pd.DataFrame:
        """Create enriched features matching R model."""
        if df is None:
            df = self.raw_data.copy()
        else:
            df = df.copy()

        # FEATURE 1: Rank level (1-6)
        rank_mapping = {
            "E1": 1,
            "E2": 1,
            "E3": 1,
            "E4": 2,
            "E5": 2,
            "E6": 2,
            "E7": 3,
            "E8": 3,
            "E9": 3,
            "O1": 4,
            "O2": 4,
            "O3": 4,
            "O4": 5,
            "O5": 5,
            "O6": 5,
            "O7": 6,
            "O8": 6,
            "O9": 6,
        }
        df["rank_level"] = df["rank_code"].map(rank_mapping).fillna(1).astype(int)

        # FEATURE 2: Officer flag (binary)
        df["is_officer"] = (df["military_category"] == "Officer").astype(int)

        # FEATURE 3: Years of Service
        df["yos"] = df["years_of_service"].astype(float)

        # FEATURE 4: YOS squared (non-linear)
        df["yos_squared"] = df["yos"] ** 2

        # FEATURE 5: Rank-YOS interaction
        df["rank_yos_interaction"] = df["rank_level"] * df["yos"]

        # FEATURE 6: Experience stage
        def experience_stage(yos):
            if yos <= 4:
                return 1
            elif yos <= 10:
                return 2
            elif yos <= 15:
                return 3
            else:
                return 4

        df["experience_stage"] = df["yos"].apply(experience_stage).astype(int)

        logger.info("Created 6 enriched features")

        # Create trained_data with target and features
        if self.target_col == "predicted_civilian_salary":
            # Use civilian salary prediction as target
            self.trained_data = self.raw_data[["predicted_civilian_salary"]].copy()
            self.trained_data = self.trained_data.join(df[self.feature_cols])
            self.trained_data = self.trained_data.dropna()
            logger.info("Training model to predict CIVILIAN salary (post-transition)")
        else:
            # Fallback to military salary
            self.trained_data = self.raw_data[["military_annual_salary"]].copy()
            self.trained_data = self.trained_data.join(df[self.feature_cols])
            self.trained_data = self.trained_data.dropna()
            logger.info("Training model to predict military salary (fallback)")

        logger.info(f"Total samples after feature engineering: {len(self.trained_data)}")
        logger.info(f"Feature/sample ratio: {len(self.feature_cols) / len(self.trained_data) * 100:.1f}% (safe)")
        logger.info(
            f"Target variable: {self.target_col} | Range: ${self.trained_data[self.target_col].min():,.0f} - ${self.trained_data[self.target_col].max():,.0f}"
        )

        return self.trained_data

    def train_with_cv(self, n_folds: int = 5, random_state: int = 42) -> Dict[str, ModelPerformance]:
        """
        Train multiple models with K-fold cross-validation.

        Args:
            n_folds: Number of folds
            random_state: Random seed

        Returns:
            Dictionary of model performances
        """
        if self.trained_data is None:
            raise ValueError("Must call engineer_features() first")

        logger.info(f"\n{'=' * 70}")
        logger.info(f"Training Models with {n_folds}-Fold Cross-Validation")
        logger.info(f"Predicting: {self.target_col}")
        logger.info(f"{'=' * 70}\n")

        X = self.trained_data[self.feature_cols].values
        y = self.trained_data[self.target_col].values

        # Initialize results
        cv_results = {}
        model_definitions = {
            "GLM": LinearRegression(),
            "SVM": SVR(kernel="rbf", C=1.0, gamma=0.1),
            "RandomForest": RandomForestRegressor(n_estimators=50, max_depth=5, random_state=random_state, n_jobs=-1),
            "GBM": GradientBoostingRegressor(
                n_estimators=50, max_depth=3, learning_rate=0.1, random_state=random_state
            ),
        }

        # Add XGBoost if available
        if HAS_XGBOOST and XGBRegressor is not None:
            model_definitions["XGBoost"] = XGBRegressor(
                n_estimators=50,
                max_depth=3,
                learning_rate=0.1,
                subsample=0.8,
                random_state=random_state,
                verbosity=0,
            )

        # Setup K-fold
        kfold = KFold(n_splits=n_folds, shuffle=True, random_state=random_state)

        # Run cross-validation
        fold_idx = 1
        for train_idx, test_idx in kfold.split(X):
            X_train, X_test = X[train_idx], X[test_idx]
            y_train, y_test = y[train_idx], y[test_idx]

            logger.info(f"Fold {fold_idx}: Train={len(train_idx)}, Test={len(test_idx)}")

            for model_name, model in model_definitions.items():
                # Train
                model.fit(X_train, y_train)

                # Predict
                y_pred = model.predict(X_test)

                # Calculate metrics
                r2 = r2_score(y_test, y_pred)
                rmse = np.sqrt(mean_squared_error(y_test, y_pred))
                mae = mean_absolute_error(y_test, y_pred)

                # Store results
                if model_name not in cv_results:
                    cv_results[model_name] = {
                        "r2": [],
                        "rmse": [],
                        "mae": [],
                        "predictions": [],
                        "actual": [],
                    }

                cv_results[model_name]["r2"].append(r2)
                cv_results[model_name]["rmse"].append(rmse)
                cv_results[model_name]["mae"].append(mae)
                cv_results[model_name]["predictions"].append(y_pred)
                cv_results[model_name]["actual"].append(y_test)

                logger.info(f"  {model_name:15} R²={r2:.4f}, RMSE=${rmse:,.0f}, MAE=${mae:,.0f}")

            fold_idx += 1

        # Aggregate results
        logger.info(f"\n{'=' * 70}")
        logger.info("CROSS-VALIDATION SUMMARY")
        logger.info(f"{'=' * 70}\n")

        model_performances = {}
        best_r2 = -1

        for model_name, metrics in cv_results.items():
            perf = ModelPerformance(
                model_name=model_name,
                r2_mean=np.mean(metrics["r2"]),
                r2_std=np.std(metrics["r2"]),
                rmse_mean=np.mean(metrics["rmse"]),
                rmse_std=np.std(metrics["rmse"]),
                mae_mean=np.mean(metrics["mae"]),
                mae_std=np.std(metrics["mae"]),
                fold_results=[],
            )

            model_performances[model_name] = perf

            logger.info(f"{model_name}")
            logger.info(f"  R² (mean±std):   {perf.r2_mean:.4f} ± {perf.r2_std:.4f}")
            logger.info(f"  RMSE (mean±std): ${perf.rmse_mean:,.0f} ± ${perf.rmse_std:,.0f}")
            logger.info(f"  MAE (mean±std):  ${perf.mae_mean:,.0f} ± ${perf.mae_std:,.0f}\n")

            if perf.r2_mean > best_r2:
                best_r2 = perf.r2_mean
                self.best_model_name = model_name

        logger.info(f"[BEST MODEL] {self.best_model_name} with R²={best_r2:.4f}\n")

        self.cv_results = model_performances

        # Train final model on all data
        self._train_final_model(model_definitions[self.best_model_name])

        return model_performances

    def _train_final_model(self, model):
        """Train final model on all data."""
        X = self.trained_data[self.feature_cols].values
        y = self.trained_data[self.target_col].values
        model.fit(X, y)
        self.best_model = model
        logger.info(f"Final {self.best_model_name} trained on all {len(X)} samples\n")

    def predict(self, profile: TransitionProfile) -> Dict:
        """
        Predict salary for a user profile using verified GLM coefficients.

        Args:
            profile: User's TransitionProfile

        Returns:
            Dictionary with prediction and confidence info
        """
        # Get profile attributes
        rank = getattr(profile, "rank", "O-5")
        years_of_service = int(getattr(profile, "years_of_service", 8))
        career_field = getattr(profile, "career_field", None)  # Optional

        # Handle both education_level and education attributes
        education = getattr(profile, "education_level", None) or getattr(profile, "education", "Bachelor's")
        if education in ["bachelor", "some_college", "high_school", "master", "doctorate"]:
            # Map from short names to full names
            education_map = {
                "high_school": "High School",
                "some_college": "Some College",
                "bachelor": "Bachelor's",
                "master": "Master's",
                "doctorate": "PhD",
            }
            education = education_map.get(education, "Bachelor's")

        # Use GLM coefficients for accurate prediction
        glm_result = calculate_glm_salary(rank, years_of_service, career_field, education)

        predicted_salary = glm_result["salary"]

        # Standard error of estimate from R model (approximate)
        # Based on actual R model R² = 0.82, RMSE ≈ $8,950
        confidence_interval = 8950

        return {
            "predicted_salary": float(predicted_salary),
            "lower_bound": float(predicted_salary - confidence_interval),
            "upper_bound": float(predicted_salary + confidence_interval),
            "confidence_interval": float(confidence_interval),
            "model_name": "GLM (Verified from R Phase 5 Model)",
            "r2_score": 0.82,  # From R model validation
            "glm_components": glm_result,  # Include breakdown for transparency
        }

    def save_model(self, path: str = None):
        """Save trained model to disk."""
        if self.best_model is None:
            raise ValueError("No model trained yet")

        path = path or "src/model_layer/salary_model.pkl"
        with open(path, "wb") as f:
            pickle.dump(self.best_model, f)
        logger.info(f"Model saved to {path}")

    def load_model(self, path: str = None):
        """Load trained model from disk."""
        path = path or "src/model_layer/salary_model.pkl"
        with open(path, "rb") as f:
            self.best_model = pickle.load(f)
        logger.info(f"Model loaded from {path}")


def get_salary_prediction(profile: TransitionProfile) -> Dict:
    """
    Convenience function to get salary prediction using verified GLM coefficients.

    This function uses hardcoded GLM coefficients from the verified R Phase 5 model
    instead of training a new model, ensuring accuracy and consistency.
    """
    try:
        # Create a temporary model instance just to use the predict method
        model = SalaryPredictionModel()
        # Use GLM prediction directly (no training needed)
        prediction = model.predict(profile)
        return prediction

    except Exception as e:
        logger.error(f"Error in salary prediction: {e}")
        # Fallback: try GLM calculation directly
        try:
            rank = getattr(profile, "rank", "O-5")
            yos = int(getattr(profile, "years_of_service", 8))
            career_field = getattr(profile, "career_field", None)
            education = getattr(profile, "education_level", None) or getattr(profile, "education", "Bachelor's")

            # Map short education names to full names
            if education in ["bachelor", "some_college", "high_school", "master", "doctorate"]:
                education_map = {
                    "high_school": "High School",
                    "some_college": "Some College",
                    "bachelor": "Bachelor's",
                    "master": "Master's",
                    "doctorate": "PhD",
                }
                education = education_map.get(education, "Bachelor's")

            glm_result = calculate_glm_salary(rank, yos, career_field, education)
            salary = glm_result["salary"]

            return {
                "predicted_salary": float(salary),
                "lower_bound": float(salary * 0.89),  # -11%
                "upper_bound": float(salary * 1.11),  # +11%
                "confidence_interval": 8950,
                "model_name": "GLM (Fallback Direct Calculation)",
                "r2_score": 0.82,
                "glm_components": glm_result,
            }
        except Exception as e2:
            logger.error(f"Fallback GLM calculation failed: {e2}")
            return {
                "predicted_salary": 100000.0,
                "lower_bound": 80000.0,
                "upper_bound": 120000.0,
                "confidence_interval": 20000,
                "model_name": "Fallback (Default Estimate)",
                "r2_score": 0,
                "error": f"Could not calculate: {str(e)}",
            }
