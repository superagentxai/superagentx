import asyncio

from agentx.handler.weather import WeatherHandler

# API KEY is required if commercial. otherwise not required
# w_handler = WeatherHandler(api_key='<API_KEY>')
w_handler = WeatherHandler()


async def test_forecast_weather():
    res = await w_handler.ahandle(
        location="Chennai",
        forecast_days=7,
        past_days=0,
        current=True,
        daily=True,
        hourly=True,
        action='forecast'
    )

    assert res

async def test_historical_weather():
    res = await w_handler.ahandle(
        action="historical",
        location="chennai",
        start_date="2024-08-14",
        end_date="2024-08-28",
        daily=True,
        hourly=True
    )
    assert res

async def test_climate_weather():
    res = await w_handler.ahandle(
        location="chennai",
        start_date="2024-08-14",
        end_date="2024-08-28",
        daily=True,
        action="climate"
    )
    assert res

async def test_flood_weather():
    res = await w_handler.ahandle(
        location="chennai",
        forecast_days=3,
        past_days=0,
        daily=True,
        action="flood"
    )
    assert res

async def test_air_quality_weather():
    res = await w_handler.ahandle(
        location="chennai",
        forecast_days=3,
        past_days=0,
        current=True,
        hourly=True,
        action="air_quality"
    )
    assert res

async def test_marine_weather():
    res = await w_handler.ahandle(
        location="chennai",
        forecast_days=3,
        past_days=0,
        current=True,
        daily=True,
        hourly=True,
        action="marine"
    )
    assert res


if __name__ == '__main__':
    asyncio.run(test_flood_weather())
