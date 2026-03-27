# Settings配置测试文档

## 概述

本目录包含了对系统所有配置项的全面测试，确保配置系统的正确性和可靠性。

## 测试文件

### 1. test_settings.py

测试 `backend/app/config.py` 中的 Settings 类的所有功能。

#### 测试类别

##### TestSettingsBasic - 基础配置测试
- `test_default_settings`: 测试默认配置值
- `test_secret_key_validation`: 测试SECRET_KEY验证规则
- `test_production_secret_key_validation`: 测试生产环境密钥验证

##### TestAPIKeyConfiguration - API Key配置测试
- `test_dashscope_api_key`: 测试DashScope API Key配置
- `test_llm_api_key_fallback`: 测试LLM API Key作为备用
- `test_api_key_priority`: 测试API Key优先级（dashscope优先）
- `test_api_key_min_length`: 测试API Key最小长度验证

##### TestLLMConfiguration - LLM配置测试
- `test_llm_base_url`: 测试LLM基础URL配置
- `test_llm_model_configuration`: 测试LLM模型配置
- `test_embedding_model_configuration`: 测试Embedding模型配置

##### TestDataStorageConfiguration - 数据存储配置测试
- `test_chroma_persist_dir`: 测试ChromaDB持久化目录
- `test_mongo_configuration`: 测试MongoDB配置

##### TestMemoryConfiguration - 记忆系统配置测试
- `test_memory_max_tokens`: 测试记忆最大token数
- `test_memory_max_sessions`: 测试记忆最大会话数

##### TestCORSConfiguration - CORS配置测试
- `test_cors_origins_default`: 测试默认CORS origins
- `test_cors_origins_parsing`: 测试CORS origins解析
- `test_cors_origins_empty_handling`: 测试空CORS origins处理
- `test_cors_single_origin`: 测试单个CORS origin

##### TestEnvironmentVariables - 环境变量加载测试
- `test_env_file_loading`: 测试从.env文件加载配置
- `test_env_override`: 测试环境变量覆盖
- `test_case_insensitive_env`: 测试环境变量大小写不敏感

##### TestSettingsIntegration - 集成测试
- `test_complete_configuration`: 测试完整配置
- `test_settings_singleton`: 测试settings单例

##### TestSettingsValidation - 配置验证测试
- `test_invalid_types`: 测试无效类型
- `test_required_fields`: 测试必需字段
- `test_field_constraints`: 测试字段约束

### 2. test_config_loader.py

测试 `backend/app/core/config_loader.py` 中的 ConfigLoader 类的所有功能。

#### 测试类别

##### TestConfigLoader - 配置加载器测试
- `test_singleton_pattern`: 测试单例模式
- `test_load_settings_config`: 测试加载settings配置
- `test_load_skills_config`: 测试加载skills配置
- `test_load_agents_config`: 测试加载agents配置
- `test_load_tools_config`: 测试加载tools配置
- `test_load_prompts_config`: 测试加载prompts配置
- `test_get_setting`: 测试获取设置值
- `test_get_setting_with_default`: 测试获取设置值（带默认值）
- `test_reload_config`: 测试重新加载配置
- `test_reload_all_configs`: 测试重新加载所有配置
- `test_config_caching`: 测试配置缓存

##### TestAgentsConfig - Agents配置测试
- `test_agents_config_exists`: 测试agents配置文件存在
- `test_agents_config_structure`: 测试agents配置结构
- `test_orchestrator_agent_config`: 测试orchestrator agent配置

##### TestSkillsConfig - Skills配置测试
- `test_skills_config_exists`: 测试skills配置文件存在
- `test_skills_config_structure`: 测试skills配置结构
- `test_skill_processors`: 测试skill处理器配置

##### TestToolsConfig - Tools配置测试
- `test_tools_config_exists`: 测试tools配置文件存在
- `test_tools_config_structure`: 测试tools配置结构

##### TestPromptsConfig - Prompts配置测试
- `test_prompts_config_exists`: 测试prompts配置文件存在
- `test_prompts_config_structure`: 测试prompts配置结构

##### TestConfigIntegration - 配置集成测试
- `test_all_configs_loadable`: 测试所有配置文件可加载
- `test_config_consistency`: 测试配置一致性

## 运行测试

### 运行所有settings测试

```bash
python backend/tests/run_settings_tests.py
```

### 运行单个测试文件

```bash
# 测试Settings类
pytest backend/tests/test_settings.py -v

# 测试ConfigLoader类
pytest backend/tests/test_config_loader.py -v
```

### 运行特定测试类

```bash
# 测试API Key配置
pytest backend/tests/test_settings.py::TestAPIKeyConfiguration -v

# 测试配置加载器
pytest backend/tests/test_config_loader.py::TestConfigLoader -v
```

### 运行特定测试方法

```bash
# 测试SECRET_KEY验证
pytest backend/tests/test_settings.py::TestSettingsBasic::test_secret_key_validation -v

# 测试单例模式
pytest backend/tests/test_config_loader.py::TestConfigLoader::test_singleton_pattern -v
```

## 测试覆盖的配置项

### Settings类 (backend/app/config.py)

| 配置项 | 类型 | 默认值 | 测试状态 |
|--------|------|--------|----------|
| app_env | str | "development" | ✓ |
| app_debug | bool | True | ✓ |
| secret_key | str | "dev-secret-key..." | ✓ |
| dashscope_api_key | Optional[str] | None | ✓ |
| llm_api_key | Optional[str] | None | ✓ |
| llm_base_url | str | "https://dashscope..." | ✓ |
| llm_model | str | "qwen-plus" | ✓ |
| embedding_model | str | "text-embedding-v3" | ✓ |
| chroma_persist_dir | str | "./data/chroma" | ✓ |
| mongo_url | str | "mongodb://localhost:27017" | ✓ |
| mongo_db_name | str | "agent" | ✓ |
| memory_max_tokens | int | 4000 | ✓ |
| memory_max_sessions | int | 1000 | ✓ |
| cors_origins | str | "http://localhost:5173,..." | ✓ |

### 属性方法

| 方法 | 返回类型 | 测试状态 |
|------|----------|----------|
| embedding_api_key | Optional[str] | ✓ |
| api_key | Optional[str] | ✓ |
| allowed_origins | list[str] | ✓ |

### 配置文件

| 文件 | 路径 | 测试状态 |
|------|------|----------|
| 核心配置 | backend/app/core/config.json | ✓ |
| Agents配置 | backend/app/agents/config.json | ✓ |
| Skills配置 | backend/app/skills/config.json | ✓ |
| Tools配置 | backend/app/tools/config.json | ✓ |
| Prompts配置 | backend/app/prompts/config.json | ✓ |

## 测试要求

### 环境准备

1. 安装依赖：
```bash
pip install pytest pydantic pydantic-settings
```

2. 确保配置文件存在：
   - backend/.env 或 backend/.env.example
   - backend/app/core/config.json
   - backend/app/agents/config.json
   - backend/app/skills/config.json
   - backend/app/tools/config.json
   - backend/app/prompts/config.json

### 环境变量

测试会使用以下环境变量（可选）：
- APP_ENV
- APP_DEBUG
- SECRET_KEY
- DASHSCOPE_API_KEY
- LLM_API_KEY
- LLM_MODEL
- LLM_BASE_URL
- EMBEDDING_MODEL
- MONGO_URL
- MONGO_DB_NAME
- CHROMA_PERSIST_DIR
- MEMORY_MAX_TOKENS
- MEMORY_MAX_SESSIONS
- CORS_ORIGINS

## 测试结果示例

```
================================ test session starts =================================
platform win32 -- Python 3.11.0, pytest-7.4.0
collected 45 items

backend/tests/test_settings.py::TestSettingsBasic::test_default_settings PASSED [ 2%]
backend/tests/test_settings.py::TestSettingsBasic::test_secret_key_validation PASSED [ 4%]
...
backend/tests/test_config_loader.py::TestConfigLoader::test_singleton_pattern PASSED [95%]
backend/tests/test_config_loader.py::TestConfigLoader::test_load_settings_config PASSED [97%]
...

================================ 45 passed in 2.34s ==================================
```

## 故障排除

### 常见问题

1. **ImportError: No module named 'backend'**
   - 确保从项目根目录运行测试
   - 或使用 `python -m pytest backend/tests/test_settings.py`

2. **ValidationError: SECRET_KEY必须设置**
   - 在 .env 文件中设置有效的 SECRET_KEY（至少32字符）

3. **FileNotFoundError: config.json not found**
   - 确保所有配置文件都存在
   - 检查文件路径是否正确

4. **测试失败：配置值不匹配**
   - 检查 .env 文件中的配置
   - 确保环境变量没有意外覆盖

## 扩展测试

如果添加了新的配置项，请按以下步骤更新测试：

1. 在 `test_settings.py` 中添加新的测试方法
2. 测试默认值
3. 测试自定义值
4. 测试验证规则
5. 更新本文档

## 贡献

如果发现配置项未被测试覆盖，请：
1. 添加相应的测试用例
2. 更新本文档
3. 提交PR

## 许可

与主项目相同
