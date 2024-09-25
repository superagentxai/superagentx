from agentx.handler.google.gmail import GmailHandler

gmail_handler = GmailHandler(
    credentials="/Users/arulvivek/Desktop/Agentx/credentials.json"
)


def test_email_count():
    res = gmail_handler.get_user_profile()
    # print(res)


def test_send_email():
    res = gmail_handler.send_email(
        from_address="arul@decisonforce.io",
        to="vasankeerthi502@gmail.com",
        subject="Test Sample",
        content="Hi Keerthi How are you?"
    )
    print(res)


def test_create_draft_email():
    res = gmail_handler.create_draft_email(
        from_address="arul@decisonforce.io",
        to="syed@decisionforce.io",
    )
    print(res)
