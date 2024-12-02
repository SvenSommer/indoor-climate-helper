import os
import logging
import threading
from flask import Flask, request, jsonify
from services.database_service import DatabaseService
from services.worker_services import WorkerThreads
from dotenv import load_dotenv
from pytz import timezone
from datetime import datetime
from modules.database_setup import Device, SessionLocal, Room, Measurement, setup_database
from flask_cors import CORS
from sqlalchemy import func

# Load environment variables
load_dotenv()
load_dotenv()
LOG_FILE = os.getenv("LOG_FILE", "app.log")
local_tz = timezone("Europe/Berlin")
# Logging setup
logging.basicConfig(filename=LOG_FILE, level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

# Flask app setup
app = Flask(__name__)

CORS(app)

# Helper function to get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize and start the threads
if threading.active_count() == 1: # Only the main thread is running
    worker_threads = WorkerThreads()
    worker_threads.start_threads()


# POST endpoint: Add a new room
@app.route("/rooms", methods=["POST"])
def add_room():
    db_service = DatabaseService()
    try:
        data = request.json
        name = data.get("name")
        if not name:
            return jsonify({"error": "Room name is required"}), 400

        new_room = db_service.add_room(name)
        logging.info(f"Room '{new_room.name}' added successfully.")
        return jsonify({"message": "Room added successfully", "room_id": new_room.id}), 201
    except Exception as e:
        logging.error(f"Error adding room: {e}")
        return jsonify({"error": "Failed to add room"}), 500
    finally:
        db_service.close()

# GET endpoint: Retrieve all rooms
@app.route("/rooms", methods=["GET"])
def get_rooms():
    db_service = DatabaseService()
    try:
        rooms = db_service.get_all_rooms()
        room_list = []
        for room in rooms:
            last_measurement = db_service.get_last_measurement_for_room(room.id)
            devices = db_service.get_room_devices(room.id)

            room_list.append({
                "id": room.id,
                "name": room.name,
                "last_measurement": {
                    "timestamp": last_measurement.timestamp.astimezone(local_tz).isoformat() if last_measurement else None,
                    "temperature": last_measurement.temperature if last_measurement else None,
                    "humidity": last_measurement.humidity if last_measurement else None,
                },
                "devices": [
                    {
                        "id": device.id,
                        "name": device.name,
                        "device_type": device.device_type,
                        "ip": device.ip
                    }
                    for device in devices
                ],
            })
        return jsonify({"rooms": room_list}), 200
    except Exception as e:
        logging.error(f"Error retrieving rooms: {e}")
        return jsonify({"error": "Failed to retrieve rooms"}), 500
    finally:
        db_service.close()

# GET endpoint: Retrieve a specific room by ID
@app.route("/rooms/<int:room_id>", methods=["GET"])
def get_room(room_id):
    db_service = DatabaseService()
    try:
        room = db_service.get_room_by_id(room_id)
        if not room:
            return jsonify({"error": "Room not found"}), 404
        last_measurement = db_service.get_last_measurement_for_room(room_id)
        devices = db_service.get_room_devices(room_id)
        room_data = {
            "id": room.id,
            "name": room.name,
            "last_measurement": {
                "timestamp": last_measurement.timestamp.isoformat() if last_measurement else None,
                "temperature": last_measurement.temperature if last_measurement else None,
                "humidity": last_measurement.humidity if last_measurement else None,
            },
            "devices": [
                {
                    "id": device.id,
                    "name": device.name,
                    "device_type": device.device_type,
                    "ip": device.ip
                }
                for device in devices
            ],
        }
        return jsonify(room_data), 200
    except Exception as e:
        logging.error(f"Error retrieving room with ID {room_id}: {e}")
        return jsonify({"error": "Failed to retrieve room"}), 500
    finally:
        db_service.close()

# PUT endpoint: Update a room by ID
@app.route("/rooms/<int:room_id>", methods=["PUT"])
def update_room(room_id):
    db_service = DatabaseService()
    try:
        data = request.json
        room = db_service.get_room_by_id(room_id)
        if not room:
            return jsonify({"error": "Room not found"}), 404

        # Update fields if provided
        if "name" in data:
            room.name = data["name"]

        # Commit changes using the database session
        db_service.db.commit()
        logging.info(f"Room with ID {room_id} updated successfully.")
        return jsonify({"message": "Room updated successfully"}), 200
    except Exception as e:
        logging.error(f"Error updating room with ID {room_id}: {e}")
        return jsonify({"error": "Failed to update room"}), 500
    finally:
        db_service.close()

# DELETE endpoint: Delete a specific room by ID
@app.route("/rooms/<int:room_id>", methods=["DELETE"])
def delete_room(room_id):
    db_service = DatabaseService()
    try:
        success = db_service.delete_room(room_id)
        if success:
            logging.info(f"Room with ID '{room_id}' deleted successfully.")
            return jsonify({"message": "Room deleted successfully"}), 200
        return jsonify({"error": "Room not found"}), 404
    except Exception as e:
        logging.error(f"Error deleting room: {e}")
        return jsonify({"error": "Failed to delete room"}), 500
    finally:
        db_service.close()
    

    
# POST endpoint: Add a new device
@app.route("/devices", methods=["POST"])
def add_device():
    """Add a new device."""
    db = next(get_db())
    data = request.json
    try:
        new_device = Device(
            name=data["name"],
            room_id=data["room_id"],
            device_type=data["device_type"],
            ip=data.get("ip"),
            username=data.get("username"),
            password=data.get("password")
        )
        db.add(new_device)
        db.commit()
        logging.info(f"Device '{new_device.name}' added successfully.")
        return jsonify({"message": "Device added successfully", "device": new_device.id}), 201
    except Exception as e:
        logging.error(f"Error adding device: {e}")
        return jsonify({"error": "Failed to add device"}), 500
    finally:
        db.close()

# GET endpoint: Retrieve all devices
@app.route("/devices", methods=["GET"])
def get_devices():
    """Retrieve all devices."""
    db = next(get_db())
    try:
        devices = db.query(Device).all()
        device_list = [
            {
                "id": device.id,
                "name": device.name,
                "room_id": device.room_id,
                "device_type": device.device_type,
                "ip": device.ip
            }
            for device in devices
        ]
        return jsonify({"devices": device_list}), 200
    except Exception as e:
        logging.error(f"Error retrieving devices: {e}")
        return jsonify({"error": "Failed to retrieve devices"}), 500
    finally:
        db.close()

# GET endpoint: Retrieve a specific device by ID
@app.route("/devices/<int:device_id>", methods=["GET"])
def get_device(device_id):
    """Retrieve a specific device by ID."""
    db = next(get_db())
    try:
        device = db.query(Device).filter_by(id=device_id).first()
        if not device:
            return jsonify({"error": "Device not found"}), 404
        return jsonify(
            {
                "id": device.id,
                "name": device.name,
                "room_id": device.room_id,
                "device_type": device.device_type,
                "ip": device.ip,
                "username": device.username,
                "password": device.password,
            }
        ), 200
    except Exception as e:
        logging.error(f"Error retrieving device with ID {device_id}: {e}")
        return jsonify({"error": "Failed to retrieve device"}), 500
    finally:
        db.close()

# PUT endpoint: Update a device by ID
@app.route("/devices/<int:device_id>", methods=["PUT"])
def update_device(device_id):
    """Update a device."""
    db = next(get_db())
    data = request.json
    try:
        device = db.query(Device).filter_by(id=device_id).first()
        if not device:
            return jsonify({"error": "Device not found"}), 404

        # Update fields if provided
        if "name" in data:
            device.name = data["name"]
        if "room_id" in data:
            device.room_id = data["room_id"]
        if "device_type" in data:
            device.device_type = data["device_type"]
        if "ip" in data:
            device.ip = data["ip"]
        if "username" in data:
            device.username = data["username"]
        if "password" in data:
            device.password = data["password"]

        db.commit()
        logging.info(f"Device with ID {device_id} updated successfully.")
        return jsonify({"message": "Device updated successfully"}), 200
    except Exception as e:
        logging.error(f"Error updating device with ID {device_id}: {e}")
        return jsonify({"error": "Failed to update device"}), 500
    finally:
        db.close()

# DELETE endpoint: Delete a device by ID
@app.route("/devices/<int:device_id>", methods=["DELETE"])
def delete_device(device_id):
    """Delete a device."""
    db = next(get_db())
    try:
        device = db.query(Device).filter_by(id=device_id).first()
        if not device:
            return jsonify({"error": "Device not found"}), 404

        db.delete(device)
        db.commit()
        logging.info(f"Device with ID {device_id} deleted successfully.")
        return jsonify({"message": "Device deleted successfully"}), 200
    except Exception as e:
        logging.error(f"Error deleting device with ID {device_id}: {e}")
        return jsonify({"error": "Failed to delete device"}), 500
    finally:
        db.close()

# POST endpoint: Add a new measurement
@app.route("/measurements", methods=["POST"])
def add_measurement():
    db = next(get_db())
    data = request.json
    room_name = data.get("room_name")
    temperature = data.get("temperature")
    humidity = data.get("humidity")

    if not room_name:
        return jsonify({"error": "Room name is required"}), 400

    try:
        room = db.query(Room).filter_by(name=room_name).first()
        if not room:
            return jsonify({"error": "Room not found"}), 404

        new_measurement = Measurement(
            room_id=room.id,
            timestamp=datetime.utcnow(),
            temperature=temperature,
            humidity=humidity,
        )
        db.add(new_measurement)
        db.commit()
        logging.info(f"Measurement added for room '{room_name}'.")
        return jsonify({"message": "Measurement added successfully"}), 201
    except Exception as e:
        logging.error(f"Error adding measurement: {e}")
        return jsonify({"error": "Failed to add measurement"}), 500

# GET endpoint: Get all measurements for a room_id
@app.route("/measurements/<int:room_id>", methods=["GET"])
def get_measurements(room_id):
    db = next(get_db())
    try:
        # Query-Parameter abrufen
        sorting = request.args.get("sorting", "timestamp")
        order = request.args.get("order", "asc")
        count = request.args.get("count", type=int, default=None)
        offset = request.args.get("offset", type=int, default=0)
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")

        # Basis-Query
        query = db.query(Measurement).filter_by(room_id=room_id)

        # Datumsfilter anwenden
        if start_date:
            query = query.filter(func.date(Measurement.timestamp) >= start_date)
        if end_date:
            query = query.filter(func.date(Measurement.timestamp) <= end_date)

        # Gesamte Anzahl der Messungen berechnen
        total_count = query.count()

        # Erster und letzter Zeitstempel berechnen
        first_date = query.order_by(Measurement.timestamp.asc()).first()
        last_date = query.order_by(Measurement.timestamp.desc()).first()
        first_date_str = first_date.timestamp.isoformat() if first_date else None
        last_date_str = last_date.timestamp.isoformat() if last_date else None

        # Sortieren und Pagination anwenden
        if order.lower() == "desc":
            query = query.order_by(getattr(Measurement, sorting).desc())
        else:
            query = query.order_by(getattr(Measurement, sorting))

        if offset:
            query = query.offset(offset)
        if count:
            query = query.limit(count)

        # Ergebnisse abrufen
        measurements = query.all()
        measurement_list = [
            {
                "id": m.id,
                "timestamp": m.timestamp.astimezone(local_tz).isoformat(),
                "temperature": m.temperature,
                "humidity": m.humidity,
            }
            for m in measurements
        ]

        return jsonify({
            "measurements": measurement_list,
            "totalCount": total_count,
            "firstDate": first_date_str,  # Erster Zeitstempel
            "lastDate": last_date_str    # Letzter Zeitstempel
        }), 200
    except Exception as e:
        logging.error(f"Error retrieving measurements: {e}")
        return jsonify({"error": "Failed to retrieve measurements"}), 500
    
# DELETE endpoint: Delete a specific measurement by ID
@app.route("/measurement/<int:measurement_id>", methods=["DELETE"])
def delete_measurement(measurement_id):
    db = next(get_db())
    try:
        measurement = db.query(Measurement).filter_by(id=measurement_id).first()
        if not measurement:
            return jsonify({"error": "Measurement not found"}), 404

        db.delete(measurement)
        db.commit()
        logging.info(f"Measurement with ID '{measurement_id}' deleted successfully.")
        return jsonify({"message": "Measurement deleted successfully"}), 200
    except Exception as e:
        logging.error(f"Error deleting measurement: {e}")
        return jsonify({"error": "Failed to delete measurement"}), 500

# DELETE endpoint: Delete all measurements for a room
@app.route("/measurements/<int:room_id>", methods=["DELETE"])
def delete_measurements(room_id):
    db = next(get_db())
    try:
        measurements = db.query(Measurement).filter_by(room_id=room_id).all()
        if not measurements:
            return jsonify({"error": "No measurements found for the specified room"}), 404

        for measurement in measurements:
            db.delete(measurement)
        db.commit()
        logging.info(f"All measurements for room ID '{room_id}' deleted successfully.")
        return jsonify({"message": "All measurements deleted successfully"}), 200
    except Exception as e:
        logging.error(f"Error deleting measurements: {e}")
        return jsonify({"error": "Failed to delete measurements"}), 500
    
# POST endpoint: Abrufen und Speichern von Wetterdaten
@app.route("/weather", methods=["POST"])
def fetch_and_save_weather_data():
    try:
        db_service = DatabaseService()
        worker_threads.save_weather_data(db_service)
        logging.info("Weather data fetched and saved successfully via API endpoint.")
        return jsonify({"message": "Weather data fetched and saved successfully"}), 201
    except Exception as e:
        logging.error(f"Error fetching and saving weather data: {e}")
        return jsonify({"error": "Failed to fetch and save weather data"}), 500
    
# POST endpoint: Abrufen und Speichern von Shelly-Daten
@app.route("/shelly", methods=["POST"])
def fetch_and_save_shelly_data():
    try:
        db_service = DatabaseService()
        worker_threads.save_shelly_data(db_service)
        logging.info("Shelly data fetched and saved successfully via API endpoint.")
        return jsonify({"message": "Shelly data fetched and saved successfully"}), 201
    except Exception as e:
        logging.error(f"Error fetching and saving Shelly data: {e}")
        return jsonify({"error": "Failed to fetch and save Shelly data"}), 500

# Run the Flask app
if __name__ == "__main__":
    app.run(debug=False, use_reloader=False)