from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4


class PlanningRepository:
    def __init__(self) -> None:
        base = Path(os.getcwd()) / "runs"
        base.mkdir(parents=True, exist_ok=True)
        self.path = base / "planning_store.json"
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
                        "name": "消费贷经营诊断拆解规则",
                        "enabled": True,
                        "match_keywords": ["消费贷", "转化", "逾期", "客群"],
                        "split_template": [
                            "漏斗诊断",
                            "客群分层",
                            "风险收益联动",
                            "策略动作建议",
                        ],
                        "preferred_agents": [
                            "消费贷风险分析Agent",
                            "贷款经营分析Agent",
                        ],
                        "toolchain": {"sql": True, "rag": True, "rule_validation": True},
                    },
                    {
                        "id": str(uuid4()),
                        "name": "经营贷专项分析拆解规则",
                        "enabled": True,
                        "match_keywords": ["经营贷", "额度", "迁徙", "RAROC"],
                        "split_template": [
                            "授信与额度使用",
                            "动支与留存表现",
                            "迁徙与逾期质量",
                            "策略执行排程",
                        ],
                        "preferred_agents": ["贷款经营分析Agent"],
                        "toolchain": {"sql": True, "rag": True, "rule_validation": True},
                    },
                ],
                "chains": [
                    {
                        "id": str(uuid4()),
                        "name": "SmartBI A2A 标准协作链",
                        "enabled": True,
                        "mode": "a2a_dispatch",
                        "steps": [
                            {"name": "Planner", "role": "任务拆分与优先级", "handoff_to": "Data Analyst Agent"},
                            {"name": "Data Analyst Agent", "role": "SQL+指标计算", "handoff_to": "Risk Agent"},
                            {"name": "Risk Agent", "role": "风险收益校验", "handoff_to": "Strategy Agent"},
                            {"name": "Strategy Agent", "role": "策略建议与渠道动作草案", "handoff_to": "Approval Agent"},
                            {"name": "Approval Agent", "role": "邮件发送与回邮确认", "handoff_to": "Executor Agent"},
                        ],
                    }
                ],
                "plan_history": [],
                "execution_logs": [],
                "executions": [],
                "updated_at": now,
            }
        )

    def load(self) -> dict[str, Any]:
        with self.path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        data.setdefault("rules", [])
        data.setdefault("chains", [])
        data.setdefault("plan_history", [])
        data.setdefault("execution_logs", [])
        data.setdefault("executions", [])
        return data

    def save(self, data: dict[str, Any]) -> None:
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
