"""
Agent 基础模块

本模块定义了Agent系统的核心抽象基类和执行引擎，为整个Agent架构提供统一的接口规范。
所有具体的Agent实现都应继承BaseAgent基类，并通过AgentEngine进行统一管理和调度。

核心组件:
    - AgentState: Agent状态枚举，定义Agent的生命周期状态
    - BaseAgent: Agent抽象基类，定义Agent的核心接口
    - AgentEngine: Agent执行引擎，负责Agent的注册、发现和执行

使用示例:
    class MyAgent(BaseAgent):
        @property
        def agent_id(self) -> str:
            return "my_agent"
        
        @property
        def name(self) -> str:
            return "My Custom Agent"
        
        async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
            # 实现具体的Agent逻辑
            return {"result": "success"}
    
    # 注册到引擎
    agent_engine.register(MyAgent())
    
    # 执行Agent
    result = await agent_engine.execute("my_agent", {"input": "data"})
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from enum import Enum
from app.core.config_loader import config_loader


class AgentState(Enum):
    """
    Agent状态枚举类
    
    定义Agent在其生命周期中可能处于的各种状态，用于状态管理和监控。
    
    属性:
        IDLE: 空闲状态，Agent未执行任何任务，可以接受新的请求
        PROCESSING: 处理中状态，Agent正在执行任务，不可接受新请求
        COMPLETED: 完成状态，Agent成功完成任务
        ERROR: 错误状态，Agent执行过程中发生错误
    
    使用场景:
        - 监控Agent运行状态
        - 实现状态机逻辑
        - 负载均衡和任务调度
    """
    IDLE = "idle"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"


class BaseAgent(ABC):
    """
    Agent抽象基类
    
    定义了所有Agent必须实现的核心接口，确保Agent实现的一致性和可扩展性。
    采用抽象基类模式，强制子类实现关键方法。
    
    设计原则:
        - 接口隔离: 只定义必要的抽象方法
        - 单一职责: 每个Agent专注于特定领域
        - 开闭原则: 对扩展开放，对修改关闭
    
    属性:
        agent_id (str): Agent的唯一标识符，用于注册和查找
        name (str): Agent的显示名称，用于日志和UI展示
    
    方法:
        run: Agent的核心执行方法，处理输入数据并返回结果
    
    示例:
        class QAAgent(BaseAgent):
            @property
            def agent_id(self) -> str:
                return "qa_agent"
            
            @property
            def name(self) -> str:
                return "问答助手"
            
            async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
                query = input_data.get("query")
                answer = await self._process_query(query)
                return {"answer": answer}
    """
    
    @property
    @abstractmethod
    def agent_id(self) -> str:
        """
        Agent的唯一标识符
        
        返回:
            str: Agent的唯一ID字符串，建议使用下划线分隔的小写命名
        
        要求:
            - 必须全局唯一
            - 建议格式: {domain}_{function}_agent
            - 示例: "qa_agent", "document_processor_agent"
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Agent的显示名称
        
        返回:
            str: Agent的可读名称，用于日志、UI展示等
        
        要求:
            - 简洁明了，易于理解
            - 支持中英文
            - 示例: "问答助手", "Document Processor"
        """
        pass
    
    @abstractmethod
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行Agent的核心逻辑
        
        这是Agent的主要入口方法，接收输入数据，执行业务逻辑，返回处理结果。
        所有具体的Agent实现都必须提供此方法的具体实现。
        
        参数:
            input_data (Dict[str, Any]): 输入数据字典，包含Agent执行所需的所有参数
                - 键名和值类型由具体Agent定义
                - 建议使用明确的键名，如 "query", "document_id" 等
                - 应包含必要的验证和错误处理
        
        返回:
            Dict[str, Any]: 执行结果字典，包含处理后的数据
                - 必须包含执行状态信息（如 "success", "error"）
                - 包含具体的业务数据
                - 建议统一返回格式: {"success": bool, "data": Any, "error": Optional[str]}
        
        异常:
            - 子类实现可能抛出各种业务异常
            - 建议捕获异常并返回错误信息，而不是直接抛出
        
        性能考虑:
            - 此方法为异步方法，支持并发执行
            - 避免在方法内进行阻塞操作
            - 长时间运行的任务应考虑进度反馈机制
        
        示例:
            async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
                try:
                    query = input_data.get("query")
                    if not query:
                        return {"success": False, "error": "缺少query参数"}
                    
                    result = await self._process(query)
                    return {"success": True, "data": result}
                except Exception as e:
                    return {"success": False, "error": str(e)}
        """
        pass


class AgentEngine:
    """
    Agent执行引擎
    
    负责Agent的生命周期管理，包括注册、发现、执行和监控。
    采用注册表模式，提供统一的Agent管理入口。
    
    核心功能:
        1. Agent注册: 将Agent实例注册到引擎中，建立ID到实例的映射
        2. Agent发现: 根据ID查找已注册的Agent实例
        3. Agent执行: 调用Agent的run方法执行具体逻辑
        4. Agent列表: 获取所有已注册的Agent ID列表
    
    设计模式:
        - 注册表模式(Registry Pattern): 集中管理所有Agent实例
        - 单例模式(Singleton Pattern): 全局唯一的引擎实例
    
    线程安全:
        - 当前实现非线程安全
        - 如需并发注册，应添加锁机制
    
    使用示例:
        # 创建并注册Agent
        qa_agent = QAAgent()
        agent_engine.register(qa_agent)
        
        # 执行Agent
        result = await agent_engine.execute("qa_agent", {"query": "什么是Agent?"})
        
        # 列出所有Agent
        all_agents = agent_engine.list_all()
    """
    
    def __init__(self):
        """
        初始化Agent执行引擎
        
        创建空的Agent注册表，用于存储Agent ID到实例的映射关系。
        """
        self._agents: Dict[str, BaseAgent] = {}
    
    def register(self, agent: BaseAgent) -> None:
        """
        注册Agent实例到引擎
        
        将Agent实例添加到注册表中，使其可以通过ID被查找和执行。
        如果ID已存在，将覆盖之前的Agent实例。
        
        参数:
            agent (BaseAgent): 要注册的Agent实例，必须实现BaseAgent接口
        
        返回:
            None
        
        注意事项:
            - 重复注册相同ID的Agent会覆盖之前的实例
            - 建议在应用启动时完成所有Agent的注册
            - 注册后的Agent实例不应被修改
        
        示例:
            agent_engine.register(QAAgent())
            agent_engine.register(DocumentAgent())
        """
        self._agents[agent.agent_id] = agent
    
    def get(self, agent_id: str) -> BaseAgent:
        """
        根据ID获取Agent实例
        
        从注册表中查找指定ID的Agent实例，如果不存在则抛出异常。
        
        参数:
            agent_id (str): Agent的唯一标识符
        
        返回:
            BaseAgent: 对应ID的Agent实例
        
        异常:
            ValueError: 当指定的agent_id不存在时抛出
        
        性能考虑:
            - 使用字典查找，时间复杂度O(1)
            - 适合高频调用
        
        示例:
            try:
                agent = agent_engine.get("qa_agent")
                result = await agent.run({"query": "test"})
            except ValueError as e:
                print(f"Agent不存在: {e}")
        """
        agent = self._agents.get(agent_id)
        if not agent:
            raise ValueError(f"Agent not found: {agent_id}")
        return agent
    
    async def execute(self, agent_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行指定Agent的业务逻辑
        
        根据agent_id查找Agent实例，并调用其run方法执行业务逻辑。
        这是调用Agent的主要入口方法。
        
        参数:
            agent_id (str): Agent的唯一标识符
            input_data (Dict[str, Any]): 传递给Agent的输入数据
        
        返回:
            Dict[str, Any]: Agent执行的结果数据
        
        异常:
            ValueError: 当指定的agent_id不存在时抛出
            Exception: Agent执行过程中可能抛出的业务异常
        
        性能考虑:
            - 异步执行，支持并发调用多个Agent
            - 建议添加超时和重试机制
            - 可考虑添加执行日志和监控
        
        示例:
            # 执行单个Agent
            result = await agent_engine.execute("qa_agent", {
                "query": "什么是Agent架构?"
            })
            
            # 并发执行多个Agent
            import asyncio
            results = await asyncio.gather(
                agent_engine.execute("qa_agent", {"query": "问题1"}),
                agent_engine.execute("qa_agent", {"query": "问题2"})
            )
        """
        agent = self.get(agent_id)
        return await agent.run(input_data)
    
    def list_all(self) -> List[str]:
        """
        获取所有已注册的Agent ID列表
        
        返回当前引擎中所有已注册Agent的ID列表，用于监控和管理。
        
        返回:
            List[str]: Agent ID列表，顺序不确定
        
        性能考虑:
            - 返回列表的副本，修改不影响内部注册表
            - 时间复杂度O(n)，n为Agent数量
        
        使用场景:
            - 监控和展示可用的Agent
            - 动态发现和调用Agent
            - 系统健康检查
        
        示例:
            all_agents = agent_engine.list_all()
            print(f"当前已注册的Agent: {all_agents}")
            # 输出: ['qa_agent', 'document_agent', 'search_agent']
        """
        return list(self._agents.keys())


# 全局Agent引擎实例
# 采用单例模式，确保整个应用使用同一个引擎实例
agent_engine = AgentEngine()
