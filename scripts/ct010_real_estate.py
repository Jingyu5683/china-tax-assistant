#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CT-010 不动产交易多税种协调测算
支持：增值税(一般/简易) + 土增税(四级累进) + 契税 + 企税/个税 + 印花税
用法：python ct010_real_estate.py [JSON参数]
不传参时使用内置示例数据

政策依据（P0）：
- 增值税法 主席令第十六号 / 财政部 税务总局公告2026年第9号
- 土地增值税暂行条例 国务院令第138号
- 财税[2006]21号（土增税扣除项目）
- 契税法 主席令第52号
- 财税[2018]57号（重组免土增税）/ 财税[2018]17号（重组免契税）
- 企业所得税法 主席令63号 / 个人所得税法 主席令第9号
"""

import json
import sys
import math

# ============================================================
# 内置示例数据
# ============================================================
EXAMPLE_DATA = {
    "transfer_price": 80000000,          # 转让收入（含税，元）
    "property_type": "commercial",       # commercial / residential / industrial / land
    "is_developer": False,               # 是否房地产开发企业
    "acquisition_method": "purchase",    # purchase / self_build / investment
    "acquisition_year": 2018,            # 取得年份
    "acquisition_price": 30000000,       # 取得价格（元）
    "vat_method": "compare",             # general / simplified / compare（对比两种）
    "vat_general_input_credit": 500000,  # 一般计税可抵扣进项（元）
    "surcharge_rate": 0.12,              # 附加税率（城建7%+教育3%+地方2%=12%）
    "land_cost": 10000000,               # 取得土地使用权金额（元）
    "development_cost": 0,               # 开发成本（元）
    "development_expense_rate": 0.10,    # 开发费用率（按取得+开发合计的%）
    "old_house_method": "invoice",       # invoice / appraisal / na
    "invoice_annual_rate": 0.05,         # 发票法年利率5%
    "appraisal_replacement_cost": 0,     # 评估法重置成本（元）
    "appraisal_depreciation_rate": 0.6,  # 成新度折扣率
    "deed_tax_rate": 0.03,               # 契税税率
    "seller_type": "enterprise",         # enterprise / individual
    "income_tax_rate": 0.25,             # 所得税率（企25%/高新15%/个20%）
    "property_net_value": 25000000,      # 资产净值（会计账面净值，用于所得税计算）
    "reorganization_exempt": False       # 是否适用重组免税
}


def calc_land_appreciation_tax(transfer_income: float, deductions: float) -> dict:
    """计算土地增值税（四级超率累进税率）"""
    appreciation = transfer_income - deductions
    if appreciation <= 0:
        return {
            "appreciation": round(appreciation, 2),
            "appreciation_rate": 0,
            "tax_rate": 0,
            "quick_deduction": 0,
            "tax_amount": 0,
            "bracket": "无增值（免税）"
        }
    
    rate = appreciation / deductions
    
    if rate <= 0.50:
        tax_rate, quick_ded, bracket = 0.30, 0, "≤50%（30%）"
    elif rate <= 1.00:
        tax_rate, quick_ded, bracket = 0.40, 0.05, "50%-100%（40%）"
    elif rate <= 2.00:
        tax_rate, quick_ded, bracket = 0.50, 0.15, "100%-200%（50%）"
    else:
        tax_rate, quick_ded, bracket = 0.60, 0.35, ">200%（60%）"
    
    tax = appreciation * tax_rate - deductions * quick_ded
    
    return {
        "appreciation": round(appreciation, 2),
        "appreciation_rate": round(rate * 100, 2),
        "tax_rate": tax_rate,
        "quick_deduction_rate": quick_ded,
        "tax_amount": round(max(0, tax), 2),
        "bracket": bracket
    }


def calc_vat_general(price: float, input_credit: float) -> dict:
    """一般计税方式"""
    output_tax = price / (1 + 0.09) * 0.09
    vat = max(0, output_tax - input_credit)
    income_ex_vat = price - output_tax  # 不含增值税收入
    return {
        "vat_amount": round(vat, 2),
        "output_tax": round(output_tax, 2),
        "input_credit": round(input_credit, 2),
        "income_ex_vat": round(income_ex_vat, 2),
        "method": "一般计税9%"
    }


def calc_vat_simplified(price: float, acquisition_price: float, acquisition_year: int) -> dict:
    """简易征收方式"""
    # 差额征税：(转让收入 - 取得价) / (1+5%) * 5%
    if acquisition_price > 0:
        vat = (price - acquisition_price) / (1 + 0.05) * 0.05
    else:
        vat = price / (1 + 0.05) * 0.05
    vat = max(0, vat)
    income_ex_vat = price - vat  # 简易征收下，增值税不在价内单独核算
    return {
        "vat_amount": round(vat, 2),
        "vat_base": round(max(0, price - acquisition_price), 2),
        "income_ex_vat": round(income_ex_vat, 2),
        "method": "简易征收5%"
    }


def calc_real_estate_tax(params: dict) -> dict:
    """不动产交易多税种协调测算主函数"""
    p = {**EXAMPLE_DATA, **params}
    
    price = p["transfer_price"]
    is_dev = p["is_developer"]
    acquisition_year = p["acquisition_year"]
    current_year = 2026  # 当前年度
    
    results = {
        "transfer_price": price,
        "property_type": p["property_type"],
        "is_developer": is_dev,
        "vat_general": None,
        "vat_simplified": None,
        "selected_method": None,
        "land_tax_general": None,
        "land_tax_simplified": None,
        "deed_tax": None,
        "income_tax": None,
        "stamp_duty": None,
        "seller_total_general": None,
        "seller_total_simplified": None,
        "buyer_tax": None,
        "sensitivity": None
    }
    
    # ---- 1. 增值税 ----
    vat_gen = calc_vat_general(price, p["vat_general_input_credit"])
    vat_simp = calc_vat_simplified(price, p["acquisition_price"], acquisition_year)
    
    results["vat_general"] = vat_gen
    results["vat_simplified"] = vat_simp
    
    # ---- 2. 土增税（分别按两种增值税方式计算） ----
    for method_key, vat_result in [("general", vat_gen), ("simplified", vat_simp)]:
        income_ex_vat = vat_result["income_ex_vat"]
        vat_amount = vat_result["vat_amount"]
        
        # 扣除项目
        deductions = 0
        deduction_details = {}
        
        # (1) 取得土地使用权金额
        land_cost = p["land_cost"]
        deductions += land_cost
        deduction_details["取得土地使用权金额"] = land_cost
        
        # (2) 开发成本（房企+非房企开发）
        dev_cost = p["development_cost"]
        deductions += dev_cost
        deduction_details["开发成本"] = dev_cost
        
        # (3) 开发费用
        dev_expense = (land_cost + dev_cost) * p["development_expense_rate"]
        deductions += dev_expense
        deduction_details["开发费用"] = round(dev_expense, 2)
        
        # (4) 与转让相关的税金
        related_tax = vat_amount * (1 + p["surcharge_rate"])  # 增值税+附加
        # 印花税
        stamp = income_ex_vat * 0.0005
        related_tax += stamp
        deductions += related_tax
        deduction_details["转让相关税金"] = round(related_tax, 2)
        
        # (5) 加计扣除20%（仅房企）
        if is_dev:
            extra_deduction = (land_cost + dev_cost) * 0.20
            deductions += extra_deduction
            deduction_details["加计扣除20%（房企）"] = round(extra_deduction, 2)
        
        # 非房企旧房特殊扣除
        if not is_dev and p.get("old_house_method") == "invoice" and p["acquisition_price"] > 0:
            # 发票法：发票金额 + 发票金额 × 5% × 持有年数
            holding_years = current_year - acquisition_year
            invoice_deduction = p["acquisition_price"] * (1 + p["invoice_annual_rate"] * holding_years)
            # 替换土地成本和开发成本
            old_deductions = invoice_deduction
            # 保留转让税金
            old_deductions += related_tax
            deductions = old_deductions
            deduction_details = {"购房发票金额×(1+5%×年数)": round(invoice_deduction, 2), "转让相关税金": round(related_tax, 2)}
        elif not is_dev and p.get("old_house_method") == "appraisal" and p.get("appraisal_replacement_cost", 0) > 0:
            # 评估法：重置成本 × 成新度折扣率
            appraisal_deduction = p["appraisal_replacement_cost"] * p["appraisal_depreciation_rate"]
            old_deductions = appraisal_deduction + related_tax
            deductions = old_deductions
            deduction_details = {"重置成本×成新度": round(appraisal_deduction, 2), "转让相关税金": round(related_tax, 2)}
        
        # 计算土增税
        lat = calc_land_appreciation_tax(income_ex_vat, deductions)
        lat["deduction_details"] = deduction_details
        lat["total_deductions"] = round(deductions, 2)
        
        if method_key == "general":
            results["land_tax_general"] = lat
        else:
            results["land_tax_simplified"] = lat
    
    # ---- 3. 契税（受让方） ----
    deed_tax = price / (1 + 0.09) * p["deed_tax_rate"]  # 按不含增值税价格
    if p.get("reorganization_exempt"):
        deed_tax = 0
    results["deed_tax"] = {
        "amount": round(deed_tax, 2),
        "rate": p["deed_tax_rate"],
        "exempt": p.get("reorganization_exempt", False),
        "note": "重组免税（17号文）" if p.get("reorganization_exempt") else f"契税{p['deed_tax_rate']*100:.0f}%"
    }
    
    # ---- 4. 企税/个税 ----
    # 两种增值税方式下的转让所得
    for method_key, vat_result in [("general", vat_gen), ("simplified", vat_simp)]:
        income_ex_vat = vat_result["income_ex_vat"]
        vat_amount = vat_result["vat_amount"]
        surcharge = vat_amount * p["surcharge_rate"]
        lat_result = results[f"land_tax_{method_key}"]
        stamp_duty_amount = income_ex_vat * 0.0005
        
        # 转让所得 = 不含税收入 - 资产净值 - 相关税金
        related_taxes = surcharge + lat_result["tax_amount"] + stamp_duty_amount
        transfer_income = income_ex_vat - p["property_net_value"] - related_taxes
        income_tax = max(0, transfer_income * p["income_tax_rate"])
        
        vat_result[f"income_tax"] = {
            "transfer_income": round(transfer_income, 2),
            "tax_amount": round(income_tax, 2),
            "rate": p["income_tax_rate"]
        }
    
    # ---- 5. 印花税 ----
    results["stamp_duty"] = round(price / (1 + 0.09) * 0.0005, 2)
    
    # ---- 6. 汇总 ----
    for method_key, vat_result in [("general", vat_gen), ("simplified", vat_simp)]:
        vat = vat_result["vat_amount"]
        surcharge = vat * p["surcharge_rate"]
        lat_result = results[f"land_tax_{method_key}"]
        lat = lat_result["tax_amount"]
        it = vat_result[f"income_tax"]["tax_amount"]
        stamp = results["stamp_duty"]
        
        seller_total = vat + surcharge + lat + it + stamp
        results[f"seller_total_{method_key}"] = {
            "vat": round(vat, 2),
            "surcharge": round(surcharge, 2),
            "land_tax": round(lat, 2),
            "income_tax": round(it, 2),
            "stamp_duty": round(stamp, 2),
            "total": round(seller_total, 2),
            "effective_rate": round(seller_total / price * 100, 2)
        }
    
    # 买方税负
    results["buyer_tax"] = {
        "deed_tax": round(deed_tax, 2),
        "stamp_duty": round(results["stamp_duty"], 2),
        "total": round(deed_tax + results["stamp_duty"], 2)
    }
    
    # ---- 7. 敏感性分析：增值税方式对总税负的影响 ----
    gen_total = results["seller_total_general"]["total"]
    simp_total = results["seller_total_simplified"]["total"]
    diff = gen_total - simp_total
    results["sensitivity"] = {
        "general_total": round(gen_total, 2),
        "simplified_total": round(simp_total, 2),
        "difference": round(diff, 2),
        "recommendation": "一般计税总税负更低" if diff < 0 else "简易征收总税负更低" if diff > 0 else "两种方式总税负相同"
    }
    
    # 选择增值税方式
    if p["vat_method"] == "general":
        results["selected_method"] = "general"
    elif p["vat_method"] == "simplified":
        results["selected_method"] = "simplified"
    else:
        results["selected_method"] = "simplified" if diff > 0 else "general"
    
    return results


def format_output(results: dict) -> str:
    """格式化输出"""
    lines = []
    lines.append("=" * 64)
    lines.append("  CT-010 不动产交易多税种协调测算结果")
    lines.append("=" * 64)
    
    prop_map = {"commercial": "商业", "residential": "住宅", "industrial": "工业", "land": "土地使用权"}
    
    lines.append(f"\n【基本信息】")
    lines.append(f"  转让收入（含税）：{results['transfer_price']:,.2f} 元")
    lines.append(f"  不动产类型：{prop_map.get(results['property_type'], results['property_type'])}")
    lines.append(f"  是否房企：{'是' if results['is_developer'] else '否'}")
    
    # 增值税对比
    lines.append(f"\n{'─'*64}")
    lines.append(f"【增值税对比】")
    vg = results["vat_general"]
    vs = results["vat_simplified"]
    lines.append(f"  一般计税9%：增值税 {vg['vat_amount']:,.2f} 元（销项{vg['output_tax']:,.2f} - 进项{vg['input_credit']:,.2f}）")
    lines.append(f"               不含税收入 {vg['income_ex_vat']:,.2f} 元")
    lines.append(f"  简易征收5%：增值税 {vs['vat_amount']:,.2f} 元（差额计税）")
    lines.append(f"               不含税收入 {vs['income_ex_vat']:,.2f} 元")
    
    # 土增税对比
    for label, lt_key in [("一般计税下", "land_tax_general"), ("简易征收下", "land_tax_simplified")]:
        lt = results[lt_key]
        lines.append(f"\n{'─'*64}")
        lines.append(f"【土增税计算 — {label}】")
        lines.append(f"  扣除项目合计：{lt['total_deductions']:,.2f} 元")
        for name, val in lt.get("deduction_details", {}).items():
            lines.append(f"    {name}：{val:,.2f} 元")
        lines.append(f"  增值额：{lt['appreciation']:,.2f} 元")
        lines.append(f"  增值率：{lt['appreciation_rate']:.2f}%")
        lines.append(f"  适用税率档：{lt['bracket']}")
        lines.append(f"  应纳土增税：{lt['tax_amount']:,.2f} 元")
    
    # 所得税
    lines.append(f"\n{'─'*64}")
    lines.append(f"【所得税计算】")
    for label, key in [("一般计税下", "vat_general"), ("简易征收下", "vat_simplified")]:
        it = results[key]["income_tax"]
        lines.append(f"  {label}：")
        lines.append(f"    转让所得：{it['transfer_income']:,.2f} 元")
        lines.append(f"    所得税额：{it['tax_amount']:,.2f} 元（税率{it['rate']*100:.0f}%）")
    
    # 契税
    dt = results["deed_tax"]
    lines.append(f"\n【契税（受让方）】")
    lines.append(f"  契税额：{dt['amount']:,.2f} 元（{dt['note']}）")
    
    # 卖方税负汇总
    lines.append(f"\n{'═'*64}")
    lines.append(f"【卖方税负汇总对比】")
    lines.append(f"  {'项目':>12} {'一般计税':>16} {'简易征收':>16}")
    summary_items = [
        ("vat", "增值税"), ("surcharge", "增值税附加"), ("land_tax", "土地增值税"),
        ("income_tax", "所得税"), ("stamp_duty", "印花税"), ("total", "合计"),
        ("effective_rate", "综合税负率")
    ]
    for key, label in summary_items:
        gen = results["seller_total_general"][key]
        simp = results["seller_total_simplified"][key]
        if key == "effective_rate":
            lines.append(f"  {label:>12} {gen:>14.2f}% {simp:>14.2f}%")
        else:
            lines.append(f"  {label:>12} {gen:>14,.2f} {simp:>14,.2f}")
    
    # 买方税负
    bt = results["buyer_tax"]
    lines.append(f"\n【买方税负】")
    lines.append(f"  契税+印花税合计：{bt['total']:,.2f} 元")
    
    # 敏感性结论
    sens = results["sensitivity"]
    lines.append(f"\n【增值税方式敏感性分析】")
    lines.append(f"  一般计税卖方总税负：{sens['general_total']:,.2f} 元")
    lines.append(f"  简易征收卖方总税负：{sens['simplified_total']:,.2f} 元")
    lines.append(f"  差额：{sens['difference']:,.2f} 元")
    lines.append(f"  结论：{sens['recommendation']}")
    lines.append(f"  推荐计税方式：{'一般计税9%' if results['selected_method'] == 'general' else '简易征收5%'}")
    
    # 免责声明
    lines.append("")
    lines.append("┌" + "─" * 62 + "┐")
    lines.append("│ ⚠️ 以上计算结果仅作为估算参考，不构成税务建议。                 │")
    lines.append("│ 最终方案测算需根据企业实际情况调整基础假设，                   │")
    lines.append("│ 建议咨询专业税务机构。                                         │")
    lines.append("└" + "─" * 62 + "┘")
    
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
    
    results = calc_real_estate_tax(params)
    print(format_output(results))
