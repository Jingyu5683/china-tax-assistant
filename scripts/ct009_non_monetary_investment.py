#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CT-009 非货币性资产投资递延纳税测算
支持：企业116号文（5年分期计入所得）/ 个人41号文（5年分期缴纳税额）
用法：python ct009_non_monetary_investment.py [JSON参数]
不传参时使用内置示例数据

政策依据（P0）：
- 财税[2014]116号（居民企业非货币性资产投资递延纳税）
- 总局公告2015年第33号（116号文执行口径）
- 财税[2015]41号（个人非货币性资产投资分期纳税）
- 总局公告2015年第20号（41号文执行口径）
- 财税[2009]59号（特殊性税务处理，与116号不可叠加）
- 增值税法 / 财政部 税务总局公告2026年第10号
"""

import json
import sys
import math

# ============================================================
# 内置示例数据
# ============================================================
EXAMPLE_DATA = {
    "investor_type": "enterprise",    # enterprise / individual
    "asset_type": "technology",       # technology / equipment / real_estate / equity / other
    "fair_value": 15000000,           # 评估公允价值（元）
    "tax_base": 2000000,              # 计税基础（元）
    "tax_rate": 0.25,                 # 适用税率（企税25%/高新15%/个税20%）
    "defer_years": 5,                 # 递延年数
    "vat_exempt": True,               # 增值税是否免税（技术出资可免）
    "vat_rate": 0.13,                 # 增值税率（不免时适用）
    "vat_input_credit": 0,            # 可抵扣进项税额
    "consider_npv": True,             # 是否做NPV分析
    "discount_rate": 0.08,            # 折现率
    "early_exit_year": None,          # 提前退出年份（None=不退出，1-5）
    "other_annual_income": 5000000,   # 企业其他年度应纳税所得额（影响边际税率）
    "compare_59wen": True             # 是否对比59号文方案
}


def calc_non_monetary_investment(params: dict) -> dict:
    """非货币性资产投资递延纳税测算主函数"""
    p = {**EXAMPLE_DATA, **params}
    
    fair_value = p["fair_value"]
    tax_base = p["tax_base"]
    transfer_gain = fair_value - tax_base  # 转让所得
    investor = p["investor_type"]
    defer_years = p["defer_years"]
    
    results = {
        "investor_type": investor,
        "asset_type": p["asset_type"],
        "fair_value": fair_value,
        "tax_base": tax_base,
        "transfer_gain": transfer_gain,
        "defer_years": defer_years,
        "enterprise_deferred": None,   # 116号文计算结果
        "individual_deferred": None,   # 41号文计算结果
        "vat": None,                   # 增值税
        "npv_analysis": None,          # NPV分析
        "early_exit_impact": None,     # 递延中断影响
        "compare_59wen": None          # 59号文对比
    }
    
    # ---- 1. 企业116号文递延纳税 ----
    if investor == "enterprise":
        annual_gain = transfer_gain / defer_years  # 每年确认转让所得
        rate = p["tax_rate"]
        
        # 逐年计算
        yearly_details = []
        cumulative_tax_base = tax_base  # 取得股权计税基础
        cumulative_tax = 0
        
        for yr in range(1, defer_years + 1):
            # 每年确认1/5所得
            yr_gain = annual_gain
            # 与其他所得合并计税
            total_taxable = p.get("other_annual_income", 0) + yr_gain
            yr_tax = yr_gain * rate  # 简化：按比例计算（实际可能与所得跨档有关）
            # 计税基础调整
            cumulative_tax_base += yr_gain
            cumulative_tax += yr_tax
            
            yearly_details.append({
                "year": yr,
                "deferred_gain_recognized": round(yr_gain, 2),
                "other_income": p.get("other_annual_income", 0),
                "total_taxable_income": round(total_taxable, 2),
                "tax_on_deferred": round(yr_tax, 2),
                "equity_tax_base": round(cumulative_tax_base, 2),
                "cumulative_tax": round(cumulative_tax, 2)
            })
        
        # 即期纳税总额
        immediate_tax = transfer_gain * rate
        
        results["enterprise_deferred"] = {
            "annual_gain_recognized": round(annual_gain, 2),
            "annual_tax": round(annual_gain * rate, 2),
            "total_deferred_tax": round(cumulative_tax, 2),
            "immediate_tax": round(immediate_tax, 2),
            "tax_deferral_amount": round(immediate_tax - cumulative_tax, 2),  # 理论上相等，无跨档时
            "yearly_details": yearly_details,
            "final_equity_tax_base": round(cumulative_tax_base, 2),
            "note": "116号文：分期均匀计入应纳税所得额，每年确认{0}元转让所得，与其他所得合并计税".format(round(annual_gain, 2))
        }
    
    # ---- 2. 个人41号文递延纳税 ----
    elif investor == "individual":
        # 一次性计算总税额，再分5年缴纳
        total_tax = transfer_gain * 0.20  # 财产转让所得20%
        annual_payment = total_tax / defer_years
        
        yearly_details = []
        cumulative_paid = 0
        remaining_tax = total_tax
        
        for yr in range(1, defer_years + 1):
            yr_payment = annual_payment
            cumulative_paid += yr_payment
            remaining_tax -= yr_payment
            yearly_details.append({
                "year": yr,
                "annual_payment": round(yr_payment, 2),
                "cumulative_paid": round(cumulative_paid, 2),
                "remaining_tax": round(remaining_tax, 2)
            })
        
        results["individual_deferred"] = {
            "total_tax": round(total_tax, 2),
            "annual_payment": round(annual_payment, 2),
            "yearly_details": yearly_details,
            "note": f"41号文：分期缴纳应纳税额，每年缴纳{round(annual_payment, 2):,.2f}元（与企业116号文不同：企业分期计入所得，个人分期缴纳税额）"
        }
    
    # ---- 3. 增值税 ----
    asset_type = p["asset_type"]
    vat_amount = 0
    vat_note = ""
    
    if asset_type == "equity":
        vat_note = "股权出资不征增值税"
    elif asset_type == "technology" and p.get("vat_exempt"):
        vat_note = "技术出资免征增值税（需合同认定+备查，依据财政部 税务总局公告2026年第10号）"
    elif asset_type == "technology" and not p.get("vat_exempt"):
        vat_base = fair_value / (1 + p["vat_rate"])
        vat_amount = vat_base * p["vat_rate"] - p.get("vat_input_credit", 0)
        vat_amount = max(0, vat_amount)
        vat_note = f"技术出资按视同销售计税{p['vat_rate']*100:.0f}%（未办理免税认定）"
    else:
        # 设备/不动产/其他
        vat_base = fair_value / (1 + p["vat_rate"])
        vat_amount = vat_base * p["vat_rate"] - p.get("vat_input_credit", 0)
        vat_amount = max(0, vat_amount)
        type_map = {"equipment": "设备", "real_estate": "不动产", "other": "其他资产"}
        vat_note = f"{type_map.get(asset_type, asset_type)}出资视同销售{p['vat_rate']*100:.0f}%"
    
    results["vat"] = {
        "amount": round(vat_amount, 2),
        "asset_type": asset_type,
        "exempt": p.get("vat_exempt", False) and asset_type in ("technology",),
        "note": vat_note
    }
    
    # ---- 4. NPV分析 ----
    if p.get("consider_npv"):
        r = p["discount_rate"]
        
        if investor == "enterprise" and results["enterprise_deferred"]:
            # 即期纳税
            immediate_tax = results["enterprise_deferred"]["immediate_tax"]
            # 递延纳税折现值
            pv_deferred = 0
            for yr_detail in results["enterprise_deferred"]["yearly_details"]:
                pv_deferred += yr_detail["tax_on_deferred"] / (1 + r) ** yr_detail["year"]
            
            npv_benefit = immediate_tax - pv_deferred
            
            results["npv_analysis"] = {
                "immediate_tax_pv": round(immediate_tax, 2),
                "deferred_tax_pv": round(pv_deferred, 2),
                "npv_benefit": round(npv_benefit, 2),
                "note": f"递延纳税的资金时间价值收益：{round(npv_benefit, 2):,.2f}元（折现率{r*100:.0f}%）"
            }
        
        elif investor == "individual" and results["individual_deferred"]:
            immediate_tax = results["individual_deferred"]["total_tax"]
            pv_deferred = 0
            for yr_detail in results["individual_deferred"]["yearly_details"]:
                pv_deferred += yr_detail["annual_payment"] / (1 + r) ** yr_detail["year"]
            
            npv_benefit = immediate_tax - pv_deferred
            
            results["npv_analysis"] = {
                "immediate_tax_pv": round(immediate_tax, 2),
                "deferred_tax_pv": round(pv_deferred, 2),
                "npv_benefit": round(npv_benefit, 2),
                "note": f"分期缴纳的资金时间价值收益：{round(npv_benefit, 2):,.2f}元（折现率{r*100:.0f}%）"
            }
    
    # ---- 5. 递延中断（提前退出） ----
    exit_year = p.get("early_exit_year")
    if exit_year and 1 <= exit_year < defer_years:
        if investor == "enterprise" and results["enterprise_deferred"]:
            # 已确认的所得
            recognized = annual_gain * exit_year
            # 未确认的所得一次性计入
            unrecogized = transfer_gain - recognized
            # 加速纳税
            accel_tax = unrecognized * p["tax_rate"]
            # 加上已缴部分
            already_paid = annual_gain * p["tax_rate"] * exit_year
            
            results["early_exit_impact"] = {
                "exit_year": exit_year,
                "already_recognized": round(recognized, 2),
                "unrecognized_one_time": round(unrecognized, 2),
                "accelerated_tax": round(accel_tax, 2),
                "total_tax_same_as_immediate": True,  # 总税额不变，只是时间分布改变
                "note": f"第{exit_year}年退出：未确认的{round(unrecognized, 2):,.2f}元所得一次性计入第{exit_year}年，总税额不变但集中缴纳"
            }
        
        elif investor == "individual" and results["individual_deferred"]:
            # 已缴纳的税额
            already_paid = results["individual_deferred"]["total_tax"] / defer_years * exit_year
            # 未缴税额一次性缴纳
            remaining = results["individual_deferred"]["total_tax"] - already_paid
            
            results["early_exit_impact"] = {
                "exit_year": exit_year,
                "already_paid": round(already_paid, 2),
                "remaining_one_time": round(remaining, 2),
                "note": f"第{exit_year}年退出：未缴纳的{round(remaining, 2):,.2f}元税额一次性缴纳"
            }
    
    # ---- 6. 59号文对比 ----
    if p.get("compare_59wen"):
        results["compare_59wen"] = {
            "wen_116": {
                "name": "116号文递延纳税",
                "mechanism": "5年分期均匀计入应纳税所得额",
                "tax_timing": "5年逐步缴纳",
                "tax_base_adjustment": "取得股权计税基础逐年递增（33号公告）",
                "best_for": "股权支付比例<85%，不满足59号文条件"
            },
            "wen_59": {
                "name": "59号文特殊性税务处理",
                "mechanism": "暂不确认转让所得（完全递延）",
                "tax_timing": "递延至后续处置时",
                "tax_base_adjustment": "取得股权按原计税基础确定（不调整）",
                "best_for": "股权支付≥85%，且完全递延更优"
            },
            "key_difference": "116号文=分期计入所得（5年内有税负）；59号文=暂不确认所得（5年内零税负，计税基础更低）",
            "not_stackable": "两者不可叠加适用，同一笔所得只能择一"
        }
    
    return results


def format_output(results: dict) -> str:
    """格式化输出"""
    lines = []
    lines.append("=" * 60)
    lines.append("  CT-009 非货币性资产投资递延纳税测算结果")
    lines.append("=" * 60)
    
    inv_map = {"enterprise": "企业（116号文）", "individual": "个人（41号文）"}
    asset_map = {"technology": "技术/专利", "equipment": "设备", "real_estate": "不动产", "equity": "股权", "other": "其他"}
    
    lines.append(f"\n【基本信息】")
    lines.append(f"  投资方类型：{inv_map.get(results['investor_type'], results['investor_type'])}")
    lines.append(f"  资产类型：{asset_map.get(results['asset_type'], results['asset_type'])}")
    lines.append(f"  评估公允价值：{results['fair_value']:,.2f} 元")
    lines.append(f"  计税基础：{results['tax_base']:,.2f} 元")
    lines.append(f"  转让所得：{results['transfer_gain']:,.2f} 元")
    lines.append(f"  递延年数：{results['defer_years']} 年")
    
    # 企业116号文
    if results["enterprise_deferred"]:
        ed = results["enterprise_deferred"]
        lines.append(f"\n【企业116号文递延纳税计算】")
        lines.append(f"  每年确认转让所得：{ed['annual_gain_recognized']:,.2f} 元")
        lines.append(f"  每年增加税额：{ed['annual_tax']:,.2f} 元")
        lines.append(f"  即期纳税总额：{ed['immediate_tax']:,.2f} 元")
        lines.append(f"  5年递延纳税总额：{ed['total_deferred_tax']:,.2f} 元")
        lines.append(f"  最终取得股权计税基础：{ed['final_equity_tax_base']:,.2f} 元（逐年调整至公允价值）")
        lines.append(f"\n  逐年明细：")
        lines.append(f"  {'年份':>4} {'确认所得':>14} {'其他所得':>12} {'合计所得':>14} {'税额':>12} {'股权计税基础':>14}")
        for yr in ed["yearly_details"]:
            lines.append(f"  第{yr['year']}年 {yr['deferred_gain_recognized']:>12,.2f} {yr['other_income']:>12,.2f} {yr['total_taxable_income']:>12,.2f} {yr['tax_on_deferred']:>12,.2f} {yr['equity_tax_base']:>12,.2f}")
        lines.append(f"  {ed['note']}")
    
    # 个人41号文
    if results["individual_deferred"]:
        id = results["individual_deferred"]
        lines.append(f"\n【个人41号文分期纳税计算】")
        lines.append(f"  应纳税所得额：{results['transfer_gain']:,.2f} 元")
        lines.append(f"  应纳税总额：{id['total_tax']:,.2f} 元（20%财产转让所得）")
        lines.append(f"  每年缴纳税额：{id['annual_payment']:,.2f} 元")
        lines.append(f"\n  逐年明细：")
        lines.append(f"  {'年份':>4} {'年缴税额':>14} {'累计已缴':>14} {'剩余税额':>14}")
        for yr in id["yearly_details"]:
            lines.append(f"  第{yr['year']}年 {yr['annual_payment']:>12,.2f} {yr['cumulative_paid']:>12,.2f} {yr['remaining_tax']:>12,.2f}")
        lines.append(f"  {id['note']}")
    
    # 增值税
    if results["vat"]:
        vat = results["vat"]
        lines.append(f"\n【增值税处理】")
        if vat["amount"] > 0:
            lines.append(f"  增值税额：{vat['amount']:,.2f} 元")
        lines.append(f"  说明：{vat['note']}")
    
    # NPV分析
    if results["npv_analysis"]:
        npv = results["npv_analysis"]
        lines.append(f"\n【NPV资金时间价值分析】")
        lines.append(f"  即期纳税现值：{npv['immediate_tax_pv']:,.2f} 元")
        lines.append(f"  递延纳税折现值：{npv['deferred_tax_pv']:,.2f} 元")
        lines.append(f"  NPV收益：{npv['npv_benefit']:,.2f} 元")
        lines.append(f"  {npv['note']}")
    
    # 递延中断
    if results["early_exit_impact"]:
        ex = results["early_exit_impact"]
        lines.append(f"\n【递延中断影响（第{ex['exit_year']}年退出）】")
        if "already_recognized" in ex:
            lines.append(f"  已确认所得：{ex['already_recognized']:,.2f} 元")
            lines.append(f"  未确认所得一次性计入：{ex['unrecognized_one_time']:,.2f} 元")
            lines.append(f"  加速缴税额：{ex['accelerated_tax']:,.2f} 元")
        else:
            lines.append(f"  已缴税额：{ex['already_paid']:,.2f} 元")
            lines.append(f"  剩余税额一次性缴纳：{ex['remaining_one_time']:,.2f} 元")
        lines.append(f"  {ex['note']}")
    
    # 59号文对比
    if results["compare_59wen"]:
        cmp = results["compare_59wen"]
        lines.append(f"\n【116号文 vs 59号文对比】")
        lines.append(f"  116号文：{cmp['wen_116']['mechanism']}")
        lines.append(f"    最适用：{cmp['wen_116']['best_for']}")
        lines.append(f"  59号文：{cmp['wen_59']['mechanism']}")
        lines.append(f"    最适用：{cmp['wen_59']['best_for']}")
        lines.append(f"  关键差异：{cmp['key_difference']}")
        lines.append(f"  ⚠️ {cmp['not_stackable']}")
    
    # 免责声明
    lines.append("")
    lines.append("┌" + "─" * 58 + "┐")
    lines.append("│ ⚠️ 以上计算结果仅作为估算参考，不构成税务建议。               │")
    lines.append("│ 最终方案测算需根据企业实际情况调整基础假设，                 │")
    lines.append("│ 建议咨询专业税务机构。                                       │")
    lines.append("└" + "─" * 58 + "┘")
    
    return "\n".join(lines)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        try:
            params = json.loads(sys.argv[1])
        except json.JSONDecodeError as e:
            print(f"参数JSON解析失败: {e}")
            sys.exit(1)
    else:
        params = {}
    
    results = calc_non_monetary_investment(params)
    print(format_output(results))
