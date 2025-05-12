from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
)
from constructs import Construct

class FeaturePipelineLayerStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create feature pipeline dependencies layer (requests, tenacity, dotenv)
        self.feature_pipeline_layer = _lambda.LayerVersion(
            self, 'FeaturePipelineDependenciesLayer',
            code=_lambda.Code.from_asset('lambda_layer_feature_pipeline'),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_9],
            description='Feature pipeline dependencies layer including requests, tenacity, and python-dotenv'
        )