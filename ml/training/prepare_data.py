"""
Data Preparation Pipeline for ML Models
Prepares features from satellite, weather, and parcel data
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class DataPreparationPipeline:
    """Pipeline for preparing training data"""

    def __init__(self, output_dir: str = "ml/data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def prepare_features(
        self,
        parcel_data: pd.DataFrame,
        ndvi_history: pd.DataFrame,
        weather_data: pd.DataFrame,
        soil_data: pd.DataFrame,
        yield_data: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Combine all data sources into feature matrix

        Args:
            parcel_data: Parcel characteristics (area, crop type, etc.)
            ndvi_history: Time series of NDVI values
            weather_data: Historical weather data
            soil_data: Soil properties
            yield_data: Historical yield records

        Returns:
            DataFrame with engineered features
        """
        logger.info("Preparing features from multiple data sources...")

        # Start with parcel data
        features = parcel_data.copy()

        # Add NDVI features
        ndvi_features = self._engineer_ndvi_features(ndvi_history)
        features = features.merge(ndvi_features, on="parcel_id", how="left")

        # Add weather features
        weather_features = self._engineer_weather_features(weather_data)
        features = features.merge(weather_features, on="parcel_id", how="left")

        # Add soil features
        soil_features = self._engineer_soil_features(soil_data)
        features = features.merge(soil_features, on="parcel_id", how="left")

        # Add temporal features
        features = self._add_temporal_features(features)

        # Add target variable (yield)
        features = features.merge(
            yield_data[["parcel_id", "year", "yield_tons_per_ha"]],
            on=["parcel_id", "year"],
            how="inner"
        )

        logger.info(f"Prepared {len(features)} samples with {len(features.columns)} features")

        return features

    def _engineer_ndvi_features(self, ndvi_history: pd.DataFrame) -> pd.DataFrame:
        """
        Engineer features from NDVI time series

        Features:
        - Current NDVI
        - 30-day average
        - 60-day average
        - Seasonal deviation
        - Trend (increasing/decreasing)
        - Volatility
        """
        features = []

        for parcel_id in ndvi_history["parcel_id"].unique():
            parcel_ndvi = ndvi_history[ndvi_history["parcel_id"] == parcel_id].sort_values("date")

            if len(parcel_ndvi) == 0:
                continue

            # Current NDVI (most recent)
            current_ndvi = parcel_ndvi.iloc[-1]["ndvi"]

            # Moving averages
            ndvi_30day = parcel_ndvi.iloc[-30:]["ndvi"].mean() if len(parcel_ndvi) >= 30 else current_ndvi
            ndvi_60day = parcel_ndvi.iloc[-60:]["ndvi"].mean() if len(parcel_ndvi) >= 60 else ndvi_30day

            # Seasonal average (same period last year)
            seasonal_avg = parcel_ndvi["ndvi"].mean()

            # Deviation from seasonal average
            seasonal_deviation = (current_ndvi - seasonal_avg) / (seasonal_avg + 1e-8)

            # Trend (linear regression slope over last 60 days)
            if len(parcel_ndvi) >= 60:
                recent_ndvi = parcel_ndvi.iloc[-60:]["ndvi"].values
                days = np.arange(len(recent_ndvi))
                trend = np.polyfit(days, recent_ndvi, 1)[0]
            else:
                trend = 0.0

            # Volatility (standard deviation)
            volatility = parcel_ndvi.iloc[-60:]["ndvi"].std() if len(parcel_ndvi) >= 60 else 0.0

            # Peak NDVI (maximum in growing season)
            peak_ndvi = parcel_ndvi["ndvi"].max()

            features.append({
                "parcel_id": parcel_id,
                "ndvi_current": current_ndvi,
                "ndvi_30day_avg": ndvi_30day,
                "ndvi_60day_avg": ndvi_60day,
                "ndvi_seasonal_deviation": seasonal_deviation,
                "ndvi_trend": trend,
                "ndvi_volatility": volatility,
                "ndvi_peak": peak_ndvi,
            })

        return pd.DataFrame(features)

    def _engineer_weather_features(self, weather_data: pd.DataFrame) -> pd.DataFrame:
        """
        Engineer features from weather data

        Features:
        - Cumulative precipitation (30, 60, 90 days)
        - Average temperature
        - Growing Degree Days (GDD)
        - Days without rain
        - Temperature extremes
        - Frost days
        """
        features = []

        for parcel_id in weather_data["parcel_id"].unique():
            parcel_weather = weather_data[weather_data["parcel_id"] == parcel_id].sort_values("date")

            if len(parcel_weather) == 0:
                continue

            # Cumulative precipitation
            precip_30d = parcel_weather.iloc[-30:]["precipitation"].sum() if len(parcel_weather) >= 30 else 0
            precip_60d = parcel_weather.iloc[-60:]["precipitation"].sum() if len(parcel_weather) >= 60 else 0
            precip_90d = parcel_weather.iloc[-90:]["precipitation"].sum() if len(parcel_weather) >= 90 else 0

            # Average temperature
            temp_avg_30d = parcel_weather.iloc[-30:]["temperature"].mean() if len(parcel_weather) >= 30 else 0
            temp_avg_60d = parcel_weather.iloc[-60:]["temperature"].mean() if len(parcel_weather) >= 60 else 0

            # Growing Degree Days (base 10°C, max 30°C)
            temps = parcel_weather.iloc[-90:]["temperature"] if len(parcel_weather) >= 90 else parcel_weather["temperature"]
            gdd = sum(max(0, min(t, 30) - 10) for t in temps)

            # Days without rain (consecutive)
            days_no_rain = 0
            for precip in reversed(parcel_weather.iloc[-30:]["precipitation"].values):
                if precip < 1:  # Less than 1mm considered no rain
                    days_no_rain += 1
                else:
                    break

            # Temperature extremes
            temp_max = parcel_weather.iloc[-60:]["temperature"].max() if len(parcel_weather) >= 60 else 0
            temp_min = parcel_weather.iloc[-60:]["temperature"].min() if len(parcel_weather) >= 60 else 0

            # Frost days (temp < 0°C)
            frost_days = sum(1 for t in parcel_weather.iloc[-90:]["temperature"] if t < 0)

            features.append({
                "parcel_id": parcel_id,
                "precipitation_30d": precip_30d,
                "precipitation_60d": precip_60d,
                "precipitation_90d": precip_90d,
                "temp_avg_30d": temp_avg_30d,
                "temp_avg_60d": temp_avg_60d,
                "growing_degree_days": gdd,
                "days_no_rain": days_no_rain,
                "temp_max": temp_max,
                "temp_min": temp_min,
                "frost_days": frost_days,
            })

        return pd.DataFrame(features)

    def _engineer_soil_features(self, soil_data: pd.DataFrame) -> pd.DataFrame:
        """
        Engineer features from soil data

        Features:
        - Soil type (one-hot encoded)
        - pH
        - Organic carbon
        - Texture class
        - Drainage quality
        """
        features = soil_data.copy()

        # One-hot encode soil type
        soil_dummies = pd.get_dummies(features["soil_type"], prefix="soil")
        features = pd.concat([features, soil_dummies], axis=1)

        # One-hot encode drainage
        if "drainage" in features.columns:
            drainage_dummies = pd.get_dummies(features["drainage"], prefix="drainage")
            features = pd.concat([features, drainage_dummies], axis=1)

        return features

    def _add_temporal_features(self, features: pd.DataFrame) -> pd.DataFrame:
        """
        Add temporal features

        Features:
        - Year
        - Month
        - Days since planting
        - Growing season day
        """
        if "date" in features.columns:
            features["year"] = pd.to_datetime(features["date"]).dt.year
            features["month"] = pd.to_datetime(features["date"]).dt.month
            features["day_of_year"] = pd.to_datetime(features["date"]).dt.dayofyear

        if "planting_date" in features.columns:
            features["days_since_planting"] = (
                pd.to_datetime(features["date"]) - pd.to_datetime(features["planting_date"])
            ).dt.days

        return features

    def create_train_test_split(
        self,
        features: pd.DataFrame,
        test_size: float = 0.2,
        stratify_by: Optional[str] = "year"
    ) -> tuple:
        """
        Split data into train and test sets

        Args:
            features: Feature DataFrame
            test_size: Proportion for test set
            stratify_by: Column to stratify split

        Returns:
            Tuple of (X_train, X_test, y_train, y_test)
        """
        from sklearn.model_selection import train_test_split

        # Separate features and target
        target_col = "yield_tons_per_ha"
        feature_cols = [col for col in features.columns if col not in [target_col, "parcel_id", "date"]]

        X = features[feature_cols]
        y = features[target_col]

        # Handle stratification
        stratify = features[stratify_by] if stratify_by and stratify_by in features.columns else None

        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=test_size,
            random_state=42,
            stratify=stratify
        )

        logger.info(f"Train set: {len(X_train)} samples")
        logger.info(f"Test set: {len(X_test)} samples")

        return X_train, X_test, y_train, y_test

    def save_prepared_data(
        self,
        X_train: pd.DataFrame,
        X_test: pd.DataFrame,
        y_train: pd.Series,
        y_test: pd.Series,
        filename: str = "prepared_data"
    ):
        """
        Save prepared data to disk

        Args:
            X_train: Training features
            X_test: Test features
            y_train: Training target
            y_test: Test target
            filename: Base filename for saved files
        """
        output_path = self.output_dir / filename

        # Save as CSV
        pd.concat([X_train, y_train], axis=1).to_csv(f"{output_path}_train.csv", index=False)
        pd.concat([X_test, y_test], axis=1).to_csv(f"{output_path}_test.csv", index=False)

        # Save as pickle for faster loading
        pd.concat([X_train, y_train], axis=1).to_pickle(f"{output_path}_train.pkl")
        pd.concat([X_test, y_test], axis=1).to_pickle(f"{output_path}_test.pkl")

        logger.info(f"Saved prepared data to {output_path}")


def main():
    """Main execution function"""
    # This would load actual data from database or files
    # For now, create mock data structure

    pipeline = DataPreparationPipeline()

    # Load data (mock)
    parcel_data = pd.DataFrame({
        "parcel_id": ["P001", "P002"],
        "area_hectares": [10.5, 15.2],
        "crop_type": ["maize", "wheat"],
    })

    ndvi_history = pd.DataFrame({
        "parcel_id": ["P001", "P001"],
        "date": pd.date_range("2023-01-01", periods=2),
        "ndvi": [0.7, 0.75],
    })

    weather_data = pd.DataFrame({
        "parcel_id": ["P001", "P001"],
        "date": pd.date_range("2023-01-01", periods=2),
        "temperature": [20, 22],
        "precipitation": [5, 0],
    })

    soil_data = pd.DataFrame({
        "parcel_id": ["P001", "P002"],
        "soil_type": ["loam", "clay"],
        "soil_ph": [6.5, 7.0],
        "organic_carbon": [2.5, 3.0],
    })

    yield_data = pd.DataFrame({
        "parcel_id": ["P001", "P002"],
        "year": [2023, 2023],
        "yield_tons_per_ha": [8.5, 7.2],
    })

    # Prepare features
    features = pipeline.prepare_features(
        parcel_data, ndvi_history, weather_data, soil_data, yield_data
    )

    # Split data
    X_train, X_test, y_train, y_test = pipeline.create_train_test_split(features)

    # Save
    pipeline.save_prepared_data(X_train, X_test, y_train, y_test)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
