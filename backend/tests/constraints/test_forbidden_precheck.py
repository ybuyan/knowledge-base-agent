"""
测试禁止主题预检查功能

验证在查询处理的最开始就检查并拒绝禁止主题。
"""

import pytest
from app.services.qa_agent import QAAgent, QAConfig
from app.core.constraint_config import get_constraint_config


class TestForbiddenPrecheck:
    """测试禁止主题预检查"""
    
    def test_check_forbidden_topics_method(self):
        """测试 _check_forbidden_topics 方法"""
        agent = QAAgent()
        config = get_constraint_config()
        
        # 测试包含禁止主题的查询
        query1 = "我的工资是多少？"
        result1 = agent._check_forbidden_topics(query1, config)
        
        assert result1 is not None
        assert "工资" in result1
        assert "禁止" in result1
        
        print(f"\n查询: {query1}")
        print(f"结果: {result1}")
        
        # 测试包含禁止主题的查询（薪资）
        query2 = "公司的薪资标准是什么？"
        result2 = agent._check_forbidden_topics(query2, config)
        
        assert result2 is not None
        assert "薪资" in result2
        assert "禁止" in result2
        
        print(f"\n查询: {query2}")
        print(f"结果: {result2}")
        
        # 测试不包含禁止主题的查询
        query3 = "年假政策是什么？"
        result3 = agent._check_forbidden_topics(query3, config)
        
        assert result3 is None
        
        print(f"\n查询: {query3}")
        print(f"结果: 允许（None）")
    
    def test_build_forbidden_message(self):
        """测试拒绝消息构建"""
        agent = QAAgent()
        
        # 测试主题类型
        message1 = agent._build_forbidden_message("工资", "主题")
        
        assert "工资" in message1
        assert "主题" in message1
        assert "禁止" in message1
        assert "抱歉" in message1
        
        print("\n" + "="*70)
        print("拒绝消息示例（主题）:")
        print("="*70)
        print(message1)
        print("="*70)
        
        # 测试关键词类型
        message2 = agent._build_forbidden_message("薪水", "关键词")
        
        assert "薪水" in message2
        assert "关键词" in message2
        
        print("\n" + "="*70)
        print("拒绝消息示例（关键词）:")
        print("="*70)
        print(message2)
        print("="*70)
    
    def test_various_salary_queries(self):
        """测试各种工资相关查询"""
        agent = QAAgent()
        config = get_constraint_config()
        
        salary_queries = [
            "我的工资是多少？",
            "公司的薪资标准是什么？",
            "工资什么时候发？",
            "薪资待遇如何？",
            "请问工资多少？",
            "能告诉我薪资吗？"
        ]
        
        print("\n" + "="*70)
        print("各种工资相关查询的预检查结果:")
        print("="*70)
        
        for query in salary_queries:
            result = agent._check_forbidden_topics(query, config)
            status = "❌ 拒绝" if result else "✅ 允许"
            print(f"\n{status} | {query}")
            if result:
                print(f"     拒绝原因: 包含禁止主题/关键词")
        
        # 验证所有工资查询都被拒绝
        for query in salary_queries:
            result = agent._check_forbidden_topics(query, config)
            assert result is not None, f"查询 '{query}' 应该被拒绝"
    
    def test_allowed_queries(self):
        """测试允许的查询"""
        agent = QAAgent()
        config = get_constraint_config()
        
        allowed_queries = [
            "年假政策是什么？",
            "如何申请病假？",
            "公司的福利有哪些？",
            "工作时间是怎样的？",
            "节日福利有什么？"
        ]
        
        print("\n" + "="*70)
        print("允许的查询预检查结果:")
        print("="*70)
        
        for query in allowed_queries:
            result = agent._check_forbidden_topics(query, config)
            status = "❌ 拒绝" if result else "✅ 允许"
            print(f"\n{status} | {query}")
        
        # 验证所有允许的查询都通过
        for query in allowed_queries:
            result = agent._check_forbidden_topics(query, config)
            assert result is None, f"查询 '{query}' 应该被允许"
    
    @pytest.mark.asyncio
    async def test_process_with_forbidden_query(self):
        """测试 process 方法处理禁止查询"""
        agent = QAAgent()
        
        query = "我的工资是多少？"
        
        print("\n" + "="*70)
        print(f"测试完整流程 - 查询: {query}")
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
                # 提取 content
                import json
                try:
                    # 移除 "data: " 前缀
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
        assert "工资" in full_response or "薪资" in full_response
        assert "禁止" in full_response or "抱歉" in full_response
        
        # 验证不是 fallback 消息
        assert "知识库中没有找到" not in full_response
        
        print("\n✅ 验证通过: 查询被正确拒绝，不是 fallback 消息")


def test_configuration_check():
    """检查配置是否正确"""
    config = get_constraint_config()
    
    print("\n" + "="*70)
    print("当前约束配置:")
    print("="*70)
    
    forbidden_topics = config.generation.get('forbidden_topics', [])
    forbidden_keywords = config.generation.get('forbidden_keywords', [])
    
    print(f"\n禁止主题: {forbidden_topics}")
    print(f"禁止关键词: {forbidden_keywords}")
    
    assert len(forbidden_topics) > 0, "应该配置禁止主题"
    assert '工资' in forbidden_topics or '薪资' in forbidden_topics
    
    print("\n✅ 配置检查通过")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
