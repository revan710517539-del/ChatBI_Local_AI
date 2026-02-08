from __future__ import annotations

import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from typing import Any
from uuid import uuid4

from chatbi.domain.market_watch.service import MarketWatchService
from chatbi.domain.monitoring.dtos import (
    DiagnosisConfigUpdateDTO,
    MonitoringEmailConfigUpdateDTO,
    MonitoringRuleConfigUpdateDTO,
)
from chatbi.domain.monitoring.repository import MonitoringRepository


class MonitoringService:
    def __init__(self, repo: MonitoringRepository | None = None) -> None:
        self.repo = repo or MonitoringRepository()

    def list_rules(self) -> list[dict[str, Any]]:
        return self.repo.load().get("rules", [])

    def update_rules(self, payload: MonitoringRuleConfigUpdateDTO) -> list[dict[str, Any]]:
        data = self.repo.load()
        data["rules"] = [x.model_dump() for x in payload.rules]
        self.repo.save(data)
        return data["rules"]

    def get_diagnosis_config(self) -> dict[str, Any]:
        return self.repo.load().get("diagnosis_config", {})

    def update_diagnosis_config(self, payload: DiagnosisConfigUpdateDTO) -> dict[str, Any]:
        data = self.repo.load()
        data["diagnosis_config"] = payload.model_dump()
        self.repo.save(data)
        return data["diagnosis_config"]

    def get_email_config(self) -> dict[str, Any]:
        return self.repo.load().get("email_config", {})

    def update_email_config(self, payload: MonitoringEmailConfigUpdateDTO) -> dict[str, Any]:
        data = self.repo.load()
        cfg = data.setdefault("email_config", {})
        cfg.update(payload.model_dump(exclude_unset=True))
        self.repo.save(data)
        return cfg

    @staticmethod
    def _now() -> str:
        return datetime.utcnow().isoformat()

    def _collect_metrics(self) -> dict[str, float]:
        now = datetime.utcnow()
        minute_shift = ((now.minute % 6) - 3) / 1000.0

        metrics = {
            "bl_overdue_rate": round(0.0208 + minute_shift, 6),
            "cl_overdue_rate": round(0.0221 + minute_shift * 0.8, 6),
            "bl_migration_rate": round(0.027 + minute_shift * 0.9, 6),
            "cl_migration_rate": round(0.031 + minute_shift, 6),
            "bl_credit_utilization_rate": round(0.562 - minute_shift * 0.7, 6),
            "cl_credit_utilization_rate": round(0.641 - minute_shift * 0.5, 6),
            "raroc": round(0.109 + minute_shift * 0.4, 6),
            "cost_income_ratio": round(0.337 + minute_shift * 0.6, 6),
        }

        try:
            market = MarketWatchService().market_analysis(limit=8, force_refresh=False)
            pulse = market.get("market_pulse", {})
            metrics["market_risk_heat"] = float(pulse.get("risk_heat") or 0)
            metrics["market_growth_heat"] = float(pulse.get("growth_heat") or 0)
            metrics["market_compliance_heat"] = float(pulse.get("compliance_heat") or 0)
        except Exception:
            metrics["market_risk_heat"] = 4.0
            metrics["market_growth_heat"] = 5.0
            metrics["market_compliance_heat"] = 4.0

        return metrics

    @staticmethod
    def _match(value: float, operator: str, threshold: float) -> bool:
        if operator == ">":
            return value > threshold
        if operator == ">=":
            return value >= threshold
        if operator == "<":
            return value < threshold
        if operator == "<=":
            return value <= threshold
        if operator == "==":
            return value == threshold
        return False

    @staticmethod
    def _alert_key(alert: dict[str, Any]) -> str:
        day = (alert.get("triggered_at") or "")[:10]
        return f"{alert.get('rule_id')}|{day}|{alert.get('metric_key')}"

    def _build_diagnosis(self, metric_key: str, value: float, threshold: float) -> dict[str, Any]:
        cfg = self.get_diagnosis_config()
        rules = cfg.get("attribution_rules", [])
        matched = next((x for x in rules if x.get("metric_key") == metric_key), None)

        possible_causes = (matched or {}).get("possible_causes") or [
            "指标出现偏离，需核验渠道、客群和口径是否发生结构变化。"
        ]
        suggested_actions = (matched or {}).get("suggested_actions") or cfg.get("default_actions") or [
            "建议先执行口径复核，再进入A/B实验验证策略效果。"
        ]
        summary = f"{metric_key} 当前值 {value}，超出阈值 {threshold}。"

        return {
            "summary": summary,
            "possible_causes": possible_causes,
            "suggested_actions": suggested_actions,
        }

    def get_snapshot(self) -> dict[str, Any]:
        data = self.repo.load()
        metrics = self._collect_metrics()
        snap = {
            "collected_at": self._now(),
            "metrics": metrics,
        }
        data["latest_snapshot"] = snap
        self.repo.save(data)
        return snap

    def _send_email(self, recipient: str, subject: str, body: str) -> tuple[bool, str]:
        data = self.repo.load()
        cfg = data.get("email_config", {})
        sender = cfg.get("sender")
        host = cfg.get("smtp_host")
        port = int(cfg.get("smtp_port") or 587)
        user = cfg.get("smtp_user")
        password = cfg.get("smtp_password")
        use_tls = bool(cfg.get("use_tls", True))

        if not (sender and recipient and host and user and password):
            return False, "邮件配置不完整，当前为模拟提醒。"

        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = recipient

        with smtplib.SMTP(host, port, timeout=20) as server:
            if use_tls:
                server.starttls()
            server.login(user, password)
            server.sendmail(sender, [recipient], msg.as_string())
        return True, "发送成功"

    def check_alerts(self, send_email: bool = True) -> dict[str, Any]:
        data = self.repo.load()
        metrics = self._collect_metrics()
        snapshot = {
            "collected_at": self._now(),
            "metrics": metrics,
        }
        data["latest_snapshot"] = snapshot

        alerts = data.setdefault("alerts", [])
        active_keys = {
            self._alert_key(x)
            for x in alerts
            if x.get("status") in {"new", "notified"}
        }
        new_alerts: list[dict[str, Any]] = []

        for rule in data.get("rules", []):
            if not rule.get("enabled", True):
                continue
            metric_key = str(rule.get("metric_key") or "")
            if metric_key not in metrics:
                continue

            value = float(metrics[metric_key])
            operator = str(rule.get("operator") or ">")
            threshold = float(rule.get("threshold") or 0)
            if not self._match(value, operator, threshold):
                continue

            alert = {
                "id": str(uuid4()),
                "rule_id": rule.get("id"),
                "rule_name": rule.get("name"),
                "metric_key": metric_key,
                "operator": operator,
                "threshold": threshold,
                "current_value": value,
                "severity": rule.get("severity", "medium"),
                "scope": rule.get("scope", "data"),
                "status": "new",
                "triggered_at": self._now(),
                "ack_note": None,
                "diagnosis": self._build_diagnosis(metric_key, value, threshold),
                "notification": {
                    "sent": False,
                    "sent_at": None,
                    "recipient": None,
                    "result": None,
                },
            }

            key = self._alert_key(alert)
            if key in active_keys:
                continue

            if send_email:
                cfg = data.get("email_config", {})
                recipient = cfg.get("recipient") or ""
                subject = f"[SmartBI监控告警] {alert['rule_name']}"
                body = "\n".join(
                    [
                        f"触发时间: {alert['triggered_at']}",
                        f"规则: {alert['rule_name']}",
                        f"指标: {alert['metric_key']}",
                        f"当前值: {alert['current_value']}",
                        f"阈值: {alert['operator']} {alert['threshold']}",
                        "",
                        f"归因: {alert['diagnosis']['summary']}",
                        "可能原因:",
                        *[f"- {x}" for x in alert["diagnosis"].get("possible_causes", [])],
                        "建议动作:",
                        *[f"- {x}" for x in alert["diagnosis"].get("suggested_actions", [])],
                    ]
                )
                ok, reason = self._send_email(recipient, subject, body)
                alert["notification"] = {
                    "sent": ok,
                    "sent_at": self._now(),
                    "recipient": recipient,
                    "result": reason,
                }
                alert["status"] = "notified" if ok else "new"

            alerts.append(alert)
            new_alerts.append(alert)

        data["alerts"] = alerts[-1000:]
        self.repo.save(data)

        return {
            "snapshot": snapshot,
            "new_alerts": new_alerts,
            "active_alerts": [x for x in reversed(data["alerts"]) if x.get("status") in {"new", "notified"}],
        }

    def list_alerts(self, limit: int = 200, status: str | None = None) -> list[dict[str, Any]]:
        data = self.repo.load()
        items = list(reversed(data.get("alerts", [])))
        if status:
            items = [x for x in items if x.get("status") == status]
        return items[:limit]

    def acknowledge_alert(self, alert_id: str, note: str | None = None) -> dict[str, Any]:
        data = self.repo.load()
        for item in data.get("alerts", []):
            if item.get("id") != alert_id:
                continue
            item["status"] = "acknowledged"
            item["ack_note"] = note
            item["ack_at"] = self._now()
            self.repo.save(data)
            return item
        raise ValueError(f"Alert not found: {alert_id}")

    def send_alert_email(self, alert_id: str) -> dict[str, Any]:
        data = self.repo.load()
        cfg = data.get("email_config", {})
        recipient = cfg.get("recipient") or ""

        for item in data.get("alerts", []):
            if item.get("id") != alert_id:
                continue

            subject = f"[SmartBI告警补发] {item.get('rule_name')}"
            body = "\n".join(
                [
                    f"触发时间: {item.get('triggered_at')}",
                    f"规则: {item.get('rule_name')}",
                    f"指标: {item.get('metric_key')}",
                    f"当前值: {item.get('current_value')}",
                    f"阈值: {item.get('operator')} {item.get('threshold')}",
                    "",
                    f"归因: {(item.get('diagnosis') or {}).get('summary')}",
                ]
            )
            ok, reason = self._send_email(recipient, subject, body)
            item["notification"] = {
                "sent": ok,
                "sent_at": self._now(),
                "recipient": recipient,
                "result": reason,
            }
            if ok:
                item["status"] = "notified"
            self.repo.save(data)
            return item

        raise ValueError(f"Alert not found: {alert_id}")
