# GuideAgent 日志快速参考

## 🎯 关键日志标记

当用户输入 "我想请假" 时，你会看到这些日志：

```log
# 1️⃣ 意图识别
INFO:...orchestrator_agent:OrchestratorAgent 意图: '我想请假' -> guide

# 2️⃣ 路由到 GuideAgent
INFO:...orchestrator_agent:🎯 [GUIDE] 路由到 GuideAgent | query='我想请假'

# 3️⃣ GuideAgent 启动
INFO:...guide_agent:🚀 [GUIDE] GuideAgent 开始执行 | query='我想请假' | session_id='xxx'

# 4️⃣ 匹配 Skill
INFO:...guide_agent:🔍 [GUIDE] 开始匹配 guide skill | query='我想请假'
INFO:...guide_agent:✅ [GUIDE] 匹配成功 | skill_id='leave_guide' | trigger='我想请假'

# 5️⃣ 执行 Skill
INFO:...guide_agent:📋 [GUIDE] 准备执行 skill | skill_id='leave_guide'
INFO:...guide_agent:⚙️  [GUIDE] 开始执行 SkillEngine | skill_id='leave_guide'

# 6️⃣ Skill Engine
INFO:...engine:🎬 [SKILL] 开始执行 Skill | skill_id='leave_guide' | version='1.0' | type='guide'
INFO:...engine:📝 [SKILL] Pipeline 步骤数: 1 | skill_id='leave_guide'
INFO:...engine:   [1/1] 执行步骤 | step='generate_answer' | processor='LLMGenerator' | params={'prompt_template': 'leave_guide', 'stream': False}

# 7️⃣ LLM 处理
INFO:...llm:🤖 [LLM] 开始处理 | prompt_template='leave_guide' | stream=False
INFO:...llm:📄 [LLM] 加载 Prompt 配置 | template_id='leave_guide' | name='请假指引'
INFO:...llm:💬 [LLM] 准备调用 LLM | system_prompt_length=491 | user_prompt_length=4

# 8️⃣ LLM 完成
INFO:...llm:✅ [LLM] LLM 调用完成 | answer_length=138 | prompt_template='leave_guide'

# 9️⃣ Skill 完成
INFO:...engine:✅ [SKILL] Skill 执行完成 | skill_id='leave_guide' | output_keys=['answer']

# 🔟 GuideAgent 完成
INFO:...guide_agent:✅ [GUIDE] Skill 执行成功 | skill_id='leave_guide' | answer_length=138
```

## 🔍 如何验证 leave_guide 被使用

### 方法 1: 运行测试脚本
```bash
python backend/test_guide_with_logs.py
```

查找这些关键日志：
- ✅ `skill_id='leave_guide'` - 确认使用了 leave_guide skill
- ✅ `prompt_template='leave_guide'` - 确认使用了 leave_guide prompt
- ✅ `type='guide'` - 确认 skill 类型正确

### 方法 2: 在生产环境查看日志
```bash
# 实时查看所有 GUIDE 相关日志
tail -f logs/app.log | grep "\[GUIDE\]"

# 或者在 Windows PowerShell
Get-Content logs/app.log -Wait | Select-String "\[GUIDE\]"
```

### 方法 3: 检查特定标记
```bash
# 查看是否使用了 leave_guide
tail -f logs/app.log | grep "leave_guide"
```

## ✅ 成功标志

如果看到以下日志，说明 leave_guide 正在被使用：

1. ✅ `skill_id='leave_guide'` - Skill 被匹配
2. ✅ `prompt_template='leave_guide'` - Prompt 被加载
3. ✅ `name='请假指引'` - 正确的 Prompt 配置
4. ✅ `type='guide'` - 正确的 Skill 类型

## ❌ 问题排查

### 如果没有看到 `[GUIDE]` 日志
**原因**: 意图识别失败
**检查**: 
```log
INFO:...orchestrator_agent:OrchestratorAgent 意图: '我想请假' -> qa  # ❌ 应该是 guide
```
**解决**: 确认查询包含触发关键词

### 如果看到 `❌ [GUIDE] 未匹配到任何 guide skill`
**原因**: Skill 未加载或配置错误
**检查**: 运行 `python backend/test_leave_guide.py`
**解决**: 确认 SKILL.md 中 `skill_type: guide`

### 如果 prompt_template 不是 leave_guide
**原因**: Pipeline 配置错误
**检查**: 
```log
INFO:...engine:   [1/1] 执行步骤 | ... | params={'prompt_template': 'qa_rag', ...}  # ❌ 应该是 leave_guide
```
**解决**: 检查 SKILL.md 中的 pipeline 配置

## 📊 日志统计

完整的 leave_guide 执行会产生：
- 🎯 1 条路由日志
- 🚀 1 条启动日志
- 🔍 1 条匹配开始日志
- ✅ 1 条匹配成功日志
- 📋 1 条准备执行日志
- ⚙️  1 条 SkillEngine 启动日志
- 🎬 1 条 Skill 执行日志
- 📝 1 条 Pipeline 信息日志
- 🤖 1 条 LLM 处理日志
- 📄 1 条 Prompt 加载日志
- 💬 1 条 LLM 调用准备日志
- ✅ 3 条完成日志（LLM、Skill、GuideAgent）

**总计**: 约 15 条关键日志

## 🚀 快速测试命令

```bash
# 测试并查看日志
python backend/test_guide_with_logs.py

# 只看关键信息
python backend/test_guide_with_logs.py 2>&1 | grep -E "GUIDE|SKILL|LLM"

# 检查 skill 加载
python backend/test_leave_guide.py
```

## 📝 日志级别

- `INFO` - 正常流程日志（默认）
- `DEBUG` - 详细调试信息
- `WARNING` - 警告信息
- `ERROR` - 错误信息

修改日志级别：
```python
# 在 main.py 中
logging.basicConfig(level=logging.DEBUG)  # 显示更多细节
```

## 🎉 验证成功

当你看到完整的日志链路，并且包含：
- ✅ `skill_id='leave_guide'`
- ✅ `prompt_template='leave_guide'`
- ✅ `name='请假指引'`
- ✅ LLM 返回了收集信息的对话

说明 leave_guide 技能已经成功运行！
