"""
测试 ChromaDB 初始化
运行方式: cd backend && python -m tests.test_chroma
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.chroma import init_chroma, get_chroma_stats


def main():
    print("=" * 50)
    print("测试 ChromaDB 初始化")
    print("=" * 50)
    
    try:
        result = init_chroma()
        print(f"\n状态: {result['status']}")
        print(f"消息: {result['message']}")
        print(f"集合: {result['collections']}")
        
        stats = get_chroma_stats()
        print(f"\n文档数量: {stats['documents_count']}")
        print(f"对话数量: {stats['conversations_count']}")
        
        print("\n" + "=" * 50)
        print("✅ ChromaDB 初始化成功!")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n❌ 初始化失败: {e}")


if __name__ == "__main__":
    main()
