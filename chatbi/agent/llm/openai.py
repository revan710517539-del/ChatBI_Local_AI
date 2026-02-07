"""
OpenAI-compatible LLM implementation

Supports both OpenAI API and compatible providers (DeepSeek, Tongyi, etc.)
with streaming and non-streaming generation.
"""

import os
from typing import AsyncGenerator

import dspy
from dotenv import load_dotenv
from openai import AsyncOpenAI
from loguru import logger

from chatbi.agent.llm.base_llm import BaseLLM


class OpenaiModel(BaseLLM):
    """OpenAI-compatible LLM provider"""

    name: str = "openai"

    def __init__(self):
        load_dotenv()

        self.api_key = os.getenv("LLM_API_KEY")
        self.base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
        self.model = os.getenv("LLM_MODEL", "qwen-max")

        # dspy for structured generation
        self.llm = dspy.LM(
            model=f"openai/{self.model}", api_key=self.api_key, api_base=self.base_url
        )
        dspy.configure(lm=self.llm, suppress_debug_info=True)

        # AsyncOpenAI client for streaming
        self.client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)

        logger.info(f"OpenaiModel initialized with model: {self.model}")

    async def generate(self, prompt: str, temperature: float = 0.7) -> str:
        """
        Generate text from prompt (async, non-streaming)

        Args:
            prompt: Input prompt
            temperature: Sampling temperature

        Returns:
            Generated text
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                stream=False,
            )

            content = response.choices[0].message.content
            return content if content else ""

        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            raise

    async def generate_stream(
        self, prompt: str, temperature: float = 0.7
    ) -> AsyncGenerator[str, None]:
        """
        Generate text from prompt with streaming

        Args:
            prompt: Input prompt
            temperature: Sampling temperature

        Yields:
            Text chunks
        """
        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                stream=True,
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"LLM streaming failed: {e}")
            yield f"Error: {str(e)}"
