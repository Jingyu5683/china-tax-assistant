#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CT-003 所得税亏损弥补 · 交互计算脚本
版本: v1.0
用途: 逐年跟踪可弥补亏损余额、测算税盾价值、评估弥补策略

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


def run(params):
    losses = params.get("losses", [])  # [{year, amount, type: "general"/"hightech"}]
    future_profits = params.get("future_profits", [])  # [{year, taxable_income}]
    tax_rate = params.get("tax_rate", 0.25)
    discount_rate = params.get("discount_rate", 0.08)

    # 弥补期限
    CARRYFORWARD_YEARS = {
        "general": 5,
        "hightech": 10,
        "tech_sme": 10,
        "ic": 10,
    }

    print(f"\n{'='*60}")
    print(f"CT-003 所得税亏损弥补 · 估算计算")
    print(f"{'='*60}")

    # 构建亏损台账
    print(f"\n📋 输入参数:")
    print(f"  所得税税率: {tax_rate*100:.1f}%")
    print(f"  折现率: {discount_rate*100:.1f}%")

    loss_ledger = []
    print(f"\n  历史亏损记录:")
    for l in losses:
        period = CARRYFORWARD_YEARS.get(l.get("type", "general"), 5)
        expiry_year = l["year"] + period
        loss_ledger.append({
            "year": l["year"],
            "amount": l["amount"],
            "type": l.get("type", "general"),
            "period": period,
            "expiry_year": expiry_year,
            "remaining": l["amount"],
            "offsets": {},  # {弥补年度: 弥补额}
            "status": "active",
        })
        print(f"    {l['year']}年: {l['amount']:,.2f} 元 ({l.get('type', 'general')}, 期限{period}年, 到期{expiry_year}年)")

    print(f"\n  预计未来利润:")
    for p in future_profits:
        print(f"    {p['year']}年: {p['taxable_income']:,.2f} 元")

    # 逐年弥补计算 (FIFO)
    print(f"\n{'─'*60}")
    print(f"逐年弥补计算")
    print(f"{'─'*60}")

    yearly_results = []
    total_tax_saving_npv = 0

    for fp in future_profits:
        year = fp["year"]
        available_income = fp["taxable_income"]
        year_offsets = []

        if available_income <= 0:
            # 当年亏损
            loss_type = fp.get("type", "general")
            period = CARRYFORWARD_YEARS.get(loss_type, 5)
            loss_ledger.append({
                "year": year,
                "amount": abs(available_income),
                "type": loss_type,
                "period": period,
                "expiry_year": year + period,
                "remaining": abs(available_income),
                "offsets": {},
                "status": "active",
            })
            yearly_results.append({
                "year": year,
                "taxable_income": available_income,
                "total_offset": 0,
                "remaining_income": available_income,
                "details": [],
            })
            print(f"\n  {year}年: 当年亏损 {abs(available_income):,.2f} 元，无弥补")
            continue

        # FIFO弥补：先到期的先用
        total_offset = 0
        for ledger_entry in sorted(loss_ledger, key=lambda x: x["expiry_year"]):
            if ledger_entry["remaining"] <= 0 or ledger_entry["expiry_year"] <= year:
                continue
            if available_income <= 0:
                break

            offset = min(ledger_entry["remaining"], available_income)
            ledger_entry["remaining"] -= offset
            ledger_entry["offsets"][year] = offset
            available_income -= offset
            total_offset += offset
            year_offsets.append({
                "loss_year": ledger_entry["year"],
                "amount": offset,
                "loss_remaining_after": ledger_entry["remaining"],
            })

        tax_saving = total_offset * tax_rate
        # 折现（从亏损年度到弥补年度的时间价值简化处理：按弥补年度折现）
        years_from_now = 0
        for fo in future_profits:
            if fo["year"] <= year:
                years_from_now += 1
        npv_saving = tax_saving / ((1 + discount_rate) ** years_from_now)
        total_tax_saving_npv += npv_saving

        yearly_results.append({
            "year": year,
            "taxable_income": fp["taxable_income"],
            "total_offset": total_offset,
            "remaining_income": available_income,
            "tax_saving": round(tax_saving, 2),
            "npv_saving": round(npv_saving, 2),
            "details": year_offsets,
        })

        print(f"\n  {year}年: 纳税调整后所得 {fp['taxable_income']:,.2f} 元")
        for yo in year_offsets:
            print(f"    → 弥补{yo['loss_year']}年亏损: {yo['amount']:,.2f} 元 (剩余 {yo['loss_remaining_after']:,.2f})")
        print(f"    弥补合计: {total_offset:,.2f} 元 | 节税: {tax_saving:,.2f} 元 | 节税现值: {npv_saving:,.2f} 元")

    # 亏损余额跟踪表
    print(f"\n{'─'*60}")
    print(f"亏损余额跟踪")
    print(f"{'─'*60}")
    print(f"  {'亏损年度':>6} | {'原始亏损':>14} | {'剩余余额':>14} | {'到期年度':>6} | 状态")
    print(f"  {'─'*6}─┼─{'─'*14}─┼─{'─'*14}─┼─{'─'*6}─┼─{'─'*10}")

    total_remaining = 0
    total_expired = 0
    for entry in sorted(loss_ledger, key=lambda x: x["year"]):
        if entry["remaining"] > 0:
            total_remaining += entry["remaining"]
            # 判断是否即将到期
            last_profit_year = max(fp["year"] for fp in future_profits) if future_profits else 0
            if entry["expiry_year"] <= last_profit_year:
                status = "⚠️到期未弥补"
                total_expired += entry["remaining"]
            else:
                status = "正常"
        else:
            status = "✅已弥补"

        print(f"  {entry['year']:>6} | {entry['amount']:>14,.2f} | {entry['remaining']:>14,.2f} | {entry['expiry_year']:>6} | {status}")

    # 税盾价值汇总
    print(f"\n{'─'*60}")
    print(f"税盾价值汇总")
    print(f"{'─'*60}")
    print(f"  可弥补亏损余额合计: {total_remaining:,.2f} 元")
    print(f"  亏损税盾总价值: {total_remaining * tax_rate:,.2f} 元")
    print(f"  已实现节税折现值: {total_tax_saving_npv:,.2f} 元")
    if total_expired > 0:
        print(f"  ⚠️ 到期未弥补亏损: {total_expired:,.2f} 元 (损失税盾 {total_expired * tax_rate:,.2f} 元)")

    # 弥补策略建议
    print(f"\n{'─'*60}")
    print(f"弥补策略提示")
    print(f"{'─'*60}")

    for entry in sorted(loss_ledger, key=lambda x: x["expiry_year"]):
        if entry["remaining"] > 0:
            last_profit_year = max(fp["year"] for fp in future_profits) if future_profits else 0
            years_left = entry["expiry_year"] - last_profit_year
            if years_left <= 2 and years_left > 0:
                print(f"  ⚠️ {entry['year']}年亏损 {entry['remaining']:,.2f} 元 将在{years_left}年后到期，建议评估是否需要加速弥补")
            elif years_left <= 0:
                print(f"  ❌ {entry['year']}年亏损 {entry['remaining']:,.2f} 元 已到期无法弥补")

    print(DISCLAIMER)

    return {
        "yearly_results": yearly_results,
        "total_remaining": total_remaining,
        "tax_shield_value": total_remaining * tax_rate,
        "realized_npv": total_tax_saving_npv,
        "expired_loss": total_expired,
    }


if __name__ == "__main__":
    example_params = {
        "losses": [
            {"year": 2022, "amount": 5000000, "type": "general"},
            {"year": 2023, "amount": 3000000, "type": "general"},
            {"year": 2024, "amount": 1000000, "type": "hightech"},
        ],
        "future_profits": [
            {"year": 2025, "taxable_income": 2000000},
            {"year": 2026, "taxable_income": 4000000},
            {"year": 2027, "taxable_income": 5000000},
            {"year": 2028, "taxable_income": 6000000},
        ],
        "tax_rate": 0.25,
        "discount_rate": 0.08,
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
