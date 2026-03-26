import logging
import json
import re

from superagentx.llm import LLMClient, ChatCompletionParams
from superagentx.prompt import PromptTemplate

logger = logging.getLogger(__name__)


async def _parse_llm_response(response):

    # -----------------------------
    # Normalize response
    # -----------------------------
    if isinstance(response, list) and response:
        response = response[0]

    if hasattr(response, "content"):
        text = response.content
    else:
        text = response

    if not isinstance(text, str):
        return None

    text = text.strip()

    # remove Markdown code block
    text = text.replace("```json", "").replace("```", "").strip()

    # -----------------------------
    # Try JSON parse
    # -----------------------------
    try:
        return json.loads(text)
    except Exception:
        pass

    # -----------------------------
    # Extract JSON array
    # -----------------------------
    match = re.search(r"\[.*?]", text, re.S)

    if match:
        try:
            return json.loads(match.group())
        except Exception:
            pass

    return None


class RouterEngine:
    """
    Dynamic routing engine for SuperAgentX.

    Routing priority:
        1. Condition routing
        2. Capability routing
        3. LLM routing
        4. Fallback
    """

    def __init__(
        self,
        condition_fn=None,
        llm: LLMClient = None,
        mode="hybrid"
    ):
        self.condition_fn = condition_fn
        self.llm = llm
        self.mode = mode

    async def route(self, agents, context):

        try:

            query = str(context.get("query", "")).lower()

            # ------------------------------------------------
            # CONDITION ROUTING
            # ------------------------------------------------
            if self.mode in ("condition", "hybrid") and self.condition_fn:

                roles = self.condition_fn(context)

                if roles:

                    filtered = [
                        a for a in agents
                        if getattr(a, "role", None) in roles
                    ]

                    if filtered:
                        logger.debug(
                            f"Router(condition): {[a.role for a in filtered]}"
                        )
                        return filtered

            # ------------------------------------------------
            # CAPABILITY ROUTING
            # ------------------------------------------------
            if self.mode in ("capability", "hybrid"):

                capable_agents = []

                for agent in agents:

                    caps = getattr(agent, "capabilities", [])

                    for cap in caps:
                        if cap.lower() in query:
                            capable_agents.append(agent)
                            break

                if capable_agents:

                    logger.debug(
                        f"Router(capability): {[a.role for a in capable_agents]}"
                    )

                    return capable_agents

            # ------------------------------------------------
            # LLM ROUTING
            # ------------------------------------------------
            if self.mode in ("llm", "hybrid") and self.llm:

                agent_names = [a.role for a in agents]

                prompt = f"""
You are an AI routing system.

Task:
{query}

Available agents:
{agent_names}

Select which agents should execute this task.

Return ONLY JSON list of agent names.

Example:
["agent1","agent2"]
"""
                prompt_template = PromptTemplate()
                messages = await prompt_template.get_messages(
                    input_prompt=prompt
                )
                chat_params = ChatCompletionParams(messages=messages)
                response = await self.llm.afunc_chat_completion(chat_completion_params=chat_params)
                selected = await _parse_llm_response(response)

                if selected:

                    filtered = [
                        a for a in agents
                        if a.role in selected
                    ]

                    if filtered:

                        logger.debug(
                            f"Router(llm): {[a.role for a in filtered]}"
                        )

                        return filtered

            # ------------------------------------------------
            # FALLBACK
            # ------------------------------------------------
            logger.debug("Router(fallback): returning all agents")

            return agents

        except Exception as e:

            logger.warning(f"RouterEngine error: {e}")

            return agents

