from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4


class AgentBuilderRepository:
    def __init__(self) -> None:
        self.base_dir = Path(os.getcwd()) / "runs"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.path = self.base_dir / "agent_profiles.json"
        self._bootstrap()

    def _bootstrap(self) -> None:
        if self.path.exists():
            return
        now = datetime.utcnow().isoformat()
        data = {
            "profiles": [
                {
                    "id": str(uuid4()),
                    "name": "贷款经营分析Agent",
                    "scene": "business_loan_ops",
                    "description": "经营贷全链路经营分析与风险监测",
                    "system_prompt": "你是经营贷数据分析专家，重点关注授信、动支、还款、逾期与迁徙。",
                    "llm_source_id": None,
                    "enable_rag": True,
                    "enable_sql_tool": True,
                    "enable_rule_validation": True,
                    "created_at": now,
                    "updated_at": now,
                },
                {
                    "id": str(uuid4()),
                    "name": "消费贷风险分析Agent",
                    "scene": "consumer_loan_risk",
                    "description": "消费贷客群结构、转化漏斗与风险质量分析",
                    "system_prompt": "你是消费贷风险分析专家，输出结论时必须同时给经营建议与风险提示。",
                    "llm_source_id": None,
                    "enable_rag": True,
                    "enable_sql_tool": True,
                    "enable_rule_validation": True,
                    "created_at": now,
                    "updated_at": now,
                },
            ],
            "execution_logs": {},
        }
        self.save(data)

    def load(self) -> dict[str, Any]:
        with self.path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def save(self, data: dict[str, Any]) -> None:
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
