
from superagentx.agent import Agent
from superagentx.agentxpipe import AgentXPipe
from superagentx.engine import Engine
from superagentx.llm import LLMClient
from superagentx.memory import Memory
from superagentx.prompt import PromptTemplate

# Import handlers
from superagentx_handlers.google.gmail import GmailHandler
from superagentx_handlers.crm.hubspot_crm import HubSpotHandler


async def get_superagentx_voice_to_text_pipe() -> AgentXPipe:
    # LLM Configuration
    llm_config = {
        'llm_type': 'openai'
    }
    llm_client = LLMClient(llm_config=llm_config)

    # Enable Memory
    memory = Memory(memory_config={"llm_client": llm_client})

    # Enable Handler
    gmail_handler = GmailHandler(
        credentials="//path to json crendentials."
    )
    hubspot_handler = HubSpotHandler()

    system_prompt = """
        1. Get last email which is which is subject contains insurance or policy or claim
    """

    hubspot_system_prompt = """
            1. Create only one ticket at a time in hubspot crm
        """

    # Prompt Template

    gmail_prompt_template = PromptTemplate(
        system_message=system_prompt
    )

    hubspot_prompt_template = PromptTemplate(
        system_message=hubspot_system_prompt
    )

    # Read last email to create a new ticket in HubSpot.
    # Example - Engine(s)
    # -------------------
    gmail_engine = Engine(
        handler=gmail_handler,
        llm=llm_client,
        prompt_template=gmail_prompt_template
    )
    hubspot_engine = Engine(
        handler=hubspot_handler,
        llm=llm_client,
        prompt_template=hubspot_prompt_template
    )

    # Create Agents
    # Create Agent with Gmail, Hubspot Engines execute in sequential
    gmail_agent = Agent(
        goal="Get me the best search results",
        role="You are the best gmail reader",
        llm=llm_client,
        prompt_template=gmail_prompt_template,
        engines=[[gmail_engine]]
    )

    hubspot_agent = Agent(
        name='CRM Agent',
        goal="Create new Ticket in Hubspot",
        role="You are the Hubspot admin",
        llm=llm_client,
        prompt_template=hubspot_prompt_template,
        engines=[[hubspot_engine]]
    )

    # Create Pipe - Interface
    # Pipe Interface to send it to public accessible interface (Cli Console / WebSocket / Restful API)
    pipe = AgentXPipe(
        agents=[gmail_agent, hubspot_agent],
        memory=memory
    )
    return pipe

