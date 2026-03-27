#!/usr/bin/env python
"""
测试统一的文件扩展名常量
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.constants import DocumentConstants


def test_constants():
    """测试 DocumentConstants 的各种属性"""
    
    print("=" * 60)
    print("文件扩展名常量测试")
    print("=" * 60)
    
    # 1. 支持的格式
    print("\n1. 支持的格式（不带点）:")
    print(f"   {DocumentConstants.SUPPORTED_FORMATS}")
    print(f"   总计: {len(DocumentConstants.SUPPORTED_FORMATS)} 种格式")
    
    # 2. 支持的扩展名
    print("\n2. 支持的扩展名（带点）:")
    print(f"   {DocumentConstants.SUPPORTED_EXTENSIONS}")
    print(f"   总计: {len(DocumentConstants.SUPPORTED_EXTENSIONS)} 个扩展名")
    
    # 3. 扩展名集合
    print("\n3. 扩展名集合（用于快速查找）:")
    print(f"   类型: {type(DocumentConstants.SUPPORTED_EXTENSIONS_SET)}")
    print(f"   大小: {len(DocumentConstants.SUPPORTED_EXTENSIONS_SET)}")
    
    # 4. 扩展名到类型的映射
    print("\n4. 扩展名到类型的映射:")
    for ext, type_name in sorted(DocumentConstants.EXTENSION_TO_TYPE.items()):
        print(f"   {ext:8} -> {type_name}")
    
    # 5. 文档类型分类
    print("\n5. 文档类型分类:")
    for category, formats in DocumentConstants.DOCUMENT_TYPES.items():
        print(f"   {category:12}: {formats}")
    
    # 6. HTML Accept 属性
    print("\n6. HTML Accept 属性值:")
    print(f"   {DocumentConstants.ACCEPT_TYPES}")
    
    # 7. 其他常量
    print("\n7. 其他常量:")
    print(f"   最大文件大小: {DocumentConstants.MAX_FILE_SIZE_MB} MB")
    print(f"   默认分块大小: {DocumentConstants.DEFAULT_CHUNK_SIZE}")
    print(f"   默认分块重叠: {DocumentConstants.DEFAULT_CHUNK_OVERLAP}")
    
    # 8. 测试查找功能
    print("\n8. 测试查找功能:")
    test_files = [
        "document.pdf",
        "spreadsheet.xlsx",
        "image.png",
        "unknown.xyz"
    ]
    
    for filename in test_files:
        ext = "." + filename.split(".")[-1]
        is_supported = ext in DocumentConstants.SUPPORTED_EXTENSIONS_SET
        file_type = DocumentConstants.EXTENSION_TO_TYPE.get(ext, "未知")
        print(f"   {filename:20} -> 支持: {is_supported:5} | 类型: {file_type}")
    
    # 9. 验证一致性
    print("\n9. 验证数据一致性:")
    
    # 检查 SUPPORTED_EXTENSIONS 和 EXTENSION_TO_TYPE 的一致性
    extensions_from_formats = set(DocumentConstants.SUPPORTED_EXTENSIONS)
    extensions_from_mapping = set(DocumentConstants.EXTENSION_TO_TYPE.keys())
    
    print(f"   SUPPORTED_EXTENSIONS 数量: {len(extensions_from_formats)}")
    print(f"   EXTENSION_TO_TYPE 数量: {len(extensions_from_mapping)}")
    
    # 找出差异
    only_in_formats = extensions_from_formats - extensions_from_mapping
    only_in_mapping = extensions_from_mapping - extensions_from_formats
    
    if only_in_formats:
        print(f"   ⚠️  只在 SUPPORTED_EXTENSIONS 中: {only_in_formats}")
    if only_in_mapping:
        print(f"   ⚠️  只在 EXTENSION_TO_TYPE 中: {only_in_mapping}")
    
    if not only_in_formats and not only_in_mapping:
        print(f"   ✓ 数据一致性检查通过")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    test_constants()
