# 评估指标体系设计文档

> Phase 1.3 输出文档 - 评估指标体系定义
> 创建日期: 2026-04-14
> 版本: v1.0

---

## 一、概述

### 1.1 评估指标的作用

评估指标是优化测试框架的核心，用于：
- **量化效果**：将主观感受转化为客观数据
- **对比决策**：在多个变体间选择最优方案
- **追踪进步**：衡量优化是否有效
- **驱动迭代**：识别改进方向

### 1.2 设计原则

| 原则 | 说明 | 示例 |
|------|------|------|
| **可量化** | 指标必须是数值型，可计算 | 成功率 95% (✅) vs "很快" (❌) |
| **可比较** | 不同变体间可直接对比 | 准确率可对比 |
| **可获取** | 能够通过实验测量得到 | 可通过脚本统计 |
| **有意义** | 与目标直接相关 | 成功率 vs 代码行数 |

---

## 二、通用评估维度

### 2.1 三大核心维度

```
┌─────────────────────────────────────────┐
│           通用评估维度                    │
├─────────────┬─────────────┬─────────────┤
│   有效性    │   效率      │   稳定性    │
│Effectiveness│ Efficiency  │ Reliability │
├─────────────┼─────────────┼─────────────┤
│ 任务完成    │ 执行时间    │ 成功率      │
│ 目标达成    │ 资源消耗    │ 一致性      │
│ 质量水平    │ 成本开销    │ 错误率      │
└─────────────┴─────────────┴─────────────┘
```

### 2.2 维度说明

| 维度 | 关注点 | 典型指标 |
|------|--------|----------|
| **有效性** | 做得对不对、好不好 | 准确率、完成率、质量分 |
| **效率** | 做得快不快、省不省 | 执行时间、资源占用、成本 |
| **稳定性** | 做得稳不稳、可不可靠 | 成功率、错误率、方差 |

---

## 三、场景特定评估指标

### 3.1 网页抓取场景 (web_scrape)

**目标**：找到最优的抓取工具组合

**一级指标**（核心决策依据）：

| 指标名 | 符号 | 计算方式 | 目标值 | 权重 |
|--------|------|----------|--------|------|
| **信息完整率** | P_complete | 成功提取字段数 / 总字段数 | > 90% | 35% |
| **准确率** | P_accuracy | 正确提取数 / 总提取数 | > 85% | 35% |
| **成功率** | P_success | 成功请求数 / 总请求数 | > 95% | 30% |

**二级指标**（辅助分析）：

| 指标名 | 符号 | 计算方式 | 说明 |
|--------|------|----------|------|
| 平均响应时间 | T_avg | 总耗时 / 请求数 | 反映效率 |
| 信息密度 | D_info | 有效内容量 / 页面大小 | 反映质量 |
| 错误分类 | E_types | 超时/解析失败/网络错误计数 | 问题诊断 |

**综合得分计算**：
```
Score_web = 0.35 × P_complete + 0.35 × P_accuracy + 0.30 × P_success

如果 T_avg > 阈值: Score_web *= 0.9  # 时间惩罚
```

### 3.2 长任务执行场景 (long_task)

**目标**：优化多步骤任务的执行稳定性

**一级指标**：

| 指标名 | 符号 | 计算方式 | 目标值 | 权重 |
|--------|------|----------|--------|------|
| **完成率** | R_complete | 完成任务数 / 总任务数 | > 92% | 40% |
| **步骤成功率** | R_step | 成功步骤数 / 总步骤数 | > 95% | 35% |
| **平均步骤时间** | T_step | 总时间 / 总步骤数 | < 60s | 25% |

**二级指标**：

| 指标名 | 说明 |
|--------|------|
| 中断率 | 用户/系统中断的比例 |
| 重试次数 | 平均每任务的重试次数 |
| 错误恢复率 | 自动恢复成功 / 错误总数 |

**综合得分**：
```
Score_task = 0.40 × R_complete + 0.35 × R_step + 0.25 × (1 / T_step_norm)
```

### 3.3 Skill vs 注意力场景 (skill_attention)

**目标**：优化 Skill 触发准确性和响应质量

**一级指标**：

| 指标名 | 符号 | 计算方式 | 目标值 | 权重 |
|--------|------|----------|--------|------|
| **触发准确率** | A_trigger | 正确触发 / 应触发总数 | > 88% | 40% |
| **响应质量分** | Q_response | 1-5 评分均值 | > 4.0 | 35% |
| **误触发率** | F_trigger | 误触发 / 总触发 | < 5% | 25% |

**二级指标**：

| 指标名 | 说明 |
|--------|------|
| 响应时间 | 从请求到响应的时间 |
| Token 效率 | 有效信息 / 总 Token 数 |
| 用户满意度 | 显式反馈评分 |

**综合得分**：
```
Score_skill = 0.40 × A_trigger + 0.35 × Q_response + 0.25 × (1 - F_trigger)
```

---

## 四、指标计算示例

### 4.1 网页抓取实验数据

```
实验数据:
- 请求 URL 数: 100
- 成功响应: 95
- 成功解析: 90
- 正确提取字段: 850 / 1000 期望字段
- 总耗时: 245.3 秒

指标计算:
- P_success = 95 / 100 = 0.95 (95%)
- P_complete = 850 / 1000 = 0.85 (85%)
- P_accuracy = 90 / 95 = 0.947 (94.7%)
- T_avg = 245.3 / 100 = 2.453 秒

综合得分:
Score = 0.35×0.85 + 0.35×0.947 + 0.30×0.95 = 0.916 (91.6%)
```

### 4.2 metrics_json 结构

```json
{
  "scenario": "web_scrape",
  "primary_metric": "score",
  "values": {
    "score": 0.916,
    "success_rate": 0.95,
    "completeness": 0.85,
    "accuracy": 0.947,
    "avg_time_sec": 2.453
  },
  "metadata": {
    "total_requests": 100,
    "successful": 95,
    "parsed": 90,
    "fields_expected": 1000,
    "fields_extracted": 850
  }
}
```

---

## 五、评估工具设计

### 5.1 指标计算函数（Python）

```python
def evaluate_web_scrape(results):
    """网页抓取场景评估"""
    total = results['total_requests']
    success = results['successful']
    parsed = results['parsed']
    fields_exp = results['fields_expected']
    fields_ext = results['fields_extracted']
    
    p_success = success / total
    p_complete = fields_ext / fields_exp
    p_accuracy = parsed / success if success > 0 else 0
    
    score = (0.35 * p_complete + 
             0.35 * p_accuracy + 
             0.30 * p_success)
    
    return {
        'score': round(score, 3),
        'success_rate': round(p_success, 3),
        'completeness': round(p_complete, 3),
        'accuracy': round(p_accuracy, 3)
    }

def evaluate_long_task(results):
    """长任务执行场景评估"""
    complete = results['completed_tasks']
    total = results['total_tasks']
    steps_success = results['successful_steps']
    steps_total = results['total_steps']
    time_total = results['total_time_sec']
    
    r_complete = complete / total
    r_step = steps_success / steps_total if steps_total > 0 else 0
    t_step = time_total / steps_total if steps_total > 0 else 0
    
    # 归一化时间得分 (假设目标 60s)
    t_step_norm = min(t_step / 60, 1.0)
    
    score = (0.40 * r_complete + 
             0.35 * r_step + 
             0.25 * (1 - t_step_norm))
    
    return {
        'score': round(score, 3),
        'completion_rate': round(r_complete, 3),
        'step_success_rate': round(r_step, 3),
        'avg_step_time': round(t_step, 1)
    }

def evaluate_skill_attention(results):
    """Skill vs 注意力场景评估"""
    correct = results['correct_triggers']
    should = results['should_trigger']
    total = results['total_triggers']
    quality = results['response_quality_sum']
    count = results['response_count']
    
    a_trigger = correct / should if should > 0 else 0
    q_response = quality / count if count > 0 else 0
    f_trigger = (total - correct) / total if total > 0 else 0
    
    score = (0.40 * a_trigger + 
             0.35 * min(q_response / 5, 1.0) + 
             0.25 * (1 - f_trigger))
    
    return {
        'score': round(score, 3),
        'trigger_accuracy': round(a_trigger, 3),
        'response_quality': round(q_response, 1),
        'false_positive_rate': round(f_trigger, 3)
    }
```

### 5.2 变体对比报告

```python
def compare_variants(df, scenario):
    """对比不同变体的表现"""
    
    # 按变体分组统计
    summary = df.groupby('variant_id').agg({
        'score': ['mean', 'std', 'count'],
        'success_rate': 'mean',
        'duration_sec': 'mean'
    }).round(3)
    
    # 找出最佳变体
    best = summary['score']['mean'].idxmax()
    
    return {
        'summary': summary,
        'best_variant': best,
        'best_score': summary.loc[best, ('score', 'mean')]
    }
```

---

## 六、验收检查清单

- [x] 评估维度定义（有效性、效率、稳定性）
- [x] 网页抓取场景指标（一级/二级）
- [x] 长任务执行场景指标
- [x] Skill vs 注意力场景指标
- [x] 指标计算示例
- [x] 综合得分公式
- [x] 工具函数设计
- [x] metrics_json 结构规范

---

## 七、与框架设计对齐

本文档定义的指标与 `framework-design.md` 中的评估分析组件对齐：

```
framework-design.md:
├── 3.3 评估分析组件 (Result Analyzer)
│   ├── calculate_metrics() ← 本文档定义计算公式
│   ├── compare_variants()  ← 本文档定义对比方法
│   └── find_best_variant() ← 基于综合得分选择
│
本文档:
├── 三、场景特定评估指标
├── 四、指标计算示例
└── 五、评估工具设计
```

---

*本文档是 OpenClaw 优化测试框架 Phase 1.3 的输出成果。*
