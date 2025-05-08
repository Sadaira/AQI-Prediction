# create_base_layer.ps1
$ErrorActionPreference = "Stop"

# Clean up existing files
if (Test-Path "lambda_layer_base/python") {
    Remove-Item -Recurse -Force "lambda_layer_base/python"
}
New-Item -ItemType Directory -Force -Path "lambda_layer_base/python"
Set-Location "lambda_layer_base/python"

# Install base packages
pip install `
    --platform manylinux2014_x86_64 `
    --target . `
    --implementation cp `
    --python-version 3.9 `
    --only-binary=:all: `
    numpy==1.24.3 `
    pandas==2.0.3

# Clean up
Get-ChildItem -Recurse -Include "__pycache__","*.pyc","*.pyo","*.pyd","tests","docs" | Remove-Item -Recurse -Force
Set-Location "../.."
