# train.py
import argparse
import os
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
import joblib

def model_fn(model_dir):
    """Load model from the model_dir. This is the same model that is saved
    in the main if statement.
    """
    model = joblib.load(os.path.join(model_dir, "model.joblib"))
    return model

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    
    # Hyperparameters sent by the client are passed as command-line arguments to the script
    parser.add_argument('--max_depth', type=int, default=6)
    parser.add_argument('--n_estimators', type=int, default=100)
    
    # SageMaker specific arguments
    parser.add_argument('--model-dir', type=str, default=os.environ.get('SM_MODEL_DIR'))
    parser.add_argument('--train', type=str, default=os.environ.get('SM_CHANNEL_TRAIN'))
    
    args = parser.parse_args()
    
    # Load training data
    training_dir = args.train
    train_data = pd.read_csv(os.path.join(training_dir, "train.csv"))
    
    # Split features and target
    X_train = train_data.drop(['pm25'], axis=1)
    y_train = train_data['pm25']
    
    # Train model
    model = RandomForestRegressor(
        max_depth=args.max_depth,
        n_estimators=args.n_estimators,
        random_state=42
    )
    model.fit(X_train, y_train)
    
    # Save model
    joblib.dump(model, os.path.join(args.model_dir, "model.joblib"))
