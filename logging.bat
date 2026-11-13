@echo off
echo CloudTrail
aws cloudtrail describe-trails --profile PROFILE_NAME
echo =======================
echo Config Recorders
aws configservice describe-configuration-recorder-status --profile PROFILE_NAME
echo =======================
echo GuardDuty
aws guardduty list-detectors --profile PROFILE_NAME
echo ======================
echo SecurityHub
aws securityhub describe-hub --profile PROFILE_NAME
echo ======================
echo VPC Flow Logs
aws ec2 describe-flow-logs --profile PROFILE_NAME --output table
echo ======================
echo CloudWatch Log Groups
aws logs describe-log-groups --profile PROFILE_NAME --query "logGroups[].[logGroupName,retentionInDays]" --output table


