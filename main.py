# 𝙍𝘼𝙕𝙊𝙍 𝙓 𝘽𝙤𝙩 - V2 (Optimized & Cleaned)
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

# --- API ENDPOINTS ---
CHECKER_API_URL = 'http://62.72.20.10:8081/'
PROXY_FILE = 'proxy.txt'

# 👇 ضع رابط ملف الـ sites.txt الخاص بك على جيتهب (بصيغة RAW) 👇
GITHUB_SITES_URL = os.getenv("GITHUB_SITES_URL", "https://raw.githubusercontent.com/username/repo/main/sites.txt")

SP_PER_USER_WORKERS = 30
WORKERS = 70  # سرعة الفحص
PROXY_PER_USER_WORKERS = 50
BIN_WORKERS = 20

API_TIMEOUT = 30
BIN_TIMEOUT = 15
PROXY_TIMEOUT = 12
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

ANIME_GIFS = [
    "https://media.giphy.com/media/1n4iuWZFnTeN6qvdpD/giphy.gif",
    "https://media.giphy.com/media/11KzOet1ElBDz2/giphy.gif",
    "https://media.giphy.com/media/4ilFRqgbzbx4c/giphy.gif",
    "https://media.giphy.com/media/xT1R9yebNpKAAJjH0s/giphy.gif",
    "https://media.giphy.com/media/108BDeJ2BvtZRu/giphy.gif",
    "https://media.giphy.com/media/F3uJq1J1x0u6k/giphy.gif",
    "https://media.giphy.com/media/7ZjnR6t2kU2lO/giphy.gif"
]

_DEAD_INDICATORS = (
    'receipt id is empty', 'handle is empty', 'product id is empty',
    'tax amount is empty', 'payment method identifier is empty',
    'invalid url', 'error in 1st req', 'error in 1 req',
    'cloudflare', 'connection failed', 'timed out',
    'access denied', 'tlsv1 alert', 'ssl routines',
    Normally I can help with things like this, but I don't seem to have access to that content. You can try again or ask me for something else.
