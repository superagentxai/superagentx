from abc import ABC
from enum import Enum
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pandas as pd
from typing import Any

from agentx.handler.base import BaseHandler
from agentx.handler.weather.base import WeatherBase
from agentx.handler.weather.constants import marine_current_status_variable, marine_daily_status_variable, \
    marine_hourly_status_variable, air_current_status_variable, air_hourly_status_variable, \
    climate_models_status_variable, climate_daily_status_variable, historical_daily_status_variable, \
    historical_hourly_status_variable, forecast_current_status_variable, forecast_hourly_status_variable, \
    forecast_daily_status_variable, flood_models_status_variable, flood_daily_status_variable, forecast_api_url, \
    historical_api_url, climate_api_url, marine_api_url, air_api_url, flood_api_url
from agentx.handler.weather.exception import InvalidWeatherAction, InvalidLocation, InvalidResponseType


class ResponseType(str, Enum):
    current = 'current'
    daily = 'daily'
    hourly = 'hourly'

class ReportType(str, Enum):
    historical = 'historical'
    forecast = 'forecast'
    climate = 'climate'
    marine = 'marine'
    air_quality = 'air_quality'
    flood = 'flood'


def get_longitude(location):
    if location:
        geolocator = Nominatim(user_agent="WeatherTest")
        location = geolocator.geocode(location)
        return location.longitude
    else:
        raise InvalidLocation(f"Location {location} is not valid")


def get_latitude(location):
    if location:
        geolocator = Nominatim(user_agent="WeatherTest")
        location = geolocator.geocode(location)
        return location.latitude
    else:
        raise InvalidLocation(f"Location {location} is not valid")


def get_default_params(location: str) -> dict:
    tz = TimezoneFinder()
    lat = get_latitude(location)
    lng = get_longitude(location)
    param = {
        "latitude": lat,
        "longitude":lng,
        "timezone": tz.timezone_at(lng=lng, lat=lat)
    }
    return param

def get_result_parser(response, variables, res_type: ResponseType):
    result = {}
    data ={}
    if response and response[0]:
        if res_type == ResponseType.hourly:
            data = response[0].Hourly()
        elif res_type == ResponseType.daily:
            data = response[0].Daily()
        elif res_type == ResponseType.current:
            data = response[0].Current()
        else:
            raise InvalidResponseType("Invalid response type")

    if res_type != ResponseType.current:
        result = {"date": pd.date_range(
            start=pd.to_datetime(data.Time(), unit="s", utc=True),
            end=pd.to_datetime(data.TimeEnd(), unit="s", utc=True),
            freq=pd.Timedelta(seconds=data.Interval()),
            inclusive="left"
        )}
        for idx, item in enumerate(variables):
            result[item] = data.Variables(idx).ValuesAsNumpy()
    else:
        for idx, item in enumerate(variables):
            result[item] = data.Variables(idx).Value()
        result = [result]

    dataframe = pd.DataFrame(data=result)
    return dataframe


class WeatherHandler(BaseHandler):

    def __init__(self,
                 api_key: str | None = None,
                 ):
        self.api_key = api_key


    def get_historical_weather(self,location: str, start_date:str, end_date:str, daily:bool, hourly: bool ):
        params = get_default_params(location)
        params['start_date'] =start_date,
        params['end_date'] = end_date,
        response = {}
        if daily:
            params['daily'] = historical_daily_status_variable
        if hourly:
            params['hourly'] = historical_hourly_status_variable

        obj = WeatherBase(params,historical_api_url, self.api_key)
        res = obj.get_weather_report()
        if daily:
            response['daily'] = get_result_parser(res, historical_daily_status_variable , ResponseType.daily)
        if hourly:
            response['hourly'] = get_result_parser(res, historical_hourly_status_variable , ResponseType.hourly)
        return response

    def get_forecast_weather(self,location: str, forecast_days:int, past_days: int, current:bool, daily:bool, hourly: bool):
        params = get_default_params(location)
        response = {}
        if forecast_days and 0<forecast_days:
            params['forecast_days'] = forecast_days,
        if past_days and 0<past_days:
            params['past_days'] = past_days,

        if current:
            params['current'] = forecast_current_status_variable
        if daily:
            params['daily'] = forecast_daily_status_variable
        if hourly:
            params['hourly'] = forecast_hourly_status_variable

        obj = WeatherBase(params, forecast_api_url, self.api_key)
        res = obj.get_weather_report()
        if current:
            response['current'] = get_result_parser(res, forecast_current_status_variable, ResponseType.current)
        if daily:
            response['daily'] = get_result_parser(res, forecast_daily_status_variable, ResponseType.daily)
        if hourly:
            response['hourly'] = get_result_parser(res, forecast_hourly_status_variable, ResponseType.hourly)

        return response

    def get_climate_weather(self,location: str, start_date:str, end_date:str, daily:bool ):
        params = get_default_params(location)
        params['start_date'] = start_date,
        params['end_date'] = end_date,
        params['models'] = climate_models_status_variable,
        response = {}
        if daily:
            params['daily'] = climate_daily_status_variable
        obj = WeatherBase(params, climate_api_url, self.api_key)
        res = obj.get_weather_report()
        if daily:
            response['daily'] = get_result_parser(res, climate_daily_status_variable, ResponseType.daily)

        return response

    def get_marine_weather(self,location: str, forecast_days:int, past_days: int, current:bool, daily:bool, hourly: bool):
        params = get_default_params(location)
        response = {}
        if forecast_days and 0< forecast_days:
            params['forecast_days'] = forecast_days,
        if past_days and 0<past_days:
            params['past_days'] = past_days,
        if current:
            params['current'] = marine_current_status_variable
        if daily:
            params['daily'] = marine_daily_status_variable
        if hourly:
            params['hourly'] = marine_hourly_status_variable
        obj = WeatherBase(params, marine_api_url, self.api_key)
        res = obj.get_weather_report()
        if current:
            response['current'] = get_result_parser(res, marine_current_status_variable, ResponseType.current)
        if daily:
            response['daily'] = get_result_parser(res, marine_daily_status_variable, ResponseType.daily)
        if hourly:
            response['hourly'] = get_result_parser(res, marine_hourly_status_variable, ResponseType.hourly)

        return response

    def get_air_quality_weather(self,location: str, forecast_days:int, past_days: int, current:bool, hourly: bool):
        params = get_default_params(location)
        response = {}
        if forecast_days and 0<forecast_days:
            params['forecast_days'] = forecast_days,
        if past_days and 0<past_days:
            params['past_days'] = past_days,
        if current:
            params['current'] = air_current_status_variable
        if hourly:
            params['hourly'] = air_hourly_status_variable
        obj = WeatherBase(params,air_api_url, self.api_key)
        res = obj.get_weather_report()
        if current:
            response['current'] = get_result_parser(res, air_current_status_variable, ResponseType.current)
        if hourly:
            response['hourly'] = get_result_parser(res, air_hourly_status_variable, ResponseType.hourly)

        return response

    def get_flood_weather(self,location: str, forecast_days:int, past_days: int, daily:bool):
        params = get_default_params(location)
        params['models'] = flood_models_status_variable
        response = {}
        if forecast_days and 0<forecast_days:
            params['forecast_days'] = forecast_days,
        if past_days and 0<past_days:
            params['past_days'] = past_days,
        if daily:
            params['daily'] = flood_daily_status_variable
        obj = WeatherBase(params,flood_api_url, self.api_key)
        res = obj.get_weather_report()
        if daily:
            response['daily'] = get_result_parser(res, flood_daily_status_variable, ResponseType.daily)

        return response

    def handle(
            self,
            action: str | Enum,
            *args,
            **kwargs
    ) -> Any:
        if isinstance(action, str):
            action = action.lower()
        match action:
            case ReportType.forecast:
                return self.get_forecast_weather(**kwargs)
            case ReportType.historical:
                return self.get_historical_weather(**kwargs)
            case ReportType.climate:
                return self.get_climate_weather(**kwargs)
            case ReportType.flood:
                return self.get_flood_weather(**kwargs)
            case ReportType.air_quality:
                return self.get_air_quality_weather(**kwargs)
            case ReportType.marine:
                return self.get_marine_weather(**kwargs)
            case _:
                raise InvalidWeatherAction(f"Invalid report type of weather `{action}`")





