import os
import pytest

from agentx.handler.aws.ec2 import AWSEC2Handler, logger

'''
 Run Pytest:  

   1.pytest --log-cli-level=INFO tests/handlers/test_aws_ec2.py::TestAWSEC2::test_ec2_handler_get_all_instances
   2.pytest --log-cli-level=INFO tests/handlers/test_aws_ec2.py::TestAWSEC2::test_ec2_handler_start_instance
   3.pytest --log-cli-level=INFO tests/handlers/test_aws_ec2.py::TestAWSEC2::test_ec2_handler_instance_status
   4.pytest --log-cli-level=INFO tests/handlers/test_aws_ec2.py::TestAWSEC2::test_ec2_handler_stop_instance

'''


@pytest.fixture
def aws_ec2_client_init() -> AWSEC2Handler:
    ec2_handler = AWSEC2Handler(
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name="ap-south-1"
    )
    return ec2_handler


class TestAWSEC2:

    async def test_ec2_handler_get_all_instances(self, aws_ec2_client_init: AWSEC2Handler):
        await aws_ec2_client_init.get_all_instances()


    async def test_ec2_handler_start_instance(self, aws_ec2_client_init: AWSEC2Handler):
        ec2_handler = await aws_ec2_client_init.start_instance(
            instance_id="i-036aba9f3527bf366"
        )
        assert isinstance(ec2_handler, dict)


    async def test_ec2_handler_get_instance_status(self, aws_ec2_client_init: AWSEC2Handler):
        ec2_handler = await aws_ec2_client_init.get_instance_status(
            instance_id="i-036aba9f3527bf366"
        )
        logger.info(ec2_handler)


    async def test_ec2_handler_stop_instance(self, aws_ec2_client_init: AWSEC2Handler):
        ec2_handler = await aws_ec2_client_init.stop_instance(
            instance_id="i-036aba9f3527bf366"
        )
        assert isinstance(ec2_handler, dict)
