#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CT-001 固定资产一次性税前扣除 · 交互计算脚本
版本: v1.0
用途: 对比"正常折旧"与"一次性扣除"两种方案的现金流差异

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


def calc_normal_depreciation(asset_cost, dep_years, residual_rate, tax_rate,
                              annual_revenue, annual_variable_cost,
                              annual_fixed_cost, discount_rate):
    """v1: 正常折旧方案"""
    annual_dep = asset_cost * (1 - residual_rate) / dep_years
    rows = []
    cumulative_npv = 0

    for y in range(1, dep_years + 1):
        pre_tax_profit = annual_revenue - annual_variable_cost - annual_fixed_cost - annual_dep
        tax_adjustment = 0  # 税法折旧 = 会计折旧，无差异
        taxable_income = pre_tax_profit + tax_adjustment
        tax = max(taxable_income * tax_rate, 0) if taxable_income > 0 else 0
        net_profit = pre_tax_profit - tax
        operating_cf = net_profit + annual_dep
        # 第1年扣除初始投资
        project_cf = operating_cf - (asset_cost if y == 1 else 0)
        npv = project_cf / ((1 + discount_rate) ** y)
        cumulative_npv += npv

        rows.append({
            "year": y,
            "dep": round(annual_dep, 2),
            "tax_adjustment": round(tax_adjustment, 2),
            "taxable_income": round(taxable_income, 2),
            "tax": round(tax, 2),
            "net_profit": round(net_profit, 2),
            "operating_cf": round(operating_cf, 2),
            "project_cf": round(project_cf, 2),
            "npv": round(npv, 2),
        })

    return rows, round(cumulative_npv, 2), round(annual_dep, 2)


def calc_accelerated_deduction(asset_cost, dep_years, residual_rate, tax_rate,
                                annual_revenue, annual_variable_cost,
                                annual_fixed_cost, discount_rate):
    """v2: 一次性扣除方案"""
    annual_dep_accounting = asset_cost * (1 - residual_rate) / dep_years
    rows = []
    cumulative_npv = 0
    dtl_balance = 0

    for y in range(1, dep_years + 1):
        pre_tax_profit = annual_revenue - annual_variable_cost - annual_fixed_cost - annual_dep_accounting
        # 税法折旧：第1年全额，之后为0
        tax_dep = asset_cost if y == 1 else 0
        tax_adjustment = annual_dep_accounting - tax_dep  # 第1年负(调减)，之后正(调增)
        taxable_income = pre_tax_profit + tax_adjustment
        tax = max(taxable_income * tax_rate, 0) if taxable_income > 0 else 0
        net_profit = pre_tax_profit - tax
        operating_cf = net_profit + annual_dep_accounting
        project_cf = operating_cf - (asset_cost if y == 1 else 0)
        npv = project_cf / ((1 + discount_rate) ** y)
        cumulative_npv += npv

        # 递延所得税
        if y == 1:
            dtl = (tax_dep - annual_dep_accounting) * tax_rate
            dtl_balance = dtl
        else:
            dtl_change = (annual_dep_accounting - tax_dep) * tax_rate  # 转回
            dtl_balance -= dtl_change

        rows.append({
            "year": y,
            "dep_accounting": round(annual_dep_accounting, 2),
            "dep_tax": round(tax_dep, 2),
            "tax_adjustment": round(tax_adjustment, 2),
            "taxable_income": round(taxable_income, 2),
            "tax": round(tax, 2),
            "net_profit": round(net_profit, 2),
            "operating_cf": round(operating_cf, 2),
            "project_cf": round(project_cf, 2),
            "npv": round(npv, 2),
            "dtl_balance": round(max(dtl_balance, 0), 2),
        })

    return rows, round(cumulative_npv, 2)


def compare_plans(v1_rows, v2_rows, tax_rate, discount_rate):
    """v1 vs v2 现金流差异对比"""
    diff_rows = []
    total_npv_diff = 0

    for r1, r2 in zip(v1_rows, v2_rows):
        tax_diff = r1["tax"] - r2["tax"]
        npv_diff = tax_diff / ((1 + discount_rate) ** r1["year"])
        total_npv_diff += npv_diff
        diff_rows.append({
            "year": r1["year"],
            "v1_tax": r1["tax"],
            "v2_tax": r2["tax"],
            "tax_diff": round(tax_diff, 2),
            "npv_diff": round(npv_diff, 2),
        })

    return diff_rows, round(total_npv_diff, 2)


def quick_tax_shield(asset_cost, dep_years, residual_rate, tax_rate, discount_rate):
    """简化速算：一次性扣除的税盾收益"""
    annual_dep = asset_cost * (1 - residual_rate) / dep_years

    # 第1年税盾
    year1_shield = asset_cost * tax_rate / ((1 + discount_rate) ** 1)

    # 第2~N年税盾回吐
    payback_total = 0
    for y in range(2, dep_years + 1):
        payback = annual_dep * tax_rate / ((1 + discount_rate) ** y)
        payback_total += payback

    net_benefit = year1_shield - payback_total
    return round(year1_shield, 2), round(payback_total, 2), round(net_benefit, 2)


def format_table(headers, rows, col_widths=None):
    """格式化表格输出"""
    if not col_widths:
        col_widths = [max(len(str(h)), max(len(str(r.get(h, ""))) for r in rows)) + 2 for h in headers]

    line = "+" + "+".join("-" * w for w in col_widths) + "+"
    header_line = "|" + "|".join(str(h).center(w) for h, w in zip(headers, col_widths)) + "|"

    result = [line, header_line, line]
    for row in rows:
        row_line = "|" + "|".join(str(row.get(h, "")).center(w) for h, w in zip(headers, col_widths)) + "|"
        result.append(row_line)
    result.append(line)
    return "\n".join(result)


def run(params):
    asset_cost = params["asset_cost"]
    dep_years = params["dep_years"]
    residual_rate = params.get("residual_rate", 0.05)
    tax_rate = params["tax_rate"]
    annual_revenue = params.get("annual_revenue", 0)
    annual_variable_cost = params.get("annual_variable_cost", 0)
    annual_fixed_cost = params.get("annual_fixed_cost", 0)
    discount_rate = params.get("discount_rate", 0.08)

    print(f"\n{'='*60}")
    print(f"CT-001 固定资产一次性税前扣除 · 估算计算")
    print(f"{'='*60}")
    print(f"\n📋 输入参数:")
    print(f"  设备原值: {asset_cost:,.2f} 元")
    print(f"  折旧年限: {dep_years} 年")
    print(f"  残值率: {residual_rate*100:.1f}%")
    print(f"  所得税税率: {tax_rate*100:.1f}%")
    print(f"  折现率: {discount_rate*100:.1f}%")
    if annual_revenue:
        print(f"  年增加收入: {annual_revenue:,.2f} 元")
        print(f"  年变动付现成本: {annual_variable_cost:,.2f} 元")
        print(f"  年固定付现成本: {annual_fixed_cost:,.2f} 元")

    # v1 正常折旧
    v1_rows, v1_npv, annual_dep = calc_normal_depreciation(
        asset_cost, dep_years, residual_rate, tax_rate,
        annual_revenue, annual_variable_cost, annual_fixed_cost, discount_rate
    )

    # v2 一次性扣除
    v2_rows, v2_npv = calc_accelerated_deduction(
        asset_cost, dep_years, residual_rate, tax_rate,
        annual_revenue, annual_variable_cost, annual_fixed_cost, discount_rate
    )

    print(f"\n{'─'*60}")
    print(f"方案v1: 正常折旧（年折旧额 {annual_dep:,.2f} 元）")
    print(f"{'─'*60}")
    if annual_revenue:
        headers = ["year", "tax", "net_profit", "project_cf", "npv"]
        print(format_table(headers, v1_rows))
    else:
        # 简化模式：只看税和现金流
        for r in v1_rows:
            print(f"  第{r['year']}年: 折旧 {r['dep']:,.2f} | 所得税 {r['tax']:,.2f} | 净利润 {r['net_profit']:,.2f}")
    print(f"  NPV合计: {v1_npv:,.2f} 元")

    print(f"\n{'─'*60}")
    print(f"方案v2: 一次性扣除")
    print(f"{'─'*60}")
    if annual_revenue:
        headers = ["year", "dep_accounting", "dep_tax", "tax_adjustment", "tax", "net_profit", "project_cf", "npv"]
        print(format_table(headers, v2_rows))
    else:
        for r in v2_rows:
            print(f"  第{r['year']}年: 会计折旧 {r['dep_accounting']:,.2f} | 税法折旧 {r['dep_tax']:,.2f} | 纳税调增(减) {r['tax_adjustment']:,.2f} | 所得税 {r['tax']:,.2f} | DTL余额 {r['dtl_balance']:,.2f}")
    print(f"  NPV合计: {v2_npv:,.2f} 元")

    # 对比
    diff_rows, total_npv_diff = compare_plans(v1_rows, v2_rows, tax_rate, discount_rate)
    print(f"\n{'─'*60}")
    print(f"v1 vs v2 对比（所得税差异）")
    print(f"{'─'*60}")
    for r in diff_rows:
        print(f"  第{r['year']}年: v1税 {r['v1_tax']:,.2f} | v2税 {r['v2_tax']:,.2f} | 差异 {r['tax_diff']:,.2f} | 折现差异 {r['npv_diff']:,.2f}")
    print(f"  NPV差异合计: {total_npv_diff:,.2f} 元")

    # 简化速算
    shield_y1, payback, net_benefit = quick_tax_shield(
        asset_cost, dep_years, residual_rate, tax_rate, discount_rate
    )
    print(f"\n{'─'*60}")
    print(f"简化速算（仅考虑折旧差异的税盾收益）")
    print(f"{'─'*60}")
    print(f"  第1年税盾收益: {shield_y1:,.2f} 元")
    print(f"  第2~{dep_years}年税盾回吐: {payback:,.2f} 元")
    print(f"  净收益: {net_benefit:,.2f} 元")

    if net_benefit > 0:
        print(f"\n  ✅ 一次性扣除方案更优，净税盾收益 {net_benefit:,.2f} 元")
    elif net_benefit == 0:
        print(f"\n  ➡️ 两方案等价")
    else:
        print(f"\n  ⚠️ 正常折旧方案更优（可能因亏损抵扣受限）")

    print(DISCLAIMER)

    return {
        "v1_npv": v1_npv,
        "v2_npv": v2_npv,
        "npv_diff": total_npv_diff,
        "net_tax_shield": net_benefit,
        "v1_rows": v1_rows,
        "v2_rows": v2_rows,
    }


if __name__ == "__main__":
    # 示例参数
    example_params = {
        "asset_cost": 3000000,       # 设备原值 300万
        "dep_years": 5,              # 折旧5年
        "residual_rate": 0.05,      # 残值率5%
        "tax_rate": 0.25,           # 所得税税率25%
        "annual_revenue": 1000000,  # 年增加收入100万
        "annual_variable_cost": 300000,  # 年变动成本30万
        "annual_fixed_cost": 100000,    # 年固定成本10万
        "discount_rate": 0.08,      # 折现率8%
    }

    # 如果通过命令行传JSON参数
    if len(sys.argv) > 1:
        try:
            params = json.loads(sys.argv[1])
        except json.JSONDecodeError:
            print("参数格式错误，请传入有效JSON")
            sys.exit(1)
    else:
        params = example_params

    result = run(params)
