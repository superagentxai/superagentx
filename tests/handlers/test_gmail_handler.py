import logging

import pytest

from superagentx.handler.google.gmail import GmailHandler

logger = logging.getLogger(__name__)

'''
  Run Pytest:
  
    1.pytest --log-cli-level=INFO tests/handlers/test_gmail_handler.py::TestGmailHandler::test_get_user_profile
    2.pytest --log-cli-level=INFO tests/handlers/test_gmail_handler.py::TestGmailHandler::test_send_email
    3.pytest --log-cli-level=INFO tests/handlers/test_gmail_handler.py::TestGmailHandler::test_create_draft_email
    4.pytest --log-cli-level=INFO tests/handlers/test_gmail_handler.py::TestGmailHandler::test_read_mail
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

    async def test_read_mail(self, gmail_handler_init: GmailHandler):
        res = await gmail_handler_init.read_mail()
        logger.info(f"Inbox: {res}")
        # assert res

    async def test_send_email(self, gmail_handler_init: GmailHandler):
        res = await gmail_handler_init.send_email(
            from_address="",
            to="",
            subject="",
            content=""
        )
        logger.info(f"Result: {res}")
        assert res

    async def test_create_draft_email(self, gmail_handler_init: GmailHandler):
        res = await gmail_handler_init.create_draft_email(
            from_address="",
            to=""
        )
        logger.info(f"Result: {res}")
        assert res
