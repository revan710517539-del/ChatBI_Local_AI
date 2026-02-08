from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4


class StrategyLabRepository:
    def __init__(self) -> None:
        base = Path(os.getcwd()) / "runs"
        base.mkdir(parents=True, exist_ok=True)
        self.path = base / "strategy_lab_store.json"
        self._bootstrap()

    def _trend_rows(self, loan_type: str, days: int = 12) -> list[dict[str, Any]]:
        base_cr = 0.185 if loan_type == "consumer" else 0.152
        base_od = 0.023 if loan_type == "consumer" else 0.019
        base_raroc = 0.103 if loan_type == "consumer" else 0.111
        start = datetime.utcnow() - timedelta(days=days - 1)
        rows: list[dict[str, Any]] = []
        for i in range(days):
            d = (start + timedelta(days=i)).strftime("%Y-%m-%d")
            swing = ((i % 5) - 2) * 0.0015
            rows.append(
                {
                    "date": d,
                    "conversion_control": round(base_cr + swing, 4),
                    "conversion_treatment": round(base_cr + 0.012 + swing * 0.9, 4),
                    "overdue_control": round(base_od + swing * 0.6, 4),
                    "overdue_treatment": round(base_od - 0.002 + swing * 0.5, 4),
                    "raroc_control": round(base_raroc + swing * 1.4, 4),
                    "raroc_treatment": round(base_raroc + 0.006 + swing * 1.2, 4),
                }
            )
        return rows

    def _bootstrap(self) -> None:
        if self.path.exists():
            return
        now = datetime.utcnow().isoformat()
        experiments = [
            {
                "id": str(uuid4()),
                "name": "消费贷M1预警触达A/B",
                "strategy_id": "mock-strategy-consumer",
                "loan_type": "consumer",
                "status": "completed",
                "channel": "短信+外呼",
                "segment": "M1预警客群",
                "sample_size_control": 4200,
                "sample_size_treatment": 4300,
                "start_date": (datetime.utcnow() - timedelta(days=20)).strftime("%Y-%m-%d"),
                "end_date": (datetime.utcnow() - timedelta(days=6)).strftime("%Y-%m-%d"),
                "metrics": {
                    "conversion_rate": {"control": 0.187, "treatment": 0.201, "uplift": 0.014},
                    "overdue_rate": {"control": 0.026, "treatment": 0.022, "uplift": -0.004},
                    "raroc": {"control": 0.101, "treatment": 0.108, "uplift": 0.007},
                    "avg_balance": {"control": 6.2, "treatment": 6.6, "uplift": 0.4},
                },
                "attribution": [
                    {"factor": "策略文案分层", "contribution": 0.34, "evidence": "高风险客群回访率提升"},
                    {"factor": "触达节奏调整", "contribution": 0.29, "evidence": "T+1/T+3双触达改善"},
                    {"factor": "准入限额收敛", "contribution": 0.21, "evidence": "新增高风险敞口下降"},
                    {"factor": "渠道结构优化", "contribution": 0.16, "evidence": "外呼命中率提升"},
                ],
                "trend": self._trend_rows("consumer", 12),
                "created_at": now,
                "updated_at": now,
            },
            {
                "id": str(uuid4()),
                "name": "经营贷低动支激活A/B",
                "strategy_id": "mock-strategy-business",
                "loan_type": "business",
                "status": "running",
                "channel": "APP Push+客户经理",
                "segment": "高授信低动支",
                "sample_size_control": 2800,
                "sample_size_treatment": 2900,
                "start_date": (datetime.utcnow() - timedelta(days=10)).strftime("%Y-%m-%d"),
                "end_date": None,
                "metrics": {
                    "conversion_rate": {"control": 0.146, "treatment": 0.157, "uplift": 0.011},
                    "overdue_rate": {"control": 0.019, "treatment": 0.018, "uplift": -0.001},
                    "raroc": {"control": 0.112, "treatment": 0.117, "uplift": 0.005},
                    "avg_balance": {"control": 18.2, "treatment": 19.1, "uplift": 0.9},
                },
                "attribution": [
                    {"factor": "额度激活文案", "contribution": 0.31, "evidence": "激活动支率提高"},
                    {"factor": "客户经理跟进", "contribution": 0.27, "evidence": "高价值客户触达率上升"},
                    {"factor": "RAG知识库指引", "contribution": 0.22, "evidence": "经营场景命中度提高"},
                    {"factor": "渠道协同", "contribution": 0.20, "evidence": "APP与人工链路闭环"},
                ],
                "trend": self._trend_rows("business", 12),
                "created_at": now,
                "updated_at": now,
            },
        ]
        self.save({"experiments": experiments})

    def load(self) -> dict[str, Any]:
        with self.path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        data.setdefault("experiments", [])
        return data

    def save(self, data: dict[str, Any]) -> None:
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
