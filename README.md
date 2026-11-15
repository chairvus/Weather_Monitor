# 🌤️ Weather Monitor System

A modern, real-time and historical weather desktop application built with Python and CustomTkinter. 

This application allows users to search for specific locations (down to the street/village level), view current weather conditions, look up historical weather data by date, and save local snapshots of the data.

## ✨ Features

- **Global Location Search:** Powered by OpenStreetMap Nominatim, allowing precise searches (e.g., villages, districts, or specific streets).
- **Current Weather:** Real-time temperature, humidity, wind speed, and "feels like" data.
- **Historical Data:** Input a past date (`YYYY-MM-DD`) to view the maximum and minimum temperatures for that day.
- **Smart Address Formatting:** Automatically removes duplicate location names (e.g., "Bantul, Bantul, Bantul" becomes "Bantul") and corrects known OpenStreetMap data errors.
- **Auto-Refresh:** Automatically updates current weather data at a configurable interval.
- **Unit Toggle:** Instantly switch between Celsius (°C) and Fahrenheit (°F).
- **Data Logging & Export:** Automatically logs weather data to a local CSV file and allows users to manually export a snapshot to JSON.
- **Dark Mode UI:** A sleek, modern interface built with CustomTkinter.

## 🛠️ Tech Stack

- **Language:** Python 3.13+
- **GUI Framework:** [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)
- **Weather API:** [Open-Meteo](https://open-meteo.com/) (Free, no API key required)
- **Geocoding API:** [OpenStreetMap Nominatim](https://nominatim.org/) (Free, no API key required)
- **Image Processing:** Pillow (PIL)

## 📂 Project Structure

```text
weather-monitor/
│
├── main.py                  # Application entry point
├── config.py                # Configuration and environment variables
├── requirements.txt         # Python dependencies
├── .env                     # Local environment variables (Ignored by Git)
│
├── ui/                      # User Interface modules
│   ├── app_window.py        # Main application window and event loop
│   └── widgets.py           # Custom UI components (Weather Card)
│
├── services/                # External API and data processing
│   ├── weather_api.py       # Handles Open-Meteo and Nominatim API requests
│   └── data_parser.py       # Formats raw JSON into clean data for the UI
│
├── utils/                   # Utility scripts
│   ├── logger.py            # Application logging
│   └── storage.py           # Local CSV and JSON file handling
│
└── assets/                  # Icons, fonts, and images
