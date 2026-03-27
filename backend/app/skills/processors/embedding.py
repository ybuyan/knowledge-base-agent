from typing import Dict, Any, List
from app.skills.base import BaseProcessor, ProcessorRegistry
from app.core.embeddings import get_embeddings


@ProcessorRegistry.register("EmbeddingProcessor")
class EmbeddingProcessor(BaseProcessor):
    
    @property
    def name(self) -> str:
        return "EmbeddingProcessor"
    
    async def process(self, context: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        embeddings = get_embeddings()
        batch_size = params.get("batch_size", 10)
        
        if "query" in context:
            query_embedding = await embeddings.aembed_query(context["query"])
            return {"query_embedding": query_embedding}
        
        if "chunks" in context:
            chunks = context["chunks"]
            all_embeddings = []
            
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i+batch_size]
                batch_embeddings = await embeddings.aembed_documents(batch)
                all_embeddings.extend(batch_embeddings)
            
            return {
                "chunk_embeddings": all_embeddings,
                "document_id": context.get("document_id"),
                "document_name": context.get("document_name")
            }
        
        raise ValueError("No text to embed")
