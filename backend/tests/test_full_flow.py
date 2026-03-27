#!/usr/bin/env python
"""
完整测试：模拟前端请求，验证 sources 和消息保存
"""
import sys
sys.path.insert(0, 'c:\\D\\code\\learning\\Agent\\AI-assistent\\backend')

import asyncio
import json
from app.core.mongodb import connect_to_mongo, close_mongo_connection
from app.services.qa_agent import get_qa_agent
from app.services.response_builder import ResponseBuilder
from app.services.session_service import session_service
from app.services.message_service import message_service

async def test_full_flow():
    """测试完整的问答流程"""
    
    # 0. 初始化 MongoDB 连接
    print("=" * 60)
    print("0. 初始化 MongoDB 连接")
    print("=" * 60)
    
    connected = await connect_to_mongo()
    if not connected:
        print("⚠️ MongoDB 未连接，跳过数据库测试")
        print("将只测试 sources 返回...")
        
        # 只测试 sources 返回
        agent = get_qa_agent()
        query = "产假天数"
        print(f"\n查询: {query}")
        
        sources = []
        async for chunk in agent.process(query, []):
            if chunk.startswith("data: "):
                data_str = chunk[6:].strip()
                if data_str:
                    try:
                        data = json.loads(data_str)
                        if data.get("type") == "done":
                            sources = data.get("sources", [])
                    except:
                        pass
        
        print(f"\n返回的 sources: {sources}")
        if sources:
            print(f"✅ Sources 正确! Filename: {sources[0].get('filename', 'N/A')}")
        else:
            print("❌ Sources 为空!")
        return
    
    # 1. 创建测试 session
    print("=" * 60)
    print("1. 创建测试 session")
    print("=" * 60)
    
    session = await session_service.create_session(
        user_id="default_user",
        title="测试会话"
    )
    
    if session is None:
        print("❌ 创建 session 失败!")
        return
    
    session_id = str(session["_id"])
    print(f"Session ID: {session_id}")
    
    # 2. 模拟问答
    test_queries = [
        "产假天数",
        "法定产假时长",
    ]
    
    agent = get_qa_agent()
    
    for query in test_queries:
        print(f"\n{'=' * 60}")
        print(f"查询: {query}")
        print("=" * 60)
        
        full_response = ""
        sources = []
        
        async for chunk in agent.process(query, []):
            if chunk.startswith("data: "):
                data_str = chunk[6:].strip()
                if data_str:
                    try:
                        data = json.loads(data_str)
                        if data.get("type") == "text":
                            full_response += data.get("content", "")
                            print(f"Text chunk: {data.get('content', '')[:50]}...")
                        elif data.get("type") == "done":
                            sources = data.get("sources", [])
                            print(f"\nDone chunk received!")
                            print(f"Sources: {sources}")
                    except:
                        pass
        
        # 3. 保存消息
        print(f"\n保存消息...")
        print(f"Full response length: {len(full_response)}")
        print(f"Sources count: {len(sources)}")
        
        if sources:
            print(f"Source filename: {sources[0].get('filename', 'N/A')}")
        
        # 保存到数据库
        await message_service.add_message(
            session_id=session_id,
            user_id="default_user",
            role="user",
            content=query
        )
        
        await message_service.add_message(
            session_id=session_id,
            user_id="default_user",
            role="assistant",
            content=full_response,
            sources=sources
        )
        
        await session_service.update_session_activity(session_id, full_response)
        
        print(f"消息已保存!")
    
    # 4. 验证消息已保存
    print(f"\n{'=' * 60}")
    print("验证消息已保存")
    print("=" * 60)
    
    messages = await message_service.get_messages(session_id, "default_user")
    print(f"找到 {len(messages)} 条消息")
    
    for msg in messages:
        print(f"  - Role: {msg['role']}")
        print(f"    Content: {msg['content'][:50]}...")
        if msg.get('sources'):
            print(f"    Sources: {msg['sources']}")
    
    # 5. 清理测试数据
    print(f"\n清理测试数据...")
    await session_service.delete_session(session_id, "default_user")
    print("测试完成!")
    
    await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(test_full_flow())
