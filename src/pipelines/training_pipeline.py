# src/pipelines/training_pipeline.py
import boto3
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

class TrainingPipeline:
    def __init__(self, feature_group_table_name: str, bucket_name: str):
        self.feature_group_table_name = feature_group_table_name
        self.bucket_name = bucket_name
        self.athena = boto3.client('athena')
        self.s3 = boto3.client('s3')
        
    def prepare_training_data(self):
        """Query Feature Store and prepare training data"""
        query = f"""
        SELECT 
            temp, humidity, precip, windspeed, conditions,
            cloudcover, visibility, solarradiation, pm25
        FROM "{self.feature_group_table_name}"
        WHERE pm25 IS NOT NULL 
        AND temp IS NOT NULL 
        AND humidity IS NOT NULL
        """
        
        logger.info("Executing Athena query to get training data")
        
        # Execute query
        response = self.athena.start_query_execution(
            QueryString=query,
            QueryExecutionContext={'Database': 'sagemaker_featurestore'},
            ResultConfiguration={
                'OutputLocation': f's3://{self.bucket_name}/athena-results/'
            }
        )
        
        query_execution_id = response['QueryExecutionId']
        
        # Wait for completion
        while True:
            result = self.athena.get_query_execution(QueryExecutionId=query_execution_id)
            status = result['QueryExecution']['Status']['State']
            if status in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
                break
        
        if status == 'SUCCEEDED':
            # Get results location
            results_location = result['QueryExecution']['ResultConfiguration']['OutputLocation']
            bucket = results_location.split('/')[2]
            key = '/'.join(results_location.split('/')[3:])
            
            # Download and process data
            self.s3.download_file(bucket, key, 'query_results.csv')
            df = pd.read_csv('query_results.csv')
            
            # Clean data
            df = df.dropna()
            df = df[df['pm25'] > 0]  # Remove invalid PM2.5 values
            
            # Upload to S3 for training
            df.to_csv('train.csv', index=False)
            self.s3.upload_file('train.csv', self.bucket_name, 'training-data/train.csv')
            
            logger.info(f"Training data prepared: {len(df)} records")
            return df
        else:
            logger.error(f"Query failed: {status}")
            return None
    
    def start_training_job(self, job_name: str, role_arn: str):
        """Start SageMaker training job"""
        sagemaker = boto3.client('sagemaker')
        
        training_job_config = {
            'TrainingJobName': job_name,
            'RoleArn': role_arn,
            'AlgorithmSpecification': {
                'TrainingInputMode': 'File'
            },
            'AlgorithmName': 'arn:aws:sagemaker:us-east-1:865070037744:algorithm/xgboost-2022-04-13-07-44-50-522',
            'InputDataConfig': [{
                'ChannelName': 'train',
                'DataSource': {
                    'S3DataSource': {
                        'S3DataType': 'S3Prefix',
                        'S3Uri': f's3://{self.bucket_name}/training-data/',
                        'S3DataDistributionType': 'FullyReplicated'
                    }
                }
            }],
            'OutputDataConfig': {
                'S3OutputPath': f's3://{self.bucket_name}/model-output/'
            },
            'ResourceConfig': {
                'InstanceType': 'ml.m5.large',
                'InstanceCount': 1,
                'VolumeSizeInGB': 20
            },
            'StoppingCondition': {
                'MaxRuntimeInSeconds': 3600
            },
            'HyperParameters': {
                'max_depth': '6',
                'eta': '0.2',
                'gamma': '4',
                'min_child_weight': '6',
                'subsample': '0.8',
                'objective': 'reg:squarederror',
                'num_round': '100'
            }
        }
        
        response = sagemaker.create_training_job(**training_job_config)
        logger.info(f"Training job started: {job_name}")
        return response