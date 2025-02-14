from flask import Flask, request, jsonify
import json
import time
import requests
import websocket
import threading

app = Flask(__name__)
onliners = {}

def authenticate(token):
    headers = {"Authorization": token, "Content-Type": "application/json"}
    validate = requests.get('https://discordapp.com/api/v9/users/@me', headers=headers)
    if validate.status_code != 200:
        return None
    return headers

def onliner(token, status, custom_status, onliner_name):
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
        while onliners.get(onliner_name, None) == ws:
            time.sleep(heartbeat / 1000)
            ws.send(json.dumps(online))
    
    thread = threading.Thread(target=keep_alive)
    thread.start()
    onliners[onliner_name] = {"ws": ws, "token": token}
    return True

@app.route("/onliner", methods=["GET"])
def start_onliner():
    token = request.args.get("token")
    status = request.args.get("status", "online")
    custom_status = request.args.get("custom_status", "")
    onliner_name = request.args.get("onliner_name", "default")
    
    if not token:
        return jsonify({"error": "Token is required"}), 400
    
    if onliner_name in onliners:
        return jsonify({"error": "Onliner name already exists"}), 400
    
    success = onliner(token, status, custom_status, onliner_name)
    if success:
        return jsonify({"message": "Onliner started", "onliner_name": onliner_name})
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
    app.run(debug=True)
