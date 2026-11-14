@echo off
setlocal enabledelayedexpansion

set PROFILE=PROFILE_NAME

echo ========================================
echo SSM PARAMETER STORE AUDIT
echo ========================================
echo.

echo [*] Listing all SSM parameters...
aws ssm describe-parameters --profile %PROFILE% --output json > ssm_params.json

echo.
echo ========================================
echo SSM Parameter Values (decrypted)
echo ========================================
echo.

for /f "delims=" %%N in ('python -I -c "import json;[print(p['Name']) for p in json.load(open('ssm_params.json')).get('Parameters',[])]"') do (
    echo ----------------------------------------
    echo Parameter: %%N
    echo ----------------------------------------
    aws ssm get-parameter --name "%%N" --with-decryption --profile %PROFILE% --output json
    echo.
)

echo ========================================
echo Done.
echo ========================================
