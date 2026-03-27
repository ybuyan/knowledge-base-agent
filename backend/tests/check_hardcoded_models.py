#!/usr/bin/env python3
"""
检查代码中是否还有硬编码的模型名称

使用方法：
    python scripts/check_hardcoded_models.py
"""
import os
import re
from pathlib import Path
from typing import List, Tuple

# 需要检查的模型名称
HARDCODED_PATTERNS = [
    r'model\s*=\s*["\']qwen-plus["\']',
    r'model\s*=\s*["\']qwen-turbo["\']',
    r'model\s*=\s*["\']qwen-max["\']',
    r'model\s*=\s*["\']gpt-4["\']',
    r'model\s*=\s*["\']gpt-3\.5-turbo["\']',
    r'model\s*=\s*["\']text-embedding-v3["\']',
    r'model:\s*str\s*=\s*["\']qwen-plus["\']',
    r'model:\s*str\s*=\s*["\']gpt-4["\']',
]

# 排除的文件和目录
EXCLUDE_PATTERNS = [
    'config.py',  # 配置文件中的默认值是允许的
    'test_',      # 测试文件
    '__pycache__',
    '.pyc',
    'venv',
    'node_modules',
    '.git',
    'docs/',      # 文档中的示例
    'scripts/',   # 脚本本身
]

def should_check_file(file_path: str) -> bool:
    """判断是否应该检查该文件"""
    # 只检查 Python 文件
    if not file_path.endswith('.py'):
        return False
    
    # 排除特定文件和目录
    for pattern in EXCLUDE_PATTERNS:
        if pattern in file_path:
            return False
    
    return True

def check_file(file_path: str) -> List[Tuple[int, str, str]]:
    """
    检查文件中的硬编码模型名称
    
    返回: [(行号, 匹配的模式, 行内容), ...]
    """
    issues = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        for line_num, line in enumerate(lines, 1):
            # 跳过注释行
            if line.strip().startswith('#'):
                continue
            
            # 检查每个模式
            for pattern in HARDCODED_PATTERNS:
                if re.search(pattern, line):
                    issues.append((line_num, pattern, line.strip()))
    
    except Exception as e:
        print(f"⚠️  读取文件失败: {file_path} - {e}")
    
    return issues

def main():
    """主函数"""
    print("=" * 70)
    print("检查硬编码的模型名称")
    print("=" * 70)
    print()
    
    # 获取项目根目录
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    app_dir = project_root / 'app'
    
    if not app_dir.exists():
        print(f"❌ 找不到 app 目录: {app_dir}")
        return
    
    print(f"📁 检查目录: {app_dir}")
    print()
    
    # 收集所有需要检查的文件
    files_to_check = []
    for root, dirs, files in os.walk(app_dir):
        # 排除目录
        dirs[:] = [d for d in dirs if not any(pattern in d for pattern in EXCLUDE_PATTERNS)]
        
        for file in files:
            file_path = os.path.join(root, file)
            if should_check_file(file_path):
                files_to_check.append(file_path)
    
    print(f"📝 共需检查 {len(files_to_check)} 个文件")
    print()
    
    # 检查每个文件
    total_issues = 0
    files_with_issues = []
    
    for file_path in files_to_check:
        issues = check_file(file_path)
        if issues:
            total_issues += len(issues)
            files_with_issues.append((file_path, issues))
    
    # 输出结果
    if total_issues == 0:
        print("✅ 太棒了！没有发现硬编码的模型名称")
        print()
        print("所有模型配置都正确使用了 settings.llm_model 或 settings.embedding_model")
    else:
        print(f"❌ 发现 {total_issues} 处硬编码的模型名称")
        print()
        
        for file_path, issues in files_with_issues:
            rel_path = os.path.relpath(file_path, project_root)
            print(f"📄 {rel_path}")
            
            for line_num, pattern, line_content in issues:
                print(f"   第 {line_num} 行: {line_content}")
            print()
        
        print("=" * 70)
        print("修复建议:")
        print("=" * 70)
        print()
        print("将硬编码的模型名称替换为配置:")
        print()
        print("  ❌ model=\"qwen-plus\"")
        print("  ✅ from app.config import settings")
        print("     model=settings.llm_model")
        print()
        print("  ❌ model=\"text-embedding-v3\"")
        print("  ✅ from app.config import settings")
        print("     model=settings.embedding_model")
        print()
        print("详细说明请查看: backend/docs/MODEL_CONFIGURATION.md")
    
    print()
    print("=" * 70)
    print(f"检查完成！共检查 {len(files_to_check)} 个文件，发现 {total_issues} 个问题")
    print("=" * 70)
    
    # 返回退出码
    return 1 if total_issues > 0 else 0

if __name__ == "__main__":
    exit(main())
