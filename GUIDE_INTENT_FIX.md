# Guide Intent 修复 - 解决多轮对话空响应问题

## 问题描述

用户在多轮对话中（例如先问"我想请婚假"，然后回答"2024年4月24号"）时，系统返回空响应。

### 日志分析

```
✅ [GUIDE] Skill 执行成功 | answer_length=997  ← GuideAgent 返回 997 字符
[KB Optimize] Query: '流程是什么'  ← QA Agent 又执行了一次！
WARNING:[V2] 空响应，跳过持久化  ← 最终响应为空
```

## 根本原因

有两个问题导致空响应：

### 问题 1: GuideAgent 缺少 intent 字段

GuideAgent 返回的结果没有 `intent` 字段，导致 Chat API 无法识别这是 guide 意图的响应。

### 问题 2: OrchestratorAgent 的意图识别不考虑历史上下文

当用户在多轮对话中回答"2024年4月24号"时：
1. LLM 意图识别只看当前查询，不考虑历史对话
2. "2024年4月24号"被识别为 "qa" 意图（查询日期信息）
3. 路由到 QA Agent，从知识库检索，返回不相关的内容或空响应
4. QA Agent 的结果也没有 `intent` 字段
5. Chat API 的 `orch_handled` 检查失败，继续调用 QA Agent（二次执行）

### 代码层面原因

**backend/app/agents/implementations/guide_agent.py**
```python
return {
    "answer": answer,
    "session_id": session_id,
    # ❌ 缺少 "intent": "guide" 字段
}
```

**backend/app/agents/implementations/orchestrator_agent.py**
```python
# 意图识别不考虑历史上下文
async def detect_intent_with_llm(query: str) -> str:  # ❌ 没有 history 参数
    user_prompt = f"用户查询：{query}\n\n请判断意图类型："
    # ...

# QA Agent 结果没有 intent 字段
return await agent_engine.execute(
    "qa_agent",
    {"query": query, "question": query, "history": history, "session_id": session_id},
)  # ❌ 没有添加 intent 字段
```

**backend/app/api/routes/chat.py**
```python
orch_handled = (
    orch_result.get("ui_components") is not None or
    orch_result.get("process_state") is not None or
    orch_result.get("intent") in ("confirm", "memory", "hybrid")  # ❌ 缺少 "guide"
)
```

## 解决方案

### 修改 1: GuideAgent 返回 intent 字段

**文件**: `backend/app/agents/implementations/guide_agent.py`

在所有返回语句中添加 `"intent": "guide"` 字段：

```python
# 成功执行
return {
    "answer": answer,
    "session_id": session_id,
    "intent": "guide",  # ✅ 新增
}

# 未找到匹配 skill
return {
    "answer": "抱歉，我暂时无法提供该流程的指引。请联系管理员。",
    "intent": "guide",  # ✅ 新增
}

# 执行失败
return {
    "answer": "抱歉，生成指引时出现错误。请稍后再试。",
    "session_id": session_id,
    "intent": "guide",  # ✅ 新增
}

# 空查询
return {
    "answer": "请问您需要什么帮助？",
    "intent": "guide"  # ✅ 新增
}
```

### 修改 2: OrchestratorAgent 确保所有路径都有 intent 字段

**文件**: `backend/app/agents/implementations/orchestrator_agent.py`

```python
# Guide 意图
if intent == "guide":
    logger.info("🎯 [GUIDE] 路由到 GuideAgent | query='%s'", query)
    result = await agent_engine.execute(
        "guide_agent",
        {"query": query, "session_id": session_id, "history": history},
    )
    # 确保 intent 字段存在
    if "intent" not in result:
        result["intent"] = "guide"  # ✅ 新增
    return result

# QA 意图（默认）
result = await agent_engine.execute(
    "qa_agent",
    {"query": query, "question": query, "history": history, "session_id": session_id},
)
# 确保 intent 字段存在
if "intent" not in result:
    result["intent"] = "qa"  # ✅ 新增
return result
```

### 修改 3: 意图识别考虑历史上下文

**文件**: `backend/app/agents/implementations/orchestrator_agent.py`

```python
async def detect_intent_with_llm(query: str, history: list = None) -> str:  # ✅ 添加 history 参数
    """使用 LLM 进行意图识别
    
    Args:
        query: 当前查询
        history: 历史对话记录（用于判断是否是多轮对话的延续）
    """
    try:
        # 检查是否是多轮对话的延续
        context_hint = ""
        if history and len(history) >= 2:
            # 获取最近一轮对话
            last_user_msg = None
            last_assistant_msg = None
            for msg in reversed(history):
                if msg.get("role") == "assistant" and not last_assistant_msg:
                    last_assistant_msg = msg.get("content", "")
                elif msg.get("role") == "user" and not last_user_msg:
                    last_user_msg = msg.get("content", "")
                if last_user_msg and last_assistant_msg:
                    break
            
            # 如果上一轮是流程指引相关的对话，添加上下文提示
            if last_assistant_msg and any(keyword in last_assistant_msg for keyword in 
                ["申请", "流程", "步骤", "办理", "需要", "材料", "指引", "请问", "确认"]):
                context_hint = f"\n\n上下文：用户上一轮问了「{last_user_msg[:50]}」，系统回复了流程指引相关内容。当前查询可能是对上一轮对话的延续。"
        
        user_prompt = f"用户查询：{query}{context_hint}\n\n请判断意图类型："
        # ...
```

### 修改 4: Chat API 识别 guide 意图

**文件**: `backend/app/api/routes/chat.py`

```python
orch_handled = (
    orch_result.get("ui_components") is not None or
    orch_result.get("process_state") is not None or
    orch_result.get("intent") in ("confirm", "memory", "hybrid", "guide")  # ✅ 添加 "guide"
)
```

## 执行流程对比

### 修复前（错误）

```
用户: "我想请婚假"
  ↓
OrchestratorAgent (LLM 意图识别，无历史上下文)
  ↓ intent = "guide"
GuideAgent
  ↓ 返回 {"answer": "...", session_id: "..."}  ← 缺少 intent
Chat API 检查 orch_handled
  ↓ orch_handled = False (因为没有 intent 字段)
QA Agent 执行
  ↓
最终响应: 可能正确，但执行了两次 ❌

---

用户: "2024年4月24号"（多轮对话延续）
  ↓
OrchestratorAgent (LLM 意图识别，无历史上下文)
  ↓ intent = "qa" ← 错误！应该是 "guide"
QA Agent
  ↓ 返回 {"answer": "...", sources: [...]}  ← 缺少 intent
Chat API 检查 orch_handled
  ↓ orch_handled = False (因为没有 intent 字段)
QA Agent 再次执行
  ↓ 返回空响应
最终响应: 空 ❌
```

### 修复后（正确）

```
用户: "我想请婚假"
  ↓
OrchestratorAgent (LLM 意图识别，无历史上下文)
  ↓ intent = "guide"
GuideAgent
  ↓ 返回 {"answer": "...", "intent": "guide"}  ✅
Chat API 检查 orch_handled
  ↓ orch_handled = True (因为 intent="guide" 在列表中)
直接返回 GuideAgent 的答案
  ↓
最终响应: 正确 ✅

---

用户: "2024年4月24号"（多轮对话延续）
  ↓
OrchestratorAgent (LLM 意图识别，带历史上下文)
  ↓ 检测到上一轮是流程指引对话
  ↓ 添加上下文提示给 LLM
  ↓ intent = "guide" ✅ 正确！
GuideAgent (历史记录匹配)
  ↓ 返回 {"answer": "...", "intent": "guide"}
Chat API 检查 orch_handled
  ↓ orch_handled = True
直接返回 GuideAgent 的答案
  ↓
最终响应: 正确的多轮对话延续 ✅
```

## 测试验证

运行测试脚本：
```bash
cd backend
python diagnose_guide_flow.py
```

测试结果：
```
【第一轮】用户: 我想请婚假
✅ OrchestratorAgent 返回:
   - intent: guide
   - answer 长度: 104
✅ Chat API orch_handled 检查: True
✅ 正确：Chat API 会直接返回结果，不调用 QA Agent

【第二轮】用户: 2024年4月24号
✅ OrchestratorAgent 返回:
   - intent: guide  ← 正确识别为 guide 意图！
   - answer 长度: 281
✅ Chat API orch_handled 检查: True
✅ 正确：Chat API 会直接返回结果，不调用 QA Agent
```

## 影响范围

- ✅ 修复多轮对话中短查询返回空响应的问题
- ✅ 意图识别现在考虑历史上下文，更准确
- ✅ 确保所有 Agent 返回的结果都有 intent 字段
- ✅ 防止 Chat API 重复调用 Agent
- ✅ 保持其他意图（qa, memory, hybrid）的正常工作
- ✅ 不影响现有功能

## 部署说明

1. 重启后端服务以加载更新的代码
2. 测试场景：
   - 询问"我想请婚假" → 应返回指引
   - 继续回答"2024年4月24号" → 应返回多轮对话延续（不是空响应）
   - 询问"年假有多少天" → 应走 QA Agent（知识查询）

## 相关文件

- `backend/app/api/routes/chat.py` - Chat API 路由
- `backend/app/agents/implementations/guide_agent.py` - GuideAgent 实现
- `backend/app/agents/implementations/orchestrator_agent.py` - OrchestratorAgent 意图识别（带历史上下文）
- `backend/diagnose_guide_flow.py` - 测试脚本
