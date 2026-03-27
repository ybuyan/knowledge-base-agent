import sys
import os
import asyncio

sys.path.insert(0, 'backend')

# 必须先导入并注册 agents
from app.agents.implementations import QAAgent
from app.agents import agent_engine

# 注册 agent
agent_engine.register(QAAgent())

async def test():
    result = await agent_engine.execute("qa_agent", {
        "question": "公司有哪些福利？",
        "session_id": "test"
    })
    
    print(f"回答长度: {len(result.get('answer', ''))}")
    print(f"来源数量: {len(result.get('sources', []))}")
    
    if result.get('sources'):
        print(f"\n来源:")
        for i, s in enumerate(result['sources'][:3]):
            print(f"  {i+1}. {s.get('filename')}: {s.get('content', '')[:60]}...")

asyncio.run(test())
