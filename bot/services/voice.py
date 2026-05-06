import httpx
import base64
import logging
from bot.config import Config

logger = logging.getLogger(__name__)

async def transcribe_voice(audio_bytes: bytes) -> str:
    """
    Convert audio bytes (OGG format) to text using Gemini API.
    """
    if not Config.GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY is not set.")
        return ""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={Config.GEMINI_API_KEY}"
    
    # Encode audio bytes to base64 string
    audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
    
    payload = {
        "contents": [{
            "parts": [
                {"text": "Пожалуйста, расшифруй это голосовое сообщение в текст. Напиши только сам текст, без лишних комментариев и кавычек."},
                {
                    "inlineData": {
                        "mimeType": "audio/ogg",
                        "data": audio_b64
                    }
                }
            ]
        }]
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=20.0)
            if response.status_code != 200:
                logger.error(f"Gemini Voice API Error: {response.status_code} - {response.text}")
            response.raise_for_status()
            
            data = response.json()
            content_text = data["candidates"][0]["content"]["parts"][0]["text"]
            return content_text.strip()
            
    except httpx.HTTPStatusError as e:
        logger.error(f"Gemini Voice API Error: {e.response.status_code}")
        return f"__ERROR__:API {e.response.status_code}"
    except Exception as e:
        logger.error(f"Error transcribing voice with Gemini API: {e}")
        return "__ERROR__:UNKNOWN"
