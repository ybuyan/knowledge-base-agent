#!/usr/bin/env python3
"""
快速测试脚本

用于快速验证约束配置是否正确加载和工作
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.core.constraint_config import get_constraint_config, DEFAULT_CONSTRAINTS
from app.services.answer_validator import get_answer_validator


def print_section(title: str):
    """打印分节标题"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def test_config_loading():
    """测试配置加载"""
    print_section("测试 1: 配置加载")
    
    try:
        config = get_constraint_config()
        print("✅ 配置加载成功")
        
        # 验证配置结构
        assert hasattr(config, 'retrieval'), "缺少 retrieval 属性"
        assert hasattr(config, 'generation'), "缺少 generation 属性"
        assert hasattr(config, 'validation'), "缺少 validation 属性"
        assert hasattr(config, 'fallback'), "缺少 fallback 属性"
        
        print("✅ 配置结构完整")
        return True
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        return False


def test_retrieval_config():
    """测试检索配置"""
    print_section("测试 2: 检索配置")
    
    try:
        config = get_constraint_config()
        retrieval = config.retrieval
        
        print(f"启用状态: {retrieval.get('enabled')}")
        print(f"最小相似度: {retrieval.get('min_similarity_score')}")
        print(f"最小文档数: {retrieval.get('min_relevant_docs')}")
        print(f"最大文档数: {retrieval.get('max_relevant_docs')}")
        print(f"内容覆盖阈值: {retrieval.get('content_coverage_threshold')}")
        
        # 验证必需字段
        assert 'enabled' in retrieval, "缺少 enabled 字段"
        assert 'min_similarity_score' in retrieval, "缺少 min_similarity_score 字段"
        assert 'max_relevant_docs' in retrieval, "缺少 max_relevant_docs 字段"
        
        print("\n✅ 检索配置正确")
        return True
    except Exception as e:
        print(f"\n❌ 检索配置错误: {e}")
        return False


def test_generation_config():
    """测试生成配置"""
    print_section("测试 3: 生成配置")
    
    try:
        config = get_constraint_config()
        generation = config.generation
        
        print(f"严格模式: {generation.get('strict_mode')}")
        print(f"允许通用知识: {generation.get('allow_general_knowledge')}")
        print(f"需要引用: {generation.get('require_citations')}")
        print(f"最大回答长度: {generation.get('max_answer_length')}")
        print(f"禁止主题: {generation.get('forbidden_topics')}")
        print(f"禁止关键词: {generation.get('forbidden_keywords')}")
        
        # 验证必需字段
        assert 'strict_mode' in generation, "缺少 strict_mode 字段"
        assert 'forbidden_topics' in generation, "缺少 forbidden_topics 字段"
        assert 'forbidden_keywords' in generation, "缺少 forbidden_keywords 字段"
        
        print("\n✅ 生成配置正确")
        return True
    except Exception as e:
        print(f"\n❌ 生成配置错误: {e}")
        return False


def test_validation_config():
    """测试验证配置"""
    print_section("测试 4: 验证配置")
    
    try:
        config = get_constraint_config()
        validation = config.validation
        
        print(f"启用状态: {validation.get('enabled')}")
        print(f"检查来源归属: {validation.get('check_source_attribution')}")
        print(f"最小置信度: {validation.get('min_confidence_score')}")
        print(f"幻觉检测: {validation.get('hallucination_detection')}")
        
        # 验证必需字段
        assert 'enabled' in validation, "缺少 enabled 字段"
        assert 'min_confidence_score' in validation, "缺少 min_confidence_score 字段"
        
        print("\n✅ 验证配置正确")
        return True
    except Exception as e:
        print(f"\n❌ 验证配置错误: {e}")
        return False


def test_fallback_config():
    """测试兜底配置"""
    print_section("测试 5: 兜底配置")
    
    try:
        config = get_constraint_config()
        fallback = config.fallback
        
        print(f"无结果消息: {fallback.get('no_result_message')}")
        print(f"建议相似问题: {fallback.get('suggest_similar')}")
        print(f"建议联系: {fallback.get('suggest_contact')}")
        print(f"联系信息: {fallback.get('contact_info')}")
        
        # 验证必需字段
        assert 'no_result_message' in fallback, "缺少 no_result_message 字段"
        assert 'contact_info' in fallback, "缺少 contact_info 字段"
        
        print("\n✅ 兜底配置正确")
        return True
    except Exception as e:
        print(f"\n❌ 兜底配置错误: {e}")
        return False


def test_validator_initialization():
    """测试验证器初始化"""
    print_section("测试 6: 验证器初始化")
    
    try:
        validator = get_answer_validator()
        print("✅ 验证器初始化成功")
        
        # 验证验证器有配置
        assert hasattr(validator, 'config'), "验证器缺少 config 属性"
        print("✅ 验证器配置正确")
        
        return True
    except Exception as e:
        print(f"❌ 验证器初始化失败: {e}")
        return False


def test_retrieval_validation():
    """测试检索验证功能"""
    print_section("测试 7: 检索验证功能")
    
    try:
        validator = get_answer_validator()
        
        # 测试数据
        documents = ["文档1", "文档2", "文档3"]
        metadatas = [
            {"source": "doc1.pdf"},
            {"source": "doc2.pdf"},
            {"source": "doc3.pdf"}
        ]
        distances = [0.2, 0.8, 1.5]  # 相似度: 0.9, 0.6, 0.25
        
        filtered_docs, filtered_contents = validator.validate_retrieval(
            documents, metadatas, distances
        )
        
        print(f"原始文档数: {len(documents)}")
        print(f"过滤后文档数: {len(filtered_docs)}")
        print(f"过滤后内容数: {len(filtered_contents)}")
        
        if filtered_docs:
            print(f"\n保留的文档相似度:")
            for doc in filtered_docs:
                print(f"  - {doc['metadata']['source']}: {doc['similarity']:.3f}")
        
        print("\n✅ 检索验证功能正常")
        return True
    except Exception as e:
        print(f"\n❌ 检索验证功能错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_source_attribution():
    """测试来源归属检查"""
    print_section("测试 8: 来源归属检查")
    
    try:
        validator = get_answer_validator()
        
        # 测试有引用的回答
        answer_with_citation = "根据文档[1]，公司规定员工需要遵守考勤制度。"
        sources = [{"content": "考勤制度规定", "source": "doc1.pdf"}]
        
        has_attribution, warnings = validator.check_source_attribution(
            answer_with_citation, sources
        )
        
        print(f"回答: {answer_with_citation}")
        print(f"有来源归属: {has_attribution}")
        print(f"警告: {warnings if warnings else '无'}")
        
        # 测试无引用的回答
        answer_without_citation = "公司规定员工需要遵守考勤制度。"
        has_attribution2, warnings2 = validator.check_source_attribution(
            answer_without_citation, sources
        )
        
        print(f"\n回答: {answer_without_citation}")
        print(f"有来源归属: {has_attribution2}")
        print(f"警告: {warnings2 if warnings2 else '无'}")
        
        print("\n✅ 来源归属检查功能正常")
        return True
    except Exception as e:
        print(f"\n❌ 来源归属检查错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_hallucination_detection():
    """测试幻觉检测"""
    print_section("测试 9: 幻觉检测")
    
    try:
        validator = get_answer_validator()
        
        # 测试有幻觉风险的回答
        answer_with_hallucination = "我猜测这个政策可能是这样的，大概需要3天时间。"
        context = "政策规定"
        
        has_hallucination, indicators, confidence = validator.detect_hallucination(
            answer_with_hallucination, context
        )
        
        print(f"回答: {answer_with_hallucination}")
        print(f"有幻觉风险: {has_hallucination}")
        print(f"置信度: {confidence:.3f}")
        print(f"风险指标: {indicators if indicators else '无'}")
        
        # 测试正常回答
        answer_clean = "根据文档，政策规定如下。"
        has_hallucination2, indicators2, confidence2 = validator.detect_hallucination(
            answer_clean, context
        )
        
        print(f"\n回答: {answer_clean}")
        print(f"有幻觉风险: {has_hallucination2}")
        print(f"置信度: {confidence2:.3f}")
        print(f"风险指标: {indicators2 if indicators2 else '无'}")
        
        print("\n✅ 幻觉检测功能正常")
        return True
    except Exception as e:
        print(f"\n❌ 幻觉检测错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有快速测试"""
    print("\n" + "="*60)
    print("  约束系统快速测试")
    print("="*60)
    
    tests = [
        test_config_loading,
        test_retrieval_config,
        test_generation_config,
        test_validation_config,
        test_fallback_config,
        test_validator_initialization,
        test_retrieval_validation,
        test_source_attribution,
        test_hallucination_detection
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n❌ 测试异常: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    # 总结
    print_section("测试总结")
    passed = sum(results)
    total = len(results)
    
    print(f"通过: {passed}/{total}")
    print(f"失败: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
