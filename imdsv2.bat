@echo off
for /f %%r in (regions.txt) do call :check %%r
goto :eof

:check
echo region: %1
aws ec2 describe-instances --profile PROFILE_NAME --region %1 --filters "Name=metadata-options.http-tokens,Values=optional" --query "Reservations[].Instances[].[InstanceId,State.Name]" --output table
echo "============================================"
goto :eof
