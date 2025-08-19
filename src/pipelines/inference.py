import joblib
import pandas as pd
import os

def model_fn(model_dir):
    """Load model from the model directory"""
    model = joblib.load(os.path.join(model_dir, 'model.joblib'))
    return model

def input_fn(request_body, content_type='text/csv'):
    """Parse input data"""
    if content_type == 'text/csv':
        # Parse CSV input
        features = request_body.strip().split(',')
        feature_names = ['temp', 'humidity', 'precip', 'windspeed', 'cloudcover', 'visibility', 'solarradiation']
        data = pd.DataFrame([features], columns=feature_names, dtype=float)
        return data
    else:
        raise ValueError(f"Unsupported content type: {content_type}")

def predict_fn(input_data, model):
    """Make prediction"""
    prediction = model.predict(input_data)
    return prediction[0]

def output_fn(prediction, accept='text/csv'):
    """Format output"""
    return str(prediction)