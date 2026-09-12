from pydantic import BaseModel


class PolicyDecision(BaseModel):

    decision: str

    reason: str | None = None

    matched_policy: str | None = None