from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

from chatbi.domain.mcp_skill.repository import MCPSkillRepository
from chatbi.domain.strategy_lab.repository import StrategyLabRepository


class StrategyLabService:
    def __init__(
        self,
        repo: StrategyLabRepository | None = None,
        mcp_repo: MCPSkillRepository | None = None,
    ) -> None:
        self.repo = repo or StrategyLabRepository()
        self.mcp_repo = mcp_repo or MCPSkillRepository()

    def list_experiments(self, limit: int = 100) -> list[dict[str, Any]]:
        data = self.repo.load()
        return list(reversed(data.get("experiments", [])[-limit:]))

    def get_experiment(self, experiment_id: str) -> dict[str, Any]:
        for item in self.repo.load().get("experiments", []):
            if item.get("id") == experiment_id:
                return item
        raise ValueError(f"Experiment not found: {experiment_id}")

    def get_experiment_trend(self, experiment_id: str) -> list[dict[str, Any]]:
        exp = self.get_experiment(experiment_id)
        return exp.get("trend", [])

    def summary(self) -> dict[str, Any]:
        exps = self.repo.load().get("experiments", [])
        running = [x for x in exps if x.get("status") == "running"]
        completed = [x for x in exps if x.get("status") == "completed"]

        def avg_metric(items: list[dict[str, Any]], metric: str) -> float:
            vals = []
            for item in items:
                uplift = (((item.get("metrics") or {}).get(metric) or {}).get("uplift"))
                if isinstance(uplift, (int, float)):
                    vals.append(float(uplift))
            return round(sum(vals) / len(vals), 4) if vals else 0.0

        return {
            "experiment_count": len(exps),
            "running_count": len(running),
            "completed_count": len(completed),
            "avg_conversion_uplift": avg_metric(exps, "conversion_rate"),
            "avg_overdue_uplift": avg_metric(exps, "overdue_rate"),
            "avg_raroc_uplift": avg_metric(exps, "raroc"),
        }

    def create_from_strategy(
        self,
        strategy_id: str,
        name: str | None = None,
        sample_size_control: int = 3000,
        sample_size_treatment: int = 3000,
        duration_days: int = 14,
    ) -> dict[str, Any]:
        mcp_data = self.mcp_repo.load()
        strategy = None
        for item in mcp_data.get("strategies", []):
            if item.get("id") == strategy_id:
                strategy = item
                break
        if not strategy:
            raise ValueError(f"Strategy not found: {strategy_id}")

        content = strategy.get("content", {})
        loan_type = str(content.get("loan_type") or "mixed")
        title = name or f"{content.get('topic', '策略')} A/B 实验"

        base_conversion = 0.18 if loan_type == "consumer" else 0.15
        base_overdue = 0.023 if loan_type == "consumer" else 0.019
        base_raroc = 0.102 if loan_type == "consumer" else 0.111

        data = self.repo.load()
        now = datetime.utcnow().isoformat()
        exp = {
            "id": str(uuid4()),
            "name": title,
            "strategy_id": strategy_id,
            "loan_type": loan_type,
            "status": "running",
            "channel": "A2A推荐渠道组合",
            "segment": "策略命中客群",
            "sample_size_control": sample_size_control,
            "sample_size_treatment": sample_size_treatment,
            "start_date": datetime.utcnow().strftime("%Y-%m-%d"),
            "end_date": (datetime.utcnow() + timedelta(days=duration_days)).strftime("%Y-%m-%d"),
            "metrics": {
                "conversion_rate": {
                    "control": round(base_conversion, 4),
                    "treatment": round(base_conversion + 0.011, 4),
                    "uplift": 0.011,
                },
                "overdue_rate": {
                    "control": round(base_overdue, 4),
                    "treatment": round(base_overdue - 0.002, 4),
                    "uplift": -0.002,
                },
                "raroc": {
                    "control": round(base_raroc, 4),
                    "treatment": round(base_raroc + 0.006, 4),
                    "uplift": 0.006,
                },
                "avg_balance": {
                    "control": 9.1 if loan_type == "consumer" else 18.4,
                    "treatment": 9.6 if loan_type == "consumer" else 19.1,
                    "uplift": 0.5 if loan_type == "consumer" else 0.7,
                },
            },
            "attribution": [
                {"factor": "策略动作组合", "contribution": 0.33, "evidence": "人机协同后动作更精细"},
                {"factor": "A2A执行稳定性", "contribution": 0.27, "evidence": "任务状态机减少中断"},
                {"factor": "市场观察输入", "contribution": 0.22, "evidence": "政策变化及时进入策略"},
                {"factor": "客群分层", "contribution": 0.18, "evidence": "目标客群匹配度提升"},
            ],
            "trend": StrategyLabRepository()._trend_rows(loan_type, 14),
            "created_at": now,
            "updated_at": now,
        }
        data.setdefault("experiments", []).append(exp)
        self.repo.save(data)
        return exp

    def update_status(self, experiment_id: str, status: str) -> dict[str, Any]:
        data = self.repo.load()
        for item in data.get("experiments", []):
            if item.get("id") != experiment_id:
                continue
            item["status"] = status
            if status == "completed" and not item.get("end_date"):
                item["end_date"] = datetime.utcnow().strftime("%Y-%m-%d")
            item["updated_at"] = datetime.utcnow().isoformat()
            self.repo.save(data)
            return item
        raise ValueError(f"Experiment not found: {experiment_id}")
