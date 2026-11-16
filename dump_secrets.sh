#!/bin/bash
PROFILE="PROFILE_NAME"

aws secretsmanager list-secrets --profile "$PROFILE" --query "SecretList[].Name" --output json > secrets_list.json
python3 -I -c "import json;[print(a.strip()) for a in json.load(open('secrets_list.json'))]" > secrets_list.txt

while IFS= read -r secret; do
    echo "$secret"
    aws secretsmanager get-secret-value --secret-id "$secret" --profile "$PROFILE" --query "{Value:SecretString,Binary:SecretBinary}" --output json
    echo "============================================================"
done < secrets_list.txt
