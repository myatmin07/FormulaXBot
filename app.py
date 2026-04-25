from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import urllib3
import re

# Disable SSL Warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

# Vercel ပေါ်ကနေ လှမ်းချိတ်ဆက်ခွင့်ပြုရန် (CORS Enable လုပ်ခြင်း)
CORS(app)

# ---------------------------------------------------------
# Outline Management API URLs
# ---------------------------------------------------------
OUTLINE_APIS = {
    "sg": "https://168.144.97.72:28370/Vird_PHEuZqmB9hMSXMJZw",
    "us": "https://167.71.28.84:8226/SOyNR8u0N_5fw2i-Uz7-6Q"
}

def bytes_to_gb(bytes_value):
    """Convert bytes to Gigabytes"""
    if not bytes_value:
        return 0.0
    gb_value = bytes_value / (1024 * 1024 * 1024)
    return round(gb_value, 2)

def extract_ip_port(access_url):
    """Extract IP and Port from the user's ss:// access URL to determine the server"""
    match = re.search(r'@([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+):([0-9]+)', access_url)
    if match:
        ip = match.group(1)
        port = match.group(2)
        return ip, port
    return None, None

def find_server_api_by_ip(target_ip):
    """Find which Management API matches the server IP"""
    for region, api_url in OUTLINE_APIS.items():
        if target_ip in api_url:
            return api_url
    return None

@app.route('/api/check_usage', methods=['POST'])
def check_usage():
    try:
        data = request.get_json()
        access_url = data.get('access_url', '').strip()
        
        if not access_url or not access_url.startswith('ss://'):
            return jsonify({'success': False, 'error': 'Invalid Outline Key format. Must start with ss://'}), 400

        # Step 1: Identify which server this key belongs to
        ip, port = extract_ip_port(access_url)
        if not ip:
             return jsonify({'success': False, 'error': 'Could not extract server IP from the key.'}), 400
             
        api_url = find_server_api_by_ip(ip)
        if not api_url:
             return jsonify({'success': False, 'error': 'Server IP not recognized in our database.'}), 404

        # Step 2: Fetch all access keys from that server to match the URL
        keys_res = requests.get(f"{api_url}/access-keys", verify=False, timeout=10)
        if keys_res.status_code != 200:
             return jsonify({'success': False, 'error': 'Failed to connect to the Outline Server.'}), 500
             
        keys_data = keys_res.json().get('accessKeys', [])
        
        target_key_id = None
        data_limit_bytes = None
        key_name = "Unknown"
        
        for key in keys_data:
            if key.get('accessUrl') == access_url:
                target_key_id = key.get('id')
                data_limit_bytes = key.get('dataLimit', {}).get('bytes')
                key_name = key.get('name', f"Key {target_key_id}")
                break
                
        if not target_key_id:
             return jsonify({'success': False, 'error': 'This key does not exist on the server. It may have been deleted.'}), 404

        # Step 3: Fetch the data transfer metrics
        metrics_res = requests.get(f"{api_url}/metrics/transfer", verify=False, timeout=10)
        if metrics_res.status_code != 200:
            return jsonify({'success': False, 'error': 'Failed to fetch usage metrics.'}), 500
            
        metrics_data = metrics_res.json().get('bytesTransferredByUserId', {})
        
        used_bytes = metrics_data.get(target_key_id, 0)
        used_gb = bytes_to_gb(used_bytes)
        limit_gb = bytes_to_gb(data_limit_bytes) if data_limit_bytes else "Unlimited"
        
        percentage = 0
        if isinstance(limit_gb, (int, float)) and limit_gb > 0:
            percentage = min(100, round((used_gb / limit_gb) * 100))

        return jsonify({
            'success': True,
            'data': {
                'key_name': key_name,
                'used_gb': used_gb,
                'limit_gb': limit_gb,
                'percentage': percentage,
                'server_ip': ip
            }
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    print("Formula-X VPN Data Checker API is running on port 5000...")
    app.run(host='0.0.0.0', port=5000)
