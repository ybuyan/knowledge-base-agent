"""
Tool Types - Tool系统数据类型定义

本模块定义了Tool系统的核心数据结构，包括Tool调用、执行结果、决策对象等。
使用dataclass简化数据类的定义，提供类型安全和代码提示支持。

核心数据结构:
    - ToolCall: 工具调用请求，封装调用参数
    - ToolResult: 工具执行结果，包含执行状态和数据
    - ToolDecision: LLM的工具决策结果
    - ResponseChunk: 流式响应数据块
    - RAGContext: RAG检索上下文

设计原则:
    - 不可变性: 使用dataclass的frozen特性保证线程安全
    - 类型安全: 所有字段都有明确的类型注解
    - 可序列化: 支持转换为JSON格式用于API传输

使用示例:
    # 创建Tool调用
    call = ToolCall(
        id="call_123",
        name="search_knowledge",
        arguments={"query": "年假规定"}
    )
    
    # 执行并获取结果
    result = ToolResult(
        success=True,
        data={"documents": [...]},
        tool_name="search_knowledge",
        tool_call_id="call_123"
    )
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime
import hashlib
import json


@dataclass
class ToolCall:
    """
    Tool调用请求
    
    封装一次工具调用的所有必要信息，包括唯一标识、工具名称和参数。
    支持从OpenAI的tool_call格式转换。
    
    属性:
        id (str): 调用的唯一标识符
            - 格式: "call_" + 随机字符串
            - 用于关联调用和结果
            - 必须全局唯一
        
        name (str): 工具名称
            - 必须与ToolRegistry中注册的名称一致
            - 区分大小写
            - 示例: "search_knowledge", "get_system_status"
        
        arguments (Dict[str, Any]): 调用参数字典
            - 键值对形式
            - 参数类型由工具定义决定
            - 必须符合工具的参数schema
    
    使用示例:
        # 从OpenAI响应创建
        call = ToolCall.from_openai_tool_call(openai_tool_call)
        
        # 手动创建
        call = ToolCall(
            id="call_abc123",
            name="search_knowledge",
            arguments={"query": "年假", "top_k": 5}
        )
        
        # 获取缓存键
        cache_key = call.get_cache_key()
    """
    id: str
    name: str
    arguments: Dict[str, Any]
    
    @classmethod
    def from_openai_tool_call(cls, tool_call) -> "ToolCall":
        """
        从OpenAI ToolCall对象创建ToolCall实例
        
        解析OpenAI API返回的tool_call对象，提取关键信息。
        
        参数:
            tool_call: OpenAI的tool_call对象
                - 必须包含id属性
                - 必须包含function.name和function.arguments
        
        返回:
            ToolCall: 新创建的ToolCall实例
        
        异常:
            json.JSONDecodeError: 当arguments不是有效JSON时抛出
        
        示例:
            response = await client.chat.completions.create(...)
            tool_call = response.choices[0].message.tool_calls[0]
            call = ToolCall.from_openai_tool_call(tool_call)
        """
        return cls(
            id=tool_call.id,
            name=tool_call.function.name,
            arguments=json.loads(tool_call.function.arguments)
        )
    
    def get_cache_key(self) -> str:
        """
        生成缓存键
        
        基于工具名称和参数生成唯一的缓存键，用于结果缓存。
        相同的工具调用会生成相同的缓存键。
        
        返回:
            str: MD5哈希值，32位十六进制字符串
        
        缓存策略:
            - 使用工具名称和参数的组合
            - 参数按key排序确保一致性
            - 使用MD5哈希减少键长度
        
        示例:
            call1 = ToolCall(id="1", name="search", arguments={"q": "test"})
            call2 = ToolCall(id="2", name="search", arguments={"q": "test"})
            # call1.get_cache_key() == call2.get_cache_key()
        """
        args_str = json.dumps(self.arguments, sort_keys=True)
        return hashlib.md5(f"{self.name}:{args_str}".encode()).hexdigest()


@dataclass
class ToolResult:
    """
    Tool执行结果
    
    封装工具执行的结果数据，包括执行状态、返回数据和元信息。
    支持转换为OpenAI的tool消息格式。
    
    属性:
        success (bool): 执行是否成功
            - True: 工具执行成功，data字段有效
            - False: 执行失败，查看error字段了解原因
        
        data (Dict[str, Any]): 执行结果数据
            - 成功时包含工具返回的数据
            - 结构由具体工具定义
            - 失败时可能为空字典
        
        tool_name (str): 工具名称
            - 与ToolCall的name对应
        
        tool_call_id (str): 调用ID
            - 与ToolCall的id对应
            - 用于关联调用和结果
        
        error (Optional[str]): 错误信息
            - 成功时为None
            - 失败时包含错误描述
        
        cached (bool): 是否来自缓存
            - 默认False
            - 由缓存系统设置为True
        
        execution_time (float): 执行耗时（秒）
            - 默认0.0
            - 由执行器记录实际耗时
        
        timestamp (datetime): 时间戳
            - 默认为创建时的UTC时间
            - 用于日志和监控
    
    使用示例:
        # 成功结果
        result = ToolResult(
            success=True,
            data={"documents": [...]},
            tool_name="search_knowledge",
            tool_call_id="call_123"
        )
        
        # 失败结果
        result = ToolResult(
            success=False,
            data={},
            tool_name="search_knowledge",
            tool_call_id="call_123",
            error="网络连接失败"
        )
        
        # 转换为OpenAI格式
        message = result.to_openai_tool_message()
    """
    success: bool
    data: Dict[str, Any]
    tool_name: str
    tool_call_id: str
    error: Optional[str] = None
    cached: bool = False
    execution_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_openai_tool_message(self) -> Dict[str, Any]:
        """
        转换为OpenAI Tool消息格式
        
        将执行结果转换为OpenAI API要求的tool消息格式，
        用于继续对话或生成最终回答。
        
        返回:
            Dict[str, Any]: OpenAI格式的tool消息
                - role: "tool"
                - tool_call_id: 调用ID
                - name: 工具名称
                - content: JSON格式的结果数据
        
        格式说明:
            - content必须是字符串格式
            - 使用JSON序列化data字段
            - ensure_ascii=False支持中文
        
        示例:
            result = ToolResult(...)
            messages.append(result.to_openai_tool_message())
        """
        return {
            "role": "tool",
            "tool_call_id": self.tool_call_id,
            "name": self.tool_name,
            "content": json.dumps(self.data, ensure_ascii=False)
        }


@dataclass
class ToolDecision:
    """
    LLM的工具决策
    
    封装LLM对是否需要调用工具的决策结果。
    这是实现Agent自主决策的核心数据结构。
    
    属性:
        should_use_tool (bool): 是否需要使用工具
            - True: LLM决定需要调用工具
            - False: LLM决定直接回答
        
        tool_calls (List[ToolCall]): 需要调用的工具列表
            - 当should_use_tool为True时非空
            - 支持多工具并行调用
            - 默认为空列表
        
        reasoning (str): 决策理由
            - LLM的思考过程
            - 可能为空字符串
            - 用于调试和日志
    
    设计考虑:
        - 支持多工具并行调用
        - 兼容OpenAI的function calling格式
        - 提供便捷的属性检查
    
    使用示例:
        # 从OpenAI响应创建
        decision = ToolDecision.from_openai_response(response)
        
        # 检查决策
        if decision.should_use_tool:
            for call in decision.tool_calls:
                print(f"调用: {call.name}")
        else:
            print(f"直接回答: {decision.reasoning}")
    """
    should_use_tool: bool
    tool_calls: List[ToolCall] = field(default_factory=list)
    reasoning: str = ""
    
    @property
    def has_tool_calls(self) -> bool:
        """
        检查是否有工具调用
        
        便捷属性，用于快速判断是否有需要执行的工具。
        
        返回:
            bool: tool_calls列表是否非空
        
        使用场景:
            - 在决策后快速检查
            - 避免空列表遍历
        
        示例:
            if decision.has_tool_calls:
                results = await executor.execute_batch(decision.tool_calls)
        """
        return len(self.tool_calls) > 0
    
    @classmethod
    def from_openai_response(cls, response) -> "ToolDecision":
        """
        从OpenAI响应创建ToolDecision
        
        解析OpenAI Chat Completion响应，提取工具决策信息。
        
        参数:
            response: OpenAI Chat Completion响应对象
                - 必须包含choices列表
                - 第一个choice包含message
        
        返回:
            ToolDecision: 解析后的决策对象
        
        解析逻辑:
            1. 提取message对象
            2. 检查是否有tool_calls属性
            3. 如果有，创建ToolCall列表
            4. 如果没有，返回不使用工具的决策
        
        示例:
            response = await client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                tools=tools,
                tool_choice="auto"
            )
            decision = ToolDecision.from_openai_response(response)
        """
        message = response.choices[0].message
        tool_calls = getattr(message, "tool_calls", None)
        content = getattr(message, "content", "") or ""
        
        if tool_calls and len(tool_calls) > 0:
            return cls(
                should_use_tool=True,
                tool_calls=[ToolCall.from_openai_tool_call(tc) for tc in tool_calls],
                reasoning=content
            )
        
        return cls(should_use_tool=False, reasoning=content)


@dataclass
class ResponseChunk:
    """
    响应数据块
    
    用于流式响应的数据块，支持多种响应类型。
    可以转换为SSE（Server-Sent Events）格式。
    
    属性:
        type (str): 数据块类型
            - "text": 文本内容块
            - "tool_call": 工具调用块
            - "done": 完成块
            - "error": 错误块
        
        content (Optional[str]): 文本内容
            - type为"text"时有效
            - 流式输出的文本片段
        
        tool_name (Optional[str]): 工具名称
            - type为"tool_call"时有效
        
        tool_args (Optional[Dict]): 工具参数
            - type为"tool_call"时有效
        
        sources (Optional[List[Dict]]): 引用来源列表
            - type为"done"时有效
            - 包含文档来源信息
        
        error (Optional[str]): 错误信息
            - type为"error"时有效
    
    SSE格式:
        data: {"type": "text", "content": "..."}
        
    使用示例:
        # 文本块
        chunk = ResponseChunk(type="text", content="你好")
        yield chunk.to_sse_data()
        
        # 完成块
        chunk = ResponseChunk(type="done", sources=[...])
        yield chunk.to_sse_data()
    """
    type: str  # "text", "tool_call", "done", "error"
    content: Optional[str] = None
    tool_name: Optional[str] = None
    tool_args: Optional[Dict] = None
    sources: Optional[List[Dict]] = None
    error: Optional[str] = None
    
    def to_sse_data(self) -> str:
        """
        转换为SSE数据格式
        
        将数据块转换为Server-Sent Events格式，用于流式传输。
        
        返回:
            str: SSE格式的字符串
                - 格式: "data: {json}\n\n"
                - 符合SSE规范
        
        转换规则:
            1. 构建包含所有非None字段的字典
            2. 序列化为JSON
            3. 添加SSE前缀和后缀
        
        示例:
            chunk = ResponseChunk(type="text", content="Hello")
            sse_data = chunk.to_sse_data()
            # 返回: 'data: {"type": "text", "content": "Hello"}\n\n'
        """
        data = {
            "type": self.type,
            "content": self.content,
            "tool_name": self.tool_name,
            "tool_args": self.tool_args,
            "sources": self.sources,
            "error": self.error
        }
        # 移除None值，减少传输数据量
        data = {k: v for k, v in data.items() if v is not None}
        return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


@dataclass
class Observation:
    """
    ReAct 循环中单轮的观察结果

    记录一次 Reason → Act → Observe 迭代的完整信息，
    供下一轮 LLM 推理时作为上下文输入。

    属性:
        iteration (int): 当前迭代轮次（从 1 开始）
        tool_calls (List[ToolCall]): 本轮执行的工具调用列表
        results (List[ToolResult]): 本轮工具执行结果列表
        reasoning (str): LLM 本轮的推理说明
    """
    iteration: int
    tool_calls: List[ToolCall]
    results: List[ToolResult]
    reasoning: str = ""

    def to_context_message(self) -> Dict[str, Any]:
        """将观察结果格式化为 LLM 可读的上下文消息"""
        summaries = []
        for tc, tr in zip(self.tool_calls, self.results):
            status = "成功" if tr.success else f"失败: {tr.error}"
            summaries.append(f"- 工具 {tc.name}: {status}")
        return {
            "role": "user",
            "content": f"[第{self.iteration}轮工具调用结果]\n" + "\n".join(summaries)
        }


@dataclass
class RAGContext:
    """
    RAG检索上下文
    
    封装RAG（Retrieval-Augmented Generation）检索的结果，
    包括检索到的文档、来源信息和格式化的上下文文本。
    
    属性:
        documents (List[Dict[str, Any]]): 检索到的文档列表
            - 每个文档是一个字典
            - 包含content和metadata等信息
        
        sources (List[Dict[str, Any]]): 引用来源列表
            - 用于展示给用户
            - 包含id、filename、content等
        
        context_text (str): 格式化的上下文文本
            - 用于传递给LLM
            - 格式: "[1] 文档内容\n\n[2] 文档内容..."
        
        similarity_score (float): 相似度得分
            - 默认0.0
            - 范围0-1，越高越相关
        
        document_count (int): 文档数量
            - 与documents列表长度一致
    
    使用场景:
        - 向量检索后传递给LLM
        - 展示引用来源给用户
        - 记录检索日志
    
    使用示例:
        context = RAGContext(
            documents=[{"content": "...", "metadata": {...}}],
            sources=[{"id": "1", "filename": "doc.pdf", "content": "..."}],
            context_text="[1] 文档内容...",
            document_count=1
        )
        
        # 传递给LLM
        messages = [{"role": "user", "content": f"上下文: {context.context_text}\n问题: ..."}]
    """
    documents: List[Dict[str, Any]]
    sources: List[Dict[str, Any]]
    context_text: str
    similarity_score: float = 0.0
    document_count: int = 0
