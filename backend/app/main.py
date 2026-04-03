from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import settings
from app.core.chroma import init_chroma
from app.core.mongodb import connect_to_mongo, close_mongo_connection
from app.core.exceptions import AppException
from app.api.routes import documents, chat, health, constraints, prompts, links, auth, process
from app.api.dependencies import require_hr
from app.mcp.router import router as mcp_router
import logging
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="公司制度问答助手 API",
    description="基于 RAG 的智能问答系统",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Trace-ID"],
)


@app.middleware("http")
async def add_trace_id(request: Request, call_next):
    trace_id = request.headers.get("X-Trace-ID", str(uuid.uuid4()))
    request.state.trace_id = trace_id
    
    response = await call_next(request)
    response.headers["X-Trace-ID"] = trace_id
    return response


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    trace_id = getattr(request.state, "trace_id", "-")
    logger.error(f"[{trace_id}] {exc.code}: {exc.message}")
    
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "trace_id": trace_id
            }
        }
    )


@app.on_event("startup")
async def startup_event():
    logger.info("初始化 ChromaDB...")
    init_chroma()
    logger.info("ChromaDB 初始化完成")
    
    logger.info("初始化 MongoDB...")
    await connect_to_mongo(settings.mongo_url, settings.mongo_db_name)
    
    # 先注册工具（必须在 QAAgent 实例化之前，否则 ToolRegistry 为空）
    from app.tools.implementations import (
        SearchKnowledgeTool, SystemStatusTool,
        ListDocumentsTool, GetDocumentInfoTool,
        IntroduceAssistantTool, GetAssistantStatusTool
    )
    
    from app.skills.registry import ProcessorRegistry
    from app.agents.implementations import DocumentAgent, QAAgent, MemoryAgent, OrchestratorAgent
    from app.agents.implementations.process_agent import ProcessAgent
    from app.agents import agent_engine
    
    agent_engine.register(DocumentAgent())
    agent_engine.register(QAAgent())
    agent_engine.register(MemoryAgent())
    agent_engine.register(OrchestratorAgent())
    agent_engine.register(ProcessAgent())
    
    logger.info("处理器已注册: " + str(ProcessorRegistry.list_all()))
    logger.info("Agents 已注册: %s", agent_engine.list_all())
    
    # Start background scanner for server-uploaded files
    from app.api.routes.documents import start_background_scanner
    start_background_scanner()

    # 注册 MCP 服务器
    from app.mcp.knowledge_server import KnowledgeMCPServer
    from app.mcp.document_server import DocumentMCPServer
    from app.mcp.base import MCPServerRegistry
    # Servers are auto-registered when modules are imported (via MCPServerRegistry.register at module level)
    logger.info("MCP 服务器已注册: %s", MCPServerRegistry.list_all())


@app.on_event("shutdown")
async def shutdown_event():
    await close_mongo_connection()
    logger.info("应用关闭完成")


@app.get("/")
async def root():
    return {
        "message": "公司制度问答助手 API",
        "version": "1.0.0",
        "docs": "/docs"
    }


app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"], dependencies=[Depends(require_hr)])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(constraints.router, prefix="/api/constraints", tags=["constraints"], dependencies=[Depends(require_hr)])
app.include_router(links.router, prefix="/api/links", tags=["links"])
app.include_router(prompts.router, prefix="/api", tags=["prompts"])
app.include_router(process.router, prefix="/api/process", tags=["process"])
app.include_router(mcp_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    )
