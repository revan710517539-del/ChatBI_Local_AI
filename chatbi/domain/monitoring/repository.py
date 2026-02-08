from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4


class MonitoringRepository:
    def __init__(self) -> None:
        base = Path(os.getcwd()) / "runs"
        base.mkdir(parents=True, exist_ok=True)
        self.path = base / "monitoring_store.json"
        self._bootstrap()

    def _bootstrap(self) -> None:
        if self.path.exists():
            return

        now = datetime.utcnow().isoformat()
        self.save(
            {
                "rules": [
                    {
                        "id": str(uuid4()),
                        "name": "经营贷逾期率预警",
                        "metric_key": "bl_overdue_rate",
                        "operator": ">",
                        "threshold": 0.02,
                        "severity": "high",
                        "scope": "data",
                        "enabled": True,
                    },
                    {
                        "id": str(uuid4()),
                        "name": "消费贷迁徙率预警",
                        "metric_key": "cl_migration_rate",
                        "operator": ">",
                        "threshold": 0.03,
                        "severity": "high",
                        "scope": "data",
                        "enabled": True,
                    },
                    {
                        "id": str(uuid4()),
                        "name": "额度使用率偏低预警",
                        "metric_key": "bl_credit_utilization_rate",
                        "operator": "<",
                        "threshold": 0.58,
                        "severity": "medium",
                        "scope": "data",
                        "enabled": True,
                    },
                    {
                        "id": str(uuid4()),
                        "name": "市场合规热度预警",
                        "metric_key": "market_compliance_heat",
                        "operator": ">=",
                        "threshold": 6,
                        "severity": "medium",
                        "scope": "market",
                        "enabled": True,
                    },
                ],
                "diagnosis_config": {
                    "attribution_rules": [
                        {
                            "metric_key": "bl_overdue_rate",
                            "possible_causes": [
                                "经营贷存量客群现金流承压，短期还款能力下降",
                                "催收触达节奏偏后，M1阶段介入不足",
                            ],
                            "suggested_actions": [
                                "将高风险行业客群下调准入额度并提高首月监控频率",
                                "针对M1客群启动分层提醒与协商还款策略",
                            ],
                        },
                        {
                            "metric_key": "cl_migration_rate",
                            "possible_causes": [
                                "消费贷新客准入策略偏宽，风险客群渗透上升",
                                "免核/快审链路风险兜底不足",
                            ],
                            "suggested_actions": [
                                "收紧高风险渠道评分阈值并缩短预授信有效期",
                                "在电核前增加反欺诈规则校验",
                            ],
                        },
                        {
                            "metric_key": "bl_credit_utilization_rate",
                            "possible_causes": [
                                "高授信客群激活动作不足",
                                "经营贷利率或活动权益对目标客群吸引力不足",
                            ],
                            "suggested_actions": [
                                "对低动支优质客群实施期限优惠+场景化动支活动",
                                "联动客户经理对授信未动支客群开展定向触达",
                            ],
                        },
                    ],
                    "default_actions": [
                        "触发异常后24小时内完成口径复核与客群分层复盘",
                        "策略上线前先进入A/B实验，次周复盘归因效果",
                    ],
                },
                "email_config": {
                    "sender": "",
                    "recipient": "",
                    "smtp_host": "",
                    "smtp_port": 587,
                    "smtp_user": "",
                    "smtp_password": "",
                    "use_tls": True,
                },
                "latest_snapshot": {
                    "collected_at": now,
                    "metrics": {},
                },
                "alerts": [],
            }
        )

    def load(self) -> dict[str, Any]:
        with self.path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        data.setdefault("rules", [])
        data.setdefault("diagnosis_config", {})
        data.setdefault("email_config", {})
        data.setdefault("latest_snapshot", {"collected_at": None, "metrics": {}})
        data.setdefault("alerts", [])
        return data

    def save(self, data: dict[str, Any]) -> None:
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
