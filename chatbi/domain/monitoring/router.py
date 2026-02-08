from __future__ import annotations

from fastapi import APIRouter, Query

from chatbi.domain.monitoring.dtos import (
    AlertAckDTO,
    DiagnosisConfigUpdateDTO,
    MonitoringCheckDTO,
    MonitoringEmailConfigUpdateDTO,
    MonitoringRuleConfigUpdateDTO,
)
from chatbi.domain.monitoring.service import MonitoringService
from chatbi.middleware.standard_response import StandardResponse

router = APIRouter(prefix="/api/v1/monitoring", tags=["Monitoring"])


@router.get("/rule-config")
async def get_rule_config() -> StandardResponse[list[dict]]:
    service = MonitoringService()
    return StandardResponse(status="success", message="Monitoring rules fetched", data=service.list_rules())


@router.put("/rule-config")
async def update_rule_config(payload: MonitoringRuleConfigUpdateDTO) -> StandardResponse[list[dict]]:
    service = MonitoringService()
    return StandardResponse(status="success", message="Monitoring rules updated", data=service.update_rules(payload))


@router.get("/diagnosis-config")
async def get_diagnosis_config() -> StandardResponse[dict]:
    service = MonitoringService()
    return StandardResponse(
        status="success",
        message="Diagnosis config fetched",
        data=service.get_diagnosis_config(),
    )


@router.put("/diagnosis-config")
async def update_diagnosis_config(payload: DiagnosisConfigUpdateDTO) -> StandardResponse[dict]:
    service = MonitoringService()
    return StandardResponse(
        status="success",
        message="Diagnosis config updated",
        data=service.update_diagnosis_config(payload),
    )


@router.get("/email-config")
async def get_email_config() -> StandardResponse[dict]:
    service = MonitoringService()
    return StandardResponse(status="success", message="Email config fetched", data=service.get_email_config())


@router.put("/email-config")
async def update_email_config(payload: MonitoringEmailConfigUpdateDTO) -> StandardResponse[dict]:
    service = MonitoringService()
    return StandardResponse(status="success", message="Email config updated", data=service.update_email_config(payload))


@router.get("/snapshot")
async def get_snapshot() -> StandardResponse[dict]:
    service = MonitoringService()
    return StandardResponse(status="success", message="Monitoring snapshot fetched", data=service.get_snapshot())


@router.post("/alerts/check")
async def check_alerts(payload: MonitoringCheckDTO) -> StandardResponse[dict]:
    service = MonitoringService()
    return StandardResponse(
        status="success",
        message="Monitoring check completed",
        data=service.check_alerts(send_email=payload.send_email),
    )


@router.get("/alerts")
async def list_alerts(
    limit: int = Query(200, ge=1, le=1000),
    status: str | None = Query(None),
) -> StandardResponse[list[dict]]:
    service = MonitoringService()
    return StandardResponse(
        status="success",
        message="Alerts fetched",
        data=service.list_alerts(limit=limit, status=status),
    )


@router.post("/alerts/{alert_id}/ack")
async def ack_alert(alert_id: str, payload: AlertAckDTO) -> StandardResponse[dict]:
    service = MonitoringService()
    return StandardResponse(
        status="success",
        message="Alert acknowledged",
        data=service.acknowledge_alert(alert_id=alert_id, note=payload.note),
    )


@router.post("/alerts/{alert_id}/send-email")
async def send_alert_email(alert_id: str) -> StandardResponse[dict]:
    service = MonitoringService()
    return StandardResponse(
        status="success",
        message="Alert email sent",
        data=service.send_alert_email(alert_id),
    )
