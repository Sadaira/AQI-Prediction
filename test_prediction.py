import boto3
import json

# Test prediction with sample weather data
runtime = boto3.client('sagemaker-runtime')

# Sample weather features (Los Angeles typical values)
sample_features = {
    'temp': 75.0,      # Temperature in F
    'humidity': 65.0,   # Humidity %
    'precip': 0.0,     # Precipitation
    'windspeed': 8.5,  # Wind speed
    'cloudcover': 25.0, # Cloud cover %
    'visibility': 10.0, # Visibility
    'solarradiation': 250.0 # Solar radiation
}

# Convert to CSV format for XGBoost
feature_order = ['temp', 'humidity', 'precip', 'windspeed', 'cloudcover', 'visibility', 'solarradiation']
csv_data = ','.join([str(sample_features[col]) for col in feature_order])

# Replace with your actual endpoint name
endpoint_name = "aqi-prediction-20250818-161138"

try:
    response = runtime.invoke_endpoint(
        EndpointName=endpoint_name,
        ContentType='text/csv',
        Body=csv_data
    )
    
    result = response['Body'].read().decode()
    predicted_pm25 = float(result.strip())
    
    print(f"Weather conditions: {sample_features}")
    print(f"Predicted PM2.5: {predicted_pm25:.2f} µg/m³")
    
except Exception as e:
    print(f"Error: {e}")
    print("Make sure to update the endpoint_name variable with your actual endpoint name")