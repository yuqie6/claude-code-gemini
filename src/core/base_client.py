from abc import ABC, abstractmethod
from typing import AsyncGenerator

class BaseAPIClient(ABC):
    """Abstract base class for API clients."""

    @abstractmethod
    async def create_chat_completion(
        self, request: dict, request_id: str
    ) -> dict:
        """Create a non-streaming chat completion."""
        pass

    @abstractmethod
    async def create_chat_completion_stream(
        self, request: dict, request_id: str
    ) -> AsyncGenerator[bytes, None]:
        """Create a streaming chat completion."""
        # This is an async generator, so it should yield bytes.
        # The 'pass' is just a placeholder; the implementation will use 'yield'.
        yield b''