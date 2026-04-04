# Auth Context 传递问题修复

## 问题描述

假期余额查询功能在实际使用时，auth_context 始终为 guest 用户：
```
auth_context：{'username': '', 'user_id': None, 'role': 'guest'}
```

导致用户无法查询自己的假期余额。

## 根本原因

1. **后端问题**：`chat.py` 中的 `_get_username()` 函数只提取了用户名，没有查询数据库获取完整的用户信息（user_id, role 等）
2. **前端问题**：`askStreamV2` 使用 `fetch` 直接发送请求，没有附加 JWT token 到 Authorization header

## 修复方案

### 1. 后端修复 (backend/app/api/routes/chat.py)

**修改前**：
```python
def _get_username() -> str:
    try:
        auth = http_request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return ""
        from app.api.dependencies import decode_token
        payload = decode_token(auth[7:])
        return payload.get("sub", "")
    except Exception:
        return ""

current_username = _get_username()
```

**修改后**：
```python
async def _get_auth_context() -> Dict[str, Any]:
    """提取认证上下文"""
    try:
        auth = http_request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return {"username": "", "user_id": None, "role": "guest"}
        
        from app.api.dependencies import decode_token, get_user_by_username
        payload = decode_token(auth[7:])
        username = payload.get("sub", "")
        
        if not username:
            return {"username": "", "user_id": None, "role": "guest"}
        
        # 从数据库查询用户信息
        user = await get_user_by_username(username)
        if not user:
            return {"username": username, "user_id": None, "role": "guest"}
        
        return {
            "username": username,
            "user_id": str(user["_id"]),
            "role": user.get("role", "user"),
            "is_active": user.get("is_active", True)
        }
    except Exception as e:
        logger.warning(f"Failed to extract auth context: {e}")
        return {"username": "", "user_id": None, "role": "guest"}

auth_context = await _get_auth_context()
current_username = auth_context["username"]
```

**关键改进**：
- 从 JWT token 解析出 username
- 查询数据库获取完整用户信息（包括 user_id）
- 构建完整的 auth_context 对象
- 将 auth_context 传递给 OrchestratorAgent

### 2. 前端修复 (frontend/src/api/index.ts)

**修改前**：
```typescript
const response = await fetch('/api/chat/v2/ask/stream', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ question, session_id: sessionId }),
  signal
})
```

**修改后**：
```typescript
// 获取 JWT token 并添加到请求头
const token = localStorage.getItem('auth_token')
const headers: Record<string, string> = {
  'Content-Type': 'application/json'
}
if (token) {
  headers['Authorization'] = `Bearer ${token}`
}

const response = await fetch('/api/chat/v2/ask/stream', {
  method: 'POST',
  headers,
  body: JSON.stringify({ question, session_id: sessionId }),
  signal
})
```

**关键改进**：
- 从 localStorage 读取 JWT token
- 将 token 添加到 Authorization header
- 确保后端能够解析用户身份

### 3. 假期类型提取 (backend/app/agents/implementations/orchestrator_agent.py)

添加 `_extract_leave_type()` 方法，从用户查询中智能提取假期类型：

```python
def _extract_leave_type(self, query: str) -> str:
    """从查询中提取假期类型"""
    leave_type_keywords = {
        "年假": ["年假", "年休假", "带薪年假"],
        "病假": ["病假"],
        "事假": ["事假"],
        "婚假": ["婚假", "结婚假"],
        "产假": ["产假", "生育假"],
        "陪产假": ["陪产假", "护理假", "陪护假"],
        "高温假": ["高温假", "防暑降温假"]
    }
    
    for leave_type, keywords in leave_type_keywords.items():
        for keyword in keywords:
            if keyword in query:
                return leave_type
    
    return None
```

在处理 `leave_balance` 意图时调用：
```python
leave_type = self._extract_leave_type(query)
if leave_type:
    logger.info("🔍 [LEAVE_BALANCE] 识别到假期类型: %s", leave_type)

result = await tool_executor.execute_tool(
    "check_leave_balance",
    {"leave_type": leave_type} if leave_type else {},
    auth_context=input_data.get("auth_context")
)
```

**效果**：
- "我的年假还剩多少" → 只返回年假
- "我的假期余额" → 返回所有假期类型

### 4. 其他修复

#### backend/app/api/routes/chat.py (路由处理)
添加 `leave_balance` 到 `orch_handled` 检查，防止重复调用 QAAgent：
```python
orch_handled = (
    orch_result.get("ui_components") is not None or
    orch_result.get("process_state") is not None or
    orch_result.get("intent") in ("confirm", "memory", "hybrid", "guide", "leave_balance")  # 新增
)
```

处理不同类型的响应字段（`answer` 或 `message`）：
```python
full_response = orch_result.get("answer") or orch_result.get("message", "")
```

#### backend/app/main.py
添加 LeaveBalanceTool 到导入列表，确保工具在启动时注册：
```python
from app.tools.implementations import (
    SearchKnowledgeTool, SystemStatusTool,
    ListDocumentsTool, GetDocumentInfoTool,
    IntroduceAssistantTool, GetAssistantStatusTool,
    LeaveBalanceTool  # 新增
)
```

#### backend/app/tools/implementations/leave_balance.py
简化审计日志，使用标准 logger 而不是 AuditLogger（因为 AuditLogger 需要 Request 对象）：
```python
async def _log_audit(self, ...):
    """记录审计日志（简化版）"""
    try:
        logger.info(
            f"[AUDIT] user={username} (id={user_id}) action={action} "
            f"resource={leave_type or 'all'} success={success} details={details}"
        )
    except Exception as e:
        logger.error(f"记录审计日志失败: {e}", exc_info=True)
```

## 验证测试

创建了两个测试脚本验证完整流程：

### 1. 单元测试 (backend/test_auth_context.py)
验证 auth_context 传递流程：

```bash
cd backend
python test_auth_context.py
```

### 2. 端到端测试 (backend/test_leave_balance_e2e.py)
验证从 HTTP 请求到返回结果的完整流程：

```bash
cd backend
python test_leave_balance_e2e.py
```

**测试结果**：
```
✅ 测试通过！auth_context 正确传递

📊 hr 的假期余额
查询时间：2026-04-04 20:33:48

• 事假：无限额（按需申请）
• 产假：总额 98.0 天，已用 29.4 天，剩余 68.6 天
• 婚假：总额 10.0 天，已用 3.0 天，剩余 7.0 天
• 年假：总额 10.0 天，已用 3.0 天，剩余 7.0 天
• 病假：无限额（按需申请）
• 陪产假：总额 15.0 天，已用 4.5 天，剩余 10.5 天
• 高温假：总额 5.0 天，已用 1.5 天，剩余 3.5 天
```

## 数据流图

```
Frontend (askStreamV2)
  ↓ [Authorization: Bearer <JWT>]
Backend (chat.py)
  ↓ [_get_auth_context() 解析 JWT]
  ↓ [查询数据库获取用户信息]
  ↓ [构建 auth_context]
OrchestratorAgent
  ↓ [识别 leave_balance 意图]
  ↓ [传递 auth_context]
ToolExecutor
  ↓ [execute_tool(..., auth_context=...)]
LeaveBalanceTool
  ↓ [验证 auth_context]
  ↓ [查询用户余额]
  ✓ [返回余额信息]
```

## 测试用户

系统中有两个测试用户（密码都是 `123`）：

1. **hr** (HR 角色)
   - user_id: `7afcb609-df93-4da5-ad6e-319832a5c2e8`
   - 有完整的假期余额数据

2. **bob** (员工角色)
   - user_id: `94ffac08-abdf-4ab3-b78f-53ba4e3f15c6`
   - 有完整的假期余额数据

## 后续工作

- [ ] 前端需要重新构建并部署
- [ ] 测试实际登录用户查询假期余额
- [ ] 验证权限隔离（用户只能查询自己的余额）
- [ ] 集成到请假流程中的余额检查
