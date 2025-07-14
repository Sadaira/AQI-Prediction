# src/pipelines/train.py
import argparse
import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import xgboost as xgb
import mlflow
import boto3
import joblib

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model-dir', type=str, default=os.environ.get('SM_MODEL_DIR'))
    parser.add_argument('--train', type=str, default=os.environ.get('SM_CHANNEL_TRAIN'))
    parser.add_argument('--max-depth', type=int, default=6)
    parser.add_argument('--eta', type=float, default=0.2)
    parser.add_argument('--gamma', type=int, default=4)
    parser.add_argument('--min-child-weight', type=int, default=6)
    parser.add_argument('--subsample', type=float, default=0.8)
    parser.add_argument('--n-estimators', type=int, default=100)
    
    args = parser.parse_args()
    
    # Set MLflow tracking URI to S3
    mlflow.set_tracking_uri("s3://your-bucket/mlflow-tracking")
    mlflow.set_experiment("pm25-prediction")
    
    with mlflow.start_run():
        # Log parameters
        mlflow.log_param("max_depth", args.max_depth)
        mlflow.log_param("eta", args.eta)
        mlflow.log_param("gamma", args.gamma)
        mlflow.log_param("min_child_weight", args.min_child_weight)
        mlflow.log_param("subsample", args.subsample)
        mlflow.log_param("n_estimators", args.n_estimators)
        
        # Load training data
        train_data = pd.read_csv(os.path.join(args.train, 'train.csv'))
        
        # Prepare features and target
        feature_columns = ['temp', 'humidity', 'precip', 'windspeed', 'conditions', 
                          'cloudcover', 'visibility', 'solarradiation']
        X = train_data[feature_columns]
        y = train_data['pm25']
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Train XGBoost model
        model = xgb.XGBRegressor(
            max_depth=args.max_depth,
            learning_rate=args.eta,
            gamma=args.gamma,
            min_child_weight=args.min_child_weight,
            subsample=args.subsample,
            n_estimators=args.n_estimators,
            random_state=42
        )
        
        model.fit(X_train_scaled, y_train)
        
        # Make predictions
        y_pred = model.predict(X_test_scaled)
        
        # Calculate metrics
        mse = mean_squared_error(y_test, y_pred)
        rmse = np.sqrt(mse)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        # Log metrics
        mlflow.log_metric("mse", mse)
        mlflow.log_metric("rmse", rmse)
        mlflow.log_metric("mae", mae)
        mlflow.log_metric("r2", r2)
        
        # Log model artifacts
        mlflow.log_artifact(os.path.join(args.model_dir, 'model.joblib'))
        mlflow.log_artifact(os.path.join(args.model_dir, 'scaler.joblib'))
        
        # Save model and scaler
        joblib.dump(model, os.path.join(args.model_dir, 'model.joblib'))
        joblib.dump(scaler, os.path.join(args.model_dir, 'scaler.joblib'))
        
        print(f"Model trained successfully. RMSE: {rmse:.2f}, R2: {r2:.3f}")

if __name__ == '__main__':
    main()
