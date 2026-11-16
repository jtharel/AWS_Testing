#!/bin/bash
PROFILE="PROFILE_NAME"

aws cloudformation list-stacks --profile "$PROFILE" --query "StackSummaries[?StackStatus!='DELETE_COMPLETE'].StackName" --output json > cf_stacks.json
python3 -I -c "import json;[print(a.strip()) for a in json.load(open('cf_stacks.json'))]" > cf_stacks.txt

echo ""
echo "STACK PARAMETERS"
echo ""
while IFS= read -r stack; do
    echo "$stack"
    aws cloudformation describe-stacks --stack-name "$stack" --profile "$PROFILE" --query "Stacks[].Parameters[]" --output json
    echo "============================================================"
done < cf_stacks.txt

echo ""
echo "STACK OUTPUTS"
echo ""
while IFS= read -r stack; do
    echo "$stack"
    aws cloudformation describe-stacks --stack-name "$stack" --profile "$PROFILE" --query "Stacks[].Outputs[]" --output json
    echo "============================================================"
done < cf_stacks.txt
