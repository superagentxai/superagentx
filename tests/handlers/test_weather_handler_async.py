import logging

import pytest
from pandas.core.frame import DataFrame

from agentx.handler.weather import WeatherHandler

logger = logging.getLogger(__name__)

'''
 Run Pytest:  

   1.pytest --log-cli-level=INFO tests/handlers/test_weather_handler_async.py::TestWeatherHandler::test_forecast_weather
   2.pytest --log-cli-level=INFO tests/handlers/test_weather_handler_async.py::TestWeatherHandler::test_historical_weather
   3.pytest --log-cli-level=INFO tests/handlers/test_weather_handler_async.py::TestWeatherHandler::test_climate_weather
   4.pytest --log-cli-level=INFO tests/handlers/test_weather_handler_async.py::TestWeatherHandler::test_flood_weather
   5.pytest --log-cli-level=INFO tests/handlers/test_weather_handler_async.py::TestWeatherHandler::test_air_quality_weather
   6.pytest --log-cli-level=INFO tests/handlers/test_weather_handler_async.py::TestWeatherHandler::test_marine_weather

'''

# API KEY is required if commercial. otherwise not required
# w_handler = WeatherHandler(api_key='<API_KEY>')
@pytest.fixture
def weather_client_init() -> WeatherHandler:
    w_handler = WeatherHandler()
    return w_handler


class TestWeatherHandler:
    async def test_forecast_weather(self, weather_client_init:WeatherHandler):
        res = await weather_client_init.get_forecast_weather(
            location="Chennai",
            forecast_days=7,
            past_days=0,
            current=True,
            daily=True,
            hourly=True,
        )
        logger.info(f"Result: {res}")
        assert isinstance(res, dict)
        for key, _res in res.items():
            assert isinstance(_res, DataFrame)

    async def test_historical_weather(self, weather_client_init:WeatherHandler):
        res = await  weather_client_init.get_historical_weather(
            location="chennai",
            start_date="2024-08-14",
            end_date="2024-08-28",
            daily=True,
            hourly=True
        )
        logger.info(f"Result: {res}")
        assert isinstance(res, dict)
        for key, _res in res.items():
            assert isinstance(_res, DataFrame)

    async def test_climate_weather(self, weather_client_init:WeatherHandler):
        res = await  weather_client_init.get_climate_weather(
            location="chennai",
            start_date="2024-08-14",
            end_date="2024-08-28",
            daily=True,
        )
        logger.info(f"Result: {res}")
        assert isinstance(res, dict)
        for key, _res in res.items():
            assert isinstance(_res, DataFrame)

    async def test_flood_weather(self, weather_client_init:WeatherHandler):
        res = await  weather_client_init.get_flood_weather(
            location="chennai",
            forecast_days=3,
            past_days=0,
            daily=True,
        )
        logger.info(f"Result: {res}")
        assert isinstance(res, dict)
        for key, _res in res.items():
            assert isinstance(_res, DataFrame)

    async def test_air_quality_weather(self, weather_client_init:WeatherHandler):
        res = await  weather_client_init.get_air_quality_weather(
            location="chennai",
            forecast_days=3,
            past_days=0,
            current=True,
            hourly=True,
        )
        logger.info(f"Result: {res}")
        assert isinstance(res, dict)
        for key, _res in res.items():
            assert isinstance(_res, DataFrame)

    async def test_marine_weather(self, weather_client_init:WeatherHandler):
        res = await  weather_client_init.get_marine_weather(
            location="chennai",
            forecast_days=3,
            past_days=0,
            current=True,
            daily=True,
            hourly=True,
        )
        logger.info(f"Result: {res}")
        assert isinstance(res, dict)
        for key, _res in res.items():
            assert isinstance(_res, DataFrame)
