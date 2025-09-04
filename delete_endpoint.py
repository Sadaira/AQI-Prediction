import boto3

sagemaker = boto3.client('sagemaker')

# Delete the old endpoint that's charging continuously
old_endpoint_name = "aqi-prediction-20250818-161138"

try:
    # Delete endpoint
    sagemaker.delete_endpoint(EndpointName=old_endpoint_name)
    print(f"Deleted endpoint: {old_endpoint_name}")
    
    # Delete endpoint configuration
    sagemaker.delete_endpoint_config(EndpointConfigName=old_endpoint_name)
    print(f"Deleted endpoint config: {old_endpoint_name}")
    
except Exception as e:
    print(f"Error: {e}")