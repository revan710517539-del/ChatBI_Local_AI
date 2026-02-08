from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any


class CustomerInsightRepository:
    def __init__(self) -> None:
        base = Path(os.getcwd()) / "runs"
        base.mkdir(parents=True, exist_ok=True)
        self.path = base / "customer_insight_store.json"
        self._bootstrap()

    def _bootstrap(self) -> None:
        if self.path.exists():
            return
        now = datetime.utcnow().isoformat()
        data = {
            "customers": [
                {
                    "customer_id": "CUST1001",
                    "name": "王海峰",
                    "city": "杭州",
                    "loan_type": "经营贷",
                    "credit_limit": 680000,
                    "used_limit": 420000,
                    "utilization_rate": 0.62,
                    "risk_level": "中",
                    "overdue_days": 0,
                    "migration_tag": "M0稳定",
                    "income_estimate": 56000,
                    "industry": "批发零售",
                    "next_best_action": "推荐备货季增额+分期利率券",
                    "updated_at": now,
                },
                {
                    "customer_id": "CUST2008",
                    "name": "李晓晴",
                    "city": "深圳",
                    "loan_type": "消费贷",
                    "credit_limit": 180000,
                    "used_limit": 145000,
                    "utilization_rate": 0.81,
                    "risk_level": "中高",
                    "overdue_days": 3,
                    "migration_tag": "M1预警",
                    "income_estimate": 24000,
                    "industry": "互联网",
                    "next_best_action": "触发还款提醒并建议账单重排",
                    "updated_at": now,
                },
            ],
            "segments": [
                {
                    "segment_id": "SEG_BIZ_HIGH_GROWTH",
                    "name": "经营贷-高成长商户",
                    "size": 3280,
                    "loan_type": "经营贷",
                    "avg_credit_limit": 520000,
                    "avg_utilization_rate": 0.58,
                    "overdue_rate": 0.013,
                    "raroc": 0.124,
                    "insight": "增长潜力高、风险可控，适合做额度激活与供应链联动产品。",
                },
                {
                    "segment_id": "SEG_CONS_RISK_EDGE",
                    "name": "消费贷-风险边缘客群",
                    "size": 5860,
                    "loan_type": "消费贷",
                    "avg_credit_limit": 120000,
                    "avg_utilization_rate": 0.79,
                    "overdue_rate": 0.029,
                    "raroc": 0.095,
                    "insight": "用信活跃但风险上升，宜采用分层催收+额度弹性控制。",
                },
            ],
        }
        self.save(data)

    def load(self) -> dict[str, Any]:
        with self.path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def save(self, data: dict[str, Any]) -> None:
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
