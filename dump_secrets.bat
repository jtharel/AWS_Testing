@echo off
aws secretsmanager list-secrets --profile PROFILE_NAME --query "SecretList[].Name" --output json > secrets_list.json
python -I -c "import json;[print(a.strip()) for a in json.load(open('secrets_list.json'))]" > secrets_list.txt
for /f "delims=" %%a in (secrets_list.txt) do call :check "%%a"
goto :eof

:check
echo %~1
aws secretsmanager get-secret-value --secret-id "%~1" --profile PROFILE_NAME --query "{Value:SecretString,Binary:SecretBinary}" --output json
echo ============================================================
goto :eof
