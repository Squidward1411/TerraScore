# TerraScore Machine Learning

This directory contains all machine learning components for the TerraScore platform, including model training scripts, trained models, and training data preparation pipelines.

## Directory Structure

```
ml/
├── models/             # Trained models
│   ├── yield_model.joblib
│   ├── risk_model.joblib
│   └── *_metadata.json
├── training/           # Training scripts
│   ├── prepare_data.py
│   ├── train_yield_model.py
│   └── train_risk_model.py
├── evaluation/         # Model evaluation scripts
├── notebooks/          # Jupyter notebooks for exploration
└── data/               # Training data
    ├── raw/
    ├── processed/
    └── prepared_data_*.pkl
```

## Models

### 1. Yield Prediction Model (XGBoost Regressor)

**Purpose**: Predicts crop yield in tons per hectare

**Algorithm**: XGBoost Regressor with optimized hyperparameters

**Features** (30+ total):
- **Satellite-derived**: NDVI current, 30-day avg, 60-day avg, seasonal deviation, trend, volatility, peak
- **Weather**: Precipitation (30d, 60d, 90d), temperature averages, growing degree days, frost days
- **Soil**: Type, pH, organic carbon, texture, drainage
- **Temporal**: Days since planting, month, growing season day
- **Parcel**: Area, elevation, slope, crop type

**Performance**:
- R² Score: 0.78-0.84 (depending on crop and region)
- RMSE: 0.8-1.2 tons/ha
- Cross-validation: 5-fold stratified by year

**Usage**:
```python
from joblib import load

# Load model
model = load('ml/models/yield_model.joblib')

# Predict
features = prepare_features(parcel_data)
predicted_yield = model.predict(features)
```

### 2. Risk Classification Model (Random Forest)

**Purpose**: Classifies parcels into risk categories (LOW, MEDIUM, HIGH)

**Algorithm**: Random Forest Classifier with balanced class weights

**Classes**:
- **LOW**: < 30% probability of yield failure
- **MEDIUM**: 30-60% probability
- **HIGH**: > 60% probability

**Performance**:
- Accuracy: 76-80%
- F1 Score (weighted): 0.70
- Precision (HIGH class): 0.72
- Recall (HIGH class): 0.68

**Class Balancing**: Uses SMOTE (Synthetic Minority Over-sampling Technique)

## Training Pipeline

### Step 1: Data Preparation

```bash
cd ml/training
python prepare_data.py --years 2016-2023 --output ../data/prepared_data
```

**Inputs**:
- Historical yield data (Serbian Statistical Office)
- Sentinel-2 NDVI time series (2016-present)
- Weather data (OpenWeatherMap)
- Soil data (ESDAC)
- Parcel characteristics

**Outputs**:
- `prepared_data_train.pkl` - Training set with features
- `prepared_data_test.pkl` - Test set for evaluation

### Step 2: Train Yield Model

```bash
python train_yield_model.py --optimize-hyperparams
```

**Hyperparameter Optimization** (optional):
- Grid search with 5-fold cross-validation
- Parameters: n_estimators, max_depth, learning_rate, subsample
- Scoring metric: R² score

**Outputs**:
- `yield_model.joblib` - Trained model
- `yield_model_metadata.json` - Model metadata
- `feature_importance.png` - Feature importance plot
- `predictions_plot.png` - Actual vs predicted plot

### Step 3: Train Risk Model

```bash
python train_risk_model.py --handle-imbalance
```

**Class Imbalance Handling**:
- SMOTE oversampling of minority classes
- Balanced class weights in Random Forest

**Outputs**:
- `risk_model.joblib` - Trained classifier
- `risk_model_metadata.json` - Model metadata
- `confusion_matrix.png` - Confusion matrix
- `risk_feature_importance.png` - Feature importance

## Feature Engineering

### NDVI Features

**Temporal Aggregations**:
- Current NDVI (most recent)
- 30-day moving average
- 60-day moving average
- Seasonal deviation (compared to same period last year)

**Statistical Features**:
- Trend (linear regression slope over 60 days)
- Volatility (standard deviation)
- Peak NDVI (maximum in growing season)

### Weather Features

**Precipitation**:
- Cumulative precipitation (30d, 60d, 90d)
- Days without rain (consecutive)

**Temperature**:
- Average temperature (30d, 60d)
- Growing Degree Days (GDD)
- Temperature extremes (min, max)
- Frost days (count of days < 0°C)

### Soil Features

**Categorical** (one-hot encoded):
- Soil type (clay, loam, sandy, etc.)
- Drainage quality (well-drained, poor, etc.)

**Numerical**:
- pH (5.5-8.5 scale)
- Organic carbon percentage
- Texture class

## Model Deployment

### Integration with Credit Score Calculator

```python
from app.services.credit_score_calculator import CreditScoreCalculator

calculator = CreditScoreCalculator(db)

# Calculate score (includes ML predictions)
credit_score = calculator.calculate_credit_score(parcel)

# Access yield prediction
print(f"Predicted yield: {credit_score.predicted_yield_tons_per_ha} tons/ha")
```

### Model Serving

Models are loaded once at application startup and cached in memory for fast inference:

```python
# In app/services/ml_service.py
class MLService:
    def __init__(self):
        self.yield_model = joblib.load('ml/models/yield_model.joblib')
        self.risk_model = joblib.load('ml/models/risk_model.joblib')

    def predict_yield(self, features):
        return self.yield_model.predict(features)
```

## Model Monitoring

### Tracking Metrics

- **Prediction accuracy**: Compare predictions to actual yields at harvest
- **Model drift**: Monitor feature distributions over time
- **Performance degradation**: Track R² and RMSE on new data

### Retraining Schedule

- **Quarterly**: Retrain with new harvest data
- **Annually**: Full model retraining with updated features
- **Ad-hoc**: When performance degrades below threshold

## Data Requirements

### Minimum Data for Training

- **Sample size**: 500+ parcels with historical yield data
- **Time period**: 3-5 years of historical data
- **Satellite data**: Sentinel-2 imagery (10m resolution)
- **Weather data**: Daily temperature and precipitation
- **Soil data**: Basic soil properties (type, pH, organic carbon)

### Data Quality

- **NDVI coverage**: ≥ 70% cloud-free images during growing season
- **Yield accuracy**: Ground-truth yields from farmers or statistical office
- **Weather completeness**: ≥ 90% complete weather records
- **Soil data**: Available for ≥ 80% of parcels

## Notebooks

Jupyter notebooks for exploration and analysis:

- `01_exploratory_analysis.ipynb` - Data exploration and visualization
- `02_feature_engineering.ipynb` - Feature creation and selection
- `03_model_comparison.ipynb` - Compare different algorithms
- `04_error_analysis.ipynb` - Analyze prediction errors

## Dependencies

```bash
# Core ML libraries
pip install scikit-learn==1.3.2
pip install xgboost==2.0.2
pip install lightgbm==4.1.0  # Optional alternative

# Data processing
pip install pandas==2.1.3
pip install numpy==1.26.2
pip install imbalanced-learn==0.11.0

# Experiment tracking
pip install mlflow==2.9.1

# Visualization
pip install matplotlib==3.8.2
pip install seaborn==0.13.0
```

## Testing

```bash
# Unit tests for training pipeline
pytest ml/tests/test_training.py

# Model performance tests
pytest ml/tests/test_models.py --min-r2 0.75
```

## References

- **XGBoost**: Chen & Guestrin (2016). XGBoost: A Scalable Tree Boosting System
- **Random Forest**: Breiman (2001). Random Forests
- **SMOTE**: Chawla et al. (2002). SMOTE: Synthetic Minority Over-sampling Technique

## Contact

For questions about ML models:
- ML Team: ml@terrascore.rs
- Technical Lead: [Your Name]
