from __future__ import annotations

from pydantic import BaseModel, Field


class MonitoringRuleDTO(BaseModel):
    id: str
    name: str
    metric_key: str
    operator: str = ">"
    threshold: float
    severity: str = "medium"
    scope: str = "data"
    enabled: bool = True


class MonitoringRuleConfigUpdateDTO(BaseModel):
    rules: list[MonitoringRuleDTO] = Field(default_factory=list)


class DiagnosisConfigUpdateDTO(BaseModel):
    attribution_rules: list[dict] = Field(default_factory=list)
    default_actions: list[str] = Field(default_factory=list)


class MonitoringEmailConfigUpdateDTO(BaseModel):
    sender: str | None = None
    recipient: str | None = None
    smtp_host: str | None = None
    smtp_port: int | None = None
    smtp_user: str | None = None
    smtp_password: str | None = None
    use_tls: bool | None = None


class MonitoringCheckDTO(BaseModel):
    send_email: bool = True


class AlertAckDTO(BaseModel):
    note: str | None = None
