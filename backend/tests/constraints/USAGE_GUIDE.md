# 约束系统测试使用指南

## 快速开始

### 1. 首次使用 - 快速验证

运行快速测试脚本，验证约束系统是否正常工作：

```bash
cd backend
python tests/constraints/quick_test.py
```

预期输出：
```
============================================================
  约束系统快速测试
============================================================

============================================================
  测试 1: 配置加载
============================================================

✅ 配置加载成功
✅ 配置结构完整

... (更多测试输出)

============================================================
  测试总结
============================================================

通过: 9/9
失败: 0/9

🎉 所有测试通过！
```

### 2. 运行单元测试

单元测试不需要启动服务器，可以直接运行：

```bash
# 使用测试脚本
python tests/constraints/run_tests.py --unit

# 或使用 pytest
pytest tests/constraints/test_constraint_config.py -v
pytest tests/constraints/test_answer_validator.py -v
pytest tests/constraints/test_constraint_integration.py -v
```

### 3. 运行 API 测试

API 测试需要先启动后端服务器：

```bash
# 终端 1: 启动服务器
cd backend
python app/main.py

# 终端 2: 运行 API 测试
python tests/constraints/run_tests.py --api
```

### 4. 生成覆盖率报告

```bash
python tests/constraints/run_tests.py --coverage
```

报告将生成在 `htmlcov/index.html`，用浏览器打开查看。

## 常用测试场景

### 场景 1: 验证配置修改

修改 `backend/config/constraints.json` 后，运行测试验证：

```bash
# 快速验证
python tests/constraints/quick_test.py

# 完整验证
pytest tests/constraints/test_constraint_config.py -v
```

### 场景 2: 测试新的验证逻辑

添加新的验证逻辑后，运行相关测试：

```bash
pytest tests/constraints/test_answer_validator.py -v
```

### 场景 3: 测试系统集成

修改了多个组件后，运行集成测试：

```bash
pytest tests/constraints/test_constraint_integration.py -v
```

### 场景 4: 调试特定测试

运行单个测试方法并显示详细输出：

```bash
pytest tests/constraints/test_constraint_config.py::TestConstraintConfigLoading::test_singleton_pattern -v -s
```

参数说明：
- `-v`: 详细输出
- `-s`: 显示 print 语句
- `--tb=short`: 简短的错误追踪

## 测试脚本使用

### run_tests.py 参数

```bash
# 查看帮助
python tests/constraints/run_tests.py --help

# 运行所有测试
python tests/constraints/run_tests.py --all

# 运行单元测试
python tests/constraints/run_tests.py --unit

# 运行 API 测试
python tests/constraints/run_tests.py --api

# 运行特定测试
python tests/constraints/run_tests.py --test tests/constraints/test_constraint_config.py

# 生成覆盖率报告
python tests/constraints/run_tests.py --coverage

# 静默模式
python tests/constraints/run_tests.py --all --quiet
```

## Pytest 高级用法

### 运行带标记的测试

```bash
# 只运行单元测试
pytest tests/constraints/ -m unit -v

# 只运行集成测试
pytest tests/constraints/ -m integration -v

# 只运行 API 测试
pytest tests/constraints/ -m api -v
```

### 并行运行测试

安装 pytest-xdist：
```bash
pip install pytest-xdist
```

并行运行：
```bash
pytest tests/constraints/ -n auto
```

### 失败时停止

```bash
pytest tests/constraints/ -x  # 第一个失败时停止
pytest tests/constraints/ --maxfail=3  # 3 个失败后停止
```

### 只运行失败的测试

```bash
# 第一次运行
pytest tests/constraints/ -v

# 只重新运行失败的测试
pytest tests/constraints/ --lf
```

### 显示最慢的测试

```bash
pytest tests/constraints/ --durations=10
```

## 调试技巧

### 1. 使用 pdb 调试

在测试代码中添加断点：
```python
def test_something():
    import pdb; pdb.set_trace()
    # 测试代码
```

或使用 pytest 的 `--pdb` 选项：
```bash
pytest tests/constraints/test_constraint_config.py --pdb
```

### 2. 查看详细日志

```bash
pytest tests/constraints/ -v -s --log-cli-level=DEBUG
```

### 3. 只运行匹配的测试

```bash
# 运行名称包含 "config" 的测试
pytest tests/constraints/ -k config -v

# 运行名称包含 "validation" 的测试
pytest tests/constraints/ -k validation -v
```

### 4. 生成 JUnit XML 报告

```bash
pytest tests/constraints/ --junitxml=test-results.xml
```

## 常见问题

### Q1: 测试失败 - 配置文件未找到

**问题**: `FileNotFoundError: constraints.json not found`

**解决**:
```bash
# 确保在 backend 目录下运行
cd backend
python tests/constraints/quick_test.py

# 或检查配置文件是否存在
ls config/constraints.json
```

### Q2: API 测试失败 - 连接被拒绝

**问题**: `ConnectionRefusedError: [Errno 111] Connection refused`

**解决**:
```bash
# 先启动服务器
python app/main.py

# 然后在另一个终端运行 API 测试
python tests/constraints/run_tests.py --api
```

### Q3: 导入错误

**问题**: `ModuleNotFoundError: No module named 'app'`

**解决**:
```bash
# 确保在 backend 目录下
cd backend

# 或设置 PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Q4: 测试通过但覆盖率低

**解决**:
```bash
# 查看未覆盖的代码
pytest tests/constraints/ --cov=app.core.constraint_config --cov-report=term-missing

# 添加更多测试用例覆盖未测试的代码路径
```

## 编写新测试

### 测试模板

```python
"""
测试模块描述
"""

import pytest
from unittest.mock import patch, MagicMock

from app.core.constraint_config import ConstraintConfig


class TestYourFeature:
    """测试类描述"""
    
    @pytest.fixture
    def setup_data(self):
        """准备测试数据"""
        return {
            "key": "value"
        }
    
    def test_basic_functionality(self, setup_data):
        """测试基本功能"""
        # Arrange (准备)
        config = ConstraintConfig()
        
        # Act (执行)
        result = config.get_all()
        
        # Assert (断言)
        assert result is not None
        assert "retrieval" in result
    
    def test_error_handling(self):
        """测试错误处理"""
        config = ConstraintConfig()
        
        with pytest.raises(ValueError):
            config.update(None)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

### 测试命名规范

- 测试文件: `test_*.py`
- 测试类: `Test*`
- 测试方法: `test_*`
- Fixture: 描述性名称，如 `sample_documents`

### 断言最佳实践

```python
# ✅ 好的断言 - 明确且有意义
assert result.is_valid == True, "验证应该通过"
assert len(filtered_docs) == 2, f"应该过滤为 2 个文档，实际 {len(filtered_docs)}"

# ❌ 不好的断言 - 不够明确
assert result
assert filtered_docs
```

## 持续集成

### GitHub Actions 示例

创建 `.github/workflows/test-constraints.yml`:

```yaml
name: Constraint Tests

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
        cd backend
        pip install -r requirements.txt
        pip install pytest pytest-asyncio httpx pytest-cov
    
    - name: Run unit tests
      run: |
        cd backend
        pytest tests/constraints/test_constraint_config.py -v
        pytest tests/constraints/test_answer_validator.py -v
        pytest tests/constraints/test_constraint_integration.py -v
    
    - name: Generate coverage report
      run: |
        cd backend
        pytest tests/constraints/ --cov=app.core.constraint_config --cov=app.services.answer_validator --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v2
      with:
        file: ./backend/coverage.xml
```

## 性能测试

### 测试大量文档的过滤性能

```python
import time

def test_performance_large_dataset():
    """测试大数据集性能"""
    validator = AnswerValidator()
    
    # 生成大量测试数据
    documents = [f"文档{i}" for i in range(1000)]
    metadatas = [{"source": f"doc{i}.pdf"} for i in range(1000)]
    distances = [i * 0.001 for i in range(1000)]
    
    start_time = time.time()
    filtered_docs, _ = validator.validate_retrieval(documents, metadatas, distances)
    elapsed_time = time.time() - start_time
    
    print(f"处理 1000 个文档耗时: {elapsed_time:.3f} 秒")
    assert elapsed_time < 1.0, "性能不达标"
```

## 总结

- 使用 `quick_test.py` 进行快速验证
- 使用 `run_tests.py` 运行完整测试套件
- 使用 pytest 进行灵活的测试控制
- 定期运行测试确保代码质量
- 添加新功能时同步添加测试

有问题？查看 [README.md](README.md) 或 [TEST_SUMMARY.md](TEST_SUMMARY.md)
