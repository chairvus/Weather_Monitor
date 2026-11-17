# services/weather_api.py
import requests
from datetime import datetime
from config import Config
from services.data_parser import parse_weather_data
from utils.logger import log_info, log_error


DISTRICT_CORRECTIONS = {
    "berbah": "Umbulharjo",  # Fixes the Giwangan mismatch
}


def _build_clean_address(place_name, district, city, state, country):
    """
    BEST PRACTICE: De-duplication Loop.
    Combines address parts but removes duplicates.
    Example: ["Bantul", "Bantul", "Bantul", "DIY", "Indonesia"] -> "Bantul, DIY, Indonesia"
    """
    raw_parts = [place_name, district, city, state, country]
    unique_parts = []
    seen = set()

    for part in raw_parts:
        if part and part.strip():
            part_lower = part.strip().lower()
            # If we haven't seen this exact word yet, add it to the list
            if part_lower not in seen:
                unique_parts.append(part.strip())
                seen.add(part_lower)

    return ", ".join(unique_parts)


def search_locations_nominatim(query):
    """Searches for locations and builds a concise, duplicate-free address."""
    try:
        headers = {"User-Agent": "WeatherMonitorApp/1.0"}
        params = {
            "q": query,
            "format": "json",
            "addressdetails": 1,
            "limit": 10,
            "accept-language": "id",
        }
        res = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params=params,
            headers=headers,
            timeout=10,
        )
        res.raise_for_status()

        locations = []
        for res_item in res.json():
            raw_name = res_item.get("display_name", "Unknown")
            addr = res_item.get("address", {})

            # 1. Extract raw components
            place_name = (
                addr.get("name")
                or addr.get("amenity")
                or addr.get("road")
                or addr.get("suburb")
                or addr.get("village")
                or raw_name.split(",")[0]
            )

            raw_district = (
                addr.get("suburb") or addr.get("district") or addr.get("county") or ""
            )
            district = DISTRICT_CORRECTIONS.get(raw_district.lower(), raw_district)

            city = (
                addr.get("city") or addr.get("municipality") or addr.get("town") or ""
            )
            state = addr.get("state") or ""
            country = addr.get("country") or ""

            # 2. Build the clean string using the de-duplication loop
            concise_label = _build_clean_address(
                place_name, district, city, state, country
            )
            if not concise_label:
                concise_label = raw_name

            locations.append(
                {
                    "label": concise_label,
                    "full_address": concise_label,
                    "latitude": float(res_item["lat"]),
                    "longitude": float(res_item["lon"]),
                    "name": concise_label,
                }
            )
        return locations
    except Exception as e:
        log_error(f"Nominatim search failed: {str(e)}")
        return []


def reverse_geocode_nominatim(lat, lon):
    """Gets the address from coordinates with de-duplication."""
    try:
        headers = {"User-Agent": "WeatherMonitorApp/1.0"}
        params = {
            "lat": lat,
            "lon": lon,
            "format": "json",
            "addressdetails": 1,
            "accept-language": "id",
        }
        res = requests.get(
            "https://nominatim.openstreetmap.org/reverse",
            params=params,
            headers=headers,
            timeout=10,
        )
        res.raise_for_status()
        data = res.json()

        addr = data.get("address", {})
        place_name = (
            addr.get("amenity")
            or addr.get("road")
            or addr.get("suburb")
            or "Current Location"
        )

        raw_district = (
            addr.get("suburb") or addr.get("district") or addr.get("county") or ""
        )
        district = DISTRICT_CORRECTIONS.get(raw_district.lower(), raw_district)

        city = addr.get("city") or addr.get("municipality") or addr.get("town") or ""
        state = addr.get("state") or ""
        country = addr.get("country") or ""

        clean_address = _build_clean_address(place_name, district, city, state, country)
        return clean_address if clean_address else "Unknown Location"
    except Exception as e:
        log_error(f"Reverse geocode failed: {str(e)}")
        return "Unknown Location"


def fetch_weather_by_coords(lat, lon, location_name, unit="celsius", date_str=None):
    """Fetches weather data (Current or Historical) from Open-Meteo."""
    try:
        if date_str:
            selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            if selected_date > datetime.now().date():
                raise ValueError(
                    "Future dates are not supported by the Historical API."
                )

            base_url = "https://archive-api.open-meteo.com/v1/archive"
            weather_query = (
                f"latitude={lat}&longitude={lon}"
                "&daily=temperature_2m_max,temperature_2m_min,weather_code,wind_speed_10m_max,uv_index_max,"
                "relative_humidity_2m_max,relative_humidity_2m_min,apparent_temperature_max,apparent_temperature_min"
                f"&temperature_unit={unit}&timezone=auto&start_date={date_str}&end_date={date_str}"
            )
        else:
            base_url = "https://api.open-meteo.com/v1/forecast"
            weather_query = (
                f"latitude={lat}&longitude={lon}"
                "&current=temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code,apparent_temperature,uv_index"
                f"&temperature_unit={unit}&timezone=auto"
            )

        url = f"{base_url}?{weather_query}"
        res = requests.get(url, timeout=10)
        res.raise_for_status()

        return parse_weather_data(res.json(), location_name, unit, date_str)
    except Exception as e:
        log_error(f"Failed to fetch weather for {location_name}: {str(e)}")
        raise e
