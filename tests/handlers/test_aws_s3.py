import os
import pytest

from agentx.handler.aws.s3 import AWSS3Handler


'''
 Run Pytest:  

   1.pytest --log-cli-level=INFO tests/handlers/test_aws_s3.py::TestAWSS3::test_s3_handler_upload
   2.pytest --log-cli-level=INFO tests/handlers/test_aws_s3.py::TestAWSS3::test_s3_handler_list_bucket
   3.pytest --log-cli-level=INFO tests/handlers/test_aws_s3.py::TestAWSS3::test_s3_handler_download
 
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

    async def test_s3_handler_upload(self, aws_s3_client_init: AWSS3Handler):
        await aws_s3_client_init.upload_file(file_name="<file_path>")

    async def test_s3_handler_list_bucket(self, aws_s3_client_init: AWSS3Handler):
        s3_handler = await aws_s3_client_init.list_bucket()
        assert isinstance(s3_handler, dict)

    async def test_s3_handler_download(self, aws_s3_client_init: AWSS3Handler):
        await aws_s3_client_init.download_file(file_name="<file_path>", object_name="")