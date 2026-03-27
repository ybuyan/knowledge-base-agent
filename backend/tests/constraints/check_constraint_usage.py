#!/usr/bin/env python3
"""
检查约束配置是否真正应用到项目中

这个脚本会检查约束配置在各个模块中的使用情况
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.core.constraint_config import get_constraint_config
from app.prompts.strict_qa import StrictQAPrompt, ConstraintPromptBuilder


def print_section(title: str):
    """打印分节标题"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def check_config_loading():
    """检查配置加载"""
    print_section("1. 检查配置加载")
    
    config = get_constraint_config()
    
    print("✅ 配置加载成功")
    print(f"\n当前配置:")
    print(f"  禁止主题: {config.generation.get('forbidden_topics')}")
    print(f"  禁止关键词: {config.generation.get('forbidden_keywords')}")
    print(f"  严格模式: {config.generation.get('strict_mode')}")
    print(f"  最小相似度: {config.retrieval.get('min_similarity_score')}")
    
    return True


def check_prompt_building():
    """检查 Prompt 构建"""
    print_section("2. 检查 Prompt 构建")
    
    config = get_constraint_config()
    context = "这是知识库内容"
    query = "公司的工资标准是什么？"
    
    # 方法 1: StrictQAPrompt.build_messages (QA Agent 使用的方法)
    print("方法 1: StrictQAPrompt.build_messages (QA Agent 当前使用)")
    messages1 = StrictQAPrompt.build_messages(context, query)
    system_prompt1 = messages1[0]['content']
    
    print(f"  系统提示词长度: {len(system_prompt1)} 字符")
    
    # 检查是否包含禁止主题
    forbidden_topics = config.generation.get('forbidden_topics', [])
    contains_forbidden = any(topic in system_prompt1 for topic in forbidden_topics)
    
    if contains_forbidden:
        print(f"  ✅ 包含禁止主题说明")
    else:
        print(f"  ❌ 不包含禁止主题说明")
        print(f"  ⚠️  这意味着约束配置没有被应用！")
    
    # 方法 2: ConstraintPromptBuilder.build_system_prompt (应该使用的方法)
    print("\n方法 2: ConstraintPromptBuilder.build_system_prompt (应该使用)")
    constraints = {"generation": config.generation}
    system_prompt2 = ConstraintPromptBuilder.build_system_prompt(context, constraints)
    
    print(f"  系统提示词长度: {len(system_prompt2)} 字符")
    
    contains_forbidden2 = any(topic in system_prompt2 for topic in forbidden_topics)
    
    if contains_forbidden2:
        print(f"  ✅ 包含禁止主题说明")
        print(f"  禁止主题: {forbidden_topics}")
    else:
        print(f"  ❌ 不包含禁止主题说明")
    
    # 对比
    print(f"\n对比:")
    print(f"  方法 1 长度: {len(system_prompt1)}")
    print(f"  方法 2 长度: {len(system_prompt2)}")
    print(f"  差异: {len(system_prompt2) - len(system_prompt1)} 字符")
    
    if len(system_prompt2) > len(system_prompt1):
        print(f"  ⚠️  方法 2 包含更多约束信息")
    
    return contains_forbidden


def check_qa_agent_usage():
    """检查 QA Agent 中的使用"""
    print_section("3. 检查 QA Agent 中的使用")
    
    # 读取 qa_agent.py 文件
    qa_agent_file = project_root / "app" / "services" / "qa_agent.py"
    
    with open(qa_agent_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否导入了约束配置
    if "from app.core.constraint_config import get_constraint_config" in content:
        print("✅ 导入了 constraint_config")
    else:
        print("❌ 未导入 constraint_config")
    
    # 检查是否使用了 ConstraintPromptBuilder
    if "ConstraintPromptBuilder" in content:
        print("✅ 使用了 ConstraintPromptBuilder")
    else:
        print("❌ 未使用 ConstraintPromptBuilder")
        print("   当前使用: StrictQAPrompt.build_messages")
    
    # 检查在哪里使用了约束配置
    if "constraint_config = get_constraint_config()" in content:
        print("✅ 获取了约束配置实例")
        
        # 检查使用位置
        uses = []
        if "retrieval_config = constraint_config.retrieval" in content:
            uses.append("检索配置")
        if "suggest_config = get_constraint_config().suggest_questions" in content:
            uses.append("建议问题配置")
        
        if uses:
            print(f"   使用位置: {', '.join(uses)}")
        else:
            print("   ⚠️  获取了配置但可能未充分使用")
    else:
        print("❌ 未获取约束配置实例")
    
    # 关键检查：在生成回答时是否使用了约束
    if "StrictQAPrompt.build_messages(rag_context.context_text, query, history)" in content:
        print("\n⚠️  关键问题发现:")
        print("   在 _execute_rag_flow 中使用了 StrictQAPrompt.build_messages")
        print("   这个方法不会自动应用约束配置中的禁止主题和关键词！")
        print("   需要改为使用 ConstraintPromptBuilder.build_system_prompt")
        return False
    
    return True


def check_answer_validator_usage():
    """检查答案验证器的使用"""
    print_section("4. 检查答案验证器的使用")
    
    qa_agent_file = project_root / "app" / "services" / "qa_agent.py"
    
    with open(qa_agent_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否使用了验证器
    if "validator = get_answer_validator()" in content:
        print("✅ 创建了答案验证器实例")
    else:
        print("❌ 未创建答案验证器实例")
        return False
    
    # 检查是否使用了检索验证
    if "validator.validate_retrieval" in content:
        print("✅ 使用了检索验证 (validate_retrieval)")
        print("   这会根据约束配置过滤低相似度文档")
    else:
        print("❌ 未使用检索验证")
    
    # 检查是否使用了答案验证
    if "validator.validate_answer" in content:
        print("✅ 使用了答案验证 (validate_answer)")
    else:
        print("⚠️  未使用答案验证 (validate_answer)")
        print("   建议在生成回答后验证答案质量")
    
    return True


def check_chat_api_usage():
    """检查 Chat API 中的使用"""
    print_section("5. 检查 Chat API 中的使用")
    
    chat_file = project_root / "app" / "api" / "routes" / "chat.py"
    
    with open(chat_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否导入了约束配置
    if "from app.core.constraint_config import get_constraint_config" in content:
        print("✅ 导入了 constraint_config")
    else:
        print("❌ 未导入 constraint_config")
    
    # 检查是否有禁止主题的预检查
    if "forbidden" in content.lower() and "check" in content.lower():
        print("✅ 可能有禁止主题的预检查")
    else:
        print("❌ 没有禁止主题的预检查")
        print("   建议添加预检查，在调用 LLM 前拒绝禁止主题")
    
    return True


def generate_recommendations():
    """生成改进建议"""
    print_section("改进建议")
    
    print("基于检查结果，以下是改进建议：\n")
    
    print("1. 修改 QA Agent 的 Prompt 构建")
    print("   当前: StrictQAPrompt.build_messages(context, query, history)")
    print("   改为: 使用 ConstraintPromptBuilder 并传入约束配置")
    print()
    print("   示例代码:")
    print("   ```python")
    print("   # 在 _execute_rag_flow 方法中")
    print("   constraint_config = get_constraint_config()")
    print("   constraints = {")
    print("       'generation': constraint_config.generation,")
    print("       'validation': constraint_config.validation")
    print("   }")
    print("   ")
    print("   # 构建系统提示词")
    print("   system_prompt = ConstraintPromptBuilder.build_system_prompt(")
    print("       rag_context.context_text,")
    print("       constraints")
    print("   )")
    print("   ")
    print("   # 构建消息列表")
    print("   messages = [{'role': 'system', 'content': system_prompt}]")
    print("   if history:")
    print("       messages.extend(history)")
    print("   messages.append({'role': 'user', 'content': query})")
    print("   ```")
    print()
    
    print("2. 添加禁止主题的预检查")
    print("   在 Chat API 或 QA Agent 的 process 方法开始处添加:")
    print("   ```python")
    print("   def check_forbidden_topics(query: str, config) -> tuple:")
    print("       forbidden_topics = config.generation.get('forbidden_topics', [])")
    print("       for topic in forbidden_topics:")
    print("           if topic in query:")
    print("               return True, topic")
    print("       return False, None")
    print("   ")
    print("   # 在 process 方法中")
    print("   is_forbidden, topic = check_forbidden_topics(query, constraint_config)")
    print("   if is_forbidden:")
    print("       fallback_msg = constraint_config.fallback.get('no_result_message')")
    print("       yield ResponseBuilder.text_chunk(fallback_msg)")
    print("       return")
    print("   ```")
    print()
    
    print("3. 添加答案后验证")
    print("   在生成完整回答后，验证答案质量:")
    print("   ```python")
    print("   # 生成回答后")
    print("   validation_result = validator.validate_answer(")
    print("       full_answer,")
    print("       rag_context.sources,")
    print("       rag_context.context_text")
    print("   )")
    print("   ")
    print("   if not validation_result.is_valid:")
    print("       logger.warning(f'答案验证失败: {validation_result.warnings}')")
    print("       # 可以选择返回兜底消息或重新生成")
    print("   ```")
    print()
    
    print("4. 添加审计日志")
    print("   记录禁止主题的查询尝试:")
    print("   ```python")
    print("   if is_forbidden:")
    print("       logger.warning(")
    print("           f'禁止主题查询: topic={topic}, '")
    print("           f'query={query[:50]}...'")
    print("       )")
    print("   ```")


def main():
    """运行所有检查"""
    print("\n" + "="*70)
    print("  约束配置使用情况检查")
    print("="*70)
    
    results = {
        "配置加载": check_config_loading(),
        "Prompt 构建": check_prompt_building(),
        "QA Agent 使用": check_qa_agent_usage(),
        "答案验证器使用": check_answer_validator_usage(),
        "Chat API 使用": check_chat_api_usage()
    }
    
    # 生成改进建议
    generate_recommendations()
    
    # 总结
    print_section("检查总结")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    print(f"检查项目: {total}")
    print(f"通过: {passed}")
    print(f"失败: {total - passed}")
    print()
    
    for name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {name}: {status}")
    
    print()
    
    if passed == total:
        print("🎉 所有检查通过！约束配置已正确应用。")
        return 0
    else:
        print("⚠️  发现问题！约束配置未完全应用到项目中。")
        print("   请查看上面的改进建议进行修复。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
