@echo off
for /f "delims=" %%a in (ec2_instance_ids.txt) do call :check "%%a"
goto :eof

:check
aws ec2 describe-instances --instance-ids "%~1" --profile PROFILE_NAME --query "Reservations[].Instances[].[InstanceId,PublicIpAddress,PrivateIpAddress,State.Name]" --output text
goto :eof
