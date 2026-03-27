"""
生成Settings测试报告

使用方法:
    python backend/tests/generate_test_report.py
"""
import sys
import pytest
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def generate_report():
    """生成测试报告"""
    test_files = [
        "backend/tests/settings/test_settings.py",
        "backend/tests/settings/test_config_loader.py"
    ]
    
    report_file = Path("backend/tests/settings/test_report.txt")
    
    print("=" * 70)
    print("生成Settings配置测试报告")
    print("=" * 70)
    print()
    
    # 运行测试并生成报告
    args = [
        "-v",
        "--tb=short",
        "--color=no",
        f"--html=backend/tests/settings/test_report.html",
        "--self-contained-html",
    ] + test_files
    
    # 运行测试
    exit_code = pytest.main(args)
    
    # 生成文本报告
    with open(report_file, "w", encoding="utf-8") as f:
        f.write("=" * 70 + "\n")
        f.write("Settings配置测试报告\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"测试结果: {'通过' if exit_code == 0 else '失败'}\n\n")
        
        f.write("测试文件:\n")
        for test_file in test_files:
            f.write(f"  - {test_file}\n")
        
        f.write("\n详细报告请查看: test_report.html\n")
    
    print("\n" + "=" * 70)
    print(f"报告已生成:")
    print(f"  - 文本报告: {report_file}")
    print(f"  - HTML报告: backend/tests/settings/test_report.html")
    print("=" * 70)
    
    return exit_code


if __name__ == "__main__":
    try:
        sys.exit(generate_report())
    except Exception as e:
        print(f"生成报告时出错: {e}")
        sys.exit(1)
