import uuid
from typing import Dict, Any, List
from app.skills.base import BaseProcessor, ProcessorRegistry
from app.core.chroma import get_documents_collection, get_conversations_collection


@ProcessorRegistry.register("VectorStore")
class VectorStore(BaseProcessor):
    
    @property
    def name(self) -> str:
        return "VectorStore"
    
    async def process(self, context: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        collection_name = params.get("collection", "documents")
        
        if collection_name == "documents":
            collection = get_documents_collection()
            return await self._store_documents(context, collection)
        else:
            collection = get_conversations_collection()
            return await self._store_conversation(context, collection)
    
    async def _store_documents(self, context: Dict[str, Any], collection) -> Dict[str, Any]:
        chunks = context.get("chunks", [])
        chunk_embeddings = context.get("chunk_embeddings", [])
        document_id = context.get("document_id", str(uuid.uuid4()))
        document_name = context.get("document_name", "unknown")
        
        if not chunks or not chunk_embeddings:
            return {"stored_count": 0}
        
        ids = [f"{document_id}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [
            {
                "document_id": document_id,
                "document_name": document_name,
                "chunk_index": i
            }
            for i in range(len(chunks))
        ]
        
        collection.add(
            ids=ids,
            embeddings=chunk_embeddings,
            documents=chunks,
            metadatas=metadatas
        )
        
        return {
            "stored_count": len(chunks),
            "document_id": document_id
        }
    
    async def _store_conversation(self, context: Dict[str, Any], collection) -> Dict[str, Any]:
        question = context.get("question", context.get("query", ""))
        answer = context.get("answer", "")
        session_id = context.get("session_id", str(uuid.uuid4()))
        
        from app.core.embeddings import get_embeddings
        embeddings = get_embeddings()
        
        conv_id = str(uuid.uuid4())
        conv_text = f"Q: {question}\nA: {answer}"
        conv_embedding = await embeddings.aembed_query(conv_text)
        
        collection.add(
            ids=[conv_id],
            embeddings=[conv_embedding],
            documents=[conv_text],
            metadatas=[{
                "session_id": session_id,
                "type": "qa_pair"
            }]
        )
        
        return {
            "conversation_id": conv_id,
            "session_id": session_id
        }
