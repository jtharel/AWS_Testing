#!/bin/bash
PROFILE="PROFILE_NAME"

aws sns list-topics --profile "$PROFILE" --query "Topics[].TopicArn" --output json > sns_topics.json
python3 -I -c "import json;[print(a.strip()) for a in json.load(open('sns_topics.json'))]" > sns_topics.txt

echo ""
while IFS= read -r topic; do
    RESULT=$(aws sns get-topic-attributes --topic-arn "$topic" --profile "$PROFILE" --query "Attributes.KmsMasterKeyId" --output text 2>&1)
    if [ -z "$RESULT" ] || [ "$RESULT" = "None" ]; then
        echo "[NOT ENCRYPTED] $topic"
    elif echo "$RESULT" | grep -qi "ERROR"; then
        echo "[ERROR] $topic"
    else
        echo "[ENCRYPTED - $RESULT] $topic"
    fi
done < sns_topics.txt
