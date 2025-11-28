import boto3

REGION = 'us-east-1'
client = boto3.client('cognito-idp', region_name  = 'us-east-1')

# Creating a User Pool
user_pool_response  = client.create_user_pool(
    PoolName  = 'ElectronicProductCompareApp',
    Policies = {
        'PasswordPolicy':{
            'MinimumLength': 8,
            'RequireUppercase': True,
            'RequireLowercase': True,
            'RequireNumbers': True,
            'RequireSymbols':False
        }
    },
    AutoVerifiedAttributes = ['email'],
    EmailConfiguration={
        "EmailSendingAccount": "COGNITO_DEFAULT"
    }
    )
user_pool_id = user_pool_response['UserPool']['Id']
print(f"User Pool created: {user_pool_id}")

#Creating App Client
app_client_response = client.create_user_pool_client(
    UserPoolId = user_pool_id,
    ClientName  = 'ProductComparisonAppClient',
    GenerateSecret=False,
    ExplicitAuthFlows=[
        'ALLOW_USER_PASSWORD_AUTH',
        'ALLOW_ADMIN_USER_PASSWORD_AUTH',
        'ALLOW_REFRESH_TOKEN_AUTH'
    ]
)

app_client_id = app_client_response['UserPoolClient']['ClientId']
print(f"App Client created: {app_client_id}")

# Creating User Group 
for group_name in ['Admin', 'User']:
    client.create_group(
        GroupName = group_name,
        UserPoolId = user_pool_id,
        Description =f'{group_name} group for role-based access'
    )
    print(f"Group created: {group_name}")

print(f"User Pool ID: {user_pool_id}")
print(f"App Client ID: {app_client_id}")
print(f"Region: {REGION}")


admin_email = 'chaitalikadamaws@gmail.com'
admin_password = 'Admin@123'  

# Creating admin user
client.admin_create_user(
    UserPoolId=user_pool_id,
    Username=admin_email,
    UserAttributes=[
        {'Name': 'email', 'Value': admin_email},
        {'Name': 'email_verified', 'Value': 'true'}
    ],
    TemporaryPassword=admin_password,
    MessageAction='SUPPRESS' 
    )

client.admin_set_user_password(
    UserPoolId=user_pool_id,
    Username=admin_email,
    Password=admin_password,
    Permanent=True
)

client.admin_add_user_to_group(
    UserPoolId=user_pool_id,
    Username=admin_email,
    GroupName='Admin'
)
print("Admin user created and added to Admin group")