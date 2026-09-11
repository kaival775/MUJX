import os
import requests
import base64
from typing import Optional

class VoiceService:
    def __init__(self):
        self.sarvam_key = os.getenv("SARVAM_API_KEY")
        self.tts_url = "https://api.sarvam.ai/text-to-speech"
        
        if not self.sarvam_key:
            print("?? SARVAM_API_KEY missing. Voice service will use browser defaults.")

    def text_to_speech_sarvam(self, text: str, language_code: str = "hi-IN") -> Optional[str]:
        """
        Converts text to speech using Sarvam AI.
        Returns base64 encoded audio string or None if failed.
        """
        if not self.sarvam_key:
            return None

        # Map browser lang codes to Sarvam lang codes
        # Sarvam typically uses: hi-IN, mr-IN, en-IN, etc.
        voice_map = {
            "hi-IN": "hi-IN",
            "mr-IN": "mr-IN",
            "en-IN": "en-IN"
        }
        
        target_lang = voice_map.get(language_code, "hi-IN")

        payload = {
            "inputs": [text],
            "target_language_code": target_lang,
            "speaker": "meera", # Meera is a popular high-quality female voice for Indic
            "pitch": 0,
            "pace": 1.0,
            "loudness": 1.5,
            "enable_preprocessing": True,
            "model": "bulbul:v1"
        }
        
        headers = {
            "Content-Type": "application/json",
            "api-subscription-key": self.sarvam_key
        }

        try:
            response = requests.post(self.tts_url, json=payload, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            if "audios" in data and len(data["audios"]) > 0:
                return data["audios"][0]
            return None
        except Exception as e:
            print(f"?? Sarvam TTS Error: {e}")
            return None

# Singleton instance
voice_service = VoiceService()
