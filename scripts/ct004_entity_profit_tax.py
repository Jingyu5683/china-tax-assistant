#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CT-004 单体利润及各项税费 · 交互计算脚本
版本: v1.0
用途: 从收入到净利润全链路 + 各税种计算 + 税负结构分析

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


def calc_vat(params):
    """增值税计算"""
    vat = params.get("vat", {})
    output_tax = vat.get("output_tax", 0)         # 销项税额
    input_tax = vat.get("input_tax", 0)           # 进项税额
    input_transfer = vat.get("input_transfer", 0)  # 进项税额转出
    prior_credit = vat.get("prior_credit", 0)      # 上期留抵
    simple_tax = vat.get("simple_tax", 0)          # 简易计税

    net_input = input_tax - input_transfer
    general_vat = output_tax - net_input - prior_credit
    total_vat = general_vat + simple_tax

    # 留抵判断
    if general_vat < 0:
        credit_carryforward = abs(general_vat)
        general_vat = 0
    else:
        credit_carryforward = 0

    return {
        "output_tax": output_tax,
        "input_tax": input_tax,
        "input_transfer": input_transfer,
        "net_input": net_input,
        "prior_credit": prior_credit,
        "general_vat": round(general_vat, 2),
        "simple_tax": simple_tax,
        "total_vat": round(total_vat, 2),
        "credit_carryforward": round(credit_carryforward, 2),
    }


def calc_surtaxes(total_vat, consumption_tax, params):
    """城建税+教育费附加"""
    st = params.get("surtaxes", {})
    base = total_vat + consumption_tax
    urban_rate = st.get("urban_maintenance_rate", 0.07)  # 7%/5%/1%
    edu_rate = 0.03
    local_edu_rate = 0.02

    urban = base * urban_rate
    edu = base * edu_rate
    local_edu = base * local_edu_rate
    total = urban + edu + local_edu

    return {
        "base": round(base, 2),
        "urban_maintenance": round(urban, 2),
        "education_surcharge": round(edu, 2),
        "local_education": round(local_edu, 2),
        "total_surtaxes": round(total, 2),
    }


def calc_other_taxes(params):
    """印花税/房产税/土地使用税等"""
    ot = params.get("other_taxes", {})
    stamp = ot.get("stamp_tax", 0)
    property_tax = ot.get("property_tax", 0)
    land_tax = ot.get("land_use_tax", 0)
    vehicle_tax = ot.get("vehicle_tax", 0)
    env_tax = ot.get("env_tax", 0)
    total = stamp + property_tax + land_tax + vehicle_tax + env_tax

    return {
        "stamp_tax": stamp,
        "property_tax": property_tax,
        "land_use_tax": land_tax,
        "vehicle_tax": vehicle_tax,
        "env_tax": env_tax,
        "total_other": round(total, 2),
    }


def calc_income_tax(profit_total, tax_adjustments, loss_offset, params):
    """企业所得税计算"""
    it = params.get("income_tax", {})
    rate = it.get("rate", 0.25)

    # 小微判断
    is_small = it.get("is_small_micro", False)

    taxable_income = profit_total + tax_adjustments.get("net_adjustment", 0) - loss_offset

    if is_small and taxable_income > 0 and taxable_income <= 3000000:
        # 小微优惠：25%计入×20%税率 = 实际5%
        cit = taxable_income * 0.25 * 0.20
        effective_rate = 0.05
    else:
        cit = max(taxable_income * rate, 0) if taxable_income > 0 else 0
        effective_rate = rate

    return {
        "profit_total": profit_total,
        "net_adjustment": tax_adjustments.get("net_adjustment", 0),
        "loss_offset": loss_offset,
        "taxable_income": round(taxable_income, 2),
        "rate": rate,
        "is_small_micro": is_small,
        "cit": round(cit, 2),
        "effective_rate": effective_rate,
    }


def run(params):
    print(f"\n{'='*60}")
    print(f"CT-004 单体利润及各项税费 · 估算计算")
    print(f"{'='*60}")

    # ===== 3-1 营业利润 =====
    p = params.get("profit", {})
    revenue = p.get("revenue", 0)
    cost = p.get("cost", 0)
    gross_profit = revenue - cost
    gross_margin = gross_profit / revenue if revenue else 0

    period_expenses = p.get("period_expenses", 0)
    rd_expense = p.get("rd_expense", 0)
    interest_expense = p.get("interest_expense", 0)
    other_income = p.get("other_income", 0)
    investment_income = p.get("investment_income", 0)
    credit_impairment = p.get("credit_impairment", 0)
    asset_impairment = p.get("asset_impairment", 0)

    # ===== 增值税 & 税金及附加 =====
    vat_result = calc_vat(params)
    consumption_tax = params.get("consumption_tax", 0)
    surtaxes_result = calc_surtaxes(vat_result["total_vat"], consumption_tax, params)
    other_taxes_result = calc_other_taxes(params)

    total_surcharge = surtaxes_result["total_surtaxes"] + other_taxes_result["total_other"]

    # 营业利润
    operating_profit = (gross_profit - total_surcharge - period_expenses +
                        other_income + investment_income +
                        credit_impairment + asset_impairment)

    # ===== 3-2 利润总额及所得税 =====
    non_operating_income = p.get("non_operating_income", 0)
    non_operating_expense = p.get("non_operating_expense", 0)
    profit_total = operating_profit + non_operating_income - non_operating_expense

    # 纳税调整
    adj = params.get("tax_adjustments", {})
    additions = adj.get("additions", {})
    deductions = adj.get("deductions", {})
    total_additions = sum(additions.values()) if additions else 0
    total_deductions = sum(deductions.values()) if deductions else 0
    net_adjustment = total_additions - total_deductions

    tax_adj_result = {
        "additions": additions,
        "total_additions": round(total_additions, 2),
        "deductions": deductions,
        "total_deductions": round(total_deductions, 2),
        "net_adjustment": round(net_adjustment, 2),
    }

    loss_offset = adj.get("loss_offset", 0)

    # 所得税
    cit_result = calc_income_tax(profit_total, tax_adj_result, loss_offset, params)

    net_profit = profit_total - cit_result["cit"]

    # ===== 输出 =====
    print(f"\n📋 利润表")
    print(f"{'─'*60}")
    print(f"  营业收入:               {revenue:>14,.2f}")
    print(f"  营业成本:               {cost:>14,.2f}")
    print(f"  毛利:                   {gross_profit:>14,.2f}  (毛利率 {gross_margin*100:.1f}%)")
    print(f"  税金及附加:             {total_surcharge:>14,.2f}")
    print(f"    其中: 城建税+教育附加  {surtaxes_result['total_surtaxes']:>14,.2f}")
    print(f"          其他税           {other_taxes_result['total_other']:>14,.2f}")
    print(f"  期间费用:               {period_expenses:>14,.2f}")
    if rd_expense:
        print(f"    其中: 研发费用        {rd_expense:>14,.2f}")
    if interest_expense:
        print(f"    其中: 利息支出        {interest_expense:>14,.2f}")
    print(f"  其他收益:               {other_income:>14,.2f}")
    print(f"  投资收益:               {investment_income:>14,.2f}")
    print(f"  信用减值损失:           {credit_impairment:>14,.2f}")
    print(f"  资产减值损失:           {asset_impairment:>14,.2f}")
    print(f"  ─────────────────────────────────")
    print(f"  营业利润:               {operating_profit:>14,.2f}")
    print(f"  营业外收入:             {non_operating_income:>14,.2f}")
    print(f"  营业外支出:             {non_operating_expense:>14,.2f}")
    print(f"  ─────────────────────────────────")
    print(f"  利润总额:               {profit_total:>14,.2f}")

    # 纳税调整明细
    if total_additions or total_deductions:
        print(f"\n📋 纳税调整明细")
        print(f"{'─'*60}")
        if additions:
            print(f"  纳税调增:")
            for k, v in additions.items():
                if v:
                    print(f"    {k}: {v:>14,.2f}")
        if deductions:
            print(f"  纳税调减:")
            for k, v in deductions.items():
                if v:
                    print(f"    {k}: {v:>14,.2f}")
        print(f"  ─────────────────────────────────")
        print(f"  净调整额: {net_adjustment:>14,.2f}")

    if loss_offset:
        print(f"  弥补以前年度亏损:      {loss_offset:>14,.2f}")

    print(f"\n📋 所得税计算")
    print(f"{'─'*60}")
    print(f"  应纳税所得额:          {cit_result['taxable_income']:>14,.2f}")
    print(f"  适用税率:              {cit_result['rate']*100:.0f}%{'(小微优惠)' if cit_result['is_small_micro'] else ''}")
    print(f"  应交企业所得税:        {cit_result['cit']:>14,.2f}")
    print(f"  实际有效税率:           {cit_result['effective_rate']*100:.1f}%")
    print(f"  ─────────────────────────────────")
    print(f"  净利润:                {net_profit:>14,.2f}")

    # 增值税明细
    print(f"\n📋 增值税计算")
    print(f"{'─'*60}")
    print(f"  销项税额:              {vat_result['output_tax']:>14,.2f}")
    print(f"  进项税额:              {vat_result['input_tax']:>14,.2f}")
    print(f"  进项税额转出:          {vat_result['input_transfer']:>14,.2f}")
    print(f"  上期留抵:              {vat_result['prior_credit']:>14,.2f}")
    print(f"  一般计税应纳增值税:    {vat_result['general_vat']:>14,.2f}")
    print(f"  简易计税:              {vat_result['simple_tax']:>14,.2f}")
    print(f"  ─────────────────────────────────")
    print(f"  本期应交增值税:        {vat_result['total_vat']:>14,.2f}")
    if vat_result['credit_carryforward'] > 0:
        print(f"  期末留抵税额:          {vat_result['credit_carryforward']:>14,.2f}")

    # 税负分析
    print(f"\n📋 综合税负分析")
    print(f"{'─'*60}")

    all_taxes = {
        "增值税": vat_result["total_vat"],
        "城建税+教育附加": surtaxes_result["total_surtaxes"],
        "企业所得税": cit_result["cit"],
        "印花税": other_taxes_result["stamp_tax"],
        "房产税": other_taxes_result["property_tax"],
        "土地使用税": other_taxes_result["land_use_tax"],
        "其他": other_taxes_result["vehicle_tax"] + other_taxes_result["env_tax"],
    }

    total_tax = sum(all_taxes.values())
    print(f"  {'税种':>14} | {'应纳税额':>14} | {'占总税负':>8} | {'占收入':>8}")
    print(f"  {'─'*14}─┼─{'─'*14}─┼─{'─'*8}─┼─{'─'*8}")

    for tax_name, tax_amount in all_taxes.items():
        if tax_amount > 0:
            pct_total = tax_amount / total_tax * 100 if total_tax else 0
            pct_revenue = tax_amount / revenue * 100 if revenue else 0
            print(f"  {tax_name:>14} | {tax_amount:>14,.2f} | {pct_total:>7.1f}% | {pct_revenue:>7.1f}%")

    print(f"  {'─'*14}─┼─{'─'*14}─┼─{'─'*8}─┼─{'─'*8}")
    print(f"  {'合计':>14} | {total_tax:>14,.2f} | {'100.0%':>8} | {total_tax/revenue*100:>7.1f}%" if revenue else "")

    # 核心指标
    print(f"\n📋 核心税负指标")
    print(f"{'─'*60}")
    print(f"  增值税税负率:           {vat_result['total_vat']/revenue*100:.2f}%" if revenue else "  增值税税负率: N/A")
    print(f"  企税实际税负率:         {cit_result['cit']/profit_total*100:.2f}%" if profit_total else "  企税实际税负率: N/A")
    print(f"  综合税负率:             {total_tax/revenue*100:.2f}%" if revenue else "  综合税负率: N/A")
    print(f"  企税有效税率:           {cit_result['effective_rate']*100:.1f}%")

    print(DISCLAIMER)

    return {
        "revenue": revenue,
        "gross_profit": gross_profit,
        "operating_profit": operating_profit,
        "profit_total": profit_total,
        "net_profit": net_profit,
        "total_tax": total_tax,
        "cit": cit_result["cit"],
        "vat": vat_result["total_vat"],
    }


if __name__ == "__main__":
    example_params = {
        "profit": {
            "revenue": 50000000,
            "cost": 35000000,
            "period_expenses": 6000000,
            "rd_expense": 2000000,
            "interest_expense": 500000,
            "other_income": 300000,
            "investment_income": 0,
            "credit_impairment": -100000,
            "asset_impairment": 0,
            "non_operating_income": 50000,
            "non_operating_expense": 20000,
        },
        "vat": {
            "output_tax": 4500000,
            "input_tax": 3200000,
            "input_transfer": 100000,
            "prior_credit": 0,
            "simple_tax": 0,
        },
        "consumption_tax": 0,
        "surtaxes": {
            "urban_maintenance_rate": 0.07,
        },
        "other_taxes": {
            "stamp_tax": 75000,
            "property_tax": 200000,
            "land_use_tax": 50000,
            "vehicle_tax": 10000,
            "env_tax": 0,
        },
        "tax_adjustments": {
            "additions": {
                "业务招待费超标": 80000,
                "职工福利费超标": 50000,
            },
            "deductions": {
                "研发费用加计扣除": 2000000,
                "国债利息收入": 100000,
            },
            "loss_offset": 0,
        },
        "income_tax": {
            "rate": 0.25,
            "is_small_micro": False,
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
