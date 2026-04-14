# OpenClaw 优化测试框架：架构设计文档

> Phase 1.1 输出文档 - 框架核心架构设计
> 创建日期: 2026-04-14
> 基于 autoresearch 方法论

---

## 一、框架概述和目标

### 1.1 项目背景

OpenClaw 优化测试框架是受 Andrej Karpathy 的 **autoresearch** 项目启发而设计的自动化实验系统。autoresearch 通过让 AI Agent 在固定约束下自主进行数百次实验，实现了 ML 训练流程的自动优化。

本框架将 autoresearch 的核心方法论应用到 OpenClaw 生态，解决以下优化需求：
- 网页信息抓取工具的最优组合选择
- 长任务执行流程的稳定性优化
- Skill vs 注意力的触发准确性优化

### 1.2 核心理念

```
修改 → 执行 → 评估 → 决策 → 记录 → 重复
```

### 1.3 设计原则（继承自 autoresearch）

| 原则 | 说明 | OpenClaw 应用 |
|------|------|---------------|
| **Single File Scope** | Agent 只修改单一文件，保持可控 | 限定实验对象为单个配置文件或脚本 |
| **Fixed Time Budget** | 固定时间预算，结果可比 | 每个实验设定统一执行时限 |
| **Simplicity Criterion** | 简化优于复杂 | 删除代码/简化流程也是好结果 |
| **Program as Skill** | Markdown 文件作为 Agent 指令 | 实验指令文档化、可复用 |
| **Git-based Tracking** | 结构化实验记录 | experiments.tsv 统一格式 |

### 1.4 框架目标

1. **标准化实验流程**：统一的执行、记录、分析模式
2. **可复用基础设施**：一套框架支撑多个优化场景
3. **数据驱动决策**：基于量化指标选择最优方案
4. **自动化运行**：支持批量实验、后台执行

---

## 二、核心架构设计

### 2.1 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                    OpenClaw 优化测试框架                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │   实验设计    │───→│   实验执行    │───→│   结果评估    │       │
│  │   (Design)   │    │  (Execute)   │    │ (Evaluate)   │       │
│  └──────────────┘    └──────────────┘    └──────────────┘       │
│         ↑                                    │                   │
│         └────────────────────────────────────┘                   │
│                    (反馈循环)                                     │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│  支撑组件：                                                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │  实验记录管理 │  │  评估指标计算 │  │  结果分析工具 │            │
│  │ experiments  │  │   metrics    │  │   analyzer   │            │
│  └──────────────┘  └──────────────┘  └──────────────┘            │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 模块划分

| 模块 | 职责 | 对应文件/组件 |
|------|------|--------------|
| **实验设计层** | 定义实验变量、配置变体、生成实验计划 | `experiment-plan.md`, `variants/` |
| **实验执行层** | 运行单个实验、控制执行环境、捕获输出 | `run-experiment.sh` / `executor.py` |
| **结果记录层** | 统一格式记录实验数据、版本管理 | `experiments.tsv` |
| **评估分析层** | 计算评估指标、统计分析、生成报告 | `analyze-results.py` |
| **决策反馈层** | 基于结果决策下一步、生成优化建议 | Agent 决策逻辑 |

### 2.3 实验生命周期流程

```
┌─────────────┐
│  实验准备    │
│  (Prepare)  │
└──────┬──────┘
       │ 加载基准配置
       ▼
┌─────────────┐     ┌─────────────┐
│  生成变体    │────→│  变体配置A  │
│  (Variant)  │     │  变体配置B  │
└──────┬──────┘     │  变体配置C  │
       │            └─────────────┘
       ▼
┌─────────────┐
│  执行实验    │ ←── 固定时间预算
│  (Execute)  │     环境隔离
└──────┬──────┘     输出捕获
       │
       ▼
┌─────────────┐
│  记录结果    │ →── experiments.tsv
│   (Log)     │     commit 追踪
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  评估分析    │ ←── 指标计算
│  (Analyze)  │     统计分析
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  决策反馈    │ →── 继续/终止/调整
│  (Decide)   │
└─────────────┘
       │
       └──────→ (循环或结束)
```

---

## 三、关键组件说明

### 3.1 实验执行组件 (Experiment Executor)

**职责**：
- 接收实验配置（变体参数）
- 准备实验环境（隔离、初始化）
- 执行实验任务（带时间限制）
- 捕获执行输出和状态

**输入**：
```json
{
  "experiment_id": "exp_001",
  "variant": "config_A",
  "parameters": {
    "timeout_seconds": 300,
    "max_retries": 3
  },
  "target_script": "test_scenario.py"
}
```

**输出**：
```json
{
  "experiment_id": "exp_001",
  "status": "completed|timeout|error",
  "duration_seconds": 245,
  "stdout_log": "...",
  "stderr_log": "...",
  "exit_code": 0
}
```

**实现方式**：
- 简单场景：Shell 脚本 `run-experiment.sh`
- 复杂场景：Python 模块 `executor.py`

### 3.2 结果记录组件 (Experiment Logger)

**职责**：
- 统一格式记录每次实验数据
- 支持追加写入和查询
- 与 Git 集成实现版本追踪

**核心文件**：`experiments.tsv`

**字段设计**：
| 字段 | 类型 | 说明 |
|------|------|------|
| `timestamp` | ISO8601 | 实验执行时间 |
| `experiment_id` | string | 唯一标识符 |
| `variant_id` | string | 变体标识 |
| `scenario` | string | 所属场景 |
| `status` | enum | completed/timeout/error/skipped |
| `duration_sec` | float | 执行耗时 |
| `metrics_json` | json | 评估指标（JSON格式） |
| `git_commit` | string | 代码版本 |
| `description` | string | 实验描述 |

**示例记录**：
```tsv
timestamp	experiment_id	variant_id	scenario	status	duration_sec	metrics_json	git_commit	description
2026-04-14T10:30:00Z	exp_001	v_a_01	web_scrape	completed	245.3	{"accuracy":0.85,"time":120}	abc1234	Baseline with tool A
```

### 3.3 评估分析组件 (Result Analyzer)

**职责**：
- 从 experiments.tsv 加载数据
- 计算评估指标（成功率、平均时间等）
- 统计分析（最佳变体、置信区间）
- 生成可视化报告

**核心功能**：

| 功能 | 说明 | 输出 |
|------|------|------|
| `load_experiments()` | 加载实验数据 | DataFrame |
| `calculate_metrics()` | 计算场景特定指标 | Metrics dict |
| `compare_variants()` | 变体间对比分析 | Comparison report |
| `find_best_variant()` | 识别最优变体 | Best variant ID |
| `generate_report()` | 生成实验报告 | Markdown/HTML |

**评估指标计算示例**（网页抓取场景）：
```python
def evaluate_web_scrape(experiment_results):
    return {
        "success_rate": success_count / total_count,
        "avg_time": mean(execution_times),
        "info_completeness": total_extracted / total_expected,
        "accuracy": correct_items / total_items
    }
```

### 3.4 实验设计组件 (Experiment Designer)

**职责**：
- 定义实验变量和变体矩阵
- 生成实验计划（哪些变体需要测试）
- 管理实验依赖和优先级

**变体定义格式**：
```yaml
# experiment-plan.yaml
scenario: web_scrape
target: tool_combination
variables:
  - name: parser
    options: ["beautifulsoup", "lxml", "html.parser"]
  - name: fetcher
    options: ["requests", "httpx", "curl"]
  - name: timeout
    options: [10, 30, 60]

matrix:
  type: full_factorial  # 全组合或抽样
  sample_size: 20       # 如使用抽样
```

---

## 四、数据流设计

### 4.1 数据流向图

```
                    ┌──────────────────┐
                    │   experiment-    │
                    │   plan.yaml      │
                    └────────┬─────────┘
                             │ 读取
                             ▼
┌──────────┐           ┌──────────────────┐           ┌──────────────┐
│  Variant │ ──生成──→ │   Executor       │ ──执行──→ │  Target      │
│  Matrix  │           │   (run-exp.sh)   │           │  Script/Tool │
└──────────┘           └────────┬─────────┘           └──────┬───────┘
                                │                          │
                                │ 捕获                      │ 输出
                                │ 输出                      ▼
                                │                    ┌──────────────┐
                                │                    │  Raw Output  │
                                │                    │  (logs/)     │
                                │                    └──────┬───────┘
                                │                           │
                                ▼                           │ 解析
                       ┌──────────────────┐                │
                       │   Parser         │ ←──────────────┘
                       │   (extract)      │
                       └────────┬─────────┘
                                │
                                ▼ 指标计算
                       ┌──────────────────┐
                       │   Metrics        │
                       │   Calculator     │
                       └────────┬─────────┘
                                │
                                ▼ 写入
                       ┌──────────────────┐      ┌──────────────┐
                       │   experiments    │────→ │   Analyzer   │
                       │   .tsv           │      │   (report)   │
                       └──────────────────┘      └──────────────┘
```

### 4.2 数据存储规范

**实验记录文件**：`experiments.tsv`
- **格式**：TSV（Tab-Separated Values），便于脚本处理
- **位置**：项目根目录或 `data/` 子目录
- **版本控制**：纳入 Git 管理，每次实验后提交
- **备份**：重要里程碑推送至 GitHub

**实验输出目录**：`experiments/`
```
experiments/
├── YYYY-MM-DD/
│   ├── exp_001/
│   │   ├── stdout.log
│   │   ├── stderr.log
│   │   ├── output.json
│   │   └── config.yaml
│   ├── exp_002/
│   └── ...
└── latest/ → 符号链接到最新批次
```

**原始数据缓存**：`cache/`
- 用于缓存外部依赖数据
- 不纳入版本控制（.gitignore）

### 4.3 数据格式规范

**Metrics JSON 标准格式**：
```json
{
  "scenario": "web_scrape",
  "primary_metric": "accuracy",
  "values": {
    "accuracy": 0.85,
    "precision": 0.82,
    "recall": 0.88,
    "f1_score": 0.85,
    "execution_time_sec": 125.5,
    "memory_peak_mb": 512
  },
  "metadata": {
    "test_cases": 50,
    "passed": 43,
    "failed": 7
  }
}
```

---

## 五、代码组织建议（本地 vs GitHub）

### 5.1 复杂度评估决策树

```
                    ┌─────────────────┐
                    │  评估代码复杂度  │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
        [简单脚本]      [中等项目]      [复杂系统]
       单文件 <200行   多文件，无依赖   多模块，外部依赖
              │              │              │
              ▼              ▼              ▼
        ┌──────────┐   ┌──────────┐   ┌──────────┐
        │ 本地存储  │   │ 本地项目  │   │ GitHub   │
        │ /scripts │   │ /workspace│   │ 仓库     │
        └──────────┘   └──────────┘   └──────────┘
```

### 5.2 存储位置建议

| 场景 | 建议位置 | 示例 |
|------|----------|------|
| **简单执行脚本** | `/workspace/scripts/` | `run-experiment.sh` |
| **单场景分析脚本** | `/workspace/jerry/design/optimization-framework/scripts/` | `analyze-web-scrape.py` |
| **框架核心代码** | GitHub: `nanox2001/openclaw-optimization-framework` | `executor/`, `analyzer/` |
| **实验配置/变体** | 本地版本控制 | `configs/`, `variants/` |
| **实验数据** | 本地 + GitHub | `experiments.tsv` |

### 5.3 推荐的代码结构

**方案 A：本地优先（Phase 1-2 推荐）**
```
/workspace/jerry/design/optimization-framework/
├── phase1-design/
│   └── framework-design.md
├── phase2-acceptance/
│   └── ...
├── scripts/                    # 执行/分析脚本
│   ├── run-experiment.sh
│   ├── analyze-results.py
│   └── common.py              # 共享工具函数
├── configs/                   # 实验配置模板
│   ├── web_scrape.yaml
│   └── long_task.yaml
├── experiments.tsv            # 实验记录（git-tracked）
└── README.md
```

**方案 B：GitHub 仓库（Phase 3+ 考虑）**
```
nanox2001/openclaw-optimization-framework/
├── README.md
├── pyproject.toml            # Python 包配置
├── src/
│   └── openclaw_opt/
│       ├── __init__.py
│       ├── executor.py       # 实验执行引擎
│       ├── logger.py         # 记录管理
│       ├── analyzer.py       # 分析工具
│       └── metrics/          # 评估指标模块
│           ├── __init__.py
│           ├── web_scrape.py
│           ├── long_task.py
│           └── skill_attention.py
├── configs/
│   └── scenarios/
├── tests/
└── experiments/              # 实验数据（可 git-lfs）
```

### 5.4 版本控制策略

**本地阶段**（Phase 1-2）：
- 使用本地 Git 仓库
- 定期推送至 GitHub 备份
- 分支策略：`main` + `feature/xxx`

**协作阶段**（Phase 3+）：
- GitHub 仓库作为主仓库
- 实验数据使用 git-lfs（如文件过大）
- 实验结果通过 PR 合并

---

## 六、执行指引（Agent 如何使用框架）

### 6.1 Agent 角色与职责

| 角色 | 职责 | 边界 |
|------|------|------|
| **实验设计师** | 定义变体、配置实验 | CAN: 修改 configs/, plan.yaml<br>CANNOT: 修改核心执行代码 |
| **实验执行者** | 运行实验、记录结果 | CAN: 调用 run-experiment.sh<br>CANNOT: 直接修改 experiments.tsv |
| **结果分析员** | 分析数据、生成报告 | CAN: 调用 analyze-results.py<br>CANNOT: 手动修改实验数据 |
| **决策制定者** | 选择最优方案、规划下一步 | CAN: 读取报告、提出建议<br>CANNOT: 跳过实验直接得出结论 |

### 6.2 标准实验流程（Agent 执行手册）

**步骤 1：实验准备**
```bash
# 进入工作目录
cd /workspace/jerry/design/optimization-framework

# 确认当前状态
git status
cat experiments.tsv | tail -5

# 创建实验批次目录
mkdir -p experiments/$(date +%Y-%m-%d)
```

**步骤 2：设计实验**
```bash
# 基于场景选择配置模板
cp configs/web_scrape.yaml configs/active_experiment.yaml

# 编辑变体（Agent 可修改的部分）
# 修改 variables 部分，定义要测试的参数组合
```

**步骤 3：执行批量实验**
```bash
# 运行单个实验
./scripts/run-experiment.sh \
  --config configs/active_experiment.yaml \
  --variant variant_a \
  --output experiments/$(date +%Y-%m-%d)/exp_001/

# 或运行批量实验
./scripts/run-batch.sh \
  --plan configs/active_experiment.yaml \
  --batch-size 10
```

**步骤 4：验证记录**
```bash
# 检查 experiments.tsv 是否更新
tail -1 experiments.tsv

# 确认 Git 状态
git diff experiments.tsv

# 提交实验记录
git add experiments.tsv experiments/
git commit -m "exp(web_scrape): batch $(date +%Y%m%d)"
```

**步骤 5：分析结果**
```bash
# 生成分析报告
python3 scripts/analyze-results.py \
  --scenario web_scrape \
  --input experiments.tsv \
  --output reports/web_scrape_$(date +%Y%m%d).md

# 查看报告
cat reports/web_scrape_$(date +%Y%m%d).md
```

**步骤 6：决策与迭代**
```bash
# 基于报告决策
# - 如果找到最优方案 → 结束实验，输出结论
# - 如果需要更多探索 → 调整变体，返回步骤 2
# - 如果结果异常 → 检查配置，修复后重试
```

### 6.3 Agent 指令模板（program.md 风格）

```markdown
# 网页抓取工具优化实验 - Agent 指令

## 目标
找到不同网页场景下的最优工具组合（parser + fetcher + timeout）

## 你的职责
作为实验执行者，你需要：
1. 根据配置生成变体组合
2. 依次执行每个变体实验
3. 记录结果到 experiments.tsv
4. 分析结果并报告最优方案

## CAN
- 修改 configs/active_experiment.yaml 中的 variables
- 执行 scripts/run-experiment.sh
- 调用 scripts/analyze-results.py
- 查看 experiments/ 目录下的日志

## CANNOT
- 修改 scripts/ 目录下的执行脚本
- 手动编辑 experiments.tsv（必须通过脚本写入）
- 超过 --timeout 限制继续实验
- 跳过失败的实验而不记录

## 实验流程
1. 读取 configs/web_scrape.yaml 作为基准
2. 设计 3-5 个关键变体（聚焦最有潜力的组合）
3. 逐个执行，每次执行后等待完成并记录
4. 每批次完成后运行分析
5. 基于结果决定：继续/调整/结束

## 成功标准
- 至少测试 10 个变体组合
- 找到成功率 > 90% 且平均时间 < 60s 的方案
- 输出带数据支撑的最终推荐

## 实验记录格式
每次实验后确保 experiments.tsv 包含：
- 时间戳、变体ID、状态、耗时
- JSON 格式的指标数据
- 简短描述（变体特点）
```

### 6.4 常见问题与处理

| 问题 | 诊断 | 处理 |
|------|------|------|
| 实验超时 | 目标脚本运行过久 | 检查是否有无限循环；调整 timeout 参数 |
| 记录写入失败 | TSV 格式错误 | 检查 metrics_json 是否为有效 JSON |
| 变体结果差异小 | 参数变化不够显著 | 扩大参数范围或更换关键变量 |
| Git 冲突 | 并行修改 experiments.tsv | 先 pull 再合并，或手动解决冲突 |
| 指标计算异常 | 输出解析失败 | 检查目标脚本输出格式是否符合预期 |

### 6.5 最佳实践

**实验设计**：
- 每次实验批次聚焦 1-2 个关键变量
- 预留基线变体用于对比
- 设置合理的停止条件（如：连续 5 次无改进则终止）

**数据记录**：
- 实验描述要具体（"使用 httpx + 30s 超时" 而非 "变体 B"）
- 失败实验也要记录，标注失败原因
- 定期提交 experiments.tsv（每批次后）

**结果分析**：
- 不仅看平均值，还要看分布（标准差、分位数）
- 考虑资源约束（内存、并发）
- 多指标权衡时可视化 Pareto 前沿

---

## 七、与 autoresearch 方法论的对齐

### 7.1 继承的设计

| autoresearch 特性 | 本框架实现 |
|-------------------|-----------|
| Single file scope | 限定 Agent 修改 configs/ 和变体参数 |
| Fixed time budget | 每个实验配置 timeout，超时自动终止 |
| Simplicity criterion | 明确删除/简化代码也是有效优化 |
| Program as skill | 每个场景提供 program.md 风格指令 |
| Git-based tracking | experiments.tsv + Git 提交 |
| TSV 结构化记录 | 采用相同格式，便于分析 |

### 7.2 针对 OpenClaw 的适配

| 差异点 | autoresearch | OpenClaw 框架 |
|--------|--------------|---------------|
| 优化目标 | ML 模型训练 | 工具配置/流程优化 |
| 评估指标 | val_bpb (连续值) | 多指标综合评估 |
| 执行环境 | GPU 训练集群 | 通用计算环境 |
| 实验对象 | train.py (代码) | 配置文件/工具链 |
| 自动化程度 | 全自动 overnight | 半自动，Agent 辅助决策 |

### 7.3 扩展设计

本框架在 autoresearch 基础上新增：
- **多场景支持**：可复用的框架支撑不同优化场景
- **多指标评估**：支持成功率、时间、资源等多维度评估
- **Agent 协作模式**：人机协作决策，而非完全自主
- **渐进式部署**：从本地脚本到 GitHub 仓库的渐进演化

---

## 八、验收检查清单

框架设计完成标准：

- [x] 架构设计文档完成（本文档）
- [ ] 实验记录格式规范文档（Phase 1.2）
- [ ] 评估指标体系文档（Phase 1.3）
- [ ] 执行脚本开发完成（Phase 1.4）
- [ ] 分析工具开发完成（Phase 1.5）
- [ ] 框架测试验收通过（Phase 2）

---

## 九、附录

### 9.1 术语表

| 术语 | 定义 |
|------|------|
| **变体 (Variant)** | 实验配置的一个具体参数组合 |
| **场景 (Scenario)** | 一类相关的优化问题（如网页抓取） |
| **指标 (Metric)** | 用于评估实验结果的量化标准 |
| **批次 (Batch)** | 一组连续执行的实验 |
| **基线 (Baseline)** | 用于对比的参考配置 |

### 9.2 参考文档

- [优化框架规划](../optimization-framework-plan.md)
- [autoresearch 研究分析](../../../research/autoresearch-inspiration.md)
- [项目 README](../README.md)
- [autoresearch GitHub](https://github.com/karpathy/autoresearch)

### 9.3 相关 Phase 文档

| Phase | 文档路径 | 说明 |
|-------|----------|------|
| Phase 1.1 | `phase1-design/framework-design.md` | 本文档 - 框架架构设计 |
| Phase 1.2 | `phase1-design/experiments-format.md` | 实验记录格式规范 |
| Phase 1.3 | `phase1-design/evaluation-metrics.md` | 评估指标体系 |
| Phase 2 | `phase2-acceptance/` | 框架测试验收 |
| Phase 3 | `phase3-scenario-a/` | 网页抓取优化 |
| Phase 4 | `phase4-scenario-b/` | 长任务执行优化 |
| Phase 5 | `phase5-scenario-c/` | Skill vs 注意力优化 |
| Phase 6 | `phase6-summary/` | 总结输出 |

---

## 十、版本历史

| 版本 | 日期 | 修改内容 | 作者 |
|------|------|----------|------|
| v1.0 | 2026-04-14 | 初始版本，完成框架架构设计 | Agent |

---

*本文档是 OpenClaw 优化测试框架 Phase 1.1 的输出成果，遵循 autoresearch 方法论设计。*
/