#!/bin/bash
PROFILE="PROFILE_NAME"

echo "CloudTrail"
aws cloudtrail describe-trails --profile "$PROFILE"
echo "======================="
echo "Config Recorders"
aws configservice describe-configuration-recorder-status --profile "$PROFILE"
echo "======================="
echo "GuardDuty"
aws guardduty list-detectors --profile "$PROFILE"
echo "======================"
echo "SecurityHub"
aws securityhub describe-hub --profile "$PROFILE"
echo "======================"
echo "VPC Flow Logs"
aws ec2 describe-flow-logs --profile "$PROFILE" --output table
echo "======================"
echo "CloudWatch Log Groups"
aws logs describe-log-groups --profile "$PROFILE" --query "logGroups[].[logGroupName,retentionInDays]" --output table
