@echo off
aws cloudformation list-stacks --profile PROFILE_NAME --query "StackSummaries[?StackStatus!='DELETE_COMPLETE'].StackName" --output json > cf_stacks.json
python -I -c "import json;[print(a.strip()) for a in json.load(open('cf_stacks.json'))]" > cf_stacks.txt

echo.
echo STACK PARAMETERS
echo.
for /f "delims=" %%a in (cf_stacks.txt) do call :checkparams "%%a"

echo.
echo STACK OUTPUTS
echo.
for /f "delims=" %%a in (cf_stacks.txt) do call :checkoutputs "%%a"
goto :eof

:checkparams
echo %~1
aws cloudformation describe-stacks --stack-name "%~1" --profile PROFILE_NAME --query "Stacks[].Parameters[]" --output json
echo ============================================================
goto :eof

:checkoutputs
echo %~1
aws cloudformation describe-stacks --stack-name "%~1" --profile PROFILE_NAME --query "Stacks[].Outputs[]" --output json
echo ============================================================
goto :eof
