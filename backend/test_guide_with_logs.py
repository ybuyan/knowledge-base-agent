"""
测试 GuideAgent 并显示详细日志
"""
import sys
import asyncio
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# 配置日志 - 显示所有 INFO 级别的日志
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)

# 导入并注册所有 agents
from app.agents.implementations import DocumentAgent, QAAgent, MemoryAgent, OrchestratorAgent, GuideAgent
from app.agents.base import agent_engine

# 注册 agents
agent_engine.register(DocumentAgent())
agent_engine.register(QAAgent())
agent_engine.register(MemoryAgent())
agent_engine.register(OrchestratorAgent())
agent_engine.register(GuideAgent())


async def test_with_logs():
    """测试并显示详细日志"""
    print("=" * 80)
    print("GuideAgent 日志追踪测试")
    print("=" * 80)
    print("\n提示：查找带有 [GUIDE]、[SKILL]、[LLM] 标记的日志\n")
    print("=" * 80)
    
    test_query = "我想请假"
    
    print(f"\n📨 用户查询: {test_query}\n")
    print("-" * 80)
    
    try:
        result = await agent_engine.execute("orchestrator_agent", {
            "query": test_query,
            "session_id": "test_session_logs",
            "history": []
        })
        
        print("-" * 80)
        print(f"\n✅ 执行成功\n")
        print(f"回答:\n{result.get('answer', '无回答')}\n")
        
    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_with_logs())
