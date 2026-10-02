$projectRoot = Split-Path -Parent $PSScriptRoot

$env:PYTHONPATH = $projectRoot

uvicorn app.main:app --host 0.0.0.0 --port 8000