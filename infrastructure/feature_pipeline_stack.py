# infrastructure/feature_pipeline_stack.py
from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_events as events,
<<<<<<< HEAD
=======
    aws_events_targets as targets,
>>>>>>> 49a6fcfd8ebc68d07fc025c01259e5bf6d637156
    aws_iam as iam,
    aws_secretsmanager as secretsmanager,
    Duration
)
<<<<<<< HEAD
from aws_cdk.aws_events_targets import LambdaFunction
=======
>>>>>>> 49a6fcfd8ebc68d07fc025c01259e5bf6d637156
from constructs import Construct
import os

class FeaturePipelineStack(Stack):
<<<<<<< HEAD
    def __init__(self, scope: Construct, construct_id: str, *, base_layer=None, ml_layer=None, feature_pipeline_layer=None, **kwargs) -> None:
=======
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
>>>>>>> 49a6fcfd8ebc68d07fc025c01259e5bf6d637156
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

<<<<<<< HEAD
        # Reference existing Lambda layers by ARN
        pandasNumpyLayer = _lambda.LayerVersion.from_layer_version_arn(
            self, 'ExistingBaseLayer',
            layer_version_arn='arn:aws:lambda:us-east-1:784376946367:layer:pandas-numpy-layer:1'
        )

        feature_pipeline_layer = _lambda.LayerVersion.from_layer_version_arn(
            self, 'ExistingFeaturePipelineLayer',
            layer_version_arn='arn:aws:lambda:us-east-1:784376946367:layer:featurePipelineLayer:1'
        )
        
        # Create a list of layers to use
        layers = [pandasNumpyLayer, feature_pipeline_layer]
        


        feature_pipeline_lambda = _lambda.Function(
            self, 'FeaturePipelineLambda',
            runtime=_lambda.Runtime.PYTHON_3_10,
            handler='lambda.feature_pipeline_handler.lambda_handler',
            code=_lambda.Code.from_asset('src'),
            layers=layers,
            timeout=Duration.minutes(5),
            memory_size=1024,
            environment={
                'WEATHER_API_SECRET_NAME': 'weather-api-key-4ZbyEj',
                'AIR_QUALITY_API_SECRET_NAME': 'air-quality-api-key-AM8xem',
=======
        # Create Lambda function
        feature_pipeline_lambda = _lambda.Function(
            self, 'FeaturePipelineLambda',
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler='lambda.feature_pipeline_handler.lambda_handler',
            code=_lambda.Code.from_asset(
                'src',
                bundling={
                    'image': _lambda.Runtime.PYTHON_3_9.bundling_image,
                    'command': [
                        "bash", "-c",
                        "pip install --target /asset-output/ -r requirements.txt && cp -au . /asset-output/"
                    ],
                }
            ),
            timeout=Duration.minutes(5),
            memory_size=1024,
            environment={
                'WEATHER_API_SECRET_NAME': 'weather-api-key-4ZbyEj',  # Use exact secret name
                'AIR_QUALITY_API_SECRET_NAME': 'air-quality-api-key-AM8xem',  # Use exact secret name
>>>>>>> 49a6fcfd8ebc68d07fc025c01259e5bf6d637156
                'FEATURE_GROUP_NAME': 'air-quality-features-08-14-56-40',
                'CITIES': 'los angeles'
            }
        )

        feature_pipeline_lambda.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
<<<<<<< HEAD
                    'secretsmanager:GetSecretValue',
                    'secretsmanager:DescribeSecret',
                    'secretsmanager:ListSecrets'
                ],
                resources=[
                    '*'
                    # f'arn:aws:secretsmanager:{Stack.of(self).region}:{Stack.of(self).account}:secret:weather-api-key-4ZbyEj-*',
                    # f'arn:aws:secretsmanager:{Stack.of(self).region}:{Stack.of(self).account}:secret:air-quality-api-key-AM8xem-*'
=======
                    'secretsmanager:GetSecretValue'
                ],
                resources=[
                    f'arn:aws:secretsmanager:{Stack.of(self).region}:{Stack.of(self).account}:secret:weather-api-key-4ZbyEj-*',
                    f'arn:aws:secretsmanager:{Stack.of(self).region}:{Stack.of(self).account}:secret:air-quality-api-key-AM8xem-*'
>>>>>>> 49a6fcfd8ebc68d07fc025c01259e5bf6d637156
                ]
            )
        )

        # Grant Lambda permission to read secrets
<<<<<<< HEAD
        # weather_api_secret.grant_read(feature_pipeline_lambda)
        # air_quality_api_secret.grant_read(feature_pipeline_lambda)
=======
        weather_api_secret.grant_read(feature_pipeline_lambda)
        air_quality_api_secret.grant_read(feature_pipeline_lambda)
>>>>>>> 49a6fcfd8ebc68d07fc025c01259e5bf6d637156

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
<<<<<<< HEAD
        rule.add_target(LambdaFunction(feature_pipeline_lambda))
=======
        rule.add_target(targets.LambdaFunction(feature_pipeline_lambda))
>>>>>>> 49a6fcfd8ebc68d07fc025c01259e5bf6d637156

        # Add SageMaker permissions
        feature_pipeline_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    'sagemaker:PutRecord',
                    'sagemaker:DescribeFeatureGroup'
                ],
                resources=['*']
            )
<<<<<<< HEAD
        )
=======
        )
>>>>>>> 49a6fcfd8ebc68d07fc025c01259e5bf6d637156
