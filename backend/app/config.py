from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import Optional
from pathlib import Path


class Settings(BaseSettings):
    """应用配置"""
    app_env: str = "development"
    app_debug: bool = True
    
    secret_key: str = Field(default="dev-secret-key-for-development-only-32ch", min_length=32)
    
    # API Key 配置
    dashscope_api_key: Optional[str] = Field(default=None, min_length=10)
    llm_api_key: Optional[str] = Field(default=None, min_length=10)
    
    # LLM 模型配置
    llm_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    llm_model: str = "qwen-plus"
    
    # Embedding 模型配置
    embedding_model: str = "text-embedding-v3"
    
    # 数据存储配置
    chroma_persist_dir: str = "./data/chroma"
    mongo_url: str = "mongodb://localhost:27017"
    mongo_db_name: str = "agent"
    
    # 记忆配置
    memory_max_tokens: int = 6000
    memory_max_sessions: int = 1000
    
    # CORS 配置
    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    
    @field_validator('secret_key')
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        if not v or len(v) < 32:
            raise ValueError("SECRET_KEY 必须设置，且长度不少于32个字符")
        if "change-in-production" in v.lower() or "your-secret-key" in v.lower():
            if cls._is_production():
                raise ValueError("生产环境请设置安全的SECRET_KEY，不要使用默认值")
        return v
    
    @classmethod
    def _is_production(cls) -> bool:
        import os
        return os.getenv("APP_ENV", "development") == "production"
    
    @property
    def embedding_api_key(self) -> Optional[str]:
        """获取 Embedding API Key"""
        return self.dashscope_api_key or self.llm_api_key
    
    @property
    def api_key(self) -> Optional[str]:
        """获取 LLM API Key"""
        return self.dashscope_api_key or self.llm_api_key
    
    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
    
    class Config:
        env_file = Path(__file__).parent.parent / ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()
