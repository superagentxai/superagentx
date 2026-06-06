import asyncio
from superagentx.handler.base import BaseHandler


class DummyHandler(BaseHandler):

    async def get_name(self, **kwargs):
        await asyncio.sleep(0.01)
        return {"name": "SuperAgentX"}

    async def get_age(self):
        return {"age": 5}

    async def fail_method(self):
        raise ValueError("Simulated failure")

    def greet(self, name: dict):
        print(f"Hello, {name} !")

        print(f"Previous agent result: {name}")
        return {"greeting": f"Hello {name}!"}

    async def echo(self, value):
        return {"value": value}
