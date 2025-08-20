import streamlit as st
import boto3
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# Configure page
st.set_page_config(page_title="LA Air Quality Predictor", page_icon="🌬️", layout="wide")

# Initialize SageMaker runtime
@st.cache_resource
def get_sagemaker_client():
    return boto3.client('sagemaker-runtime')

runtime = get_sagemaker_client()

# App header
st.title("🌬️ Los Angeles Air Quality Predictor")
st.markdown("Predict PM2.5 levels using real-time weather data powered by AWS SageMaker")

# Sidebar for inputs
st.sidebar.header("Weather Conditions")

# Input widgets
temp = st.sidebar.slider("Temperature (°F)", 40, 110, 75)
humidity = st.sidebar.slider("Humidity (%)", 10, 100, 65)
precip = st.sidebar.slider("Precipitation (inches)", 0.0, 2.0, 0.0, 0.1)
windspeed = st.sidebar.slider("Wind Speed (mph)", 0, 30, 8)
cloudcover = st.sidebar.slider("Cloud Cover (%)", 0, 100, 25)
visibility = st.sidebar.slider("Visibility (miles)", 1, 15, 10)
solarradiation = st.sidebar.slider("Solar Radiation (W/m²)", 0, 500, 250)

# Prediction button
if st.sidebar.button("🔮 Predict Air Quality", type="primary"):
    # Prepare data
    features = [temp, humidity, precip, windspeed, cloudcover, visibility, solarradiation]
    csv_data = ','.join([str(f) for f in features])
    
    try:
        # Make prediction
        response = runtime.invoke_endpoint(
            EndpointName="aqi-prediction-20250818-161138",
            ContentType='text/csv',
            Body=csv_data
        )
        
        predicted_pm25 = float(response['Body'].read().decode().strip())
        
        # Display results
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Predicted PM2.5", f"{predicted_pm25:.1f} µg/m³")
            
            # AQI category
            if predicted_pm25 <= 12:
                aqi_category = "Good"
                color = "green"
            elif predicted_pm25 <= 35:
                aqi_category = "Moderate"
                color = "yellow"
            elif predicted_pm25 <= 55:
                aqi_category = "Unhealthy for Sensitive Groups"
                color = "orange"
            else:
                aqi_category = "Unhealthy"
                color = "red"
            
            st.markdown(f"**Air Quality:** :{color}[{aqi_category}]")
        
        with col2:
            # Gauge chart
            fig = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = predicted_pm25,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "PM2.5 Level"},
                gauge = {
                    'axis': {'range': [None, 100]},
                    'bar': {'color': color},
                    'steps': [
                        {'range': [0, 12], 'color': "lightgreen"},
                        {'range': [12, 35], 'color': "yellow"},
                        {'range': [35, 55], 'color': "orange"},
                        {'range': [55, 100], 'color': "red"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ))
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
        
        # Weather summary
        st.subheader("Current Weather Conditions")
        weather_data = {
            "Metric": ["Temperature", "Humidity", "Precipitation", "Wind Speed", "Cloud Cover", "Visibility", "Solar Radiation"],
            "Value": [f"{temp}°F", f"{humidity}%", f"{precip}\"", f"{windspeed} mph", f"{cloudcover}%", f"{visibility} mi", f"{solarradiation} W/m²"]
        }
        st.table(pd.DataFrame(weather_data))
        
    except Exception as e:
        st.error(f"Prediction failed: {e}")

# Information section
st.markdown("---")
st.subheader("About This Model")
st.markdown("""
- **Model**: XGBoost Regression trained on 1800+ historical records
- **Features**: Weather data from Visual Crossing API
- **Target**: PM2.5 air quality measurements
- **Infrastructure**: AWS SageMaker Feature Store, Training Jobs, and Real-time Endpoints
""")

st.markdown("**PM2.5 Guidelines:**")
st.markdown("- 🟢 **Good (0-12)**: Air quality is satisfactory")
st.markdown("- 🟡 **Moderate (12-35)**: Acceptable for most people")  
st.markdown("- 🟠 **Unhealthy for Sensitive (35-55)**: May cause issues for sensitive individuals")
st.markdown("- 🔴 **Unhealthy (55+)**: Everyone may experience health effects")