# tests/conftest.py
import pytest
import os
from unittest.mock import patch

@pytest.fixture(autouse=True)
def env_setup():
    """Setup environment variables for testing"""
    with patch.dict(os.environ, {
        'WEATHER_API_KEY': 'test_weather_key',
        'AIR_QUALITY_API_KEY': 'test_air_key',
        'FEATURE_GROUP_NAME': 'test-feature-group'
    }):
        yield

@pytest.fixture
def sample_weather_data():
    """Sample weather API response"""
    return {
        'days': [{
            'datetime': '2024-01-20',
            'temp': 72,
            'humidity': 65,
            'conditions': 'Clear'
        }]
    }

@pytest.fixture
def sample_air_quality_data():
    """Sample air quality API response"""
    return {
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
