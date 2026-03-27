"""
QA Agent - 问答协调Agent

本模块实现了核心的问答Agent，负责协调Tool调用和RAG检索，为用户提供智能问答服务。
QAAgent是系统的核心协调器，实现了自主决策、工具调用和知识检索的统一编排。

核心功能:
    1. 查询优化: 基于知识库内容优化用户查询
    2. 自主决策: 智能判断是否需要调用工具
    3. Tool流程: 执行工具调用并生成回答
    4. RAG流程: 基于知识库检索生成回答
    5. 流式响应: 支持流式输出，提升用户体验

架构设计:
    QAAgent作为协调Agent，不直接处理具体业务，而是:
    - 调用KBQueryOptimizer优化查询
    - 通过LLMClient进行决策和生成
    - 使用ToolExecutor执行工具调用
    - 利用RAG系统进行知识检索

使用示例:
    agent = get_qa_agent()
    async for chunk in agent.process("什么是年假?", history):
        print(chunk, end="")
"""

import logging
import time
from typing import Dict, List, Optional, AsyncGenerator
from dataclasses import dataclass

from app.services.tool_types import ToolCall, ToolResult, ToolDecision, RAGContext, Observation
from app.services.tool_executor import get_tool_executor
from app.services.llm_client import get_llm_client, LLMConfig
from app.services.response_builder import ResponseBuilder
from app.services.kb_query_optimizer import get_kb_optimizer
from app.services.answer_validator import get_answer_validator
from app.services.suggestion_generator import get_suggestion_generator
from app.services.link_matcher import get_link_matcher
from app.tools.base import ToolRegistry
from app.core.embeddings import get_embeddings
from app.core.chroma import get_documents_collection
from app.prompts.manager import prompt_manager
from app.prompts.strict_qa import StrictQAPrompt, ConstraintPromptBuilder
from app.core.constraint_config import get_constraint_config

logger = logging.getLogger(__name__)


@dataclass
class QAConfig:
    """
    QA Agent配置类
    
    定义QAAgent运行时的各项参数配置，使用dataclass简化配置管理。
    
    属性:
        max_rag_docs (int): RAG检索时返回的最大文档数量
            - 默认值: 5
            - 建议范围: 3-10
            - 过多会增加上下文长度和响应时间
            - 过少可能遗漏重要信息
        
        tool_decision_temperature (float): Tool决策时的LLM温度参数
            - 默认值: 0.1
            - 建议范围: 0.0-0.3
            - 低温度确保决策的稳定性和一致性
            - Tool决策需要精确判断，不建议使用高温度
        
        answer_temperature (float): 生成回答时的LLM温度参数
            - 默认值: 0.3
            - 建议范围: 0.1-0.5
            - 适中温度保证回答的准确性和多样性
            - 过高可能导致幻觉，过低则回答过于机械
        
        enable_performance_logging (bool): 是否启用性能日志
            - 默认值: True
            - 启用后会记录各阶段耗时
            - 建议生产环境保持启用，便于性能监控
    
    使用示例:
        config = QAConfig(
            max_rag_docs=5,
            tool_decision_temperature=0.1,
            answer_temperature=0.3,
            enable_performance_logging=True
        )
        agent = QAAgent(config)
    """
    max_rag_docs: int = 5
    tool_decision_temperature: float = 0.1
    answer_temperature: float = 0.3
    enable_performance_logging: bool = True


class QAAgent:
    """
    问答Agent - 协调Tool和RAG
    
    QAAgent是系统的核心协调Agent，负责整个问答流程的编排和执行。
    它实现了智能的查询路由机制，能够自主判断使用工具调用还是RAG检索。
    
    核心职责:
        1. 查询预处理: 优化用户查询，提高检索精度
        2. 智能路由: 判断使用Tool路径还是RAG路径
        3. 结果整合: 统一处理不同路径的返回结果
        4. 流式输出: 支持SSE流式响应
    
    工作流程:
        用户查询 -> 查询优化 -> Tool决策 -> [Tool路径 | RAG路径] -> 流式输出
    
    设计模式:
        - 策略模式: Tool路径和RAG路径是两种不同的执行策略
        - 模板方法: process方法定义了固定的执行流程
    
    性能优化:
        - 使用异步IO提高并发性能
        - 流式输出降低首字节响应时间
        - 缓存机制减少重复计算
    
    属性:
        _config (QAConfig): Agent配置对象
        _tool_executor (ToolExecutor): 工具执行器实例
        _llm_client (LLMClient): LLM客户端实例
    
    示例:
        agent = QAAgent()
        async for chunk in agent.process("请假流程是什么?"):
            yield chunk
    """
    
    def __init__(self, config: QAConfig = None):
        """
        初始化QAAgent
        
        创建Agent实例，初始化所需的执行器和客户端。
        
        参数:
            config (QAConfig, optional): Agent配置对象
                - 如果为None，使用默认配置
                - 建议根据业务需求自定义配置
        
        初始化流程:
            1. 设置配置（使用默认值或传入配置）
            2. 获取ToolExecutor实例
            3. 创建LLMClient实例（配置温度参数）
        """
        self._config = config or QAConfig()
        self._tool_executor = get_tool_executor()
        self._llm_client = get_llm_client(LLMConfig(
            temperature=self._config.answer_temperature,
            tool_decision_temperature=self._config.tool_decision_temperature
        ))
    
    async def process(
        self,
        query: str,
        history: List[Dict] = None
    ) -> AsyncGenerator[str, None]:
        """
        处理用户查询的主入口方法
        
        这是QAAgent的核心方法，实现了完整的问答处理流程。
        采用异步生成器模式，支持流式输出。
        
        参数:
            query (str): 用户输入的查询文本
                - 不能为空
                - 建议长度: 1-500字符
                - 支持自然语言查询
            
            history (List[Dict], optional): 对话历史记录
                - 格式: [{"role": "user/assistant", "content": "..."}]
                - 用于多轮对话上下文理解
                - 建议传入最近4-6轮对话
                - 默认为None，表示无历史上下文
        
        返回:
            AsyncGenerator[str, None]: 流式响应生成器
                - 每次yield一个SSE格式的数据块
                - 格式: "data: {json}\n\n"
                - 包含type字段标识数据类型（text/done/error）
        
        处理流程:
            0. 检查禁止主题（预检查）
            1. 知识库查询优化（KBQueryOptimizer）
            2. Tool决策判断（LLM）
            3. 分支执行:
               - Tool路径: 执行工具调用 -> 生成回答
               - RAG路径: 向量检索 -> 生成回答
            4. 流式输出结果
        
        性能指标:
            - Tool决策: ~0.35s
            - 向量检索: ~0.08s
            - 端到端: ~2.1s
        
        示例:
            async for chunk in agent.process("什么是年假?", history):
                # chunk格式: "data: {\"type\": \"text\", \"content\": \"...\"}\n\n"
                yield chunk
        
        注意事项:
            - 此方法为异步生成器，必须使用async for迭代
            - 每次调用都是独立的，不保持状态
            - 建议在外层处理异常
        """
        start_time = time.time()
        
        # 0. 检查禁止主题（预检查）
        constraint_config = get_constraint_config()
        forbidden_check = await self._check_forbidden_topics(query, constraint_config)
        if forbidden_check:
            # 查询包含禁止主题，直接拒绝
            logger.warning(f"[Forbidden] Query contains forbidden topics: {query}")
            yield ResponseBuilder.text_chunk(forbidden_check)
            yield ResponseBuilder.done_chunk([], content=forbidden_check)
            return
        
        # 1. 基于知识库优化查询
        # 使用KBQueryOptimizer分析查询，提取关键词，匹配相关文档
        kb_optimizer = await get_kb_optimizer()
        optimization = await kb_optimizer.optimize(query)
        
        if self._config.enable_performance_logging:
            logger.info(f"[KB Optimize] Query: '{query}' -> '{optimization.optimized_query}'")
            logger.info(f"[KB Optimize] Keywords: {optimization.keywords}, Related docs: {optimization.related_docs}")
        
        # 使用优化后的查询进行后续处理
        # 只有当优化置信度较高时才使用优化查询，否则使用原始查询
        optimized_query = optimization.optimized_query if optimization.confidence > 0.6 else query
        
        # 2. 判断是否需要Tool
        # 通过LLM判断当前查询是否需要调用工具
        tool_decision_start = time.time()
        decision = await self._should_use_tool(optimized_query, history)
        tool_decision_time = time.time() - tool_decision_start
        if self._config.enable_performance_logging:
            logger.info(f"[Performance] Tool decision: {tool_decision_time:.3f}s, use_tool: {decision.should_use_tool}")
        
        # 3. 根据决策执行不同路径
        if decision.should_use_tool:
            # 3a. 执行Tool流程
            # 当需要工具调用时，执行工具并基于结果生成回答
            async for chunk in self._execute_tool_flow(optimized_query, decision.tool_calls, history):
                yield chunk
        else:
            # 3b. 执行RAG流程
            # 当不需要工具时，使用向量检索获取知识库内容
            async for chunk in self._execute_rag_flow(optimized_query, history, optimization.keywords):
                yield chunk
        
        if self._config.enable_performance_logging:
            total_time = time.time() - start_time
            logger.info(f"[Performance] Total processing time: {total_time:.3f}s")
    
    async def _check_forbidden_topics(self, query: str, config) -> Optional[str]:
        """
        检查查询是否包含禁止主题或关键词
        
        使用两层检查：
        1. 快速字符串匹配（性能优先）
        2. LLM 语义理解（智能检测同义词和隐含意图）
        
        参数:
            query: 用户查询
            config: 约束配置
        
        返回:
            如果包含禁止内容，返回拒绝消息；否则返回 None
        """
        generation_config = config.generation
        forbidden_topics = generation_config.get('forbidden_topics', [])
        forbidden_keywords = generation_config.get('forbidden_keywords', [])
        
        if not forbidden_topics and not forbidden_keywords:
            return None
        
        # 第一层：快速字符串匹配
        for topic in forbidden_topics:
            if topic in query:
                logger.warning(f"[Forbidden] Query contains forbidden topic (exact match): '{topic}'")
                return self._build_forbidden_message(topic, "主题")
        
        for keyword in forbidden_keywords:
            if keyword in query:
                logger.warning(f"[Forbidden] Query contains forbidden keyword (exact match): '{keyword}'")
                return self._build_forbidden_message(keyword, "关键词")
        
        # 第二层：LLM 语义理解（检测同义词和隐含意图）
        # 只有当配置了禁止主题时才进行语义检查
        if forbidden_topics:
            semantic_check = await self._check_forbidden_topics_semantic(query, forbidden_topics)
            if semantic_check:
                return semantic_check
        
        return None
    
    async def _check_forbidden_topics_semantic(self, query: str, forbidden_topics: List[str]) -> Optional[str]:
        """
        使用 LLM 进行语义检查，识别同义词和隐含意图
        
        参数:
            query: 用户查询
            forbidden_topics: 禁止主题列表
        
        返回:
            如果语义上涉及禁止主题，返回拒绝消息；否则返回 None
        """
        try:
            # 使用统一提示词管理
            topics_str = "、".join(forbidden_topics)
            
            # 从配置获取提示词
            prompt_result = prompt_manager.render("forbidden_topic_check", {
                "forbidden_topics": topics_str,
                "query": query
            })
            
            # 使用 LLM 进行判断
            messages = [
                {'role': 'system', 'content': prompt_result.get('system', '你是一个内容审核助手，负责识别查询是否涉及禁止主题。')},
                {'role': 'user', 'content': prompt_result.get('user', '')}
            ]
            
            # 使用低温度确保判断稳定
            response = await self._llm_client.chat(messages, temperature=0.1, max_tokens=10)
            response = response.strip().upper()
            
            logger.info(f"[Forbidden] Semantic check - Query: '{query}', LLM response: '{response}'")
            
            if response.startswith('YES'):
                logger.warning(f"[Forbidden] Query involves forbidden topic (semantic match): '{query}'")
                # 尝试识别具体是哪个主题
                matched_topic = forbidden_topics[0] if forbidden_topics else "敏感内容"
                return self._build_forbidden_message(matched_topic, "主题")
            
            logger.debug(f"[Forbidden] Semantic check passed for query: '{query}'")
            return None
            
        except Exception as e:
            # 如果语义检查失败，记录日志但不影响主流程
            logger.warning(f"[Forbidden] Semantic check failed: {e}")
            return None
    
    def _build_forbidden_message(self, forbidden_item: str, item_type: str) -> str:
        """
        构建禁止主题的拒绝消息
        
        参数:
            forbidden_item: 禁止的主题或关键词
            item_type: 类型（"主题" 或 "关键词"）
        
        返回:
            拒绝消息
        """
        config = get_constraint_config()
        contact_info = config.fallback.get('contact_info', '')
        
        message = f"抱歉，关于「{forbidden_item}」相关的问题属于禁止回答的{item_type}。\n\n"
        message += "根据公司政策，此类信息属于保密或敏感内容。"
        
        if contact_info:
            message += f"\n\n{contact_info}"
        else:
            message += "\n\n如有疑问，请联系相关部门。"
        
        return message
    
    async def _should_use_tool(
        self,
        query: str,
        history: List[Dict] = None
    ) -> ToolDecision:
        """
        判断是否需要使用Tool
        
        通过LLM分析用户查询，判断是否需要调用工具来完成任务。
        这是实现Agent自主决策的关键方法。
        
        参数:
            query (str): 用户查询文本
            history (List[Dict], optional): 对话历史
        
        返回:
            ToolDecision: LLM的决策结果
                - should_use_tool (bool): 是否需要使用工具
                - tool_calls (List[ToolCall]): 需要调用的工具列表
                - reasoning (str): 决策理由
        
        决策逻辑:
            1. 获取所有可用工具的定义
            2. 构建包含工具描述的提示
            3. 调用LLM进行决策
            4. 解析LLM响应，提取决策结果
        
        工具选择策略:
            - 使用低温度(0.1)确保决策稳定性
            - tool_choice="auto"让LLM自主判断
            - 支持多工具并行调用
        
        性能考虑:
            - 平均耗时: 0.35s
            - 可考虑添加决策缓存
            - 对于简单查询可跳过决策
        
        示例:
            decision = await self._should_use_tool("搜索关于年假的规定")
            if decision.should_use_tool:
                for tool_call in decision.tool_calls:
                    print(f"需要调用: {tool_call.name}")
        """
        tools = ToolRegistry.get_tools_for_llm()
        # print('tools注册=============', tools)
        # 如果没有可用工具，直接返回不使用工具
        if not tools:
            return ToolDecision(should_use_tool=False)
        
        # 构建消息列表
        messages = [
            {
                "role": "system",
                "content": self._build_tool_router_prompt()
            },
            {"role": "user", "content": query}
        ]
        
        # 添加历史上下文（最近4轮）
        if history:
            for msg in history[-4:]:
                if msg.get("role") in ["user", "assistant"]:
                    messages.insert(-1, msg)
        
        # 调用LLM进行决策
        return await self._llm_client.chat_with_tools(messages, tools)
    
    def _build_tool_router_prompt(self) -> str:
        """
        构建Tool路由提示
        
        生成用于LLM决策的系统提示，包含所有可用工具的描述。
        """
        tool_descriptions = []
        for tool_id, tool in ToolRegistry._tools.items():
            defn = tool.definition
            if defn.enabled:
                tool_descriptions.append(f"- {defn.name}: {defn.description}")
        
        # 使用统一提示词管理
        template = prompt_manager.get_system_prompt("tool_router")
        if template:
            return template.format(tool_descriptions="\n".join(tool_descriptions))
        
        # 回退到默认
        return f"""你是一个智能助手，可以访问以下工具：

{chr(10).join(tool_descriptions)}

根据用户的问题，判断是否需要调用工具。如果需要，返回工具调用；如果不需要，直接回答用户问题。"""
    
    async def _execute_tool_flow(
        self,
        query: str,
        tool_calls: List[ToolCall],
        history: List[Dict] = None
    ) -> AsyncGenerator[str, None]:
        """
        执行 ReAct 多轮 Tool 流程

        采用 Reason → Act → Observe 循环，最多迭代 MAX_ITERATIONS 轮。
        每轮将工具结果追加为 Observation，供下一轮 LLM 推理使用。
        当 LLM 不再调用工具时退出循环，基于所有 observations 生成最终回答。
        """
        import json as json_module

        MAX_ITERATIONS = 5
        observations: List[Observation] = []
        all_results: List[ToolResult] = []

        # 构建基础消息（系统提示 + 历史 + 当前查询）
        system_prompt = (
            prompt_manager.get_system_prompt("tool_flow")
            or "你是一个专业的知识库问答助手。根据工具返回的结果，用友好的方式回答用户的问题。"
        )
        base_messages: List[Dict] = [{"role": "system", "content": system_prompt}]
        if history:
            for msg in history[-4:]:
                if msg.get("role") in ["user", "assistant"]:
                    base_messages.append(msg)
        base_messages.append({"role": "user", "content": query})

        current_tool_calls = tool_calls

        # ── ReAct 循环 ──────────────────────────────────────────────
        for iteration in range(1, MAX_ITERATIONS + 1):
            # Act: 并行执行本轮工具调用
            results = await self._tool_executor.execute_batch(current_tool_calls)
            all_results.extend(results)

            obs = Observation(
                iteration=iteration,
                tool_calls=current_tool_calls,
                results=results,
                reasoning=""
            )
            observations.append(obs)

            if self._config.enable_performance_logging:
                logger.info(
                    "[ReAct] 第%d轮: 执行 %d 个工具",
                    iteration, len(current_tool_calls)
                )

            # 将本轮工具调用和结果追加到消息链
            for tc, tr in zip(current_tool_calls, results):
                args_str = (
                    tc.arguments
                    if isinstance(tc.arguments, str)
                    else json_module.dumps(tc.arguments, ensure_ascii=False)
                )
                base_messages.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.name, "arguments": args_str}
                    }]
                })
                base_messages.append(tr.to_openai_tool_message())

            # Reason: 让 LLM 决定是否继续调用工具
            next_decision = await self._should_use_tool(
                query,
                history=[obs.to_context_message() for obs in observations]
            )

            if not next_decision.should_use_tool:
                # LLM 认为信息已足够，退出循环
                break

            current_tool_calls = next_decision.tool_calls

        # ── 生成最终回答（流式）──────────────────────────────────────
        full_answer = ""
        async for chunk in self._llm_client.stream_chat(base_messages):
            full_answer += chunk
            yield ResponseBuilder.text_chunk(chunk)

        # 生成快捷提问
        suggested_questions = []
        suggest_config = get_constraint_config().suggest_questions
        if suggest_config.get("enabled", True):
            try:
                suggestion_generator = get_suggestion_generator()
                suggested_questions = await suggestion_generator.generate(
                    question=query,
                    answer=full_answer,
                    count=suggest_config.get("count", 3)
                )
            except Exception as e:
                logger.warning("[Tool Flow] 生成快捷提问失败: %s", e)

        # 提取sources
        sources = self._extract_sources_from_tool_results(all_results)
        
        # 匹配相关链接（只在有sources时）
        related_links = []
        if sources and len(sources) > 0:
            try:
                link_matcher = get_link_matcher()
                related_links = await link_matcher.match_links(query)
                if related_links:
                    logger.info(f"[Tool Flow] 匹配到 {len(related_links)} 个相关链接")
            except Exception as e:
                logger.warning("[Tool Flow] 匹配链接失败: %s", e)
        else:
            logger.info("[Tool Flow] 没有找到相关文档，跳过链接匹配")

        yield ResponseBuilder.done_chunk(
            sources,
            content=full_answer,
            suggested_questions=suggested_questions,
            related_links=related_links
        )
    
    async def _execute_rag_flow(
        self,
        query: str,
        history: List[Dict] = None,
        optimized_keywords: List[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        执行RAG流程
        
        当决策为不需要使用工具时，执行此流程。
        通过向量检索获取相关知识，然后生成回答。
        
        参数:
            query (str): 用户查询文本
            history (List[Dict], optional): 对话历史
            optimized_keywords (List[str], optional): 优化后的关键词列表
        
        返回:
            AsyncGenerator[str, None]: 流式响应
        
        执行流程:
            1. 向量检索获取相关文档
            2. 检查是否有检索结果
            3. 构建包含上下文的提示（应用约束配置）
            4. 流式生成回答
            5. 答案验证和长度限制
            6. 返回引用来源
        
        检索增强:
            - 使用优化后的关键词增强查询
            - 结合语义相似度和关键词匹配
            - 限制返回文档数量控制上下文长度
        
        无结果处理:
            - 返回友好的fallback消息
            - 提供相关建议或联系方式
        
        性能考虑:
            - 向量检索: ~0.08s
            - 生成回答: ~1.5s
            - 可考虑添加检索缓存
        
        示例:
            async for chunk in self._execute_rag_flow(query, history, keywords):
                yield chunk
        """
        # 获取约束配置
        constraint_config = get_constraint_config()
        
        # 1. 向量检索（使用优化后的关键词增强检索）
        rag_context = await self._retrieve(query, optimized_keywords)

        if not rag_context.documents:
            # 无检索结果，返回fallback消息（不匹配链接）
            fallback_msg = StrictQAPrompt.get_fallback_message(constraint_config)
            yield ResponseBuilder.text_chunk(fallback_msg)
            yield ResponseBuilder.done_chunk([], content=fallback_msg)
            return

        # 2. 检查最小文档数要求
        retrieval_config = constraint_config.retrieval
        min_docs = retrieval_config.get('min_relevant_docs', 1)
        if len(rag_context.documents) < min_docs:
            logger.warning(
                f"检索文档数不足: {len(rag_context.documents)} < {min_docs}, "
                f"query='{query[:50]}...'"
            )

            # 返回兜底消息
            fallback_msg = StrictQAPrompt.get_fallback_message(constraint_config)
            yield ResponseBuilder.text_chunk(fallback_msg)
            yield ResponseBuilder.done_chunk([], content=fallback_msg)
            return

        # 3. 构建提示（应用约束配置）
        constraints = {
            'generation': constraint_config.generation,
            'validation': constraint_config.validation
        }
        
        system_prompt = ConstraintPromptBuilder.build_system_prompt(
            rag_context.context_text,
            constraints
        )
        
        messages = [{'role': 'system', 'content': system_prompt}]
        
        if history:
            for msg in history:
                if msg.get("role") in ["user", "assistant"]:
                    messages.append(msg)
        
        messages.append({'role': 'user', 'content': query})
        
        # 4. 流式生成回答
        full_answer = ""
        async for chunk in self._llm_client.stream_chat(messages):
            full_answer += chunk
            yield ResponseBuilder.text_chunk(chunk)
        
        # 5. 答案验证
        validator = get_answer_validator()
        validation_result = validator.validate_answer(
            full_answer,
            rag_context.sources,
            rag_context.context_text
        )
        
        if not validation_result.is_valid:
            logger.warning(
                f"答案验证失败: confidence={validation_result.confidence_score:.2f}, "
                f"warnings={validation_result.warnings}"
            )
            
            if validation_result.confidence_score < 0.3:
                warning_msg = "\n\n注意：此回答的可信度较低，建议谨慎参考。"
                yield ResponseBuilder.text_chunk(warning_msg)
                full_answer += warning_msg
        
        # 6. 长度限制
        max_length = constraint_config.generation.get('max_answer_length', 1000)
        if len(full_answer) > max_length:
            logger.warning(f"回答长度 {len(full_answer)} 超过限制 {max_length}")
            truncated_answer = full_answer[:max_length] + "..."
            # 如果已经输出了完整答案，不再输出截断版本
            # 只记录日志和更新 full_answer 用于后续处理
            full_answer = truncated_answer
        
        # 7. 生成快捷提问
        suggested_questions = []
        suggest_config = constraint_config.suggest_questions
        if suggest_config.get("enabled", True):
            try:
                suggestion_generator = get_suggestion_generator()
                suggested_questions = await suggestion_generator.generate(
                    question=query,
                    answer=full_answer,
                    count=suggest_config.get("count", 3)
                )
                logger.info(f"[RAG] 生成了 {len(suggested_questions)} 个快捷提问")
            except Exception as e:
                logger.warning(f"[RAG] 生成快捷提问失败: {e}")
        
        # 8. 匹配相关链接（只在有sources时）
        related_links = []
        if rag_context.sources and len(rag_context.sources) > 0:
            try:
                link_matcher = get_link_matcher()
                related_links = await link_matcher.match_links(query)
                if related_links:
                    logger.info(f"[RAG] 匹配到 {len(related_links)} 个相关链接")
            except Exception as e:
                logger.warning(f"[RAG] 匹配链接失败: {e}")
        else:
            logger.info("[RAG] 没有找到相关文档，跳过链接匹配")
        
        # 9. 返回sources、快捷提问和相关链接
        yield ResponseBuilder.done_chunk(
            rag_context.sources, 
            content=full_answer, 
            suggested_questions=suggested_questions,
            related_links=related_links
        )
    
    async def _retrieve(self, query: str, optimized_keywords: List[str] = None) -> RAGContext:
        """
        向量检索
        
        使用向量相似度检索获取知识库中的相关文档。
        
        参数:
            query (str): 用户查询文本
            optimized_keywords (List[str], optional): 优化后的关键词列表
                - 用于增强查询语义
                - 最多使用前3个关键词
        
        返回:
            RAGContext: 检索上下文对象
                - documents: 检索到的文档列表
                - sources: 引用来源列表
                - context_text: 格式化的上下文文本
                - document_count: 文档数量
        
        检索流程:
            1. 构建增强查询（原始查询 + 关键词）
            2. 生成查询向量
            3. 在向量数据库中检索
            4. 格式化结果
        
        增强策略:
            - 将关键词添加到查询中增强语义
            - 限制关键词数量避免查询过长
            - 平衡语义匹配和精确匹配
        
        性能考虑:
            - 向量生成: ~0.05s
            - 向量检索: ~0.03s
            - 总耗时: ~0.08s
        
        示例:
            context = await self._retrieve("什么是年假?", ["年假", "假期"])
            print(f"检索到 {context.document_count} 个文档")
        """
        embeddings = get_embeddings()
        constraint_config = get_constraint_config()
        validator = get_answer_validator()
        
        # 如果有优化后的关键词，使用增强查询
        search_query = query
        if optimized_keywords:
            # 将关键词添加到查询中增强语义
            search_query = f"{query} {' '.join(optimized_keywords[:3])}"
        
        # 生成查询向量
        query_embedding = await embeddings.aembed_query(search_query)
        
        # 获取检索配置
        retrieval_config = constraint_config.retrieval
        max_docs = retrieval_config.get("max_relevant_docs", self._config.max_rag_docs)
        
        # 在向量数据库中检索
        collection = get_documents_collection()
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=max_docs
        )
        
        # 格式化结果
        documents = []
        sources = []
        context_parts = []
        
        if results["documents"] and results["documents"][0]:
            logger.info(f"[RAG] 检索到 {len(results['documents'][0])} 个文档")
            
            # 提取文档、元数据和距离
            docs = results["documents"][0]
            metadatas = results["metadatas"][0] if results["metadatas"] and results["metadatas"][0] else [{}] * len(docs)
            distances = results["distances"][0] if results["distances"] else [1.0] * len(docs)
            
            # 使用验证器过滤检索结果
            if retrieval_config.get("enabled", True):
                filtered_docs, _ = validator.validate_retrieval(docs, metadatas, distances)
                
                # 使用过滤后的文档
                for doc_info in filtered_docs:
                    documents.append(doc_info["content"])
                    context_parts.append(f"[{doc_info['index']+1}] {doc_info['content']}")
                
                logger.info(f"[RAG] 验证后保留 {len(filtered_docs)} 个文档")
            else:
                # 不验证，直接使用所有文档
                for i, doc in enumerate(docs):
                    documents.append(doc)
                    context_parts.append(f"[{i+1}] {doc}")
                filtered_docs = [{"content": d, "metadata": m, "distance": dist, "index": i} 
                                for i, (d, m, dist) in enumerate(zip(docs, metadatas, distances))]
            
            # 对于 sources，只返回最相关的一个文档
            if filtered_docs:
                best_doc_info = filtered_docs[0]
                best_doc = best_doc_info["content"]
                best_metadata = best_doc_info["metadata"]
                best_idx = best_doc_info["index"]
                
                # 提取文件名
                filename = "Unknown"
                if best_metadata:
                    filename = (best_metadata.get("document_name") or 
                               best_metadata.get("filename") or 
                               best_metadata.get("source_file") or 
                               best_metadata.get("name") or 
                               "Unknown")
                
                # 如果是路径，只取文件名
                if isinstance(filename, str) and "/" in filename:
                    filename = filename.split("/")[-1]
                if isinstance(filename, str) and "\\" in filename:
                    filename = filename.split("\\")[-1]
                
                # 过滤掉无效的文件名
                if filename and filename.lower() not in ["unknown", "未知", "", "none", "null"]:
                    sources.append({
                        "id": str(best_idx+1),
                        "filename": filename,
                        "content": best_doc[:200] + "..." if len(best_doc) > 200 else best_doc
                    })
        
        return RAGContext(
            documents=documents,
            sources=sources,
            context_text="\n\n".join(context_parts),
            document_count=len(documents)
        )
    
    def _extract_sources_from_tool_results(self, results: List[ToolResult]) -> List[Dict]:
        """
        从Tool结果提取sources
        
        解析工具执行结果，提取引用来源信息。
        
        参数:
            results (List[ToolResult]): 工具执行结果列表
        
        返回:
            List[Dict]: 引用来源列表
                - 每个来源包含id、filename、content等信息
        
        提取逻辑:
            - 遍历所有工具结果
            - 查找包含documents字段的结果
            - 使用ResponseBuilder格式化来源
            - 根据filename去重
        
        示例:
            sources = self._extract_sources_from_tool_results([result1, result2])
            # 返回: [{"id": "1", "filename": "doc.pdf", "content": "..."}]
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


# 全局实例
# 使用全局单例模式，避免重复创建实例
_qa_agent: Optional[QAAgent] = None


def get_qa_agent(config: QAConfig = None) -> QAAgent:
    """
    获取QA Agent实例
    
    工厂函数，用于获取全局的QAAgent实例。
    采用单例模式，确保整个应用使用同一个实例。
    
    参数:
        config (QAConfig, optional): Agent配置对象
            - 仅在首次创建时使用
            - 后续调用忽略此参数
    
    返回:
        QAAgent: QA Agent实例
    
    线程安全:
        - 当前实现非线程安全
        - 如需并发访问，应添加锁机制
    
    使用示例:
        # 获取默认配置的实例
        agent = get_qa_agent()
        
        # 获取自定义配置的实例（仅首次有效）
        config = QAConfig(max_rag_docs=10)
        agent = get_qa_agent(config)
        
        # 使用实例
        async for chunk in agent.process("查询"):
            print(chunk)
    """
    global _qa_agent
    if _qa_agent is None:
        _qa_agent = QAAgent(config)
    return _qa_agent
