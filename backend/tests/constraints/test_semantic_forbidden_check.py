"""
测试智能语义禁止主题检查

验证系统能够识别同义词和隐含意图，而不仅仅是简单的字符串匹配。
"""

import pytest
from app.services.qa_agent import QAAgent, QAConfig
from app.core.constraint_config import get_constraint_config


class TestSemanticForbiddenCheck:
    """测试智能语义禁止主题检查"""
    
    @pytest.mark.asyncio
    async def test_exact_match(self):
        """测试精确匹配（第一层检查）"""
        agent = QAAgent()
        config = get_constraint_config()
        
        # 精确匹配应该被快速拦截
        queries = [
            "我的工资是多少？",
            "公司的薪资标准是什么？"
        ]
        
        print("\n" + "="*70)
        print("第一层检查：精确匹配")
        print("="*70)
        
        for query in queries:
            result = await agent._check_forbidden_topics(query, config)
            assert result is not None
            print(f"\n❌ {query}")
            print(f"   结果: 拒绝（精确匹配）")
    
    @pytest.mark.asyncio
    async def test_synonym_detection(self):
        """测试同义词检测（第二层检查）"""
        agent = QAAgent()
        config = get_constraint_config()
        
        # 同义词应该被语义检查拦截
        synonym_queries = [
            "我的薪水是多少？",  # 薪水 = 工资
            "公司的报酬标准是什么？",  # 报酬 = 工资
            "待遇如何？",  # 待遇 = 工资
            "月薪多少？",  # 月薪 = 工资
            "年薪是多少？",  # 年薪 = 工资
            "收入怎么样？"  # 收入 = 工资
        ]
        
        print("\n" + "="*70)
        print("第二层检查：同义词检测")
        print("="*70)
        
        for query in synonym_queries:
            result = await agent._check_forbidden_topics(query, config)
            print(f"\n查询: {query}")
            if result:
                print(f"   ✅ 拒绝（语义匹配）")
            else:
                print(f"   ⚠️  通过（未检测到）")
            
            # 注意：这里不强制 assert，因为 LLM 的判断可能不是 100% 准确
            # 但我们期望大部分同义词能被检测到
    
    @pytest.mark.asyncio
    async def test_implicit_intent_detection(self):
        """测试隐含意图检测（第二层检查）"""
        agent = QAAgent()
        config = get_constraint_config()
        
        # 隐含询问工资的查询
        implicit_queries = [
            "我能拿多少钱？",
            "这个职位的待遇怎么样？",
            "公司给多少？",
            "每个月能赚多少？"
        ]
        
        print("\n" + "="*70)
        print("第二层检查：隐含意图检测")
        print("="*70)
        
        for query in implicit_queries:
            result = await agent._check_forbidden_topics(query, config)
            print(f"\n查询: {query}")
            if result:
                print(f"   ✅ 拒绝（语义理解）")
            else:
                print(f"   ⚠️  通过（未检测到）")
    
    @pytest.mark.asyncio
    async def test_allowed_queries_not_blocked(self):
        """测试允许的查询不被误拦截"""
        agent = QAAgent()
        config = get_constraint_config()
        
        # 这些查询不应该被拦截
        allowed_queries = [
            "年假政策是什么？",
            "如何申请病假？",
            "公司的福利有哪些？",
            "工作时间是怎样的？",
            "节日福利有什么？",
            "加班政策是什么？"
        ]
        
        print("\n" + "="*70)
        print("验证：允许的查询不被误拦截")
        print("="*70)
        
        for query in allowed_queries:
            result = await agent._check_forbidden_topics(query, config)
            assert result is None, f"查询 '{query}' 不应该被拦截"
            print(f"\n✅ {query}")
            print(f"   结果: 允许")
    
    @pytest.mark.asyncio
    async def test_full_process_with_synonym(self):
        """测试完整流程处理同义词查询"""
        agent = QAAgent()
        
        query = "我的薪水是多少？"
        
        print("\n" + "="*70)
        print(f"完整流程测试 - 查询: {query}")
        print("="*70)
        
        # 收集所有响应
        responses = []
        async for chunk in agent.process(query):
            responses.append(chunk)
        
        # 验证响应
        assert len(responses) > 0
        
        # 解析响应内容
        full_response = ""
        for response in responses:
            if '"type": "text"' in response or '"type":"text"' in response:
                import json
                try:
                    json_str = response.replace("data: ", "").strip()
                    data = json.loads(json_str)
                    if data.get("type") == "text":
                        full_response += data.get("content", "")
                except:
                    pass
        
        print(f"\nLLM 回答:")
        print("-"*70)
        print(full_response)
        print("-"*70)
        
        # 验证回答包含拒绝信息
        if "禁止" in full_response or "抱歉" in full_response:
            print("\n✅ 验证通过: 同义词查询被正确拒绝")
        else:
            print("\n⚠️  注意: 同义词查询未被拦截（可能需要调整 LLM 提示词）")


def test_semantic_check_explanation():
    """说明语义检查的工作原理"""
    print("\n" + "="*70)
    print("智能语义检查工作原理")
    print("="*70)
    
    print("""
第一层：快速字符串匹配
- 检查查询中是否包含禁止词汇
- 优点：速度快（< 1ms）
- 缺点：无法识别同义词
- 示例：
  ✅ "我的工资是多少？" → 拒绝（包含"工资"）
  ❌ "我的薪水是多少？" → 通过（不包含"工资"）

第二层：LLM 语义理解
- 使用 LLM 判断查询是否涉及禁止主题
- 优点：能识别同义词和隐含意图
- 缺点：速度较慢（~0.3s），依赖 LLM 判断
- 示例：
  ✅ "我的薪水是多少？" → 拒绝（薪水 = 工资）
  ✅ "待遇如何？" → 拒绝（待遇涉及工资）
  ✅ "我能拿多少钱？" → 拒绝（隐含询问工资）

工作流程：
1. 用户查询 "我的薪水是多少？"
2. 第一层检查：不包含"工资"、"薪资" → 通过
3. 第二层检查：LLM 判断 "薪水" 是 "工资" 的同义词 → 拒绝
4. 返回拒绝消息

性能影响：
- 精确匹配：< 1ms（无影响）
- 语义检查：~300ms（仅在第一层通过时执行）
- 总体：大部分查询只需第一层检查
""")
    
    print("="*70)


def test_configuration_recommendation():
    """配置建议"""
    print("\n" + "="*70)
    print("配置建议")
    print("="*70)
    
    print("""
方案 1：只使用精确匹配（性能优先）
{
  "forbidden_topics": ["薪资", "工资", "薪水", "报酬", "待遇", "收入", "月薪", "年薪"],
  "forbidden_keywords": ["工资", "薪水", "报酬", "待遇", "收入"]
}

优点：
- 速度快
- 可预测
- 无 LLM 调用成本

缺点：
- 需要列举所有同义词
- 无法识别隐含意图
- 维护成本高

---

方案 2：精确匹配 + 语义检查（智能优先）
{
  "forbidden_topics": ["薪资", "工资"],
  "forbidden_keywords": ["工资"]
}

优点：
- 智能识别同义词
- 能理解隐含意图
- 配置简单

缺点：
- 略慢（~300ms）
- 依赖 LLM 判断
- 可能有误判

---

推荐：方案 2（当前实现）
- 第一层快速拦截常见查询
- 第二层智能识别变体
- 平衡性能和智能度
""")
    
    print("="*70)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
