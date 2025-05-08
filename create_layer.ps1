# create_layer.ps1
$ErrorActionPreference = "Stop"

# Clean up existing files
if (Test-Path "lambda_layer/python") {
    Remove-Item -Recurse -Force "lambda_layer/python"
}

# Create directories
New-Item -ItemType Directory -Force -Path "lambda_layer/python"
Set-Location "lambda_layer/python"

# Install packages with specific platform and Python version
pip install `
    --platform manylinux2014_x86_64 `
    --target . `
    --implementation cp `
    --python-version 3.9 `
    --only-binary=:all: `
    numpy==1.24.3 `
    pandas==2.0.3 `
    scikit-learn==1.3.0 `
    xgboost==2.0.1

# Clean up unnecessary files
Get-ChildItem -Recurse -Include "__pycache__","*.pyc","*.pyo","*.pyd","tests","docs" | Remove-Item -Recurse -Force

# Go back to project root
Set-Location "../.."
