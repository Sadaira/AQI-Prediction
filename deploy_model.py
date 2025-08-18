from src.pipelines.inference_pipeline import InferencePipeline
from datetime import datetime

# Configuration
bucket_name = 'sagemaker-us-east-1-784376946367'
role_arn = 'arn:aws:iam::784376946367:role/sagemakerRole'
model_name = f"aqi-prediction-model-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
endpoint_config_name = f"aqi-prediction-config-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
endpoint_name = f"aqi-prediction-endpoint-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

# Model artifact from the completed training job
model_data_url = f"s3://{bucket_name}/model-output/aqi-prediction-sdk-20250813-164255/output/model.tar.gz"

# Initialize inference pipeline
inference = InferencePipeline(bucket_name, model_name)

try:
    # Create model
    print("Creating model...")
    model_response = inference.create_model(role_arn, model_data_url)
    print(f"Model created: {model_name}")
    
    # Create endpoint configuration
    print("Creating endpoint configuration...")
    config_response = inference.create_endpoint_config(endpoint_config_name)
    print(f"Endpoint config created: {endpoint_config_name}")
    
    # Create endpoint
    print("Creating endpoint...")
    endpoint_response = inference.create_endpoint(endpoint_name, endpoint_config_name)
    print(f"Endpoint created: {endpoint_name}")
    print("Endpoint is being deployed. This may take several minutes...")
    
except Exception as e:
    print(f"Error: {e}")