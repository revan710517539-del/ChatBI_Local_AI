from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from chatbi.database.connection_manager import connection_manager
from chatbi.domain.dashboard.indicator_catalog import INDICATOR_DEFINITIONS
from chatbi.domain.datasource import DatabaseType


@dataclass
class MetricFilters:
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    channels: Optional[list[str]] = None
    customer_segments: Optional[list[str]] = None
    customer_groups: Optional[list[str]] = None
    loan_product: Optional[str] = None


class MetricEngine:
    def __init__(self) -> None:
        self.def_map = {x["metric_key"]: x for x in INDICATOR_DEFINITIONS}

    @staticmethod
    def _quote(val: str) -> str:
        return "'" + str(val).replace("'", "''") + "'"

    def _build_where_suffix(self, filters: MetricFilters) -> str:
        clauses: list[str] = []
        if filters.start_date:
            clauses.append(f"biz_date >= {self._quote(filters.start_date)}")
        if filters.end_date:
            clauses.append(f"biz_date <= {self._quote(filters.end_date)}")
        if filters.channels:
            vals = ",".join(self._quote(x) for x in filters.channels)
            clauses.append(f"channel IN ({vals})")
        if filters.customer_segments:
            vals = ",".join(self._quote(x) for x in filters.customer_segments)
            clauses.append(f"customer_segment IN ({vals})")
        if filters.customer_groups:
            vals = ",".join(self._quote(x) for x in filters.customer_groups)
            clauses.append(f"customer_group IN ({vals})")
        if filters.loan_product:
            clauses.append(f"loan_type = {self._quote(filters.loan_product)}")
        if not clauses:
            return ""
        return " AND " + " AND ".join(clauses)

    def build_sql(self, metric_key: str, filters: MetricFilters) -> str:
        meta = self.def_map.get(metric_key)
        if not meta:
            raise ValueError(f"Metric not found: {metric_key}")
        raw_tpl = meta["sql_template"]
        suffix = self._build_where_suffix(filters)
        return raw_tpl.replace(";", f"{suffix};")

    async def execute_metric(
        self,
        datasource,
        metric_key: str,
        filters: MetricFilters,
    ) -> dict[str, Any]:
        sql = self.build_sql(metric_key, filters)
        result = await connection_manager.execute_query(
            db_type=DatabaseType(datasource.type),
            connection_info=datasource.connection_info,
            query=sql,
            timeout=20,
            max_rows=1,
        )
        rows = result.get("rows", [])
        value = None
        if rows:
            value = rows[0].get("metric_value")
        meta = self.def_map[metric_key]
        return {
            "metric_key": metric_key,
            "metric_name": meta["metric_name"],
            "definition": meta["definition"],
            "sql": sql,
            "value": value,
        }

