"""
通用流程节点 Tools

任何流程都可复用的基础节点类型：
- TextInfoTool     文字说明
- InfoCollectTool  信息收集与校验
- SubmitTool       提交并生成单号
"""
import uuid
from typing import Any, Dict

from app.tools.base import BaseTool, ToolDefinition, ToolRegistry


@ToolRegistry.register("text_info")
class TextInfoTool(BaseTool):
    """文字说明节点：展示说明文案，自动进入下一步"""

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            id="text_info",
            name="text_info",
            description="展示流程步骤说明文案",
            category="process",
            parameters={
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "说明文案"},
                },
                "required": ["content"],
            },
            implementation="TextInfoTool",
        )

    async def execute(self, content: str, **kwargs) -> Dict[str, Any]:
        return {"success": True, "display": content, "auto_next": True}


@ToolRegistry.register("info_collect")
class InfoCollectTool(BaseTool):
    """信息收集节点：校验用户输入是否满足字段要求"""

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            id="info_collect",
            name="info_collect",
            description="收集并校验用户填写的信息",
            category="process",
            parameters={
                "type": "object",
                "properties": {
                    "fields": {
                        "type": "array",
                        "description": "字段定义列表",
                        "items": {
                            "type": "object",
                            "properties": {
                                "key": {"type": "string"},
                                "label": {"type": "string"},
                                "type": {"type": "string", "enum": ["text", "date", "select", "number"]},
                                "required": {"type": "boolean"},
                                "options": {"type": "array", "items": {"type": "string"}},
                            },
                        },
                    },
                    "user_input": {"type": "object", "description": "用户已填写的数据"},
                },
                "required": ["fields"],
            },
            implementation="InfoCollectTool",
        )

    async def execute(self, fields: list, user_input: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
        user_input = user_input or {}
        errors = [
            f"「{f['label']}」为必填项"
            for f in fields
            if f.get("required") and not user_input.get(f["key"])
        ]
        if errors:
            return {"success": False, "errors": errors}
        return {"success": True, "collected": user_input}


@ToolRegistry.register("process_submit")
class SubmitTool(BaseTool):
    """提交节点：汇总已收集数据，生成申请单号"""

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            id="process_submit",
            name="process_submit",
            description="提交流程数据并返回申请单号",
            category="process",
            parameters={
                "type": "object",
                "properties": {
                    "flow_name":      {"type": "string"},
                    "collected_data": {"type": "object"},
                },
                "required": ["flow_name", "collected_data"],
            },
            implementation="SubmitTool",
        )

    async def execute(self, flow_name: str, collected_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        ticket_id = f"REQ-{uuid.uuid4().hex[:8].upper()}"
        return {
            "success": True,
            "ticket_id": ticket_id,
            "message": f"「{flow_name}」已提交成功，申请单号：{ticket_id}，预计 1-3 个工作日审批完成。",
        }


@ToolRegistry.register("fetch_user_info")
class FetchUserInfoTool(BaseTool):
    """
    从 users 表查询当前登录用户信息，写入 collected_data。
    通用工具，任何需要用户基本信息的流程都可复用。
    查询字段：username / display_name / department / email / role
    """

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            id="fetch_user_info",
            name="fetch_user_info",
            description="从用户表查询当前登录用户信息，自动填充到流程上下文",
            category="process",
            parameters={
                "type": "object",
                "properties": {
                    "username": {"type": "string", "description": "登录用户名"},
                    "fields": {
                        "type": "array",
                        "description": "需要提取的字段列表，默认全部",
                        "items": {"type": "string"},
                    },
                },
                "required": ["username"],
            },
            implementation="FetchUserInfoTool",
        )

    async def execute(self, username: str, fields: list = None, **kwargs) -> Dict[str, Any]:
        from app.core.mongodb import get_mongo_db

        db = get_mongo_db()
        if db is None:
            return {"success": False, "errors": ["数据库不可用，无法获取用户信息"]}

        user = await db["users"].find_one(
            {"username": username},
            {"hashed_password": 0, "_id": 0},  # 不返回密码和 _id
        )
        if not user:
            return {"success": False, "errors": [f"未找到用户：{username}"]}

        # 按需提取字段
        allowed = {"username", "display_name", "department", "email", "role"}
        extract = set(fields) & allowed if fields else allowed
        user_info = {k: user.get(k, "") for k in extract}

        return {"success": True, "user_info": user_info, "collected": user_info}
