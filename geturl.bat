@echo off
echo Make sure you have environment variable set for AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY and AWS_SESSION_TOKEN
echo .

python -I -c "import os,json,urllib.parse,urllib.request;s=json.dumps({'sessionId':os.environ['AWS_ACCESS_KEY_ID'],'sessionKey':os.environ['AWS_SECRET_ACCESS_KEY'],'sessionToken':os.environ['AWS_SESSION_TOKEN']});r=json.loads(urllib.request.urlopen('https://signin.aws.amazon.com/federation?Action=getSigninToken&SessionDuration=1800&Session='+urllib.parse.quote(s)).read());print('https://signin.aws.amazon.com/federation?Action=login&Issuer=&Destination='+urllib.parse.quote('https://console.aws.amazon.com/')+'&SigninToken='+r['SigninToken'])"
