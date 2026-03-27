from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

_model: Optional[Any] = None


def _load_model(model_name: str):
    global _model
    if _model is None:
        try:
            from sentence_transformers import CrossEncoder
            logger.info(f"加载重排序模型: {model_name}")
            _model = CrossEncoder(model_name)
            logger.info("重排序模型加载成功")
        except ImportError:
            logger.warning("sentence_transformers 未安装，重排序功能不可用")
            return None
        except Exception as e:
            logger.error(f"加载重排序模型失败: {e}")
            return None
    return _model


class Reranker:
    
    def __init__(self, model_name: str = "BAAI/bge-reranker-base"):
        self.model_name = model_name
        self._model = None
    
    @property
    def model(self):
        if self._model is None:
            self._model = _load_model(self.model_name)
        return self._model
    
    def is_available(self) -> bool:
        return self.model is not None
    
    def rerank(
        self, 
        query: str, 
        documents: List[Dict[str, Any]], 
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        if not documents:
            return []
        
        if not self.is_available():
            logger.warning("重排序模型不可用，返回原始文档")
            return documents[:top_k]
        
        try:
            pairs = [[query, doc["content"]] for doc in documents]
            scores = self.model.predict(pairs)
            
            ranked = sorted(
                zip(documents, scores), 
                key=lambda x: x[1], 
                reverse=True
            )
            
            result = []
            for doc, score in ranked[:top_k]:
                result.append({
                    **doc,
                    "rerank_score": float(score)
                })
            
            logger.debug(f"重排序完成，返回 {len(result)} 个文档")
            return result
            
        except Exception as e:
            logger.error(f"重排序失败: {e}")
            return documents[:top_k]


_reranker_instance: Optional[Reranker] = None


def get_reranker(model_name: str = "BAAI/bge-reranker-base") -> Reranker:
    global _reranker_instance
    if _reranker_instance is None:
        _reranker_instance = Reranker(model_name)
    return _reranker_instance
