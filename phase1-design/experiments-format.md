# experiments.tsv 格式规范文档

> Phase 1.2 输出文档 - 实验记录格式定义
> 创建日期: 2026-04-14
> 版本: v1.0

---

## 一、格式概述

### 1.1 为什么选择 TSV？

| 格式 | 优点 | 缺点 | 适用性 |
|------|------|------|--------|
| **TSV** | 简单、易读、无转义问题、Shell/Python 原生支持 | 不支持嵌套结构 | ✅ 推荐 |
| CSV | 广泛支持 | 逗号转义复杂、字段含逗号需引号 | ⚠️ 可用但不推荐 |
| JSON | 支持嵌套 | 人类阅读困难、追加写入不便 | ⚠️ metrics 字段内使用 |
| YAML | 人类友好 | 解析复杂、追加不便 | ❌ 不适合日志 |

**TSV 优势**：
- 每行一条记录，便于追加和流式处理
- Tab 分隔符极少出现在自然文本中，无需转义
- Unix 工具链原生支持（awk, cut, sort, uniq）
- Python pandas 可直接读取
- Git diff 友好（单行变化清晰）

### 1.2 文件位置与命名

**主记录文件**：`experiments.tsv`
- 位置：项目根目录或 `data/` 子目录
- 编码：UTF-8
- 换行：Unix (LF)

**历史归档**：
```
data/
├── experiments.tsv           # 当前活动记录
├── experiments.tsv.bak       # 自动备份
└── archive/
    ├── experiments-2026-04.tsv
    ├── experiments-2026-03.tsv
    └── ...
```

---

## 二、字段定义

### 2.1 核心字段（所有场景通用）

| 字段名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| `timestamp` | ISO8601 | ✅ | 实验执行时间（UTC） | `2026-04-14T10:30:00Z` |
| `experiment_id` | string | ✅ | 唯一标识符，格式 `exp_<NNNN>` | `exp_0001` |
| `variant_id` | string | ✅ | 变体标识 | `v_a_01`, `baseline` |
| `scenario` | string | ✅ | 所属场景 | `web_scrape`, `long_task`, `skill_attention` |
| `phase` | string | ✅ | 所属 Phase | `phase3`, `phase4`, `phase5` |
| `status` | enum | ✅ | 执行状态 | `completed`, `timeout`, `error`, `skipped` |
| `duration_sec` | float | ✅ | 执行耗时（秒） | `245.3` |
| `metrics_json` | JSON | ✅ | 评估指标（JSON 字符串） | `{"accuracy":0.85}` |
| `config_hash` | string | ✅ | 配置文件的 SHA256 前8位 | `a1b2c3d4` |
| `git_commit` | string | ✅ | 代码版本（完整 hash） | `abc1234def5678...` |
| `agent_id` | string | ⚪ | 执行 Agent 标识 | `main`, `subagent-8d5c2cac` |
| `description` | string | ⚪ | 实验描述（简短） | `Baseline with httpx 30s` |
| `notes` | string | ⚪ | 补充说明 | `Network unstable during test` |
| `parent_exp_id` | string | ⚪ | 父实验 ID（用于迭代） | `exp_0001` |
| `iteration` | int | ⚪ | 迭代次数 | `1`, `2`, `3` |

### 2.2 字段详细说明

#### `experiment_id` 生成规则
```
格式: exp_<4位数字>
生成: 自动递增，从 exp_0001 开始
示例: exp_0001, exp_0002, ..., exp_9999
```

#### `variant_id` 命名规范
```
格式: <类型>_<参数简写>_<序号>
示例:
  - v_a_01     (variant A, 第1次)
  - v_baseline (基线对照)
  - v_httpx_30s (httpx + 30s timeout)
  - v_bs4_lxml (beautifulsoup + lxml parser)
```

#### `status` 枚举值
| 值 | 含义 | 触发条件 |
|----|------|----------|
| `completed` | 成功完成 | 脚本正常退出，exit_code=0 |
| `timeout` | 超时终止 | 超过 `--timeout` 限制 |
| `error` | 执行错误 | 脚本异常退出，exit_code≠0 |
| `skipped` | 跳过执行 | 前置条件不满足 |

---

## 三、记录示例

### 3.1 完整示例行

```tsv
timestamp	experiment_id	variant_id	scenario	phase	status	duration_sec	metrics_json	config_hash	git_commit	agent_id	description	notes	parent_exp_id	iteration
2026-04-14T10:30:00Z	exp_0001	v_baseline	web_scrape	phase3	completed	245.3	{"scenario":"web_scrape","primary_metric":"accuracy","values":{"accuracy":0.85},"metadata":{"tool":"requests"}}	a1b2c3d4	abc1234def5678...	main	Baseline with requests	Network stable		1
2026-04-14T10:35:12Z	exp_0002	v_httpx_30s	web_scrape	phase3	completed	198.7	{"scenario":"web_scrape","primary_metric":"accuracy","values":{"accuracy":0.88},"metadata":{"tool":"httpx"}}	b2c3d4e5	abc1234def5678...	main	Httpx variant	Faster		1
```

### 3.2 人类可读的格式化视图

```
Record 1:
  Timestamp:    2026-04-14T10:30:00Z
  Experiment:   exp_0001
  Variant:      v_baseline
  Scenario:     web_scrape
  Phase:        phase3
  Status:       completed ✓
  Duration:     245.3s
  Metrics:      accuracy: 85%
  Config Hash:  a1b2c3d4
  Description:  Baseline with requests
```

---

## 四、使用规范

### 4.1 写入规则（Python 示例）

```python
import csv
import json

with open('experiments.tsv', 'a', newline='') as f:
    writer = csv.writer(f, delimiter='\t')
    writer.writerow([
        '2026-04-14T10:30:00Z',
        'exp_0001',
        'v_baseline',
        'web_scrape',
        'phase3',
        'completed',
        245.3,
        json.dumps({'accuracy': 0.85}),
        'a1b2c3d4',
        'abc1234...',
        'main',
        'Baseline',
        '',
        '',
        1
    ])
```

### 4.2 查询方法

**Shell 命令**：
```bash
# 查看最新记录
tail -5 experiments.tsv

# 筛选特定场景
awk -F'\t' '$4=="web_scrape"' experiments.tsv

# 统计成功率
awk -F'\t' '$6=="completed" {count++} END {print count}' experiments.tsv
```

**Python pandas**：
```python
import pandas as pd
import json

df = pd.read_csv('experiments.tsv', sep='\t')
completed = df[df['status'] == 'completed']
```

---

## 五、不同场景的 metrics_json 扩展

### 5.1 网页抓取场景 (web_scrape)

```json
{
  "scenario": "web_scrape",
  "primary_metric": "accuracy",
  "values": {
    "success_rate": 0.95,
    "info_completeness": 0.92,
    "accuracy": 0.85,
    "execution_time_sec": 125.5
  },
  "metadata": {
    "fetcher": "httpx",
    "parser": "beautifulsoup",
    "timeout": 30
  }
}
```

### 5.2 长任务执行场景 (long_task)

```json
{
  "scenario": "long_task",
  "primary_metric": "completion_rate",
  "values": {
    "completion_rate": 0.92,
    "avg_step_time_sec": 45.2,
    "error_rate": 0.03
  },
  "metadata": {
    "max_steps": 50,
    "retry_policy": "exponential"
  }
}
```

### 5.3 Skill vs 注意力场景 (skill_attention)

```json
{
  "scenario": "skill_attention",
  "primary_metric": "trigger_accuracy",
  "values": {
    "trigger_accuracy": 0.88,
    "false_positive_rate": 0.05,
    "response_quality": 4.2
  },
  "metadata": {
    "prompt_version": "v2.1",
    "guard_style": "concise"
  }
}
```

---

## 六、工具支持

### 6.1 提供的工具脚本

框架将提供以下工具脚本：

| 脚本 | 功能 |
|------|------|
| `log-experiment.sh` | 添加一条实验记录 |
| `query-experiments.py` | 查询和筛选实验 |
| `export-report.py` | 生成实验报告 |
| `validate-format.py` | 验证 TSV 格式 |

### 6.2 log-experiment.sh 使用示例

```bash
./log-experiment.sh \
  --variant v_baseline \
  --scenario web_scrape \
  --status completed \
  --duration 245.3 \
  --metrics '{"accuracy":0.85}' \
  --description "Baseline test"
```

---

## 七、验收检查清单

- [x] 格式概述清晰（为什么用 TSV）
- [x] 字段定义完整（14个字段，含必填/可选）
- [x] 提供有效示例
- [x] 使用规范明确（写入、查询、版本控制）
- [x] 场景扩展说明（web_scrape, long_task, skill_attention）
- [x] 工具支持规划

---

*本文档是 OpenClaw 优化测试框架 Phase 1.2 的输出成果。*