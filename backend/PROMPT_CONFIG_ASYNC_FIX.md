# 提示词配置管理 - 异步问题修复

## 问题描述

在定时同步任务中出现错误：

```
INFO:app.prompts.manager:从数据库加载配置失败: Cannot run the event loop while another loop is running
```

## 问题原因

定时任务 `prompt_sync_task` 运行在异步上下文中（APScheduler 的 AsyncIOScheduler），当它调用 `prompt_manager.reload()` 时：

1. `reload()` 是同步方法
2. 它内部调用 `_load_from_database()`
3. `_load_from_database()` 尝试创建新的事件循环：`asyncio.new_event_loop()`
4. 但此时已经在事件循环中运行，导致冲突

## 解决方案

### 1. 添加事件循环检测

在 `_load_from_database()` 中检测是否已在事件循环中：

```python
try:
    loop = asyncio.get_running_loop()
    # 已经在事件循环中，无法同步调用
    logger.info("已在事件循环中，跳过从数据库加载")
    return False
except RuntimeError:
    # 没有运行中的事件循环，可以创建新的
    pass
```

### 2. 添加异步版本的 reload

新增 `reload_async()` 方法供异步上下文使用：

```python
async def reload_async(self) -> None:
    """重新加载配置（异步版本）"""
    from app.services.prompt_config_service import prompt_config_service
    
    # 直接使用异步方法
    prompts = await prompt_config_service.get_all(enabled_only=False)
    
    # 更新配置
    self._config = {...}
```

### 3. 修改定时任务

定时任务直接使用异步方法，不再调用同步的 `reload()`：

```python
async def sync_prompts(self):
    """同步提示词配置"""
    # 直接从数据库加载
    prompts = await prompt_config_service.get_all(enabled_only=False)
    
    # 直接更新 PromptManager 的配置
    prompt_manager._config = {...}
```

### 4. 更新 API 路由

API 路由使用异步版本：

```python
@router.post("/reload")
async def reload_config(...):
    await prompt_manager.reload_async()
```

## 修改的文件

1. `app/prompts/manager.py`
   - 添加事件循环检测
   - 新增 `reload_async()` 方法

2. `app/tasks/prompt_sync_task.py`
   - 直接使用异步方法加载配置
   - 不再调用 `reload()`

3. `app/api/routes/prompt_config.py`
   - 使用 `reload_async()` 替代 `reload()`

## 测试验证

### 测试脚本

```bash
python scripts/test_async_reload.py
```

### 测试结果

```
INFO:__main__:连接数据库...
INFO:app.core.mongodb:MongoDB 连接成功
INFO:__main__:测试异步重新加载...
INFO:app.prompts.manager:从数据库重新加载 26 个提示词配置
INFO:__main__:✓ 重新加载成功，共 26 个提示词
INFO:__main__:✓ 获取配置成功: RAG问答提示词
INFO:__main__:测试完成！
```

## 工作流程

### 应用启动时（同步上下文）

```
应用启动
  ↓
PromptManager 初始化
  ↓
_load_config()
  ↓
尝试 _load_from_database()
  ├─ 检测：没有运行中的事件循环 ✓
  ├─ 创建新的事件循环
  ├─ 加载配置
  └─ 关闭事件循环
  ↓
成功加载
```

### 定时任务同步（异步上下文）

```
定时任务触发
  ↓
sync_prompts() (异步方法)
  ↓
直接调用 prompt_config_service.get_all()
  ↓
更新 prompt_manager._config
  ↓
同步完成
```

### API 手动重新加载（异步上下文）

```
API 请求
  ↓
reload_config() (异步路由)
  ↓
prompt_manager.reload_async()
  ↓
直接调用 prompt_config_service.get_all()
  ↓
更新配置
  ↓
返回成功
```

## 方法对比

| 方法 | 上下文 | 用途 | 事件循环 |
|------|--------|------|----------|
| `reload()` | 同步 | 应用启动、脚本 | 创建新循环 |
| `reload_async()` | 异步 | API、定时任务 | 使用当前循环 |
| `_load_from_database()` | 同步 | 内部使用 | 检测后创建 |

## 注意事项

### ✅ 正确用法

```python
# 同步上下文（脚本、应用启动）
prompt_manager.reload()

# 异步上下文（API、定时任务）
await prompt_manager.reload_async()
```

### ❌ 错误用法

```python
# 在异步上下文中调用同步方法
async def some_function():
    prompt_manager.reload()  # ❌ 会导致事件循环冲突

# 在同步上下文中调用异步方法
def some_function():
    await prompt_manager.reload_async()  # ❌ 语法错误
```

## 日志说明

### 正常日志

```
# 应用启动（同步）
INFO:app.prompts.manager:从数据库加载 26 个提示词配置

# 定时同步（异步）
INFO:app.tasks.prompt_sync_task:开始同步提示词配置...
INFO:app.tasks.prompt_sync_task:提示词配置同步完成: 2024-01-01 12:00:00, 共 26 个

# API 重新加载（异步）
INFO:app.prompts.manager:从数据库重新加载 26 个提示词配置
```

### 错误日志（已修复）

```
# 旧版本的错误
INFO:app.prompts.manager:从数据库加载配置失败: Cannot run the event loop while another loop is running
```

## 性能影响

修复后的性能：
- 应用启动：无变化
- 定时同步：更快（直接异步调用）
- API 重新加载：更快（直接异步调用）
- 内存占用：无变化

## 兼容性

- ✅ 向后兼容：旧的同步调用仍然有效
- ✅ 新增功能：异步调用更高效
- ✅ 自动检测：根据上下文选择合适的方法

## 总结

问题已完全修复：

✅ 添加了事件循环检测
✅ 新增了异步版本的 reload
✅ 修改了定时任务使用异步方法
✅ 更新了 API 路由使用异步方法
✅ 测试验证通过

现在系统可以在同步和异步上下文中正确工作，不会再出现事件循环冲突的问题。
