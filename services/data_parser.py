# services/data_parser.py
from datetime import datetime


def decode_weather_code(code):
    if code == 0:
        return "Clear Sky"
    elif code in [1, 2, 3]:
        return "Partly Cloudy"
    elif code in [45, 48]:
        return "Fog"
    elif code in [51, 53, 55]:
        return "Drizzle"
    elif code in [61, 63, 65]:
        return "Rain"
    elif code in [71, 73, 75]:
        return "Snow"
    elif code in [80, 81, 82]:
        return "Rain Showers"
    elif code in [95, 96, 99]:
        return "Thunderstorm"
    else:
        return "Unknown"


def parse_weather_data(raw_json, location_name, unit, date_str=None):
    temp_symbol = "°C" if unit == "celsius" else "°F"

    if date_str:
        # Parse Historical (Daily) Data
        daily = raw_json["daily"]
        return {
            "city": location_name,
            "local_time": f"Historical Data: {date_str}",
            "temp": f"{daily['temperature_2m_max'][0]} / {daily['temperature_2m_min'][0]}",
            "temp_symbol": temp_symbol,
            # NEW: Format as Max / Min
            "feels_like": f"{daily.get('apparent_temperature_max', ['N/A'])[0]} / {daily.get('apparent_temperature_min', ['N/A'])[0]}",
            "uv_index": daily.get("uv_index_max", ["N/A"])[0],
            "humidity": f"{daily.get('relative_humidity_2m_max', ['N/A'])[0]} / {daily.get('relative_humidity_2m_min', ['N/A'])[0]}",
            "wind_speed": daily.get("wind_speed_10m_max", ["N/A"])[0],
            "condition": decode_weather_code(daily["weather_code"][0]),
            "is_historical": True,
        }
    else:
        # Parse Current Data
        current = raw_json["current"]
        raw_time = current.get("time", "")
        try:
            dt = datetime.fromisoformat(raw_time)
            local_time_str = dt.strftime("%b %d, %Y - %H:%M")
        except:
            local_time_str = raw_time

        return {
            "city": location_name,
            "local_time": local_time_str,
            "temp": current["temperature_2m"],
            "temp_symbol": temp_symbol,
            "feels_like": current["apparent_temperature"],
            "uv_index": current.get("uv_index", 0),
            "humidity": current["relative_humidity_2m"],
            "wind_speed": current["wind_speed_10m"],
            "condition": decode_weather_code(current["weather_code"]),
            "is_historical": False,
        }
