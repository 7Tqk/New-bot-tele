import os
import json
import datetime
import random
import uuid

DB_FILE = "database.json"

def read_db():
    if not os.path.exists(DB_FILE):
        return {
            "users": {},
            "keys": [],
            "proxies": [],
            "sites": [],
            "cards": [],
            "global_sites": [],
            "joined_users": {}
        }
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {
            "users": {},
            "keys": [],
            "proxies": [],
            "sites": [],
            "cards": [],
            "global_sites": [],
            "joined_users": {}
        }

def write_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

async def init_db():
    try:
        data = read_db()
        write_db(data)
        print("✅ 𝗥𝗔𝗭𝗢𝗥 𝗫 𝗗𝗮𝘁𝗮𝗯𝗮𝘀𝗲 𝗶𝗻𝗶𝘁𝗶𝗮𝗹𝗶𝘇𝗲𝗱 𝘀𝘂𝗰𝗰𝗲𝘀𝘀𝗳𝘂𝗹𝗹𝘆! (Local JSON)")
    except Exception as e:
        print(f"⚠️ 𝗗𝗕 𝗶𝗻𝗶𝘁 𝘄𝗮𝗿𝗻𝗶𝗻𝗴: {e}")

async def ensure_user(user_id: int):
    data = read_db()
    uid_str = str(user_id)
    if uid_str not in data["users"]:
        data["users"][uid_str] = {
            "user_id": user_id,
            "plan": "Bronze",
            "expiry": None,
            "banned": False,
            "banned_by": None,
            "created_at": datetime.datetime.utcnow().isoformat()
        }
        write_db(data)

async def get_user_plan(user_id: int) -> str:
    data = read_db()
    uid_str = str(user_id)
    user = data["users"].get(uid_str)
    
    if not user:
        return "Bronze"
        
    plan = user.get("plan", "Bronze")
    expiry = user.get("expiry")
    
    if expiry:
        exp_date = datetime.datetime.fromisoformat(expiry)
        if datetime.datetime.utcnow() > exp_date:
            data["users"][uid_str]["plan"] = "Bronze"
            data["users"][uid_str]["expiry"] = None
            write_db(data)
            return "Bronze"
            
    return plan

async def set_user_plan(user_id: int, plan: str, days: int = 0):
    data = read_db()
    uid_str = str(user_id)
    
    expiry = None
    if days > 0:
        expiry = (datetime.datetime.utcnow() + datetime.timedelta(days=days)).isoformat()
        
    if uid_str not in data["users"]:
        data["users"][uid_str] = {"user_id": user_id, "created_at": datetime.datetime.utcnow().isoformat()}
        
    data["users"][uid_str]["plan"] = plan
    data["users"][uid_str]["expiry"] = expiry
    data["users"][uid_str]["premium_days"] = days
    data["users"][uid_str]["updated_at"] = datetime.datetime.utcnow().isoformat()
    
    write_db(data)

async def is_premium_user(user_id: int) -> bool:
    plan = await get_user_plan(user_id)
    return plan in ["Core", "Elite", "Root", "X"]

async def is_banned_user(user_id: int) -> bool:
    data = read_db()
    user = data["users"].get(str(user_id))
    return user.get("banned", False) if user else False

async def mark_user_joined(user_id: int):
    data = read_db()
    data["joined_users"][str(user_id)] = {
        "user_id": user_id,
        "joined_at": datetime.datetime.utcnow().isoformat()
    }
    write_db(data)

async def is_user_marked_joined(user_id: int) -> bool:
    data = read_db()
    return str(user_id) in data["joined_users"]

async def remove_joined_mark(user_id: int):
    data = read_db()
    if str(user_id) in data["joined_users"]:
        del data["joined_users"][str(user_id)]
        write_db(data)

async def add_proxy_db(user_id: int, proxy_data: dict):
    data = read_db()
    proxy_doc = {
        "_id": str(uuid.uuid4()),
        "user_id": user_id,
        "ip": proxy_data.get("ip"),
        "port": proxy_data.get("port"),
        "username": proxy_data.get("username"),
        "password": proxy_data.get("password"),
        "proxy_url": proxy_data.get("proxy_url"),
        "proxy_type": proxy_data.get("type", "http"),
        "added_at": datetime.datetime.utcnow().isoformat()
    }
    data["proxies"].append(proxy_doc)
    write_db(data)

async def get_all_user_proxies(user_id: int):
    data = read_db()
    user_proxies = [p for p in data["proxies"] if p["user_id"] == user_id]
    user_proxies.sort(key=lambda x: x.get("added_at", ""))
    return user_proxies[:200]

async def get_proxy_count(user_id: int) -> int:
    data = read_db()
    return sum(1 for p in data["proxies"] if p["user_id"] == user_id)

async def get_random_proxy(user_id: int):
    proxies = await get_all_user_proxies(user_id)
    if not proxies:
        return None
    return random.choice(proxies)

async def remove_proxy_by_index(user_id: int, index: int):
    data = read_db()
    user_proxies = [p for p in data["proxies"] if p["user_id"] == user_id]
    user_proxies.sort(key=lambda x: x.get("added_at", ""))
    
    if 0 <= index < len(user_proxies):
        target_proxy = user_proxies[index]
        data["proxies"] = [p for p in data["proxies"] if p.get("_id") != target_proxy.get("_id")]
        write_db(data)
        return target_proxy
    return None

async def remove_proxy_by_url(user_id: int, proxy_url: str):
    data = read_db()
    initial_length = len(data["proxies"])
    data["proxies"] = [p for p in data["proxies"] if not (p["user_id"] == user_id and p["proxy_url"] == proxy_url)]
    
    if len(data["proxies"]) < initial_length:
        write_db(data)
        return True
    return False

async def clear_all_proxies(user_id: int) -> int:
    data = read_db()
    initial_length = len(data["proxies"])
    data["proxies"] = [p for p in data["proxies"] if p["user_id"] != user_id]
    deleted_count = initial_length - len(data["proxies"])
    
    if deleted_count > 0:
        write_db(data)
    return deleted_count

async def add_site_db(user_id: int, site: str) -> bool:
    data = read_db()
    for s in data["sites"]:
        if s["user_id"] == user_id and s["site"] == site:
            return False
            
    data["sites"].append({
        "user_id": user_id,
        "site": site,
        "added_at": datetime.datetime.utcnow().isoformat()
    })
    write_db(data)
    return True

async def get_user_sites(user_id: int):
    data = read_db()
    return [s["site"] for s in data["sites"] if s["user_id"] == user_id]

async def remove_site_db(user_id: int, site: str) -> bool:
    data = read_db()
    initial_length = len(data["sites"])
    data["sites"] = [s for s in data["sites"] if not (s["user_id"] == user_id and s["site"] == site)]
    
    if len(data["sites"]) < initial_length:
        write_db(data)
        return True
    return False

async def add_global_site(site: str) -> bool:
    data = read_db()
    if any(s["site"] == site for s in data["global_sites"]):
        return False
        
    data["global_sites"].append({
        "site": site,
        "added_at": datetime.datetime.utcnow().isoformat()
    })
    write_db(data)
    return True

async def get_global_sites():
    data = read_db()
    return [s["site"] for s in data["global_sites"]]

async def remove_global_site(site: str) -> bool:
    data = read_db()
    initial_length = len(data["global_sites"])
    data["global_sites"] = [s for s in data["global_sites"] if s["site"] != site]
    
    if len(data["global_sites"]) < initial_length:
        write_db(data)
        return True
    return False

async def get_total_users() -> int:
    data = read_db()
    return len(data["users"])

async def get_premium_count() -> int:
    data = read_db()
    premium_plans = ["Core", "Elite", "Root", "X"]
    return sum(1 for u in data["users"].values() if u.get("plan") in premium_plans)

async def get_all_premium_users():
    data = read_db()
    premium_plans = ["Core", "Elite", "Root", "X"]
    return [u for u in data["users"].values() if u.get("plan") in premium_plans]

async def get_total_sites_count() -> int:
    data = read_db()
    return len(data["sites"])

async def get_users_with_sites() -> int:
    data = read_db()
    unique_users = set(s["user_id"] for s in data["sites"])
    return len(unique_users)

async def get_sites_per_user():
    data = read_db()
    counts = {}
    for s in data["sites"]:
        uid = s["user_id"]
        counts[uid] = counts.get(uid, 0) + 1
    return [{"user_id": k, "cnt": v} for k, v in counts.items()]

async def get_all_sites_detail():
    data = read_db()
    sorted_sites = sorted(data["sites"], key=lambda x: x["user_id"])
    return sorted_sites
    doc = await joined_col.find_one({"user_id": user_id})
    return doc is not None

async def remove_joined_mark(user_id: int):
    await joined_col.delete_one({"user_id": user_id})

async def add_proxy_db(user_id: int, proxy_data: dict):
    proxy_doc = {
        "user_id": user_id,
        "ip": proxy_data.get("ip"),
        "port": proxy_data.get("port"),
        "username": proxy_data.get("username"),
        "password": proxy_data.get("password"),
        "proxy_url": proxy_data.get("proxy_url"),
        "proxy_type": proxy_data.get("type", "http"),
        "added_at": datetime.datetime.utcnow()
    }
    await proxies_col.insert_one(proxy_doc)

async def get_all_user_proxies(user_id: int):
    cursor = proxies_col.find({"user_id": user_id}).sort("added_at", 1)
    return await cursor.to_list(length=200)

async def get_proxy_count(user_id: int) -> int:
    return await proxies_col.count_documents({"user_id": user_id})

async def get_random_proxy(user_id: int):
    import random
    proxies = await get_all_user_proxies(user_id)
    if not proxies:
        return None
    return random.choice(proxies)

async def remove_proxy_by_index(user_id: int, index: int):
    proxies = await get_all_user_proxies(user_id)
    if 0 <= index < len(proxies):
        proxy = proxies[index]
        await proxies_col.delete_one({"_id": proxy["_id"]})
        return proxy
    return None

async def remove_proxy_by_url(user_id: int, proxy_url: str):
    result = await proxies_col.delete_one({
        "user_id": user_id,
        "proxy_url": proxy_url
    })
    return result.deleted_count > 0

async def clear_all_proxies(user_id: int) -> int:
    result = await proxies_col.delete_many({"user_id": user_id})
    return result.deleted_count

async def add_site_db(user_id: int, site: str) -> bool:
    existing = await sites_col.find_one({"user_id": user_id, "site": site})
    if existing:
        return False
    await sites_col.insert_one({
        "user_id": user_id,
        "site": site,
        "added_at": datetime.datetime.utcnow()
    })
    return True

async def get_user_sites(user_id: int):
    cursor = sites_col.find({"user_id": user_id})
    docs = await cursor.to_list(length=50000)
    return [doc["site"] for doc in docs]

async def remove_site_db(user_id: int, site: str) -> bool:
    result = await sites_col.delete_one({"user_id": user_id, "site": site})
    return result.deleted_count > 0

async def add_global_site(site: str) -> bool:
    try:
        await global_sites_col.insert_one({
            "site": site,
            "added_at": datetime.datetime.utcnow()
        })
        return True
    except:
        return False

async def get_global_sites():
    cursor = global_sites_col.find()
    docs = await cursor.to_list(length=10000)
    return [doc["site"] for doc in docs]

async def remove_global_site(site: str) -> bool:
    result = await global_sites_col.delete_one({"site": site})
    return result.deleted_count > 0

async def get_total_users() -> int:
    return await users_col.count_documents({})

async def get_premium_count() -> int:
    return await users_col.count_documents({
        "plan": {"$in": ["Core", "Elite", "Root", "X"]}
    })

async def get_all_premium_users():
    cursor = users_col.find({"plan": {"$in": ["Core", "Elite", "Root", "X"]}})
    return await cursor.to_list(length=1000)

async def get_total_sites_count() -> int:
    return await sites_col.count_documents({})

async def get_users_with_sites() -> int:
    pipeline = [{"$group": {"_id": "$user_id"}}]
    result = await sites_col.aggregate(pipeline).to_list(length=10000)
    return len(result)

async def get_sites_per_user():
    pipeline = [
        {"$group": {"_id": "$user_id", "cnt": {"$sum": 1}}},
        {"$project": {"user_id": "$_id", "cnt": 1, "_id": 0}}
    ]
    return await sites_col.aggregate(pipeline).to_list(length=1000)

async def get_all_sites_detail():
    cursor = sites_col.find().sort("user_id", 1)
    return await cursor.to_list(length=10000)
