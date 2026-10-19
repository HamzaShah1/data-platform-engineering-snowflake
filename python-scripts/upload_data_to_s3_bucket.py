import boto3
import logging
from botocore.exceptions import ClientError
from pathlib import Path

PROJECT_DIR = Path("/Users/hamzashah/data-platform-engineering-snowflake")

LOCAL_DIR = PROJECT_DIR / "datasets" / "processed"
BUCKET_NAME = "data-platform-project-processed-csv-bucket"
S3_PREFIX = "processed"

def upload_file(file_name, bucket, object_name=None):
    if object_name is None:
        object_name = os.path.basename(file_name)
    
    s3_client = boto3.client("s3")
    try:
        response = s3_client.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True

for file in LOCAL_DIR.iterdir():
    if file.is_file() and file.suffix == ".csv":
        s3_key = f"{S3_PREFIX}/{file.name}"
        success = upload_file(file, BUCKET_NAME, s3_key)

        if success:
            print(f"uploaded {file} successfully")


