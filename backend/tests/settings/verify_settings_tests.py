"""
验证Settings测试套件的完整性

使用方法:
    python backend/tests/verify_settings_tests.py
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def verify_test_files():
    """验证测试文件存在"""
    print("=" * 70)
    print("验证测试文件")
    print("=" * 70)
    
    base_path = Path(__file__).parent
    test_files = [
        "test_settings.py",
        "test_config_loader.py",
        "run_settings_tests.py",
        "generate_test_report.py",
        "verify_settings_tests.py",
    ]
    
    all_exist = True
    for test_file in test_files:
        path = base_path / test_file
        exists = path.exists()
        status = "✓" if exists else "✗"
        print(f"{status} {test_file}")
        if not exists:
            all_exist = False
    
    return all_exist


def verify_documentation():
    """验证文档文件存在"""
    print("\n" + "=" * 70)
    print("验证文档文件")
    print("=" * 70)
    
    base_path = Path(__file__).parent
    doc_files = [
        "SETTINGS_TESTS_README.md",
        "SETTINGS_TEST_SUMMARY.md",
        "QUICK_REFERENCE.md",
        "README.md",
    ]
    
    all_exist = True
    for doc_file in doc_files:
        path = base_path / doc_file
        exists = path.exists()
        status = "✓" if exists else "✗"
        print(f"{status} {doc_file}")
        if not exists:
            all_exist = False
    
    return all_exist


def verify_config_files():
    """验证配置文件存在"""
    print("\n" + "=" * 70)
    print("验证配置文件")
    print("=" * 70)
    
    base_path = Path(__file__).parent.parent.parent
    config_files = [
        "app/config.py",
        "app/core/config_loader.py",
        "app/core/config.json",
        "app/agents/config.json",
        "app/skills/config.json",
        "app/tools/config.json",
        "app/prompts/config.json",
        ".env.example",
    ]
    
    all_exist = True
    for config_file in config_files:
        path = base_path / config_file
        exists = path.exists()
        status = "✓" if exists else "✗"
        print(f"{status} {config_file}")
        if not exists:
            all_exist = False
    
    return all_exist


def verify_test_structure():
    """验证测试结构"""
    print("\n" + "=" * 70)
    print("验证测试结构")
    print("=" * 70)
    
    try:
        import pytest
        
        base_path = Path(__file__).parent
        # 收集测试
        exit_code = pytest.main([
            str(base_path / "test_settings.py"),
            str(base_path / "test_config_loader.py"),
            "--collect-only",
            "-q"
        ])
        
        if exit_code == 0:
            print("✓ 测试结构正确")
            return True
        else:
            print("✗ 测试结构有问题")
            return False
    except Exception as e:
        print(f"✗ 验证测试结构时出错: {e}")
        return False


def run_quick_test():
    """运行快速测试"""
    print("\n" + "=" * 70)
    print("运行快速测试")
    print("=" * 70)
    
    try:
        import pytest
        
        base_path = Path(__file__).parent
        # 运行一个简单的测试
        exit_code = pytest.main([
            str(base_path / "test_settings.py") + "::TestSettingsBasic::test_default_settings",
            "-v",
            "-q"
        ])
        
        if exit_code == 0:
            print("✓ 快速测试通过")
            return True
        else:
            print("✗ 快速测试失败")
            return False
    except Exception as e:
        print(f"✗ 运行快速测试时出错: {e}")
        return False


def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("Settings测试套件完整性验证")
    print("=" * 70 + "\n")
    
    results = {
        "测试文件": verify_test_files(),
        "文档文件": verify_documentation(),
        "配置文件": verify_config_files(),
        "测试结构": verify_test_structure(),
        "快速测试": run_quick_test(),
    }
    
    print("\n" + "=" * 70)
    print("验证结果汇总")
    print("=" * 70)
    
    all_passed = True
    for name, passed in results.items():
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"{name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 70)
    if all_passed:
        print("✓ 所有验证通过！测试套件完整且可用。")
        print("\n运行完整测试:")
        print("  cd backend")
        print("  python tests/settings/run_settings_tests.py")
    else:
        print("✗ 部分验证失败，请检查上述错误。")
    print("=" * 70 + "\n")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
