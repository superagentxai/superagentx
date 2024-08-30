from agentx.handler.email import EmailHandler

email_handler = EmailHandler(
    host="",
    port=345,
    username="",
    password=""
)


def test_email_1():
    res = email_handler.handle(action="SEND", **{})
    assert res
