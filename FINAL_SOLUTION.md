# 最终解决方案：请假指引功能

## 问题分析

当前架构中：
- `skill_type: process` 的 skill 会被 orchestrator 识别并路由
- `skill_type: qa` 的 skill 不会被单独路由，统一走 `qa_rag`
- `triggers` 配置只对 `process` 类型有效

所以 `leave_guide` 设置为 `qa` 类型后，不会被特殊处理，而是走通用的知识库问答。

## 解决方案

### 方案 A：将指引内容放入知识库（推荐）

1. 创建请假指引文档（已完成）：
   - `backend/app/skills/definitions/leave_guide/references/请假操作指引.md`

2. 将文档上传到知识库：
   - 通过前端上传功能
   - 或使用 API 直接导入

3. 用户询问"我想请假"时：
   - orchestrator 识别为 `qa` 意图
   - qa_agent 调用 `qa_rag` skill
   - 从知识库检索到请假指引文档
   - 返回指引内容

**优点**：
- 无需修改代码
- 利用现有的 RAG 能力
- 指引内容可以随时更新

**缺点**：
- 需要手动上传文档到知识库
- 依赖检索质量

### 方案 B：修改 orchestrator 支持 QA 类型的 skill 路由

需要修改代码，让 orchestrator 也能识别 QA 类型 skill 的 triggers。

**步骤**：
1. 修改 `_get_process_skills()` 也返回有 triggers 的 QA skill
2. 修改意图分类逻辑，支持 `qa:<skill_id>`
3. 修改 QA Agent，根据 skill_id 调用对应的 skill

**优点**：
- 更灵活的路由机制
- 不依赖知识库

**缺点**：
- 需要修改核心代码
- 增加系统复杂度

### 方案 C：创建专门的 LeaveGuideAgent

创建一个新的 Agent 专门处理请假指引。

**优点**：
- 职责清晰
- 不影响现有逻辑

**缺点**：
- 需要开发新 Agent
- 需要修改 orchestrator 路由逻辑

## 推荐实施步骤（方案 A）

### 1. 上传指引文档到知识库

使用前端上传功能，或运行以下脚本：

```python
# upload_leave_guide.py
import asyncio
from pathlib import Path
from app.agents.implementations.document_agent import DocumentAgent

async def main():
    agent = DocumentAgent()
    doc_path = Path("app/skills/definitions/leave_guide/references/请假操作指引.md")
    
    result = await agent.run({
        "file_path": str(doc_path),
        "filename": "请假操作指引.md"
    })
    
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

### 2. 测试

用户：我想请假
系统：[从知识库检索到请假指引文档，返回指引内容]

### 3. 优化（可选）

如果检索效果不好，可以：
- 调整文档内容，增加关键词
- 调整 chunk_size 和 chunk_overlap
- 使用 reranker 提升检索精度

## 临时解决方案

如果不想上传文档，可以直接在 `qa_rag` 的 SKILL.md 中添加请假指引：

编辑 `backend/app/skills/definitions/qa_rag/SKILL.md`，在指引部分添加：

```markdown
## 请假相关问题

当用户询问请假相关问题时，提供以下指引：

### 假期类型
- 年假、病假、事假、婚假、产假、陪产假、高温假（6-9月）

### 申请流程
1. 发起请假申请
2. 直属上级审批
3. HR 备案

### 申请入口
https://oa.company.com/leave

### 申请模板
【年假申请】
申请人：xxx
时间：xxxx 年 xx 月 xx 日 - xxxx 年 xx 月 xx 日，共 X 天
事由：个人事务

### 注意事项
- 请提前 3 天申请
- 审批时间：1-3 个工作日
```

这样 LLM 在回答时会参考这些指引。
