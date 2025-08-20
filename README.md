# Air Quality Prediction
An end-to-end MLOps system that predicts PM2.5 air quality levels in Los Angeles using real-time weather data, built with AWS SageMaker and serverless architecture.

## Data Source
The data used for this project is being retrieved from the [Visual Crossing Weather API](https://www.visualcrossing.com/weather-api) and [World Air Quality Index API](https://aqicn.org/api/). The historical data was retrieved from [here](https://aqicn.org/historical) where you can download CSVs from a specific city or station.

## Prediction Problem
This is a **regression problem** that predicts PM2.5 air quality levels (µg/m³) based on weather conditions. The model uses 7 weather features to predict air quality:

- **Target Variable**: PM2.5 concentration (µg/m³)
- **Features**: Temperature, Humidity, Precipitation, Wind Speed, Cloud Cover, Visibility, Solar Radiation
- **Model**: XGBoost Regressor
- **Training Data**: 1,836 historical records

## Architecture
This project implements a complete MLOps pipeline using AWS services:

```
Weather APIs → Lambda → Feature Store → Training → Model → Endpoint → Streamlit App
```

### Feature Pipelines
**Serverless Feature Pipeline (AWS Lambda)**
- Fetches real-time weather data from Visual Crossing API
- Retrieves air quality data from WAQI API
- Processes and validates features
- Stores data in SageMaker Feature Store
- Scheduled execution via EventBridge (hourly)

### Training Pipeline
**Automated Model Training**
- Queries Feature Store data via Athena
- Prepares training dataset (1,836 records)
- Trains XGBoost model using SageMaker Training Jobs
- Stores model artifacts in S3

### Inference Pipeline
**Real-time Predictions**
- Deployed XGBoost model on SageMaker Endpoint
- REST API for real-time predictions
- Streamlit dashboard for interactive predictions
- Instance: ml.m5.large for reliable hosting

## Project Structure
```
AQI-Prediction/
├── src/
│   ├── lambda/
│   │   └── feature_pipeline_handler.py    # Lambda function
│   └── pipelines/
│       ├── feature_pipeline.py            # Feature processing
│       ├── training_pipeline.py           # Model training
│       ├── inference_pipeline.py          # Model deployment
│       ├── train_simple.py               # Training script
│       └── inference.py                  # Inference script
├── infrastructure/
│   └── feature_pipeline_stack.py         # CDK infrastructure
├── tests/
│   └── test_pipelines/
│       └── test_training_pipeline.py     # Pipeline tests
├── app.py                                # Streamlit dashboard
├── deploy_model_sdk.py                   # Model deployment
└── start_training_sdk.py                 # Training job starter
```

## Getting Started

### Prerequisites
- AWS Account with SageMaker access
- Python 3.8+
- AWS CLI configured
- API keys for Visual Crossing and WAQI

### Installation
```bash
git clone <repository-url>
cd AQI-Prediction
pip install -r requirements.txt
```

### Usage

**Train Model**:
```bash
python start_training_sdk.py
```

**Deploy Model**:
```bash
python deploy_model_sdk.py
```

**Launch Dashboard**:
```bash
streamlit run app.py
```

## Key Features
- ✅ **Serverless Architecture**: Lambda-based feature pipeline
- ✅ **Feature Store**: Centralized feature management with SageMaker
- ✅ **Automated Training**: SageMaker Training Jobs with XGBoost
- ✅ **Real-time Inference**: SageMaker Endpoints for predictions
- ✅ **Interactive Dashboard**: Streamlit app with visualizations
- ✅ **Infrastructure as Code**: AWS CDK for reproducible deployments

## Technologies Used
- **Cloud**: AWS (Lambda, SageMaker, S3, Athena, EventBridge)
- **ML Framework**: XGBoost, SageMaker Python SDK
- **Infrastructure**: AWS CDK (Python)
- **Frontend**: Streamlit with Plotly visualizations
- **APIs**: Visual Crossing Weather, World Air Quality Index
- **Data Storage**: SageMaker Feature Store, S3

## Model Performance
- **Training Data**: 1,836 records
- **Features**: 7 weather variables
- **Algorithm**: XGBoost Regression
- **Training Time**: ~140 seconds
- **Deployment**: Real-time endpoint (ml.m5.large)