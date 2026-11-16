import csv
import os
import json
from datetime import datetime
from tkinter import filedialog

# 1. Define the base directory and expand the '~'
DATA_DIR = os.path.expanduser("~/Documents/WeatherMonitor/data")
os.makedirs(DATA_DIR, exist_ok=True)

CSV_FILE = os.path.join(DATA_DIR, "weather_history.csv")
LAST_LOCATION_FILE = os.path.join(DATA_DIR, "last_location.json")


def save_to_csv(data):
    file_exists = os.path.isfile(CSV_FILE)
    with open(CSV_FILE, mode="a", newline="") as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(
                [
                    "Timestamp",
                    "City",
                    "Temp",
                    "Condition",
                    "Humidity (%)",
                    "Wind (km/h)",
                    "Feels Like",
                    "UV Index",
                ]
            )
        writer.writerow(
            [
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                data["city"],
                data["temp"],
                data["condition"],
                data["humidity"],
                data["wind_speed"],
                data.get("feels_like", "N/A"),
                data.get("uv_index", "N/A"),
            ]
        )


def save_manual_snapshot(data):
    file_path = filedialog.asksaveasfilename(
        defaultextension=".json",
        filetypes=[("JSON files", "*.json"), ("Text files", "*.txt")],
        title="Save Weather Snapshot",
    )
    if file_path:
        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)
        return True
    return False


def save_last_location(location_data):
    with open(LAST_LOCATION_FILE, "w") as f:
        json.dump(location_data, f)


def load_last_location():
    if os.path.exists(LAST_LOCATION_FILE):
        try:
            with open(LAST_LOCATION_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return None
    return None
