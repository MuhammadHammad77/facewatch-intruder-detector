import os
import sys

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

import asyncio
from dotenv import load_dotenv

# Load env variables from backend folder
load_dotenv("facewatch-backend/backend/.env")

from supabase import create_client

def test_supabase():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    if not url or not key:
        print("Missing credentials")
        return
    
    print(f"Connecting to {url}")
    try:
        client = create_client(url, key)
        result = client.table("known_faces").select("id").limit(1).execute()
        print("✅ Success! Table 'known_faces' exists and is readable.")
    except Exception as e:
        print("❌ Error connecting to Supabase or reading 'known_faces':", e)

if __name__ == "__main__":
    test_supabase()
