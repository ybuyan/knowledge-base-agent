"""
测试 Embedding 连接
运行方式: cd backend && python -m tests.test_embedding
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.embeddings import get_embeddings


async def main():
    print("=" * 50)
    print("测试 Embedding 模型连接")
    print("=" * 50)
    
    try:
        embeddings = get_embeddings()
        print(f"\n模型: {embeddings.model}")
        
        print("\n发送测试文本: '这是一个测试文本'")
        print("-" * 50)
        
        result = await embeddings.aembed_query("这是一个测试文本")
        
        print(f"\n向量维度: {len(result)}")
        print(f"向量前5个值: {result[:5]}")
        
        print("\n" + "=" * 50)
        print("✅ Embedding 连接测试成功!")
        print("=" * 50)
        
    except ValueError as e:
        print(f"\n❌ 配置错误: {e}")
        print("\n请在 backend/.env 文件中配置:")
        print("  DASHSCOPE_API_KEY=your_api_key")
        
    except Exception as e:
        print(f"\n❌ 连接失败: {e}")


if __name__ == "__main__":
    asyncio.run(main())
