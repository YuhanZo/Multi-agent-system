# 多智能体公司研究与分析系统 — 项目文档

> 版本：v0.3 | 更新日期：2026-03-18 | 分支：`main` + `Felix-dev`

---

## 目录

1. [项目介绍](#1-项目介绍)
2. [技术架构](#2-技术架构)
3. [完整工作流](#3-完整工作流)
4. [模块详解](#4-模块详解)
5. [当前进展](#5-当前进展)
6. [团队分工](#6-团队分工)
7. [已知问题](#7-已知问题)
8. [近期规划](#8-近期规划)

---

## 1. 项目介绍

### 背景

本项目是一个基于 **LangGraph + Claude（Anthropic）** 的多智能体（Multi-Agent）系统，旨在自动化完成对目标公司的研究与投资分析。

### 目标

用户输入一个公司名称，系统自动输出：

- 产品、市场、商业三个维度的研究报告
- 六维评分雷达图（产品力 / 市场空间 / 商业模式 / 技术壁垒 / 增长潜力 / 团队执行力）
- 结构化公司档案（融资轮次、估值、竞争对手等）
- 投资建议与风险提示
- 经过质量评估与自动修订的综合分析报告

### 技术选型

| 组件 | 技术 |
|------|------|
| Agent 框架 | LangGraph |
| LLM | Claude Sonnet 4.6（编排层）/ Claude Haiku 4.5 或 Qwen（工作层）|
| 搜索工具 | Tavily Search API（接入中）|
| 配置管理 | Pydantic Settings |
| 追踪监控 | LangSmith |
| 包管理 | pyproject.toml + setuptools |

---

## 2. 技术架构

```
用户输入: company_name
        │
        ▼
┌──────────────────────────────────┐
│         Research Team            │
│  (app/agent/research_team/)      │
│                                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │ Product  │ │  Market  │ │Business  │  │  ← 3 Workers 并行
│  │Researcher│ │Researcher│ │Researcher│  │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘  │
│       └────────────┼────────────┘        │
│                    ▼                     │
│           ┌──────────────┐               │
│           │   Synthesizer │               │
│           └──────────────┘               │
└──────────────────┬───────────────────────┘
                   │  company_profile + research info
                   ▼
┌──────────────────────────────────────────┐
│         Analysis Team                    │   
│  (app/agent/analysis_team/)              │
│                                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │Extractor │ │  Scorer  │ │ Advisor  │  │  ← 3 Analyzers 并行
│  └────┬─────┘ └────┬─────┘ └────┬─────┘  │
│       └────────────┼────────────┘        │
│                    ▼                     │
│           ┌──────────────┐               │
│           │Report Generator│              │
│           └──────┬───────┘               │
│                  ▼                       │
│           ┌──────────────┐               │
│           │  Evaluator   │               │  ← 质量评估
│           └──────┬───────┘               │
│                  │                       │
│         ┌────────┴────────┐              │
│      通过(is_pass)     未通过(revise)     │
│         │            (最多3次)            │
│         ▼                ▼              │
│        END        Report Generator      │
└──────────────────────────────────────────┘
                   │
                   ▼
          最终输出：analysis_report
```

---

## 3. 完整工作流

### Step 1 — 研究阶段（Research Team）

```
START
  ├──► product_researcher   → product_info
  ├──► market_researcher    → market_info
  └──► business_researcher  → business_info
              ↓（三路并行，均完成后汇聚）
       profile_synthesizer  → company_profile
              ↓
            END (→ 传入 Analysis Team)
```

**各节点职责：**

| 节点 | 模型 | 职责 |
|------|------|------|
| `product_researcher` | Qwen Turbo (Worker) | 产品功能、目标用户、核心能力 |
| `market_researcher` | Qwen Turbo (Worker) | 市场规模、竞争格局、用户口碑 |
| `business_researcher` | Qwen Turbo (Worker) | 融资情况、收入模型、商业指标 |
| `profile_synthesizer` | Qwen Turbo (Compactor) | 汇总三维研究 → 统一公司档案 |

---

### Step 2 — 分析阶段（Analysis Team）

```
Research 输出 (company_profile + 三维 info)
  ├──► extractor   → structured_info (JSON: 融资轮次/估值/竞争对手)
  ├──► scorer      → dimension_scores (6维评分 1-10)
  └──► advisor     → investment_advice (投资建议文本)
              ↓（三路并行，均完成后汇聚）
       report_generator → analysis_report
              ↓
         evaluator（质量评估）
              ↓
      ┌───────┴───────┐
   is_pass=true    is_pass=false
   revision≥3         ↓
      ↓          report_generator（修订）
     END              ↓ 最多循环3次
                     END
```

**各节点职责：**

| 节点 | 模型 | 职责 |
|------|------|------|
| `extractor` | Qwen Turbo (Worker) | 提取结构化事实数据（JSON）|
| `scorer` | Qwen Turbo (Worker) | 六维评分：产品/市场/商业/技术/增长/团队 |
| `advisor` | Qwen Plus (Orchestrator) | 投资建议与竞争策略 |
| `report_generator` | Qwen Plus (Orchestrator) | 综合三项分析生成最终报告 |
| `evaluator` | Qwen Turbo (Worker) | 评估报告质量（完整性/数据支撑/逻辑一致性等）|

---

### Step 3 — 评估循环（Eval Loop）

评估器（`evaluator`）基于以下五个维度对报告打分：

1. **完整性** — 是否覆盖全部六个分析领域
2. **数据支撑** — 结论是否有具体数字/指标支撑
3. **逻辑一致性** — 评分与叙述是否自洽
4. **可操作性** — 投资建议是否具体可执行
5. **风险披露** — 是否识别并解释了关键风险

输出：`{"is_pass": bool, "eval_feedback": "..."}`

若未通过 且 `revision_count < 3`，反馈传回 `report_generator` 触发修订。

---

## 4. 模块详解

### 4.1 状态定义

**CompanyResearchState**（研究阶段共享状态）

```python
company_name: str          # 输入：公司名
product_info: str          # 产品研究结果
market_info: str           # 市场研究结果
business_info: str         # 商业研究结果
reference_sources: Annotated[list[dict], operator.add]  # 并发安全的引用来源聚合
company_profile: str       # 综合公司档案
```

**AnalysisState**（分析阶段，继承自研究状态）

```python
# 继承 CompanyResearchState 所有字段，新增：
structured_info: dict          # 结构化事实（JSON）
dimension_scores: DimensionScore  # 六维评分
investment_advice: str          # 投资建议
analysis_report: str            # 最终报告
revision_count: int             # 修订次数（默认 0）
eval_feedback: str              # 评估反馈
is_pass: bool                   # 是否通过质量检查
```

**DimensionScore**

```python
product: int      # 产品力     (1-10)
market: int       # 市场空间   (1-10)
business: int     # 商业模式   (1-10)
technology: int   # 技术壁垒   (1-10)
growth: int       # 增长潜力   (1-10)
team: int         # 团队执行力  (1-10)
```

### 4.2 LLM Factory（多供应商支持）

`app/core/llm_factory.py` 实现了供应商无关的 LLM 创建工厂：

```
LLMFactory.create(role=ModelRole.WORKER, provider="qwen")
```

| 供应商 | Orchestrator | Worker | Compactor |
|--------|-------------|--------|-----------|
| `anthropic` | claude-sonnet-4-6 | claude-haiku-4-5 | claude-haiku-4-5 |
| `openai` | gpt-4o | gpt-4o-mini | gpt-4o-mini |
| `qwen` | qwen-plus | qwen-turbo | qwen-turbo |

切换供应商只需修改 `.env` 中的 `LLM_PROVIDER=qwen`，代码无需改动。

### 4.3 动态 N Workers（graph_dynamic.py）

除静态版本外，Analysis Team 还实现了基于 LangGraph Send API 的动态版本：

```
dispatch_workers()  →  Send("worker", task) × N
                              ↓
                    analysis_results (并发安全聚合)
                              ↓
                      report_generator
```

通过在状态中设置 `analysis_tasks: ["extract", "score", "advise"]` 动态决定并发 Worker 数量，单个 `worker` 节点复用，通过任务名路由到不同逻辑。

### 4.4 Prompt 体系

| 文件 | 用途 |
|------|------|
| `research_product.md` | 产品研究员系统 Prompt |
| `research_market.md` | 市场研究员系统 Prompt |
| `research_business.md` | 商业分析师系统 Prompt |
| `research_synthesize.md` | 综合档案合成器 Prompt |
| `analysis_extract.md` | 结构化信息提取 Prompt |
| `analysis_score.md` | 六维评分 Prompt |
| `analysis_advise.md` | 投资建议 Prompt |
| `analysis_report.md` | 报告生成 Prompt |
| `analysis_eval.md` | 报告质量评估 Prompt |

---

## 5. 当前进展

### 整体完成度

| 模块 | 状态 | 备注 |
|------|------|------|
| Research Team（3并行 + 合成器）| ✅ 完成 | `main` 分支 |
| Analysis Team 静态版（3并行 + 报告）| ✅ 完成 | `main` 分支 |
| Analysis Team 动态版（Send API）| ✅ 完成 | `dev-nWorkers2` 分支，待合并 |
| Eval + 自动修订循环 | ✅ 完成 | `main` 分支 |
| 两队串联完整 Pipeline（main.py）| ✅ 完成 | `main` 分支 |
| LLM Factory（多供应商）| ✅ 完成 | `main` 分支 |
| Tavily 工具实现 | ⚠️ 部分完成 | `Felix-dev` 分支，有 Bug |
| Tavily 真正接入到 Research Agent | ❌ 未完成 | 工具绑定后未使用 |
| 端到端集成测试（真实数据）| ❌ 未完成 | 测试仍用 Mock 数据 |

### 分支状态

| 分支 | 说明 |
|------|------|
| `main` | 最新稳定版，两队串联完成，含 Eval 循环 |
| `dev-nWorkers2` | 动态 N Worker 功能，待 PR 合并进 main |
| `Felix-dev` | Tavily 工具开发中，有 Bug 待修复 |
| `dev-duan-factory` | LLMFactory 实现（已合并进 main）|

---

## 6. 团队分工

| 成员 | 负责模块 |
|------|------|
| 你（Yuhan）| Analysis Team — 静态版、动态 N Worker 版 |
| Felix | Research Team 编排、Tavily 搜索工具接入 |
| Duan | LLM Factory、Eval Agent、工厂模式重构 |

---

## 7. 已知问题

### P0 — 阻塞性问题

**Tavily 工具绑定了但未使用（Felix-dev）**

```python
# 现状（有 Bug）：
llm_with_tools = llm.bind_tools(search_tool)  # 绑定了
chain = prompt | llm                           # ← 用的还是原始 llm！

# 修复方案：
chain = prompt | llm_with_tools               # 改这一行
# 同时需要添加 ToolNode 处理 tool_call 结果
```

所有研究结果目前仍来自 LLM 内置知识（无实时搜索），`reference_sources` 返回的是硬编码 mock URL。

### P1 — 重要问题

- **本地 `dev-nWorkers2` 落后 remote main 15 个文件**，需要同步后再合并
- **Analysis Team 动态版（`graph_dynamic.py`）未接入 Eval 循环**，仅静态版有评估节点

### P2 — 待改进

- `analysis_state.py` 动态版所需的 `analysis_tasks` / `analysis_results` 字段未在 `AnalysisState` 中定义（在 `graph_dynamic.py` 里单独处理）
- 测试全部使用 Mock 的 Notion 公司数据，缺少真实端到端集成测试

---

## 8. 近期规划

### 本周优先级

| 优先级 | 任务 | 负责 | 说明 |
|--------|------|------|------|
| 🔴 P0 | 修复 Tavily 工具绑定 Bug | Felix | `chain = prompt \| llm_with_tools` + 添加 ToolNode |
| 🔴 P0 | 同步本地 `dev-nWorkers2` → rebase main | Yuhan | 拉取 remote main 后 rebase |
| 🔴 P0 | 合并动态 N Worker PR 进 main | Yuhan | 功能完整，可以开 PR |
| 🟡 P1 | 动态版接入 Eval 循环 | Yuhan | `graph_dynamic.py` 补充 evaluator 节点 |
| 🟡 P1 | 端到端集成测试 | 全员 | 用真实公司（如 Mihoyo）跑完整流程 |
| 🟢 P2 | 统一 `AnalysisState` 字段 | 全员 | 合并静态/动态版的状态定义 |

### 下周展望

- Tavily 真实搜索数据流入 Research → Analysis 完整验证
- 考虑接入 LangSmith 追踪，建立 Eval 指标 Dashboard
- 评估是否需要将 `reference_sources` 传递给 Analysis Team 用于报告引用

---

*文档由 Claude Code 根据代码库自动生成 | 如有出入请以代码为准*
