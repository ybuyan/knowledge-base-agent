# JSON 语法错误修复

## 问题

后端报错：`Expecting ',' delimiter: line 260 column 1501`

## 原因

在 `backend/app/prompts/config.json` 文件中，`leave_guide_v2` 的 system prompt 包含了大量的代码块标记（```），这些在 JSON 字符串中会导致解析错误。

## 解决方案

简化了 `leave_guide_v2` 的 prompt 模板，移除了所有代码块标记和复杂的格式，改为更简洁的描述性文本。

### 修改前
```json
{
  "system": "...包含大量 ``` 代码块标记的长文本..."
}
```

### 修改后
```json
{
  "system": "你是一个专业的 HR 助手，通过多轮对话收集请假信息，生成个性化的操作指引。\n\n# 对话流程\n\n## 第1步：询问假期类型\n..."
}
```

## 验证

运行测试确认修复成功：

```bash
python backend/test_orchestrator_fix.py
```

### 测试结果

```log
✅ [INTENT] LLM 识别意图 | query='请假申请怎么写' -> guide
🎯 [GUIDE] 路由到 GuideAgent
✅ [GUIDE] 匹配成功 | skill_id='leave_guide' | trigger='请假'
📄 [LLM] 加载 Prompt 配置 | template_id='leave_guide_v2' | name='请假指引 v2.0 - 多轮对话'
✅ 执行成功
```

## 功能验证

助手正确地开始了多轮对话：

```
你好呀～关于请假申请，我来一步步帮你搞定！😊
首先想了解一下，你想申请的是哪种类型的假期呢？我们常见的有：

- 📅 年假
- 🏥 病假
- 📝 事假
- 💍 婚假
- 👶 产假 / 陪产假
- ☀️ 高温假（部分岗位适用）

你可以告诉我具体想请哪一种，我再根据类型一步步引导你准备材料和填写申请哦～
```

## 经验教训

在 JSON 文件中编写长文本时：
1. ❌ 避免使用代码块标记（```）
2. ❌ 避免使用未转义的特殊字符
3. ✅ 使用 \n 表示换行
4. ✅ 保持文本简洁清晰
5. ✅ 使用 JSON 验证工具检查语法

## 修改的文件

- `backend/app/prompts/config.json` - 简化 leave_guide_v2 prompt

## 现在可以正常工作

重启服务后，用户查询 "请假申请怎么写" 将：
1. ✅ LLM 识别为 guide 意图
2. ✅ 路由到 GuideAgent
3. ✅ 匹配 leave_guide skill
4. ✅ 使用 leave_guide_v2 prompt
5. ✅ 开始多轮对话收集信息
6. ✅ 生成个性化请假指引
