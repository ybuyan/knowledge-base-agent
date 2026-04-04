"""
OrchestratorAgent — 意图路由 Agent

意图分类结果：
  qa                    知识查询
  memory                历史记忆检索
  hybrid                混合（知识 + 记忆）
  guide                 流程指引
"""
import asyncio
import logging
from typing import Any, Dict, List

from app.agents.base import BaseAgent
from app.core.llm import call_llm

logger = logging.getLogger(__name__)

# 保留关键词作为快速路径（可选）
_MEMORY_KW: List[str] = ["上次", "之前", "刚才", "你说过", "我问过", "刚刚说", "前面提到"]
_HYBRID_KW: List[str] = ["对比", "不同", "区别", "和之前", "和上次", "比较"]

# 意图识别的 system prompt
INTENT_DETECTION_PROMPT = """你是一个意图识别助手。请判断用户查询属于以下哪种意图：

1. **leave_balance** - 假期余额查询（新增）
   - 用户想查询假期余额、剩余天数
   - 例如：我的假期余额、年假还剩多少、查询假期、还有多少天假、我的年假、剩余假期
   - 关键特征：包含"余额"、"剩余"、"还有多少"、"查询假期"、"我的假期"、"还剩"等词

2. **guide** - 流程指引
   - 用户想了解如何办理某个流程、操作步骤
   - 例如：请假怎么办、如何申请、办理流程、申请怎么写、需要什么材料
   - 关键特征：询问"怎么做"、"如何办理"、"流程"、"步骤"
   - **重要**：如果上下文显示这是流程指引对话的延续（系统在询问信息，用户在回答），必须识别为 guide
   - **重要**：用户提供的日期、数字、简短回答（如"2024年4月24号"、"3天"、"是的"）在流程指引上下文中应识别为 guide

3. **memory** - 历史记忆
   - 用户明确询问之前的对话内容
   - 例如：上次说的、之前提到、你刚才说、我之前问过
   - 关键特征：明确的时间词（上次、之前、刚才、刚刚）+ 询问语气
   - **注意**：用户只是在回答问题（如提供日期、数字），不是 memory，而是 guide 的延续

4. **hybrid** - 混合查询
   - 需要对比历史信息和知识库
   - 例如：和之前的有什么区别、对比一下
   - 关键特征：对比词（对比、区别、不同）

5. **qa** - 知识查询（默认）
   - 查询知识库中的信息
   - 例如：年假有多少天、报销流程是什么
   - 关键特征：询问具体信息、政策、规定

请只返回意图类型，不要解释。格式：intent_type

示例：
用户：我的年假还剩多少
回答：leave_balance

用户：查询我的假期余额
回答：leave_balance

用户：请假申请怎么写
回答：guide

用户：年假有多少天
回答：qa

用户：上次你说的报销流程
回答：memory

用户查询：2024年4月24号
上下文：用户上一轮问了「我想请婚假」，系统回复了流程指引相关内容。当前查询可能是对上一轮对话的延续（用户在回答系统的问题）。
回答：guide

用户查询：3天
上下文：用户上一轮问了「我想请婚假」，系统回复了流程指引相关内容。当前查询可能是对上一轮对话的延续（用户在回答系统的问题）。
回答：guide"""


async def detect_intent_with_llm(query: str, history: list = None) -> str:
    """使用 LLM 进行意图识别
    
    Args:
        query: 当前查询
        history: 历史对话记录（用于判断是否是多轮对话的延续）
    """
    try:
        # 检查是否是多轮对话的延续
        context_hint = ""
        if history and len(history) >= 2:
            # 获取最近一轮对话
            last_user_msg = None
            last_assistant_msg = None
            for msg in reversed(history):
                if msg.get("role") == "assistant" and not last_assistant_msg:
                    last_assistant_msg = msg.get("content", "")
                elif msg.get("role") == "user" and not last_user_msg:
                    last_user_msg = msg.get("content", "")
                if last_user_msg and last_assistant_msg:
                    break
            
            # 如果上一轮是流程指引相关的对话，添加上下文提示
            if last_assistant_msg and any(keyword in last_assistant_msg for keyword in 
                ["申请", "流程", "步骤", "办理", "需要", "材料", "指引", "请问", "确认", 
                 "登记日期", "结婚", "婚假", "请假", "几天", "什么时候", "提供", "信息收集"]):
                context_hint = f"\n\n上下文：用户上一轮问了「{last_user_msg[:50]}」，系统回复了流程指引相关内容。当前查询可能是对上一轮对话的延续（用户在回答系统的问题）。"
        
        user_prompt = f"用户查询：{query}{context_hint}\n\n请判断意图类型："
        
        logger.debug("🤔 [INTENT] 使用 LLM 进行意图识别 | query='%s' | has_context=%s", 
                    query, bool(context_hint))
        logger.debug("🤔 [INTENT] 完整 prompt: %s", user_prompt)  # 添加调试日志
        
        result = await call_llm(user_prompt, INTENT_DETECTION_PROMPT)
        intent = result.strip().lower()
        
        # 验证返回的意图是否有效
        valid_intents = ["leave_balance", "guide", "memory", "hybrid", "qa"]
        if intent not in valid_intents:
            logger.warning("⚠️  [INTENT] LLM 返回无效意图: %s，使用默认 qa", intent)
            return "qa"
        
        logger.info("✅ [INTENT] LLM 识别意图 | query='%s' -> %s", query[:40], intent)
        return intent
        
    except Exception as e:
        logger.error("❌ [INTENT] LLM 意图识别失败: %s，回退到关键词匹配", str(e))
        return await detect_intent_with_keywords(query)


async def detect_intent_with_keywords(query: str) -> str:
    """使用关键词进行意图识别（快速路径/回退方案）"""
    for kw in _HYBRID_KW:
        if kw in query:
            return "hybrid"
    for kw in _MEMORY_KW:
        if kw in query:
            return "memory"
    
    # guide 意图通过 GuideAgent 的 triggers 匹配，这里不做判断
    return "qa"


async def detect_intent(query: str, history: list = None, use_llm: bool = True) -> str:
    """
    检测用户意图
    
    Args:
        query: 用户查询
        history: 历史对话记录
        use_llm: 是否使用 LLM 进行意图识别（默认 True）
    
    Returns:
        意图类型: guide, memory, hybrid, qa
    """
    if use_llm:
        return await detect_intent_with_llm(query, history)
    else:
        return await detect_intent_with_keywords(query)


class OrchestratorAgent(BaseAgent):

    @property
    def agent_id(self) -> str:
        return "orchestrator_agent"

    @property
    def name(self) -> str:
        return "编排路由Agent"

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        from app.agents.base import agent_engine
        from app.agents.config_loader import agent_config

        query: str = input_data.get("query", "")
        session_id: str = input_data.get("session_id", "")
        history: list = input_data.get("history", [])

        # 根据配置选择意图识别方法
        use_llm = agent_config.get_intent_detection_method() == "llm"
        intent = await detect_intent(query, history=history, use_llm=use_llm)
        logger.info("OrchestratorAgent 意图: '%s' -> %s (method=%s)", 
                   query[:40], intent, "llm" if use_llm else "keyword")

        # 假期余额查询意图
        if intent == "leave_balance":
            logger.info("🎯 [LEAVE_BALANCE] 路由到 LeaveBalanceTool | query='%s'", query)
            from app.services.tool_executor import ToolExecutor
            
            # 从查询中提取假期类型
            leave_type = self._extract_leave_type(query)
            if leave_type:
                logger.info("🔍 [LEAVE_BALANCE] 识别到假期类型: %s", leave_type)
            
            tool_executor = ToolExecutor()
            result = await tool_executor.execute_tool(
                "check_leave_balance",
                {"leave_type": leave_type} if leave_type else {},
                auth_context=input_data.get("auth_context")
            )
            result["intent"] = "leave_balance"
            return result

        if intent == "guide":
            logger.info("🎯 [GUIDE] 路由到 GuideAgent | query='%s'", query)
            result = await agent_engine.execute(
                "guide_agent",
                {"query": query, "session_id": session_id, "history": history},
            )
            # 确保 intent 字段存在
            if "intent" not in result:
                result["intent"] = "guide"
            return result

        if intent == "memory":
            result = await agent_engine.execute(
                "memory_agent",
                {"query": query, "session_id": session_id},
            )
            result["intent"] = "memory"
            return result

        if intent == "hybrid":
            qa_task = agent_engine.execute(
                "qa_agent", {"query": query, "history": history, "session_id": session_id}
            )
            memory_task = agent_engine.execute(
                "memory_agent", {"query": query, "session_id": session_id}
            )
            qa_result, memory_result = await asyncio.gather(qa_task, memory_task)
            return {
                "intent": "hybrid",
                "qa": qa_result,
                "memories": memory_result.get("memories", []),
            }

        # 默认 qa
        result = await agent_engine.execute(
            "qa_agent",
            {"query": query, "question": query, "history": history, "session_id": session_id},
        )
        # 确保 intent 字段存在
        if "intent" not in result:
            result["intent"] = "qa"
        return result
    
    def _extract_leave_type(self, query: str) -> str:
        """从查询中提取假期类型"""
        # 定义假期类型关键词映射
        leave_type_keywords = {
            "年假": ["年假", "年休假", "带薪年假"],
            "病假": ["病假"],
            "事假": ["事假"],
            "婚假": ["婚假", "结婚假"],
            "产假": ["产假", "生育假"],
            "陪产假": ["陪产假", "护理假", "陪护假"],
            "高温假": ["高温假", "防暑降温假"]
        }
        
        # 检查查询中是否包含假期类型关键词
        for leave_type, keywords in leave_type_keywords.items():
            for keyword in keywords:
                if keyword in query:
                    return leave_type
        
        return None
