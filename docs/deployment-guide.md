# 部署指南

本文档说明如何在不同平台和环境下部署 China Tax Assistant。

---

## 通用步骤

1. 克隆仓库：`git clone https://github.com/Jingyu5683/china-tax-assistant.git`
2. 选择要使用的指令文件：
   - 法规查询 → `instructions-query.md`
   - 税务筹划 → `instructions-planning.md`
3. 将指令文件内容设为系统提示词
4. 将 `references/` 目录作为知识库提供给模型

---

## 平台适配

### Coze（扣子）

1. 创建 Coze Agent
2. 在 Agent 的技能配置中，将 `instructions-query.md` 内容作为技能指令
3. 上传 `references/` 目录下的文件作为知识库
4. 联网检索：Coze 内置 `search_web` 工具，无需额外配置
5. 计算脚本：可通过 Coze 的代码执行功能运行

### ChatGPT

1. 将指令文件内容粘贴到 Custom Instructions 或 GPTs 的 Instructions 中
2. 开启 Web Search / Browse 联网功能
3. 按需上传 `references/` 文件作为 Knowledge 附件
4. 注意：ChatGPT 附件有大小限制，建议分批上传最相关的税种文件

### Claude

1. 使用 Claude API 时，将指令内容写入 `system` 字段
2. 使用 Claude.ai 对话时，将指令内容作为 Project Instructions
3. 联网：需要客户端支持或通过工具调用实现
4. 知识库：通过 API 的 `attachments` 或 RAG 方式提供

### 本地部署（Ollama / vLLM / LM Studio 等）

1. 将指令内容写入对话的 system 字段
2. 使用 RAG 框架（推荐 LlamaIndex / LangChain）索引 `references/` 目录
3. 联网检索：接入 SerpAPI / Tavily / Bing Search API
4. 计算脚本：直接在本地 Python 环境运行

**RAG 配置建议：**
```python
# LlamaIndex 示例
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex

documents = SimpleDirectoryReader("references/").load_data()
index = VectorStoreIndex.from_documents(documents)
query_engine = index.as_query_engine()
```

### 无联网环境

指令集内置了联网不可用时的兜底策略：
- 自动降级为知识库版本回答
- 强制标注"截至知识库更新日期，建议联网核实"
- 不影响核心查询功能，但时效性无法保证

---

## 计算脚本部署

计算脚本为纯 Python，无外部依赖（仅使用标准库）：

```bash
cd scripts

# 查看帮助
python ct001_fixed_asset.py --help

# 运行计算
python ct001_fixed_asset.py --params '{"cost": 100000, "useful_life": 10, "deduction_year": 2026}'
```

脚本输出为 JSON 格式的税负对比结果。

---

## 自定义适配

### 修改联网检索工具

指令文件中的联网检索部分使用了通用描述。如果你的平台有特定的搜索工具，需修改以下部分：

- `instructions-query.md` 中的「检索优先级」和「兜底策略」章节
- `instructions-planning.md` 中的「信息来源优先级」章节

将通用的"联网检索 P0 来源"替换为你的平台特定工具调用方式。

### 裁剪知识库

`references/` 目录包含全部税种知识。如果只需要特定税种，可以只保留相关子目录：

```bash
# 只保留增值税和所得税
rm -rf references/consumption-tax references/stamp-tax references/land-appreciation-tax
# ... 按需删除
```

**不可删除的共享文件：**
- `references/anti-hallucination.md` — 反幻觉协议
- `references/sources-guide.md` — 来源分层指南
