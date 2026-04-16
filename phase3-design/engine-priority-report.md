# Phase 3: 搜索引擎优先级对比实验报告

> **测试完成**: 2026-04-16
> **样本量**: 对照组 25 | 实验组 25 (共50次搜索请求)
> **测试轮次**: 5轮，每轮5个查询
> **模式**: 模拟测试 (验证策略设计)

---

## 一、实验设计

### 1.1 实验目标
对比两种搜索引擎优先级策略的效果：
- **对照组 (Control)**: Tavily优先 → Brave → Google（当前策略）
- **实验组 (Treatment)**: Brave优先 → Tavily → Google（新策略）

### 1.2 测试查询集

| ID | 类别 | 查询 | 最佳引擎 |
|----|------|------|---------|
| tech_1 | 技术 | how to optimize asyncio performance python | tavily |
| news_1 | 新闻 | latest AI regulation news 2026 | brave |
| realtime_1 | 实时 | Sydney weather forecast tomorrow | brave |
| academic_1 | 学术 | LLM reasoning chain of thought papers | tavily |
| product_1 | 产品 | best noise cancelling headphones review | brave |

### 1.3 模拟参数
- Tavily: 技术/学术问题效果好，响应时间 0.8s
- Brave: 新闻/实时/产品效果好，响应时间 0.5s
- Google: 通用备选，响应时间 1.2s，免费

---

## 二、实验结果

### 2.1 整体指标对比

| 指标 | 对照组 (Tavily优先) | 实验组 (Brave优先) | 差异 | 结论 |
|------|---------------------|-------------------|------|------|
| **成功率** | 100.00% | 100.00% | 0.00% | 持平 |
| **平均耗时** | 0.766s | 0.542s | -0.224s | **实验组更快** ✅ |
| **平均Fallback** | 0.24 | 0.16 | -0.08 | **实验组更少** ✅ |
| **平均质量** | 3.96/5 | 4.04/5 | +0.08 | **实验组更高** ✅ |
| **总消耗** | 30 credits | 28 credits | -2 | **实验组更省** ✅ |

### 2.2 按查询类别分析

| 类别 | 对照组成功率 | 实验组成功率 | 对照组Fallback | 实验组Fallback |
|------|-------------|-------------|---------------|---------------|
| 技术 (technical) | 100% | 100% | 0.0 | 0.0 |
| 新闻 (news) | 100% | 100% | 0.8 | 0.2 |
| 实时 (realtime) | 100% | 100% | 0.2 | 0.4 |
| 学术 (academic) | 100% | 100% | 0.0 | 0.2 |
| 产品 (product) | 100% | 100% | 0.2 | 0.0 |

### 2.3 引擎使用分布

**对照组 (Tavily优先)**:
- Tavily: 20次 (80%)
- Brave: 4次 (16%)
- Google: 1次 (4%)

**实验组 (Brave优先)**:
- Brave: 22次 (88%)
- Tavily: 2次 (8%)
- Google: 1次 (4%)

---

## 三、结论与建议

### 3.1 主要发现

1. **响应时间**: 实验组 (Brave优先) 平均快 0.224秒 (-29.3%)
2. **Fallback次数**: 实验组平均少 0.08次 (-33.3%)
3. **结果质量**: 实验组质量略高 (+0.08/5, +2.0%)
4. **额度消耗**: 实验组节省 2 credits (-6.7%)

### 3.2 策略评估

| 策略 | 优点 | 缺点 |
|------|------|------|
| **对照组 (Tavily优先)** | 技术/学术查询质量高 | 新闻/实时场景需多次Fallback |
| **实验组 (Brave优先)** | 响应快、Fallback少 | 技术查询可能需Fallback |

### 3.3 落地建议

**推荐策略**: ✅ **Brave优先 → Tavily → Google**

理由：
1. 整体响应时间更短
2. Fallback次数更少
3. 结果质量略高
4. 额度消耗更低

**优化建议**：
- 技术/学术查询可考虑直接使用Tavily
- 新闻/实时查询优先使用Brave
- 复杂查询可保留Fallback策略

---

## 四、实验数据

### 4.1 输出文件

| 文件 | 说明 |
|------|------|
| `experiments/engine-priority/engine-priority-analysis.json` | 分析报告 (JSON) |
| `experiments/engine-priority/round{N}-control.json` | 对照组第N轮数据 |
| `experiments/engine-priority/round{N}-treatment.json` | 实验组第N轮数据 |
| `configs/engine-priority-control.json` | 对照组配置 |
| `configs/engine-priority-treatment.json` | 实验组配置 |

### 4.2 后续验证

由于本次使用模拟测试，建议：
1. **真实API验证**: 配置 TAVILY_API_KEY 和 BRAVE_API_KEY 后重新测试
2. **扩大样本量**: 增加更多查询类型和轮次
3. **A/B测试**: 在生产环境中逐步切换验证

---

*报告生成: 2026-04-16*
