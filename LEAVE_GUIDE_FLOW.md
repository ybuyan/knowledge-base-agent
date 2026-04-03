# leave_guide 使用流程详解

## 完整调用链

```
用户输入: "我想请假"
    ↓
1. OrchestratorAgent.run()
   - 调用 detect_intent("我想请假")
   - 匹配关键词 "我想请假" in _GUIDE_KW
   - 返回 intent = "guide"
    ↓
2. OrchestratorAgent 路由
   - 检测到 intent == "guide"
   - 调用 agent_engine.execute("guide_agent", {...})
    ↓
3. GuideAgent.run()
   - 接收 input_data: {query: "我想请假", session_id: "...", history: [...]}
   - 调用 _match_guide_skill("我想请假")
    ↓
4. GuideAgent._match_guide_skill()
   - 遍历所有 skills: skill_engine.skill_loader._cache
   - 找到 skill_id = "leave_guide"
   - 检查 skill_type == "guide" ✓
   - 检查 triggers: ["我想请假", "怎么请假", ...]
   - 匹配成功: "我想请假" in triggers
   - 返回 skill_id = "leave_guide"
    ↓
5. GuideAgent 执行 skill
   - 构建 context:
     {
       "query": "我想请假",
       "question": "我想请假",  ← 这里使用 leave_guide
       "session_id": "...",
       "history": [...]
     }
   - 调用 skill_engine.execute("leave_guide", context)
    ↓
6. SkillEngine.execute("leave_guide", context)
   - 加载 leave_guide skill 定义
   - 读取 pipeline:
     [
       {
         "step": "generate_answer",
         "processor": "LLMGenerator",
         "params": {
           "prompt_template": "leave_guide",  ← 这里使用 leave_guide
           "stream": false
         }
       }
     ]
   - 执行 pipeline 中的每个 step
    ↓
7. LLMGenerator.process(context, params)
   - 读取 params["prompt_template"] = "leave_guide"
   - 从 config_loader 加载 prompt:
     config_loader.get_prompt("leave_guide")  ← 这里使用 leave_guide
   - 获取 prompt 配置:
     {
       "template": {
         "system": "你是一个企业 HR 助手...",
         "user": "{question}"
       },
       "variables": ["question"]
     }
   - 从 context 中提取变量:
     question = context["question"] = "我想请假"
   - 格式化 user_prompt:
     user_prompt = "{question}".format(question="我想请假")
   - 调用 LLM:
     call_llm(user_prompt, system_prompt)
    ↓
8. LLM 生成回答
   - 使用 system_prompt 中的指引
   - 开始多轮对话收集信息
   - 返回: "您好！很高兴为您服务。为了帮您更好地办理请假手续..."
    ↓
9. 返回结果
   - LLMGenerator 返回 {"answer": "..."}
   - SkillEngine 返回结果
   - GuideAgent 返回 {"answer": "...", "session_id": "..."}
   - OrchestratorAgent 返回给用户
```

## leave_guide 的三个使用位置

### 1. Skill ID (skill_id = "leave_guide")
**位置**: `backend/app/skills/definitions/leave_guide/SKILL.md`
```yaml
name: leave_guide  ← Skill 的唯一标识符
```

**用途**: 
- GuideAgent 通过这个 ID 来执行 skill
- SkillEngine 通过这个 ID 加载 skill 定义

**调用**: 
```python
skill_id = self._match_guide_skill(query)  # 返回 "leave_guide"
result = await self.skill_engine.execute(skill_id, context)  # 执行 "leave_guide"
```

### 2. Prompt Template ID (prompt_template = "leave_guide")
**位置**: `backend/app/skills/definitions/leave_guide/SKILL.md`
```yaml
pipeline:
  - step: generate_answer
    processor: LLMGenerator
    params:
      prompt_template: leave_guide  ← Prompt 模板的 ID
```

**用途**:
- LLMGenerator 通过这个 ID 从 config.json 加载 prompt 模板

**调用**:
```python
prompt_template_id = params.get("prompt_template", "qa_rag")  # 获取 "leave_guide"
prompt_config = config_loader.get_prompt(prompt_template_id)  # 加载 prompt 配置
```

### 3. Prompt Configuration (prompts.leave_guide)
**位置**: `backend/app/prompts/config.json`
```json
{
  "prompts": {
    "leave_guide": {  ← Prompt 配置的 key
      "id": "leave_guide",
      "name": "请假指引",
      "template": {
        "system": "你是一个企业 HR 助手...",
        "user": "{question}"
      },
      "variables": ["question"]
    }
  }
}
```

**用途**:
- 定义 LLM 的 system prompt 和 user prompt 模板
- 指定需要的变量（question）

**调用**:
```python
template = prompt_config["template"]
system_prompt = template.get("system", "")
user_template = template.get("user", "")
user_prompt = user_template.format(question=context["question"])
```

## 关键配置关联

```
SKILL.md (leave_guide)
    ↓ skill_id
GuideAgent._match_guide_skill()
    ↓ 返回 "leave_guide"
SkillEngine.execute("leave_guide")
    ↓ 读取 pipeline
LLMGenerator.process()
    ↓ params["prompt_template"] = "leave_guide"
config_loader.get_prompt("leave_guide")
    ↓ 加载 prompt 配置
prompts.leave_guide
    ↓ 使用 template
LLM 生成回答
```

## 数据流

```
用户查询 "我想请假"
    ↓
context = {
  "query": "我想请假",
  "question": "我想请假",  ← 映射给 prompt template
  "session_id": "...",
  "history": []
}
    ↓
skill_id = "leave_guide"  ← 匹配到的 skill
    ↓
pipeline.params.prompt_template = "leave_guide"  ← 从 SKILL.md 读取
    ↓
prompt_config = prompts["leave_guide"]  ← 从 config.json 读取
    ↓
system_prompt = "你是一个企业 HR 助手..."
user_prompt = "我想请假"
    ↓
LLM 生成回答
```

## 总结

`leave_guide` 这个名称在三个地方使用，但含义不同：

1. **Skill ID**: 标识一个 skill 定义（SKILL.md 文件）
2. **Prompt Template ID**: 在 pipeline 中指定使用哪个 prompt 模板
3. **Prompt Config Key**: 在 config.json 中存储 prompt 配置

它们通过以下方式关联：
- GuideAgent 匹配到 skill_id = "leave_guide"
- Skill 的 pipeline 指定 prompt_template = "leave_guide"
- LLMGenerator 从 config.json 加载 prompts["leave_guide"]
- 最终使用 prompt 模板生成 LLM 的输入

这种设计实现了配置的分离和复用：
- Skill 定义了工作流程（pipeline）
- Prompt 定义了 LLM 的行为（system/user prompt）
- 它们通过 ID 关联，可以独立修改
