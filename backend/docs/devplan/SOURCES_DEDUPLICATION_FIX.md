# Sources 去重修复

## 问题描述

在问答来源（sources）中出现了重复的文档，例如同一个"请假制度.docx"显示了3次。

## 问题原因

在 `qa_agent.py` 的 `_extract_sources_from_tool_results` 方法中，代码会遍历所有工具执行结果并提取sources。当多个工具调用返回相同的文档时，就会导致sources列表中出现重复项。

### 问题代码

```python
def _extract_sources_from_tool_results(self, results: List[ToolResult]) -> List[Dict]:
    sources = []
    for result in results:
        if result.data.get("documents"):
            sources.extend(
                ResponseBuilder.build_sources_from_documents(result.data["documents"])
            )
    return sources[:ResponseBuilder.MAX_SOURCES]
```

### 问题场景

1. 用户提问："请假流程是什么？"
2. 系统调用多个工具进行检索
3. 多个工具都返回了"请假制度.docx"
4. 结果：sources列表中出现3个相同的"请假制度.docx"

## 解决方案

添加基于文件名的去重逻辑：

### 修复后的代码

```python
def _extract_sources_from_tool_results(self, results: List[ToolResult]) -> List[Dict]:
    """
    从Tool结果提取sources
    
    解析工具执行结果，提取引用来源信息。
    
    参数:
        results (List[ToolResult]): 工具执行结果列表
    
    返回:
        List[Dict]: 引用来源列表（已去重）
    """
    sources = []
    seen_filenames = set()  # 用于去重
    
    for result in results:
        if result.data.get("documents"):
            temp_sources = ResponseBuilder.build_sources_from_documents(result.data["documents"])
            
            # 去重：只添加未见过的文件名
            for source in temp_sources:
                filename = source.get("filename", "")
                if filename and filename not in seen_filenames:
                    seen_filenames.add(filename)
                    sources.append(source)
    
    # 重新分配ID
    for i, source in enumerate(sources):
        source["id"] = str(i + 1)
    
    return sources[:ResponseBuilder.MAX_SOURCES]
```

## 修复逻辑

1. **使用集合追踪已见文件名**: 创建 `seen_filenames` 集合存储已经添加的文件名
2. **遍历时检查重复**: 在添加source前，检查filename是否已存在
3. **重新分配ID**: 去重后重新分配连续的ID（1, 2, 3...）
4. **保持限制**: 仍然遵守 `MAX_SOURCES` 限制（最多5个）

## 测试建议

### 1. 单元测试

```python
def test_extract_sources_deduplication():
    """测试sources去重功能"""
    from app.services.qa_agent import QAAgent
    from app.services.tool_types import ToolResult
    
    # 模拟多个工具返回相同文档
    result1 = ToolResult(
        success=True,
        data={
            "documents": [
                {"metadata": {"document_name": "请假制度.docx"}, "content": "内容1"}
            ]
        }
    )
    
    result2 = ToolResult(
        success=True,
        data={
            "documents": [
                {"metadata": {"document_name": "请假制度.docx"}, "content": "内容2"}
            ]
        }
    )
    
    result3 = ToolResult(
        success=True,
        data={
            "documents": [
                {"metadata": {"document_name": "报销制度.docx"}, "content": "内容3"}
            ]
        }
    )
    
    agent = QAAgent()
    sources = agent._extract_sources_from_tool_results([result1, result2, result3])
    
    # 验证去重
    assert len(sources) == 2, f"期望2个sources，实际{len(sources)}"
    
    filenames = [s["filename"] for s in sources]
    assert "请假制度.docx" in filenames
    assert "报销制度.docx" in filenames
    assert filenames.count("请假制度.docx") == 1, "请假制度.docx应该只出现一次"
    
    # 验证ID重新分配
    assert sources[0]["id"] == "1"
    assert sources[1]["id"] == "2"
```

### 2. 集成测试

```bash
# 测试实际问答流程
curl -X POST http://localhost:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "question": "请假流程是什么？",
    "session_id": "test-session"
  }'
```

检查返回的sources字段，确保没有重复的文件名。

### 3. 手动测试

1. 启动服务
2. 提问："请假流程是什么？"
3. 查看返回的sources列表
4. 验证：每个文件名只出现一次

## 预期效果

### 修复前

```json
{
  "sources": [
    {"id": "1", "filename": "请假制度.docx", "content": "..."},
    {"id": "2", "filename": "请假制度.docx", "content": "..."},
    {"id": "3", "filename": "请假制度.docx", "content": "..."}
  ]
}
```

### 修复后

```json
{
  "sources": [
    {"id": "1", "filename": "请假制度.docx", "content": "..."}
  ]
}
```

## 注意事项

1. **去重依据**: 基于完整的文件名进行去重
2. **内容保留**: 保留第一次出现的文档内容
3. **ID连续性**: 去重后重新分配ID，保持连续
4. **性能影响**: 使用集合查找，时间复杂度O(1)，性能影响可忽略

## 相关文件

- `backend/app/services/qa_agent.py` - 主要修复文件
- `backend/app/services/response_builder.py` - sources构建逻辑
- `backend/app/services/tool_types.py` - 工具结果类型定义

## 修复日期

2026年3月26日

## 后续优化建议

### 1. 更智能的去重

考虑基于文档内容的相似度去重，而不仅仅是文件名：

```python
def _is_duplicate_content(content1: str, content2: str, threshold: float = 0.9) -> bool:
    """检查两个文档内容是否重复"""
    # 使用编辑距离或余弦相似度
    similarity = calculate_similarity(content1, content2)
    return similarity > threshold
```

### 2. 保留最相关的文档

当有重复时，保留相似度最高的那个：

```python
# 按相似度排序，保留最相关的
sources_by_filename = {}
for source in all_sources:
    filename = source["filename"]
    if filename not in sources_by_filename:
        sources_by_filename[filename] = source
    elif source["similarity"] > sources_by_filename[filename]["similarity"]:
        sources_by_filename[filename] = source
```

### 3. 添加日志

记录去重情况，便于监控和调试：

```python
if filename in seen_filenames:
    logger.debug(f"[Sources] 跳过重复文档: {filename}")
else:
    logger.debug(f"[Sources] 添加文档: {filename}")
    seen_filenames.add(filename)
```

## 总结

通过添加基于文件名的去重逻辑，成功解决了sources列表中出现重复文档的问题。修复后，每个文件名在sources列表中只会出现一次，提升了用户体验。
