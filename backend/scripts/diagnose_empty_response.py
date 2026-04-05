"""
诊断空响应问题
"""
import sys
import asyncio
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# 设置详细日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s:%(name)s:%(message)s'
)

from app.agents.implementations import DocumentAgent, QAAgent, MemoryAgent, OrchestratorAgent, GuideAgent
from app.agents.base import agent_engine

# 注册 agents
agent_engine.register(DocumentAgent())
agent_engine.register(QAAgent())
agent_engine.register(MemoryAgent())
agent_engine.register(OrchestratorAgent())
agent_engine.register(GuideAgent())


async def diagnose():
    """诊断空响应"""
    print("=" * 80)
    print("诊断空响应问题")
    print("=" * 80)
    
    # 第1轮
    print("\n第1轮：我想请婚假")
    print("-" * 80)
    
    result1 = await agent_engine.execute("orchestrator_agent", {
        "query": "我想请婚假",
        "session_id": "diagnose",
        "history": []
    })
    
    answer1 = result1.get('answer', '')
    print(f"\n返回长度: {len(answer1)}")
    print(f"返回内容: {answer1[:200] if answer1 else '【空】'}...")
    
    history = [
        {"role": "user", "content": "我想请婚假"},
        {"role": "assistant", "content": answer1}
    ]
    
    # 第2轮
    print("\n" + "=" * 80)
    print("第2轮：流程是什么")
    print("-" * 80)
    
    result2 = await agent_engine.execute("orchestrator_agent", {
        "query": "流程是什么",
        "session_id": "diagnose",
        "history": history
    })
    
    answer2 = result2.get('answer', '')
    print(f"\n返回长度: {len(answer2)}")
    print(f"返回内容: {answer2[:200] if answer2 else '【空】'}...")
    
    # 检查
    print("\n" + "=" * 80)
    print("诊断结果")
    print("=" * 80)
    
    if not answer1:
        print("❌ 第1轮返回为空")
    else:
        print(f"✅ 第1轮返回正常 ({len(answer1)} 字符)")
    
    if not answer2:
        print("❌ 第2轮返回为空")
    else:
        print(f"✅ 第2轮返回正常 ({len(answer2)} 字符)")


if __name__ == "__main__":
    asyncio.run(diagnose())
