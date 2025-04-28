#!/usr/bin/env python3
from aws_cdk import App, Environment
from infrastructure.feature_pipeline_stack import FeaturePipelineStack
from infrastructure.lambda_layer_stack import LambdaLayerStack

app = App()
env = Environment(
    region='us-east-1'
)
# Create the Lambda Layer stack
lambda_layer_stack = LambdaLayerStack(app, "AQIPredictionLambdaLayer", env=env)

# Create the Feature Pipeline stack with the layer
FeaturePipelineStack(
    app, 
    "AQIPredictionFeaturePipeline",
    lambda_layer=lambda_layer_stack.lambda_layer,
    env=env
)

app.synth()