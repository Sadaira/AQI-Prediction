import boto3
from sagemaker import get_execution_role
from sagemaker.xgboost import XGBoost
from datetime import datetime

# Initialize
bucket_name = 'sagemaker-us-east-1-784376946367'
role_arn = 'arn:aws:iam::784376946367:role/sagemakerRole'

# Create XGBoost estimator
xgb = XGBoost(
    entry_point='train_simple.py',
    source_dir='src/pipelines',
    framework_version='1.5-1',
    py_version='py3',
    instance_type='ml.m5.large',
    instance_count=1,
    role=role_arn,
    output_path=f's3://{bucket_name}/model-output/',
    hyperparameters={
        'max_depth': 6,
        'eta': 0.2,
        'gamma': 4,
        'min_child_weight': 6,
        'subsample': 0.8,
        'objective': 'reg:squarederror',
        'num_round': 100
    }
)

# Start training
job_name = f"aqi-prediction-sdk-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
xgb.fit({'train': f's3://{bucket_name}/training-data/'}, job_name=job_name)
print(f"Training job started: {job_name}")