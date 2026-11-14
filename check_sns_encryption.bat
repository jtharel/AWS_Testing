@echo off
setlocal enabledelayedexpansion
aws sns list-topics --profile PROFILE_NAME --query "Topics[].TopicArn" --output json > sns_topics.json
python -I -c "import json;[print(a.strip()) for a in json.load(open('sns_topics.json'))]" > sns_topics.txt
echo.
for /f "delims=" %%a in (sns_topics.txt) do call :check "%%a"
goto :eof

:check
set "RESULT="
for /f "delims=" %%r in ('aws sns get-topic-attributes --topic-arn "%~1" --profile PROFILE_NAME --query "Attributes.KmsMasterKeyId" --output text 2^>^&1') do set "RESULT=%%r"
if "!RESULT!"=="" (
    echo [NOT ENCRYPTED] %~1
) else if "!RESULT!"=="None" (
    echo [NOT ENCRYPTED] %~1
) else (
    echo !RESULT! | findstr /i "ERROR" >nul 2>&1
    if !errorlevel!==0 (
        echo [ERROR] %~1
    ) else (
        echo [ENCRYPTED - !RESULT!] %~1
    )
)
goto :eof
