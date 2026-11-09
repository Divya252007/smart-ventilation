
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import datetime, timezone

from database import (
    initialize_database,
    save_reading,
    get_latest,
    get_history
)

app = FastAPI(title="Smart Ventilation API")

initialize_database()


class SensorData(BaseModel):
    mq135: int = Field(ge=0, le=4095)
    temperature: Optional[float] = None
    humidity: Optional[float] = None

    pir_motion: bool
    mode: Literal["INDOOR", "OUTDOOR"]

    fan_on: bool
    relay_on: bool
    red_led: bool
    green_led: bool
    buzzer_on: bool

    air_status: str = "Unknown"
    temperature_status: str = "Unknown"
    alert_message: str = ""


@app.get("/")
def home():
    return {
        "application": "Smart Ventilation System",
        "status": "API running"
    }


@app.get("/api/health")
def health():
    return {
        "status": "online",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.post("/api/telemetry")
def receive_sensor_data(data: SensorData):
    payload = data.model_dump()

    # Basic sanity checks for sensor values
    if payload["temperature"] is not None:
        if not -20 <= payload["temperature"] <= 100:
            raise HTTPException(400, "Invalid temperature")

    if payload["humidity"] is not None:
        if not 0 <= payload["humidity"] <= 100:
            raise HTTPException(400, "Invalid humidity")

    save_reading(payload)

    return {
        "success": True,
        "message": "Sensor data received",
        "received_at": datetime.now(timezone.utc).isoformat()
    }


@app.get("/api/latest")
def latest_reading():
    reading = get_latest()

    if reading is None:
        return {"available": False, "data": None}

    return {
        "available": True,
        "data": reading
    }


@app.get("/api/history")
def sensor_history(limit: int = 500):
    limit = max(1, min(limit, 2000))

    return {
        "count": len(get_history(limit)),
        "data": get_history(limit)
    }
