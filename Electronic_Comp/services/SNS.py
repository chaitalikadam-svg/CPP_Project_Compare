import boto3

# Create SNS client
sns = boto3.client('sns')

def notify_user_verified(email):
    #Creating SNS topic for admin 
    response = sns.create_topic(Name='UserNotification')
    topic_arn = response['TopicArn']
    #print(f"Topic ARN: {topic_arn}")
    response = sns.subscribe(
            TopicArn=topic_arn,
            Protocol='email',
            Endpoint=email
        )
    print(f"Subscription ARN: {response['SubscriptionArn']}")