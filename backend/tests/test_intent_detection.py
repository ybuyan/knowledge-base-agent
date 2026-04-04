"""
测试意图识别 - LLM vs 关键词
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

from app.agents.implementations.orchestrator_agent import detect_intent


async def test_intent_detection():
    """测试意图识别"""
    print("=" * 80)
    print("意图识别测试 - LLM 方法")
    print("=" * 80)
    
    test_cases = [
        # guide 意图
        ("我想请假", "guide"),
        ("怎么请假", "guide"),
        ("请假流程是什么", "guide"),
        ("请假申请怎么写", "guide"),
        ("如何申请年假", "guide"),
        ("办理请假需要什么材料", "guide"),
        ("请假步骤", "guide"),
        
        # qa 意图
        ("年假有多少天", "qa"),
        ("报销政策是什么", "qa"),
        ("公司地址在哪里", "qa"),
        
        # memory 意图
        ("上次你说的", "memory"),
        ("之前提到的", "memory"),
        ("刚才说的是什么", "memory"),
        
        # hybrid 意图
        ("和之前的政策有什么区别", "hybrid"),
        ("对比一下", "hybrid"),
    ]
    
    print("\n使用 LLM 进行意图识别:\n")
    
    correct = 0
    total = len(test_cases)
    
    for query, expected in test_cases:
        intent = await detect_intent(query, use_llm=True)
        status = "✅" if intent == expected else "❌"
        
        if intent == expected:
            correct += 1
        
        print(f"{status} 查询: {query:30s} | 预期: {expected:8s} | 实际: {intent:8s}")
    
    print(f"\n准确率: {correct}/{total} ({correct/total*100:.1f}%)")
    
    print("\n" + "=" * 80)
    print("对比：关键词方法")
    print("=" * 80)
    
    print("\n使用关键词进行意图识别:\n")
    
    correct_kw = 0
    
    for query, expected in test_cases:
        intent = await detect_intent(query, use_llm=False)
        status = "✅" if intent == expected else "❌"
        
        if intent == expected:
            correct_kw += 1
        
        print(f"{status} 查询: {query:30s} | 预期: {expected:8s} | 实际: {intent:8s}")
    
    print(f"\n准确率: {correct_kw}/{total} ({correct_kw/total*100:.1f}%)")
    
    print("\n" + "=" * 80)
    print("总结")
    print("=" * 80)
    print(f"LLM 方法准确率: {correct/total*100:.1f}%")
    print(f"关键词方法准确率: {correct_kw/total*100:.1f}%")
    print(f"提升: {(correct-correct_kw)/total*100:+.1f}%")


if __name__ == "__main__":
    asyncio.run(test_intent_detection())
