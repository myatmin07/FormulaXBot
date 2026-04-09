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

# ==========================================
# 1. CONFIGURATION
# ==========================================
API_TOKEN = '8483869457:AAFBlSIu_6biWRAZ7lgGBrT-smj7C7tsQ20'
ADMIN_ID = 5890904598
bot = telebot.TeleBot(API_TOKEN)

SALES_FILE = "formula_x_sales.json"
HISTORY_FILE = "formula_x_user_history.json"
PRODUCTS_FILE = "formula_x_products.json"
ACCOUNTS_FILE = "formula_x_accounts.json"
PENDING_FILE = "formula_x_pending.json"

db_lock = threading.Lock()
PRODUCTS_DB = {}

# ==========================================
# 2. DEFAULT PRODUCTS DATA
# ==========================================
default_products = {
    # Chat GPT Category
    "cgpt_plus_12m": {"name": "🤖 ChatGPT Plus (12 M)", "price": 105000, "stock": 50, "prefix": "FX-GP12"},
    "cgpt_plus_1m": {"name": "🤖 ChatGPT Plus (1 M)", "price": 25000, "stock": 50, "prefix": "FX-GP1"},
    "cgpt_go_12m": {"name": "🧠 ChatGPT Go (12 M)", "price": 20000, "stock": 50, "prefix": "FX-GG12"},
    "cgpt_pro_1m": {"name": "🚀 ChatGPT PRO (1 M)", "price": 350000, "stock": 10, "prefix": "FX-GPR1"},
    
    # Direct Main Menu Items
    "ai_claude_1m": {"name": "🟣 Claude Pro (1 M)", "price": 90000, "stock": 50, "prefix": "FX-CL1"},
    "tool_canva": {"name": "🎨 Canva Edu Lifetime", "price": 5000, "stock": -1, "prefix": "FX-CV"},
    "tool_perplex_1y": {"name": "🔍 Perplexity (1 Y)", "price": 50000, "stock": 18, "prefix": "FX-PX"},
    
    # Grok Ai Category
    "grok_super_1m": {"name": "🦸‍♂️ Super Grok (1 M)", "price": 15000, "stock": 50, "prefix": "FX-SP1"},
    
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

# ==========================================
# 3. CORE FUNCTIONS (DB & STORAGE)
# ==========================================
def init_db():
    global PRODUCTS_DB
    if os.path.exists(PRODUCTS_FILE):
        try:
            with open(PRODUCTS_FILE, "r", encoding="utf-8") as f: PRODUCTS_DB = json.load(f)
        except: PRODUCTS_DB = copy.deepcopy(default_products)
    else: PRODUCTS_DB = copy.deepcopy(default_products)

    # Clean old data
    keys_to_remove = [k for k in PRODUCTS_DB.keys() if k not in default_products]
    for k in keys_to_remove: del PRODUCTS_DB[k]
    # Add new products
    for k, v in default_products.items():
        if k not in PRODUCTS_DB: PRODUCTS_DB[k] = copy.deepcopy(v)
        else: PRODUCTS_DB[k]['name'] = v['name']
    save_products_db()

def save_products_db():
    with db_lock:
        tmp_path = PRODUCTS_FILE + ".tmp"
        try:
            with open(tmp_path, "w", encoding="utf-8") as f: json.dump(PRODUCTS_DB, f, indent=4)
            os.replace(tmp_path, PRODUCTS_FILE)
        except: pass

init_db()

def safe_load_json(filepath, default_data):
    with db_lock:
        if not os.path.exists(filepath): return copy.deepcopy(default_data)
        try:
            with open(filepath, "r", encoding="utf-8") as f: return json.load(f)
        except: return copy.deepcopy(default_data)

def safe_save_json(filepath, data):
    with db_lock:
        tmp_path = filepath + ".tmp"
        try:
            with open(tmp_path, "w", encoding="utf-8") as f: json.dump(data, f, indent=4)
            os.replace(tmp_path, filepath)
        except: pass

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
    payload = {"uuid": new_uuid, "name": profile_name, "usage_limit_GB": gb, "package_days": days, "mode": "no_reset", "comment": "FormulaX"}
    headers = {"Hiddify-API-Key": api_key, "Content-Type": "application/json"}
    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=10, verify=False)
        if response.status_code in [200, 201]: return f"{client_base_url}{new_uuid}/#{profile_name}", f"{client_base_url}{new_uuid}/sub/#{profile_name}"
        return None, None
    except: return None, None

def format_acc_data(key, raw_data):
    parts = raw_data.split('|') if '|' in raw_data else raw_data.split(':')
    parts = [p.strip() for p in parts]
    if "cgpt" in key.lower() or "ai_" in key.lower() or "grok" in key.lower():
        if len(parts) >= 3: return f"Please login at Outlook.com first.\n📧 Email - <code>{parts[0]}</code>\n🔑 Password - <code>{parts[1]}</code>\n🤖 Chat GPT Password - <code>{parts[2]}</code>"
        elif len(parts) == 2: return f"Please login at Outlook.com first.\n📧 Email - <code>{parts[0]}</code>\n🔑 Password - <code>{parts[1]}</code>"
    elif key.startswith("evpn_pc_"): return f"🛡️ License - <code>{raw_data.strip()}</code>"
    elif "hid_" in key: return f"🚀 Key -\n<code>{raw_data.strip()}</code>"
    else:
        if len(parts) >= 2: return f"📧 Email - <code>{parts[0]}</code>\n🔑 Password - <code>{parts[1]}</code>"
    return f"<code>{raw_data.strip()}</code>"

def process_approval(order_id, data):
    target_id = int(data['user_id'])
    key = data['key']
    qty_sold = data['qty']
    p_info = PRODUCTS_DB.get(key)
    if not p_info: return
    with db_lock:
        if p_info['stock'] > 0: PRODUCTS_DB[key]['stock'] = max(0, PRODUCTS_DB[key]['stock'] - qty_sold)
    save_products_db()
    log_sale(target_id, p_info['name'], qty_sold, data['total'])
    
    delivered = []
    if p_info.get('is_hiddify'):
        for _ in range(qty_sold):
            l1, l2 = generate_hiddify_links(p_info['days'], p_info['gb'], target_id)
            if l1: delivered.append(f"🔗 <b>Link (1):</b>\n<code>{l1}</code>\n\n🔗 <b>Link (2):</b>\n<code>{l2}</code>")
            else:
                accs = get_and_deduct_accounts(key, 1, target_id)
                if accs: delivered.append(format_acc_data(key, accs[0]))
    else:
        accs = get_and_deduct_accounts(key, qty_sold, target_id)
        if accs: 
            for a in accs: delivered.append(format_acc_data(key, a))
        
    if len(delivered) == qty_sold:
        acc_text = "\n\n🔑 <b>Your Account Details:</b>\n\n" + "\n\n".join([f"🔸 <b>Item {i}:</b>\n{a}" for i, a in enumerate(delivered, 1)])
        bot.send_message(target_id, f"🎉 <b>Your order has been approved!</b>{acc_text}", parse_mode="HTML")
        bot.send_message(ADMIN_ID, f"✅ Successfully delivered to User {target_id}.")
    else:
        bot.send_message(target_id, f"🎉 <b>Your order has been approved!</b>\n\n⚠️ Accounts are being restocked. Admin will send them manually. Contact @FORMULA_X0.", parse_mode="HTML")
        bot.send_message(ADMIN_ID, f"⚠️ User {target_id}: <b>Out of Stock!</b> Send manually.")

# ==========================================
# 4. BOT LOGIC (CATEGORIES & MENUS)
# ==========================================
def get_menu(cat="main", page=0, user_id=None):
    markup = types.InlineKeyboardMarkup(row_width=1)
    items_per_page = 5
    
    if cat == "main":
        main_list = [
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
        current = main_list[start:end]
        for item in current:
            if item["type"] == "cat": markup.add(types.InlineKeyboardButton(item["name"], callback_data=item["data"]))
            else:
                k = item["key"]
                if k in PRODUCTS_DB: markup.add(types.InlineKeyboardButton(f"{PRODUCTS_DB[k]['name']}" + (" ❌" if PRODUCTS_DB[k]['stock'] == 0 else ""), callback_data=f"buy_{k}" if PRODUCTS_DB[k]['stock'] != 0 else "oos"))
        nav = []
        if page > 0: nav.append(types.InlineKeyboardButton("⬅️ Previous", callback_data=f"page_main_{page-1}"))
        if end < len(main_list): nav.append(types.InlineKeyboardButton("Next ➡️", callback_data=f"page_main_{page+1}"))
        if nav: markup.row(*nav)
        markup.row(types.InlineKeyboardButton("📋 Order History", callback_data="my_orders"), types.InlineKeyboardButton("💬 Contact Admin", callback_data="contact_admin"))
        if user_id == ADMIN_ID: markup.add(types.InlineKeyboardButton("⚙️ Admin Panel", callback_data="open_admin_panel"))

    elif cat == "cat_evpn":
        markup.add(types.InlineKeyboardButton("📱 For Mobile", callback_data="cat_ev_m_0"), types.InlineKeyboardButton("💻 For PC", callback_data="cat_ev_p_0"))
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
            if k in PRODUCTS_DB: markup.add(types.InlineKeyboardButton(f"{PRODUCTS_DB[k]['name']}" + (" ❌" if PRODUCTS_DB[k]['stock'] == 0 else ""), callback_data=f"buy_{k}" if PRODUCTS_DB[k]['stock'] != 0 else "oos"))
        nav = []
        if page > 0: nav.append(types.InlineKeyboardButton("⬅️ Prev", callback_data=f"{cat}_{page-1}"))
        if end < len(keys): nav.append(types.InlineKeyboardButton("Next ➡️", callback_data=f"{cat}_{page+1}"))
        if nav: markup.row(*nav)
        markup.add(types.InlineKeyboardButton("🏠 Back", callback_data="page_main_0"))
        
    return markup

@bot.message_handler(commands=['start'])
def start(m):
    msg = "👋 <b>Warmly welcome to Formula X Store.</b>\n\nPlease select an option below:"
    bot.send_message(m.chat.id, msg, reply_markup=get_menu("main", 0, m.from_user.id), parse_mode="HTML")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    uid = message.from_user.id
    if uid in user_orders and "awaiting_slip" in user_orders[uid]:
        oid = user_orders[uid]["awaiting_slip"]
        pending = load_pending()
        if oid in pending:
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(types.InlineKeyboardButton("✅ Approve Order", callback_data=f"approve_{oid}"), types.InlineKeyboardButton("❌ Reject Order", callback_data=f"reject_{oid}"))
            caption = f"🔔 <b>New Payment Slip!</b>\n\n🆔 Order ID: <code>{oid}</code>\n👤 User: {uid}\n💰 Total: {pending[oid]['total']} Ks\n🛍️ Product: {pending[oid]['key']}"
            bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=caption, reply_markup=markup, parse_mode="HTML")
            bot.reply_to(message, "✅ <b>Payment slip received.</b> Admin will verify it shortly.", parse_mode="HTML")
            del user_orders[uid]["awaiting_slip"]

@bot.callback_query_handler(func=lambda call: True)
def cb(call):
    uid, cid, mid = call.from_user.id, call.message.chat.id, call.message.message_id
    try: bot.answer_callback_query(call.id)
    except: pass
    
    try:
        if call.data == "open_admin_panel" and uid == ADMIN_ID:
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(types.InlineKeyboardButton("💰 Edit Prices", callback_data="admin_editprice"), types.InlineKeyboardButton("📦 Manage Stock", callback_data="admin_setstock"), types.InlineKeyboardButton("➕ Add Accs", callback_data="admin_addacc"), types.InlineKeyboardButton("👀 View Accs", callback_data="admin_viewacc"), types.InlineKeyboardButton("❌ Close", callback_data="admin_close"))
            bot.send_message(cid, "👨‍💻 <b>Admin Panel</b>", reply_markup=markup, parse_mode="HTML")
        elif call.data == "admin_close": bot.delete_message(cid, mid)
        elif call.data == "admin_editprice": bot.edit_message_text("💰 Select product to edit price:", cid, mid, reply_markup=get_admin_product_menu("price"))
        elif call.data == "admin_setstock": bot.edit_message_text("📦 Select product to manage stock:", cid, mid, reply_markup=get_admin_product_menu("stk"))
        elif call.data == "admin_addacc": bot.edit_message_text("➕ Select product to add accounts:", cid, mid, reply_markup=get_admin_product_menu("addacc"))
        elif call.data == "admin_viewacc": bot.edit_message_text("👀 Select product to view accounts:", cid, mid, reply_markup=get_admin_product_menu("vw"))
        
        elif call.data.startswith("adm_price_"):
            key = call.data.split("_")[-1]
            msg = bot.send_message(cid, f"Enter new price for {PRODUCTS_DB[key]['name']} (Current: {PRODUCTS_DB[key]['price']} Ks):")
            bot.register_next_step_handler(msg, step_edit_price, key)
        elif call.data.startswith("adm_stk_"):
            key = call.data.split("_")[-1]
            msg = bot.send_message(cid, f"Enter new stock for {PRODUCTS_DB[key]['name']}:")
            bot.register_next_step_handler(msg, step_setstock, key)
        elif call.data.startswith("adm_addacc_"):
            key = call.data.split("_")[-1]
            msg = bot.send_message(cid, f"Send accounts/keys for {PRODUCTS_DB[key]['name']} (One per line):")
            bot.register_next_step_handler(msg, step_addacc_data, key)
        elif call.data.startswith("adm_vw_"):
            key = call.data.split("_")[-1]
            accs = load_accounts().get(key, [])
            if not accs: bot.send_message(cid, "No accounts.")
            else:
                txt = f"📋 <b>{PRODUCTS_DB[key]['name']}</b>\n\n" + "\n".join([f"{i}. <code>{a['data']}</code>" for i, a in enumerate(accs[:20], 1)])
                bot.send_message(cid, txt, parse_mode="HTML")

        elif call.data.startswith("page_main_"): bot.edit_message_text("👋 <b>Welcome!</b> Select option:", cid, mid, reply_markup=get_menu("main", int(call.data.split("_")[2]), uid), parse_mode="HTML")
        elif call.data.startswith("cat_"):
            parts = call.data.split("_")
            bot.edit_message_text("Please select a plan:", cid, mid, reply_markup=get_menu("_".join(parts[:-1]), int(parts[-1]), uid), parse_mode="HTML")
        elif call.data == "oos": bot.answer_callback_query(call.id, "Out of stock!", show_alert=True)
        elif call.data.startswith("buy_"):
            key = call.data.split("buy_")[1]
            user_orders[uid] = {"key": key}
            markup = types.InlineKeyboardMarkup(row_width=1)
            for i in range(1, 4): markup.add(types.InlineKeyboardButton(f"Qty: {i}", callback_data=f"qty_{i}"))
            markup.add(types.InlineKeyboardButton("✍️ Custom Quantity", callback_data="qty_custom"), types.InlineKeyboardButton("🏠 Main Menu", callback_data="page_main_0"))
            bot.edit_message_text(f"🛍️ <b>{PRODUCTS_DB[key]['name']}</b>\n💵 Price: <b>{PRODUCTS_DB[key]['price']} Ks</b>\n\nSelect quantity:", cid, mid, reply_markup=markup, parse_mode="HTML")
            
        elif call.data.startswith("qty_"):
            if uid not in user_orders: return
            if call.data == "qty_custom":
                msg = bot.send_message(cid, "Enter quantity:")
                bot.register_next_step_handler(msg, step_custom_qty, uid, cid)
                return
            user_orders[uid]["qty"] = int(call.data.split("_")[1])
            if user_orders[uid]["key"] == "tool_canva":
                msg = bot.send_message(cid, "Enter Canva email:")
                bot.register_next_step_handler(msg, lambda m: [user_orders.get(uid).update({"email": m.text}), confirm(cid, uid)][-1])
            else: confirm(cid, uid)
            
        elif call.data == "pay":
            oid = generate_random_note()
            user_orders[uid]["oid"] = oid
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(types.InlineKeyboardButton("🏦 Pay with Wave Pay", callback_data="p_w"), types.InlineKeyboardButton("💳 Pay with KBZ Pay", callback_data="p_k"))
            bot.edit_message_text(f"🛒 <b>Order ID:</b> <code>{oid}</code>\nChoose payment:", cid, mid, reply_markup=markup, parse_mode="HTML")
        elif call.data.startswith("p_"):
            order = user_orders[uid]
            p = PRODUCTS_DB[order['key']]
            total = p['price'] * order['qty']
            pending = load_pending()
            pending[order['oid']] = {"user_id": uid, "key": order['key'], "qty": order['qty'], "total": total}
            save_pending(pending)
            user_orders[uid]["awaiting_slip"] = order['oid']
            bot.edit_message_text(f"💳 <b>Payment</b>\n\nPhone: <code>09770088206</code>\nName: Myat Min Lwin\nTotal: <b>{total} Ks</b>\nNote: <code>{order['oid']}</code>\n\n✅ Send screenshot to this chat.", cid, mid, parse_mode="HTML")
            
        elif call.data.startswith("approve_") or call.data.startswith("reject_"):
            act, oid = call.data.split("_")
            pending = load_pending()
            if oid not in pending: return
            data = pending[oid]
            if act == "approve":
                bot.edit_message_caption(f"✅ APPROVED: {oid}", cid, mid)
                process_approval(oid, data)
            else:
                bot.send_message(data['user_id'], f"❌ Order {oid} Rejected.")
                bot.edit_message_caption(f"❌ REJECTED: {oid}", cid, mid)
            del pending[oid]
            save_pending(pending)
        elif call.data == "contact_admin": bot.send_message(cid, "Contact @FORMULA_X0")
        elif call.data == "my_orders":
            hist = safe_load_json(HISTORY_FILE, {}).get(str(uid), [])
            msg = "📋 <b>History</b>\n\n" + "\n".join([f"📦 {h['product']} - {h['total']} Ks" for h in hist[-5:]]) if hist else "No history."
            bot.send_message(cid, msg, parse_mode="HTML")
    except Exception as e: print(f"Error: {e}")

# --- Admin Step Handlers ---
def step_edit_price(m, key):
    try:
        with db_lock: PRODUCTS_DB[key]['price'] = int(m.text.strip())
        save_products_db()
        bot.send_message(m.chat.id, "✅ Price Updated.")
    except: bot.send_message(m.chat.id, "Invalid number.")
def step_setstock(m, key):
    try:
        with db_lock: PRODUCTS_DB[key]['stock'] = int(m.text.strip())
        save_products_db()
        bot.send_message(m.chat.id, "✅ Stock Updated.")
    except: bot.send_message(m.chat.id, "Invalid number.")
def step_addacc_data(m, key):
    admin_states[ADMIN_ID] = {'key': key, 'accs': m.text.strip().split('\n')}
    msg = bot.send_message(m.chat.id, "How many users per account?")
    bot.register_next_step_handler(msg, step_addacc_uses)
def step_addacc_uses(m):
    try:
        uses, state = int(m.text.strip()), admin_states.get(ADMIN_ID)
        key, acc_list = state['key'], state['accs']
        db = load_accounts()
        if key not in db: db[key] = []
        for a in acc_list: db[key].append({"data": a.strip(), "uses_left": uses, "used_by": []})
        save_accounts(db)
        with db_lock: 
            if PRODUCTS_DB[key]['stock'] == -1: PRODUCTS_DB[key]['stock'] = 0
            PRODUCTS_DB[key]['stock'] += len(acc_list) * uses
        save_products_db()
        bot.send_message(m.chat.id, "✅ Done.")
    except: bot.send_message(m.chat.id, "Error.")
def step_custom_qty(m, uid, cid):
    try:
        qty = int(m.text.strip())
        user_orders[uid]["qty"] = qty
        confirm(cid, uid)
    except: bot.send_message(cid, "Invalid number.")
def confirm(cid, uid):
    p = PRODUCTS_DB[user_orders[uid]['key']]
    total = p['price'] * user_orders[uid]['qty']
    markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("✅ Pay", callback_data="pay"), types.InlineKeyboardButton("❌ Cancel", callback_data="page_main_0"))
    bot.send_message(cid, f"🛒 <b>Confirm Order</b>\nProduct: {p['name']}\nQty: {user_orders[uid]['qty']}\nTotal: {total} Ks", reply_markup=markup, parse_mode="HTML")

def get_admin_product_menu(action):
    markup = types.InlineKeyboardMarkup(row_width=1)
    for k, p in PRODUCTS_DB.items(): markup.add(types.InlineKeyboardButton(p['name'], callback_data=f"adm_{action}_{k}"))
    return markup

if __name__ == "__main__":
    print("🤖 FormulaX Bot is Fucking ...")
    bot.infinity_polling()