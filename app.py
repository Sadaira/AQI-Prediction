from aws_cdk import App
from infrastructure.feature_pipeline_stack import FeaturePipelineStack
from infrastructure.lambda_layer_stack import LambdaLayerStack

app = App()

# Create the layer stack first
layer_stack = LambdaLayerStack(app, "AQIPredictionLambdaLayer")

# Create the feature pipeline stack with both layers
feature_pipeline = FeaturePipelineStack(
    app, "AQIPredictionFeaturePipeline",
    base_layer=layer_stack.base_layer,
    ml_layer=layer_stack.ml_layer
)

app.synth()
