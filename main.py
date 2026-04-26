import telebot
from telebot import types
import json
import os
import random
import string
import uuid
import requests
from datetime import datetime
import pytz
import urllib3
import time

# Disable SSL Warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- Configuration ---
API_TOKEN = '8483869457:AAFBlSIu_6biWRAZ7lgGBrT-smj7C7tsQ20'
ADMIN_ID = 5890904598
bot = telebot.TeleBot(API_TOKEN)

WEBAPP_URL = "https://xndk.vercel.app"

# Data Files
PENDING_FILE = "formula_x_pending.json"
USAGE_FILE = "formula_x_usage.json"
STOCK_FILE = "formula_x_stock.json"
USERS_FILE = "formula_x_users.json"
HISTORY_FILE = "formula_x_history.json"
SETTINGS_FILE = "formula_x_settings.json" # To save hidden buttons
MAX_LIMIT_GB = 3000

# --- Database Management ---
def save_db(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def load_db(file):
    if not os.path.exists(file):
        return {}
    with open(file, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return {}

# --- Custom Settings & Stock Logic ---
def toggle_visibility(prod):
    db = load_db(SETTINGS_FILE)
    hidden = db.get("hidden_prods", [])
    if prod in hidden:
        hidden.remove(prod)
    else:
        hidden.append(prod)
    db["hidden_prods"] = hidden
    save_db(SETTINGS_FILE, db)

def is_hidden(prod):
    return prod in load_db(SETTINGS_FILE).get("hidden_prods", [])

def get_stock(prod):
    return load_db(STOCK_FILE).get(prod, [])

def pop_stock(prod):
    db = load_db(STOCK_FILE)
    if prod not in db or len(db[prod]) == 0:
        return None
    acc = db[prod].pop(0)
    save_db(STOCK_FILE, db)
    return acc

def add_user(uid, name):
    db = load_db(USERS_FILE)
    if str(uid) not in db:
        db[str(uid)] = {"name": name, "joined": datetime.now(pytz.timezone('Asia/Yangon')).strftime("%Y-%m-%d")}
        save_db(USERS_FILE, db)

def add_history(uid, record):
    db = load_db(HISTORY_FILE)
    if str(uid) not in db:
        db[str(uid)] = []
    db[str(uid)].append(record)
    save_db(HISTORY_FILE, db)

# --- Emoji Formatting ---
def tg_emoji(emoji_id, fallback):
    return f'<tg-emoji emoji-id="{emoji_id}">{fallback}</tg-emoji>'

# Premium Emoji IDs
E_CHATGPT_ID = "6242255100924924923"
E_ALIGHT_ID = "6239810925231084514"
E_BACK_ID = "6084482488078437565"
E_GEMINI_ID = "5796314805564346672"
E_ZOOM_ID = "6239869452750428117"
E_KPAY_ID = "6201684659458280710"
E_WAVE_ID = "6143387285938245920"
E_SPOTIFY_ID = "5352614520332240585"
E_GROK_ID = "5454065032298009119"
E_YOUTUBE_ID = "5934029049260150525"
E_STOCK_ADD_ID = "5370604433233177619"
E_HIDE_ID = "5872988737826197458"
E_PLUS_ID = "5274008024585871702"
E_LINK_ID = "5271604874419647061"
E_BULB_ID = "5422439311196834318"
E_OUTLINE_ID = "5866384714507491897"
E_HIDDIFY_ID = "5940644462832127906"
E_MYINFO_ID = "5258011929993026890"
E_VERIFIED_ID = "5206607081334906820"
E_CONTACT_ID = "5458603043203327669"
E_CAPCUT_ID = "5364339557712020484"

# Global Reusable HTML Emoji Tags
E_TIP = tg_emoji("5841359499146825803", "⌨️")
E_STORE = tg_emoji("5229064374403998351", "🛍️")
E_OUTLINE = tg_emoji(E_OUTLINE_ID, "📱")
E_HIDDIFY = tg_emoji(E_HIDDIFY_ID, "🔑")
E_CAPCUT = tg_emoji(E_CAPCUT_ID, "✂️")
E_ALIGHT = tg_emoji(E_ALIGHT_ID, "🌀")
E_CHATGPT = tg_emoji(E_CHATGPT_ID, "🤖")
E_SPOTIFY = tg_emoji(E_SPOTIFY_ID, "🎵")
E_GEMINI = tg_emoji(E_GEMINI_ID, "✨")
E_ZOOM = tg_emoji(E_ZOOM_ID, "📹")
E_GROK = tg_emoji(E_GROK_ID, "👁")
E_YOUTUBE = tg_emoji(E_YOUTUBE_ID, "▶️")
E_ORDER = tg_emoji("5231200819986047254", "📊")
E_PRICE = tg_emoji("5197434882321567830", "💵")
E_EMAIL = tg_emoji("5472239203590888751", "📧")
E_PASSWORD = tg_emoji("5256248974767046755", "🔑")
E_LINK = tg_emoji(E_LINK_ID, "🔗")
E_BULB = tg_emoji(E_BULB_ID, "💡")
E_PLUS = tg_emoji(E_PLUS_ID, "➕")
E_WAVE = tg_emoji(E_WAVE_ID, "🌊")
E_KPAY = tg_emoji(E_KPAY_ID, "🔵")
E_MYINFO = tg_emoji(E_MYINFO_ID, "👤")
E_VERIFIED = tg_emoji(E_VERIFIED_ID, "✔️")

def send_styled(chat_id, text, kb_json, mid=None):
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML", "reply_markup": json.dumps(kb_json), "disable_web_page_preview": True}
    url = f"https://api.telegram.org/bot{API_TOKEN}/editMessageText" if mid else f"https://api.telegram.org/bot{API_TOKEN}/sendMessage"
    if mid:
        payload["message_id"] = mid
    return requests.post(url, data=payload)

def get_main_menu(uid):
    rows = []
    all_prods = [
        ("CapCut", "capcut", E_CAPCUT_ID),
        ("Alight Motion", "alight", E_ALIGHT_ID),
        ("ChatGPT", "chatgpt", E_CHATGPT_ID),
        ("Spotify", "spotify", E_SPOTIFY_ID),
        ("Grok", "grok", E_GROK_ID),
        ("Gemini", "gemini", E_GEMINI_ID),
        ("YouTube", "youtube", E_YOUTUBE_ID),
        ("Zoom", "zoom", E_ZOOM_ID)
    ]

def contact_admin_kb(back_data="back_home"):
    return {"inline_keyboard": [
        [{"text": "Contact Admin", "url": "https://t.me/FORMULA_X0", "icon_custom_emoji_id": E_CONTACT_ID}],
        [{"text": "Back", "callback_data": back_data, "icon_custom_emoji_id": E_BACK_ID, "style": "danger"}]
    ]}

# --- VPN API Logic ---
XUI_URL = "https://152.42.165.158:56869/G93DW24bMmtXj9Vpv5"
XUI_USERNAME = "8R7vfIqhS1"
XUI_PASSWORD = "kKF8GLiNHK"
INBOUND_ID = 1
SUB_URL_BASE = "https://152.42.165.158:2096/sub/"

OUTLINE_APIS = {
    "sg": "https://168.144.97.72:28370/Vird_PHEuZqmB9hMSXMJZw",
    "us": "https://167.71.28.84:8226/SOyNR8u0N_5fw2i-Uz7-6Q"
}

def generate_outline_keys(server, gb, qty):
    api_url = OUTLINE_APIS.get(server)
    if not api_url: return []
    links = []
    bytes_limit = int(gb) * 1024 * 1024 * 1024
    try:
        for _ in range(qty):
            res = requests.post(f"{api_url}/access-keys", verify=False, timeout=10)
            if res.status_code == 201:
                data = res.json()
                key_id = data.get("id")
                requests.put(f"{api_url}/access-keys/{key_id}/data-limit", json={"limit": {"bytes": bytes_limit}}, verify=False, timeout=10)
                requests.put(f"{api_url}/access-keys/{key_id}/name", json={"name": f"FX-{gb}GB-{random.randint(100, 999)}"}, verify=False, timeout=10)
                links.append(data.get("accessUrl"))
            time.sleep(0.5)
        return links
    except:
        return []

def generate_3xui_keys(days, gb, user_id, qty):
    session = requests.Session()
    try:
        login_res = session.post(f"{XUI_URL}/login", data={"username": XUI_USERNAME, "password": XUI_PASSWORD}, verify=False, timeout=10)
        if not login_res.json().get('success'): return []
        sub_links = []
        add_client_url = f"{XUI_URL}/panel/api/inbounds/addClient"
        total_bytes = int(gb) * 1024 * 1024 * 1024
        expiry_time = int((time.time() + (days * 86400)) * 1000)
        for _ in range(qty):
            client_uuid = str(uuid.uuid4())
            sub_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=16))
            payload = {"id": INBOUND_ID, "settings": json.dumps({"clients": [{"id": client_uuid, "flow": "xtls-rprx-vision", "email": f"FX-{user_id}-{random.randint(1000, 9999)}", "totalGB": total_bytes, "expiryTime": expiry_time, "enable": True, "tgId": "", "subId": sub_id}]})}
            res = session.post(add_client_url, json=payload, headers={"Accept": "application/json", "Content-Type": "application/json"}, verify=False, timeout=15)
            if res.json().get('success'):
                sub_links.append(f"{SUB_URL_BASE}{sub_id}")
            time.sleep(0.5)
        return sub_links
    except:
        return []

def get_current_usage():
    data = load_db(USAGE_FILE)
    return data.get("total_sold_gb", 0)

def add_usage(gb):
    data = load_db(USAGE_FILE)
    data["total_sold_gb"] = data.get("total_sold_gb", 0) + gb
    save_db(USAGE_FILE, data)

@bot.message_handler(commands=['start'])
def start_cmd(m):
    add_user(m.from_user.id, m.from_user.first_name)
    tz = pytz.timezone('Asia/Yangon')
    now = datetime.now(tz).strftime("%A, %B %d")

@bot.message_handler(func=lambda m: m.text in ["🛍️ Discover Products", "🔔 Contact Admin", "👤 My Info", "📊 Order History"])
def text_reply(m):
    uid = m.from_user.id
    if m.text == "🛍️ Discover Products":
        send_styled(m.chat.id, f"{E_STORE} Discover our products:", get_main_menu(uid))
    elif m.text == "🔔 Contact Admin":
        text = "Contact Admin\nNeed help? Reach out anytime:\n@FORMULA_X0"
        send_styled(m.chat.id, text, contact_admin_kb())
    elif m.text == "👤 My Info":
        db = load_db(USERS_FILE)
        joined = db.get(str(uid), {}).get("joined", "Unknown")
        text = f"{E_MYINFO} My Info\n\nName: {m.from_user.first_name}\nID: {uid}\nJoined Date: {joined}"
        send_styled(m.chat.id, text, contact_admin_kb())
    elif m.text == "📊 Order History":
        history = load_db(HISTORY_FILE).get(str(uid), [])
        text = f"{E_ORDER} Order History\n\n" + ("\n".join(history[-10:]) if history else "No orders found yet.")
        send_styled(m.chat.id, text, contact_admin_kb())

@bot.callback_query_handler(func=lambda call: True)
def query_handler(call):
    try:
        bot.answer_callback_query(call.id)
    except:
        pass

def process_vpn_qty(message, prod_type, server, gb_val):
    try:
        qty_str = message.text.strip()
        if not qty_str.isdigit():
            sent = bot.send_message(message.chat.id, "⚠️ Invalid input. Enter a number:", parse_mode="HTML")
            bot.register_next_step_handler(sent, process_vpn_qty, prod_type, server, gb_val)
            return

def process_stock(m, p):
    if ":" not in m.text:
        bot.reply_to(m, "❌ Invalid format. Use email:password", parse_mode="HTML")
        return
    email, pwd = m.text.split(":", 1)
    db = load_db(STOCK_FILE)
    if p not in db:
        db[p] = []
    db[p].append({"email": email.strip(), "password": pwd.strip()})
    save_db(STOCK_FILE, db) # Fully saves inside the file
    bot.reply_to(m, f"✅ Stock successfully added to {p.upper()}.\nTotal Available: {len(db[p])}", parse_mode="HTML")

@bot.message_handler(content_types=['photo'])
def handle_payment_slip(message):
    uid = message.from_user.id
    pending = load_db(PENDING_FILE)

if __name__ == "__main__":
    print("Formula X Final is starting on VPS...")
    bot.infinity_polling()
