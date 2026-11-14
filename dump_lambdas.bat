@echo off
setlocal enabledelayedexpansion
aws lambda list-functions --profile PROFILE_NAME --query "Functions[].FunctionName" --output json > lambda_list.json
python -I -c "import json;[print(a.strip()) for a in json.load(open('lambda_list.json'))]" > lambda_list.txt

if not exist lambda_code mkdir lambda_code

echo.
echo === LAMBDA ENVIRONMENT VARIABLES ===
echo.
for /f "delims=" %%a in (lambda_list.txt) do call :checkenv "%%a"

echo.
echo === DOWNLOADING LAMBDA CODE ===
echo.
for /f "delims=" %%a in (lambda_list.txt) do call :getcode "%%a"
goto :eof

:checkenv
echo %~1
aws lambda get-function-configuration --function-name "%~1" --profile PROFILE_NAME --query "Environment.Variables" --output json
echo ============================================================
goto :eof

:getcode
echo Downloading: %~1
for /f "delims=" %%u in ('aws lambda get-function --function-name "%~1" --profile PROFILE_NAME --query "Code.Location" --output text') do (
    curl -s -o "lambda_code\%~1.zip" "%%u"
)
echo Saved to lambda_code\%~1.zip
echo ============================================================
goto :eof
