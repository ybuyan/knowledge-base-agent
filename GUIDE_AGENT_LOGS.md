# GuideAgent 日志追踪指南

## 日志标记说明

所有 GuideAgent 相关的日志都使用特殊标记，方便过滤和追踪：

- `🎯 [GUIDE]` - Orchestrator 路由到 GuideAgent
- `🚀 [GUIDE]` - GuideAgent 开始执行
- `🔍 [GUIDE]` - 开始匹配 guide skill
- `✅ [GUIDE]` - 匹配成功
- `❌ [GUIDE]` - 匹配失败
- `⚠️  [GUIDE]` - 警告信息
- `📋 [GUIDE]` - 准备执行 skill
- `⚙️  [GUIDE]` - 开始执行 SkillEngine
- `🎬 [SKILL]` - Skill 开始执行
- `📝 [SKILL]` - Pipeline 信息
- `🤖 [LLM]` - LLM 处理开始
- `📄 [LLM]` - Prompt 配置加载
- `💬 [LLM]` - 准备调用 LLM
- `🌊 [LLM]` - 流式模式
- `✅ [LLM]` - LLM 调用完成

## 完整日志流程示例

当用户输入 "我想请假" 时，你会看到以下日志：

```log
# 1. Orchestrator 检测意图
INFO:app.agents.implementations.orchestrator_agent:OrchestratorAgent 意图: '我想请假' -> guide

# 2. 路由到 GuideAgent
INFO:app.agents.implementations.orchestrator_agent:🎯 [GUIDE] 路由到 GuideAgent | query='我想请假'

# 3. GuideAgent 开始执行
INFO:app.agents.implementations.guide_agent:🚀 [GUIDE] GuideAgent 开始执行 | query='我想请假' | session_id='xxx'

# 4. 开始匹配 skill
INFO:app.agents.implementations.guide_agent:🔍 [GUIDE] 开始匹配 guide skill | query='我想请假'

# 5. 匹配成功
INFO:app.agents.implementations.guide_agent:✅ [GUIDE] 匹配成功 | skill_id='leave_guide' | trigger='我想请假' | query='我想请假'

# 6. 准备执行 skill
INFO:app.agents.implementations.guide_agent:📋 [GUIDE] 准备执行 skill | skill_id='leave_guide'

# 7. 开始执行 SkillEngine
INFO:app.agents.implementations.guide_agent:⚙️  [GUIDE] 开始执行 SkillEngine | skill_id='leave_guide' | context_keys=['query', 'question', 'session_id', 'history']

# 8. Skill 开始执行
INFO:app.skills.engine:🎬 [SKILL] 开始执行 Skill | skill_id='leave_guide' | version='1.0' | type='guide'

# 9. Pipeline 信息
INFO:app.skills.engine:📝 [SKILL] Pipeline 步骤数: 1 | skill_id='leave_guide'

# 10. 执行 Pipeline 步骤
INFO:app.skills.engine:   [1/1] 执行步骤 | step='generate_answer' | processor='LLMGenerator' | params={'prompt_template': 'leave_guide', 'stream': False}

# 11. LLM 开始处理
INFO:app.skills.processors.llm:🤖 [LLM] 开始处理 | prompt_template='leave_guide' | stream=False

# 12. 加载 Prompt 配置
INFO:app.skills.processors.llm:📄 [LLM] 加载 Prompt 配置 | template_id='leave_guide' | name='请假指引'

# 13. 准备调用 LLM
INFO:app.skills.processors.llm:💬 [LLM] 准备调用 LLM | system_prompt_length=XXX | user_prompt_length=XXX

# 14. LLM 调用完成
INFO:app.skills.processors.llm:✅ [LLM] LLM 调用完成 | answer_length=XXX | prompt_template='leave_guide'

# 15. Skill 执行完成
INFO:app.skills.engine:✅ [SKILL] Skill 执行完成 | skill_id='leave_guide' | output_keys=['answer']

# 16. GuideAgent 执行成功
INFO:app.agents.implementations.guide_agent:✅ [GUIDE] Skill 执行成功 | skill_id='leave_guide' | answer_length=XXX
```

## 如何过滤日志

### 查看所有 GuideAgent 相关日志
```bash
# Linux/Mac
tail -f logs/app.log | grep "\[GUIDE\]"

# Windows PowerShell
Get-Content logs/app.log -Wait | Select-String "\[GUIDE\]"
```

### 查看 Skill 执行日志
```bash
# Linux/Mac
tail -f logs/app.log | grep "\[SKILL\]"

# Windows PowerShell
Get-Content logs/app.log -Wait | Select-String "\[SKILL\]"
```

### 查看 LLM 调用日志
```bash
# Linux/Mac
tail -f logs/app.log | grep "\[LLM\]"

# Windows PowerShell
Get-Content logs/app.log -Wait | Select-String "\[LLM\]"
```

### 查看完整流程（所有相关日志）
```bash
# Linux/Mac
tail -f logs/app.log | grep -E "\[GUIDE\]|\[SKILL\]|\[LLM\]"

# Windows PowerShell
Get-Content logs/app.log -Wait | Select-String -Pattern "\[GUIDE\]|\[SKILL\]|\[LLM\]"
```

## 关键日志点说明

### 1. 意图识别
```log
INFO:...orchestrator_agent:OrchestratorAgent 意图: '我想请假' -> guide
```
- 确认 Orchestrator 正确识别了 guide 意图
- 如果这里不是 `guide`，说明关键词匹配有问题

### 2. Skill 匹配
```log
INFO:...guide_agent:✅ [GUIDE] 匹配成功 | skill_id='leave_guide' | trigger='我想请假'
```
- 确认 GuideAgent 找到了 leave_guide skill
- 显示匹配的触发词
- 如果看到 `❌ [GUIDE] 未匹配到任何 guide skill`，说明 triggers 配置有问题

### 3. Prompt 模板加载
```log
INFO:...llm:📄 [LLM] 加载 Prompt 配置 | template_id='leave_guide' | name='请假指引'
```
- 确认使用了正确的 prompt 模板
- 如果这里是其他模板（如 `qa_rag`），说明 pipeline 配置有问题

### 4. LLM 调用
```log
INFO:...llm:💬 [LLM] 准备调用 LLM | system_prompt_length=XXX | user_prompt_length=XXX
INFO:...llm:✅ [LLM] LLM 调用完成 | answer_length=XXX | prompt_template='leave_guide'
```
- 确认 LLM 被正确调用
- 可以看到 prompt 的长度和返回答案的长度

## 故障排查

### 问题 1: 没有看到 `[GUIDE]` 日志
**可能原因**:
- Orchestrator 没有识别为 guide 意图
- 检查日志中的意图识别结果

**解决方法**:
- 确认查询包含触发关键词（"我想请假"、"怎么请假" 等）
- 检查 `orchestrator_agent.py` 中的 `_GUIDE_KW` 列表

### 问题 2: 看到 `❌ [GUIDE] 未匹配到任何 guide skill`
**可能原因**:
- leave_guide skill 未加载
- skill_type 不是 "guide"
- triggers 配置错误

**解决方法**:
```bash
# 运行测试脚本检查
python backend/test_leave_guide.py
```

### 问题 3: Prompt 模板不是 leave_guide
**可能原因**:
- SKILL.md 中的 pipeline 配置错误

**解决方法**:
- 检查 `backend/app/skills/definitions/leave_guide/SKILL.md`
- 确认 `params.prompt_template` 是 `leave_guide`

### 问题 4: LLM 返回的不是预期的对话
**可能原因**:
- Prompt 模板配置错误
- system prompt 不正确

**解决方法**:
- 检查 `backend/app/prompts/config.json` 中的 `leave_guide` 配置
- 确认 system prompt 包含正确的指引

## 调试技巧

### 1. 启用 DEBUG 日志
在 `backend/app/main.py` 中修改日志级别：
```python
logging.basicConfig(level=logging.DEBUG)
```

### 2. 实时监控日志
```bash
# 启动服务时直接查看日志
cd backend
uvicorn app.main:app --reload --log-level debug 2>&1 | grep -E "\[GUIDE\]|\[SKILL\]|\[LLM\]"
```

### 3. 使用测试脚本
```bash
# 端到端测试
python backend/test_guide_agent_e2e.py

# 基础测试
python backend/test_leave_guide.py
```

## 日志文件位置

根据你的配置，日志可能在：
- 控制台输出（默认）
- `logs/app.log`（如果配置了文件日志）
- Docker 容器日志（如果使用 Docker）

## 性能监控

通过日志可以监控性能：
```log
# 查看 LLM 调用时间
INFO:...llm:💬 [LLM] 准备调用 LLM | ...
INFO:...llm:✅ [LLM] LLM 调用完成 | ...
# 两条日志之间的时间差就是 LLM 调用耗时
```

## 总结

使用这些日志标记，你可以：
1. ✅ 确认 leave_guide skill 被正确使用
2. ✅ 追踪完整的执行流程
3. ✅ 快速定位问题
4. ✅ 监控性能
5. ✅ 调试配置问题

重启服务后，发送 "我想请假" 查询，你就能在日志中看到完整的执行流程！
