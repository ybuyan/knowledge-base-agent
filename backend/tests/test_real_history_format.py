"""
测试真实的历史记录格式
模拟 chat API 传递给 OrchestratorAgent 的实际历史记录
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.agents.base import agent_engine
from app.agents.implementations import GuideAgent, OrchestratorAgent


async def test_real_format():
    """测试真实的历史记录格式"""
    
    # 注册 agents
    agent_engine.register(GuideAgent())
    agent_engine.register(OrchestratorAgent())
    
    print("=" * 80)
    print("测试：模拟真实的历史记录格式")
    print("=" * 80)
    
    # 第一轮对话
    print("\n【第一轮】用户: 我想请婚假")
    result1 = await agent_engine.execute(
        "orchestrator_agent",
        {
            "query": "我想请婚假",
            "session_id": "test_session",
            "history": []
        }
    )
    
    print(f"✅ 返回 intent: {result1.get('intent')}")
    print(f"✅ 返回 answer 前50字: {result1.get('answer', '')[:50]}")
    
    # 模拟 chat API 构建的历史记录（从数据库读取）
    # 注意：chat API 从 message_service.get_messages() 获取历史
    # 格式是: {"role": "user/assistant", "content": "..."}
    history = [
        {"role": "user", "content": "我想请婚假"},
        {"role": "assistant", "content": result1.get("answer", "")}
    ]
    
    print(f"\n📝 构建的历史记录:")
    print(f"   - 历史记录长度: {len(history)}")
    print(f"   - history[0]: role={history[0]['role']}, content前30字={history[0]['content'][:30]}")
    print(f"   - history[1]: role={history[1]['role']}, content前30字={history[1]['content'][:30]}")
    
    # 第二轮对话
    print("\n" + "=" * 80)
    print("【第二轮】用户: 2024年4月24号")
    print("-" * 80)
    
    result2 = await agent_engine.execute(
        "orchestrator_agent",
        {
            "query": "2024年4月24号",
            "session_id": "test_session",
            "history": history
        }
    )
    
    print(f"\n✅ 返回 intent: {result2.get('intent')}")
    print(f"✅ 返回 answer 前100字: {result2.get('answer', '')[:100]}")
    
    if result2.get('intent') == 'guide':
        print("\n🎉 成功！正确识别为 guide 意图")
    else:
        print(f"\n❌ 失败！错误识别为 {result2.get('intent')} 意图")
        print(f"   memories: {result2.get('memories', 'N/A')}")
        print(f"   qa: {result2.get('qa', 'N/A')}")


if __name__ == "__main__":
    asyncio.run(test_real_format())
