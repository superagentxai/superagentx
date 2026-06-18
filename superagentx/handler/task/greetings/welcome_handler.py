import logging
from superagentx.handler.base import BaseHandler

logger = logging.getLogger(__name__)


class WelcomeHandler(BaseHandler):
    """
    Simple handler used to demonstrate CodeEngine functionality.
    Returns raw dicts so CodeEngine can unwrap them properly.
    """

    def __init__(self, first_name: str | None = None, last_name: str | None = None):
        super().__init__()
        self.first_name = first_name
        self.last_name = last_name

    async def get_first_name(self) -> dict:
        """
        Return the user's first name or default to 'SuperAgentX'.
        Returns a raw dict so CodeEngine can parse it directly.
        """
        first_name = self.first_name or "SuperAgentX"
        last_name = self.last_name

        logger.debug("WelcomeHandler.get_first_name -> %s", first_name)

        return {"first_name": first_name, "last_name": last_name}

    async def send_greeting(self, message: str) -> dict:
        """
        Send a greeting message.
        """
        logger.info("Sending greeting: %s", message)

        return {
            "status": "sent",
            "message": message
        }
