import boto3

REGION = 'us-east-1'
COGNITO_CLIENT_ID = '35rp3sdkr3id99mea4ghog2eg'
EMAIL = 'user_email@example.com'

client = boto3.client('cognito-idp', region_name=REGION)

response = client.resend_confirmation_code(
    ClientId=COGNITO_CLIENT_ID,
    Username=EMAIL
)

print(response)
