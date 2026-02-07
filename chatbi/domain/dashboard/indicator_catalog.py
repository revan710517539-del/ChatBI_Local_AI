from __future__ import annotations

from typing import Any


def _tpl(metric_key: str, loan_type: str, expr: str) -> str:
    return (
        "SELECT "
        f"{expr} AS metric_value "
        "FROM loan_funnel_daily "
        f"WHERE loan_type = '{loan_type}' "
        "AND 1=1;"
    )


INDICATOR_DEFINITIONS: list[dict[str, Any]] = [
    # 经营贷 - 展业/申请/授信/动支/还款/逾期
    {"loan_product": "business", "stage": "展业", "metric_key": "bl_active_bdm", "metric_name": "活跃展业人数(客户经理)", "definition": "统计周期内有展业行为的客户经理人数", "sql_template": _tpl("bl_active_bdm", "business", "COUNT(DISTINCT CASE WHEN bdm_active=1 THEN bdm_id END)")},
    {"loan_product": "business", "stage": "展业", "metric_key": "bl_channel_pass_rate", "metric_name": "展业人员整体通过率", "definition": "展业流量进入授信通过的转化比例", "sql_template": _tpl("bl_channel_pass_rate", "business", "AVG(channel_pass_rate)")},
    {"loan_product": "business", "stage": "申请", "metric_key": "bl_register_users", "metric_name": "注册人数", "definition": "统计周期内完成注册的申请用户人数", "sql_template": _tpl("bl_register_users", "business", "SUM(register_user_cnt)")},
    {"loan_product": "business", "stage": "申请", "metric_key": "bl_apply_orders", "metric_name": "申请订单数", "definition": "统计周期内提交申请单数", "sql_template": _tpl("bl_apply_orders", "business", "SUM(apply_order_cnt)")},
    {"loan_product": "business", "stage": "申请", "metric_key": "bl_completion_rate", "metric_name": "完件率", "definition": "申请订单完成资料提交比例", "sql_template": _tpl("bl_completion_rate", "business", "AVG(completion_rate)")},
    {"loan_product": "business", "stage": "授信一段", "metric_key": "bl_stage1_enter_users", "metric_name": "初审申请提额人数", "definition": "进入授信一段的申请用户人数", "sql_template": _tpl("bl_stage1_enter_users", "business", "SUM(stage1_enter_user_cnt)")},
    {"loan_product": "business", "stage": "授信一段", "metric_key": "bl_stage1_pass_users", "metric_name": "初审亲见通过人数", "definition": "授信一段亲见审核通过人数", "sql_template": _tpl("bl_stage1_pass_users", "business", "SUM(stage1_pass_user_cnt)")},
    {"loan_product": "business", "stage": "授信一段", "metric_key": "bl_stage1_success_orders", "metric_name": "初审授信成功订单数", "definition": "授信一段最终授信成功订单数", "sql_template": _tpl("bl_stage1_success_orders", "business", "SUM(stage1_success_order_cnt)")},
    {"loan_product": "business", "stage": "授信二段", "metric_key": "bl_stage2_enter_users", "metric_name": "进入二段人数", "definition": "由一段流转进入二段审核人数", "sql_template": _tpl("bl_stage2_enter_users", "business", "SUM(stage2_enter_user_cnt)")},
    {"loan_product": "business", "stage": "授信二段", "metric_key": "bl_stage2_pass_users", "metric_name": "二段亲见通过人数", "definition": "授信二段亲见审核通过人数", "sql_template": _tpl("bl_stage2_pass_users", "business", "SUM(stage2_pass_user_cnt)")},
    {"loan_product": "business", "stage": "授信二段", "metric_key": "bl_stage2_success_orders", "metric_name": "二段授信成功人数", "definition": "授信二段授信成功用户人数", "sql_template": _tpl("bl_stage2_success_orders", "business", "SUM(stage2_success_user_cnt)")},
    {"loan_product": "business", "stage": "授信三段", "metric_key": "bl_stage3_enter_users", "metric_name": "进入三段人数", "definition": "进入终审授信阶段人数", "sql_template": _tpl("bl_stage3_enter_users", "business", "SUM(stage3_enter_user_cnt)")},
    {"loan_product": "business", "stage": "授信三段", "metric_key": "bl_stage3_success_users", "metric_name": "终审授信成功人数", "definition": "终审授信成功用户人数", "sql_template": _tpl("bl_stage3_success_users", "business", "SUM(stage3_success_user_cnt)")},
    {"loan_product": "business", "stage": "动支", "metric_key": "bl_disburse_users_t30", "metric_name": "动支人数(T30)", "definition": "授信后30天内发生动支的用户人数", "sql_template": _tpl("bl_disburse_users_t30", "business", "SUM(disburse_user_t30_cnt)")},
    {"loan_product": "business", "stage": "动支", "metric_key": "bl_disburse_orders", "metric_name": "动支笔数", "definition": "统计周期动支交易笔数", "sql_template": _tpl("bl_disburse_orders", "business", "SUM(disburse_order_cnt)")},
    {"loan_product": "business", "stage": "动支", "metric_key": "bl_disburse_amount", "metric_name": "新增放款金额", "definition": "统计周期新增放款金额", "sql_template": _tpl("bl_disburse_amount", "business", "SUM(disburse_amount)")},
    {"loan_product": "business", "stage": "还款", "metric_key": "bl_onbook_users", "metric_name": "在贷人数", "definition": "期末仍在贷用户人数", "sql_template": _tpl("bl_onbook_users", "business", "SUM(onbook_user_cnt)")},
    {"loan_product": "business", "stage": "还款", "metric_key": "bl_new_onbook_users", "metric_name": "当期新增在贷人数", "definition": "统计周期新增进入在贷状态人数", "sql_template": _tpl("bl_new_onbook_users", "business", "SUM(new_onbook_user_cnt)")},
    {"loan_product": "business", "stage": "还款", "metric_key": "bl_repaid_users", "metric_name": "已还款人数", "definition": "统计周期完成结清还款人数", "sql_template": _tpl("bl_repaid_users", "business", "SUM(repaid_user_cnt)")},
    {"loan_product": "business", "stage": "逾期", "metric_key": "bl_overdue_users", "metric_name": "逾期人数", "definition": "统计周期发生逾期的用户人数", "sql_template": _tpl("bl_overdue_users", "business", "SUM(overdue_user_cnt)")},
    {"loan_product": "business", "stage": "逾期", "metric_key": "bl_overdue_rate", "metric_name": "逾期率", "definition": "逾期用户数/在贷用户数", "sql_template": _tpl("bl_overdue_rate", "business", "AVG(overdue_rate)")},
    {"loan_product": "business", "stage": "逾期", "metric_key": "bl_npl_rate", "metric_name": "不良率", "definition": "不良贷款余额/贷款余额", "sql_template": _tpl("bl_npl_rate", "business", "AVG(npl_ratio)")},
    # 消费贷
    {"loan_product": "consumer", "stage": "展业", "metric_key": "cl_active_bdm", "metric_name": "活跃展业人数(客户经理)", "definition": "统计周期内有展业行为的客户经理人数", "sql_template": _tpl("cl_active_bdm", "consumer", "COUNT(DISTINCT CASE WHEN bdm_active=1 THEN bdm_id END)")},
    {"loan_product": "consumer", "stage": "展业", "metric_key": "cl_channel_pass_rate", "metric_name": "展业人员整体通过率", "definition": "展业流量进入授信通过的转化比例", "sql_template": _tpl("cl_channel_pass_rate", "consumer", "AVG(channel_pass_rate)")},
    {"loan_product": "consumer", "stage": "申请", "metric_key": "cl_register_users", "metric_name": "注册人数", "definition": "统计周期内完成注册的申请用户人数", "sql_template": _tpl("cl_register_users", "consumer", "SUM(register_user_cnt)")},
    {"loan_product": "consumer", "stage": "申请", "metric_key": "cl_apply_orders", "metric_name": "申请订单数", "definition": "统计周期内提交申请单数", "sql_template": _tpl("cl_apply_orders", "consumer", "SUM(apply_order_cnt)")},
    {"loan_product": "consumer", "stage": "申请", "metric_key": "cl_completion_rate", "metric_name": "完件率", "definition": "申请订单完成资料提交比例", "sql_template": _tpl("cl_completion_rate", "consumer", "AVG(completion_rate)")},
    {"loan_product": "consumer", "stage": "授信", "metric_key": "cl_stage1_need_sign_users", "metric_name": "需面核人数", "definition": "进入面核环节的用户人数", "sql_template": _tpl("cl_stage1_need_sign_users", "consumer", "SUM(facecheck_need_user_cnt)")},
    {"loan_product": "consumer", "stage": "授信", "metric_key": "cl_stage1_face_pass_users", "metric_name": "面签通过人数", "definition": "面核通过人数", "sql_template": _tpl("cl_stage1_face_pass_users", "consumer", "SUM(facecheck_pass_user_cnt)")},
    {"loan_product": "consumer", "stage": "授信", "metric_key": "cl_stage1_phone_pass_users", "metric_name": "电核通过人数", "definition": "电话核实通过人数", "sql_template": _tpl("cl_stage1_phone_pass_users", "consumer", "SUM(phonecheck_pass_user_cnt)")},
    {"loan_product": "consumer", "stage": "授信", "metric_key": "cl_final_pass_users", "metric_name": "终审通过人数", "definition": "终审授信通过人数", "sql_template": _tpl("cl_final_pass_users", "consumer", "SUM(final_pass_user_cnt)")},
    {"loan_product": "consumer", "stage": "授信", "metric_key": "cl_final_pass_orders", "metric_name": "终审通过订单数", "definition": "终审授信通过订单数", "sql_template": _tpl("cl_final_pass_orders", "consumer", "SUM(final_pass_order_cnt)")},
    {"loan_product": "consumer", "stage": "动支", "metric_key": "cl_disburse_users_t30", "metric_name": "动支人数(T30)", "definition": "授信后30天内发生动支用户人数", "sql_template": _tpl("cl_disburse_users_t30", "consumer", "SUM(disburse_user_t30_cnt)")},
    {"loan_product": "consumer", "stage": "动支", "metric_key": "cl_disburse_orders", "metric_name": "动支笔数", "definition": "统计周期动支交易笔数", "sql_template": _tpl("cl_disburse_orders", "consumer", "SUM(disburse_order_cnt)")},
    {"loan_product": "consumer", "stage": "动支", "metric_key": "cl_disburse_amount", "metric_name": "动支金额", "definition": "统计周期动支交易金额", "sql_template": _tpl("cl_disburse_amount", "consumer", "SUM(disburse_amount)")},
    {"loan_product": "consumer", "stage": "还款", "metric_key": "cl_onbook_users", "metric_name": "在贷人数", "definition": "期末仍在贷用户人数", "sql_template": _tpl("cl_onbook_users", "consumer", "SUM(onbook_user_cnt)")},
    {"loan_product": "consumer", "stage": "还款", "metric_key": "cl_new_onbook_users", "metric_name": "当期新增在贷人数", "definition": "统计周期新增进入在贷状态人数", "sql_template": _tpl("cl_new_onbook_users", "consumer", "SUM(new_onbook_user_cnt)")},
    {"loan_product": "consumer", "stage": "还款", "metric_key": "cl_repaid_users", "metric_name": "已还款人数", "definition": "统计周期完成结清还款人数", "sql_template": _tpl("cl_repaid_users", "consumer", "SUM(repaid_user_cnt)")},
    {"loan_product": "consumer", "stage": "逾期", "metric_key": "cl_overdue_users", "metric_name": "逾期人数", "definition": "统计周期发生逾期的用户人数", "sql_template": _tpl("cl_overdue_users", "consumer", "SUM(overdue_user_cnt)")},
    {"loan_product": "consumer", "stage": "逾期", "metric_key": "cl_overdue_rate", "metric_name": "逾期率", "definition": "逾期用户数/在贷用户数", "sql_template": _tpl("cl_overdue_rate", "consumer", "AVG(overdue_rate)")},
    {"loan_product": "consumer", "stage": "逾期", "metric_key": "cl_npl_rate", "metric_name": "不良率", "definition": "不良贷款余额/贷款余额", "sql_template": _tpl("cl_npl_rate", "consumer", "AVG(npl_ratio)")},
    # 核心经营看板指标（经营贷/消费贷）
    {"loan_product": "business", "stage": "经营看板", "metric_key": "bl_credit_utilization_rate", "metric_name": "经营贷额度使用率", "definition": "经营贷额度使用情况（以动支金额占比近似）", "sql_template": _tpl("bl_credit_utilization_rate", "business", "AVG(disburse_amount / NULLIF(disburse_amount + 100000, 0))")},
    {"loan_product": "consumer", "stage": "经营看板", "metric_key": "cl_credit_utilization_rate", "metric_name": "消费贷额度使用率", "definition": "消费贷额度使用情况（以动支金额占比近似）", "sql_template": _tpl("cl_credit_utilization_rate", "consumer", "AVG(disburse_amount / NULLIF(disburse_amount + 100000, 0))")},
    {"loan_product": "business", "stage": "经营看板", "metric_key": "bl_migration_rate", "metric_name": "经营贷迁徙率", "definition": "经营贷M1向M3的迁徙率", "sql_template": _tpl("bl_migration_rate", "business", "AVG(migration_rate_m1_to_m3)")},
    {"loan_product": "consumer", "stage": "经营看板", "metric_key": "cl_migration_rate", "metric_name": "消费贷迁徙率", "definition": "消费贷M1向M3的迁徙率", "sql_template": _tpl("cl_migration_rate", "consumer", "AVG(migration_rate_m1_to_m3)")},
    {"loan_product": "business", "stage": "经营看板", "metric_key": "bl_raroc", "metric_name": "经营贷风险收益比", "definition": "经营贷风险调整后收益率", "sql_template": _tpl("bl_raroc", "business", "AVG(raroc)")},
    {"loan_product": "consumer", "stage": "经营看板", "metric_key": "cl_raroc", "metric_name": "消费贷风险收益比", "definition": "消费贷风险调整后收益率", "sql_template": _tpl("cl_raroc", "consumer", "AVG(raroc)")},
    {"loan_product": "business", "stage": "经营看板", "metric_key": "bl_net_interest_margin", "metric_name": "经营贷净息差", "definition": "经营贷净息差", "sql_template": _tpl("bl_net_interest_margin", "business", "AVG(net_interest_margin)")},
    {"loan_product": "consumer", "stage": "经营看板", "metric_key": "cl_net_interest_margin", "metric_name": "消费贷净息差", "definition": "消费贷净息差", "sql_template": _tpl("cl_net_interest_margin", "consumer", "AVG(net_interest_margin)")},
    # 通用财务/风险
    {"loan_product": "common", "stage": "财务", "metric_key": "net_interest_margin", "metric_name": "净息差", "definition": "利息净收入/生息资产平均余额", "sql_template": _tpl("net_interest_margin", "business", "AVG(net_interest_margin)")},
    {"loan_product": "common", "stage": "财务", "metric_key": "raroc", "metric_name": "风险收益比(RAROC)", "definition": "风险调整后收益率", "sql_template": _tpl("raroc", "business", "AVG(raroc)")},
    {"loan_product": "common", "stage": "财务", "metric_key": "cost_income_ratio", "metric_name": "成本收入比", "definition": "营业成本/营业收入", "sql_template": _tpl("cost_income_ratio", "business", "AVG(cost_income_ratio)")},
    {"loan_product": "common", "stage": "风险", "metric_key": "migration_rate_m1_m3", "metric_name": "迁徙率(M1->M3)", "definition": "M1逾期滚动至M3的迁徙比例", "sql_template": _tpl("migration_rate_m1_m3", "business", "AVG(migration_rate_m1_to_m3)")},
    {"loan_product": "common", "stage": "风险", "metric_key": "provision_coverage", "metric_name": "拨备覆盖率", "definition": "贷款损失准备/不良贷款余额", "sql_template": _tpl("provision_coverage", "business", "AVG(provision_coverage)")},
    {"loan_product": "common", "stage": "风险", "metric_key": "capital_adequacy_ratio", "metric_name": "资本充足率", "definition": "资本净额/风险加权资产", "sql_template": _tpl("capital_adequacy_ratio", "business", "AVG(capital_adequacy_ratio)")},
]
