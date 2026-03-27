# 外部链接功能规格说明

## 需求概述

在 AI 回答中自动添加相关的外部链接，例如询问请假时给出请假申请系统的网址。链接配置存储在数据库中，方便动态管理。

## 功能设计

### 1. 数据库存储

创建 `external_links` 集合存储链接配置：

```javascript
// MongoDB Collection: external_links
{
  "_id": ObjectId,
  "id": "leave_request",           // 唯一标识
  "keywords": ["请假", "休假", "年假", "病假", "事假"],  // 触发关键词
  "title": "请假申请系统",          // 链接标题
  "url": "https://leave.company.com",  // 链接地址
  "description": "在线提交请假申请",  // 链接描述
  "enabled": true,                  // 是否启用
  "priority": 1,                    // 优先级（数字越小越优先）
  "created_at": ISODate,
  "updated_at": ISODate
}
```

### 2. 链接匹配逻辑

- 基于关键词匹配：当用户问题包含配置的关键词时，自动添加相关链接
- 支持多个链接：一个问题可能匹配多个链接
- 按优先级排序：多个匹配时按优先级显示
- 去重处理：避免重复添加相同链接

### 3. 链接显示位置

在回答内容下方、快捷提问上方显示相关链接：

```
[AI 回答内容]

相关链接：
🔗 [请假申请系统](https://leave.company.com) - 在线提交请假申请

快捷提问：
- [按钮1] [按钮2] [按钮3]
```

### 4. API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/links` | GET | 获取所有链接 |
| `/api/links` | POST | 创建链接 |
| `/api/links/{id}` | PUT | 更新链接 |
| `/api/links/{id}` | DELETE | 删除链接 |
| `/api/links/match` | POST | 匹配链接（内部调用） |

### 5. 数据持久化

- 链接信息随消息一起保存到 `messages` 集合
- 刷新页面后仍然显示

## 技术实现

### 后端修改

| 文件 | 修改内容 |
|------|---------|
| `services/link_service.py` | 新建：链接 CRUD 服务 |
| `services/link_matcher.py` | 新建：链接匹配服务 |
| `services/qa_agent.py` | 集成链接匹配 |
| `services/response_builder.py` | 添加 `related_links` 支持 |
| `services/message_service.py` | 保存 `related_links` |
| `api/routes/links.py` | 新建：链接管理 API |
| `api/routes/chat.py` | 返回 `relatedLinks` 字段 |

### 前端修改

| 文件 | 修改内容 |
|------|---------|
| `api/index.ts` | 添加链接 API |
| `stores/chat.ts` | 添加 `relatedLinks` 字段 |
| `views/Chat/ChatView.vue` | 显示相关链接 |
| `views/Settings/Links.vue` | 新建：链接管理页面 |

## API 响应格式

### 聊天响应
```json
{
  "type": "done",
  "sources": [...],
  "suggested_questions": [...],
  "related_links": [
    {
      "id": "leave_request",
      "title": "请假申请系统",
      "url": "https://leave.company.com",
      "description": "在线提交请假申请"
    }
  ]
}
```

### 链接列表
```json
{
  "links": [
    {
      "id": "leave_request",
      "title": "请假申请系统",
      "url": "https://leave.company.com",
      "description": "在线提交请假申请",
      "keywords": ["请假", "休假", "年假"],
      "enabled": true,
      "priority": 1
    }
  ]
}
```

## 默认链接数据

系统初始化时插入默认链接：

| 标题 | 关键词 | URL |
|------|--------|-----|
| 请假申请系统 | 请假, 休假, 年假, 病假, 事假 | /leave |
| 费用报销系统 | 报销, 费用, 发票 | /expense |
| 内部推荐 | 内推, 推荐, 招聘 | /referral |
| 员工手册 | 员工手册, 规章制度, 制度 | /handbook |
| IT支持 | IT, 电脑, 网络, 软件 | /it-support |
