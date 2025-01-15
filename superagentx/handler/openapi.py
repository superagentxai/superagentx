import logging
import json
import yaml
import requests
from yaml import safe_load

from superagentx.handler.base import BaseHandler
from superagentx.handler.decorators import tool

logger = logging.getLogger(__name__)


class OpenAPIHandler(BaseHandler):

    def __init__(self, *, base_url: str, spec_url_path: str = None, spec_file_path: str = None):
        super().__init__()
        self.base_url = base_url
        self.base_url = self.base_url.rstrip('/') if self.base_url else self.base_url
        self.spec_url = f"{self.base_url}/{spec_url_path}" if self.base_url and spec_url_path else None
        self.spec_file_path = spec_file_path

    async def _load_spec(self) -> dict:
        """Load and parse the OpenAPI specification file."""
        if self.spec_url:
            response = requests.get(self.spec_url)
            response.raise_for_status()
            spec_data = response.json() if self.spec_url.endswith(".json") else safe_load(response.text)
            return spec_data
        if self.spec_file_path.endswith(".json"):
            with open(self.spec_file_path, "r") as file:
                return json.load(file)
        elif self.spec_file_path.endswith(".yaml") or self.spec_file_path.endswith(".yml"):
            with open(self.spec_file_path, "r") as file:
                return yaml.safe_load(file)
        else:
            raise ValueError("Unsupported file format. Use JSON or YAML.")

    async def get_endpoints(self):
        """Retrieve all endpoints from the OpenAPI spec."""
        spec = await self._load_spec()
        return list(spec.get("paths", {}).keys())

    async def get_operations(self, endpoint: str):
        """Retrieve operations (HTTP methods) for a specific endpoint."""
        spec = await self._load_spec()
        paths = spec.get("paths", {})
        if endpoint not in paths:
            raise ValueError(f"Endpoint '{endpoint}' not found in the OpenAPI spec.")
        return list(paths[endpoint].keys())

    async def get_operation_details(self, endpoint: str, method: str):
        """Retrieve details for a specific operation (HTTP method) on an endpoint."""
        spec = await self._load_spec()
        paths = spec.get("paths", {})
        if endpoint not in paths:
            raise ValueError(f"Endpoint '{endpoint}' not found in the OpenAPI spec.")
        operations = paths[endpoint]
        if method.lower() not in operations:
            raise ValueError(f"Method '{method}' not available for endpoint '{endpoint}'.")
        return operations[method.lower()]

    @tool
    async def call_endpoint(self, endpoint: str, method: str, params=None, body=None, headers=None):
        """
        Make an API call to the specified endpoint.

        Args:
            endpoint (str): The endpoint path (e.g., "/pets").
            method (str): HTTP method (e.g., "GET", "POST").
            params (dict): Query or path parameters for the request.
            body (dict): Request body for POST/PUT methods.
            headers (dict): Additional headers for the request.

        Returns:
            Response object from the HTTP request.
        """
        params = params or {}
        headers = headers or {}
        # Extract path parameters
        path_params = params.get("path", {})
        endpoint_path = endpoint.format(**path_params)

        # Query parameters
        query_params = params

        # Construct the full URL
        url = f"{self.base_url}{endpoint_path}"

        # Make the HTTP request
        response = requests.request(
            method=method.upper(),
            url=url,
            params=query_params,
            json=body,
            headers=headers,
        )

        # Check if the response is successful
        if response.status_code >= 400:
            raise requests.HTTPError(
                f"Error {response.status_code}: {response.text}"
            )

        return response.json()
