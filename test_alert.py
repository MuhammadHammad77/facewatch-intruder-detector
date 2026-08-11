import asyncio
import sys
sys.path.append(r"C:\Users\Majid\Downloads\intruder detector\facewatch-backend\backend")
from routers.video_stream import _fire_alert
from db.supabase_client import init_db

async def test():
    await init_db()
    try:
        await _fire_alert("/snapshots/test.jpg", "0", 0.99)
        print("Alert fired successfully!")
    except Exception as e:
        print(f"Error firing alert: {e}")

if __name__ == "__main__":
    asyncio.run(test())
