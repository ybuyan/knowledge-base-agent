from fastapi import APIRouter
from app.core.llm import test_llm_connection
from app.core.embeddings import test_embedding_connection
from app.core.chroma import get_chroma_stats

router = APIRouter()


@router.get("/health")
async def health_check():
    return {"status": "ok"}


@router.get("/status")
async def get_status():
    llm_result = await test_llm_connection()
    embedding_result = await test_embedding_connection()
    chroma_result = get_chroma_stats()
    
    return {
        "llm": llm_result,
        "embedding": embedding_result,
        "chroma": chroma_result
    }
