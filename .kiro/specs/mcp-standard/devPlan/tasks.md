# 外部链接功能任务清单

## 后端任务

### 1. 配置管理
- [ ] 在 `constraint_config.py` 添加 `external_links` 配置属性
- [ ] 在 `constraints.json` 添加默认链接配置

### 2. 链接匹配服务
- [ ] 创建 `services/link_matcher.py`
  - [ ] 实现 `LinkMatcher` 类
  - [ ] 实现 `match_links(query: str)` 方法
  - [ ] 基于关键词匹配相关链接

### 3. 集成到 QA 流程
- [ ] 在 `qa_agent.py` 导入 `LinkMatcher`
- [ ] 在 `_execute_rag_flow` 中调用链接匹配
- [ ] 将匹配结果添加到响应中

### 4. 响应构建
- [ ] 在 `response_builder.py` 添加 `related_links` 参数
- [ ] 更新 `done_chunk` 方法

### 5. 数据持久化
- [ ] 在 `message_service.py` 添加 `related_links` 字段
- [ ] 更新 `add_message` 方法
- [ ] 更新 `get_messages` API 返回格式

## 前端任务

### 1. 数据模型
- [ ] 在 `stores/chat.ts` 添加 `relatedLinks` 字段到 `Message` 接口
- [ ] 添加 `updateLastAssistantRelatedLinks` 函数

### 2. API 处理
- [ ] 在 `api/index.ts` 处理 `related_links` 字段

### 3. UI 显示
- [ ] 在 `ChatView.vue` 显示相关链接
- [ ] 添加链接样式

### 4. 配置页面
- [ ] 在 `Constraints.vue` 添加链接管理功能
- [ ] 实现添加/编辑/删除链接

## 测试任务

- [ ] 测试链接匹配功能
- [ ] 测试链接显示
- [ ] 测试配置保存
- [ ] 测试刷新页面后链接显示
