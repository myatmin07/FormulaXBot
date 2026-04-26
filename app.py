from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import urllib3
import re
import os
import json

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)
CORS(app)

API_TOKEN = '8483869457:AAFBlSIu_6biWRAZ7lgGBrT-smj7C7tsQ20'

OUTLINE_APIS = {
    "formulax.ponerdigital.shop": "https://168.144.97.72:28370/Vird_PHEuZqmB9hMSXMJZw",
    "formulax.poner.shop": "https://167.71.28.84:8226/SOyNR8u0N_5fw2i-Uz7-6Q",
    "168.144.97.72": "https://168.144.97.72:28370/Vird_PHEuZqmB9hMSXMJZw",
    "167.71.28.84": "https://167.71.28.84:8226/SOyNR8u0N_5fw2i-Uz7-6Q"
}

def load_db(file):
    if not os.path.exists(file): return {}
    with open(file, "r", encoding="utf-8") as f:
        try: return json.load(f)
        except: return {}

def save_db(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def bytes_to_gb(bytes_val):
    if not bytes_val: return 0.00
    return round(bytes_val / (1024 * 1024 * 1024), 2)

@app.route('/api/user_photo', methods=['GET'])
def get_user_photo():
    user_id = request.args.get('user_id')
    try:
        res = requests.get(f"https://api.telegram.org/bot{API_TOKEN}/getUserProfilePhotos?user_id={user_id}&limit=1")
        data = res.json()
        if data.get('ok') and data['result']['total_count'] > 0:
            file_id = data['result']['photos'][0][0]['file_id']
            file_res = requests.get(f"https://api.telegram.org/bot{API_TOKEN}/getFile?file_id={file_id}")
            file_data = file_res.json()
            if file_data.get('ok'):
                file_path = file_data['result']['file_path']
                photo_url = f"https://api.telegram.org/file/bot{API_TOKEN}/{file_path}"
                return jsonify({"success": True, "photo_url": photo_url})
    except:
        pass
    return jsonify({"success": False, "photo_url": None})

def fetch_fresh_photo(user_id):
    try:
        res = requests.get(f"https://api.telegram.org/bot{API_TOKEN}/getUserProfilePhotos?user_id={user_id}&limit=1")
        data = res.json()
        if data.get('ok') and data['result']['total_count'] > 0:
            file_id = data['result']['photos'][0][0]['file_id']
            file_res = requests.get(f"https://api.telegram.org/bot{API_TOKEN}/getFile?file_id={file_id}")
            file_data = file_res.json()
            if file_data.get('ok'):
                file_path = file_data['result']['file_path']
                return f"https://api.telegram.org/file/bot{API_TOKEN}/{file_path}"
    except:
        pass
    return None

@app.route('/api/auth_status', methods=['GET'])
def auth_status():
    user_id = request.args.get('user_id')
    if str(user_id) == "5890904598":
        return jsonify({"authorized": True})
    auth_db = load_db('formula_x_auth.json')
    if str(user_id) in auth_db:
        return jsonify({"authorized": True})
    return jsonify({"authorized": False})

@app.route('/api/profile', methods=['GET'])
def get_profile():
    user_id = request.args.get('user_id')
    history = load_db('formula_x_history.json').get(str(user_id), [])
    total_orders = len(history)
    total_spent = sum(item.get('total', 0) for item in history)
    return jsonify({"total_orders": total_orders, "total_spent": total_spent})
    
@app.route('/api/history', methods=['GET'])
def get_history():
    user_id = request.args.get('user_id')
    history = load_db('formula_x_history.json').get(str(user_id), [])
    return jsonify(history)
    
@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    history_db = load_db('formula_x_history.json')
    users_db = load_db('formula_x_users.json')
    
    leaderboard = []
    for uid, orders in history_db.items():
        total_spent = sum(o.get('total', 0) for o in orders)
        if total_spent > 0:
            name = users_db.get(uid, {}).get('name', f"User {uid}")
            photo = fetch_fresh_photo(uid)
            leaderboard.append({
                "name": name, 
                "spent": total_spent,
                "photo": photo
            })
            
    leaderboard.sort(key=lambda x: x['spent'], reverse=True)
    return jsonify(leaderboard[:5])

@app.route('/api/check_usage', methods=['POST'])
def check_usage():
    try:
        data = request.get_json()
        access_url = data.get('access_url', '').strip()
        
        match = re.search(r'@([^/:?#]+)', access_url)
        if not match:
            return jsonify({'success': False, 'error': 'Invalid Key Format'}), 400
        
        target_host = match.group(1).strip()
        api_url = OUTLINE_APIS.get(target_host)
        
        if not api_url:
            return jsonify({'success': False, 'error': 'Server not supported'}), 404

        keys_res = requests.get(f"{api_url}/access-keys", verify=False, timeout=10)
        metrics_res = requests.get(f"{api_url}/metrics/transfer", verify=False, timeout=10)
        
        if keys_res.status_code != 200 or metrics_res.status_code != 200:
            return jsonify({'success': False, 'error': 'Server API Error'}), 500
            
        keys_data = keys_res.json().get('accessKeys', [])
        metrics_data = metrics_res.json().get('bytesTransferredByUserId') or {}
        
        base_access_url = access_url.split('#')[0].strip()
        
        for key in keys_data:
            server_base = key.get('accessUrl', '').split('#')[0].strip()
            if server_base == base_access_url:
                kid = str(key.get('id'))
                used_bytes = metrics_data.get(kid, 0)
                limit_bytes = key.get('dataLimit', {}).get('bytes')
                
                used_gb = bytes_to_gb(used_bytes)
                limit_gb = bytes_to_gb(limit_bytes) if limit_bytes else "Unlimited"
                
                percentage = 0
                if limit_bytes and limit_bytes > 0:
                    percentage = min(100, round((used_bytes / limit_bytes) * 100))
                
                server_name = "Singapore" if "ponerdigital" in target_host or "168.144" in target_host else "USA"
                
                return jsonify({
                    'success': True,
                    'data': {
                        'key_name': key.get('name', 'Active Key'),
                        'used_gb': used_gb,
                        'limit_gb': limit_gb,
                        'percentage': percentage,
                        'server': server_name
                    }
                })
        
        return jsonify({'success': False, 'error': 'Key not found on server'}), 404

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
