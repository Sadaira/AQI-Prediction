import argparse
import pandas as pd
import xgboost as xgb
import joblib
import os

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--max_depth', type=int, default=6)
    parser.add_argument('--eta', type=float, default=0.2)
    parser.add_argument('--gamma', type=float, default=4)
    parser.add_argument('--min_child_weight', type=int, default=6)
    parser.add_argument('--subsample', type=float, default=0.8)
    parser.add_argument('--objective', type=str, default='reg:squarederror')
    parser.add_argument('--num_round', type=int, default=100)
    
    args = parser.parse_args()
    
    # Load training data
    train_data = pd.read_csv('/opt/ml/input/data/train/train.csv')
    
    # Prepare features and target
    feature_cols = ['temp', 'humidity', 'precip', 'windspeed', 'cloudcover', 'visibility', 'solarradiation']
    X = train_data[feature_cols]
    y = train_data['pm25']
    
    # Train XGBoost model
    model = xgb.XGBRegressor(
        max_depth=args.max_depth,
        learning_rate=args.eta,
        gamma=args.gamma,
        min_child_weight=args.min_child_weight,
        subsample=args.subsample,
        objective=args.objective,
        n_estimators=args.num_round
    )
    
    model.fit(X, y)
    
    # Save model
    model_path = os.path.join('/opt/ml/model', 'model.joblib')
    joblib.dump(model, model_path)
    
    print(f"Model trained and saved to {model_path}")

if __name__ == '__main__':
    main()