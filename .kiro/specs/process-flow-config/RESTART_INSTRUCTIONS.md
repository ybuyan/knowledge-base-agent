# 重启后端服务指南

## GuideAgent 已实现完成

所有代码已经就绪，现在需要重启后端服务以加载新的配置。

## 重启步骤

### 1. 停止当前后端服务
如果后端服务正在运行，请先停止它（Ctrl+C）

### 2. 启动后端服务
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

或者使用你现有的启动脚本。

## 验证服务启动

启动后，你应该在日志中看到：
```
INFO:app.main:Agents 已注册: ['document_agent', 'qa_agent', 'memory_agent', 'orchestrator_agent', 'guide_agent']
```

确认 `guide_agent` 已经注册。

## 测试 GuideAgent

### 方法 1: 通过 API 测试
发送请求到聊天接口：
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "我想请假",
    "session_id": "test_session"
  }'
```

### 方法 2: 通过前端测试
1. 启动前端应用
2. 在聊天界面输入："我想请假"
3. 应该看到助手开始收集信息

### 预期响应
助手应该回复类似：
```
您好！很高兴为您服务。为了帮您更好地办理请假手续，我需要了解一些基本信息：

1. 您想申请哪种类型的假期呢？（例如：年假、病假、事假、婚假、产假/陪产假、高温假等）
2. 大概想请几天？
3. 计划什么时候开始请假呢？

您可以告诉我这些信息，我会为您生成详细的请假指引哦 😊
```

## 完整对话流程测试

### 第一轮
**用户**: 我想请假
**助手**: 收集信息（假期类型、天数、时间）

### 第二轮
**用户**: 年假，3天，从6月15日开始
**助手**: 生成详细的请假操作指引

预期输出包括：
- 📊 假期余额
- 📝 申请流程
- 🔗 申请入口
- 📄 参考模板
- ⚠️ 注意事项

## 触发关键词

以下任何查询都会触发 GuideAgent：
- "我想请假"
- "怎么请假"
- "请假流程"
- "如何申请"
- "怎么办理"
- "办理流程"

## 故障排查

### 如果 GuideAgent 没有被触发
1. 检查日志中是否有 `guide_agent` 注册
2. 检查意图识别日志：`OrchestratorAgent 意图: '...' -> guide`
3. 确认 leave_guide skill 已加载

### 如果出现错误
1. 检查 `backend/app/prompts/config.json` 中 `leave_guide` 配置
2. 检查 `backend/app/skills/definitions/leave_guide/SKILL.md` 配置
3. 查看后端日志获取详细错误信息

## 已修改的文件

1. `backend/app/agents/implementations/guide_agent.py` - 新增
2. `backend/app/agents/implementations/orchestrator_agent.py` - 添加 guide 意图
3. `backend/app/skills/definitions/leave_guide/SKILL.md` - 配置为 guide 类型
4. `backend/app/prompts/config.json` - 添加 leave_guide 模板
5. `backend/app/main.py` - 注册 GuideAgent
6. `backend/app/agents/implementations/__init__.py` - 导出 GuideAgent

所有更改已完成，重启服务即可生效！
