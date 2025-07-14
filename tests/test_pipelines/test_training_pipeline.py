# tests/test_pipelines/test_training_pipeline.py
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from pipelines.training_pipeline import TrainingPipeline

def test_data_preparation():
    # Use your existing Feature Store bucket with new folders
    table_name = "air_quality_features_08_14_56_40_1744124210" 
    bucket_name = "sagemaker-us-east-1-784376946367" 
    
    # Initialize training pipeline
    pipeline = TrainingPipeline(table_name, bucket_name)
    
    # Test data preparation
    print("Starting data preparation...")
    df = pipeline.prepare_training_data()
    
    if df is not None:
        print(f"Success! Retrieved {len(df)} records")
        print(f"Columns: {df.columns.tolist()}")
        print(f"Sample data:")
        print(df.head())
        print(f"Data types:")
        print(df.dtypes)
        print(f"PM2.5 stats:")
        print(df['pm25'].describe())
    else:
        print("Failed to prepare training data")

if __name__ == "__main__":
    test_data_preparation()