@echo off
for /f %%b in (buckets.txt) do call :check %%b
get :eof

:check
echo Bucket %1
aws s3 ls s3://%1 --recursive --human-readable --summarize --profile PROFILE_NAME
echo ==============================================================
goto :eof
