#!/bin/bash
PROFILE="PROFILE_NAME"

echo "EC2 EBS Volumes and encrypted status:"
aws ec2 describe-volumes --profile "$PROFILE" --query "Volumes[].{ID:VolumeId,Encrypted:Encrypted,Size:Size}" --output table

echo ""
echo ""
echo "EC2 EBS Snapshots and encrypted status:"
aws ec2 describe-snapshots --owner-id self --profile "$PROFILE" --query "Snapshots[].{ID:SnapshotId,Encrypted:Encrypted,Size:VolumeSize,Date:StartTime}" --output table

echo "Encryption set by default:"
aws ec2 get-ebs-encryption-by-default --profile "$PROFILE"
