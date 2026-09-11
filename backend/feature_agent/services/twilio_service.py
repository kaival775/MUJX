from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from feature_agent.config.settings import (
    TWILIO_ACCOUNT_SID,
    TWILIO_AUTH_TOKEN,
    TWILIO_PHONE_NUMBER,
    PUBLIC_SERVER_URL,
    VAPI_ASSISTANT_ID,
)
from feature_agent.utils.logger import get_logger

logger = get_logger("twilio_service")


def get_twilio_client() -> Client:
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        raise RuntimeError("Twilio credentials are not configured.")
    return Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


def place_outbound_call(farmer_phone: str) -> dict:
    """
    Dial the farmer via Twilio and bridge the answered call to Vapi via SIP.
    Vapi's SIP URI routes the call to the configured assistant.
    """
    client = get_twilio_client()
    vapi_sip_uri = f"sip:{VAPI_ASSISTANT_ID}@sip.vapi.ai"
    twiml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<Response>"
        f"<Dial><Sip>{vapi_sip_uri}</Sip></Dial>"
        "</Response>"
    )
    try:
        call = client.calls.create(
            to=farmer_phone,
            from_=TWILIO_PHONE_NUMBER,
            twiml=twiml,
            status_callback=f"{PUBLIC_SERVER_URL}/api/feature-agent/call-events",
            status_callback_method="POST",
            status_callback_event=["initiated", "ringing", "answered", "completed"],
        )
        logger.info(f"Twilio call placed | SID={call.sid} | to={farmer_phone}")
        return {"call_sid": call.sid, "status": call.status, "to": farmer_phone}
    except TwilioRestException as e:
        logger.error(f"Twilio error: {e}")
        raise RuntimeError(f"Twilio call failed: {e.msg}")
    except Exception as e:
        logger.error(f"Unexpected error placing call: {e}")
        raise RuntimeError(f"Call placement error: {e}")
