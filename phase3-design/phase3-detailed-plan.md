# Phase 3 详细计划：网页抓取工具优化

## 目标

提升对各种类型网页和平台内容抓取的成功率和效率，建立最优的工具组合策略。

---

## 当前差距分析

| 维度 | 当前状态 | 目标状态 | 差距 |
|------|---------|---------|------|
| **策略设计** | 6类场景定义、工具映射 | ✅ 完成 | 无 |
| **配置文件** | config.yaml 完整 | ✅ 完成 | 无 |
| **场景检测实现** | ❌ 只有描述，无代码 | 可执行检测逻辑 | **100%差距** |
| **成功率验证** | ❌ 全部估算值 | 实测验证数据 | **100%差距** |
| **Fallback实现** | ❌ 未测试 | 已验证有效 | **100%差距** |
| **工具切换逻辑** | ❌ 未实现 | 自动切换代码 | **100%差距** |
| **统计分析** | ⚠️ 50%模拟数据 | 真实数据报告 | **50%差距** |

---

## 关键问题：配置 ≠ 实现

当前 config.yaml 定义了策略，但 **search.py 未使用这些策略**。

```
问题：只有静态配置，没有可执行逻辑
影响：策略无法实际应用，优化效果无法验证
严重性：Phase 3 实际进度仅 20%，远未完成
```

---

## 需要完成的具体工作

### P1: 场景检测实现

**当前配置（描述性）**：
```yaml
detect: "url matches blog/article pattern, no auth required"
```

**需要实现（可执行）**：
```yaml
detect:
  url_patterns: ["*.blog", "*/article/*", "*/post/*"]
  exclude: ["medium.com", "reddit.com"]
  auth_required: false
```

**代码实现需求**：
```python
def detect_scenario(url_or_query):
    """根据 URL/查询特征识别场景"""
    # 1. URL 模式匹配（正则或字符串匹配）
    # 2. 平台识别（域名列表）
    # 3. 反爬检测（已知反爬网站列表）
    # 4. 返回场景名称（static/anti_scrape/platform/spa/search/realtime）
```

---

### P1: 成功率验证

| 场景 | 当前数据来源 | 需要执行 |
|------|-------------|---------|
| static | 估算 | 10+ 实际测试 |
| anti_scrape | 估算 | 10+ 实际测试 |
| platform | 估算 | 10+ 实际测试 |
| spa | 估算 | 10+ 实际测试 |
| search | 模拟数据 | 20+ 实际搜索 |
| realtime | 估算 | 10+ 实际测试 |

**总计需要**：**70+ 测试用例**（当前仅 10-11 个）

---

### P1: 工具切换逻辑

**当前代码**：
```python
def search_with_fallback(query):
    engines = ["tavily", "brave", "google"]
    for engine in engines:
        result = execute_search(engine, query)
        if result.success:
            return result
```

**需要实现**：
```python
def smart_search(request):
    # 1. 检测场景
    scenario = detect_scenario(request)
    
    # 2. 选择工具链
    tools = load_tools_for_scenario(scenario)
    
    # 3. 执行工具链（含 Fallback）
    for tool in tools:
        result = execute_tool(tool, request)
        if result.success:
            record_success(tool, scenario)
            return result
        else:
            record_failure(tool, scenario)
            continue  # Fallback 到下一个工具
    
    return error_result
```

---

### P2: 参数优化

| 参数 | 当前 | 需探索 |
|------|------|--------|
| timeout | 固定 15/30s | 动态调整策略 |
| retry_count | 固定 1 | 根据重要性调整 |
| wait_strategy | networkidle | SPA 类型细化 |

---

### P3: 扩展优化

| 方向 | 内容 |
|------|------|
| 新场景 | SSR 页面、登录内容、API 端点、文件下载 |
| 智能决策 | URL 分类、历史学习、额度优化 |
| 平台扩展 | 更多 opencli 命令 |

---

## 执行计划

### Step 3.1: 场景检测实现 (P1)

| 子任务 | 预估时间 | 输出 |
|--------|---------|------|
| 设计检测规则 | 1h | detect_rules.yaml |
| 实现 detect_scenario() | 2h | search.py 新函数 |
| 单元测试 | 1h | test_detect.py |
| 验证准确性 | 1h | 测试报告 |

**总计**: 5h

---

### Step 3.2: 真实环境测试 (P1)

| 子任务 | 预估时间 | 输出 |
|--------|---------|------|
| 准备测试用例 | 2h | 70+ URLs/Queries |
| Host 环境执行 | 4h | 实验数据 JSON |
| 收集统计数据 | 2h | 成功率报告 |
| 分析结果 | 2h | 分析报告 |

**总计**: 10h

---

### Step 3.3: 工具切换实现 (P1)

| 子任务 | 预估时间 | 输出 |
|--------|---------|------|
| 实现 smart_search() | 2h | search.py 核心逻辑 |
| 实现 Fallback 机制 | 1h | fallback.py |
| 集成测试 | 2h | 测试报告 |
| 验证有效性 | 2h | 对比报告 |

**总计**: 7h

---

### Step 3.4: 参数优化 (P2)

| 子任务 | 预估时间 | 输出 |
|--------|---------|------|
| timeout 实验 | 2h | 优化配置 |
| retry 实验 | 1h | 优化配置 |
| wait_strategy 实验 | 2h | SPA 策略 |

**总计**: 5h

---

### Step 3.5: 最终报告 (P1)

| 子任务 | 预估时间 | 输出 |
|--------|---------|------|
| 数据汇总 | 2h | 统计报告 |
| 策略文档 | 2h | 最终策略文档 |
| 方法论总结 | 2h | Phase 3 总结 |

**总计**: 6h

---

**总预估**: 33h

---

## 验收标准

| 标准 | 完成定义 | 验证方式 |
|------|---------|---------|
| **场景检测** | 6类场景自动识别准确率 >90% | 测试验证 |
| **成功率数据** | 6类场景各有 10+ 真实测试数据 | 数据文件 |
| **工具策略** | smart_search() 实现并验证有效 | 代码 + 测试 |
| **对比报告** | 优化前 vs 优化后数据对比 | 分析报告 |
| **文档完整** | SKILL.md + 最终策略文档 | 文档检查 |

---

## 阻塞与依赖

| 问题 | 任务ID | 解决方案 |
|------|--------|---------|
| Sandbox 限制 | `task-20260417083500` | Host 环境测试 |
| opencli Node 缺失 | 同上 | Host 环境 |
| browser Socket 限制 | 同上 | Host 环境 |

---

## 当前进度

```
总体进度: 20% (设计阶段，未实现)

✅ 完成: 策略设计、配置文件
⚠️ 进行中: 无
⏳ 待执行: 场景检测实现、真实测试、代码实现、验证、报告
```

---

*创建时间: 2026-04-17*
*关联任务: task-20260414222302*