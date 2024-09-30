import logging
import boto3
from botocore.exceptions import NoCredentialsError, ClientError

from agentx.handler.base import BaseHandler

logger = logging.getLogger(__name__)


class AWSEC2Handler(BaseHandler):

    def __init__(
            self,
            aws_access_key_id: str,
            aws_secret_access_key: str,
            region_name: str | None = None
    ):
        self.region = region_name
        self.ec2_client = boto3.client(
           'ec2',
            region_name=self.region,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key
        )
        logger.info(self.ec2_client)

    async def get_all_instances(self):
        """
        Asynchronously retrieves and returns a list of all instances managed by this handler.

        This method interacts with an external service (e.g., AWS EC2, Google Cloud Compute, etc.) to fetch details
        of all instances currently available or active in the system. It is designed to be run asynchronously,
        allowing other tasks to execute concurrently without blocking.
        """
        try:
            _response = self.ec2_client.describe_instances()
            logger.info(_response)
        except Exception as ex:
            logger.error(f"Get all Instance getting error: {ex}")


    async def start_instance(
            self,
            instance_id
    ):
        """
            Asynchronously starts an instance with the given instance ID.

            This method interacts with an external service (e.g., AWS EC2, Google Cloud Compute, etc.) to start
            a specific instance identified by the provided instance ID. It is designed to be run asynchronously
            to allow non-blocking execution.

            parameter:
                instance_id (str): The unique identifier of the instance to be start.
        """
        try:
            response = self.ec2_client.start_instances(InstanceIds=[instance_id])
            logging.info(f"Started EC2 instance: {instance_id}")
            return response
        except NoCredentialsError:
            logging.error("Credentials not available.")
            return None
        except ClientError as e:
            logging.error(f"Client error: {e}")
            return None


    async def get_instance_status (
            self,
            instance_id
    ):
        """
           Asynchronously retrieves the status of the current instance.

           This method communicates with an external service (e.g., AWS EC2, Google Cloud Compute, etc.) to
           obtain the current status of a specific instance. It is designed to run asynchronously, allowing
           other tasks to continue without blocking.
           parameter:
                instance_id (str): The unique identifier of the instance to be status.
        """
        try:
            response = self.ec2_client.describe_instance_status(InstanceIds=[instance_id])
            logging.info(response)
            status = response['InstanceStatuses'][0] if response['InstanceStatuses'] else None
            logging.info(f"Instance status: {status}")
            return status
        except NoCredentialsError:
            logging.error("Credentials not available.")
            return None
        except ClientError as e:
            logging.error(f"Client error: {e}")
            return None


    async def stop_instance(
            self,
            instance_id
    ):
        """
            Asynchronously stops an instance with the given instance ID.

            This method interacts with an external service (e.g., AWS EC2, Google Cloud Compute, etc.) to stop
            a specific instance identified by the provided instance ID. It is designed to run asynchronously to
            allow non-blocking execution.

            parameter:
                instance_id (str): The unique identifier of the instance to be stopped.
        """
        try:
            response = self.ec2_client.stop_instances(InstanceIds=[instance_id])
            logging.info(f"Stopped EC2 instance: {instance_id}")
            return response
        except NoCredentialsError:
            logging.error("Credentials not available.")
            return None
        except ClientError as e:
            logging.error(f"Client error: {e}")
            return None


    def __dir__(self):
        return (

            "get_all_instances",
            "start_instance",
            "instance_status",
            "stop_instance"
        )
