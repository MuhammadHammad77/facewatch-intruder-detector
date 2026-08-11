import requests
import sys
import os

url = "http://localhost:8000/api/stream/upload"
filepath = r"C:\Users\Majid\Downloads\WhatsApp Video 2026-07-26 at 11.01.13 AM.mp4"

if not os.path.exists(filepath):
    print("File not found.")
    sys.exit(1)

print(f"Uploading {filepath}...")
with open(filepath, 'rb') as f:
    files = {'file': (os.path.basename(filepath), f, 'video/mp4')}
    response = requests.post(url, files=files)

print("Status Code:", response.status_code)
try:
    print("Response JSON:", response.json())
except Exception as e:
    print("Response Text:", response.text)
