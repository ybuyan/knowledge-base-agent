#!/usr/bin/env python3
"""
约束系统测试运行脚本

提供便捷的测试运行接口，支持多种测试模式
"""

import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd: list, description: str) -> int:
    """运行命令并显示结果"""
    print(f"\n{'='*60}")
    print(f"  {description}")
    print(f"{'='*60}\n")
    
    result = subprocess.run(cmd, cwd=Path(__file__).parent.parent.parent)
    return result.returncode


def run_all_tests(verbose: bool = True, coverage: bool = False):
    """运行所有约束测试"""
    cmd = ["pytest", "tests/constraints/"]
    
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend([
            "--cov=app.core.constraint_config",
            "--cov=app.services.answer_validator",
            "--cov-report=html",
            "--cov-report=term"
        ])
    
    return run_command(cmd, "运行所有约束测试")


def run_unit_tests(verbose: bool = True):
    """运行单元测试（不需要服务器）"""
    tests = [
        "tests/constraints/test_constraint_config.py",
        "tests/constraints/test_answer_validator.py",
        "tests/constraints/test_constraint_integration.py"
    ]
    
    cmd = ["pytest"] + tests
    if verbose:
        cmd.append("-v")
    
    return run_command(cmd, "运行单元测试")


def run_api_tests(verbose: bool = True):
    """运行 API 测试（需要服务器运行）"""
    cmd = ["pytest", "tests/constraints/test_constraint_api.py"]
    
    if verbose:
        cmd.append("-v")
    
    cmd.append("--asyncio-mode=auto")
    
    print("\n⚠️  注意：API 测试需要后端服务器运行在 http://localhost:8000")
    print("   如果服务器未运行，请先执行: python backend/app/main.py\n")
    
    return run_command(cmd, "运行 API 测试")


def run_specific_test(test_path: str, verbose: bool = True):
    """运行特定测试"""
    cmd = ["pytest", test_path]
    
    if verbose:
        cmd.append("-v")
    
    return run_command(cmd, f"运行测试: {test_path}")


def run_with_markers(marker: str, verbose: bool = True):
    """运行带特定标记的测试"""
    cmd = ["pytest", "tests/constraints/", "-m", marker]
    
    if verbose:
        cmd.append("-v")
    
    return run_command(cmd, f"运行标记为 '{marker}' 的测试")


def generate_coverage_report():
    """生成测试覆盖率报告"""
    cmd = [
        "pytest",
        "tests/constraints/",
        "--cov=app.core.constraint_config",
        "--cov=app.services.answer_validator",
        "--cov-report=html",
        "--cov-report=term-missing"
    ]
    
    result = run_command(cmd, "生成测试覆盖率报告")
    
    if result == 0:
        print("\n✅ 覆盖率报告已生成到: htmlcov/index.html")
        print("   使用浏览器打开查看详细报告\n")
    
    return result


def main():
    parser = argparse.ArgumentParser(
        description="约束系统测试运行脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 运行所有测试
  python run_tests.py --all
  
  # 运行单元测试
  python run_tests.py --unit
  
  # 运行 API 测试
  python run_tests.py --api
  
  # 生成覆盖率报告
  python run_tests.py --coverage
  
  # 运行特定测试文件
  python run_tests.py --test tests/constraints/test_constraint_config.py
  
  # 运行特定测试类
  python run_tests.py --test tests/constraints/test_constraint_config.py::TestConstraintConfigLoading
  
  # 运行特定测试方法
  python run_tests.py --test tests/constraints/test_constraint_config.py::TestConstraintConfigLoading::test_singleton_pattern
        """
    )
    
    parser.add_argument(
        "--all",
        action="store_true",
        help="运行所有约束测试"
    )
    
    parser.add_argument(
        "--unit",
        action="store_true",
        help="运行单元测试（不需要服务器）"
    )
    
    parser.add_argument(
        "--api",
        action="store_true",
        help="运行 API 测试（需要服务器运行）"
    )
    
    parser.add_argument(
        "--test",
        type=str,
        help="运行特定测试文件、类或方法"
    )
    
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="生成测试覆盖率报告"
    )
    
    parser.add_argument(
        "--marker",
        type=str,
        help="运行带特定标记的测试"
    )
    
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="减少输出信息"
    )
    
    args = parser.parse_args()
    
    verbose = not args.quiet
    exit_code = 0
    
    # 如果没有指定任何选项，显示帮助
    if not any([args.all, args.unit, args.api, args.test, args.coverage, args.marker]):
        parser.print_help()
        return 0
    
    # 运行测试
    if args.all:
        exit_code = run_all_tests(verbose=verbose, coverage=args.coverage)
    
    elif args.unit:
        exit_code = run_unit_tests(verbose=verbose)
    
    elif args.api:
        exit_code = run_api_tests(verbose=verbose)
    
    elif args.test:
        exit_code = run_specific_test(args.test, verbose=verbose)
    
    elif args.coverage:
        exit_code = generate_coverage_report()
    
    elif args.marker:
        exit_code = run_with_markers(args.marker, verbose=verbose)
    
    # 显示结果
    print("\n" + "="*60)
    if exit_code == 0:
        print("  ✅ 测试通过")
    else:
        print("  ❌ 测试失败")
    print("="*60 + "\n")
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
