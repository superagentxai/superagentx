
#forecast
FORCAST_API_URL = "https://api.open-meteo.com/v1/forecast"
FORCAST_CURRENT_STATUS_VARIABLE = [
    "temperature_2m",
    "relative_humidity_2m",
    "apparent_temperature",
    "is_day",
    "precipitation",
    "rain",
    "showers",
    "snowfall",
    "weather_code",
    "cloud_cover",
    "pressure_msl",
    "surface_pressure",
    "wind_speed_10m",
    "wind_direction_10m",
    "wind_gusts_10m"
]
FORECAST_HOURLY_STATUS_VARIABLE = [
    "temperature_2m",
    "dew_point_2m",
    "rain",
    "showers",
    "snowfall",
    "snow_depth",
    "weather_code",
    "surface_pressure",
    "cloud_cover_low",
    "cloud_cover_mid",
    "cloud_cover_high",
    "visibility",
    "wind_speed_10m",
    "wind_speed_80m",
    "wind_speed_120m",
    "wind_speed_180m",
    "wind_direction_10m",
    "wind_direction_80m",
    "wind_direction_120m",
    "wind_direction_180m",
    "temperature_80m",
    "temperature_120m",
    "temperature_180m",
    "soil_temperature_0cm",
    "soil_temperature_6cm",
    "soil_temperature_18cm",
    "soil_moisture_0_to_1cm",
    "soil_moisture_1_to_3cm"
]
FORECAST_DAILY_STATUS_VARIABLE = [
    "weather_code",
    "temperature_2m_max",
    "temperature_2m_min",
    "apparent_temperature_max",
    "sunrise",
    "sunset",
    "daylight_duration",
    "sunshine_duration",
    "precipitation_sum",
    "rain_sum",
    "showers_sum",
    "snowfall_sum",
    "precipitation_hours",
    "wind_speed_10m_max",
    "wind_gusts_10m_max",
    "wind_direction_10m_dominant",
    "shortwave_radiation_sum"
]

# historical
HISTORICAL_API_URL = "https://archive-api.open-meteo.com/v1/archive"
HISTORICAL_DAILY_STATUS_VARIABLE =[
    "weather_code",
    "temperature_2m_max",
    "temperature_2m_min",
    "temperature_2m_mean",
    "sunrise",
    "sunset",
    "daylight_duration",
    "sunshine_duration",
    "precipitation_sum",
    "rain_sum",
    "snowfall_sum",
    "wind_speed_10m_max",
    "wind_gusts_10m_max",
    "wind_direction_10m_dominant",
    "shortwave_radiation_sum"
]
HISTORICAL_HOURLY_STATUS_VARIABLE =  [
    "temperature_2m",
    "relative_humidity_2m",
    "rain",
    "snowfall",
    "snow_depth",
    "weather_code",
    "surface_pressure",
    "cloud_cover",
    "cloud_cover_high",
    "wind_speed_10m",
    "wind_speed_100m",
    "wind_direction_10m",
    "wind_direction_100m",
    "soil_temperature_0_to_7cm",
    "soil_temperature_7_to_28cm",
    "soil_temperature_28_to_100cm",
    "soil_temperature_100_to_255cm",
    "soil_moisture_7_to_28cm"
]

#marine
MARINE_API_URL = "https://marine-api.open-meteo.com/v1/marine"
MARINE_CURRENT_STATUS_VARIABLE = [
    "wave_height",
    "wave_direction",
    "wind_wave_height",
    "wind_wave_direction",
    "swell_wave_height",
    "swell_wave_direction",
    "ocean_current_velocity",
    "ocean_current_direction"
]
MARINE_HOURLY_STATUS_VARIABLE = [
    "wave_height",
    "wave_direction",
    "wind_wave_height",
    "wind_wave_direction",
    "swell_wave_height",
    "swell_wave_direction",
    "ocean_current_velocity"
]
MARINE_DAILY_STATUS_VARIABLE = [
    "wave_height_max",
    "wave_direction_dominant",
    "swell_wave_height_max",
    "swell_wave_direction_dominant"
]

#air quality
AIR_API_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
AIR_CURRENT_STATUS_VARIABLE =  [
    "carbon_monoxide",
    "nitrogen_dioxide",
    "sulphur_dioxide",
    "ozone",
    "dust",
    "ammonia"
]
AIR_HOURLY_STATUS_VARIABLE = [
    "pm10",
    "pm2_5",
    "carbon_monoxide",
    "nitrogen_dioxide",
    "ozone",
    "dust",
    "ammonia"
]

#climate
CLIMATE_API_URL = "https://climate-api.open-meteo.com/v1/climate"
CLIMATE_MODELS_STATUS_VARIABLE = [
    "CMCC_CM2_VHR4",
    "FGOALS_f3_H",
    "HiRAM_SIT_HR",
    "MRI_AGCM3_2_S",
    "EC_Earth3P_HR",
    "MPI_ESM1_2_XR",
    "NICAM16_8S"
]
CLIMATE_DAILY_STATUS_VARIABLE = [
    "temperature_2m_mean",
    "temperature_2m_max",
    "temperature_2m_min",
    "wind_speed_10m_mean",
    "wind_speed_10m_max",
    "cloud_cover_mean",
    "relative_humidity_2m_mean",
    "relative_humidity_2m_max",
    "precipitation_sum",
    "rain_sum",
    "snowfall_sum"
]

# flood
FLOOD_API_URL = "https://flood-api.open-meteo.com/v1/flood"
FLOOD_DAILY_STATUS_VARIABLE = [
    "river_discharge",
    "river_discharge_mean",
    "river_discharge_median",
    "river_discharge_max",
    "river_discharge_min",
    "river_discharge_p25",
    "river_discharge_p75"
]
FLOOD_MODELS_STATUS_VARIABLE = [
    "seamless_v4",
    "forecast_v4",
    "consolidated_v4",
    "seamless_v3",
    "forecast_v3",
    "consolidated_v3"
]
