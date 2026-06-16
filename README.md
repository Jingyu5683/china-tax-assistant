# 🏛️ China Tax Assistant — 中国税务法规查询与筹划助手

> 一套可搭配任意大语言模型使用的中国税务知识库 + 指令集，覆盖法规查询、政策解读、税务筹划与风险量化评价。

**本项目由 AI 助手 [小明](https://www.coze.cn) 协助开发。** 小明是一个基于 Coze 平台的智能 Agent，在项目全周期中承担了知识库编写、指令设计、代码开发与质量核查工作。

---

## ✨ 这是什么

本项目提供两套互补的系统能力：

| 模块 | 能力 | 典型场景 |
|------|------|---------|
| **tax-query** | 法规检索与政策解读 | "小规模纳税人月销8万开专票2万，增值税怎么交？" |
| **tax-planning** | 税务筹划与风险量化 | "公司拟向境外母公司分红500万，如何优化税负？" |

**核心设计原则：**
- 🛡️ **反幻觉** — 四层防护（时效核查 → 多源交叉核对 → 低匹配拦截 → 强制来源输出），最大限度避免 AI 编造法规
- 🕐 **时效标注** — 每条法规引用附带文号、生效日期、失效日期
- 🎯 **用户适配** — 自动识别企业财务/企业主/税务师/学生等角色，差异化输出
- 📊 **可计算** — 7个估算模板 + Python 计算脚本，税负测算不再纯文字

---

## 📂 项目结构

```
china-tax-assistant/
├── instructions-query.md              # 法规查询系统指令
├── instructions-planning.md           # 税务筹划系统指令
├── references/                        # 知识库（纯 Markdown，平台无关）
│   ├── anti-hallucination.md          #   反幻觉协议（共享）
│   ├── interactive-questionnaire.md   #   问卷式交互决策树
│   ├── common-issues.md               #   43个高频问题
│   ├── policy-guides.md               #   政策指引专题索引
│   ├── sources-guide.md               #   来源分层指南
│   ├── vat/                           #   增值税（税率表、优惠政策）
│   ├── income-tax/                    #   所得税（企税+个税+优惠）
│   ├── consumption-tax/               #   消费税
│   ├── stamp-tax/                     #   印花税
│   ├── land-appreciation-tax/         #   土地增值税
│   ├── deed-tax/                      #   契税
│   ├── resource-tax/                  #   资源税
│   ├── environmental-tax/             #   环境保护税
│   ├── surtax/                        #   城建税及教育费附加
│   ├── customs-duty/                  #   关税与海关
│   ├── international-tax/             #   国际税收（协定/CFC/转让定价/BEPS/香港税制）
│   ├── tax-dispute/                   #   税务争议
│   ├── tax-collection-law/            #   征管法与数电票
│   ├── tax-cases/                     #   税案通报案例库
│   ├── study-guide/                   #   学习指南
│   └── tax-planning/                  #   筹划引导框架 + 估算模板
├── scripts/                           # 计算脚本（Python，独立运行）
├── docs/
│   └── deployment-guide.md            #   各平台部署指南
├── LICENSE                            # MIT
└── README.md
```

---

## 🚀 使用方式

### 方式一：系统指令（推荐）

将 `instructions-query.md` 或 `instructions-planning.md` 的内容设为 LLM 的系统提示词，同时将 `references/` 目录作为知识库提供。

**ChatGPT / Claude / DeepSeek 等：**
1. 复制指令文件内容作为 Custom Instructions 或 System Prompt
2. 按需上传 `references/` 下的知识库文件作为附件

**本地部署（Ollama / vLLM 等）：**
1. 将指令内容写入对话的 system 字段
2. 用 RAG 框架（如 LlamaIndex）索引 `references/` 目录，实现动态检索

### 方式二：知识库 + 手动参考

不使用系统指令，仅将 `references/` 作为税务知识库查阅：
- 税率表、优惠政策索引、国际税收协定等均可独立使用
- `scripts/` 下的 Python 脚本可独立运行

### 计算脚本

```bash
cd scripts
python ct001_fixed_asset.py --params '{"cost": 100000, "useful_life": 10, "deduction_year": 2026}'
```

每个脚本支持 JSON 参数输入，输出结构化税负对比结果。

---

## 🛡️ 反幻觉机制

四层防护确保法规引用准确性：

```
时效核查（法规是否现行有效）
    ↓
多源交叉核对（至少 2 个独立来源一致）
    ↓
低匹配拦截（检索结果匹配度低时拒绝回答）
    ↓
强制来源输出（每条结论标注法规文号 + 来源）
```

详见 [`references/anti-hallucination.md`](references/anti-hallucination.md)。

---

## 🌐 联网检索

指令集默认要求联网检索 P0 来源（国家税务总局官网）验证法规时效性。不同平台配置方式：

| 平台 | 联网工具 | 配置方式 |
|------|---------|---------|
| Coze | `search_web` 内置 | 直接使用 |
| ChatGPT | Web Search / Browse | 开启联网模式 |
| Claude | 支持联网的客户端 | API + 工具调用 |
| 本地部署 | SerpAPI / Tavily | 接入搜索 API |
| 无联网 | — | 自动降级为知识库版本，标注时效提示 |

> 离线也能用：内置兜底策略，联网不可用时自动降级为知识库回答，并强制标注"建议联网核实"。

---

## 🤝 贡献指南

欢迎 Issue 和 PR！

**特别欢迎的方向：**
- 🐛 法规错误 — 引用条文有误，务必提 Issue
- 📝 地方口径补充 — 各省市执行口径差异
- 🔍 时效性标注 — 发现过时法规请指出
- 💡 场景补充 — 实际工作中的税务问题
- 🧪 对抗测试 — 用刁钻问题"考倒"助手
- 🔧 新平台适配 — 为其他 LLM 平台编写部署指南

提交规范：Issue 标题 `[税种] 简要描述`，如 `[增值税] 留抵退税政策引用已过期`

---

## ⚖️ 免责声明

本项目基于公开法律法规和权威来源编写，仅供学习参考，**不构成任何税务建议**。税法具有时效性和地域性，具体税务处理请以主管税务机关口径为准。使用本项目产生的任何后果，由使用者自行承担。

## 📄 许可证

[MIT License](LICENSE)

## 🙏 致谢

- 知识库来源：国家税务总局、财政部、香港税务局、OECD、四大税务专栏等公开资料
- 本项目由 AI 助手 **小明** 协助开发 — 包括知识库编写、指令设计、估算模板与计算脚本开发、反幻觉协议设计
