from app.config import settings
from typing import List, Optional
import httpx
import logging

from app.core.cache import embedding_cache

logger = logging.getLogger(__name__)

_embeddings_instance: Optional["EmbeddingsWrapper"] = None


def get_embeddings() -> "EmbeddingsWrapper":
    """
    获取全局 EmbeddingsWrapper 实例（单例模式）
    
    Returns:
        EmbeddingsWrapper: 向量化服务实例
    """
    global _embeddings_instance
    if _embeddings_instance is None:
        _embeddings_instance = EmbeddingsWrapper(
            api_key=settings.embedding_api_key,
            model=settings.embedding_model,
            base_url=settings.llm_base_url
        )
    return _embeddings_instance


class EmbeddingsWrapper:
    """
    向量化服务封装类
    
    封装了对 Embedding API 的调用，支持同步和异步操作，
    并集成了缓存机制以提高性能。
    """
    _client: Optional[httpx.AsyncClient] = None
    
    def __init__(self, api_key: str, model: str, base_url: str):
        """
        初始化向量化服务
        
        Args:
            api_key: API 密钥
            model: 模型名称
            base_url: API 基础 URL
        """
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
    
    @classmethod
    async def _get_client(cls) -> httpx.AsyncClient:
        """
        获取或创建 HTTP 客户端
        
        Returns:
            httpx.AsyncClient: 异步 HTTP 客户端
        """
        if cls._client is None or cls._client.is_closed:
            cls._client = httpx.AsyncClient(
                timeout=60.0,
                verify=False,
            )
        return cls._client
    
    async def aembed_query(self, text: str) -> List[float]:
        """
        异步向量化单条文本
        
        Args:
            text: 要向量化的文本
            
        Returns:
            List[float]: 文本的向量表示
        """
        # 检查缓存
        cached = embedding_cache.get(text)
        if cached is not None:
            return cached
        
        # 调用 API
        client = await self._get_client()
        url = f"{self.base_url}/embeddings"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "input": text,
            "encoding_format": "float"
        }
        
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        embedding = data["data"][0]["embedding"]
        
        # 缓存结果
        embedding_cache.set(text, embedding)
        return embedding
    
    async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        异步向量化多条文本（批量处理）
        
        Args:
            texts: 要向量化的文本列表
            
        Returns:
            List[List[float]]: 文本列表的向量表示
        """
        results = []
        uncached_texts = []
        uncached_indices = []
        
        # 检查缓存，分离已缓存和未缓存的文本
        for i, text in enumerate(texts):
            cached = embedding_cache.get(text)
            if cached is not None:
                results.append((i, cached))
            else:
                uncached_texts.append(text)
                uncached_indices.append(i)
        
        # 处理未缓存的文本
        if uncached_texts:
            client = await self._get_client()
            url = f"{self.base_url}/embeddings"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": self.model,
                "input": uncached_texts,
                "encoding_format": "float"
            }
            
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            # 处理 API 返回结果
            for idx, item in enumerate(data["data"]):
                embedding = item["embedding"]
                text_idx = uncached_indices[idx]
                results.append((text_idx, embedding))
                embedding_cache.set(uncached_texts[idx], embedding)
        
        # 按原始顺序排序
        results.sort(key=lambda x: x[0])
        return [embedding for _, embedding in results]
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        同步向量化多条文本（用于批处理）
        
        Args:
            texts: 要向量化的文本列表
            
        Returns:
            List[List[float]]: 文本列表的向量表示
        """
        import httpx
        
        results = []
        uncached_texts = []
        uncached_indices = []
        
        # 检查缓存
        for i, text in enumerate(texts):
            cached = embedding_cache.get(text)
            if cached is not None:
                results.append((i, cached))
            else:
                uncached_texts.append(text)
                uncached_indices.append(i)
        
        # 处理未缓存的文本
        if uncached_texts:
            # 使用同步 HTTP 客户端
            with httpx.Client(timeout=60.0, verify=False) as client:
                url = f"{self.base_url}/embeddings"
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": self.model,
                    "input": uncached_texts,
                    "encoding_format": "float"
                }
                
                response = client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                
                for idx, item in enumerate(data["data"]):
                    embedding = item["embedding"]
                    text_idx = uncached_indices[idx]
                    results.append((text_idx, embedding))
                    embedding_cache.set(uncached_texts[idx], embedding)
        
        # 按原始顺序排序
        results.sort(key=lambda x: x[0])
        return [embedding for _, embedding in results]
    
    @classmethod
    async def close(cls):
        """
        关闭 HTTP 客户端
        """
        if cls._client is not None and not cls._client.is_closed:
            await cls._client.aclose()
            cls._client = None
            logger.info("Embedding HTTP客户端已关闭")


async def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    便捷函数：异步向量化多条文本
    
    Args:
        texts: 要向量化的文本列表
        
    Returns:
        List[List[float]]: 文本列表的向量表示
    """
    embeddings = get_embeddings()
    return await embeddings.aembed_documents(texts)


async def embed_query(query: str) -> List[float]:
    """
    便捷函数：异步向量化单条查询文本
    
    Args:
        query: 要向量化的查询文本
        
    Returns:
        List[float]: 查询文本的向量表示
    """
    embeddings = get_embeddings()
    return await embeddings.aembed_query(query)


async def test_embedding_connection() -> dict:
    """
    测试 Embedding API 连接
    
    Returns:
        dict: 连接测试结果
    """
    try:
        embeddings = get_embeddings()
        result = await embeddings.aembed_query("测试文本")
        return {
            "status": "success",
            "message": "Embedding 连接成功",
            "dimension": len(result),
            "model": embeddings.model,
            "cache_stats": embedding_cache.stats()
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Embedding 连接失败: {str(e)}"
        }


def get_cache_stats() -> dict:
    """
    获取缓存统计信息
    
    Returns:
        dict: 缓存统计数据
    """
    return embedding_cache.stats()
