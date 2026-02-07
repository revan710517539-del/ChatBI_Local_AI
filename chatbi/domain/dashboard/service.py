from __future__ import annotations

from typing import Any, Optional

from chatbi.agent.langchain_orchestrator import SmartBILangChainOrchestrator
from chatbi.database.connection_manager import connection_manager
from chatbi.domain.ai_config.service import AIConfigService
from chatbi.domain.datasource import DatabaseType
from chatbi.domain.datasource.repository import DatasourceRepository
from chatbi.domain.dashboard.indicator_catalog import INDICATOR_DEFINITIONS
from chatbi.domain.dashboard.metric_engine import MetricEngine, MetricFilters


BUSINESS_LOAN_METRICS = [
    ("bl_register_users", "经营贷注册人数", ""),
    ("bl_apply_orders", "经营贷申请订单数", ""),
    ("bl_completion_rate", "经营贷完件率", ""),
    ("bl_stage3_success_users", "经营贷终审授信成功人数", ""),
    ("bl_disburse_orders", "经营贷动支笔数", ""),
    ("bl_disburse_amount", "经营贷新增放款金额", ""),
    ("bl_onbook_users", "经营贷在贷人数", ""),
    ("bl_repaid_users", "经营贷已还款人数", ""),
    ("bl_overdue_rate", "经营贷逾期率", ""),
    ("bl_migration_rate", "经营贷迁徙率", ""),
    ("bl_credit_utilization_rate", "经营贷额度使用率", ""),
    ("bl_raroc", "经营贷风险收益比", ""),
    ("bl_net_interest_margin", "经营贷净息差", ""),
]

CONSUMER_LOAN_METRICS = [
    ("cl_register_users", "消费贷注册人数", ""),
    ("cl_apply_orders", "消费贷申请订单数", ""),
    ("cl_completion_rate", "消费贷完件率", ""),
    ("cl_final_pass_users", "消费贷终审通过人数", ""),
    ("cl_disburse_orders", "消费贷动支笔数", ""),
    ("cl_disburse_amount", "消费贷动支金额", ""),
    ("cl_onbook_users", "消费贷在贷人数", ""),
    ("cl_repaid_users", "消费贷已还款人数", ""),
    ("cl_overdue_rate", "消费贷逾期率", ""),
    ("cl_migration_rate", "消费贷迁徙率", ""),
    ("cl_credit_utilization_rate", "消费贷额度使用率", ""),
    ("cl_raroc", "消费贷风险收益比", ""),
    ("cl_net_interest_margin", "消费贷净息差", ""),
]

EXTRA_FIN_RISK_METRICS = [
    ("cost_income_ratio", "成本收入比", ""),
    ("raroc", "风险收益比(RAROC)", ""),
    ("migration_rate_m1_m3", "迁徙率(M1->M3)", ""),
    ("provision_coverage", "拨备覆盖率", ""),
    ("capital_adequacy_ratio", "资本充足率", ""),
]


class DashboardService:
    def __init__(self, datasource_repo: DatasourceRepository):
        self.datasource_repo = datasource_repo
        self.ai_config_service = AIConfigService()
        self.lc_orchestrator = SmartBILangChainOrchestrator()
        self.metric_engine = MetricEngine()

    async def _resolve_datasource(self, datasource_id: Optional[str]):
        if datasource_id:
            ds = await self.datasource_repo.get_by_id(datasource_id)
            if ds:
                return ds
        all_ds = await self.datasource_repo.get_all(limit=100)
        if not all_ds:
            return None
        for ds in all_ds:
            ds_type = ds.type.value if hasattr(ds.type, "value") else str(ds.type)
            if "duckdb" in ds_type.lower():
                return ds
        return all_ds[0]

    async def _run_metric_sql(self, datasource, sql: str) -> Optional[float]:
        try:
            db_type = DatabaseType(datasource.type)
            result = await connection_manager.execute_query(
                db_type=db_type,
                connection_info=datasource.connection_info,
                query=sql,
                timeout=20,
                max_rows=1,
            )
            rows = result.get("rows", [])
            if not rows:
                return None
            val = rows[0].get("v")
            if val is None:
                return None
            return float(val)
        except Exception:
            return None

    async def get_loan_kpis(self, datasource_id: Optional[str] = None) -> dict[str, Any]:
        datasource = await self._resolve_datasource(datasource_id)
        if not datasource:
            return self._fallback_payload()

        default_filters = MetricFilters()

        async def collect(metrics):
            items = []
            for key, name, _sql in metrics:
                result = await self.metric_engine.execute_metric(
                    datasource=datasource,
                    metric_key=key,
                    filters=default_filters,
                )
                items.append({"key": key, "name": name, "value": result["value"], "sql": result["sql"]})
            return items

        business = await collect(BUSINESS_LOAN_METRICS)
        consumer = await collect(CONSUMER_LOAN_METRICS)
        extra = await collect(EXTRA_FIN_RISK_METRICS)
        metrics_text = "\n".join([f"{x['name']}: {x['value']}" for x in business + consumer + extra])
        summary = self.lc_orchestrator.summarize_for_dashboard(
            llm_cfg=self.ai_config_service.resolve_llm_source(scene="dashboard"),
            metrics_text=metrics_text,
        )
        return {
            "datasource_id": str(datasource.id),
            "business_loan": business,
            "consumer_loan": consumer,
            "finance_risk": extra,
            "summary": summary,
        }

    async def query_metrics_with_filters(
        self,
        datasource_id: Optional[str],
        metric_keys: list[str],
        start_date: Optional[str],
        end_date: Optional[str],
        channels: Optional[list[str]],
        customer_segments: Optional[list[str]],
        customer_groups: Optional[list[str]],
        loan_product: Optional[str],
    ) -> dict[str, Any]:
        datasource = await self._resolve_datasource(datasource_id)
        if not datasource:
            return {"datasource_id": None, "items": [], "message": "No datasource available"}

        filters = MetricFilters(
            start_date=start_date,
            end_date=end_date,
            channels=channels,
            customer_segments=customer_segments,
            customer_groups=customer_groups,
            loan_product=loan_product,
        )
        items = []
        for key in metric_keys:
            try:
                items.append(
                    await self.metric_engine.execute_metric(
                        datasource=datasource,
                        metric_key=key,
                        filters=filters,
                    )
                )
            except Exception as e:
                items.append({"metric_key": key, "error": str(e)})
        return {"datasource_id": str(datasource.id), "filters": filters.__dict__, "items": items}

    @staticmethod
    def _fallback_payload() -> dict[str, Any]:
        return {
            "datasource_id": None,
            "business_loan": [{"key": k, "name": n, "value": 0.0} for k, n, _ in BUSINESS_LOAN_METRICS],
            "consumer_loan": [{"key": k, "name": n, "value": 0.0} for k, n, _ in CONSUMER_LOAN_METRICS],
            "finance_risk": [{"key": k, "name": n, "value": 0.0} for k, n, _ in EXTRA_FIN_RISK_METRICS],
            "summary": "当前未检测到可用数据源，已返回默认指标模板。",
        }

    @staticmethod
    def get_metric_catalog() -> dict[str, Any]:
        return {
            "business_loan": [{"key": k, "name": n, "sql": s} for k, n, s in BUSINESS_LOAN_METRICS],
            "consumer_loan": [{"key": k, "name": n, "sql": s} for k, n, s in CONSUMER_LOAN_METRICS],
            "finance_risk": [{"key": k, "name": n, "sql": s} for k, n, s in EXTRA_FIN_RISK_METRICS],
        }

    @staticmethod
    def get_indicator_definitions() -> list[dict[str, Any]]:
        return INDICATOR_DEFINITIONS
