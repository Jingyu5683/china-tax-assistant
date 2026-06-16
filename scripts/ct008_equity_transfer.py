#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CT-008 股权转让税负测算
支持：居民企业/非居民企业/个人/合伙企业 转让股权的各税种计算
用法：python ct008_equity_transfer.py [JSON参数]
不传参时使用内置示例数据

政策依据（P0）：
- 企业所得税法 主席令63号
- 个人所得税法 主席令第9号
- 总局公告2014年第67号（个人股权转让）
- 总局公告2017年第37号（非居民源泉扣缴）
- 总局公告2015年第7号（非居民间接转让）
- 财税[2009]59号（特殊性税务处理）
- 增值税法 主席令第十六号 / 财政部 税务总局公告2026年第9号
"""

import json
import sys
import math

# ============================================================
# 内置示例数据
# ============================================================
EXAMPLE_DATA = {
    "transferor_type": "resident_enterprise",  # resident_enterprise / non_resident / individual / partnership
    "is_high_tech": False,                      # 是否高新技术企业（居民企业适用）
    "transfer_price": 50000000,                 # 转让收入（元）
    "tax_base": 10000000,                       # 计税基础（元）
    "is_related_party": True,                   # 是否关联方
    "is_listed_stock": False,                   # 是否上市公司股票
    "treaty_rate": None,                        # 协定税率（非居民企业适用，None则用默认10%）
    "vat_input_credit": 0,                      # 增值税进项税额（上市公司股票转让适用）
    "special_reorganization": {                 # 特殊性税务处理检查
        "check": True,                          # 是否检查
        "commercial_purpose": True,             # 合理商业目的
        "equity_acquired_pct": 60,              # 收购股权比例%
        "equity_payment_pct": 90,               # 股权支付比例%
        "business_continuity": True,            # 经营连续性（12个月内）
        "equity_continuity": True               # 权益连续性（12个月内）
    },
    "consider_npv": True,                       # 是否考虑NPV
    "discount_rate": 0.08                       # 折现率
}


def calc_equity_transfer(params: dict) -> dict:
    """股权转让税负测算主函数"""
    p = {**EXAMPLE_DATA, **params}
    
    transferor = p["transferor_type"]
    price = p["transfer_price"]
    base = p["tax_base"]
    gain = price - base  # 股权转让所得
    
    results = {
        "transferor_type": transferor,
        "transfer_price": price,
        "tax_base": base,
        "equity_transfer_gain": gain,
        "taxes": {},
        "special_reorganization": None,
        "nuclear_risk_check": None,
        "total_tax": 0,
        "effective_tax_rate": 0
    }
    
    # ---- 1. 所得税/预提税 ----
    if transferor == "resident_enterprise":
        rate = 0.15 if p.get("is_high_tech") else 0.25
        income_tax = max(0, gain * rate)
        results["taxes"]["企业所得税"] = {
            "amount": round(income_tax, 2),
            "rate": rate,
            "note": f"高新技术企业15%" if p.get("is_high_tech") else "标准税率25%"
        }
    
    elif transferor == "non_resident":
        rate = p.get("treaty_rate") if p.get("treaty_rate") is not None else 0.10
        withholding_tax = max(0, gain * rate)
        results["taxes"]["预提所得税"] = {
            "amount": round(withholding_tax, 2),
            "rate": rate,
            "note": f"协定税率{rate*100:.0f}%" if p.get("treaty_rate") is not None else "默认税率10%（37号公告源泉扣缴）"
        }
    
    elif transferor == "individual":
        income_tax = max(0, gain * 0.20)
        results["taxes"]["个人所得税"] = {
            "amount": round(income_tax, 2),
            "rate": 0.20,
            "note": "财产转让所得20%"
        }
    
    elif transferor == "partnership":
        # 合伙企业：先分后税，合伙人各自纳税
        results["taxes"]["合伙人各自纳税"] = {
            "amount": 0,
            "rate": None,
            "note": "合伙企业先分后税，需按合伙人类型分别计算"
        }
    
    # ---- 2. 印花税 ----
    stamp_duty = price * 0.0005  # 0.05% 产权转移书据
    results["taxes"]["印花税"] = {
        "amount": round(stamp_duty, 2),
        "rate": 0.0005,
        "note": "产权转移书据0.05%"
    }
    
    # ---- 3. 增值税（仅上市公司股票转让，企业转让） ----
    vat = 0
    vat_note = "不涉及"
    if p.get("is_listed_stock") and transferor in ("resident_enterprise", "partnership"):
        # 金融商品转让：差额计税 (卖出价-买入价)/(1+6%)*6%
        vat_rate = 0.06
        vat_base_amount = max(0, (price - base) / (1 + vat_rate))
        vat = vat_base_amount * vat_rate - p.get("vat_input_credit", 0)
        vat = max(0, vat)
        vat_note = f"金融商品转让差额计税{(vat_rate*100):.0f}%"
    elif p.get("is_listed_stock") and transferor == "individual":
        vat_note = "个人转让上市公司股票免征增值税"
    
    if vat > 0:
        results["taxes"]["增值税"] = {
            "amount": round(vat, 2),
            "rate": 0.06,
            "note": vat_note
        }
    
    # ---- 4. 特殊性税务处理检查（59号文） ----
    sr = p.get("special_reorganization")
    if sr and sr.get("check"):
        checks = {
            "合理商业目的": sr.get("commercial_purpose", False),
            f"收购股权比例≥50%（实际{sr.get('equity_acquired_pct', 0)}%）": sr.get("equity_acquired_pct", 0) >= 50,
            f"股权支付比例≥85%（实际{sr.get('equity_payment_pct', 0)}%）": sr.get("equity_payment_pct", 0) >= 85,
            "经营连续性（12个月内）": sr.get("business_continuity", False),
            "权益连续性（12个月内）": sr.get("equity_continuity", False),
        }
        all_pass = all(checks.values())
        
        # 如果适用特殊性税务处理，计算递延效果
        deferred_tax = 0
        npv_benefit = 0
        if all_pass and gain > 0:
            # 递延纳税：暂不确认所得，相当于获得资金的时间价值
            if transferor == "resident_enterprise":
                rate = 0.15 if p.get("is_high_tech") else 0.25
                deferred_tax = gain * rate
            elif transferor == "non_resident":
                rate = p.get("treaty_rate") if p.get("treaty_rate") is not None else 0.10
                deferred_tax = gain * rate
            
            # NPV分析：假设递延12个月后缴税
            if p.get("consider_npv") and deferred_tax > 0:
                npv_benefit = deferred_tax - deferred_tax / (1 + p.get("discount_rate", 0.08))
        
        results["special_reorganization"] = {
            "eligible": all_pass,
            "checks": checks,
            "deferred_tax": round(deferred_tax, 2) if all_pass else 0,
            "npv_benefit": round(npv_benefit, 2) if all_pass else 0,
            "note": "满足59号文五条件，可暂不确认转让所得" if all_pass else "不满足59号文全部条件，不适用特殊性税务处理"
        }
    
    # ---- 5. 67号公告核定征收风险自查（个人转让） ----
    if transferor == "individual":
        results["nuclear_risk_check"] = {
            "risk_factors": [
                "申报价格低于对应净资产份额",
                "申报价格低于初始投资成本",
                "申报价格低于同类股权转让价格",
                "无正当理由的低价转让（继承/内部划转等除外）",
                "标的企业有不动产/无形资产等增值资产但按亏损定价",
                "关联方之间非公允定价"
            ],
            "note": "67号公告第12-14条：计税价格明显偏低且无正当理由的，税务机关有权核定征收",
            "suggestion": "建议准备评估报告/转让定价分析报告支持公允性"
        }
    
    # ---- 6. 汇总 ----
    total = sum(t["amount"] for t in results["taxes"].values() if isinstance(t.get("amount"), (int, float)))
    results["total_tax"] = round(total, 2)
    results["effective_tax_rate"] = round(total / price * 100, 4) if price > 0 else 0
    
    return results


def format_output(results: dict) -> str:
    """格式化输出"""
    lines = []
    lines.append("=" * 60)
    lines.append("  CT-008 股权转让税负测算结果")
    lines.append("=" * 60)
    
    type_map = {
        "resident_enterprise": "居民企业",
        "non_resident": "非居民企业",
        "individual": "个人",
        "partnership": "合伙企业"
    }
    
    lines.append(f"\n【基本信息】")
    lines.append(f"  转让方类型：{type_map.get(results['transferor_type'], results['transferor_type'])}")
    lines.append(f"  转让收入：{results['transfer_price']:,.2f} 元")
    lines.append(f"  计税基础：{results['tax_base']:,.2f} 元")
    lines.append(f"  股权转让所得：{results['equity_transfer_gain']:,.2f} 元")
    
    lines.append(f"\n【各税种计算】")
    for name, detail in results["taxes"].items():
        if detail.get("amount", 0) > 0 or name in ("合伙人各自纳税",):
            lines.append(f"  {name}：")
            lines.append(f"    税额：{detail.get('amount', 0):,.2f} 元")
            if detail.get("rate") is not None:
                lines.append(f"    税率：{detail['rate']*100:.1f}%")
            lines.append(f"    说明：{detail.get('note', '')}")
    
    lines.append(f"\n【税负汇总】")
    lines.append(f"  总税负：{results['total_tax']:,.2f} 元")
    lines.append(f"  综合税负率：{results['effective_tax_rate']:.2f}%")
    
    # 特殊性税务处理
    if results["special_reorganization"]:
        sr = results["special_reorganization"]
        lines.append(f"\n【特殊性税务处理（59号文）】")
        lines.append(f"  是否适用：{'✅ 满足条件' if sr['eligible'] else '❌ 不满足条件'}")
        for check, passed in sr["checks"].items():
            lines.append(f"    {'✅' if passed else '❌'} {check}")
        if sr["eligible"]:
            lines.append(f"  递延纳税额：{sr['deferred_tax']:,.2f} 元")
            lines.append(f"  NPV收益（资金时间价值）：{sr['npv_benefit']:,.2f} 元")
        lines.append(f"  {sr['note']}")
    
    # 核定征收风险
    if results["nuclear_risk_check"]:
        nr = results["nuclear_risk_check"]
        lines.append(f"\n【核定征收风险自查（67号公告）】")
        lines.append(f"  以下情形可能触发核定征收：")
        for f in nr["risk_factors"]:
            lines.append(f"    ⚠️ {f}")
        lines.append(f"  {nr['note']}")
        lines.append(f"  建议：{nr['suggestion']}")
    
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
    
    results = calc_equity_transfer(params)
    print(format_output(results))
