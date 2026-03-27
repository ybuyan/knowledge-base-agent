from typing import Dict, Any, List
from app.skills.base import BaseProcessor, ProcessorRegistry
from app.core.chroma import get_documents_collection, get_conversations_collection


@ProcessorRegistry.register("VectorRetriever")
class VectorRetriever(BaseProcessor):
    
    @property
    def name(self) -> str:
        return "VectorRetriever"
    
    async def process(self, context: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """
        从向量数据库中检索相关文档或对话
        
        该方法使用向量相似度检索从ChromaDB中查找与查询最相关的内容。
        支持从documents集合（知识库文档）或conversations集合（历史对话）中检索。
        
        Args:
            context: 上下文字典，必须包含:
                - query_embedding: 查询的向量表示（由EmbeddingProcessor生成）
            params: 参数字典，可选参数:
                - collection: 集合名称，"documents"（知识库）或"conversations"（对话历史），默认"documents"
                - top_k: 返回的最相关结果数量，默认5
                - score_threshold: 距离阈值，用于过滤低相似度结果，默认0.0（不过滤）
        
        Returns:
            Dict[str, Any]: 包含检索结果的字典
                - retrieved_{collection_name}: 检索到的文档列表，每个文档包含:
                    - content: 文档内容文本
                    - metadata: 文档元数据（如document_id, filename, chunk_index等）
                    - score: 相似度分数（ChromaDB距离，越小越相似）
        
        Raises:
            ValueError: 当context中缺少query_embedding时抛出
        
        Note:
            - ChromaDB使用距离度量（如cosine distance），距离越小表示越相似
            - score_threshold为0.0时不进行过滤，返回所有top_k结果
            - score_threshold > 0时，只返回距离 <= threshold的结果
            - 返回的key名称动态生成：retrieved_documents 或 retrieved_conversations
        
        Example:
            >>> context = {"query_embedding": [0.1, 0.2, ...]}
            >>> params = {"collection": "documents", "top_k": 5, "score_threshold": 0.7}
            >>> result = await processor.process(context, params)
            >>> # result = {
            >>> #     "retrieved_documents": [
            >>> #         {"content": "年假是...", "metadata": {...}, "score": 0.15},
            >>> #         {"content": "病假是...", "metadata": {...}, "score": 0.23},
            >>> #         ...
            >>> #     ]
            >>> # }
        """
        # 1. 获取参数
        collection_name = params.get("collection", "documents")
        top_k = params.get("top_k", 5)
        score_threshold = params.get("score_threshold", 0.0)
        
        # 2. 验证必需的查询向量
        query_embedding = context.get("query_embedding")
        if not query_embedding:
            raise ValueError("query_embedding is required")
        
        # 3. 根据集合名称获取对应的ChromaDB集合
        if collection_name == "documents":
            collection = get_documents_collection()  # 知识库文档集合
        else:
            collection = get_conversations_collection()  # 历史对话集合
        
        # 4. 执行向量相似度检索
        results = collection.query(
            query_embeddings=[query_embedding],  # 查询向量（必须是列表格式）
            n_results=top_k  # 返回最相似的top_k个结果
        )
        
        # 5. 处理检索结果
        retrieved_docs = []
        if results["documents"]:
            # 遍历检索到的每个文档
            for i, doc in enumerate(results["documents"][0]):
                # 提取元数据（如document_id, filename等）
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                # 提取距离分数（ChromaDB返回的是距离，不是相似度）
                distance = results["distances"][0][i] if results["distances"] else 0
                
                # 6. 根据阈值过滤结果
                # ChromaDB距离越小越相似，所以使用 <= 判断
                # score_threshold=0.0 表示不过滤，返回所有结果
                if distance <= score_threshold or score_threshold == 0.0:
                    retrieved_docs.append({
                        "content": doc,  # 文档内容
                        "metadata": metadata,  # 文档元数据
                        "score": distance  # 相似度分数（距离）
                    })
        
        # 7. 返回结果，key名称动态生成（如retrieved_documents或retrieved_conversations）
        return {f"retrieved_{collection_name}": retrieved_docs}
