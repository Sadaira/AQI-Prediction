# app.py
#!/usr/bin/env python3
from aws_cdk import App
from infrastructure.feature_pipeline_stack import FeaturePipelineStack

app = App()
FeaturePipelineStack(app, "AQIPredictionFeaturePipeline")
app.synth()
