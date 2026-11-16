#!/bin/bash
PROFILE="PROFILE_NAME"

echo "========================================"
echo "SSM PARAMETER STORE AUDIT"
echo "========================================"
echo ""

echo "[*] Listing all SSM parameters..."
aws ssm describe-parameters --profile "$PROFILE" --output json > ssm_params.json

echo ""
echo "========================================"
echo "SSM Parameter Values (decrypted)"
echo "========================================"
echo ""

python3 -I -c "import json;[print(p['Name']) for p in json.load(open('ssm_params.json')).get('Parameters',[])]" | while IFS= read -r name; do
    echo "----------------------------------------"
    echo "Parameter: $name"
    echo "----------------------------------------"
    aws ssm get-parameter --name "$name" --with-decryption --profile "$PROFILE" --output json
    echo ""
done

echo "========================================"
echo "Done."
echo "========================================"
