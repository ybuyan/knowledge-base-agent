"""
GuideAgent - 流程指引 Agent

数据驱动设计：流程定义存储在 MongoDB flow_guides 集合中，
通过 triggers 字段动态匹配，无需为每个流程编写独立 skill 代码。
"""
import logging
from typing import Dict, Any, Optional, AsyncGenerator
from app.agents.base import BaseAgent, agent_engine
from app.skills.engine import SkillEngine

logger = logging.getLogger(__name__)

GENERIC_GUIDE_SKILL = "flow_guide"  # 通用流程指引 skill


class GuideAgent(BaseAgent):

    @property
    def agent_id(self) -> str:
        return "guide_agent"

    @property
    def name(self) -> str:
        return "流程指引Agent"

    def __init__(self):
        self.skill_engine = SkillEngine()

    async def _match_flow_guide(self, query: str, session_id: str = "", history: list = None) -> Optional[Any]:
        """
        从数据库动态匹配流程指引。

        匹配策略：
        1. 先用当前 query 做关键词匹配（新流程优先）
        2. 当前 query 没命中，且 session 有锁定流程 → 沿用锁定（多轮对话连续性）
        3. 都没有 → 返回 None
        """
        logger.info("🔍 [GUIDE] 开始从 DB 匹配流程 | query='%s' | session_id='%s'", query, session_id)

        try:
            from app.services.flow_guide_repository import get_flow_guide_repository
            repo = get_flow_guide_repository()
            all_guides = await repo.get_all(status="active")
        except Exception as e:
            logger.error("[GUIDE] 获取流程列表失败: %s", e)
            return None

        # 1. 先用当前 query 匹配（只匹配 query，不搜历史）
        for guide in all_guides:
            triggers = guide.triggers or []
            if not triggers:
                name = guide.name
                triggers = [name]
                for suffix in ["流程", "申请流程", "审批流程", "办理流程"]:
                    core = name.replace(suffix, "").strip()
                    if core:
                        triggers.append(core)

            for trigger in triggers:
                if trigger and trigger in query:
                    logger.info("✅ [GUIDE] 匹配到流程 | guide='%s' | trigger='%s'", guide.name, trigger)
                    # 锁定（或切换）到新流程
                    if session_id:
                        from app.core.process_context import save_process_context
                        await save_process_context(session_id, {"guide_id": guide.id, "guide_name": guide.name})
                    return guide

        # 2. 当前 query 没命中，检查 session 是否有锁定流程
        if session_id:
            from app.core.process_context import get_process_context
            ctx = await get_process_context(session_id)
            locked_guide_id = ctx.get("guide_id") if ctx else None
            if locked_guide_id:
                try:
                    guide = await repo.get_by_id(locked_guide_id)
                    if guide and guide.status == "active":
                        logger.info("🔒 [GUIDE] 沿用已锁定流程 | guide='%s'", guide.name)
                        return guide
                except Exception as e:
                    logger.warning("[GUIDE] 获取锁定流程失败: %s", e)

        logger.warning("❌ [GUIDE] 未匹配到任何流程 | query='%s'", query)
        return None

    def _build_llm_context(self, matched_guide, query: str, session_id: str, history: list) -> Dict[str, Any]:
        """构建传给 LLMGenerator / stream_llm 的上下文和 prompt 变量"""
        steps_text = "\n".join(
            f"{s.sequence}. {s.title}：{s.description}"
            for s in matched_guide.steps
        )
        return {
            "query": query,
            "question": query,
            "session_id": session_id,
            "history": history,
            "flow_guide_name": matched_guide.name,
            "flow_guide_description": matched_guide.description,
            "flow_guide_steps": steps_text,
        }

    def _build_prompts(self, context: Dict[str, Any]):
        """从 config_loader 加载 flow_guide_generic prompt，填充变量，返回 (system, user)"""
        from app.core.config_loader import config_loader
        prompt_config = config_loader.get_prompt("flow_guide_generic")
        if not prompt_config:
            raise ValueError("Prompt template not found: flow_guide_generic")

        template = prompt_config["template"]
        system_tpl = template.get("system", "")
        user_tpl = template.get("user", "{question}")
        variables = prompt_config.get("variables", [])

        prompt_vars = {var: context.get(var, "") for var in variables}

        user_prompt = user_tpl.format(**prompt_vars) if user_tpl else context.get("question", "")
        system_prompt = system_tpl
        if system_prompt and prompt_vars:
            try:
                system_prompt = system_prompt.format(**prompt_vars)
            except (KeyError, ValueError):
                pass
        return system_prompt, user_prompt

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        query: str = input_data.get("query", "")
        session_id: str = input_data.get("session_id", "")
        history: list = input_data.get("history", [])

        logger.info("🚀 [GUIDE] GuideAgent 开始执行 | query='%s' | session_id='%s'", query, session_id)

        if not query:
            return {"answer": "请问您需要什么帮助？", "intent": "guide"}

        matched_guide = await self._match_flow_guide(query, session_id=session_id, history=history)

        if not matched_guide:
            logger.warning("⚠️  [GUIDE] 未找到匹配的流程，返回默认回复")
            return {
                "answer": "抱歉，我暂时无法提供该流程的指引。请联系管理员。",
                "intent": "guide",
            }

        logger.info("📋 [GUIDE] 准备执行通用 skill | guide='%s'", matched_guide.name)

        context = self._build_llm_context(matched_guide, query, session_id, history)
        # 补充 skill engine 需要的字段
        context["flow_guide"] = {
            "id": matched_guide.id,
            "name": matched_guide.name,
            "category": matched_guide.category,
            "description": matched_guide.description,
            "steps": [{"sequence": s.sequence, "title": s.title, "description": s.description}
                      for s in matched_guide.steps],
        }

        try:
            result = await self.skill_engine.execute(GENERIC_GUIDE_SKILL, context)
            answer = result.get("answer", "")

            logger.info("✅ [GUIDE] Skill 执行成功 | guide='%s' | answer_length=%d",
                        matched_guide.name, len(answer))

            if not answer or not answer.strip():
                logger.error("⚠️  [GUIDE] 返回的 answer 为空！| result=%s", result)

            return {
                "answer": answer,
                "session_id": session_id,
                "intent": "guide",
                "ui_components": {
                    "flow_guide_hint": {"id": matched_guide.id, "name": matched_guide.name}
                },
            }

        except Exception as e:
            logger.error("❌ [GUIDE] Skill 执行失败 | guide='%s' | error=%s", matched_guide.name, str(e))
            import traceback
            logger.error(traceback.format_exc())
            return {
                "answer": "抱歉，生成指引时出现错误。请稍后再试。",
                "session_id": session_id,
                "intent": "guide",
            }

    async def run_stream(self, input_data: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式版本：逐 token yield，最后 yield 包含 ui_components 的 done 事件。

        Yields:
            {"type": "text", "content": "..."}
            {"type": "done", "ui_components": {...}}
            {"type": "error", "content": "..."}  # 出错时
        """
        from app.core.llm import stream_llm

        query: str = input_data.get("query", "")
        session_id: str = input_data.get("session_id", "")
        history: list = input_data.get("history", [])

        if not query:
            yield {"type": "text", "content": "请问您需要什么帮助？"}
            yield {"type": "done"}
            return

        matched_guide = await self._match_flow_guide(query, session_id=session_id, history=history)

        if not matched_guide:
            yield {"type": "text", "content": "抱歉，我暂时无法提供该流程的指引。请联系管理员。"}
            yield {"type": "done"}
            return

        logger.info("🌊 [GUIDE] 流式执行 | guide='%s'", matched_guide.name)

        try:
            context = self._build_llm_context(matched_guide, query, session_id, history)
            system_prompt, user_prompt = self._build_prompts(context)

            async for chunk in stream_llm(user_prompt, system_prompt, history=history):
                yield {"type": "text", "content": chunk}

            yield {
                "type": "done",
                "ui_components": {
                    "flow_guide_hint": {"id": matched_guide.id, "name": matched_guide.name}
                },
            }

        except Exception as e:
            logger.error("❌ [GUIDE] 流式执行失败 | guide='%s' | error=%s", matched_guide.name, str(e))
            yield {"type": "error", "content": "抱歉，生成指引时出现错误。请稍后再试。"}


agent_engine.register(GuideAgent())
