"""
测试基于上下文的 skill 匹配
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


async def test_context_matching():
    """测试基于上下文的匹配"""
    print("=" * 80)
    print("测试基于上下文的 Skill 匹配")
    print("=" * 80)
    
    # 模拟对话：用户先提到婚假，然后简短查询
    conversations = [
        "我想请婚假",
        "流程是什么",  # 简短查询，不包含"婚假"关键词
        "需要什么材料",  # 另一个简短查询
    ]
    
    history = []
    session_id = "test_context"
    
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
            
            if answer == "抱歉，我暂时无法提供该流程的指引。请联系管理员。":
                print(f"\n❌ 匹配失败，返回默认回复")
            else:
                print(f"\n✅ 匹配成功")
            
            print(f"\n助手:\n{answer[:200]}...\n")
            
            # 更新历史
            history.append({"role": "user", "content": query})
            history.append({"role": "assistant", "content": answer})
            
        except Exception as e:
            print(f"\n❌ 执行失败: {e}")
            import traceback
            traceback.print_exc()
            break
    
    print(f"\n{'=' * 80}")
    print("测试完成")
    print(f"{'=' * 80}")


if __name__ == "__main__":
    asyncio.run(test_context_matching())
