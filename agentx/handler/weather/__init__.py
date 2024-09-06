from enum import Enum
from typing import Any

import pandas as pd
from agentx.handler.base import BaseHandler
from agentx.handler.weather.base import WeatherBase
from agentx.handler.weather.constants import MARINE_CURRENT_STATUS_VARIABLE, MARINE_DAILY_STATUS_VARIABLE, \
    MARINE_HOURLY_STATUS_VARIABLE, AIR_CURRENT_STATUS_VARIABLE, AIR_HOURLY_STATUS_VARIABLE, \
    CLIMATE_MODELS_STATUS_VARIABLE, CLIMATE_DAILY_STATUS_VARIABLE, HISTORICAL_DAILY_STATUS_VARIABLE, \
    HISTORICAL_HOURLY_STATUS_VARIABLE, FORCAST_CURRENT_STATUS_VARIABLE, FORECAST_HOURLY_STATUS_VARIABLE, \
    FORECAST_DAILY_STATUS_VARIABLE, FLOOD_MODELS_STATUS_VARIABLE, FLOOD_DAILY_STATUS_VARIABLE, FORCAST_API_URL, \
    HISTORICAL_API_URL, CLIMATE_API_URL, MARINE_API_URL, AIR_API_URL, FLOOD_API_URL
from agentx.handler.weather.exception import InvalidWeatherAction, InvalidLocation, InvalidResponseType
from agentx.utils.helper import sync_to_async
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder


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

def get_result_parser(
        *,
        response,
        variables,
        res_type: ResponseType
):
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

    def __init__(
            self,
            api_key: str | None = None,
    ):
        self.api_key = api_key


    def get_historical_weather(
            self,
            *,
            location: str,
            start_date:str,
            end_date:str,
            daily:bool,
            hourly: bool
    ):
        params = get_default_params(location)
        params['start_date'] =start_date,
        params['end_date'] = end_date,
        response = {}
        if daily:
            params['daily'] = HISTORICAL_DAILY_STATUS_VARIABLE
        if hourly:
            params['hourly'] = HISTORICAL_HOURLY_STATUS_VARIABLE

        obj = WeatherBase(
            params=params,
            url=HISTORICAL_API_URL,
            api_key=self.api_key
        )
        res = obj.get_weather_report()
        if daily:
            response['daily'] = get_result_parser(
                response=res,
                variables=HISTORICAL_DAILY_STATUS_VARIABLE,
                res_type=ResponseType.daily
            )
        if hourly:
            response['hourly'] = get_result_parser(
                response=res,
                variables=HISTORICAL_HOURLY_STATUS_VARIABLE,
                res_type=ResponseType.hourly
            )
        return response

    def get_forecast_weather(
            self,
            *,
            location: str,
            forecast_days:int,
            past_days: int,
            current:bool,
            daily:bool,
            hourly: bool
    ):
        params = get_default_params(location)
        response = {}
        if forecast_days and 0 < forecast_days:
            params['forecast_days'] = forecast_days,
        if past_days and 0 < past_days:
            params['past_days'] = past_days,

        if current:
            params['current'] = FORCAST_CURRENT_STATUS_VARIABLE
        if daily:
            params['daily'] = FORECAST_DAILY_STATUS_VARIABLE
        if hourly:
            params['hourly'] = FORECAST_HOURLY_STATUS_VARIABLE

        obj = WeatherBase(
            params=params,
            url=FORCAST_API_URL,
            api_key=self.api_key
        )
        res = obj.get_weather_report()
        if current:
            response['current'] = get_result_parser(
                response=res,
                variables=FORCAST_CURRENT_STATUS_VARIABLE,
                res_type=ResponseType.current
            )
        if daily:
            response['daily'] = get_result_parser(
                response=res,
                variables=FORECAST_DAILY_STATUS_VARIABLE,
                res_type=ResponseType.daily
            )
        if hourly:
            response['hourly'] = get_result_parser(
                response=res,
                variables=FORECAST_HOURLY_STATUS_VARIABLE,
                res_type=ResponseType.hourly
            )
        return response

    def get_climate_weather(
            self,
            *,
            location: str,
            start_date: str,
            end_date: str,
            daily: bool
    ):
        params = get_default_params(location)
        params['start_date'] = start_date,
        params['end_date'] = end_date,
        params['models'] = CLIMATE_MODELS_STATUS_VARIABLE,
        response = {}
        if daily:
            params['daily'] = CLIMATE_DAILY_STATUS_VARIABLE
        obj = WeatherBase(
            params=params,
            url=CLIMATE_API_URL,
            api_key=self.api_key
        )
        res = obj.get_weather_report()
        if daily:
            response['daily'] = get_result_parser(
                response=res,
                variables=CLIMATE_DAILY_STATUS_VARIABLE,
                res_type=ResponseType.daily
            )
        return response

    def get_marine_weather(
            self,
            *,
            location: str,
            forecast_days: int,
            past_days: int,
            current: bool,
            daily: bool,
            hourly: bool
    ):
        params = get_default_params(location)
        response = {}
        if forecast_days and 0 < forecast_days:
            params['forecast_days'] = forecast_days,
        if past_days and 0<past_days:
            params['past_days'] = past_days,
        if current:
            params['current'] = MARINE_CURRENT_STATUS_VARIABLE
        if daily:
            params['daily'] = MARINE_DAILY_STATUS_VARIABLE
        if hourly:
            params['hourly'] = MARINE_HOURLY_STATUS_VARIABLE
        obj = WeatherBase(
            params=params,
            url=MARINE_API_URL,
            api_key=self.api_key
        )
        res = obj.get_weather_report()
        if current:
            response['current'] = get_result_parser(
                response=res,
                variables=MARINE_CURRENT_STATUS_VARIABLE,
                res_type=ResponseType.current
            )
        if daily:
            response['daily'] = get_result_parser(
                response=res,
                variables=MARINE_DAILY_STATUS_VARIABLE,
                res_type=ResponseType.daily
            )
        if hourly:
            response['hourly'] = get_result_parser(
                response=res,
                variables=MARINE_HOURLY_STATUS_VARIABLE,
                res_type=ResponseType.hourly
            )
        return response

    def get_air_quality_weather(
            self,
            *,
            location: str,
            forecast_days: int,
            past_days: int,
            current: bool,
            hourly: bool
    ):
        params = get_default_params(location)
        response = {}
        if forecast_days and 0<forecast_days:
            params['forecast_days'] = forecast_days,
        if past_days and 0<past_days:
            params['past_days'] = past_days,
        if current:
            params['current'] = AIR_CURRENT_STATUS_VARIABLE
        if hourly:
            params['hourly'] = AIR_HOURLY_STATUS_VARIABLE
        obj = WeatherBase(
            params=params,
            url=AIR_API_URL,
            api_key=self.api_key
        )
        res = obj.get_weather_report()
        if current:
            response['current'] = get_result_parser(
                response=res,
                variables=AIR_CURRENT_STATUS_VARIABLE,
                res_type=ResponseType.current
            )
        if hourly:
            response['hourly'] = get_result_parser(
                response=res,
                variables=AIR_HOURLY_STATUS_VARIABLE,
                res_type=ResponseType.hourly
            )
        return response

    def get_flood_weather(
            self,
            location: str,
            forecast_days: int,
            past_days: int,
            daily: bool
    ):
        params = get_default_params(location)
        params['models'] = FLOOD_MODELS_STATUS_VARIABLE
        response = {}
        if forecast_days and 0 < forecast_days:
            params['forecast_days'] = forecast_days,
        if past_days and 0<past_days:
            params['past_days'] = past_days,
        if daily:
            params['daily'] = FLOOD_DAILY_STATUS_VARIABLE
        obj = WeatherBase(
            params=params,
            url=FLOOD_API_URL,
            api_key=self.api_key
        )
        res = obj.get_weather_report()
        if daily:
            response['daily'] = get_result_parser(
                response=res,
                variables=FLOOD_DAILY_STATUS_VARIABLE,
                res_type=ResponseType.daily
            )
        return response

    async def ahandle(
            self,
            *,
            action: str | Enum,
            **kwargs
    ) -> Any:
        if isinstance(action, str):
            action = action.lower()
        match action:
            case ReportType.forecast:
                return await sync_to_async(self.get_forecast_weather, **kwargs)
            case ReportType.historical:
                return await sync_to_async(self.get_historical_weather, **kwargs)
            case ReportType.climate:
                return await sync_to_async(self.get_climate_weather, **kwargs)
            case ReportType.flood:
                return await sync_to_async(self.get_flood_weather, **kwargs)
            case ReportType.air_quality:
                return await sync_to_async(self.get_air_quality_weather, **kwargs)
            case ReportType.marine:
                return await sync_to_async(self.get_marine_weather, **kwargs)
            case _:
                raise InvalidWeatherAction(f"Invalid report type of weather `{action}`")

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
