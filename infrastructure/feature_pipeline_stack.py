# infrastructure/feature_pipeline_stack.py
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
import os

class FeaturePipelineStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, *, base_layer=None, ml_layer=None, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Import existing secrets
        weather_api_secret = secretsmanager.Secret.from_secret_name_v2(
            self, 'WeatherAPISecret',
            'weather-api-key-4ZbyEj'
        )

        air_quality_api_secret = secretsmanager.Secret.from_secret_name_v2(
            self, 'AirQualityAPISecret',
            'air-quality-api-key-AM8xem'
        )

        feature_pipeline_lambda = _lambda.Function(
            self, 'FeaturePipelineLambda',
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler='lambda.feature_pipeline_handler.lambda_handler',
            code=_lambda.Code.from_asset('src'),
            layers=[base_layer, ml_layer] if base_layer and ml_layer else [],
            timeout=Duration.minutes(5),
            memory_size=1024,
            environment={
                'WEATHER_API_SECRET_NAME': 'weather-api-key-4ZbyEj',
                'AIR_QUALITY_API_SECRET_NAME': 'air-quality-api-key-AM8xem',
                'FEATURE_GROUP_NAME': 'air-quality-features-08-14-56-40',
                'CITIES': 'los angeles'
            }
        )

        feature_pipeline_lambda.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    'secretsmanager:GetSecretValue'
                ],
                resources=[
                    f'arn:aws:secretsmanager:{Stack.of(self).region}:{Stack.of(self).account}:secret:weather-api-key-4ZbyEj-*',
                    f'arn:aws:secretsmanager:{Stack.of(self).region}:{Stack.of(self).account}:secret:air-quality-api-key-AM8xem-*'
                ]
            )
        )

        # Grant Lambda permission to read secrets
        weather_api_secret.grant_read(feature_pipeline_lambda)
        air_quality_api_secret.grant_read(feature_pipeline_lambda)

        # Add CloudWatch permissions
        feature_pipeline_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    'cloudwatch:PutMetricData',
                    'cloudwatch:GetMetricData',
                    'cloudwatch:GetMetricStatistics',
                    'cloudwatch:ListMetrics'
                ],
                resources=['*']
            )
        )

        # Create EventBridge rule
        rule = events.Rule(
            self, 'FeaturePipelineSchedule',
            schedule=events.Schedule.cron(
                minute='0',
                hour='12',
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
