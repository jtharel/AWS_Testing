#!/bin/bash
PROFILE="PROFILE_NAME"

aws iam list-users --profile "$PROFILE" --query "Users[].UserName" --output json > users_list.json
python3 -I -c "import json;[print(a.strip()) for a in json.load(open('users_list.json'))]" > users_list.txt

while IFS= read -r user; do
    echo "=== User $user ==="
    echo ""
    echo "-- Directly Attached Policies (FINDING if not empty) --"
    aws iam list-attached-user-policies --user-name "$user" --profile "$PROFILE" --query "AttachedPolicies[].PolicyName" --output text
    echo ""
    echo "-- Inline Policies (FINDING if not empty) --"
    aws iam list-user-policies --user-name "$user" --profile "$PROFILE" --query "PolicyNames" --output text
    echo ""
    echo "-- Groups --"
    aws iam list-groups-for-user --user-name "$user" --profile "$PROFILE" --query "Groups[].GroupName" --output text
    echo ""
    echo "-- Policies Inherited Through Groups --"
    for group in $(aws iam list-groups-for-user --user-name "$user" --profile "$PROFILE" --query "Groups[].GroupName" --output text); do
        echo "  Group: $group"
        aws iam list-attached-group-policies --group-name "$group" --profile "$PROFILE" --query "AttachedPolicies[].PolicyName" --output text
        aws iam list-group-policies --group-name "$group" --profile "$PROFILE" --query "PolicyNames" --output text
    done
    echo "============================================================"
done < users_list.txt
