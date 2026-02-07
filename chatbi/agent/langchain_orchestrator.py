from __future__ import annotations

import hashlib
from typing import Any, Optional

from loguru import logger

try:
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_openai import ChatOpenAI
except Exception:  # pragma: no cover
    ChatPromptTemplate = None
    ChatOpenAI = None


class SmartBILangChainOrchestrator:
    """
    LangChain-based orchestration for SmartBI.

    The class intentionally keeps a minimal runtime contract:
    - Build scene-aware analysis prompt
    - Allow future extension for tools/agents without coupling to current pipeline
    """

    @staticmethod
    def build_analysis_input(
        question: str,
        scene_prompt: str,
        rag_context: str | None = None,
        agent_prompt: str | None = None,
    ) -> str:
        sections = []
        if scene_prompt:
            sections.append(f"[Scene Prompt]\n{scene_prompt}")
        if agent_prompt:
            sections.append(f"[Agent Prompt]\n{agent_prompt}")
        if rag_context:
            sections.append(f"[Knowledge Context]\n{rag_context}")
        sections.append(f"[User Question]\n{question}")
        return "\n\n".join(sections)

    def summarize_for_dashboard(
        self,
        llm_cfg: Optional[dict[str, Any]],
        metrics_text: str,
    ) -> str:
        """
        Optional LangChain inference path for dashboard narrative.
        Falls back to deterministic text when provider is unavailable.
        """
        if not llm_cfg or not ChatPromptTemplate or not ChatOpenAI:
            return self._fallback_summary(metrics_text)

        try:
            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        "You are a senior loan analytics assistant. Provide concise Chinese executive summary.",
                    ),
                    ("human", "{input}"),
                ]
            )
            llm = ChatOpenAI(
                model=llm_cfg.get("model"),
                base_url=llm_cfg.get("base_url"),
                api_key=llm_cfg.get("api_key") or "ollama",
                temperature=0.2,
            )
            chain = prompt | llm
            resp = chain.invoke({"input": metrics_text})
            return getattr(resp, "content", None) or self._fallback_summary(metrics_text)
        except Exception as e:
            logger.warning(f"LangChain dashboard summary failed: {e}")
            return self._fallback_summary(metrics_text)

    @staticmethod
    def _fallback_summary(metrics_text: str) -> str:
        digest = hashlib.md5(metrics_text.encode("utf-8")).hexdigest()[:8]
        return f"贷款业务指标已更新（摘要ID: {digest}）。建议优先关注逾期率、迁徙率、额度使用率与风险收益比。"

