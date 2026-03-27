import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_embeddings():
    mock = MagicMock()
    mock.aembed_query = AsyncMock(return_value=[0.1] * 1536)
    mock.aembed_documents = AsyncMock(return_value=[[0.1] * 1536])
    return mock


@pytest.fixture
def mock_chroma_collection():
    mock = MagicMock()
    mock.query.return_value = {
        "ids": [["doc1", "doc2"]],
        "documents": [["测试内容1", "测试内容2"]],
        "metadatas": [[{"source": "test1"}, {"source": "test2"}]],
        "distances": [[0.1, 0.2]]
    }
    mock.add = MagicMock()
    mock.count.return_value = 10
    return mock


@pytest.fixture
def mock_mongodb():
    mock_db = MagicMock()
    mock_db.document_status = MagicMock()
    mock_db.document_status.find_one = AsyncMock(return_value=None)
    mock_db.document_status.update_one = AsyncMock()
    mock_db.document_status.delete_one = AsyncMock()
    mock_db.document_status.count_documents = AsyncMock(return_value=0)
    mock_db.document_status.find = MagicMock()
    return mock_db


@pytest.fixture
def mock_llm():
    mock = MagicMock()
    
    async def mock_stream(messages):
        for chunk in ["这是", "测试", "回答"]:
            mock_chunk = MagicMock()
            mock_chunk.content = chunk
            yield mock_chunk
    
    mock.astream = mock_stream
    mock.ainvoke = AsyncMock(return_value=MagicMock(content="测试回答"))
    return mock


@pytest.fixture
def mock_settings():
    mock = MagicMock()
    mock.app_env = "test"
    mock.app_debug = True
    mock.secret_key = "test-secret-key-for-testing-32ch"
    mock.dashscope_api_key = "test_api_key"
    mock.llm_api_key = "test_api_key"
    mock.llm_base_url = "https://test.api.com/v1"
    mock.llm_model = "test-model"
    mock.embedding_model = "test-embedding"
    mock.mongo_url = "mongodb://localhost:27017"
    mock.mongo_db_name = "test-db"
    mock.chroma_persist_dir = "./test_data/chroma"
    mock.allowed_origins = ["http://localhost:3000"]
    return mock


@pytest.fixture
def sample_document_status():
    from app.models.document import DocumentStatusModel
    from datetime import datetime
    return DocumentStatusModel(
        id="test-doc-id",
        filename="test.pdf",
        status="READY",
        size=1024,
        uploadTime=datetime.now().isoformat(),
        file_path="/tmp/test.pdf",
        chunk_count=5
    )
