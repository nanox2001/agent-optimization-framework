#!/bin/bash
# Phase 4 Experiment Runner
# 执行优化实验，记录真实数据

set -e

EXPERIMENT_DIR="/home/jerry/.openclaw/workspace/jerry/design/optimization-framework/phase4-design/experiments"
DATA_DIR="$EXPERIMENT_DIR/data"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 确保目录存在
mkdir -p "$DATA_DIR"

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# 记录实验结果
record_result() {
    local experiment_id="$1"
    local variant="$2"
    local metric="$3"
    local value="$4"
    local unit="$5"
    
    echo "${TIMESTAMP},${experiment_id},${variant},${metric},${value},${unit}" >> "$DATA_DIR/results.csv"
}

# 初始化结果文件
init_results() {
    if [ ! -f "$DATA_DIR/results.csv" ]; then
        echo "timestamp,experiment_id,variant,metric,value,unit" > "$DATA_DIR/results.csv"
    fi
}

# 执行带超时的命令
run_with_timeout() {
    local timeout_sec="$1"
    local cmd="$2"
    local output_file="$3"
    
    timeout "$timeout_sec" bash -c "$cmd" > "$output_file" 2>&1
    return $?
}

# 主入口
case "${1:-all}" in
    "e1")
        log "Running E1: Retry Mechanism Experiment"
        bash "$EXPERIMENT_DIR/e1-retry/run.sh"
        ;;
    "e2")
        log "Running E2: Checkpoint Experiment"
        bash "$EXPERIMENT_DIR/e2-checkpoint/run.sh"
        ;;
    "all")
        log "Running all experiments"
        init_results
        bash "$EXPERIMENT_DIR/e1-retry/run.sh"
        bash "$EXPERIMENT_DIR/e2-checkpoint/run.sh"
        log "All experiments completed"
        ;;
    *)
        echo "Usage: $0 [e1|e2|all]"
        exit 1
        ;;
esac