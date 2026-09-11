from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from services.voice_service import voice_service

voice_router = APIRouter()

class TTSRequest(BaseModel):
    text: str
    language: Optional[str] = "hi-IN"

@voice_router.post("/speak")
async def text_to_speech(request: TTSRequest):
    """
    Produce high-quality Indic voice from text.
    Returns: { "success": True, "audio": "base64_encoded_audio" }
    """
    if not request.text or len(request.text.strip()) == 0:
         raise HTTPException(status_code=400, detail="Text is required")

    audio_base64 = voice_service.text_to_speech_sarvam(request.text, request.language)
    
    if not audio_base64:
         # Fallback logic here if needed, or error
         return {
             "success": False,
             "message": "Sarvam AI voice failed or not configured",
             "audio": None
         }

    return {
        "success": True,
        "audio": audio_base64,
        "language": request.language
    }

@voice_router.get("/health")
async def voice_health():
    """Check if voice services are available."""
    has_key = voice_service.sarvam_key is not None
    return {
        "status": "online" if has_key else "limited (no API key)",
        "service": "Annadata Saathi Voice Engine"
    }
