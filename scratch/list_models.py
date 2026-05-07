import httpx
import asyncio
from bot.config import Config

async def list_models():
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={Config.GEMINI_API_KEY}"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                for model in data.get('models', []):
                    print(f"- {model['name']} (Supported: {model['supportedGenerationMethods']})")
            else:
                print(f"Error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(list_models())
