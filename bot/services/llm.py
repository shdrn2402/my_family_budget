import json
import logging
from typing import List, Dict, Any
import httpx
from bot.config import Config

logger = logging.getLogger(__name__)

async def parse_natural_language(text: str) -> List[Dict[str, Any]]:
    """
    Parses natural language text into structured expense items using Gemini API.
    Uses httpx to avoid extra pip dependencies, leveraging Gemini's Structured Outputs.
    """
    if not Config.GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY is not set.")
        return []

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={Config.GEMINI_API_KEY}"
    
    # We define the JSON schema for strict structured output
    schema = {
        "type": "OBJECT",
        "properties": {
            "items": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "item_name": {
                            "type": "STRING", 
                            "description": "The name of the item or service purchased, in lowercase."
                        },
                        "amount": {
                            "type": "NUMBER", 
                            "description": "The cost or amount of the purchase."
                        },
                        "account_alias": {
                            "type": "STRING", 
                            "description": "The account used to pay (e.g., 'наличные', 'кредитка', 'дебет', 'bank', 'cash', 'card', 'debit'). Must be a single word. Leave empty if not mentioned."
                        }
                    },
                    "required": ["item_name", "amount", "account_alias"]
                }
            }
        },
        "required": ["items"]
    }
    
    payload = {
        "contents": [{
            "parts": [{"text": f"Extract all expense transactions from the text. Return JSON matching the schema. Translate vague account terms to 'наличные', 'кредитка', 'дебет', 'bank', 'cash', 'card', 'debit' or leave empty.\n\nText: '{text}'"}]
        }],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": schema
        }
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=15.0)
            if response.status_code != 200:
                logger.error(f"Gemini API Error: {response.status_code} - {response.text}")
            response.raise_for_status()
            
            data = response.json()
            content_text = data["candidates"][0]["content"]["parts"][0]["text"]
            
            result_json = json.loads(content_text)
            return result_json.get("items", [])
            
    except httpx.HTTPStatusError as e:
        logger.error(f"Gemini API Error: {e.response.status_code}")
        return [{"error": "llm_failed", "details": f"API Error: {e.response.status_code}"}]
    except Exception as e:
        logger.error(f"Error parsing with Gemini API: {e}")
        return [{"error": "llm_failed", "details": str(e)}]
