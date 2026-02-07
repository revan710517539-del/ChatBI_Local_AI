from __future__ import annotations

from collections.abc import Iterable
from typing import Optional

from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel


class CreateCompletionsDTO(BaseModel):
    messages: Iterable[ChatCompletionMessageParam]
    n: Optional[int] | None = 1
    temperature: Optional[float] | None = 0
