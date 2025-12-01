import boto3
from django.conf import settings

# Create SNS client
sns = boto3.client('sns', region_name=settings.AWS_REGION)

def notify_user_verified(email):
    #Creating SNS topic
    response = sns.create_topic(Name='UserNotification')
    topic_arn = response['TopicArn']
    #print(f"Topic ARN: {topic_arn}")
    response = sns.subscribe(
            TopicArn=topic_arn,
            Protocol='email',
            Endpoint=email
        )
    print(f"Subscription ARN: {response['SubscriptionArn']}")