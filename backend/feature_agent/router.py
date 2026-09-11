import re
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, field_validator
from feature_agent.services import vapi_service, twilio_service
from feature_agent.config.settings import validate_config
from feature_agent.utils.logger import get_logger

logger = get_logger("feature_agent.router")
router = APIRouter(prefix="/api/feature-agent", tags=["Feature Agent: Annadata Saathi"])

PHONE_RE = re.compile(r"^\+[1-9]\d{7,14}$")


class StartCallRequest(BaseModel):
    farmer_phone: str

    @field_validator("farmer_phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        v = v.strip()
        if not PHONE_RE.match(v):
            raise ValueError("Invalid phone. Use E.164 format e.g. +919876543210")
        return v


@router.get("/health")
def health_check():
    missing = validate_config()
    if missing:
        return {"status": "degraded", "missing": missing}
    return {"status": "ok", "service": "Annadata Saathi Voice Agent"}


@router.post("/start-call")
def start_call(body: StartCallRequest):
    """Dial the farmer and bridge the call to the Vapi AI assistant."""
    logger.info(f"[CALL REQUEST] to={body.farmer_phone}")
    missing = validate_config()
    if missing:
        raise HTTPException(503, f"Service not configured. Missing: {', '.join(missing)}")
    try:
        result = twilio_service.place_outbound_call(body.farmer_phone)
        logger.info(f"[CALL STARTED] SID={result['call_sid']}")
        return {
            "success": True,
            "message": "Call initiated. Annadata Saathi will connect shortly.",
            "call_sid": result["call_sid"],
            "status": result["status"],
            "to": result["to"],
        }
    except RuntimeError as e:
        logger.error(f"[CALL FAILED] {e}")
        raise HTTPException(502, str(e))


@router.post("/call-events")
async def call_events(request: Request):
    """Twilio status callback — logs all call lifecycle events."""
    form = await request.form()
    event = {
        "call_sid": form.get("CallSid"),
        "call_status": form.get("CallStatus"),
        "from_number": form.get("From"),
        "to_number": form.get("To"),
        "duration": form.get("CallDuration"),
    }
    status = event.get("call_status", "unknown")
    if status in ("initiated", "ringing"):
        logger.info(f"[CALL EVENT] {status.upper()} | SID={event['call_sid']}")
    elif status == "in-progress":
        logger.info(f"[CALL EVENT] ANSWERED | SID={event['call_sid']}")
    elif status == "completed":
        logger.info(f"[CALL EVENT] COMPLETED | SID={event['call_sid']} | duration={event['duration']}s")
    elif status in ("failed", "busy", "no-answer", "canceled"):
        logger.warning(f"[CALL EVENT] {status.upper()} | SID={event['call_sid']}")
    else:
        logger.info(f"[CALL EVENT] raw={event}")
    return {"received": True}


@router.get("/call-status/{call_id}")
def call_status(call_id: str):
    """Fetch live status of a Vapi call by ID."""
    try:
        data = vapi_service.get_call_status(call_id)
        return {"success": True, "call": data}
    except RuntimeError as e:
        raise HTTPException(502, str(e))


@router.get("/verify-assistant")
def verify_assistant():
    """Confirm the configured Vapi assistant is reachable and valid."""
    try:
        result = vapi_service.verify_assistant()
        return result
    except RuntimeError as e:
        raise HTTPException(502, str(e))
