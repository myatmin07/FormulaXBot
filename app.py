from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import urllib3
import concurrent.futures

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)
CORS(app) 

SERVERS = {
    "Singapore": "https://167.71.28.84:8226/SOyNR8u0N_5fw2i-Uz7-6Q",
    "USA": "https://168.144.97.72:28370/Vird_PHEuZqmB9hMSXMJZw"
}

def format_bytes(byte_value):
    if not byte_value:
        return "0.00 GB"
    gb_value = byte_value / (1024 ** 3)
    return f"{gb_value:.2f} GB"

def check_single_server(server_name, api_url, clean_user_key):
    try:
        keys_response = requests.get(f"{api_url}/access-keys", verify=False, timeout=10)
        
        if keys_response.status_code != 200:
            return None

        keys_data = keys_response.json().get("accessKeys", [])
        matched_key = None
        
        for k in keys_data:
            server_access_url = k.get("accessUrl", "")
            clean_access_url = server_access_url.split("#")[0].split("?")[0].strip()
            
            if clean_access_url == clean_user_key:
                matched_key = k
                break

        if matched_key:
            key_id = str(matched_key.get("id"))
            
            limit_bytes = None
            if "dataLimit" in matched_key and "bytes" in matched_key["dataLimit"]:
                limit_bytes = matched_key["dataLimit"]["bytes"]
            
            limit_str = format_bytes(limit_bytes) if limit_bytes else "Unlimited"

            used_bytes = 0
            try:
                metrics_response = requests.get(f"{api_url}/metrics/transfer", verify=False, timeout=10)
                if metrics_response.status_code == 200:
                    metrics_data = metrics_response.json()
                    transfer_dict = metrics_data.get("bytesTransferredByUserId", {})
                    used_bytes = transfer_dict.get(key_id, 0)
            except Exception:
                pass 
                
            used_str = format_bytes(used_bytes)

            return {
                "status": "success",
                "server": server_name,
                "limit": limit_str,
                "used": used_str
            }
            
    except Exception:
        return None
        
    return None

@app.route('/api/check', methods=['GET'])
def check_outline_key():
    user_key = request.args.get('key', '').strip()
    
    if not user_key:
        return jsonify({"status": "error", "message": "Key parameter is missing"}), 400

    clean_user_key = user_key.split("#")[0].split("?")[0].strip()

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(check_single_server, name, url, clean_user_key) for name, url in SERVERS.items()]
        
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                return jsonify(result), 200

    return jsonify({"status": "error", "message": "Invalid Key or Key not found"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=False)
