"""
测试禁止主题功能 - 工资查询场景

验证当用户询问工资相关问题时，系统是否正确拒绝回答。
"""

import pytest
from app.prompts.strict_qa import ConstraintPromptBuilder
from app.core.constraint_config import get_constraint_config


class TestForbiddenSalaryQuery:
    """测试禁止工资查询场景"""
    
    def test_salary_query_prompt_contains_forbidden_topics(self):
        """测试工资查询时 Prompt 包含禁止主题说明"""
        # 获取实际配置
        config = get_constraint_config()
        
        # 模拟知识库上下文
        context = """
        公司福利制度：
        1. 年假：入职满一年享有5天年假
        2. 病假：每年10天带薪病假
        3. 节日福利：春节、中秋等节日发放礼品
        """
        
        # 构建约束
        constraints = {
            'generation': config.generation
        }
        
        # 构建系统提示词
        system_prompt = ConstraintPromptBuilder.build_system_prompt(
            context,
            constraints
        )
        
        # 验证禁止主题说明在 Prompt 中
        assert "禁止回答的主题" in system_prompt
        assert "薪资" in system_prompt or "工资" in system_prompt
        
        print("\n" + "="*70)
        print("系统提示词内容（部分）:")
        print("="*70)
        
        # 提取禁止主题部分
        if "禁止回答的主题" in system_prompt:
            lines = system_prompt.split('\n')
            for i, line in enumerate(lines):
                if "禁止回答的主题" in line:
                    # 打印禁止主题部分
                    for j in range(i, min(i+3, len(lines))):
                        print(lines[j])
                    break
        
        print("="*70)
    
    def test_salary_query_full_prompt(self):
        """测试完整的工资查询场景 Prompt"""
        config = get_constraint_config()
        
        context = """
        员工手册摘要：
        - 工作时间：周一至周五 9:00-18:00
        - 年假政策：入职满一年5天，满三年10天
        - 加班政策：需提前申请，可调休或补贴
        """
        
        constraints = {
            'generation': config.generation
        }
        
        system_prompt = ConstraintPromptBuilder.build_system_prompt(
            context,
            constraints
        )
        
        # 模拟用户查询
        user_query = "我的工资是多少？"
        
        # 构建完整消息
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_query}
        ]
        
        print("\n" + "="*70)
        print("完整对话场景:")
        print("="*70)
        print(f"\n用户查询: {user_query}")
        print("\n系统提示词中的关键约束:")
        print("-"*70)
        
        # 提取关键约束部分
        if "严格模式" in system_prompt:
            print("✅ 严格模式: 已启用")
        
        if "知识来源限制" in system_prompt:
            print("✅ 知识来源限制: 只使用知识库内容")
        
        if "引用要求" in system_prompt:
            print("✅ 引用要求: 必须标注信息来源")
        
        if "禁止回答的主题" in system_prompt:
            print("✅ 禁止主题: 薪资、工资")
        
        if "禁止使用的关键词" in system_prompt:
            print("✅ 禁止关键词: 工资")
        
        print("\n预期 LLM 回答:")
        print("-"*70)
        print("抱歉，关于薪资/工资相关的问题属于禁止回答的主题。")
        print("如有疑问，请联系人力资源部门。")
        print("="*70)
        
        # 验证
        assert len(messages) == 2
        assert messages[0]['role'] == 'system'
        assert messages[1]['role'] == 'user'
        assert "禁止" in messages[0]['content']
    
    def test_different_salary_queries(self):
        """测试不同的工资相关查询"""
        config = get_constraint_config()
        context = "公司政策文档"
        
        constraints = {
            'generation': config.generation
        }
        
        system_prompt = ConstraintPromptBuilder.build_system_prompt(
            context,
            constraints
        )
        
        # 各种工资相关查询
        salary_queries = [
            "我的工资是多少？",
            "公司的薪资标准是什么？",
            "工资什么时候发？",
            "薪资待遇如何？",
            "月薪多少？",
            "年薪是多少？",
            "奖金怎么算？"
        ]
        
        print("\n" + "="*70)
        print("各种工资相关查询的处理:")
        print("="*70)
        
        for query in salary_queries:
            print(f"\n查询: {query}")
            print(f"预期: ❌ 拒绝回答（禁止主题）")
        
        print("\n" + "="*70)
        print("允许的查询示例:")
        print("="*70)
        
        allowed_queries = [
            "年假政策是什么？",
            "如何申请病假？",
            "公司的福利有哪些？",
            "工作时间是怎样的？"
        ]
        
        for query in allowed_queries:
            print(f"\n查询: {query}")
            print(f"预期: ✅ 正常回答（基于知识库）")
        
        print("="*70)
    
    def test_configuration_values(self):
        """测试配置值是否正确"""
        config = get_constraint_config()
        
        print("\n" + "="*70)
        print("当前约束配置:")
        print("="*70)
        
        print(f"\n【生成约束】")
        print(f"  strict_mode: {config.generation.get('strict_mode')}")
        print(f"  allow_general_knowledge: {config.generation.get('allow_general_knowledge')}")
        print(f"  require_citations: {config.generation.get('require_citations')}")
        print(f"  max_answer_length: {config.generation.get('max_answer_length')}")
        print(f"  forbidden_topics: {config.generation.get('forbidden_topics')}")
        print(f"  forbidden_keywords: {config.generation.get('forbidden_keywords')}")
        
        print(f"\n【验证约束】")
        print(f"  enabled: {config.validation.get('enabled')}")
        print(f"  min_confidence_score: {config.validation.get('min_confidence_score')}")
        
        print("="*70)
        
        # 验证禁止主题配置
        forbidden_topics = config.generation.get('forbidden_topics', [])
        assert '薪资' in forbidden_topics or '工资' in forbidden_topics
        
        # 验证禁止关键词配置
        forbidden_keywords = config.generation.get('forbidden_keywords', [])
        assert '工资' in forbidden_keywords


def test_manual_verification_guide():
    """手动验证指南"""
    print("\n" + "="*70)
    print("手动验证指南")
    print("="*70)
    
    print("\n【步骤 1】启动后端服务")
    print("  cd backend")
    print("  python -m uvicorn app.main:app --reload")
    
    print("\n【步骤 2】发送测试请求")
    print("  方法 1: 使用前端界面")
    print("    - 打开浏览器访问前端")
    print("    - 输入: '我的工资是多少？'")
    print("    - 观察回答")
    
    print("\n  方法 2: 使用 curl 命令")
    print('  curl -X POST http://localhost:8000/api/chat/stream \\')
    print('    -H "Content-Type: application/json" \\')
    print('    -d \'{"message": "我的工资是多少？", "session_id": "test"}\'')
    
    print("\n【步骤 3】预期结果")
    print("  ✅ LLM 应该拒绝回答")
    print("  ✅ 回答中应该说明该主题被禁止")
    print("  ✅ 可能建议联系相关部门")
    
    print("\n【步骤 4】对比测试")
    print("  允许的查询: '年假政策是什么？'")
    print("  ✅ 应该正常回答（基于知识库）")
    print("  ✅ 回答中应该包含引用标记 [1]、[2]")
    
    print("\n【步骤 5】检查日志")
    print("  查看后端日志，确认:")
    print("  - 使用了 ConstraintPromptBuilder")
    print("  - 约束配置被正确加载")
    print("  - 答案验证被执行")
    
    print("="*70)


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "-s"])
    
    # 显示手动验证指南
    test_manual_verification_guide()
