from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
import requests
import urllib3
import concurrent.futures

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()

app = Flask(__name__)
CORS(app)

SERVERS = {
    "Singapore": os.getenv("OUTLINE_SG_API", "").strip(),
    "USA": os.getenv("OUTLINE_US_API", "").strip()
}


def format_bytes(byte_value):
    if byte_value is None:
        return "Unlimited"

    try:
        byte_value = int(byte_value)
    except Exception:
        return "0.00 GB"

    gb_value = byte_value / (1024 ** 3)
    return f"{gb_value:.2f} GB"


def normalize_key(key):
    return str(key or "").strip().split("#")[0].split("?")[0].strip()


def get_user_key():
    data = request.get_json(silent=True) or {}

    key = (
        data.get("key")
        or data.get("accessKey")
        or data.get("access_url")
        or data.get("accessUrl")
        or request.args.get("key")
        or ""
    )

    return str(key).strip()


def check_single_server(server_name, api_url, clean_user_key):
    if not api_url:
        return None

    try:
        keys_response = requests.get(
            f"{api_url.rstrip('/')}/access-keys",
            verify=False,
            timeout=12
        )

        if keys_response.status_code != 200:
            return None

        keys_data = keys_response.json().get("accessKeys", [])
        matched_key = None

        for item in keys_data:
            server_access_url = item.get("accessUrl", "")
            clean_access_url = normalize_key(server_access_url)

            if clean_access_url == clean_user_key:
                matched_key = item
                break

        if not matched_key:
            return None

        key_id = str(matched_key.get("id", ""))
        key_name = matched_key.get("name") or "--"

        data_limit = matched_key.get("dataLimit") or {}
        limit_bytes = data_limit.get("bytes")
        data_limit_text = format_bytes(limit_bytes)

        used_bytes = 0

        try:
            metrics_response = requests.get(
                f"{api_url.rstrip('/')}/metrics/transfer",
                verify=False,
                timeout=12
            )

            if metrics_response.status_code == 200:
                metrics_data = metrics_response.json()
                transfer_data = metrics_data.get("bytesTransferredByUserId", {})
                used_bytes = int(transfer_data.get(key_id, 0))
        except Exception:
            used_bytes = 0

        data_used_text = format_bytes(used_bytes)

        return {
            "status": "success",
            "message": "Outline key found.",
            "server": server_name,
            "keyName": key_name,
            "dataLimit": data_limit_text,
            "dataUsed": data_used_text,
            "limit": data_limit_text,
            "used": data_used_text
        }

    except Exception as error:
        return {
            "status": "server_error",
            "server": server_name,
            "message": str(error)
        }


@app.after_request
def add_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Accept"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "online",
        "service": "FormulaX Outline Checker API"
    }), 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "online"
    }), 200


@app.route("/api/check", methods=["GET", "POST", "OPTIONS"])
def check_outline_key():
    if request.method == "OPTIONS":
        return jsonify({
            "status": "ok"
        }), 200

    user_key = get_user_key()

    if not user_key:
        return jsonify({
            "status": "error",
            "message": "Key parameter is missing.",
            "server": "--",
            "keyName": "--",
            "dataLimit": "--",
            "dataUsed": "--"
        }), 400

    if not user_key.startswith("ss://"):
        return jsonify({
            "status": "error",
            "message": "Invalid Outline key format. The key must start with ss://",
            "server": "--",
            "keyName": "--",
            "dataLimit": "--",
            "dataUsed": "--"
        }), 400

    clean_user_key = normalize_key(user_key)

    active_servers = {
        name: url for name, url in SERVERS.items() if url
    }

    if not active_servers:
        return jsonify({
            "status": "error",
            "message": "Outline servers are not configured.",
            "server": "--",
            "keyName": "--",
            "dataLimit": "--",
            "dataUsed": "--"
        }), 500

    server_errors = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(active_servers)) as executor:
        futures = [
            executor.submit(check_single_server, name, url, clean_user_key)
            for name, url in active_servers.items()
        ]

        for future in concurrent.futures.as_completed(futures):
            result = future.result()

            if result and result.get("status") == "success":
                return jsonify(result), 200

            if result and result.get("status") == "server_error":
                server_errors.append(f"{result.get('server')}: {result.get('message')}")

    return jsonify({
        "status": "not_found",
        "message": "Outline key was not found on the configured servers.",
        "server": "--",
        "keyName": "--",
        "dataLimit": "--",
        "dataUsed": "--",
        "errors": server_errors
    }), 404


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)
