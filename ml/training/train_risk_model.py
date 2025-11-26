"""
Train Random Forest Risk Classification Model
Classifies parcels into risk categories (LOW, MEDIUM, HIGH)
"""
import pandas as pd
import numpy as np
from pathlib import Path
import joblib
import json
import logging
from datetime import datetime

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score, GridSearchCV
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    confusion_matrix,
    classification_report
)
from imblearn.over_sampling import SMOTE
import matplotlib.pyplot as plt
import seaborn as sns

logger = logging.getLogger(__name__)


class RiskModelTrainer:
    """Trainer for risk classification model"""

    def __init__(self, model_dir: str = "ml/models"):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.model = None
        self.feature_names = None
        self.classes = ["LOW", "MEDIUM", "HIGH"]

    def prepare_risk_labels(self, y_yield: pd.Series, threshold_low: float = 0.7, threshold_high: float = 0.3):
        """
        Convert yield values to risk categories

        Args:
            y_yield: Actual or predicted yields
            threshold_low: Yields above this percentile are LOW risk
            threshold_high: Yields below this percentile are HIGH risk

        Returns:
            Risk category labels
        """
        # Calculate percentiles
        p_low = np.percentile(y_yield, threshold_low * 100)
        p_high = np.percentile(y_yield, threshold_high * 100)

        # Create risk categories
        risk_labels = []
        for yield_val in y_yield:
            if yield_val >= p_low:
                risk_labels.append("LOW")
            elif yield_val <= p_high:
                risk_labels.append("HIGH")
            else:
                risk_labels.append("MEDIUM")

        return np.array(risk_labels)

    def train(
        self,
        X_train: pd.DataFrame,
        y_train: np.ndarray,
        handle_imbalance: bool = True,
        optimize_hyperparams: bool = True
    ):
        """
        Train Random Forest classification model

        Args:
            X_train: Training features
            y_train: Training risk labels
            handle_imbalance: Whether to use SMOTE for class imbalance
            optimize_hyperparams: Whether to run hyperparameter optimization
        """
        logger.info("Training Random Forest risk classification model...")

        self.feature_names = list(X_train.columns)

        # Handle class imbalance with SMOTE
        if handle_imbalance:
            logger.info("Applying SMOTE for class balancing...")
            smote = SMOTE(random_state=42)
            X_train_balanced, y_train_balanced = smote.fit_resample(X_train, y_train)
            logger.info(f"Original class distribution: {pd.Series(y_train).value_counts()}")
            logger.info(f"Balanced class distribution: {pd.Series(y_train_balanced).value_counts()}")
        else:
            X_train_balanced = X_train
            y_train_balanced = y_train

        if optimize_hyperparams:
            # Hyperparameter grid
            param_grid = {
                "n_estimators": [100, 200, 300],
                "max_depth": [10, 20, 30, None],
                "min_samples_split": [2, 5, 10],
                "min_samples_leaf": [1, 2, 4],
                "max_features": ["sqrt", "log2"],
                "class_weight": ["balanced", "balanced_subsample"]
            }

            # Grid search with cross-validation
            base_model = RandomForestClassifier(random_state=42, n_jobs=-1)

            grid_search = GridSearchCV(
                base_model,
                param_grid,
                cv=5,
                scoring="f1_weighted",
                n_jobs=-1,
                verbose=1
            )

            grid_search.fit(X_train_balanced, y_train_balanced)

            self.model = grid_search.best_estimator_
            logger.info(f"Best parameters: {grid_search.best_params_}")
            logger.info(f"Best CV F1 score: {grid_search.best_score_:.4f}")

        else:
            # Train with default parameters
            self.model = RandomForestClassifier(
                n_estimators=200,
                max_depth=20,
                min_samples_split=5,
                min_samples_leaf=2,
                max_features="sqrt",
                class_weight="balanced",
                random_state=42,
                n_jobs=-1
            )

            self.model.fit(X_train_balanced, y_train_balanced)

        # Cross-validation scores
        cv_scores = cross_val_score(
            self.model, X_train_balanced, y_train_balanced,
            cv=5,
            scoring="f1_weighted"
        )

        logger.info(f"Cross-validation F1 scores: {cv_scores}")
        logger.info(f"Mean CV F1 score: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")

    def evaluate(
        self,
        X_test: pd.DataFrame,
        y_test: np.ndarray
    ) -> dict:
        """
        Evaluate model on test set

        Args:
            X_test: Test features
            y_test: Test risk labels

        Returns:
            Dictionary of evaluation metrics
        """
        logger.info("Evaluating model on test set...")

        y_pred = self.model.predict(X_test)
        y_pred_proba = self.model.predict_proba(X_test)

        # Calculate metrics
        accuracy = accuracy_score(y_test, y_pred)
        precision, recall, f1, support = precision_recall_fscore_support(
            y_test, y_pred, average="weighted"
        )

        # Per-class metrics
        precision_per_class, recall_per_class, f1_per_class, _ = precision_recall_fscore_support(
            y_test, y_pred, average=None, labels=self.classes
        )

        metrics = {
            "accuracy": accuracy,
            "precision_weighted": precision,
            "recall_weighted": recall,
            "f1_weighted": f1,
            "precision_per_class": dict(zip(self.classes, precision_per_class)),
            "recall_per_class": dict(zip(self.classes, recall_per_class)),
            "f1_per_class": dict(zip(self.classes, f1_per_class)),
        }

        logger.info(f"\nTest Accuracy: {accuracy:.4f}")
        logger.info(f"Test Precision (weighted): {precision:.4f}")
        logger.info(f"Test Recall (weighted): {recall:.4f}")
        logger.info(f"Test F1 Score (weighted): {f1:.4f}")

        logger.info("\nPer-class metrics:")
        for cls in self.classes:
            logger.info(f"  {cls}: P={metrics['precision_per_class'][cls]:.4f}, "
                       f"R={metrics['recall_per_class'][cls]:.4f}, "
                       f"F1={metrics['f1_per_class'][cls]:.4f}")

        # Classification report
        logger.info(f"\nClassification Report:\n{classification_report(y_test, y_pred)}")

        return metrics

    def plot_confusion_matrix(
        self,
        X_test: pd.DataFrame,
        y_test: np.ndarray
    ):
        """
        Plot confusion matrix

        Args:
            X_test: Test features
            y_test: Test labels
        """
        y_pred = self.model.predict(X_test)
        cm = confusion_matrix(y_test, y_pred, labels=self.classes)

        plt.figure(figsize=(8, 6))
        sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
                    xticklabels=self.classes, yticklabels=self.classes)
        plt.ylabel("Actual")
        plt.xlabel("Predicted")
        plt.title("Confusion Matrix - Risk Classification")
        plt.tight_layout()

        output_path = self.model_dir / "confusion_matrix.png"
        plt.savefig(output_path)
        logger.info(f"Saved confusion matrix to {output_path}")

    def get_feature_importance(self) -> pd.DataFrame:
        """Get feature importance"""
        importance = self.model.feature_importances_

        feature_importance = pd.DataFrame({
            "feature": self.feature_names,
            "importance": importance
        }).sort_values("importance", ascending=False)

        return feature_importance

    def plot_feature_importance(self, top_n: int = 20):
        """Plot top N most important features"""
        importance_df = self.get_feature_importance().head(top_n)

        plt.figure(figsize=(10, 8))
        plt.barh(importance_df["feature"], importance_df["importance"])
        plt.xlabel("Importance Score")
        plt.title(f"Top {top_n} Most Important Features (Risk Model)")
        plt.tight_layout()

        output_path = self.model_dir / "risk_feature_importance.png"
        plt.savefig(output_path)
        logger.info(f"Saved feature importance plot to {output_path}")

    def save_model(self, filename: str = "risk_model"):
        """Save trained model"""
        model_path = self.model_dir / f"{filename}.joblib"
        metadata_path = self.model_dir / f"{filename}_metadata.json"

        joblib.dump(self.model, model_path)
        logger.info(f"Saved model to {model_path}")

        metadata = {
            "model_type": "Random Forest Classifier",
            "training_date": datetime.now().isoformat(),
            "feature_names": self.feature_names,
            "n_features": len(self.feature_names),
            "classes": self.classes,
        }

        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Saved metadata to {metadata_path}")

    def load_model(self, filename: str = "risk_model"):
        """Load trained model"""
        model_path = self.model_dir / f"{filename}.joblib"
        metadata_path = self.model_dir / f"{filename}_metadata.json"

        self.model = joblib.load(model_path)
        logger.info(f"Loaded model from {model_path}")

        with open(metadata_path, "r") as f:
            metadata = json.load(f)
            self.feature_names = metadata["feature_names"]
            self.classes = metadata["classes"]


def main():
    """Main training pipeline"""
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
    y_yield_train = train_data[target_col]
    X_test = test_data[feature_cols]
    y_yield_test = test_data[target_col]

    # Convert yields to risk categories
    trainer = RiskModelTrainer()
    y_train = trainer.prepare_risk_labels(y_yield_train)
    y_test = trainer.prepare_risk_labels(y_yield_test)

    # Train model
    trainer.train(X_train, y_train, handle_imbalance=True, optimize_hyperparams=False)

    # Evaluate
    metrics = trainer.evaluate(X_test, y_test)

    # Visualizations
    trainer.plot_confusion_matrix(X_test, y_test)
    trainer.plot_feature_importance()

    # Save model
    trainer.save_model()

    logger.info("\n=== Training Complete ===")
    logger.info(f"Final Test F1 Score: {metrics['f1_weighted']:.4f}")


if __name__ == "__main__":
    main()
