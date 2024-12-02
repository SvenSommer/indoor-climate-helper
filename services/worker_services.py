import os
import time
import logging
import threading
from modules.shelly_module import get_shelly_environment
from modules.weather_module import get_weather_data
from services.database_service import DatabaseService
from dotenv import load_dotenv

load_dotenv()
LOG_FILE = os.getenv("LOG_FILE", "app.log")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
LATITUDE = float(os.getenv("LATITUDE", 0.0))
LONGITUDE = float(os.getenv("LONGITUDE", 0.0))
LOCATION_NAME = os.getenv("LOCATION_NAME", "Potsdam")
INTERVAL_SECONDS_WEATHER = int(os.getenv("INTERVAL_SECONDS_WEATHER", 120))  # Default: 2 minute
INTERVAL_SECONDS_SHELLY = int(os.getenv("INTERVAL_SECONDS_SHELLY", 60))  # Default: 1 minute

class WorkerThreads:
    def __init__(self):
        self.weather_thread = None
        self.shelly_thread = None

    def start_threads(self):
        if not self.weather_thread or not self.weather_thread.is_alive():
            self.weather_thread = threading.Thread(target=self.periodic_weather_update, daemon=True)
            self.weather_thread.start()
            logging.info("Weather thread started.")
        else:
            logging.info("Weather thread is already running. Skipping start.")

        if not self.shelly_thread or not self.shelly_thread.is_alive():
            self.shelly_thread = threading.Thread(target=self.periodic_shelly_update, daemon=True)
            self.shelly_thread.start()
            logging.info("Shelly thread started.")
        else:
            logging.info("Shelly thread is already running. Skipping start.")

    @staticmethod
    def periodic_weather_update():
        db_service = DatabaseService()  # Verbindung nur einmal öffnen
        try:
            while True:
                WorkerThreads.save_weather_data(db_service)
                time.sleep(INTERVAL_SECONDS_WEATHER)
        except Exception as e:
            logging.error(f"Error in periodic weather update: {e}")
        finally:
            db_service.close()

    @staticmethod
    def periodic_shelly_update():
        db_service = DatabaseService()  # Verbindung nur einmal öffnen
        try:
            while True:
                WorkerThreads.save_shelly_data(db_service)
                time.sleep(INTERVAL_SECONDS_SHELLY)
        except Exception as e:
            logging.error(f"Error in periodic Shelly update: {e}")
        finally:
            db_service.close()

    @staticmethod
    def save_weather_data(db_service):
        try:
            temperature, humidity = get_weather_data(LATITUDE, LONGITUDE, OPENWEATHER_API_KEY)
            if temperature is not None and humidity is not None:
                external_room = db_service.get_room_by_name(LOCATION_NAME)
                if external_room:
                    db_service.save_measurement(external_room.id, temperature, humidity)
                    logging.info("Weather data saved successfully.")
                else:
                    logging.error("External room not found. Weather data not saved.")
        except Exception as e:
            logging.error(f"Error saving weather data: {e}")

    @staticmethod
    def save_shelly_data(db_service):
        try:
            shelly_devices = db_service.get_shelly_devices()
            for device in shelly_devices:
                temperature, humidity = get_shelly_environment(device.ip)
                if temperature is not None and humidity is not None:
                    db_service.save_measurement(device.room_id, temperature, humidity)
                    logging.info(f"Shelly data saved for device '{device.name}' (IP: {device.ip}).")
                else:
                    logging.error(f"Failed to fetch data for Shelly device '{device.name}' (IP: {device.ip}).")
        except Exception as e:
            logging.error(f"Error saving Shelly data: {e}")