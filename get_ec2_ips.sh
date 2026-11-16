#!/bin/bash
PROFILE="PROFILE_NAME"

while IFS= read -r instance; do
    aws ec2 describe-instances --instance-ids "$instance" --profile "$PROFILE" --query "Reservations[].Instances[].[InstanceId,PublicIpAddress,PrivateIpAddress,State.Name]" --output text
done < instance_ids.txt
