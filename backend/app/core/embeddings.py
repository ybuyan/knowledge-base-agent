from app.config import settings
from typing import List, Optional
import httpx
import logging

from app.core.cache import embedding_cache

logger = logging.getLogger(__name__)

_embeddings_instance: Optional["EmbeddingsWrapper"] = None


def get_embeddings() -> "EmbeddingsWrapper":
    global _embeddings_instance
    if _embeddings_instance is None:
        _embeddings_instance = EmbeddingsWrapper(
            api_key=settings.embedding_api_key,
            model=settings.embedding_model,
            base_url=settings.llm_base_url
        )
    return _embeddings_instance


class EmbeddingsWrapper:
    _client: Optional[httpx.AsyncClient] = None
    
    def __init__(self, api_key: str, model: str, base_url: str):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
    
    @classmethod
    async def _get_client(cls) -> httpx.AsyncClient:
        if cls._client is None or cls._client.is_closed:
            cls._client = httpx.AsyncClient(
                timeout=60.0,
                verify=False,
            )
        return cls._client
    
    async def aembed_query(self, text: str) -> List[float]:
        cached = embedding_cache.get(text)
        if cached is not None:
            return cached
        
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
        
        embedding_cache.set(text, embedding)
        return embedding
    
    async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
        results = []
        uncached_texts = []
        uncached_indices = []
        
        for i, text in enumerate(texts):
            cached = embedding_cache.get(text)
            if cached is not None:
                results.append((i, cached))
            else:
                uncached_texts.append(text)
                uncached_indices.append(i)
        
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
            
            for idx, item in enumerate(data["data"]):
                embedding = item["embedding"]
                text_idx = uncached_indices[idx]
                results.append((text_idx, embedding))
                embedding_cache.set(uncached_texts[idx], embedding)
        
        results.sort(key=lambda x: x[0])
        return [embedding for _, embedding in results]
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Synchronous version for batch processing"""
        import httpx
        
        results = []
        uncached_texts = []
        uncached_indices = []
        
        # Check cache first
        for i, text in enumerate(texts):
            cached = embedding_cache.get(text)
            if cached is not None:
                results.append((i, cached))
            else:
                uncached_texts.append(text)
                uncached_indices.append(i)
        
        if uncached_texts:
            # Use synchronous HTTP client
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
        
        results.sort(key=lambda x: x[0])
        return [embedding for _, embedding in results]
    
    @classmethod
    async def close(cls):
        if cls._client is not None and not cls._client.is_closed:
            await cls._client.aclose()
            cls._client = None
            logger.info("Embedding HTTP客户端已关闭")


async def embed_texts(texts: List[str]) -> List[List[float]]:
    embeddings = get_embeddings()
    return await embeddings.aembed_documents(texts)


async def embed_query(query: str) -> List[float]:
    embeddings = get_embeddings()
    return await embeddings.aembed_query(query)


async def test_embedding_connection() -> dict:
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
    return embedding_cache.stats()
