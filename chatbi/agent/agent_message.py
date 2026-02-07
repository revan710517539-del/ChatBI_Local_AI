from typing import Optional, Any, Dict

class AgentMessage:
    def __init__(
        self,
        name: Optional[str] = None,
        agent_name: Optional[str] = None,
        id: Optional[str] = None,
        answer: Optional[str] = None,
        content: Optional[str] = None,
        reason: Optional[str] = None,
        reasoning: Optional[str] = None,
        type: str = "text",
        intent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        # Capture extra kwargs for flexibility
        **kwargs
    ):
        self.name = name or agent_name or "unknown"
        self.id = id
        self.answer = answer or content
        self.reason = reason
        self.reasoning = reasoning
        self.type = type
        self.intent = intent
        self.metadata = metadata or {}
        self.metadata.update(kwargs) # Store extra args in metadata
        
        # Aliases for compatibility
        self.content = self.answer

    def to_dict(self):
        return {
            "name": self.name,
            "id": self.id,
            "answer": self.answer,
            "reason": self.reason,
            "reasoning": self.reasoning,
            "type": self.type,
            "intent": self.intent,
            "metadata": self.metadata
        }

    def __str__(self) -> str:
        return str(self.to_dict())
