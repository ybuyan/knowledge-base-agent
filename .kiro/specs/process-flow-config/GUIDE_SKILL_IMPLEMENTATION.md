# 指引类 Skill 实现方案

## 需求说明

用户希望通过对话方式收集请假信息，然后生成一份**操作指引文档**，告诉用户具体怎么去请假（而不是直接帮用户提交申请）。

## 与现有流程的区别

| 特性 | 流程执行（process） | 指引生成（guide） |
|------|-------------------|------------------|
| 交互方式 | 流程卡片（表单） | 对话收集 |
| 最终输出 | 提交申请，返回申请单号 | 生成指引文档 |
| 用户操作 | AI 完成所有操作 | 用户根据指引自己操作 |
| 适用场景 | 系统集成，自动化流程 | 咨询、指导、外部系统 |

## 实现方案

### 方案 1：简化实现（推荐）

利用现有的 QA 能力，通过 prompt 工程实现：

1. **修改 SKILL.md**，添加详细的指引模板
2. **使用 LLM Processor**，让 AI 根据对话生成指引
3. **不需要新的 Processor**，复用现有能力

示例配置：
```yaml
skill_type: qa
pipeline:
  - step: generate_guide
    processor: LLMProcessor
    params:
      prompt_template: leave_guide
      stream: false
```

### 方案 2：完整实现

创建新的 Processor 类型：

1. **DialogCollector**：通过多轮对话收集信息
2. **GuideGenerator**：根据模板生成指引文档
3. **新增 skill_type: guide**

需要开发：
- `backend/app/skills/processors/dialog_collector.py`
- `backend/app/skills/processors/guide_generator.py`
- 前端支持多轮对话收集

## 快速实现（方案 1）

### 步骤 1：创建指引模板

在 `backend/app/prompts/config.json` 添加：

```json
{
  "leave_guide": {
    "enabled": true,
    "description": "请假指引生成",
    "template": {
      "system": "你是一个企业 HR 助手，帮助员工了解请假流程...",
      "user": "用户信息：{user_info}\n用户问题：{query}\n\n请生成详细的请假指引..."
    }
  }
}
```

### 步骤 2：修改 SKILL.md

```yaml
---
name: leave_guide
skill_type: qa
triggers:
  - 我想请假
  - 怎么请假
  - 请假流程
---

# 请假指引

当用户询问请假相关问题时，通过对话收集以下信息：
1. 假期类型
2. 请假天数
3. 开始日期

然后生成包含以下内容的指引文档：
- 假期余额信息
- 申请流程步骤
- 申请入口链接
- 申请模板示例
- 注意事项

模板格式：
[详细模板内容...]
```

### 步骤 3：测试

用户：我想请假
AI：好的，请问您要申请什么类型的假期？
用户：年假，3天，从6月15日开始
AI：[生成指引文档]

## 示例输出

```
您好！以下是年假申请指引：

📊 假期余额
您当前剩余年假 5 天，可申请 3 天年假。

📝 申请流程
1. 发起请假申请
2. 直属上级审批
3. HR 备案

🔗 申请入口
https://oa.company.com/leave

📄 参考模板
【年假申请】
申请人：张三
时间：2024 年 06 月 15 日 - 2024 年 06 月 17 日，共 3 天
事由：个人事务

⚠️ 注意事项
- 请提前 3 天申请
- 审批时间：1-3 个工作日
- 紧急情况请先电话联系直属上级
```

## 优势

1. **无需修改代码**：利用现有 QA 能力
2. **快速实现**：只需配置 prompt 和 SKILL.md
3. **灵活调整**：通过修改 prompt 调整输出格式
4. **自然对话**：LLM 自动处理多轮对话

## 下一步

1. 确认使用方案 1 还是方案 2
2. 如果方案 1，我可以帮你配置 prompt 和 SKILL.md
3. 如果方案 2，需要开发新的 Processor 类
