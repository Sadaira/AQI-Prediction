# src/lambda/feature_pipeline_handler.py
import os
import json
import logging
from datetime import datetime
from ..pipelines.feature_pipeline import FeaturePipeline

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    try:
        # Initialize feature pipeline
        pipeline = FeaturePipeline(
            feature_group_name=os.environ['FEATURE_GROUP_NAME']
        )
        
        # Get cities from environment variable (comma-separated)
        cities = os.environ.get('CITIES', 'los angeles').split(',')
        
        results = {}
        for city in cities:
            try:
                features = pipeline.run_pipeline(city=city.strip())
                results[city] = 'success'
                logger.info(f"Successfully processed features for {city}")
            except Exception as e:
                results[city] = f'failed: {str(e)}'
                logger.error(f"Failed to process features for {city}: {str(e)}")
        
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
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
        }
