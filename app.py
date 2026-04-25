from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import urllib3
import re

# Disable SSL Warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)
CORS(app) # Vercel ကနေ လှမ်းချိတ်လို့ရအောင်

# --- Server API Mapping ---
OUTLINE_APIS = {
    "168.144.97.72": "https://168.144.97.72:28370/Vird_PHEuZqmB9hMSXMJZw",
    "167.71.28.84": "https://167.71.28.84:8226/SOyNR8u0N_5fw2i-Uz7-6Q"
}

def bytes_to_gb(bytes_val):
    if not bytes_val: return 0.0
    return round(bytes_val / (1024 * 1024 * 1024), 2)

@app.route('/api/check_usage', methods=['POST'])
def check_usage():
    try:
        data = request.get_json()
        access_url = data.get('access_url', '').strip()
        
        # IP Extract လုပ်ခြင်း
        match = re.search(r'@([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+):', access_url)
        if not match:
            return jsonify({'success': False, 'error': 'Invalid Key Format'}), 400
        
        target_ip = match.group(1)
        api_url = OUTLINE_APIS.get(target_ip)
        
        if not api_url:
            return jsonify({'success': False, 'error': 'Server not supported'}), 404

        # Keys ဆွဲထုတ်ခြင်း
        keys_res = requests.get(f"{api_url}/access-keys", verify=False, timeout=10)
        metrics_res = requests.get(f"{api_url}/metrics/transfer", verify=False, timeout=10)
        
        if keys_res.status_code != 200 or metrics_res.status_code != 200:
            return jsonify({'success': False, 'error': 'Server Error'}), 500
            
        keys_data = keys_res.json().get('accessKeys', [])
        metrics_data = metrics_res.json().get('bytesTransferredByUserId', {})
        
        for key in keys_data:
            if key.get('accessUrl') == access_url:
                kid = key.get('id')
                used_bytes = metrics_data.get(kid, 0)
                limit_bytes = key.get('dataLimit', {}).get('bytes')
                
                used_gb = bytes_to_gb(used_bytes)
                limit_gb = bytes_to_gb(limit_bytes) if limit_bytes else "Unlimited"
                
                percentage = 0
                if limit_bytes:
                    percentage = min(100, round((used_bytes / limit_bytes) * 100))
                
                return jsonify({
                    'success': True,
                    'data': {
                        'key_name': key.get('name', 'Active Key'),
                        'used_gb': used_gb,
                        'limit_gb': limit_gb,
                        'percentage': percentage,
                        'server': "Singapore" if "168.144" in target_ip else "USA"
                    }
                })
        
        return jsonify({'success': False, 'error': 'Key not found on server'}), 404

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)