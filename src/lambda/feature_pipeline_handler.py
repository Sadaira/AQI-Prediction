# src/lambda/feature_pipeline_handler.py
import os
import json
import logging
from datetime import datetime
import boto3
import sys
import pandas as pd
import numpy as np
from pathlib import Path

src_dir = str(Path(__file__).resolve().parents[1])
sys.path.append(src_dir)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    try:
        # For testing purposes only - hardcode API keys
        # IMPORTANT: Remove these hardcoded keys before deploying to production
        weather_api_key = "7KJHSXG9NPA2TPE8VP52NTSPB"  # Replace with your actual key
        air_quality_api_key = "4f3f6e2b1360980aec87f727b4e6d7fb70a6169f"  # Replace with your actual key
        
        # Get city from environment variable
        city = os.environ.get('CITIES', 'los angeles').split(',')[0].strip()
        logger.info(f"Processing city: {city}")
        
        # Fetch weather data directly
        logger.info(f"Fetching weather data for {city}")
        import requests
        weather_response = requests.get(
            f'https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{city}/today',
            params={
                'unitGroup': 'us',
                'include': 'days',
                'key': weather_api_key,
                'contentType': 'json'
            }
        )
        weather_response.raise_for_status()
        weather_data = pd.DataFrame(weather_response.json()['days'])
        logger.info(f"Weather data columns: {weather_data.columns.tolist()}")
        
        # Fetch air quality data directly
        logger.info(f"Fetching air quality data for {city}")
        air_quality_response = requests.get(
            f'https://api.waqi.info/feed/{city}/',
            params={'token': air_quality_api_key}
        )
        air_quality_response.raise_for_status()
        
        aq_data = air_quality_response.json()['data']
        iaqi = aq_data['iaqi']
        
        # Handle missing parameters
        params = ['pm10', 'pm25', 'no2', 'so2', 'co', 'o3']
        for param in params:
            if param not in iaqi:
                iaqi[param] = {"v": np.nan}
        
        air_quality_data = pd.DataFrame({
            'date': [aq_data['time']['s'][:10]],
            **{param: [iaqi[param]['v']] for param in params}
        })
        logger.info(f"Air quality data columns: {air_quality_data.columns.tolist()}")
        
        # Process and combine data
        logger.info("Processing features")
        
        # Rename columns for consistency
        if 'datetime' in weather_data.columns:
            weather_data = weather_data.rename(columns={'datetime': 'date'})
        
        # Get the feature definitions from the Feature Group
        feature_group_name = 'air-quality-features-08-14-56-40'
        sagemaker_client = boto3.client('sagemaker')
        
        response = sagemaker_client.describe_feature_group(
            FeatureGroupName=feature_group_name
        )
        
        # Extract feature names from the response
        valid_features = [feature['FeatureName'] for feature in response['FeatureDefinitions']]
        logger.info(f"Valid features in Feature Group: {valid_features}")
        
        # Create a dictionary to hold feature values (this ensures uniqueness)
        feature_dict = {}
        
        # Required features for the Feature Group
        record_id = datetime.now().strftime('%Y%m%d%H%M%S')
        timestamp = int(datetime.now().timestamp())
        
        # Add required features
        if 'event_time' in valid_features:
            feature_dict['event_time'] = str(timestamp)
        
        if 'record_id' in valid_features:
            feature_dict['record_id'] = record_id
        
        if 'timestamp' in valid_features:
            feature_dict['timestamp'] = str(timestamp)
        
        # Add weather data features
        if len(weather_data) > 0:
            for col in weather_data.columns:
                if col in valid_features:
                    value = weather_data.iloc[0][col]
                    if pd.notna(value):
                        # Handle specific columns that need type conversion
                        if col in ['precipprob', 'snow', 'snowdepth', 'winddir', 'cloudcover', 'visibility', 'uvindex', 'conditions']:
                            # Convert to integer
                            if col == 'conditions':
                                # Map conditions to integers
                                conditions_map = {
                                    'Clear': 1, 
                                    'Partially cloudy': 2,
                                    'Rain, Partially cloudy': 3,
                                    'Rain': 4, 
                                    'Overcast': 5,
                                    'Rain, Overcast': 6
                                }
                                value = conditions_map.get(str(value), 0)
                            else:
                                try:
                                    value = int(float(value))
                                except (ValueError, TypeError):
                                    value = 0
                        elif col in ['temp', 'humidity', 'precip', 'windspeed', 'tempmax', 'tempmin', 'feelslike', 'feelslikemax', 'feelslikemin', 'dew', 'windgust', 'solarradiation', 'solarenergy', 'moonphase']:
                            # Convert to float with 2 decimal places
                            try:
                                value = round(float(value), 2)
                            except (ValueError, TypeError):
                                value = 0.0
                        
                        feature_dict[col] = str(value)
                    else:
                        # Handle null values based on expected type
                        if col in ['precipprob', 'snow', 'snowdepth', 'winddir', 'cloudcover', 'visibility', 'uvindex', 'conditions']:
                            feature_dict[col] = '0'
                        elif col in ['temp', 'humidity', 'precip', 'windspeed', 'tempmax', 'tempmin', 'feelslike', 'feelslikemax', 'feelslikemin', 'dew', 'windgust', 'solarradiation', 'solarenergy', 'moonphase']:
                            feature_dict[col] = '0.0'
                        else:
                            feature_dict[col] = ''

        # Add air quality data features
        if len(air_quality_data) > 0:
            for col in air_quality_data.columns:
                if col in valid_features and col not in feature_dict:  # Only add if not already present
                    value = air_quality_data.iloc[0][col]
                    if pd.notna(value):
                        if col == 'pm25':
                            try:
                                value = int(float(value))
                            except (ValueError, TypeError):
                                value = 0
                        feature_dict[col] = str(value)
                    else:
                        feature_dict[col] = ''
        
        # Convert dictionary to the required format for PutRecord
        record = [
            {
                'FeatureName': key,
                'ValueAsString': value
            }
            for key, value in feature_dict.items()
        ]
        
        # Log the record for debugging
        logger.info(f"Record to be written: {json.dumps(record)}")
        
        # Write to Feature Store
        logger.info("Writing to Feature Store")
        featurestore_runtime = boto3.client('sagemaker-featurestore-runtime')
        
        featurestore_runtime.put_record(
            FeatureGroupName=feature_group_name,
            Record=record
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Feature pipeline execution completed successfully',
                'timestamp': datetime.now().isoformat(),
                'city': city
            })
        }
    except Exception as e:
        import traceback
        logger.error(f"Error: {str(e)}")
        logger.error(traceback.format_exc())
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
        }
