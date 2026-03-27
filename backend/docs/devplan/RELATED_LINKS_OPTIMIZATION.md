# 相关链接功能优化

## 优化内容

### 问题
1. 只在最后一条消息显示链接，导致历史消息的链接丢失
2. 即使回答内容为"抱歉，我在知识库中没有找到相关信息"也会显示链接
3. 点击快捷提问时会清除链接

### 解决方案

#### 1. 每条消息显示各自的链接

**前端修改** (`frontend/src/views/Chat/ChatView.vue`):
- 修改前：`v-if="message.role === 'assistant' && index === chatStore.messages.length - 1 && chatStore.currentRelatedLinks && chatStore.currentRelatedLinks.length > 0"`
- 修改后：`v-if="message.role === 'assistant' && message.relatedLinks && message.relatedLinks.length > 0 && !(index === chatStore.messages.length - 1 && isStreaming)"`

**说明**：
- 每条助手消息都显示自己的 `relatedLinks`
- 只在当前消息是最后一条且正在流式输出时隐藏链接
- 历史消息的链接会一直保持显示

#### 2. 只在有实际内容时匹配链接

**后端修改** (`backend/app/services/qa_agent.py`):

**Tool Flow**:
```python
# 匹配相关链接（只在有实际内容时）
related_links = []
if full_answer and len(full_answer.strip()) > 0:
    try:
        link_matcher = get_link_matcher()
        related_links = await link_matcher.match_links(query)
    except Exception as e:
        logger.warning("[Tool Flow] 匹配链接失败: %s", e)
```

**RAG Flow**:
```python
# 5. 匹配相关链接（只在有实际回答内容时）
related_links = []
if full_answer and len(full_answer.strip()) > 0:
    try:
        link_matcher = get_link_matcher()
        related_links = await link_matcher.match_links(query)
        if related_links:
            logger.info(f"[RAG] 匹配到 {len(related_links)} 个相关链接")
    except Exception as e:
        logger.warning(f"[RAG] 匹配链接失败: {e}")
```

**无结果 Fallback**:
```python
if not rag_context.documents:
    # 无检索结果，返回fallback消息（不匹配链接）
    fallback_msg = StrictQAPrompt.get_fallback_message()
    yield ResponseBuilder.text_chunk(fallback_msg)
    yield ResponseBuilder.done_chunk([], content=fallback_msg)
    return
```

**说明**：
- 检查 `full_answer` 是否有实际内容
- 无检索结果时不匹配链接
- 避免在"没有找到相关信息"时显示无关链接

#### 3. 简化 Store 逻辑

**前端修改** (`frontend/src/stores/chat.ts`):

移除了会话级别的链接累积逻辑：
- 删除 `currentRelatedLinks` ref
- 删除 `loadRelatedLinksFromMessages()` 函数
- 简化 `updateLastAssistantRelatedLinks()` 方法
- 从 store 返回值中移除 `currentRelatedLinks`

**修改后的 `updateLastAssistantRelatedLinks`**:
```typescript
function updateLastAssistantRelatedLinks(links: Link[]) {
  const lastAssistant = [...messages.value].reverse().find(m => m.role === 'assistant')
  if (lastAssistant) {
    lastAssistant.relatedLinks = links
  }
}
```

**说明**：
- 链接直接存储在每条消息中
- 不再需要会话级别的链接累积
- 简化了代码逻辑，减少了状态管理复杂度

## 优化效果

### 1. 链接持久化
- 每条消息的链接独立存储和显示
- 点击快捷提问不会影响已有消息的链接
- 历史消息的链接始终可见

### 2. 更精准的链接匹配
- 只在有实际回答内容时才匹配链接
- "没有找到相关信息"的回答不会显示链接
- 提升用户体验，避免误导

### 3. 代码简化
- 移除了不必要的会话级别状态
- 减少了状态同步的复杂度
- 更容易维护和理解

## 测试建议

1. 测试正常问答场景，确认链接正确显示
2. 测试无结果场景，确认不显示链接
3. 测试快捷提问，确认历史链接保持显示
4. 测试多轮对话，确认每条消息的链接独立显示
5. 测试会话切换，确认链接正确加载

## 相关文件

- `backend/app/services/qa_agent.py` - QA Agent 链接匹配逻辑
- `backend/app/services/link_matcher.py` - 链接匹配器
- `backend/app/services/link_service.py` - 链接服务
- `frontend/src/stores/chat.ts` - Chat Store
- `frontend/src/views/Chat/ChatView.vue` - Chat 视图
