from aws_cdk import App
from infrastructure.feature_pipeline_stack import FeaturePipelineStack
from infrastructure.lambda_layer_stack import LambdaLayerStack
from infrastructure.feature_pipeline_layer_stack import FeaturePipelineLayerStack

app = App()

# Create the layer stacks first
layer_stack = LambdaLayerStack(app, "AQIPredictionLambdaLayer")
feature_pipeline_layer_stack = FeaturePipelineLayerStack(app, "AQIPredictionFeaturePipelineLayer")

# Create the feature pipeline stack with all layers
feature_pipeline = FeaturePipelineStack(
    app, "AQIPredictionFeaturePipeline",
    base_layer=layer_stack.base_layer,
    ml_layer=layer_stack.ml_layer,
    feature_pipeline_layer=feature_pipeline_layer_stack.feature_pipeline_layer
)

app.synth()