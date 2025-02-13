import json
import time
import threading
import requests
import websocket

online_accounts = {}

def authenticate(token):
    headers = {"Authorization": token, "Content-Type": "application/json"}
    validate = requests.get('https://discordapp.com/api/v9/users/@me', headers=headers)
    if validate.status_code != 200:
        return None
    return headers

def onliner(token, duration):
    headers = authenticate(token)
    if not headers:
        return False

    userinfo = requests.get('https://discordapp.com/api/v9/users/@me', headers=headers).json()
    username = userinfo["username"]
    
    ws = websocket.WebSocket()
    while True:
        try:
            ws.connect("wss://gateway.discord.gg/?v=9&encoding=json")
            break
        except:
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
            "presence": {"status": "online", "afk": False},
        },
    }
    
    ws.send(json.dumps(auth))
    online_accounts[username] = token

    end_time = time.time() + duration
    while time.time() < end_time:
        try:
            online = {"op": 1, "d": None}
            time.sleep(heartbeat / 1000)
            ws.send(json.dumps(online))
        except:
            break

    del online_accounts[username]
    return True

def run_onliner(token, duration):
    thread = threading.Thread(target=onliner, args=(token, duration))
    thread.start()
    return thread
