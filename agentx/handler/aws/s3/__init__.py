import logging
from enum import Enum
from typing import Any

import boto3
from botocore.exceptions import NoCredentialsError, ClientError

from agentx.exceptions import InvalidType
from agentx.handler.aws.exceptions import ListFilesFailed, FileUploadFailed, FileDownloadFailed
from agentx.handler.base import BaseHandler
from agentx.utils.helper import sync_to_async

logger = logging.getLogger(__name__)


class AWSS3HandlerEnum(str, Enum):
    LIST_BUCKET = "list_bucket"
    UPLOAD_FILE = "upload_file"
    DOWNLOAD_FILE = "download_file"


class AWSS3Handler(BaseHandler):
    """
       A handler class for managing interactions with Amazon S3 (Simple Storage Service).
       This class extends BaseHandler and provides methods for uploading, downloading, deleting,
       and managing objects in S3 buckets, facilitating efficient storage and retrieval of data in the cloud.
    """

    def __init__(
            self,
            aws_access_key_id: str,
            aws_secret_access_key: str,
            bucket_name: str | None = None,
            region_name: str | None = None
    ):
        self.bucket_name = bucket_name
        self.region = region_name
        self._storage = boto3.client(
           's3',
            region_name=self.region,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key
        )

    async def handle(
            self,
            *,
            action: str | Enum,
            **kwargs
    ) -> Any:

        """
        Asynchronously processes the specified action, which can be a string or an Enum, along with any additional
        keyword arguments. This method executes the corresponding logic based on the provided action and parameters.

        parameters:
            action (str | Enum): The action to be performed. This can either be a string or an Enum value representing
                                the action.
            **kwargs: Additional keyword arguments that may be passed to customize the behavior of the handler.

        Returns:
            Any: The result of handling the action. The return type may vary depending on the specific action handled.
        """

        if isinstance(action, str):
            action = action.lower()

        match action:
            case AWSS3HandlerEnum.LIST_BUCKET:
                return await self.list_bucket()
            case AWSS3HandlerEnum.UPLOAD_FILE:
                return await self.upload_file(**kwargs)
            case AWSS3HandlerEnum.DOWNLOAD_FILE:
                return await self.download_file(**kwargs)
            case _:
                raise InvalidType(f"Invalid action {action}")

    async def list_bucket(self):
        """
            Asynchronously retrieves a list of all objects in the specified S3 bucket.
            This method provides an overview of the contents stored in the bucket, facilitating data management
            and organization.
        """

        try:
            res = await sync_to_async(self._storage.list_buckets)
            if res and isinstance(res, dict):
                return res.get('Contents')
        except (NoCredentialsError, ClientError) as ex:
            _msg = "Error listing files"
            logger.error(_msg, exc_info=ex)
            raise ListFilesFailed(ex)

    async def upload_file(
            self,
            file_name: str,
            object_name: str | None = None
    ):

        """
        Asynchronously uploads a file to an S3 bucket, specifying the file name and optional object name in the bucket.
        This method facilitates the storage of files in AWS S3, allowing users to manage their cloud data effectively.

        Parameter:
           file_name (str): The name of the file to be uploaded, including its path.
           object_name (str | None, optional): The name to assign to the object in the S3 bucket.
           If None, the object name will default to the file name. Defaults to None.
        """

        if object_name is None:
            object_name = file_name
        try:
            await sync_to_async(self._storage.upload_file,
                Filename=file_name,
                Bucket=self.bucket_name,
                Key=object_name
            )
            logger.info(f"File '{file_name}' uploaded to '{self.bucket_name}/{object_name}'.")
        except (FileNotFoundError, NoCredentialsError, ClientError) as ex:
            _msg = f'File {file_name} upload failed!'
            raise FileUploadFailed(ex)

    async def download_file(
            self,
            object_name: str,
            file_name: str | None = None
    ):

        """
        Asynchronously downloads a file from an S3 bucket to a local path.
        This method facilitates the retrieval of stored data from AWS S3, allowing users to access their files conveniently.

        parameter:
            file_name (str): The name of the file to be uploaded, including its path.
           object_name (str | None, optional): The name to assign to the object in the S3 bucket.
        """

        if file_name is None:
            file_name = object_name
        try:
            await sync_to_async(self._storage.download_file,
                Bucket=self.bucket_name,
                Key=object_name,
                Filename=file_name
            )
            logger.info(f"File '{file_name}' downloaded from '{self.bucket_name}/{object_name}'.")
        except (NoCredentialsError, ClientError) as ex:
            _msg = f'File {file_name} download failed!'
            logger.error(_msg, exc_info=ex)
            raise FileDownloadFailed(ex)


    def __dir__(self):
        return (
            "download_file",
            "upload_file",
            "list_bucket"
        )
