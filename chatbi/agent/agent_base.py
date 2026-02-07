from typing import Optional

from chatbi.agent.agent_message import AgentMessage
from chatbi.observability import LangfuseObserver


class AgentBase:
    def __init__(self, name: str, llm_provider=None, observer: Optional[LangfuseObserver] = None):
        self.name = name
        self.llm = llm_provider.get_generator() if llm_provider else None
        self.observer = observer

    @classmethod
    def replay(self, **kwargs) -> AgentMessage:
        pass
