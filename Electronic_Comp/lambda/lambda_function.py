import boto3
import json

# Initialize clients
sns = boto3.client("sns")
cognito = boto3.client("cognito-idp")

# Replace with your values
USER_POOL_ID = "us-east-1_wSOb7NGER"
TOPIC_ARN = "arn:aws:sns:us-east-1:882202387716:UserNotification"

def lambda_handler(event, context):
    # 1. Extract S3 info from event
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    s3_path = f"s3://{bucket}/{key}"
    
    print(f"Admin added new product uploaded: {s3_path}")

    # 2. List Cognito users
    users = cognito.list_users(UserPoolId=USER_POOL_ID)
    
    emails = []
    for user in users['Users']:
        for attr in user['Attributes']:
            if attr['Name'] == 'email':
                emails.append(attr['Value'])

    # 3. Publish to SNS (all subscribers will get it)
    message = f"Admin has uploaded new product to compare inside TechieVS, lets compare, review and win"
    response = sns.publish(
        TopicArn=TOPIC_ARN,
        Message=message,
        Subject="New Product Added by TechieVS"
    )
    
    print(f"Message published: {response['MessageId']}")
    return {"statusCode": 200, "body": json.dumps("Notification sent")}