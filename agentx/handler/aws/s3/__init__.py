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

    def handle(
            self,
            *,
            action: str | Enum, **kwargs
    ) -> Any:

        """
           params:
               action(str): Give an action what has given in the Enum.
        """

        if isinstance(action, str):
            action = action.lower()

        match action:
            case AWSS3HandlerEnum.LIST_BUCKET:
                return self.list_bucket()
            case AWSS3HandlerEnum.UPLOAD_FILE:
                return self.upload_file(**kwargs)
            case AWSS3HandlerEnum.DOWNLOAD_FILE:
                return self.download_file(**kwargs)
            case _:
                raise InvalidType(f"Invalid action {action}")

    def list_bucket(self):
        try:
            res = self._storage.list_buckets()
            if res and isinstance(res, dict):
                return res.get('Contents')
        except (NoCredentialsError, ClientError) as ex:
            _msg = "Error listing files"
            logger.error(_msg, exc_info=ex)
            raise ListFilesFailed(ex)

    def upload_file(
            self,
            file_name: str,
            object_name: str | None = None
    ):

        """
           params:
               file_name(str):File to upload.
               object_name(str):S3 object name. If not specified then file_name is used
        """

        if object_name is None:
            object_name = file_name
        try:
            self._storage.upload_file(
                Filename=file_name,
                Bucket=self.bucket_name,
                Key=object_name
            )
            logger.info(f"File '{file_name}' uploaded to '{self.bucket_name}/{object_name}'.")
        except (FileNotFoundError, NoCredentialsError, ClientError) as ex:
            _msg = f'File {file_name} upload failed!'
            raise FileUploadFailed(ex)

    def download_file(
            self,
            object_name: str,
            file_name: str | None = None
    ):

        """
           params:
               file_name(str):File to upload.
               object_name(str):S3 object name. If not specified then file_name is used
        """

        if file_name is None:
            file_name = object_name
        try:
            self._storage.download_file(
                Bucket=self.bucket_name,
                Key=object_name,
                Filename=file_name
            )
            logger.info(f"File '{file_name}' downloaded from '{self.bucket_name}/{object_name}'.")
        except (NoCredentialsError, ClientError) as ex:
            _msg = f'File {file_name} download failed!'
            logger.error(_msg, exc_info=ex)
            raise FileDownloadFailed(ex)

    async def ahandle(
            self,
            *,
            action: str | Enum,
            **kwargs
    ) -> Any:

        """
            params:
                action(str): Give an action what has given in the Enum.
        """

        if isinstance(action, str):
            action = action.lower()

        match action:
            case AWSS3HandlerEnum.LIST_BUCKET:
                return await sync_to_async(self.list_bucket)
            case AWSS3HandlerEnum.UPLOAD_FILE:
                return await sync_to_async(self.upload_file, **kwargs)
            case AWSS3HandlerEnum.DOWNLOAD_FILE:
                return await sync_to_async(self.download_file, **kwargs)
            case _:
                raise InvalidType(f"Invalid action {action}")
