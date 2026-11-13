@echo off
echo Do not forget to update the account id in this script:
echo .
echo S3 account level sharing
aws s3control get-public-access-block --account-id ACCOUNT_ID --profile PROFILE_NAME
echo ========================================

echo EBS Snapshot Block Public Access
aws ec2 get-snapshot-block-public-access-state --profile PROFILE_NAME
echo ========================================

echo EBS Snapshots
aws ec2 describe-snapshots --owner-id self --restorable-by-user-ids all --profile PROFILE_NAME
echo ========================================
