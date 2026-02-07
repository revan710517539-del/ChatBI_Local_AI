import dspy
from loguru import logger

from chatbi.agent.agent_message import (
    AgentMessage,
)
from chatbi.agent.llm import LLM
from chatbi.agent.prompts.sql_prompt import get_sql_prompt, get_correction_prompt

dspy.enable_logging()


class SqlSignature(dspy.Signature):
    """Signature for the text2sql method."""

    context = dspy.InputField(desc="The context of the question, e.g. table schema.")
    question = dspy.InputField()
    answer = dspy.OutputField(desc="The PostgreSQL SQL query, do not use markdown.")
    reason = dspy.OutputField()


class SqlSignatureV2(dspy.Signature):
    """Signature for the text2sql method."""

    messages: list[dict] = dspy.InputField()
    answer = dspy.OutputField(desc="The PostgreSQL SQL query, do not use markdown.")
    reason = dspy.OutputField()


class SqlAgent:
    def __init__(self, name="SqlAgent"):
        self.name = name

        # initialize the LLM model
        LLM["openai"].get_model()

    def reply(
        self,
        id: str,
        question: str,
        table_schema,
        previous_sql: str = None,
        error_message: str = None,
        system_prompt: str | None = None,
    ) -> AgentMessage:
        logger.debug(f"[{self.name}]: infer sql (correction={bool(error_message)})")

        infer = dspy.ChainOfThought(SqlSignatureV2)
        if error_message and previous_sql:
            messages = get_correction_prompt(
                question=question,
                wrong_sql=previous_sql,
                error_message=error_message,
                table_schema=table_schema,
            )
        else:
            messages = get_sql_prompt(
                question=question,
                table_schema=table_schema,
                initial_prompt=system_prompt,
            )

        logger.debug(f"[{self.name}]: messages: {messages}")
        # response = self.model.llm(messages=messages)
        response = infer(messages=messages)

        answer = response["answer"]
        reason = response["reason"]
        reasoning = response["reasoning"]

        logger.debug(f"[{self.name}]: response: {response}")

        return AgentMessage(
            name=self.name,
            id=id,
            type="sql",
            answer=answer,
            reason=reason,
            reasoning=reasoning,
        )
