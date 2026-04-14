# OpenClaw 优化测试框架 - 测试用例设计文档

> Phase 2 输出文档 - 验收测试用例
> 创建日期: 2026-04-15
> 版本: v1.0

---

## 一、测试范围

### 1.1 测试目标

本文档为 OpenClaw 优化测试框架设计全面的验收测试用例，确保框架各核心模块功能正确、稳定可靠。

### 1.2 覆盖模块

| 模块 | 对应文件 | 测试重点 |
|------|----------|----------|
| **实验执行脚本** | `run-experiment.sh` | 参数解析、实验ID生成、超时控制、TSV记录写入 |
| **实验运行器** | `experiment-runner.sh` | 配置读取、实验执行、JSON输出格式 |
| **结果分析工具** | `analyze-results.py` | 数据加载、统计分析、报告生成、变体对比 |
| **TSV记录格式** | `experiments.tsv` | 字段完整性、格式正确性、数据一致性 |
| **评估指标计算** | 指标计算函数 | 准确性、场景适配、边界情况处理 |

### 1.3 测试类型

- **功能测试**：验证各功能模块按设计正确运行
- **边界测试**：验证极端情况和异常处理
- **集成测试**：验证模块间协作
- **数据验证**：验证输入输出数据格式和准确性

---

## 二、测试用例列表

### 2.1 实验执行脚本测试 (run-experiment.sh)

#### TC-001: 基本参数解析验证

| 项目 | 内容 |
|------|------|
| **用例ID** | TC-001 |
| **测试目的** | 验证脚本能正确解析所有必需和可选参数 |
| **前置条件** | 1. 脚本具有执行权限<br>2. 配置文件 `configs/test.yaml` 存在<br>3. `data/` 目录可写 |
| **测试步骤** | 1. 执行: `./run-experiment.sh --config configs/test.yaml --variant v_test --scenario web_scrape --phase phase3 --timeout 300 --description "Test experiment"`<br>2. 观察输出和返回码 |
| **预期结果** | 1. 脚本正常执行，返回码 0<br>2. 正确显示所有参数值<br>3. 生成正确的实验ID格式 (exp_XXXX) |
| **优先级** | 高 |

#### TC-002: 缺少必需参数处理

| 项目 | 内容 |
|------|------|
| **用例ID** | TC-002 |
| **测试目的** | 验证脚本对缺少必需参数的处理 |
| **前置条件** | 脚本具有执行权限 |
| **测试步骤** | 1. 执行: `./run-experiment.sh` (不带任何参数)<br>2. 执行: `./run-experiment.sh --config configs/test.yaml` (缺少 --variant)<br>3. 执行: `./run-experiment.sh --variant v_test` (缺少 --config) |
| **预期结果** | 1. 每次执行都返回非零退出码<br>2. 显示错误信息指明缺少的参数<br>3. 显示帮助信息 |
| **优先级** | 高 |

#### TC-003: 无效配置文件处理

| 项目 | 内容 |
|------|------|
| **用例ID** | TC-003 |
| **测试目的** | 验证脚本对不存在配置文件的异常处理 |
| **前置条件** | 脚本具有执行权限 |
| **测试步骤** | 1. 执行: `./run-experiment.sh --config /nonexistent/path.yaml --variant v_test` |
| **预期结果** | 1. 返回非零退出码<br>2. 显示错误信息: "配置文件不存在"<br>3. 不创建任何实验记录 |
| **优先级** | 高 |

#### TC-004: 实验ID递增验证

| 项目 | 内容 |
|------|------|
| **用例ID** | TC-004 |
| **测试目的** | 验证实验ID按顺序递增 |
| **前置条件** | 1. `experiments.tsv` 文件已存在并有若干记录<br>2. 最后一个实验ID为 exp_0005 |
| **测试步骤** | 1. 连续执行3次实验<br>2. 检查生成的实验ID |
| **预期结果** | 1. 第一次生成 exp_0006<br>2. 第二次生成 exp_0007<br>3. 第三次生成 exp_0008<br>4. ID格式始终为 exp_4位数字 |
| **优先级** | 中 |

#### TC-005: 超时机制验证

| 项目 | 内容 |
|------|------|
| **用例ID** | TC-005 |
| **测试目的** | 验证超时机制能正确终止长时间运行的实验 |
| **前置条件** | 1. 存在执行时间超过5秒的测试配置<br>2. 测试脚本模拟长时间运行 |
| **测试步骤** | 1. 执行: `./run-experiment.sh --config configs/slow.yaml --variant v_slow --timeout 2`<br>2. 等待执行完成 |
| **预期结果** | 1. 实验在约2秒后被终止<br>2. TSV中 status 字段为 "timeout"<br>3. exit_code 为 124<br>4. duration_sec 约等于2 |
| **优先级** | 高 |

#### TC-006: Dry-run 模式验证

| 项目 | 内容 |
|------|------|
| **用例ID** | TC-006 |
| **测试目的** | 验证 dry-run 模式不写入实际记录 |
| **前置条件** | 1. 记录当前 experiments.tsv 行数<br>2. 脚本具有执行权限 |
| **测试步骤** | 1. 执行: `./run-experiment.sh --config configs/test.yaml --variant v_dry --dry-run`<br>2. 检查 experiments.tsv 行数 |
| **预期结果** | 1. 脚本显示 "[DRY RUN]" 信息<br>2. experiments.tsv 行数不变<br>3. 不生成实验输出目录 |
| **优先级** | 中 |

#### TC-007: TSV记录格式验证

| 项目 | 内容 |
|------|------|
| **用例ID** | TC-007 |
| **测试目的** | 验证生成的 TSV 记录格式符合规范 |
| **前置条件** | 1. 成功执行一次实验<br>2. experiments.tsv 文件存在 |
| **测试步骤** | 1. 读取 experiments.tsv 最后一行<br>2. 分割字段验证数量和格式 |
| **预期结果** | 1. 共15个字段（含表头16列）<br>2. timestamp 为 ISO8601 格式<br>3. experiment_id 格式正确<br>4. duration_sec 为数字<br>5. metrics_json 为有效 JSON |
| **优先级** | 高 |

#### TC-008: 输出目录结构验证

| 项目 | 内容 |
|------|------|
| **用例ID** | TC-008 |
| **测试目的** | 验证输出目录和文件正确创建 |
| **前置条件** | 成功执行一次实验 |
| **测试步骤** | 1. 检查实验输出目录<br>2. 验证各文件存在性和内容 |
| **预期结果** | 1. 目录结构: `data/experiments/YYYY-MM-DD/exp_XXXX/`<br>2. 包含文件: stdout.log, stderr.log, config.yaml, summary.json<br>3. config.yaml 与输入配置一致 |
| **优先级** | 中 |

---

### 2.2 实验运行器测试 (experiment-runner.sh)

#### TC-009: 基本执行验证

| 项目 | 内容 |
|------|------|
| **用例ID** | TC-009 |
| **测试目的** | 验证实验运行器能正确执行并返回结果 |
| **前置条件** | 1. 配置文件存在且有效<br>2. 脚本具有执行权限 |
| **测试步骤** | 1. 直接执行: `./experiment-runner.sh configs/test.yaml v_test`<br>2. 验证输出格式 |
| **预期结果** | 1. 返回码为 0<br>2. 最后一行输出为有效 JSON<br>3. JSON 包含 scenario, primary_metric, values, metadata 字段 |
| **优先级** | 高 |

#### TC-010: 无效配置处理

| 项目 | 内容 |
|------|------|
| **用例ID** | TC-010 |
| **测试目的** | 验证对不存在配置文件的处理 |
| **前置条件** | 脚本具有执行权限 |
| **测试步骤** | 1. 执行: `./experiment-runner.sh /nonexistent.yaml v_test` |
| **预期结果** | 1. 返回非零退出码<br>2. 向 stderr 输出错误信息<br>3. 不输出 JSON |
| **优先级** | 中 |

#### TC-011: JSON输出格式验证

| 项目 | 内容 |
|------|------|
| **用例ID** | TC-011 |
| **测试目的** | 验证输出的 JSON 符合 metrics_json 规范 |
| **前置条件** | 成功执行实验运行器 |
| **测试步骤** | 1. 捕获最后一行输出<br>2. 使用 jq 验证 JSON 格式<br>3. 检查必需字段 |
| **预期结果** | 1. JSON 格式有效，可被 jq 解析<br>2. 包含 scenario 字段<br>3. 包含 primary_metric 字段<br>4. values 对象包含数值指标<br>5. metadata 包含实验元数据 |
| **优先级** | 高 |

---

### 2.3 结果分析工具测试 (analyze-results.py)

#### TC-012: 基本数据加载验证

| 项目 | 内容 |
|------|------|
| **用例ID** | TC-012 |
| **测试目的** | 验证工具能正确加载 TSV 文件 |
| **前置条件** | 1. 存在有效的 experiments.tsv 文件<br>2. 文件包含至少5条记录 |
| **测试步骤** | 1. 执行: `python3 analyze-results.py --input data/experiments.tsv`<br>2. 观察输出 |
| **预期结果** | 1. 工具正常执行，无异常<br>2. 显示实验统计信息<br>3. 显示变体对比表格 |
| **优先级** | 高 |

#### TC-013: 场景筛选验证

| 项目 | 内容 |
|------|------|
| **用例ID** | TC-013 |
| **测试目的** | 验证 --scenario 参数能正确筛选数据 |
| **前置条件** | experiments.tsv 包含多个场景的记录（web_scrape, long_task） |
| **测试步骤** | 1. 执行: `python3 analyze-results.py --scenario web_scrape`<br>2. 执行: `python3 analyze-results.py --scenario long_task`<br>3. 对比两次输出 |
| **预期结果** | 1. 每次只显示对应场景的数据<br>2. 统计数字与场景数据匹配<br>3. 不显示其他场景的记录 |
| **优先级** | 高 |

#### TC-014: 统计计算准确性验证

| 项目 | 内容 |
|------|------|
| **用例ID** | TC-014 |
| **测试目的** | 验证统计指标计算准确 |
| **前置条件** | 准备已知数据的测试 TSV 文件 |
| **测试步骤** | 1. 创建测试数据: 10条记录，7成功，2超时，1错误，平均耗时 100s<br>2. 执行分析工具<br>3. 验证统计结果 |
| **预期结果** | 1. total_experiments = 10<br>2. completed = 7<br>3. timeout = 2<br>4. error = 1<br>5. success_rate = 0.7<br>6. avg_duration ≈ 100 |
| **优先级** | 高 |

#### TC-015: 变体对比排序验证

| 项目 | 内容 |
|------|------|
| **用例ID** | TC-015 |
| **测试目的** | 验证变体按得分正确排序 |
| **前置条件** | TSV 包含3个变体，得分分别为 0.8, 0.9, 0.85 |
| **测试步骤** | 1. 执行分析工具<br>2. 查看变体对比表格 |
| **预期结果** | 1. 排名第一的变体是得分为 0.9 的<br>2. 排名第二的是 0.85<br>3. 排名第三的是 0.8<br>4. "最佳变体"部分显示得分为0.9的变体 |
| **优先级** | 中 |

#### TC-016: 报告输出到文件验证

| 项目 | 内容 |
|------|------|
| **用例ID** | TC-016 |
| **测试目的** | 验证 --output 参数能正确写入文件 |
| **前置条件** | 具有写入权限 |
| **测试步骤** | 1. 执行: `python3 analyze-results.py --output report.md`<br>2. 检查生成的文件 |
| **预期结果** | 1. 文件 report.md 存在<br>2. 文件内容与标准输出一致<br>3. 文件包含完整的 Markdown 报告 |
| **优先级** | 中 |

#### TC-017: JSON格式报告验证

| 项目 | 内容 |
|------|------|
| **用例ID** | TC-017 |
| **测试目的** | 验证 --format json 输出正确 |
| **前置条件** | 存在有效实验数据 |
| **测试步骤** | 1. 执行: `python3 analyze-results.py --format json`<br>2. 验证输出格式 |
| **预期结果** | 1. 输出为有效 JSON<br>2. 包含 stats 和 summary 字段<br>3. 所有数值类型正确 |
| **优先级** | 低 |

#### TC-018: 空数据或无效输入处理

| 项目 | 内容 |
|------|------|
| **用例ID** | TC-018 |
| **测试目的** | 验证工具对空数据或无效文件的处理 |
| **前置条件** | 1. 创建空 TSV 文件<br>2. 创建只有表头的 TSV 文件 |
| **测试步骤** | 1. 执行工具指向空文件<br>2. 执行工具指向只有表头的文件 |
| **预期结果** | 1. 工具不崩溃<br>2. 显示 "No experiments found" 或类似信息<br>3. 正常退出（返回码0） |
| **优先级** | 中 |

#### TC-019: 不存在输入文件处理

| 项目 | 内容 |
|------|------|
| **用例ID** | TC-019 |
| **测试目的** | 验证对不存在输入文件的错误处理 |
| **前置条件** | 确保 /nonexistent.tsv 不存在 |
| **测试步骤** | 1. 执行: `python3 analyze-results.py --input /nonexistent.tsv` |
| **预期结果** | 1. 返回非零退出码<br>2. 向 stderr 输出错误信息<br>3. 显示文件未找到信息 |
| **优先级** | 中 |

---

### 2.4 TSV格式验证测试

#### TC-020: 字段数量验证

| 项目 | 内容 |
|------|------|
| **用例ID** | TC-020 |
| **测试目的** | 验证 TSV 文件具有正确的字段数量 |
| **前置条件** | 存在 experiments.tsv 文件 |
| **测试步骤** | 1. 读取表头行<br>2. 分割字段计数 |
| **预期结果** | 1. 表头包含 15 个字段<br>2. 每行数据字段数与表头一致<br>3. 字段顺序符合规范 |
| **优先级** | 高 |

#### TC-021: 必填字段完整性验证

| 项目 | 内容 |
||------|------|
| **用例ID** | TC-021 |
| **测试目的** | 验证必填字段完整性 |
| **前置条件** | experiments.tsv 包含多条记录 |
| **测试步骤** | 1. 遍历所有记录<br>2. 检查必填字段: timestamp, experiment_id, variant_id, scenario, phase, status, duration_sec, metrics_json, config_hash, git_commit |
| **预期结果** | 1. 所有必填字段都不为空<br>2. status 值在枚举范围内 (completed, timeout, error, skipped)<br>3. duration_sec 为有效数字 |
| **优先级** | 高 |

#### TC-022: Timestamp 格式验证

| 项目 | 内容 |
|------|------|
| **用例ID** | TC-022 |
| **测试目的** | 验证 timestamp 字段符合 ISO8601 格式 |
| **前置条件** | experiments.tsv 包含有效记录 |
| **测试步骤** | 1. 提取所有 timestamp 值<br>2. 使用正则验证格式: `YYYY-MM-DDTHH:MM:SSZ` |
| **预期结果** | 1. 所有 timestamp 匹配 ISO8601 UTC 格式<br>2. 使用 Z 后缀表示 UTC<br>3. 日期和时间部分有效 |
| **优先级** | 中 |

#### TC-023: Experiment ID 格式验证

| 项目 | 内容 |
|------|------|
| **用例ID** | TC-023 |
| **测试目的** | 验证 experiment_id 格式规范 |
| **前置条件** | experiments.tsv 包含多条记录 |
| **测试步骤** | 1. 提取所有 experiment_id<br>2. 验证格式: `exp_` + 4位数字 |
| **预期结果** | 1. 所有 ID 匹配模式 `exp_[0-9]{4}`<br>2. 数字部分按递增顺序<br>3. 无前导零丢失 |
| **优先级** | 中 |

#### TC-024: Metrics JSON 有效性验证

| 项目 | 内容 |
|------|------|
| **用例ID** | TC-024 |
| **测试目的** | 验证 metrics_json 字段为有效 JSON |
| **前置条件** | experiments.tsv 包含记录 |
| **测试步骤** | 1. 提取 metrics_json 字段<br>2. 使用 jq 或 Python json 模块解析 |
| **预期结果** | 1. 所有 metrics_json 可被正确解析<br>2. 包含必需字段: scenario, primary_metric, values<br>3. values 对象包含数值指标 |
| **优先级** | 高 |

#### TC-025: Git Commit 格式验证

| 项目 | 内容 |
|------|------|
| **用例ID** | TC-025 |
| **测试目的** | 验证 git_commit 字段格式 |
| **前置条件** | experiments.tsv 包含记录 |
| **测试步骤** | 1. 提取 git_commit 字段<br>2. 验证为有效的 Git SHA |
| **预期结果** | 1. 为 40 位十六进制字符串，或 "unknown"<br>2. 或 7-8 位短 SHA |
| **优先级** | 低 |

---

### 2.5 评估指标计算测试

#### TC-026: 网页抓取指标计算验证

| 项目 | 内容 |
|------|------|
| **用例ID** | TC-026 |
| **测试目的** | 验证网页抓取场景指标计算准确 |
| **前置条件** | 准备已知输入数据 |
| **测试步骤** | 1. 输入数据: 100次请求, 95成功, 90解析成功, 850/1000字段提取正确<br>2. 调用计算函数<br>3. 验证输出 |
| **预期结果** | 1. success_rate = 0.95<br>2. completeness = 0.85<br>3. accuracy = 0.947 (90/95)<br>4. 综合得分 = 0.916 (按权重计算) |
| **优先级** | 高 |

#### TC-027: 长任务指标计算验证

| 项目 | 内容 |
|------|------|
| **用例ID** | TC-027 |
| **测试目的** | 验证长任务场景指标计算准确 |
| **前置条件** | 准备已知输入数据 |
| **测试步骤** | 1. 输入: 100任务, 92完成, 950/1000步骤成功, 总时间 45000s<br>2. 调用计算函数 |
| **预期结果** | 1. completion_rate = 0.92<br>2. step_success_rate = 0.95<br>3. avg_step_time = 45s<br>4. 综合得分按公式正确计算 |
| **优先级** | 高 |

#### TC-028: Skill vs 注意力指标计算验证

| 项目 | 内容 |
|------|------|
| **用例ID** | TC-028 |
| **测试目的** | 验证 Skill vs 注意力场景指标计算准确 |
| **前置条件** | 准备已知输入数据 |
| **测试步骤** | 1. 输入: 应触发100次, 正确触发88次, 总触发95次, 质量分总和 210, 响应数 50<br>2. 调用计算函数 |
| **预期结果** | 1. trigger_accuracy = 0.88<br>2. response_quality = 4.2 (210/50)<br>3. false_positive_rate = 0.074 ((95-88)/95)<br>4. 综合得分按权重正确计算 |
| **优先级** | 高 |

#### TC-029: 除零边界情况处理

| 项目 | 内容 |
|------|------|
| **用例ID** | TC-029 |
| **测试目的** | 验证指标计算对除零情况的处理 |
| **前置条件** | 准备边界输入数据 |
| **测试步骤** | 1. 输入: total_requests = 0<br>2. 输入: successful = 0<br>3. 观察计算结果 |
| **预期结果** | 1. 不抛出异常<br>2. 返回 0 或合理默认值<br>3. 程序不崩溃 |
| **优先级** | 高 |

#### TC-030: 综合得分边界值验证

| 项目 | 内容 |
|------|------|
| **用例ID** | TC-030 |
| **测试目的** | 验证综合得分在边界情况下的计算 |
| **前置条件** | 准备极值输入 |
| **测试步骤** | 1. 所有指标为 1.0 (完美)<br>2. 所有指标为 0.0 (完全失败)<br>3. 验证得分 |
| **预期结果** | 1. 完美情况得分接近 1.0<br>2. 完全失败情况得分接近 0.0<br>3. 得分始终在 [0, 1] 范围内 |
| **优先级** | 中 |

---

### 2.6 集成测试

#### TC-031: 端到端实验流程验证

| 项目 | 内容 |
|------|------|
| **用例ID** | TC-031 |
| **测试目的** | 验证完整的实验执行到分析流程 |
| **前置条件** | 1. 所有脚本可用<br>2. 测试配置存在<br>3. 环境干净 |
| **测试步骤** | 1. 执行 run-experiment.sh 运行3个变体<br>2. 验证 experiments.tsv 记录<br>3. 执行 analyze-results.py 生成报告 |
| **预期结果** | 1. 所有步骤无错误<br>2. TSV 包含3条记录<br>3. 报告正确识别3个变体<br>4. 最佳变体被正确选出 |
| **优先级** | 高 |

#### TC-032: 多场景数据共存验证

| 项目 | 内容 |
|------|------|
| **用例ID** | TC-032 |
| **测试目的** | 验证多场景数据可在同一 TSV 中正确管理 |
| **前置条件** | 环境干净 |
| **测试步骤** | 1. 执行 web_scrape 场景实验<br>2. 执行 long_task 场景实验<br>3. 分析时分别筛选 |
| **预期结果** | 1. TSV 包含两种场景的记录<br>2. --scenario 筛选只返回对应场景<br>3. 数据不互相干扰 |
| **优先级** | 中 |

#### TC-033: 重复实验记录验证

| 项目 | 内容 |
|------|------|
| **用例ID** | TC-033 |
| **测试目的** | 验证同一变体多次执行被正确记录和分析 |
| **前置条件** | 环境准备就绪 |
| **测试步骤** | 1. 同一变体执行3次<br>2. 分析结果 |
| **预期结果** | 1. TSV 包含3条独立记录<br>2. 分析报告显示该变体的平均得分<br>3. 运行次数显示为3 |
| **优先级** | 中 |

---

## 三、测试数据设计

### 3.1 测试配置文件

#### configs/test_basic.yaml
```yaml
scenario: web_scrape
target: test
parameters:
  timeout: 10
  retries: 1
test_mode: true
```

#### configs/test_slow.yaml
```yaml
scenario: long_task
target: slow_test
parameters:
  simulate_delay: 10
  steps: 5
test_mode: true
```

#### configs/test_web_scrape.yaml
```yaml
scenario: web_scrape
variables:
  parser: ["beautifulsoup", "lxml"]
  fetcher: ["requests", "httpx"]
  timeout: [10, 30]
test_cases: 100
```

### 3.2 测试用 TSV 数据

#### tests/fixtures/test_experiments.tsv
```tsv
timestamp	experiment_id	variant_id	scenario	phase	status	duration_sec	metrics_json	config_hash	git_commit	agent_id	description	notes	parent_exp_id	iteration
2026-04-14T10:00:00Z	exp_0001	v_baseline	web_scrape	phase3	completed	120.5	{"scenario":"web_scrape","primary_metric":"accuracy","values":{"accuracy":0.85},"metadata":{}}	a1b2c3d4	abc1234	main	Baseline test			1
2026-04-14T10:05:00Z	exp_0002	v_httpx	web_scrape	phase3	completed	98.3	{"scenario":"web_scrape","primary_metric":"accuracy","values":{"accuracy":0.88},"metadata":{}}	b2c3d4e5	abc1234	main	Httpx variant			1
2026-04-14T10:10:00Z	exp_0003	v_slow	web_scrape	phase3	timeout	300.0	{"scenario":"web_scrape","primary_metric":"duration","values":{"duration_sec":300},"metadata":{}}	c3d4e5f6	abc1234	main	Slow config			1
2026-04-14T10:15:00Z	exp_0004	v_error	web_scrape	phase3	error	5.2	{"scenario":"web_scrape","primary_metric":"error","values":{"error":1},"metadata":{}}	d4e5f6g7	abc1234	main	Error test			1
2026-04-14T10:20:00Z	exp_0005	v_baseline	long_task	phase4	completed	200.0	{"scenario":"long_task","primary_metric":"completion_rate","values":{"completion_rate":0.92},"metadata":{}}	e5f6g7h8	abc1234	main	Long task test			1
```

### 3.3 Mock 实验运行器

#### tests/mocks/mock_runner.sh
```bash
#!/bin/bash
# Mock experiment runner for testing
CONFIG_FILE="$1"
VARIANT_ID="$2"

# Simulate different behaviors based on variant
if [[ "$VARIANT_ID" == *"slow"* ]]; then
    sleep 10
elif [[ "$VARIANT_ID" == *"error"* ]]; then
    exit 1
fi

# Output metrics JSON
cat << EOF
{
  "scenario": "web_scrape",
  "primary_metric": "accuracy",
  "values": {
    "success_rate": 0.95,
    "accuracy": 0.88,
    "completeness": 0.92,
    "execution_time_sec": 125.5
  },
  "metadata": {
    "variant": "$VARIANT_ID",
    "test_cases": 100,
    "passed": 95
  }
}
EOF
exit 0
```

### 3.4 边界测试数据

| 测试场景 | 输入数据 | 预期行为 |
|----------|----------|----------|
| 零请求 | total_requests = 0 | 返回 0，不崩溃 |
| 全失败 | success = 0, total = 100 | success_rate = 0 |
| 完美成功 | all metrics = 1.0 | score = 1.0 |
| 极大数值 | duration = 999999 | 正确处理 |
| 特殊字符 | description 含制表符/换行 | 正确转义或拒绝 |

---

## 四、测试环境要求

### 4.1 硬件要求

| 项目 | 最低要求 | 推荐配置 |
|------|----------|----------|
| CPU | 1 核 | 2 核 |
| 内存 | 512 MB | 1 GB |
| 磁盘 | 1 GB 可用空间 | 5 GB 可用空间 |

### 4.2 软件依赖

| 依赖 | 版本要求 | 用途 |
|------|----------|------|
| Bash | 4.0+ | 执行 Shell 脚本 |
| Python | 3.8+ | 运行分析工具 |
| jq | 1.5+ | JSON 验证和处理 |
| bc | 任意 | 数值计算 |
| git | 2.0+ | 版本追踪 |

### 4.3 Python 依赖包

```txt
# requirements-test.txt
pytest>=7.0.0
pytest-cov>=4.0.0
pandas>=1.5.0
```

### 4.4 目录结构要求

```
/workspace/jerry/design/optimization-framework/
├── phase1-design/
│   ├── framework-design.md
│   ├── experiments-format.md
│   └── evaluation-metrics.md
├── phase2-acceptance/
│   ├── test-cases.md (本文档)
│   ├── test-results.md (测试执行记录)
│   └── acceptance-report.md (验收报告)
├── scripts/
│   ├── run-experiment.sh
│   ├── experiment-runner.sh
│   └── analyze-results.py
├── configs/
│   └ test_basic.yaml
│   └ test_slow.yaml
│   └ test_web_scrape.yaml
├── data/
│   └ experiments.tsv
│   └ experiments/
│       └ YYYY-MM-DD/
│           └ exp_XXXX/
├── tests/
│   ├── fixtures/
│   │   └ test_experiments.tsv
│   ├── mocks/
│   │   └ mock_runner.sh
│   └── test_runner.sh
└── README.md
```

---

## 五、测试执行计划

### 5.1 测试执行顺序

按优先级和依赖关系，建议执行顺序：

| 执行顺序 | 测试组 | 用例数 | 说明 |
|----------|--------|--------|------|
| 1 | 基本功能验证 | TC-001~003 | 高优先级，验证核心功能 |
| 2 | 参数和格式验证 | TC-004~008 | 验证数据格式正确性 |
| 3 | 实验运行器测试 | TC-009~011 | 验证执行流程 |
| 4 | 分析工具测试 | TC-012~019 | 验证分析功能 |
| 5 | TSV格式验证 | TC-020~025 | 验证数据记录规范 |
| 6 | 指标计算测试 | TC-026~030 | 验证评估准确性 |
| 7 | 集成测试 | TC-031~033 | 端到端验证 |

### 5.2 测试执行脚本

创建 `tests/test_runner.sh` 统一执行所有测试：

```bash
#!/bin/bash
# 框架验收测试执行脚本

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
FRAMEWORK_DIR="$(dirname "$SCRIPT_DIR")"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 测试结果统计
TOTAL=0
PASSED=0
FAILED=0
SKIPPED=0

# 执行单个测试
run_test() {
    local test_id="$1"
    local test_name="$2"
    local test_func="$3"
    
    TOTAL=$((TOTAL + 1))
    echo -e "\n${YELLOW}执行测试: $test_id - $test_name${NC}"
    
    if $test_func; then
        PASSED=$((PASSED + 1))
        echo -e "${GREEN}✓ 通过${NC}"
    else
        FAILED=$((FAILED + 1))
        echo -e "${RED}✗ 失败${NC}"
    fi
}

# 打印测试报告
print_report() {
    echo -e "\n================================"
    echo -e "测试执行报告"
    echo -e "================================"
    echo -e "总计: $TOTAL"
    echo -e "${GREEN}通过: $PASSED${NC}"
    echo -e "${RED}失败: $FAILED${NC}"
    echo -e "${YELLOW}跳过: $SKIPPED${NC}"
    
    if [ $FAILED -eq 0 ]; then
        echo -e "\n${GREEN}所有测试通过！框架验收成功。${NC}"
        exit 0
    else
        echo -e "\n${RED}有测试失败，需要修复问题后重新验收。${NC}"
        exit 1
    fi
}

# 执行所有测试
echo "开始框架验收测试..."

# 这里添加具体测试函数调用
# run_test "TC-001" "基本参数解析验证" test_tc001
# ...

print_report
```

### 5.3 预期测试结果

| 测试组 | 预期结果 | 通过标准 |
|--------|----------|----------|
| 功能测试 | 全部通过 | 100% |
| 格式验证 | 全部通过 | 100% |
| 指标计算 | 计算准确 |误差 < 0.01 |
| 集成测试 | 流程完整 | 全部通过 |

---

## 六、验收标准汇总

### 6.1 必须通过的测试

以下测试必须全部通过才能验收：

- TC-001: 基本参数解析验证
- TC-005: 超时机制验证
- TC-007: TSV记录格式验证
- TC-012: 基本数据加载验证
- TC-014: 统计计算准确性验证
- TC-024: Metrics JSON 有效性验证
- TC-026: 网页抓取指标计算验证
- TC-031: 端到端实验流程验证

### 6.2 验收通过条件

| 条件 | 标准 |
|------|------|
| 总体通过率 | ≥ 90% |
| 高优先级测试 | 100% 通过 |
| 中优先级测试 | ≥ 80% 通过 |
| 低优先级测试 | ≥ 60% 通过 |
| 关键路径测试 | 全部通过 |

### 6.3 验收失败处理

如验收失败：
1. 记录失败测试及原因
2. 定位问题模块
3. 返回 Phase 1 修复
4. 重新执行验收测试
5. 直到通过为止

---

## 七、附录

### 7.1 测试用例快速参考

| 用例ID | 测试名称 | 模块 | 优先级 |
|--------|----------|------|--------|
| TC-001 | 基本参数解析验证 | run-experiment.sh | 高 |
| TC-002 | 缺少必需参数处理 | run-experiment.sh | 高 |
| TC-003 | 无效配置文件处理 | run-experiment.sh | 高 |
| TC-004 | 实验ID递增验证 | run-experiment.sh | 中 |
| TC-005 | 超时机制验证 | run-experiment.sh | 高 |
| TC-006 | Dry-run 模式验证 | run-experiment.sh | 中 |
| TC-007 | TSV记录格式验证 | run-experiment.sh | 高 |
| TC-008 | 输出目录结构验证 | run-experiment.sh | 中 |
| TC-009 | 基本执行验证 | experiment-runner.sh | 高 |
| TC-010 | 无效配置处理 | experiment-runner.sh | 中 |
| TC-011 | JSON输出格式验证 | experiment-runner.sh | 高 |
| TC-012 | 基本数据加载验证 | analyze-results.py | 高 |
| TC-013 | 场景筛选验证 | analyze-results.py | 高 |
| TC-014 | 统计计算准确性验证 | analyze-results.py | 高 |
| TC-015 | 变体对比排序验证 | analyze-results.py | 中 |
| TC-016 | 报告输出到文件验证 | analyze-results.py | 中 |
| TC-017 | JSON格式报告验证 | analyze-results.py | 低 |
| TC-018 | 空数据处理 | analyze-results.py | 中 |
| TC-019 | 不存在文件处理 | analyze-results.py | 中 |
| TC-020 | 字段数量验证 | TSV格式 | 高 |
| TC-021 | 必填字段完整性验证 | TSV格式 | 高 |
| TC-022 | Timestamp格式验证 | TSV格式 | 中 |
| TC-023 | Experiment ID格式验证 | TSV格式 | 中 |
| TC-024 | Metrics JSON有效性验证 | TSV格式 | 高 |
| TC-025 | Git Commit格式验证 | TSV格式 | 低 |
| TC-026 | 网页抓取指标计算验证 | 评估指标 | 高 |
| TC-027 | 长任务指标计算验证 | 评估指标 | 高 |
| TC-028 | Skill注意力指标计算验证 | 评估指标 | 高 |
| TC-029 | 除零边界情况处理 | 评估指标 | 高 |
| TC-030 | 综合得分边界值验证 | 评估指标 | 中 |
| TC-031 | 端到端实验流程验证 | 集成测试 | 高 |
| TC-032 | 多场景数据共存验证 | 集成测试 | 中 |
| TC-033 | 重复实验记录验证 | 集成测试 | 中 |

**统计**：33 个测试用例
- 高优先级：17 个
- 中优先级：13 个
- 低优先级：3 个

---

*文档完成日期: 2026-04-15*
*版本: v1.0*
├── scripts/
│   ├── run-experiment.sh
│   ├── experiment-runner.sh
│   └── analyze-results.py
├── tests/
│   ├── fixtures/
│   │   └── test_experiments.tsv
│   ├── mocks/
│   │   └── mock_runner.sh
│   └── configs/
│       ├── test_basic.yaml
│       ├── test_slow.yaml
│       └── test_web_scrape.yaml
├── data/
│   └── experiments.tsv (测试时创建)
└── README.md
```

### 4.5 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `AGENT_ID` | 执行 Agent 标识 | "test" |
| `PROJECT_DIR` | 项目根目录 | 脚本所在目录的父目录 |
| `DATA_DIR` | 数据目录 | `$PROJECT_DIR/data` |

---

## 五、测试执行计划

### 5.1 测试阶段

| 阶段 | 测试用例 | 目标 |
|------|----------|------|
| **阶段1: 单元测试** | TC-001 ~ TC-019 | 各模块独立功能 |
| **阶段2: 格式验证** | TC-020 ~ TC-025 | TSV格式合规性 |
| **阶段3: 指标计算** | TC-026 ~ TC-030 | 评估准确性 |
| **阶段4: 集成测试** | TC-031 ~ TC-033 | 端到端流程 |

### 5.2 优先级执行顺序

高优先级: TC-001, TC-002, TC-003, TC-005, TC-007, TC-009, TC-012, TC-013, TC-014, TC-020, TC-021, TC-024, TC-026, TC-027, TC-028, TC-029, TC-031

中优先级: TC-004, TC-006, TC-008, TC-010, TC-015, TC-016, TC-018, TC-019, TC-022, TC-023, TC-030, TC-032, TC-033

低优先级: TC-011, TC-017, TC-025

### 5.3 自动化测试脚本

建议创建自动化测试脚本 `tests/run_all_tests.sh`：

```bash
#!/bin/bash
# OpenClaw 框架自动化测试脚本

set -e

echo "=== OpenClaw 框架测试套件 ==="
echo ""

# 准备测试环境
./tests/setup_test_env.sh

# 执行高优先级测试
echo "[1/4] 执行高优先级测试..."
./tests/test_high_priority.sh

# 执行中优先级测试
echo "[2/4] 执行中优先级测试..."
./tests/test_medium_priority.sh

# 执行格式验证测试
echo "[3/4] 执行格式验证测试..."
./tests/test_format_validation.sh

# 执行集成测试
echo "[4/4] 执行集成测试..."
./tests/test_integration.sh

echo ""
echo "=== 测试完成 ==="
```

---

## 六、验收标准检查清单

### 6.1 功能覆盖检查

- [ ] 测试用例覆盖所有核心功能模块
- [ ] 每个模块至少有3个测试用例
- [ ] 边界情况有专门测试用例
- [ ] 异常处理路径被覆盖

### 6.2 文档质量检查

- [ ] 每个测试用例有明确的用例ID
- [ ] 测试目的描述清晰
- [ ] 前置条件具体可操作
- [ ] 测试步骤详细完整
- [ ] 预期结果可验证
- [ ] 优先级划分合理

### 6.3 测试数据检查

- [ ] 测试配置文件设计完整
- [ ] TSV测试数据符合格式规范
- [ ] Mock运行器可正常工作
- [ ] 边界测试数据覆盖关键场景

### 6.4 环境要求检查

- [ ] 硬件要求明确
- [ ] 软件依赖完整
- [ ] Python依赖版本明确
- [ ] 目录结构定义清晰

---

## 七、附录

### 7.1 测试用例汇总表

| 用例ID | 模块 | 测试目的 | 优先级 |
|--------|------|----------|--------|
| TC-001 | run-experiment.sh | 参数解析 | 高 |
| TC-002 | run-experiment.sh | 缺少参数处理 | 高 |
| TC-003 | run-experiment.sh | 无效配置处理 | 高 |
| TC-004 | run-experiment.sh | 实验ID递增 | 中 |
| TC-005 | run-experiment.sh | 超时机制 | 高 |
| TC-006 | run-experiment.sh | Dry-run模式 | 中 |
| TC-007 | run-experiment.sh | TSV记录格式 | 高 |
| TC-008 | run-experiment.sh | 输出目录结构 | 中 |
| TC-009 | experiment-runner.sh | 基本执行 | 高 |
| TC-010 | experiment-runner.sh | 无效配置处理 | 中 |
| TC-011 | experiment-runner.sh | JSON输出格式 | 高 |
| TC-012 | analyze-results.py | 数据加载 | 高 |
| TC-013 | analyze-results.py | 场景筛选 | 高 |
| TC-014 | analyze-results.py | 统计计算 | 高 |
| TC-015 | analyze-results.py | 变体排序 | 中 |
| TC-016 | analyze-results.py | 文件输出 | 中 |
| TC-017 | analyze-results.py | JSON报告 | 低 |
| TC-018 | analyze-results.py | 空数据处理 | 中 |
| TC-019 | analyze-results.py | 文件不存在处理 | 中 |
| TC-020 | TSV格式 | 字段数量 | 高 |
| TC-021 | TSV格式 | 必填字段 | 高 |
| TC-022 | TSV格式 | Timestamp格式 | 中 |
| TC-023 | TSV格式 | Experiment ID格式 | 中 |
| TC-024 | TSV格式 | Metrics JSON有效 | 高 |
| TC-025 | TSV格式 | Git Commit格式 | 低 |
| TC-026 | 指标计算 | 网页抓取场景 | 高 |
| TC-027 | 指标计算 | 长任务场景 | 高 |
| TC-028 | 指标计算 | Skill vs注意力场景 | 高 |
| TC-029 | 指标计算 | 除零边界 | 高 |
| TC-030 | 指标计算 | 边界值 | 中 |
| TC-031 | 集成测试 | 端到端流程 | 高 |
| TC-032 | 集成测试 | 多场景共存 | 中 |
| TC-033 | 集成测试 | 重复实验记录 | 中 |

### 7.2 优先级统计

| 优先级 | 数量 | 占比 |
|--------|------|------|
| 高 | 19 | 57.6% |
| 中 | 12 | 36.4% |
| 低 | 2 | 6.0% |
| **总计** | **33** | **100%** |

### 7.3 模块覆盖统计

| 模块 | 测试用例数 | 覆盖率 |
|------|------------|--------|
| run-experiment.sh | 8 | 24.2% |
| experiment-runner.sh | 3 | 9.1% |
| analyze-results.py | 8 | 24.2% |
| TSV格式验证 | 6 | 18.2% |
| 评估指标计算 | 5 | 15.2% |
| 集成测试 | 3 | 9.1% |

### 7.4 修订历史

| 版本 | 日期 | 修改内容 | 作者 |
|------|------|----------|------|
| v1.0 | 2026-04-15 | 初始版本，完成33个测试用例设计 | Agent |

---

*本文档是 OpenClaw 优化测试框架 Phase 2 的输出成果，用于指导框架的验收测试工作。*
