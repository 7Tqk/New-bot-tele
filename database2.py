import os
import json
import datetime
import random
import uuid
import asyncio

DB_FILE = "database.json"
DB_LOCK = asyncio.Lock()

async def _read_db():
    if not os.path.exists(DB_FILE):
        return {"users": {}, "keys": [], "proxies": [], "sites": [], "cards": [], "global_sites": [], "joined_users": {}}
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"users": {}, "keys": [], "proxies": [], "sites": [], "cards": [], "global_sites": [], "joined_users": {}}

async def _write_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

async def init_db():
    async with DB_LOCK:
        data = await _read_db()
        await _write_db(data)
        print("✅ 𝗥𝗔𝗭𝗢𝗥 𝗫 𝗗𝗮𝘁𝗮𝗯𝗮𝘀𝗲 𝗶𝗻𝗶𝘁𝗶𝗮𝗹𝗶𝘇𝗲𝗱 𝘀𝘂𝗰𝗰𝗲𝘀𝘀𝗳𝘂𝗹𝗹𝘆! (Local JSON - Locked & Secured)")

async def ensure_user(user_id: int):
    async with DB_LOCK:
        data = await _read_db()
        uid_str = str(user_id)
        if uid_str not in data["users"]:
            data["users"][uid_str] = {
                "user_id": user_id, "plan": "Bronze", "expiry": None,
                "banned": False, "created_at": datetime.datetime.utcnow().isoformat()
            }
            await _write_db(data)

async def get_user_plan(user_id: int) -> str:
    async with DB_LOCK:
        data = await _read_db()
        uid_str = str(user_id)
        user = data["users"].get(uid_str)
        if not user: return "Bronze"
        plan = user.get("plan", "Bronze")
        expiry = user.get("expiry")
        if expiry:
            exp_date = datetime.datetime.fromisoformat(expiry)
            if datetime.datetime.utcnow() > exp_date:
                data["users"][uid_str]["plan"] = "Bronze"
                data["users"][uid_str]["expiry"] = None
                await _write_db(data)
                return "Bronze"
        return plan

async def set_user_plan(user_id: int, plan: str, days: int = 0):
    async with DB_LOCK:
        data = await _read_db()
        uid_str = str(user_id)
        expiry = None
        if days > 0: expiry = (datetime.datetime.utcnow() + datetime.timedelta(days=days)).isoformat()
        if uid_str not in data["users"]:
            data["users"][uid_str] = {"user_id": user_id, "created_at": datetime.datetime.utcnow().isoformat()}
        data["users"][uid_str]["plan"] = plan
        data["users"][uid_str]["expiry"] = expiry
        data["users"][uid_str]["premium_days"] = days
        await _write_db(data)

async def is_premium_user(user_id: int) -> bool:
    plan = await get_user_plan(user_id)
    return plan in ["Core", "Elite", "Root", "X"]

async def is_banned_user(user_id: int) -> bool:
    async with DB_LOCK:
        data = await _read_db()
        user = data["users"].get(str(user_id))
        return user.get("banned", False) if user else False

async def mark_user_joined(user_id: int):
    async with DB_LOCK:
        data = await _read_db()
        data["joined_users"][str(user_id)] = {"user_id": user_id, "joined_at": datetime.datetime.utcnow().isoformat()}
        await _write_db(data)

async def is_user_marked_joined(user_id: int) -> bool:
    async with DB_LOCK:
        data = await _read_db()
        return str(user_id) in data["joined_users"]

async def remove_joined_mark(user_id: int):
    async with DB_LOCK:
        data = await _read_db()
        if str(user_id) in data["joined_users"]:
            del data["joined_users"][str(user_id)]
            await _write_db(data)

async def add_proxy_db(user_id: int, proxy_data: dict):
    async with DB_LOCK:
        data = await _read_db()
        proxy_data["_id"] = str(uuid.uuid4())
        proxy_data["user_id"] = user_id
        data["proxies"].append(proxy_data)
        await _write_db(data)

async def get_all_user_proxies(user_id: int):
    async with DB_LOCK:
        data = await _read_db()
        return [p for p in data["proxies"] if p["user_id"] == user_id][:200]

async def get_proxy_count(user_id: int) -> int:
    async with DB_LOCK:
        data = await _read_db()
        return sum(1 for p in data["proxies"] if p["user_id"] == user_id)

async def get_random_proxy(user_id: int):
    proxies = await get_all_user_proxies(user_id)
    return random.choice(proxies) if proxies else None

async def remove_proxy_by_index(user_id: int, index: int):
    async with DB_LOCK:
        data = await _read_db()
        user_proxies = [p for p in data["proxies"] if p["user_id"] == user_id]
        if 0 <= index < len(user_proxies):
            target = user_proxies[index]
            data["proxies"] = [p for p in data["proxies"] if p.get("_id") != target.get("_id")]
            await _write_db(data)
            return target
        return None

async def remove_proxy_by_url(user_id: int, proxy_url: str):
    async with DB_LOCK:
        data = await _read_db()
        init_len = len(data["proxies"])
        data["proxies"] = [p for p in data["proxies"] if not (p["user_id"] == user_id and p["proxy_url"] == proxy_url)]
        if len(data["proxies"]) < init_len:
            await _write_db(data)
            return True
        return False

async def clear_all_proxies(user_id: int) -> int:
    async with DB_LOCK:
        data = await _read_db()
        init_len = len(data["proxies"])
        data["proxies"] = [p for p in data["proxies"] if p["user_id"] != user_id]
        deleted = init_len - len(data["proxies"])
        if deleted > 0: await _write_db(data)
        return deleted

async def add_site_db(user_id: int, site: str) -> bool:
    async with DB_LOCK:
        data = await _read_db()
        if any(s["user_id"] == user_id and s["site"] == site for s in data["sites"]): return False
        data["sites"].append({"user_id": user_id, "site": site, "added_at": datetime.datetime.utcnow().isoformat()})
        await _write_db(data)
        return True

async def get_user_sites(user_id: int):
    async with DB_LOCK:
        data = await _read_db()
        return [s["site"] for s in data["sites"] if s["user_id"] == user_id]

async def remove_site_db(user_id: int, site: str) -> bool:
    async with DB_LOCK:
        data = await _read_db()
        init_len = len(data["sites"])
        data["sites"] = [s for s in data["sites"] if not (s["user_id"] == user_id and s["site"] == site)]
        if len(data["sites"]) < init_len:
            await _write_db(data)
            return True
        return False

async def add_global_site(site: str) -> bool:
    async with DB_LOCK:
        data = await _read_db()
        if any(s["site"] == site for s in data["global_sites"]): return False
        data["global_sites"].append({"site": site})
        await _write_db(data)
        return True

async def get_global_sites():
    async with DB_LOCK:
        data = await _read_db()
        return [s["site"] for s in data["global_sites"]]

async def remove_global_site(site: str) -> bool:
    async with DB_LOCK:
        data = await _read_db()
        init_len = len(data["global_sites"])
        data["global_sites"] = [s for s in data["global_sites"] if s["site"] != site]
        if len(data["global_sites"]) < init_len:
            await _write_db(data)
            return True
        return False

async def get_total_users() -> int:
    async with DB_LOCK:
        data = await _read_db()
        return len(data["users"])

async def get_premium_count() -> int:
    async with DB_LOCK:
        data = await _read_db()
        return sum(1 for u in data["users"].values() if u.get("plan") in ["Core", "Elite", "Root", "X"])

async def get_total_sites_count() -> int:
    async with DB_LOCK:
        data = await _read_db()
        return len(data["sites"])
