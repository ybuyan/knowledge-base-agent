"""
测试 leave_guide skill 和 GuideAgent
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.skills.engine import SkillEngine


def test_leave_guide():
    """测试请假指引功能"""
    print("=" * 70)
    print("测试 leave_guide skill")
    print("=" * 70)
    
    engine = SkillEngine()
    
    # 检查 leave_guide 是否存在
    leave_guide = engine.get_skill("leave_guide")
    
    if leave_guide:
        print("\n✅ leave_guide skill 已加载")
        print(f"   名称: {leave_guide['display_name']}")
        print(f"   类型: {leave_guide.get('skill_type', 'qa')}")
        print(f"   描述: {leave_guide['description']}")
        
        # 检查 triggers
        triggers = leave_guide.get('triggers', [])
        if triggers:
            print(f"\n   触发词:")
            for trigger in triggers:
                print(f"     - {trigger}")
        
        # 检查 pipeline
        pipeline = leave_guide.get('pipeline', [])
        if pipeline:
            print(f"\n   Pipeline:")
            for step in pipeline:
                print(f"     - {step.get('step')}: {step.get('processor')}")
        else:
            print("\n   ⚠️  没有 pipeline")
    else:
        print("\n❌ leave_guide skill 未找到")
    
    print("\n" + "=" * 70)
    print("测试意图识别")
    print("=" * 70)
    
    test_queries = [
        ("我想请假", "guide"),
        ("怎么请假", "guide"),
        ("请假流程是什么", "guide"),
        ("如何申请假期", "guide"),
        ("年假有多少天", "qa"),
        ("上次你说的", "memory"),
    ]
    
    from app.agents.implementations.orchestrator_agent import detect_intent
    import asyncio
    
    async def test_intents():
        for query, expected in test_queries:
            intent = await detect_intent(query)
            status = "✅" if intent == expected else "❌"
            print(f"\n{status} 查询: {query}")
            print(f"   预期: {expected}, 实际: {intent}")
    
    asyncio.run(test_intents())
    
    print("\n" + "=" * 70)
    print("架构说明")
    print("=" * 70)
    print("""
工作流程：
1. 用户："我想请假"
2. Orchestrator: 检测到 "我想请假" 关键词 → 识别为 guide 意图
3. Orchestrator: 路由到 GuideAgent
4. GuideAgent: 匹配到 leave_guide skill (通过 triggers)
5. SkillEngine: 执行 leave_guide 的 pipeline
6. LLMGenerator: 使用 leave_guide prompt 模板
7. LLM: 通过多轮对话收集信息，生成流程指引
8. 返回：请假操作指引
    """)


if __name__ == "__main__":
    test_leave_guide()

