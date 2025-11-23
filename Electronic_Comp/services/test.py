import boto3

def get_presigned_image_url(product_id, expires_in=3600):
    s3 = boto3.client("s3", region_name="us-east-1")
    key = product_id

    try:
        url = s3.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": "chaitalibucket1001",
                "Key": key,
                "ResponseContentType": "image/jpeg"  # forces browser to render as image
            },
            ExpiresIn=expires_in
        )
        print("✅ Pre-signed URL:", url)
        return url
    except Exception as e:
        print("❌ Error:", e)
        return None

# Test
get_presigned_image_url("IPHO_001")