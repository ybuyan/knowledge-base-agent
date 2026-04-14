from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

import tiktoken


@dataclass
class Message:
    role: str
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    token_count: int = 0

    def __post_init__(self):
        if self.token_count == 0:
            self.token_count = self._count_tokens(self.content)

    @staticmethod
    def _count_tokens(text: str, model: str = None) -> int:
        """计算文本的 token 数量"""
        if model is None:
            from app.config import settings

            model = settings.llm_model

        try:
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))

    def to_dict(self) -> Dict:
        return {"role": self.role, "content": self.content}

    def to_openai_format(self) -> Dict:
        return {"role": self.role, "content": self.content}


class MemoryStrategy(ABC):
    @abstractmethod
    def manage(self, messages: List[Message], max_tokens: int) -> List[Message]:
        pass


class SlidingWindowStrategy(MemoryStrategy):
    def __init__(self, keep_system: bool = True, min_messages: int = 2):
        self.keep_system = keep_system
        self.min_messages = min_messages

    def manage(self, messages: List[Message], max_tokens: int) -> List[Message]:
        if not messages:
            return messages

        system_messages = []
        conversation_messages = []

        for m in messages:
            if m.role == "system":
                system_messages.append(m)
            else:
                conversation_messages.append(m)

        total_tokens = sum(m.token_count for m in system_messages) + sum(
            m.token_count for m in conversation_messages
        )

        while (
            total_tokens > max_tokens and len(conversation_messages) > self.min_messages
        ):
            removed = conversation_messages.pop(0)
            total_tokens -= removed.token_count

        return system_messages + conversation_messages


class ShortTermMemory:
    def __init__(
        self,
        max_tokens: int = 4000,
        model: str = None,
        strategy: Optional[MemoryStrategy] = None,
    ):
        if model is None:
            from app.config import settings

            model = settings.llm_model

        self.max_tokens = max_tokens
        self.model = model
        self.messages: List[Message] = []
        self.strategy = strategy or SlidingWindowStrategy()
        self._encoding = self._get_encoding(model)
        self._initialized = False

    def _get_encoding(self, model: str):
        try:
            return tiktoken.encoding_for_model(model)
        except KeyError:
            return tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        return len(self._encoding.encode(text))

    def add_message(self, role: str, content: str) -> Message:
        message = Message(
            role=role, content=content, token_count=self.count_tokens(content)
        )
        self.messages.append(message)
        return message

    def add_system_prompt(self, content: str) -> None:
        system_msg = Message(
            role="system", content=content, token_count=self.count_tokens(content)
        )
        existing_system = [m for m in self.messages if m.role == "system"]
        if existing_system:
            self.messages.remove(existing_system[0])
        self.messages.insert(0, system_msg)
        self._initialized = True

    def get_context(self, apply_strategy: bool = True) -> List[Dict]:
        if apply_strategy:
            managed_messages = self.strategy.manage(self.messages, self.max_tokens)
        else:
            managed_messages = self.messages
        return [m.to_openai_format() for m in managed_messages]

    def get_messages(self) -> List[Message]:
        return self.messages.copy()

    def get_token_count(self) -> int:
        return sum(m.token_count for m in self.messages)

    def get_remaining_tokens(self) -> int:
        return self.max_tokens - self.get_token_count()

    def clear(self) -> None:
        self.messages = []
        self._initialized = False

    def load_messages(self, messages: List[Dict]) -> None:
        self.messages = []
        for msg in messages:
            self.add_message(msg["role"], msg["content"])
        self._initialized = True

    def truncate_to_fit(self, new_content: str) -> None:
        new_tokens = self.count_tokens(new_content)
        while self.get_token_count() + new_tokens > self.max_tokens:
            non_system = [m for m in self.messages if m.role != "system"]
            if not non_system:
                break
            self.messages.remove(non_system[0])

    def is_initialized(self) -> bool:
        return self._initialized

    def get_last_message(self) -> Optional[Message]:
        if self.messages:
            return self.messages[-1]
        return None

    def get_message_count(self) -> int:
        return len([m for m in self.messages if m.role != "system"])
