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

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={Config.GEMINI_API_KEY}"
    
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

async def translate_question_to_sql(question: str, user_id: int) -> Dict[str, Any]:
    """
    Translates a natural language question (RU/EN) into a safe PostgreSQL SELECT query.
    """
    if not Config.GEMINI_API_KEY:
        return {"error": "no_api_key"}

    # We don't pass current_date from Python anymore to keep it DB-native as requested.
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={Config.GEMINI_API_KEY}"
    
    schema = {
        "type": "OBJECT",
        "properties": {
            "sql": {"type": "STRING", "description": "PostgreSQL query. Use CURRENT_DATE for relative dates."},
            "explanation": {"type": "STRING", "description": "Short explanation of what the query does."},
            "is_safe": {"type": "BOOLEAN", "description": "True if it's only a SELECT query and belongs to the user_id."}
        },
        "required": ["sql", "explanation", "is_safe"]
    }

    prompt = f"""
    You are a PostgreSQL expert for a family budget app. Translate user questions (RU/EN) into SQL.
    Database Schema:
    - transactions (id, user_id, account_id, category_id, amount, description, comment, date)
    - categories (id, name, parent_id) -- 'name' is JSONB: {{"en": "Food", "ru": "Еда"}}
    - accounts (id, name, type, user_id)
    
    RULES:
    1. ALWAYS filter by user_id = {user_id}.
    2. ONLY use SELECT statements.
    3. Use ILIKE for text search.
    4. To filter by category name:
       - For Russian: categories.name->>'ru' ILIKE '%название%'
       - For English: categories.name->>'en' ILIKE '%name%'
    5. 'amount' is negative for expenses, positive for income. To get total spending, use ABS(SUM(amount)) where amount < 0.
    6. GROUPING BY CATEGORY:
       - By default, group results by PARENT category to keep reports clean.
       - Use `COALESCE(categories.parent_id, categories.id)` to find the top-level category ID.
       - Join the result back with `categories` table to get the name of the parent category.
       - Example: GROUP BY COALESCE(c.parent_id, c.id)
    7. Use CURRENT_DATE for relative date queries (e.g., 'this month', 'last week', 'since start of year').
    8. Return JSON with 'sql', 'explanation', 'is_safe'.
    """

    payload = {
        "contents": [{
            "parts": [{"text": f"{prompt}\n\nQuestion: '{question}'"}]
        }],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": schema
        }
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=20.0)
            response.raise_for_status()
            data = response.json()
            return json.loads(data["candidates"][0]["content"]["parts"][0]["text"])
    except Exception as e:
        logger.error(f"SQL Generation Error: {e}")
        return {"error": str(e)}

async def generate_answer_from_data(question: str, data_rows: List[Dict], error: str = None) -> str:
    """
    Generates a natural language answer (RU/EN) based on the SQL query results.
    """
    if error:
        return f"Error: {error}"
    
    if not data_rows:
        return "Ничего не нашел по этому запросу / I found no data for this request."

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={Config.GEMINI_API_KEY}"
    
    prompt = f"""
    Answer the user's question based on the database results.
    Use the same language as the question (Russian or English).
    Be concise, friendly, and format numbers/dates clearly.
    
    IMPORTANT: The currency is Israeli Shekels. 
    ALWAYS include the currency symbol (₪) for EVERY monetary value in your response. 
    DO NOT use $. Example: '150.50 ₪'.
    
    Question: '{question}'
    Data: {json.dumps(data_rows, default=str)}
    """

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=15.0)
            response.raise_for_status()
            result = response.json()
            return result["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        logger.error(f"Answer Generation Error: {e}")
        return f"Результаты / Results: {data_rows}"


