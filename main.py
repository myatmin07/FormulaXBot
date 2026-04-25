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
    if not os.path.exists(file): return {}
    with open(file, "r", encoding="utf-8") as f:
        try: return json.load(f)
        except: return {}

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
    acc = db[prod].pop(0) # Pop the first item permanently
    save_db(STOCK_FILE, db)
    return acc

def add_user(uid, name):
    db = load_db(USERS_FILE)
    if str(uid) not in db:
        db[str(uid)] = {"name": name, "joined": datetime.now(pytz.timezone('Asia/Yangon')).strftime("%Y-%m-%d")}
        save_db(USERS_FILE, db)

def add_history(uid, record):
    db = load_db(HISTORY_FILE)
    if str(uid) not in db: db[str(uid)] = []
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

# --- Raw API Request for UI ---
def send_styled(chat_id, text, kb_json, mid=None):
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML", "reply_markup": json.dumps(kb_json), "disable_web_page_preview": True}
    url = f"https://api.telegram.org/bot{API_TOKEN}/editMessageText" if mid else f"https://api.telegram.org/bot{API_TOKEN}/sendMessage"
    if mid: payload["message_id"] = mid
    return requests.post(url, data=payload)

# --- Keyboards ---
def get_main_menu(uid):
    rows = []
    
    if not is_hidden("out"): rows.append([{"text": "Outline VPN", "callback_data": "prod_out", "icon_custom_emoji_id": E_OUTLINE_ID, "style": "success"}])
    if not is_hidden("hid"): rows.append([{"text": "Hiddify / V2Ray", "callback_data": "prod_hid", "icon_custom_emoji_id": E_HIDDIFY_ID, "style": "primary"}])
    
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
    except: return []

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
            if res.json().get('success'): sub_links.append(f"{SUB_URL_BASE}{sub_id}")
            time.sleep(0.5)
        return sub_links
    except: return []

def get_current_usage():
    data = load_db(USAGE_FILE)
    return data.get("total_sold_gb", 0)

def add_usage(gb):
    data = load_db(USAGE_FILE)
    data["total_sold_gb"] = data.get("total_sold_gb", 0) + gb
    save_db(USAGE_FILE, data)

# --- Handlers ---
@bot.message_handler(commands=['start'])
def start_cmd(m):
    add_user(m.from_user.id, m.from_user.first_name)
    tz = pytz.timezone('Asia/Yangon')
    now = datetime.now(tz).strftime("%A, %B %d")
    
    reply_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    reply_markup.add("🛍️ Discover Products", "🔔 Contact Admin")
    reply_markup.add("👤 My Info", "📊 Order History")
    
    caption = f"{m.from_user.first_name} — Hope your day is going smoothly\nYangon time: <i>{now}</i>.\n\n{E_TIP} <b>Tip:</b> Use the menu below your message box."
    
    # --- GitHub Raw Link Replaced Here ---
    img_url = "https://raw.githubusercontent.com/myatmin07/Formula/refs/heads/main/file_000000009dd0720899ff78779c7e1fd2.png"
    
    try:
        bot.send_photo(m.chat.id, img_url, caption=caption, parse_mode="HTML", reply_markup=reply_markup)
    except:
        bot.send_message(m.chat.id, caption, parse_mode="HTML", reply_markup=reply_markup)
        
    send_styled(m.chat.id, f"{E_STORE} <b>Discover our products:</b>", get_main_menu(m.from_user.id))

@bot.message_handler(func=lambda m: m.text in ["🛍️ Discover Products", "🔔 Contact Admin", "👤 My Info", "📊 Order History"])
def text_reply(m):
    uid = m.from_user.id
    if m.text == "🛍️ Discover Products":
        send_styled(m.chat.id, f"{E_STORE} <b>Discover our products:</b>", get_main_menu(uid))
    elif m.text == "🔔 Contact Admin":
        text = "<b>Contact Admin</b>\nNeed help? Reach out anytime:\n@FORMULA_X0"
        send_styled(m.chat.id, text, contact_admin_kb())
    elif m.text == "👤 My Info":
        db = load_db(USERS_FILE)
        joined = db.get(str(uid), {}).get("joined", "Unknown")
        text = f"{E_MYINFO} <b>My Info</b>\n\nName: {m.from_user.first_name}\nID: <code>{uid}</code>\nJoined Date: {joined}"
        send_styled(m.chat.id, text, contact_admin_kb())
    elif m.text == "📊 Order History":
        history = load_db(HISTORY_FILE).get(str(uid), [])
        text = f"{E_ORDER} <b>Order History</b>\n\n" + ("\n".join(history[-10:]) if history else "No orders found yet.")
        send_styled(m.chat.id, text, contact_admin_kb())

@bot.callback_query_handler(func=lambda call: True)
def query_handler(call):
    try: bot.answer_callback_query(call.id)
    except: pass
    
    uid, cid, mid = call.from_user.id, call.message.chat.id, call.message.message_id
    data = call.data

    if data == "back_home":
        send_styled(cid, f"{E_STORE} <b>Discover our products:</b>", get_main_menu(uid), mid)

    elif data == "prod_out":
        kb = {"inline_keyboard": [[{"text": "🇸🇬 Singapore", "callback_data": "srv_out_sg"}], [{"text": "🇺🇸 USA", "callback_data": "srv_out_us"}], [{"text": "Back", "callback_data": "back_home", "icon_custom_emoji_id": E_BACK_ID, "style": "danger"}]]}
        send_styled(cid, f"{E_OUTLINE} <b>Select Outline VPN Server:</b>", kb, mid)

    elif data == "prod_hid":
        kb = {"inline_keyboard": [[{"text": "🇸🇬 Singapore", "callback_data": "srv_hid_sg"}], [{"text": "Back", "callback_data": "back_home", "icon_custom_emoji_id": E_BACK_ID, "style": "danger"}]]}
        send_styled(cid, f"{E_HIDDIFY} <b>Select Hiddify Server:</b>", kb, mid)

    elif data == "prod_capcut":
        kb = {"inline_keyboard": [[{"text": "Team | 35Days | 5500 MMK", "callback_data": "buy_acc_capcut_5500"}], [{"text": "Back", "callback_data": "back_home", "icon_custom_emoji_id": E_BACK_ID, "style": "danger"}]]}
        send_styled(cid, f"{E_CAPCUT} <b>CapCut Premium:</b>", kb, mid)

    elif data == "prod_alight":
        kb = {"inline_keyboard": [[{"text": "Private - 1 Year | 5,000 MMK", "callback_data": "buy_acc_alight_5000"}], [{"text": "Back", "callback_data": "back_home", "icon_custom_emoji_id": E_BACK_ID, "style": "danger"}]]}
        send_styled(cid, f"{E_ALIGHT} <b>Alight Motion:</b>", kb, mid)

    elif data == "prod_chatgpt":
        kb = {"inline_keyboard": [
            [{"text": "Plus 1 Month | 2000 MMK", "callback_data": "buy_acc_chatgpt_plus_2000"}],
            [{"text": "Plus Renew 1 Month | 35000 MMK", "callback_data": "buy_acc_chatgpt_renew_35000"}],
            [{"text": "BUSINESS 1 Month | 25000 MMK", "callback_data": "buy_acc_chatgpt_biz_25000"}],
            [{"text": "Back", "callback_data": "back_home", "icon_custom_emoji_id": E_BACK_ID, "style": "danger"}]
        ]}
        text = f"{E_CHATGPT} <b>Select a plan:</b>\n\n"
        text += "• <b>Plus & Plus Renew:</b> Private, Full Warranty.\n"
        text += "• <b>Business:</b> Private, 1 Time Replacement."
        send_styled(cid, text, kb, mid)
        
    elif data == "prod_spotify":
        kb = {"inline_keyboard": [
            [{"text": "2 Month | Individual | 9000 MMK", "callback_data": "buy_acc_spotify_2_9000"}],
            [{"text": "3 Month | Individual | 13500 MMK", "callback_data": "buy_acc_spotify_3_13500"}],
            [{"text": "Back", "callback_data": "back_home", "icon_custom_emoji_id": E_BACK_ID, "style": "danger"}]
        ]}
        send_styled(cid, f"{E_SPOTIFY} <b>Select a plan:</b>", kb, mid)

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
            ("CapCut", "capcut", E_CAPCUT_ID), 
            ("Alight Motion", "alight", E_ALIGHT_ID), 
            ("Gemini Pro", "gemini_pro", E_GEMINI_ID), 
            ("Gemini Veo", "gemini_veo", E_GEMINI_ID), 
            ("Zoom", "zoom", E_ZOOM_ID), 
            ("Grok 7D", "grok_7", E_GROK_ID), 
            ("Grok 15D", "grok_15", E_GROK_ID), 
            ("YouTube", "youtube", E_YOUTUBE_ID),
            ("CGPT Plus", "chatgpt_plus", E_CHATGPT_ID),
            ("CGPT Renew", "chatgpt_renew", E_CHATGPT_ID),
            ("CGPT Biz", "chatgpt_biz", E_CHATGPT_ID),
            ("Spotify 2M", "spotify_2", E_SPOTIFY_ID),
            ("Spotify 3M", "spotify_3", E_SPOTIFY_ID)
        ]
        kb = {"inline_keyboard": [[{"text": n, "callback_data": f"astk_{p}", "icon_custom_emoji_id": e}] for n, p, e in prods] + [[{"text": "Back", "callback_data": "back_home", "icon_custom_emoji_id": E_BACK_ID, "style": "danger"}]]}
        send_styled(cid, "<b>Admin: Select product to add stock:</b>", kb, mid)

    elif data == "admin_vis_btn" and uid == ADMIN_ID:
        prods = [
            ("Outline", "out", E_OUTLINE_ID), ("Hiddify", "hid", E_HIDDIFY_ID), 
            ("CapCut", "capcut", E_CAPCUT_ID), ("Alight", "alight", E_ALIGHT_ID), 
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
        bot.answer_callback_query(call.id, f"Toggled {p} visibility")
        query_handler(types.CallbackQuery(id=call.id, from_user=call.from_user, data="admin_vis_btn", chat_instance=call.chat_instance, message=call.message, json_string=""))

    elif data.startswith("astk_") and uid == ADMIN_ID:
        p = data.split("_", 1)[1]
        sent = bot.send_message(cid, f"✍️ Send account for <b>{p.upper()}</b> (Format: <code>email:password</code>):", parse_mode="HTML")
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
            text = f"⚠️ <b>Out of Stock!</b>\n{prod.replace('_', ' ').title()} is currently out of stock.\n\nPlease contact admin to purchase."
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
        text = f"🛒 <b>Order Summary</b>\n\nProduct: {prod.replace('_', ' ').title()}\nPrice: <b>{price:,} MMK</b>\nOrder ID: #{oid}\n\nSelect Payment:"
        send_styled(cid, text, kb, mid)

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
        
        if prod_type == "out": icon, prod_name, plan_desc = E_OUTLINE, "Outline VPN", f"{order['gb']} GB | 1 Month"
        elif prod_type == "hid": icon, prod_name, plan_desc = E_HIDDIFY, "Hiddify / V2Ray", f"{order['gb']} GB | 1 Month"
        elif prod_type == "capcut": icon, prod_name, plan_desc = E_CAPCUT, "CapCut Team", "35 Days"
        elif prod_type == "alight": icon, prod_name, plan_desc = E_ALIGHT, "Alight Motion", "Private - 1 Year"
        elif prod_type == "gemini_pro": icon, prod_name, plan_desc = E_GEMINI, "Gemini Pro", "1 Year (1 Month Warranty)"
        elif prod_type == "gemini_veo": icon, prod_name, plan_desc = E_GEMINI, "Veo3 Ultra", "25K Credit (24 hr warranty)"
        elif prod_type == "zoom": icon, prod_name, plan_desc = E_ZOOM, "Zoom", "100p | 28 Days"
        elif prod_type == "grok_7": icon, prod_name, plan_desc = E_GROK, "Grok", "Super 7 Days"
        elif prod_type == "grok_15": icon, prod_name, plan_desc = E_GROK, "Grok", "Super 15 Days"
        elif prod_type == "youtube": icon, prod_name, plan_desc = E_YOUTUBE, "YouTube Premium", "Individual 1 Month"
        elif prod_type == "chatgpt_plus": icon, prod_name, plan_desc = E_CHATGPT, "ChatGPT Plus", "1 Month"
        elif prod_type == "chatgpt_renew": icon, prod_name, plan_desc = E_CHATGPT, "ChatGPT Plus Renew", "1 Month"
        elif prod_type == "chatgpt_biz": icon, prod_name, plan_desc = E_CHATGPT, "ChatGPT Business", "1 Month"
        elif prod_type == "spotify_2": icon, prod_name, plan_desc = E_SPOTIFY, "Spotify", "Individual 2 Months"
        elif prod_type == "spotify_3": icon, prod_name, plan_desc = E_SPOTIFY, "Spotify", "Individual 3 Months"
            
        text = f"{icon} <b>{prod_name}</b>\n\n"
        text += f"{E_STORE} {order['qty']}x {plan_desc}\n"
        text += f"{E_PRICE} Price: {total:,} MMK\n"
        text += f"{E_ORDER} Order ID: #{oid}\n\n"
        text += f"{bank_logo} Pay via {bank_name}\n\n"
        text += f"{tg_emoji('5407025283456835913', '📱')} Account: <code>09770088206</code>\n"
        text += f"{tg_emoji('5258011929993026890', '👤')} Name: Myat Min Lwin\n"
        text += f"{tg_emoji('5801018335919347111', '📌')} Note: Payment\n\n"
        text += f"{tg_emoji('5258205968025525531', '📸')} Please send your payment screenshot to complete the order."
        
        kb = {"inline_keyboard": [[{"text": "Cancel Order", "callback_data": "back_home", "icon_custom_emoji_id": E_BACK_ID, "style": "danger"}]]}
        send_styled(cid, text, kb, mid)

    elif data.startswith("approve_"):
        oid = call.data.split("_")[1]
        pending = load_db(PENDING_FILE)
        if oid not in pending: return
        
        order = pending[oid]
        bot.edit_message_caption(f"⌛ <b>Processing Order #{oid}...</b>", cid, mid, parse_mode="HTML")
        
        prod_type = order.get('product')
        tz = pytz.timezone('Asia/Yangon')
        date_str = datetime.now(tz).strftime('%Y-%m-%d')
        
        # --- VPN Delivery ---
        if prod_type in ["out", "hid"]:
            if prod_type == "out":
                links = generate_outline_keys(order['server'], order['gb'], order['qty'])
                if len(links) == order['qty']:
                    links_text = "\n\n".join([f"{E_LINK} Link {i+1}:\n<code>{l}</code>" for i, l in enumerate(links)])
                    success_msg = f"{E_VERIFIED} <b>Payment Received Successfully!</b>\n\nHere are your Outline VPN keys:\n\n{links_text}\n\n{E_BULB} <b>How to use:</b>\n1. Copy key.\n2. Open Outline App.\n3. Click {E_PLUS} to add server."
                    bot.send_message(order['uid'], success_msg, parse_mode="HTML")
                    bot.edit_message_caption(f"✅ <b>DELIVERED:</b> Order #{oid}\nOutline keys sent.", cid, mid, parse_mode="HTML")
                    add_usage(order['gb'] * order['qty'])
                    add_history(order['uid'], f"• #{oid} Outline VPN {order['gb']}GB - confirmed - {date_str}")
                    del pending[oid]
                else:
                    bot.send_message(ADMIN_ID, f"⚠️ Error: API failed for Order #{oid}.")
            else:
                links = generate_3xui_keys(30, order['gb'], order['uid'], order['qty'])
                if len(links) == order['qty']:
                    links_text = "\n\n".join([f"{E_LINK} Link {i+1}:\n<code>{l}</code>" for i, l in enumerate(links)])
                    success_msg = f"{E_VERIFIED} <b>Payment Received Successfully!</b>\n\nHere are your Hiddify/V2Ray links:\n{links_text}"
                    bot.send_message(order['uid'], success_msg, parse_mode="HTML")
                    bot.edit_message_caption(f"✅ <b>DELIVERED:</b> Order #{oid}\nHiddify keys sent.", cid, mid, parse_mode="HTML")
                    add_usage(order['gb'] * order['qty'])
                    add_history(order['uid'], f"• #{oid} Hiddify VPN {order['gb']}GB - confirmed - {date_str}")
                    del pending[oid]
                else:
                    bot.send_message(ADMIN_ID, f"⚠️ Error: API failed for Order #{oid}.")
                    
        # --- Accounts Delivery (1 Acc 1 User) ---
        else:
            acc = pop_stock(prod_type) # Ensures 1 Acc 1 User safely
            if not acc:
                bot.send_message(ADMIN_ID, f"❌ <b>OUT OF STOCK!</b>\nCannot deliver {prod_type} for Order #{oid}. Please manually send to user <code>{order['uid']}</code>.", parse_mode="HTML")
                bot.edit_message_caption(f"❌ <b>FAILED:</b> Out of Stock for Order #{oid}.", cid, mid, parse_mode="HTML")
                return

            titles = {
                "capcut": "CapCut Team plan access for 1 month",
                "alight": "Alight Motion Private access for 1 Year",
                "gemini_pro": "Gemini Pro for 1 Year",
                "gemini_veo": "Veo3 Ultra 25K Credit",
                "zoom": "Zoom 100p | 28 Days",
                "grok_7": "Grok Super 7 Days",
                "grok_15": "Grok Super 15 Days",
                "youtube": "YouTube Premium Individual 1 Month",
                "chatgpt_plus": "ChatGPT Plus 1 Month (Private, Full Warranty)",
                "chatgpt_renew": "ChatGPT Plus Renew 1 Month (Private, Full Warranty)",
                "chatgpt_biz": "ChatGPT Business 1 Month (Private, 1 Time Replacement)",
                "spotify_2": "Spotify Individual 2 Months",
                "spotify_3": "Spotify Individual 3 Months"
            }
            warranties = {"gemini_pro": "1 Month Warranty", "gemini_veo": "24 hour warranty"}
            
            text = f"<b>What you get:</b> {titles.get(prod_type, 'Premium Account')}\n"
            if warranties.get(prod_type): text += f"<i>({warranties[prod_type]})</i>\n"
            text += f"\n<b>Instructions:</b>\n"
            text += f"• Sign in with the email and password below.\n"
            
            if "capcut" in prod_type or "grok" in prod_type:
                text += f"• ⚠️ <b>Do not change Mail & Password</b>\n"
                
            text += f"• Use only within the terms you agreed with the seller.\n"
            text += f"• If something fails, tap Contact Admin below.\n\n"
            text += f"{E_EMAIL} <b>Email</b>\n<code>{acc['email']}</code>\n\n"
            text += f"{E_PASSWORD} <b>Password</b>\n<code>{acc['password']}</code>"
            
            send_styled(order['uid'], text, contact_admin_kb())
            time.sleep(0.5)
            bot.send_message(order['uid'], f"{E_VERIFIED} Payment verified! Check the message above for your account details.", parse_mode="HTML")
            
            bot.edit_message_caption(f"✅ <b>DELIVERED:</b> Order #{oid}\n{prod_type.replace('_', ' ').title()} Account details sent.", cid, mid, parse_mode="HTML")
            add_history(order['uid'], f"• #{oid} {prod_type.replace('_', ' ').title()} - confirmed - {date_str}")
            del pending[oid]

        save_db(PENDING_FILE, pending)

def process_vpn_qty(message, prod_type, server, gb_val):
    try:
        qty_str = message.text.strip()
        if not qty_str.isdigit():
            sent = bot.send_message(message.chat.id, "⚠️ Invalid input. Enter a number:", parse_mode="HTML")
            bot.register_next_step_handler(sent, process_vpn_qty, prod_type, server, gb_val)
            return
            
        qty = int(qty_str)
        if qty <= 0: raise ValueError
        
        current_usage = get_current_usage()
        if (current_usage + (gb_val * qty)) > MAX_LIMIT_GB:
            bot.send_message(message.chat.id, f"⚠️ <b>Out of Stock!</b> Limit is 3TB. Remaining: {MAX_LIMIT_GB - current_usage} GB.", parse_mode="HTML")
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
        summary = f"🛒 <b>Order Summary</b>\n\n{icon} {prod_name} - {gb_val} GB | 1 Month\n📦 Quantity: {qty}\n{E_PRICE} Total: <b>{total:,} MMK</b>\n{E_ORDER} Order ID: #{oid}\n\nSelect Payment Method:"
        
        send_styled(message.chat.id, summary, kb)
    except:
        bot.send_message(message.chat.id, "⚠️ Invalid quantity.", parse_mode="HTML")

def process_stock(m, p):
    if ":" not in m.text:
        bot.reply_to(m, "❌ Invalid format. Use <code>email:password</code>", parse_mode="HTML")
        return
    email, pwd = m.text.split(":", 1)
    db = load_db(STOCK_FILE)
    if p not in db: db[p] = []
    db[p].append({"email": email.strip(), "password": pwd.strip()})
    save_db(STOCK_FILE, db) # Fully saves inside the file
    bot.reply_to(m, f"✅ Stock successfully added to <b>{p.upper()}</b>.\nTotal Available: {len(db[p])}", parse_mode="HTML")

@bot.message_handler(content_types=['photo'])
def handle_payment_slip(message):
    uid = message.from_user.id
    pending = load_db(PENDING_FILE)
    
    user_orders = [oid for oid, val in pending.items() if val.get('uid') == uid]
    
    if not user_orders:
        return 
        
    order_id = user_orders[-1]
    
    for old_oid in user_orders[:-1]:
        del pending[old_oid]
    save_db(PENDING_FILE, pending)

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Approve", callback_data=f"approve_{order_id}"), types.InlineKeyboardButton("❌ Reject", callback_data=f"reject_{order_id}"))
    
    order = pending[order_id]
    prod_name = order.get('product', '').replace('_', ' ').title()
    if prod_name == "Out": prod_name = "Outline VPN"
    elif prod_name == "Hid": prod_name = "Hiddify VPN"
    
    gb_txt = f"{order.get('gb')} GB" if order.get('gb', 0) > 0 else "Account"
    
    caption = f"🔔 <b>New Payment Slip!</b>\n\n🆔 Order: #{order_id}\n👤 User: <code>{uid}</code>\n💰 Total: {order['total']:,} MMK\n📦 Product: {prod_name} - {gb_txt} (Qty: {order['qty']})"
    
    bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=caption, reply_markup=markup, parse_mode="HTML")
    bot.reply_to(message, "✅ <b>Slip received.</b> Admin will verify it shortly.", parse_mode="HTML")

@bot.message_handler(content_types=['web_app_data'])
def handle_webapp_data(message):
    try:
        data = json.loads(message.web_app_data.data)
        
        if data.get('action') == "buy_vpn_webapp":
            product = "Outline" if data.get('product') == "out" else "Hiddify"
            msg = f"🔔 **New Order Received**\n\n"
            msg += f"👤 User: {message.from_user.first_name}\n"
            msg += f"📦 Product: {product}\n"
            msg += f"🌍 Server: {data.get('server', '').upper()}\n"
            msg += f"📊 Data: {data.get('gb')} GB\n"
            msg += f"💰 Price: {data.get('price')} MMK\n\n"
            msg += "Please send your payment screenshot to proceed."
            
            bot.send_message(message.chat.id, msg, parse_mode="Markdown")

        elif data.get('action') == "check_key_webapp":
            access_url = data.get('access_url')
            bot.send_message(message.chat.id, "🔍 Checking key status... Please wait.")
            
            try:
                import requests
                res = requests.post('http://127.0.0.1:5000/api/check_usage', json={"access_url": access_url})
                result = res.json()
                
                if result.get('success'):
                    d = result.get('data')
                    r_msg = f"📊 **Key Status Result**\n\n"
                    r_msg += f"📍 Server: {d.get('server').upper()}\n"
                    r_msg += f"📤 Used: {d.get('used_gb')} GB\n"
                    r_msg += f"📥 Limit: {d.get('limit_gb')} GB\n"
                    r_msg += f"🔄 Usage: {d.get('percentage')}%\n"
                    bot.send_message(message.chat.id, r_msg, parse_mode="Markdown")
                else:
                    bot.send_message(message.chat.id, f"❌ Error: {result.get('error')}")
            except Exception as e:
                bot.send_message(message.chat.id, "❌ Cannot connect to API. Please ensure app.py is running on port 5000.")

    except Exception as e:
        print(f"Error processing web_app_data: {e}")
if __name__ == "__main__":
    print("Formula X Final is starting on VPS...")
    bot.infinity_polling()
