import logging

import pytest

from agentx.handler.google.gmail import GmailHandler

logger = logging.getLogger(__name__)

'''
  Run Pytest:
  
    1.pytest --log-cli-level=INFO tests/handlers/test_gmail_handler.py::TestGmailHandler::test_get_user_profile
    2.pytest --log-cli-level=INFO tests/handlers/test_gmail_handler.py::TestGmailHandler::test_send_email
    3.pytest --log-cli-level=INFO tests/handlers/test_gmail_handler.py::TestGmailHandler::test_create_draft_email  
'''


@pytest.fixture
def gmail_handler_init() -> GmailHandler:
    gmail_handler = GmailHandler(
        credentials=""
    )
    return gmail_handler


class TestGmailHandler:

    async def test_get_user_profile(self, gmail_handler_init: GmailHandler):
        res = await gmail_handler_init.get_user_profile()
        logger.info(f"Result: {res}")
        assert res

    async def test_send_email(self, gmail_handler_init: GmailHandler):
        res = await gmail_handler_init.send_email(
            from_address="arul@decisionfacts.io",
            to="syed@decisionfacts.io",
            subject="Test Email",
            content="Hi anna this is test email from handler"
        )
        logger.info(f"Result: {res}")
        assert res

    async def test_create_draft_email(self, gmail_handler_init: GmailHandler):
        res = await gmail_handler_init.create_draft_email(
            from_address="arul@decisionfacts.io",
            to="syed@decisionfacts.io"
        )
        logger.info(f"Result: {res}")
        assert res
