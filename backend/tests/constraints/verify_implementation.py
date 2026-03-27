"""
验证新实施功能的脚本
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def check_min_relevant_docs():
    """检查 min_relevant_docs 实施"""
    print("\n检查功能 1: retrieval.min_relevant_docs")
    print("=" * 60)
    
    qa_agent_file = project_root / "app" / "services" / "qa_agent.py"
    with open(qa_agent_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查关键代码
    checks = [
        ("min_docs = retrieval_config.get('min_relevant_docs'", "读取配置"),
        ("if len(rag_context.documents) < min_docs:", "检查文档数量"),
        ("检索文档数不足", "日志记录"),
        ("fallback_msg = StrictQAPrompt.get_fallback_message", "返回兜底消息")
    ]
    
    passed = 0
    for check_str, desc in checks:
        if check_str in content:
            print(f"  [OK] {desc}")
            passed += 1
        else:
            print(f"  [FAIL] {desc}")
    
    print(f"\n结果: {passed}/{len(checks)} 检查通过")
    return passed == len(checks)


def check_suggest_contact():
    """检查 suggest_contact 实施"""
    print("\n检查功能 2: fallback.suggest_contact")
    print("=" * 60)
    
    strict_qa_file = project_root / "app" / "prompts" / "strict_qa.py"
    with open(strict_qa_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查关键代码
    checks = [
        ("def get_fallback_message", "方法定义"),
        ("config=None", "支持 config 参数"),
        ("fallback_config.get('suggest_contact'", "读取配置"),
        ("if fallback_config.get('suggest_contact', True):", "条件判断"),
    ]
    
    passed = 0
    for check_str, desc in checks:
        if check_str in content:
            print(f"  [OK] {desc}")
            passed += 1
        else:
            print(f"  [FAIL] {desc}")
    
    print(f"\n结果: {passed}/{len(checks)} 检查通过")
    return passed == len(checks)


def check_tests():
    """检查测试文件"""
    print("\n检查测试文件")
    print("=" * 60)
    
    test_files = [
        "test_min_relevant_docs.py",
        "test_suggest_contact.py"
    ]
    
    passed = 0
    for test_file in test_files:
        test_path = project_root / "tests" / "constraints" / test_file
        if test_path.exists():
            print(f"  [OK] {test_file} 存在")
            passed += 1
        else:
            print(f"  [FAIL] {test_file} 不存在")
    
    print(f"\n结果: {passed}/{len(test_files)} 测试文件存在")
    return passed == len(test_files)


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("  验证新实施功能")
    print("=" * 60)
    
    results = []
    
    # 检查功能实施
    results.append(("min_relevant_docs", check_min_relevant_docs()))
    results.append(("suggest_contact", check_suggest_contact()))
    results.append(("测试文件", check_tests()))
    
    # 总结
    print("\n" + "=" * 60)
    print("  总结")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "[OK]" if result else "[FAIL]"
        print(f"  {status} {name}")
    
    print(f"\n总计: {passed}/{total} 功能验证通过")
    
    if passed == total:
        print("\n所有功能实施成功!")
        return 0
    else:
        print(f"\n还有 {total - passed} 个功能需要修复")
        return 1


if __name__ == "__main__":
    sys.exit(main())
