"""
端到端测试 GuideAgent
"""
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# 导入并注册所有 agents
from app.agents.implementations import DocumentAgent, QAAgent, MemoryAgent, OrchestratorAgent, GuideAgent
from app.agents.base import agent_engine

# 注册 agents
agent_engine.register(DocumentAgent())
agent_engine.register(QAAgent())
agent_engine.register(MemoryAgent())
agent_engine.register(OrchestratorAgent())
agent_engine.register(GuideAgent())


async def test_guide_agent():
    """测试 GuideAgent 端到端流程"""
    print("=" * 70)
    print("端到端测试 GuideAgent")
    print("=" * 70)
    
    # 测试数据
    test_cases = [
        {
            "query": "我想请假",
            "session_id": "test_session_001",
            "history": []
        },
        {
            "query": "怎么请假",
            "session_id": "test_session_002",
            "history": []
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'=' * 70}")
        print(f"测试用例 {i}: {test_case['query']}")
        print(f"{'=' * 70}")
        
        try:
            # 通过 Orchestrator 执行（模拟真实流程）
            result = await agent_engine.execute("orchestrator_agent", test_case)
            
            print(f"\n✅ 执行成功")
            print(f"\n回答:\n{result.get('answer', '无回答')}")
            
            if "intent" in result:
                print(f"\n意图: {result['intent']}")
            
        except Exception as e:
            print(f"\n❌ 执行失败: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'=' * 70}")
    print("测试完成")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    asyncio.run(test_guide_agent())
