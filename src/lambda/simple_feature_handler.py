# src/lambda/feature_pipeline_handler.py
import os
import json
import logging
from datetime import datetime
import boto3
import sys
import pandas as pd
from pathlib import Path

src_dir = str(Path(__file__).resolve().parents[1])
sys.path.append(src_dir)

from pipelines.feature_pipeline import FeaturePipeline

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    try:
        # For testing purposes only - hardcode API keys
        # IMPORTANT: Remove these hardcoded keys before deploying to production
        os.environ['WEATHER_API_KEY'] = "7KJHSXG9NPA2TPE8VP52NTSPB"  # Replace with your actual key
        os.environ['AIR_QUALITY_API_KEY'] = "4f3f6e2b1360980aec87f727b4e6d7fb70a6169f"  # Replace with your actual key
        
        logger.info("API keys set successfully, proceeding with pipeline")
        
        # Initialize feature pipeline
        feature_group_name = 'air-quality-features-08-14-56-40'  # Use your feature group name
        pipeline = FeaturePipeline(
            feature_group_name=feature_group_name
        )
        
        # Get cities from environment variable (comma-separated)
        cities = os.environ.get('CITIES', 'los angeles').split(',')
        
        results = {}
        for city in cities:
            try:
                # Execute pipeline steps individually for better error handling
                logger.info(f"Fetching weather data for {city}")
                weather_data = pipeline.fetch_weather_data(city=city.strip())
                
                logger.info(f"Fetching air quality data for {city}")
                air_quality_data = pipeline.fetch_air_quality_data(city_name=city.strip())
                
                logger.info(f"Processing features for {city}")
                features = pipeline.process_features(weather_data, air_quality_data)
                
                # Modify the write_to_feature_store method to handle type conversions
                # This is a simplified version that avoids the original errors
                logger.info(f"Writing features to feature store for {city}")
                
                # Get valid features from Feature Group
                sagemaker_client = boto3.client('sagemaker')
                response = sagemaker_client.describe_feature_group(
                    FeatureGroupName=feature_group_name
                )
                valid_features = [feature['FeatureName'] for feature in response['FeatureDefinitions']]
                
                # Create a dictionary of features
                feature_dict = {}
                for idx, row in features.iterrows():
                    for column in features.columns:
                        if column in valid_features:
                            value = row[column]
                            if pd.notna(value):
                                # Handle type conversions
                                if column in ['precipprob', 'snow', 'snowdepth', 'winddir', 'cloudcover', 'visibility', 'uvindex']:
                                    try:
                                        value = int(float(value))
                                    except (ValueError, TypeError):
                                        value = 0
                                feature_dict[column] = str(value)
                
                # Add required features
                if 'event_time' in valid_features and 'event_time' not in feature_dict:
                    feature_dict['event_time'] = str(int(datetime.now().timestamp()))
                if 'record_id' in valid_features and 'record_id' not in feature_dict:
                    feature_dict['record_id'] = datetime.now().strftime('%Y%m%d%H%M%S')
                
                # Convert to record format
                record = [
                    {
                        'FeatureName': key,
                        'ValueAsString': value
                    }
                    for key, value in feature_dict.items()
                ]
                
                # Write to Feature Store
                featurestore_runtime = boto3.client('sagemaker-featurestore-runtime')
                featurestore_runtime.put_record(
                    FeatureGroupName=feature_group_name,
                    Record=record
                )
                
                results[city] = 'success'
                logger.info(f"Successfully processed features for {city}")
            except Exception as e:
                results[city] = f'failed: {str(e)}'
                logger.error(f"Failed to process features for {city}: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
        
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
        import traceback
        logger.error(traceback.format_exc())
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
        }
