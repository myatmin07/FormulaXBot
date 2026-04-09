import telebot
from telebot import types
import json
import os
import random
import string
import uuid
import requests
from datetime import datetime
import urllib3
import threading
import copy
import time

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

API_TOKEN = '8483869457:AAFBlSIu_6biWRAZ7lgGBrT-smj7C7tsQ20'
ADMIN_ID = 5890904598
bot = telebot.TeleBot(API_TOKEN)

SALES_FILE = "formula_x_sales.json"
HISTORY_FILE = "formula_x_user_history.json"
PRODUCTS_FILE = "formula_x_products.json"
ACCOUNTS_FILE = "formula_x_accounts.json"
PENDING_FILE = "formula_x_pending.json"

db_lock = threading.Lock()

# ==========================================
# 1. IN-MEMORY DATABASE (ဈေးနှုန်းများ အသေဖြစ်စေရန်)
# ==========================================
PRODUCTS_DB = {}

default_products = {
    # ChatGPT Category
    "cgpt_plus_12m": {"name": "🤖 ChatGPT Plus (12 M)", "price": 105000, "stock": 50, "prefix": "FX-GP12"},
    "cgpt_plus_1m": {"name": "🤖 ChatGPT Plus (1 M)", "price": 25000, "stock": 50, "prefix": "FX-GP1"},
    "cgpt_go_12m": {"name": "🧠 ChatGPT Go (12 M)", "price": 20000, "stock": 50, "prefix": "FX-GG12"},
    "cgpt_pro_1m": {"name": "🚀 ChatGPT PRO (1 M)", "price": 350000, "stock": 10, "prefix": "FX-GPR1"},
    
    # Claude (Main Menu Direct)
    "ai_claude_1m": {"name": "🟣 Claude Pro (1 M)", "price": 90000, "stock": 50, "prefix": "FX-CL1"},
    
    # Grok AI Category
    "grok_super_1m": {"name": "🦸‍♂️ Super Grok (1 M)", "price": 15000, "stock": 50, "prefix": "FX-SP1"},
    
    # Premium Tools Category
    "tool_canva": {"name": "🎨 Canva Edu Lifetime", "price": 5000, "stock": -1, "prefix": "FX-CV"},
    "tool_perplex_1y": {"name": "🔍 Perplexity (1 Y)", "price": 50000, "stock": 18, "prefix": "FX-PX"},
    
    # Capcut Category
    "capcut_pro": {"name": "🎬 Capcut Pro (1 M)", "price": 8000, "stock": -1, "prefix": "FX-CCP"},
    "capcut_team": {"name": "👥 Capcut Team (1 M)", "price": 10000, "stock": -1, "prefix": "FX-CCT"},
    
    # Express VPN Category
    "evpn_pc_1y": {"name": "💻 Express VPN (1 Y)", "price": 10000, "stock": 50, "prefix": "FX-EPC1"},
    "evpn_pc_2y": {"name": "💻 Express VPN (2 Y)", "price": 18000, "stock": 20, "prefix": "FX-EPC2"},
    "evpn_mob_1m_1d": {"name": "📱 Express VPN (1 M)", "price": 2000, "stock": 50, "prefix": "FX-EM1"},
    "evpn_mob_1m_8d": {"name": "📱 Express VPN (1 M)", "price": 11000, "stock": 50, "prefix": "FX-EM8"},
    "evpn_mob_3m_1d": {"name": "📱 Express VPN (3 M)", "price": 5000, "stock": 50, "prefix": "FX-EM3"},
    "evpn_mob_6m_1d": {"name": "📱 Express VPN (6 M)", "price": 8000, "stock": 50, "prefix": "FX-EM6"},
    "evpn_mob_1y_1d": {"name": "📱 Express VPN (1 Y)", "price": 10000, "stock": 50, "prefix": "FX-EMY1"},
    "evpn_mob_2y_1d": {"name": "📱 Express VPN (2 Y)", "price": 16000, "stock": 50, "prefix": "FX-EMY2"},
    
    # Hiddify VPN Category
    "hid_hk_1m": {"name": "🇭🇰 Hiddify VPN (1 M)", "price": 3000, "stock": 0, "prefix": "FX-HK1", "is_hiddify": True, "days": 30, "gb": 100},
    "hid_hk_2m": {"name": "🇭🇰 Hiddify VPN (2 M)", "price": 6000, "stock": 0, "prefix": "FX-HK2", "is_hiddify": True, "days": 60, "gb": 200},
    "hid_hk_3m": {"name": "🇭🇰 Hiddify VPN (3 M)", "price": 9000, "stock": 0, "prefix": "FX-HK3", "is_hiddify": True, "days": 90, "gb": 300},
}

user_orders = {}
admin_states = {}

def init_db():
    global PRODUCTS_DB
    if os.path.exists(PRODUCTS_FILE):
        try:
            with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
                PRODUCTS_DB = json.load(f)
        except Exception:
            PRODUCTS_DB = copy.deepcopy(default_products)
    else:
        PRODUCTS_DB = copy.deepcopy(default_products)

    # ဖိုင်အဟောင်းထဲမှ မလိုတော့သော ကောင်များအား ရှင်းလင်းခြင်း
    keys_to_remove = [k for k in PRODUCTS_DB.keys() if k not in default_products]
    for k in keys_to_remove:
        del PRODUCTS_DB[k]

    # အသစ်ထည့်ထားသော ကောင်များရှိပါက ပေါင်းထည့်ခြင်း
    for k, v in default_products.items():
        if k not in PRODUCTS_DB:
            PRODUCTS_DB[k] = copy.deepcopy(v)
        else:
            # အမည်ကိုသာ Update လုပ်မည်၊ ဈေးနှုန်းနှင့် Stock ကို လုံးဝ မပြောင်းလဲပါ
            PRODUCTS_DB[k]['name'] = v['name']
            
    save_products_db()

def save_products_db():
    with db_lock:
        tmp_path = PRODUCTS_FILE + ".tmp"
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(PRODUCTS_DB, f, indent=4)
            os.replace(tmp_path, PRODUCTS_FILE)
        except Exception:
            pass

# Initialize database at startup
init_db()

def safe_load_json(filepath, default_data):
    with db_lock:
        if not os.path.exists(filepath):
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(default_data, f, indent=4)
            return copy.deepcopy(default_data)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return copy.deepcopy(default_data)

def safe_save_json(filepath, data):
    with db_lock:
        tmp_path = filepath + ".tmp"
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            os.replace(tmp_path, filepath)
        except Exception:
            pass

def load_accounts(): return safe_load_json(ACCOUNTS_FILE, {})
def save_accounts(data): safe_save_json(ACCOUNTS_FILE, data)
def load_pending(): return safe_load_json(PENDING_FILE, {})
def save_pending(data): safe_save_json(PENDING_FILE, data)

def generate_random_note():
    chars = string.ascii_uppercase + string.digits
    return f"FX-{''.join(random.choices(chars, k=5))}"

def log_sale(user_id, product_name, qty, total):
    date_str = datetime.now().strftime("%Y-%m-%d")
    sale_entry = {"product": product_name, "qty": qty, "total": total, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    
    admin_data = safe_load_json(SALES_FILE, {})
    if date_str not in admin_data: admin_data[date_str] = []
    admin_data[date_str].append(sale_entry)
    safe_save_json(SALES_FILE, admin_data)
    
    user_history = safe_load_json(HISTORY_FILE, {})
    str_uid = str(user_id)
    if str_uid not in user_history: user_history[str_uid] = []
    user_history[str_uid].append(sale_entry)
    safe_save_json(HISTORY_FILE, user_history)

def get_and_deduct_accounts(product_key, qty, user_id):
    accs = load_accounts()
    if product_key not in accs: return None
    assigned = []
    needed = qty
    for acc in accs[product_key]:
        if needed == 0: break
        if acc['uses_left'] > 0 and user_id not in acc['used_by']:
            acc['uses_left'] -= 1
            acc['used_by'].append(user_id)
            assigned.append(acc['data'])
            needed -= 1
            
    accs[product_key] = [acc for acc in accs[product_key] if acc['uses_left'] > 0]
    save_accounts(accs)
    return assigned if len(assigned) == qty else None

def generate_hiddify_links(days, gb, user_id):
    admin_base_url = "https://formula-x.poner.shop/rJVGQZ4DWgZBDLdMAoCoOR/"
    client_base_url = "https://formula-x.poner.shop/JNpnvuHe0iglpK/"
    api_key = "853bce49-34dd-4e8b-a5f6-e90003ef458c"
    api_url = f"{admin_base_url}api/v1/user/" 
    new_uuid = str(uuid.uuid4())
    profile_name = f"FX-{user_id}-{random.randint(100,999)}"
    
    payload = {
        "uuid": new_uuid, "name": profile_name, "usage_limit_GB": gb, 
        "package_days": days, "mode": "no_reset", "comment": "FormulaX"
    }
    headers = {"Hiddify-API-Key": api_key, "Content-Type": "application/json"}
    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=10, verify=False)
        if response.status_code in [200, 201]: 
            return f"{client_base_url}{new_uuid}/#{profile_name}", f"{client_base_url}{new_uuid}/sub/#{profile_name}"
        return None, None
    except: return None, None

def format_acc_data(key, raw_data):
    parts = raw_data.split('|') if '|' in raw_data else raw_data.split(':')
    parts = [p.strip() for p in parts]
    
    if "cgpt" in key.lower():
        if len(parts) >= 3:
            return f"Please login at Outlook.com first.\n📧 Email - <code>{parts[0]}</code>\n🔑 Password - <code>{parts[1]}</code>\n🤖 Chat GPT Password - <code>{parts[2]}</code>"
        elif len(parts) == 2:
            return f"Please login at Outlook.com first.\n📧 Email - <code>{parts[0]}</code>\n🔑 Password - <code>{parts[1]}</code>"
    elif key.startswith("evpn_pc_"):
        return f"🛡️ License - <code>{raw_data.strip()}</code>"
    elif "hid_" in key:
        return f"🚀 Key -\n<code>{raw_data.strip()}</code>"
    else:
        if len(parts) >= 2:
            return f"📧 Email - <code>{parts[0]}</code>\n🔑 Password - <code>{parts[1]}</code>"
    return f"<code>{raw_data.strip()}</code>"

def process_approval(order_id, data):
    target_id = int(data['user_id'])
    key = data['key']
    qty_sold = data['qty']
    p_info = PRODUCTS_DB.get(key)
    
    if not p_info: return
    
    with db_lock:
        if p_info['stock'] > 0: 
            PRODUCTS_DB[key]['stock'] = max(0, PRODUCTS_DB[key]['stock'] - qty_sold)
    save_products_db()
    log_sale(target_id, p_info['name'], qty_sold, data['total'])
    
    delivered = []
    if p_info.get('is_hiddify'):
        for _ in range(qty_sold):
            link1, link2 = generate_hiddify_links(p_info['days'], p_info['gb'], target_id)
            if link1 and link2: 
                delivered.append(f"🔗 <b>Link (1):</b>\n<code>{link1}</code>\n\n🔗 <b>Link (2):</b>\n<code>{link2}</code>")
            else:
                accs = get_and_deduct_accounts(key, 1, target_id)
                if accs: delivered.append(format_acc_data(key, accs[0]))
    else:
        accs = get_and_deduct_accounts(key, qty_sold, target_id)
        if accs: 
            for a in accs: delivered.append(format_acc_data(key, a))
        
    if len(delivered) == qty_sold:
        if p_info.get('is_hiddify'):
            acc_text = "\n\n🔑 <b>Your VPN Links:</b>\n\n" + "\n\n==================\n\n".join([f"🔸 <b>Account {i}:</b>\n{a}" for i, a in enumerate(delivered, 1)])
            acc_text += "\n\n💡 <b>How to use:</b>\n1. Copy <b>Link (1)</b> above.\n2. Open the Hiddify App and tap the <code>+</code> button.\n3. Select <code>Add from Clipboard</code>.\n<i>(If Link 1 does not work, please try Link 2 instead.)</i>"
        else:
            acc_text = "\n\n🔑 <b>Your Account Details:</b>\n\n" + "\n\n".join([f"🔸 <b>Account {i}:</b>\n{a}" for i, a in enumerate(delivered, 1)])
            if key.startswith('evpn'): acc_text += "\n\n⚠️ <i>Please kindly use Express VPN strictly according to the specified device limits.</i>"
            
        bot.send_message(target_id, f"🎉 <b>Your order has been approved!</b>{acc_text}", parse_mode="HTML")
        bot.send_message(ADMIN_ID, f"✅ Successfully delivered to User {target_id}.")
    else:
        bot.send_message(target_id, f"🎉 <b>Your order has been approved!</b>\n\n⚠️ <b>Please wait a moment.</b>\n\nAccounts are currently being restocked. The admin will manually send your account details shortly. Please kindly contact @FORMULA_X0.", parse_mode="HTML")
        bot.send_message(ADMIN_ID, f"⚠️ User: {target_id}\n<b>Out of Stock / API Error. Please manually send the details.</b>\nProduct: {p_info['name']}")

def admin_panel_view(chat_id):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("💰 Edit Prices", callback_data="admin_editprice"),
        types.InlineKeyboardButton("📦 Manage Stock", callback_data="admin_setstock"),
        types.InlineKeyboardButton("➕ Add Accounts", callback_data="admin_addacc"),
        types.InlineKeyboardButton("👀 View Accounts", callback_data="admin_viewacc"),
        types.InlineKeyboardButton("❌ Close", callback_data="admin_close")
    )
    bot.send_message(chat_id, "👨‍💻 <b>Admin Control Panel</b>\n\nPlease select an action:", reply_markup=markup, parse_mode="HTML")

@bot.message_handler(commands=['admin'])
def admin_command(m):
    if m.from_user.id == ADMIN_ID: admin_panel_view(m.chat.id)

def get_admin_product_menu(action):
    markup = types.InlineKeyboardMarkup(row_width=1)
    for k, p in PRODUCTS_DB.items():
        if action == "addacc" and k == "tool_canva": continue 
        markup.add(types.InlineKeyboardButton(p['name'], callback_data=f"adm_{action}_{k}"))
    markup.add(types.InlineKeyboardButton("⬅️ Back to Admin Panel", callback_data="admin_back"))
    return markup

def step_setstock(m, key):
    try:
        new_stock = int(m.text.strip())
        with db_lock:
            PRODUCTS_DB[key]['stock'] = new_stock
        save_products_db()
        bot.send_message(m.chat.id, f"✅ Stock for <b>{PRODUCTS_DB[key]['name']}</b> has been updated to <b>{new_stock}</b>.", parse_mode="HTML")
    except ValueError:
        bot.send_message(m.chat.id, "❌ Please enter a valid number.")

def step_edit_price(m, key):
    try:
        new_price = int(m.text.strip())
        with db_lock:
            PRODUCTS_DB[key]['price'] = new_price
        save_products_db()
        bot.send_message(m.chat.id, f"✅ Price for <b>{PRODUCTS_DB[key]['name']}</b> has been updated to <b>{new_price} Ks</b>.", parse_mode="HTML")
    except ValueError:
        bot.send_message(m.chat.id, "❌ Please enter a valid number.")

def step_addacc_data(m, key):
    accounts = m.text.strip().split('\n')
    admin_states[ADMIN_ID] = {'key': key, 'accs': accounts}
    msg = bot.send_message(m.chat.id, f"Received <b>{len(accounts)}</b> accounts.\n\n<b>How many users can share each account?</b> (e.g., 3)", parse_mode="HTML")
    bot.register_next_step_handler(msg, step_addacc_uses)

def step_addacc_uses(m):
    try:
        uses = int(m.text.strip())
        state = admin_states.get(ADMIN_ID)
        if not state: return
        key = state['key']
        acc_list = state['accs']
        
        accs_db = load_accounts()
        if key not in accs_db: accs_db[key] = []
        
        for a in acc_list:
            if a.strip(): accs_db[key].append({"data": a.strip(), "uses_left": uses, "used_by": []})
        save_accounts(accs_db)
        
        added_stock = len(acc_list) * uses
        with db_lock:
            if PRODUCTS_DB[key]['stock'] == -1: PRODUCTS_DB[key]['stock'] = 0
            PRODUCTS_DB[key]['stock'] += added_stock
        save_products_db()
        
        bot.send_message(m.chat.id, f"✅ Accounts saved successfully.\nAdded <b>{added_stock}</b> to the stock.", parse_mode="HTML")
        admin_states.pop(ADMIN_ID, None)
    except ValueError:
        bot.send_message(m.chat.id, "❌ Please enter a valid number.")

def step_custom_qty(m, uid, cid):
    order = user_orders.get(uid)
    if not order: return
    
    try:
        qty = int(m.text.strip())
        if qty < 1:
            msg = bot.send_message(cid, "❌ The quantity must be at least 1. Please try again:")
            bot.register_next_step_handler(msg, step_custom_qty, uid, cid)
            return
            
        p = PRODUCTS_DB[order['key']]
        
        if p['stock'] != -1 and qty > p['stock']:
            bot.send_message(cid, f"❌ We apologize. Only <b>{p['stock']}</b> items are currently in stock. Please use /start to select again.", parse_mode="HTML")
            return

        user_orders[uid]["qty"] = qty
        if user_orders[uid]["key"] == "tool_canva":
            msg = bot.send_message(cid, "📧 Please enter your Canva email address:")
            bot.register_next_step_handler(msg, lambda msg_txt: [user_orders.get(uid).update({"email": msg_txt.text}), confirm(cid, uid)][-1])
        else:
            confirm(cid, uid)
    except ValueError:
        msg = bot.send_message(cid, "❌ Invalid input. Please enter a numerical value (e.g., 5):")
        bot.register_next_step_handler(msg, step_custom_qty, uid, cid)

def confirm(cid, uid):
    order = user_orders.get(uid)
    if not order: return
    p = PRODUCTS_DB[order['key']]
    total = p['price'] * order['qty']
    
    warranty_text = "🛡️ <b>Full Warranty</b>"
    if order['key'] == "tool_canva":
        warranty_text = "🛡️ <b>1 Year Warranty</b>"
        
    msg = f"🛒 <b>Order Confirmation</b>\n\n🛍️ <b>Product:</b> {p['name']}\n📦 <b>Quantity:</b> {order['qty']}\n💰 <b>Total Amount:</b> {total} Ks\n{warranty_text}"
    if order.get("email"): msg += f"\n📧 <b>Canva Email:</b> {order['email']}"
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("✅ Proceed to Payment", callback_data="pay"),
        types.InlineKeyboardButton("❌ Cancel", callback_data="page_main_0")
    )
    bot.send_message(cid, msg, reply_markup=markup, parse_mode="HTML")

def get_menu(cat="main", page=0, user_id=None):
    markup = types.InlineKeyboardMarkup(row_width=1)
    items_per_page = 5
    
    if cat == "main":
        main_items = [
            {"type": "cat", "name": "🤖 Chat GPT", "data": "cat_cgpt_0"},
            {"type": "prod", "key": "ai_claude_1m"},
            {"type": "cat", "name": "🌌 Grok Ai", "data": "cat_grok_0"},
            {"type": "cat", "name": "🛡️ Express VPN", "data": "cat_evpn_0"},
            {"type": "cat", "name": "🚀 Hiddify VPN", "data": "cat_hiddify_0"},
            {"type": "cat", "name": "🎬 Capcut Premium", "data": "cat_capcut_0"},
            {"type": "prod", "key": "tool_canva"},
            {"type": "prod", "key": "tool_perplex_1y"}
        ]
        
        start = page * items_per_page
        end = start + items_per_page
        current_items = main_items[start:end]
        
        for item in current_items:
            if item["type"] == "cat":
                markup.add(types.InlineKeyboardButton(item["name"], callback_data=item["data"]))
            else:
                k = item["key"]
                if k in PRODUCTS_DB:
                    p = PRODUCTS_DB[k]
                    # ခလုတ်တွင် ဈေးနှုန်းမပြတော့ပါ
                    s = " ❌" if p['stock'] == 0 else ""
                    markup.add(types.InlineKeyboardButton(f"{p['name']}{s}", callback_data=f"buy_{k}" if p['stock'] != 0 else "oos"))
        
        nav = []
        if page > 0: nav.append(types.InlineKeyboardButton("⬅️ Previous", callback_data=f"page_main_{page-1}"))
        if end < len(main_items): nav.append(types.InlineKeyboardButton("Next ➡️", callback_data=f"page_main_{page+1}"))
        if nav: markup.row(*nav)
        
        markup.row(
            types.InlineKeyboardButton("📋 Order History", callback_data="my_orders"),
            types.InlineKeyboardButton("💬 Contact Admin", callback_data="contact_admin")
        )
        if user_id == ADMIN_ID: markup.add(types.InlineKeyboardButton("⚙️ Admin Panel", callback_data="open_admin_panel"))

    elif cat == "cat_evpn":
        markup.add(types.InlineKeyboardButton("📱 For Mobile", callback_data="cat_ev_m_0"))
        markup.add(types.InlineKeyboardButton("💻 For PC", callback_data="cat_ev_p_0"))
        markup.row(types.InlineKeyboardButton("📋 Order History", callback_data="my_orders"), types.InlineKeyboardButton("💬 Contact Admin", callback_data="contact_admin"))
        markup.add(types.InlineKeyboardButton("🏠 Main Menu", callback_data="page_main_0"))
        return markup
        
    else:
        if cat == "cat_cgpt": keys = [k for k in PRODUCTS_DB.keys() if k.startswith("cgpt_")]
        elif cat == "cat_grok": keys = ["grok_super_1m"]
        elif cat == "cat_capcut": keys = ["capcut_pro", "capcut_team"]
        elif cat == "cat_ev_m": keys = [k for k in PRODUCTS_DB.keys() if k.startswith("evpn_mob_")]
        elif cat == "cat_ev_p": keys = [k for k in PRODUCTS_DB.keys() if k.startswith("evpn_pc_")]
        elif cat == "cat_hiddify": keys = [k for k in PRODUCTS_DB.keys() if k.startswith("hid_")]
        else: keys = []
            
        start = page * items_per_page
        end = start + items_per_page
        page_keys = keys[start:end]
        
        for k in page_keys:
            if k in PRODUCTS_DB:
                p = PRODUCTS_DB[k]
                # ခလုတ်တွင် ဈေးနှုန်းမပြတော့ပါ
                s = " ❌" if p['stock'] == 0 else ""
                markup.add(types.InlineKeyboardButton(f"{p['name']}{s}", callback_data=f"buy_{k}" if p['stock'] != 0 else "oos"))
                
        nav = []
        if page > 0: nav.append(types.InlineKeyboardButton("⬅️ Previous", callback_data=f"{cat}_{page-1}"))
        if end < len(keys): nav.append(types.InlineKeyboardButton("Next ➡️", callback_data=f"{cat}_{page+1}"))
        if nav: markup.row(*nav)
        
        markup.row(types.InlineKeyboardButton("📋 Order History", callback_data="my_orders"), types.InlineKeyboardButton("💬 Contact Admin", callback_data="contact_admin"))
        back_cat = "cat_evpn_0" if "ev_" in cat else "page_main_0"
        markup.add(types.InlineKeyboardButton("🏠 Back", callback_data=back_cat))
        
    return markup

@bot.message_handler(commands=['start'])
def start(m):
    msg = "👋 <b>Warmly welcome to Formula X Store.</b>\n\nYou can easily purchase your desired items here. Once the payment slip is verified, your accounts/keys will be automatically delivered."
    bot.send_message(m.chat.id, msg, reply_markup=get_menu("main", 0, m.from_user.id), parse_mode="HTML")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    uid = message.from_user.id
    if uid in user_orders and "awaiting_slip" in user_orders[uid]:
        oid = user_orders[uid]["awaiting_slip"]
        pending = load_pending()
        if oid in pending:
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(
                types.InlineKeyboardButton("✅ Approve Order", callback_data=f"approve_{oid}"),
                types.InlineKeyboardButton("❌ Reject Order", callback_data=f"reject_{oid}")
            )
            caption = f"🔔 <b>New Payment Slip Received!</b>\n\n🆔 <b>Order ID:</b> <code>{oid}</code>\n👤 <b>User:</b> {uid}\n💰 <b>Total:</b> {pending[oid]['total']} Ks\n🛍️ <b>Product:</b> {pending[oid]['key']}"
            bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=caption, reply_markup=markup, parse_mode="HTML")
            bot.reply_to(message, "✅ <b>Payment slip received successfully.</b>\n\nOnce the admin verifies it, your account details will automatically be sent to you.", parse_mode="HTML")
            del user_orders[uid]["awaiting_slip"]

@bot.callback_query_handler(func=lambda call: True)
def cb(call):
    try: bot.answer_callback_query(call.id)
    except: pass

    uid = call.from_user.id
    cid = call.message.chat.id
    mid = call.message.message_id
    
    try:
        if call.data == "open_admin_panel":
            if uid == ADMIN_ID: admin_panel_view(cid)
        elif call.data == "admin_close":
            bot.delete_message(cid, mid)
        elif call.data == "admin_back":
            admin_panel_view(cid)
            bot.delete_message(cid, mid)
            
        elif call.data == "admin_editprice":
            bot.edit_message_text("💰 Select the product to edit its price:", cid, mid, reply_markup=get_admin_product_menu("price"))
        elif call.data == "admin_setstock":
            bot.edit_message_text("📦 Select the product to manage its stock:", cid, mid, reply_markup=get_admin_product_menu("stk"))
        elif call.data == "admin_addacc":
            bot.edit_message_text("➕ Select the product to add new accounts:", cid, mid, reply_markup=get_admin_product_menu("addacc"))
        elif call.data == "admin_viewacc":
            bot.edit_message_text("👀 Select the product to view saved accounts:", cid, mid, reply_markup=get_admin_product_menu("vw"))
            
        elif call.data.startswith("adm_price_"):
            key = call.data.split("adm_price_")[1]
            p = PRODUCTS_DB[key]
            msg = bot.send_message(cid, f"<b>{p['name']}</b>\nCurrent Price: {p['price']} Ks\n\nPlease enter the new price:", parse_mode="HTML")
            bot.register_next_step_handler(msg, step_edit_price, key)
            
        elif call.data.startswith("adm_stk_"):
            key = call.data.split("adm_stk_")[1]
            p = PRODUCTS_DB[key]
            msg = bot.send_message(cid, f"<b>{p['name']}</b>\nCurrent Stock: {p['stock']}\n\nPlease enter the new stock amount:", parse_mode="HTML")
            bot.register_next_step_handler(msg, step_setstock, key)
            
        elif call.data.startswith("adm_addacc_"):
            key = call.data.split("adm_addacc_")[1]
            p = PRODUCTS_DB[key]
            if "cgpt" in key:
                prompt_text = f"Please send <b>Email and Passwords</b> for <b>{p['name']}</b>.\n\n(Send one per line using the format: <b>Email|Email_Pass|GPT_Pass</b>)\nExample:\nuser@outlook.com|pass123|gpt456"
            elif key.startswith("evpn_pc_"):
                prompt_text = f"Please send <b>License Keys</b> for <b>{p['name']}</b>.\n\n(Send one per line)\nExample:\nEXYZ123456789"
            elif p.get('is_hiddify') or "hid_" in key:
                prompt_text = f"Please send <b>VPN Links</b> for <b>{p['name']}</b>.\n\nExample:\nvless://..."
            else:
                prompt_text = f"Please send <b>Email and Passwords</b> for <b>{p['name']}</b>.\n\n(Send one per line using the format: <b>Email|Password</b>)\nExample:\nuser@gmail.com|pass123"
            msg = bot.send_message(cid, prompt_text, parse_mode="HTML")
            bot.register_next_step_handler(msg, step_addacc_data, key)
            
        elif call.data.startswith("adm_vw_"):
            key = call.data.split("adm_vw_")[1]
            accs = load_accounts().get(key, [])
            if not accs: bot.send_message(cid, "There are no saved accounts for this product.")
            else:
                text = f"📋 <b>Account List ({len(accs)})</b>\n\n"
                for i, a in enumerate(accs, 1): text += f"{i}. <code>{a['data']}</code> (Uses left: {a['uses_left']})\n"
                bot.send_message(cid, text, parse_mode="HTML")

        elif call.data.startswith("page_main_"): 
            page = int(call.data.split("_")[2])
            bot.edit_message_text("👋 <b>Warmly welcome to Formula X Store.</b>\n\nPlease select an option below:", cid, mid, reply_markup=get_menu("main", page, uid), parse_mode="HTML")
            
        elif call.data.startswith("cat_"):
            parts = call.data.split("_")
            page = int(parts[-1])
            cat = "_".join(parts[:-1])
            menu_text = "👋 <b>Warmly welcome to Formula X Store.</b>\n\nPlease select an option below:"
            if cat == "cat_evpn" or cat.startswith("cat_ev_"): menu_text = "🛡️ <b>Express VPN</b>\n\nPlease select a plan:"
            elif cat == "cat_hiddify": menu_text = "🚀 <b>Hiddify VPN</b>\n\nPlease select a plan:"
            elif cat == "cat_capcut": menu_text = "🎬 <b>Capcut Premium</b>\n\nPlease select a plan:"
            elif cat == "cat_cgpt": menu_text = "🤖 <b>Chat GPT Plans</b>\n\nPlease select a plan:"
            elif cat == "cat_grok": menu_text = "🌌 <b>Grok Ai</b>\n\nPlease select a plan:"
            bot.edit_message_text(menu_text, cid, mid, reply_markup=get_menu(cat, page, uid), parse_mode="HTML")
            
        elif call.data == "oos": 
            bot.answer_callback_query(call.id, "Sorry, this item is currently out of stock.", show_alert=True)
            
        elif call.data.startswith("buy_"):
            key = call.data.split("buy_")[1]
            user_orders[uid] = {"key": key}
            p = PRODUCTS_DB[key]
            
            markup = types.InlineKeyboardMarkup(row_width=1)
            for i in range(1, 4): markup.add(types.InlineKeyboardButton(f"Qty: {i}", callback_data=f"qty_{i}"))
            markup.add(types.InlineKeyboardButton("✍️ Custom Quantity", callback_data="qty_custom"))
            markup.add(types.InlineKeyboardButton("🏠 Main Menu", callback_data="page_main_0"))
            
            # ခလုတ်ကို နှိပ်လိုက်မှသာ ဈေးနှုန်းကို ပြပေးမည်
            details_msg = f"🛍️ <b>Product:</b> {p['name']}\n💵 <b>Price:</b> {p['price']} Ks\n\n<i>Please select the quantity you wish to purchase:</i>"
            bot.edit_message_text(details_msg, cid, mid, reply_markup=markup, parse_mode="HTML")
            
        elif call.data.startswith("qty_"):
            if uid not in user_orders or "key" not in user_orders[uid]: 
                bot.answer_callback_query(call.id, "⏱ Session expired. Please send /start again.", show_alert=True)
                return
            if call.data == "qty_custom":
                msg = bot.send_message(cid, "✍️ Please enter the desired quantity (e.g., 5):")
                bot.register_next_step_handler(msg, step_custom_qty, uid, cid)
                return
            qty = int(call.data.split("_")[1])
            user_orders[uid]["qty"] = qty
            if user_orders[uid]["key"] == "tool_canva":
                msg = bot.send_message(cid, "📧 Please enter your Canva email address:")
                bot.register_next_step_handler(msg, lambda m: [user_orders.get(uid).update({"email": m.text}), confirm(cid, uid)][-1])
            else: 
                bot.delete_message(cid, mid)
                confirm(cid, uid)
                
        elif call.data == "pay":
            if uid not in user_orders or "key" not in user_orders[uid]: 
                bot.answer_callback_query(call.id, "⏱ Session expired. Please send /start again.", show_alert=True)
                return
            oid = generate_random_note()
            user_orders[uid]["oid"] = oid
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(types.InlineKeyboardButton("🏦 Pay with Wave Pay", callback_data="p_w"), types.InlineKeyboardButton("💳 Pay with KBZ Pay", callback_data="p_k"), types.InlineKeyboardButton("🏠 Main Menu", callback_data="page_main_0"))
            bot.edit_message_text(f"🛒 <b>Order ID:</b> <code>{oid}</code>\n\nPlease choose your payment method:", cid, mid, reply_markup=markup, parse_mode="HTML")
            
        elif call.data.startswith("p_"):
            if uid not in user_orders or "qty" not in user_orders[uid]: 
                bot.answer_callback_query(call.id, "⏱ Session expired. Please send /start again.", show_alert=True)
                return
            order = user_orders[uid]
            p = PRODUCTS_DB[order['key']]
            total = p['price'] * order['qty']
            
            pending = load_pending()
            pending[order['oid']] = {"user_id": uid, "key": order['key'], "qty": order['qty'], "total": total}
            save_pending(pending)
            user_orders[uid]["awaiting_slip"] = order['oid']
            
            warranty_msg = "🛡️ <b>Full Warranty</b> is provided. You can purchase with confidence."
            if order['key'] == "tool_canva": warranty_msg = "🛡️ <b>1 Year Warranty</b> is provided. You can purchase with confidence."
            
            pay_msg = f"💳 <b>Payment Information</b>\n\n📱 <b>Phone:</b> <code>09770088206</code>\n👤 <b>Name:</b> Myat Min Lwin\n💰 <b>Total Amount:</b> {total} Ks\n\n📝 <b>Payment Note:</b> <code>{order['oid']}</code>\n\n⚠️ <i>Please include the exact note above during your transfer to receive your items automatically.</i>\n\n{warranty_msg}\n\n✅ <b>Please send the payment screenshot/slip to this chat.</b>"
            bot.edit_message_text(pay_msg, cid, mid, parse_mode="HTML")
            
        elif call.data.startswith("approve_") or call.data.startswith("reject_"):
            action, oid = call.data.split("_")
            pending = load_pending()
            if oid not in pending: 
                bot.answer_callback_query(call.id, "This order has already been processed.", show_alert=True)
                return
            data = pending[oid]
            if action == "approve":
                bot.edit_message_caption(f"✅ APPROVED\nOrder ID: {oid}\nDelivering keys to the user...", cid, mid)
                process_approval(oid, data)
            else:
                bot.send_message(data['user_id'], f"❌ Dear user, your order (ID: {oid}) has been cancelled due to an invalid payment slip.")
                bot.edit_message_caption(f"❌ REJECTED\nOrder ID: {oid}\nCancelled due to invalid payment.", cid, mid)
            del pending[oid]
            save_pending(pending)
            
        elif call.data == "contact_admin":
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(types.InlineKeyboardButton("🏠 Main Menu", callback_data="page_main_0"))
            bot.edit_message_text("👨‍💻 For any inquiries, please contact @FORMULA_X0.", cid, mid, reply_markup=markup)
            
        elif call.data == "my_orders":
            hist = safe_load_json(HISTORY_FILE, {}).get(str(uid), [])
            msg = "📋 <b>Your Order History</b>\n\n" + "\n".join([f"📦 {h['product']} - {h['total']} Ks" for h in hist[-5:]]) if hist else "No order history found."
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(types.InlineKeyboardButton("🏠 Main Menu", callback_data="page_main_0"))
            bot.edit_message_text(msg, cid, mid, reply_markup=markup, parse_mode="HTML")
            
    except telebot.apihelper.ApiTelegramException as e:
        if "message is not modified" not in str(e).lower(): print(f"Telegram API Error: {e}")
    except Exception as e:
        print(f"Callback Error: {e}")

if __name__ == "__main__":
    print("🤖 FormulaX Bot is successfully running...")
    while True:
        try:
            bot.polling(none_stop=True, timeout=60, long_polling_timeout=60)
        except requests.exceptions.ConnectionError:
            time.sleep(5)
        except Exception:
            time.sleep(5)