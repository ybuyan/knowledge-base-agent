"""
ProcessExecutor — 流程执行引擎 Processor

从 SKILL.md 的 nodes 定义中读取当前步骤，
调用对应 Tool，维护 process_context，
返回结构化 ui_components 供前端渲染流程卡片。
"""
import logging
from typing import Any, Dict

from app.skills.base import BaseProcessor, ProcessorRegistry
from app.tools.base import ToolRegistry
from app.core.process_context import (
    get_process_context,
    save_process_context,
    clear_process_context,
)

logger = logging.getLogger(__name__)


@ProcessorRegistry.register("ProcessExecutor")
class ProcessExecutor(BaseProcessor):

    @property
    def name(self) -> str:
        return "ProcessExecutor"

    async def process(self, context: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        session_id: str = context.get("session_id", "")
        action: str = context.get("process_action", "next")   # next/prev/restart/cancel/input
        user_input: Dict = context.get("process_input", {})
        skill: Dict = context.get("_skill", {})

        nodes: list = skill.get("nodes", [])
        flow_name: str = skill.get("display_name", skill.get("name", "流程"))

        if not nodes:
            return {"answer": "流程配置为空，请联系管理员。", "ui_components": None}

        # ── 加载或初始化上下文 ──────────────────────────────
        ctx = await get_process_context(session_id) or {}

        # 当前流程 ID 不匹配时重置（用户切换了流程）
        if ctx.get("flow_id") != skill.get("name"):
            ctx = {}

        current_step: int = ctx.get("current_step", 0)
        collected: Dict = ctx.get("collected_data", {})

        # ── 处理操作指令 ────────────────────────────────────
        if action == "cancel":
            await clear_process_context(session_id)
            return {
                "answer": "流程已取消，如需重新办理请再次提问。",
                "ui_components": {"type": "process_cancelled"},
                "process_state": None,
            }

        if action == "restart":
            current_step = 0
            collected = {}

        if action == "prev" and current_step > 0:
            current_step -= 1

        # ── 执行当前节点 ────────────────────────────────────
        node = nodes[current_step]
        node_type: str = node.get("type", "text_info")
        tool_id: str = node.get("tool", node_type)

        result = {}
        try:
            tool = ToolRegistry.get(tool_id)
            tool_params = dict(node.get("params", {}))

            if node_type == "info_collect":
                # 合并用户输入
                if user_input:
                    collected.update(user_input)
                tool_params["user_input"] = {k: collected.get(k) for k in [f["key"] for f in tool_params.get("fields", [])]}
                result = await tool.execute(**tool_params)
                if not result.get("success") and action == "next":
                    return self._build_response(
                        flow_name, nodes, current_step, collected,
                        error=result.get("errors", []),
                        session_id=session_id, skill=skill,
                    )
                if result.get("success"):
                    collected.update(result.get("collected", {}))

            elif node_type == "process_submit":
                tool_params["flow_name"] = flow_name
                tool_params["collected_data"] = collected
                result = await tool.execute(**tool_params)

            elif node_type == "balance_check":
                # username 优先从 collected 取（fetch_user_info 已写入），其次从 context
                tool_params["username"] = collected.get("username") or context.get("username", "")
                tool_params["leave_type"] = collected.get("leave_type", "")
                tool_params["start_date"] = collected.get("start_date", "")
                tool_params["end_date"] = collected.get("end_date", "")
                result = await tool.execute(**tool_params)
                if not result.get("success"):
                    await save_process_context(session_id, {
                        "flow_id": skill.get("name"),
                        "current_step": current_step,
                        "collected_data": collected,
                    })
                    return self._build_response(
                        flow_name, nodes, current_step, collected,
                        error=result.get("errors", []),
                        session_id=session_id, skill=skill,
                    )
                # 余额充足，写入信息供后续步骤展示
                collected["balance_info"] = result.get("balance_info", "")
                collected["requested_days"] = result.get("requested_days", 0)

            elif node_type == "fetch_user_info":
                username = context.get("username") or collected.get("username", "")
                if not username:
                    return self._build_response(
                        flow_name, nodes, current_step, collected,
                        error=["未获取到用户登录信息，请先登录系统"],
                        session_id=session_id, skill=skill,
                    )
                wanted = node.get("params", {}).get("fields")
                result = await tool.execute(username=username, fields=wanted)
                if not result.get("success"):
                    return self._build_response(
                        flow_name, nodes, current_step, collected,
                        error=result.get("errors", []),
                        session_id=session_id, skill=skill,
                    )
                collected.update(result.get("user_info", {}))

            else:
                result = await tool.execute(**tool_params)

        except Exception as e:
            logger.error("ProcessExecutor tool error: %s", e)
            result = {"success": False, "errors": [str(e)]}

        # ── 判断是否进入下一步 ──────────────────────────────
        is_last = current_step >= len(nodes) - 1
        advance = action in ("next", "restart") and result.get("success", True)

        if advance and not is_last:
            current_step += 1
        elif advance and is_last:
            # 流程完成
            await clear_process_context(session_id)
            finish_msg = result.get("message", f"「{flow_name}」已完成。")
            return {
                "answer": finish_msg,
                "ui_components": {
                    "type": "process_done",
                    "message": finish_msg,
                    "ticket_id": result.get("ticket_id"),
                },
                "process_state": None,
            }

        # ── 保存上下文 ──────────────────────────────────────
        await save_process_context(session_id, {
            "flow_id": skill.get("name"),
            "current_step": current_step,
            "collected_data": collected,
        })

        return self._build_response(flow_name, nodes, current_step, collected, session_id=session_id, skill=skill)

    # ── 辅助方法 ────────────────────────────────────────────

    def _build_response(
        self,
        flow_name: str,
        nodes: list,
        current_step: int,
        collected: Dict,
        error: list = None,
        session_id: str = "",
        skill: Dict = None,
    ) -> Dict[str, Any]:
        node = nodes[current_step]
        total = len(nodes)
        skill = skill or {}

        ui = {
            "type": "process_card",
            "flow_name": flow_name,
            "flow_id": skill.get("id", ""),
            "current_step": current_step,
            "total_steps": total,
            "node": {
                "id": node.get("id"),
                "title": node.get("title", f"步骤 {current_step + 1}"),
                "type": node.get("type", "text_info"),
                "content": node.get("content", ""),
                "fields": node.get("params", {}).get("fields", []),
                "auto_next": node.get("type") in ("fetch_user_info", "balance_check", "text_info"),
            },
            "collected_data": collected,
            "errors": error or [],
            "can_prev": current_step > 0,
            "can_next": True,
            "steps_overview": [
                {
                    "index": i,
                    "title": n.get("title", f"步骤 {i + 1}"),
                    "status": "done" if i < current_step else ("current" if i == current_step else "pending"),
                }
                for i, n in enumerate(nodes)
            ],
        }

        answer = f"**{flow_name}** — 步骤 {current_step + 1}/{total}：{node.get('title', '')}"
        if node.get("content"):
            answer += f"\n\n{node['content']}"

        return {
            "answer": answer,
            "ui_components": ui,
            "process_state": {
                "flow_id": flow_name,
                "current_step": current_step,
                "total_steps": total,
            },
        }
