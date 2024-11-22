import asyncio
from superagentx.handler.send_email import EmailHandler


async def send_email():
    email_handler = EmailHandler(
        host="vetharupini-HP",
        port=0
    )
    body = {
    "sender": "vetharupini@decisionfacts.io",
    "to": ["pbalamurugan297@gmail.com"],
    "subject": "test",
    "body": "Hi"
    }
    await email_handler.send_email(**body)


async def main():
    res = await send_email()

if __name__ == '__main__':
    asyncio.run(main())