@echo off

echo === Elastic IPs ===
aws ec2 describe-addresses --profile PROFILE_NAME --output table
echo ============================================================

echo === EC2 Instances with Public IPs ===
aws ec2 describe-instances --profile PROFILE_NAME --query "Reservations[].Instances[].[InstanceId,PublicIpAddress,State.Name]" --output table
echo ============================================================

echo === Internet-Facing Load Balancers (v2) ===
aws elbv2 describe-load-balancers --profile PROFILE_NAME --query "LoadBalancers[?Scheme=='internet-facing'].[LoadBalancerName,DNSName,Type]" --output table
echo ============================================================

echo === Internet-Facing Load Balancers (Classic) ===
aws elb describe-load-balancers --profile PROFILE_NAME --query "LoadBalancerDescriptions[?Scheme=='internet-facing'].[LoadBalancerName,DNSName]" --output table
echo ============================================================

echo === CloudFront Distributions ===
aws cloudfront list-distributions --profile PROFILE_NAME --query "DistributionList.Items[].[Id,DomainName,Status]" --output table
echo ============================================================

echo === API Gateways (REST) ===
aws apigateway get-rest-apis --profile PROFILE_NAME --output table
echo ============================================================

echo === API Gateways (HTTP/WebSocket) ===
aws apigatewayv2 get-apis --profile PROFILE_NAME --output table
echo ============================================================

echo === Publicly Accessible RDS Instances ===
aws rds describe-db-instances --profile PROFILE_NAME --query "DBInstances[?PubliclyAccessible==`true`].[DBInstanceIdentifier,Endpoint.Address]" --output table
echo ============================================================

echo === NAT Gateways ===
aws ec2 describe-nat-gateways --profile PROFILE_NAME --query "NatGateways[].[NatGatewayId,NatGatewayAddresses[].PublicIp]" --output table
echo ============================================================
