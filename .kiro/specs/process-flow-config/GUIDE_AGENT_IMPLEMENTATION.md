# GuideAgent 实现完成

## 概述

GuideAgent 已成功实现，用于通过多轮对话收集信息并生成流程操作指引。

## 架构

```
用户查询 "我想请假"
    ↓
OrchestratorAgent (意图识别)
    ↓ 检测到 "guide" 意图
GuideAgent
    ↓ 匹配 triggers
leave_guide skill
    ↓ 执行 pipeline
LLMGenerator (使用 leave_guide prompt)
    ↓
LLM 多轮对话收集信息
    ↓
生成流程指引
```

## 已完成的工作

### 1. GuideAgent 实现
- **文件**: `backend/app/agents/implementations/guide_agent.py`
- **功能**:
  - 根据 triggers 匹配对应的 guide skill
  - 执行 skill 的 pipeline
  - 处理多轮对话
  - 生成流程指引

### 2. Orchestrator 路由
- **文件**: `backend/app/agents/implementations/orchestrator_agent.py`
- **功能**:
  - 添加 guide 意图检测
  - 关键词: `["我想请假", "怎么请假", "请假流程", "如何申请", "怎么办理", "办理流程"]`
  - 路由到 GuideAgent

### 3. leave_guide Skill
- **文件**: `backend/app/skills/definitions/leave_guide/SKILL.md`
- **配置**:
  - `skill_type: guide`
  - `triggers`: 匹配请假相关查询
  - `pipeline`: 使用 LLMGenerator 处理

### 4. Prompt 模板
- **文件**: `backend/app/prompts/config.json`
- **模板**: `leave_guide`
- **功能**:
  - 系统提示词定义对话方式
  - 收集假期类型、天数、时间
  - 生成详细操作指引模板

### 5. Agent 注册
- **文件**: `backend/app/main.py`
- **修改**: 添加 `GuideAgent` 注册

## 测试结果

### 基础测试 (test_leave_guide.py)
✅ leave_guide skill 加载成功
✅ 意图识别正确
✅ Pipeline 配置正确

### 端到端测试 (test_guide_agent_e2e.py)
✅ "我想请假" → 正确路由到 GuideAgent
✅ "怎么请假" → 正确路由到 GuideAgent
✅ LLM 使用 leave_guide prompt 进行多轮对话
✅ 收集信息：假期类型、天数、时间

## 对话示例

**用户**: 我想请假

**助手**: 您好！很高兴为您服务。为了帮您更好地办理请假手续，我需要了解一些基本信息：

1. 您想申请哪种类型的假期呢？（例如：年假、病假、事假、婚假、产假/陪产假、高温假等）
2. 大概想请几天？
3. 计划什么时候开始请假呢？

您可以告诉我这些信息，我会为您生成详细的请假指引哦 😊

## 下一步

### 需要重启后端服务
后端服务需要重启以加载新的 GuideAgent 配置：

```bash
# 停止当前服务
# 重启服务
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 测试完整流程
1. 用户: "我想请假"
2. 助手: 收集信息（假期类型、天数、时间）
3. 用户: 提供信息
4. 助手: 生成详细的请假操作指引

### 预期输出格式
```
📊 **假期余额**
您当前剩余年假 X 天，可申请 Y 天年假。

📝 **申请流程**
1. 发起请假申请
2. 直属上级审批
3. HR 备案

🔗 **申请入口**
https://oa.company.com/leave

📄 **参考模板**
【年假申请】
申请人：xxx
时间：xxxx 年 xx 月 xx 日 - xxxx 年 xx 月 xx 日，共 X 天
事由：个人事务

⚠️ **注意事项**
- 请提前 3 天申请
- 审批时间：1-3 个工作日
- 紧急情况请先电话联系直属上级
- 高温假仅限 6-9 月申请
```

## 文件清单

### 核心文件
- `backend/app/agents/implementations/guide_agent.py` - GuideAgent 实现
- `backend/app/agents/implementations/orchestrator_agent.py` - 意图路由
- `backend/app/skills/definitions/leave_guide/SKILL.md` - Skill 定义
- `backend/app/prompts/config.json` - Prompt 模板
- `backend/app/main.py` - Agent 注册

### 测试文件
- `backend/test_leave_guide.py` - 基础测试
- `backend/test_guide_agent_e2e.py` - 端到端测试

## 重要说明

1. **不自动提交申请**: GuideAgent 只提供操作指引，不会直接帮用户提交申请
2. **多轮对话**: 如果用户信息不完整，通过对话补充收集
3. **假期类型**: 支持年假、病假、事假、婚假、产假、陪产假、高温假
4. **注意事项**: 根据假期类型提供对应的注意事项（如高温假的时间限制）
