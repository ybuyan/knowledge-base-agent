#!/usr/bin/env python3
"""
全面检查所有约束配置项是否应用到代码中

检查 constraints.json 中的每一个配置项
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.core.constraint_config import get_constraint_config


def print_section(title: str, level: int = 1):
    """打印分节标题"""
    if level == 1:
        print(f"\n{'='*70}")
        print(f"  {title}")
        print(f"{'='*70}\n")
    else:
        print(f"\n{'-'*70}")
        print(f"  {title}")
        print(f"{'-'*70}\n")


def check_retrieval_config():
    """检查检索配置的应用"""
    print_section("1. 检索配置 (retrieval)", 1)
    
    config = get_constraint_config()
    retrieval = config.retrieval
    
    print("配置项:")
    for key, value in retrieval.items():
        print(f"  {key}: {value}")
    
    results = {}
    
    # 1.1 检查 enabled
    print_section("1.1 enabled - 是否启用检索约束", 2)
    print(f"配置值: {retrieval.get('enabled')}")
    
    qa_agent_file = project_root / "app" / "services" / "qa_agent.py"
    with open(qa_agent_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'retrieval_config.get("enabled"' in content:
        print("✅ 在 qa_agent.py 中使用")
        print("   位置: _retrieve 方法")
        results['retrieval.enabled'] = True
    else:
        print("❌ 未在代码中使用")
        results['retrieval.enabled'] = False
    
    # 1.2 检查 min_similarity_score
    print_section("1.2 min_similarity_score - 最小相似度阈值", 2)
    print(f"配置值: {retrieval.get('min_similarity_score')}")
    
    validator_file = project_root / "app" / "services" / "answer_validator.py"
    with open(validator_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'min_similarity_score' in content or 'min_similarity' in content:
        print("✅ 在 answer_validator.py 中使用")
        print("   位置: validate_retrieval 方法")
        print("   用途: 过滤低相似度文档")
        results['retrieval.min_similarity_score'] = True
    else:
        print("❌ 未在代码中使用")
        results['retrieval.min_similarity_score'] = False
    
    # 1.3 检查 min_relevant_docs
    print_section("1.3 min_relevant_docs - 最小相关文档数", 2)
    print(f"配置值: {retrieval.get('min_relevant_docs')}")
    
    with open(qa_agent_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if "retrieval_config.get('min_relevant_docs'" in content or 'min_docs' in content:
        print("✅ 在 qa_agent.py 中使用")
        print("   位置: _execute_rag_flow 方法")
        print("   用途: 检查检索到的文档数量是否满足最小要求")
        results['retrieval.min_relevant_docs'] = True
    else:
        print("⚠️  此配置项在代码中未使用")
        print("   建议: 在检索后检查文档数量是否满足最小要求")
        results['retrieval.min_relevant_docs'] = False
    
    # 1.4 检查 max_relevant_docs
    print_section("1.4 max_relevant_docs - 最大相关文档数", 2)
    print(f"配置值: {retrieval.get('max_relevant_docs')}")
    
    with open(qa_agent_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'max_relevant_docs' in content or 'max_docs' in content:
        print("✅ 在 qa_agent.py 中使用")
        print("   位置: _retrieve 方法")
        print("   用途: 限制检索文档数量")
        results['retrieval.max_relevant_docs'] = True
    else:
        print("❌ 未在代码中使用")
        results['retrieval.max_relevant_docs'] = False
    
    # 1.5 检查 content_coverage_threshold
    print_section("1.5 content_coverage_threshold - 内容覆盖阈值", 2)
    print(f"配置值: {retrieval.get('content_coverage_threshold')}")
    print("⚠️  此配置项在代码中未使用")
    print("   建议: 用于检查检索内容是否充分覆盖查询")
    results['retrieval.content_coverage_threshold'] = False
    
    return results


def check_generation_config():
    """检查生成配置的应用"""
    print_section("2. 生成配置 (generation)", 1)
    
    config = get_constraint_config()
    generation = config.generation
    
    print("配置项:")
    for key, value in generation.items():
        print(f"  {key}: {value}")
    
    results = {}
    
    # 读取相关文件
    prompt_file = project_root / "app" / "prompts" / "strict_qa.py"
    with open(prompt_file, 'r', encoding='utf-8') as f:
        prompt_content = f.read()
    
    qa_agent_file = project_root / "app" / "services" / "qa_agent.py"
    with open(qa_agent_file, 'r', encoding='utf-8') as f:
        qa_content = f.read()
    
    # 2.1 检查 strict_mode
    print_section("2.1 strict_mode - 严格模式", 2)
    print(f"配置值: {generation.get('strict_mode')}")
    
    if "generation.get('strict_mode'" in prompt_content and 'ConstraintPromptBuilder.build_system_prompt' in qa_content:
        print("✅ 在代码中使用")
        print("   位置: ConstraintPromptBuilder.build_system_prompt")
        print("   用途: 控制回答的严格程度")
        results['generation.strict_mode'] = True
    else:
        print("⚠️  此配置项在代码中未直接使用")
        print("   说明: 严格模式应该影响回答生成策略")
        print("   建议: 在 Prompt 中根据此配置调整指令")
        results['generation.strict_mode'] = False
    
    # 2.2 检查 allow_general_knowledge
    print_section("2.2 allow_general_knowledge - 允许通用知识", 2)
    print(f"配置值: {generation.get('allow_general_knowledge')}")
    
    if "generation.get('allow_general_knowledge'" in prompt_content and 'ConstraintPromptBuilder.build_system_prompt' in qa_content:
        print("✅ 在代码中使用")
        print("   位置: ConstraintPromptBuilder.build_system_prompt")
        print("   用途: 控制是否允许使用通用知识")
        results['generation.allow_general_knowledge'] = True
    else:
        print("⚠️  此配置项在代码中未直接使用")
        print("   说明: 控制是否允许 LLM 使用训练数据中的通用知识")
        print("   建议: 在 Prompt 中根据此配置调整指令")
        results['generation.allow_general_knowledge'] = False
    
    # 2.3 检查 require_citations
    print_section("2.3 require_citations - 需要引用", 2)
    print(f"配置值: {generation.get('require_citations')}")
    
    if "generation.get('require_citations'" in prompt_content and 'ConstraintPromptBuilder.build_system_prompt' in qa_content:
        print("✅ 在代码中使用")
        print("   位置: ConstraintPromptBuilder.build_system_prompt")
        print("   用途: 要求回答包含引用标记")
        results['generation.require_citations'] = True
    else:
        print("⚠️  此配置项在代码中未直接使用")
        print("   说明: 控制回答是否必须包含引用标记")
        print("   建议: 在 Prompt 中根据此配置调整指令")
        results['generation.require_citations'] = False
    
    # 2.4 检查 max_answer_length
    print_section("2.4 max_answer_length - 最大回答长度", 2)
    print(f"配置值: {generation.get('max_answer_length')}")
    
    if "generation.get('max_answer_length'" in qa_content:
        print("✅ 在代码中使用")
        print("   位置: qa_agent.py _execute_rag_flow 方法")
        print("   用途: 限制回答的最大字符数")
        results['generation.max_answer_length'] = True
    else:
        print("⚠️  此配置项在代码中未直接使用")
        print("   说明: 控制回答的最大字符数")
        print("   建议: 在生成回答后检查长度并截断")
        results['generation.max_answer_length'] = False
    
    # 2.5 检查 forbidden_topics
    print_section("2.5 forbidden_topics - 禁止主题", 2)
    print(f"配置值: {generation.get('forbidden_topics')}")
    
    if 'forbidden_topics' in prompt_content and 'ConstraintPromptBuilder.build_system_prompt' in qa_content:
        print("✅ 在代码中使用")
        print("   位置: ConstraintPromptBuilder.build_system_prompt")
        print("   用途: 在 Prompt 中添加禁止主题说明")
        results['generation.forbidden_topics'] = True
    else:
        print("⚠️  在 strict_qa.py 中定义了处理方法")
        print("   但在 qa_agent.py 中未使用 ConstraintPromptBuilder")
        print("   ❌ 实际未生效")
        results['generation.forbidden_topics'] = False
    
    # 2.6 检查 forbidden_keywords
    print_section("2.6 forbidden_keywords - 禁止关键词", 2)
    print(f"配置值: {generation.get('forbidden_keywords')}")
    
    if 'forbidden_keywords' in prompt_content and 'ConstraintPromptBuilder.build_system_prompt' in qa_content:
        print("✅ 在代码中使用")
        print("   位置: ConstraintPromptBuilder.build_system_prompt")
        print("   用途: 在 Prompt 中添加禁止关键词说明")
        results['generation.forbidden_keywords'] = True
    else:
        print("⚠️  在 strict_qa.py 中定义了处理方法")
        print("   但在 qa_agent.py 中未使用 ConstraintPromptBuilder")
        print("   ❌ 实际未生效")
        results['generation.forbidden_keywords'] = False
    
    return results


def check_validation_config():
    """检查验证配置的应用"""
    print_section("3. 验证配置 (validation)", 1)
    
    config = get_constraint_config()
    validation = config.validation
    
    print("配置项:")
    for key, value in validation.items():
        print(f"  {key}: {value}")
    
    results = {}
    
    validator_file = project_root / "app" / "services" / "answer_validator.py"
    with open(validator_file, 'r', encoding='utf-8') as f:
        validator_content = f.read()
    
    # 3.1 检查 enabled
    print_section("3.1 enabled - 是否启用验证", 2)
    print(f"配置值: {validation.get('enabled')}")
    
    if 'validation_config.get("enabled"' in validator_content:
        print("✅ 在 answer_validator.py 中使用")
        print("   位置: validate_answer 方法")
        results['validation.enabled'] = True
    else:
        print("❌ 未在代码中使用")
        results['validation.enabled'] = False
    
    # 3.2 检查 check_source_attribution
    print_section("3.2 check_source_attribution - 检查来源归属", 2)
    print(f"配置值: {validation.get('check_source_attribution')}")
    
    if 'check_source_attribution' in validator_content:
        print("✅ 在 answer_validator.py 中使用")
        print("   位置: check_source_attribution 方法")
        print("   用途: 验证回答是否包含引用标记")
        results['validation.check_source_attribution'] = True
    else:
        print("❌ 未在代码中使用")
        results['validation.check_source_attribution'] = False
    
    # 3.3 检查 min_confidence_score
    print_section("3.3 min_confidence_score - 最小置信度", 2)
    print(f"配置值: {validation.get('min_confidence_score')}")
    
    if 'min_confidence_score' in validator_content:
        print("✅ 在 answer_validator.py 中使用")
        print("   位置: validate_answer 方法")
        print("   用途: 判断回答是否有效")
        results['validation.min_confidence_score'] = True
    else:
        print("❌ 未在代码中使用")
        results['validation.min_confidence_score'] = False
    
    # 3.4 检查 hallucination_detection
    print_section("3.4 hallucination_detection - 幻觉检测", 2)
    print(f"配置值: {validation.get('hallucination_detection')}")
    
    if 'hallucination_detection' in validator_content:
        print("✅ 在 answer_validator.py 中使用")
        print("   位置: detect_hallucination 方法")
        print("   用途: 检测回答中的不确定性词汇和数字")
        results['validation.hallucination_detection'] = True
    else:
        print("❌ 未在代码中使用")
        results['validation.hallucination_detection'] = False
    
    # 检查 validate_answer 是否在 qa_agent 中被调用
    qa_agent_file = project_root / "app" / "services" / "qa_agent.py"
    with open(qa_agent_file, 'r', encoding='utf-8') as f:
        qa_content = f.read()
    
    print_section("验证器在 QA Agent 中的使用", 2)
    if 'validator.validate_answer' in qa_content:
        print("✅ qa_agent.py 中调用了 validate_answer")
    else:
        print("❌ qa_agent.py 中未调用 validate_answer")
        print("   ⚠️  虽然验证器实现了功能，但未在生成回答后使用")
        print("   建议: 在 _execute_rag_flow 中生成回答后调用验证")
    
    return results


def check_fallback_config():
    """检查兜底配置的应用"""
    print_section("4. 兜底配置 (fallback)", 1)
    
    config = get_constraint_config()
    fallback = config.fallback
    
    print("配置项:")
    for key, value in fallback.items():
        print(f"  {key}: {value}")
    
    results = {}
    
    # 4.1 检查 no_result_message
    print_section("4.1 no_result_message - 无结果消息", 2)
    print(f"配置值: {fallback.get('no_result_message')}")
    
    qa_agent_file = project_root / "app" / "services" / "qa_agent.py"
    with open(qa_agent_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    prompt_file = project_root / "app" / "prompts" / "strict_qa.py"
    with open(prompt_file, 'r', encoding='utf-8') as f:
        prompt_content = f.read()
    
    if 'get_fallback_message' in content or 'get_fallback_message' in prompt_content:
        print("✅ 在代码中使用")
        print("   位置: StrictQAPrompt.get_fallback_message")
        print("   用途: 当无检索结果时返回")
        results['fallback.no_result_message'] = True
    else:
        print("❌ 未在代码中使用")
        results['fallback.no_result_message'] = False
    
    # 4.2 检查 suggest_similar
    print_section("4.2 suggest_similar - 建议相似问题", 2)
    print(f"配置值: {fallback.get('suggest_similar')}")
    print("⚠️  此配置项在代码中未使用")
    print("   说明: 控制是否在无结果时建议相似问题")
    print("   建议: 在兜底消息中根据此配置决定是否生成建议")
    results['fallback.suggest_similar'] = False
    
    # 4.3 检查 suggest_contact
    print_section("4.3 suggest_contact - 建议联系方式", 2)
    print(f"配置值: {fallback.get('suggest_contact')}")
    
    if "fallback_config.get('suggest_contact'" in prompt_content or 'suggest_contact' in prompt_content:
        print("✅ 在 strict_qa.py 中使用")
        print("   位置: get_fallback_message 方法")
        print("   用途: 控制是否显示联系信息")
        results['fallback.suggest_contact'] = True
    else:
        print("⚠️  此配置项在代码中未使用")
        print("   说明: 控制是否在无结果时显示联系方式")
        print("   建议: 在兜底消息中根据此配置决定是否显示联系信息")
        results['fallback.suggest_contact'] = False
    
    # 4.4 检查 contact_info
    print_section("4.4 contact_info - 联系信息", 2)
    print(f"配置值: {fallback.get('contact_info')[:50]}...")
    
    if 'contact_info' in prompt_content:
        print("✅ 在 strict_qa.py 中使用")
        print("   位置: get_fallback_message 方法")
        print("   用途: 在兜底消息中显示联系信息")
        results['fallback.contact_info'] = True
    else:
        print("❌ 未在代码中使用")
        results['fallback.contact_info'] = False
    
    return results


def check_suggest_questions_config():
    """检查建议问题配置的应用"""
    print_section("5. 建议问题配置 (suggest_questions)", 1)
    
    config = get_constraint_config()
    
    # 检查是否有 suggest_questions 配置
    if hasattr(config, 'suggest_questions'):
        suggest_questions = config.suggest_questions
        
        print("配置项:")
        for key, value in suggest_questions.items():
            print(f"  {key}: {value}")
    else:
        print("⚠️  配置文件中未定义 suggest_questions")
        print("   但在 DEFAULT_CONSTRAINTS 中有定义")
        suggest_questions = {
            "enabled": True,
            "count": 3,
            "types": ["相关追问", "深入探索", "对比分析"]
        }
    
    results = {}
    
    qa_agent_file = project_root / "app" / "services" / "qa_agent.py"
    with open(qa_agent_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 5.1 检查 enabled
    print_section("5.1 enabled - 是否启用建议问题", 2)
    print(f"配置值: {suggest_questions.get('enabled')}")
    
    if 'suggest_config.get("enabled"' in content:
        print("✅ 在 qa_agent.py 中使用")
        print("   位置: _execute_rag_flow 和 _execute_tool_flow 方法")
        print("   用途: 控制是否生成建议问题")
        results['suggest_questions.enabled'] = True
    else:
        print("❌ 未在代码中使用")
        results['suggest_questions.enabled'] = False
    
    # 5.2 检查 count
    print_section("5.2 count - 建议问题数量", 2)
    print(f"配置值: {suggest_questions.get('count')}")
    
    if 'suggest_config.get("count"' in content:
        print("✅ 在 qa_agent.py 中使用")
        print("   位置: 传递给 suggestion_generator")
        print("   用途: 控制生成的建议问题数量")
        results['suggest_questions.count'] = True
    else:
        print("❌ 未在代码中使用")
        results['suggest_questions.count'] = False
    
    # 5.3 检查 types
    print_section("5.3 types - 建议问题类型", 2)
    print(f"配置值: {suggest_questions.get('types')}")
    print("⚠️  此配置项在代码中未使用")
    print("   说明: 定义建议问题的类型")
    print("   建议: 在 suggestion_generator 中根据类型生成不同风格的问题")
    results['suggest_questions.types'] = False
    
    return results


def generate_summary(all_results):
    """生成总结报告"""
    print_section("总结报告", 1)
    
    total = len(all_results)
    used = sum(1 for v in all_results.values() if v)
    unused = total - used
    
    print(f"配置项总数: {total}")
    print(f"已应用: {used} ({used/total*100:.1f}%)")
    print(f"未应用: {unused} ({unused/total*100:.1f}%)")
    print()
    
    # 按类别统计
    categories = {
        'retrieval': [],
        'generation': [],
        'validation': [],
        'fallback': [],
        'suggest_questions': []
    }
    
    for key, value in all_results.items():
        category = key.split('.')[0]
        if category in categories:
            categories[category].append((key, value))
    
    print("按类别统计:")
    for category, items in categories.items():
        if items:
            used_count = sum(1 for _, v in items if v)
            total_count = len(items)
            print(f"  {category}: {used_count}/{total_count} 已应用")
    
    print()
    print("未应用的配置项:")
    for key, value in all_results.items():
        if not value:
            print(f"  ❌ {key}")
    
    print()
    print("已应用的配置项:")
    for key, value in all_results.items():
        if value:
            print(f"  ✅ {key}")


def generate_recommendations():
    """生成改进建议"""
    print_section("改进建议", 1)
    
    print("基于检查结果，以下配置项需要应用到代码中：\n")
    
    print("1. 高优先级（影响核心功能）")
    print("   - generation.forbidden_topics: 禁止主题")
    print("   - generation.forbidden_keywords: 禁止关键词")
    print("   - generation.strict_mode: 严格模式")
    print("   - generation.allow_general_knowledge: 允许通用知识")
    print("   - generation.require_citations: 需要引用")
    print()
    
    print("2. 中优先级（影响质量）")
    print("   - generation.max_answer_length: 最大回答长度")
    print("   - retrieval.min_relevant_docs: 最小相关文档数")
    print("   - retrieval.content_coverage_threshold: 内容覆盖阈值")
    print("   - validation.* 在 qa_agent 中调用")
    print()
    
    print("3. 低优先级（用户体验）")
    print("   - fallback.suggest_similar: 建议相似问题")
    print("   - fallback.suggest_contact: 建议联系方式")
    print("   - suggest_questions.types: 建议问题类型")
    print()
    
    print("详细修复方案请参考:")
    print("  - backend/docs/CONSTRAINT_FIX_PLAN.md")
    print("  - backend/docs/CONSTRAINT_FIX_CHECKLIST.md")


def main():
    """运行所有检查"""
    print("\n" + "="*70)
    print("  约束配置全面检查")
    print("="*70)
    
    all_results = {}
    
    # 检查各个配置类别
    all_results.update(check_retrieval_config())
    all_results.update(check_generation_config())
    all_results.update(check_validation_config())
    all_results.update(check_fallback_config())
    all_results.update(check_suggest_questions_config())
    
    # 生成总结
    generate_summary(all_results)
    
    # 生成建议
    generate_recommendations()
    
    # 返回状态码
    used = sum(1 for v in all_results.values() if v)
    total = len(all_results)
    
    if used == total:
        print("\n🎉 所有配置项都已应用！")
        return 0
    else:
        print(f"\n⚠️  有 {total - used}/{total} 个配置项未应用。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
