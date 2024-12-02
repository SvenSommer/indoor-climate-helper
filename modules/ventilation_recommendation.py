from datetime import datetime, timedelta
import logging
from pytz import timezone

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

def calculate_ventilation_recommendation(db_service, room_id):
    """
    Berechnet die Lüftungsempfehlung für einen Raum basierend auf historischen Messwerten.
    """
    try:
        interval_minutes = 60
        local_tz = timezone('Europe/Berlin')  # Lokale Zeitzone
        end_time = datetime.now(local_tz)
        start_time = end_time - timedelta(minutes=interval_minutes)

        logging.debug(f"Calculating ventilation for room {room_id} between {start_time} and {end_time}")

        measurements = db_service.get_measurements_for_room(room_id, start_time, end_time)

        if not measurements:
            logging.warning(f"No measurements found for room {room_id} in the given period.")
            return None

        logging.debug(f"Found measurements for room {room_id}: {[(m.timestamp, m.humidity) for m in measurements]}")

        # Extrahiere die Luftfeuchtigkeit und Zeitstempel
        humidities = [m.humidity for m in measurements]
        timestamps = [m.timestamp for m in measurements]

        # Maximal- und Minimalwerte bestimmen
        max_humidity = max(humidities)
        max_index = humidities.index(max_humidity)
        max_time = timestamps[max_index]

        min_humidity = min(humidities)
        min_index = humidities.index(min_humidity)
        min_time = timestamps[min_index]

        # Trendanalyse
        if humidities[-1] > humidities[0]:
            trend = "increasing"
            logging.debug(f"Trend for room {room_id} is increasing.")
        else:
            trend = "decreasing"
            logging.debug(f"Trend for room {room_id} is decreasing.")

        # Empfehlung basierend auf dem Trend
        if trend == "increasing":
            return {
                "action": "Bereiten Sie das Lüften vor.",
                "current_trend": "steigend",
                "maximum_humidity": max_humidity,
                "time_of_maximum": max_time.isoformat(),
            }
        else:
            return {
                "action": "Der Raum wird aktuell gelüftet.",
                "current_trend": "fallend",
                "minimum_humidity": min_humidity,
                "time_of_minimum": min_time.isoformat(),
            }
    except Exception as e:
        logging.error(f"Error calculating ventilation recommendation for room {room_id}: {e}")
        return None