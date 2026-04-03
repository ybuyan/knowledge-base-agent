"""
请假流程专属 Tools

LeaveBalanceCheckTool: 校验假期余额是否足够
"""
from datetime import datetime
from typing import Any, Dict

from app.tools.base import BaseTool, ToolDefinition, ToolRegistry


@ToolRegistry.register("leave_balance_check")
class LeaveBalanceCheckTool(BaseTool):
    """假期余额校验：查询 MongoDB leave_balances，判断余额是否足够"""

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            id="leave_balance_check",
            name="leave_balance_check",
            description="校验用户假期余额是否足够",
            category="process",
            parameters={
                "type": "object",
                "properties": {
                    "username":   {"type": "string", "description": "用户名"},
                    "leave_type": {"type": "string", "description": "假期类型"},
                    "start_date": {"type": "string", "description": "开始日期 YYYY-MM-DD"},
                    "end_date":   {"type": "string", "description": "结束日期 YYYY-MM-DD"},
                },
                "required": ["username", "leave_type", "start_date", "end_date"],
            },
            implementation="LeaveBalanceCheckTool",
        )

    async def execute(self, username: str, leave_type: str, start_date: str, end_date: str, **kwargs) -> Dict[str, Any]:
        # 计算请假天数（含首尾）
        try:
            d1 = datetime.strptime(start_date, "%Y-%m-%d")
            d2 = datetime.strptime(end_date, "%Y-%m-%d")
            if d2 < d1:
                return {"success": False, "errors": ["结束日期不能早于开始日期"]}
            requested_days = (d2 - d1).days + 1
        except ValueError:
            return {"success": False, "errors": ["日期格式错误，请使用 YYYY-MM-DD"]}

        from app.core.mongodb import get_mongo_db
        db = get_mongo_db()
        if db is None:
            return {"success": True, "requested_days": requested_days, "balance_info": "余额查询不可用，已跳过校验"}

        doc = await db["leave_balances"].find_one({"username": username})
        if not doc:
            return {"success": True, "requested_days": requested_days, "balance_info": "未找到余额记录，已跳过校验"}

        balance = doc.get("balances", {}).get(leave_type)
        if not balance:
            return {"success": True, "requested_days": requested_days, "balance_info": f"未找到「{leave_type}」余额记录"}

        remaining = balance.get("remaining_days", 0)
        if requested_days > remaining:
            return {
                "success": False,
                "errors": [f"「{leave_type}」余额不足：申请 {requested_days} 天，剩余 {remaining} 天"],
            }

        return {
            "success": True,
            "requested_days": requested_days,
            "remaining_days": remaining,
            "balance_info": f"余额充足：申请 {requested_days} 天，剩余 {remaining} 天",
        }
