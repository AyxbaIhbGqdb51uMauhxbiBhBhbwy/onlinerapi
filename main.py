from flask import Flask, request, jsonify
from onliner import run_onliner, online_accounts

app = Flask(__name__)

time_mapping = {
    "1d": 86400,
    "1w": 604800,
    "1m": 2592000,
    "1y": 31536000
}

@app.route("/onliner")
def start_onliner():
    token = request.args.get("token")
    time_format = request.args.get("time")

    if not token or not time_format:
        return jsonify({"error": "Missing parameters"}), 400

    duration = time_mapping.get(time_format)
    if not duration:
        return jsonify({"error": "Invalid time format"}), 400

    run_onliner(token, duration)
    return jsonify({"message": "Onliner started"}), 200

@app.route("/delete")
def delete_onliner():
    username = request.args.get("onliner")

    if username in online_accounts:
        del online_accounts[username]
        return jsonify({"message": f"Onliner for {username} stopped"}), 200
    return jsonify({"error": "Account not found"}), 404

@app.route("/data")
def get_online_accounts():
    return jsonify(online_accounts), 200

if __name__ == "__main__":
    app.run()
