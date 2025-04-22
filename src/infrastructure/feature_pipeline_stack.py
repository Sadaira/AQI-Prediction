# infrastructure/feature_pipeline_stack.py
from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_events as events,
    aws_events_targets as targets,
    aws_iam as iam,
    Duration,
    SecretValue
)
from constructs import Construct

class FeaturePipelineStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create Lambda function
        feature_pipeline_lambda = _lambda.Function(
            self, 'FeaturePipelineLambda',
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset('src'),  # Include entire src directory
            handler='lambda.feature_pipeline_handler.lambda_handler',
            timeout=Duration.minutes(5),
            environment={
                'FEATURE_GROUP_NAME': 'your-feature-group-name',
                'CITIES': 'los angeles',
                'WEATHER_API_KEY': SecretValue.secrets_manager('weather-api-key').to_string(),
                'AIR_QUALITY_API_KEY': SecretValue.secrets_manager('air-quality-api-key').to_string()
            }
        )

        # Add SageMaker Feature Store permissions
        feature_pipeline_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    'sagemaker:PutRecord',
                    'sagemaker:DescribeFeatureGroup'
                ],
                resources=['*']
            )
        )

        # Create EventBridge rule to trigger Lambda daily
        rule = events.Rule(
            self, 'FeaturePipelineSchedule',
            schedule=events.Schedule.cron(
                minute='0',
                hour='0',
                month='*',
                week_day='*',
                year='*'
            )
        )

        rule.add_target(targets.LambdaFunction(feature_pipeline_lambda))
