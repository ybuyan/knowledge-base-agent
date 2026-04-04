# 实现计划：假期余额查询功能

## 概述

本实现计划将假期余额查询功能集成到知识库助手系统中。该功能通过 MCP Tool 架构实现，支持用户直接查询假期余额，并在请假流程中自动检查余额是否充足。实现包括 LeaveBalanceTool 创建、数据库集合设计、Skill 和 Agent 集成、以及完整的测试覆盖。

## 任务列表

- [x] 1. 创建数据模型和类型定义
  - 创建 `backend/app/models/leave_balance.py` 文件
  - 实现 `LeaveBalance` Pydantic 模型
  - 实现 `LeaveBalanceResponse` 响应模型
  - 实现 `LeaveType` 枚举类
  - 添加辅助方法：`is_unlimited()`, `is_sufficient()`, `to_dict()`
  - _需求: 1.4, 5.1, 5.4, 5.5, 6.2_

- [ ]* 1.1 为数据模型编写单元测试
  - 创建 `backend/tests/models/test_leave_balance.py`
  - 测试 LeaveBalance 模型的验证逻辑
  - 测试 `is_unlimited()` 和 `is_sufficient()` 方法
  - 测试 LeaveType 枚举的辅助方法
  - _需求: 1.4, 5.4, 5.5_

- [x] 2. 创建 MongoDB 集合和索引
  - 创建数据库初始化脚本 `backend/init_leave_balances.py`
  - 创建 `leave_balances` 集合
  - 创建复合唯一索引：`(user_id, leave_type, year)`
  - 创建单字段索引：`user_id` 和 `year`
  - 添加集合验证规则（schema validation）
  - _需求: 6.1, 6.2, 6.3_

- [x] 3. 创建种子数据脚本
  - 创建 `backend/seed_leave_balances.py`
  - 为测试用户生成假期余额数据
  - 支持多种假期类型（年假、病假、事假、婚假、产假、陪产假、高温假）
  - 支持当前年度的余额初始化
  - _需求: 5.1, 6.4_

- [x] 4. 实现 LeaveBalanceTool 核心逻辑
  - [x] 4.1 创建 LeaveBalanceTool 基础结构
    - 创建 `backend/app/tools/implementations/leave_balance.py`
    - 继承 `BaseTool` 基类
    - 实现 `definition` 属性，定义 Tool 元数据
    - 使用 `@ToolRegistry.register("check_leave_balance")` 装饰器注册
    - _需求: 1.1, 9.1, 9.2, 9.3_

  - [x] 4.2 实现权限验证逻辑
    - 从 `kwargs` 中提取 `auth_context`
    - 验证用户是否已登录（role != "guest"）
    - 提取 `user_id` 和 `username`
    - 实现未登录用户的错误处理
    - _需求: 2.1, 2.2, 2.3, 2.4, 8.1_

  - [x] 4.3 实现数据库查询逻辑
    - 连接 MongoDB 数据库
    - 根据 `user_id` 和可选的 `leave_type` 查询余额
    - 查询当前年度的余额数据
    - 处理数据不存在的情况
    - _需求: 1.2, 1.3, 6.5, 8.3_

  - [x] 4.4 实现余额格式化输出
    - 将查询结果转换为 `LeaveBalance` 模型列表
    - 生成格式化的文本消息（表格或列表形式）
    - 包含假期类型、总额度、已使用、剩余天数
    - 对剩余天数不足的假期进行视觉提示
    - 添加查询时间戳
    - _需求: 1.5, 7.1, 7.2, 7.3, 7.4, 7.5_

  - [x] 4.5 实现错误处理和审计日志
    - 捕获数据库查询异常
    - 返回明确的错误信息
    - 使用 `AuditLogger` 记录所有查询操作
    - 记录审计日志字段：时间戳、user_id、username、操作类型、查询参数、结果状态
    - _需求: 1.6, 2.5, 8.1, 8.2, 8.3, 8.4, 8.5, 10.1, 10.2, 10.3, 10.4, 10.5_

- [ ]* 4.6 为 LeaveBalanceTool 编写单元测试
  - 创建 `backend/tests/tools/test_leave_balance.py`
  - 测试权限验证逻辑（已登录 vs 未登录）
  - 测试查询所有假期类型
  - 测试查询特定假期类型
  - 测试数据不存在的情况
  - 测试数据库异常处理
  - 使用 Mock 模拟 MongoDB 和 AuditLogger
  - _需求: 1.2, 1.3, 2.3, 8.1, 8.2, 8.3_

- [ ]* 4.7 为 LeaveBalanceTool 编写属性测试
  - **属性 1: 权限隔离性 - 用户只能查询自己的余额**
  - **验证需求: 2.2**
  - 使用 Hypothesis 生成随机 user_id
  - 验证查询结果中的所有余额记录都属于请求用户
  - _需求: 2.2_

- [ ]* 4.8 为 LeaveBalanceTool 编写属性测试
  - **属性 2: 余额一致性 - remaining_days = total_quota - used_days**
  - **验证需求: 1.4, 6.2**
  - 使用 Hypothesis 生成随机余额数据
  - 验证返回的余额数据满足一致性约束
  - _需求: 1.4, 6.2_

- [ ] 5. 检查点 - 确保 LeaveBalanceTool 测试通过
  - 确保所有测试通过，如有问题请询问用户。

- [x] 6. 更新 Leave_Guide_Skill 集成余额检查
  - [x] 6.1 更新 Leave_Guide_Skill 提示词
    - 修改 `backend/app/prompts/config.json` 中的 `leave_guide_v2` prompt
    - 在阶段 2（请假天数确认）后添加阶段 2.5（余额检查）
    - 添加调用 `check_leave_balance` tool 的逻辑
    - 添加余额不足的提示和处理逻辑
    - 在生成的指引中包含余额信息
    - _需求: 3.1, 3.2, 3.3, 3.4, 3.5_

  - [x] 6.2 更新 Leave_Guide_Skill 文档
    - 修改 `backend/app/skills/definitions/leave_guide/SKILL.md`
    - 添加阶段 2.5 的文档说明
    - 更新流程图和示例对话
    - _需求: 3.1_

- [ ]* 6.3 为 Leave_Guide_Skill 余额检查编写集成测试
  - 创建 `backend/tests/skills/test_leave_guide_balance_check.py`
  - 测试余额充足的场景（继续流程）
  - 测试余额不足的场景（终止流程）
  - 测试余额检查失败的场景（错误处理）
  - _需求: 3.1, 3.2, 3.3, 3.4_

- [x] 7. 更新 Orchestrator Agent 添加余额查询意图识别
  - [x] 7.1 更新意图识别提示词
    - 修改 `backend/app/agents/implementations/orchestrator_agent.py`
    - 在 `INTENT_DETECTION_PROMPT` 中添加 `leave_balance` 意图
    - 添加意图识别关键词：余额、剩余、还有多少、查询假期
    - _需求: 4.1, 4.4_

  - [x] 7.2 实现余额查询意图路由
    - 在 `OrchestratorAgent.run()` 方法中添加 `leave_balance` 意图处理
    - 调用 `ToolExecutor.execute_tool("check_leave_balance", ...)`
    - 传递 `auth_context` 到 Tool
    - 返回格式化的余额信息
    - _需求: 4.2, 4.3_

- [ ]* 7.3 为 Orchestrator 意图识别编写单元测试
  - 创建 `backend/tests/agents/test_orchestrator_leave_balance.py`
  - 测试余额查询意图识别（多种表达方式）
  - 测试意图路由到 LeaveBalanceTool
  - 测试 auth_context 传递
  - _需求: 4.1, 4.2, 4.4_

- [x] 8. 更新 Tool Executor 支持 auth_context 传递
  - 修改 `backend/app/services/tool_executor.py`
  - 在 `execute_tool()` 方法中添加 `auth_context` 参数
  - 将 `auth_context` 注入到 Tool 的 `kwargs` 中
  - 确保向后兼容（auth_context 为可选参数）
  - _需求: 2.1, 2.2_

- [ ]* 8.1 为 Tool Executor 编写单元测试
  - 创建 `backend/tests/services/test_tool_executor_auth.py`
  - 测试 auth_context 传递到 Tool
  - 测试 auth_context 为 None 的情况
  - _需求: 2.1_

- [ ] 9. 检查点 - 确保集成测试通过
  - 确保所有测试通过，如有问题请询问用户。

- [ ]* 10. 创建端到端集成测试
  - 创建 `backend/tests/integration/test_leave_balance_e2e.py`
  - 测试直接查询余额的完整流程
  - 测试请假流程中的余额检查
  - 测试权限控制（未登录用户）
  - 测试审计日志记录
  - _需求: 1.1, 2.3, 3.1, 4.1, 10.1_

- [x] 11. 更新文档
  - 更新 `README.md` 添加假期余额查询功能说明
  - 创建 `docs/leave_balance_tool.md` 详细文档
  - 包含 API 使用示例、数据模型、配置说明
  - 添加故障排查指南
  - _需求: 1.1, 1.2, 1.3_

- [ ] 12. 最终检查点 - 确保所有测试通过
  - 确保所有测试通过，如有问题请询问用户。

## 注意事项

- 标记 `*` 的任务为可选任务，可跳过以加快 MVP 交付
- 每个任务都引用了具体的需求编号，确保可追溯性
- 检查点任务确保增量验证
- 属性测试验证通用正确性属性
- 单元测试验证具体示例和边界情况
- 集成测试验证端到端流程

## 实现顺序说明

1. 首先创建数据模型和数据库结构（任务 1-3）
2. 然后实现核心 Tool 逻辑（任务 4）
3. 接着集成到 Skill 和 Agent（任务 6-8）
4. 最后进行端到端测试和文档更新（任务 10-11）
5. 每个阶段都有检查点确保质量
