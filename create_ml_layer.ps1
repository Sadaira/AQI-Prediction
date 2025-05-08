# create_ml_layer.ps1
$ErrorActionPreference = "Stop"

# Clean up existing files
if (Test-Path "lambda_layer_ml/python") {
    Remove-Item -Recurse -Force "lambda_layer_ml/python"
}
New-Item -ItemType Directory -Force -Path "lambda_layer_ml/python"
Set-Location "lambda_layer_ml/python"

# Install ML packages
pip install `
    --platform manylinux2014_x86_64 `
    --target . `
    --implementation cp `
    --python-version 3.9 `
    --only-binary=:all: `
    scikit-learn==1.3.0 `
    xgboost==2.0.1

# Clean up
Get-ChildItem -Recurse -Include "__pycache__","*.pyc","*.pyo","*.pyd","tests","docs" | Remove-Item -Recurse -Force
Set-Location "../.."
