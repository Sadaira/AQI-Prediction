# src/lambda/feature_pipeline_handler.py
import os
import json
import logging
from datetime import datetime
import boto3
import sys
from pathlib import Path

src_dir = str(Path(__file__).resolve().parents[1])
sys.path.append(src_dir)

from pipelines.feature_pipeline import FeaturePipeline

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    try:
        # Log environment variables (don't log in production!)
        logger.info(f"Environment variables: {dict(os.environ)}")
        
        # Initialize Secrets Manager client
        secrets_client = boto3.client('secretsmanager')
        
        # Get Weather API key
        try:
            weather_secret_name = os.environ['WEATHER_API_SECRET_NAME']
            logger.info(f"Attempting to retrieve weather API key from secret: {weather_secret_name}")
            weather_api_key = secrets_client.get_secret_value(
                SecretId=weather_secret_name
            )['SecretString']
            logger.info("Successfully retrieved weather API key")
        except Exception as e:
            logger.error(f"Failed to retrieve weather API key: {str(e)}")
            raise
        
        # Get Air Quality API key
        try:
            air_quality_secret_name = os.environ['AIR_QUALITY_API_SECRET_NAME']
            logger.info(f"Attempting to retrieve air quality API key from secret: {air_quality_secret_name}")
            air_quality_api_key = secrets_client.get_secret_value(
                SecretId=air_quality_secret_name
            )['SecretString']
            logger.info("Successfully retrieved air quality API key")
        except Exception as e:
            logger.error(f"Failed to retrieve air quality API key: {str(e)}")
            raise
            
        # Set these as environment variables for the pipeline to use
        os.environ['WEATHER_API_KEY'] = weather_api_key
        os.environ['AIR_QUALITY_API_KEY'] = air_quality_api_key
            
        logger.info("API keys set successfully, proceeding with pipeline")
        
        # Initialize feature pipeline
        pipeline = FeaturePipeline(
            feature_group_name=os.environ['FEATURE_GROUP_NAME']
        )
        
        # Get cities from environment variable (comma-separated)
        cities = os.environ.get('CITIES', 'los angeles').split(',')
        
        results = {}
        for city in cities:
            try:
                features = pipeline.run_pipeline(city=city.strip())
                results[city] = 'success'
                logger.info(f"Successfully processed features for {city}")
            except Exception as e:
                results[city] = f'failed: {str(e)}'
                logger.error(f"Failed to process features for {city}: {str(e)}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Feature pipeline execution completed',
                'timestamp': datetime.now().isoformat(),
                'results': results
            })
        }
    except Exception as e:
        logger.error(f"Lambda execution failed: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
        }
