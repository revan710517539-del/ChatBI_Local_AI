from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from chatbi.domain.planning.dtos import PlanExecutionRecordDTO
from chatbi.domain.planning.repository import PlanningRepository


class PlanningService:
    def __init__(self, repo: PlanningRepository | None = None) -> None:
        self.repo = repo or PlanningRepository()

    def list_rules(self) -> list[dict[str, Any]]:
        return self.repo.load().get("rules", [])

    def update_rules(self, rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
        data = self.repo.load()
        data["rules"] = rules
        data["updated_at"] = datetime.utcnow().isoformat()
        self.repo.save(data)
        return rules

    def list_chains(self) -> list[dict[str, Any]]:
        return self.repo.load().get("chains", [])

    def update_chains(self, chains: list[dict[str, Any]]) -> list[dict[str, Any]]:
        data = self.repo.load()
        data["chains"] = chains
        data["updated_at"] = datetime.utcnow().isoformat()
        self.repo.save(data)
        return chains

    @staticmethod
    def _infer_loan_type(question: str) -> str:
        q = question.lower()
        if "经营贷" in question or "business" in q:
            return "business"
        if "消费贷" in question or "consumer" in q:
            return "consumer"
        return "mixed"

    def build_plan(
        self,
        question: str,
        scene: str = "data_discuss",
        loan_type: str | None = None,
    ) -> dict[str, Any]:
        data = self.repo.load()
        rules = [r for r in data.get("rules", []) if r.get("enabled", True)]
        chains = [c for c in data.get("chains", []) if c.get("enabled", True)]
        chain = (
            chains[0]
            if chains
            else {"name": "Default A2A Chain", "mode": "a2a_dispatch", "steps": []}
        )

        inferred_type = loan_type or self._infer_loan_type(question)
        matched_rule = None
        q = question.lower()
        for rule in rules:
            kws = [str(x).lower() for x in rule.get("match_keywords", [])]
            if any(k in q for k in kws):
                matched_rule = rule
                break
        if not matched_rule and rules:
            matched_rule = rules[0]

        split_template = (
            matched_rule.get("split_template", [])
            if matched_rule
            else ["指标拆解", "风险评估", "策略建议"]
        )
        preferred_agents = (
            matched_rule.get("preferred_agents", [])
            if matched_rule
            else ["贷款经营分析Agent"]
        )
        tools = (
            matched_rule.get("toolchain", {"sql": True, "rag": True, "rule_validation": True})
            if matched_rule
            else {"sql": True, "rag": True, "rule_validation": True}
        )

        tasks: list[dict[str, Any]] = []
        previous_id = None
        for idx, title in enumerate(split_template, start=1):
            task_id = f"task_{idx}"
            assigned_agent = (
                preferred_agents[min(idx - 1, len(preferred_agents) - 1)]
                if preferred_agents
                else "贷款经营分析Agent"
            )
            tasks.append(
                {
                    "task_id": task_id,
                    "title": title,
                    "objective": f"围绕{inferred_type}贷款完成[{title}]并输出可执行结论",
                    "assigned_agent": assigned_agent,
                    "depends_on": [previous_id] if previous_id else [],
                    "tools": tools,
                }
            )
            previous_id = task_id

        plan = {
            "plan_id": str(uuid4()),
            "scene": scene,
            "question": question,
            "loan_type": inferred_type,
            "workflow_mode": chain.get("mode", "a2a_dispatch"),
            "workflow_chain": chain,
            "strategy_focus": "客群理解 + 漏斗转化 + 风险收益平衡 + 远程协作执行",
            "tasks": tasks,
            "rationale": [
                "先诊断再决策，避免直接给策略导致误判。",
                "消费贷关注转化效率与逾期弹性，经营贷关注额度效率与迁徙稳定性。",
                "策略动作需先邮件审批，再进入执行队列。",
            ],
            "created_at": datetime.utcnow().isoformat(),
        }

        data.setdefault("plan_history", []).append(plan)
        data["plan_history"] = data["plan_history"][-300:]
        self.repo.save(data)
        return plan

    def list_plan_history(self, limit: int = 100) -> list[dict[str, Any]]:
        data = self.repo.load()
        items = data.get("plan_history", [])
        return list(reversed(items[-limit:]))

    @staticmethod
    def _now() -> str:
        return datetime.utcnow().isoformat()

    @staticmethod
    def _deps_completed(task: dict[str, Any], tasks_by_id: dict[str, dict[str, Any]]) -> bool:
        deps = task.get("depends_on", [])
        return all(tasks_by_id.get(dep, {}).get("status") == "completed" for dep in deps)

    def _normalize_execution(self, execution: dict[str, Any]) -> dict[str, Any]:
        tasks = execution.get("tasks", [])
        tasks_by_id = {t["task_id"]: t for t in tasks}

        if execution.get("state") in {"completed", "failed", "cancelled"}:
            return execution

        for task in tasks:
            if task.get("status") == "pending" and self._deps_completed(task, tasks_by_id):
                task["status"] = "ready"

        if all(t.get("status") in {"completed", "skipped"} for t in tasks):
            execution["state"] = "completed"
            execution["finished_at"] = execution.get("finished_at") or self._now()
        elif any(t.get("status") == "failed" for t in tasks):
            execution["state"] = "failed"
        elif any(t.get("status") == "running" for t in tasks) or any(
            t.get("status") == "ready" for t in tasks
        ):
            execution["state"] = "running"
        else:
            execution["state"] = execution.get("state", "pending")

        execution["updated_at"] = self._now()
        return execution

    def _append_log(self, data: dict[str, Any], execution_id: str, step: str, status: str, detail: str, metadata: dict[str, Any] | None = None) -> None:
        item = {
            "execution_id": execution_id,
            "step": step,
            "status": status,
            "detail": detail,
            "metadata": metadata or {},
            "timestamp": self._now(),
        }
        data.setdefault("execution_logs", []).append(item)
        data["execution_logs"] = data["execution_logs"][-2000:]

    def _get_plan_by_id(self, data: dict[str, Any], plan_id: str) -> dict[str, Any] | None:
        for p in data.get("plan_history", []):
            if p.get("plan_id") == plan_id:
                return p
        return None

    def start_execution(
        self,
        *,
        plan_id: str | None = None,
        question: str | None = None,
        scene: str = "data_discuss",
        loan_type: str | None = None,
        auto_start: bool = True,
    ) -> dict[str, Any]:
        data = self.repo.load()

        plan = None
        if plan_id:
            plan = self._get_plan_by_id(data, plan_id)
            if not plan:
                raise ValueError(f"Plan not found: {plan_id}")
        elif question:
            plan = self.build_plan(question=question, scene=scene, loan_type=loan_type)
            data = self.repo.load()
        else:
            raise ValueError("Either plan_id or question is required")

        execution_id = str(uuid4())
        tasks = []
        for t in plan.get("tasks", []):
            tasks.append(
                {
                    "task_id": t.get("task_id"),
                    "title": t.get("title"),
                    "assigned_agent": t.get("assigned_agent"),
                    "depends_on": t.get("depends_on", []),
                    "tools": t.get("tools", {}),
                    "status": "pending",
                    "attempts": 0,
                    "started_at": None,
                    "finished_at": None,
                    "output_summary": None,
                    "error": None,
                }
            )

        execution = {
            "execution_id": execution_id,
            "plan_id": plan.get("plan_id"),
            "question": plan.get("question"),
            "scene": plan.get("scene"),
            "loan_type": plan.get("loan_type"),
            "workflow_mode": plan.get("workflow_mode"),
            "state": "pending",
            "auto_start": auto_start,
            "created_at": self._now(),
            "updated_at": self._now(),
            "started_at": None,
            "finished_at": None,
            "tasks": tasks,
            "result_summary": None,
        }

        execution = self._normalize_execution(execution)
        if auto_start:
            execution["started_at"] = self._now()
            execution["state"] = "running"

        data.setdefault("executions", []).append(execution)
        data["executions"] = data["executions"][-500:]
        self._append_log(
            data,
            execution_id=execution_id,
            step="execution_start",
            status="success",
            detail="A2A execution created",
            metadata={"plan_id": plan.get("plan_id"), "task_count": len(tasks)},
        )
        self.repo.save(data)
        return execution

    def list_executions(self, limit: int = 100) -> list[dict[str, Any]]:
        data = self.repo.load()
        items = data.get("executions", [])[-limit:]
        items = [self._normalize_execution(dict(x)) for x in items]
        return list(reversed(items))

    def get_execution(self, execution_id: str) -> dict[str, Any]:
        data = self.repo.load()
        for item in data.get("executions", []):
            if item.get("execution_id") == execution_id:
                normalized = self._normalize_execution(item)
                self.repo.save(data)
                return normalized
        raise ValueError(f"Execution not found: {execution_id}")

    def task_action(self, execution_id: str, task_id: str, action: str, note: str | None = None) -> dict[str, Any]:
        data = self.repo.load()
        execution = None
        for item in data.get("executions", []):
            if item.get("execution_id") == execution_id:
                execution = item
                break
        if not execution:
            raise ValueError(f"Execution not found: {execution_id}")

        tasks = execution.get("tasks", [])
        task = next((t for t in tasks if t.get("task_id") == task_id), None)
        if not task:
            raise ValueError(f"Task not found: {task_id}")

        tasks_by_id = {t["task_id"]: t for t in tasks}

        if action == "start":
            if not self._deps_completed(task, tasks_by_id):
                raise ValueError("Dependencies not completed")
            task["status"] = "running"
            task["attempts"] = int(task.get("attempts", 0)) + 1
            task["started_at"] = task.get("started_at") or self._now()
            task["error"] = None
            execution["state"] = "running"
            execution["started_at"] = execution.get("started_at") or self._now()
        elif action == "complete":
            if task.get("status") not in {"running", "ready", "pending"}:
                raise ValueError("Task status does not allow complete")
            task["status"] = "completed"
            task["finished_at"] = self._now()
            task["output_summary"] = note or f"{task.get('title')}完成"
            task["error"] = None
        elif action == "fail":
            if task.get("status") not in {"running", "ready", "pending"}:
                raise ValueError("Task status does not allow fail")
            task["status"] = "failed"
            task["finished_at"] = self._now()
            task["error"] = note or "Task failed"
            execution["state"] = "failed"
        elif action == "retry":
            if task.get("status") != "failed":
                raise ValueError("Only failed task can retry")
            task["status"] = "pending"
            task["finished_at"] = None
            task["error"] = None
            execution["state"] = "running"
        elif action == "skip":
            if task.get("status") in {"completed", "skipped"}:
                raise ValueError("Task already finalized")
            task["status"] = "skipped"
            task["finished_at"] = self._now()
            task["output_summary"] = note or "Task skipped"
        else:
            raise ValueError(f"Unsupported action: {action}")

        execution = self._normalize_execution(execution)
        self._append_log(
            data,
            execution_id=execution_id,
            step=f"task_{action}",
            status="success",
            detail=f"{task_id} -> {action}",
            metadata={"note": note},
        )
        self.repo.save(data)
        return execution

    def tick_execution(self, execution_id: str) -> dict[str, Any]:
        data = self.repo.load()
        execution = None
        for item in data.get("executions", []):
            if item.get("execution_id") == execution_id:
                execution = item
                break
        if not execution:
            raise ValueError(f"Execution not found: {execution_id}")

        execution = self._normalize_execution(execution)
        if execution.get("state") in {"completed", "failed", "cancelled"}:
            self.repo.save(data)
            return execution

        tasks = execution.get("tasks", [])
        running = next((t for t in tasks if t.get("status") == "running"), None)
        if not running:
            ready = next((t for t in tasks if t.get("status") == "ready"), None)
            if ready:
                ready["status"] = "running"
                ready["attempts"] = int(ready.get("attempts", 0)) + 1
                ready["started_at"] = ready.get("started_at") or self._now()
                running = ready

        if running:
            running["status"] = "completed"
            running["finished_at"] = self._now()
            running["output_summary"] = f"{running.get('title')}自动执行完成"

        execution = self._normalize_execution(execution)
        if execution.get("state") == "completed":
            execution["result_summary"] = "A2A流程已完成，全部任务执行结束。"

        self._append_log(
            data,
            execution_id=execution_id,
            step="tick",
            status="success",
            detail="State machine advanced by one step",
            metadata={"state": execution.get("state")},
        )
        self.repo.save(data)
        return execution

    def run_execution(self, execution_id: str, max_steps: int = 20) -> dict[str, Any]:
        execution = self.get_execution(execution_id)
        steps = max(1, min(max_steps, 200))
        for _ in range(steps):
            if execution.get("state") in {"completed", "failed", "cancelled"}:
                break
            execution = self.tick_execution(execution_id)
        return execution

    def record_execution(self, payload: PlanExecutionRecordDTO) -> dict[str, Any]:
        data = self.repo.load()
        item = {
            "plan_id": payload.plan_id,
            "status": payload.status,
            "note": payload.note,
            "metadata": payload.metadata,
            "ts": self._now(),
        }
        data.setdefault("execution_logs", []).append(item)
        data["execution_logs"] = data["execution_logs"][-1000:]
        self.repo.save(data)
        return item

    def list_execution_logs(
        self,
        limit: int = 200,
        execution_id: str | None = None,
    ) -> list[dict[str, Any]]:
        data = self.repo.load()
        logs = data.get("execution_logs", [])
        if execution_id:
            logs = [x for x in logs if x.get("execution_id") == execution_id]
        return list(reversed(logs[-limit:]))
