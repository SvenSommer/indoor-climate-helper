import os
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///rooms.db")
LOG_FILE = os.getenv("LOG_FILE", "setup.log")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
DEHUMIDIFIER_EMAIL = os.getenv("DEHUMIDIFIER_EMAIL")
DEHUMIDIFIER_PASSWORD = os.getenv("DEHUMIDIFIER_PASSWORD")


# Logging setup
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.DEBUG if DEBUG else logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# SQLAlchemy setup
Base = declarative_base()
engine = create_engine(DATABASE_URL, echo=DEBUG)
SessionLocal = sessionmaker(bind=engine)

# Models
class Room(Base):
    __tablename__ = "rooms"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)  # VARCHAR(255)

class Measurement(Base):
    __tablename__ = "measurements"
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    temperature = Column(Float, nullable=True)
    humidity = Column(Float, nullable=True)

class Device(Base):
    __tablename__ = "devices"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)  # VARCHAR(255)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    device_type = Column(String(255), nullable=False)  # VARCHAR(255)
    ip = Column(String(255), nullable=True)  # VARCHAR(255)
    username = Column(String(255), nullable=True)  # VARCHAR(255)
    password = Column(String(255), nullable=True)  # VARCHAR(255)

# Function to initialize the database
def setup_database():
    session = None
    try:
        Base.metadata.create_all(engine)
        logging.info("Database tables created successfully.")
        session = SessionLocal()
        add_external_room(session)
    except Exception as e:
        logging.error(f"Failed to setup the database: {e}")
    finally:
        if session:  # Prüfen, ob session definiert ist
            session.close()

# Helper function to add the external room
def add_external_room(session):
    try:
        external_room = session.query(Room).filter_by(name="external").first()
        if not external_room:
            session.add(Room(name="external"))
            session.commit()
            logging.info("External room added to the database.")
    except Exception as e:
        logging.error(f"Error adding the external room: {e}")
        session.rollback()

if __name__ == "__main__":
    setup_database()