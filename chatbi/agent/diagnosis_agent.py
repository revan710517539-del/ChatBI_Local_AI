import dspy
from loguru import logger

from chatbi.agent.agent_message import AgentMessage
from chatbi.agent.agent_base import AgentBase
from chatbi.agent.prompts.diagnosis_prompt import DiagnosisSignature
from chatbi.domain.diagnosis.dtos import InsightSummary


class DiagnosisAgent(AgentBase):
    def __init__(self, name="DiagnosisAgent"):
        super().__init__(name=name)

    def reply(
        self, 
        id: str, 
        question: str, 
        sql: str, 
        data_sample: str
    ) -> AgentMessage:
        """
        Generate insights from data.
        """
        logger.debug(f"[{self.name}]: generating diagnosis for {id}")

        infer = dspy.ChainOfThought(DiagnosisSignature)
        
        try:
            # Add timeout handling capability if supported by dspy configuration or wrap with system timeout
            # For now, we rely on dspy/provider timeout settings but catch the errors gracefully
            response = infer(
                question=question, 
                sql=sql, 
                data_sample=data_sample
            )
            
            summary = response.summary
            key_points = response.key_points

            # Construct InsightSummary object to validate
            insight = InsightSummary(
                summary=summary,
                key_points=key_points.split("\n") if isinstance(key_points, str) else key_points
            )
            
            return AgentMessage(
                name=self.name,
                id=id,
                type="diagnosis",
                answer=insight.model_dump(),
                reason="",
                reasoning=getattr(response, "reasoning", "") or ""
            )
            
        except Exception as e:
            error_str = str(e).lower()
            is_timeout = "timeout" in error_str or "timed out" in error_str
            
            if is_timeout:
                logger.warning(f"[{self.name}] Diagnosis generation timed out. Returning minimal response.")
                reason = "Analysis timed out"
                summary = "Analysis took too long to generate. Please try again later."
            else:
                logger.error(f"[{self.name}] Failed to generate diagnosis: {e}")
                reason = str(e)
                summary = "Unable to generate insights due to an error."

            # Return empty/fallback
            return AgentMessage(
                name=self.name,
                id=id,
                type="diagnosis",
                answer={"summary": summary, "key_points": []},
                reason=reason,
                reasoning=""
            )
