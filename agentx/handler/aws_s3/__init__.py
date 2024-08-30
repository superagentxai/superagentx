import logging
from enum import Enum
from typing import Any

import boto3
from botocore.config import Config
from botocore.exceptions import NoCredentialsError, ClientError
from poetry.utils.helpers import Downloader, download_file

from agentx.handler.aws_s3.exceptions import ListFilesFailed
from agentx.handler.base import BaseHandler

logger = logging.getLogger(__name__)


class AWSS3HandlerEnum(str, Enum):

    LIST_BUCKET = "list_bucket"
    UPLOAD_FILE = "upload_file"
    DOWNLOAD_FILE = "download_file"
    LIST_FILES = "list_files"


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

    def handle(self, *, action: str | Enum, **kwargs) -> Any:
        match action:
            case AWSS3HandlerEnum.LIST_BUCKET:
                self.list_buckets(**kwargs)
            case AWSS3HandlerEnum.UPLOAD_FILE:
                self.upload_file(**kwargs)
            case AWSS3HandlerEnum.DOWNLOAD_FILE:
                self.download_file(**kwargs)
            case AWSS3HandlerEnum.LIST_FILES:
                self.list_files()

    def list_buckets(
            self,
            prefix: str | None = None,
            delimiter: str = "/"
    ):
        try:
            res = self._storage.list_buckets(
                Bucket=self.bucket_name,
                Delimiter=delimiter,
                Prefix=prefix
            )
            if res and isinstance(res, dict):
                return res.get('Contents')
        except (NoCredentialsError, ClientError) as ex:
            _msg = "Error listing files"
            logger.error("Error listing files", exc_info=ex)
            raise ListFilesFailed(ex)



    def upload_file(self, file_name, object_name=None):
        if object_name is None:
            object_name = file_name
        try:
            self._storage.upload_file(file_name, self.bucket_name, object_name)
            logger.info(f"File '{file_name}' uploaded to '{self.bucket_name}/{object_name}'.")
            return True
        except FileNotFoundError:
            logger.error(f"The file '{file_name}' was not found.")
            return False
        except NoCredentialsError:
            logger.error("Credentials not available.")
            return False
        except ClientError as e:
            logger.error(f"Client error: {e}")
            return False

    def download_file(self, object_name, file_name=None):
        if file_name is None:
            file_name = object_name
        try:
            self._storage.download_file(self.bucket_name, object_name, file_name)
            logger.info(f"File '{file_name}' downloaded from '{self.bucket_name}/{object_name}'.")
            return True
        except NoCredentialsError:
            logger.error("Credentials not available.")
            return False
        except ClientError as e:
            logger.error(f"Client error: {e}")
            return False

    def list_files(self):
        try:
            response = self._storage.list_objects_v2(Bucket=self.bucket_name)
            for item in response.get('Contents', []):
                logger.info(f"File found: {item['Key']}")
            return response.get('Contents', [])
        except NoCredentialsError:
            logger.error("Credentials not available.")
            return []
        except ClientError as e:
            logger.error(f"Client error: {e}")
            return []

