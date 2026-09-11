import requests
from feature_agent.config.settings import VAPI_API_KEY, VAPI_ASSISTANT_ID, VAPI_BASE_URL
from feature_agent.utils.logger import get_logger

logger = get_logger("vapi_service")


def get_headers() -> dict:
    return {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json",
    }


def verify_assistant() -> dict:
    """Fetch assistant config from Vapi to confirm it exists and is active."""
    url = f"{VAPI_BASE_URL}/assistant/{VAPI_ASSISTANT_ID}"
    try:
        resp = requests.get(url, headers=get_headers(), timeout=10)
        resp.raise_for_status()
        data = resp.json()
        logger.info(f"Vapi assistant verified: {data.get('name', VAPI_ASSISTANT_ID)}")
        return {"status": "ok", "assistant": data}
    except requests.HTTPError as e:
        logger.error(f"Vapi assistant verification failed: {e} | body: {e.response.text}")
        raise RuntimeError(f"Vapi assistant not found or invalid: {e.response.status_code}")
    except Exception as e:
        logger.error(f"Vapi connection error: {e}")
        raise RuntimeError(f"Cannot reach Vapi: {e}")


def initiate_vapi_web_call(farmer_phone: str) -> dict:
    """
    Create an outbound phone call via Vapi directly (Vapi-managed telephony).
    Vapi will use its own SIP/PSTN to dial the farmer.
    Returns the Vapi call object.
    """
    url = f"{VAPI_BASE_URL}/call/phone"
    payload = {
        "assistantId": VAPI_ASSISTANT_ID,
        "customer": {
            "number": farmer_phone,
        },
    }
    try:
        resp = requests.post(url, json=payload, headers=get_headers(), timeout=15)
        resp.raise_for_status()
        data = resp.json()
        logger.info(f"Vapi call initiated | id={data.get('id')} | to={farmer_phone}")
        return data
    except requests.HTTPError as e:
        logger.error(f"Vapi call failed: {e} | body: {e.response.text}")
        raise RuntimeError(f"Vapi call initiation failed: {e.response.text}")
    except Exception as e:
        logger.error(f"Vapi request error: {e}")
        raise RuntimeError(f"Cannot reach Vapi: {e}")


def get_call_status(call_id: str) -> dict:
    """Fetch live status of a Vapi call."""
    url = f"{VAPI_BASE_URL}/call/{call_id}"
    try:
        resp = requests.get(url, headers=get_headers(), timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"Failed to fetch call status for {call_id}: {e}")
        raise RuntimeError(f"Cannot fetch call status: {e}")
