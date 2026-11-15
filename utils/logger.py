import logging
import os

# Use an absolute path in the user's home directory
LOG_DIR = os.path.expanduser("~/Documents/WeatherMonitor/logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "app.log")

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def log_info(msg):
    logging.info(msg)


def log_error(msg):
    logging.error(msg)
