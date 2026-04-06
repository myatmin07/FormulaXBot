import telebot
from telebot import types
import json
import os
import random
import threading
import uuid
import requests
from datetime import datetime
from flask import Flask, request

# ==========================================
# 1. CONFIGURATION
# ==========================================
API_TOKEN = '8483869457:AAFBlSIu_6biWRAZ7lgGBrT-smj7C7tsQ20'
ADMIN_ID = 5890904598
bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

SALES_FILE = "formula_x_sales.json"
HISTORY_FILE = "formula_x_user_history.json"
PRODUCTS_FILE = "formula_x_products.json"
ACCOUNTS_FILE = "formula_x_accounts.json"
PENDING_FILE = "formula_x_pending.json"
SETTINGS_FILE = "formula_x_settings.json"

# ==========================================
# 2. DEFAULT SETTINGS & DATA
# ==========================================
default_settings = {
    "hiddify_url": "https://45.39.190.143.sslip.io/rJVGQZ4DWgZBDLdMAoCoOR/", 
    "hiddify_api_key": "853bce49-34dd-4e8b-a5f6-e90003ef458c" 
}

default_products = {
    "gpt_plus": {"name": "🤖 ChatGPT Plus Official Plan(1M)", "price": 25000, "stock": 30, "prefix": "FX-CP"},
    "gpt_biz":  {"name": "💼 ChatGPT Business (1M)", "price": 30000, "stock": 50, "prefix": "FX-CB"},
    "gpt_go":   {"name": "🧠 ChatGPT Go (3M)", "price": 9000, "stock": 5000, "prefix": "FX-CG"},
    "canva":    {"name": "🎨 Canva Edu Lifetime", "price": 5000, "stock": -1, "prefix": "FX-CV"},
    "grok_ai":  {"name": "🚀 Grok Ai (1M)", "price": 25000, "stock": 100, "prefix": "FX-GR"},
    "perplex":  {"name": "🔍 Perplexity (1Y)", "price": 50000, "stock": 18, "prefix": "FX-PX"},
    "evpn_pc_1y": {"name": "💻 1 YEAR (1 Device)", "price": 10000, "stock": 50, "prefix": "FX-EPC1"},
    "evpn_pc_2y": {"name": "💻 2 YEAR (1 Device)", "price": 18000, "stock": 20, "prefix": "FX-EPC2"},
    "evpn_mob_1m_1d": {"name": "📱 1 MONTH (1 Device)", "price": 2000, "stock": 50, "prefix": "FX-EM1"},
    "evpn_mob_1m_8d": {"name": "📱 1 MONTH (8 Devices)", "price": 11000, "stock": 50, "prefix": "FX-EM8"},
    "evpn_mob_3m_1d": {"name": "📱 3 MONTH (1 Device)", "price": 5000, "stock": 50, "prefix": "FX-EM3"},
    "evpn_mob_6m_1d": {"name": "📱 6 MONTH (1 Device)", "price": 8000, "stock": 50, "prefix": "FX-EM6"},
    "evpn_mob_1y_1d": {"name": "📱 1 YEAR (1 Device)", "price": 10000, "stock": 50, "prefix": "FX-EMY1"},
    "evpn_mob_2y_1d": {"name": "📱 2 YEAR (1 Device)", "price": 16000, "stock": 50, "prefix": "FX-EMY2"},
    "hid_hk_1m": {"name": "🇭🇰 1 Month (100GB)", "price": 3000, "stock": -1, "prefix": "FX-HK1", "is_hiddify": True, "days": 30, "gb": 100},
    "hid_hk_2m": {"name": "🇭🇰 2 Month (200GB)", "price": 6000, "stock": -1, "prefix": "FX-HK2", "is_hiddify": True, "days": 60, "gb": 200},
    "hid_hk_3m": {"name": "🇭🇰 3 Month (300GB)", "price": 9000, "stock": -1, "prefix": "FX-HK3", "is_hiddify": True, "days": 90, "gb": 300},
}

user_orders = {}

# ==========================================
# 3. HELPER FUNCTIONS
# ==========================================
def load_json(filepath, default_data):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f: return json.load(f)
        except: return default_data
    save_json(filepath, default_data)
    return default_data

def save_json(filepath, data):
    with open(filepath, "w", encoding="utf-8") as f: json.dump(data, f, indent=4)

def load_settings(): 
    settings = load_json(SETTINGS_FILE, default_settings)
    if "your-panel-domain" in settings.get("hiddify_url", ""):
        save_json(SETTINGS_FILE, default_settings)
        return default_settings
    return settings

def load_products(): 
    data = load_json(PRODUCTS_FILE, default_products)
    changed = False
    for k, v in default_products.items():
        if k not in data:
            data[k] = v
            changed = True
    if changed:
        save_products(data)
    return data

def save_products(data): save_json(PRODUCTS_FILE, data)
def load_accounts(): return load_json(ACCOUNTS_FILE, {})
def save_accounts(data): save_json(ACCOUNTS_FILE, data)
def load_pending(): return load_json(PENDING_FILE, {})
def save_pending(data): save_json(PENDING_FILE, data)

def log_sale(user_id, product_name, qty, total):
    date_str = datetime.now().strftime("%Y-%m-%d")
    sale_entry = {"product": product_name, "qty": qty, "total": total, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    
    admin_data = load_json(SALES_FILE, {})
    if date_str not in admin_data: admin_data[date_str] = []
    admin_data[date_str].append(sale_entry)
    save_json(SALES_FILE, admin_data)
    
    user_history = load_json(HISTORY_FILE, {})
    str_uid = str(user_id)
    if str_uid not in user_history: user_history[str_uid] = []
    user_history[str_uid].append(sale_entry)
    save_json(HISTORY_FILE, user_history)

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

def generate_hiddify_user(days, gb, user_id):
    settings = load_settings()
    base_url = settings.get("hiddify_url", "").strip()
    api_key = settings.get("hiddify_api_key", "").strip()
    
    if not base_url or not api_key:
        return None 
        
    if not base_url.endswith("/"): base_url += "/"
    api_url = f"{base_url}api/v1/user/"
    
    new_uuid = str(uuid.uuid4())
    payload = [{
        "uuid": new_uuid, 
        "name": f"FX_{user_id}_{random.randint(100,999)}", 
        "usage_limit_GB": gb, 
        "package_days": days, 
        "mode": "no_reset", 
        "comment": "FormulaX Bot Auto-Gen"
    }]
    
    headers = {
        "Accept": "application/json",
        "Hiddify-API-Key": api_key
    }
    
    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=15)
        if response.status_code in [200, 201]:
            return f"{base_url}{new_uuid}/"
        return None
    except Exception: 
        return None

def process_approval(order_id, data, is_auto=False):
    target_id = int(data['user_id'])
    key = data['key']
    qty_sold = data['qty']
    prods = load_products()
    p_info = prods.get(key)
    
    if not p_info: return
    
    if p_info['stock'] != -1: 
        p_info['stock'] = max(0, p_info['stock'] - qty_sold)
    save_products(prods)
    log_sale(target_id, p_info['name'], qty_sold, data['total'])
    
    delivered = []
    if p_info.get('is_hiddify'):
        for _ in range(qty_sold):
            link = generate_hiddify_user(p_info['days'], p_info['gb'], target_id)
            if link: delivered.append(f"🌐 <b>သင်၏ Server Link (Key):</b>\n<code>{link}</code>")
    else:
        accs = get_and_deduct_accounts(key, qty_sold, target_id)
        if accs: delivered = accs
        
    tag = "⚡ <b>(Auto)</b>" if is_auto else "✅ <b>(Admin)</b>"
    
    if len(delivered) == qty_sold:
        acc_text = "\n\n🔑 <b>အကောင့်အချက်အလက်များ:</b>\n\n" + "\n\n".join([f"{i}. {a}" for i, a in enumerate(delivered, 1)])
        if key.startswith('evpn'): acc_text += "\n\n⚠️ Express VPN အား သတ်မှတ်ထားသော Device အရေအတွက်အတိုင်းသာ သုံးစွဲပေးပါရန် မေတ္တာရပ်ခံအပ်ပါသည်။"
        
        bot.send_message(target_id, f"🎉 <b>အော်ဒါ အတည်ပြုပြီးပါပြီ။ {tag}</b>{acc_text}", parse_mode="HTML")
        bot.send_message(ADMIN_ID, f"{tag} အတည်ပြုခြင်း အောင်မြင်ပါသည်။\n\nUser: {target_id}\nProduct: {p_info['name']}")
    else:
        bot.send_message(target_id, f"🎉 <b>အော်ဒါ အတည်ပြုပြီးပါပြီ။ {tag}</b>\n\n⚠️ သို့သော် စနစ်အတွင်း Stock မလုံလောက်သဖြင့် Admin မှ အကောင့်ကို ခေတ္တနေလျှင် ကိုယ်တိုင် ပေးပို့ပေးပါမည်။ ကျေးဇူးပြု၍ ခေတ္တစောင့်ဆိုင်းပေးပါ။", parse_mode="HTML")
        bot.send_message(ADMIN_ID, f"⚠️ {tag}\nUser: {target_id}\n<b>Stock မလုံလောက်ပါ / Hiddify API ချိတ်မရပါ။ Admin ကိုယ်တိုင် ပေးပို့ပါ။</b>")

# ==========================================
# 4. TELEGRAM BOT UI & LOGIC
# ==========================================
def get_menu(cat="main"):
    markup = types.InlineKeyboardMarkup(row_width=1)
    prods = load_products()
    if cat == "main":
        markup.add(types.InlineKeyboardButton("🛡️ Express VPN", callback_data="cat_evpn"), 
                   types.InlineKeyboardButton("🚀 Hiddify VPN", callback_data="cat_hiddify"))
        for k in ["gpt_plus", "gpt_biz", "gpt_go", "canva", "grok_ai", "perplex"]:
            if k in prods:
                p = prods[k]
                s = f" (လက်ကျန်: {p['stock']})" if p['stock'] != -1 else ""
                markup.add(types.InlineKeyboardButton(f"{p['name']} • {p['price']} MMK{s}", callback_data=f"buy_{k}" if p['stock'] != 0 else "oos"))
        markup.add(types.InlineKeyboardButton("📋 ကျွန်ုပ်၏ ဝယ်ယူမှုများ", callback_data="my_orders"), 
                   types.InlineKeyboardButton("💬 Admin နှင့် ဆက်သွယ်ရန်", callback_data="contact_admin"))
    elif cat == "cat_evpn":
        markup.add(types.InlineKeyboardButton("📱 Mobile အတွက်", callback_data="cat_ev_m"), 
                   types.InlineKeyboardButton("💻 PC အတွက်", callback_data="cat_ev_p"), 
                   types.InlineKeyboardButton("⬅️ ပင်မမီနူးသို့ ပြန်သွားမည်", callback_data="main"))
    else:
        pre = "evpn_mob_" if cat == "cat_ev_m" else "evpn_pc_" if cat == "cat_ev_p" else "hid_hk_"
        for k, p in prods.items():
            if k.startswith(pre):
                s = f" (လက်ကျန်: {p['stock']})" if p['stock'] != -1 and not p.get('is_hiddify') else ""
                markup.add(types.InlineKeyboardButton(f"{p['name']} • {p['price']} MMK{s}", callback_data=f"buy_{k}" if p['stock'] != 0 else "oos"))
        markup.add(types.InlineKeyboardButton("⬅️ နောက်သို့ ပြန်သွားမည်", callback_data="cat_evpn" if cat.startswith("cat_ev_") else "main"))
    return markup

@bot.message_handler(commands=['start'])
def start(m):
    msg = "👋 <b>Formula X Store မှ နွေးထွေးစွာ ကြိုဆိုပါတယ်။</b>\n\nကိုယ်တိုင်အလွယ်တကူ ဝယ်ယူနိုင်ပြီး ငွေလွှဲပြေစာ ပို့ပြီးသည်နှင့် အကောင့်/Key များကို အလိုအလျောက် ရရှိမည်ဖြစ်ပါသည်။\n\n💡 <i>အကူအညီလိုအပ်ပါက @FORMULA_X0 သို့မဟုတ် အောက်ပါ 'Admin နှင့် ဆက်သွယ်ရန်' ကို နှိပ်ပါ။</i>"
    bot.send_message(m.chat.id, msg, reply_markup=get_menu("main"), parse_mode="HTML")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    uid = message.from_user.id
    if uid in user_orders and "awaiting_slip" in user_orders[uid]:
        oid = user_orders[uid]["awaiting_slip"]
        pending = load_pending()
        
        if oid in pending:
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton("✅ Approve ပြုလုပ်မည်", callback_data=f"approve_{oid}"),
                types.InlineKeyboardButton("❌ ငွေမဝင်ပါ (Reject)", callback_data=f"reject_{oid}")
            )
            
            caption = f"🔔 <b>ငွေလွှဲပြေစာ အသစ်ရောက်ရှိနေပါသည်။</b>\n\nOrder ID: <code>{oid}</code>\nUser ID: {uid}\nကျသင့်ငွေ: {pending[oid]['total']} MMK\n\n✅ စစ်ဆေးပြီး မှန်ကန်ပါက Approve ကိုနှိပ်ပါ။"
            bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=caption, reply_markup=markup, parse_mode="HTML")
            
            bot.reply_to(message, "✅ <b>ငွေလွှဲပြေစာ လက်ခံရရှိပါပြီ။</b>\n\nAdmin မှ စစ်ဆေးပြီးပါက သင့်ထံသို့ အကောင့်အချက်အလက်များ အလိုအလျောက် ဝင်ရောက်လာပါမည်။ ခေတ္တစောင့်ဆိုင်းပေးပါ။", parse_mode="HTML")
            del user_orders[uid]["awaiting_slip"]

def confirm(message, uid):
    order = user_orders.get(uid)
    if not order: return
    p = load_products()[order['key']]
    total = p['price'] * order['qty']
    
    msg = f"🛒 <b>အော်ဒါ အတည်ပြုခြင်း</b>\n\nပစ္စည်းအမည်: {p['name']}\nအရေအတွက်: {order['qty']}\nစုစုပေါင်းကျသင့်ငွေ: <b>{total} MMK</b>"
    if order.get("email"):
        msg += f"\nCanva Email: {order['email']}"
        
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ အတည်ပြုပြီး ငွေပေးချေမည်", callback_data="pay"))
    markup.add(types.InlineKeyboardButton("❌ ပယ်ဖျက်မည်", callback_data="main"))
    
    cid = message.chat.id if hasattr(message, 'chat') else uid
    bot.send_message(cid, msg, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: True)
def cb(call):
    try: bot.answer_callback_query(call.id)
    except: pass

    uid = call.from_user.id
    cid = call.message.chat.id
    mid = call.message.message_id
    
    try:
        if call.data == "main": 
            bot.edit_message_text("👋 <b>Formula X Store</b>\n\nအောက်ပါ Menu များမှတစ်ဆင့် လိုအပ်သော ပစ္စည်းများကို ရွေးချယ်နိုင်ပါသည်။", cid, mid, reply_markup=get_menu("main"), parse_mode="HTML")
        elif call.data.startswith("cat_"): 
            bot.edit_message_reply_markup(cid, mid, reply_markup=get_menu(call.data))
        elif call.data == "oos": 
            bot.answer_callback_query(call.id, "ယခုပစ္စည်းမှာ လက်ကျန်ကုန်နေပါသည် ခင်ဗျာ။", show_alert=True)
        elif call.data.startswith("buy_"):
            key = call.data.split("_")[1]
            user_orders[uid] = {"key": key}
            markup = types.InlineKeyboardMarkup(row_width=3)
            markup.add(*[types.InlineKeyboardButton(str(i), callback_data=f"qty_{i}") for i in range(1, 6)])
            markup.add(types.InlineKeyboardButton("🏠 ပင်မမီနူးသို့", callback_data="main"))
            bot.edit_message_text(f"ပစ္စည်းအမည်: <b>{load_products()[key]['name']}</b>\n\nဝယ်ယူလိုသော အရေအတွက်ကို ရွေးချယ်ပါ -", cid, mid, reply_markup=markup, parse_mode="HTML")
        elif call.data.startswith("qty_"):
            if uid not in user_orders or "key" not in user_orders[uid]:
                bot.answer_callback_query(call.id, "⏱ Session သက်တမ်းကုန်သွားပါပြီ။ /start ပြန်နှိပ်ပါ။", show_alert=True)
                return
            qty = int(call.data.split("_")[1])
            user_orders[uid]["qty"] = qty
            if user_orders[uid]["key"] == "canva":
                bot.edit_message_text("📧 သင့်၏ Canva အသုံးပြုမည့် Email ကို စာရိုက်၍ ပေးပို့ပါ:", cid, mid)
                bot.register_next_step_handler(call.message, lambda m: [user_orders.get(uid).update({"email": m.text}), confirm(m, uid)][-1])
            else: 
                bot.delete_message(cid, mid)
                confirm(call.message, uid)
        elif call.data == "pay":
            if uid not in user_orders or "key" not in user_orders[uid]:
                bot.answer_callback_query(call.id, "⏱ Session သက်တမ်းကုန်သွားပါပြီ။ /start ပြန်နှိပ်ပါ။", show_alert=True)
                return
            oid = f"{load_products()[user_orders[uid]['key']]['prefix']}-{random.randint(1000, 9999)}"
            user_orders[uid]["oid"] = oid
            markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("Wave Pay ဖြင့်ချေမည်", callback_data="p_w"), types.InlineKeyboardButton("KBZ Pay ဖြင့်ချေမည်", callback_data="p_k"))
            bot.edit_message_text(f"🛒 အော်ဒါအမှတ်စဉ်: <b>{oid}</b>\n\nအောက်ပါ ငွေပေးချေမှု နည်းလမ်းတစ်ခုခုကို ရွေးချယ်ပါ:", cid, mid, reply_markup=markup, parse_mode="HTML")
        elif call.data.startswith("p_"):
            if uid not in user_orders or "key" not in user_orders[uid] or "qty" not in user_orders[uid]:
                bot.answer_callback_query(call.id, "⏱ Session သက်တမ်းကုန်သွားပါပြီ။ /start ပြန်နှိပ်ပါ။", show_alert=True)
                return
            order = user_orders[uid]
            p = load_products()[order['key']]
            total = p['price'] * order['qty']
            
            pending = load_pending()
            pending[order['oid']] = {"user_id": uid, "key": order['key'], "qty": order['qty'], "total": total}
            save_pending(pending)
            
            user_orders[uid]["awaiting_slip"] = order['oid']
            
            pay_msg = f"💳 <b>ငွေပေးချေရန်</b>\n\nဖုန်းနံပါတ်: <code>09770088206</code>\nအကောင့်အမည်: Myat Min Lwin\nကျသင့်ငွေ: <b>{total} MMK</b>\n\n✅ <b>ငွေလွှဲပြီးပါက Screenshot (ငွေလွှဲပြေစာ) ကို ဤ Chat ထဲသို့ ဓာတ်ပုံအနေဖြင့် ပေးပို့ပေးပါ။</b>"
            bot.edit_message_text(pay_msg, cid, mid, parse_mode="HTML")
            
        elif call.data.startswith("approve_") or call.data.startswith("reject_"):
            action, oid = call.data.split("_")
            pending = load_pending()
            
            if oid not in pending:
                bot.answer_callback_query(call.id, "အော်ဒါ မရှိတော့ပါ (သို့မဟုတ်) အတည်ပြုပြီးသား ဖြစ်နေပါသည်။", show_alert=True)
                return
                
            data = pending[oid]
            if action == "approve":
                bot.edit_message_caption(f"✅ APPROVED\nOrder ID: {oid}\n\nUser ထံသို့ Key ပေးပို့နေပါသည်...", cid, mid)
                process_approval(oid, data, is_auto=False)
            else:
                bot.send_message(data['user_id'], f"❌ လူကြီးမင်း၏ အော်ဒါ (ID: {oid}) ငွေလွှဲပြေစာမှာ မှားယွင်းနေသဖြင့် ပယ်ဖျက်လိုက်ပါသည်။ အသေးစိတ်သိရှိလိုပါက Admin နှင့် ဆက်သွယ်ပါ။")
                bot.edit_message_caption(f"❌ REJECTED\nOrder ID: {oid}\nငွေမဝင်သဖြင့် ပယ်ဖျက်လိုက်ပါသည်။", cid, mid)
                
            del pending[oid]
            save_pending(pending)
            
        elif call.data == "contact_admin":
            bot.edit_message_text("👨‍💻 သိလိုသည်များ၊ အခက်အခဲရှိသည်များကို @FORMULA_X0 သို့ ဆက်သွယ်မေးမြန်းနိုင်ပါသည်။", cid, mid, reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🏠 ပင်မမီနူးသို့", callback_data="main")))
        elif call.data == "my_orders":
            hist = load_json(HISTORY_FILE, {}).get(str(uid), [])
            msg = "📋 <b>သင်၏ ဝယ်ယူမှုမှတ်တမ်းများ</b>\n\n" + "\n".join([f"📦 {h['product']} - {h['total']} MMK" for h in hist[-5:]]) if hist else "မှတ်တမ်း မရှိသေးပါ။"
            bot.edit_message_text(msg, cid, mid, reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🏠 ပင်မမီနူးသို့", callback_data="main")), parse_mode="HTML")
            
    except telebot.apihelper.ApiTelegramException:
        pass
    except Exception as e:
        print(f"Callback Error: {e}")

@app.route('/sms', methods=['POST'])
def receive_sms():
    content = request.json if request.is_json else request.form
    txt = content.get('message', content.get('text', ''))
    if not txt: return "No data", 400
    pending = load_pending()
    for oid, data in pending.items():
        if str(oid) in txt and str(data['total']) in txt.replace(',', ''):
            process_approval(oid, data, is_auto=True)
            del pending[oid]
            save_pending(pending)
            return "Approved", 200
    return "Processed", 200

def run_flask(): 
    app.run(host='0.0.0.0', port=5000)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    print("🤖 FormulaX Bot စတင်အလုပ်လုပ်နေပါပြီ...")
    bot.polling(none_stop=True)
