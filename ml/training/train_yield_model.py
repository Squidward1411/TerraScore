"""
Train XGBoost Yield Prediction Model
Predicts crop yield in tons per hectare
"""
import pandas as pd
import numpy as np
from pathlib import Path
import joblib
import json
import logging
from datetime import datetime

from xgboost import XGBRegressor
from sklearn.model_selection import cross_val_score, GridSearchCV
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)


class YieldModelTrainer:
    """Trainer for yield prediction model"""

    def __init__(self, model_dir: str = "ml/models"):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.model = None
        self.feature_names = None

    def train(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        optimize_hyperparams: bool = True
    ):
        """
        Train XGBoost regression model

        Args:
            X_train: Training features
            y_train: Training target (yield)
            optimize_hyperparams: Whether to run hyperparameter optimization
        """
        logger.info("Training XGBoost yield prediction model...")

        self.feature_names = list(X_train.columns)

        if optimize_hyperparams:
            # Hyperparameter grid
            param_grid = {
                "n_estimators": [100, 200, 300],
                "max_depth": [3, 5, 7],
                "learning_rate": [0.01, 0.05, 0.1],
                "subsample": [0.8, 0.9, 1.0],
                "colsample_bytree": [0.8, 0.9, 1.0],
                "min_child_weight": [1, 3, 5],
            }

            # Grid search with cross-validation
            base_model = XGBRegressor(
                objective="reg:squarederror",
                random_state=42,
                n_jobs=-1
            )

            grid_search = GridSearchCV(
                base_model,
                param_grid,
                cv=5,
                scoring="r2",
                n_jobs=-1,
                verbose=1
            )

            grid_search.fit(X_train, y_train)

            self.model = grid_search.best_estimator_
            logger.info(f"Best parameters: {grid_search.best_params_}")
            logger.info(f"Best CV R² score: {grid_search.best_score_:.4f}")

        else:
            # Train with default parameters
            self.model = XGBRegressor(
                n_estimators=200,
                max_depth=5,
                learning_rate=0.05,
                subsample=0.9,
                colsample_bytree=0.9,
                min_child_weight=3,
                objective="reg:squarederror",
                random_state=42,
                n_jobs=-1
            )

            self.model.fit(X_train, y_train)

        # Cross-validation scores
        cv_scores = cross_val_score(
            self.model, X_train, y_train,
            cv=5,
            scoring="r2"
        )

        logger.info(f"Cross-validation R² scores: {cv_scores}")
        logger.info(f"Mean CV R² score: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")

    def evaluate(
        self,
        X_test: pd.DataFrame,
        y_test: pd.Series
    ) -> dict:
        """
        Evaluate model on test set

        Args:
            X_test: Test features
            y_test: Test target

        Returns:
            Dictionary of evaluation metrics
        """
        logger.info("Evaluating model on test set...")

        y_pred = self.model.predict(X_test)

        metrics = {
            "r2_score": r2_score(y_test, y_pred),
            "rmse": np.sqrt(mean_squared_error(y_test, y_pred)),
            "mae": mean_absolute_error(y_test, y_pred),
            "mape": np.mean(np.abs((y_test - y_pred) / y_test)) * 100,
        }

        logger.info(f"Test R² Score: {metrics['r2_score']:.4f}")
        logger.info(f"Test RMSE: {metrics['rmse']:.4f} tons/ha")
        logger.info(f"Test MAE: {metrics['mae']:.4f} tons/ha")
        logger.info(f"Test MAPE: {metrics['mape']:.2f}%")

        return metrics

    def get_feature_importance(self) -> pd.DataFrame:
        """
        Get feature importance from trained model

        Returns:
            DataFrame with feature names and importance scores
        """
        importance = self.model.feature_importances_

        feature_importance = pd.DataFrame({
            "feature": self.feature_names,
            "importance": importance
        }).sort_values("importance", ascending=False)

        return feature_importance

    def plot_feature_importance(self, top_n: int = 20):
        """
        Plot top N most important features

        Args:
            top_n: Number of top features to plot
        """
        importance_df = self.get_feature_importance().head(top_n)

        plt.figure(figsize=(10, 8))
        plt.barh(importance_df["feature"], importance_df["importance"])
        plt.xlabel("Importance Score")
        plt.title(f"Top {top_n} Most Important Features")
        plt.tight_layout()

        output_path = self.model_dir / "feature_importance.png"
        plt.savefig(output_path)
        logger.info(f"Saved feature importance plot to {output_path}")

    def plot_predictions(
        self,
        X_test: pd.DataFrame,
        y_test: pd.Series
    ):
        """
        Plot actual vs predicted yields

        Args:
            X_test: Test features
            y_test: Actual test yields
        """
        y_pred = self.model.predict(X_test)

        plt.figure(figsize=(10, 6))
        plt.scatter(y_test, y_pred, alpha=0.5)
        plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--', lw=2)
        plt.xlabel("Actual Yield (tons/ha)")
        plt.ylabel("Predicted Yield (tons/ha)")
        plt.title("Actual vs Predicted Crop Yield")
        plt.tight_layout()

        output_path = self.model_dir / "predictions_plot.png"
        plt.savefig(output_path)
        logger.info(f"Saved predictions plot to {output_path}")

    def save_model(self, filename: str = "yield_model"):
        """
        Save trained model to disk

        Args:
            filename: Base filename for model and metadata
        """
        model_path = self.model_dir / f"{filename}.joblib"
        metadata_path = self.model_dir / f"{filename}_metadata.json"

        # Save model
        joblib.dump(self.model, model_path)
        logger.info(f"Saved model to {model_path}")

        # Save metadata
        metadata = {
            "model_type": "XGBoost Regressor",
            "training_date": datetime.now().isoformat(),
            "feature_names": self.feature_names,
            "n_features": len(self.feature_names),
        }

        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Saved metadata to {metadata_path}")

    def load_model(self, filename: str = "yield_model"):
        """
        Load trained model from disk

        Args:
            filename: Base filename of saved model
        """
        model_path = self.model_dir / f"{filename}.joblib"
        metadata_path = self.model_dir / f"{filename}_metadata.json"

        self.model = joblib.load(model_path)
        logger.info(f"Loaded model from {model_path}")

        with open(metadata_path, "r") as f:
            metadata = json.load(f)
            self.feature_names = metadata["feature_names"]

        logger.info(f"Loaded metadata from {metadata_path}")


def main():
    """Main training pipeline"""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Load prepared data
    data_dir = Path("ml/data")
    train_data = pd.read_pickle(data_dir / "prepared_data_train.pkl")
    test_data = pd.read_pickle(data_dir / "prepared_data_test.pkl")

    # Separate features and target
    target_col = "yield_tons_per_ha"
    feature_cols = [col for col in train_data.columns if col != target_col]

    X_train = train_data[feature_cols]
    y_train = train_data[target_col]
    X_test = test_data[feature_cols]
    y_test = test_data[target_col]

    # Initialize trainer
    trainer = YieldModelTrainer()

    # Train model
    trainer.train(X_train, y_train, optimize_hyperparams=False)

    # Evaluate
    metrics = trainer.evaluate(X_test, y_test)

    # Feature importance
    importance = trainer.get_feature_importance()
    logger.info(f"\nTop 10 most important features:\n{importance.head(10)}")

    # Plot results
    trainer.plot_feature_importance()
    trainer.plot_predictions(X_test, y_test)

    # Save model
    trainer.save_model()

    logger.info("\n=== Training Complete ===")
    logger.info(f"Final Test R² Score: {metrics['r2_score']:.4f}")
    logger.info(f"Final Test RMSE: {metrics['rmse']:.4f} tons/ha")


if __name__ == "__main__":
    main()
