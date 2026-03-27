"""
运行所有settings相关的测试

使用方法:
    python backend/tests/run_settings_tests.py
"""
import sys
import pytest
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def run_tests():
    """运行所有settings测试"""
    test_files = [
        "tests/settings/test_settings.py",
        "tests/settings/test_config_loader.py"
    ]
    
    print("=" * 70)
    print("运行Settings配置测试")
    print("=" * 70)
    
    # 运行测试
    args = [
        "-v",  # 详细输出
        "--tb=short",  # 简短的traceback
        "--color=yes",  # 彩色输出
        "-x",  # 遇到第一个失败就停止
    ] + test_files
    
    exit_code = pytest.main(args)
    
    print("\n" + "=" * 70)
    if exit_code == 0:
        print("✓ 所有测试通过!")
    else:
        print("✗ 部分测试失败")
    print("=" * 70)
    
    return exit_code


if __name__ == "__main__":
    sys.exit(run_tests())
