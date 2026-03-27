# Settings测试快速参考

## 快速开始

### 运行所有测试
```bash
cd backend
python tests/settings/run_settings_tests.py
```

### 运行特定测试
```bash
# Settings类测试
python -m pytest tests/settings/test_settings.py -v

# ConfigLoader测试
python -m pytest tests/settings/test_config_loader.py -v
```

## 常用测试命令

### 按类别运行
```bash
# API Key配置测试
pytest tests/settings/test_settings.py::TestAPIKeyConfiguration -v

# LLM配置测试
pytest tests/settings/test_settings.py::TestLLMConfiguration -v

# CORS配置测试
pytest tests/settings/test_settings.py::TestCORSConfiguration -v

# 配置加载器测试
pytest tests/settings/test_config_loader.py::TestConfigLoader -v
```

### 运行单个测试
```bash
# 测试默认配置
pytest tests/settings/test_settings.py::TestSettingsBasic::test_default_settings -v

# 测试API Key验证
pytest tests/settings/test_settings.py::TestAPIKeyConfiguration::test_api_key_min_length -v

# 测试配置加载
pytest tests/settings/test_config_loader.py::TestConfigLoader::test_load_settings_config -v
```

### 调试选项
```bash
# 显示print输出
pytest tests/settings/test_settings.py -v -s

# 遇到第一个失败就停止
pytest tests/settings/test_settings.py -v -x

# 显示详细的traceback
pytest tests/settings/test_settings.py -v --tb=long

# 只运行失败的测试
pytest tests/settings/test_settings.py -v --lf
```

## 测试覆盖的配置项

### Settings类 (app/config.py)
| 配置项 | 测试类 | 测试方法 |
|--------|--------|----------|
| app_env | TestSettingsBasic | test_default_settings |
| app_debug | TestSettingsBasic | test_default_settings |
| secret_key | TestSettingsBasic | test_secret_key_validation |
| dashscope_api_key | TestAPIKeyConfiguration | test_dashscope_api_key |
| llm_api_key | TestAPIKeyConfiguration | test_llm_api_key_fallback |
| llm_base_url | TestLLMConfiguration | test_llm_base_url |
| llm_model | TestLLMConfiguration | test_llm_model_configuration |
| embedding_model | TestLLMConfiguration | test_embedding_model_configuration |
| chroma_persist_dir | TestDataStorageConfiguration | test_chroma_persist_dir |
| mongo_url | TestDataStorageConfiguration | test_mongo_configuration |
| mongo_db_name | TestDataStorageConfiguration | test_mongo_configuration |
| memory_max_tokens | TestMemoryConfiguration | test_memory_max_tokens |
| memory_max_sessions | TestMemoryConfiguration | test_memory_max_sessions |
| cors_origins | TestCORSConfiguration | test_cors_origins_default |

### ConfigLoader类 (app/core/config_loader.py)
| 方法 | 测试类 | 测试方法 |
|------|--------|----------|
| load() | TestConfigLoader | test_load_settings_config |
| get_setting() | TestConfigLoader | test_get_setting |
| reload() | TestConfigLoader | test_reload_config |
| 单例模式 | TestConfigLoader | test_singleton_pattern |
| 配置缓存 | TestConfigLoader | test_config_caching |

### 配置文件
| 文件 | 测试类 | 测试方法 |
|------|--------|----------|
| core/config.json | TestConfigIntegration | test_config_consistency |
| agents/config.json | TestAgentsConfig | test_agents_config_structure |
| skills/config.json | TestSkillsConfig | test_skills_config_structure |
| tools/config.json | TestToolsConfig | test_tools_config_structure |
| prompts/config.json | TestPromptsConfig | test_prompts_config_structure |

## 环境变量

测试使用的环境变量（可选）：
```bash
APP_ENV=development
APP_DEBUG=true
SECRET_KEY=your-secret-key-32-characters-min
DASHSCOPE_API_KEY=your-api-key
LLM_MODEL=qwen-plus
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
EMBEDDING_MODEL=text-embedding-v3
MONGO_URL=mongodb://localhost:27017
MONGO_DB_NAME=agent
CHROMA_PERSIST_DIR=./data/chroma
MEMORY_MAX_TOKENS=4000
MEMORY_MAX_SESSIONS=1000
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

## 故障排除

### 问题: ModuleNotFoundError: No module named 'backend'
**解决方案**: 从backend目录运行测试
```bash
cd backend
python -m pytest tests/settings/test_settings.py
```

### 问题: ValidationError: SECRET_KEY必须设置
**解决方案**: 在.env文件中设置有效的SECRET_KEY（至少32字符）
```bash
SECRET_KEY=your-secure-secret-key-32-chars-min
```

### 问题: FileNotFoundError: config.json not found
**解决方案**: 确保所有配置文件都存在
```bash
ls backend/app/core/config.json
ls backend/app/agents/config.json
ls backend/app/skills/config.json
ls backend/app/tools/config.json
ls backend/app/prompts/config.json
```

### 问题: 测试失败：配置值不匹配
**解决方案**: 检查.env文件中的配置，确保环境变量没有意外覆盖
```bash
cat backend/.env
```

## 添加新测试

### 1. 添加新的配置项测试
```python
# 在 test_settings.py 中添加
def test_new_config_item(self):
    """测试新配置项"""
    settings = Settings(new_config="value")
    assert settings.new_config == "value"
```

### 2. 添加新的验证测试
```python
def test_new_validation(self):
    """测试新验证规则"""
    with pytest.raises(ValidationError):
        Settings(new_config="invalid")
```

### 3. 添加新的配置文件测试
```python
# 在 test_config_loader.py 中添加
def test_new_config_file(self):
    """测试新配置文件"""
    config_path = Path(__file__).parent.parent.parent / "app" / "new" / "config.json"
    assert config_path.exists()
```

## 测试最佳实践

1. **使用fixtures**: 使用pytest fixtures进行测试隔离
2. **使用monkeypatch**: 避免环境变量污染
3. **测试边界条件**: 测试最小值、最大值、空值等
4. **测试错误情况**: 使用pytest.raises测试异常
5. **保持测试独立**: 每个测试应该独立运行
6. **使用描述性名称**: 测试方法名应该清楚描述测试内容

## 相关文档

- [SETTINGS_TESTS_README.md](./SETTINGS_TESTS_README.md) - 完整测试文档
- [SETTINGS_TEST_SUMMARY.md](./SETTINGS_TEST_SUMMARY.md) - 测试总结报告
- [../app/config.py](../app/config.py) - Settings类源码
- [../app/core/config_loader.py](../app/core/config_loader.py) - ConfigLoader源码

## 联系方式

如有问题或建议，请联系开发团队。
