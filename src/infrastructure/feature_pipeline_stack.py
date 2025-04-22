# infrastructure/feature_pipeline_stack.py
from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_events as events,
    aws_events_targets as targets,
    aws_iam as iam,
    Duration
)
from constructs import Construct

class FeaturePipelineStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Create Lambda function
        feature_pipeline_lambda = _lambda.Function(
            self, 'FeaturePipelineLambda',
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset('src/lambda'),
            handler='feature_pipeline_handler.lambda_handler',
            timeout=Duration.minutes(5),
            environment={
                'FEATURE_GROUP_NAME': 'air-quality-features-08-14-56-40',
                'CITIES': 'los angeles',
                'WEATHER_API_KEY': '{{resolve:secretsmanager:weather-api-key}}',
                'AIR_QUALITY_API_KEY': '{{resolve:secretsmanager:air-quality-api-key}}'
            }
        )

        # Add necessary permissions
        feature_pipeline_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    'sagemaker:PutRecord',
                    'sagemaker:DescribeFeatureGroup'
                ],
                resources=['*']
            )
        )

        # Create EventBridge rule to trigger Lambda
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
