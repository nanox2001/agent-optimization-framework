# Phase 4 配置参数统一汇总

**版本**: 2026-04-17 v2（第二轮评审后）
**用途**: 统一所有参数定义，避免实现时混乱

---

## 核心参数定义（全局配置）

| 参数 | 统一值 | 说明 | 出现章节 |
|------|--------|------|---------|
| `max_retries` | **2** | 最大重试次数 | 4.2.3 |
| `base_timeout` | **180s** | 基础超时时间 | 4.2.5 |
| `max_timeout` | **600s** | 最大超时时间 | 4.2.9 |
| `retry_budget_per_hour` | **10** | 每小时重试预算 | 4.2.3 |
| `checkpoint_retention` | **24h** | 失败checkpoint保留时间 | 4.2.6 |
| `circuit_breaker_threshold` | **5** | 熔断失败阈值 | 4.2.3 |
| `cost_alert_threshold` | **0.8** | 成本告警阈值（80%预算）| 4.2.7 |

---

## 组合方案（C+B）执行流程

```
任务启动
    ↓
复杂度判定 → 动态超时(180s/300s/600s)
    ↓
执行任务（首次超时）
    ↓
超时？
    ├─ No → 成功 → 返回结果 → 删除checkpoint
    └─ Yes → 
           ↓
       渐进式重试(attempt=2, timeout+60s)
           ↓
       执行任务
           ↓
       超时？
           ├─ No → 成功 → 返回结果
           └─ Yes →
                  ↓
              渐进式重试(attempt=3, timeout+60s)
                  ↓
              执行任务
                  ↓
              成功？
                  ├─ Yes → 返回结果
                  └─ No → 熔断检查 → 人工队列
```

---

## 监控告警统一配置

| 指标 | 阈值 | 告警级别 | 关联配置 |
|------|------|---------|---------|
| `retry_rate` | >20% | warning | max_retries |
| `retry_success_rate` | <50% | critical | - |
| `circuit_breaker_open` | =1 | critical | circuit_breaker_threshold |
| `cost_per_hour` | >$0.5 | warning | retry_budget |

---

## 边界条件处理

| 场景 | 处理方式 | 关联配置 |
|------|---------|---------|
| 重试次数用尽 | 人工队列 | max_retries=2 |
| 连续失败N次 | 熔断暂停10分钟 | circuit_breaker_threshold=5 |
| Agent崩溃 | 从checkpoint恢复 | checkpoint_retention=24h |
| 任务取消 | 清理checkpoint | on_cancel: delete |

---

*创建: 2026-04-17 18:15*
*用途: 实现前统一参数定义*