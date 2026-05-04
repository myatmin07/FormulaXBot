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
import re
import traceback

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- Configuration ---
API_TOKEN = '8483869457:AAFI5GOrPxESGhsvJIgpZEcIRmZb3XbK7sg'
ADMIN_ID = 5890904598
bot = telebot.TeleBot(API_TOKEN)

# Data Files
PENDING_FILE = "formula_x_pending.json"
USAGE_FILE = "formula_x_usage.json"
STOCK_FILE = "formula_x_stock.json"
USERS_FILE = "formula_x_users.json"
HISTORY_FILE = "formula_x_history.json"
SETTINGS_FILE = "formula_x_settings.json" 
KEYS_FILE = "formula_x_keys.json" 
MAX_LIMIT_GB = 3000

# --- Database Management ---
def save_db(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def load_db(file):
    if not os.path.exists(file): return {}
    with open(file, "r", encoding="utf-8") as f:
        try: return json.load(f)
        except: return {}

# --- Access Check Logic ---
def check_access(uid):
    if uid == ADMIN_ID: return True
    db = load_db(USERS_FILE)
    user = db.get(str(uid), {})
    return user.get("is_authorized", False)

# --- Custom Settings & Stock Logic ---
def toggle_visibility(prod):
    db = load_db(SETTINGS_FILE)
    hidden = db.get("hidden_prods", [])
    if prod in hidden: hidden.remove(prod)
    else: hidden.append(prod)
    db["hidden_prods"] = hidden
    save_db(SETTINGS_FILE, db)

def is_hidden(prod):
    return prod in load_db(SETTINGS_FILE).get("hidden_prods", [])

def get_stock(prod):
    return load_db(STOCK_FILE).get(prod, [])

def pop_stock(prod):
    db = load_db(STOCK_FILE)
    if prod not in db or len(db[prod]) == 0: return None
    acc = db[prod].pop(0) 
    save_db(STOCK_FILE, db)
    return acc

def add_user(uid, name):
    db = load_db(USERS_FILE)
    if str(uid) not in db:
        db[str(uid)] = {
            "name": name, 
            "joined": datetime.now(pytz.timezone('Asia/Yangon')).strftime("%Y-%m-%d %H:%M"),
            "is_authorized": False
        }
        save_db(USERS_FILE, db)

def add_order_history(uid, oid, prod_desc, status, date_str):
    db = load_db(HISTORY_FILE)
    if str(uid) not in db: db[str(uid)] = []
    db[str(uid)].append({"oid": oid, "desc": prod_desc, "status": status, "date": date_str})
    save_db(HISTORY_FILE, db)

def update_order_history(uid, oid, new_status):
    db = load_db(HISTORY_FILE)
    if str(uid) in db:
        for item in db[str(uid)]:
            if isinstance(item, dict) and item.get("oid") == oid:
                item["status"] = new_status
        save_db(HISTORY_FILE, db)

def get_server_usage(server_id):
    data = load_db(USAGE_FILE)
    return data.get(server_id, 0)

def add_server_usage(server_id, gb):
    data = load_db(USAGE_FILE)
    data[server_id] = data.get(server_id, 0) + gb
    save_db(USAGE_FILE, data)

# --- Emoji IDs ---
def tg_emoji(emoji_id, fallback):
    return f'<tg-emoji emoji-id="{emoji_id}">{fallback}</tg-emoji>'

# Premium Emojis
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
E_DAYS_ID = "5382194935057372936"
E_SUMMARY_ID = "4960766907113276588"
E_QTY_ID = "5823347218056221496"
E_STORE_ID = "5229064374403998351" 
E_ORDER_ID = "5841276284155467413" 
E_HELP_ID = "5461117441612462242"   
E_MENU_ID = "5427168083074628963"   
E_QUESTION_ID = "5436113877181941026"
E_DOWN_ID = "5406745015365943482"
E_EMAIL_PREM_ID = "5253742260054409879"
E_PASS_PREM_ID = "5307843983102204243"
E_ACCESS_ID = "5296369303661067030"
E_WELCOME_ID = "5461151367559141950"
E_TOTAL_ID = "5409048419211682843"

# Tags
E_TIP = tg_emoji("5841359499146825803", "⌨️")
E_STORE = tg_emoji(E_STORE_ID, "🛍️")
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
E_ORDER = tg_emoji(E_ORDER_ID, "🆔") 
E_PRICE = tg_emoji("5197434882321567830", "💲")
E_LINK = tg_emoji(E_LINK_ID, "🔗")
E_BULB = tg_emoji(E_BULB_ID, "💡")
E_PLUS = tg_emoji(E_PLUS_ID, "➕")
E_WAVE = tg_emoji(E_WAVE_ID, "🌊")
E_KPAY = tg_emoji(E_KPAY_ID, "🔵")
E_MYINFO = tg_emoji(E_MYINFO_ID, "👤") 
E_VERIFIED = tg_emoji(E_VERIFIED_ID, "✅")
E_DAYS = tg_emoji(E_DAYS_ID, "⏳")
E_SUMMARY = tg_emoji(E_SUMMARY_ID, "📦") 
E_QTY = tg_emoji(E_QTY_ID, "📦")
E_QUESTION = tg_emoji(E_QUESTION_ID, "❓")
E_DOWN = tg_emoji(E_DOWN_ID, "⬇️")
E_EMAIL_PREM = tg_emoji(E_EMAIL_PREM_ID, "📧")
E_PASS_PREM = tg_emoji(E_PASS_PREM_ID, "🔑")
E_ACCESS = tg_emoji(E_ACCESS_ID, "🔒")
E_WELCOME = tg_emoji(E_WELCOME_ID, "🎉")
E_TOTAL = tg_emoji(E_TOTAL_ID, "💰") 

PROD_INFO = {
    "capcut": (E_CAPCUT, "CapCut", "Team 35 Days"),
    "alight": (E_ALIGHT, "Alight Motion", "Private - 1 Year"),
    "gemini_pro": (E_GEMINI, "Gemini Pro", "1 Year"),
    "gemini_veo": (E_GEMINI, "Veo3 Ultra", "25K Credit"),
    "zoom": (E_ZOOM, "Zoom Premium", "100p | 28 Days"),
    "grok_7": (E_GROK, "Grok", "Super 7 Days"),
    "grok_15": (E_GROK, "Grok", "Super 15 Days"),
    "youtube": (E_YOUTUBE, "YouTube Premium", "Individual 1 Month"),
    "chatgpt_plus": (E_CHATGPT, "ChatGPT Plus", "1 Month"),
    "chatgpt_renew": (E_CHATGPT, "ChatGPT Plus Renew", "1 Month"),
    "chatgpt_biz": (E_CHATGPT, "ChatGPT Business", "1 Month"),
    "spotify_2": (E_SPOTIFY, "Spotify", "2 Months Individual"),
    "spotify_3": (E_SPOTIFY, "Spotify", "3 Months Individual")
}

# --- Beautiful Account Formatting ---
def format_acc_details(raw_data):
    raw = str(raw_data).strip()
    email = ""
    pwd = ""
    
    if ":" in raw:
        parts = raw.split(":", 1)
        email, pwd = parts[0].strip(), parts[1].strip()
    elif "\n" in raw:
        parts = raw.split("\n", 1)
        email, pwd = parts[0].strip(), parts[1].strip()
    else:
        return f"<code>{raw}</code>"
        
    formatted = f"{E_EMAIL_PREM} <b>Email:</b>\n<code>{email}</code>\n\n"
    formatted += f"{E_PASS_PREM} <b>Password:</b>\n<code>{pwd}</code>"
    return formatted

# --- Raw API Requests ---
def send_styled(chat_id, text, kb_json, mid=None):
    payload = {
        "chat_id": chat_id, "text": text, "parse_mode": "HTML", 
        "reply_markup": kb_json, "link_preview_options": {"is_disabled": True}
    }
    if mid:
        payload["message_id"] = mid
        res = requests.post(f"https://api.telegram.org/bot{API_TOKEN}/editMessageText", json=payload)
        if not res.json().get('ok'):
            requests.post(f"https://api.telegram.org/bot{API_TOKEN}/deleteMessage", json={"chat_id": chat_id, "message_id": mid})
            del payload["message_id"]
            return requests.post(f"https://api.telegram.org/bot{API_TOKEN}/sendMessage", json=payload)
        return res
    else:
        return requests.post(f"https://api.telegram.org/bot{API_TOKEN}/sendMessage", json=payload)

def send_photo_with_raw_keyboard(chat_id, photo_url, caption, reply_markup=None):
    payload = {"chat_id": chat_id, "photo": photo_url, "caption": caption, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    res = requests.post(f"https://api.telegram.org/bot{API_TOKEN}/sendPhoto", data=payload)
    if not res.json().get('ok'):
        payload_text = {"chat_id": chat_id, "text": caption, "parse_mode": "HTML"}
        if reply_markup:
            payload_text["reply_markup"] = json.dumps(reply_markup)
        requests.post(f"https://api.telegram.org/bot{API_TOKEN}/sendMessage", data=payload_text)

# --- Keyboards ---
def get_main_menu(uid):
    rows = []
    if not is_hidden("out"): rows.append([{"text": "Outline VPN", "callback_data": "prod_out", "icon_custom_emoji_id": E_OUTLINE_ID, "style": "success"}])
    if not is_hidden("hid"): rows.append([{"text": "Hiddify / V2Ray", "callback_data": "prod_hid", "icon_custom_emoji_id": E_HIDDIFY_ID, "style": "primary"}])
    
    all_prods = [
        ("CapCut", "capcut", "5364339557712020484"), ("Alight Motion", "alight", E_ALIGHT_ID),
        ("ChatGPT", "chatgpt", E_CHATGPT_ID), ("Spotify", "spotify", E_SPOTIFY_ID),
        ("Grok", "grok", E_GROK_ID), ("Gemini", "gemini", E_GEMINI_ID),
        ("YouTube", "youtube", E_YOUTUBE_ID), ("Zoom", "zoom", E_ZOOM_ID)
    ]
    
    visible_prods = [p for p in all_prods if not is_hidden(p[1])]
    for i in range(0, len(visible_prods), 2):
        row = []
        for p in visible_prods[i:i+2]:
            row.append({"text": p[0], "callback_data": f"prod_{p[1]}", "icon_custom_emoji_id": p[2]})
        rows.append(row)
        
    if uid == ADMIN_ID:
        rows.append([
            {"text": "Add Stock", "callback_data": "admin_stock_btn", "icon_custom_emoji_id": E_STOCK_ADD_ID, "style": "primary"},
            {"text": "Visibility", "callback_data": "admin_vis_btn", "icon_custom_emoji_id": E_HIDE_ID}
        ])
    return {"inline_keyboard": rows}

def contact_admin_kb(back_data="back_home"):
    return {"inline_keyboard": [
        [{"text": "Contact Admin", "url": "https://t.me/FORMULA_X0", "icon_custom_emoji_id": "5458603043203327669"}],
        [{"text": "Back", "callback_data": back_data, "icon_custom_emoji_id": E_BACK_ID, "style": "danger"}]
    ]}

# --- VPN API Logic ---
XUI_URL = "https://152.42.165.158:56869/G93DW24bMmtXj9Vpv5"
XUI_USERNAME = "8R7vfIqhS1"
XUI_PASSWORD = "kKF8GLiNHK"
INBOUND_ID = 1 
SUB_URL_BASE = "https://152.42.165.158:2096/sub/"

OUTLINE_APIS = {
    "sg": "https://formulax.poner.shop:8226/SOyNR8u0N_5fw2i-Uz7-6Q",
    "us": "https://formulaxoutlinekey.online:28370/Vird_PHEuZqmB9hMSXMJZw"
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
                requests.put(f"{api_url}/access-keys/{key_id}/name", json={"name": f"FX-{gb}GB-{uuid.uuid4().hex[:8]}"}, verify=False, timeout=10)
                links.append(data.get("accessUrl"))
            time.sleep(0.5)
        return links
    except Exception as e:
        print(f"Outline API Error: {e}")
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
            payload = {"id": INBOUND_ID, "settings": json.dumps({"clients": [{"id": client_uuid, "flow": "xtls-rprx-vision", "email": f"FX-{user_id}-{uuid.uuid4().hex[:8]}", "totalGB": total_bytes, "expiryTime": expiry_time, "enable": True, "tgId": "", "subId": sub_id}]})}
            res = session.post(add_client_url, json=payload, headers={"Accept": "application/json", "Content-Type": "application/json"}, verify=False, timeout=15)
            if res.json().get('success'): sub_links.append(f"{SUB_URL_BASE}{sub_id}")
            time.sleep(0.5)
        return sub_links
    except: return []

# --- Handlers ---

@bot.message_handler(commands=['clearstock'])
def clear_stock_cmd(m):
    if m.from_user.id == ADMIN_ID:
        save_db(STOCK_FILE, {})
        bot.reply_to(m, "✅ <b>All stock has been successfully cleared.</b>\nYou can now add new accounts without them mixing up!", parse_mode="HTML")

# --- Access Generation for Admin ---
@bot.message_handler(commands=['genkey'])
def genkey_cmd(m):
    if m.from_user.id != ADMIN_ID: return
    try:
        qty = int(m.text.split()[1])
    except:
        qty = 1
        
    db = load_db(KEYS_FILE)
    if "keys" not in db: db["keys"] = []
    
    new_keys = []
    for _ in range(qty):
        k = f"FX-{uuid.uuid4().hex[:6].upper()}"
        db["keys"].append(k)
        new_keys.append(k)
        
    save_db(KEYS_FILE, db)
    keys_str = "\n".join([f"<code>{k}</code>" for k in new_keys])
    bot.reply_to(m, f"✅ <b>Generated {qty} Keys:</b>\n\n{keys_str}", parse_mode="HTML")

# --- User Access System ---
@bot.message_handler(commands=['access'])
def access_cmd(m):
    uid = m.from_user.id
    if check_access(uid):
        bot.reply_to(m, "✅ You already have access to the bot!")
        return
        
    try:
        key = m.text.split()[1]
    except:
        bot.reply_to(m, f"⚠️ Format: <code>/access YOUR_KEY</code>\n\nPlease enter the valid key provided by admin.", parse_mode="HTML")
        return
        
    db = load_db(KEYS_FILE)
    keys = db.get("keys", [])
    
    if key in keys:
        keys.remove(key)
        db["keys"] = keys
        save_db(KEYS_FILE, db)
        
        users = load_db(USERS_FILE)
        if str(uid) not in users:
            users[str(uid)] = {"name": m.from_user.first_name, "joined": datetime.now(pytz.timezone('Asia/Yangon')).strftime("%Y-%m-%d %H:%M"), "is_authorized": True}
        else:
            users[str(uid)]["is_authorized"] = True
        save_db(USERS_FILE, users)
        
        msg = f"✅ Access granted!\n\nYou can now use the bot. Choose an option below {E_DOWN}"
        
        reply_markup = {
            "keyboard": [
                [{"text": "Discover Products", "icon_custom_emoji_id": "5229064374403998351"}],
                [
                    {"text": "Contact Admin", "icon_custom_emoji_id": "5458603043203327669"}, 
                    {"text": "My Info", "icon_custom_emoji_id": "5258011929993026890"}
                ],
                [{"text": "Order History", "icon_custom_emoji_id": "5841276284155467413"}],
                [{"text": "Help", "icon_custom_emoji_id": "5461117441612462242"}],
                [{"text": "Main Menu", "icon_custom_emoji_id": "5427168083074628963"}]
            ],
            "resize_keyboard": True
        }
        
        payload = {
            "chat_id": m.chat.id,
            "text": msg,
            "parse_mode": "HTML",
            "reply_markup": json.dumps(reply_markup)
        }
        requests.post(f"https://api.telegram.org/bot{API_TOKEN}/sendMessage", json=payload)
    else:
        bot.reply_to(m, "❌ Invalid or already used key.", parse_mode="HTML")

@bot.message_handler(commands=['start'])
def start_cmd(m):
    uid = m.from_user.id
    add_user(uid, m.from_user.first_name)
    
    img_url = "https://raw.githubusercontent.com/myatmin07/Formula/refs/heads/main/file_000000009dd0720899ff78779c7e1fd2.png"
    
    if not check_access(uid):
        msg = f"{E_ACCESS} <b>Access Required</b>\n\nYou need an access key to use this bot.\nPlease enter your key using the command:\n<code>/access YOUR_KEY_HERE</code>"
        send_photo_with_raw_keyboard(m.chat.id, img_url, msg)
        return

    tz = pytz.timezone('Asia/Yangon')
    now = datetime.now(tz).strftime("%A, %B %d")
    
    reply_markup = {
        "keyboard": [
            [{"text": "Discover Products", "icon_custom_emoji_id": "5229064374403998351"}],
            [
                {"text": "Contact Admin", "icon_custom_emoji_id": "5458603043203327669"}, 
                {"text": "My Info", "icon_custom_emoji_id": "5258011929993026890"}
            ],
            [{"text": "Order History", "icon_custom_emoji_id": "5841276284155467413"}],
            [{"text": "Help", "icon_custom_emoji_id": "5461117441612462242"}],
            [{"text": "Main Menu", "icon_custom_emoji_id": "5427168083074628963"}]
        ],
        "resize_keyboard": True
    }
    
    caption = f"{m.from_user.first_name} — Hope your day is going smoothly\nTime: <i>{now}</i>.\n\n{E_TIP} <b>Tip:</b> Use the menu below your message box."
    send_photo_with_raw_keyboard(m.chat.id, img_url, caption, reply_markup)
    send_styled(m.chat.id, f"{E_STORE} <b>Discover our products:</b>", get_main_menu(uid))

@bot.message_handler(func=lambda m: m.text and any(btn in m.text for btn in ["Discover", "Contact", "My Info", "History", "Help", "Main Menu"]))
def text_reply(m):
    uid = m.from_user.id
    if not check_access(uid):
        msg = f"{E_ACCESS} <b>Access Required</b>\n\nPlease enter your key using the command:\n<code>/access YOUR_KEY_HERE</code>"
        bot.send_message(m.chat.id, msg, parse_mode="HTML")
        return

    text = m.text
    if "Discover" in text or "Main Menu" in text:
        msg = f"{E_WELCOME} <b>Welcome to Formula-X Resell Bot!</b>\n\n"
        msg += f"{E_OUTLINE} <b>Outline VPN</b> – Instant keys for lightweight, reliable VPN access.\n"
        msg += f"{E_HIDDIFY} <b>Hiddify / V2Ray</b> – Vless configs for unlimited devices.\n"
        msg += f"{E_CAPCUT} <b>CapCut</b> – Team 1 month plan.\n"
        msg += f"{E_ALIGHT} <b>Alight Motion</b> – Private 1 year (email + inbox link).\n"
        msg += f"{E_CHATGPT} <b>ChatGPT</b> – 1 month account upgrade.\n"
        msg += f"{E_GROK} <b>Grok</b> – Super 7 days plan.\n"
        msg += f"{E_YOUTUBE} <b>YouTube</b> – Premium Individual 1 month.\n"
        msg += f"{E_ZOOM} <b>Zoom</b> – 100 participants | 28 days.\n\n"
        msg += f"Choose an option below {E_DOWN}"
        send_styled(m.chat.id, msg, get_main_menu(uid))
        
    elif "Contact" in text:
        msg = "<b>Contact Admin</b>\nNeed help? Reach out anytime:\n@FORMULA_X0"
        send_styled(m.chat.id, msg, contact_admin_kb())
        
    elif "My Info" in text:
        db = load_db(USERS_FILE)
        joined = db.get(str(uid), {}).get("joined", "Unknown")
        history = load_db(HISTORY_FILE).get(str(uid), [])
        recent_lines = []
        for item in history:
            if isinstance(item, dict) and item.get("status") == "confirmed":
                recent_lines.append(f"• {item.get('desc', 'Unknown Item')} - confirmed")
            elif isinstance(item, str) and "confirmed" in item.lower():
                recent_lines.append(item)
                
        history_text = "\n".join(recent_lines[-10:]) if recent_lines else "No recent orders."
        msg = f"{E_MYINFO} <b>My Info</b>\n\n<b>Name:</b> {m.from_user.first_name}\n<b>ID:</b> <code>{uid}</code>\n<b>Joined at:</b> {joined}\n\n<b>Recent Orders:</b>\n{history_text}"
        send_styled(m.chat.id, msg, contact_admin_kb())
        
    elif "History" in text:
        history = load_db(HISTORY_FILE).get(str(uid), [])
        history_lines = []
        for item in reversed(history): 
            if isinstance(item, dict):
                history_lines.append(f"• #{item.get('oid', 'N/A')} {item.get('desc', 'Unknown')} – {item.get('status', 'unknown')} – {item.get('date', '')}")
            else:
                history_lines.append(str(item))
                
        history_text = "\n".join(history_lines[:15]) if history_lines else "No orders found yet."
        msg = f"{E_ORDER} <b>Order History</b>\n\n{history_text}"
        send_styled(m.chat.id, msg, contact_admin_kb())
        
    elif "Help" in text:
        msg = f"{E_QUESTION} <b>Help</b>\n\n"
        msg += f"{E_OUTLINE} <b>Outline VPN</b> – Instant keys for lightweight, reliable VPN access.\n"
        msg += f"{E_HIDDIFY} <b>Hiddify / V2Ray</b> – Vless configs for unlimited devices.\n"
        msg += f"{E_CAPCUT} <b>CapCut</b> – Team plan (pay → screenshot)\n"
        msg += f"{E_ALIGHT} <b>Alight Motion</b> – Private 1 year (pay → screenshot)\n"
        msg += f"{E_CHATGPT} <b>ChatGPT</b> – 1 month account upgrade\n"
        msg += f"{E_GROK} <b>Grok</b> – Super 7 days (pay → screenshot)\n"
        msg += f"{E_YOUTUBE} <b>YouTube</b> – Premium Individual 1 month (pay → screenshot)\n"
        msg += f"{E_ZOOM} <b>Zoom</b> – 100p | 28 days (pay → screenshot)\n\n"
        msg += "Choose a product → Select plan → Pay → Send payment screenshot.\n\n"
        msg += "<b>Payment:</b> Transfer to the Wave Pay or KPay account shown. Then send a screenshot of the payment confirmation. Your order is verified automatically.\n\n"
        msg += "<b>Support:</b> Contact @FORMULA_X0 if you have questions."
        send_styled(m.chat.id, msg, contact_admin_kb())

@bot.callback_query_handler(func=lambda call: True)
def query_handler(call):
    try: bot.answer_callback_query(call.id)
    except: pass
    
    uid, cid, mid = call.from_user.id, call.message.chat.id, call.message.message_id
    data = call.data

    if not check_access(uid) and not data.startswith("admin_"): return

    if data.startswith("prod_") and data not in ["prod_out", "prod_hid"]:
        stock_map = {
            "prod_capcut": ["capcut"],
            "prod_alight": ["alight"],
            "prod_youtube": ["youtube"],
            "prod_zoom": ["zoom"],
            "prod_chatgpt": ["chatgpt_plus", "chatgpt_renew", "chatgpt_biz"],
            "prod_spotify": ["spotify_2", "spotify_3"],
            "prod_grok": ["grok_7", "grok_15"],
            "prod_gemini": ["gemini_pro", "gemini_veo"]
        }
        if data in stock_map:
            keys = stock_map[data]
            db = load_db(STOCK_FILE)
            if all(len(db.get(k, [])) == 0 for k in keys):
                text = f"⚠️ <b>Out of Stock!</b>\nThis item is currently out of stock.\n\nPlease contact admin to purchase."
                send_styled(cid, text, contact_admin_kb("back_home"), mid)
                return

    if data == "back_home":
        send_styled(cid, f"{E_STORE} <b>Discover our products:</b>", get_main_menu(uid), mid)
        
    elif data == "out_of_stock":
        text = f"⚠️ <b>Out of Stock!</b>\nThis item is currently out of stock.\n\nPlease contact admin to purchase."
        send_styled(cid, text, contact_admin_kb("back_home"), mid)

    elif data == "prod_out":
        kb = {"inline_keyboard": [[{"text": "🇸🇬 Singapore", "callback_data": "srv_out_sg"}], [{"text": "🇺🇸 USA", "callback_data": "srv_out_us"}], [{"text": "Back", "callback_data": "back_home", "icon_custom_emoji_id": E_BACK_ID, "style": "danger"}]]}
        send_styled(cid, f"{E_OUTLINE} <b>Select Outline VPN Server:</b>", kb, mid)

    elif data == "prod_hid":
        kb = {"inline_keyboard": [[{"text": "🇸🇬 Singapore", "callback_data": "srv_hid_sg"}], [{"text": "Back", "callback_data": "back_home", "icon_custom_emoji_id": E_BACK_ID, "style": "danger"}]]}
        send_styled(cid, f"{E_HIDDIFY} <b>Select Hiddify Server:</b>", kb, mid)

    elif data == "prod_capcut":
        kb = {"inline_keyboard": [[{"text": "Team | 35 Days | 5500 MMK", "callback_data": "buy_acc_capcut_5500"}], [{"text": "Back", "callback_data": "back_home", "icon_custom_emoji_id": E_BACK_ID, "style": "danger"}]]}
        send_styled(cid, f"{E_CAPCUT} <b>CapCut Premium:</b>", kb, mid)

    elif data == "prod_alight":
        kb = {"inline_keyboard": [[{"text": "Private - 1 Year | 5,000 MMK", "callback_data": "buy_acc_alight_5000"}], [{"text": "Back", "callback_data": "back_home", "icon_custom_emoji_id": E_BACK_ID, "style": "danger"}]]}
        send_styled(cid, f"{E_ALIGHT} <b>Alight Motion:</b>", kb, mid)

    elif data == "prod_chatgpt":
        kb = {"inline_keyboard": [
            [{"text": "Plus 1 Month | 20000 MMK", "callback_data": "buy_acc_chatgpt_plus_20000"}],
            [{"text": "Plus Renew 1 Month | 35000 MMK", "callback_data": "buy_acc_chatgpt_renew_35000"}],
            [{"text": "BUSINESS 1 Month | 25000 MMK", "callback_data": "buy_acc_chatgpt_biz_25000"}],
            [{"text": "Back", "callback_data": "back_home", "icon_custom_emoji_id": E_BACK_ID, "style": "danger"}]
        ]}
        text = f"{E_CHATGPT} <b>Select a plan:</b>\n\n• <b>Plus & Plus Renew:</b> Private, Full Warranty.\n• <b>Business:</b> Private, 1 Time Replacement."
        send_styled(cid, text, kb, mid)
        
    elif data == "prod_spotify":
        kb = {"inline_keyboard": []}
        db = load_db(STOCK_FILE)
        text = f"{E_SPOTIFY} <b>Select a Spotify plan:</b>\n\n"
        for prod, duration, price, title in [("spotify_2", 60, 9000, "2 Months Individual"), ("spotify_3", 90, 13500, "3 Months Individual")]:
            stock = db.get(prod, [])
            if stock:
                acc = stock[0]
                ts = acc.get("timestamp", time.time())
                days_passed = int((time.time() - ts) / 86400)
                days_left = max(0, duration - days_passed)
                text += f"• <b>{title}</b>\n  {E_PRICE} {price:,} MMK • {E_DAYS} {days_left} days left\n\n"
                kb["inline_keyboard"].append([{"text": f"Buy {title} - {price:,} MMK", "callback_data": f"buy_acc_{prod}_{price}"}])
            else:
                text += f"• <b>{title}</b>\n  ❌ Out of Stock\n\n"
                kb["inline_keyboard"].append([{"text": f"{title} | Out of Stock", "callback_data": f"out_of_stock"}])
                
        kb["inline_keyboard"].append([{"text": "Back", "callback_data": "back_home", "icon_custom_emoji_id": E_BACK_ID, "style": "danger"}])
        send_styled(cid, text, kb, mid)

    elif data == "prod_gemini":
        kb = {"inline_keyboard": [
            [{"text": "Gemini Pro | 1 Year | 10,000 MMK", "callback_data": "buy_acc_gemini_pro_10000"}],
            [{"text": "Veo3 Ultra | 25K Credit | 16,000 MMK", "callback_data": "buy_acc_gemini_veo_16000"}],
            [{"text": "Back", "callback_data": "back_home", "icon_custom_emoji_id": E_BACK_ID, "style": "danger"}]
        ]}
        send_styled(cid, f"{E_GEMINI} <b>Select Gemini Plan:</b>", kb, mid)

    elif data == "prod_zoom":
        kb = {"inline_keyboard": [[{"text": "100p | 28 Days | 8,000 MMK", "callback_data": "buy_acc_zoom_8000"}], [{"text": "Back", "callback_data": "back_home", "icon_custom_emoji_id": E_BACK_ID, "style": "danger"}]]}
        send_styled(cid, f"{E_ZOOM} <b>Zoom Premium:</b>", kb, mid)

    elif data == "prod_grok":
        kb = {"inline_keyboard": [[{"text": "Super 7 Days | 4,000 MMK", "callback_data": "buy_acc_grok_7_4000"}], [{"text": "Super 15 Days | 8,000 MMK", "callback_data": "buy_acc_grok_15_8000"}], [{"text": "Back", "callback_data": "back_home", "icon_custom_emoji_id": E_BACK_ID, "style": "danger"}]]}
        send_styled(cid, f"{E_GROK} <b>Grok Select Plan:</b>", kb, mid)

    elif data == "prod_youtube":
        kb = {"inline_keyboard": [[{"text": "Premium Individual 1 Month | 8,000 MMK", "callback_data": "buy_acc_youtube_8000"}], [{"text": "Back", "callback_data": "back_home", "icon_custom_emoji_id": E_BACK_ID, "style": "danger"}]]}
        send_styled(cid, f"{E_YOUTUBE} <b>YouTube Premium:</b>", kb, mid)

    elif data == "admin_stock_btn" and uid == ADMIN_ID:
        prods = [
            ("CapCut", "capcut", "5364339557712020484"), ("Alight Motion", "alight", E_ALIGHT_ID), 
            ("Gemini Pro", "gemini_pro", E_GEMINI_ID), ("Gemini Veo", "gemini_veo", E_GEMINI_ID), 
            ("Zoom", "zoom", E_ZOOM_ID), ("Grok 7D", "grok_7", E_GROK_ID), 
            ("Grok 15D", "grok_15", E_GROK_ID), ("YouTube", "youtube", E_YOUTUBE_ID),
            ("CGPT Plus", "chatgpt_plus", E_CHATGPT_ID), ("CGPT Renew", "chatgpt_renew", E_CHATGPT_ID),
            ("CGPT Biz", "chatgpt_biz", E_CHATGPT_ID), ("Spotify 2M", "spotify_2", E_SPOTIFY_ID),
            ("Spotify 3M", "spotify_3", E_SPOTIFY_ID)
        ]
        kb = {"inline_keyboard": [[{"text": n, "callback_data": f"astk_{p}", "icon_custom_emoji_id": e}] for n, p, e in prods] + [[{"text": "Back", "callback_data": "back_home", "icon_custom_emoji_id": E_BACK_ID, "style": "danger"}]]}
        send_styled(cid, "<b>Admin: Select product to add stock:</b>", kb, mid)

    elif data == "admin_vis_btn" and uid == ADMIN_ID:
        prods = [
            ("Outline", "out", E_OUTLINE_ID), ("Hiddify", "hid", E_HIDDIFY_ID), 
            ("CapCut", "capcut", "5364339557712020484"), ("Alight", "alight", E_ALIGHT_ID), 
            ("ChatGPT", "chatgpt", E_CHATGPT_ID), ("Spotify", "spotify", E_SPOTIFY_ID), 
            ("Grok", "grok", E_GROK_ID), ("Gemini", "gemini", E_GEMINI_ID), 
            ("YouTube", "youtube", E_YOUTUBE_ID), ("Zoom", "zoom", E_ZOOM_ID)
        ]
        kb = {"inline_keyboard": []}
        for n, p, e in prods:
            status = "🔴 Hidden" if is_hidden(p) else "🟢 Visible"
            kb["inline_keyboard"].append([{"text": f"{n} [{status}]", "callback_data": f"tvis_{p}", "icon_custom_emoji_id": e}])
        kb["inline_keyboard"].append([{"text": "Back", "callback_data": "back_home", "icon_custom_emoji_id": E_BACK_ID, "style": "danger"}])
        send_styled(cid, f"{tg_emoji(E_HIDE_ID, '👁‍🗨')} <b>Manage Visibility:</b>\nClick to toggle Hide/Show", kb, mid)

    elif data.startswith("tvis_") and uid == ADMIN_ID:
        p = data.split("_")[1]
        toggle_visibility(p)
        query_handler(types.CallbackQuery(id=call.id, from_user=call.from_user, data="admin_vis_btn", chat_instance=call.chat_instance, message=call.message, json_string=""))

    elif data.startswith("astk_") and uid == ADMIN_ID:
        p = data.split("_", 1)[1]
        sent = bot.send_message(cid, f"✍️ Send account details for <b>{p.upper()}</b>\n(Email and Password will be auto-formatted beautifully):", parse_mode="HTML")
        bot.register_next_step_handler(sent, process_stock, p)

    elif data.startswith("srv_"):
        parts = data.split("_")
        prod_type = parts[1]
        server = parts[2]
        
        icon = E_OUTLINE if prod_type == "out" else E_HIDDIFY
        name = "Outline VPN" if prod_type == "out" else "Hiddify / V2Ray"
        flag = "🇸🇬" if server == "sg" else "🇺🇸"
        srv_name = "Singapore" if server == "sg" else "USA"
        
        text = f"{icon} <b>{name} - {flag} {srv_name}</b>\n\nSelect a plan:"
        kb = {"inline_keyboard": [
            [{"text": "50 GB | 1,500 MMK | 1 Month", "callback_data": f"plan_{prod_type}_{server}_50"}],
            [{"text": "100 GB | 3,000 MMK | 1 Month", "callback_data": f"plan_{prod_type}_{server}_100"}],
            [{"text": "150 GB | 4,000 MMK | 1 Month", "callback_data": f"plan_{prod_type}_{server}_150"}],
            [{"text": "200 GB | 5,000 MMK | 1 Month", "callback_data": f"plan_{prod_type}_{server}_200"}],
            [{"text": "Back", "callback_data": f"prod_{'out' if prod_type == 'out' else 'hid'}", "icon_custom_emoji_id": E_BACK_ID, "style": "danger"}]
        ]}
        send_styled(cid, text, kb, mid)

    elif data.startswith("plan_"):
        parts = data.split("_")
        prod_type = parts[1]
        server = parts[2]
        gb_val = int(parts[3])
        sent = bot.send_message(cid, "✍️ <b>Please type the quantity you want to buy (e.g., 5):</b>", parse_mode="HTML")
        bot.register_next_step_handler(sent, process_vpn_qty, prod_type, server, gb_val)

    elif data.startswith("buy_acc_"):
        stripped = data[8:]
        last_us_idx = stripped.rfind('_')
        prod = stripped[:last_us_idx]
        price = int(stripped[last_us_idx+1:])
        
        if not get_stock(prod):
            text = f"⚠️ <b>Out of Stock!</b>\nThis item is currently out of stock.\n\nPlease contact admin to purchase."
            send_styled(cid, text, contact_admin_kb("back_home"), mid)
            return

        oid = ''.join(random.choices(string.digits, k=5))
        pending = load_db(PENDING_FILE)
        pending[oid] = {"uid": uid, "product": prod, "total": price, "qty": 1, "gb": 0, "server": "none"}
        save_db(PENDING_FILE, pending)
        
        kb = {"inline_keyboard": [
            [{"text": "Wave Pay", "callback_data": f"pay_wav_{oid}", "icon_custom_emoji_id": E_WAVE_ID}],
            [{"text": "KPay", "callback_data": f"pay_kpy_{oid}", "icon_custom_emoji_id": E_KPAY_ID}],
            [{"text": "Cancel Order", "callback_data": "back_home", "icon_custom_emoji_id": E_BACK_ID, "style": "danger"}]
        ]}
        
        icon = PROD_INFO.get(prod, (E_STORE, "Product", ""))[0]
        prod_name = PROD_INFO.get(prod, (E_STORE, prod.replace('_', ' ').title(), ""))[1]
        plan_desc = PROD_INFO.get(prod, (E_STORE, "", ""))[2]
        
        summary = f"{tg_emoji('4960766907113276588', '📦')} <b>Order Summary</b>\n\n"
        if plan_desc:
            summary += f"{icon} {prod_name} - {plan_desc}\n"
        else:
            summary += f"{icon} {prod_name}\n"
        summary += f"{tg_emoji('5823347218056221496', '📦')} Quantity: 1\n"
        summary += f"{E_PRICE} Total: <b>{price:,} MMK</b>\n"
        summary += f"{tg_emoji('5841276284155467413', '🆔')} Order ID: #{oid}\n\n"
        summary += f"Select Payment Method:"
        
        send_styled(cid, summary, kb, mid)

    elif data.startswith("pay_"):
        parts = data.split("_")
        method = parts[1]
        oid = parts[-1]
        
        pending = load_db(PENDING_FILE)
        if oid not in pending: return
        order = pending[oid]
        prod_type = order['product']
        total = order['total']

        bank_logo = E_WAVE if method == "wav" else E_KPAY
        bank_name = "Wave Pay" if method == "wav" else "KPay"
        
        if prod_type == "out": 
            icon, prod_name, plan_desc = E_OUTLINE, "Outline VPN", f"{order['gb']} GB | 1 Month"
        elif prod_type == "hid": 
            icon, prod_name, plan_desc = E_HIDDIFY, "Hiddify / V2Ray", f"{order['gb']} GB | 1 Month"
        else:
            info = PROD_INFO.get(prod_type, (E_STORE, prod_type.replace('_', ' ').title(), ""))
            icon, prod_name, plan_desc = info[0], info[1], info[2]
            
        summary = f"{icon} {order['qty']}x {prod_name}"
        if plan_desc:
            summary += f" - {plan_desc}"
        summary += f"\n{E_PRICE} Price: <b>{total:,} MMK</b>\n"
        summary += f"{tg_emoji('5841276284155467413', '🆔')} Order ID: #{oid}\n\n"
        summary += f"{bank_logo} Pay via {bank_name}\n\n"
        summary += f"{tg_emoji('5407025283456835913', '📱')} Account: <code>09770088206</code>\n"
        summary += f"{tg_emoji('5258011929993026890', '👤')} Name: Myat Min Lwin\n"
        summary += f"{tg_emoji('5801018335919347111', '📌')} Note: Payment\n\n"
        summary += f"{tg_emoji('5258205968025525531', '📸')} Please send your payment screenshot to complete the order."
        
        kb = {"inline_keyboard": [[{"text": "Cancel Order", "callback_data": "back_home", "icon_custom_emoji_id": E_BACK_ID, "style": "danger"}]]}
        send_styled(cid, summary, kb, mid)

    elif data.startswith("approve_"):
        bot.edit_message_reply_markup(cid, mid, reply_markup=None)
        oid = call.data.split("_")[1]
        pending = load_db(PENDING_FILE)
        if oid not in pending: return
        
        order = pending[oid]
        bot.edit_message_caption(f"⌛ <b>Processing Order #{oid}...</b>", cid, mid, parse_mode="HTML")
        
        prod_type = order.get('product')
        tz = pytz.timezone('Asia/Yangon')
        date_str = datetime.now(tz).strftime('%Y-%m-%d')
        
        if prod_type in ["out", "hid"]:
            srv_key = f"{prod_type}_{order.get('server', 'sg')}"
            if prod_type == "out":
                links = generate_outline_keys(order['server'], order['gb'], order['qty'])
                if len(links) == order['qty']:
                    links_text = "\n\n".join([f"{E_LINK} Link {i+1}:\n<code>{l}</code>" for i, l in enumerate(links)])
                    success_msg = f"{tg_emoji('5206607081334906820', '✅')} <b>Order confirmed!</b>\n\nHere are your Outline VPN keys:\n\n{links_text}\n\n{E_BULB} <b>How to use:</b>\n1. Copy key.\n2. Open Outline App.\n3. Click {E_PLUS} to add server."
                    bot.send_message(order['uid'], success_msg, parse_mode="HTML")
                    bot.send_message(order['uid'], f"{tg_emoji('5206607081334906820', '✅')} <b>Payment Verified!</b>\nPlease check the above message for your keys.", parse_mode="HTML")
                    bot.edit_message_caption(f"{tg_emoji('5206607081334906820', '✅')} <b>DELIVERED:</b> Order #{oid}\nOutline keys sent.", cid, mid, parse_mode="HTML")
                    add_server_usage(srv_key, order['gb'] * order['qty'])
                    update_order_history(order['uid'], oid, "confirmed")
                    del pending[oid]
                else:
                    bot.send_message(ADMIN_ID, f"⚠️ Error: API failed for Order #{oid}.")
            else:
                links = generate_3xui_keys(30, order['gb'], order['uid'], order['qty'])
                if len(links) == order['qty']:
                    links_text = "\n\n".join([f"{E_LINK} Link {i+1}:\n<code>{l}</code>" for i, l in enumerate(links)])
                    success_msg = f"{tg_emoji('5206607081334906820', '✅')} <b>Order confirmed!</b>\n\nHere are your Hiddify/V2Ray links:\n{links_text}\n\n{E_BULB} <b>How to use:</b>\n1. Copy link.\n2. Open Hiddify App.\n3. Click {E_PLUS} and Add from Clipboard."
                    bot.send_message(order['uid'], success_msg, parse_mode="HTML")
                    bot.send_message(order['uid'], f"{tg_emoji('5206607081334906820', '✅')} <b>Payment Verified!</b>\nPlease check the above message for your links.", parse_mode="HTML")
                    bot.edit_message_caption(f"{tg_emoji('5206607081334906820', '✅')} <b>DELIVERED:</b> Order #{oid}\nHiddify keys sent.", cid, mid, parse_mode="HTML")
                    add_server_usage(srv_key, order['gb'] * order['qty'])
                    update_order_history(order['uid'], oid, "confirmed")
                    del pending[oid]
                else:
                    bot.send_message(ADMIN_ID, f"⚠️ Error: API failed for Order #{oid}.")
                    
        else:
            acc = pop_stock(prod_type)
            if not acc:
                bot.send_message(ADMIN_ID, f"❌ <b>OUT OF STOCK!</b>\nCannot deliver {prod_type} for Order #{oid}. Please manually send to user <code>{order['uid']}</code>.", parse_mode="HTML")
                bot.edit_message_caption(f"❌ <b>FAILED:</b> Out of Stock for Order #{oid}.", cid, mid, parse_mode="HTML")
                return
            
            info = PROD_INFO.get(prod_type, (E_STORE, prod_type.replace('_', ' ').title(), ""))
            icon, prod_name, plan_desc = info[0], info[1], info[2]
            
            acc_formatted = format_acc_details(acc['data'])
            text = f"{tg_emoji('5206607081334906820', '✅')} <b>Order confirmed!</b>\n\n"
            text += f"{icon} <b>{prod_name} — {plan_desc}</b>\n"
            text += f"{tg_emoji('5841276284155467413', '🆔')} Order ID: #{oid}\n\n"
            text += f"<b>Your account:</b>\n{acc_formatted}\n\n"
            
            markup = {"inline_keyboard": []}

            if prod_type == "capcut":
                text += f"<b>Instructions:</b>\n• Sign in to CapCut with Email & Password.\n• Allowed: 4 Devices 📱\n• Auto-renews every 7 days (5 times).\n• ⚠️ <b>Do NOT change Password</b>"
            elif prod_type == "alight":
                text += f"<b>Instructions:</b>\n• Open Alight Motion ➔ Sign in.\n• Choose 'Sign in with email' & enter the Email.\n• Open Inbox via button below for the login link."
                email_match = re.search(r'[\w\.-]+@[\w\.-]+', acc['data'])
                if email_match:
                    markup["inline_keyboard"].append([{"text": "Mail Access 📥", "url": f"https://generator.email/{email_match.group(0)}"}])
            elif "spotify" in prod_type:
                text += f"<b>Instructions:</b>\n• Open Spotify App.\n• Sign in with the credentials above.\n• ⚠️ Keep credentials private. Do not change password."
            elif "chatgpt" in prod_type:
                text += f"<b>Instructions:</b>\n• Go to chatgpt.com or use the App.\n• Login using the provided details.\n• ⚠️ Do not change any settings."
            elif "grok" in prod_type:
                text += f"<b>Instructions:</b>\n• Sign in with the credentials above.\n• ⚠️ <b>Do NOT change Mail & Password</b>."
            else:
                text += f"<b>Instructions:</b>\n• Sign in with the credentials above.\n• Use within agreed terms."

            markup["inline_keyboard"].append([{"text": "Contact Admin (if problem)", "url": "https://t.me/FORMULA_X0", "icon_custom_emoji_id": "5458603043203327669"}])
            
            bot.send_message(order['uid'], text, reply_markup=json.dumps(markup), parse_mode="HTML")
            bot.send_message(order['uid'], f"{tg_emoji('5206607081334906820', '✅')} <b>Payment Verified!</b>\nPlease check the above message for your account details.", parse_mode="HTML")
            
            bot.edit_message_caption(f"{tg_emoji('5206607081334906820', '✅')} <b>DELIVERED:</b> Order #{oid}\n{prod_name} details sent.", cid, mid, parse_mode="HTML")
            update_order_history(order['uid'], oid, "confirmed")
            del pending[oid]

        save_db(PENDING_FILE, pending)

    elif data.startswith("reject_") or data.startswith("rjw_"):
        bot.edit_message_reply_markup(cid, mid, reply_markup=None)
        if data.startswith("reject_"):
            oid = data.split("_")[1]
            pending = load_db(PENDING_FILE)
            if oid in pending:
                uid_to_notify = pending[oid]['uid']
                del pending[oid]
                save_db(PENDING_FILE, pending)
                bot.send_message(uid_to_notify, "❌ <b>Payment Rejected</b>\n\nYour payment slip was invalid or incomplete. Please contact the admin for support.", parse_mode="HTML")
                update_order_history(uid_to_notify, oid, "cancelled")
        else:
            uid_to_notify = data.split("_")[1]
            bot.send_message(uid_to_notify, "❌ <b>Payment Rejected</b>\n\nYour web order payment slip was invalid or incomplete. Please contact the admin for support.", parse_mode="HTML")
        
        caption = call.message.caption or ""
        new_caption = caption + "\n\n❌ <b>ORDER REJECTED</b>"
        bot.edit_message_caption(new_caption, cid, mid, parse_mode="HTML")

def process_vpn_qty(message, prod_type, server, gb_val):
    try:
        qty_str = message.text.strip()
        if not qty_str.isdigit():
            sent = bot.send_message(message.chat.id, "⚠️ Invalid input. Enter a number:", parse_mode="HTML")
            bot.register_next_step_handler(sent, process_vpn_qty, prod_type, server, gb_val)
            return
            
        qty = int(qty_str)
        if qty <= 0: raise ValueError
        
        srv_key = f"{prod_type}_{server}"
        current_usage = get_server_usage(srv_key)
        
        if (current_usage + (gb_val * qty)) > MAX_LIMIT_GB:
            remaining = MAX_LIMIT_GB - current_usage
            bot.send_message(message.chat.id, f"⚠️ <b>Out of Stock!</b>\nServer limit reached. Remaining: {remaining} GB.", parse_mode="HTML")
            return

        prices = {50: 1500, 100: 3000, 150: 4000, 200: 5000}
        total = prices[gb_val] * qty
        oid = ''.join(random.choices(string.digits, k=5))
        
        pending = load_db(PENDING_FILE)
        pending[oid] = {"uid": message.chat.id, "product": prod_type, "server": server, "gb": gb_val, "qty": qty, "total": total}
        save_db(PENDING_FILE, pending)
        
        kb = {"inline_keyboard": [
            [{"text": "Wave Pay", "callback_data": f"pay_wav_{oid}", "icon_custom_emoji_id": E_WAVE_ID}],
            [{"text": "KPay", "callback_data": f"pay_kpy_{oid}", "icon_custom_emoji_id": E_KPAY_ID}],
            [{"text": "Cancel Order", "callback_data": "back_home", "icon_custom_emoji_id": E_BACK_ID, "style": "danger"}]
        ]}
        
        icon = E_OUTLINE if prod_type == "out" else E_HIDDIFY
        prod_name = "Outline VPN" if prod_type == "out" else "Hiddify / V2Ray"
        
        summary = f"{tg_emoji('4960766907113276588', '📦')} <b>Order Summary</b>\n\n"
        summary += f"{icon} {prod_name} - {gb_val} GB | 1 Month\n"
        summary += f"{tg_emoji('5823347218056221496', '📦')} Quantity: {qty}\n"
        summary += f"{E_PRICE} Total: <b>{total:,} MMK</b>\n"
        summary += f"{tg_emoji('5841276284155467413', '🆔')} Order ID: #{oid}\n\n"
        summary += f"Select Payment Method:"
        
        send_styled(message.chat.id, summary, kb)
    except:
        bot.send_message(message.chat.id, "⚠️ Invalid quantity.", parse_mode="HTML")

def process_stock(m, p):
    db = load_db(STOCK_FILE)
    if p not in db: db[p] = []
    
    db[p].append({
        "data": m.text,
        "timestamp": time.time()
    })
    
    save_db(STOCK_FILE, db) 
    bot.reply_to(m, f"✅ Stock successfully added to <b>{p.upper()}</b>.\nTotal Available: {len(db[p])}", parse_mode="HTML")

@bot.message_handler(content_types=['photo'])
def handle_payment_slip(message):
    uid = message.from_user.id
    if not check_access(uid): return
    
    pending = load_db(PENDING_FILE)
    user_orders = [oid for oid, val in pending.items() if val.get('uid') == uid]
    if not user_orders:
        return 
        
    order_id = user_orders[-1]
    
    for old_oid in user_orders[:-1]:
        del pending[old_oid]
    save_db(PENDING_FILE, pending)

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Approve", callback_data=f"approve_{order_id}"), 
        types.InlineKeyboardButton("❌ Reject", callback_data=f"reject_{order_id}")
    )
    
    order = pending[order_id]
    prod_type = order.get('product', '')
    
    if prod_type == "out":
        srv_name = "Singapore" if order.get('server') == 'sg' else "USA"
        prod_desc = f"Outline {srv_name} {order.get('gb', 0)}GB 1mo"
    elif prod_type == "hid":
        srv_name = "Singapore" if order.get('server') == 'sg' else "USA"
        prod_desc = f"Hiddify {srv_name} {order.get('gb', 0)}GB 1mo"
    else:
        prod_desc_raw = PROD_INFO.get(prod_type, ("", prod_type.title(), ""))[1]
        prod_desc = f"{prod_desc_raw}"
        if 'total' in order:
            prod_desc += f" {order['total']:,} MMK"

    caption = f"{tg_emoji('5458603043203327669', '🔔')} <b>New Payment Slip!</b>\n\n{tg_emoji('5841276284155467413', '🆔')} Order: #{order_id}\n{tg_emoji('5258011929993026890', '👤')} User: <code>{uid}</code>\n{tg_emoji('5409048419211682843', '💰')} Total: {order['total']:,} MMK\n{tg_emoji('4960766907113276588', '📦')} Product: {prod_desc} (Qty: {order['qty']})"
    
    bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=caption, reply_markup=markup, parse_mode="HTML")
    bot.reply_to(message, "⏳ <b>Verifying your receipt...</b>\nPlease wait a moment while the admin checks your payment.", parse_mode="HTML")
    
    tz = pytz.timezone('Asia/Yangon')
    date_str = datetime.now(tz).strftime('%Y-%m-%d')
    add_order_history(uid, order_id, prod_desc, "pending", date_str)

if __name__ == "__main__":
    while True:
        try:
            bot.infinity_polling(timeout=20, long_polling_timeout=15)
        except Exception as e:
            time.sleep(3)