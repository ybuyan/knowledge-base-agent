# 需求文档：假期余额查询功能

## 介绍

本功能为知识库助手系统添加假期余额查询能力。用户可以通过对话直接查询自己的假期余额，系统也会在请假流程中自动检查余额是否充足。该功能通过 MCP Tool 实现，支持权限控制，确保用户只能查询自己的假期信息。

## 术语表

- **Leave_Balance_Tool**: 假期余额查询工具，实现为 MCP Tool
- **Leave_Guide_Skill**: 请假指引技能，负责收集请假信息并生成操作指引
- **Auth_Context**: 认证上下文，包含当前登录用户的身份信息
- **MCP_Auth_Middleware**: MCP 认证中间件，负责验证用户身份
- **Orchestrator_Agent**: 编排代理，负责调度 Tool 和 Skill
- **Leave_Type**: 假期类型，包括年假、病假、事假、婚假、产假、陪产假、高温假等
- **Leave_Balance**: 假期余额，包含假期类型、总额度、已使用、剩余额度等信息

## 需求

### 需求 1: 假期余额查询 Tool

**用户故事:** 作为系统用户，我想查询自己的假期余额，以便了解各类假期的剩余天数

#### 验收标准

1. THE Leave_Balance_Tool SHALL 实现为独立的 MCP Tool
2. WHEN 用户请求查询假期余额，THE Leave_Balance_Tool SHALL 返回当前用户的所有假期类型及其余额信息
3. THE Leave_Balance_Tool SHALL 支持查询特定假期类型的余额
4. THE Leave_Balance_Tool SHALL 返回的余额信息包含假期类型、总额度、已使用天数、剩余天数
5. WHEN 查询成功，THE Leave_Balance_Tool SHALL 返回格式化的余额信息文本
6. IF 查询失败，THEN THE Leave_Balance_Tool SHALL 返回明确的错误信息

### 需求 2: 权限控制

**用户故事:** 作为系统管理员，我想确保用户只能查询自己的假期余额，以保护隐私和数据安全

#### 验收标准

1. THE Leave_Balance_Tool SHALL 通过 MCP_Auth_Middleware 获取 Auth_Context
2. THE Leave_Balance_Tool SHALL 仅查询 Auth_Context 中 user_id 对应的假期余额
3. WHEN 用户未登录（guest 角色），THE Leave_Balance_Tool SHALL 返回权限不足错误
4. THE Leave_Balance_Tool SHALL 不接受 user_id 作为输入参数
5. THE Leave_Balance_Tool SHALL 记录所有查询操作的审计日志

### 需求 3: 请假 Skill 集成余额检查

**用户故事:** 作为请假用户，我想在请假流程中自动检查余额，以避免提交超额的请假申请

#### 验收标准

1. WHEN Leave_Guide_Skill 收集完假期类型和天数信息，THE Leave_Guide_Skill SHALL 调用 Leave_Balance_Tool 检查余额
2. IF 剩余余额不足，THEN THE Leave_Guide_Skill SHALL 提示用户余额不足并终止流程
3. IF 剩余余额充足，THEN THE Leave_Guide_Skill SHALL 继续后续流程
4. THE Leave_Guide_Skill SHALL 在余额不足提示中显示当前余额和请求天数
5. THE Leave_Guide_Skill SHALL 在生成的请假指引中包含余额信息

### 需求 4: 直接查询场景支持

**用户故事:** 作为用户，我想直接询问假期余额，而不需要进入请假流程

#### 验收标准

1. WHEN 用户询问"我的假期余额"、"年假还剩多少"等问题，THE Orchestrator_Agent SHALL 识别为余额查询意图
2. THE Orchestrator_Agent SHALL 直接调用 Leave_Balance_Tool 而不是 Leave_Guide_Skill
3. THE Orchestrator_Agent SHALL 将 Leave_Balance_Tool 返回的余额信息展示给用户
4. THE Leave_Balance_Tool SHALL 支持自然语言触发词，包括"余额"、"剩余"、"还有多少"、"查询假期"等

### 需求 5: 多假期类型支持

**用户故事:** 作为用户，我想查询不同类型假期的余额，以便合理安排休假计划

#### 验收标准

1. THE Leave_Balance_Tool SHALL 支持查询以下假期类型：年假、病假、事假、婚假、产假、陪产假、高温假
2. WHEN 用户未指定假期类型，THE Leave_Balance_Tool SHALL 返回所有假期类型的余额
3. WHEN 用户指定假期类型，THE Leave_Balance_Tool SHALL 仅返回该类型的余额
4. THE Leave_Balance_Tool SHALL 对于无限额度的假期类型（如病假、事假）显示"无限额"或"按需申请"
5. THE Leave_Balance_Tool SHALL 对于有限额度的假期类型显示具体的数值

### 需求 6: 余额数据存储

**用户故事:** 作为系统，我需要持久化存储用户的假期余额数据，以支持查询和更新操作

#### 验收标准

1. THE System SHALL 在 MongoDB 中创建 leave_balances 集合存储余额数据
2. THE leave_balances 集合 SHALL 包含字段：user_id、leave_type、total_quota、used_days、remaining_days、year
3. THE System SHALL 为每个用户的每种假期类型创建独立的余额记录
4. THE System SHALL 支持按年度管理假期余额（年假等按年度重置）
5. WHEN 查询余额时，THE System SHALL 返回当前年度的余额数据

### 需求 7: 余额格式化输出

**用户故事:** 作为用户，我想看到清晰易读的余额信息，以便快速了解假期情况

#### 验收标准

1. THE Leave_Balance_Tool SHALL 以表格或列表形式格式化余额信息
2. THE 格式化输出 SHALL 包含假期类型名称、总额度、已使用、剩余额度
3. THE 格式化输出 SHALL 使用中文显示假期类型名称
4. THE 格式化输出 SHALL 对剩余天数不足的假期类型进行视觉提示
5. THE 格式化输出 SHALL 包含查询时间戳

### 需求 8: 错误处理

**用户故事:** 作为用户，我想在查询失败时收到明确的错误提示，以便了解问题原因

#### 验收标准

1. IF 用户未登录，THEN THE Leave_Balance_Tool SHALL 返回"请先登录后查询假期余额"
2. IF 数据库查询失败，THEN THE Leave_Balance_Tool SHALL 返回"系统错误，请稍后重试"
3. IF 用户余额数据不存在，THEN THE Leave_Balance_Tool SHALL 返回"未找到假期余额数据，请联系 HR"
4. IF 指定的假期类型不存在，THEN THE Leave_Balance_Tool SHALL 返回"不支持的假期类型"
5. THE Leave_Balance_Tool SHALL 记录所有错误到日志系统

### 需求 9: Tool 注册和发现

**用户故事:** 作为系统，我需要将假期余额查询 Tool 注册到系统中，以便被调用

#### 验收标准

1. THE Leave_Balance_Tool SHALL 继承 BaseTool 基类
2. THE Leave_Balance_Tool SHALL 通过 ToolRegistry.register 装饰器注册
3. THE Leave_Balance_Tool SHALL 定义 ToolDefinition，包含 id、name、description、parameters
4. THE ToolDefinition SHALL 包含 category 字段，值为 "leave"
5. THE ToolDefinition SHALL 包含 enabled 字段，默认值为 true
6. THE Leave_Balance_Tool SHALL 实现 execute 方法处理查询逻辑

### 需求 10: 审计日志

**用户故事:** 作为系统管理员，我想记录所有假期余额查询操作，以便审计和追踪

#### 验收标准

1. WHEN Leave_Balance_Tool 执行查询，THE System SHALL 记录审计日志
2. THE 审计日志 SHALL 包含时间戳、user_id、username、操作类型、查询参数
3. THE 审计日志 SHALL 包含查询结果状态（成功/失败）
4. THE 审计日志 SHALL 使用 MCP audit_logger 模块记录
5. THE 审计日志 SHALL 持久化存储到数据库

