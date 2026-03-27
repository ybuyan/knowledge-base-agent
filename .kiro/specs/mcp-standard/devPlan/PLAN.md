# 快捷提问功能实现计划

## 需求分析

在 AI 回答内容的下方添加快捷提问按钮，提问内容基于当前问题和回答内容自动生成，数量可通过 setting 配置。

## 实现方案

### 1. 后端实现

#### 1.1 添加配置项
在 `constraint_config.py` 的 `fallback` 配置中添加：
```python
"suggest_questions": {
    "enabled": True,
    "count": 3,  # 生成的快捷提问数量
    "types": ["相关追问", "深入探索", "对比分析"]  # 提问类型
}
```

#### 1.2 创建快捷提问生成服务
新建 `app/services/suggestion_generator.py`：
- 基于问题和回答内容生成相关提问
- 使用 LLM 生成智能提问
- 支持不同类型的提问（追问、探索、对比）

#### 1.3 更新 API 响应
在 `/api/chat/v2/ask/stream` 的 `done` 响应中添加 `suggested_questions` 字段

### 2. 前端实现

#### 2.1 更新响应类型
在 `frontend/src/stores/chat.ts` 中添加 `suggestedQuestions` 字段

#### 2.2 创建快捷提问组件
在回答消息下方显示快捷提问按钮

#### 2.3 添加配置页面
在 Setting 页面添加快捷提问数量配置

## 文件修改清单

| 文件 | 修改内容 |
|------|---------|
| `backend/app/core/constraint_config.py` | 添加 suggest_questions 配置 |
| `backend/app/services/suggestion_generator.py` | 新建：快捷提问生成服务 |
| `backend/app/services/qa_agent.py` | 集成快捷提问生成 |
| `backend/app/services/response_builder.py` | 添加 suggested_questions 支持 |
| `backend/config/constraints.json` | 添加配置项 |
| `frontend/src/stores/chat.ts` | 添加 suggestedQuestions 字段 |
| `frontend/src/views/Chat/ChatView.vue` | 显示快捷提问按钮 |
| `frontend/src/views/Settings/Constraints.vue` | 添加配置项 |

## 实现步骤

1. **后端配置** - 添加快捷提问配置项
2. **后端服务** - 创建快捷提问生成服务
3. **后端集成** - 在 QA 流程中生成快捷提问
4. **前端展示** - 显示快捷提问按钮
5. **前端配置** - 添加设置页面配置项
6. **测试验证** - 完整功能测试
