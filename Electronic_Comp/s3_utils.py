# Electronic_Comp/s3_utils.py
import boto3
from botocore.exceptions import ClientError

def get_presigned_image_url(product_id, bucket_name="chaitalibucket1001", region="us-east-1", expires_in=3600):
    """
    Generate a pre-signed URL for an S3 object key equal to product_id.
    Forces Content-Type to image/jpeg so the browser renders inline.
    """
    s3_client = boto3.client("s3", region_name=region)
    try:
        return s3_client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": bucket_name,
                "Key": product_id,
                "ResponseContentType": "image/jpeg"
            },
            ExpiresIn=expires_in
        )
    except ClientError:
        return None