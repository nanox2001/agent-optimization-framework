#!/bin/bash
#
# OpenClaw 优化测试框架 - 实验执行脚本
# Phase 1.4 输出
#
# 用法: ./run-experiment.sh --config <config.yaml> --variant <variant_id> [选项]
#

set -euo pipefail

# 默认配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
DATA_DIR="${PROJECT_DIR}/data"
EXPERIMENTS_FILE="${DATA_DIR}/experiments.tsv"
TIMEOUT=300
VERBOSE=0

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 打印帮助信息
usage() {
    cat << EOF
OpenClaw 实验执行脚本

用法:
    $0 --config <config.yaml> --variant <variant_id> [选项]

必需参数:
    --config <file>      实验配置文件路径
    --variant <id>       变体标识符

可选参数:
    --scenario <name>    场景名称 (默认: 从配置读取)
    --phase <n>          Phase 编号 (默认: phase3)
    --timeout <sec>      超时时间，秒 (默认: 300)
    --description <text> 实验描述
    --output-dir <dir>   输出目录 (默认: data/experiments/YYYYMMDD/)
    --dry-run            模拟运行，不记录结果
    -v, --verbose        详细输出
    -h, --help           显示帮助

示例:
    $0 --config configs/web_scrape.yaml --variant v_baseline
    $0 --config configs/long_task.yaml --variant v_retry --timeout 600 --description "With retry logic"

EOF
}

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 解析参数
CONFIG_FILE=""
VARIANT_ID=""
SCENARIO=""
PHASE="phase3"
DESCRIPTION=""
OUTPUT_DIR=""
DRY_RUN=0

while [[ $# -gt 0 ]]; do
    case $1 in
        --config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        --variant)
            VARIANT_ID="$2"
            shift 2
            ;;
        --scenario)
            SCENARIO="$2"
            shift 2
            ;;
        --phase)
            PHASE="$2"
            shift 2
            ;;
        --timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        --description)
            DESCRIPTION="$2"
            shift 2
            ;;
        --output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=1
            shift
            ;;
        -v|--verbose)
            VERBOSE=1
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            log_error "未知参数: $1"
            usage
            exit 1
            ;;
    esac
done

# 验证必需参数
if [[ -z "$CONFIG_FILE" ]]; then
    log_error "缺少必需参数: --config"
    usage
    exit 1
fi

if [[ -z "$VARIANT_ID" ]]; then
    log_error "缺少必需参数: --variant"
    usage
    exit 1
fi

if [[ ! -f "$CONFIG_FILE" ]]; then
    log_error "配置文件不存在: $CONFIG_FILE"
    exit 1
fi

# 确保数据目录存在
mkdir -p "$DATA_DIR"

# 生成实验 ID
if [[ -f "$EXPERIMENTS_FILE" ]]; then
    LAST_ID=$(tail -1 "$EXPERIMENTS_FILE" | cut -f2)
    if [[ "$LAST_ID" =~ ^exp_([0-9]+)$ ]]; then
        LAST_NUM="${BASH_REMATCH[1]}"
        NEXT_NUM=$((10#$LAST_NUM + 1))
    else
        NEXT_NUM=1
    fi
else
    NEXT_NUM=1
fi
EXPERIMENT_ID=$(printf "exp_%04d" "$NEXT_NUM")

# 获取当前时间戳
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# 获取 Git commit
GIT_COMMIT=$(git -C "$PROJECT_DIR" rev-parse HEAD 2>/dev/null || echo "unknown")

# 计算配置文件的 hash
CONFIG_HASH=$(sha256sum "$CONFIG_FILE" | cut -c1-8)

# 确定场景
if [[ -z "$SCENARIO" ]]; then
    # 尝试从配置文件读取
    SCENARIO=$(grep -E "^scenario:" "$CONFIG_FILE" | cut -d: -f2 | tr -d ' ' || echo "unknown")
fi

# 设置输出目录
if [[ -z "$OUTPUT_DIR" ]]; then
    OUTPUT_DIR="${DATA_DIR}/experiments/$(date +%Y-%m-%d)/${EXPERIMENT_ID}"
fi
mkdir -p "$OUTPUT_DIR"

log_info "开始实验: $EXPERIMENT_ID"
log_info "变体: $VARIANT_ID"
log_info "场景: $SCENARIO"
log_info "配置: $CONFIG_FILE"
log_info "输出: $OUTPUT_DIR"

# 保存配置副本
cp "$CONFIG_FILE" "${OUTPUT_DIR}/config.yaml"

# 执行实验（带超时）
START_TIME=$(date +%s.%N)

if [[ $VERBOSE -eq 1 ]]; then
    log_info "执行命令 (超时: ${TIMEOUT}s)..."
fi

# 创建临时文件用于捕获输出
STDOUT_FILE="${OUTPUT_DIR}/stdout.log"
STDERR_FILE="${OUTPUT_DIR}/stderr.log"
EXIT_CODE=0

# 执行实验脚本
if [[ $DRY_RUN -eq 0 ]]; then
    # 实际执行
    timeout "$TIMEOUT" bash "${SCRIPT_DIR}/experiment-runner.sh" \
        "$CONFIG_FILE" \
        "$VARIANT_ID" \
        > "$STDOUT_FILE" \
        2> "$STDERR_FILE" \
        || EXIT_CODE=$?
else
    # 模拟运行
    log_info "[DRY RUN] 模拟执行..."
    echo "Simulated output for $VARIANT_ID" > "$STDOUT_FILE"
    echo "Simulated metrics" > "$STDERR_FILE"
    EXIT_CODE=0
fi

END_TIME=$(date +%s.%N)
DURATION=$(echo "$END_TIME - $START_TIME" | bc 2>/dev/null || echo "0")

# 确定状态
if [[ $EXIT_CODE -eq 0 ]]; then
    STATUS="completed"
    log_info "实验完成 ✓"
elif [[ $EXIT_CODE -eq 124 ]]; then
    STATUS="timeout"
    log_warn "实验超时 ⚠"
else
    STATUS="error"
    log_error "实验失败 ✗ (exit code: $EXIT_CODE)"
fi

# 解析指标（从输出中提取 JSON）
METRICS_JSON="{}"
if [[ -f "$STDOUT_FILE" ]]; then
    # 尝试从 stdout 最后一行解析 JSON
    LAST_LINE=$(tail -1 "$STDOUT_FILE")
    if echo "$LAST_LINE" | jq empty 2>/dev/null; then
        METRICS_JSON="$LAST_LINE"
    fi
fi

# 如果 metrics 为空，构建基础 metrics
if [[ "$METRICS_JSON" == "{}" ]]; then
    METRICS_JSON=$(jq -n \
        --arg scenario "$SCENARIO" \
        --argjson duration "$DURATION" \
        '{
            scenario: $scenario,
            primary_metric: "duration",
            values: {
                duration_sec: $duration
            },
            metadata: {}
        }')
fi

# 压缩 JSON（单行）
METRICS_COMPRESSED=$(echo "$METRICS_JSON" | jq -c .)

# 构建 TSV 记录
AGENT_ID="${AGENT_ID:-main}"
PARENT_EXP_ID="${PARENT_EXP_ID:-}"
ITERATION="${ITERATION:-1}"
NOTES=""

TSV_LINE="${TIMESTAMP}\t${EXPERIMENT_ID}\t${VARIANT_ID}\t${SCENARIO}\t${PHASE}\t${STATUS}\t${DURATION}\t${METRICS_COMPRESSED}\t${CONFIG_HASH}\t${GIT_COMMIT}\t${AGENT_ID}\t${DESCRIPTION}\t${NOTES}\t${PARENT_EXP_ID}\t${ITERATION}"

# 写入 experiments.tsv
if [[ $DRY_RUN -eq 0 ]]; then
    # 创建文件头（如果不存在）
    if [[ ! -f "$EXPERIMENTS_FILE" ]]; then
        echo -e "timestamp\texperiment_id\tvariant_id\tscenario\tphase\tstatus\tduration_sec\tmetrics_json\tconfig_hash\tgit_commit\tagent_id\tdescription\tnotes\tparent_exp_id\titeration" > "$EXPERIMENTS_FILE"
    fi
    
    # 追加记录
    echo -e "$TSV_LINE" >> "$EXPERIMENTS_FILE"
    log_info "记录已保存: $EXPERIMENTS_FILE"
fi

# 生成摘要报告
cat > "${OUTPUT_DIR}/summary.json" << EOF
{
    "experiment_id": "$EXPERIMENT_ID",
    "variant_id": "$VARIANT_ID",
    "scenario": "$SCENARIO",
    "phase": "$PHASE",
    "status": "$STATUS",
    "duration_sec": $DURATION,
    "timestamp": "$TIMESTAMP",
    "config_hash": "$CONFIG_HASH",
    "git_commit": "$GIT_COMMIT",
    "exit_code": $EXIT_CODE,
    "output_files": {
        "stdout": "stdout.log",
        "stderr": "stderr.log",
        "config": "config.yaml",
        "summary": "summary.json"
    }
}
EOF

log_info "实验摘要: ${OUTPUT_DIR}/summary.json"

# 输出最终结果
echo ""
echo "========================================"
echo "实验执行结果"
echo "========================================"
echo "ID:        $EXPERIMENT_ID"
echo "Variant:   $VARIANT_ID"
echo "Status:    $STATUS"
echo "Duration:  ${DURATION}s"
echo "Output:    $OUTPUT_DIR"
echo "========================================"

exit 0