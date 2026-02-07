"""
Base LLM interface for agent communication

Provides both synchronous and streaming LLM generation.
"""

from abc import ABC, abstractmethod
from typing import AsyncGenerator

import dspy


class BaseLLM(ABC):
    """Base class for LLM providers"""

    name: str
    api_key: str
    base_url: str
    model: str
    llm: dspy.LM | None = None

    @abstractmethod
    async def generate(self, prompt: str, temperature: float = 0.7) -> str:
        """
        Generate text from prompt (async)

        Args:
            prompt: Input prompt
            temperature: Sampling temperature (0.0-2.0)

        Returns:
            Generated text
        """
        pass

    @abstractmethod
    async def generate_stream(
        self, prompt: str, temperature: float = 0.7
    ) -> AsyncGenerator[str, None]:
        """
        Generate text from prompt with streaming (async)

        Args:
            prompt: Input prompt
            temperature: Sampling temperature

        Yields:
            Text chunks as they are generated
        """
        pass
