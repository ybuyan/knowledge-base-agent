#!/usr/bin/env python
"""
测试处理器注册表
验证所有处理器是否正确注册
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# 导入所有处理器以触发注册
from app.skills.processors import (
    DocumentParser,
    TextSplitter,
    SmartTextSplitter,
    EmbeddingProcessor,
    VectorRetriever,
    VectorStore,
    LLMGenerator,
    ContextBuilder,
    KeywordIndexBuilder
)
from app.skills.base import ProcessorRegistry


def test_processor_registry():
    """测试处理器注册表"""
    
    print("=" * 60)
    print("处理器注册表测试")
    print("=" * 60)
    
    # 获取所有已注册的处理器
    registered_processors = ProcessorRegistry.list_all()
    
    print(f"\n已注册的处理器数量: {len(registered_processors)}")
    print("\n已注册的处理器列表:")
    for i, name in enumerate(sorted(registered_processors), 1):
        processor = ProcessorRegistry.get(name)
        print(f"  {i}. {name:25} -> {processor.__class__.__name__}")
    
    # 测试每个处理器是否可以获取
    print("\n" + "=" * 60)
    print("测试处理器获取")
    print("=" * 60)
    
    expected_processors = [
        "DocumentParser",
        "TextSplitter",
        "SmartTextSplitter",
        "EmbeddingProcessor",
        "VectorRetriever",
        "VectorStore",
        "LLMGenerator",
        "ContextBuilder",
        "KeywordIndexBuilder"
    ]
    
    all_ok = True
    for name in expected_processors:
        try:
            processor = ProcessorRegistry.get(name)
            print(f"  ✓ {name:25} - 成功获取")
        except ValueError as e:
            print(f"  ✗ {name:25} - 失败: {e}")
            all_ok = False
    
    # 测试不存在的处理器
    print("\n" + "=" * 60)
    print("测试错误处理")
    print("=" * 60)
    
    try:
        ProcessorRegistry.get("NonExistentProcessor")
        print("  ✗ 应该抛出 ValueError")
        all_ok = False
    except ValueError as e:
        print(f"  ✓ 正确抛出异常: {e}")
    
    # 验证配置文件中使用的处理器
    print("\n" + "=" * 60)
    print("验证配置文件中的处理器")
    print("=" * 60)
    
    import json
    config_path = Path(__file__).parent.parent / "app" / "skills" / "config.json"
    
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        used_processors = set()
        for skill in config.get("skills", []):
            for step in skill.get("pipeline", []):
                processor_name = step.get("processor")
                if processor_name:
                    used_processors.add(processor_name)
        
        print(f"\n配置文件中使用的处理器: {len(used_processors)} 个")
        
        for name in sorted(used_processors):
            try:
                ProcessorRegistry.get(name)
                print(f"  ✓ {name:25} - 已注册")
            except ValueError:
                print(f"  ✗ {name:25} - 未注册！")
                all_ok = False
    else:
        print(f"  配置文件不存在: {config_path}")
    
    # 总结
    print("\n" + "=" * 60)
    if all_ok:
        print("✓ 所有测试通过")
    else:
        print("✗ 部分测试失败")
    print("=" * 60)
    
    return all_ok


if __name__ == "__main__":
    success = test_processor_registry()
    sys.exit(0 if success else 1)
