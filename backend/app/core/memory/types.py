"""
记忆系统类型定义
"""
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import math


class MemoryType(str, Enum):
    """记忆类型"""
    WORKING = "working"        # 工作记忆：当前对话上下文
    TEMPORARY = "temporary"    # 临时记忆：用户标记的重要信息
    SHORT_TERM = "short_term"  # 短期记忆：最近的对话历史
    LONG_TERM = "long_term"    # 长期记忆：压缩的历史摘要
    PERMANENT = "permanent"    # 永久记忆：用户保存的知识


class MemorySource(str, Enum):
    """记忆来源"""
    USER_MARKED = "user_marked"      # 用户手动标记
    AUTO_GENERATED = "auto_generated"  # 系统自动生成
    IMPORTED = "imported"            # 外部导入
    CONVERSATION = "conversation"    # 对话生成


@dataclass
class MemoryMetadata:
    """记忆元数据"""
    title: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    source: MemorySource = MemorySource.AUTO_GENERATED
    importance: float = 0.5  # 重要性评分 0-1
    confidence: float = 1.0  # 置信度 0-1
    related_memories: List[str] = field(default_factory=list)  # 关联记忆ID
    custom_fields: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Memory:
    """记忆对象"""
    id: str
    user_id: str
    session_id: str
    memory_type: MemoryType
    content: str
    metadata: MemoryMetadata
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    weight: float = 0.5
    is_active: bool = True
    vector_id: Optional[str] = None
    
    def calculate_weight(self) -> float:
        """
        计算记忆权重
        
        权重计算考虑因素：
        1. 基础权重（根据记忆类型）
        2. 时间衰减（除永久记忆和工作记忆外）
        3. 访问频率加成
        4. 重要性评分
        """
        # 基础权重
        base_weights = {
            MemoryType.WORKING: 1.0,
            MemoryType.TEMPORARY: 0.85,
            MemoryType.SHORT_TERM: 0.6,
            MemoryType.LONG_TERM: 0.2,
            MemoryType.PERMANENT: 0.5
        }
        base_weight = base_weights.get(self.memory_type, 0.5)
        
        # 永久记忆和工作记忆不衰减
        if self.memory_type in [MemoryType.PERMANENT, MemoryType.WORKING]:
            return base_weight * self.metadata.importance
        
        # 时间衰减（指数衰减）
        days_old = (datetime.utcnow() - self.created_at).days
        
        # 不同记忆类型的衰减速度不同
        decay_rates = {
            MemoryType.TEMPORARY: 7,    # 7天半衰期
            MemoryType.SHORT_TERM: 30,  # 30天半衰期
            MemoryType.LONG_TERM: 90    # 90天半衰期
        }
        decay_rate = decay_rates.get(self.memory_type, 30)
        time_decay = math.exp(-days_old / decay_rate)
        
        # 访问频率加成（最多+0.15）
        access_boost = min(0.15, self.access_count * 0.01)
        
        # 重要性加成
        importance_factor = self.metadata.importance
        
        # 最终权重
        final_weight = (base_weight * time_decay * importance_factor) + access_boost
        
        # 限制在 0.05-1.0 范围内
        return max(0.05, min(1.0, final_weight))
    
    def is_expired(self) -> bool:
        """检查记忆是否过期"""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
    
    def should_archive(self) -> bool:
        """判断是否应该归档（转为长期记忆）"""
        if self.memory_type != MemoryType.SHORT_TERM:
            return False
        
        # 超过30天且访问次数少于5次
        days_old = (datetime.utcnow() - self.created_at).days
        return days_old > 30 and self.access_count < 5
    
    def should_delete(self) -> bool:
        """判断是否应该删除"""
        # 已过期
        if self.is_expired():
            return True
        
        # 长期记忆超过1年且权重很低
        if self.memory_type == MemoryType.LONG_TERM:
            days_old = (datetime.utcnow() - self.created_at).days
            return days_old > 365 and self.weight < 0.1
        
        return False
    
    def increment_access(self):
        """增加访问计数"""
        self.access_count += 1
        self.last_accessed = datetime.utcnow()
        self.weight = self.calculate_weight()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "memory_type": self.memory_type.value,
            "content": self.content,
            "metadata": {
                "title": self.metadata.title,
                "tags": self.metadata.tags,
                "source": self.metadata.source.value,
                "importance": self.metadata.importance,
                "confidence": self.metadata.confidence,
                "related_memories": self.metadata.related_memories,
                "custom_fields": self.metadata.custom_fields
            },
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "expires_at": self.expires_at,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed,
            "weight": self.weight,
            "is_active": self.is_active,
            "vector_id": self.vector_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Memory":
        """从字典创建"""
        metadata_dict = data.get("metadata", {})
        metadata = MemoryMetadata(
            title=metadata_dict.get("title"),
            tags=metadata_dict.get("tags", []),
            source=MemorySource(metadata_dict.get("source", "auto_generated")),
            importance=metadata_dict.get("importance", 0.5),
            confidence=metadata_dict.get("confidence", 1.0),
            related_memories=metadata_dict.get("related_memories", []),
            custom_fields=metadata_dict.get("custom_fields", {})
        )
        
        return cls(
            id=data["id"],
            user_id=data["user_id"],
            session_id=data["session_id"],
            memory_type=MemoryType(data["memory_type"]),
            content=data["content"],
            metadata=metadata,
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            expires_at=data.get("expires_at"),
            access_count=data.get("access_count", 0),
            last_accessed=data.get("last_accessed"),
            weight=data.get("weight", 0.5),
            is_active=data.get("is_active", True),
            vector_id=data.get("vector_id")
        )


@dataclass
class MemoryQuery:
    """记忆查询参数"""
    query_text: str
    user_id: str
    session_id: Optional[str] = None
    memory_types: Optional[List[MemoryType]] = None
    tags: Optional[List[str]] = None
    min_weight: float = 0.1
    max_age_days: Optional[int] = None
    top_k: int = 10
    include_inactive: bool = False
