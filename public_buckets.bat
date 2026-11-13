@echo off

for /f %%b in (buckets.txt) do call :check %%b
get :eof

:check
echo Bucket %1
aws s3api get-bucket-acl --bucket %1 --profile PROFILE_NAME
echo =============================================
goto :eof
