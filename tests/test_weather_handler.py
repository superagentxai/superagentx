from agentx.handler.weather import WeatherHandler

# API KEY is required if commercial. otherwise not required
# w_handler = WeatherHandler(api_key='<API_KEY>')
w_handler = WeatherHandler()


def test_forecast_weather():
    res = w_handler.handle(
        location="Chennai",
        forecast_days=7,
        past_days=0,
        current=True,
        daily=True,
        hourly=True,
        action='forecast'
    )

    assert res

def test_historical_weather():
    res = w_handler.handle(
        action="historical",
        location="chennai",
        start_date="2024-08-14",
        end_date="2024-08-28",
        daily=True,
        hourly=True
    )
    assert res

def test_climate_weather():
    res = w_handler.handle(location="chennai",
                           start_date="2024-08-14",
                           end_date="2024-08-28",
                           daily=True,
                           action="climate"
                           )
    assert res

def test_flood_weather():
    res = w_handler.handle(location="chennai",
                           forecast_days=3,
                           past_days=0,
                           daily=True,
                           action="flood"
                           )
    assert res
def test_air_quality_weather():
    res = w_handler.handle(location="chennai",
                           forecast_days=3,
                           past_days=0,
                           current=True,
                           hourly=True,
                           action="air_quality"
                           )
    assert res
def test_marine_weather():
    res = w_handler.handle(location="chennai",
                           forecast_days=3,
                           past_days=0,
                           current=True,
                           daily=True,
                           hourly=True,
                           action="marine"
                           )
    assert res




