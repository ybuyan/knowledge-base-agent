"""
端到端测试 - 模拟完整的 Chat API 流程
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.agents.base import agent_engine
from app.agents.implementations import GuideAgent, OrchestratorAgent
from app.services.message_service import message_service

DEFAULT_USER_ID = "default_user"


async def test_end_to_end():
    """端到端测试"""
    
    # 注册 agents
    agent_engine.register(GuideAgent())
    agent_engine.register(OrchestratorAgent())
    
    # 创建测试 session
    session_id = "test_e2e_session"
    
    print("=" * 80)
    print("端到端测试：完整模拟 Chat API 流程")
    print("=" * 80)
    
    # ========== 第一轮对话 ==========
    print("\n【第一轮】用户: 我想请婚假")
    print("-" * 80)
    
    query1 = "我想请婚假"
    
    # 1. 获取历史（应该为空）
    messages = await message_service.get_messages(session_id, DEFAULT_USER_ID)
    history1 = []
    for msg in messages[-12:]:
        history1.append({"role": msg["role"], "content": msg["content"]})
    
    print(f"✅ 获取历史消息: {len(history1)} 条")
    
    # 2. 调用 OrchestratorAgent
    result1 = await agent_engine.execute(
        "orchestrator_agent",
        {
            "query": query1,
            "session_id": session_id,
            "history": history1
        }
    )
    
    print(f"✅ OrchestratorAgent 返回:")
    print(f"   - intent: {result1.get('intent')}")
    print(f"   - answer 长度: {len(result1.get('answer', ''))}")
    print(f"   - answer 前50字: {result1.get('answer', '')[:50]}")
    
    # 3. 持久化对话
    answer1 = result1.get("answer", "")
    
    # 保存用户消息
    await message_service.add_message(
        session_id=session_id,
        user_id=DEFAULT_USER_ID,
        role="user",
        content=query1
    )
    
    # 保存AI回复
    await message_service.add_message(
        session_id=session_id,
        user_id=DEFAULT_USER_ID,
        role="assistant",
        content=answer1
    )
    
    print(f"✅ 对话已持久化")
    
    # ========== 第二轮对话 ==========
    print("\n" + "=" * 80)
    print("【第二轮】用户: 应为 2024年2月14日 领证")
    print("-" * 80)
    
    query2 = "应为 2024年2月14日 领证"
    
    # 1. 获取历史（应该包含第一轮）
    messages = await message_service.get_messages(session_id, DEFAULT_USER_ID)
    history2 = []
    for msg in messages[-12:]:
        history2.append({"role": msg["role"], "content": msg["content"]})
    
    print(f"✅ 获取历史消息: {len(history2)} 条")
    if history2:
        for i, msg in enumerate(history2):
            print(f"   [{i}] {msg['role']}: {msg['content'][:30]}")
    
    # 2. 调用 OrchestratorAgent
    result2 = await agent_engine.execute(
        "orchestrator_agent",
        {
            "query": query2,
            "session_id": session_id,
            "history": history2
        }
    )
    
    print(f"\n✅ OrchestratorAgent 返回:")
    print(f"   - intent: {result2.get('intent')}")
    print(f"   - answer 长度: {len(result2.get('answer', ''))}")
    print(f"   - answer 前100字: {result2.get('answer', '')[:100]}")
    
    # 检查结果
    if result2.get('intent') == 'guide' and len(result2.get('answer', '')) > 50:
        print("\n🎉 测试通过！多轮对话正常工作")
    else:
        print(f"\n❌ 测试失败！")
        print(f"   期望: intent='guide', answer 长度 > 50")
        print(f"   实际: intent='{result2.get('intent')}', answer 长度 = {len(result2.get('answer', ''))}")


if __name__ == "__main__":
    asyncio.run(test_end_to_end())
