import pytest

from agentx.handler.email import EmailHandler

'''
 Run Pytest:
   
   # sync 
   1.pytest --log-cli-level=INFO tests/handlers/test_email_handler.py::TestEmail::test_email
   
   # async
   2.pytest --log-cli-level=INFO tests/handlers/test_email_handler.py::TestEmail::test_aemail  
    
'''

@pytest.fixture
def email_client_init() -> EmailHandler:
    email_handler = EmailHandler(
        host="",
        port=345,
        username="",
        password=""
    )
    return email_handler

class TestEmail:

    def test_email(self, email_client_init: EmailHandler):
        res = email_client_init.handle(action="SEND", **{})
        assert isinstance(res, object)

    def test_aemail(self, email_client_init: EmailHandler):
        res = email_client_init.ahandle(action="SEND", **{})
        assert isinstance(res, object)
