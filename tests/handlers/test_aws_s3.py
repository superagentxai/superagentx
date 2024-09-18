import os
import pytest

from agentx.handler.aws.s3 import AWSS3Handler


'''
 Run Pytest:  
 
   # sync  
   1.pytest --log-cli-level=INFO tests/handlers/test_aws_s3.py::TestAWSS3::test_s3_handler_upload
   2.pytest --log-cli-level=INFO tests/handlers/test_aws_s3.py::TestAWSS3::test_s3_handler_list_bucket
   3.pytest --log-cli-level=INFO tests/handlers/test_aws_s3.py::TestAWSS3::test_s3_handler_download
   
   #async
   4.pytest --log-cli-level=INFO tests/handlers/test_aws_s3.py::TestAWSS3::test_s3_ahandler_upload
   5.pytest --log-cli-level=INFO tests/handlers/test_aws_s3.py::TestAWSS3::test_s3_ahandler_list_bucket
   6.pytest --log-cli-level=INFO tests/handlers/test_aws_s3.py::TestAWSS3::test_s3_ahandler_download
 
'''

@pytest.fixture
def aws_s3_client_init() -> AWSS3Handler:
    s3_handler = AWSS3Handler(
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        bucket_name="test",
        region_name="eu-central-1"
    )
    return s3_handler

class TestAWSS3:

    def test_s3_handler_upload(self, aws_s3_client_init: AWSS3Handler):
        aws_s3_client_init.handle(action="upload_file", file_name="<file_path>")

    def test_s3_handler_list_bucket(self, aws_s3_client_init: AWSS3Handler):
        s3_handler = aws_s3_client_init.handle(action="list_bucket")
        assert isinstance(s3_handler, dict)

    def test_s3_handler_download(self, aws_s3_client_init: AWSS3Handler):
        aws_s3_client_init.handle(action="download_file", object_name="<file_path>")

    def test_s3_ahandler_upload(self, aws_s3_client_init: AWSS3Handler):
        aws_s3_client_init.handle(action="upload_file", file_name="<file_path>")

    def test_s3_ahandler_list_bucket(self, aws_s3_client_init: AWSS3Handler):
        s3_handler = aws_s3_client_init.ahandle(action="list_bucket")
        assert isinstance(s3_handler, dict)

    def test_s3_ahandler_download(self, aws_s3_client_init: AWSS3Handler):
        s3_handler = aws_s3_client_init.handle(action="upload_file", file_name="<file_path>")