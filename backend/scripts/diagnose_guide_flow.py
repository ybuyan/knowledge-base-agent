"""
诊断 Guide 流程 - 完整追踪从 OrchestratorAgent 到 Chat API 的流程
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.agents.base import agent_engine
from app.agents.implementations import GuideAgent, OrchestratorAgent


async def diagnose():
    """完整诊断流程"""
    
    # 注册 agents
    agent_engine.register(GuideAgent())
    agent_engine.register(OrchestratorAgent())
    
    print("=" * 80)
    print("诊断场景：用户先问'我想请婚假'，然后问'2024年4月24号'")
    print("=" * 80)
    
    # 第一轮对话
    print("\n【第一轮】用户: 我想请婚假")
    print("-" * 80)
    
    result1 = await agent_engine.execute(
        "orchestrator_agent",
        {
            "query": "我想请婚假",
            "session_id": "test_session",
            "history": []
        }
    )
    
    print(f"\n✅ OrchestratorAgent 返回:")
    print(f"   - intent: {result1.get('intent', 'NOT_FOUND')}")
    print(f"   - answer 长度: {len(result1.get('answer', ''))}")
    print(f"   - answer 前100字: {result1.get('answer', '')[:100]}")
    
    # 模拟 chat API 的检查
    orch_handled_1 = (
        result1.get("ui_components") is not None or
        result1.get("process_state") is not None or
        result1.get("intent") in ("confirm", "memory", "hybrid", "guide")
    )
    print(f"\n✅ Chat API orch_handled 检查: {orch_handled_1}")
    
    if not orch_handled_1:
        print("❌ 警告：Chat API 会继续调用 QA Agent！")
    else:
        print("✅ 正确：Chat API 会直接返回结果，不调用 QA Agent")
    
    # 第二轮对话
    print("\n" + "=" * 80)
    print("【第二轮】用户: 2024年4月24号")
    print("-" * 80)
    
    history = [
        {"role": "user", "content": "我想请婚假"},
        {"role": "assistant", "content": result1.get("answer", "")}
    ]
    
    result2 = await agent_engine.execute(
        "orchestrator_agent",
        {
            "query": "2024年4月24号",
            "session_id": "test_session",
            "history": history
        }
    )
    
    print(f"\n✅ OrchestratorAgent 返回:")
    print(f"   - intent: {result2.get('intent', 'NOT_FOUND')}")
    print(f"   - answer 长度: {len(result2.get('answer', ''))}")
    print(f"   - answer 前100字: {result2.get('answer', '')[:100]}")
    
    # 模拟 chat API 的检查
    orch_handled_2 = (
        result2.get("ui_components") is not None or
        result2.get("process_state") is not None or
        result2.get("intent") in ("confirm", "memory", "hybrid", "guide")
    )
    print(f"\n✅ Chat API orch_handled 检查: {orch_handled_2}")
    
    if not orch_handled_2:
        print("❌ 警告：Chat API 会继续调用 QA Agent！")
    else:
        print("✅ 正确：Chat API 会直接返回结果，不调用 QA Agent")
    
    # 检查返回的完整结构
    print("\n" + "=" * 80)
    print("【详细检查】result2 的完整结构:")
    print("-" * 80)
    for key, value in result2.items():
        if isinstance(value, str) and len(value) > 100:
            print(f"   {key}: (长度 {len(value)}) {value[:100]}...")
        else:
            print(f"   {key}: {value}")
    
    print("\n" + "=" * 80)
    print("诊断完成")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(diagnose())
