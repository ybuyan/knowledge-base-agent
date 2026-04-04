"""
测试婚假相关查询的意图识别
"""
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.agents.implementations.orchestrator_agent import detect_intent


async def test():
    queries = [
        "我想请婚假",
        "婚假怎么申请",
        "我可以正常申请婚假，我需要怎么做",
        "婚假需要什么材料",
        "我已经结婚了，想申请婚假",
    ]
    
    print("测试婚假相关查询的意图识别\n")
    
    for query in queries:
        intent = await detect_intent(query, use_llm=True)
        print(f"查询: {query}")
        print(f"意图: {intent}")
        print("-" * 60)


if __name__ == "__main__":
    asyncio.run(test())
