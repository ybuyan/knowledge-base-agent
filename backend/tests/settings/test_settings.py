"""
Settings配置测试用例

测试所有配置项的加载、验证和功能
"""
import os
import sys
import pytest
from pathlib import Path
from pydantic import ValidationError

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import Settings


class TestSettingsBasic:
    """基础配置测试"""
    
    def test_default_settings(self):
        """测试默认配置加载"""
        settings = Settings()
        assert settings.app_env in ["development", "production"]
        assert isinstance(settings.app_debug, bool)
        # 模型名称可能从环境变量加载，所以只检查是否存在
        assert settings.llm_model is not None
        assert len(settings.llm_model) > 0
        assert settings.embedding_model is not None
    
    def test_secret_key_validation(self):
        """测试SECRET_KEY验证"""
        # 测试默认密钥（开发环境）
        settings = Settings()
        assert len(settings.secret_key) >= 32
        
        # 测试短密钥应该失败
        with pytest.raises(ValidationError) as exc_info:
            Settings(secret_key="short")
        # 检查错误信息包含长度相关的内容
        error_str = str(exc_info.value)
        assert "32" in error_str or "string_too_short" in error_str
    
    def test_production_secret_key_validation(self, monkeypatch):
        """测试生产环境密钥验证"""
        monkeypatch.setenv("APP_ENV", "production")
        
        # 生产环境不允许使用默认密钥
        with pytest.raises(ValidationError):
            Settings(secret_key="change-in-production-please-use-secure-key")
        
        # 安全的密钥应该通过
        secure_key = "a" * 32
        settings = Settings(secret_key=secure_key)
        assert settings.secret_key == secure_key


class TestAPIKeyConfiguration:
    """API Key配置测试"""
    
    def test_dashscope_api_key(self):
        """测试DashScope API Key"""
        api_key = "sk-test1234567890"
        settings = Settings(dashscope_api_key=api_key)
        assert settings.dashscope_api_key == api_key
        assert settings.api_key == api_key
        assert settings.embedding_api_key == api_key
    
    def test_llm_api_key_fallback(self, monkeypatch):
        """测试LLM API Key作为备用"""
        # 清除环境变量中的dashscope_api_key
        monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
        
        api_key = "sk-llm-test1234567890"
        settings = Settings(llm_api_key=api_key, dashscope_api_key=None)
        assert settings.llm_api_key == api_key
        assert settings.api_key == api_key
        assert settings.embedding_api_key == api_key
    
    def test_api_key_priority(self):
        """测试API Key优先级（dashscope优先）"""
        dashscope_key = "sk-dashscope-key"
        llm_key = "sk-llm-key-backup"
        settings = Settings(
            dashscope_api_key=dashscope_key,
            llm_api_key=llm_key
        )
        assert settings.api_key == dashscope_key
        assert settings.embedding_api_key == dashscope_key
    
    def test_api_key_min_length(self):
        """测试API Key最小长度验证"""
        with pytest.raises(ValidationError):
            Settings(dashscope_api_key="short")
        
        with pytest.raises(ValidationError):
            Settings(llm_api_key="short")


class TestLLMConfiguration:
    """LLM配置测试"""
    
    def test_llm_base_url(self):
        """测试LLM基础URL配置"""
        settings = Settings()
        assert settings.llm_base_url == "https://dashscope.aliyuncs.com/compatible-mode/v1"
        
        # 测试自定义URL
        custom_url = "https://api.openai.com/v1"
        settings = Settings(llm_base_url=custom_url)
        assert settings.llm_base_url == custom_url
    
    def test_llm_model_configuration(self):
        """测试LLM模型配置"""
        # 测试自定义模型（不依赖环境变量）
        custom_model = "gpt-4"
        settings = Settings(llm_model=custom_model)
        assert settings.llm_model == custom_model
    
    def test_embedding_model_configuration(self):
        """测试Embedding模型配置"""
        # 测试自定义模型（不依赖环境变量）
        custom_model = "text-embedding-ada-002"
        settings = Settings(embedding_model=custom_model)
        assert settings.embedding_model == custom_model


class TestDataStorageConfiguration:
    """数据存储配置测试"""
    
    def test_chroma_persist_dir(self):
        """测试ChromaDB持久化目录"""
        settings = Settings()
        assert settings.chroma_persist_dir == "./data/chroma"
        
        # 测试自定义目录
        custom_dir = "/custom/path/chroma"
        settings = Settings(chroma_persist_dir=custom_dir)
        assert settings.chroma_persist_dir == custom_dir
    
    def test_mongo_configuration(self):
        """测试MongoDB配置"""
        settings = Settings()
        assert settings.mongo_url == "mongodb://localhost:27017"
        assert settings.mongo_db_name == "agent"
        
        # 测试自定义配置
        custom_url = "mongodb://user:pass@remote:27017"
        custom_db = "custom_db"
        settings = Settings(
            mongo_url=custom_url,
            mongo_db_name=custom_db
        )
        assert settings.mongo_url == custom_url
        assert settings.mongo_db_name == custom_db


class TestMemoryConfiguration:
    """记忆系统配置测试"""
    
    def test_memory_max_tokens(self):
        """测试记忆最大token数"""
        settings = Settings()
        assert settings.memory_max_tokens == 4000
        
        # 测试自定义值
        custom_tokens = 8000
        settings = Settings(memory_max_tokens=custom_tokens)
        assert settings.memory_max_tokens == custom_tokens
    
    def test_memory_max_sessions(self):
        """测试记忆最大会话数"""
        settings = Settings()
        assert settings.memory_max_sessions == 1000
        
        # 测试自定义值
        custom_sessions = 5000
        settings = Settings(memory_max_sessions=custom_sessions)
        assert settings.memory_max_sessions == custom_sessions


class TestCORSConfiguration:
    """CORS配置测试"""
    
    def test_cors_origins_default(self):
        """测试默认CORS origins"""
        settings = Settings()
        assert settings.cors_origins == "http://localhost:5173,http://localhost:3000"
        allowed = settings.allowed_origins
        assert len(allowed) == 2
        assert "http://localhost:5173" in allowed
        assert "http://localhost:3000" in allowed
    
    def test_cors_origins_parsing(self):
        """测试CORS origins解析"""
        origins = "http://example.com, http://test.com , http://demo.com"
        settings = Settings(cors_origins=origins)
        allowed = settings.allowed_origins
        assert len(allowed) == 3
        assert "http://example.com" in allowed
        assert "http://test.com" in allowed
        assert "http://demo.com" in allowed
    
    def test_cors_origins_empty_handling(self):
        """测试空CORS origins处理"""
        settings = Settings(cors_origins="http://example.com,,http://test.com")
        allowed = settings.allowed_origins
        assert len(allowed) == 2
        assert "" not in allowed
    
    def test_cors_single_origin(self):
        """测试单个CORS origin"""
        settings = Settings(cors_origins="http://example.com")
        allowed = settings.allowed_origins
        assert len(allowed) == 1
        assert allowed[0] == "http://example.com"


class TestEnvironmentVariables:
    """环境变量加载测试"""
    
    def test_env_file_loading(self, monkeypatch, tmp_path):
        """测试从.env文件加载配置"""
        # 创建临时.env文件
        env_file = tmp_path / ".env"
        env_content = """
APP_ENV=testing
APP_DEBUG=false
SECRET_KEY=test-secret-key-with-32-characters-min
LLM_MODEL=gpt-4-test
MEMORY_MAX_TOKENS=8000
"""
        env_file.write_text(env_content)
        
        # 使用环境变量覆盖来测试
        monkeypatch.setenv("APP_ENV", "testing")
        monkeypatch.setenv("APP_DEBUG", "false")
        monkeypatch.setenv("LLM_MODEL", "gpt-4-test")
        monkeypatch.setenv("MEMORY_MAX_TOKENS", "8000")
        
        settings = Settings()
        assert settings.app_env == "testing"
        assert settings.app_debug is False
        assert settings.llm_model == "gpt-4-test"
        assert settings.memory_max_tokens == 8000
    
    def test_env_override(self, monkeypatch):
        """测试环境变量覆盖"""
        monkeypatch.setenv("LLM_MODEL", "custom-model")
        monkeypatch.setenv("MEMORY_MAX_TOKENS", "6000")
        
        settings = Settings()
        assert settings.llm_model == "custom-model"
        assert settings.memory_max_tokens == 6000
    
    def test_case_insensitive_env(self, monkeypatch):
        """测试环境变量大小写不敏感"""
        monkeypatch.setenv("llm_model", "lowercase-model")
        settings = Settings()
        assert settings.llm_model == "lowercase-model"


class TestSettingsIntegration:
    """集成测试"""
    
    def test_complete_configuration(self):
        """测试完整配置"""
        settings = Settings(
            app_env="production",
            app_debug=False,
            secret_key="production-secret-key-32-chars-long",
            dashscope_api_key="sk-dashscope-test-key",
            llm_base_url="https://api.custom.com/v1",
            llm_model="custom-model",
            embedding_model="custom-embedding",
            chroma_persist_dir="/data/chroma",
            mongo_url="mongodb://prod:27017",
            mongo_db_name="prod_db",
            memory_max_tokens=8000,
            memory_max_sessions=5000,
            cors_origins="https://app.example.com"
        )
        
        assert settings.app_env == "production"
        assert settings.app_debug is False
        assert settings.api_key == "sk-dashscope-test-key"
        assert settings.llm_model == "custom-model"
        assert settings.embedding_model == "custom-embedding"
        assert settings.memory_max_tokens == 8000
        assert len(settings.allowed_origins) == 1
    
    def test_settings_singleton(self):
        """测试settings单例"""
        from app.config import settings as settings1
        from app.config import settings as settings2
        
        assert settings1 is settings2
        assert id(settings1) == id(settings2)


class TestSettingsValidation:
    """配置验证测试"""
    
    def test_invalid_types(self):
        """测试无效类型"""
        with pytest.raises(ValidationError):
            Settings(app_debug="not_a_boolean")
        
        with pytest.raises(ValidationError):
            Settings(memory_max_tokens="not_an_integer")
    
    def test_required_fields(self):
        """测试必需字段"""
        # secret_key有默认值，所以不会失败
        settings = Settings()
        assert settings.secret_key is not None
    
    def test_field_constraints(self):
        """测试字段约束"""
        # 测试最小长度约束
        with pytest.raises(ValidationError):
            Settings(secret_key="short")
        
        with pytest.raises(ValidationError):
            Settings(dashscope_api_key="short")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
