"""
增强记忆系统使用示例
"""
import asyncio
from datetime import datetime

from app.core.memory import (
    get_enhanced_memory_manager,
    MemoryType,
    MemoryMetadata,
    MemorySource,
    MemoryQuery
)


async def example_basic_usage():
    """基础使用示例"""
    manager = get_enhanced_memory_manager()
    user_id = "user_123"
    session_id = "session_456"
    
    print("=" * 60)
    print("1. 创建工作记忆（当前对话）")
    print("=" * 60)
    
    # 用户提问
    memory1 = await manager.create_memory(
        user_id=user_id,
        session_id=session_id,
        content="用户问：我们公司的年假政策是什么？",
        memory_type=MemoryType.WORKING
    )
    print(f"创建工作记忆: {memory1.id}, 权重: {memory1.weight}")
    
    # AI回答
    memory2 = await manager.create_memory(
        user_id=user_id,
        session_id=session_id,
        content="AI答：根据公司政策，员工每年享有10天带薪年假...",
        memory_type=MemoryType.WORKING
    )
    print(f"创建工作记忆: {memory2.id}, 权重: {memory2.weight}")
    
    print("\n" + "=" * 60)
    print("2. 标记为临时记忆（重要信息）")
    print("=" * 60)
    
    # 用户觉得这个信息很重要，标记为临时记忆
    await manager.mark_as_temporary(
        memory_id=memory2.id,
        user_id=user_id,
        expires_in_days=30,  # 30天后过期
        importance=0.9
    )
    print(f"标记为临时记忆，30天后过期")
    
    print("\n" + "=" * 60)
    print("3. 保存为永久记忆")
    print("=" * 60)
    
    # 创建一个永久记忆
    permanent_memory = await manager.create_memory(
        user_id=user_id,
        session_id=session_id,
        content="公司地址：北京市朝阳区xxx大厦",
        memory_type=MemoryType.PERMANENT,
        metadata=MemoryMetadata(
            title="公司地址",
            tags=["公司信息", "地址"],
            source=MemorySource.USER_MARKED,
            importance=1.0
        )
    )
    print(f"创建永久记忆: {permanent_memory.id}")
    
    print("\n" + "=" * 60)
    print("4. 检索记忆")
    print("=" * 60)
    
    query = MemoryQuery(
        query_text="年假政策",
        user_id=user_id,
        session_id=session_id,
        top_k=5
    )
    
    memories = await manager.retrieve_memories(query)
    print(f"检索到 {len(memories)} 条记忆:")
    for i, mem in enumerate(memories, 1):
        print(f"  {i}. [{mem.memory_type.value}] 权重:{mem.weight:.3f} - {mem.content[:50]}...")
    
    print("\n" + "=" * 60)
    print("5. 会话结束，转换工作记忆")
    print("=" * 60)
    
    # 会话结束，将工作记忆转为短期记忆
    await manager.convert_working_to_short_term(session_id, user_id)
    print("工作记忆已转换为短期记忆")
    
    print("\n" + "=" * 60)
    print("6. 列出所有记忆")
    print("=" * 60)
    
    all_memories = await manager.list_memories(user_id=user_id, limit=10)
    print(f"用户共有 {len(all_memories)} 条记忆:")
    for mem in all_memories:
        print(f"  - [{mem.memory_type.value}] {mem.metadata.title or mem.content[:30]}")


async def example_advanced_usage():
    """高级使用示例"""
    manager = get_enhanced_memory_manager()
    user_id = "user_789"
    
    print("\n" + "=" * 60)
    print("高级功能示例")
    print("=" * 60)
    
    # 1. 创建带标签的记忆
    print("\n1. 创建分类记忆")
    memory1 = await manager.create_memory(
        user_id=user_id,
        session_id="session_001",
        content="项目A的截止日期是2024年12月31日",
        memory_type=MemoryType.TEMPORARY,
        metadata=MemoryMetadata(
            title="项目A截止日期",
            tags=["项目", "截止日期", "重要"],
            importance=0.9
        ),
        expires_in_days=90
    )
    print(f"创建记忆: {memory1.metadata.title}, 标签: {memory1.metadata.tags}")
    
    # 2. 按标签检索
    print("\n2. 按标签检索")
    query = MemoryQuery(
        query_text="项目",
        user_id=user_id,
        tags=["项目"],
        top_k=10
    )
    project_memories = await manager.retrieve_memories(query)
    print(f"找到 {len(project_memories)} 条项目相关记忆")
    
    # 3. 按类型列出
    print("\n3. 列出临时记忆")
    temp_memories = await manager.list_memories(
        user_id=user_id,
        memory_type=MemoryType.TEMPORARY
    )
    print(f"临时记忆数量: {len(temp_memories)}")
    for mem in temp_memories:
        days_left = (mem.expires_at - datetime.utcnow()).days if mem.expires_at else None
        print(f"  - {mem.metadata.title}, 剩余天数: {days_left}")
    
    # 4. 更新记忆
    print("\n4. 更新记忆")
    await manager.update_memory(
        memory_id=memory1.id,
        user_id=user_id,
        metadata=MemoryMetadata(
            title="项目A截止日期（已延期）",
            tags=["项目", "截止日期", "重要", "已延期"],
            importance=0.95
        )
    )
    print("记忆已更新")
    
    # 5. 清理过期记忆
    print("\n5. 清理过期记忆")
    await manager.cleanup_expired_memories(user_id)
    print("过期记忆已清理")
    
    # 6. 归档旧记忆
    print("\n6. 归档旧记忆")
    await manager.archive_old_memories(user_id)
    print("旧记忆已归档")


async def example_weight_calculation():
    """权重计算示例"""
    manager = get_enhanced_memory_manager()
    user_id = "user_weight_test"
    session_id = "session_weight"
    
    print("\n" + "=" * 60)
    print("权重计算示例")
    print("=" * 60)
    
    # 创建不同类型的记忆
    memory_types = [
        (MemoryType.WORKING, "工作记忆"),
        (MemoryType.TEMPORARY, "临时记忆"),
        (MemoryType.SHORT_TERM, "短期记忆"),
        (MemoryType.LONG_TERM, "长期记忆"),
        (MemoryType.PERMANENT, "永久记忆")
    ]
    
    print("\n初始权重:")
    for mem_type, name in memory_types:
        memory = await manager.create_memory(
            user_id=user_id,
            session_id=session_id,
            content=f"这是一条{name}测试",
            memory_type=mem_type,
            metadata=MemoryMetadata(importance=0.5)
        )
        print(f"  {name}: {memory.weight:.3f}")
    
    print("\n不同重要性的权重:")
    for importance in [0.3, 0.5, 0.7, 0.9]:
        memory = await manager.create_memory(
            user_id=user_id,
            session_id=session_id,
            content=f"重要性{importance}的记忆",
            memory_type=MemoryType.SHORT_TERM,
            metadata=MemoryMetadata(importance=importance)
        )
        print(f"  重要性 {importance}: 权重 {memory.weight:.3f}")


async def example_memory_lifecycle():
    """记忆生命周期示例"""
    manager = get_enhanced_memory_manager()
    user_id = "user_lifecycle"
    session_id = "session_lifecycle"
    
    print("\n" + "=" * 60)
    print("记忆生命周期示例")
    print("=" * 60)
    
    # 1. 对话开始 - 创建工作记忆
    print("\n阶段1: 对话开始")
    memory = await manager.create_memory(
        user_id=user_id,
        session_id=session_id,
        content="用户询问产品价格",
        memory_type=MemoryType.WORKING
    )
    print(f"创建工作记忆: {memory.memory_type.value}")
    
    # 2. 用户标记为重要 - 转为临时记忆
    print("\n阶段2: 用户标记为重要")
    await manager.mark_as_temporary(
        memory_id=memory.id,
        user_id=user_id,
        expires_in_days=7
    )
    updated = await manager.get_memory(memory.id, user_id)
    print(f"转为临时记忆: {updated.memory_type.value}, 7天后过期")
    
    # 3. 用户决定永久保存
    print("\n阶段3: 保存为永久记忆")
    await manager.save_as_permanent(
        memory_id=memory.id,
        user_id=user_id,
        title="产品价格信息",
        tags=["产品", "价格"]
    )
    final = await manager.get_memory(memory.id, user_id)
    print(f"转为永久记忆: {final.memory_type.value}, 不会过期")
    
    print("\n记忆生命周期完成:")
    print(f"  工作记忆 → 临时记忆 → 永久记忆")


if __name__ == "__main__":
    # 运行示例
    asyncio.run(example_basic_usage())
    asyncio.run(example_advanced_usage())
    asyncio.run(example_weight_calculation())
    asyncio.run(example_memory_lifecycle())
