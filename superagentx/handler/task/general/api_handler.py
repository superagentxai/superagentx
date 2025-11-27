import asyncio

from superagentx.handler.base import BaseHandler


class APIHandler(BaseHandler):

    async def fetch_weather(self, city: str):
        await asyncio.sleep(0.2)
        return {"temp": 26, "condition": "Sunny", "city": city}

    async def fetch_stock(self, symbol: str):
        await asyncio.sleep(0.1)
        raise ValueError("Simulated stock API failure")  # FAIL intentionally

    async def fetch_news(self, topic: str):
        await asyncio.sleep(0.3)
        return {"topic": topic, "headline": "AI is transforming automation!"}

    def combine_successful(self, weather: dict | None, stock: dict | None, news: dict | None):
        return {
            "weather": weather,
            "stock": stock,
            "news": news,
            "summary": "Report generated with available data (failed calls skipped)."
        }
