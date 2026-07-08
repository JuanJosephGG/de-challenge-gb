import boto3
from botocore.exceptions import ClientError
from src.config.settings import settings

def get_s3_client():
    return boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION
    )

def upload_file_to_s3(file_obj, object_name: str) -> bool:
    s3_client = get_s3_client()
    try:
        s3_client.upload_fileobj(file_obj, settings.AWS_S3_BUCKET_NAME, object_name)
        return True
    except ClientError as e:
        print(f"Error subiendo a S3: {e}")
        return False