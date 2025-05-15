# src/pipelines/feature_pipeline.py
import os
import time
import logging
import boto3
import numpy as np
import pandas as pd
import requests
from datetime import datetime
from typing import Dict, Optional, List
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FeaturePipelineMonitoring:
    def __init__(self):
        self.cloudwatch = boto3.client('cloudwatch')
        self.namespace = 'AQIPrediction/FeaturePipeline'

    def log_metric(self, metric_name: str, value: float, unit: str = 'Count'):
        try:
            self.cloudwatch.put_metric_data(
                Namespace=self.namespace,
                MetricData=[{
                    'MetricName': metric_name,
                    'Value': value,
                    'Unit': unit,
                    'Timestamp': datetime.now()
                }]
            )
            logger.info(f"Logged metric {metric_name}: {value}")
        except Exception as e:
            logger.error(f"Error logging metric {metric_name}: {str(e)}")

class DataQualityValidator:
    @staticmethod
    def validate_features(df: pd.DataFrame) -> Dict[str, bool]:
        validation_results = {}
        
        # Basic data checks
        validation_results['has_data'] = len(df) > 0
        validation_results['no_missing_pm25'] = df['pm25'].isna().sum() == 0
        
        # Value range checks
        if 'temperature' in df.columns:
            # Use .all() to convert Series to boolean
            validation_results['valid_temperature'] = df['temperature'].between(-50, 150).all()
        if 'humidity' in df.columns:
            validation_results['valid_humidity'] = df['humidity'].between(0, 100).all()
        if 'pm25' in df.columns:
            validation_results['valid_pm25'] = df['pm25'].between(0, 500).all()

        return validation_results


class FeaturePipeline:
    def __init__(self, feature_group_name: str):
        """Initialize the feature pipeline with API keys and AWS client."""
        load_dotenv()  # Load environment variables

        self.feature_group_name = feature_group_name
        self.featurestore_runtime = boto3.client('sagemaker-featurestore-runtime')
        self.monitoring = FeaturePipelineMonitoring()
        self.validator = DataQualityValidator()

        # Get API keys from environment variables
        self.weather_key = os.getenv('WEATHER_API_KEY')
        self.air_quality_key = os.getenv('AIR_QUALITY_API_KEY')
          
        if not all([self.weather_key, self.air_quality_key]):
            raise ValueError("Missing required API keys in environment variables")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def fetch_weather_data(self, city: str = 'los angeles') -> pd.DataFrame:
        """Fetch weather data from Visual Crossing API."""
        try:
            response = requests.get(
                f'https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{city}/today',
                params={
                    'unitGroup': 'us',
                    'include': 'days',
                    'key': self.weather_key,
                    'contentType': 'json'
                }
            )
            response.raise_for_status()
            data = pd.DataFrame(response.json()['days'])
            self.monitoring.log_metric('WeatherAPISuccess', 1)
            return data
        except requests.exceptions.RequestException as e:
            self.monitoring.log_metric('WeatherAPIError', 1)
            logger.error(f"Error fetching weather data: {str(e)}")
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def fetch_air_quality_data(self, city_name='los angeles') -> pd.DataFrame:
        """Fetch air quality data from WAQI API."""
        try:
            response = requests.get(
                f'https://api.waqi.info/feed/{city_name}/',
                params={'token': self.air_quality_key}
            )
            response.raise_for_status()
            
            data = response.json()['data']
            iaqi = data['iaqi']
            
            # Handle missing parameters
            params = ['pm10', 'pm25', 'no2', 'so2', 'co', 'o3']
            for param in params:
                if param not in iaqi:
                    iaqi[param] = {"v": np.nan}
            
            df = pd.DataFrame({
                'city': [city_name],
                'date': [data['time']['s'][:10]],
                **{param: [iaqi[param]['v']] for param in params}
            })
            self.monitoring.log_metric('AirQualityAPISuccess', 1)
            return df
        except requests.exceptions.RequestException as e:
            self.monitoring.log_metric('AirQualityAPIError', 1)
            logger.error(f"Error fetching air quality data: {str(e)}")
            raise

    def process_features(self, weather_data: pd.DataFrame, 
                        air_quality_data: pd.DataFrame) -> pd.DataFrame:
        """Process and combine weather and air quality features."""
        try:
            # Log input record counts
            self.monitoring.log_metric('WeatherDataCount', len(weather_data))
            self.monitoring.log_metric('AirQualityDataCount', len(air_quality_data))

            # Convert dates to datetime
            air_quality_data['date'] = pd.to_datetime(air_quality_data['date'])
            weather_data.rename(columns={'datetime': 'date'}, inplace=True)

            # Combine datasets
            features = pd.concat([weather_data, air_quality_data], axis=1)

            # Drop unnecessary columns
            columns_to_drop = ['name', 'description', 'icon', 'stations',
                                'sunrise', 'sunset', 'severerisk',
                                'preciptype', 'pm10', 'o3',
                                'no2', 'so2', 'co']
            features.drop(columns=[col for col in columns_to_drop 
                                if col in features.columns], inplace=True)
            
            # Clean and convert pm25 values
            if features['pm25'].dtype == 'object':  # If pm25 is string
                features['pm25'] = (features['pm25'].astype(str)
                                .str.strip()
                                .replace(' ', np.nan))
            features['pm25'] = pd.to_numeric(features['pm25'], errors='coerce')
            features['pm25'] = features['pm25'].astype('Int64')
            
            # Map weather conditions to numerical values
            conditions = {
                'Clear': 1, 'Partially cloudy': 2,
                'Rain, Partially cloudy': 3,
                'Rain': 4, 'Overcast': 5,
                'Rain, Overcast': 6
            }
            if 'conditions' in features.columns:
                features['conditions'] = features['conditions'].map(conditions)
            # Add timestamp and record_id if not present
            if 'timestamp' not in features.columns:
                features['timestamp'] = pd.Series([int(round(time.time()))] * len(features), dtype="float64")
            if 'record_id' not in features.columns:
                features['record_id'] = features.index.astype(str)

            # Validate processed features
            validation_results = self.validator.validate_features(features)
            for check, result in validation_results.items():
                self.monitoring.log_metric(f'Validation_{check}', 1 if result else 0)

            if not all(validation_results.values()):
                failed_checks = [check for check, result in validation_results.items() if not result]
                raise ValueError(f"Data quality validation failed for: {failed_checks}")

            self.monitoring.log_metric('ProcessedRecordCount', len(features))
            return features

        except Exception as e:
            self.monitoring.log_metric('ProcessingError', 1)
            logger.error(f"Error processing features: {str(e)}")
            raise

    def write_to_feature_store(self, features: pd.DataFrame) -> None:
        """Write processed features to SageMaker Feature Store."""
        successful_writes = 0
        failed_writes = 0

        for idx, row in features.iterrows():
            record = []
            
            # Process each column individually
            for column in features.columns:
                value = row[column]
                
                # Convert to simple string, handling all types
                if pd.isna(value):
                    value_str = ""
                else:
                    # Convert to string and clean up any newlines
                    value_str = str(value).replace("\n", " ").strip()
                
                record.append({
                    'FeatureName': column,
                    'ValueAsString': value_str
                })
            
            try:
                self.featurestore_runtime.put_record(
                    FeatureGroupName=self.feature_group_name,
                    Record=record
                )
                successful_writes += 1
                logger.info(f"Successfully wrote record {idx} to Feature Store")
            except Exception as e:
                failed_writes += 1
                logger.error(f"Error writing record {idx} to Feature Store: {str(e)}")
                raise

        self.monitoring.log_metric('SuccessfulWrites', successful_writes)
        self.monitoring.log_metric('FailedWrites', failed_writes)

    def run_pipeline(self, city: str = 'los angeles') -> pd.DataFrame:
        """Execute the complete feature pipeline."""
        logger.info("Starting feature pipeline execution")
        try:
            weather_data = self.fetch_weather_data(city)
            logger.info("Successfully fetched weather data")
            
            air_quality_data = self.fetch_air_quality_data(city)
            logger.info("Successfully fetched air quality data")
            
            features = self.process_features(weather_data, air_quality_data)
            logger.info("Successfully processed features")
            
            self.write_to_feature_store(features)
            logger.info("Successfully wrote features to Feature Store")
            
            self.monitoring.log_metric('PipelineSuccess', 1)
            return features
            
        except Exception as e:
            self.monitoring.log_metric('PipelineError', 1)
            logger.error(f"Pipeline execution failed: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise
