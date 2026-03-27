"""
全局常量配置
"""

from typing import List, Set, Dict


class DocumentConstants:
    """文档处理相关常量"""

    # 支持的文档格式（不带点）
    SUPPORTED_FORMATS: List[str] = [
        "pdf", "docx", "txt", "md",
        "xlsx", "xls", "pptx",
        "png", "jpg", "jpeg", "gif", "bmp", "webp"
    ]

    # 支持的扩展名（带点）
    SUPPORTED_EXTENSIONS: List[str] = [f".{fmt}" for fmt in SUPPORTED_FORMATS]
    
    # 扩展名集合（用于快速查找）
    SUPPORTED_EXTENSIONS_SET: Set[str] = set(SUPPORTED_EXTENSIONS)

    # 扩展名到格式类型的映射
    EXTENSION_TO_TYPE: Dict[str, str] = {
        '.pdf': 'pdf',
        '.doc': 'docx',
        '.docx': 'docx',
        '.txt': 'txt',
        '.md': 'txt',
        '.xlsx': 'xlsx',
        '.xls': 'xlsx',
        '.pptx': 'pptx',
        '.png': 'image',
        '.jpg': 'image',
        '.jpeg': 'image',
        '.gif': 'image',
        '.bmp': 'image',
        '.webp': 'image'
    }

    # 文档类型分类
    DOCUMENT_TYPES: Dict[str, List[str]] = {
        'text': ['pdf', 'docx', 'txt', 'md'],
        'spreadsheet': ['xlsx', 'xls'],
        'presentation': ['pptx'],
        'image': ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp']
    }

    # HTML accept 属性值
    ACCEPT_TYPES: str = ",".join(SUPPORTED_EXTENSIONS)

    # 文件大小限制
    MAX_FILE_SIZE_MB: int = 50

    # 分块参数
    DEFAULT_CHUNK_SIZE: int = 500
    DEFAULT_CHUNK_OVERLAP: int = 50
