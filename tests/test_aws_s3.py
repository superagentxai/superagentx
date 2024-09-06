import os

from agentx.handler.aws_s3 import AWSS3Handler

s3_handler = AWSS3Handler(
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    bucket_name="<BUCKET_NAME>",
    region_name="eu-central-1"
)
def test_s3_handler_upload():
    s3_handler.handle(action="upload_file",file_name="<file_path>")

def test_s3_handler_list_bucket():
    s3_handler.handle(action="list_bucket")

def test_s3_handler_download():
    s3_handler.handle(action="download_file",object_name="<file_path>")





