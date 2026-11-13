@echo off
aws iam list-users --profile PROFILE_NAME --query "Users[].UserName" --output json > users_list.json
python -I -c "import json;[print(a.strip()) for a in json.load(open('users_list.json'))]" > users_list.txt
for /f "delims=" %%a in (users_list.txt) do call :check "%%a"
goto :eof

:check
echo === User %~1 ===
echo.
echo -- Directly Attached Policies (FINDING if not empty) --
aws iam list-attached-user-policies --user-name "%~1" --profile PROFILE_NAME --query "AttachedPolicies[].PolicyName" --output text
echo.
echo -- Inline Policies (FINDING if not empty) --
aws iam list-user-policies --user-name "%~1" --profile PROFILE_NAME --query "PolicyNames" --output text
echo.
echo -- Groups --
aws iam list-groups-for-user --user-name "%~1" --profile PROFILE_NAME --query "Groups[].GroupName" --output text
echo.
echo -- Policies Inherited Through Groups --
for /f "delims=" %%g in ('aws iam list-groups-for-user --user-name "%~1" --profile PROFILE_NAME --query "Groups[].GroupName" --output text') do call :groupcheck "%%g"
echo ============================================================
goto :eof

:groupcheck
echo   Group: %~1
aws iam list-attached-group-policies --group-name "%~1" --profile PROFILE_NAME --query "AttachedPolicies[].PolicyName" --output text
aws iam list-group-policies --group-name "%~1" --profile PROFILE_NAME --query "PolicyNames" --output text
goto :eof
