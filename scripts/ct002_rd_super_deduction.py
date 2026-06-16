#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CT-002 研发费用加计扣除 · 交互计算脚本
版本: v1.0
用途: ①基于研发预算测算加计扣除节税额 ②倒推高新/软件企业指标上下限

⚠️ 本脚本输出结果仅作为估算参考，不构成税务建议。
   最终方案测算需根据企业实际情况调整基础假设，建议咨询专业税务机构。
"""

import json
import sys
import math

DISCLAIMER = """
╔══════════════════════════════════════════════════════════════════╗
║  ⚠️  重要声明                                                    ║
║  本计算结果仅作为估算参考，不构成税务建议。                       ║
║  最终方案测算需根据企业实际情况调整基础假设。                     ║
║  建议结合实际情况咨询专业税务机构。                               ║
╚══════════════════════════════════════════════════════════════════╝
"""


def calc_part_a(expenses, super_deduction_rate, tax_rate):
    """
    Part A: 基于研发费用归集表计算加计扣除额和节税额
    expenses: {
        "personnel": 人员人工费用,
        "direct_input": 直接投入费用,
        "depreciation": 折旧费用,
        "amortization": 无形资产摊销,
        "design": 新产品设计费等,
        "other_related": 其他相关费用,
        "entrusted_domestic": 委托外部研发（境内）,
        "entrusted_overseas": 委托外部研发（境外）,
    }
    """
    # Step 1: 委托外部研发限额调整
    domestic_entrust_deductible = expenses["entrusted_domestic"] * 0.80

    # 境外委托限额
    domestic_self_total = (expenses["personnel"] + expenses["direct_input"] +
                          expenses["depreciation"] + expenses["amortization"] +
                          expenses["design"])
    overseas_limit = min(expenses["entrusted_overseas"] * 0.80,
                         domestic_self_total * 2 / 3)
    overseas_entrust_deductible = overseas_limit

    # 委托调整额
    domestic_adjustment = expenses["entrusted_domestic"] - domestic_entrust_deductible
    overseas_adjustment = expenses["entrusted_overseas"] - overseas_entrust_deductible
    total_entrust_adjustment = domestic_adjustment + overseas_adjustment

    # Step 2: 其他相关费用限额
    five_items_sum = (expenses["personnel"] + expenses["direct_input"] +
                      expenses["depreciation"] + expenses["amortization"] +
                      expenses["design"] + domestic_entrust_deductible +
                      overseas_entrust_deductible)
    other_limit = five_items_sum * 0.10 / (1 - 0.10)  # 10%限额公式
    other_deductible = min(expenses["other_related"], other_limit)
    other_adjustment = max(expenses["other_related"] - other_limit, 0)

    # Step 3: 计算加计扣除
    total_expenses = sum(expenses.values())
    adjusted_expenses = total_expenses - total_entrust_adjustment - other_adjustment
    super_deduction_amount = adjusted_expenses * super_deduction_rate
    tax_saving = super_deduction_amount * tax_rate

    # 政府补助冲减（如有）
    gov_subsidy_deduction = expenses.get("gov_subsidy_offset", 0)
    if gov_subsidy_deduction > 0:
        adjusted_expenses -= gov_subsidy_deduction
        super_deduction_amount = adjusted_expenses * super_deduction_rate
        tax_saving = super_deduction_amount * tax_rate

    result = {
        "total_raw_expenses": round(total_expenses, 2),
        "domestic_entrust_deductible": round(domestic_entrust_deductible, 2),
        "overseas_entrust_deductible": round(overseas_entrust_deductible, 2),
        "total_entrust_adjustment": round(total_entrust_adjustment, 2),
        "other_related_limit": round(other_limit, 2),
        "other_related_deductible": round(other_deductible, 2),
        "other_adjustment": round(other_adjustment, 2),
        "adjusted_deductible_expenses": round(adjusted_expenses, 2),
        "super_deduction_rate": super_deduction_rate,
        "super_deduction_amount": round(super_deduction_amount, 2),
        "tax_rate": tax_rate,
        "tax_saving": round(tax_saving, 2),
    }

    return result


def calc_part_b_hightech(revenue_3y, employee_count, total_revenue_current,
                         tech_personnel_count=0, ht_revenue_current=0):
    """
    Part B: 倒推高新技术企业指标上下限
    """
    # 研发费用占比分档
    if revenue_3y <= 50000000:  # 5000万
        rd_ratio_min = 0.05
        scale_label = "≤5000万"
    elif revenue_3y <= 200000000:  # 2亿
        rd_ratio_min = 0.04
        scale_label = "5000万~2亿"
    else:
        rd_ratio_min = 0.03
        scale_label = ">2亿"

    rd_min_3y = revenue_3y * rd_ratio_min
    rd_min_annual = rd_min_3y / 3

    # 科技人员
    tech_personnel_min = math.ceil(employee_count * 0.10)
    if tech_personnel_count > 0:
        tech_ratio = tech_personnel_count / employee_count
        tech_status = "✅达标" if tech_ratio >= 0.10 else "❌不达标"
    else:
        tech_ratio = 0
        tech_status = "⚠️未填写"

    # 高新收入
    ht_revenue_min = total_revenue_current * 0.60
    if ht_revenue_current > 0:
        ht_ratio = ht_revenue_current / total_revenue_current
        ht_status = "✅达标" if ht_ratio >= 0.60 else "❌不达标"
    else:
        ht_ratio = 0
        ht_status = "⚠️未填写"

    result = {
        "scale_label": scale_label,
        "revenue_3y": revenue_3y,
        "rd_ratio_min": rd_ratio_min,
        "rd_min_3y": round(rd_min_3y, 2),
        "rd_min_annual": round(rd_min_annual, 2),
        "employee_count": employee_count,
        "tech_personnel_min": tech_personnel_min,
        "tech_personnel_count": tech_personnel_count,
        "tech_ratio": round(tech_ratio, 4),
        "tech_status": tech_status,
        "ht_revenue_min": round(ht_revenue_min, 2),
        "ht_revenue_current": ht_revenue_current,
        "ht_ratio": round(ht_ratio, 4),
        "ht_status": ht_status,
    }

    return result


def calc_part_b_software(total_revenue, employee_count):
    """
    Part B: 倒推软件企业指标上下限
    """
    result = {
        "total_revenue": total_revenue,
        "self_sw_revenue_min": round(total_revenue * 0.40, 2),
        "sw_product_revenue_min": round(total_revenue * 0.50, 2),
        "rd_expense_min": round(total_revenue * 0.06, 2),
        "domestic_rd_min": round(total_revenue * 0.06 * 0.60, 2),
        "rd_personnel_min": math.ceil(employee_count * 0.20),
        "employee_count": employee_count,
    }
    return result


def run(params):
    print(f"\n{'='*60}")
    print(f"CT-002 研发费用加计扣除 · 估算计算")
    print(f"{'='*60}")

    part = params.get("part", "A")  # A or B or both

    if part in ("A", "both"):
        expenses = params.get("expenses", {})
        super_rate = params.get("super_deduction_rate", 1.00)
        tax_rate = params.get("tax_rate", 0.25)

        print(f"\n📋 Part A 输入参数:")
        for k, v in expenses.items():
            print(f"  {k}: {v:,.2f}" if isinstance(v, (int, float)) else f"  {k}: {v}")
        print(f"  加计扣除比例: {super_rate*100:.0f}%")
        print(f"  所得税税率: {tax_rate*100:.1f}%")

        result_a = calc_part_a(expenses, super_rate, tax_rate)

        print(f"\n{'─'*60}")
        print(f"Part A: 加计扣除计算结果")
        print(f"{'─'*60}")
        print(f"  研发费用总额: {result_a['total_raw_expenses']:,.2f} 元")
        print(f"  ─── 委托外部研发调整 ───")
        print(f"  境内委托可计入: {result_a['domestic_entrust_deductible']:,.2f} 元")
        print(f"  境外委托可计入: {result_a['overseas_entrust_deductible']:,.2f} 元")
        print(f"  委托调整额(调减): {result_a['total_entrust_adjustment']:,.2f} 元")
        print(f"  ─── 其他相关费用调整 ───")
        print(f"  其他相关费用限额: {result_a['other_related_limit']:,.2f} 元")
        print(f"  其他相关费用可计入: {result_a['other_related_deductible']:,.2f} 元")
        print(f"  其他相关费用调整额(调减): {result_a['other_adjustment']:,.2f} 元")
        print(f"  ─── 汇总 ───")
        print(f"  调整后可加计扣除研发费用: {result_a['adjusted_deductible_expenses']:,.2f} 元")
        print(f"  加计扣除额: {result_a['super_deduction_amount']:,.2f} 元")
        print(f"  🎯 节税额: {result_a['tax_saving']:,.2f} 元")

    if part in ("B", "both"):
        print(f"\n{'─'*60}")
        print(f"Part B: 高新/软件企业指标倒推")
        print(f"{'─'*60}")

        # 高新指标
        hightech = params.get("hightech", {})
        if hightech:
            result_b_ht = calc_part_b_hightech(
                revenue_3y=hightech.get("revenue_3y", 0),
                employee_count=hightech.get("employee_count", 0),
                total_revenue_current=hightech.get("total_revenue_current", 0),
                tech_personnel_count=hightech.get("tech_personnel_count", 0),
                ht_revenue_current=hightech.get("ht_revenue_current", 0),
            )

            print(f"\n  📊 高新技术企业指标倒推")
            print(f"  近三年销售收入规模: {result_b_ht['scale_label']}")
            print(f"  近三年销售收入总额: {result_b_ht['revenue_3y']:,.2f} 元")
            print(f"  ─── 研发费用占比 ───")
            print(f"  最低占比要求: {result_b_ht['rd_ratio_min']*100:.0f}%")
            print(f"  三年研发费用最低合计: {result_b_ht['rd_min_3y']:,.2f} 元")
            print(f"  年均研发费用最低: {result_b_ht['rd_min_annual']:,.2f} 元")
            print(f"  ─── 科技人员占比 ───")
            print(f"  企业职工总数: {result_b_ht['employee_count']}")
            print(f"  最低科技人员数: {result_b_ht['tech_personnel_min']} 人")
            if result_b_ht['tech_personnel_count'] > 0:
                print(f"  实际科技人员: {result_b_ht['tech_personnel_count']} 人 (占比 {result_b_ht['tech_ratio']*100:.1f}% {result_b_ht['tech_status']})")
            print(f"  ─── 高新技术产品/服务收入占比 ───")
            print(f"  最低高新收入: {result_b_ht['ht_revenue_min']:,.2f} 元")
            if result_b_ht['ht_revenue_current'] > 0:
                print(f"  实际高新收入: {result_b_ht['ht_revenue_current']:,.2f} 元 (占比 {result_b_ht['ht_ratio']*100:.1f}% {result_b_ht['ht_status']})")

        # 软件企业指标
        software = params.get("software", {})
        if software:
            result_b_sw = calc_part_b_software(
                total_revenue=software.get("total_revenue", 0),
                employee_count=software.get("employee_count", 0),
            )

            print(f"\n  📊 软件企业指标倒推")
            print(f"  企业预计总收入: {result_b_sw['total_revenue']:,.2f} 元")
            print(f"  自主软件收入最低额: {result_b_sw['self_sw_revenue_min']:,.2f} 元 (≥40%)")
            print(f"  软件产品收入最低额: {result_b_sw['sw_product_revenue_min']:,.2f} 元 (≥50%)")
            print(f"  研发费用最低额: {result_b_sw['rd_expense_min']:,.2f} 元 (≥6%)")
            print(f"  境内研发费用最低额: {result_b_sw['domestic_rd_min']:,.2f} 元 (≥60%)")
            print(f"  研发人员最低数: {result_b_sw['rd_personnel_min']} 人 (≥20%)")

    print(DISCLAIMER)


if __name__ == "__main__":
    example_params = {
        "part": "both",
        "expenses": {
            "personnel": 2000000,
            "direct_input": 1500000,
            "depreciation": 300000,
            "amortization": 200000,
            "design": 500000,
            "other_related": 800000,
            "entrusted_domestic": 600000,
            "entrusted_overseas": 400000,
        },
        "super_deduction_rate": 1.00,
        "tax_rate": 0.25,
        "hightech": {
            "revenue_3y": 150000000,
            "employee_count": 200,
            "total_revenue_current": 60000000,
            "tech_personnel_count": 30,
            "ht_revenue_current": 40000000,
        },
        "software": {
            "total_revenue": 30000000,
            "employee_count": 100,
        },
    }

    if len(sys.argv) > 1:
        try:
            params = json.loads(sys.argv[1])
        except json.JSONDecodeError:
            print("参数格式错误，请传入有效JSON")
            sys.exit(1)
    else:
        params = example_params

    run(params)
