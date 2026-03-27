# 剩余功能实施计划

## 概述

本计划涵盖 4 个未实施的约束配置功能（排除 content_coverage_threshold）：

1. **retrieval.min_relevant_docs** - 最小相关文档数（中优先级）
2. **fallback.suggest_contact** - 建议联系方式开关（低优先级）
3. **fallback.suggest_similar** - 建议相似问题（低优先级）
4. **suggest_questions.types** - 建议问题类型（低优先级）

**预计总时间**: 8-12 小时  
**建议实施顺序**: 按优先级从高到低

---

## 功能 1: retrieval.min_relevant_docs

### 基本信息
- **优先级**: 中
- **预计时间**: 1.5 小时（开发 1h + 测试 0.5h）
- **影响范围**: `qa_agent.py`
- **配置值**: `1`

### 功能说明
检索后验证文档数量是否满足最小要求。如果检索到的相关文档数量少于此阈值，返回兜底消息而不是生成回答。

### 实施步骤

#### 步骤 1: 修改 qa_agent.py (30 分钟)

**位置**: `_execute_rag_flow` 方法，检索后验证部分

**修改内容**:
```python
# 在 _execute_rag_flow 方法中，检索后添加文档数量检查
async def _execute_rag_flow(self, query: str, history: List[Dict]) -> AsyncGenerator[str, None]:
    # ... 现有代码 ...
    
    # 1. 检索相关文档
    docs, metadatas, distances = await self._retrieve(optimized_query)
    
    # 使用验证器过滤检索结果
    retrieval_config = constraint_config.retrieval
    if retrieval_config.get("enabled", True):
        filtered_docs, retrieval_quality = validator.validate_retrieval(
            docs, metadatas, distances
        )
    else:
        filtered_docs = list(zip(docs, metadatas, distances))
        retrieval_quality = 1.0
    
    # 【新增】检查文档数量是否满足最小要求
    min_docs = retrieval_config.get('min_relevant_docs', 1)
    if len(filtered_docs) < min_docs:
        logger.warning(
            f"检索文档数不足: {len(filtered_docs)} < {min_docs}, "
            f"query='{query[:50]}...'"
        )
        
        # 返回兜底消息
        fallback_msg = constraint_config.fallback.get(
            'no_result_message',
            '抱歉，我在知识库中没有找到相关信息。'
        )
        
        # 添加联系信息（如果配置启用）
        if constraint_config.fallback.get('suggest_contact', True):
            contact_info = constraint_config.fallback.get('contact_info', '')
            if contact_info:
                fallback_msg += f"\n\n{contact_info}"
        
        yield ResponseBuilder.text_chunk(fallback_msg)
        yield ResponseBuilder.done_chunk([], content=fallback_msg)
        return
    
    # 继续正常流程...
```

#### 步骤 2: 添加单元测试 (30 分钟)

**文件**: `backend/tests/constraints/test_min_relevant_docs.py`

```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.qa_agent import QAAgent

@pytest.mark.asyncio
async def test_min_relevant_docs_sufficient():
    """测试文档数量满足最小要求"""
    agent = QAAgent()
    
    with patch.object(agent, '_retrieve') as mock_retrieve:
        # 模拟检索到 3 个文档
        mock_retrieve.return_value = (
            ['doc1', 'doc2', 'doc3'],
            [{'source': 's1'}, {'source': 's2'}, {'source': 's3'}],
            [0.9, 0.85, 0.8]
        )
        
        # 配置最小文档数为 2
        with patch('app.services.qa_agent.get_constraint_config') as mock_config:
            mock_config.return_value.retrieval = {
                'enabled': True,
                'min_relevant_docs': 2,
                'min_similarity_score': 0.7
            }
            
            # 应该正常生成回答
            result = []
            async for chunk in agent.process("测试问题"):
                result.append(chunk)
            
            # 验证没有返回兜底消息
            assert len(result) > 0
            assert '未找到相关信息' not in str(result)

@pytest.mark.asyncio
async def test_min_relevant_docs_insufficient():
    """测试文档数量不足最小要求"""
    agent = QAAgent()
    
    with patch.object(agent, '_retrieve') as mock_retrieve:
        # 模拟只检索到 1 个文档
        mock_retrieve.return_value = (
            ['doc1'],
            [{'source': 's1'}],
            [0.9]
        )
        
        # 配置最小文档数为 3
        with patch('app.services.qa_agent.get_constraint_config') as mock_config:
            mock_config.return_value.retrieval = {
                'enabled': True,
                'min_relevant_docs': 3,
                'min_similarity_score': 0.7
            }
            mock_config.return_value.fallback = {
                'no_result_message': '未找到相关信息',
                'suggest_contact': False
            }
            
            # 应该返回兜底消息
            result = []
            async for chunk in agent.process("测试问题"):
                result.append(chunk)
            
            # 验证返回了兜底消息
            assert any('未找到相关信息' in str(chunk) for chunk in result)
```

#### 步骤 3: 验证和文档 (30 分钟)

1. 运行测试确保通过
2. 更新 `check_all_constraints.py` 检查脚本
3. 更新配置文档

---

## 功能 2: fallback.suggest_contact

### 基本信息
- **优先级**: 低
- **预计时间**: 1 小时（开发 0.5h + 测试 0.5h）
- **影响范围**: `strict_qa.py`
- **配置值**: `true`

### 功能说明
控制是否在兜底消息中显示联系信息。目前 `contact_info` 总是显示，需要添加开关控制。

### 实施步骤

#### 步骤 1: 修改 strict_qa.py (20 分钟)

**位置**: `StrictQAPrompt.get_fallback_message` 方法

**修改内容**:
```python
@staticmethod
def get_fallback_message(config=None) -> str:
    """
    获取兜底消息
    
    Args:
        config: 约束配置对象
    
    Returns:
        str: 兜底消息
    """
    if config is None:
        config = get_constraint_config()
    
    fallback_config = config.fallback
    
    # 基础消息
    message = fallback_config.get(
        'no_result_message',
        '抱歉，我在知识库中没有找到相关信息。'
    )
    
    # 【修改】只有当 suggest_contact 为 true 时才添加联系信息
    if fallback_config.get('suggest_contact', True):
        contact_info = fallback_config.get('contact_info', '')
        if contact_info:
            message += f"\n\n{contact_info}"
    
    return message
```

#### 步骤 2: 更新调用位置 (10 分钟)

确保所有调用 `get_fallback_message` 的地方都传递了 config 参数：

```python
# 在 qa_agent.py 中
fallback_msg = StrictQAPrompt.get_fallback_message(constraint_config)
```

#### 步骤 3: 添加测试 (30 分钟)

**文件**: `backend/tests/constraints/test_suggest_contact.py`


```python
import pytest
from app.prompts.strict_qa import StrictQAPrompt
from app.core.constraint_config import ConstraintConfig
from unittest.mock import MagicMock

def test_suggest_contact_enabled():
    """测试启用联系信息建议"""
    config = MagicMock(spec=ConstraintConfig)
    config.fallback = {
        'no_result_message': '未找到相关信息',
        'suggest_contact': True,
        'contact_info': '请联系：support@company.com'
    }
    
    message = StrictQAPrompt.get_fallback_message(config)
    
    assert '未找到相关信息' in message
    assert 'support@company.com' in message

def test_suggest_contact_disabled():
    """测试禁用联系信息建议"""
    config = MagicMock(spec=ConstraintConfig)
    config.fallback = {
        'no_result_message': '未找到相关信息',
        'suggest_contact': False,
        'contact_info': '请联系：support@company.com'
    }
    
    message = StrictQAPrompt.get_fallback_message(config)
    
    assert '未找到相关信息' in message
    assert 'support@company.com' not in message
```

---

## 功能 3: fallback.suggest_similar

### 基本信息
- **优先级**: 低
- **预计时间**: 4-6 小时（开发 3-4h + 测试 1-2h）
- **影响范围**: 新增 `similar_question_finder.py`，修改 `strict_qa.py`
- **配置值**: `true`

### 功能说明
当无法找到相关信息时，向用户建议相似的问题。需要实现相似问题查找功能。

### 实施步骤

#### 步骤 1: 创建相似问题查找器 (2 小时)

**文件**: `backend/app/services/similar_question_finder.py`

```python
"""
相似问题查找器

基于向量相似度从历史问题中查找相似问题
"""

from typing import List, Optional
import logging
from app.core.chroma import get_chroma_client

logger = logging.getLogger(__name__)

class SimilarQuestionFinder:
    """相似问题查找器"""
    
    def __init__(self):
        self.chroma_client = get_chroma_client()
        self.collection_name = "conversations"
    
    async def find_similar(
        self,
        query: str,
        top_k: int = 3,
        min_similarity: float = 0.7
    ) -> List[str]:
        """
        查找相似问题
        
        Args:
            query: 用户查询
            top_k: 返回的相似问题数量
            min_similarity: 最小相似度阈值
        
        Returns:
            List[str]: 相似问题列表
        """
        try:
            collection = self.chroma_client.get_collection(self.collection_name)
            
            # 从对话历史中检索相似问题
            results = collection.query(
                query_texts=[query],
                n_results=top_k * 2,  # 多检索一些，后续过滤
                include=['documents', 'metadatas', 'distances']
            )
            
            if not results or not results['documents']:
                return []
            
            similar_questions = []
            seen_questions = set()
            
            for doc, metadata, distance in zip(
                results['documents'][0],
                results['metadatas'][0],
                results['distances'][0]
            ):
                # 计算相似度（距离转换为相似度）
                similarity = 1 - distance
                
                if similarity < min_similarity:
                    continue
                
                # 提取问题（假设 metadata 中有 question 字段）
                question = metadata.get('question', '')
                if not question or question == query:
                    continue
                
                # 去重
                if question in seen_questions:
                    continue
                
                seen_questions.add(question)
                similar_questions.append(question)
                
                if len(similar_questions) >= top_k:
                    break
            
            return similar_questions
        
        except Exception as e:
            logger.error(f"查找相似问题失败: {e}")
            return []

# 单例模式
_finder_instance: Optional[SimilarQuestionFinder] = None

def get_similar_question_finder() -> SimilarQuestionFinder:
    """获取相似问题查找器实例"""
    global _finder_instance
    if _finder_instance is None:
        _finder_instance = SimilarQuestionFinder()
    return _finder_instance
```

#### 步骤 2: 修改 strict_qa.py (1 小时)

```python
from app.services.similar_question_finder import get_similar_question_finder

@staticmethod
async def get_fallback_message_async(config=None, query: str = None) -> str:
    """
    获取兜底消息（异步版本，支持相似问题查找）
    
    Args:
        config: 约束配置对象
        query: 用户查询（用于查找相似问题）
    
    Returns:
        str: 兜底消息
    """
    if config is None:
        config = get_constraint_config()
    
    fallback_config = config.fallback
    
    # 基础消息
    message = fallback_config.get(
        'no_result_message',
        '抱歉，我在知识库中没有找到相关信息。'
    )
    
    # 添加相似问题建议
    if fallback_config.get('suggest_similar', False) and query:
        try:
            finder = get_similar_question_finder()
            similar_questions = await finder.find_similar(query, top_k=3)
            
            if similar_questions:
                message += "\n\n您可能想问："
                for i, q in enumerate(similar_questions, 1):
                    message += f"\n{i}. {q}"
        except Exception as e:
            logger.error(f"查找相似问题失败: {e}")
    
    # 添加联系信息
    if fallback_config.get('suggest_contact', True):
        contact_info = fallback_config.get('contact_info', '')
        if contact_info:
            message += f"\n\n{contact_info}"
    
    return message
```

#### 步骤 3: 更新 qa_agent.py (30 分钟)

```python
# 在需要返回兜底消息的地方使用异步版本
fallback_msg = await StrictQAPrompt.get_fallback_message_async(
    constraint_config,
    query=query
)
```

#### 步骤 4: 添加测试 (1-2 小时)

**文件**: `backend/tests/constraints/test_suggest_similar.py`

---

## 功能 4: suggest_questions.types

### 基本信息
- **优先级**: 低
- **预计时间**: 3-4 小时（开发 2-3h + 测试 1h）
- **影响范围**: `suggestion_generator.py`
- **配置值**: `["相关追问", "深入探索", "对比分析"]`

### 功能说明
根据配置的类型生成不同风格的建议问题，提升问题多样性。

### 实施步骤

#### 步骤 1: 修改 suggestion_generator.py (2 小时)

```python
async def generate(
    self,
    context: str,
    question: str,
    answer: str,
    count: int = 3
) -> List[str]:
    """
    生成快捷提问
    
    Args:
        context: 上下文
        question: 用户问题
        answer: 回答内容
        count: 生成数量
    
    Returns:
        List[str]: 快捷提问列表
    """
    suggest_config = self.config.suggest_questions
    
    if not suggest_config.get("enabled", True):
        return []
    
    # 获取配置的问题类型
    types = suggest_config.get('types', ['相关追问'])
    if not types:
        types = ['相关追问']
    
    # 根据类型生成不同风格的问题
    suggestions = []
    
    for question_type in types[:count]:
        try:
            suggestion = await self._generate_by_type(
                question_type,
                context,
                question,
                answer
            )
            if suggestion:
                suggestions.append(suggestion)
        except Exception as e:
            logger.error(f"生成 {question_type} 类型问题失败: {e}")
    
    return suggestions[:count]

async def _generate_by_type(
    self,
    question_type: str,
    context: str,
    question: str,
    answer: str
) -> Optional[str]:
    """
    根据类型生成问题
    
    Args:
        question_type: 问题类型
        context: 上下文
        question: 用户问题
        answer: 回答内容
    
    Returns:
        Optional[str]: 生成的问题
    """
    # 定义不同类型的 Prompt 模板
    type_prompts = {
        '相关追问': '''基于以下对话，生成一个相关的追问。
要求：
- 与当前话题相关
- 自然延续对话
- 简洁明了

问题：{question}
回答：{answer}

生成一个相关追问：''',
        
        '深入探索': '''基于以下对话，生成一个深入探讨细节的问题。
要求：
- 深入某个具体细节
- 探索更多信息
- 有助于全面理解

问题：{question}
回答：{answer}

生成一个深入探索的问题：''',
        
        '对比分析': '''基于以下对话，生成一个对比分析类的问题。
要求：
- 对比不同方面
- 分析差异或联系
- 拓展思考维度

问题：{question}
回答：{answer}

生成一个对比分析的问题：'''
    }
    
    # 获取对应类型的 Prompt
    prompt_template = type_prompts.get(
        question_type,
        type_prompts['相关追问']
    )
    
    prompt = prompt_template.format(
        question=question,
        answer=answer[:500]  # 限制长度
    )
    
    # 调用 LLM 生成
    try:
        response = await self.llm_client.chat(
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0.8,
            max_tokens=100
        )
        
        # 清理和验证
        suggestion = response.strip()
        if suggestion and len(suggestion) > 5:
            return suggestion
        
        return None
    
    except Exception as e:
        logger.error(f"LLM 生成问题失败: {e}")
        return None
```

#### 步骤 2: 添加测试 (1 小时)

**文件**: `backend/tests/constraints/test_suggestion_types.py`

---

## 实施时间表

### 第一周（推荐）
- **Day 1-2**: 实施功能 1 (min_relevant_docs) - 1.5 小时
- **Day 2**: 实施功能 2 (suggest_contact) - 1 小时
- **总计**: 2.5 小时

### 第二周（可选）
- **Day 1-2**: 实施功能 4 (suggest_questions.types) - 3-4 小时
- **Day 3-4**: 实施功能 3 (suggest_similar) - 4-6 小时
- **总计**: 7-10 小时

---

## 验收标准

### 功能 1: min_relevant_docs
- [ ] 文档数不足时返回兜底消息
- [ ] 文档数满足时正常生成回答
- [ ] 单元测试通过
- [ ] 日志记录正确

### 功能 2: suggest_contact
- [ ] suggest_contact=true 时显示联系信息
- [ ] suggest_contact=false 时不显示联系信息
- [ ] 单元测试通过

### 功能 3: suggest_similar
- [ ] suggest_similar=true 时显示相似问题
- [ ] suggest_similar=false 时不显示相似问题
- [ ] 相似问题查找准确
- [ ] 单元测试通过

### 功能 4: suggest_questions.types
- [ ] 根据配置类型生成不同风格问题
- [ ] 生成的问题符合类型特征
- [ ] 单元测试通过

---

## 风险和注意事项

### 功能 1
- **风险**: 可能导致过多查询返回兜底消息
- **缓解**: 设置合理的 min_relevant_docs 值（建议 1-2）

### 功能 2
- **风险**: 无
- **注意**: 确保向后兼容，默认值为 true

### 功能 3
- **风险**: 相似问题查找可能较慢
- **缓解**: 设置合理的超时时间，失败时优雅降级

### 功能 4
- **风险**: LLM 调用增加成本
- **缓解**: 使用缓存，限制生成数量

---

## 总结

**推荐实施顺序**:
1. 功能 2 (suggest_contact) - 最简单，1 小时
2. 功能 1 (min_relevant_docs) - 重要性高，1.5 小时
3. 功能 4 (suggest_questions.types) - 用户体验提升，3-4 小时
4. 功能 3 (suggest_similar) - 最复杂，4-6 小时

**第一阶段（必须）**: 功能 1 + 功能 2 = 2.5 小时  
**第二阶段（可选）**: 功能 3 + 功能 4 = 7-10 小时

---

**文档创建时间**: 2024-03-25  
**预计完成时间**: 第一阶段 1 天，第二阶段 2-3 天  
**状态**: 待实施
