"""
初始化用户数据 + HR 假期数据
运行: python seed_users.py
"""
import asyncio
import uuid
from datetime import datetime, date
from motor.motor_asyncio import AsyncIOMotorClient
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from app.config import settings

# TODO: 恢复加密时替换为 bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()
def hash_password(password: str) -> str:
    return password  # 暂时明文存储

USERS = [
    {
        "_id": str(uuid.uuid4()),
        "username": "hr",
        "email": "hr@company.com",
        "hashed_password": hash_password("123"),
        "display_name": "HR",
        "role": "hr",
        "department": "人力资源部",
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    },
    {
        "_id": str(uuid.uuid4()),
        "username": "bob",
        "email": "bob@company.com",
        "hashed_password": hash_password("123"),
        "display_name": "Bob",
        "role": "employee",
        "department": "研发部",
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    },
]

# HR 假期余额数据（一条记录包含所有假期类型）
HR_LEAVE_BALANCE = {
    "_id": str(uuid.uuid4()),
    "username": "hr",
    "year": 2026,
    "balances": {
        "年假": {"total_days": 15, "used_days": 5, "remaining_days": 10},
        "病假": {"total_days": 10, "used_days": 2, "remaining_days": 8},
        "事假": {"total_days": 5,  "used_days": 1, "remaining_days": 4},
        "婚假": {"total_days": 3,  "used_days": 0, "remaining_days": 3},
    },
    "updated_at": datetime.utcnow(),
}


async def seed():
    client = AsyncIOMotorClient(settings.mongo_url)
    db = client[settings.mongo_db_name]

    # ── 用户 ──────────────────────────────────────────────
    print("=== 用户数据 ===")
    users_col = db["users"]
    for user in USERS:
        user_data = {k: v for k, v in user.items() if k != "_id"}
        result = await users_col.update_one(
            {"username": user["username"]},
            {"$set": user_data},
            upsert=True
        )
        action = "更新" if result.matched_count else "创建"
        print(f"[{action}] {user['username']} ({user['role']})  密码=123")

    # ── 假期余额 ──────────────────────────────────────────────
    print("\n=== HR 假期余额数据 ===")
    balances_col = db["leave_balances"]
    await balances_col.delete_many({"username": "hr"})
    await balances_col.insert_one(HR_LEAVE_BALANCE)
    print("[OK] 写入 1 条余额记录")

    # ── 汇总 ──────────────────────────────────────────────
    print("\n=== 当前用户列表 ===")
    async for u in users_col.find({}, {"username": 1, "role": 1, "display_name": 1, "department": 1}):
        print(f"  {u['username']:8} role={u['role']:10} name={u['display_name']}  dept={u.get('department','')}")

    print("\n=== HR 假期余额 ===")
    doc = await balances_col.find_one({"username": "hr"}, {"_id": 0, "username": 0, "updated_at": 0})
    print(f"  year={doc['year']}")
    for leave_type, data in doc["balances"].items():
        print(f"  {leave_type:4}  总={data['total_days']}天  已用={data['used_days']}天  剩余={data['remaining_days']}天")

    client.close()


if __name__ == "__main__":
    asyncio.run(seed())
