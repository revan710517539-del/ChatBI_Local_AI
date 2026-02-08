from __future__ import annotations

import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from typing import Any
from uuid import uuid4

from chatbi.domain.mcp_skill.dtos import (
    EmailConfigUpdateDTO,
    MCPServerCreateDTO,
    MCPServerUpdateDTO,
    SkillCreateDTO,
    SkillUpdateDTO,
    StrategyGenerateDTO,
)
from chatbi.domain.mcp_skill.repository import MCPSkillRepository


class MCPSkillService:
    def __init__(self, repo: MCPSkillRepository | None = None) -> None:
        self.repo = repo or MCPSkillRepository()

    def list_mcp_servers(self) -> list[dict[str, Any]]:
        return self.repo.load().get("mcp_servers", [])

    def create_mcp_server(self, payload: MCPServerCreateDTO) -> dict[str, Any]:
        data = self.repo.load()
        now = datetime.utcnow().isoformat()
        item = {"id": str(uuid4()), **payload.model_dump(), "created_at": now, "updated_at": now}
        data.setdefault("mcp_servers", []).append(item)
        self.repo.save(data)
        return item

    def update_mcp_server(self, server_id: str, payload: MCPServerUpdateDTO) -> dict[str, Any]:
        data = self.repo.load()
        for item in data.setdefault("mcp_servers", []):
            if item["id"] != server_id:
                continue
            item.update(payload.model_dump(exclude_unset=True))
            item["updated_at"] = datetime.utcnow().isoformat()
            self.repo.save(data)
            return item
        raise ValueError(f"MCP server not found: {server_id}")

    def delete_mcp_server(self, server_id: str) -> None:
        data = self.repo.load()
        old = len(data.setdefault("mcp_servers", []))
        data["mcp_servers"] = [x for x in data["mcp_servers"] if x["id"] != server_id]
        if len(data["mcp_servers"]) == old:
            raise ValueError(f"MCP server not found: {server_id}")
        self.repo.save(data)

    def list_skills(self) -> list[dict[str, Any]]:
        return self.repo.load().get("skills", [])

    def create_skill(self, payload: SkillCreateDTO) -> dict[str, Any]:
        data = self.repo.load()
        now = datetime.utcnow().isoformat()
        item = {"id": str(uuid4()), **payload.model_dump(), "created_at": now, "updated_at": now}
        data.setdefault("skills", []).append(item)
        self.repo.save(data)
        return item

    def update_skill(self, skill_id: str, payload: SkillUpdateDTO) -> dict[str, Any]:
        data = self.repo.load()
        for item in data.setdefault("skills", []):
            if item["id"] != skill_id:
                continue
            item.update(payload.model_dump(exclude_unset=True))
            item["updated_at"] = datetime.utcnow().isoformat()
            self.repo.save(data)
            return item
        raise ValueError(f"Skill not found: {skill_id}")

    def delete_skill(self, skill_id: str) -> None:
        data = self.repo.load()
        old = len(data.setdefault("skills", []))
        data["skills"] = [x for x in data["skills"] if x["id"] != skill_id]
        if len(data["skills"]) == old:
            raise ValueError(f"Skill not found: {skill_id}")
        self.repo.save(data)

    def get_email_config(self) -> dict[str, Any]:
        return self.repo.load().get("email_config", {})

    def update_email_config(self, payload: EmailConfigUpdateDTO) -> dict[str, Any]:
        data = self.repo.load()
        cfg = data.setdefault("email_config", {})
        cfg.update(payload.model_dump(exclude_unset=True))
        self.repo.save(data)
        return cfg

    @staticmethod
    def _strategy_template(topic: str, loan_type: str, kpi_snapshot: dict[str, Any]) -> dict[str, Any]:
        if not kpi_snapshot:
            if loan_type == "business":
                kpi_snapshot = {
                    "overdue_rate": 0.018,
                    "migration_rate_m1_m3": 0.026,
                    "credit_utilization_rate": 0.67,
                    "raroc": 0.11,
                }
            elif loan_type == "consumer":
                kpi_snapshot = {
                    "overdue_rate": 0.022,
                    "migration_rate_m1_m3": 0.026,
                    "credit_utilization_rate": 0.68,
                    "raroc": 0.109,
                }
            else:
                kpi_snapshot = {
                    "overdue_rate": 0.02,
                    "migration_rate_m1_m3": 0.026,
                    "credit_utilization_rate": 0.675,
                    "raroc": 0.109,
                }

        evidence = [
            f"当前逾期率={kpi_snapshot.get('overdue_rate')}",
            f"迁徙率(M1->M3)={kpi_snapshot.get('migration_rate_m1_m3')}",
            f"额度使用率={kpi_snapshot.get('credit_utilization_rate')}",
            f"风险收益比(RAROC)={kpi_snapshot.get('raroc')}",
        ]

        actions = [
            {
                "channel": "APP Push + 企微",
                "target": "高授信低动支客群",
                "action": "额度激活+利率券组合策略",
                "guardrail": "排除近30天M2+客户",
            },
            {
                "channel": "外呼",
                "target": "还款意愿下降客群",
                "action": "分层还款提醒+账单重排建议",
                "guardrail": "先审批后下发，回收触达效果",
            },
        ]

        return {
            "topic": topic,
            "loan_type": loan_type,
            "summary": "先稳风险、再提转化，在授信-动支-还款链路形成闭环。",
            "evidence": evidence,
            "actions": actions,
            "expected_impact": {
                "overdue_rate": "下降0.15~0.3pct",
                "credit_utilization_rate": "提升2~4pct",
                "raroc": "提升0.5~1.2pct",
            },
        }

    def generate_strategy(self, payload: StrategyGenerateDTO) -> dict[str, Any]:
        data = self.repo.load()
        now = datetime.utcnow().isoformat()
        strategy = {
            "id": str(uuid4()),
            "status": "draft",
            "approval": {
                "require_email_reply": True,
                "reply_status": "pending",
                "approved_at": None,
                "reply_text": None,
            },
            "content": self._strategy_template(payload.topic, payload.loan_type, payload.kpi_snapshot),
            "audience": payload.audience,
            "created_at": now,
            "updated_at": now,
            "mail": {
                "sent": False,
                "sent_at": None,
                "recipient": None,
                "message_id": None,
            },
            "execution": {
                "executed": False,
                "executed_at": None,
                "result": None,
            },
            "collaboration": [],
        }
        data.setdefault("strategies", []).append(strategy)
        self.repo.save(data)
        return strategy

    @staticmethod
    def _action_from_discussion(text: str) -> dict[str, Any] | None:
        content = text.lower()
        if "逾期" in text or "风险" in text or "m1" in content or "m2" in content:
            return {
                "channel": "短信 + 外呼",
                "target": "近30天风险上升客群",
                "action": "增强还款提醒频率并提供分层协商方案",
                "guardrail": "排除投诉高敏客群，控制触达频率",
            }
        if "转化" in text or "获客" in text or "动支" in text:
            return {
                "channel": "APP Push + 企微",
                "target": "授信通过未动支客群",
                "action": "限时动支激励与场景化额度使用引导",
                "guardrail": "保留风险门槛，不做高风险客群强刺激",
            }
        return None

    def refine_strategy(self, strategy_id: str, discussion: str, operator: str = "human") -> dict[str, Any]:
        data = self.repo.load()
        for item in data.get("strategies", []):
            if item["id"] != strategy_id:
                continue

            content = item.setdefault("content", {})
            summary = str(content.get("summary") or "")
            content["summary"] = (
                f"{summary} | 协同调整: {discussion[:160]}"
                if summary
                else f"协同调整: {discussion[:160]}"
            )

            collab = item.setdefault("collaboration", [])
            collab.append(
                {
                    "ts": datetime.utcnow().isoformat(),
                    "operator": operator,
                    "discussion": discussion,
                }
            )
            item["collaboration"] = collab[-100:]

            suggested = self._action_from_discussion(discussion)
            if suggested:
                actions = content.setdefault("actions", [])
                actions.append(suggested)
                content["actions"] = actions[-10:]

            evidence = content.setdefault("evidence", [])
            evidence.append(f"协同讨论输入: {discussion[:80]}")
            content["evidence"] = evidence[-12:]

            item["status"] = "revised"
            item["updated_at"] = datetime.utcnow().isoformat()
            self.repo.save(data)
            return item
        raise ValueError(f"Strategy not found: {strategy_id}")

    def list_strategies(self, limit: int = 100) -> list[dict[str, Any]]:
        data = self.repo.load()
        items = data.get("strategies", [])
        return list(reversed(items[-limit:]))

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
            return False, "邮件配置不完整，已进入模拟发送模式。"

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

    def send_strategy_email(self, strategy_id: str) -> dict[str, Any]:
        data = self.repo.load()
        cfg = data.get("email_config", {})
        recipient = cfg.get("recipient")
        for item in data.get("strategies", []):
            if item["id"] != strategy_id:
                continue
            content = item.get("content", {})
            subject = f"[SmartBI策略审批] {content.get('topic', '贷款策略建议')}"
            body = (
                "请审批以下策略，回复 AGREE 才会执行。\n\n"
                f"摘要: {content.get('summary')}\n"
                f"依据: {'; '.join(content.get('evidence', []))}\n"
                f"动作: {content.get('actions', [])}\n"
            )
            ok, reason = self._send_email(recipient or "", subject, body)
            item["mail"]["sent"] = True if ok else False
            item["mail"]["recipient"] = recipient
            item["mail"]["sent_at"] = datetime.utcnow().isoformat()
            item["mail"]["message_id"] = str(uuid4())
            item["status"] = "awaiting_reply"
            item["updated_at"] = datetime.utcnow().isoformat()
            item["mail"]["reason"] = reason
            self.repo.save(data)
            return item
        raise ValueError(f"Strategy not found: {strategy_id}")

    def approve_strategy(self, strategy_id: str, reply_text: str = "AGREE") -> dict[str, Any]:
        data = self.repo.load()
        for item in data.get("strategies", []):
            if item["id"] != strategy_id:
                continue
            item["approval"]["reply_status"] = "approved" if "agree" in reply_text.lower() else "rejected"
            item["approval"]["reply_text"] = reply_text
            item["approval"]["approved_at"] = datetime.utcnow().isoformat()
            item["status"] = "approved" if item["approval"]["reply_status"] == "approved" else "rejected"
            item["updated_at"] = datetime.utcnow().isoformat()
            self.repo.save(data)
            return item
        raise ValueError(f"Strategy not found: {strategy_id}")

    def execute_strategy(self, strategy_id: str) -> dict[str, Any]:
        data = self.repo.load()
        for item in data.get("strategies", []):
            if item["id"] != strategy_id:
                continue
            if item.get("approval", {}).get("reply_status") != "approved":
                raise ValueError("Strategy not approved. Please wait for email reply approval.")
            item["execution"] = {
                "executed": True,
                "executed_at": datetime.utcnow().isoformat(),
                "result": {
                    "status": "simulated_dispatched",
                    "details": "已按审批结果模拟下发到渠道MCP与外呼MCP（未触发真实外部执行）。",
                },
            }
            item["status"] = "executed"
            item["updated_at"] = datetime.utcnow().isoformat()
            self.repo.save(data)
            return item
        raise ValueError(f"Strategy not found: {strategy_id}")
