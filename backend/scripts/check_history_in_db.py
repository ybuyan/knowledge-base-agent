"""
检查数据库中的历史记录
"""
import asyncio
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.message_service import message_service
from app.services.session_service import session_service

DEFAULT_USER_ID = "default_user"


async def check_history():
    """检查数据库中的历史记录"""
    
    print("=" * 80)
    print("检查数据库中的历史记录")
    print("=" * 80)
    
    # 获取所有会话
    sessions = await session_service.get_sessions(DEFAULT_USER_ID, skip=0, limit=10)
    
    print(f"\n✅ 找到 {len(sessions)} 个会话")
    
    if not sessions:
        print("❌ 没有找到任何会话")
        return
    
    # 显示最近的会话
    for i, session in enumerate(sessions[:5]):
        session_id = str(session["_id"])
        title = session.get("title", "未命名")
        created_at = session.get("created_at", "")
        message_count = session.get("message_count", 0)
        
        print(f"\n{'=' * 80}")
        print(f"会话 {i+1}: {title}")
        print(f"Session ID: {session_id}")
        print(f"创建时间: {created_at}")
        print(f"消息数量: {message_count}")
        print("-" * 80)
        
        # 获取该会话的消息
        messages = await message_service.get_messages(session_id, DEFAULT_USER_ID)
        
        if not messages:
            print("   ❌ 该会话没有消息")
            continue
        
        print(f"   ✅ 该会话有 {len(messages)} 条消息:")
        
        for j, msg in enumerate(messages):
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            created_at = msg.get("created_at", "")
            
            # 格式化时间
            if isinstance(created_at, datetime):
                time_str = created_at.strftime("%H:%M:%S")
            else:
                time_str = str(created_at)
            
            # 截断内容
            content_preview = content[:50] + "..." if len(content) > 50 else content
            
            print(f"   [{j+1}] {time_str} | {role:10s} | {content_preview}")
    
    # 测试获取历史记录的功能
    print("\n" + "=" * 80)
    print("测试：模拟 Chat API 获取历史记录")
    print("=" * 80)
    
    if sessions:
        test_session_id = str(sessions[0]["_id"])
        print(f"\n使用会话: {test_session_id}")
        
        # 模拟 Chat API 的历史记录获取逻辑
        messages = await message_service.get_messages(test_session_id, DEFAULT_USER_ID)
        history = []
        for msg in messages[-12:]:  # 最近12条
            try:
                role = msg["role"] if isinstance(msg, dict) else getattr(msg, "role", "user")
                content = msg["content"] if isinstance(msg, dict) else getattr(msg, "content", "")
                history.append({"role": role, "content": content})
            except Exception as e:
                print(f"   ❌ 解析消息失败: {e}")
        
        print(f"\n✅ 构建的历史记录: {len(history)} 条")
        for i, msg in enumerate(history):
            content_preview = msg["content"][:50] + "..." if len(msg["content"]) > 50 else msg["content"]
            print(f"   [{i}] {msg['role']:10s} | {content_preview}")
        
        # 检查是否包含 "婚假" 关键词
        has_marriage_leave = any("婚假" in msg["content"] for msg in history if msg["role"] == "user")
        print(f"\n✅ 历史记录中是否包含'婚假': {has_marriage_leave}")
        
        if has_marriage_leave:
            print("   ✅ 应该能够通过历史记录匹配到 leave_guide skill")
        else:
            print("   ❌ 无法通过历史记录匹配到 leave_guide skill")


if __name__ == "__main__":
    asyncio.run(check_history())
