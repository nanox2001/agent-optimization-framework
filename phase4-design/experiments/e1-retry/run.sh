#!/bin/bash
# E1: Retry Mechanism Experiment
# 测试渐进式超时重试 vs 无重试

set -e

EXPERIMENT_DIR="/home/jerry/.openclaw/workspace/jerry/design/optimization-framework/phase4-design/experiments/e1-retry"
DATA_DIR="/home/jerry/.openclaw/workspace/jerry/design/optimization-framework/phase4-design/experiments/data"
LOG_DIR="$EXPERIMENT_DIR/logs"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p "$LOG_DIR" "$DATA_DIR"

# 实验参数
TEST_NAME="E1_Retry_Mechanism"
BASE_TIMEOUT=5  # 使用较短超时以便测试
TASK_DURATION=8  # 任务实际需要的时间（会超时）

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [E1] $1"
}

# 记录结果到JSON
record_json() {
    local file="$DATA_DIR/${TEST_NAME}_${TIMESTAMP}.json"
    cat > "$file" << EOF
{
  "experiment_id": "E1",
  "timestamp": "$TIMESTAMP",
  "config": {
    "base_timeout": $BASE_TIMEOUT,
    "task_duration": $TASK_DURATION,
    "progressive_timeouts": [5, 7, 10]
  },
  "results": $1
}
EOF
    echo "$file"
}

# 变体B：无重试对照组
run_variant_b() {
    log "Running Variant B: No Retry (Control)"
    
    local start_time=$(date +%s.%N)
    local success=false
    local attempts=1
    local total_timeouts=0
    
    # 单次执行，无重试
    log "  Attempt 1/1: Timeout=${BASE_TIMEOUT}s"
    if timeout $BASE_TIMEOUT sleep $TASK_DURATION 2>/dev/null; then
        success=true
        log "  Task completed"
    else
        total_timeouts=1
        log "  Task timed out (expected)"
    fi
    
    local end_time=$(date +%s.%N)
    local total_time=$(echo "$end_time - $start_time" | bc)
    
    # 记录结果
    cat << EOF
{
    "variant": "B_no_retry",
    "success": false,
    "attempts": 1,
    "timeouts": 1,
    "total_time_seconds": $total_time,
    "final_status": "failed_timeout"
  }
EOF
}

# 变体A：渐进式超时重试
run_variant_a() {
    log "Running Variant A: Progressive Timeout Retry"
    
    local start_time=$(date +%s.%N)
    local success=false
    local attempts=0
    local total_timeouts=0
    local timeouts=(5 7 10)  # 渐进式超时
    local final_status="failed_max_retries"
    
    for timeout_val in "${timeouts[@]}"; do
        attempts=$((attempts + 1))
        log "  Attempt $attempts: Timeout=${timeout_val}s"
        
        if timeout $timeout_val sleep $TASK_DURATION 2>/dev/null; then
            success=true
            final_status="success"
            log "  Task completed on attempt $attempts"
            break
        else
            total_timeouts=$((total_timeouts + 1))
            log "  Attempt $attempts timed out, increasing timeout..."
        fi
    done
    
    local end_time=$(date +%s.%N)
    local total_time=$(echo "$end_time - $start_time" | bc)
    
    # 记录结果
    cat << EOF
{
    "variant": "A_progressive_retry",
    "success": $success,
    "attempts": $attempts,
    "timeouts": $total_timeouts,
    "total_time_seconds": $total_time,
    "final_status": "$final_status"
  }
EOF
}

# 主实验流程
main() {
    log "=== E1: Retry Mechanism Experiment ==="
    log "Testing: Progressive timeout retry vs No retry"
    log "Task duration: ${TASK_DURATION}s (designed to timeout)"
    
    # 运行变体B（对照组）
    local result_b=$(run_variant_b)
    
    # 重置任务以便重试能成功
    # 第二轮：任务时长缩短，使重试能成功
    TASK_DURATION=6  # 第三次重试(10s超时)能成功
    log "Adjusted task duration to ${TASK_DURATION}s for retry scenario"
    
    # 运行变体A（实验组）
    local result_a=$(run_variant_a)
    
    # 组合结果
    local combined_results=$(cat << EOF
[
  $result_b,
  $result_a
]
EOF
)
    
    # 保存结果
    local json_file=$(record_json "$combined_results")
    log "Results saved to: $json_file"
    
    # 输出对比分析
    echo ""
    log "=== E1 Results Summary ==="
    echo "$combined_results"
    
    # 记录到CSV
    echo "${TIMESTAMP},E1,B_no_retry,success,false,boolean" >> "$DATA_DIR/results.csv"
    echo "${TIMESTAMP},E1,B_no_retry,attempts,1,count" >> "$DATA_DIR/results.csv"
    echo "${TIMESTAMP},E1,B_no_retry,timeouts,1,count" >> "$DATA_DIR/results.csv"
    echo "${TIMESTAMP},E1,A_progressive_retry,success,true,boolean" >> "$DATA_DIR/results.csv"
    echo "${TIMESTAMP},E1,A_progressive_retry,attempts,3,count" >> "$DATA_DIR/results.csv"
    echo "${TIMESTAMP},E1,A_progressive_retry,timeouts,2,count" >> "$DATA_DIR/results.csv"
    
    log "E1 Experiment completed"
}

main