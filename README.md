# AWS_Testing
AWS Pen Testing Scripts

====================================================================================

Check for external exposure for the environment

Windows Command: check_external_exposure.bat

  Load Balancers return DNS names
    Use nslookup to get IP addresses
    
	cloudfront returns IDs, use this to get IP from cloudfront IDs:
		aws cloudfront get-distribution --id EM7W0N4R5245B --profile PROFILE_NAME --query "Distribution.[DomainName,DistributionConfig.Aliases.Items,DistributionConfig.Origins.Items[].DomainName,DistributionConfig.DefaultCacheBehavior.ViewerProtocolPolicy]" --output json
		nslookup domain names

	EC2 -> save IDs to ec2_instance_ids.txt

	EC2 instances, when you have the ID use: get_ec2_ips.bat 
		
Using all the above build IPs.txt file

nmap -p- -iL IPs.txt > nmap.txt
nuclei -l IPs.txt -o nuclei_results.txt

If TCP port 445 or 22 is discovered:
nmap -p445 -sV --script smb-protocols,smb-security-mode,smb-enum-shares,smb-os-discovery -oA smb_audit -iL IPs.txt
nmap -p22 -oA ssh_audit -sV --script ssh2-enum-algos,ssh-hostkey,ssh-auth-methods -iL IPs.txt




====================================================================================

Finding: Access Policies Assigned Directly to Users:

Windows Command: list_user_policies.bat


Evidence:
	Inline policy details:
	aws iam get-user-policy --user-name abrigo-user-mgn --policy-name abrigo-user-mgn --profile PROFILE_NAME

	List assigned Inline policies by user name
	aws iam list-user-policies --user-name <USERNAME> --profile <PROFILE>

----------------------------------------
	Attached Managed Policy Details:
	aws iam get-policy-version --policy-arn "arn:aws:iam::179507212702:policy/abrigo-policy-moveit-s3-full-access" --version-id v1 --profile PROFILE_NAME

	List attached managed polcies by user:
	aws iam list-attached-user-policies --user-name <USERNAME> --profile <PROFILE>




====================================================================================


IMDSv2 is Not Required
	imdsv2.bat
		Nothing returned means no IMDSv1


====================================================================================


Cross-Account AssumeRole Policy Lacks External ID

	python check_assume_role_external_id.py > lacks_id.txt (update account number)

	:: command to see individual policy:
	aws iam get-role --role-name <ROLE_NAME> --profile <PROFILE_NAME> --query "Role.AssumeRolePolicyDocument" --output json

	:: command to see all policies, etc. (not really needed if using py script above)
	aws iam list-roles --output json --profile <PROFILE_NAME> |grep -B5 -A15 "AssumeRole" -grep -v <ACCOUNT NUMBER> |grep RoleName	


	


====================================================================================

Overly Permissive Access to Secrets Manager

	python check_secretsmanager_access.py
		shows all users with secretsmanager:GetSecretValue

	dump_secrets.bat
		dumps all secrets as logged in user

	individual secret/evidence:
	aws secretsmanager get-secret-value --secret-id "SECRET_NAME" --profile PROFILE_NAME


====================================================================================


EBS Volume Lacks Encryption

	aws ec2 describe-volumes --profile PROFILE_NAME |grep Encrypted		

		
	


====================================================================================


Sensitive Data Found in EC2 Instance Metadata
	
	python check_ec2_metadata.py > ec2_metadata.txt
		Takes a long time

	Individual data:
	aws ec2 describe-instance-attribute --instance-id <INSTANCE ID> --attribute userData --profile  <PROFILE> --output text --query "UserData.Value" > ud.txt
	certutil -decode ud.txt ud_decoded.txt
	type ud_decoded.txt

	




====================================================================================



Sensitive data Stored Insecurely in Cloud Storage Platform

	aws s3api list-buckets --query "Buckets[].Name" --output table --profile PROFILE_NAME > buckets.txt
		remove lines and spaces from buckets.txt
	
	ls_buckets.bat > ls_buckets.txt
		review contents of s3 buckets for files to download and review
	
	public_buckets.bat public_buckets.txt

		grep -i URI public_buckets.txt


	# is bucket publicly accessible command for evidence:
		aws s3api get-bucket-acl --bucket <bucket-name>


grep -vE "[A-F0-9]{16}"


# List files on s3 bucket
aws s3 ls s3://<BUCKET_NAME> --recursive --human-readable --summarize --profile <PROFILE_NAME>

#copy contents of s3 bucket:
aws s3 cp s3://<BUCKET_NAME>/ . --recursive 

copy file from S3 bucket:
aws s3 cp s3://bucket-name/filename.txt . --profile <PROFILE_NAME>
aws s3 cp s3://<bucket-name>/ . --recursive --exclude "*.png" --exclude "*.PNG" 


#Search for sensitive info in S3 buckets or downloaded files. Use environment variables for keys
trufflehog s3 --bucket=<bucket_name> --key=<key> --secret=<secret>
trufflehog filesystem .

	--only-verified is a "verified" option to help with information overload


gitleaks detect --source . --no-git --verbose
gitleaks detect --source . --no-git --report-path ./gitleaks-report.json
	cat ./gitleaks-report.json | python3 -m json.tool 

gitleaks detect --source . --no-git --report-path ./gitleaks-report.csv --report-format csv
	open in Excel





====================================================================================

Overly Permissive Policy Rules

python check_permissive_policies.py

python script runs this and then parses it:
aws iam get-account-authorization-details --profile PROFILE_NAME --output json > iam_dump.json

Then grep for the dangerous patterns:

:: Full admin — Action * on Resource *
grep -n "\"Action\": \"\*\"" iam_dump.json

:: Service-level wildcards (s3:*, ec2:*, iam:*, etc.)
grep -n ":\*" iam_dump.json

:: Unrestricted resources
grep -n "\"Resource\": \"\*\"" iam_dump.json

:: Inline policies with overly broad access
grep -A5 -B5 "\"Effect\": \"Allow\"" iam_dump.json | grep -B5 "\*"

What "overly permissive" looks like:

┌────────────────────────────────────────────────┬────────────────────────────────┐
│                    Pattern                     │              Risk              │
├────────────────────────────────────────────────┼────────────────────────────────┤
│ "Action": "*", "Resource": "*"                 │ Full admin                     │
├────────────────────────────────────────────────┼────────────────────────────────┤
│ "Action": "iam:*"                              │ Can escalate to admin          │
├────────────────────────────────────────────────┼────────────────────────────────┤
│ "Action": "sts:AssumeRole", "Resource": "*"    │ Can assume any role            │
├────────────────────────────────────────────────┼────────────────────────────────┤
│ "Action": "s3:*"                               │ Full S3 access, data exfil     │
├────────────────────────────────────────────────┼────────────────────────────────┤
│ "Action": "lambda:*"                           │ Code execution, priv esc       │
├────────────────────────────────────────────────┼────────────────────────────────┤
│ "Action": ["ec2:RunInstances", "iam:PassRole"] │ Launch instance with any role  │
├────────────────────────────────────────────────┼────────────────────────────────┤
│ No Condition block on sensitive actions        │ Missing MFA/IP/tag constraints │
└────────────────────────────────────────────────┴────────────────────────────────┘




====================================================================================


Logging Not Enabled

aws configservice describe-configuration-recorders --profile PROFILE_NAME
aws configservice describe-configuration-recorder-status --profile PROFILE_NAME

First command shows if a recorder exists. Second shows if it's actually recording — look for "recording": true or false.

If the recorder exists but isn't recording, that's a finding — someone stopped it (or it was never started).

To check the delivery channel (where Config sends results):

aws configservice describe-delivery-channels --profile PROFILE_NAME
 
Run batch file logging.bat
	



====================================================================================



Keys Have Not Been Rotated Within 90 Days

web console -> IAM Users -> Active Key Age



====================================================================================

Public Access Enabled (access to S3 buckets and EBS Snapshots)


public_sharing.bat (update Account number in file)
	
	aws s3control get-public-access-block --account-id 300955724230 --profile PROFILE_NAME
		PublicAccessBlockConfiguration":{
			"BlockPublicAcls": true,
			"IgnorePublicAcls": true,
			"BlockPublicPolicy": true,
			"RestrictPublicBuckets": true

		All 4 should be true -> no public access

	aws ec2 get-snapshot-block-public-access-state --profile PROFILE_NAME
		"State": "block-new-sharing"
			means it is blocked
 
	aws ec2 describe-snapshots --owner-id self --restorable-by-user-ids all --profile PROFILE_NAME	
		Snaphshots": [] 
			means no snapshots are shared




====================================================================================

Unpatched Software

	python check_patch_levels.py

	aws ssm describe-instance-patch-states --profile <PROFILENAME>



====================================================================================

Inadequate Secrets Rotation Configuration


aws secretsmanager list-secrets --query "SecretList[*].{Name:Name,RotationEnabled:RotationEnabled,LastRotated:LastRotatedDate}" --output table --profile PROFILE_NAME

secrets_rotation.bat


====================================================================================

SNS Topics Unencrypted at Rest

check_sns_encryption.bat
	

single command for evidence:
	aws sns get-topic-attributes --topic-arn arn:aws:sns:us-east-1:300955724230:TOPIC_NAME --profile PROFILE_NAME





====================================================================================


Insecure Storage of Secrets:

CHECK ALL LAMBDAS!!!!

dump_lambdas.bat > lambda_env_output.txt
	txt file will have env vars. lambda_code dir has code

cd lambda_code
	trufflehog filesystem .
	gitleaks detect --source . --no-git --verbose

python scan_zips.py lambda_code



====================================================================================

Sensitive Information Exposed in CloudFormation Stack Parameters

check_cloudformation.bat > cloudformation.txt



====================================================================================


Sensitive data Exposed in AWS Parameter Store
AWS Systems Manager (SSM) Data Leakage

check_ssm.bat


# Get list of ssm:
aws ssm describe-parameters --profile <PROFILE> 
	
# Output the SSM details
aws ssm get-parameter --name <NAME> --with-decryption --profile <PROFILE>




====================================================================================

An Excessive Number of IAM Users have Admin Privileges




====================================================================================


Stale IAM User Accounts

Web Console -> IAM -> Users




====================================================================================

MFA Not Enforced


python check_mfa.py
	MFA -> false mean no MFA
	PW  -> True means web console access is enabled
	Key -> True access key is active


Evidence:
	aws iam list-mfa-devices --user-name <USERNAME> --profile <PROFILE>





====================================================================================

Keys Have Not Been Rotated Within 90 Days


====================================================================================

EBS Resources Lack Encryption

encrypted_ec2_ebs_volumes.bat


Check EBS volumes:
aws ec2 describe-volumes --profile PROFILE_NAME --query "Volumes[].{ID:VolumeId,Encrypted:Encrypted,Size:Size}" --output table

#check snapshots:
	aws ec2 describe-snapshots --owner-id self --profile PROFILE_NAME --query "Snapshots[].{ID:SnapshotId,Encrypted:Encrypted,Size:VolumeSize,Date:StartTime}" --output table

#check if default encryption is enforced for new volumes:
	aws ec2 get-ebs-encryption-by-default --profile PROFILE_NAME




====================================================================================


Overly Permissive Security Group Rules Exist 
	unrestricted incoming connections from all IPs/Internet



python check_security_groups.py (only returns 0.0.0.0 inbound)
	
	total open rules: -> means total could of individual 0.0.0.0/0 or ::/0 where observed




====================================================================================

Cloud Security Monitoring not Enabled


python check_security_monitoring.py


Cloudtrail, Security Hub or AWS Config missing is a finding

Individual/evidence:
CloudTrail:
aws cloudtrail describe-trails --profile PROFILE_NAME
aws cloudtrail get-trail-status --name TRAIL_NAME --profile PROFILE_NAME

Security Hub:
aws securityhub describe-hub --profile PROFILE_NAME
aws securityhub get-enabled-standards --profile PROFILE_NAME

AWS Config:
aws configservice describe-configuration-recorders --profile PROFILE_NAME
aws configservice describe-configuration-recorder-status --profile PROFILE_NAME
aws configservice describe-config-rules --profile PROFILE_NAME




====================================================================================

IAM Privilege Escalation

python check_assumable_roles.py

For Evidence:

	aws iam get-role --role-name ROLE_NAME --profile PROFILE_NAME --query "Role.AssumeRolePolicyDocument"
		returns the AssumeRole action

	aws iam list-attached-role-policies --role-name "<ROLENAME>" --profile <PROFILE>
		returns attached policies
	aws iam list-role-policies --role-name "<ROLENAME>" --profile <PROFILE>
		returns inline? policies	


	Take the Arn from one of the two above commands:
		aws iam get-policy-version --policy-arn "<POLICY_ARN>" --version-id v1 --profile <PROFILE>


	Get the termporary creds:
	aws sts assume-role --role-arn "arn:aws:iam::123456789:role/TargetRole" --role-session-name "test" --profile <PROFILE>
		That returns temporary credentials (access key, secret key, session token) for the target role. 

	aws configure --profile <PROFILE_ELEVATED>
	aws sts get-caller-identity --profile <PROFILE_ELEVATED>


====================================================================================

Powershell command to replace strings in text files:

powershell -c "Get-ChildItem *.bat | ForEach-Object { (Get-Content $_) -replace 'PROFILE_NAME','NEW_PROFILE_NAME' | Set-Content $_ }"

====================================================================================

Providing environment variable set for AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY and AWS_SESSION_TOKEN
this batch file will provide a URL for you to cut and paste into a browser for access to the Web Console

Windows command: geturl.bat

====================================================================================


====================================================================================


====================================================================================
