from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()

app = Flask(__name__)

PORT = int(os.getenv("PORT", "5000"))

OUTLINE_SERVERS = {
    "Singapore": os.getenv("OUTLINE_SG_API", "").strip(),
    "USA": os.getenv("OUTLINE_US_API", "").strip()
}


@app.after_request
def add_response_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Accept"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "online",
        "service": "FormulaX Outline Checker API",
        "port": PORT
    }), 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "online"
    }), 200


def clean_text(value):
    return str(value or "").strip().replace("\n", "").replace("\r", "")


def format_bytes(value):
    try:
        value = int(value or 0)
    except Exception:
        value = 0

    gb = value / (1024 ** 3)
    mb = value / (1024 ** 2)
    kb = value / 1024

    if gb >= 1:
        return f"{gb:.2f} GB"

    if mb >= 1:
        return f"{mb:.2f} MB"

    if kb >= 1:
        return f"{kb:.2f} KB"

    return "0 KB"


def get_access_keys(api_url):
    response = requests.get(
        f"{api_url.rstrip('/')}/access-keys",
        verify=False,
        timeout=15
    )

    response.raise_for_status()
    data = response.json()

    return data.get("accessKeys", [])


def get_transfer_usage(api_url):
    response = requests.get(
        f"{api_url.rstrip('/')}/metrics/transfer",
        verify=False,
        timeout=15
    )

    response.raise_for_status()
    data = response.json()

    return data.get("bytesTransferredByUserId", {})


def check_key_on_server(server_name, api_url, user_key):
    access_keys = get_access_keys(api_url)

    for access_key in access_keys:
        saved_key = clean_text(access_key.get("accessUrl"))

        if saved_key == user_key:
            key_id = str(access_key.get("id", ""))
            key_name = access_key.get("name") or "No Name"

            data_limit = access_key.get("dataLimit") or {}
            limit_bytes = data_limit.get("bytes")

            usage_data = get_transfer_usage(api_url)
            used_bytes = usage_data.get(key_id, 0)

            return {
                "found": True,
                "server": server_name,
                "key_id": key_id,
                "name": key_name,
                "limit": format_bytes(limit_bytes) if limit_bytes else "Unlimited",
                "used": format_bytes(used_bytes)
            }

    return {
        "found": False
    }


@app.route("/api/check", methods=["GET", "POST", "OPTIONS"])
def check_outline_key():
    if request.method == "OPTIONS":
        return jsonify({
            "status": "ok"
        }), 200

    user_key = clean_text(request.args.get("key"))

    if not user_key:
        return jsonify({
            "status": "error",
            "message": "Please paste your Outline access key."
        }), 400

    if not user_key.startswith("ss://"):
        return jsonify({
            "status": "error",
            "message": "Invalid Outline key format. The key must start with ss://"
        }), 400

    active_servers = {
        name: url for name, url in OUTLINE_SERVERS.items() if url
    }

    if not active_servers:
        return jsonify({
            "status": "error",
            "message": "Outline API servers are not configured on the VPS."
        }), 500

    errors = []

    for server_name, api_url in active_servers.items():
        try:
            result = check_key_on_server(server_name, api_url, user_key)

            if result.get("found"):
                return jsonify({
                    "status": "success",
                    "server": result["server"],
                    "keyId": result["key_id"],
                    "name": result["name"],
                    "limit": result["limit"],
                    "used": result["used"]
                }), 200

        except requests.exceptions.Timeout:
            errors.append(f"{server_name}: request timeout")
        except requests.exceptions.ConnectionError:
            errors.append(f"{server_name}: connection error")
        except requests.exceptions.HTTPError as error:
            status_code = error.response.status_code if error.response else "unknown"
            errors.append(f"{server_name}: HTTP {status_code}")
        except Exception as error:
            errors.append(f"{server_name}: {str(error)}")

    return jsonify({
        "status": "error",
        "message": "Key not found or Outline servers are unreachable.",
        "details": errors
    }), 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
