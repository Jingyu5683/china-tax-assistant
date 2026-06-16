# 政策巡检来源索引

> 本文件定义各税种对应的巡检 URL 和关键词，供定期巡检报告使用。  
> 每次生成周报/月报时，Agent 参照本文件，按用户高频税种优先顺序检索。

---

## P0 来源（官方，强制检索）

### 国家税务总局

| 页面 | URL | 巡检内容 |
|-----|-----|---------|
| 新政速递 | https://www.chinatax.gov.cn/chinatax/n810356/n815681/index.html | 最新公告、通知、函（近30天） |
| 留言公开 | https://www.chinatax.gov.cn/chinatax/n810356/n3255681/common_listwyc.html | 高频问答（每季度采集） |
| 政策法规库 | https://www.chinatax.gov.cn/chinatax/n810356/n810912/index.html | 法规原文全文检索 |
| 纳税服务 | https://www.chinatax.gov.cn/chinatax/n810356/n810749/index.html | 实务口径 |

### 财政部

| 页面 | URL | 巡检内容 |
|-----|-----|---------|
| 税收政策 | http://www.mof.gov.cn/zhengwuxinxi/caizhengxinwen/ | 财政部令、财税文件（近30天） |
| 政策法规 | http://www.mof.gov.cn/gkml/caizhengbuling/ | 部令全文 |

### 中国香港税务局（ird.gov.hk）

| 页面 | URL | 巡检内容 |
|-----|-----|---------|
| 最新消息 | https://www.ird.gov.hk/chs/news/index.htm | 新公告、预算案税务措施 |
| 利得税修订 | https://www.ird.gov.hk/chs/tax/bus_pft.htm | 税率/扣除规则更新 |
| 薪俸税修订 | https://www.ird.gov.hk/chs/tax/ind_tra.htm | 税率/免税额历史变化 |
| 印花税修订 | https://www.ird.gov.hk/chs/tax/sdu.htm | 印花税税率表更新 |
| DTA 更新 | https://www.ird.gov.hk/chs/tax/dta_inc.htm | 新签协定、议定书 |

---

## P1 来源（权威解读，辅助检索）

### 四大税务快讯

| 机构 | 快讯入口 | 说明 |
|-----|---------|------|
| 德勤中国 | https://www.deloitte.com/cn/zh/services/tax/perspectives/tax-newsflash.html | 税务快讯电子期刊，中英文双语，更新频繁（2026-05-28 验证可用） |
| 普华永道中国 | https://www.pwccn.com/en/services/tax/publications/taxlibrary-chinatax.html | 税务/商务新闻快报 PDF 库，JS 动态渲染需浏览器访问（2026-05-28 验证可用） |
| 毕马威中国 | https://kpmg.com/cn/zh/services/tax/china-tax-insights/china-tax-alert.html | 中国税务快讯，每期深度解读（2026-05-28 验证可用，域名已从 home.kpmg 迁至 kpmg.com） |
| 安永中国 | ⚠️ 待确认（原 ey.com/zh_cn/tax/tax-alerts-china 已下线） | 安永可能已整合至 Insights 主页，暂无可用的固定快讯入口，巡检时使用 WebSearch 补充检索 |

### 专业期刊（季度参考）

| 期刊 | 入口 | 说明 |
|-----|------|------|
| 《中国税务》杂志社 | http://www.ctax.org.cn/ | 月刊，含政策官方解读 |
| 《税务研究》 | http://www.taxresearch.org.cn/ | 双月刊，理论+实务 |
| 《国际税收》 | - | 国际税务专题 |

---

## 各税种巡检关键词

### 增值税

**P0 关键词**：
- `增值税` AND (`税率` OR `起征点` OR `免税` OR `进项抵扣` OR `小规模纳税人`)
- `增值税法`（关注立法动态与配套实施细则）
- `数字化发票` OR `全面数字化的电子发票`
- `留抵退税`

**关注文号类型**：财政部令、国家税务总局公告（增值税系列）

---

### 企业所得税

**P0 关键词**：
- `企业所得税` AND (`小微企业` OR `高新技术企业` OR `研发费用` OR `加计扣除`)
- `特殊性税务处理`（涉重组、合并、分立）
- `受控外国企业`
- `预提税` OR `预提所得税`

**关注文号类型**：国家税务总局公告（企业所得税系列）、财税[202X]XX号

---

### 个人所得税

**P0 关键词**：
- `个人所得税` AND (`专项附加扣除` OR `免税额` OR `综合所得`)
- `股权激励` OR `期权` OR `限制性股票`
- `大湾区` AND (`个人所得税` OR `补贴`)
- `外籍个人` AND `免税`

**关注文号类型**：国家税务总局公告（个人所得税系列）、财政部公告

---

### 印花税

**P0 关键词**：
- `印花税` AND (`优惠` OR `减免` OR `暂免` OR `税率`)
- `证券交易印花税`（A股）
- `合同印花税`（营业账簿）

**关注文号类型**：财政部 税务总局公告（印花税减免）

---

### 土地增值税

**P0 关键词**：
- `土地增值税` AND (`清算` OR `预征率` OR `扣除项目`)
- `房地产` AND `税务`

---

### 中国香港税制专项巡检

**关键词（英/中文同时检索）**：
- `profits tax` / `利得税` AND (`rate` / `税率` OR `deduction` / `扣除`)
- `salaries tax` / `薪俸税` AND (`allowance` / `免税额`)
- `FSIE` OR `外地收入豁免征税`
- `BEPS 2.0` OR `全球最低税` OR `支柱二`
- `双边协定` OR `DTA` AND `mainland` / `内地`
- `stamp duty` / `印花税` AND 物业

---

### 跨境税务（通用）

**P0 关键词**：
- `受益所有人` OR `beneficial owner`
- `常设机构` OR `permanent establishment`
- `转让定价` AND (`同期资料` OR `特别纳税调整`)
- `CRS` OR `共同申报准则`
- `BEPS` AND (`行动计划` OR `多边协定`)
- `协定待遇` OR `享受协定优惠` AND `申请`

---

## 巡检优先队列逻辑

Agent 生成周报时，按以下优先级决定巡检深度：

```
1. 用户本周/本月 hot_topics（从 knowledge-log.md 统计）→ 优先深度巡检
2. 发生了 P0 强制更新（法律法规有修订/新立法）→ 无论是否高频，必须包含在报告
3. 香港财年预算案（每年2月）→ 当月月报必须包含
4. 全国税收工作会议（每年1月）→ 当月月报必须包含
5. 其他 P1 解读 → 仅在月报中列出，不在周报强调
```

---

## 巡检执行脚本逻辑（伪代码）

```
function generateReport(type: "daily"|"weekly"|"monthly"):
  hot_topics = readHotTopics("knowledge-log.md", days=30)
  
  p0_updates = []
  for source in P0_SOURCES:
    updates = webFetch(source.url, keywords=source.keywords, since=lastReportDate)
    p0_updates.append(updates)
  
  matched = []
  for update in p0_updates:
    if any(topic in update.tags for topic in hot_topics):
      matched.append({...update, priority: "🔴重要"})
    else:
      matched.append({...update, priority: "🟡一般"})
  
  if type == "weekly" or "monthly":
    p1_insights = []
    for update in matched if update.priority == "🔴重要":
      insight = searchP1Sources(update.title, update.file_no)
      p1_insights.append(insight)
  
  kb_impacts = compareWithKnowledgeBase(matched)
  
  return renderReport(type, matched, p1_insights, kb_impacts)
```
