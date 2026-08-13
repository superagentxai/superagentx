import os
import httpx

from .models import PolicyDecision
from dotenv import load_dotenv
load_dotenv()

class PolicyClient:

    def __init__(self, platform_url: str | None = None):
        self.base_url = platform_url or os.getenv("PLATFORM_URL")

        if not self.base_url:
            raise ValueError(
                "PLATFORM_URL is not configured."
            )

    async def evaluate(
        self,
        payload: dict
    ) -> PolicyDecision:

        async with httpx.AsyncClient() as client:

            response = await client.post(
                f"{self.base_url}/api/v1/evaluate",
                json=payload,
                timeout=30
            )

            response.raise_for_status()

            return PolicyDecision.model_validate(
                response.json()
            )


policy_client = PolicyClient()