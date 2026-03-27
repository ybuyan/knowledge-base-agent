"""
增强记忆系统测试
"""
import pytest
import asyncio
from datetime import datetime, timedelta

from app.core.memory import (
    get_enhanced_memory_manager,
    MemoryType,
    MemoryMetadata,
    MemorySource,
    MemoryQuery,
    Memory
)


@pytest.fixture
async def manager():
    """获取记忆管理器实例"""
    return get_enhanced_memory_manager()


@pytest.fixture
def user_id():
    return "test_user_123"


@pytest.fixture
def session_id():
    return "test_session_456"


class TestMemoryCreation:
    """测试记忆创建"""
    
    @pytest.mark.asyncio
    async def test_create_working_memory(self, manager, user_id, session_id):
        """测试创建工作记忆"""
        memory = await manager.create_memory(
            user_id=user_id,
            session_id=session_id,
            content="这是一条工作记忆",
            memory_type=MemoryType.WORKING
        )
        
        assert memory is not None
        assert memory.memory_type == MemoryType.WORKING
        assert memory.weight == 1.0  # 工作记忆权重最高
        assert memory.is_active is True
    
    @pytest.mark.asyncio
    async def test_create_temporary_memory(self, manager, user_id, session_id):
        """测试创建临时记忆"""
        memory = await manager.create_memory(
            user_id=user_id,
            session_id=session_id,
            content="这是一条临时记忆",
            memory_type=MemoryType.TEMPORARY,
            expires_in_days=7
        )
        
        assert memory is not None
        assert memory.memory_type == MemoryType.TEMPORARY
        assert memory.expires_at is not None
        assert memory.weight > 0.8  # 临时记忆高权重
    
    @pytest.mark.asyncio
    async def test_create_permanent_memory(self, manager, user_id, session_id):
        """测试创建永久记忆"""
        metadata = MemoryMetadata(
            title="重要知识",
            tags=["知识库", "重要"],
            importance=1.0
        )
        
        memory = await manager.create_memory(
            user_id=user_id,
            session_id=session_id,
            content="这是一条永久记忆",
            memory_type=MemoryType.PERMANENT,
            metadata=metadata
        )
        
        assert memory is not None
        assert memory.memory_type == MemoryType.PERMANENT
        assert memory.expires_at is None  # 永久记忆不过期
        assert memory.metadata.title == "重要知识"


class TestWeightCalculation:
    """测试权重计算"""
    
    @pytest.mark.asyncio
    async def test_working_memory_weight(self, manager, user_id, session_id):
        """测试工作记忆权重"""
        memory = await manager.create_memory(
            user_id=user_id,
            session_id=session_id,
            content="工作记忆",
            memory_type=MemoryType.WORKING,
            metadata=MemoryMetadata(importance=0.5)
        )
        
        # 工作记忆权重 = 1.0 × importance
        assert memory.weight == 0.5
    
    @pytest.mark.asyncio
    async def test_importance_impact(self, manager, user_id, session_id):
        """测试重要性对权重的影响"""
        memory_low = await manager.create_memory(
            user_id=user_id,
            session_id=session_id,
            content="低重要性",
            memory_type=MemoryType.SHORT_TERM,
            metadata=MemoryMetadata(importance=0.3)
        )
        
        memory_high = await manager.create_memory(
            user_id=user_id,
            session_id=session_id + "_2",
            content="高重要性",
            memory_type=MemoryType.SHORT_TERM,
            metadata=MemoryMetadata(importance=0.9)
        )
        
        assert memory_high.weight > memory_low.weight
    
    def test_weight_recalculation(self):
        """测试权重重新计算"""
        memory = Memory(
            id="test_id",
            user_id="user",
            session_id="session",
            memory_type=MemoryType.SHORT_TERM,
            content="测试",
            metadata=MemoryMetadata(importance=0.5),
            created_at=datetime.utcnow() - timedelta(days=15),
            updated_at=datetime.utcnow(),
            access_count=5
        )
        
        weight = memory.calculate_weight()
        
        # 权重应该考虑时间衰减和访问次数
        assert 0.1 < weight < 0.7


class TestMemoryRetrieval:
    """测试记忆检索"""
    
    @pytest.mark.asyncio
    async def test_retrieve_by_query(self, manager, user_id, session_id):
        """测试按查询检索"""
        # 创建几条记忆
        await manager.create_memory(
            user_id=user_id,
            session_id=session_id,
            content="Python编程语言",
            memory_type=MemoryType.SHORT_TERM
        )
        
        await manager.create_memory(
            user_id=user_id,
            session_id=session_id,
            content="JavaScript前端开发",
            memory_type=MemoryType.SHORT_TERM
        )
        
        # 检索
        query = MemoryQuery(
            query_text="编程",
            user_id=user_id,
            top_k=5
        )
        
        memories = await manager.retrieve_memories(query)
        
        assert len(memories) > 0
        # 应该检索到包含"编程"的记忆
    
    @pytest.mark.asyncio
    async def test_filter_by_type(self, manager, user_id, session_id):
        """测试按类型过滤"""
        await manager.create_memory(
            user_id=user_id,
            session_id=session_id,
            content="临时信息",
            memory_type=MemoryType.TEMPORARY,
            expires_in_days=7
        )
        
        await manager.create_memory(
            user_id=user_id,
            session_id=session_id,
            content="永久信息",
            memory_type=MemoryType.PERMANENT
        )
        
        # 只检索临时记忆
        query = MemoryQuery(
            query_text="信息",
            user_id=user_id,
            memory_types=[MemoryType.TEMPORARY],
            top_k=10
        )
        
        memories = await manager.retrieve_memories(query)
        
        for memory in memories:
            assert memory.memory_type == MemoryType.TEMPORARY


class TestMemoryLifecycle:
    """测试记忆生命周期"""
    
    @pytest.mark.asyncio
    async def test_mark_as_temporary(self, manager, user_id, session_id):
        """测试标记为临时记忆"""
        memory = await manager.create_memory(
            user_id=user_id,
            session_id=session_id,
            content="普通记忆",
            memory_type=MemoryType.SHORT_TERM
        )
        
        # 标记为临时记忆
        success = await manager.mark_as_temporary(
            memory_id=memory.id,
            user_id=user_id,
            expires_in_days=7,
            importance=0.9
        )
        
        assert success is True
        
        # 验证转换
        updated = await manager.get_memory(memory.id, user_id)
        assert updated.memory_type == MemoryType.TEMPORARY
        assert updated.expires_at is not None
    
    @pytest.mark.asyncio
    async def test_save_as_permanent(self, manager, user_id, session_id):
        """测试保存为永久记忆"""
        memory = await manager.create_memory(
            user_id=user_id,
            session_id=session_id,
            content="重要信息",
            memory_type=MemoryType.SHORT_TERM
        )
        
        # 保存为永久记忆
        success = await manager.save_as_permanent(
            memory_id=memory.id,
            user_id=user_id,
            title="重要知识",
            tags=["知识库"]
        )
        
        assert success is True
        
        # 验证转换
        updated = await manager.get_memory(memory.id, user_id)
        assert updated.memory_type == MemoryType.PERMANENT
        assert updated.metadata.title == "重要知识"
        assert "知识库" in updated.metadata.tags
    
    @pytest.mark.asyncio
    async def test_convert_working_to_short_term(self, manager, user_id, session_id):
        """测试工作记忆转短期记忆"""
        # 创建工作记忆
        await manager.create_memory(
            user_id=user_id,
            session_id=session_id,
            content="工作记忆1",
            memory_type=MemoryType.WORKING
        )
        
        await manager.create_memory(
            user_id=user_id,
            session_id=session_id,
            content="工作记忆2",
            memory_type=MemoryType.WORKING
        )
        
        # 转换
        await manager.convert_working_to_short_term(session_id, user_id)
        
        # 验证工作记忆已清空
        # （实际测试需要检查数据库）


class TestMemoryExpiration:
    """测试记忆过期"""
    
    def test_is_expired(self):
        """测试过期检查"""
        # 未过期
        memory = Memory(
            id="test",
            user_id="user",
            session_id="session",
            memory_type=MemoryType.TEMPORARY,
            content="测试",
            metadata=MemoryMetadata(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        assert memory.is_expired() is False
        
        # 已过期
        memory.expires_at = datetime.utcnow() - timedelta(days=1)
        assert memory.is_expired() is True
    
    def test_should_archive(self):
        """测试是否应该归档"""
        memory = Memory(
            id="test",
            user_id="user",
            session_id="session",
            memory_type=MemoryType.SHORT_TERM,
            content="测试",
            metadata=MemoryMetadata(),
            created_at=datetime.utcnow() - timedelta(days=35),
            updated_at=datetime.utcnow(),
            access_count=3
        )
        
        # 超过30天且访问次数少，应该归档
        assert memory.should_archive() is True
        
        # 访问次数多，不应该归档
        memory.access_count = 10
        assert memory.should_archive() is False


class TestMemoryUpdate:
    """测试记忆更新"""
    
    @pytest.mark.asyncio
    async def test_update_content(self, manager, user_id, session_id):
        """测试更新内容"""
        memory = await manager.create_memory(
            user_id=user_id,
            session_id=session_id,
            content="原始内容",
            memory_type=MemoryType.SHORT_TERM
        )
        
        # 更新
        success = await manager.update_memory(
            memory_id=memory.id,
            user_id=user_id,
            content="更新后的内容"
        )
        
        assert success is True
        
        # 验证
        updated = await manager.get_memory(memory.id, user_id)
        assert updated.content == "更新后的内容"
    
    @pytest.mark.asyncio
    async def test_update_metadata(self, manager, user_id, session_id):
        """测试更新元数据"""
        memory = await manager.create_memory(
            user_id=user_id,
            session_id=session_id,
            content="测试",
            memory_type=MemoryType.SHORT_TERM,
            metadata=MemoryMetadata(title="原标题")
        )
        
        # 更新元数据
        new_metadata = MemoryMetadata(
            title="新标题",
            tags=["新标签"],
            importance=0.9
        )
        
        success = await manager.update_memory(
            memory_id=memory.id,
            user_id=user_id,
            metadata=new_metadata
        )
        
        assert success is True


class TestMemoryDeletion:
    """测试记忆删除"""
    
    @pytest.mark.asyncio
    async def test_delete_memory(self, manager, user_id, session_id):
        """测试删除记忆"""
        memory = await manager.create_memory(
            user_id=user_id,
            session_id=session_id,
            content="待删除",
            memory_type=MemoryType.SHORT_TERM
        )
        
        # 删除
        success = await manager.delete_memory(memory.id, user_id)
        assert success is True
        
        # 验证已删除
        deleted = await manager.get_memory(memory.id, user_id)
        assert deleted is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
