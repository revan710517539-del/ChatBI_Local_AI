"""
Prometheus Metrics Collection

Collects and exposes metrics for monitoring GenBI pipeline performance.

Metrics Categories:
1. Request Metrics: Total requests, success/error rates
2. Pipeline Metrics: Step execution times, token consumption
3. LLM Metrics: Model calls, latency, token usage
4. Cube API Metrics: Query execution time, error rates
5. Agent Metrics: Per-agent execution time and success rates
"""

from typing import Dict, Any, Optional
from functools import wraps
import time

from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Info,
    generate_latest,
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
)
from loguru import logger

from chatbi.config import get_config

config = get_config()


# Create custom registry for isolation
REGISTRY = CollectorRegistry()


# ==========================================
# Request Metrics
# ==========================================

request_total = Counter(
    "chatbi_requests_total",
    "Total number of requests",
    ["endpoint", "method", "status"],
    registry=REGISTRY,
)

request_duration = Histogram(
    "chatbi_request_duration_seconds",
    "Request duration in seconds",
    ["endpoint", "method"],
    registry=REGISTRY,
)

request_errors = Counter(
    "chatbi_request_errors_total",
    "Total number of request errors",
    ["endpoint", "error_type"],
    registry=REGISTRY,
)


# ==========================================
# Pipeline Metrics
# ==========================================

pipeline_step_duration = Histogram(
    "chatbi_pipeline_step_duration_seconds",
    "Pipeline step execution time in seconds",
    ["pipeline", "step"],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0),
    registry=REGISTRY,
)

pipeline_executions = Counter(
    "chatbi_pipeline_executions_total",
    "Total pipeline executions",
    ["pipeline", "status"],  # status: success, error
    registry=REGISTRY,
)

pipeline_step_errors = Counter(
    "chatbi_pipeline_step_errors_total",
    "Errors in pipeline steps",
    ["pipeline", "step", "error_type"],
    registry=REGISTRY,
)


# ==========================================
# LLM Metrics
# ==========================================

llm_calls_total = Counter(
    "chatbi_llm_calls_total",
    "Total LLM API calls",
    ["model", "agent", "status"],  # status: success, error
    registry=REGISTRY,
)

llm_latency = Histogram(
    "chatbi_llm_latency_seconds",
    "LLM API call latency in seconds",
    ["model", "agent"],
    buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 60.0),
    registry=REGISTRY,
)

llm_tokens_total = Counter(
    "chatbi_llm_tokens_total",
    "Total tokens consumed",
    ["model", "agent", "token_type"],  # token_type: prompt, completion
    registry=REGISTRY,
)

llm_cost_total = Counter(
    "chatbi_llm_cost_usd_total",
    "Total LLM cost in USD",
    ["model", "agent"],
    registry=REGISTRY,
)


# ==========================================
# Agent Metrics
# ==========================================

agent_execution_duration = Histogram(
    "chatbi_agent_execution_duration_seconds",
    "Agent execution time in seconds",
    ["agent_name"],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0),
    registry=REGISTRY,
)

agent_executions_total = Counter(
    "chatbi_agent_executions_total",
    "Total agent executions",
    ["agent_name", "status"],  # status: success, error
    registry=REGISTRY,
)


# ==========================================
# System Metrics
# ==========================================

active_sessions = Gauge(
    "chatbi_active_sessions",
    "Number of active user sessions",
    registry=REGISTRY,
)

cache_hits = Counter(
    "chatbi_cache_hits_total",
    "Cache hit count",
    ["cache_type"],  # cache_type: mdl, query, etc.
    registry=REGISTRY,
)

cache_misses = Counter(
    "chatbi_cache_misses_total",
    "Cache miss count",
    ["cache_type"],
    registry=REGISTRY,
)


# ==========================================
# Application Info
# ==========================================

app_info = Info(
    "chatbi_app",
    "ChatBI application information",
    registry=REGISTRY,
)

app_info.info({
    "version": config.version,
    "environment": config.env,
    "llm_provider": config.llm.provider,
    "llm_model": config.llm.model,
})


# ==========================================
# Metrics Collector Class
# ==========================================

class MetricsCollector:
    """Centralized metrics collection for GenBI pipeline.
    
    Usage:
        ```python
        collector = MetricsCollector()
        
        # Record request
        with collector.track_request("/api/v1/ask", "POST") as tracker:
            # ... handle request ...
            tracker.set_status(200)
        
        # Record LLM call
        with collector.track_llm_call("gpt-4", "QueryReasoningAgent") as tracker:
            response = await llm.generate(prompt)
            tracker.set_tokens(prompt_tokens=100, completion_tokens=50)
        
        # Record agent execution
        with collector.track_agent("QueryReasoningAgent") as tracker:
            result = await agent.replay(...)
        ```
    """
    
    def __init__(self):
        """Initialize metrics collector"""
        logger.info("MetricsCollector initialized")
    
    def track_request(self, endpoint: str, method: str):
        """Track HTTP request metrics.
        
        Args:
            endpoint: API endpoint path
            method: HTTP method
        
        Returns:
            Context manager with set_status() method
        """
        return RequestTracker(endpoint, method)
    
    def track_pipeline_step(self, pipeline: str, step: str):
        """Track pipeline step execution.
        
        Args:
            pipeline: Pipeline name (e.g., "AskPipeline")
            step: Step name (e.g., "MDL_Retrieval")
        
        Returns:
            Context manager
        """
        return PipelineStepTracker(pipeline, step)
    
    def track_llm_call(self, model: str, agent: str):
        """Track LLM API call.
        
        Args:
            model: Model name (e.g., "gpt-4")
            agent: Agent name (e.g., "QueryReasoningAgent")
        
        Returns:
            Context manager with set_tokens() and set_cost() methods
        """
        return LLMCallTracker(model, agent)
    
    def track_agent(self, agent_name: str):
        """Track agent execution.
        
        Args:
            agent_name: Agent name
        
        Returns:
            Context manager
        """
        return AgentTracker(agent_name)
    
    def record_cache_hit(self, cache_type: str):
        """Record cache hit.
        
        Args:
            cache_type: Type of cache (mdl, query, etc.)
        """
        cache_hits.labels(cache_type=cache_type).inc()
    
    def record_cache_miss(self, cache_type: str):
        """Record cache miss.
        
        Args:
            cache_type: Type of cache
        """
        cache_misses.labels(cache_type=cache_type).inc()
    
    def set_active_sessions(self, count: int):
        """Update active sessions gauge.
        
        Args:
            count: Number of active sessions
        """
        active_sessions.set(count)
    
    @staticmethod
    def get_metrics() -> bytes:
        """Get Prometheus metrics in text format.
        
        Returns:
            Metrics in Prometheus text format
        """
        return generate_latest(REGISTRY)
    
    @staticmethod
    def get_content_type() -> str:
        """Get Prometheus metrics content type.
        
        Returns:
            Content type string
        """
        return CONTENT_TYPE_LATEST


# ==========================================
# Context Managers for Tracking
# ==========================================

class RequestTracker:
    """Context manager for tracking requests"""
    
    def __init__(self, endpoint: str, method: str):
        self.endpoint = endpoint
        self.method = method
        self.start_time = None
        self.status = 500  # Default to error
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        status_str = str(self.status // 100) + "xx"
        
        request_total.labels(
            endpoint=self.endpoint,
            method=self.method,
            status=status_str,
        ).inc()
        
        request_duration.labels(
            endpoint=self.endpoint,
            method=self.method,
        ).observe(duration)
        
        if exc_type:
            error_type = exc_type.__name__ if exc_type else "unknown"
            request_errors.labels(
                endpoint=self.endpoint,
                error_type=error_type,
            ).inc()
    
    def set_status(self, status: int):
        """Set HTTP status code"""
        self.status = status


class PipelineStepTracker:
    """Context manager for tracking pipeline steps"""
    
    def __init__(self, pipeline: str, step: str):
        self.pipeline = pipeline
        self.step = step
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        
        pipeline_step_duration.labels(
            pipeline=self.pipeline,
            step=self.step,
        ).observe(duration)
        
        status = "error" if exc_type else "success"
        pipeline_executions.labels(
            pipeline=self.pipeline,
            status=status,
        ).inc()
        
        if exc_type:
            error_type = exc_type.__name__ if exc_type else "unknown"
            pipeline_step_errors.labels(
                pipeline=self.pipeline,
                step=self.step,
                error_type=error_type,
            ).inc()


class LLMCallTracker:
    """Context manager for tracking LLM calls"""
    
    def __init__(self, model: str, agent: str):
        self.model = model
        self.agent = agent
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        status = "error" if exc_type else "success"
        
        llm_calls_total.labels(
            model=self.model,
            agent=self.agent,
            status=status,
        ).inc()
        
        llm_latency.labels(
            model=self.model,
            agent=self.agent,
        ).observe(duration)
    
    def set_tokens(self, prompt_tokens: int, completion_tokens: int):
        """Record token usage"""
        llm_tokens_total.labels(
            model=self.model,
            agent=self.agent,
            token_type="prompt",
        ).inc(prompt_tokens)
        
        llm_tokens_total.labels(
            model=self.model,
            agent=self.agent,
            token_type="completion",
        ).inc(completion_tokens)
    
    def set_cost(self, cost_usd: float):
        """Record LLM cost"""
        llm_cost_total.labels(
            model=self.model,
            agent=self.agent,
        ).inc(cost_usd)


class AgentTracker:
    """Context manager for tracking agent executions"""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        status = "error" if exc_type else "success"
        
        agent_execution_duration.labels(
            agent_name=self.agent_name,
        ).observe(duration)
        
        agent_executions_total.labels(
            agent_name=self.agent_name,
            status=status,
        ).inc()


# ==========================================
# Global Singleton
# ==========================================

_global_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get global metrics collector instance.
    
    Returns:
        Singleton MetricsCollector
    """
    global _global_metrics_collector
    if _global_metrics_collector is None:
        _global_metrics_collector = MetricsCollector()
    return _global_metrics_collector
