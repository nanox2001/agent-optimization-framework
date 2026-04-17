# Phase 4 Step 4.2: 优化变体设计

**设计日期**: 2026-04-17 (更新: 2026-04-17)
**基于分析**: Step 4.1 流程分析
**评审状态**: 第一轮评审后修订版

---

## 新增章节

### 4.2.1 错误分类体系

#### 可重试错误 (Retryable)
| 错误类型 | 说明 | 重试策略 |
|----------|------|----------|
| `timeout` | 任务执行超时 | 指数退避重试 |
| `rate_limit` | API 限流 | 等待限流重置后重试 |
| `temporary_failure` | 临时服务不可用 | 延迟后重试 |
| `network_error` | 网络连接问题 | 立即重试1次，失败后延迟 |

#### 不可重试错误 (Non-Retryable)
| 错误类型 | 说明 | 处理策略 |
|----------|------|----------|
| `invalid_input` | 输入参数错误 | 直接失败，返回错误信息 |
| `permission_denied` | 权限不足 | 直接失败，记录审计日志 |
| `resource_not_found` | 资源不存在 | 直接失败，建议检查资源ID |
| `validation_error` | 数据验证失败 | 直接失败，返回详细错误 |
| `budget_exceeded` | 成本预算超限 | 直接失败，触发电竞告警 |

#### 错误分类决策流程
```yaml
error_classifier:
  rules:
    - pattern: "timeout|deadline exceeded"
      type: retryable
      max_retries: 2
    - pattern: "rate limit|too many requests"
      type: retryable
      wait_for_reset: true
    - pattern: "invalid|bad request|validation"
      type: non_retryable
      log_level: error
    - pattern: "permission|unauthorized|forbidden"
      type: non_retryable
      audit: true
    - pattern: "not found|404"
      type: non_retryable
      suggest_check: "resource_id"
```

---

### 4.2.2 幂等性设计

#### 问题分析
重试机制可能导致重复操作，如：
- 重复发送邮件/通知
- 重复创建文件/记录
- 重复扣费/资源分配

#### 幂等性保障方案

##### 方案 1: 唯一请求ID (Idempotency Key)
```yaml
idempotency_config:
  key_generation: "task_id:step_id:attempt_num"
  storage:
    backend: redis  # 或本地文件
    ttl: 86400      # 24小时过期
  check_before_action: true
```

**工作流程**:
1. 生成唯一 idempotency_key: `{task_id}:{step_id}:{attempt_num}`
2. 执行前检查：该 key 是否已完成
3. 若已完成，直接返回上次结果
4. 若未完成，执行操作并记录结果

##### 方案 2: 操作前状态检查
```yaml
pre_action_check:
  file_creation:
    - check: "file_exists"
    - if_exists: "skip_with_warning"
  email_send:
    - check: "last_email_timestamp"
    - if_within: "60s"
    - action: "skip_duplicate"
```

##### 方案 3: 补偿/回滚机制
```yaml
rollback_strategy:
  enabled: true
  compensations:
    - action: create_file
      rollback: delete_file
    - action: send_email
      rollback: send_recall_notification
    - action: db_insert
      rollback: db_delete
```

#### 幂等性实现示例
```python
# 伪代码示例
def execute_with_idempotency(task_id, step_id, action_func):
    key = f"{task_id}:{step_id}"
    
    # 检查是否已执行
    if idempotency_store.exists(key):
        return idempotency_store.get_result(key)
    
    try:
        result = action_func()
        idempotency_store.save(key, result, status="success")
        return result
    except Exception as e:
        idempotency_store.save(key, error=str(e), status="failed")
        raise
```

---

### 4.2.3 资源限制与预算控制

#### 重试预算 (Retry Budget)
```yaml
retry_budget:
  # 全局限制
  max_retries_per_task: 3
  max_retries_per_hour: 10
  max_concurrent_retries: 2
  
  # 时间窗口限制
  window:
    duration: 3600  # 1小时
    max_retries: 10
    
  # 熔断机制
  circuit_breaker:
    failure_threshold: 5      # 5次失败后熔断
    recovery_timeout: 300     # 5分钟后尝试恢复
    half_open_max_calls: 1    # 半开状态允许1次试探
```

#### 并发控制
```yaml
concurrency_limits:
  per_agent:
    max_concurrent_tasks: 3
    max_retrying_tasks: 1     # 最多1个任务处于重试状态
  global:
    max_total_retries: 10     # 系统级重试上限
    retry_queue_size: 20      # 重试队列长度
```

#### 重试风暴防护
```yaml
retry_storm_protection:
  # 指数退避
  backoff_strategy:
    type: exponential
    base_delay: 10s
    max_delay: 300s
    multiplier: 2
    jitter: true              # 添加随机抖动避免共振
  
  # 自适应限流
  adaptive_throttling:
    enabled: true
    success_rate_threshold: 0.5   # 成功率低于50%时降低重试频率
    cooldown_factor: 2            # 冷却期延长2倍
```

---

### 4.2.4 成本评估

#### API 成本估算模型
```yaml
cost_model:
  base_cost_per_call: 0.001    # 每次API调用基础成本（估算）
  retry_cost_multiplier: 1.0   # 重试成本倍数（通常相同）
  
  # 各模型成本系数
  model_cost_factors:
    glm-5: 1.0
    minimax: 1.2
    kimi: 0.8
  
  # 任务复杂度成本系数
  complexity_factors:
    simple: 1.0
    medium: 1.5
    complex: 2.5
```

#### 重试成本分析
| 场景 | 基础成本 | 重试1次 | 重试2次 | 总成本增加 |
|------|----------|---------|---------|-----------|
| 简单任务 | $0.001 | $0.002 | $0.003 | +200% |
| 中等任务 | $0.0015 | $0.003 | $0.0045 | +200% |
| 复杂任务 | $0.0025 | $0.005 | $0.0075 | +200% |

**成本优化策略**:
1. **失败快速**: 不可重试错误立即失败，不浪费预算
2. **智能重试**: 仅在成功概率>30%时重试
3. **预算预警**: 接近预算上限时降低重试次数
4. **成本上限**: 设置单次任务最大成本

```yaml
cost_control:
  max_cost_per_task: 0.01      # 单次任务成本上限
  daily_budget: 1.0            # 日预算上限
  alert_threshold: 0.8         # 80%预算时告警
```

---

### 4.2.5 复杂度判定规则

#### 关键词分类表
| 复杂度 | 关键词 | 示例任务 |
|--------|--------|----------|
| **Simple** | 查询、读取、获取、查看、搜索、列出、检查 | "查询今天天气"、"获取文件列表" |
| **Medium** | 分析、比较、整理、汇总、归类、筛选 | "分析销售数据"、"整理会议纪要" |
| **Complex** | 实现、开发、构建、设计、生成、重构、优化、迁移 | "实现用户登录功能"、"重构代码架构" |

#### 自动判定规则
```yaml
complexity_rules:
  simple:
    keywords: ["查询", "读取", "获取", "查看", "搜索", "列出", "检查", "find", "get", "list", "search", "check"]
    timeout: 180s
    retry_allowed: true
    
  medium:
    keywords: ["分析", "比较", "整理", "汇总", "归类", "筛选", "统计", "分类", "analyze", "compare", "organize", "summarize"]
    timeout: 300s
    retry_allowed: true
    
  complex:
    keywords: ["实现", "开发", "构建", "设计", "生成", "重构", "优化", "迁移", "编写", "创建", "implement", "develop", "build", "design", "generate", "refactor"]
    timeout: 600s
    retry_allowed: true
    max_retries: 1        # 复杂任务仅重试1次
```

---

### 4.2.6 Checkpoint 生命周期管理

#### 清理策略
```yaml
checkpoint_lifecycle:
  # 成功场景
  on_success:
    action: delete
    delay: 300              # 成功后5分钟删除
    archive: false          # 不保留归档
  
  # 失败场景
  on_failure:
    action: retain
    retention: 86400        # 失败保留24小时
    archive_after: 604800   # 7天后归档
  
  # 过期清理
  cleanup:
    interval: 3600          # 每小时检查
    max_age: 604800         # 7天未访问的checkpoint删除
```

---

### 4.2.7 监控告警机制

#### 关键指标监控
```yaml
monitoring:
  metrics:
    - name: retry_rate
      threshold: 0.2        # 重试率>20%告警
      severity: warning
    - name: retry_success_rate
      threshold: 0.5        # 重试成功率<50%告警
      severity: critical
    - name: circuit_breaker_open
      threshold: 1
      severity: critical
    - name: cost_per_hour
      threshold: 0.5        # 小时成本>$0.5告警
      severity: warning
```

#### 告警通道
```yaml
alert_channels:
  warning:
    - log
    - metrics_dashboard
  critical:
    - log
    - email
    - pagerduty
  cost_alert:
    - log
    - daily_report
```

---

### 4.2.8 边界条件处理

#### 边界场景清单
| 场景 | 处理方式 |
|------|----------|
| 重试次数用尽 | 降级为人工处理队列，保留checkpoint |
| 连续失败N次 | 触发熔断，暂停该类任务10分钟 |
| 外部依赖不可用 | 标记为blocked，定时检查恢复 |
| 存储空间不足 | 暂停checkpoint，告警并继续执行 |
| 任务已手动取消 | 立即停止，清理checkpoint |
| Agent进程崩溃 | 从last checkpoint恢复，记录crash日志 |

---

### 4.2.9 渐进式超时替代方案

#### 方案 C: 渐进式超时递增
```yaml
progressive_timeout:
  enabled: true
  strategy:
    initial: 180s
    increment: 60s          # 每次增加60s
    max_timeout: 600s
  conditions:
    - trigger: first_retry
      timeout: 240s
    - trigger: second_retry
      timeout: 300s
    - trigger: third_retry
      timeout: 360s
```

#### 三种方案对比

| 维度 | 方案A: 自动重试 | 方案B: 增加超时 | 方案C: 渐进式超时 |
|------|----------------|----------------|------------------|
| **核心思路** | 失败后重试，保持原超时 | 预判任务复杂度，预设更长超时 | 失败后逐步增加超时时间 |
| **适用场景** | 偶发超时，网络抖动 | 任务复杂度差异大 | 任务执行时间不确定 |
| **优点** | 简单直接，成功率提升明显 | 一次完成，无重试开销 | 平衡重试成本和成功率 |
| **缺点** | 可能重复失败，浪费资源 | 简单任务等待过长 | 实现复杂度较高 |
| **资源消耗** | 中高（多次调用） | 低（单次调用） | 中（最多2-3次调用） |
| **成功率提升** | +15-20% | +10-15% | +18-25% |
| **成本控制** | 一般 | 最优 | 较好 |
| **幂等性要求** | 必需 | 无 | 必需 |

**组合推荐方案**: 方案C + 方案B

---

## 核心痛点 → 优化方案

### P0: Subagent 重试机制

**问题**: 超时后无法恢复，丢失工作

#### 方案对比分析

| 维度 | 方案A: 自动重试 | 方案B: 动态超时 | 方案C: 渐进式超时(新增) |
|------|----------------|----------------|------------------------|
| **核心机制** | 失败后重试，保持原超时 | 根据任务类型预设不同超时 | 失败后递增超时时间 |
| **实现复杂度** | 中 | 低 | 中高 |
| **成功率提升** | +15-20% | +10-15% | +18-25% |
| **API成本** | 2-3倍（每次重试） | 1倍（单次） | 1.5-2倍（平均） |
| **幂等性要求** | **必需** | 无 | **必需** |
| **适用场景** | 偶发超时、网络抖动 | 任务类型明确、可预测 | 执行时间不确定的任务 |
| **缺点** | 重试风暴风险 | 简单任务等待过长 | 实现复杂度高 |

#### 方案 A: 自动重试（更新版）
```yaml
retry_config:
  max_retries: 2
  retry_on: [timeout, rate_limit, temporary_failure]  # 基于错误分类
  backoff: 
    type: exponential
    base: 30s
    max: 120s
    jitter: true
  # 新增：幂等性保障
  idempotency:
    key_prefix: "retry"
    storage: redis
  # 新增：资源限制
  budget:
    max_per_task: 3
    max_per_hour: 10
```

#### 方案 B: 动态超时（更新版）
```yaml
timeout_strategy:
  # 基于复杂度判定规则
  simple_task: 180s     # 关键词：查询/读取/获取
  medium_task: 300s     # 关键词：分析/整理/汇总
  complex_task: 600s    # 关键词：实现/开发/构建
  
  auto_detect: true
  complexity_rules:     # 详见4.2.5节
    simple: ["查询", "读取", "获取", "search", "get"]
    medium: ["分析", "整理", "analyze", "organize"]
    complex: ["实现", "开发", "implement", "build"]
  
  # 模型系数
  model_factors:
    glm-5: 1.0
    minimax: 1.1
    kimi: 0.9
```

#### 方案 C: 渐进式超时（推荐组合方案）
```yaml
progressive_timeout:
  description: "先尝试短超时，失败后递增"
  stages:
    - attempt: 1
      timeout: 180s
      on_failure: retry_with_increased_timeout
    - attempt: 2
      timeout: 300s
      on_failure: retry_final
    - attempt: 3
      timeout: 450s
      on_failure: fail_and_escalate
  
  # 成本上限保护
  cost_guard:
    max_cost: 0.005       # $0.005上限
    on_exceed: fail_fast
```

**最终推荐**: **方案C + 方案B组合**
- 首次使用动态超时（基于任务复杂度）
- 超时后采用渐进式递增重试
- 配合幂等性保障和资源限制
- 成功率最高(+18-25%)，成本可控

---

### P1: 中间结果保存 (Checkpoint)

**问题**: 超时后无法知道已完成部分

#### 方案对比

| 维度 | 方案A: 每步保存 | 方案B: 定时保存 |
|------|----------------|----------------|
| **粒度** | 步骤级 | 时间级(30s) |
| **精度** | 高（精确到步骤） | 中（可能重复/丢失） |
| **存储开销** | 中 | 高（频繁写入） |
| **恢复效率** | 高（精确恢复） | 中（可能重复执行） |
| **适用场景** | 多步骤任务 | 长时间连续任务 |

#### 方案 A: 每步保存（推荐，更新版）
```yaml
checkpoint_strategy:
  save_per_step: true
  checkpoint_file: .task-checkpoint.json
  include: [step_id, output_files, progress, timestamp, idempotency_key]
  
  # 新增：生命周期管理
  lifecycle:
    on_success:
      action: delete
      delay: 300              # 成功后5分钟删除
    on_failure:
      action: retain
      retention: 86400        # 失败保留24小时
    cleanup:
      interval: 3600
      max_age: 604800         # 7天清理
  
  # 新增：完整性验证
  validation:
    checksum: true
    verify_on_load: true
```

#### 方案 B: 定时保存
```yaml
checkpoint_strategy:
  interval: 30s
  checkpoint_file: .task-checkpoint.json
  
  # 优化：智能间隔
  smart_interval:
    base: 30s
    max: 120s
    idle_multiplier: 2        # 空闲时延长间隔
```

**推荐**: **方案 A**（每步保存）
- 更精确的恢复点
- 明确的清理策略（成功5分钟后删除，失败保留24h）
- 与现有任务文件配合

---

### P2: 动态超时策略

**问题**: 超时配置不够灵活

**方案**: 智能超时
```yaml
timeout_heuristics:
  factors:
    - task_complexity: [simple, medium, complex]
    - model: [glm-5, minimax, kimi]
    - env: [sandbox, host]
  formula: base_timeout * complexity_factor * model_factor
```

**示例**:
| 任务类型 | 基础超时 | 因子 | 最终超时 |
|----------|---------|------|---------|
| 简单搜索 | 180s | 1.0 | 180s |
| 数据分析 | 180s | 1.5 | 270s |
| 代码生成 | 180s | 2.0 | 360s |

---

### P3: 任务拆分模板

**问题**: 拆分粒度不一致

**方案**: 标准模板
```yaml
task_template:
  max_steps: 5
  step_types:
    - analysis: 收集信息，分析现状
    - design: 设计方案，定义输出
    - execute: 执行操作，生成结果
    - verify: 验证输出，确认质量
    - document: 文档记录，总结汇报
  max_duration_per_step: 300s
```

---

## 实验矩阵

| 实验ID | 优化点 | 变体 | 对照组 | 关键指标 |
|--------|--------|------|--------|----------|
| **E1** | 重试机制 | A: 渐进式超时重试 | B: 无重试 | 成功率, 成本, 重试率 |
| **E2** | 中间保存 | A: 每步保存+生命周期管理 | B: 不保存 | 可恢复率, 存储开销 |
| **E3** | 超时策略 | A: 动态超时(复杂度判定) | B: 固定300s | 超时率, 平均耗时 |
| **E4** | 拆分模板 | A: 标准模板 | B: 自由拆分 | 完成质量, 步骤一致性 |
| **E5** | 幂等性 | A: 带幂等性保障的重试 | B: 无幂等性检查 | 重复操作率, 数据一致性 |
| **E6** | 资源限制 | A: 预算控制+熔断 | B: 无限制 | 重试风暴次数, 成本控制 |

---

## 实验优先级

| 优先级 | 实验 | 预估提升 | 复杂度 |
|--------|------|---------|--------|
| **P0** | E1: 重试机制 | 成功率 +15-20% | 中 |
| **P1** | E2: 中间保存 | 可恢复性 +100% | 中 |
| **P2** | E3: 动态超时 | 超时率 -30% | 低 |
| **P3** | E4: 拆分模板 | 拆分质量 +10% | 低 |

---

## 实验设计

### E1: 重试机制实验（更新版）

**测试任务**: 执行一个会超时的任务
- 变体 A: 渐进式超时重试（方案C）
- 变体 B: 无重试（对照组）
- 变体 C: 纯自动重试（方案A）

**评估指标**:
| 指标 | 说明 | 告警阈值 |
|------|------|----------|
| 成功率 | 最终完成任务的比例 | <70% 告警 |
| 重试次数 | 平均重试次数 | >3 告警 |
| 重试成功率 | 重试后成功的比例 | <30% 告警 |
| 总耗时 | 包括重试的总时间 | - |
| API成本 | 实际消耗的API成本 | >$0.01/任务 |

**新增监控指标**:
```yaml
metrics:
  - retry_rate              # 重试率
  - retry_success_rate      # 重试成功率
  - cost_per_task          # 单任务成本
  - circuit_breaker_status # 熔断状态
```

---

### E2: 中间保存实验（更新版）

**测试任务**: 多步骤任务（5步）
- 变体 A: 每步保存 checkpoint + 生命周期管理
- 变体 B: 不保存

**测试场景**: 第3步超时
- 变体 A: 可从第3步继续，checkpoint在5分钟后自动清理
- 变体 B: 需从第1步重新开始

**评估指标**:
| 指标 | 说明 |
|------|------|
| 可恢复率 | 能否从checkpoint恢复 |
| 恢复完整性 | 恢复后的数据完整性 |
| 存储开销 | checkpoint占用空间 |
| 清理有效性 | 成功/失败后的清理是否正确 |

---

### E5: 幂等性实验（新增）

**测试任务**: 重复执行同一任务多次
- 变体 A: 带幂等性检查的重试
- 变体 B: 无幂等性检查的重试

**测试场景**:
1. 网络超时，触发重试
2. 检查是否产生重复操作（重复文件、重复消息等）

**评估指标**:
| 指标 | 说明 |
|------|------|
| 重复操作率 | 实际发生重复操作的比例 |
| 幂等性检查命中 | 幂等性检查正确拦截的次数 |
| 数据一致性 | 最终状态是否符合预期 |

---

### E6: 资源限制实验（新增）

**测试任务**: 高压力场景下的重试行为
- 变体 A: 带预算控制和熔断
- 变体 B: 无限制

**测试场景**:
1. 连续触发10个超时任务
2. 观察重试行为和资源消耗

**评估指标**:
| 指标 | 说明 | 阈值 |
|------|------|------|
| 重试风暴次数 | 短时间内大量重试的次数 | 0 (应避免) |
| 熔断触发次数 | 熔断机制生效的次数 | - |
| 成本超限次数 | 超出预算的次数 | 0 |
| 队列堆积 | 等待重试的任务数 | <20 |

---

*设计完成: 2026-04-17*
*第一轮评审修订: 2026-04-17*
*更新内容: 错误分类体系、幂等性设计、资源限制、成本评估、复杂度判定规则、Checkpoint生命周期、监控告警、边界条件处理、渐进式超时方案*

*下一步: Step 4.3 执行实验 (E1-E6)*