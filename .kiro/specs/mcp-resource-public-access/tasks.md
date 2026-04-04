# 实施计划：MCP 资源公开访问（mcp-resource-public-access）

## 概述

按照设计文档和需求文档，实现 MCP 资源公开访问功能。分阶段推进：先实现基础认证，再添加访问控制，然后速率限制，最后管理功能和优化。

## 任务

- [x] 1. 环境准备和数据库初始化
  - [x] 1.1 创建 MongoDB 集合和索引
    - 创建 `api_keys` 集合
    - 创建 `audit_logs` 集合
    - 创建 `rate_limit_records` 集合（可选）
    - 为所有集合创建必要的索引
  - [x] 1.2 配置环境变量
    - 添加 API Key 相关配置到 `.env`
    - 添加速率限制配置
    - 添加审计日志配置
  - [ ]* 1.3 配置 Redis（可选，用于性能优化）
    - 安装 Redis
    - 配置 Redis 连接
    - 测试 Redis 连接

- [x] 2. 实现 API Key 管理模块
  - [x] 2.1 创建 `backend/app/mcp/api_key_manager.py`
    - 实现 `APIKey` 数据模型
    - 实现 `APIKeyManager` 类
    - 实现 `generate_api_key()` 方法
    - 实现 `validate_api_key()` 方法
    - 实现 `revoke_api_key()` 方法
    - 实现 `list_user_api_keys()` 方法
    - 实现 `cleanup_expired_keys()` 方法
  - [x]* 2.2 为 API Key Manager 编写单元测试
    - 测试 API Key 生成（格式、唯一性）
    - 测试 API Key 验证（有效、过期、撤销）
    - 测试过期 Key 自动清理

- [x] 3. 实现认证中间件
  - [x] 3.1 创建 `backend/app/mcp/auth_middleware.py`
    - 实现 `AuthContext` 数据模型
    - 实现 `MCPAuthMiddleware` 类
    - 实现 `authenticate_request()` 方法
    - 实现 `validate_api_key()` 方法
    - 实现 `validate_oauth_token()` 方法（可选）
    - 实现 `create_guest_context()` 方法
  - [ ]* 3.2 为认证中间件编写单元测试
    - 测试 API Key 提取和验证
    - 测试无认证凭证时返回 guest 上下文
    - 测试无效凭证时抛出 401 异常

- [x] 4. 实现审计日志模块
  - [x] 4.1 创建 `backend/app/mcp/audit_logger.py`
    - 实现 `AuditEvent` 数据模型
    - 实现 `AuditLogger` 类
    - 实现 `log_access()` 方法
    - 实现 `log_failed_auth()` 方法
    - 实现 `get_user_access_history()` 方法
    - 实现 `get_resource_access_stats()` 方法
  - [x] 4.2 实现异步批量写入
    - 使用 `asyncio.Queue` 缓冲审计事件
    - 实现后台任务批量写入 MongoDB
    - 确保主流程不被阻塞
  - [ ]* 4.3 为审计日志模块编写单元测试
    - 测试审计事件记录到 MongoDB
    - 测试敏感信息脱敏（API Key 只记录前 8 位）
    - 测试查询功能（用户历史、资源统计）

- [x] 5. 实现资源访问控制模块
  - [x] 5.1 创建 `backend/app/mcp/access_control.py`
    - 实现 `ResourceLevel` 枚举
    - 实现 `ResourceAccessControl` 类
    - 实现 `parse_resource_level()` 方法
    - 实现 `check_access()` 方法
    - 实现 `filter_resources()` 方法
  - [ ]* 5.2 为访问控制模块编写单元测试
    - 测试 URI 级别解析（public/internal/confidential）
    - 测试各角色对各级别资源的访问权限
    - 测试资源列表过滤功能

- [x] 6. 实现速率限制模块
  - [x] 6.1 创建 `backend/app/mcp/rate_limiter.py`
    - 实现 `RateLimitExceeded` 异常
    - 实现 `RateLimiter` 类
    - 实现 `check_rate_limit()` 方法（滑动窗口算法）
    - 实现 `get_remaining_quota()` 方法
    - 实现 `reset_user_quota()` 方法
  - [ ]* 6.2 为速率限制模块编写单元测试
    - 测试滑动窗口算法正确性
    - 测试速率限制检查
    - 测试配额查询和重置
  - [ ]* 6.3 实现 Redis 支持（可选，用于性能优化）
    - 使用 Redis ZSET 存储请求记录
    - 利用 ZREMRANGEBYSCORE 自动清理过期记录
    - 实现 Redis 连接池

- [x] 7. 增强 MCP Dispatcher
  - [x] 7.1 修改 `backend/app/mcp/dispatcher.py`
    - 在 `__init__` 中添加依赖注入（access_control, audit_logger, rate_limiter）
    - 修改 `dispatch()` 方法集成速率限制检查
    - 修改 `dispatch()` 方法集成审计日志记录
    - 修改 `_handle_resources_list()` 方法实现资源过滤
    - 修改 `_handle_resources_read()` 方法实现访问权限检查
  - [ ]* 7.2 为增强的 Dispatcher 编写单元测试
    - 测试速率限制集成
    - 测试访问权限检查
    - 测试审计日志记录

- [x] 8. 增强 MCP Router
  - [x] 8.1 修改 `backend/app/mcp/router.py`
    - 实现 `get_auth_context()` 依赖注入函数
    - 修改 `mcp_endpoint()` 集成认证中间件
    - 修改 `mcp_sse_endpoint()` 集成认证中间件
    - 实现 `list_public_resources()` 端点（GET /mcp/public/resources）
    - 实现 `create_api_key()` 端点（POST /mcp/admin/api-keys）
    - 实现 `revoke_api_key()` 端点（DELETE /mcp/admin/api-keys/{key})
    - 实现 `get_audit_logs()` 端点（GET /mcp/admin/audit-logs）
  - [x] 8.2 实现管理员权限检查
    - 在管理员端点中检查 `auth_context.role == "admin"`
    - 无权限返回 403 Forbidden

- [x] 9. 更新现有 MCP Server 支持资源分级
  - [x] 9.1 修改 `backend/app/mcp/knowledge_server.py`
    - 更新资源 URI 遵循命名约定
    - 注册公开资源（knowledge://public/*）
    - 注册内部资源（knowledge://internal/*）
    - 注册机密资源（knowledge://confidential/*）
  - [x] 9.2 修改 `backend/app/mcp/document_server.py`
    - 更新资源 URI 遵循命名约定
    - 注册公开资源（document://public/*）
    - 注册内部资源（document://internal/*）
    - 注册机密资源（document://confidential/*）

- [ ] 10. 集成测试
  - [ ]* 10.1 编写认证流程集成测试
    - 测试 API Key 认证成功流程
    - 测试 API Key 认证失败流程
    - 测试 guest 用户访问公开资源
  - [ ]* 10.2 编写访问控制集成测试
    - 测试不同角色访问各级别资源
    - 测试资源列表过滤
    - 测试权限拒绝场景
  - [ ]* 10.3 编写速率限制集成测试
    - 测试速率限制触发
    - 测试速率限制恢复
    - 测试全局 IP 速率限制
  - [ ]* 10.4 编写管理员功能集成测试
    - 测试 API Key 创建
    - 测试 API Key 撤销
    - 测试审计日志查询

- [ ] 11. 性能优化
  - [ ]* 11.1 实现 API Key 缓存
    - 使用 Redis 缓存有效的 API Key 信息（TTL 5 分钟）
    - 缓存命中时跳过 MongoDB 查询
    - 缓存未命中时查询 MongoDB 并更新缓存
  - [ ]* 11.2 优化审计日志批量写入
    - 调整批量大小和超时时间
    - 监控队列长度
    - 实现背压机制
  - [ ]* 11.3 优化资源列表过滤
    - 在 MCPServer 注册资源时预先标记级别
    - 使用字典按级别分组存储资源
    - 根据用户角色直接返回对应分组
  - [ ]* 11.4 配置数据库索引
    - 验证所有索引已创建
    - 分析慢查询并优化
    - 配置连接池参数

- [ ] 12. 安全加固
  - [ ]* 12.1 实现异常访问检测
    - 检测短时间内大量失败请求
    - 检测异常访问模式
    - 自动封禁异常 IP 或 API Key
  - [ ]* 12.2 添加请求签名支持（可选）
    - 实现 HMAC 签名机制
    - 添加 nonce 和 timestamp 防止重放
    - 验证签名有效性
  - [ ]* 12.3 配置 HTTPS 和 TLS
    - 配置 SSL 证书
    - 强制使用 HTTPS
    - 禁用 HTTP 端点（生产环境）
  - [ ]* 12.4 安全审计和渗透测试
    - 进行安全审计
    - 进行渗透测试
    - 修复发现的安全问题

- [ ] 13. 文档和部署
  - [ ] 13.1 编写 API 文档
    - 文档化所有新增端点
    - 提供请求/响应示例
    - 说明认证方式
  - [ ] 13.2 编写用户文档
    - 如何获取 API Key
    - 如何使用 API Key 访问资源
    - 资源分级说明
    - 速率限制说明
  - [ ] 13.3 编写管理员文档
    - 如何管理 API Keys
    - 如何查询审计日志
    - 如何监控系统状态
  - [ ] 13.4 编写部署指南
    - 环境配置说明
    - 数据库初始化脚本
    - 部署步骤
    - 故障排查指南
  - [ ] 13.5 准备生产环境部署
    - 配置生产环境变量
    - 初始化生产数据库
    - 配置监控和告警
    - 执行部署

- [ ] 14. 最终验收
  - [ ] 14.1 功能验收
    - 验证所有功能需求都已实现
    - 验证所有业务需求的验收标准都已满足
    - 确保所有测试通过
  - [ ] 14.2 性能验收
    - 验证所有性能指标都达标
    - 进行性能测试和压力测试
    - 确保无明显性能退化
  - [ ] 14.3 安全验收
    - 通过安全审计
    - 确认无高危漏洞
    - 符合安全最佳实践
  - [ ] 14.4 文档验收
    - 确认所有文档完整
    - 确认文档准确性
    - 确认文档可读性

## 备注

- 标有 `*` 的子任务为可选项，可根据实际情况决定是否实施
- 每个任务均引用设计文档和需求文档中对应的规范
- 建议按阶段推进，每个阶段完成后进行验收
- 遇到问题及时反馈，必要时调整计划

## 里程碑

| 里程碑 | 时间 | 交付物 |
|--------|------|--------|
| M1: 基础认证完成 | 第 2 周末 | API Key 认证可用 |
| M2: 访问控制完成 | 第 3 周末 | 资源分级访问控制可用 |
| M3: 速率限制完成 | 第 4 周末 | 速率限制防护可用 |
| M4: 管理功能完成 | 第 5 周末 | 管理端点可用 |
| M5: 性能优化完成 | 第 6 周末 | 性能达标 |
| M6: 安全加固完成 | 第 7 周末 | 安全审计通过 |
| M7: 生产就绪 | 第 8 周末 | 可部署到生产环境 |
