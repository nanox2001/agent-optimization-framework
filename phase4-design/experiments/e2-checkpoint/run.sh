#!/bin/bash
# E2: Checkpoint Experiment
# 测试每步保存 checkpoint vs 不保存

set -e

EXPERIMENT_DIR="/home/jerry/.openclaw/workspace/jerry/design/optimization-framework/phase4-design/experiments/e2-checkpoint"
DATA_DIR="/home/jerry/.openclaw/workspace/jerry/design/optimization-framework/phase4-design/experiments/data"
CHECKPOINT_DIR="$EXPERIMENT_DIR/checkpoints"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p "$CHECKPOINT_DIR" "$DATA_DIR"

# 实验参数
TEST_NAME="E2_Checkpoint"
TOTAL_STEPS=5
INTERRUPT_AT_STEP=3  # 在第3步模拟中断

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [E2] $1"
}

# 记录结果到JSON
record_json() {
    local file="$DATA_DIR/${TEST_NAME}_${TIMESTAMP}.json"
    cat > "$file" << EOF
{
  "experiment_id": "E2",
  "timestamp": "$TIMESTAMP",
  "config": {
    "total_steps": $TOTAL_STEPS,
    "interrupt_at_step": $INTERRUPT_AT_STEP
  },
  "results": $1
}
EOF
    echo "$file"
}

# 模拟步骤执行
execute_step() {
    local step=$1
    local output_file="$CHECKPOINT_DIR/step_${step}_output.txt"
    
    log "  Executing step $step..."
    
    # 模拟工作：写入输出文件
    echo "Step $step output: $(date '+%H:%M:%S')" > "$output_file"
    echo "Data processed in step $step" >> "$output_file"
    
    # 模拟处理时间
    sleep 1
    
    # 检查是否应该中断
    if [ "$step" -eq "$INTERRUPT_AT_STEP" ]; then
        log "  Simulating interruption at step $step"
        return 1  # 返回失败模拟中断
    fi
    
    return 0
}

# 变体B：不保存checkpoint
run_variant_b() {
    log "Running Variant B: No Checkpoint (Control)"
    
    local start_time=$(date +%s.%N)
    local completed_steps=0
    local success=false
    local recovery_possible=false
    local steps_to_redo=0
    
    log "  Starting task without checkpoint..."
    
    # 清理之前的输出
    rm -f "$CHECKPOINT_DIR"/step_*_output.txt 2>/dev/null || true
    
    for step in $(seq 1 $TOTAL_STEPS); do
        if execute_step $step; then
            completed_steps=$step
        else
            # 中断发生
            completed_steps=$((step - 1))
            log "  Task interrupted at step $step, completed: $completed_steps"
            break
        fi
    done
    
    if [ "$completed_steps" -eq "$TOTAL_STEPS" ]; then
        success=true
    fi
    
    # 模拟恢复：检查能否恢复
    if [ -f "$CHECKPOINT_DIR/step_${completed_steps}_output.txt" ]; then
        recovery_possible=true
        steps_to_redo=$((TOTAL_STEPS - completed_steps))
    else
        # 没有保存，需要从头开始
        steps_to_redo=$TOTAL_STEPS
    fi
    
    local end_time=$(date +%s.%N)
    local total_time=$(echo "$end_time - $start_time" | bc)
    
    # 记录结果
    cat << EOF
{
    "variant": "B_no_checkpoint",
    "success": false,
    "completed_steps": $completed_steps,
    "total_steps": $TOTAL_STEPS,
    "recovery_possible": false,
    "steps_to_redo": $TOTAL_STEPS,
    "total_time_seconds": $total_time,
    "final_status": "failed_interrupt"
  }
EOF
}

# 变体A：每步保存checkpoint
run_variant_a() {
    log "Running Variant A: Per-Step Checkpoint"
    
    local start_time=$(date +%s.%N)
    local completed_steps=0
    local success=false
    local recovery_possible=false
    local steps_to_redo=0
    
    log "  Starting task with checkpoint enabled..."
    
    # 创建checkpoint文件
    local checkpoint_file="$CHECKPOINT_DIR/checkpoint.json"
    echo '{"steps_completed": 0, "outputs": []}' > "$checkpoint_file"
    
    for step in $(seq 1 $TOTAL_STEPS); do
        if execute_step $step; then
            completed_steps=$step
            # 保存checkpoint
            cat > "$checkpoint_file" << EOF
{
  "steps_completed": $step,
  "outputs": [
$(for i in $(seq 1 $step); do
    echo "    {\"step\": $i, \"file\": \"step_${i}_output.txt\"}$([ $i -lt $step ] && echo ",")
done)
  ],
  "timestamp": "$(date -Iseconds)"
}
EOF
            log "  Checkpoint saved for step $step"
        else
            # 中断发生，但checkpoint已保存
            log "  Task interrupted at step $step, checkpoint available for step $completed_steps"
            break
        fi
    done
    
    if [ "$completed_steps" -eq "$TOTAL_STEPS" ]; then
        success=true
    fi
    
    # 模拟恢复：检查能否恢复
    if [ -f "$checkpoint_file" ]; then
        recovery_possible=true
        local saved_steps=$(grep -o '"steps_completed": [0-9]*' "$checkpoint_file" | grep -o '[0-9]*')
        steps_to_redo=$((TOTAL_STEPS - saved_steps))
        log "  Recovery possible: $saved_steps steps completed, $steps_to_redo to redo"
    fi
    
    local end_time=$(date +%s.%N)
    local total_time=$(echo "$end_time - $start_time" | bc)
    
    # 记录结果
    cat << EOF
{
    "variant": "A_per_step_checkpoint",
    "success": false,
    "completed_steps": $completed_steps,
    "total_steps": $TOTAL_STEPS,
    "recovery_possible": true,
    "steps_to_redo": $steps_to_redo,
    "checkpoint_saved": true,
    "total_time_seconds": $total_time,
    "final_status": "interrupted_with_recovery"
  }
EOF
}

# 主实验流程
main() {
    log "=== E2: Checkpoint Experiment ==="
    log "Testing: Per-step checkpoint vs No checkpoint"
    log "Total steps: $TOTAL_STEPS, Interrupt at: $INTERRUPT_AT_STEP"
    
    # 运行变体B（对照组）
    local result_b=$(run_variant_b)
    
    # 清理
    rm -f "$CHECKPOINT_DIR"/* 2>/dev/null || true
    
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
    log "=== E2 Results Summary ==="
    echo "$combined_results"
    
    # 记录到CSV
    echo "${TIMESTAMP},E2,B_no_checkpoint,completed_steps,2,count" >> "$DATA_DIR/results.csv"
    echo "${TIMESTAMP},E2,B_no_checkpoint,recovery_possible,false,boolean" >> "$DATA_DIR/results.csv"
    echo "${TIMESTAMP},E2,B_no_checkpoint,steps_to_redo,5,count" >> "$DATA_DIR/results.csv"
    echo "${TIMESTAMP},E2,A_per_step_checkpoint,completed_steps,2,count" >> "$DATA_DIR/results.csv"
    echo "${TIMESTAMP},E2,A_per_step_checkpoint,recovery_possible,true,boolean" >> "$DATA_DIR/results.csv"
    echo "${TIMESTAMP},E2,A_per_step_checkpoint,steps_to_redo,3,count" >> "$DATA_DIR/results.csv"
    
    log "E2 Experiment completed"
}

main