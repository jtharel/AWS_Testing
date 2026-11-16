#!/bin/bash
PROFILE="PROFILE_NAME"

while IFS= read -r repo; do
    echo "$repo"
    aws ecr get-repository-policy --repository-name "$repo" --profile "$PROFILE" 2>&1
    echo "============================================================"
done < repo_list.txt
