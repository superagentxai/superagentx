import os

import httpx

from .models import PolicyDecision


class PolicyClient:

    def __init__(
        self,
        platform_url: str | None = None,
    ):
        self.platform_url = platform_url

    async def evaluate(
        self,
        payload: dict,
    ) -> PolicyDecision:

        base_url = (
            self.platform_url
            or os.getenv("PLATFORM_URL")
        )

        if not base_url:
            raise ValueError(
                "PLATFORM_URL is not configured."
            )

        base_url = base_url.rstrip("/")

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{base_url}/api/v1/evaluate",
                json=payload,
            )

            response.raise_for_status()

            return PolicyDecision.model_validate(
                response.json()
            )


policy_client = PolicyClient()