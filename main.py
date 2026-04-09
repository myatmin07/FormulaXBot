import telebot
from telebot import types
import json
import os
import random
import string
import threading
import copy

# ==========================================
# 1. SETUP
# ==========================================
API_TOKEN = '8483869457:AAFBlSIu_6biWRAZ7lgGBrT-smj7C7tsQ20'
ADMIN_ID = 5890904598
bot = telebot.TeleBot(API_TOKEN)

PRODUCTS_FILE = "formula_x_products.json"
ACCOUNTS_FILE = "formula_x_accounts.json"
PENDING_FILE = "formula_x_pending.json"
HISTORY_FILE = "formula_x_user_history.json"

db_lock = threading.Lock()
PRODUCTS_DB = {}

# ==========================================
# 2. PRODUCT LIST (မင်းပြောတဲ့အတိုင်း ပြင်ဆင်ထားသည်)
# ==========================================
default_products = {
    "cgpt_plus_12m": {"name": "🤖 ChatGPT Plus (12 M)", "price": 105000, "stock": 50},
    "cgpt_plus_1m": {"name": "🤖 ChatGPT Plus (1 M)", "price": 25000, "stock": 50},
    "cgpt_go_12m": {"name": "🧠 ChatGPT Go (12 M)", "price": 20000, "stock": 50},
    "cgpt_pro_1m": {"name": "🚀 ChatGPT PRO (1 M)", "price": 350000, "stock": 10},
    "ai_claude_1m": {"name": "🟣 Claude Pro (1 M)", "price": 90000, "stock": 50},
    "grok_super_1m": {"name": "🦸‍♂️ Super Grok (1 M)", "price": 15000, "stock": 50},
    "tool_canva": {"name": "🎨 Canva Edu Lifetime", "price": 5000, "stock": -1},
    "tool_perplex_1y": {"name": "🔍 Perplexity (1 Y)", "price": 50000, "stock": 18},
    "capcut_pro": {"name": "🎬 Capcut Pro (1 M)", "price": 8000, "stock": -1},
    "capcut_team": {"name": "👥 Capcut Team (1 M)", "price": 10000, "stock": -1},
    "evpn_pc_1y": {"name": "💻 Express VPN (1 Y)", "price": 10000, "stock": 50},
    "evpn_pc_2y": {"name": "💻 Express VPN (2 Y)", "price": 18000, "stock": 20},
    "evpn_mob_1m_1d": {"name": "📱 Express VPN (1 M)", "price": 2000, "stock": 50},
    "evpn_mob_1m_8d": {"name": "📱 Express VPN (1 M)", "price": 11000, "stock": 50},
    "hid_hk_1m": {"name": "🇭🇰 Hiddify VPN (1 M)", "price": 3000, "stock": 0},
}

def init_db():
    global PRODUCTS_DB
    if os.path.exists(PRODUCTS_FILE):
        with open(PRODUCTS_FILE, "r", encoding="utf-8") as f: PRODUCTS_DB = json.load(f)
    else:
        PRODUCTS_DB = copy.deepcopy(default_products)
        save_db(PRODUCTS_FILE, PRODUCTS_DB)

def save_db(file, data):
    with db_lock:
        with open(file, "w", encoding="utf-8") as f: json.dump(data, f, indent=4)

init_db()
user_orders = {}

# ==========================================
# 3. HELPER FUNCTIONS
# ==========================================
def get_main_menu(user_id):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🤖 Chat GPT", callback_data="cat_cgpt"),
        types.InlineKeyboardButton(PRODUCTS_DB["ai_claude_1m"]["name"], callback_data="buy_ai_claude_1m"),
        types.InlineKeyboardButton("🌌 Grok Ai", callback_data="cat_grok"),
        types.InlineKeyboardButton("🛡️ Express VPN", callback_data="cat_evpn"),
        types.InlineKeyboardButton("🚀 Hiddify VPN", callback_data="cat_hiddify"),
        types.InlineKeyboardButton("🎬 Capcut Premium", callback_data="cat_capcut"),
        types.InlineKeyboardButton(PRODUCTS_DB["tool_canva"]["name"], callback_data="buy_tool_canva"),
        types.InlineKeyboardButton(PRODUCTS_DB["tool_perplex_1y"]["name"], callback_data="buy_tool_perplex_1y")
    )
    if user_id == ADMIN_ID: markup.add(types.InlineKeyboardButton("⚙️ Admin Panel", callback_data="admin_panel"))
    return markup

def get_sub_menu(cat):
    markup = types.InlineKeyboardMarkup(row_width=1)
    keys = []
    if cat == "cat_cgpt": keys = [k for k in PRODUCTS_DB if k.startswith("cgpt_")]
    elif cat == "cat_evpn": keys = [k for k in PRODUCTS_DB if k.startswith("evpn_")]
    elif cat == "cat_capcut": keys = ["capcut_pro", "capcut_team"]
    elif cat == "cat_hiddify": keys = [k for k in PRODUCTS_DB if k.startswith("hid_")]
    elif cat == "cat_grok": keys = ["grok_super_1m"]
    
    for k in keys:
        name = PRODUCTS_DB[k]["name"]
        markup.add(types.InlineKeyboardButton(name, callback_data=f"buy_{k}"))
    markup.add(types.InlineKeyboardButton("🏠 Back", callback_data="back_main"))
    return markup

# ==========================================
# 4. MESSAGE HANDLERS
# ==========================================
@bot.message_handler(commands=['start'])
def welcome(m):
    bot.send_message(m.chat.id, "👋 <b>Welcome to Formula X Store</b>\nSelect an item:", reply_markup=get_main_menu(m.from_user.id), parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    uid, cid, mid = call.from_user.id, call.message.chat.id, call.message.message_id
    bot.answer_callback_query(call.id)

    if call.data == "back_main":
        bot.edit_message_text("Select an item:", cid, mid, reply_markup=get_main_menu(uid))
    
    elif call.data.startswith("cat_"):
        bot.edit_message_text("Choose a plan:", cid, mid, reply_markup=get_sub_menu(call.data))
        
    elif call.data.startswith("buy_"):
        key = call.data.split("_", 1)[1]
        user_orders[uid] = {"key": key}
        p = PRODUCTS_DB[key]
        markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("✅ Confirm & Pay", callback_data="confirm_pay"), types.InlineKeyboardButton("❌ Cancel", callback_data="back_main"))
        bot.edit_message_text(f"🛍️ <b>{p['name']}</b>\n💰 Price: <b>{p['price']} Ks</b>\n\nConfirm to get payment info:", cid, mid, reply_markup=markup, parse_mode="HTML")

    elif call.data == "confirm_pay":
        order = user_orders.get(uid)
        if not order: return
        oid = f"FX-{''.join(random.choices(string.ascii_uppercase + string.digits, k=5))}"
        user_orders[uid]["oid"] = oid
        p = PRODUCTS_DB[order['key']]
        
        # Save to Pending
        pending = {}
        if os.path.exists(PENDING_FILE):
            with open(PENDING_FILE, "r") as f: pending = json.load(f)
        pending[oid] = {"user_id": uid, "key": order['key'], "total": p['price']}
        save_db(PENDING_FILE, pending)
        
        msg = f"💳 <b>Payment Info</b>\n\nTotal: <b>{p['price']} Ks</b>\nNote: <code>{oid}</code>\n\nKBZ Pay: <code>09770088206</code>\nWave Pay: <code>09770088206</code>\n\n✅ Send slip/screenshot here."
        bot.edit_message_text(msg, cid, mid, parse_mode="HTML")

    elif call.data.startswith("approve_"):
        oid = call.data.split("_")[1]
        with open(PENDING_FILE, "r") as f: pending = json.load(f)
        if oid in pending:
            data = pending[oid]
            # Here: You should manually send account or implement account deduction
            bot.send_message(data['user_id'], f"🎉 <b>Order {oid} Approved!</b>\nAdmin will send your account details shortly.")
            bot.send_message(ADMIN_ID, f"✅ Order {oid} approved. Send details to {data['user_id']}.")
            del pending[oid]
            save_db(PENDING_FILE, pending)

@bot.message_handler(content_types=['photo'])
def handle_slip(message):
    uid = message.from_user.id
    if uid in user_orders and "oid" in user_orders[uid]:
        oid = user_orders[uid]["oid"]
        markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("✅ Approve", callback_data=f"approve_{oid}"))
        bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=f"🔔 <b>New Slip!</b>\nOrder ID: {oid}\nUser: {uid}", reply_markup=markup, parse_mode="HTML")
        bot.reply_to(message, "✅ Slip received. Admin will verify shortly.")

if __name__ == "__main__":
    print("🤖 FormulaX Bot is running...")
    bot.infinity_polling()