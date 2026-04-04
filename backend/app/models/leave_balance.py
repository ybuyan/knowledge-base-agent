"""
假期余额数据模型
用于存储和管理用户的假期余额信息
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum


class LeaveType(str, Enum):
    """假期类型枚举"""
    ANNUAL = "年假"
    SICK = "病假"
    PERSONAL = "事假"
    MARRIAGE = "婚假"
    MATERNITY = "产假"
    PATERNITY = "陪产假"
    HIGH_TEMP = "高温假"
    
    @classmethod
    def is_unlimited(cls, leave_type: str) -> bool:
        """判断假期类型是否无限额"""
        unlimited_types = [cls.SICK.value, cls.PERSONAL.value]
        return leave_type in unlimited_types
    
    @classmethod
    def get_display_name(cls, leave_type: str) -> str:
        """获取显示名称"""
        return leave_type
    
    @classmethod
    def all_types(cls) -> List[str]:
        """获取所有假期类型"""
        return [t.value for t in cls]


class LeaveBalance(BaseModel):
    """假期余额数据模型"""
    user_id: str = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    leave_type: str = Field(..., description="假期类型")
    year: int = Field(..., description="年度")
    total_quota: float = Field(..., description="总额度（天），-1表示无限额")
    used_days: float = Field(default=0.0, description="已使用天数")
    remaining_days: float = Field(..., description="剩余天数，-1表示无限额")
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    @property
    def is_unlimited(self) -> bool:
        """是否无限额度"""
        return self.total_quota == -1
    
    def is_sufficient(self, requested_days: float) -> bool:
        """检查余额是否充足"""
        if self.is_unlimited:
            return True
        return self.remaining_days >= requested_days
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "leave_type": self.leave_type,
            "year": self.year,
            "total_quota": self.total_quota,
            "used_days": self.used_days,
            "remaining_days": self.remaining_days,
            "updated_at": self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at,
            "created_at": self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at
        }


class LeaveBalanceResponse(BaseModel):
    """假期余额查询响应"""
    success: bool = Field(..., description="是否成功")
    balances: List[LeaveBalance] = Field(default_factory=list, description="余额列表")
    message: str = Field(..., description="格式化的文本消息")
    error: Optional[str] = Field(None, description="错误信息")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="查询时间")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
