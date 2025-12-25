from google import genai
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("No API Key found.")
else:
    print(f"Using API Key: {api_key[:5]}...")
    try:
        client = genai.Client(api_key=api_key)
        print("Listing models...")
        # Try to list models to see what's available
        # Note: syntax might depend on exact version, but let's try standard iteration
        # In new SDK it might be client.models.list() returning an iterable
        for m in client.models.list():
            if "gemini" in m.name:
                print(f" - {m.name} (Supported: {m.supported_actions})")
    except Exception as e:
        print(f"Error listing models: {e}")
