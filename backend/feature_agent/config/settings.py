import os
from dotenv import load_dotenv

load_dotenv()

# Vapi configuration
VAPI_API_KEY: str = os.getenv("VAPI_API_KEY", "")
VAPI_ASSISTANT_ID: str = os.getenv("VAPI_ASSISTANT_ID", "")
VAPI_BASE_URL: str = "https://api.vapi.ai"

# Twilio configuration
TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE_NUMBER: str = os.getenv("TWILIO_PHONE_NUMBER", "")

# Server configuration
PUBLIC_SERVER_URL: str = os.getenv("PUBLIC_SERVER_URL", "")

def validate_config() -> list[str]:
    """Return list of missing required env vars."""
    required = {
        "VAPI_API_KEY": VAPI_API_KEY,
        "VAPI_ASSISTANT_ID": VAPI_ASSISTANT_ID,
        "TWILIO_ACCOUNT_SID": TWILIO_ACCOUNT_SID,
        "TWILIO_AUTH_TOKEN": TWILIO_AUTH_TOKEN,
        "TWILIO_PHONE_NUMBER": TWILIO_PHONE_NUMBER,
        "PUBLIC_SERVER_URL": PUBLIC_SERVER_URL,
    }
    return [k for k, v in required.items() if not v]
