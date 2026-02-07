"""Langfuse observer for LLM call tracing and cost tracking.

This module provides observability for LLM interactions using Langfuse.
It wraps LLM calls with tracing, cost calculation, and performance metrics.
"""

import random
import time
from contextlib import contextmanager
from typing import Any, AsyncGenerator, Dict, Generator, Optional

from langfuse import Langfuse
from loguru import logger

from chatbi.config import get_config

config = get_config()


class LangfuseObserver:
    """Observer for tracking LLM calls with Langfuse.
    
    Features:
    - Automatic trace/generation creation for LLM calls
    - Token counting and cost calculation
    - Latency measurement
    - Error tracking
    - Sampling support (可配置采样率降低成本)
    """

    def __init__(
        self,
        enabled: Optional[bool] = None,
        sample_rate: Optional[float] = None,
    ):
        """Initialize Langfuse observer.
        
        Args:
            enabled: Whether to enable Langfuse tracking (default from config)
            sample_rate: Sampling rate 0.0-1.0 (default from config)
        """
        self.enabled = enabled if enabled is not None else config.langfuse.enabled
        self.sample_rate = sample_rate if sample_rate is not None else config.langfuse.sample_rate
        
        self.client: Optional[Langfuse] = None
        
        if self.enabled:
            try:
                self.client = Langfuse(
                    public_key=config.langfuse.public_key,
                    secret_key=config.langfuse.secret_key,
                    host=config.langfuse.host,
                    debug=config.langfuse.debug,
                    flush_interval=config.langfuse.flush_interval,
                )
                logger.info("Langfuse observer initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Langfuse: {e}")
                self.enabled = False
    
    def _should_sample(self) -> bool:
        """Determine if this call should be sampled (根据采样率)."""
        if self.sample_rate >= 1.0:
            return True
        return random.random() < self.sample_rate
    
    @contextmanager
    def trace_llm_call(
        self,
        name: str,
        model: str,
        prompt: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        """Context manager for tracing a single LLM call.
        
        Args:
            name: Name of the LLM call (e.g., "QueryReasoningAgent")
            model: Model name (e.g., "gpt-4")
            prompt: Input prompt
            session_id: Optional session ID for grouping traces
            user_id: Optional user ID
            metadata: Additional metadata
        
        Yields:
            Context dict with trace/generation objects
        
        Example:
            ```python
            observer = LangfuseObserver()
            with observer.trace_llm_call(
                name="QueryGeneration",
                model="gpt-4",
                prompt=user_question,
                session_id=session_id,
            ) as ctx:
                response = llm.generate(prompt)
                ctx["output"] = response
                ctx["usage"] = {"prompt_tokens": 100, "completion_tokens": 50}
            ```
        """
        if not self.enabled or not self._should_sample():
            # Disabled or not sampled - yield empty context
            yield {}
            return
        
        start_time = time.time()
        trace = None
        generation = None
        context: Dict[str, Any] = {}
        
        try:
            # Create trace
            trace = self.client.trace(
                name=name,
                session_id=session_id,
                user_id=user_id,
                metadata=metadata or {},
            )
            
            # Create generation
            generation = trace.generation(
                name=name,
                model=model,
                input=prompt,
                metadata=metadata or {},
            )
            
            context = {
                "trace": trace,
                "generation": generation,
                "output": None,
                "usage": None,
            }
            
            yield context
            
        except Exception as e:
            logger.error(f"Error in Langfuse tracing: {e}")
            yield context
        
        finally:
            # Finalize generation with output and metrics
            if generation and self.client:
                try:
                    latency_ms = int((time.time() - start_time) * 1000)
                    
                    # Extract usage from context
                    usage = context.get("usage") or {}
                    output = context.get("output")
                    
                    # Update generation
                    generation.update(
                        output=output,
                        usage=usage,
                        latency=latency_ms,
                        end_time=time.time(),
                    )
                    
                    # Flush immediately for this call
                    self.client.flush()
                    
                except Exception as e:
                    logger.error(f"Error finalizing Langfuse generation: {e}")
    
    async def trace_llm_streaming(
        self,
        name: str,
        model: str,
        prompt: str,
        stream: AsyncGenerator[str, None],
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[str, None]:
        """Trace a streaming LLM call.
        
        Args:
            name: Name of the LLM call
            model: Model name
            prompt: Input prompt
            stream: Async generator of output chunks
            session_id: Optional session ID
            user_id: Optional user ID
            metadata: Additional metadata
        
        Yields:
            Output chunks from the stream
        
        Example:
            ```python
            observer = LangfuseObserver()
            stream = llm.generate_stream(prompt)
            traced_stream = observer.trace_llm_streaming(
                name="AnswerGeneration",
                model="gpt-4",
                prompt=prompt,
                stream=stream,
                session_id=session_id,
            )
            async for chunk in traced_stream:
                yield chunk
            ```
        """
        if not self.enabled or not self._should_sample():
            # Pass through without tracing
            async for chunk in stream:
                yield chunk
            return
        
        start_time = time.time()
        trace = None
        generation = None
        output_chunks = []
        
        try:
            # Create trace
            trace = self.client.trace(
                name=name,
                session_id=session_id,
                user_id=user_id,
                metadata=metadata or {},
            )
            
            # Create generation
            generation = trace.generation(
                name=name,
                model=model,
                input=prompt,
                metadata={**(metadata or {}), "streaming": True},
            )
            
            # Stream and collect output
            async for chunk in stream:
                output_chunks.append(chunk)
                yield chunk
            
        except Exception as e:
            logger.error(f"Error in Langfuse streaming: {e}")
            # Continue yielding remaining chunks
            async for chunk in stream:
                yield chunk
        
        finally:
            # Finalize generation
            if generation and self.client:
                try:
                    latency_ms = int((time.time() - start_time) * 1000)
                    full_output = "".join(output_chunks)
                    
                    # Estimate tokens (rough approximation)
                    prompt_tokens = len(prompt.split()) * 1.3  # 平均 1 token ≈ 0.75 word
                    completion_tokens = len(full_output.split()) * 1.3
                    
                    generation.update(
                        output=full_output,
                        usage={
                            "prompt_tokens": int(prompt_tokens),
                            "completion_tokens": int(completion_tokens),
                            "total_tokens": int(prompt_tokens + completion_tokens),
                        },
                        latency=latency_ms,
                        end_time=time.time(),
                    )
                    
                    self.client.flush()
                    
                except Exception as e:
                    logger.error(f"Error finalizing streaming generation: {e}")
    
    def flush(self):
        """Flush pending traces to Langfuse (手动刷新)."""
        if self.client:
            try:
                self.client.flush()
            except Exception as e:
                logger.error(f"Error flushing Langfuse: {e}")
    
    def shutdown(self):
        """Shutdown Langfuse client (应用关闭时调用)."""
        if self.client:
            try:
                self.client.flush()
                # Langfuse client doesn't have explicit shutdown method
                logger.info("Langfuse observer shut down")
            except Exception as e:
                logger.error(f"Error shutting down Langfuse: {e}")


# Global singleton instance
_global_observer: Optional[LangfuseObserver] = None


def get_langfuse_observer() -> LangfuseObserver:
    """Get the global Langfuse observer instance.
    
    Returns:
        Singleton LangfuseObserver instance
    """
    global _global_observer
    if _global_observer is None:
        _global_observer = LangfuseObserver()
    return _global_observer
