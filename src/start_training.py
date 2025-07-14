# src/start_training.py
import sys
import os
import boto3
from datetime import datetime
sys.path.append('src')

from pipelines.training_pipeline import TrainingPipeline

def create_sagemaker_role():
    """Create SageMaker execution role if it doesn't exist"""
    iam = boto3.client('iam')
    role_name = 'AQI-SageMaker-ExecutionRole'
    
    try:
        # Check if role exists
        response = iam.get_role(RoleName=role_name)
        print(f"Using existing role: {response['Role']['Arn']}")
        return response['Role']['Arn']
    except iam.exceptions.NoSuchEntityException:
        # Create role
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": "sagemaker.amazonaws.com"},
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        role = iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=str(trust_policy).replace("'", '"'),
            Description='SageMaker execution role for AQI prediction'
        )
        
        # Attach policies
        iam.attach_role_policy(
            RoleName=role_name,
            PolicyArn='arn:aws:iam::aws:policy/AmazonSageMakerFullAccess'
        )
        iam.attach_role_policy(
            RoleName=role_name,
            PolicyArn='arn:aws:iam::aws:policy/AmazonS3FullAccess'
        )
        
        print(f"Created new role: {role['Role']['Arn']}")
        return role['Role']['Arn']

def start_training():
    # Configuration
    table_name = "784376946367_us_east_1_air_quality_features_08_14_56_40_1744124210"
    bucket_name = "sagemaker-us-east-1-784376946367"
    
    # Create role
    role_arn = create_sagemaker_role()
    
    # Initialize pipeline
    pipeline = TrainingPipeline(table_name, bucket_name)
    
    # Generate unique job name
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    job_name = f"aqi-prediction-training-{timestamp}"
    
    print(f"Starting training job: {job_name}")
    
    try:
        # Start training job
        response = pipeline.start_training_job(job_name, role_arn)
        print(f"Training job started successfully!")
        print(f"Job ARN: {response['TrainingJobArn']}")
        print(f"Monitor progress in SageMaker console or run:")
        print(f"aws sagemaker describe-training-job --training-job-name {job_name}")
        
    except Exception as e:
        print(f"Failed to start training job: {str(e)}")

if __name__ == "__main__":
    start_training()