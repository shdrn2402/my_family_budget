import httpx
import logging
import json
from bot.config import Config

logger = logging.getLogger(__name__)

async def classify_intent(text: str) -> str:
    """
    Classifies the user's intent using Gemini API.
    Returns: 'EXPENSE', 'ANALYTICS', or 'UNKNOWN'
    """
    if not Config.GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY is not set.")
        return "UNKNOWN"

    # Returning to 2.5-flash as requested
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={Config.GEMINI_API_KEY}"
    
    prompt = f"""
    Classify the intent of the following user message for a family budget bot.
    Output ONLY one word: 'EXPENSE', 'ANALYTICS', or 'UNKNOWN'.

    - 'EXPENSE': User reports a purchase or income (e.g., "coffee 10", "salary 5000").
    - 'ANALYTICS': User asks a question or requests a report (e.g., "how much spent?", "compare months").
    - 'UNKNOWN': Greeting or unrelated talk.

    Message: "{text}"
    Intent:
    """

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.0,
            "maxOutputTokens": 100
        }
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=10.0)
            if response.status_code != 200:
                # Log the error but don't crash
                logger.error(f"Router API Error {response.status_code}: {response.text}")
                return "UNKNOWN"
            
            data = response.json()
            try:
                candidate = data["candidates"][0]
                if "content" in candidate and "parts" in candidate["content"]:
                    intent = candidate["content"]["parts"][0]["text"].strip().upper()
                    intent = "".join(filter(str.isalnum, intent))
                else:
                    return "UNKNOWN"
            except (KeyError, IndexError):
                return "UNKNOWN"
            
            if "EXPENSE" in intent: return "EXPENSE"
            if "ANALYTICS" in intent: return "ANALYTICS"
            return "UNKNOWN"
    except Exception as e:
        logger.error(f"Router Error: {e}")
        return "UNKNOWN"
