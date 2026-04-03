# 多轮对话修复总结

## 问题

用户询问婚假信息后，再次说明"我可以正常申请婚假，我需要怎么做"，但系统输出了空白。

## 根本原因

发现了两个问题：

### 1. Triggers 不完整
`leave_guide` 的 triggers 中缺少"婚假"、"产假"、"陪产假"、"高温假"等关键词，导致无法匹配到 skill。

### 2. 缺少历史记录支持
LLM 调用时没有传递对话历史（history），导致多轮对话时 LLM 无法理解上下文。

## 解决方案

### 1. 更新 Triggers

**文件**: `backend/app/skills/definitions/leave_guide/SKILL.md`

**修改前**:
```yaml
triggers:
  - 请假
  - 休假
  - 年假
  - 病假
  - 事假
```

**修改后**:
```yaml
triggers:
  - 请假
  - 休假
  - 年假
  - 病假
  - 事假
  - 婚假
  - 产假
  - 陪产假
  - 高温假
```

### 2. 添加历史记录支持

#### 修改 `call_llm` 函数

**文件**: `backend/app/core/llm.py`

添加 `history` 参数支持：

```python
async def call_llm(prompt: str, system_prompt: str = "", history: list = None) -> str:
    """
    调用 LLM
    
    Args:
        prompt: 用户提示词
        system_prompt: 系统提示词
        history: 对话历史 [{"role": "user", "content": "..."}, ...]
    """
    client = await get_llm_async()
    
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    
    # 添加历史对话
    if history:
        messages.extend(history)
    
    # 添加当前用户消息
    messages.append({"role": "user", "content": prompt})
    
    response = await client.chat.completions.create(
        model=settings.llm_model,
        messages=messages,
        temperature=0.7
    )
    
    return response.choices[0].message.content
```

#### 修改 `LLMGenerator`

**文件**: `backend/app/skills/processors/llm.py`

传递 history 给 LLM：

```python
# 获取对话历史
history = context.get("history", [])

logger.info("💬 [LLM] 准备调用 LLM | system_prompt_length=%d | user_prompt_length=%d | history_length=%d", 
           len(system_prompt), len(user_prompt), len(history))

# 调用 LLM 时传递 history
answer = await call_llm(user_prompt, system_prompt, history=history)
```

## 测试结果

### 第1轮对话
```
用户: 我想请婚假

助手: 好的，申请婚假是人生中的重要时刻之一，很高兴为您服务！😊

为了帮您顺利完成婚假申请，我需要先了解一些基本信息。请您配合回答以下几个问题：

**第一步：确认婚假基本信息**

请问您的**结婚登记日期**是什么时候呢？
...
```

### 第2轮对话（带历史记录）
```
用户: 我可以正常申请婚假，我需要怎么做

日志: history_length=2  ← 成功传递了历史记录

助手: 太好了！既然您符合婚假申请条件，接下来我会一步步引导您完成整个流程。为了给您提供**个性化、准确的操作指引**，我还需要确认几个关键信息：

✅ **第一步：请您确认以下信息**

1. **结婚证登记日期**是哪一天？
2. **您计划从哪天开始休婚假**？
3. **打算请几天假**？
...
```

## 验证

运行测试脚本：

```bash
python backend/test_multi_turn_with_history.py
```

### 关键日志

```log
# 第1轮
✅ [GUIDE] 匹配成功 | skill_id='leave_guide' | trigger='婚假'
💬 [LLM] 准备调用 LLM | history_length=0

# 第2轮
✅ [GUIDE] 匹配成功 | skill_id='leave_guide' | trigger='婚假'
💬 [LLM] 准备调用 LLM | history_length=2  ← 历史记录已传递
✅ [LLM] LLM 调用完成 | answer_length=462
```

## 修改的文件

1. `backend/app/skills/definitions/leave_guide/SKILL.md` - 添加完整的 triggers
2. `backend/app/core/llm.py` - 添加 history 参数支持
3. `backend/app/skills/processors/llm.py` - 传递 history 给 LLM
4. `backend/test_multi_turn_with_history.py` - 测试脚本（新增）

## 现在的工作流程

```
用户第1轮: "我想请婚假"
  ↓
Orchestrator: guide 意图
  ↓
GuideAgent: 匹配 trigger="婚假" → leave_guide
  ↓
LLM: 无历史记录，开始收集信息
  ↓
助手: 询问结婚日期、天数等

用户第2轮: "我可以正常申请婚假，我需要怎么做"
  ↓
Orchestrator: guide 意图
  ↓
GuideAgent: 匹配 trigger="婚假" → leave_guide
  ↓
LLM: 带历史记录（包含第1轮对话）
  ↓
助手: 理解上下文，继续收集信息或生成指引
```

## 优势

1. ✅ **完整的 triggers** - 支持所有假期类型
2. ✅ **多轮对话** - LLM 能理解上下文
3. ✅ **个性化回复** - 根据对话历史调整回复
4. ✅ **连贯性** - 对话流畅自然

## 未来优化

1. **会话管理** - 在数据库中持久化 history
2. **上下文压缩** - 当 history 过长时自动压缩
3. **意图切换** - 检测用户是否切换了话题
4. **状态追踪** - 记录对话进度（收集了哪些信息）

重启服务后，多轮对话将完美工作！
