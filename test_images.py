import urllib.request
import urllib.parse
import os
import json
import time

API_URL = "http://localhost:8000"

def register_face(name, image_path):
    print(f"Registering {name}...")
    
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    
    with open(image_path, "rb") as f:
        file_bytes = f.read()
    
    filename = os.path.basename(image_path)
    
    body = (
        f"--{boundary}\r\n"
        f"Content-Disposition: form-data; name=\"name\"\r\n\r\n"
        f"{name}\r\n"
        f"--{boundary}\r\n"
        f"Content-Disposition: form-data; name=\"file\"; filename=\"{filename}\"\r\n"
        f"Content-Type: image/jpeg\r\n\r\n"
    ).encode('utf-8') + file_bytes + f"\r\n--{boundary}--\r\n".encode('utf-8')

    req = urllib.request.Request(f"{API_URL}/api/faces/register", data=body)
    req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
    
    try:
        response = urllib.request.urlopen(req)
        print(f"Successfully registered {name}!")
        print(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Failed to register {name}: {e}")
        if hasattr(e, 'read'):
            print(e.read().decode('utf-8'))

if __name__ == "__main__":
    time.sleep(2)
    register_face("Majid", "c:/Users/Majid/Downloads/intruder detector/images/majid.jpeg")
    register_face("Hammad", "c:/Users/Majid/Downloads/intruder detector/images/hammad.jpeg")
