---
name: china-tax-assistant
description: 中国税务法规查询与筹划助手。当用户提出中国税务相关问题（增值税、企业所得税、个人所得税、消费税、印花税、关税等）或需要税务筹划、税负计算时触发。支持法规查询、政策解读、税务筹划与风险量化评价，含反幻觉四层防护和7个Python税负计算脚本。
version: 1.0.0
license: MIT
compatibility: workbuddy, claude-code, openclaw, opencode
metadata:
  openclaw:
    requires:
      bins:
        - python3
    emoji: "🏛️"
    homepage: "https://github.com/Jingyu5683/china-tax-assistant"
---

# China Tax Assistant — 中国税务法规查询与筹划助手

一套可搭配任意大语言模型使用的中国税务知识库 + 指令集，覆盖法规查询、政策解读、税务筹划与风险量化评价。

## 触发条件

当用户提出以下类型问题时，使用本技能：

1. **税务查询类**："增值税税率是多少？"、"小规模纳税人有什么优惠？"、"企业所得税怎么算？"
2. **税务筹划类**："如何优化企业税负？"、"公司向境外分红怎么节税？"
3. **具体场景类**："月销售额8万要交多少增值税？"、"个税专项扣除怎么填报？"
4. **政策法规类**："最新的税务政策有哪些？"、"某项税收优惠的适用条件是什么？"

## 使用方式

### 第一步：判断问题类型

- **法规查询类问题** → 加载 `instructions-query.md`
- **税务筹划类问题** → 加载 `instructions-planning.md`

### 第二步：加载知识库

根据问题涉及的税种，读取 `references/` 目录下对应的知识库文件：

- `references/vat/` - 增值税
- `references/income-tax/` - 企业所得税、个人所得税
- `references/consumption-tax/` - 消费税
- `references/stamp-tax/` - 印花税
- `references/customs-duty/` - 关税与海关
- `references/international-tax/` - 国际税收
- `references/anti-hallucination.md` - 反幻觉协议（必读）
- `references/common-issues.md` - 43个高频问题
- `references/sources-guide.md` - 来源分层指南

### 第三步：回答问题时遵循反幻觉协议

1. **时效核查** - 确认法规是否现行有效
2. **多源交叉核对** - 至少2个独立来源一致
3. **低匹配拦截** - 检索结果匹配度低时拒绝回答
4. **强制来源输出** - 每条结论标注法规文号 + 来源

### 第四步：如需计算，使用Python脚本

对于需要计算的场景，运行 `scripts/` 目录下的Python脚本：

```bash
cd scripts
python ct001_fixed_asset.py --params '{"cost": 100000, "useful_life": 10, "deduction_year": 2026}'
```

可用脚本：
- `ct001_fixed_asset.py` - 固定资产折旧税负计算
- （其他脚本详见 `scripts/` 目录）

## 核心原则

- 🛡️ **反幻觉** — 四层防护，最大限度避免AI编造法规
- 🕐 **时效标注** — 每条法规引用附带文号、生效日期、失效日期
- 🎯 **用户适配** — 自动识别企业财务/企业主/税务师/学生等角色
- 📊 **可计算** — 7个估算模板 + Python计算脚本

## 重要提醒

- 本项目仅供学习参考，**不构成任何税务建议**
- 税法具有时效性和地域性，具体税务处理请以主管税务机关口径为准
- 联网检索P0来源（国家税务总局官网）验证法规时效性

## 文件结构

```
china-tax-assistant/
├── SKILL.md                        # 本文件
├── instructions-query.md           # 法规查询系统指令
├── instructions-planning.md         # 税务筹划系统指令
├── references/                     # 知识库（纯Markdown）
│   ├── anti-hallucination.md     # 反幻觉协议
│   ├── common-issues.md          # 43个高频问题
│   ├── vat/                      # 增值税
│   ├── income-tax/               # 所得税
│   └── ...                       # 其他税种
├── scripts/                       # Python计算脚本
└── README.md                      # 项目说明
```

## 示例对话

**用户**："小规模纳税人月销售额8万，开了2万专票，增值税怎么交？"

**助手**：
1. 加载 `instructions-query.md`
2. 读取 `references/vat/` 下的税率表和优惠政策
3. 检查政策时效性（2026年是否现行有效）
4. 给出计算过程和结果，标注政策依据
5. 提醒"建议咨询主管税务机关确认"

---

*本技能由 AI 助手小明协助开发*
