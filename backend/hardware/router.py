"""
Hardware Router — Real-time sensor data endpoints.

- Soil sensors: stored in Supabase (autonomous_sensors table)
- Fire/Gas sensors: polled every 5s from ESP32 at 10.110.7.93:8000
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import httpx
import asyncio
from core.supabase_client import supabase

router = APIRouter(prefix="/api/hardware", tags=["hardware"])

# ─── Fire/Gas Sensor Configuration ───
FIRE_GAS_SENSOR_URL = "http://10.110.7.93:8000/api/hardware/fire-gas/latest"
POLL_INTERVAL_SECONDS = 5

# In-memory cache for latest fire/gas readings (updated by background task)
_fire_gas_cache = {
    "mq2_value": 0,
    "fire_status": "Unknown",
    "last_updated": None,
    "mq2_d0": 0,
    "source": "not_yet_polled",
    "online": False
}
_poll_task = None


async def _poll_fire_gas_sensor():
    """Background task: fetch fire/gas sensor data every 5 seconds."""
    global _fire_gas_cache
    print(f"[HARDWARE] Starting fire/gas sensor polling every {POLL_INTERVAL_SECONDS}s from {FIRE_GAS_SENSOR_URL}")
    
    while True:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(FIRE_GAS_SENSOR_URL)
                if response.status_code == 200:
                    hw_response = response.json()
                    # Hardware returns: {"status":"success","data":{"mq2_value":...,"fire_status":...}}
                    sensor_data = hw_response.get("data", hw_response)
                    
                    _fire_gas_cache = {
                        "mq2_value": sensor_data.get("mq2_value", 0),
                        "fire_status": sensor_data.get("fire_status", "Unknown"),
                        "last_updated": sensor_data.get("last_updated", datetime.now().isoformat()),
                        "mq2_d0": sensor_data.get("mq2_d0", 0),
                        "source": "hardware",
                        "online": True
                    }
                else:
                    _fire_gas_cache["online"] = False
                    _fire_gas_cache["source"] = f"error_http_{response.status_code}"
        except Exception as e:
            _fire_gas_cache["online"] = False
            _fire_gas_cache["source"] = "offline"
            print(f"[HARDWARE] Fire/Gas sensor unreachable: {e}")
        
        await asyncio.sleep(POLL_INTERVAL_SECONDS)


def start_fire_gas_polling():
    """Start the background polling task (called from FastAPI startup event)."""
    global _poll_task
    if _poll_task is None:
        _poll_task = asyncio.create_task(_poll_fire_gas_sensor())
        print("[HARDWARE] Fire/Gas polling task started")


# ─── Fire/Gas Endpoints ───

@router.get("/fire-gas/latest")
async def get_fire_gas_latest():
    """
    Get latest fire and gas sensor readings.
    Returns cached data from the background polling task (updated every 5s).
    """
    # Start polling if not already running
    global _poll_task
    if _poll_task is None:
        start_fire_gas_polling()
    
    if not _fire_gas_cache["online"] and _fire_gas_cache["source"] == "not_yet_polled":
        # First request before polling has completed — do a direct fetch
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(FIRE_GAS_SENSOR_URL)
                if response.status_code == 200:
                    hw_response = response.json()
                    sensor_data = hw_response.get("data", hw_response)
                    return {
                        "status": "success",
                        "data": {
                            "mq2_value": sensor_data.get("mq2_value", 0),
                            "fire_status": sensor_data.get("fire_status", "Unknown"),
                            "last_updated": sensor_data.get("last_updated", datetime.now().isoformat()),
                            "mq2_d0": sensor_data.get("mq2_d0", 0)
                        }
                    }
        except Exception:
            pass
    
    if _fire_gas_cache["online"]:
        return {
            "status": "success",
            "data": {
                "mq2_value": _fire_gas_cache["mq2_value"],
                "fire_status": _fire_gas_cache["fire_status"],
                "last_updated": _fire_gas_cache["last_updated"],
                "mq2_d0": _fire_gas_cache["mq2_d0"]
            }
        }
    else:
        return {
            "status": "success",
            "data": {
                "mq2_value": _fire_gas_cache.get("mq2_value", 0),
                "fire_status": _fire_gas_cache.get("fire_status", "Unknown"),
                "last_updated": _fire_gas_cache.get("last_updated", datetime.now().isoformat()),
                "mq2_d0": _fire_gas_cache.get("mq2_d0", 0)
            }
        }


# ─── Soil Sensor Endpoints ───

class SensorData(BaseModel):
    soil_moisture: float
    nitrogen: int
    phosphorus: int
    potassium: int
    ph: float
    soil_temperature: float
    conductivity: float
    user_id: Optional[str] = "HARDWARE_DEFAULT"

@router.post("/sensor-data")
async def receive_sensor_data(data: SensorData):
    """
    Receives real-time sensor data from Arduino/ESP32 hardware.
    """
    try:
        sensor_payload = {
            "user_id": data.user_id,
            "data": {
                "ph": data.ph,
                "nitrogen": data.nitrogen,
                "phosphorus": data.phosphorus,
                "potassium": data.potassium,
                "conductivity": data.conductivity,
                "soil_moisture": data.soil_moisture,
                "soil_temperature": data.soil_temperature,
                "last_updated": datetime.utcnow().isoformat()
            }
        }
        
        # Try to update existing record, if not exists then insert
        existing = supabase.table("autonomous_sensors").select("id").eq("user_id", data.user_id).execute()
        
        if existing.data:
            supabase.table("autonomous_sensors").update({"data": sensor_payload["data"]}).eq("user_id", data.user_id).execute()
        else:
            supabase.table("autonomous_sensors").insert(sensor_payload).execute()
        
        print(f" Hardware data received: Moisture={data.soil_moisture}%, N={data.nitrogen}")
        
        return {
            "status": "success",
            "message": "Sensor data stored successfully",
            "data": data.dict()
        }
        
    except Exception as e:
        print(f" Hardware data error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/latest")
async def get_latest_sensor_data(user_id: str = "HARDWARE_DEFAULT"):
    """Get latest sensor reading."""
    try:
        response = supabase.table("autonomous_sensors").select("*").eq("user_id", user_id).execute()
        
        if response.data and len(response.data) > 0:
            return {"status": "success", "data": response.data[0]["data"]}
        else:
            return {"status": "no_data", "message": "No sensor data available yet"}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))