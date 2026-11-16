#!/bin/bash
PROFILE="PROFILE_NAME"

while IFS= read -r region; do
    echo "region: $region"
    aws ec2 describe-instances --profile "$PROFILE" --region "$region" --filters "Name=metadata-options.http-tokens,Values=optional" --query "Reservations[].Instances[].[InstanceId,State.Name]" --output table
    echo "============================================"
done < regions.txt
