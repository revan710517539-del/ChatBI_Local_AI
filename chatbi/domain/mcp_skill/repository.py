from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4


class MCPSkillRepository:
    def __init__(self) -> None:
        base = Path(os.getcwd()) / "runs"
        base.mkdir(parents=True, exist_ok=True)
        self.path = base / "mcp_skill_store.json"
        self._bootstrap()

    def _bootstrap(self) -> None:
        if self.path.exists():
            return
        now = datetime.utcnow().isoformat()
        self.save(
            {
                "mcp_servers": [
                    {
                        "id": str(uuid4()),
                        "name": "渠道消息MCP",
                        "endpoint": "http://localhost:9101/mcp/channel",
                        "description": "连接短信/企微/邮件通道（执行前需审批）",
                        "enabled": True,
                        "capabilities": ["send_message", "create_campaign", "sync_feedback"],
                        "created_at": now,
                        "updated_at": now,
                    },
                    {
                        "id": str(uuid4()),
                        "name": "外呼任务MCP",
                        "endpoint": "http://localhost:9102/mcp/call",
                        "description": "外呼任务下发与状态回收",
                        "enabled": False,
                        "capabilities": ["dispatch_task", "task_status"],
                        "created_at": now,
                        "updated_at": now,
                    },
                ],
                "skills": [
                    {
                        "id": str(uuid4()),
                        "name": "高风险客群预警",
                        "category": "risk",
                        "description": "逾期率/迁徙率异常时生成预警策略草案",
                        "enabled": True,
                        "trigger": "overdue_rate>0.02 or migration_rate>0.025",
                        "created_at": now,
                        "updated_at": now,
                    },
                    {
                        "id": str(uuid4()),
                        "name": "经营贷额度激活策略",
                        "category": "growth",
                        "description": "面向高授信低动支客群生成激活建议",
                        "enabled": True,
                        "trigger": "credit_utilization_rate<0.55",
                        "created_at": now,
                        "updated_at": now,
                    },
                ],
                "email_config": {
                    "sender": "",
                    "recipient": "",
                    "smtp_host": "",
                    "smtp_port": 587,
                    "smtp_user": "",
                    "smtp_password": "",
                    "use_tls": True,
                },
                "strategies": [],
            }
        )

    def load(self) -> dict[str, Any]:
        with self.path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def save(self, data: dict[str, Any]) -> None:
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
