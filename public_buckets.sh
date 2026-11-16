#!/bin/bash
PROFILE="PROFILE_NAME"

while IFS= read -r bucket; do
    echo "Bucket $bucket"
    aws s3api get-bucket-acl --bucket "$bucket" --profile "$PROFILE"
    echo "============================================="
done < buckets.txt
