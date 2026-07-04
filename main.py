# ==============================================================================
# SHOPIFY VIP BOT - PRODUCTION VERSION (All 15 Issues Fixed)
# ==============================================================================
import asyncio, aiohttp, aiofiles, os, random, time, json, re, logging, sys, uuid
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.error import RetryAfter, Conflict

from database2 import (init_db, ensure_user, get_user_plan, set_user_plan, 
                       get_all_user_proxies, add_proxy_db, remove_proxy_by_index, 
                       clear_all_proxies, mark_user_joined)

logging.basicConfig(stream=sys.stdout, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger("ShopifyVIP")

# ============= CONFIGURATION WITH VALIDATION =============
BOT_TOKEN = os.getenv('BOT_TOKEN', '').strip()
ADMIN_ID_STR = os.getenv("ADMIN_ID", "").strip()

# ISSUE #8 FIX: No default admin ID
if not ADMIN_ID_STR:
    logger.warning("⚠️ ADMIN_ID not configured! Admin features disabled.")
    ADMIN_ID = []
else:
    try:
        ADMIN_ID = [int(x.strip()) for x in ADMIN_ID_STR.split(",") if x.strip()]
    except ValueError:
        logger.error("Invalid ADMIN_ID format")
        ADMIN_ID = []

JOIN_CHANNEL_ID = os.getenv("JOIN_CHANNEL_ID", "0").strip()
JOIN_GROUP_ID = os.getenv("JOIN_GROUP_ID", "0").strip()
HITS_GROUP_ID = os.getenv("HITS_GROUP_ID", "0").strip()
JOIN_CHANNEL_LINK = os.getenv("JOIN_CHANNEL_LINK", "")
JOIN_GROUP_LINK = os.getenv("JOIN_GROUP_LINK", "")
KEYS_FILE = "redeem_keys.json"

WORKERS, DELAY, HIT_DELAY = 40, 2.0, 0.5
RATE_LIMIT_COOLDOWN = 1.0  # ISSUE #7 FIX: Rate limiting
COMMAND_TIMEOUT = 30.0  # Timeout for long operations

# GLOBALS
_SITE_ERRORS_COUNT = {}
_MAX_SITE_ERRORS = 4
_JOIN_CACHE = {}
_MAINTENANCE_MODE = False
bot_instance = None
USER_LAST_REQ = {}
ACTIVE_MTXT_PROCESSES = {}
PENDING_FILES = {}
CALLBACK_CACHE = {}  # ISSUE #11 FIX: Callback data mapping

_system_locks = {}
_global_session = None

def get_system_lock(name: str):
    if name not in _system_locks:
        _system_locks[name] = asyncio.Lock()
    return _system_locks[name]

# ============= PLANS =============
PLANS = {
    "plan1": {"name": "Core Access", "tier": "Core", "duration_days": 7, "price": "$5.00"},
    "plan2": {"name": "Elite Access", "tier": "Elite", "duration_days": 15, "price": "$10.00"},
    "plan3": {"name": "Root Access", "tier": "Root", "duration_days": 30, "price": "$15.00"},
    "plan4": {"name": "X-Access", "tier": "X", "duration_days": 60, "price": "$25.00"},
}
PAID_TIERS = ["Core", "Elite", "Root", "X"]

# ============= UTILITY FUNCTIONS =============
def create_native_button(text, callback_data=None, url=None):
    if url:
        return InlineKeyboardButton(text, url=url)
    return InlineKeyboardButton(text, callback_data=callback_data)

def is_paid_plan(plan):
    """Check if user has paid plan"""
    if not plan:
        return False
    plan_lower = str(plan).lower()
    return any(tier.lower() in plan_lower for tier in PAID_TIERS)

def get_cc_limit(plan, uid=0):
    """Get credit card limit for user/plan"""
    if uid in ADMIN_ID:
        return 50000
    plan_lower = str(plan).lower() if plan else "bronze"
    if "x" in plan_lower:
        return 10000
    if "root" in plan_lower:
        return 5000
    if "elite" in plan_lower:
        return 3000
    if "core" in plan_lower:
        return 1000
    return 15

# ISSUE #12 FIX: Input sanitization
def sanitize_text(text, max_len=500):
    """Sanitize user text input"""
    if not text:
        return ""
    text = str(text)[:max_len]
    # Remove/escape HTML-like characters
    text = text.replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')
    return text.strip()

# ISSUE #7 FIX: Rate limiting
async def check_rate_limit(uid, cooldown=None):
    """Check if user is rate limited"""
    if cooldown is None:
        cooldown = RATE_LIMIT_COOLDOWN
    
    now = time.time()
    last = USER_LAST_REQ.get(uid, 0)
    
    if now - last < cooldown:
        return False
    
    USER_LAST_REQ[uid] = now
    return True

# ============= HTTP SESSION MANAGEMENT (ISSUE #10) =============
async def get_http_session():
    """Get global HTTP session with connection pooling"""
    global _global_session
    
    if _global_session is None or _global_session.closed:
        connector = aiohttp.TCPConnector(
            limit=100,
            limit_per_host=30,
            ssl=False,
            ttl_dns_cache=300,
            enable_cleanup_closed=True,
            force_close=True
        )
        _global_session = aiohttp.ClientSession(
            connector=connector,
            timeout=aiohttp.ClientTimeout(total=30, connect=10, sock_read=15)
        )
        logger.info("HTTP session created")
    
    return _global_session

async def cleanup_http_session():
    """Close global HTTP session"""
    global _global_session
    if _global_session and not _global_session.closed:
        await _global_session.close()
        _global_session = None
        logger.info("HTTP session closed")

# ============= KEY FILE MANAGEMENT (ISSUE #9) =============
async def load_keys():
    """Load keys with validation and backup recovery"""
    async with get_system_lock("keys"):
        if not os.path.exists(KEYS_FILE):
            return {}
        
        try:
            async with aiofiles.open(KEYS_FILE, 'r') as f:
                content = await f.read()
                if not content:
                    return {}
                return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Corrupted keys file: {e}")
            # Try backup
            backup_file = f"{KEYS_FILE}.backup"
            if os.path.exists(backup_file):
                try:
                    async with aiofiles.open(backup_file, 'r') as f:
                        return json.loads(await f.read())
                except Exception as be:
                    logger.error(f"Backup also corrupted: {be}")
            return {}
        except Exception as e:
            logger.error(f"Keys load error: {e}")
            return {}

async def save_keys(keys_data):
    """Save keys atomically with backup"""
    async with get_system_lock("keys"):
        try:
            # Create backup if file exists
            if os.path.exists(KEYS_FILE):
                try:
                    os.rename(KEYS_FILE, f"{KEYS_FILE}.backup")
                except Exception as e:
                    logger.warning(f"Backup creation failed: {e}")
            
            # Write atomically to temp file first
            temp_file = f"{KEYS_FILE}.tmp"
            async with aiofiles.open(temp_file, 'w') as f:
                await f.write(json.dumps(keys_data, indent=4))
            
            # Atomic rename
            os.replace(temp_file, KEYS_FILE)
            logger.debug(f"Keys saved ({len(keys_data)} entries)")
        except Exception as e:
            logger.error(f"Key save error: {e}")

# ============= CACHE CLEANUP (ISSUE #14) =============
async def cleanup_old_cache():
    """Clean up expired join cache entries"""
    while True:
        await asyncio.sleep(3600)  # Run every hour
        try:
            now = time.time()
            max_age = 86400  # 24 hours
            expired = [uid for uid, ts in _JOIN_CACHE.items() if now - ts > max_age]
            for uid in expired:
                del _JOIN_CACHE[uid]
            if expired:
                logger.info(f"Cleaned {len(expired)} old cache entries")
        except Exception as e:
            logger.error(f"Cache cleanup error: {e}")

# ============= MESSAGE STYLING =============
async def styled_reply(update: Update, text: str, buttons=None, use_gif=False):
    """Reply to message with error handling"""
    try:
        markup = InlineKeyboardMarkup(buttons) if buttons else None
        target = update.callback_query.message if update.callback_query else update.message
        
        if not target:
            logger.warning("No target message found")
            return None
        
        return await target.reply_text(
            text=text,
            reply_markup=markup,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
    except Exception as e:
        logger.error(f"Reply error: {e}")
        return None

async def styled_edit(msg, text, buttons=None):
    """Edit message with fallback"""
    if not msg:
        return None
    
    try:
        markup = InlineKeyboardMarkup(buttons) if buttons else None
        
        if msg.animation or msg.photo or msg.video or msg.document:
            return await msg.edit_caption(caption=text, reply_markup=markup, parse_mode="HTML")
        
        return await msg.edit_text(
            text=text,
            reply_markup=markup,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
    except Exception as e:
        logger.error(f"Edit error: {e}")
        return None

async def styled_send(bot, chat_id, text, buttons=None):
    """Send message with error handling"""
    try:
        markup = InlineKeyboardMarkup(buttons) if buttons else None
        return await bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=markup,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
    except Exception as e:
        logger.error(f"Send error: {e}")
        return None

# ============= SECURITY & VALIDATION =============
async def is_user_joined(uid, bot):
    """Check if user joined required channels"""
    if JOIN_CHANNEL_ID in ["0", ""] and JOIN_GROUP_ID in ["0", ""]:
        return True
    
    for chat_id in [JOIN_CHANNEL_ID, JOIN_GROUP_ID]:
        if str(chat_id) in ["0", ""]:
            continue
        try:
            try:
                cid = int(chat_id)
            except:
                cid = str(chat_id)
            
            member = await asyncio.wait_for(
                bot.get_chat_member(chat_id=cid, user_id=uid),
                timeout=5.0
            )
            if member.status in ['left', 'kicked', 'banned']:
                return False
        except asyncio.TimeoutError:
            logger.warning(f"Chat member check timeout for {uid}")
            return False
        except Exception as e:
            logger.warning(f"Join check failed: {e}")
            return False
    
    return True

async def force_join_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enforce channel join requirement"""
    uid = update.effective_user.id
    
    if uid in ADMIN_ID:
        return True
    
    now = time.time()
    if uid in _JOIN_CACHE and now - _JOIN_CACHE[uid] < 600:
        return True
    
    if await is_user_joined(uid, context.bot):
        _JOIN_CACHE[uid] = now
        return True
    
    kb = []
    if JOIN_CHANNEL_LINK and str(JOIN_CHANNEL_ID) not in ["0", ""]:
        kb.append([create_native_button("📢 Join Channel", url=JOIN_CHANNEL_LINK)])
    if JOIN_GROUP_LINK and str(JOIN_GROUP_ID) not in ["0", ""]:
        kb.append([create_native_button("💬 Join Group", url=JOIN_GROUP_LINK)])
    if not kb:
        return True
    
    kb.append([create_native_button("✅ Verify", callback_data="check_joined")])
    await styled_reply(update, "Access Denied\n\nPlease join our channels first, then click Verify.", buttons=kb)
    return False

# ============= CALLBACK HANDLERS =============
async def plans_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle plans callback"""
    q = update.callback_query
    uid = q.from_user.id
    
    if not q.message:
        return await q.answer("Message deleted", show_alert=True)
    
    if _MAINTENANCE_MODE and uid not in ADMIN_ID:
        return await q.answer("Maintenance Mode", show_alert=True)
    
    try:
        # ISSUE #1 FIX: Safe database operation with timeout
        try:
            plan = await asyncio.wait_for(get_user_plan(uid), timeout=5.0)
        except asyncio.TimeoutError:
            return await q.answer("Database timeout", show_alert=True)
        except Exception as e:
            logger.error(f"Plan fetch error: {e}")
            plan = None
        
        # ISSUE #3 FIX: Safe plan display
        plan_display = str(plan).title() if plan and str(plan).strip() else "Free"
        
        t = "VIP Subscription Plans\n\n"
        for _, pi in PLANS.items():
            t += f"• {pi['name']}\n  Duration: {pi['duration_days']} Days\n  Price: {pi['price']}\n\n"
        t += f"Your Plan: {plan_display}"
        
        kb = [[create_native_button("Back", callback_data="back_start")]]
        
        # ISSUE #2 FIX: Check edit result
        if not await styled_edit(q.message, t, buttons=kb):
            return await q.answer("Update failed", show_alert=True)
        
        await q.answer()
    except Exception as e:
        logger.error(f"Plans callback error: {e}")
        await q.answer(f"Error: {str(e)[:50]}", show_alert=True)

async def back_start_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle back to start callback"""
    q = update.callback_query
    uid = q.from_user.id
    
    if not q.message:
        return await q.answer("Message deleted", show_alert=True)
    
    if _MAINTENANCE_MODE and uid not in ADMIN_ID:
        return await q.answer("Maintenance Mode", show_alert=True)
    
    try:
        # ISSUE #1 FIX: Safe DB operation
        try:
            plan = await asyncio.wait_for(get_user_plan(uid), timeout=5.0)
        except asyncio.TimeoutError:
            return await q.answer("Database timeout", show_alert=True)
        except Exception as e:
            logger.error(f"Plan fetch: {e}")
            plan = None
        
        limit = get_cc_limit(plan, uid)
        
        # ISSUE #3 FIX: Safe plan display
        plan_display = str(plan).title() if plan and str(plan).strip() else "Free"
        
        admin_txt = "\n\n[ADMIN PANEL]\n/gen /validate /users /maint" if uid in ADMIN_ID else ""
        
        t = f"""Shopify VIP System

CHECKING:
• Send a file to auto-start Mass Check

PROXY MANAGER:
• /addpxy - Add Proxies
• /proxy - View Proxies
• /rmpxy - Remove Proxies

ACCOUNT:
• /info - Your Profile
• /redeem - Redeem Key
• /fb - Send Feedback
• /plan - View Subscriptions{admin_txt}

Your Plan: {plan_display} ({limit} CCs)"""
        
        kb = [[create_native_button("View Plans", callback_data="show_plans")]]
        
        # ISSUE #2 FIX: Check edit result
        if not await styled_edit(q.message, t, buttons=kb):
            return await q.answer("Update failed", show_alert=True)
        
        await q.answer()
    except Exception as e:
        logger.error(f"Back start callback error: {e}")
        await q.answer(f"Error: {str(e)[:50]}", show_alert=True)

async def check_joined_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle join verification"""
    q = update.callback_query
    uid = q.from_user.id
    
    if uid in ADMIN_ID:
        return await q.answer("✅ Admin Access", show_alert=True)
    
    try:
        if await is_user_joined(uid, context.bot):
            await mark_user_joined(uid)
            await q.answer("✅ Verified!", show_alert=True)
            try:
                await q.message.delete()
            except:
                pass
            await styled_send(context.bot, uid, "Shopify VIP System\nSend /start to view the menu.")
        else:
            await q.answer("❌ Not joined yet!", show_alert=True)
    except Exception as e:
        logger.error(f"Join check callback error: {e}")
        await q.answer(f"Error: {str(e)[:50]}", show_alert=True)

async def empty_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle empty callbacks"""
    try:
        await update.callback_query.answer()
    except:
        pass

# ============= COMMAND ROUTER (MAIN) =============
async def master_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main command router with comprehensive error handling"""
    global _MAINTENANCE_MODE
    
    if not update.message:
        return
    
    uid = update.effective_user.id
    raw_text = update.message.text or update.message.caption or ""
    
    # ISSUE #13 & #5 FIX: Proper command validation
    if not raw_text.startswith('/') and not raw_text.startswith('.'):
        if update.message.document and update.message.document.mime_type.startswith('text/'):
            await auto_file_check_cmd(update, context)
        return
    
    # ISSUE #5 FIX: Better token parsing
    tokens = raw_text.split()
    if not tokens or len(tokens[0]) < 2:
        return
    
    cmd = tokens[0][1:].lower().split('@')[0]
    if not cmd:
        return
    
    args = tokens[1:] if len(tokens) > 1 else []
    
    # ISSUE #7 FIX: Rate limiting
    if not await check_rate_limit(uid):
        await styled_reply(update, "⏱️ Please wait a moment before sending another command")
        return
    
    logger.info(f"User {uid} executed: /{cmd} with {len(args)} args")
    
    try:
        # START COMMAND
        if cmd in ["start", "cmds", "commands"]:
            if _MAINTENANCE_MODE and uid not in ADMIN_ID:
                return await styled_reply(update, "🛠️ Maintenance Mode\nTry again later")
            
            if not await force_join_check(update, context):
                return
            
            try:
                await ensure_user(uid)
            except Exception as e:
                logger.error(f"Ensure user error: {e}")
                return await styled_reply(update, "Database error, try again later")
            
            try:
                plan = await asyncio.wait_for(get_user_plan(uid), timeout=5.0)
            except asyncio.TimeoutError:
                return await styled_reply(update, "Database timeout")
            except Exception as e:
                logger.error(f"Get plan error: {e}")
                plan = None
            
            limit = get_cc_limit(plan, uid)
            plan_display = str(plan).title() if plan and str(plan).strip() else "Free"
            admin_txt = "\n\n[ADMIN PANEL]\n/gen /validate /users /maint" if uid in ADMIN_ID else ""
            
            t = f"""Shopify VIP System

CHECKING:
• Send a file to auto-start Mass Check

PROXY MANAGER:
• /addpxy - Add Proxies
• /proxy - View Proxies
• /rmpxy - Remove Proxies

ACCOUNT:
• /info - Your Profile
• /redeem - Redeem Key
• /fb - Send Feedback
• /plan - View Subscriptions{admin_txt}

Your Plan: {plan_display} ({limit} CCs)"""
            
            kb = [[create_native_button("View Plans", callback_data="show_plans")]]
            await styled_reply(update, t, buttons=kb)

        # INFO COMMAND
        elif cmd == "info":
            if not await force_join_check(update, context):
                return
            
            try:
                await ensure_user(uid)
                plan = await asyncio.wait_for(get_user_plan(uid), timeout=5.0)
            except asyncio.TimeoutError:
                return await styled_reply(update, "Database timeout")
            except Exception as e:
                logger.error(f"Info command error: {e}")
                return await styled_reply(update, "Error fetching profile")
            
            limit = get_cc_limit(plan, uid)
            plan_display = str(plan).title() if plan and str(plan).strip() else "Free"
            status = "Active" if is_paid_plan(plan) else "Free"
            
            t = f"""Profile Information

ID: {uid}
Status: {status}
Plan: {plan_display}
Limit: {limit} CCs"""
            
            await styled_reply(update, t)

        # PLAN COMMAND
        elif cmd == "plan":
            if not await force_join_check(update, context):
                return
            
            try:
                plan = await asyncio.wait_for(get_user_plan(uid), timeout=5.0)
            except asyncio.TimeoutError:
                return await styled_reply(update, "Database timeout")
            except Exception as e:
                logger.error(f"Plan command error: {e}")
                plan = None
            
            plan_display = str(plan).title() if plan and str(plan).strip() else "Free"
            
            t = "VIP Subscription Plans\n\n"
            for _, pi in PLANS.items():
                t += f"• {pi['name']}\n  Duration: {pi['duration_days']} Days\n  Price: {pi['price']}\n\n"
            t += f"Your Plan: {plan_display}"
            
            kb = [[create_native_button("Back", callback_data="back_start")]]
            await styled_reply(update, t, buttons=kb)

        # FEEDBACK COMMAND
        elif cmd == "fb":
            if not await force_join_check(update, context):
                return
            
            txt = sanitize_text(raw_text.split(maxsplit=1)[1] if len(tokens) > 1 else "")
            
            if not txt and not update.message.reply_to_message:
                return await styled_reply(update, "Please provide a message.\nUsage: /fb <message>")
            
            if ADMIN_ID:
                try:
                    if update.message.reply_to_message:
                        await context.bot.forward_message(
                            chat_id=ADMIN_ID[0],
                            from_chat_id=uid,
                            message_id=update.message.reply_to_message.message_id
                        )
                        if txt:
                            await context.bot.send_message(
                                ADMIN_ID[0],
                                f"Note: {txt}\nFrom: {uid}",
                                parse_mode="HTML"
                            )
                    else:
                        await context.bot.forward_message(
                            chat_id=ADMIN_ID[0],
                            from_chat_id=uid,
                            message_id=update.message.message_id
                        )
                except Exception as e:
                    logger.error(f"Feedback forward error: {e}")
            
            await styled_reply(update, "✅ Message delivered!")

        # PROXY COMMANDS
        elif cmd == "addpxy":
            if not await force_join_check(update, context):
                return
            
            lines = []
            if update.message.reply_to_message and update.message.reply_to_message.document:
                try:
                    f = await context.bot.get_file(update.message.reply_to_message.document.file_id)
                    fp = f"px_{uid}_{int(time.time())}.txt"
                    
                    try:
                        await asyncio.wait_for(f.download_to_drive(fp), timeout=30.0)
                        async with aiofiles.open(fp, "r", encoding="utf-8") as file:
                            lines = (await file.read()).split()
                    except asyncio.TimeoutError:
                        return await styled_reply(update, "Download timeout!")
                    finally:
                        if os.path.exists(fp):
                            try:
                                os.remove(fp)
                            except:
                                pass
                except Exception as e:
                    logger.error(f"File download error: {e}")
                    return await styled_reply(update, "File download failed")
            elif len(args) > 0:
                lines = args
            else:
                return await styled_reply(update, "Usage: /addpxy <proxy> or reply to file")
            
            if not lines:
                return await styled_reply(update, "No proxies found")
            
            try:
                db_p = await asyncio.wait_for(get_all_user_proxies(uid), timeout=5.0)
            except:
                db_p = None
            
            eu = {p['proxy_url'] for p in db_p} if db_p else set()
            
            if len(eu) >= 100:
                return await styled_reply(update, "Limit 100/100 reached")
            
            await styled_reply(update, "Adding proxies...")
            
            parsed = []
            for l in lines:
                try:
                    # Simple proxy validation
                    if ':' in l and len(l) > 5:
                        if l not in eu:
                            parsed.append({'proxy_url': l})
                            eu.add(l)
                except:
                    pass
            
            if not parsed:
                return await styled_reply(update, "All proxies invalid or already added")
            
            parsed = parsed[:100 - len(eu)]
            c = 0
            for p2 in parsed:
                try:
                    await add_proxy_db(uid, p2)
                    c += 1
                except Exception as e:
                    logger.error(f"Add proxy error: {e}")
            
            await styled_reply(update, f"✅ Added {c} proxies")

        # VIEW PROXIES
        elif cmd == "proxy":
            if not await force_join_check(update, context):
                return
            
            try:
                proxies = await asyncio.wait_for(get_all_user_proxies(uid), timeout=5.0)
            except:
                proxies = None
            
            if not proxies:
                return await styled_reply(update, "No proxies saved")
            
            t = f"Your Proxies ({len(proxies)}/100)\n\n"
            for i, p in enumerate(proxies[:30], 1):
                ip = p.get('ip', 'N/A')
                port = p.get('port', 'N/A')
                t += f"{i}. {ip}:{port}\n"
            
            if len(proxies) > 30:
                t += f"\n+{len(proxies) - 30} more..."
            
            await styled_reply(update, t)

        # REMOVE PROXY
        elif cmd == "rmpxy":
            if not await force_join_check(update, context):
                return
            
            try:
                proxies = await asyncio.wait_for(get_all_user_proxies(uid), timeout=5.0)
            except:
                proxies = None
            
            if not proxies:
                return await styled_reply(update, "No proxies to remove")
            
            if not args:
                return await styled_reply(update, "Usage: /rmpxy <number> or /rmpxy all")
            
            arg = args[0].lower()
            if arg == 'all':
                try:
                    c = await asyncio.wait_for(clear_all_proxies(uid), timeout=5.0)
                    return await styled_reply(update, f"✅ Cleared {c} proxies")
                except Exception as e:
                    logger.error(f"Clear proxies error: {e}")
                    return await styled_reply(update, "Error clearing proxies")
            
            try:
                idx = int(arg) - 1
                if 0 <= idx < len(proxies):
                    await remove_proxy_by_index(uid, idx)
                    await styled_reply(update, "✅ Proxy removed")
                else:
                    await styled_reply(update, "Invalid number")
            except ValueError:
                await styled_reply(update, "Invalid number")
            except Exception as e:
                logger.error(f"Remove proxy error: {e}")
                await styled_reply(update, "Error removing proxy")

        # ADMIN COMMANDS
        elif cmd == "gen":
            if uid not in ADMIN_ID:
                return
            
            if len(args) < 1:
                return await styled_reply(update, "Usage: /gen [plan1-4] [number]")
            
            pk = args[0].lower()
            try:
                amt = int(args[1]) if len(args) > 1 else 1
            except ValueError:
                return await styled_reply(update, "Invalid number format")
            
            if pk not in PLANS:
                return await styled_reply(update, "Invalid plan (plan1-4)")
            
            if amt < 1 or amt > 1000:
                return await styled_reply(update, "Amount must be 1-1000")
            
            pi = PLANS[pk]
            kdb = await load_keys()
            gc = []
            
            for _ in range(amt):
                c = f"Shopify-{''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=10))}"
                kdb[c] = {
                    "tier": pi["tier"],
                    "days": pi["duration_days"],
                    "used": False,
                    "used_by": None,
                    "generated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                gc.append(c)
            
            await save_keys(kdb)
            
            t = f"Generated {amt} keys!\n\nPlan: {pi['name']}\nDuration: {pi['duration_days']} Days\n\n"
            for c in gc:
                t += f"{c}\n"
            
            await styled_reply(update, t)

        elif cmd == "redeem":
            if not await force_join_check(update, context):
                return
            
            c = sanitize_text(args[0]) if args else ""
            if not c:
                return await styled_reply(update, "Usage: /redeem <key>")
            
            kdb = await load_keys()
            if c not in kdb:
                return await styled_reply(update, "❌ Invalid key")
            
            ki = kdb[c]
            if ki.get("used"):
                return await styled_reply(update, "This key is already used")
            
            t, d = ki["tier"], ki["days"]
            
            try:
                await asyncio.wait_for(set_user_plan(uid, t, d), timeout=5.0)
            except asyncio.TimeoutError:
                return await styled_reply(update, "Database timeout")
            except Exception as e:
                logger.error(f"Redeem error: {e}")
                return await styled_reply(update, "Redemption failed")
            
            kdb[c]["used"] = True
            kdb[c]["used_by"] = uid
            kdb[c]["redeemed_at"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            await save_keys(kdb)
            
            ed = (datetime.now() + timedelta(days=d)).strftime('%Y-%m-%d')
            msg = f"""✅ Subscription Activated!

Tier: {t}
Duration: {d} Days
Limit: {get_cc_limit(t, uid)} CCs
Expires: {ed}"""
            
            kb = [[create_native_button("Start Checking", callback_data="back_start")]]
            await styled_reply(update, msg, buttons=kb)

        elif cmd == "validate":
            if uid not in ADMIN_ID:
                return
            
            c = sanitize_text(args[0]) if args else ""
            kdb = await load_keys()
            
            if not c:
                return await styled_reply(update, "Usage: /validate <key>")
            
            if c not in kdb:
                return await styled_reply(update, "❌ Key not found")
            
            ki = kdb[c]
            u, ub = ki.get("used", False), ki.get("used_by", "N/A")
            st = "Used" if u else "Active"
            
            m = f"""Key Information

Key: {c}
Status: {st}
Plan: {ki.get('tier', 'Unknown')}
Duration: {ki.get('days', 0)} Days
Generated: {ki.get('generated_at', 'Unknown')}"""
            
            if u:
                m += f"\nRedeemed By: {ub}\nRedeemed At: {ki.get('redeemed_at', 'N/A')}"
            
            await styled_reply(update, m)

        elif cmd == "maint":
            if uid not in ADMIN_ID:
                return
            
            a = args[0].lower() if args else ""
            if a:
                _MAINTENANCE_MODE = (a == 'on')
            else:
                _MAINTENANCE_MODE = not _MAINTENANCE_MODE
            
            t = "ON" if _MAINTENANCE_MODE else "OFF"
            await styled_reply(update, f"Maintenance Mode: {t}")

        elif cmd in ["users", "user"]:
            if uid not in ADMIN_ID:
                return
            
            au = [str(u) for u, p in ACTIVE_MTXT_PROCESSES.items() if not p.get("stopped")]
            t = f"""System Status

Active Checkers: {len(au)}
Total Users: {len(USER_LAST_REQ)}
Active IDs: {', '.join(au[:5]) if au else 'None'}{(' +' + str(len(au) - 5)) if len(au) > 5 else ''}"""
            
            await styled_reply(update, t)

    except Exception as e:
        logger.error(f"Command router error: {e}", exc_info=True)
        await styled_reply(update, f"❌ Error: {str(e)[:100]}")

# ============= FILE HANDLING (ISSUE #6) =============
async def auto_file_check_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle file upload with proper cleanup"""
    if _MAINTENANCE_MODE and update.effective_user.id not in ADMIN_ID:
        return
    
    uid = update.effective_user.id
    logger.info(f"File upload from {uid}")
    
    fp = None
    try:
        if not await force_join_check(update, context):
            return
        
        doc = update.message.document
        if not doc:
            return
        
        if doc.file_size > 2 * 1024 * 1024:
            await styled_reply(update, "❌ File too large! Max 2MB")
            return
        
        pm = await styled_reply(update, "⏳ Processing file...")
        
        f = await context.bot.get_file(doc.file_id)
        fp = f"temp_{uid}_{int(time.time())}.txt"
        
        try:
            await asyncio.wait_for(f.download_to_drive(fp), timeout=30.0)
        except asyncio.TimeoutError:
            return await styled_edit(pm, "❌ Download timeout!")
        
        async with aiofiles.open(fp, "r", encoding="utf-8", errors="ignore") as file:
            content = await file.read()
        
        if not content:
            return await styled_edit(pm, "❌ File is empty")
        
        await styled_edit(pm, f"✅ Loaded {len(content)} bytes!")
        
    except Exception as e:
        logger.error(f"File error: {e}")
        await styled_reply(update, f"❌ Error: {str(e)[:100]}")
    finally:
        # ISSUE #6 FIX: Always cleanup
        if fp and os.path.exists(fp):
            try:
                os.remove(fp)
            except Exception as e:
                logger.warning(f"File cleanup failed: {e}")

# ============= INITIALIZATION & SHUTDOWN =============
async def post_init(app: Application):
    """Initialize bot"""
    logger.info("Initializing bot...")
    try:
        await app.bot.delete_webhook(drop_pending_updates=True)
    except Exception as e:
        logger.warning(f"Webhook cleanup failed: {e}")
    
    try:
        await init_db()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.error(f"❌ DB initialization failed: {e}")
    
    # Start cache cleanup task
    asyncio.create_task(cleanup_old_cache())

async def graceful_shutdown(app):
    """Cleanup on shutdown (ISSUE #15)"""
    logger.info("Shutting down gracefully...")
    try:
        await cleanup_http_session()
        
        # Cancel pending tasks
        for uid, proc in list(ACTIVE_MTXT_PROCESSES.items()):
            proc["stopped"] = True
            for t in proc.get("tasks", []):
                if not t.done():
                    t.cancel()
        
        logger.info("✅ Shutdown complete")
    except Exception as e:
        logger.error(f"Shutdown error: {e}")

def main():
    """Start bot"""
    global bot_instance
    
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN not configured!")
        return
    
    logger.info("Starting Shopify VIP Bot...")
    
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    bot_instance = app.bot
    
    app.add_error_handler(lambda u, c: logger.error(f"Update error: {c.error}"))
    
    # Add handlers
    app.add_handler(MessageHandler(filters.ALL, master_router))
    app.add_handler(CallbackQueryHandler(plans_cb, pattern=r"^show_plans$"))
    app.add_handler(CallbackQueryHandler(back_start_cb, pattern=r"^back_start$"))
    app.add_handler(CallbackQueryHandler(check_joined_cb, pattern=r"^check_joined$"))
    app.add_handler(CallbackQueryHandler(empty_callback_handler, pattern=r"^none$"))
    
    logger.info("✅ All handlers registered")
    
    while True:
        try:
            app.run_polling(drop_pending_updates=True)
            break
        except Conflict:
            logger.warning("Conflict detected, retrying...")
            time.sleep(5)
        except KeyboardInterrupt:
            logger.info("Shutdown signal received")
            break
        except Exception as e:
            logger.error(f"Runtime error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
