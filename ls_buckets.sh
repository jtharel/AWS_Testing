#!/bin/bash
PROFILE="PROFILE_NAME"

while IFS= read -r bucket; do
    echo "Bucket $bucket"
    aws s3 ls "s3://$bucket" --recursive --human-readable --summarize --profile "$PROFILE"
    echo "=============================================================="
done < buckets.txt
