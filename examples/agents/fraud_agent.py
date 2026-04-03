import asyncio
import os
from dotenv import load_dotenv

from superagentx.llm import LLMClient
from superagentx.handler.ai import AIHandler
from superagentx_handlers.slack import SlackHandler
from superagentx.task_engine import TaskEngine
from superagentx.agent import Agent
from superagentx.prompt import PromptTemplate
from superagentx.agentxpipe import AgentXPipe

load_dotenv()


async def get_pipe():
    # ---------------------------
    # LLM CONFIG
    # ---------------------------
    gemini_config = {
        "llm_type": "gemini",
        "model": "gemini-2.5-flash-lite",
        "api_key": os.getenv("GEMINI_API_KEY")
    }

    llm = LLMClient(llm_config=gemini_config)

    # ---------------------------
    # HANDLERS
    # ---------------------------
    ai = AIHandler(role="Fraud Investigator", llm=llm)

    slack = SlackHandler(
        bot_token=os.getenv("SLACK_BOT_TOKEN"),
        channel_id=os.getenv("SLACK_CHANNEL_ID")
    )

    # ---------------------------
    # SLACK ENGINE (FIXED)
    # ---------------------------
    slack_engine = TaskEngine(
        handler=slack,
        instructions=[{
            "send_slack_message": {
                "text": "{previous_agent_result}"
            }
        }]
    )

    # ---------------------------
    # FRAUD AGENT (IMPROVED PROMPT)
    # ---------------------------
    fraud_prompt = PromptTemplate(
        system_message="""
You are a bank fraud investigator.

Analyze the account data below and determine fraud risk.

STRICT RULES:
- If new device + new geo → HIGH risk
- If ATO indicators exist → HIGH risk
- If fraud deposit + withdrawal → HIGH risk
- If OTP bypass → increase risk

Return ONLY JSON:

{
  "risk_level": "High | Medium | Somewhat Low | Low",
  "threat_type": "Account takeover | Money mule | First Party | None",
  "recommended_action": "Freeze the account | Put it on watchlist | No issues",
  "explanation": "clear reasoning"
}

DATA:
{context}
"""
    )




    fraud_agent = Agent(
        llm=llm,
        prompt_template=fraud_prompt,
        goal="Detect fraud risk and respond in strict JSON format",
        tool=ai,
        role="Fraud Investigator",
        agent_id="fraud-agent-1",
        name="Fraud Agent",
        output_format="json",
        max_retry=1
    )

    # ---------------------------
    # SLACK AGENT
    # ---------------------------
    slack_agent = Agent(
        llm=None,
        prompt_template=PromptTemplate(),
        engines=[slack_engine],
        agent_id="slack-agent-1",
        name="Slack Agent",
        output_format="json"
    )

    # ---------------------------
    # PIPE
    # ---------------------------
    pipe = AgentXPipe(
        agents=[fraud_agent, slack_agent],
        memory=[],
        name="Fraud Detection Pipe",
        stop_if_goal_not_satisfied=False
    )

    return pipe


# ---------------------------
# MAIN FUNCTION
# ---------------------------
async def main():
    print("🚀 Running Fraud Detection Pipeline...\n")

    context_data = {
        "account_profile_data": {
            "Account Name": "ABC",
            "Current Date": "2026-03-23T09:03:07Z",
            "Account Type": "Checking",
            "Ownership Structure": "Individual",
            "Account purpose": "Transactional account",
            "Account Open Date": "2025-01-11T11:11:14Z",
            "Product Tier": "Standard",
            "Channel Account Opened": "Branch",
            "KYC/IDV Performed": "Y",
            "KYC/IDV Last Performed Date": "2026-01-12T11:09:06Z",
            "KYC/IDV Performed Result": "Passed",
            "Account Standing": "Active",
            "Charge-Offs": "No",
            "Risk Score": "14/100"
        },
        "account_transaction_history": [
            {
                "event_type": "device_registration",
                "device_id": "device_01",
                "ip_address": "119.23.45.32",
                "geo_location": "Atlanta, GA",
                "device_os": "Android",
                "MFA_used": "SMS OTP",
                "Time": "2025-01-16T18:03:07Z"
            },
            {
                "event_type": "deposit",
                "Amount": "9100.00",
                "Deposit_type": "ACB Incoming Deposit",
                "Payor": "Cole Palmer",
                "Bank": "Huntington Bank",
                "Time": "2025-01-19T16:15:22Z"
            },
            {
                "event_type": "deposit",
                "Channel": "Branch",
                "Amount": "2712.00",
                "Deposit_type": "Check Deposit",
                "Payor": "Amy Jeff",
                "Location": "Alpharetta, GA",
                "Time": "2025-05-19T15:01:39Z"
            },
            {
                "event_type": "deposit",
                "Channel": "Mobile",
                "device_id": "device_01",
                "Amount": "2522.00",
                "Deposit_type": "Check Deposit",
                "Payor": "Thomas Peters",
                "Location": "Atlanta, GA",
                "Time": "2025-07-14T15:11:39Z"
            },
            {
                "event_type": "payment",
                "device_id": "device_02",
                "Payee": "Test Corp",
                "Payment_type": "ACH",
                "Amount": "3219.00",
                "Location": "Atlanta, GA",
                "Time": "2025-11-02T10:03:07Z"
            }
        ]
    }
    pipe = await get_pipe()

    result = await pipe.flow(
        query_instruction=f"Investigate this account:\n{context_data}"
    )

    print("\n FINAL RESULT:\n")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
