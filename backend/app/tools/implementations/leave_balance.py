"""
Leave Balance Tool - 假期余额查询工具
"""

from app.tools.base import BaseTool, ToolRegistry, ToolDefinition
from app.models.leave_balance import LeaveBalance, LeaveType
from app.core.mongodb import get_mongo_db
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@ToolRegistry.register("check_leave_balance")
class LeaveBalanceTool(BaseTool):
    """假期余额查询工具"""

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            id="check_leave_balance",
            name="check_leave_balance",
            description="查询当前用户的假期余额。支持查询所有假期类型或指定类型的余额。",
            enabled=True,
            category="leave",
            parameters={
                "type": "object",
                "properties": {
                    "leave_type": {
                        "type": "string",
                        "description": "假期类型（可选）。如：年假、病假、事假、婚假、产假、陪产假、高温假。不指定则返回所有类型。",
                        "enum": ["年假", "病假", "事假", "婚假", "产假", "陪产假", "高温假"]
                    }
                },
                "required": []
            },
            implementation="LeaveBalanceTool"
        )

    async def execute(self, leave_type: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        执行余额查询

        Args:
            leave_type: 假期类型（可选）
            **kwargs: 包含 auth_context 等上下文信息

        Returns:
            {
                "success": bool,
                "balances": List[Dict],  # 余额列表
                "message": str,  # 格式化的文本消息
                "error": Optional[str]
            }
        """
        try:
            # 1. 权限验证
            auth_context = kwargs.get("auth_context")
            logger.info("[LeaveBalanceTool] 权限验证 auth_context：%s", auth_context)
            if not auth_context:
                return self._error_response("缺少认证上下文")

            user_id = auth_context.get("user_id")
            username = auth_context.get("username", "未知用户")
            role = auth_context.get("role", "guest")

            # 检查用户是否已登录
            if role == "guest" or not user_id:
                await self._log_audit(None, username, "check_leave_balance", leave_type, False, "未登录")
                return self._error_response("请先登录后查询假期余额")

            # 2. 查询数据库
            balances = await self._query_balances(user_id, username, leave_type)

            # 3. 检查数据是否存在
            if not balances:
                await self._log_audit(user_id, username, "check_leave_balance", leave_type, False, "数据不存在")
                return self._error_response("未找到假期余额数据，请联系 HR")

            # 4. 格式化输出
            message = self._format_balances(balances, username)

            # 5. 记录审计日志
            await self._log_audit(user_id, username, "check_leave_balance", leave_type, True, "查询成功")

            # 6. 返回结果
            return {
                "success": True,
                "balances": [b.to_dict() for b in balances],
                "message": message,
                "error": None,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"查询假期余额失败: {e}", exc_info=True)
            await self._log_audit(
                kwargs.get("auth_context", {}).get("user_id"),
                kwargs.get("auth_context", {}).get("username", "未知用户"),
                "check_leave_balance",
                leave_type,
                False,
                f"系统错误: {str(e)}"
            )
            return self._error_response("系统错误，请稍后重试")

    async def _query_balances(
        self,
        user_id: str,
        username: str,
        leave_type: Optional[str] = None
    ) -> List[LeaveBalance]:
        """查询余额数据"""
        try:
            db = get_mongo_db()
            collection = db["leave_balances"]

            # 构建查询条件
            current_year = datetime.now().year
            query = {
                "user_id": user_id,
                "year": current_year
            }

            # 如果指定了假期类型，添加到查询条件
            if leave_type:
                # 验证假期类型是否有效
                if leave_type not in LeaveType.all_types():
                    raise ValueError(f"不支持的假期类型: {leave_type}")
                query["leave_type"] = leave_type

            # 查询数据库
            cursor = collection.find(query)
            documents = await cursor.to_list(length=None)

            # 转换为 LeaveBalance 模型
            balances = []
            for doc in documents:
                balance = LeaveBalance(
                    user_id=doc["user_id"],
                    username=doc["username"],
                    leave_type=doc["leave_type"],
                    year=doc["year"],
                    total_quota=doc["total_quota"],
                    used_days=doc["used_days"],
                    remaining_days=doc["remaining_days"],
                    updated_at=doc.get("updated_at", datetime.utcnow()),
                    created_at=doc.get("created_at", datetime.utcnow())
                )
                balances.append(balance)

            return balances

        except ValueError as e:
            # 重新抛出验证错误
            raise
        except Exception as e:
            logger.error(f"数据库查询失败: {e}", exc_info=True)
            raise

    def _format_balances(self, balances: List[LeaveBalance], username: str) -> str:
        """格式化余额信息"""
        # 如果只有一种假期类型，使用简洁格式
        if len(balances) == 1:
            balance = balances[0]
            lines = [
                f"📊 {username} 的{balance.leave_type}余额",
                f"查询时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                ""
            ]

            if balance.is_unlimited:
                lines.append(f"• {balance.leave_type}：无限额（按需申请）")
            else:
                # 检查余额是否不足（剩余少于总额的20%）
                warning = ""
                if balance.remaining_days < balance.total_quota * 0.2:
                    warning = " ⚠️"

                lines.append(
                    f"• 总额度：{balance.total_quota} 天"
                )
                lines.append(
                    f"• 已使用：{balance.used_days} 天"
                )
                lines.append(
                    f"• 剩余：{balance.remaining_days} 天{warning}"
                )

            return "\n".join(lines)

        # 多种假期类型，使用完整格式
        lines = [
            f"📊 {username} 的假期余额",
            f"查询时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            ""
        ]

        # 按假期类型排序
        sorted_balances = sorted(balances, key=lambda b: b.leave_type)

        for balance in sorted_balances:
            if balance.is_unlimited:
                lines.append(f"• {balance.leave_type}：无限额（按需申请）")
            else:
                # 检查余额是否不足（剩余少于总额的20%）
                warning = ""
                if balance.remaining_days < balance.total_quota * 0.2:
                    warning = " ⚠️"

                lines.append(
                    f"• {balance.leave_type}：总额 {balance.total_quota} 天，"
                    f"已用 {balance.used_days} 天，"
                    f"剩余 {balance.remaining_days} 天{warning}"
                )

        return "\n".join(lines)

    def _error_response(self, error_message: str) -> Dict[str, Any]:
        """返回错误响应"""
        return {
            "success": False,
            "balances": [],
            "message": error_message,
            "error": error_message,
            "timestamp": datetime.utcnow().isoformat()
        }

    async def _log_audit(
        self,
        user_id: Optional[str],
        username: str,
        action: str,
        leave_type: Optional[str],
        success: bool,
        details: str
    ):
        """记录审计日志（简化版）"""
        try:
            # 简单记录到日志，不使用 AuditLogger（因为它需要 Request 对象）
            logger.info(
                f"[AUDIT] user={username} (id={user_id}) action={action} "
                f"resource={leave_type or 'all'} success={success} details={details}"
            )
        except Exception as e:
            logger.error(f"记录审计日志失败: {e}", exc_info=True)
