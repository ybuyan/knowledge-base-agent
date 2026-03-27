# 约束系统测试套件

本目录包含约束系统的完整测试用例，涵盖配置管理、答案验证、系统集成和 API 接口等方面。

## 测试文件说明

### 1. test_constraint_config.py
测试约束配置管理功能：
- 配置加载（从文件、默认值）
- 单例模式
- 配置属性访问
- 配置更新和持久化
- 配置重置
- 错误处理

### 2. test_answer_validator.py
测试答案验证器功能：
- 检索结果验证（相似度过滤、文档数量限制）
- 来源归属检查
- 幻觉检测
- 置信度计算
- 综合答案验证

### 3. test_constraint_integration.py
测试约束系统与其他服务的集成：
- 与 QA Agent 的集成
- 与检索器的集成
- 与响应构建器的集成
- 与建议生成器的集成
- 完整验证流程
- 配置变更影响
- 错误处理

### 4. test_constraint_api.py
测试约束 API 端点：
- GET /api/constraints - 获取约束配置
- PUT /api/constraints - 更新约束配置
- POST /api/constraints/reset - 重置约束配置
- GET /api/constraints/stats - 获取约束统计
- 输入验证
- 配置持久化

## 运行测试

### 运行所有约束测试
```bash
cd backend
pytest tests/constraints/ -v
```

### 运行特定测试文件
```bash
# 配置测试
pytest tests/constraints/test_constraint_config.py -v

# 验证器测试
pytest tests/constraints/test_answer_validator.py -v

# 集成测试
pytest tests/constraints/test_constraint_integration.py -v

# API 测试（需要启动服务器）
pytest tests/constraints/test_constraint_api.py -v
```

### 运行特定测试类
```bash
pytest tests/constraints/test_constraint_config.py::TestConstraintConfigLoading -v
```

### 运行特定测试方法
```bash
pytest tests/constraints/test_constraint_config.py::TestConstraintConfigLoading::test_singleton_pattern -v
```

### 生成测试覆盖率报告
```bash
pytest tests/constraints/ --cov=app.core.constraint_config --cov=app.services.answer_validator --cov-report=html
```

## 测试覆盖范围

### 配置管理 (test_constraint_config.py)
- ✅ 单例模式
- ✅ 配置文件加载
- ✅ 默认配置加载
- ✅ JSON 解析错误处理
- ✅ 配置属性访问（retrieval, generation, validation, fallback）
- ✅ 配置更新
- ✅ 配置持久化
- ✅ 配置重置
- ✅ 默认值验证

### 答案验证 (test_answer_validator.py)
- ✅ 检索验证（相似度过滤）
- ✅ 最大文档数限制
- ✅ 检索验证禁用
- ✅ 来源归属检查
- ✅ 引用标记检测
- ✅ 幻觉检测（不确定性词汇、缺乏支持的内容、数字验证）
- ✅ 置信度计算
- ✅ 综合答案验证
- ✅ 验证禁用

### 系统集成 (test_constraint_integration.py)
- ✅ 禁止主题检测
- ✅ 禁止关键词检测
- ✅ 最大回答长度约束
- ✅ 检索过滤集成
- ✅ 兜底消息
- ✅ 建议生成约束
- ✅ 完整验证流程
- ✅ 配置变更影响
- ✅ 错误处理

### API 接口 (test_constraint_api.py)
- ✅ 获取约束配置
- ✅ 更新约束配置
- ✅ 重置约束配置
- ✅ 获取约束统计
- ✅ 输入验证
- ✅ 检索配置 API
- ✅ 生成配置 API
- ✅ 验证配置 API
- ✅ 兜底配置 API
- ✅ 配置持久化

## 测试数据

测试使用模拟数据和临时文件，不会影响生产配置。

### 示例测试数据

**文档数据：**
```python
documents = ["文档内容1", "文档内容2", "文档内容3"]
metadatas = [
    {"source": "doc1.pdf", "page": 1},
    {"source": "doc2.pdf", "page": 2},
    {"source": "doc3.pdf", "page": 3}
]
distances = [0.2, 0.8, 1.5]  # 相似度: 0.9, 0.6, 0.25
```

**约束配置：**
```python
constraints = {
    "retrieval": {
        "enabled": True,
        "min_similarity_score": 0.7,
        "max_relevant_docs": 5
    },
    "generation": {
        "strict_mode": True,
        "forbidden_topics": ["薪资", "工资"],
        "forbidden_keywords": ["可能", "大概"]
    },
    "validation": {
        "enabled": True,
        "min_confidence_score": 0.6,
        "hallucination_detection": True
    }
}
```

## 依赖项

测试需要以下 Python 包：
- pytest
- pytest-asyncio
- httpx
- unittest.mock (标准库)

安装依赖：
```bash
pip install pytest pytest-asyncio httpx
```

## 注意事项

1. **API 测试**：需要先启动后端服务器（默认 http://localhost:8000）
2. **异步测试**：使用 `pytest-asyncio` 运行异步测试
3. **单例重置**：某些测试会重置单例实例，确保测试隔离
4. **临时文件**：配置测试使用临时文件，测试后自动清理
5. **Mock 对象**：集成测试使用 mock 对象模拟依赖

## 持续集成

可以将这些测试集成到 CI/CD 流程中：

```yaml
# .github/workflows/test.yml 示例
name: Test Constraints

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio httpx pytest-cov
      - name: Run unit tests
        run: |
          pytest tests/constraints/test_constraint_config.py -v
          pytest tests/constraints/test_answer_validator.py -v
          pytest tests/constraints/test_constraint_integration.py -v
      - name: Generate coverage report
        run: |
          pytest tests/constraints/ --cov=app.core.constraint_config --cov=app.services.answer_validator --cov-report=xml
```

## 贡献指南

添加新测试时，请遵循以下规范：

1. **命名规范**：测试类以 `Test` 开头，测试方法以 `test_` 开头
2. **文档字符串**：每个测试方法添加清晰的文档字符串
3. **断言明确**：使用明确的断言消息
4. **测试隔离**：确保测试之间相互独立
5. **清理资源**：使用 fixture 和 teardown 清理测试资源

## 问题反馈

如果发现测试问题或需要添加新的测试用例，请提交 Issue 或 Pull Request。
