from flask import Flask, request, jsonify
import json
import time
import requests
import websocket
import threading
from datetime import datetime, timedelta

app = Flask(__name__)
onliners = {}

def authenticate(token):
    headers = {"Authorization": token, "Content-Type": "application/json"}
    validate = requests.get('https://discordapp.com/api/v9/users/@me', headers=headers)
    if validate.status_code != 200:
        return None
    return headers

def onliner(token, status, custom_status, onliner_name, duration=None):
    headers = authenticate(token)
    if not headers:
        return False
    
    ws = websocket.WebSocket()
    while True:
        try:
            ws.connect("wss://gateway.discord.gg/?v=9&encoding=json")
            break
        except Exception:
            time.sleep(10)
    
    start = json.loads(ws.recv())
    heartbeat = start["d"]["heartbeat_interval"]
    auth = {
        "op": 2,
        "d": {
            "token": token,
            "properties": {
                "$os": "Windows 10",
                "$browser": "Google Chrome",
                "$device": "Windows",
            },
            "presence": {"status": status, "afk": False},
        },
    }
    ws.send(json.dumps(auth))
    cstatus = {
        "op": 3,
        "d": {
            "since": 0,
            "activities": [
                {
                    "type": 4,
                    "state": custom_status,
                    "name": "Custom Status",
                    "id": "custom",
                }
            ],
            "status": status,
            "afk": False,
        },
    }
    ws.send(json.dumps(cstatus))
    online = {"op": 1, "d": "None"}
    
    def keep_alive():
        while onliners.get(onliner_name, {}).get("ws") == ws:
            time.sleep(heartbeat / 1000)
            ws.send(json.dumps(online))
    
    thread = threading.Thread(target=keep_alive)
    thread.daemon = True  # Set thread sebagai daemon agar berhenti saat program utama berhenti
    thread.start()
    
    # Simpan informasi onliner
    onliners[onliner_name] = {"ws": ws, "token": token, "thread": thread}
    
    # Jika durasi ditentukan, atur timer untuk menghentikan onliner
    if duration:
        def stop_onliner_after_duration():
            time.sleep(duration)
            if onliner_name in onliners:
                ws = onliners.pop(onliner_name)["ws"]
                ws.close()
                print(f"Onliner {onliner_name} stopped after duration {duration} seconds")
        
        duration_seconds = parse_duration(duration)
        if duration_seconds:
            timer = threading.Timer(duration_seconds, stop_onliner_after_duration)
            timer.start()
    
    return True

def parse_duration(duration_str):
    """Mengubah string durasi (1d, 1w, 1m, 1y) menjadi detik."""
    if not duration_str:
        return None
    unit = duration_str[-1]
    value = int(duration_str[:-1])
    if unit == "d":
        return value * 86400  # 1 hari = 86400 detik
    elif unit == "w":
        return value * 604800  # 1 minggu = 604800 detik
    elif unit == "m":
        return value * 2592000  # 1 bulan = 2592000 detik (30 hari)
    elif unit == "y":
        return value * 31536000  # 1 tahun = 31536000 detik (365 hari)
    else:
        return None

@app.route("/onliner", methods=["GET"])
def start_onliner():
    token = request.args.get("token")
    status = request.args.get("status", "online")
    custom_status = request.args.get("custom_status", "")
    onliner_name = request.args.get("onliner_name", "default")
    duration = request.args.get("duration")  # Durasi dalam format 1d, 1w, 1m, 1y
    
    if not token:
        return jsonify({"error": "Token is required"}), 400
    
    if onliner_name in onliners:
        return jsonify({"error": "Onliner name already exists"}), 400
    
    success = onliner(token, status, custom_status, onliner_name, duration)
    if success:
        return jsonify({"message": "Onliner started", "onliner_name": onliner_name, "duration": duration})
    return jsonify({"error": "Invalid token"}), 400

@app.route("/delete", methods=["GET"])
def delete_onliner():
    onliner_name = request.args.get("onliner")
    if onliner_name in onliners:
        ws = onliners.pop(onliner_name)["ws"]
        ws.close()
        return jsonify({"message": "Onliner stopped"})
    return jsonify({"error": "Onliner not found"}), 404

@app.route("/data", methods=["GET"])
def get_data():
    return jsonify({"onliners": [{"onliner_name": name, "token": data["token"]} for name, data in onliners.items()]})

if __name__ == "__main__":
    # Jalankan Flask dalam thread terpisah
    flask_thread = threading.Thread(target=app.run, kwargs={"debug": True})
    flask_thread.daemon = True
    flask_thread.start()

    # Jalankan loop utama untuk menjaga thread WebSocket tetap hidup
    while True:
        time.sleep(1)
