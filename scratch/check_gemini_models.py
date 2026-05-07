import httpx
import asyncio
from bot.config import Config

async def check_model(model_id):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent?key={Config.GEMINI_API_KEY}"
    payload = {"contents": [{"parts": [{"text": "Hi"}]}]}
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)
            print(f"Model {model_id}: {response.status_code}")
            if response.status_code != 200:
                print(f"Error: {response.text}")
    except Exception as e:
        print(f"Model {model_id}: Error {e}")

async def main():
    models = ["gemini-1.5-flash", "gemini-1.5-flash-latest", "gemini-1.5-flash-001", "gemini-1.5-flash-002"]
    for m in models:
        await check_model(m)

if __name__ == "__main__":
    asyncio.run(main())
