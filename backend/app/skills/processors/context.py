# -*- coding: utf-8 -*-
"""
上下文构建处理器 (ContextBuilder)

本模块负责将检索到的文档和对话历史构建成LLM可用的上下文格式。
是RAG流程中的关键组件，决定了LLM能看到什么信息。

核心功能:
    1. 文档内容格式化：将检索到的文档整理为带编号的引用格式
    2. 来源信息提取：记录文档名称和来源，用于展示引用
    3. 对话历史整合：合并相关对话历史到上下文中
    4. Token长度控制：确保上下文不超过LLM的Token限制

使用场景:
    - RAG检索后的上下文组装
    - 多文档问答的引用管理
    - 对话历史的动态整合

示例:
    processor = ContextBuilder()
    result = await processor.process(
        context={
            "retrieved_documents": [{"content": "...", "metadata": {...}}],
            "retrieved_conversations": [{"content": "..."}]
        },
        params={"max_tokens": 4000, "include_sources": True}
    )
    # result["context"] 包含格式化后的上下文
    # result["sources"] 包含来源信息列表
"""

from typing import Dict, Any, List
from app.skills.base import BaseProcessor, ProcessorRegistry


@ProcessorRegistry.register("ContextBuilder")
class ContextBuilder(BaseProcessor):
    """
    上下文构建处理器
    
    将检索结果（文档、对话历史）构建成LLM可用的上下文格式。
    支持Token长度控制和来源信息提取。
    
    属性:
        name: 处理器名称，固定为 "ContextBuilder"
    
    方法:
        process: 主处理方法，构建上下文并返回格式化结果
    """
    
    @property
    def name(self) -> str:
        """
        处理器名称
        
        返回:
            str: 固定返回 "ContextBuilder"
        """
        return "ContextBuilder"
    
    async def process(self, context: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """
        构建LLM上下文
        
        将检索到的文档和对话历史整合成格式化的上下文字符串，
        同时提取来源信息供引用展示。
        
        参数:
            context: 输入上下文，包含检索结果
                - retrieved_documents: List[Dict] 检索到的文档列表
                    每个文档包含 content(内容) 和 metadata(元数据)
                - retrieved_conversations: List[Dict] 检索到的对话历史列表
                    每个对话包含 content(内容)
                    
            params: 处理参数
                - max_tokens: int 最大Token数限制，默认4000
                    用于计算上下文长度上限（max_tokens * 4 字符）
                - include_sources: bool 是否包含来源信息，默认True
                    控制是否提取文档来源用于引用展示
        
        返回:
            Dict[str, Any]: 包含以下键的字典
                - context: str 构建好的上下文字符串
                    格式：[1] 文档内容\n\n[2] 文档内容\n\n--- 相关对话历史 ---\n对话内容
                - sources: List[Dict] 来源信息列表（当include_sources=True时）
                    每个来源包含：
                    - id: str 编号（"1", "2", ...）
                    - filename: str 文档名称（过滤后的有效名称）
                    - content: str 内容预览（前200字符+...）
        
        处理流程:
            1. 解析参数：获取 max_tokens 和 include_sources
            2. 处理检索文档：
               - 格式化文档内容为 "[编号] 内容" 格式
               - 提取有效的文档来源信息（过滤 Unknown/空名称）
            3. 处理对话历史：
               - 添加分隔线 "--- 相关对话历史 ---"
               - 追加每个对话的内容
            4. 合并上下文：用 "\n\n" 连接所有部分
            5. 长度控制：如果超过 max_tokens*4 字符，截断到限制长度
            6. 返回结果：包含 context 和 sources 的字典
        
        示例:
            >>> context = {
            ...     "retrieved_documents": [
            ...         {"content": "年假规定...", "metadata": {"document_name": "员工手册.pdf"}},
            ...         {"content": "请假流程...", "metadata": {"document_name": "制度.docx"}}
            ...     ],
            ...     "retrieved_conversations": [
            ...         {"content": "Q: 如何请假？ A: 需要提前申请..."}
            ...     ]
            ... }
            >>> params = {"max_tokens": 4000, "include_sources": True}
            >>> result = await processor.process(context, params)
            >>> print(result["context"])
            [1] 年假规定...
            
            [2] 请假流程...
            
            --- 相关对话历史 ---
            Q: 如何请假？ A: 需要提前申请...
            >>> print(result["sources"])
            [{"id": "1", "filename": "员工手册.pdf", "content": "年假规定......"},
             {"id": "2", "filename": "制度.docx", "content": "请假流程......"}]
        """
        
        # 步骤1：解析参数 - 获取最大token数和是否包含来源标志
        max_tokens = params.get("max_tokens", 4000)
        include_sources = params.get("include_sources", True)
        
        # 初始化上下文部分列表和来源列表
        context_parts = []
        sources = []
        
        # 步骤2：处理检索到的文档
        # 从上下文中获取检索文档列表，如果没有则使用空列表
        retrieved_docs = context.get("retrieved_documents", [])
        source_idx = 1  # 来源编号从1开始
        
        # 遍历每个检索到的文档
        for doc in retrieved_docs:
            # 将文档内容格式化为 "[编号] 内容" 格式，添加到上下文部分
            context_parts.append(f"[{source_idx}] {doc['content']}")
            
            # 如果需要包含来源信息，则提取文档元数据
            if include_sources:
                # 从文档元数据中获取文件名，如果没有元数据则使用空字符串
                filename = doc.get("metadata", {}).get("document_name", "")
                
                # 过滤掉无效的文件名（Unknown、空字符串、或AI生成的标记）
                # 这是为了确保只显示有意义的来源，避免显示"Unknown"等无价值信息
                if filename and filename.lower() not in ["unknown", "未知", "", "none", "null"]:
                    # 将有效的来源信息添加到来源列表
                    sources.append({
                        "id": str(source_idx),  # 来源编号（字符串格式）
                        "filename": filename,    # 文档名称
                        "content": doc["content"][:200] + "..."  # 内容预览（前200字符+省略号）
                    })
                    # 只有有效的来源才会增加编号
                    source_idx += 1
        
        # 步骤3：处理检索到的对话历史
        # 从上下文中获取检索对话列表，如果没有则使用空列表
        retrieved_convs = context.get("retrieved_conversations", [])
        
        # 如果有对话历史，则添加到上下文中
        if retrieved_convs:
            # 添加分隔线和标题，标明以下是相关对话历史
            context_parts.append("\n--- 相关对话历史 ---")
            # 遍历每个对话，将其内容添加到上下文部分
            for conv in retrieved_convs:
                context_parts.append(conv["content"])
        
        # 步骤4：合并所有上下文部分
        # 使用双换行符连接所有部分，形成完整的上下文字符串
        full_context = "\n\n".join(context_parts)
        
        # 步骤5：长度控制 - 如果上下文过长则截断
        # 简单的字符数控制：假设平均每个token约4个字符
        # 如果上下文长度超过 max_tokens * 4 字符，则截断到该长度
        if len(full_context) > max_tokens * 4:
            full_context = full_context[:max_tokens * 4]
        
        # 步骤6：返回结果字典
        # 包含构建好的上下文和来源信息列表
        return {
            "context": full_context,
            "sources": sources
        }
