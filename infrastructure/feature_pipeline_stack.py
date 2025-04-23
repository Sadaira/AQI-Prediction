from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_events as events,
    aws_events_targets as targets,
    aws_iam as iam,
    aws_secretsmanager as secretsmanager,
    Duration
)
from constructs import Construct

class FeaturePipelineStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Import existing secrets
        weather_api_secret = secretsmanager.Secret.from_secret_name_v2(
            self, 'WeatherAPISecret',
            'weather-api-key'
        )

        air_quality_api_secret = secretsmanager.Secret.from_secret_name_v2(
            self, 'AirQualityAPISecret',
            'air-quality-api-key'
        )

        # Create Lambda function
        feature_pipeline_lambda = _lambda.Function(
            self, 'FeaturePipelineLambda',
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler='feature_pipeline_handler.lambda_handler',
            code=_lambda.Code.from_asset('src/lambda'),
            timeout=Duration.minutes(5),
            environment={
                'WEATHER_API_SECRET_NAME': weather_api_secret.secret_name,
                'AIR_QUALITY_API_SECRET_NAME': air_quality_api_secret.secret_name
            }
        )

        # Grant Lambda permission to read secrets
        weather_api_secret.grant_read(feature_pipeline_lambda)
        air_quality_api_secret.grant_read(feature_pipeline_lambda)

        # Create EventBridge rule to run daily at a specific time (e.g., 12:00 PM UTC)
        rule = events.Rule(
            self, 'FeaturePipelineSchedule',
            schedule=events.Schedule.cron(
                minute='0',
                hour='12',  # This will run at 12:00 PM UTC (adjust as needed)
                day='*',
                month='*',
                year='*'
            )
        )

        # Add Lambda as target
        rule.add_target(targets.LambdaFunction(feature_pipeline_lambda))

        # Add SageMaker permissions
        feature_pipeline_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    'sagemaker:PutRecord',
                    'sagemaker:DescribeFeatureGroup'
                ],
                resources=['*']
            )
        )
