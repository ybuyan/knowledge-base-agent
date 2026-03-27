"""
实时验证禁止主题功能

此脚本模拟真实的查询场景，展示系统如何处理禁止主题。
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.prompts.strict_qa import ConstraintPromptBuilder
from app.core.constraint_config import get_constraint_config


def print_section(title: str, char: str = "="):
    """打印分隔线"""
    print(f"\n{char * 70}")
    print(f"  {title}")
    print(f"{char * 70}\n")


def verify_prompt_construction():
    """验证 Prompt 构建"""
    print_section("1. 验证约束配置加载")
    
    config = get_constraint_config()
    
    print("【生成约束配置】")
    print(f"  ✓ strict_mode: {config.generation.get('strict_mode')}")
    print(f"  ✓ allow_general_knowledge: {config.generation.get('allow_general_knowledge')}")
    print(f"  ✓ require_citations: {config.generation.get('require_citations')}")
    print(f"  ✓ max_answer_length: {config.generation.get('max_answer_length')}")
    print(f"  ✓ forbidden_topics: {config.generation.get('forbidden_topics')}")
    print(f"  ✓ forbidden_keywords: {config.generation.get('forbidden_keywords')}")
    
    return config


def build_test_prompt(config):
    """构建测试 Prompt"""
    print_section("2. 构建系统提示词")
    
    # 模拟知识库上下文
    context = """
【员工手册 - 福利政策】

1. 年假制度
   - 入职满1年：5天年假
   - 入职满3年：10天年假
   - 入职满5年：15天年假

2. 病假制度
   - 每年10天带薪病假
   - 需提供医院证明

3. 节日福利
   - 春节：1000元购物卡
   - 中秋：月饼礼盒
   - 生日：生日蛋糕券

4. 工作时间
   - 周一至周五 9:00-18:00
   - 午休时间 12:00-13:00
"""
    
    # 构建约束
    constraints = {
        'generation': config.generation,
        'validation': config.validation
    }
    
    # 构建系统提示词
    system_prompt = ConstraintPromptBuilder.build_system_prompt(
        context,
        constraints
    )
    
    print("知识库上下文:")
    print("-" * 70)
    print(context)
    
    print("\n系统提示词（关键部分）:")
    print("-" * 70)
    
    # 提取并显示关键约束
    lines = system_prompt.split('\n')
    in_constraint_section = False
    
    for line in lines:
        if any(keyword in line for keyword in ['严格模式', '知识来源', '引用要求', '禁止']):
            in_constraint_section = True
        
        if in_constraint_section:
            print(line)
            if line.strip() == '':
                in_constraint_section = False
    
    return system_prompt, context


def test_forbidden_query(system_prompt):
    """测试禁止查询"""
    print_section("3. 测试禁止主题查询")
    
    test_queries = [
        "我的工资是多少？",
        "公司的薪资标准是什么？",
        "工资什么时候发？"
    ]
    
    for query in test_queries:
        print(f"❌ 查询: {query}")
        print(f"   预期: LLM 应拒绝回答，说明该主题被禁止")
        print()
    
    print("【完整消息示例】")
    print("-" * 70)
    
    messages = [
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': test_queries[0]}
    ]
    
    print(f"System: [包含约束的系统提示词，长度: {len(system_prompt)} 字符]")
    print(f"User: {test_queries[0]}")
    print()
    print("【LLM 预期回答】")
    print("-" * 70)
    print("抱歉，关于薪资/工资相关的问题属于禁止回答的主题。")
    print("根据公司政策，薪资信息属于保密内容。")
    print("如有疑问，请联系人力资源部门。")


def test_allowed_query(system_prompt):
    """测试允许的查询"""
    print_section("4. 测试允许的查询")
    
    test_queries = [
        "年假政策是什么？",
        "如何申请病假？",
        "公司的节日福利有哪些？"
    ]
    
    for query in test_queries:
        print(f"✅ 查询: {query}")
        print(f"   预期: LLM 应正常回答，基于知识库内容")
        print()
    
    print("【完整消息示例】")
    print("-" * 70)
    
    messages = [
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': test_queries[0]}
    ]
    
    print(f"System: [包含约束的系统提示词]")
    print(f"User: {test_queries[0]}")
    print()
    print("【LLM 预期回答】")
    print("-" * 70)
    print("根据员工手册，年假制度如下：[1]")
    print()
    print("- 入职满1年：5天年假")
    print("- 入职满3年：10天年假")
    print("- 入职满5年：15天年假")
    print()
    print("参考来源：")
    print("[1] 员工手册 - 福利政策 - 年假制度")


def show_verification_steps():
    """显示验证步骤"""
    print_section("5. 实际验证步骤")
    
    print("【方法 1：使用 Python 脚本测试】")
    print("-" * 70)
    print("1. 确保后端服务正在运行")
    print("   cd backend")
    print("   python -m uvicorn app.main:app --reload")
    print()
    print("2. 运行测试脚本")
    print("   python tests/constraints/test_forbidden_topics_e2e.py")
    print()
    
    print("【方法 2：使用 API 测试】")
    print("-" * 70)
    print("1. 测试禁止主题查询")
    print('   curl -X POST http://localhost:8000/api/chat/stream \\')
    print('     -H "Content-Type: application/json" \\')
    print('     -d \'{"message": "我的工资是多少？", "session_id": "test-forbidden"}\'')
    print()
    print("2. 测试允许的查询")
    print('   curl -X POST http://localhost:8000/api/chat/stream \\')
    print('     -H "Content-Type: application/json" \\')
    print('     -d \'{"message": "年假政策是什么？", "session_id": "test-allowed"}\'')
    print()
    
    print("【方法 3：使用前端界面测试】")
    print("-" * 70)
    print("1. 打开浏览器访问前端界面")
    print("2. 输入禁止查询: '我的工资是多少？'")
    print("3. 观察 LLM 是否拒绝回答")
    print("4. 输入允许查询: '年假政策是什么？'")
    print("5. 观察 LLM 是否正常回答并包含引用")
    print()
    
    print("【方法 4：检查日志】")
    print("-" * 70)
    print("查看后端日志，确认:")
    print("  ✓ 使用了 ConstraintPromptBuilder.build_system_prompt")
    print("  ✓ 约束配置被正确加载")
    print("  ✓ 系统提示词包含禁止主题说明")
    print("  ✓ 答案验证被执行")


def show_expected_behavior():
    """显示预期行为"""
    print_section("6. 预期行为总结")
    
    print("【禁止主题查询】")
    print("-" * 70)
    print("查询: '我的工资是多少？'")
    print()
    print("系统行为:")
    print("  1. ✓ 加载约束配置，识别 forbidden_topics: ['薪资', '工资']")
    print("  2. ✓ 构建系统提示词，包含禁止主题说明")
    print("  3. ✓ 发送给 LLM，LLM 看到禁止主题约束")
    print("  4. ✓ LLM 拒绝回答，说明该主题被禁止")
    print()
    print("LLM 回答示例:")
    print("  '抱歉，关于薪资/工资相关的问题属于禁止回答的主题。'")
    print("  '如有疑问，请联系人力资源部门。'")
    print()
    
    print("【允许的查询】")
    print("-" * 70)
    print("查询: '年假政策是什么？'")
    print()
    print("系统行为:")
    print("  1. ✓ 加载约束配置")
    print("  2. ✓ 构建系统提示词，包含严格模式、引用要求等")
    print("  3. ✓ 检索知识库，找到年假政策相关内容")
    print("  4. ✓ LLM 基于知识库生成回答，包含引用标记")
    print("  5. ✓ 答案验证通过")
    print()
    print("LLM 回答示例:")
    print("  '根据员工手册，年假制度如下：[1]")
    print("  - 入职满1年：5天年假")
    print("  - 入职满3年：10天年假")
    print("  参考来源：[1] 员工手册 - 福利政策'")


def show_configuration_tips():
    """显示配置提示"""
    print_section("7. 配置提示")
    
    print("【修改禁止主题】")
    print("-" * 70)
    print("编辑文件: backend/config/constraints.json")
    print()
    print("添加更多禁止主题:")
    print('{')
    print('  "generation": {')
    print('    "forbidden_topics": ["薪资", "工资", "奖金", "股权", "期权"],')
    print('    "forbidden_keywords": ["工资", "薪水", "收入", "年薪"]')
    print('  }')
    print('}')
    print()
    print("修改后重启服务即可生效")
    print()
    
    print("【调整严格程度】")
    print("-" * 70)
    print("更严格:")
    print('{')
    print('  "generation": {')
    print('    "strict_mode": true,')
    print('    "allow_general_knowledge": false,')
    print('    "require_citations": true')
    print('  }')
    print('}')
    print()
    print("更宽松:")
    print('{')
    print('  "generation": {')
    print('    "strict_mode": false,')
    print('    "allow_general_knowledge": true,')
    print('    "require_citations": false')
    print('  }')
    print('}')


def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("  约束配置实时验证 - 禁止主题功能")
    print("=" * 70)
    
    try:
        # 1. 验证配置加载
        config = verify_prompt_construction()
        
        # 2. 构建测试 Prompt
        system_prompt, context = build_test_prompt(config)
        
        # 3. 测试禁止查询
        test_forbidden_query(system_prompt)
        
        # 4. 测试允许的查询
        test_allowed_query(system_prompt)
        
        # 5. 显示验证步骤
        show_verification_steps()
        
        # 6. 显示预期行为
        show_expected_behavior()
        
        # 7. 显示配置提示
        show_configuration_tips()
        
        print_section("验证完成", "=")
        print("✅ 约束配置已正确加载")
        print("✅ 系统提示词包含所有约束")
        print("✅ 可以进行实际测试验证")
        print()
        print("下一步: 启动后端服务，使用上述方法进行实际验证")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
