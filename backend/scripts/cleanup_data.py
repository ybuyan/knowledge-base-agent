"""
清理所有数据脚本
- 删除ChromaDB向量数据库
- 删除MongoDB集合数据
- 删除上传的文件
"""

import asyncio
import os
import shutil
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

UPLOAD_DIR = "data/uploads"
CHROMA_DIR = "data/chroma"


async def cleanup_mongodb():
    """清理MongoDB数据"""
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        
        # Connect to MongoDB directly
        client = AsyncIOMotorClient("mongodb://localhost:27017")
        database = client["agent"]
        
        # Get all collections
        collections = await database.list_collection_names()
        logger.info(f"Found collections: {collections}")
        
        # Drop each collection
        for collection_name in collections:
            await database.drop_collection(collection_name)
            logger.info(f"Dropped collection: {collection_name}")
        
        client.close()
        logger.info("MongoDB cleanup completed")
        
    except Exception as e:
        logger.error(f"MongoDB cleanup error: {e}")


def cleanup_chromadb():
    """清理ChromaDB向量数据库"""
    try:
        if os.path.exists(CHROMA_DIR):
            shutil.rmtree(CHROMA_DIR)
            logger.info(f"Deleted ChromaDB directory: {CHROMA_DIR}")
        else:
            logger.info(f"ChromaDB directory not found: {CHROMA_DIR}")
        
        # Recreate empty directory
        os.makedirs(CHROMA_DIR, exist_ok=True)
        logger.info("Recreated empty ChromaDB directory")
        
    except Exception as e:
        logger.error(f"ChromaDB cleanup error: {e}")


def cleanup_uploads():
    """清理上传的文件"""
    try:
        if os.path.exists(UPLOAD_DIR):
            # Delete all files in upload directory
            for filename in os.listdir(UPLOAD_DIR):
                file_path = os.path.join(UPLOAD_DIR, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    logger.info(f"Deleted file: {filename}")
            
            logger.info("Upload directory cleanup completed")
        else:
            logger.info(f"Upload directory not found: {UPLOAD_DIR}")
        
        # Recreate empty directory
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        logger.info("Recreated empty upload directory")
        
    except Exception as e:
        logger.error(f"Upload cleanup error: {e}")


async def main():
    """主清理函数"""
    logger.info("=" * 50)
    logger.info("开始清理所有数据...")
    logger.info("=" * 50)
    
    # 1. 清理MongoDB
    logger.info("\n[1/3] 清理 MongoDB...")
    await cleanup_mongodb()
    
    # 2. 清理ChromaDB
    logger.info("\n[2/3] 清理 ChromaDB...")
    cleanup_chromadb()
    
    # 3. 清理上传文件
    logger.info("\n[3/3] 清理上传文件...")
    cleanup_uploads()
    
    logger.info("\n" + "=" * 50)
    logger.info("所有数据清理完成！")
    logger.info("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
