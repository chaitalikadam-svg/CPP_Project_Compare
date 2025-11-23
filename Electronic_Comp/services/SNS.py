import boto3

# Create SNS client
sns = boto3.client('sns')

# Create a new SNS topic
response = sns.create_topic(Name='AdminNotification')
topic_arn = response['TopicArn']

print(f"Topic ARN: {topic_arn}")
response = sns.subscribe(
        TopicArn=topic_arn,
        Protocol='email',
        Endpoint='chaitalikadamaws@gmail.com'  
    )
    
print(f"Subscription ARN: {response['SubscriptionArn']}")

def notify_admin_login(username):
    response = sns.publish(
        TopicArn=topic_arn,
        Message='Hello! You have logged in as a Admin in your application',
        Subject='Admin has logged in'
    )
    
    print(f"Message ID: {response['MessageId']}")