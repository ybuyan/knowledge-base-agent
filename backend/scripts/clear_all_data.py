"""
清除所有知识库数据

警告：此操作将删除所有数据，包括：
- 所有文档记录（数据库）
- 所有向量数据（ChromaDB）
- 所有关键词索引（MongoDB）
- 所有对话历史（可选）
- 所有上传的文件（可选）

此操作不可逆，请谨慎使用！
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import asyncio
import shutil
from pathlib import Path
from app.core.chroma import get_chroma_client, get_documents_collection, get_conversations_collection
from app.core.mongodb import get_mongo_db
from app.models.document import DocumentDB
from app.config import settings


async def clear_database_documents():
    """清除数据库中的所有文档记录"""
    print("\n=== 清除数据库文档记录 ===")
    try:
        docs = await DocumentDB.list()
        count = len(docs)
        
        if count == 0:
            print("  没有文档记录需要清除")
            return 0
        
        for doc in docs:
            await DocumentDB.delete(doc.id)
        
        print(f"  ✓ 已删除 {count} 条文档记录")
        return count
    except Exception as e:
        print(f"  ✗ 清除失败: {e}")
        return 0


def clear_vector_data(include_conversations=False):
    """清除 ChromaDB 中的所有向量数据"""
    print("\n=== 清除向量数据 ===")
    try:
        client = get_chroma_client()
        
        # 清除文档向量
        docs_collection = get_documents_collection()
        docs_count = docs_collection.count()
        
        if docs_count > 0:
            # 删除整个集合并重新创建
            client.delete_collection("documents")
            client.create_collection("documents", metadata={"description": "文档知识库"})
            print(f"  ✓ 已删除 {docs_count} 条文档向量")
        else:
            print("  没有文档向量需要清除")
        
        # 清除对话历史向量（可选）
        if include_conversations:
            convs_collection = get_conversations_collection()
            convs_count = convs_collection.count()
            
            if convs_count > 0:
                client.delete_collection("conversations")
                client.create_collection("conversations", metadata={"description": "对话历史"})
                print(f"  ✓ 已删除 {convs_count} 条对话向量")
            else:
                print("  没有对话向量需要清除")
            
            return docs_count + convs_count
        
        return docs_count
    except Exception as e:
        print(f"  ✗ 清除失败: {e}")
        return 0


async def clear_keyword_index():
    """清除 MongoDB 中的所有关键词索引"""
    print("\n=== 清除关键词索引 ===")
    try:
        db = get_mongo_db()
        if db is None:
            print("  MongoDB 未连接，跳过")
            return 0
        
        collection = db["keyword_index"]
        count = await collection.count_documents({})
        
        if count > 0:
            result = await collection.delete_many({})
            print(f"  ✓ 已删除 {result.deleted_count} 条关键词索引")
            return result.deleted_count
        else:
            print("  没有关键词索引需要清除")
            return 0
    except Exception as e:
        print(f"  ✗ 清除失败: {e}")
        return 0


def clear_uploaded_files():
    """清除所有上传的文件"""
    print("\n=== 清除上传的文件 ===")
    try:
        # 使用硬编码的路径，与 documents.py 保持一致
        upload_dir = Path("data/uploads")
        
        if not upload_dir.exists():
            print("  上传目录不存在，跳过")
            return 0
        
        # 统计文件数量
        files = list(upload_dir.glob("*"))
        count = len([f for f in files if f.is_file()])
        
        if count == 0:
            print("  没有上传的文件需要清除")
            return 0
        
        # 删除所有文件
        for file in files:
            if file.is_file():
                file.unlink()
        
        print(f"  ✓ 已删除 {count} 个上传的文件")
        return count
    except Exception as e:
        print(f"  ✗ 清除失败: {e}")
        return 0


def clear_chroma_persist_dir():
    """清除 ChromaDB 持久化目录（完全重置）"""
    print("\n=== 清除 ChromaDB 持久化目录 ===")
    try:
        chroma_dir = Path(settings.chroma_persist_dir)
        
        if not chroma_dir.exists():
            print("  ChromaDB 目录不存在，跳过")
            return True
        
        # 删除整个目录
        shutil.rmtree(chroma_dir)
        print(f"  ✓ 已删除 ChromaDB 目录: {chroma_dir}")
        
        # 重新创建目录
        chroma_dir.mkdir(parents=True, exist_ok=True)
        print(f"  ✓ 已重新创建 ChromaDB 目录")
        
        return True
    except Exception as e:
        print(f"  ✗ 清除失败: {e}")
        return False


async def clear_all_data(
    include_conversations=False,
    include_files=True,  # 默认删除文件
    complete_reset=False
):
    """
    清除所有知识库数据
    
    参数:
        include_conversations: 是否包括对话历史
        include_files: 是否删除上传的文件（默认 True）
        complete_reset: 是否完全重置（删除 ChromaDB 目录）
    """
    print("=" * 60)
    print("清除所有知识库数据")
    print("=" * 60)
    
    total_deleted = 0
    
    # 1. 清除数据库文档记录
    db_count = await clear_database_documents()
    total_deleted += db_count
    
    # 2. 清除向量数据
    if complete_reset:
        # 完全重置：删除整个 ChromaDB 目录
        clear_chroma_persist_dir()
    else:
        # 常规清除：删除集合中的数据
        vector_count = clear_vector_data(include_conversations)
        total_deleted += vector_count
    
    # 3. 清除关键词索引
    keyword_count = await clear_keyword_index()
    total_deleted += keyword_count
    
    # 4. 清除上传的文件（默认执行）
    file_count = clear_uploaded_files()
    if not include_files:
        print("  注意：已删除上传的文件（这是必需的，以确保完全清除）")
    
    print("\n" + "=" * 60)
    print("清除完成")
    print("=" * 60)
    print(f"总计删除: {total_deleted} 条记录")
    print(f"已删除上传的文件")
    
    if complete_reset:
        print("已完全重置 ChromaDB")
    
    print("\n⚠️  重要：请重启后端服务以清除内存缓存")
    print("知识库已清空，可以重新上传文档。")


async def confirm_and_clear():
    """确认后清除数据"""
    import argparse
    
    parser = argparse.ArgumentParser(description='清除所有知识库数据')
    parser.add_argument('--yes', '-y', action='store_true', help='跳过确认，直接执行')
    parser.add_argument('--include-conversations', action='store_true', help='包括对话历史')
    parser.add_argument('--keep-files', action='store_true', help='保留上传的文件（不推荐）')
    parser.add_argument('--complete-reset', action='store_true', help='完全重置（删除 ChromaDB 目录）')
    parser.add_argument('--dry-run', action='store_true', help='仅显示将要删除的内容，不实际执行')
    
    args = parser.parse_args()
    
    # Dry run 模式
    if args.dry_run:
        print("=" * 60)
        print("DRY RUN 模式 - 仅显示将要删除的内容")
        print("=" * 60)
        
        # 统计数据
        docs = await DocumentDB.list()
        print(f"\n数据库文档记录: {len(docs)} 条")
        
        docs_collection = get_documents_collection()
        print(f"文档向量数据: {docs_collection.count()} 条")
        
        if args.include_conversations:
            convs_collection = get_conversations_collection()
            print(f"对话向量数据: {convs_collection.count()} 条")
        
        db = get_mongo_db()
        if db:
            collection = db["keyword_index"]
            count = await collection.count_documents({})
            print(f"关键词索引: {count} 条")
        
        upload_dir = Path("data/uploads")
        if upload_dir.exists():
            files = list(upload_dir.glob("*"))
            count = len([f for f in files if f.is_file()])
            print(f"上传的文件: {count} 个")
        
        print("\n要实际执行删除，请移除 --dry-run 参数")
        print("注意：默认会删除上传的文件，使用 --keep-files 可以保留")
        return
    
    # 显示警告
    print("=" * 60)
    print("⚠️  警告：此操作将删除所有知识库数据！")
    print("=" * 60)
    print("\n将要删除:")
    print("  - 所有文档记录（数据库）")
    print("  - 所有向量数据（ChromaDB）")
    print("  - 所有关键词索引（MongoDB）")
    print("  - 所有上传的文件")
    
    if args.include_conversations:
        print("  - 所有对话历史")
    
    if args.complete_reset:
        print("  - ChromaDB 完全重置")
    
    if args.keep_files:
        print("\n  注意：将保留上传的文件（不推荐，可能导致数据不一致）")
    
    print("\n此操作不可逆！")
    print("⚠️  清除后需要重启后端服务！")
    
    # 确认
    if not args.yes:
        print("\n请输入 'yes' 确认删除，或输入其他内容取消:")
        confirmation = input("> ").strip().lower()
        
        if confirmation != 'yes':
            print("\n操作已取消")
            return
    
    # 执行清除
    await clear_all_data(
        include_conversations=args.include_conversations,
        include_files=not args.keep_files,  # 默认删除文件，除非指定 --keep-files
        complete_reset=args.complete_reset
    )


if __name__ == "__main__":
    asyncio.run(confirm_and_clear())
