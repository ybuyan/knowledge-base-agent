"""
测试多轮对话请假指引
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


async def test_multi_turn():
    """测试多轮对话"""
    print("=" * 80)
    print("多轮对话请假指引测试")
    print("=" * 80)
    
    # 模拟多轮对话
    conversations = [
        ("我想请假", "第1轮：初始请求"),
        ("年假", "第2轮：选择假期类型"),
        ("3天", "第3轮：告知天数"),
        ("6月15日开始", "第4轮：告知时间"),
        ("对的，没问题", "第5轮：确认信息"),
    ]
    
    history = []
    session_id = "test_multi_turn"
    
    for i, (query, description) in enumerate(conversations, 1):
        print(f"\n{'=' * 80}")
        print(f"{description}")
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
            
            # 如果是最后一轮，检查是否生成了完整指引
            if i == len(conversations):
                if "申请流程" in answer and "申请模板" in answer:
                    print("\n✅ 成功生成完整的个性化指引！")
                else:
                    print("\n⚠️  可能需要更多轮对话")
            
        except Exception as e:
            print(f"\n❌ 执行失败: {e}")
            import traceback
            traceback.print_exc()
            break
    
    print(f"\n{'=' * 80}")
    print("测试完成")
    print(f"{'=' * 80}")


if __name__ == "__main__":
    asyncio.run(test_multi_turn())
