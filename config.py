# config.py
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    DEFAULT_CITY = os.getenv("DEFAULT_CITY", "London")
    REFRESH_INTERVAL = int(os.getenv("REFRESH_INTERVAL", 600))

    # Open-Meteo URLs
    GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
    WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
