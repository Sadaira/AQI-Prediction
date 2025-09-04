import boto3
from sagemaker.xgboost import XGBoostModel
from sagemaker.serverless import ServerlessInferenceConfig
from datetime import datetime

# Configuration
bucket_name = 'sagemaker-us-east-1-784376946367'
role_arn = 'arn:aws:iam::784376946367:role/sagemakerRole'
model_data_url = f"s3://{bucket_name}/model-output/aqi-prediction-sdk-20250813-164255/output/model.tar.gz"

# Create XGBoost model
model = XGBoostModel(
    model_data=model_data_url,
    role=role_arn,
    entry_point='inference.py',
    source_dir='src/pipelines',
    framework_version='1.5-1'
)

# Deploy to serverless endpoint
endpoint_name = f"aqi-prediction-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
serverless_config = ServerlessInferenceConfig(
    memory_size_in_mb=2048,
    max_concurrency=5
)

predictor = model.deploy(
    serverless_inference_config=serverless_config,
    endpoint_name=endpoint_name
)

print(f"Model deployed to endpoint: {endpoint_name}")
print("Endpoint is ready for predictions!")