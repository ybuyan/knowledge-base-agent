"""
调试语义检查功能
"""

import pytest
import asyncio
from app.services.qa_agent import QAAgent
from app.core.constraint_config import get_constraint_config


@pytest.mark.asyncio
async def test_semantic_check_directly():
    """直接测试语义检查方法"""
    agent = QAAgent()
    
    forbidden_topics = ["薪资", "工资"]
    query = "我的薪水是多少？"
    
    print(f"\n测试查询: {query}")
    print(f"禁止主题: {forbidden_topics}")
    
    result = await agent._check_forbidden_topics_semantic(query, forbidden_topics)
    
    print(f"\n语义检查结果: {result}")
    
    if result:
        print("✅ 语义检查成功识别")
    else:
        print("❌ 语义检查未识别")


@pytest.mark.asyncio
async def test_full_check():
    """测试完整检查流程"""
    agent = QAAgent()
    config = get_constraint_config()
    
    queries = [
        ("我的工资是多少？", "应该被第一层拦截"),
        ("我的薪水是多少？", "应该被第二层拦截"),
        ("年假政策是什么？", "应该通过")
    ]
    
    print("\n" + "="*70)
    print("完整检查流程测试")
    print("="*70)
    
    for query, expected in queries:
        print(f"\n查询: {query}")
        print(f"预期: {expected}")
        
        result = await agent._check_forbidden_topics(query, config)
        
        if result:
            print(f"结果: ❌ 拒绝")
            print(f"消息: {result[:100]}...")
        else:
            print(f"结果: ✅ 通过")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
