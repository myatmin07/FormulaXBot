from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import urllib3
import concurrent.futures

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)
CORS(app)

SERVERS = {
    "Singapore": "https://formulax.poner.shop:8226/SOyNR8u0N_5fw2i-Uz7-6Q",
    "USA": "https://formulaxoutlinekey.online:28370/Vird_PHEuZqmB9hMSXMJZw"
}

def format_bytes(value):
    try:
        value = int(value or 0)
    except:
        value = 0
    return f"{value / (1024 ** 3):.2f} GB"

def clean_key(key):
    return key.strip().split("#")[0].split("?")[0]

def check_server(server_name, api_url, user_key):
    try:
        res = requests.get(f"{api_url}/access-keys", verify=False, timeout=15)

        if res.status_code != 200:
            print(server_name, "access-keys error:", res.status_code)
            return None

        access_keys = res.json().get("accessKeys", [])

        matched = None
        for item in access_keys:
            api_key = clean_key(item.get("accessUrl", ""))
            if api_key == user_key:
                matched = item
                break

        if not matched:
            return None

        key_id = str(matched.get("id"))

        limit_bytes = matched.get("dataLimit", {}).get("bytes")
        limit_text = format_bytes(limit_bytes) if limit_bytes else "Unlimited"

        used_bytes = 0

        try:
            metrics = requests.get(f"{api_url}/metrics/transfer", verify=False, timeout=15)

            if metrics.status_code == 200:
                transfer = metrics.json().get("bytesTransferredByUserId", {})
                used_bytes = transfer.get(key_id, 0)

        except Exception as e:
            print(server_name, "metrics error:", e)

        return {
            "status": "success",
            "server": server_name,
            "limit": limit_text,
            "used": format_bytes(used_bytes)
        }

    except Exception as e:
        print(server_name, "server error:", e)
        return None

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "online",
        "message": "Formula-X Outline Checker API is running"
    })

@app.route("/api/check", methods=["GET"])
def check_key():
    key = request.args.get("key", "").strip()

    if not key:
        return jsonify({
            "status": "error",
            "message": "Key missing"
        }), 400

    if not key.startswith("ss://"):
        return jsonify({
            "status": "error",
            "message": "Invalid Outline key format"
        }), 400

    user_key = clean_key(key)

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(check_server, name, url, user_key)
            for name, url in SERVERS.items()
        ]

        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                return jsonify(result), 200

    return jsonify({
        "status": "error",
        "message": "Invalid key or key not found"
    }), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=False)
