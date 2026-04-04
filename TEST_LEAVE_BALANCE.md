# 假期余额查询功能测试指南

## 前置条件

1. 确保后端服务正在运行
2. 确保前端已重新构建（包含 Authorization header 修复）
3. 确保数据库中有测试用户和假期余额数据

## 功能特性

### 1. 智能假期类型识别

系统会自动从用户查询中提取假期类型：

- **指定类型查询**：
  - "我的年假还剩多少" → 只返回年假信息
  - "查询病假余额" → 只返回病假信息
  - "婚假还有多少天" → 只返回婚假信息

- **全部查询**：
  - "我的假期余额" → 返回所有假期类型
  - "查询我的假期" → 返回所有假期类型

### 2. 格式化输出

- **单个假期类型**：简洁格式
  ```
  📊 hr 的年假余额
  查询时间：2026-04-04 20:54:43
  
  • 总额度：10.0 天
  • 已使用：3.0 天
  • 剩余：7.0 天
  ```

- **所有假期类型**：列表格式
  ```
  📊 hr 的假期余额
  查询时间：2026-04-04 20:54:43
  
  • 年假：总额 10.0 天，已用 3.0 天，剩余 7.0 天
  • 病假：无限额（按需申请）
  • 婚假：总额 10.0 天，已用 3.0 天，剩余 7.0 天
  ...
  ```

### 3. 余额预警

当剩余天数少于总额度的 20% 时，会显示 ⚠️ 警告标志。

## 测试步骤

### 1. 登录系统

使用测试账号登录：
- 用户名：`hr` 或 `bob`
- 密码：`123`

### 2. 测试直接查询假期余额

在聊天界面输入以下任一查询：
- "我的年假还剩多少"
- "查询我的假期余额"
- "我的假期还有多少天"
- "年假余额"
- "剩余假期"

**预期结果**：
系统应该返回当前用户的假期余额信息，格式如下：

```
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

### 3. 测试查询特定假期类型

输入：
- "我的年假还剩多少"
- "病假余额"
- "婚假还有多少天"

**预期结果**：
系统应该返回指定类型的假期余额。

### 4. 测试未登录场景

1. 退出登录
2. 尝试查询假期余额

**预期结果**：
系统应该提示："请先登录后查询假期余额"

### 5. 测试请假流程中的余额检查（待实现）

输入："我想请年假"

**预期流程**：
1. 系统询问请假类型
2. 系统询问请假天数
3. **系统自动检查余额**（阶段 2.5）
4. 如果余额充足，继续流程
5. 如果余额不足，提示用户并终止流程

## 验证检查点

### ✅ 后端日志检查

查看后端日志，应该看到：

```
INFO:app.agents.implementations.orchestrator_agent:✅ [INTENT] LLM 识别意图 | query='我的年假还剩多少' -> leave_balance
INFO:app.agents.implementations.orchestrator_agent:🎯 [LEAVE_BALANCE] 路由到 LeaveBalanceTool
INFO:app.tools.implementations.leave_balance:[LeaveBalanceTool] 权限验证 auth_context：{'username': 'hr', 'user_id': '7afcb609-df93-4da5-ad6e-319832a5c2e8', 'role': 'hr'}
INFO:app.tools.implementations.leave_balance:[AUDIT] user=hr (id=7afcb609-df93-4da5-ad6e-319832a5c2e8) action=check_leave_balance resource=all success=True details=查询成功
```

**关键点**：
- auth_context 应该包含正确的 username 和 user_id
- role 不应该是 'guest'
- 查询应该成功

### ❌ 常见问题

#### 问题 1：auth_context 仍然是 guest

**症状**：
```
auth_context：{'username': '', 'user_id': None, 'role': 'guest'}
```

**可能原因**：
1. 前端没有发送 Authorization header
2. JWT token 已过期
3. 用户没有登录

**解决方案**：
1. 检查浏览器开发者工具 → Network → 请求头中是否有 `Authorization: Bearer <token>`
2. 重新登录获取新的 token
3. 确保前端代码已更新并重新构建

#### 问题 2：Tool not found

**症状**：
```
Tool execution failed: check_leave_balance, error: Tool not found: check_leave_balance
```

**可能原因**：
LeaveBalanceTool 没有在 main.py 中导入

**解决方案**：
确保 `backend/app/main.py` 中有：
```python
from app.tools.implementations import (
    ...,
    LeaveBalanceTool
)
```

#### 问题 3：数据库查询失败

**症状**：
```
数据库查询失败: 'NoneType' object is not subscriptable
```

**可能原因**：
MongoDB 连接未初始化

**解决方案**：
确保后端启动时正确初始化了 MongoDB 连接

## 性能指标

- 意图识别时间：< 1s
- 数据库查询时间：< 100ms
- 总响应时间：< 2s

## 安全验证

### 权限隔离测试

1. 使用 hr 账号登录，查询假期余额
2. 记录返回的 user_id
3. 使用 bob 账号登录，查询假期余额
4. 记录返回的 user_id

**验证**：
- hr 只能看到自己的余额数据
- bob 只能看到自己的余额数据
- 两个用户的 user_id 应该不同

### 审计日志验证

检查后端日志，确保每次查询都有审计记录：
```
[AUDIT] user=hr (id=xxx) action=check_leave_balance resource=all success=True details=查询成功
```

## 测试数据

### HR 用户余额
- 年假：总额 10 天，已用 3 天，剩余 7 天
- 病假：无限额
- 事假：无限额
- 婚假：总额 10 天，已用 3 天，剩余 7 天
- 产假：总额 98 天，已用 29.4 天，剩余 68.6 天
- 陪产假：总额 15 天，已用 4.5 天，剩余 10.5 天
- 高温假：总额 5 天，已用 1.5 天，剩余 3.5 天

### Bob 用户余额
（与 HR 相同的配置）

## 下一步

完成测试后，可以继续实现：
1. 请假流程中的余额检查（阶段 2.5）
2. 余额不足时的友好提示
3. 余额预警功能（剩余 < 20% 时提示）
