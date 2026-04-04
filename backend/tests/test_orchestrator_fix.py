"""
测试 Orchestrator 修复
"""
import sys
import asyncio
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

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


async def test_query():
    """测试查询"""
    print("=" * 80)
    print("测试: 请假申请怎么写")
    print("=" * 80)
    
    try:
        result = await agent_engine.execute("orchestrator_agent", {
            "query": "请假申请怎么写",
            "session_id": "test_fix",
            "history": []
        })
        
        print("\n✅ 执行成功")
        print(f"\n回答:\n{result.get('answer', '无回答')[:200]}...")
        
    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_query())
