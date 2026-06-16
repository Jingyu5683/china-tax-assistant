# 估算模板索引

> 由 tax-planning 技能维护，根据用户对话推荐匹配模板。
> 所有模板仅提供公式框架和计算逻辑，具体数值由用户自行确认填写。

## 模板列表

| 编号 | 模板名称 | 适用场景 | 文件路径 | 版本 | 层级 |
|------|---------|---------|---------|------|------|
| CT-001 | 固定资产一次性税前扣除 | 单位价值≤500万设备器具，对比正常折旧vs一次性扣除的现金流差异 | [fixed-asset-accelerated-deduction.md](./fixed-asset-accelerated-deduction.md) | v1.0 | 专项层 |
| CT-002 | 研发费用加计扣除+高新/软件指标 | Part A: 研发预算测算加计扣除节税额；Part B: 倒推高新/软件企业指标上下限 | [rd-super-deduction.md](./rd-super-deduction.md) | v1.0 | 专项层 |
| CT-003 | 所得税亏损弥补 | 逐年跟踪可弥补亏损余额、测算税盾价值、评估弥补策略 | [loss-carryforward.md](./loss-carryforward.md) | v1.0 | 专项层 |
| CT-004 | 单体利润及各项税费 | 从收入到净利润全链路+各税种计算+税负结构分析，汇总其他模板输出 | [entity-profit-and-tax.md](./entity-profit-and-tax.md) | v1.0 | 汇总层 |
| CT-008 | 股权转让税负测算 | 居民企业/非居民/个人/合伙企业转让股权的各税种计算+59号文特殊处理+67号文核定风险 | [equity-transfer-tax.md](./equity-transfer-tax.md) | v1.0 | 专项层 |
| CT-009 | 非货币性资产投资递延纳税 | 企业116号文5年分期计入所得/个人41号文5年分期缴税+增值税视同销售+59号文对比 | [non-monetary-investment-tax.md](./non-monetary-investment-tax.md) | v1.0 | 专项层 |
| CT-010 | 不动产交易多税种协调 | 增值税一般/简易对比+土增税四级累进+契税+企税/个税+敏感性分析 | [real-estate-tax.md](./real-estate-tax.md) | v1.0 | 专项层 |

**调用规则**：[call-rules.md](./call-rules.md) — 模板组合编排、数据流向、交叉影响、典型案例

## 路由规则

用户对话中出现以下关键词/场景时，推荐对应模板：

| 触发词/场景 | 推荐模板 |
|------------|---------|
| 一次性扣除、500万、加速折旧、设备购置税前扣除 | CT-001 |
| 固定资产投资决策、设备更新现金流对比 | CT-001 |
| 税会差异、递延所得税+设备折旧 | CT-001 |
| 加计扣除、研发费用、研发预算节税 | CT-002 Part A |
| 高新指标、高新门槛、科技人员占比、软件企业指标 | CT-002 Part B |
| 亏损弥补、税亏弥补、亏损到期、亏损税盾 | CT-003 |
| 利润表、税负测算、综合税负、年度预算 | CT-004 |
| 新投资项目、新设主体、集团投资决策 | 全套+call-rules多主体对比 |
| 股权转让、股东退出、并购重组、跨境转让 | CT-008 |
| 59号文、特殊性税务处理、股权收购 | CT-008 |
| 67号公告、个人股权转让、核定征收 | CT-008 |
| 非货币性资产投资、技术出资、设备入股、递延纳税 | CT-009 |
| 116号文、41号文、分期计入所得、分期缴税 | CT-009 |
| 不动产转让、商业办公楼、土增税、增值税选择 | CT-010 |
| 旧房转让、发票法、评估法、重置成本 | CT-010 |
| 57号文、重组免税、契税 | CT-010 |

## 计算脚本

每个估算模板配有对应的Python交互计算脚本，支持JSON参数输入，自动完成公式计算并输出格式化结果。

| 脚本 | 对应模板 | 用途 | 调用方式 |
|------|---------|------|---------|
| `../../scripts/ct001_fixed_asset.py` | CT-001 | v1正常折旧 vs v2一次性扣除对比+NPV+税盾速算 | `python ct001_fixed_asset.py '{"asset_cost":3000000,"dep_years":5,...}'` |
| `../../scripts/ct002_rd_super_deduction.py` | CT-002 | Part A加计扣除节税额 + Part B高新/软件指标倒推 | `python ct002_rd_super_deduction.py '{"part":"A","expenses":{...},...}'` |
| `../../scripts/ct003_loss_carryforward.py` | CT-003 | 亏损FIFO弥补+税盾现值+到期风险预警 | `python ct003_loss_carryforward.py '{"losses":[...],"future_profits":[...],...}'` |
| `../../scripts/ct004_entity_profit_tax.py` | CT-004 | 利润表全链路+增值税+各税种+综合税负分析 | `python ct004_entity_profit_tax.py '{"profit":{...},"vat":{...},...}'` |
| `../../scripts/ct008_equity_transfer.py` | CT-008 | 多转让方类型股权税负+59号文特殊处理+67号核定风险 | `python ct008_equity_transfer.py '{"transferor_type":"resident_enterprise","transfer_price":50000000,...}'` |
| `../../scripts/ct009_non_monetary_investment.py` | CT-009 | 116号文企业递延/41号文个人递延+增值税+NPV+59号文对比 | `python ct009_non_monetary_investment.py '{"investor_type":"enterprise","fair_value":15000000,...}'` |
| `../../scripts/ct010_real_estate.py` | CT-010 | 增值税一般/简易对比+土增税四级累进+契税+敏感性分析 | `python ct010_real_estate.py '{"transfer_price":80000000,"property_type":"commercial",...}'` |

> ⚠️ **所有脚本输出结果仅作为估算参考，不构成税务建议。最终方案测算需根据企业实际情况调整基础假设，建议咨询专业税务机构。** 每个脚本输出末尾均包含此声明。

## 模板设计原则

1. **给框架不给数值**：公式逻辑完整，具体税率/限额/政策有效期由用户自行确认
2. **政策可溯源性**：每个关键参数标注参考文号，用户可反向验证
3. **对比结构**：至少包含两种方案的计算框架和差异对比
4. **决策判断**：模板末尾给出"何时选择/何时慎选"的定性指引
