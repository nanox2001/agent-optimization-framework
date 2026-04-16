# OpenClaw 网页抓取优化测试方案 (Phase 3.2)

> **文档版本**: 1.0  
> **创建日期**: 2026-04-15  
> **目标**: 设计可执行、可量化的优化测试方案，验证三大优化点效果  

---

## 一、测试目标定义

### 1.1 核心假设 (Hypotheses)

| 编号 | 优化点 | 核心假设 | 验证指标 |
|------|--------|----------|----------|
| **H1** | 智能域名预选择 | 基于历史数据自动选择最佳工具，可减少30%的Fallback次数 | Fallback率降低≥25% |
| **H2** | 并行预抓取策略 | 对高风险URL并行发起多个请求，可降低50%关键场景延迟 | P95耗时降低≥40% |
| **H3** | 缓存与镜像自动化 | 建立热门站点镜像缓存池，可提升困难场景成功率至80% | 微信类站点成功率≥75% |

### 1.2 成功指标 (Success Metrics)

#### 1.2.1 主要指标 (Primary)

| 指标名称 | 定义 | 基线值 | 目标值 | 计算公式 |
|----------|------|--------|--------|----------|
| **整体成功率** | 成功获取有效内容的请求占比 | 68.4% | ≥85% | 成功数/总数 |
| **平均Fallback次数** | 每个请求平均经历的Fallback次数 | 1.35次 | ≤0.8次 | 总Fallback次数/总请求数 |
| **P95响应时间** | 95%请求在X毫秒内完成 | 5200ms | ≤3000ms | 第95百分位耗时 |

#### 1.2.2 次要指标 (Secondary)

| 指标名称 | 基线值 | 目标值 | 说明 |
|----------|--------|--------|------|
| 工具选择准确率 | 60% | ≥80% | 首次选择工具即成功的比例 |
| 镜像命中率 | 0% | ≥60% | 困难场景使用镜像成功的比例 |
| 重复请求节省率 | 0% | ≥30% | 缓存命中的请求占比 |
| 资源消耗 | 基准 | ≤120% | 并行策略带来的额外资源开销 |

#### 1.2.3 业务指标 (Business)

| 指标名称 | 说明 |
|----------|------|
| 用户满意度 | 用户无需手动介入的请求占比 |
| 信息完整性 | 成功提取内容占预期内容的比例 |
| 成本效益 | 单位成功请求的资源消耗 |

---

## 二、测试场景选择

### 2.1 场景分类框架

基于Phase 3.1分析，选择**3大类9小类**测试场景，覆盖不同难度和特征：

```
测试场景矩阵
├── 基础场景 (Basic) - 目标: 95%成功率
│   ├── B1: 静态HTML页面
│   ├── B2: GitHub代码仓库页
│   └── B3: 常见新闻网站
├── 困难场景 (Hard) - 目标: 80%成功率
│   ├── H1: 微信公众号文章
│   ├── H2: 需要登录的内容
│   └── H3: 反爬严格站点
└── 边界场景 (Edge) - 目标: 60%成功率
    ├── E1: 超大页面 (>1MB)
    ├── E2: 重定向链 (>3跳)
    └── E3: 特殊格式内容
```

### 2.2 场景详细定义

#### 基础场景 (Basic Scenarios)

| 编号 | 场景 | 典型特征 | 预期最佳工具 | 难度权重 |
|------|------|----------|--------------|----------|
| B1 | 静态HTML | 纯静态、无JS渲染、标准HTML | web_fetch | 1.0x |
| B2 | GitHub页面 | 结构化数据、API友好 | web_fetch | 1.0x |
| B3 | 新闻网站 | 标准文章布局、较少反爬 | Jina | 1.2x |

#### 困难场景 (Hard Scenarios)

| 编号 | 场景 | 典型特征 | 当前最佳工具 | 难度权重 |
|------|------|----------|--------------|----------|
| H1 | 微信公众号 | 反爬严格、需验证、经常更新 | browser | 2.5x |
| H2 | 登录保护内容 | 需要Cookie/Session | browser | 2.0x |
| H3 | 反爬严格站点 | Rate limit、验证码、IP封禁 | browser/Scrapling | 2.0x |

#### 边界场景 (Edge Scenarios)

| 编号 | 场景 | 典型特征 | 风险点 | 难度权重 |
|------|------|----------|--------|----------|
| E1 | 超大页面 | >1MB HTML、大量图片 | 超时、内存溢出 | 1.8x |
| E2 | 重定向链 | 多级跳转、短链接 | 循环重定向、丢失Cookie | 1.5x |
| E3 | 特殊格式 | PDF、JSON API、XML | 内容解析失败 | 1.3x |

### 2.3 场景权重分配

```yaml
测试场景权重分布:
  基础场景: 50%    # 15个URL (B1:5, B2:5, B3:5)
  困难场景: 35%    # 10个URL (H1:4, H2:3, H3:3)
  边界场景: 15%    # 5个URL (E1:2, E2:2, E3:1)
  总计: 30个URL
```

---

## 三、A/B对照设计

### 3.1 对照组 vs 实验组

| 维度 | 对照组 (Control) | 实验组 (Treatment) |
|------|------------------|-------------------|
| **策略名称** | 默认工具链 (Default Chain) | 智能优化策略 (Smart Optimized) |
| **工具选择** | 固定顺序: web_fetch → Jina → browser | 动态选择: 基于域名历史+并行预抓取 |
| **Fallback逻辑** | 串行逐一尝试 | 并行预抓取+智能Fallback |
| **缓存策略** | 无缓存 | 镜像缓存+结果缓存 |
| **超时设置** | 固定30s | 动态超时 (基于场景) |

### 3.2 控制变量

确保两组测试的公平性：

| 控制变量 | 固定值 | 说明 |
|----------|--------|------|
| URL测试集 | 相同的30个URL | 随机顺序执行，避免顺序偏差 |
| 测试环境 | 相同网络、硬件 | 同一时段执行，控制网络波动 |
| 重试次数 | 最多3次 | 防止无限重试影响指标 |
| 评估标准 | 相同质量检查逻辑 | 统一的内容完整性验证 |

### 3.3 实验配置详情

#### 对照组配置 (Default Chain)

```json
{
  "name": "control_default_chain",
  "tool_selection": "sequential_fixed",
  "chain": ["web_fetch", "jina", "scrapling", "browser"],
  "timeout": 30000,
  "fallback_mode": "on_failure",
  "cache_enabled": false,
  "parallel_fetch": false
}
```

#### 实验组配置 (Smart Optimized)

```json
{
  "name": "treatment_smart_optimized",
  "tool_selection": "dynamic_history_based",
  "primary_selector": "domain_tool_predictor",
  "parallel_fetch": {
    "enabled": true,
    "domains": ["weixin.qq.com", "zhihu.com", "paywalled_sites"],
    "tools": ["web_fetch", "jina", "scrapling"],
    "race_mode": "first_success"
  },
  "cache": {
    "enabled": true,
    "mirror_discovery": true,
    "ttl_seconds": 3600
  },
  "timeout": {
    "default": 30000,
    "by_domain": {
      "weixin.qq.com": 60000,
      "github.com": 15000
    }
  },
  "fallback_chain": ["predicted_best", "parallel_race", "browser_last_try"]
}
```

### 3.4 测试执行设计

```
A/B测试执行流程:
├── 轮次1: 对照组先执行 (避免学习效应)
│   ├── 随机顺序执行30个URL
│   ├── 记录完整指标
│   └── 冷却期5分钟
├── 轮次2: 实验组执行
│   ├── 相同URL，新随机顺序
│   ├── 记录完整指标
│   └── 冷却期5分钟
├── 轮次3-5: 重复执行 (消除偶然性)
│   └── 每组总共执行5轮 (150次请求/组)
└── 数据汇总: 跨轮次统计分析
```

---

## 四、测试数据准备

### 4.1 URL测试集 (30个URL)

#### 基础场景 - 15个URL

**B1: 静态HTML页面 (5个)**

| 编号 | URL | 域名 | 特征描述 | 预期工具 |
|------|-----|------|----------|----------|
| B1-01 | https://news.ycombinator.com | news.ycombinator.com | 纯静态、列表页 | web_fetch |
| B1-02 | https://httpbin.org/html | httpbin.org | 标准HTML测试页 | web_fetch |
| B1-03 | https://example.com | example.com | 极简静态页 | web_fetch |
| B1-04 | https://www.w3schools.com/html/ | w3schools.com | 教育类静态内容 | web_fetch |
| B1-05 | https://docs.python.org/3/ | docs.python.org | 文档类静态页 | web_fetch |

**B2: GitHub页面 (5个)**

| 编号 | URL | 域名 | 特征描述 | 预期工具 |
|------|-----|------|----------|----------|
| B2-01 | https://github.com/torvalds/linux | github.com | 大型仓库首页 | web_fetch |
| B2-02 | https://github.com/microsoft/vscode/blob/main/README.md | github.com | 单文件视图 | web_fetch |
| B2-03 | https://github.com/langchain-ai/langchain | github.com | 复杂项目页 | web_fetch |
| B2-04 | https://github.com/facebook/react/issues | github.com | Issues列表 | web_fetch |
| B2-05 | https://github.com/karpathy/autoresearch | github.com | 小型项目页 | web_fetch |

**B3: 新闻网站 (5个)**

| 编号 | URL | 域名 | 特征描述 | 预期工具 |
|------|-----|------|----------|----------|
| B3-01 | https://techcrunch.com/latest/ | techcrunch.com | 科技新闻 | Jina |
| B3-02 | https://www.theverge.com/ | theverge.com | 综合科技 | Jina |
| B3-03 | https://arstechnica.com/ | arstechnica.com | 深度技术 | Jina |
| B3-04 | https://www.reuters.com/technology/ | reuters.com | 财经科技 | Jina |
| B3-05 | https://www.wired.com/ | wired.com | 科技文化 | Jina |

#### 困难场景 - 10个URL

**H1: 微信公众号文章 (4个)**

| 编号 | URL | 域名 | 特征描述 | 预期工具 |
|------|-----|------|----------|----------|
| H1-01 | https://mp.weixin.qq.com/s/example1 | mp.weixin.qq.com | 技术类文章 | browser/镜像 |
| H1-02 | https://mp.weixin.qq.com/s/example2 | mp.weixin.qq.com | 产品类文章 | browser/镜像 |
| H1-03 | https://mp.weixin.qq.com/s/example3 | mp.weixin.qq.com | 行业分析 | browser/镜像 |
| H1-04 | https://mp.weixin.qq.com/s/example4 | mp.weixin.qq.com | 教程类 | browser/镜像 |

*注：实际测试时替换为真实的微信文章URL*

**H2: 需要登录/验证的内容 (3个)**

| 编号 | URL | 域名 | 特征描述 | 预期工具 |
|------|-----|------|----------|----------|
| H2-01 | https://www.zhihu.com/question/xxx | zhihu.com | 登录墙 | browser |
| H2-02 | https://medium.com/@author/article | medium.com | 付费墙 | browser |
| H2-03 | https://www.linkedin.com/pulse/xxx | linkedin.com | 登录限制 | browser |

**H3: 反爬严格站点 (3个)**

| 编号 | URL | 域名 | 特征描述 | 预期工具 |
|------|-----|------|----------|----------|
| H3-01 | https://www.tiktok.com/@user | tiktok.com | 反爬+JS | browser |
| H3-02 | https://www.instagram.com/p/xxx | instagram.com | 反爬+JS | browser |
| H3-03 | https://twitter.com/user/status/xxx | twitter.com | API限制 | browser |

#### 边界场景 - 5个URL

**E1: 超大页面 (2个)**

| 编号 | URL | 域名 | 特征描述 | 风险 |
|------|-----|------|----------|------|
| E1-01 | https://en.wikipedia.org/wiki/Special:LongPages | wikipedia.org | 超长百科页 | 超时风险 |
| E1-02 | https://github.com/torvalds/linux/commits/master | github.com | 大量commit列表 | 内存风险 |

**E2: 重定向链 (2个)**

| 编号 | URL | 域名 | 特征描述 | 风险 |
|------|-----|------|----------|------|
| E2-01 | https://bit.ly/3xxx | bit.ly | 短链接跳转 | 循环检测 |
| E2-02 | https://t.co/xxx | t.co | Twitter短链 | 跨域跟踪 |

**E3: 特殊格式 (1个)**

| 编号 | URL | 域名 | 特征描述 | 风险 |
|------|-----|------|----------|------|
| E3-01 | https://api.github.com/repos/torvalds/linux | api.github.com | JSON API响应 | 格式解析 |

### 4.2 预期结果定义

每个URL定义预期结果用于验证：

```json
{
  "test_cases": [
    {
      "id": "B1-01",
      "url": "https://news.ycombinator.com",
      "expected": {
        "content_type": "html",
        "min_length": 1000,
        "must_contain": ["Hacker News", "submit"],
        "forbidden_content": ["error", "blocked"]
      },
      "quality_threshold": {
        "completeness": 0.8,
        "accuracy": 0.9
      }
    }
  ]
}
```

### 4.3 数据验证规则

| 检查项 | 规则 | 失败判定 |
|--------|------|----------|
| **内容存在** | 返回内容非空且长度>500字符 | 空内容或太短 |
| **内容有效** | 包含预期关键词，不含错误提示 | 包含"error"/"blocked" |
| **格式正确** | 符合预期的内容类型 | HTML当作文本返回 |
| **完整性** | 提取内容占页面可见内容≥70% | 大量内容丢失 |

---

## 五、执行流程设计

### 5.1 测试执行架构

```
┌────────────────────────────────────────────────────────────────┐
│                    测试执行控制器                               │
│                   (Test Orchestrator)                          │
└──────────────┬────────────────────────────────┬────────────────┘
               │                                │
      ┌────────▼────────┐              ┌────────▼────────┐
      │   对照组执行器   │              │   实验组执行器   │
      │  (Control Runner)│              │(Treatment Runner)│
      └────────┬────────┘              └────────┬────────┘
               │                                │
       ┌───────▼───────┐                ┌───────▼───────┐
       │  工具链实例   │                │  工具链实例   │
       │ ┌───────────┐ │                │ ┌───────────┐ │
       │ │web_fetch  │ │                │ │智能选择器 │ │
       │ │jina       │ │                │ │并行抓取器 │ │
       │ │browser    │ │                │ │缓存管理器 │ │
       │ └───────────┘ │                │ └───────────┘ │
       └───────┬───────┘                └───────┬───────┘
               │                                │
               └────────────┬───────────────────┘
                            │
                    ┌────────▼────────┐
                    │   数据记录层    │
                    │ experiments.tsv │
                    └─────────────────┘
```

### 5.2 详细执行步骤

#### Phase 1: 准备阶段 (30分钟)

```bash
# 1. 环境检查
cd /home/jerry/.openclaw/workspace/jerry/design/optimization-framework
git status  # 确认干净状态

# 2. 数据准备
mkdir -p phase3-design/test-data/{control,treatment}
cp configs/url-test-set-30.json phase3-design/test-data/

# 3. 历史数据加载
python3 scripts/load-domain-stats.py \
  --input logs/info-collector-stats.json \
  --output phase3-design/test-data/domain-history.json

# 4. 实验目录初始化
mkdir -p experiments/phase3-ab-test-$(date +%Y%m%d)
export EXP_DIR="experiments/phase3-ab-test-$(date +%Y%m%d)"
```

#### Phase 2: 对照组执行 (60-90分钟)

```bash
# 执行5轮对照组测试
for round in 1 2 3 4 5; do
  echo "=== Control Group - Round $round ==="
  
  python3 scripts/run-ab-test.py \
    --group control \
    --config configs/control-default-chain.json \
    --urls phase3-design/test-data/url-test-set-30.json \
    --round $round \
    --output "$EXP_DIR/control-round-$round"
  
  # 轮次间冷却
  sleep 60
done

# 汇总对照组数据
python3 scripts/aggregate-results.py \
  --input "$EXP_DIR"/control-round-* \
  --output "$EXP_DIR/control-summary.json"
```

#### Phase 3: 实验组执行 (60-90分钟)

```bash
# 执行5轮实验组测试
for round in 1 2 3 4 5; do
  echo "=== Treatment Group - Round $round ==="
  
  python3 scripts/run-ab-test.py \
    --group treatment \
    --config configs/treatment-smart-optimized.json \
    --urls phase3-design/test-data/url-test-set-30.json \
    --domain-history phase3-design/test-data/domain-history.json \
    --round $round \
    --output "$EXP_DIR/treatment-round-$round"
  
  # 轮次间冷却
  sleep 60
done

# 汇总实验组数据
python3 scripts/aggregate-results.py \
  --input "$EXP_DIR"/treatment-round-* \
  --output "$EXP_DIR/treatment-summary.json"
```

#### Phase 4: 数据记录 (10分钟)

```bash
# 更新 experiments.tsv
python3 scripts/log-experiments.py \
  --control "$EXP_DIR/control-summary.json" \
  --treatment "$EXP_DIR/treatment-summary.json" \
  --append-to experiments.tsv

# Git提交
git add experiments.tsv "$EXP_DIR"
git commit -m "exp(phase3): A/B test web scrape optimization

- Control: 5 rounds x 30 URLs = 150 requests
- Treatment: 5 rounds x 30 URLs = 150 requests
- Total: 300 requests recorded"
```

#### Phase 5: 分析阶段 (20分钟)

```bash
# 生成对比分析报告
python3 scripts/analyze-ab-test.py \
  --control "$EXP_DIR/control-summary.json" \
  --treatment "$EXP_DIR/treatment-summary.json" \
  --output reports/phase3-ab-test-report.md

cat reports/phase3-ab-test-report.md
```

### 5.3 数据收集规范

#### 单次请求记录格式

```json
{
  "timestamp": "2026-04-15T10:30:00Z",
  "experiment_id": "phase3_ab_test",
  "group": "control|treatment",
  "round": 1,
  "test_case_id": "B1-01",
  "url": "https://news.ycombinator.com",
  "domain": "news.ycombinator.com",
  "scenario": "basic_static",
  
  "execution": {
    "tools_attempted": ["web_fetch", "jina", "browser"],
    "success_tool": "web_fetch",
    "fallback_count": 0,
    "duration_ms": 245,
    "timeout_occurred": false
  },
  
  "result": {
    "success": true,
    "content_length": 45231,
    "content_type": "markdown",
    "quality_score": 0.92,
    "error": null
  },
  
  "metadata": {
    "cache_hit": false,
    "mirror_used": null,
    "parallel_attempts": null
  }
}
```

#### 汇总记录格式 (experiments.tsv)

```tsv
timestamp	experiment_id	variant_id	scenario	status	duration_sec	metrics_json	git_commit	description
2026-04-15T10:00:00Z	phase3_ab_test	control_round1	web_scrape	completed	1800.5	{"success_rate":0.67,"avg_fallback":1.4,"p95_time":5100}	abc1234	Control group baseline
2026-04-15T11:00:00Z	phase3_ab_test	treatment_round1	web_scrape	completed	1650.2	{"success_rate":0.89,"avg_fallback":0.6,"p95_time":2800}	def5678	Treatment with smart selection
```

### 5.4 实时监控

执行过程中实时监控关键指标：

```bash
# 启动监控面板
python3 scripts/monitor-ab-test.py \
  --control-dir "$EXP_DIR/control-round-*" \
  --treatment-dir "$EXP_DIR/treatment-round-*" \
  --refresh 10

# 输出示例:
# =========================================
# Phase 3 A/B Test - Live Dashboard
# =========================================
# Control  Group: 45/150 completed (30%)
#   Success Rate: 68% | Avg Fallback: 1.3 | Avg Time: 3200ms
# Treatment Group: 42/150 completed (28%)
#   Success Rate: 87% | Avg Fallback: 0.7 | Avg Time: 2100ms
# =========================================
```

---

## 六、验收标准

### 6.1 统计显著性要求

| 要求项 | 标准 | 验证方法 |
|--------|------|----------|
| **样本量** | 每组≥150次有效请求 (5轮×30URL) | 计数验证 |
| **置信水平** | 95% (α=0.05) | 统计检验 |
| **效应量** | Cohen's d ≥ 0.5 (中等效应) | 效应量计算 |
| **检验方法** | 独立样本t检验 (连续指标) / 卡方检验 (成功率) | 统计测试 |

### 6.2 优化成功标准

#### 必须满足 (Must Have)

| 指标 | 基线 | 最低提升 | 目标提升 | 判定标准 |
|------|------|----------|----------|----------|
| 整体成功率 | 68.4% | +10% | +20% | ≥78.4% (最低) |
| 平均Fallback次数 | 1.35 | -25% | -40% | ≤1.01 (最低) |
| P95响应时间 | 5200ms | -20% | -40% | ≤4160ms (最低) |

#### 应该满足 (Should Have)

| 指标 | 目标 | 验收标准 |
|------|------|----------|
| 困难场景成功率 | 从40%提升到≥70% | 微信类站点成功率≥75% |
| 首次工具选择准确率 | 从60%提升到≥80% | 首次即成功比例≥80% |
| 镜像缓存命中率 | 新建指标目标≥60% | 困难场景使用镜像成功≥60% |

#### 可以拥有 (Nice to Have)

| 指标 | 目标 |
|------|------|
| 基础场景成功率 | ≥95% |
| 边界场景成功率 | ≥65% |
| 资源开销增加 | ≤20% |

### 6.3 场景特定标准

| 场景类型 | 对照组基线 | 实验组目标 | 统计显著性 |
|----------|------------|------------|------------|
| 基础场景 (B1-B3) | 85% | ≥92% | p<0.05 |
| 困难场景 (H1-H3) | 40% | ≥70% | p<0.01 |
| 边界场景 (E1-E3) | 45% | ≥60% | p<0.05 |

### 6.4 失败判定条件

出现以下情况判定优化失败：

| 条件 | 说明 | 处理 |
|------|------|------|
| 成功率下降 | 实验组成功率低于对照组 | 停止测试，分析原因 |
| 稳定性问题 | 实验组标准差>对照组2倍 | 调整配置，重新测试 |
| 资源耗尽 | 并行策略导致资源耗尽 | 限制并发度，重新测试 |
| 严重超时 | P99时间>10s | 调整超时策略，重新测试 |
| 数据异常 | 统计检验无法通过 | 增加样本量或重新设计 |

### 6.5 测试通过判定

```
测试通过条件:
├── 主要指标 (必须全部通过)
│   ├── 整体成功率提升 ≥10% ✓
│   ├── Fallback次数减少 ≥25% ✓
│   └── P95时间减少 ≥20% ✓
│
├── 统计显著性 (必须全部通过)
│   ├── 样本量充足 (≥150/组) ✓
│   ├── p值 < 0.05 ✓
│   └── 效应量 Cohen's d ≥ 0.5 ✓
│
├── 次要指标 (至少通过2/3)
│   ├── 首次选择准确率 ≥75% ✓
│   ├── 困难场景成功率 ≥65% ✓
│   └── 缓存命中率 ≥50% ✓
│
└── 通过判定: [ 是 / 否 ]
    └── 未通过项: [列出未通过的指标]
```

---

## 七、风险评估与应对

### 7.1 测试风险

| 风险 | 概率 | 影响 | 应对策略 |
|------|------|------|----------|
| **网络波动** | 中 | 高 | 多轮次执行，剔除异常值 |
| **目标站点变更** | 中 | 中 | 测试前验证URL可用性 |
| **API配额限制** | 高 | 中 | 控制请求速率，预留配额 |
| **环境差异** | 低 | 高 | 对照组/实验组同一环境执行 |
| **学习效应** | 中 | 低 | 随机顺序，冷却期设计 |

### 7.2 缓解措施

| 措施 | 说明 |
|------|------|
| **多轮次验证** | 5轮执行，取中位数结果，降低随机波动 |
| **异常值处理** | 使用IQR方法识别并处理异常值 |
| **A/A测试** | 正式测试前进行A/A测试验证系统稳定性 |
| **逐步放量** | 先小样本验证(10URL)，再全量测试 |
| **监控告警** | 实时监控成功率，低于阈值自动告警 |

---

## 八、工具与脚本

### 8.1 需要开发的脚本

| 脚本 | 功能 | 输入 | 输出 |
|------|------|------|------|
| `run-ab-test.py` | 执行单轮A/B测试 | config, urls | result json |
| `aggregate-results.py` | 多轮结果聚合 | round results | summary json |
| `analyze-ab-test.py` | 统计分析 | control/treatment | report md |
| `monitor-ab-test.py` | 实时监控 | running dirs | dashboard |
| `log-experiments.py` | 记录到TSV | summaries | experiments.tsv |

### 8.2 配置文件清单

| 配置 | 路径 | 说明 |
|------|------|------|
| 对照组配置 | `configs/control-default-chain.json` | 默认工具链 |
| 实验组配置 | `configs/treatment-smart-optimized.json` | 智能优化策略 |
| URL测试集 | `phase3-design/test-data/url-test-set-30.json` | 30个测试URL |
| 域名历史 | `phase3-design/test-data/domain-history.json` | 历史统计数据 |

---

## 九、时间计划

### 9.1 测试执行计划

| 阶段 | 任务 | 时长 | 累计 |
|------|------|------|------|
| **D1 上午** | 环境准备、配置验证 | 1h | 1h |
| **D1 上午** | A/A测试验证 | 1h | 2h |
| **D1 下午** | 对照组执行 (5轮) | 2h | 4h |
| **D1 晚上** | 实验组执行 (5轮) | 2h | 6h |
| **D2 上午** | 数据分析、报告生成 | 1h | 7h |
| **D2 上午** | 结果评审、决策 | 0.5h | 7.5h |

### 9.2 里程碑

- [ ] **M1**: 环境准备完成 (D1 10:00)
- [ ] **M2**: A/A验证通过 (D1 11:00)
- [ ] **M3**: 对照组测试完成 (D1 16:00)
- [ ] **M4**: 实验组测试完成 (D1 19:00)
- [ ] **M5**: 分析报告完成 (D2 11:00)
- [ ] **M6**: 优化决策确认 (D2 12:00)

---

## 十、附录

### 10.1 URL测试集完整列表

#### 基础场景 (15个)
```json
{
  "basic": {
    "B1_static_html": [
      "https://news.ycombinator.com",
      "https://httpbin.org/html",
      "https://example.com",
      "https://www.w3schools.com/html/",
      "https://docs.python.org/3/"
    ],
    "B2_github": [
      "https://github.com/torvalds/linux",
      "https://github.com/microsoft/vscode",
      "https://github.com/langchain-ai/langchain",
      "https://github.com/facebook/react",
      "https://github.com/karpathy/autoresearch"
    ],
    "B3_news": [
      "https://techcrunch.com/latest/",
      "https://www.theverge.com/",
      "https://arstechnica.com/",
      "https://www.reuters.com/technology/",
      "https://www.wired.com/"
    ]
  }
}
```

#### 困难场景 (10个)
```json
{
  "hard": {
    "H1_wechat": [
      "https://mp.weixin.qq.com/s/xxx1",
      "https://mp.weixin.qq.com/s/xxx2",
      "https://mp.weixin.qq.com/s/xxx3",
      "https://mp.weixin.qq.com/s/xxx4"
    ],
    "H2_login_required": [
      "https://www.zhihu.com/question/580000000",
      "https://medium.com/@author/article-name",
      "https://www.linkedin.com/pulse/article-id"
    ],
    "H3_anti_scraping": [
      "https://www.tiktok.com/@user",
      "https://www.instagram.com/p/postid",
      "https://twitter.com/user/status/postid"
    ]
  }
}
```

#### 边界场景 (5个)
```json
{
  "edge": {
    "E1_large_pages": [
      "https://en.wikipedia.org/wiki/Special:LongPages",
      "https://github.com/torvalds/linux/commits/master"
    ],
    "E2_redirects": [
      "https://bit.ly/3abc123",
      "https://t.co/abc123"
    ],
    "E3_special_format": [
      "https://api.github.com/repos/torvalds/linux"
    ]
  }
}
```

### 10.2 统计分析方法

#### 成功率比较 (卡方检验)

```python
from scipy.stats import chi2_contingency

# 构建列联表
#        成功   失败
# 对照组   a      b
# 实验组   c      d
contingency = [[a, b], [c, d]]

chi2, p_value, dof, expected = chi2_contingency(contingency)

# 要求: p_value < 0.05
```

#### 响应时间比较 (t检验)

```python
from scipy.stats import ttest_ind

t_stat, p_value = ttest_ind(control_times, treatment_times, equal_var=False)

# 效应量 Cohen's d
cohen_d = (mean_treatment - mean_control) / pooled_std

# 要求: p_value < 0.05, cohen_d >= 0.5
```

### 10.3 参考文档

| 文档 | 路径 |
|------|------|
| Phase 3.1 分析 | `phase3-design/web-scrape-analysis.md` |
| 框架设计 | `phase1-design/framework-design.md` |
| 抓取策略 | `../../../skills/info-collector/SKILL.md` |
| 实验记录格式 | `phase1-design/experiments-format.md` |

### 10.4 术语表

| 术语 | 定义 |
|------|------|
| **Fallback** | 首选工具失败后切换到备选工具 |
| **P95延迟** | 95%的请求在此时间内完成 |
| **效应量 (Cohen's d)** | 标准化后的均值差异，0.5为中等效应 |
| **A/B测试** | 对照组和实验组的对比实验 |
| **工具链** | 按顺序尝试的工具组合 |

---

## 验收检查清单

- [x] 测试目标明确可量化 (3个核心假设+6个指标)
- [x] 测试场景覆盖3类 (基础/困难/边界 = 15+10+5=30个URL)
- [x] A/B对照设计合理 (控制变量+公平对比)
- [x] URL测试集≥30个 (实际30个，详细定义)
- [x] 执行流程可操作 (5阶段详细步骤+脚本)
- [x] 验收标准清晰 (主要/次要/统计显著性要求)

---

*文档完成 - 准备进入Phase 3.3执行阶段*