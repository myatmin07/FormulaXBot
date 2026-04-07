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
import time # အသစ်ထည့်ထားသည်

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
LATEST_PRODUCTS = {}

# ==========================================
# 2. DEFAULT PRODUCTS DATA
# ==========================================
default_products = {
    "gpt_plus": {"name": "🤖 ChatGPT Plus Official Plan (1 M)", "price": 25000, "stock": 30, "prefix": "FX-CP"},
    "gpt_biz":  {"name": "💼 ChatGPT Business (1 M)", "price": 30000, "stock": 50, "prefix": "FX-CB"},
    "gpt_go":   {"name": "🧠 ChatGPT Go (3 M)", "price": 9000, "stock": 5000, "prefix": "FX-CG"},
    "canva":    {"name": "🎨 Canva Edu Lifetime", "price": 5000, "stock": -1, "prefix": "FX-CV"},
    "grok_ai":  {"name": "🚀 Grok Ai (1 M)", "price": 25000, "stock": 100, "prefix": "FX-GR"},
    "perplex":  {"name": "🔍 Perplexity (1 Y)", "price": 50000, "stock": 18, "prefix": "FX-PX"},
    "capcut_pro": {"name": "✂️ Capcut Pro (1 M)", "price": 8000, "stock": -1, "prefix": "FX-CCP"},
    "capcut_team": {"name": "👥 Capcut Team (1 M)", "price": 10000, "stock": -1, "prefix": "FX-CCT"},
    "evpn_pc_1y": {"name": "💻 Express VPN 1 Y (1 Device)", "price": 10000, "stock": 50, "prefix": "FX-EPC1"},
    "evpn_pc_2y": {"name": "💻 Express VPN 2 Y (1 Device)", "price": 18000, "stock": 20, "prefix": "FX-EPC2"},
    "evpn_mob_1m_1d": {"name": "📱 Express VPN 1 M (1 Device)", "price": 2000, "stock": 50, "prefix": "FX-EM1"},
    "evpn_mob_1m_8d": {"name": "📱 Express VPN 1 M (8 Device)", "price": 11000, "stock": 50, "prefix": "FX-EM8"},
    "evpn_mob_3m_1d": {"name": "📱 Express VPN 3 M (1 Device)", "price": 5000, "stock": 50, "prefix": "FX-EM3"},
    "evpn_mob_6m_1d": {"name": "📱 Express VPN 6 M (1 Device)", "price": 8000, "stock": 50, "prefix": "FX-EM6"},
    "evpn_mob_1y_1d": {"name": "📱 Express VPN 1 Y (1 Device)", "price": 10000, "stock": 50, "prefix": "FX-EMY1"},
    "evpn_mob_2y_1d": {"name": "📱 Express VPN 2 Y (1 Device)", "price": 16000, "stock": 50, "prefix": "FX-EMY2"},
    "hid_hk_1m": {"name": "🇭🇰 Hiddify VPN 1 M (100GB)", "price": 3000, "stock": 0, "prefix": "FX-HK1", "is_hiddify": True, "days": 30, "gb": 100},
    "hid_hk_2m": {"name": "🇭🇰 Hiddify VPN 2 M (200GB)", "price": 6000, "stock": 0, "prefix": "FX-HK2", "is_hiddify": True, "days": 60, "gb": 200},
    "hid_hk_3m": {"name": "🇭🇰 Hiddify VPN 3 M (300GB)", "price": 9000, "stock": 0, "prefix": "FX-HK3", "is_hiddify": True, "days": 90, "gb": 300},
}

user_orders = {}
admin_states = {}

# ==========================================
# 3. ROBUST DB FUNCTIONS (NO MORE RESETS)
# ==========================================
def safe_load_json(filepath, default_data):
    global LATEST_PRODUCTS
    with db_lock:
        if not os.path.exists(filepath):
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(default_data, f, indent=4)
            if filepath == PRODUCTS_FILE: LATEST_PRODUCTS = copy.deepcopy(default_data)
            return copy.deepcopy(default_data)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                if filepath == PRODUCTS_FILE: LATEST_PRODUCTS = copy.deepcopy(data)
                return data
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
            if filepath == PRODUCTS_FILE and LATEST_PRODUCTS: return copy.deepcopy(LATEST_PRODUCTS)
            return copy.deepcopy(default_data)

def safe_save_json(filepath, data):
    with db_lock:
        tmp_path = filepath + ".tmp"
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            os.replace(tmp_path, filepath)
            if filepath == PRODUCTS_FILE:
                global LATEST_PRODUCTS
                LATEST_PRODUCTS = copy.deepcopy(data)
        except Exception as e:
            print(f"Save error {filepath}: {e}")

def load_products(): 
    data = safe_load_json(PRODUCTS_FILE, default_products)
    changed = False
    for k, v in default_products.items():
        if k not in data:
            data[k] = copy.deepcopy(v)
            changed = True
        else:
            if data[k]['name'] != v['name']:
                data[k]['name'] = v['name']
                changed = True
    if changed: safe_save_json(PRODUCTS_FILE, data)
    return data

def save_products(data): safe_save_json(PRODUCTS_FILE, data)
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
    
    if "gpt" in key:
        if len(parts) >= 3:
            return f"Outlook.comမှာအရင်Loginဝင်ပါ\nEmail - <code>{parts[0]}</code>\nPassword - <code>{parts[1]}</code>\nChat GPT Password - <code>{parts[2]}</code>"
        elif len(parts) == 2:
            return f"Outlook.comမှာအရင်Loginဝင်ပါ\nEmail - <code>{parts[0]}</code>\nPassword - <code>{parts[1]}</code>"
    elif key.startswith("evpn_pc_"):
        return f"License - <code>{raw_data.strip()}</code>"
    elif "hid_" in key:
        return f"Key -\n<code>{raw_data.strip()}</code>"
    else:
        if len(parts) >= 2:
            return f"Email - <code>{parts[0]}</code>\nPassword - <code>{parts[1]}</code>"
    return f"<code>{raw_data.strip()}</code>"

def process_approval(order_id, data):
    target_id = int(data['user_id'])
    key = data['key']
    qty_sold = data['qty']
    prods = load_products()
    p_info = prods.get(key)
    
    if not p_info: return
    
    # Stock အတိအကျ နှုတ်ပေးမည်
    if p_info['stock'] > 0: 
        p_info['stock'] = max(0, p_info['stock'] - qty_sold)
    save_products(prods)
    log_sale(target_id, p_info['name'], qty_sold, data['total'])
    
    delivered = []
    if p_info.get('is_hiddify'):
        for _ in range(qty_sold):
            link1, link2 = generate_hiddify_links(p_info['days'], p_info['gb'], target_id)
            if link1 and link2: 
                delivered.append(f"🔗 <b>လင့်ခ် (၁):</b>\n<code>{link1}</code>\n\n🔗 <b>လင့်ခ် (၂):</b>\n<code>{link2}</code>")
            else:
                accs = get_and_deduct_accounts(key, 1, target_id)
                if accs: delivered.append(format_acc_data(key, accs[0]))
    else:
        accs = get_and_deduct_accounts(key, qty_sold, target_id)
        if accs: 
            for a in accs: delivered.append(format_acc_data(key, a))
        
    if len(delivered) == qty_sold:
        if p_info.get('is_hiddify'):
            acc_text = "\n\n🔑 <b>သင်၏ VPN လင့်ခ်များ:</b>\n\n" + "\n\n==================\n\n".join([f"🔸 <b>အကောင့် {i}:</b>\n{a}" for i, a in enumerate(delivered, 1)])
            acc_text += "\n\n💡 <b>အသုံးပြုနည်း:</b>\n၁။ အထက်ပါ <b>လင့်ခ် (၁)</b> အား Copy ကူးပါ။\n၂။ Hiddify App ၏ <code>+</code> ခလုတ်ကိုနှိပ်ပါ။\n၃။ <code>Add from Clipboard</code> ကိုရွေးချယ်ပါ။\n<i>(အကယ်၍ လင့်ခ် ၁ အလုပ်မလုပ်ပါက လင့်ခ် ၂ ကို အသုံးပြုကြည့်ပါ)</i>"
        else:
            acc_text = "\n\n🔑 <b>အကောင့်အချက်အလက်များ:</b>\n\n" + "\n\n".join([f"🔸 <b>အကောင့် {i}:</b>\n{a}" for i, a in enumerate(delivered, 1)])
            if key.startswith('evpn'): acc_text += "\n\n⚠️ Express VPN အား သတ်မှတ်ထားသော Device အရေအတွက်အတိုင်းသာ သုံးစွဲပေးပါရန် မေတ္တာရပ်ခံအပ်ပါသည်။"
            
        bot.send_message(target_id, f"🎉 <b>အော်ဒါ အတည်ပြုပြီးပါပြီ။</b>{acc_text}", parse_mode="HTML")
        bot.send_message(ADMIN_ID, f"✅ User {target_id} ထံသို့ ပေးပို့ခြင်း အောင်မြင်ပါသည်။")
    else:
        bot.send_message(target_id, f"🎉 <b>အော်ဒါ အတည်ပြုပြီးပါပြီ။</b>\n\n⚠️ accလက်ကျန်ထည့်ထားတာမရှိသေးလို့ admin ကတစ်ဆင့်ပို့ပေးပါမယ် @FORMULA_X0 ကိုတစ်ချက်ဆက်သွယ်ပေးပါ", parse_mode="HTML")
        bot.send_message(ADMIN_ID, f"⚠️ User: {target_id}\n<b>Stock မလုံလောက်ပါ / API ချိတ်မရပါ။ Admin ကိုယ်တိုင်ပေးပါ။</b>\nProduct: {p_info['name']}")

# ==========================================
# 4. ADMIN PANEL LOGIC
# ==========================================
def admin_panel_view(chat_id):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("💰 ဈေးနှုန်းပြောင်းရန်", callback_data="admin_editprice"),
        types.InlineKeyboardButton("📦 Stock အတိုး/အလျှော့လုပ်ရန်", callback_data="admin_setstock"),
        types.InlineKeyboardButton("➕ အကောင့်သစ်များထည့်သွင်းရန်", callback_data="admin_addacc"),
        types.InlineKeyboardButton("👀 သိမ်းဆည်းထားသောအကောင့်များကြည့်ရန်", callback_data="admin_viewacc"),
        types.InlineKeyboardButton("❌ ပိတ်မည်", callback_data="admin_close")
    )
    bot.send_message(chat_id, "👨‍💻 <b>Admin Control Panel</b>\n\nလုပ်ဆောင်လိုသော အရာကို ရွေးချယ်ပါ:", reply_markup=markup, parse_mode="HTML")

@bot.message_handler(commands=['admin'])
def admin_command(m):
    if m.from_user.id == ADMIN_ID: admin_panel_view(m.chat.id)

def get_admin_product_menu(action):
    markup = types.InlineKeyboardMarkup(row_width=1)
    prods = load_products()
    for k, p in prods.items():
        if action == "addacc" and k == "canva": continue 
        markup.add(types.InlineKeyboardButton(p['name'], callback_data=f"adm_{action}_{k}"))
    markup.add(types.InlineKeyboardButton("⬅️ Admin Panel သို့", callback_data="admin_back"))
    return markup

def step_setstock(m, key):
    try:
        new_stock = int(m.text.strip())
        prods = load_products()
        prods[key]['stock'] = new_stock
        save_products(prods)
        bot.send_message(m.chat.id, f"✅ <b>{prods[key]['name']}</b> အတွက် Stock အသစ် <b>{new_stock}</b> သို့ ပြောင်းလဲပြီးပါပြီ။", parse_mode="HTML")
    except ValueError:
        bot.send_message(m.chat.id, "❌ ဂဏန်းသာ ရိုက်ထည့်ပါ။")

def step_edit_price(m, key):
    try:
        new_price = int(m.text.strip())
        prods = load_products()
        prods[key]['price'] = new_price
        save_products(prods)
        bot.send_message(m.chat.id, f"✅ <b>{prods[key]['name']}</b> အတွက် ဈေးနှုန်းအသစ် <b>{new_price} Ks</b> သို့ ပြောင်းလဲသတ်မှတ်ပြီးပါပြီ။", parse_mode="HTML")
    except ValueError:
        bot.send_message(m.chat.id, "❌ မှားယွင်းနေပါသည်။ ဈေးနှုန်းကို ဂဏန်းဖြင့်သာ ရိုက်ထည့်ပါ။")

def step_addacc_data(m, key):
    accounts = m.text.strip().split('\n')
    admin_states[ADMIN_ID] = {'key': key, 'accs': accounts}
    msg = bot.send_message(m.chat.id, f"အကောင့် <b>{len(accounts)}</b> ခု လက်ခံရရှိပါတယ်။\n\nဒီအကောင့်တစ်ခုစီကို <b>လူဘယ်နှစ်ယောက်ကို ရောင်းမည်လဲ?</b> (ဥပမာ - 3)", parse_mode="HTML")
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
        
        prods = load_products()
        added_stock = len(acc_list) * uses
        if prods[key]['stock'] == -1: prods[key]['stock'] = 0
        prods[key]['stock'] += added_stock
        save_products(prods)
        
        bot.send_message(m.chat.id, f"✅ အကောင့်များ သိမ်းဆည်းပြီးပါပြီ။\nStock အရေအတွက် <b>{added_stock}</b> ခု တိုးသွားပါပြီ။", parse_mode="HTML")
        admin_states.pop(ADMIN_ID, None)
    except ValueError:
        bot.send_message(m.chat.id, "❌ ဂဏန်းသာ ရိုက်ထည့်ပါ။")

# ==========================================
# 5. CUSTOM QUANTITY LOGIC
# ==========================================
def step_custom_qty(m, uid, cid):
    order = user_orders.get(uid)
    if not order: return
    
    try:
        qty = int(m.text.strip())
        if qty < 1:
            msg = bot.send_message(cid, "❌ အရေအတွက်မှာ အနည်းဆုံး ၁ ခု ဖြစ်ရပါမည်။ ဂဏန်းပြန်ရိုက်ထည့်ပါ:")
            bot.register_next_step_handler(msg, step_custom_qty, uid, cid)
            return
            
        prods = load_products()
        p = prods[order['key']]
        
        if p['stock'] != -1 and qty > p['stock']:
            bot.send_message(cid, f"❌ တောင်းပန်ပါသည်။ လက်ရှိတွင် Stock အနေဖြင့် <b>({p['stock']})</b> ခုသာ ကျန်ရှိပါတော့သည်။ ကျေးဇူးပြု၍ /start ကိုနှိပ်ကာ ပြန်လည်ရွေးချယ်ပါ။", parse_mode="HTML")
            return

        user_orders[uid]["qty"] = qty
        if user_orders[uid]["key"] == "canva":
            msg = bot.send_message(cid, "📧 သင့်၏ Canva အသုံးပြုမည့် Email ကို စာရိုက်၍ ပေးပို့ပါ:")
            bot.register_next_step_handler(msg, lambda msg_txt: [user_orders.get(uid).update({"email": msg_txt.text}), confirm(cid, uid)][-1])
        else:
            confirm(cid, uid)
    except ValueError:
        msg = bot.send_message(cid, "❌ မှားယွင်းနေပါသည်။ ဝယ်ယူမည့် အရေအတွက်ကို ဂဏန်းဖြင့်သာ ရိုက်ထည့်ပါ (ဥပမာ - 5):")
        bot.register_next_step_handler(msg, step_custom_qty, uid, cid)

def confirm(cid, uid):
    order = user_orders.get(uid)
    if not order: return
    prods = load_products()
    p = prods[order['key']]
    total = p['price'] * order['qty']
    
    msg = f"🛒 <b>အော်ဒါ အတည်ပြုခြင်း</b>\n\nပစ္စည်း: {p['name']}\nအရေအတွက်: {order['qty']}\nစုစုပေါင်းကျသင့်ငွေ: <b>{total} Ks</b>"
    if order.get("email"): msg += f"\nCanva Email: {order['email']}"
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("✅ ငွေပေးချေမည်", callback_data="pay"),
        types.InlineKeyboardButton("❌ ပယ်ဖျက်မည်", callback_data="page_main_0")
    )
    bot.send_message(cid, msg, reply_markup=markup, parse_mode="HTML")

# ==========================================
# 6. USER PAGINATION MENU LOGIC 
# ==========================================
def get_menu(cat="main", page=0, user_id=None):
    markup = types.InlineKeyboardMarkup(row_width=1)
    prods = load_products()
    items_per_page = 4
    
    if cat == "main":
        if page == 0:
            markup.add(types.InlineKeyboardButton("🛡️ Express VPN", callback_data="cat_evpn_0"))
            markup.add(types.InlineKeyboardButton("🚀 Hiddify VPN", callback_data="cat_hiddify_0"))
            markup.add(types.InlineKeyboardButton("✂️ Capcut Premium", callback_data="cat_capcut_0"))
            
        ai_keys = ["gpt_plus", "gpt_biz", "gpt_go", "canva", "grok_ai", "perplex"]
        start = page * items_per_page
        end = start + items_per_page
        page_keys = ai_keys[start:end]
        
        for k in page_keys:
            if k in prods:
                p = prods[k]
                s = "" if p['stock'] == -1 else (" ❌" if p['stock'] == 0 else f" [{p['stock']}]")
                markup.add(types.InlineKeyboardButton(f"{p['name']} • {p['price']} Ks{s}", callback_data=f"buy_{k}" if p['stock'] != 0 else "oos"))
                
        nav = []
        if page > 0: nav.append(types.InlineKeyboardButton("⬅️ ယခင်စာမျက်နှာ", callback_data=f"page_main_{page-1}"))
        if end < len(ai_keys): nav.append(types.InlineKeyboardButton("နောက်စာမျက်နှာ ➡️", callback_data=f"page_main_{page+1}"))
        if nav: markup.row(*nav)
        
        markup.row(
            types.InlineKeyboardButton("📋 မှတ်တမ်း", callback_data="my_orders"),
            types.InlineKeyboardButton("💬 Admin သို့", callback_data="contact_admin")
        )
        if user_id == ADMIN_ID: markup.add(types.InlineKeyboardButton("⚙️ Admin Panel", callback_data="open_admin_panel"))
        
    elif cat == "cat_evpn":
        markup.add(types.InlineKeyboardButton("📱 Mobile အတွက်", callback_data="cat_ev_m_0"))
        markup.add(types.InlineKeyboardButton("💻 PC အတွက်", callback_data="cat_ev_p_0"))
        markup.row(types.InlineKeyboardButton("📋 မှတ်တမ်း", callback_data="my_orders"), types.InlineKeyboardButton("💬 Admin သို့", callback_data="contact_admin"))
        markup.add(types.InlineKeyboardButton("⬅️ ပင်မမီနူးသို့", callback_data="page_main_0"))
        
    elif cat == "cat_capcut":
        keys = ["capcut_pro", "capcut_team"]
        for k in keys:
            if k in prods:
                p = prods[k]
                s = "" if p['stock'] == -1 else (" ❌" if p['stock'] == 0 else f" [{p['stock']}]")
                markup.add(types.InlineKeyboardButton(f"{p['name']} • {p['price']} Ks{s}", callback_data=f"buy_{k}" if p['stock'] != 0 else "oos"))
        markup.row(types.InlineKeyboardButton("📋 မှတ်တမ်း", callback_data="my_orders"), types.InlineKeyboardButton("💬 Admin သို့", callback_data="contact_admin"))
        markup.add(types.InlineKeyboardButton("⬅️ ပင်မမီနူးသို့", callback_data="page_main_0"))
        
    else:
        pre = "evpn_mob_" if cat == "cat_ev_m" else "evpn_pc_" if cat == "cat_ev_p" else "hid_hk_"
        keys = [k for k in prods.keys() if k.startswith(pre)]
        start = page * items_per_page
        end = start + items_per_page
        page_keys = keys[start:end]
        
        for k in page_keys:
            if k in prods:
                p = prods[k]
                s = "" if p['stock'] == -1 else (" ❌" if p['stock'] == 0 else f" [{p['stock']}]")
                markup.add(types.InlineKeyboardButton(f"{p['name']} • {p['price']} Ks{s}", callback_data=f"buy_{k}" if p['stock'] != 0 else "oos"))
                
        nav = []
        if page > 0: nav.append(types.InlineKeyboardButton("⬅️ ယခင်", callback_data=f"{cat}_{page-1}"))
        if end < len(keys): nav.append(types.InlineKeyboardButton("နောက်သို့ ➡️", callback_data=f"{cat}_{page+1}"))
        if nav: markup.row(*nav)
        
        markup.row(types.InlineKeyboardButton("📋 မှတ်တမ်း", callback_data="my_orders"), types.InlineKeyboardButton("💬 Admin သို့", callback_data="contact_admin"))
        back_cat = "cat_evpn_0" if "ev_" in cat else "page_main_0"
        markup.add(types.InlineKeyboardButton("⬅️ နောက်သို့ ပြန်သွားမည်", callback_data=back_cat))
        
    return markup

@bot.message_handler(commands=['start'])
def start(m):
    msg = "👋 <b>Formula X Store မှ နွေးထွေးစွာ ကြိုဆိုပါတယ်။</b>\n\nကိုယ်တိုင်အလွယ်တကူ ဝယ်ယူနိုင်ပြီး ငွေလွှဲပြေစာ ပို့ပြီးသည်နှင့် အကောင့်/Key များကို အလိုအလျောက် ရရှိမည်ဖြစ်ပါသည်။\n\n💡 <i>[ ] အတွင်းရှိ ဂဏန်းမှာ လက်ကျန်အရေအတွက်ဖြစ်ပါသည်။</i>"
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
                types.InlineKeyboardButton("✅ Approve ပြုလုပ်မည်", callback_data=f"approve_{oid}"),
                types.InlineKeyboardButton("❌ ငွေမဝင်ပါ Reject", callback_data=f"reject_{oid}")
            )
            caption = f"🔔 <b>ငွေလွှဲပြေစာ အသစ်!</b>\n\nOrder ID: <code>{oid}</code>\nUser: {uid}\nကျသင့်ငွေ: {pending[oid]['total']} Ks\nProduct: {pending[oid]['key']}"
            bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=caption, reply_markup=markup, parse_mode="HTML")
            bot.reply_to(message, "✅ <b>ငွေလွှဲပြေစာ လက်ခံရရှိပါပြီ။</b>\n\nAdmin မှ စစ်ဆေးပြီးပါက သင့်ထံသို့ အကောင့်အချက်အလက်များ အလိုအလျောက် ဝင်ရောက်လာပါမည်။", parse_mode="HTML")
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
            bot.edit_message_text("💰 ဈေးနှုန်းပြောင်းလိုသော ပစ္စည်းကို ရွေးချယ်ပါ:", cid, mid, reply_markup=get_admin_product_menu("price"))
        elif call.data == "admin_setstock":
            bot.edit_message_text("📦 Stock ပြင်လိုသော ပစ္စည်းကို ရွေးချယ်ပါ:", cid, mid, reply_markup=get_admin_product_menu("stk"))
        elif call.data == "admin_addacc":
            bot.edit_message_text("➕ အကောင့်သစ်ထည့်လိုသော ပစ္စည်းကို ရွေးချယ်ပါ:", cid, mid, reply_markup=get_admin_product_menu("addacc"))
        elif call.data == "admin_viewacc":
            bot.edit_message_text("👀 အကောင့်ကြည့်လိုသော ပစ္စည်းကို ရွေးချယ်ပါ:", cid, mid, reply_markup=get_admin_product_menu("vw"))
            
        elif call.data.startswith("adm_price_"):
            key = call.data.split("adm_price_")[1]
            prods = load_products()
            p = prods[key]
            msg = bot.send_message(cid, f"<b>{p['name']}</b>\nလက်ရှိဈေးနှုန်း: {p['price']} Ks\n\nဈေးနှုန်းအသစ်ကို ဂဏန်းဖြင့် ရိုက်ထည့်ပါ:", parse_mode="HTML")
            bot.register_next_step_handler(msg, step_edit_price, key)
            
        elif call.data.startswith("adm_stk_"):
            key = call.data.split("adm_stk_")[1]
            prods = load_products()
            p = prods[key]
            msg = bot.send_message(cid, f"<b>{p['name']}</b>\nလက်ရှိ Stock: {p['stock']}\n\nStock အသစ်ကို စာရိုက်၍ ပေးပို့ပါ:", parse_mode="HTML")
            bot.register_next_step_handler(msg, step_setstock, key)
            
        elif call.data.startswith("adm_addacc_"):
            key = call.data.split("adm_addacc_")[1]
            prods = load_products()
            p = prods[key]
            if "gpt" in key:
                prompt_text = f"<b>{p['name']}</b> အတွက် <b>Email နှင့် Password များ</b> ပေးပို့ပါ။\n\n(<b>Email|Email_Pass|GPT_Pass</b> ပုံစံဖြင့် တစ်ကြောင်းစီပို့ပါ)\nဥပမာ:\nuser@outlook.com|pass123|gpt456"
            elif key.startswith("evpn_pc_"):
                prompt_text = f"<b>{p['name']}</b> အတွက် <b>License Key များ</b> ပေးပို့ပါ။\n\n(တစ်ကြောင်းစီပို့ပါ)\nဥပမာ:\nEXYZ123456789"
            elif p.get('is_hiddify') or "hid_" in key:
                prompt_text = f"<b>{p['name']}</b> အတွက် <b>VPN Link များ</b> ပေးပို့ပါ။\n\nဥပမာ:\nvless://..."
            else:
                prompt_text = f"<b>{p['name']}</b> အတွက် <b>Email နှင့် Password များ</b> ပေးပို့ပါ။\n\n(<b>Email|Password</b> ပုံစံဖြင့် တစ်ကြောင်းစီပို့ပါ)\nဥပမာ:\nuser@gmail.com|pass123"
            msg = bot.send_message(cid, prompt_text, parse_mode="HTML")
            bot.register_next_step_handler(msg, step_addacc_data, key)
            
        elif call.data.startswith("adm_vw_"):
            key = call.data.split("adm_vw_")[1]
            accs = load_accounts().get(key, [])
            if not accs: bot.send_message(cid, "ဤပစ္စည်းအတွက် သိမ်းဆည်းထားသော အကောင့်မရှိပါ။")
            else:
                text = f"📋 <b>အကောင့်စာရင်း ({len(accs)} ခု)</b>\n\n"
                for i, a in enumerate(accs, 1): text += f"{i}. <code>{a['data']}</code> (ကျန်: {a['uses_left']} ခါ)\n"
                bot.send_message(cid, text, parse_mode="HTML")

        elif call.data.startswith("page_main_"): 
            page = int(call.data.split("_")[2])
            bot.edit_message_text("👋 <b>Formula X Store</b>\n\nအောက်ပါ Menu များမှတစ်ဆင့် လိုအပ်သော ပစ္စည်းများကို ရွေးချယ်နိုင်ပါသည်။", cid, mid, reply_markup=get_menu("main", page, uid), parse_mode="HTML")
            
        elif call.data.startswith("cat_"):
            parts = call.data.split("_")
            page = int(parts[-1])
            cat = "_".join(parts[:-1])
            menu_text = "👋 <b>Formula X Store</b>\n\nအောက်ပါ Menu များမှတစ်ဆင့် လိုအပ်သော ပစ္စည်းများကို ရွေးချယ်နိုင်ပါသည်။"
            if cat == "cat_evpn" or cat.startswith("cat_ev_"): menu_text = "🛡️ <b>Express VPN</b>\n\nလိုအပ်သော Plan ကို ရွေးချယ်ပါ -"
            elif cat == "cat_hiddify": menu_text = "🚀 <b>Hiddify VPN</b>\n\nလိုအပ်သော Plan ကို ရွေးချယ်ပါ -"
            elif cat == "cat_capcut": menu_text = "✂️ <b>Capcut Premium</b>\n\nလိုအပ်သော Plan ကို ရွေးချယ်ပါ -"
            bot.edit_message_text(menu_text, cid, mid, reply_markup=get_menu(cat, page, uid), parse_mode="HTML")
            
        elif call.data == "oos": 
            bot.answer_callback_query(call.id, "ယခုပစ္စည်းမှာ လက်ကျန်ကုန်နေပါသည် ခင်ဗျာ။", show_alert=True)
            
        elif call.data.startswith("buy_"):
            key = call.data.split("buy_")[1]
            user_orders[uid] = {"key": key}
            prods = load_products()
            markup = types.InlineKeyboardMarkup(row_width=1)
            for i in range(1, 4): markup.add(types.InlineKeyboardButton(f"အရေအတွက်: {i} ခု", callback_data=f"qty_{i}"))
            markup.add(types.InlineKeyboardButton("✍️ စိတ်ကြိုက်အရေအတွက်", callback_data="qty_custom"))
            markup.add(types.InlineKeyboardButton("🏠 ပင်မမီနူးသို့", callback_data="page_main_0"))
            bot.edit_message_text(f"ပစ္စည်း: <b>{prods[key]['name']}</b>\n\nဝယ်ယူလိုသော အရေအတွက် ရွေးပါ -", cid, mid, reply_markup=markup, parse_mode="HTML")
            
        elif call.data.startswith("qty_"):
            if uid not in user_orders or "key" not in user_orders[uid]: 
                bot.answer_callback_query(call.id, "ကျေးဇူးပြု၍ ပစ္စည်းကို ပြန်ရွေးချယ်ပါ။", show_alert=True)
                return
            if call.data == "qty_custom":
                msg = bot.send_message(cid, "✍️ ဝယ်ယူလိုသော အရေအတွက်ကို ဂဏန်းဖြင့် ရိုက်ထည့်ပါ (ဥပမာ - 5):")
                bot.register_next_step_handler(msg, step_custom_qty, uid, cid)
                return
            qty = int(call.data.split("_")[1])
            user_orders[uid]["qty"] = qty
            if user_orders[uid]["key"] == "canva":
                msg = bot.send_message(cid, "📧 သင့်၏ Canva အသုံးပြုမည့် Email ကို စာရိုက်၍ ပေးပို့ပါ:")
                bot.register_next_step_handler(msg, lambda m: [user_orders.get(uid).update({"email": m.text}), confirm(cid, uid)][-1])
            else: 
                bot.delete_message(cid, mid)
                confirm(cid, uid)
                
        elif call.data == "pay":
            if uid not in user_orders or "key" not in user_orders[uid]: 
                bot.answer_callback_query(call.id, "ကျေးဇူးပြု၍ ပစ္စည်းကို ပြန်ရွေးချယ်ပါ။", show_alert=True)
                return
            oid = generate_random_note()
            user_orders[uid]["oid"] = oid
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(types.InlineKeyboardButton("Wave Pay ဖြင့်ချေမည်", callback_data="p_w"), types.InlineKeyboardButton("KBZ Pay ဖြင့်ချေမည်", callback_data="p_k"), types.InlineKeyboardButton("⬅️ ပင်မမီနူးသို့", callback_data="page_main_0"))
            bot.edit_message_text(f"🛒 အော်ဒါအမှတ်စဉ်: <b>{oid}</b>\n\nငွေပေးချေမှု နည်းလမ်းရွေးချယ်ပါ:", cid, mid, reply_markup=markup, parse_mode="HTML")
            
        elif call.data.startswith("p_"):
            if uid not in user_orders or "qty" not in user_orders[uid]: 
                bot.answer_callback_query(call.id, "ကျေးဇူးပြု၍ ပစ္စည်းကို ပြန်ရွေးချယ်ပါ။", show_alert=True)
                return
            order = user_orders[uid]
            prods = load_products()
            p = prods[order['key']]
            total = p['price'] * order['qty']
            
            pending = load_pending()
            pending[order['oid']] = {"user_id": uid, "key": order['key'], "qty": order['qty'], "total": total}
            save_pending(pending)
            user_orders[uid]["awaiting_slip"] = order['oid']
            
            warranty_msg = "🛡️ <b>Full Warranty</b> ပေးထားပါသဖြင့် ယုံကြည်စိတ်ချစွာ ဝယ်ယူနိုင်ပါသည်။"
            if order['key'] == "canva": warranty_msg = "🛡️ <b>Warranty 1 Year</b> ပေးထားပါသဖြင့် ယုံကြည်စိတ်ချစွာ ဝယ်ယူနိုင်ပါသည်။"
            
            pay_msg = f"💳 <b>ငွေပေးချေရန်</b>\n\nဖုန်း: <code>09770088206</code>\nအမည်: Myat Min Lwin\nကျသင့်ငွေ: <b>{total} Ks</b>\n\n📝 <b>မှတ်ချက် (Note):</b> <code>{order['oid']}</code>\n\n⚠️ <i>ဝယ်ယူထားသောပစ္စည်းများ မြန်မြန်ဆန်ဆန်ရရှိစေရန် ပေးထားသော Note အားတိကျစွာထည့်ပေးပါ။</i>\n\n{warranty_msg}\n\n✅ <b>ငွေလွှဲပြေစာကို ဤ Chat သို့ ဓာတ်ပုံအနေဖြင့် ပို့ပေးပါ။</b>"
            bot.edit_message_text(pay_msg, cid, mid, parse_mode="HTML")
            
        elif call.data.startswith("approve_") or call.data.startswith("reject_"):
            action, oid = call.data.split("_")
            pending = load_pending()
            if oid not in pending: 
                bot.answer_callback_query(call.id, "ဤအော်ဒါအား အတည်ပြုပြီး (သို့) ပယ်ဖျက်ပြီး ဖြစ်ပါသည်။", show_alert=True)
                return
            data = pending[oid]
            if action == "approve":
                bot.edit_message_caption(f"✅ APPROVED\nOrder ID: {oid}\nUser ထံသို့ Key ပေးပို့နေပါသည်...", cid, mid)
                process_approval(oid, data)
            else:
                bot.send_message(data['user_id'], f"❌ လူကြီးမင်း၏ အော်ဒါ (ID: {oid}) ငွေလွှဲပြေစာ မှားယွင်းနေသဖြင့် ပယ်ဖျက်လိုက်ပါသည်။")
                bot.edit_message_caption(f"❌ REJECTED\nOrder ID: {oid}\nငွေမဝင်သဖြင့် ပယ်ဖျက်လိုက်ပါသည်။", cid, mid)
            del pending[oid]
            save_pending(pending)
            
        elif call.data == "contact_admin":
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(types.InlineKeyboardButton("🏠 ပင်မမီနူးသို့", callback_data="page_main_0"))
            bot.edit_message_text("👨‍💻 သိလိုသည်များကို @FORMULA_X0 သို့ ဆက်သွယ်မေးမြန်းနိုင်ပါသည်။", cid, mid, reply_markup=markup)
            
        elif call.data == "my_orders":
            hist = load_json(HISTORY_FILE, {}).get(str(uid), [])
            msg = "📋 <b>သင်၏ ဝယ်ယူမှုမှတ်တမ်းများ</b>\n\n" + "\n".join([f"📦 {h['product']} - {h['total']} Ks" for h in hist[-5:]]) if hist else "မှတ်တမ်း မရှိသေးပါ။"
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(types.InlineKeyboardButton("🏠 ပင်မမီနူးသို့", callback_data="page_main_0"))
            bot.edit_message_text(msg, cid, mid, reply_markup=markup, parse_mode="HTML")
            
    except telebot.apihelper.ApiTelegramException as e:
        if "message is not modified" not in str(e).lower(): print(f"Telegram API Error: {e}")
    except Exception as e:
        print(f"Callback Error: {e}")

if __name__ == "__main__":
    print("🤖 FormulaX Bot စတင်အလုပ်လုပ်နေပါပြီ...")
    while True:
        try:
            bot.polling(none_stop=True, timeout=60, long_polling_timeout=60)
        except requests.exceptions.ConnectionError:
            print("Connection Error. Reconnecting in 5 seconds...")
            time.sleep(5)
        except Exception as e:
            print(f"Bot Error: {e}")
            time.sleep(5)