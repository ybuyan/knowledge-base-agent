"""
OrchestratorAgent — LLM 意图路由 Agent

意图分类结果：
  qa                    知识查询
  memory                历史记忆检索
  hybrid                混合（知识 + 记忆）
  process:<skill_id>    明确要办理某个流程
  confirm:<skill_id>    疑似要办理，需二次确认

process 路由到 ProcessAgent，confirm 返回确认提示，其余走原有逻辑。
"""
import asyncio
import logging
from typing import Any, Dict, List, Tuple

from app.agents.base import BaseAgent
from app.core.llm import call_llm

logger = logging.getLogger(__name__)

_MEMORY_KW: List[str] = ["上次", "之前", "刚才", "你说过", "我问过", "刚刚说", "前面提到"]
_HYBRID_KW: List[str] = ["对比", "不同", "区别", "和之前", "和上次", "比较"]

# 强意图词：包含这些词时才直接启动流程，否则走 confirm
_PROCESS_STRONG_KW: List[str] = ["申请", "办理", "发起", "提交", "帮我", "我要", "我想要", "我需要办"]


def _build_intent_prompt(process_skills: List[Dict]) -> str:
    """动态构建意图分类 prompt，包含当前可用的流程列表"""
    skill_lines = "\n".join(
        f"  - {s['id']}：{s['description']}"
        for s in process_skills
    ) or "  （暂无可用流程）"

    return f"""你是一个意图分类器。请将用户的问题分类为以下类型之一：

- qa：用户想查询信息、了解规定或政策。例如："年假有多少天""请假需要什么材料""我的请假状态"
- memory：用户引用了之前的对话内容。例如："你刚才说的""上次提到的"
- hybrid：同时需要知识库和历史对话
- process:<流程ID>：用户明确要发起、申请或办理某项业务。例如："我要请假""帮我申请年假""发起请假申请"
- confirm:<流程ID>：用户的意图模糊，可能是要办理也可能是查询，需要二次确认

当前可用流程：
{skill_lines}

判断规则：
1. 用户说"查""看""了解""是什么""有哪些""状态""材料""规定"等 → qa
2. 用户说"申请""办理""发起""我要""帮我""提交" + 具体业务 → process:<流程ID>
3. 用户只说了业务名称但意图不明确（如"请假"）→ confirm:<流程ID>
4. 无匹配流程时 → qa

只输出一个分类结果，不要输出其他内容。示例输出：
qa
process:leave_apply
confirm:leave_apply"""


async def _llm_classify(query: str, process_skills: List[Dict]) -> str:
    try:
        system = _build_intent_prompt(process_skills)
        result = await call_llm(query, system)
        intent = result.strip().lower()
        if intent in ("qa", "memory", "hybrid"):
            return intent
        if intent.startswith("process:") or intent.startswith("confirm:"):
            # 额外保护：LLM 返回 process 时，若不含强意图词则降级为 confirm
            if intent.startswith("process:"):
                skill_id = intent.split(":", 1)[1]
                has_strong = any(kw in query for kw in _PROCESS_STRONG_KW)
                if not has_strong:
                    return f"confirm:{skill_id}"
            return intent
    except Exception as e:
        logger.warning("LLM 意图分类失败，降级为 qa: %s", e)
    return "qa"


def _get_process_skills() -> List[Dict]:
    """获取所有已启用的 process 类型 skill 摘要"""
    try:
        from app.skills.engine import SkillEngine
        engine = SkillEngine()
        return [
            {"id": s["id"], "description": s["description"]}
            for s in engine.list_skills()
            if engine.skill_loader._cache.get(s["id"]) and
               engine.skill_loader._cache[s["id"]].frontmatter.get("skill_type") == "process"
        ]
    except Exception:
        return []


async def detect_intent(query: str) -> str:
    for kw in _HYBRID_KW:
        if kw in query:
            return "hybrid"
    for kw in _MEMORY_KW:
        if kw in query:
            return "memory"
    process_skills = _get_process_skills()
    return await _llm_classify(query, process_skills)


class OrchestratorAgent(BaseAgent):

    @property
    def agent_id(self) -> str:
        return "orchestrator_agent"

    @property
    def name(self) -> str:
        return "编排路由Agent"

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        from app.agents.base import agent_engine

        query: str = input_data.get("query", "")
        session_id: str = input_data.get("session_id", "")
        history: list = input_data.get("history", [])
        process_action: str = input_data.get("process_action", "next")
        process_input: Dict = input_data.get("process_input", {})
        flow_id: str = input_data.get("flow_id", "")
        username: str = input_data.get("username", "")

        # 已有进行中的流程，直接路由
        if flow_id:
            return await agent_engine.execute("process_agent", {
                "query": query,
                "session_id": session_id,
                "process_action": process_action,
                "process_input": process_input,
                "flow_id": flow_id,
                "username": username,
            })

        intent = await detect_intent(query)
        logger.info("OrchestratorAgent 意图: '%s' -> %s", query[:40], intent)

        # process:<skill_id> — 直接启动流程
        if intent.startswith("process:"):
            skill_id = intent.split(":", 1)[1]
            return await agent_engine.execute("process_agent", {
                "query": query,
                "session_id": session_id,
                "process_action": "next",
                "process_input": {},
                "flow_id": skill_id,
                "username": username,
            })

        # confirm:<skill_id> — 返回确认提示，不启动流程
        if intent.startswith("confirm:"):
            skill_id = intent.split(":", 1)[1]
            process_skills = _get_process_skills()
            skill_name = next(
                (s["description"] for s in process_skills if s["id"] == skill_id),
                skill_id
            )
            return {
                "answer": f"您是想发起「{skill_name}」吗？\n\n如果是，请回复「是的，帮我申请」；如果只是查询相关信息，请继续描述您的问题。",
                "ui_components": None,
                "intent": "confirm",
                "confirm_skill_id": skill_id,
            }

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
        return await agent_engine.execute(
            "qa_agent",
            {"query": query, "question": query, "history": history, "session_id": session_id},
        )
