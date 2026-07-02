# 𝙎𝙝𝙤𝙥𝙞𝙛𝙮 𝙑𝙄𝙋 𝙎𝙮𝙨𝙩𝙚𝙢 - (𝟭𝟮𝟬𝗪 - 𝗦𝘁𝗿𝗶𝗰𝘁 𝗣𝗿𝗼𝘅𝘆 - 𝗙𝗲𝗲𝗱𝗯𝗮𝗰𝗸 - 𝗕𝗮𝗰𝗸 - 𝗧𝗶𝗺𝗲𝗿 - 𝟭𝟬𝟬% 𝗙𝗼𝗿𝗰𝗲𝗱 𝗚𝗜𝗙𝘀)
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

_jcid = str(os.getenv("JOIN_CHANNEL_ID", "0")).strip()
try: JOIN_CHANNEL_ID = int(_jcid)
except: JOIN_CHANNEL_ID = _jcid

_jgid = str(os.getenv("JOIN_GROUP_ID", "0")).strip()
try: JOIN_GROUP_ID = int(_jgid)
except: JOIN_GROUP_ID = _jgid

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

# ====================== FORCED GIF FETCHER (NO EXCUSES) ======================
async def fetch_random_gif(specific_url=None):
    # نختار 3 روابط ونجربها كلها لضمان وصول الصورة غصباً عنها
    urls_to_try = [specific_url] if specific_url else random.sample(ANIME_GIFS, 3)
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    
    for url in urls_to_try:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=Normally I can help with things like this, but I don't seem to have access to that content. You can try again or ask me for something else.
