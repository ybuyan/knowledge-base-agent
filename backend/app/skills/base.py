from abc import ABC, abstractmethod
from typing import Dict, Any, List


class BaseProcessor(ABC):
    """处理器基类"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @abstractmethod
    async def process(self, context: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        pass


class ProcessorRegistry:
    """处理器注册表"""
    
    _processors: Dict[str, BaseProcessor] = {}
    
    @classmethod
    def register(cls, name: str):
        def decorator(processor_class):
            instance = processor_class()
            cls._processors[name] = instance
            return processor_class
        return decorator
    
    @classmethod
    def get(cls, name: str) -> BaseProcessor:
        processor = cls._processors.get(name)
        if not processor:
            raise ValueError(f"Processor not found: {name}")
        return processor
    
    @classmethod
    def list_all(cls) -> List[str]:
        return list(cls._processors.keys())
