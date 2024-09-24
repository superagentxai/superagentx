import pytest

from agentx.handler.email import EmailHandler

'''
 Run Pytest:
   
   1.pytest --log-cli-level=INFO tests/handlers/test_email_handler.py::TestEmail::test_email  
    
'''

@pytest.fixture
def email_client_init() -> EmailHandler:
    email_handler = EmailHandler(
        host="",
        port=345
    )
    return email_handler

class TestEmail:

    async def test_email(self, email_client_init: EmailHandler):
        res = await email_client_init.send_email(**{})
        assert isinstance(res, object)
