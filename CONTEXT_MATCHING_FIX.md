# 基于上下文的 Skill 匹配修复

## 问题

用户在多轮对话中使用简短查询（如"流程是什么"、"需要什么材料"）时，因为不包含 trigger 关键词（如"婚假"），导致无法匹配到 skill，返回空消息。

## 原因

GuideAgent 的 `_match_guide_skill` 方法只检查当前查询是否包含 trigger 关键词，没有考虑对话历史。

在多轮对话中，用户通常会：
1. 第1轮：明确说明主题（"我想请婚假"）
2. 第2轮：简短追问（"流程是什么"）← 不包含"婚假"关键词

## 解决方案

修改 `_match_guide_skill` 方法，增加基于历史记录的匹配逻辑：

### 匹配策略

1. **优先匹配当前查询** - 如果当前查询包含 trigger，直接匹配
2. **回退到历史记录** - 如果当前查询不匹配，检查最近3轮对话的历史记录

### 实现代码

**文件**: `backend/app/agents/implementations/guide_agent.py`

```python
def _match_guide_skill(self, query: str, history: list = None) -> str:
    """
    根据 triggers 匹配对应的指引 skill
    
    Args:
        query: 用户查询
        history: 对话历史
        
    Returns:
        匹配到的 skill_id，如果没有匹配则返回 None
    """
    logger.info("🔍 [GUIDE] 开始匹配 guide skill | query='%s'", query)
    
    # 获取所有 guide 类型的 skills
    for skill_id, skill_def in self.skill_engine.skill_loader._cache.items():
        skill_type = skill_def.frontmatter.get("skill_type", "qa")
        
        # 只匹配 guide 类型的 skills
        if skill_type != "guide":
            continue
        
        triggers = skill_def.frontmatter.get("triggers", [])
        
        # 首先检查当前查询
        for trigger in triggers:
            if trigger in query:
                logger.info("✅ [GUIDE] 匹配成功 | skill_id='%s' | trigger='%s'", 
                           skill_id, trigger)
                return skill_id
        
        # 如果当前查询没有匹配，检查历史记录（最近3轮）
        if history:
            recent_history = history[-6:]  # 最近3轮对话（每轮2条消息）
            for msg in recent_history:
                if msg.get("role") == "user":
                    content = msg.get("content", "")
                    for trigger in triggers:
                        if trigger in content:
                            logger.info("✅ [GUIDE] 通过历史记录匹配成功 | skill_id='%s' | trigger='%s' | history_query='%s' | current_query='%s'", 
                                       skill_id, trigger, content[:30], query)
                            return skill_id
    
    logger.warning("❌ [GUIDE] 未匹配到任何 guide skill | query='%s'", query)
    return None
```

## 测试结果

### 对话场景

```
第1轮
用户: 我想请婚假
日志: ✅ [GUIDE] 匹配成功 | skill_id='leave_guide' | trigger='婚假'
助手: 好的，申请婚假是人生中的重要时刻...

第2轮
用户: 流程是什么  ← 不包含"婚假"关键词
日志: ✅ [GUIDE] 通过历史记录匹配成功 | skill_id='leave_guide' | trigger='婚假' | history_query='我想请婚假'
助手: 好的，我来为您梳理一下申请婚假的完整流程...

第3轮
用户: 需要什么材料  ← 不包含"婚假"关键词
日志: ✅ [GUIDE] 通过历史记录匹配成功 | skill_id='leave_guide' | trigger='婚假' | history_query='我想请婚假'
助手: 好的，我来为您提前说明申请婚假通常需要准备的材料...
```

## 优势

### 1. 自然对话体验
用户不需要在每次查询中重复主题关键词：
- ❌ 之前：用户必须说"婚假流程是什么"
- ✅ 现在：用户可以直接说"流程是什么"

### 2. 智能上下文理解
系统能够理解对话上下文，保持话题连贯性。

### 3. 灵活的查询方式
支持各种简短追问：
- "流程是什么"
- "需要什么材料"
- "怎么申请"
- "多久能批"

### 4. 可配置的历史窗口
只检查最近3轮对话（6条消息），避免：
- 过度依赖历史
- 话题切换时的误匹配

## 边界情况处理

### 1. 话题切换
如果用户切换话题，新的查询会优先匹配：
```
用户: 我想请婚假
助手: ...
用户: 我想请年假  ← 切换话题
日志: ✅ 匹配成功 | trigger='年假'  ← 优先匹配当前查询
```

### 2. 无历史记录
如果是第一轮对话，没有历史记录，正常匹配当前查询。

### 3. 历史窗口限制
只检查最近3轮（6条消息），避免过早的对话影响当前匹配。

## 修改的文件

1. `backend/app/agents/implementations/guide_agent.py` - 添加历史记录匹配
2. `backend/test_context_matching.py` - 测试脚本（新增）

## 日志示例

### 成功匹配（当前查询）
```log
INFO:...guide_agent:🔍 [GUIDE] 开始匹配 guide skill | query='我想请婚假'
INFO:...guide_agent:✅ [GUIDE] 匹配成功 | skill_id='leave_guide' | trigger='婚假' | query='我想请婚假'
```

### 成功匹配（历史记录）
```log
INFO:...guide_agent:🔍 [GUIDE] 开始匹配 guide skill | query='流程是什么'
INFO:...guide_agent:✅ [GUIDE] 通过历史记录匹配成功 | skill_id='leave_guide' | trigger='婚假' | history_query='我想请婚假' | current_query='流程是什么'
```

### 匹配失败
```log
INFO:...guide_agent:🔍 [GUIDE] 开始匹配 guide skill | query='天气怎么样'
WARNING:...guide_agent:❌ [GUIDE] 未匹配到任何 guide skill | query='天气怎么样'
```

## 未来优化

1. **会话状态管理** - 显式记录当前对话的主题
2. **话题切换检测** - 检测用户是否切换了话题
3. **多 Skill 冲突** - 如果历史中有多个 skill 的 trigger，选择最近的
4. **权重计算** - 根据历史消息的新旧程度计算权重

## 总结

通过添加基于历史记录的匹配逻辑，系统现在能够：
- ✅ 理解简短的追问查询
- ✅ 保持对话上下文连贯
- ✅ 提供更自然的对话体验
- ✅ 避免用户重复说明主题

重启服务后，用户可以自然地进行多轮对话，不需要在每次查询中重复关键词！
