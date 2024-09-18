import pytest
import logging

from agentx.handler.weather import WeatherHandler
from pandas.core.frame import DataFrame

logger = logging.getLogger(__name__)

'''
 Run Pytest:  

   1.pytest --log-cli-level=INFO tests/handlers/test_weather_handler.py::TestWeatherHandler::test_forecast_weather
   2.pytest --log-cli-level=INFO tests/handlers/test_weather_handler.py::TestWeatherHandler::test_historical_weather
   3.pytest --log-cli-level=INFO tests/handlers/test_weather_handler.py::TestWeatherHandler::test_climate_weather
   4.pytest --log-cli-level=INFO tests/handlers/test_weather_handler.py::TestWeatherHandler::test_flood_weather
   5.pytest --log-cli-level=INFO tests/handlers/test_weather_handler.py::TestWeatherHandler::test_air_quality_weather
   6.pytest --log-cli-level=INFO tests/handlers/test_weather_handler.py::TestWeatherHandler::test_marine_weather
  
'''


# API KEY is required if commercial. otherwise not required
# w_handler = WeatherHandler(api_key='<API_KEY>')

@pytest.fixture
def weather_client_init() -> WeatherHandler:
    w_handler = WeatherHandler()
    return w_handler


class TestWeatherHandler:
    def test_forecast_weather(self, weather_client_init:WeatherHandler):
        res = weather_client_init.handle(
            location="Chennai",
            forecast_days=7,
            past_days=0,
            current=True,
            daily=True,
            hourly=True,
            action='forecast'
        )
        logger.info(f"query result: {res}")
        assert isinstance(res, dict)
        for key,_res in res.items():
            assert isinstance(_res, DataFrame)

    def test_historical_weather(self, weather_client_init:WeatherHandler):
        res = weather_client_init.handle(
            action="historical",
            location="chennai",
            start_date="2024-08-14",
            end_date="2024-08-28",
            daily=True,
            hourly=True
        )
        logger.info(f"Result: {res}")
        assert isinstance(res, dict)
        for key,_res in res.items():
            assert isinstance(_res, DataFrame)

    def test_climate_weather(self, weather_client_init:WeatherHandler):
        res = weather_client_init.handle(
            location="chennai",
            start_date="2024-08-14",
            end_date="2024-08-28",
            daily=True,
            action="climate"
        )
        logger.info(f"result {res}")
        assert isinstance(res, dict)
        for key,_res in res.items():
            assert isinstance(_res, DataFrame)

    def test_flood_weather(self, weather_client_init:WeatherHandler ):
        res = weather_client_init.handle(
            location="chennai",
            forecast_days=3,
            past_days=0,
            daily=True,
            action="flood"
        )
        logger.info(f"result {res}")
        assert isinstance(res, dict)
        for key, _res in res.items():
            assert isinstance(_res, DataFrame)

    def test_air_quality_weather(self, weather_client_init:WeatherHandler ):
        res = weather_client_init.handle(
            location="chennai",
            forecast_days=3,
            past_days=0,
            current=True,
            hourly=True,
            action="air_quality"
        )
        logger.info(f"Result: {res}")
        assert isinstance(res, dict)
        for key,_res in res.items():
            assert isinstance(_res, DataFrame)

    def test_marine_weather(self, weather_client_init:WeatherHandler ):
        res = weather_client_init.handle(
            location="chennai",
            forecast_days=3,
            past_days=0,
            current=True,
            daily=True,
            hourly=True,
            action="marine"
        )
        logger.info(f"Result: {res}")
        assert isinstance(res, dict)
        for key, _res in res.items():
            assert isinstance(_res, DataFrame)

