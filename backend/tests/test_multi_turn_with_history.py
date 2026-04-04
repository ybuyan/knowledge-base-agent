"""
测试带历史记录的多轮对话
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

from app.agents.implementations import DocumentAgent, QAAgent, MemoryAgent, OrchestratorAgent, GuideAgent
from app.agents.base import agent_engine

# 注册 agents
agent_engine.register(DocumentAgent())
agent_engine.register(QAAgent())
agent_engine.register(MemoryAgent())
agent_engine.register(OrchestratorAgent())
agent_engine.register(GuideAgent())


async def test_with_history():
    """测试带历史记录的多轮对话"""
    print("=" * 80)
    print("测试多轮对话（带历史记录）")
    print("=" * 80)
    
    # 模拟对话
    conversations = [
        "我想请婚假",
        "我可以正常申请婚假，我需要怎么做",
    ]
    
    history = []
    session_id = "test_history"
    
    for i, query in enumerate(conversations, 1):
        print(f"\n{'=' * 80}")
        print(f"第 {i} 轮对话")
        print(f"{'=' * 80}")
        print(f"\n用户: {query}\n")
        print("-" * 80)
        
        try:
            result = await agent_engine.execute("orchestrator_agent", {
                "query": query,
                "session_id": session_id,
                "history": history
            })
            
            answer = result.get('answer', '无回答')
            print(f"\n助手:\n{answer}\n")
            
            # 更新历史
            history.append({"role": "user", "content": query})
            history.append({"role": "assistant", "content": answer})
            
            print(f"\n当前历史记录长度: {len(history)}")
            
        except Exception as e:
            print(f"\n❌ 执行失败: {e}")
            import traceback
            traceback.print_exc()
            break
    
    print(f"\n{'=' * 80}")
    print("测试完成")
    print(f"{'=' * 80}")


if __name__ == "__main__":
    asyncio.run(test_with_history())
