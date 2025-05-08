from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
)
from constructs import Construct

class LambdaLayerStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create base layer (numpy, pandas)
        self.base_layer = _lambda.LayerVersion(
            self, 'BaseDependenciesLayer',
            code=_lambda.Code.from_asset('lambda_layer_base'),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_9],
            description='Base dependencies layer including numpy and pandas'
        )

        # Create ML layer (scikit-learn, xgboost)
        self.ml_layer = _lambda.LayerVersion(
            self, 'MLDependenciesLayer',
            code=_lambda.Code.from_asset('lambda_layer_ml'),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_9],
            description='ML dependencies layer including scikit-learn and xgboost'
        )
