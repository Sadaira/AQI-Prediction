# src/pipelines/feature_pipeline.py
import os
import time
import logging
import boto3
import numpy as np
import pandas as pd
import requests
from datetime import datetime
from typing import Dict, Optional
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FeaturePipeline:
    def __init__(self, feature_group_name: str):
        """Initialize the feature pipeline with API keys and AWS client."""
        load_dotenv()  # Load environment variables

        self.feature_group_name = feature_group_name
        self.featurestore_runtime = boto3.client('sagemaker-featurestore-runtime')

        # Get API keys from environment variables
        self.weather_key = os.getenv('WEATHER_API_KEY')
        self.air_quality_key = os.getenv('AIR_QUALITY_API_KEY')
          
        if not all([self.weather_key, self.air_quality_key]):
            raise ValueError("Missing required API keys in environment variables")
      

    def fetch_weather_data(self, city: str = 'los angeles') -> pd.DataFrame:
        """Fetch weather data from Visual Crossing API."""
        # json = response = requests.get(f'https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/los%20angeles/today?unitGroup=us&include=days&key={self.weather_key}&contentType=json').json()
        # return pd.DataFrame(response['days'])
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
            return pd.DataFrame(response.json()['days'])
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching weather data: {str(e)}")
            raise
    

    def fetch_air_quality_data(self, city_name='los angeles') -> pd.DataFrame:
        """Fetch air quality data from WAQI API."""
        # json = requests.get(f'https://api.waqi.info/feed/{city_name}/?token={self.air_quality_key}').json()['data']
        # iaqi = json['iaqi']
        # forecast = json['forecast']['daily']
        
        # params = ['pm10', 'pm25', 'no2', 'so2', 'co', 'o3']
        # for param in params:
        #     if param not in iaqi: # if the parameter is not present in the data, add a column with NaN values
        #         iaqi[param] = {"v": np.nan}
        # return pd.DataFrame(data={
        #     'city': [city_name],
        #     # json['aqi'],                 
        #     'date': [json['time']['s'][:10]],      # Date
        #     'pm25' : [iaqi['pm25']['v']],
        #     'pm10': [iaqi['pm10']['v']],
        #     'no2': [iaqi['no2']['v']],
        #     'so2': [iaqi['so2']['v']],
        #     'co': [iaqi['co']['v']],
        #     'o3': [iaqi['o3']['v']]
        # })
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
            
            return pd.DataFrame({
                'city': [city_name],
                'date': [data['time']['s'][:10]],
                **{param: [iaqi[param]['v']] for param in params}
            })
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching air quality data: {str(e)}")
            raise
    
    def process_features(self, weather_data: pd.DataFrame, 
                        air_quality_data: pd.DataFrame) -> pd.DataFrame:
        """Process and combine weather and air quality features."""
        try:
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
            features['pm25'] = features['pm25'].str.strip()
            features['pm25'] = features['pm25'].replace(' ', np.nan)
            features['pm25'] = pd.to_numeric(features['pm25'], errors='coerce')
            features['pm25'] = features['pm25'].astype('Int64') 
            
            # Map weather conditions to numerical values
            conditions = {
                'Clear': 1, 'Partially cloudy': 2,
                'Rain, Partially cloudy': 3,
                'Rain': 4, 'Overcast': 5,
                'Rain, Overcast': 6
                }
            features['conditions'] = features['conditions'].map(conditions)

            # features['date'] = pd.to_datetime(features['date'])

            # Add timestamp and record_id if not present
            if 'timestamp' not in features.columns:
                features['timestamp'] = pd.Series([int(round(time.time()))] * len(features), dtype="float64")
            if 'record_id' not in features.columns:
                features['record_id'] = features.index.astype(str)

            return features  
        
        except Exception as e:
            logger.error(f"Error processing features: {str(e)}")
            raise  
        
    def write_to_feature_store(self, features: pd.DataFrame) -> None:
        """Write processed features to SageMaker Feature Store."""
        for idx, row in features.iterrows():
            record = [
                {
                    'FeatureName': column,
                    'ValueAsString': str(row[column])
                }
                for column in features.columns
            ]
            
            try:
                self.featurestore_runtime.put_record(
                    FeatureGroupName=self.feature_group_name,
                    Record=record
                )
                logger.info(f"Successfully wrote record {idx} to Feature Store")
            except Exception as e:
                logger.error(f"Error writing record {idx} to Feature Store: {str(e)}")
                raise

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
            
            return features
            
        except Exception as e:
            logger.error(f"Pipeline execution failed: {str(e)}")
            raise