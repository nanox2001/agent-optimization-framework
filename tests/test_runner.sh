#!/bin/bash
# 框架验收测试执行脚本

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
FRAMEWORK_DIR="$(dirname "$SCRIPT_DIR")"
RESULTS_FILE="$FRAMEWORK_DIR/phase2-acceptance/test-results.md"

# 初始化结果文件
init_results() {
    cat > "$RESULTS_FILE" << 'HEADER'
# OpenClaw 优化测试框架 - 测试执行记录

> Phase 2.2 输出文档 - 测试执行记录
> 执行日期: 2026-04-15
> 版本: v1.0

---

## 一、测试执行概览

| 统计项 | 数值 |
|--------|------|
HEADER
}

# 运行测试并记录结果
run_test() {
    local test_id="$1"
    local test_name="$2"
    local test_cmd="$3"
    
    echo "执行测试: $test_id - $test_name"
    
    # 执行测试并捕获输出和退出码
    local output
    local exit_code
    
    output=$(eval "$test_cmd" 2>&1)
    exit_code=$?
    
    # 记录结果
    echo "### $test_id: $test_name" >> "$RESULTS_FILE"
    echo "" >> "$RESULTS_FILE"
    echo "**测试命令**: \`$test_cmd\`" >> "$RESULTS_FILE"
    echo "" >> "$RESULTS_FILE"
    echo "**退出码**: $exit_code" >> "$RESULTS_FILE"
    echo "" >> "$RESULTS_FILE"
    echo "**输出**:" >> "$RESULTS_FILE"
    echo "\`\`\`" >> "$RESULTS_FILE"
    echo "$output" >> "$RESULTS_FILE"
    echo "\`\`\`" >> "$RESULTS_FILE"
    echo "" >> "$RESULTS_FILE"
    
    if [ $exit_code -eq 0 ]; then
        echo "**结果**: ✅ 通过" >> "$RESULTS_FILE"
    else
        echo "**结果**: ❌ 失败" >> "$RESULTS_FILE"
    fi
    echo "" >> "$RESULTS_FILE"
    echo "---" >> "$RESULTS_FILE"
    echo "" >> "$RESULTS_FILE"
    
    return $exit_code
}

# 初始化结果
init_results

# 测试统计
TOTAL=0
PASSED=0
FAILED=0

echo "开始框架验收测试..."

# TC-001: 基本参数解析验证
((TOTAL++))
if run_test "TC-001" "基本参数解析验证" "./scripts/run-experiment.sh --help"; then
    ((PASSED++))
else
    ((FAILED++))
fi

# TC-002: 缺少必需参数处理
((TOTAL++))
if run_test "TC-002" "缺少必需参数处理" "./scripts/run-experiment.sh"; then
    ((FAILED++))  # 应该失败，所以如果成功则是失败的
else
    ((PASSED++))  # 应该失败
fi

# TC-003: 无效配置文件处理
((TOTAL++))
if run_test "TC-003" "无效配置文件处理" "./scripts/run-experiment.sh --config /nonexistent/path.yaml --variant v_test"; then
    ((FAILED++))
else
    ((PASSED++))
fi

# TC-009: 实验运行器基本执行验证
((TOTAL++))
if run_test "TC-009" "实验运行器基本执行验证" "./scripts/experiment-runner.sh ./configs/test_basic.yaml v_test"; then
    ((PASSED++))
else
    ((FAILED++))
fi

# TC-012: 结果分析工具基本数据加载验证
((TOTAL++))
if run_test "TC-012" "结果分析工具基本数据加载" "python3 ./scripts/analyze-results.py --input ./tests/fixtures/test_experiments.tsv"; then
    ((PASSED++))
else
    ((FAILED++))
fi

# TC-013: 场景筛选验证
((TOTAL++))
if run_test "TC-013" "场景筛选验证" "python3 ./scripts/analyze-results.py --input ./tests/fixtures/test_experiments.tsv --scenario web_scrape"; then
    ((PASSED++))
else
    ((FAILED++))
fi

# TC-018: 空数据或无效输入处理
((TOTAL++))
if run_test "TC-018" "空数据处理" "python3 ./scripts/analyze-results.py --input /dev/null"; then
    ((PASSED++))
else
    ((FAILED++))
fi

echo "测试完成: 总计=$TOTAL, 通过=$PASSED, 失败=$FAILED"

# 更新概览统计
sed -i "s/| 统计项 | 数值 |/| 统计项 | 数值 |\n| 总计测试 | $TOTAL |\n| 通过 | $PASSED |\n| 失败 | $FAILED |\n| 通过率 | $((PASSED * 100 / TOTAL))% |/" "$RESULTS_FILE"

exit 0
