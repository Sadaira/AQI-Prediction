# infrastructure/lambda_layer_stack.py
from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
)
from constructs import Construct

class LambdaLayerStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create Lambda Layer
        self.lambda_layer = _lambda.LayerVersion(
            self, 'MLDependenciesLayer',
            code=_lambda.Code.from_asset('lambda_layer'),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_9],
            description='ML dependencies layer including numpy, pandas, scikit-learn, and xgboost'
        )
