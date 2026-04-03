# Process 功能删除总结

## 已删除的内容

### 后端

1. ✅ **工具目录**
   - `backend/app/tools/implementations/process/` （整个目录）
   - 包括 `base_nodes.py`, `leave/balance_check.py` 等

2. ✅ **Processors**
   - `backend/app/skills/processors/process_executor.py`
   - `backend/app/skills/processors/guide_generator.py`

3. ✅ **Agents**
   - `backend/app/agents/implementations/process_agent.py`

4. ✅ **API Routes**
   - `backend/app/api/routes/flow_config.py`

5. ✅ **Orchestrator 简化**
   - 移除了所有 process 相关的路由逻辑
   - 移除了 `_get_process_skills()`, `_build_intent_prompt()`, `_llm_classify()` 等函数
   - 只保留 qa, memory, hybrid 三种意图

### 前端

1. ✅ **组件**
   - `frontend/src/components/Process/` (整个目录)
   - `frontend/src/views/FlowConfig/` (整个目录)

2. ✅ **ChatView 清理**
   - 移除了 ProcessCard 的 import
   - 移除了 ProcessCard 组件的使用

### Skills

1. ✅ **leave_guide 改回 qa 类型**
   - 不再使用 pipeline
   - 依赖 qa_rag 的 SKILL.md 指引

## 当前架构

### 意图路由（简化版）

```
用户输入
  ↓
OrchestratorAgent
  ├─ memory → MemoryAgent
  ├─ hybrid → QAAgent + MemoryAgent
  └─ qa → QAAgent → qa_rag skill
```

### 请假指引的工作方式

1. 用户："我想请假"
2. Orchestrator: 识别为 `qa` 意图
3. QA Agent: 调用 `qa_rag` skill
4. LLM: 根据 `qa_rag/SKILL.md` 中的"特殊场景处理 - 请假相关问题"指引回答
5. 返回：请假操作指引

## 保留的内容

1. ✅ `leave_guide/SKILL.md` - 作为文档参考
2. ✅ `leave_guide/references/请假操作指引.md` - 可选择上传到知识库
3. ✅ `qa_rag/SKILL.md` - 包含请假指引的特殊场景处理

## 下一步

1. **重启后端服务**
2. 测试"我想请假"，应该走 qa_rag 流程
3. 如果需要更好的效果，可以将 `请假操作指引.md` 上传到知识库

## 清理的文件列表

### 后端
- app/tools/implementations/process/ (目录)
- app/skills/processors/process_executor.py
- app/skills/processors/guide_generator.py
- app/agents/implementations/process_agent.py
- app/api/routes/flow_config.py

### 前端
- frontend/src/components/Process/ (目录)
- frontend/src/views/FlowConfig/ (目录)
- frontend/src/views/Chat/ChatView.vue (移除 ProcessCard 引用)

## 系统现在的特点

- ✅ 更简单：没有复杂的流程引擎
- ✅ 更灵活：通过 LLM 自然对话处理
- ✅ 更易维护：只需修改 SKILL.md 中的指引
- ✅ 统一架构：所有请求都走 QA 流程
