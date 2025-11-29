import boto3
import json

cloudwatch = boto3.client("cloudwatch", region_name="us-east-1")

dashboard_name = "ElectronicProductDashboard"
bucket_name = "chaitalibucket1001"
table_name = "ElectronicItem"
topic_name = "UserNotification"

dashboard_body = {
    "widgets": [
        # S3 Objects (Bar)
        {
            "type": "metric",
            "x": 0,
            "y": 0,
            "width": 6,
            "height": 6,
            "properties": {
                "metrics": [["AWS/S3", "NumberOfObjects", "BucketName", bucket_name, "StorageType", "AllStorageTypes"]],
                "period": 300,
                "stat": "Average",
                "title": "S3 Objects",
                "view": "bar",
                "region": "us-east-1",
                "annotations": {}
            }
        },
        # DynamoDB Read Capacity (Line)
        {
            "type": "metric",
            "x": 6,
            "y": 0,
            "width": 6,
            "height": 6,
            "properties": {
                "metrics": [["AWS/DynamoDB", "ConsumedReadCapacityUnits", "TableName", table_name]],
                "period": 300,
                "stat": "Sum",
                "title": "DynamoDB Read Capacity",
                "view": "timeSeries",
                "region": "us-east-1",
                "annotations": {}
            }
        },
        # SNS Messages Published (SingleValue)
        {
            "type": "metric",
            "x": 6,
            "y": 6,
            "width": 6,
            "height": 6,
            "properties": {
                "metrics": [["AWS/SNS", "NumberOfMessagesPublished", "TopicName", topic_name]],
                "period": 300,
                "stat": "Sum",
                "title": "SNS Messages Published",
                "view": "singleValue",
                "region": "us-east-1",
                "annotations": {}
            }
        }
    ]
}

dashboard_body_json = json.dumps(dashboard_body)

cloudwatch.put_dashboard(
    DashboardName=dashboard_name,
    DashboardBody=dashboard_body_json
)

print(f"Dashboard '{dashboard_name}' created/updated successfully!")
