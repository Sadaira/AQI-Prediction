import boto3
import pandas as pd
import json
from datetime import datetime

class InferencePipeline:
    def __init__(self, bucket_name: str, model_name: str):
        self.bucket_name = bucket_name
        self.model_name = model_name
        self.sagemaker = boto3.client('sagemaker')
        self.runtime = boto3.client('sagemaker-runtime')
        
    def create_model(self, role_arn: str, model_data_url: str):
        """Create SageMaker model"""
        model_config = {
            'ModelName': self.model_name,
            'PrimaryContainer': {
                'Image': '246618743249.dkr.ecr.us-east-1.amazonaws.com/xgboost:1.5-1',
                'ModelDataUrl': model_data_url
            },
            'ExecutionRoleArn': role_arn
        }
        
        response = self.sagemaker.create_model(**model_config)
        return response
    
    def create_endpoint_config(self, endpoint_config_name: str):
        """Create endpoint configuration"""
        config = {
            'EndpointConfigName': endpoint_config_name,
            'ProductionVariants': [{
                'VariantName': 'primary',
                'ModelName': self.model_name,
                'InitialInstanceCount': 1,
                'InstanceType': 'ml.t2.medium',
                'InitialVariantWeight': 1
            }]
        }
        
        response = self.sagemaker.create_endpoint_config(**config)
        return response
    
    def create_endpoint(self, endpoint_name: str, endpoint_config_name: str):
        """Create SageMaker endpoint"""
        endpoint_config = {
            'EndpointName': endpoint_name,
            'EndpointConfigName': endpoint_config_name
        }
        
        response = self.sagemaker.create_endpoint(**endpoint_config)
        return response
    
    def predict(self, endpoint_name: str, features: dict):
        """Make prediction using endpoint"""
        # Convert features to CSV format expected by XGBoost
        feature_order = ['temp', 'humidity', 'precip', 'windspeed', 'cloudcover', 'visibility', 'solarradiation']
        csv_data = ','.join([str(features[col]) for col in feature_order])
        
        response = self.runtime.invoke_endpoint(
            EndpointName=endpoint_name,
            ContentType='text/csv',
            Body=csv_data
        )
        
        result = json.loads(response['Body'].read().decode())
        return result