# 提示词配置重置指南

## 概述

本指南说明如何重置数据库中的提示词配置，将 `config.json` 中的最新配置同步到数据库。

## 使用场景

1. 首次部署，需要初始化数据库
2. 配置文件有重大更新，需要完全重置
3. 数据库配置损坏，需要恢复
4. 清理测试数据，重新开始

## 重置脚本

### 脚本功能

`scripts/reset_prompts.py` 会执行以下操作：

1. ✅ 删除数据库中的所有 prompts
2. ✅ 从 `app/prompts/config.json` 读取配置
3. ✅ 将所有配置导入数据库
4. ✅ 验证导入结果

### 执行步骤

```bash
cd backend
python scripts/reset_prompts.py
```

### 执行结果

```
INFO:__main__:连接数据库...
INFO:app.core.mongodb:MongoDB 连接成功: mongodb://localhost:27017, 数据库: agent
INFO:__main__:删除数据库中的所有 prompts...
INFO:__main__:已删除 24 个提示词配置
INFO:__main__:从配置文件同步提示词...
INFO:__main__:同步完成:
INFO:__main__:  - 创建: 26 个
INFO:__main__:  - 更新: 0 个
INFO:__main__:  - 跳过: 0 个
INFO:__main__:  - 错误: 0 个
INFO:__main__:
验证结果...
INFO:__main__:数据库中现有 26 个提示词配置
INFO:__main__:
前 5 个配置:
INFO:__main__:  - qa_rag: RAG问答提示词
INFO:__main__:  - strict_qa: 严格知识库问答
INFO:__main__:  - fallback: 无结果兜底提示
INFO:__main__:  - tool_router: 工具路由决策
INFO:__main__:  - tool_flow: 工具流程回答
INFO:__main__:
✓ 重置完成！
```

## 验证配置

### 检查数据库

使用检查脚本查看数据库中的配置：

```bash
python scripts/check_prompts.py
```

输出示例：

```
=== 提示词配置统计 ===
总数: 26
启用: 26
禁用: 0

=== 按分类统计 ===
suggestion          : 6 个
assistant           : 4 个
agent               : 3 个
qa                  : 3 个
optimization        : 3 个
mcp                 : 3 个
document            : 2 个
validation          : 1 个
memory              : 1 个

=== 所有提示词配置 ===

[agent]
  ✓ tool_router                    - 工具路由决策
  ✓ tool_flow                      - 工具流程回答
  ✓ intent_detection               - 意图识别

[assistant]
  ✓ clarify_question               - 问题澄清
  ✓ default_assistant              - 默认助手
  ✓ leave_guide                    - 请假指引
  ✓ leave_guide_v2                 - 请假指引 v2.0 - 多轮对话

... (更多配置)
```

### 测试应用加载

```bash
python -c "from app.prompts.manager import prompt_manager; print('配置加载成功，共', len(prompt_manager.list_all()), '个提示词')"
```

输出：
```
配置加载成功，共 26 个提示词
```

## 配置分类

当前配置包含以下分类：

| 分类 | 数量 | 说明 |
|------|------|------|
| suggestion | 6 | 快捷提问建议 |
| assistant | 4 | 通用助手 |
| agent | 3 | Agent 相关 |
| qa | 3 | 问答相关 |
| optimization | 3 | 优化相关 |
| mcp | 3 | MCP 服务器 |
| document | 2 | 文档处理 |
| validation | 1 | 内容验证 |
| memory | 1 | 记忆管理 |

## 注意事项

### ⚠️ 数据丢失警告

重置操作会删除数据库中的所有提示词配置，包括：
- 所有自定义配置
- 所有配置修改历史
- 所有配置元数据

### 建议操作流程

1. **备份现有配置**（如果需要）
   ```bash
   python scripts/export_prompt_config.py
   ```

2. **执行重置**
   ```bash
   python scripts/reset_prompts.py
   ```

3. **验证结果**
   ```bash
   python scripts/check_prompts.py
   ```

4. **重启应用**
   ```bash
   python -m app.main
   ```

## 常见问题

### Q: 重置后会影响正在运行的应用吗？

A: 不会立即影响。应用使用内存中的配置，需要等待定时同步（最多 5 分钟）或手动重启应用。

### Q: 如何保留自定义配置？

A: 
1. 先导出当前配置：`python scripts/export_prompt_config.py`
2. 将自定义配置合并到 `config.json`
3. 执行重置脚本

### Q: 重置失败怎么办？

A: 
1. 检查 MongoDB 是否正常运行
2. 检查数据库连接配置
3. 查看错误日志
4. 手动删除集合后重试：
   ```javascript
   db.prompts.drop()
   ```

### Q: 可以只更新部分配置吗？

A: 可以。使用 `init_prompt_config.py` 而不是 `reset_prompts.py`：
```bash
python scripts/init_prompt_config.py
```
这个脚本会：
- 创建不存在的配置
- 更新已存在的配置
- 不删除数据库中的配置

## 脚本对比

| 脚本 | 删除现有 | 创建新配置 | 更新现有 | 使用场景 |
|------|----------|------------|----------|----------|
| reset_prompts.py | ✅ | ✅ | - | 完全重置 |
| init_prompt_config.py | ❌ | ✅ | ✅ | 增量更新 |
| export_prompt_config.py | ❌ | ❌ | ❌ | 备份导出 |
| check_prompts.py | ❌ | ❌ | ❌ | 查看配置 |

## 最佳实践

### 开发环境

1. 使用文件模式，无需数据库
2. 直接修改 `config.json`
3. 重启应用即可

### 测试环境

1. 使用数据库模式
2. 定期重置配置保持一致
3. 测试配置管理功能

### 生产环境

1. 使用数据库模式
2. 谨慎使用重置脚本
3. 重置前务必备份
4. 在维护窗口执行
5. 重置后验证功能

## 回滚方案

如果重置后发现问题，可以回滚：

### 方案 1：从备份恢复

```bash
# 1. 恢复备份的配置文件
cp config_backup.json app/prompts/config.json

# 2. 重新执行重置
python scripts/reset_prompts.py
```

### 方案 2：从 Git 恢复

```bash
# 1. 恢复配置文件
git checkout app/prompts/config.json

# 2. 重新执行重置
python scripts/reset_prompts.py
```

### 方案 3：切换到文件模式

```bash
# 1. 停止应用
# 2. 删除数据库中的 prompts
db.prompts.drop()
# 3. 重启应用（自动使用文件模式）
```

## 监控和日志

### 关键日志

```
# 成功日志
INFO:__main__:已删除 X 个提示词配置
INFO:__main__:同步完成: 创建 X 个

# 错误日志
ERROR:__main__:重置失败: ...
ERROR:app.services.prompt_config_service:同步提示词 X 失败: ...
```

### 监控指标

- 重置执行时间
- 删除的配置数量
- 创建的配置数量
- 错误数量

## 总结

重置脚本提供了一个安全、可靠的方式来重置数据库中的提示词配置：

✅ 完全清空现有配置
✅ 从文件导入最新配置
✅ 自动验证结果
✅ 详细的日志输出

使用前请确保：
1. 已备份重要配置
2. 在维护窗口执行
3. 执行后验证功能
4. 准备好回滚方案
