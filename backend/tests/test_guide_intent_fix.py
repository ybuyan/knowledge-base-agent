"""
测试 Guide Intent 修复
验证 GuideAgent 返回的 intent 字段能正确阻止 QA Agent 二次执行
"""
import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.agents.base import agent_engine
from app.agents.implementations import GuideAgent


async def test_guide_intent():
    """测试 GuideAgent 是否返回 intent 字段"""
    
    # 注册 GuideAgent
    agent_engine.register(GuideAgent())
    
    print("=" * 60)
    print("测试 1: GuideAgent 返回 intent 字段")
    print("=" * 60)
    
    # 模拟 OrchestratorAgent 调用 GuideAgent
    result = await agent_engine.execute(
        "guide_agent",
        {
            "query": "我想请婚假",
            "session_id": "test_session",
            "history": []
        }
    )
    
    print(f"\n✅ GuideAgent 返回结果:")
    print(f"   - answer 长度: {len(result.get('answer', ''))}")
    print(f"   - intent 字段: {result.get('intent', 'NOT_FOUND')}")
    print(f"   - session_id: {result.get('session_id', 'NOT_FOUND')}")
    
    # 验证 intent 字段
    if result.get("intent") == "guide":
        print("\n✅ 测试通过：GuideAgent 正确返回 intent='guide'")
    else:
        print(f"\n❌ 测试失败：GuideAgent 未返回 intent='guide'，实际值: {result.get('intent')}")
        return False
    
    print("\n" + "=" * 60)
    print("测试 2: 短查询 + 历史记录匹配")
    print("=" * 60)
    
    # 测试短查询（依赖历史记录匹配）
    result2 = await agent_engine.execute(
        "guide_agent",
        {
            "query": "流程是什么",
            "session_id": "test_session",
            "history": [
                {"role": "user", "content": "我想请婚假"},
                {"role": "assistant", "content": "好的，我来帮您了解婚假申请流程..."}
            ]
        }
    )
    
    print(f"\n✅ GuideAgent 返回结果:")
    print(f"   - answer 长度: {len(result2.get('answer', ''))}")
    print(f"   - intent 字段: {result2.get('intent', 'NOT_FOUND')}")
    
    if result2.get("intent") == "guide":
        print("\n✅ 测试通过：短查询也正确返回 intent='guide'")
    else:
        print(f"\n❌ 测试失败：短查询未返回 intent='guide'，实际值: {result2.get('intent')}")
        return False
    
    print("\n" + "=" * 60)
    print("测试 3: 模拟 chat API 的 orch_handled 检查")
    print("=" * 60)
    
    # 模拟 chat API 的检查逻辑
    orch_result = result2
    orch_handled = (
        orch_result.get("ui_components") is not None or
        orch_result.get("process_state") is not None or
        orch_result.get("intent") in ("confirm", "memory", "hybrid", "guide")
    )
    
    print(f"\n✅ orch_handled 检查结果: {orch_handled}")
    
    if orch_handled:
        print("✅ 测试通过：chat API 会正确处理 guide 意图，不会再调用 QA Agent")
    else:
        print("❌ 测试失败：chat API 会错误地继续调用 QA Agent")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 所有测试通过！")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = asyncio.run(test_guide_intent())
    sys.exit(0 if success else 1)
