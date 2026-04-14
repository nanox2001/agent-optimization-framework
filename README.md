# OpenClaw 优化测试框架

基于 autoresearch 方法论设计的自动化优化测试框架。

## 核心理念

```
修改 → 执行 → 评估 → 决策 → 记录 → 重复
```

## 项目结构

```
optimization-framework/
├── phase1-design/           # Phase 1 设计文档
│   ├── framework-design.md      # 框架架构设计
│   ├── experiments-format.md    # 实验记录格式规范
│   └── evaluation-metrics.md    # 评估指标体系
├── scripts/                 # 执行脚本
│   ├── run-experiment.sh        # 实验执行主脚本
│   ├── experiment-runner.sh     # 实验运行器
│   └── analyze-results.py       # 结果分析工具
├── data/                    # 数据目录
│   └── experiments.tsv          # 实验记录
└── README.md               # 本文件
```

## 快速开始

### 运行实验

```bash
./scripts/run-experiment.sh \
  --config configs/web_scrape.yaml \
  --variant v_baseline \
  --scenario web_scrape
```

### 分析结果

```bash
python3 scripts/analyze-results.py \
  --scenario web_scrape \
  --output report.md
```

## 文档

- [框架架构设计](phase1-design/framework-design.md)
- [实验记录格式](phase1-design/experiments-format.md)
- [评估指标体系](phase1-design/evaluation-metrics.md)

## 应用场景

1. **网页抓取优化** - 找到最优的 parser + fetcher 组合
2. **长任务执行优化** - 优化多步骤任务执行流程
3. **Skill vs 注意力优化** - 提升触发准确性和响应质量

## License

MIT