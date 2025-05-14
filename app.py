from aws_cdk import App
from infrastructure.feature_pipeline_stack import FeaturePipelineStack

app = App()

# Create the feature pipeline stack with references to existing layers
feature_pipeline = FeaturePipelineStack(app, "AQIPredictionFeaturePipeline")

app.synth()
