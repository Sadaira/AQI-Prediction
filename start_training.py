# start_training.py
import sys
import os
import boto3
from datetime import datetime
sys.path.append('src')

from pipelines.training_pipeline import TrainingPipeline

def start_training():
    # Configuration
    table_name = "784376946367_us_east_1_air_quality_features_08_14_56_40_1744124210"
    bucket_name = "sagemaker-us-east-1-784376946367"
    
    # Use existing role
    role_arn = 'arn:aws:iam::784376946367:role/sagemakerRole'
    print(f"Using existing SageMaker role: {role_arn}")
    
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