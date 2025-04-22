# tests/test_feature_pipeline.py
import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch
from src.pipelines.feature_pipeline import FeaturePipeline

@pytest.fixture
def mock_feature_pipeline():
    with patch('boto3.client'):
        pipeline = FeaturePipeline(feature_group_name='test-feature-group')
        return pipeline

def test_fetch_weather_data(mock_feature_pipeline):
    with patch('requests.get') as mock_get:
        # Mock successful API response
        mock_get.return_value.json.return_value = {
            'days': [{
                'datetime': '2024-01-20',
                'temp': 72,
                'humidity': 65,
                'conditions': 'Clear'
            }]
        }
        mock_get.return_value.status_code = 200
        
        result = mock_feature_pipeline.fetch_weather_data()
        assert isinstance(result, pd.DataFrame)
        assert 'temp' in result.columns
        assert len(result) > 0

def test_fetch_air_quality_data(mock_feature_pipeline):
    with patch('requests.get') as mock_get:
        # Mock successful API response
        mock_get.return_value.json.return_value = {
            'data': {
                'time': {'s': '2024-01-20 00:00:00'},
                'iaqi': {
                    'pm25': {'v': 35},
                    'pm10': {'v': 40},
                    'no2': {'v': 15},
                    'so2': {'v': 5},
                    'co': {'v': 0.8},
                    'o3': {'v': 30}
                }
            }
        }
        mock_get.return_value.status_code = 200
        
        result = mock_feature_pipeline.fetch_air_quality_data()
        assert isinstance(result, pd.DataFrame)
        assert 'pm25' in result.columns
        assert len(result) > 0

def test_process_features(mock_feature_pipeline):
    # Create sample input data
    weather_data = pd.DataFrame({
        'datetime': ['2024-01-20'],
        'temp': [72],
        'humidity': [65],
        'conditions': ['Clear']
    })
    
    air_quality_data = pd.DataFrame({
        'date': ['2024-01-20'],
        'pm25': [35],
        'pm10': [40],
        'no2': [15],
        'so2': [5],
        'co': [0.8],
        'o3': [30]
    })
    
    result = mock_feature_pipeline.process_features(weather_data, air_quality_data)
    assert isinstance(result, pd.DataFrame)
    assert 'pm25' in result.columns
    assert 'temp' in result.columns
    assert 'timestamp' in result.columns

def test_write_to_feature_store(mock_feature_pipeline):
    test_features = pd.DataFrame({
        'date': ['2024-01-20'],
        'temp': [72],
        'humidity': [65],
        'pm25': [35],
        'timestamp': [1705708800],
        'record_id': ['0']
    })
    
    # Mock the featurestore_runtime client
    mock_feature_pipeline.featurestore_runtime.put_record = Mock()
    
    mock_feature_pipeline.write_to_feature_store(test_features)
    assert mock_feature_pipeline.featurestore_runtime.put_record.called
