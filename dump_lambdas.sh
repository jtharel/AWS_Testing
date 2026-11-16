#!/bin/bash
PROFILE="PROFILE_NAME"

aws lambda list-functions --profile "$PROFILE" --query "Functions[].FunctionName" --output json > lambda_list.json
python3 -I -c "import json;[print(a.strip()) for a in json.load(open('lambda_list.json'))]" > lambda_list.txt

mkdir -p lambda_code

echo ""
echo "=== LAMBDA ENVIRONMENT VARIABLES ==="
echo ""
while IFS= read -r func; do
    echo "$func"
    aws lambda get-function-configuration --function-name "$func" --profile "$PROFILE" --query "Environment.Variables" --output json
    echo "============================================================"
done < lambda_list.txt

echo ""
echo "=== DOWNLOADING LAMBDA CODE ==="
echo ""
while IFS= read -r func; do
    echo "Downloading: $func"
    URL=$(aws lambda get-function --function-name "$func" --profile "$PROFILE" --query "Code.Location" --output text)
    curl -s -o "lambda_code/${func}.zip" "$URL"
    echo "Saved to lambda_code/${func}.zip"
    echo "============================================================"
done < lambda_list.txt
