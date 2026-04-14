#!/usr/bin/env python3
"""
OpenClaw 优化测试框架 - 结果分析工具
Phase 1.5 输出

用法:
    python3 analyze-results.py --scenario <name> [--input <file>] [--output <file>]
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

def parse_args():
    parser = argparse.ArgumentParser(description='分析 OpenClaw 实验结果')
    parser.add_argument('--input', '-i', default='data/experiments.tsv', help='输入文件路径')
    parser.add_argument('--scenario', '-s', help='要分析的场景名称')
    parser.add_argument('--output', '-o', help='输出报告文件路径')
    parser.add_argument('--format', '-f', choices=['markdown', 'json'], default='markdown')
    return parser.parse_args()

def load_experiments(filepath):
    """加载实验数据"""
    records = []
    with open(filepath, 'r') as f:
        headers = f.readline().strip().split('\t')
        for line in f:
            values = line.strip().split('\t')
            record = dict(zip(headers, values))
            # 解析 metrics_json
            record['metrics'] = json.loads(record['metrics_json'])
            record['duration_sec'] = float(record['duration_sec'])
            records.append(record)
    return records

def calculate_statistics(records):
    """计算统计指标"""
    total = len(records)
    completed = sum(1 for r in records if r['status'] == 'completed')
    timeout = sum(1 for r in records if r['status'] == 'timeout')
    error = sum(1 for r in records if r['status'] == 'error')
    avg_duration = sum(r['duration_sec'] for r in records) / total if total > 0 else 0
    
    return {
        'total_experiments': total,
        'completed': completed,
        'timeout': timeout,
        'error': error,
        'success_rate': completed / total if total > 0 else 0,
        'avg_duration': avg_duration
    }

def compare_variants(records):
    """按变体分组统计"""
    variants = {}
    for r in records:
        vid = r['variant_id']
        if vid not in variants:
            variants[vid] = {'runs': 0, 'scores': [], 'durations': [], 'success': 0}
        variants[vid]['runs'] += 1
        variants[vid]['scores'].append(r['metrics'].get('values', {}).get('score', 0))
        variants[vid]['durations'].append(r['duration_sec'])
        if r['status'] == 'completed':
            variants[vid]['success'] += 1
    
    # 计算平均值
    summary = []
    for vid, data in variants.items():
        summary.append({
            'variant_id': vid,
            'runs': data['runs'],
            'avg_score': sum(data['scores']) / len(data['scores']),
            'avg_duration': sum(data['durations']) / len(data['durations']),
            'success_rate': data['success'] / data['runs']
        })
    
    # 按得分排序
    summary.sort(key=lambda x: x['avg_score'], reverse=True)
    return summary

def generate_markdown_report(records, scenario, stats, summary):
    """生成 Markdown 报告"""
    lines = []
    lines.append("# OpenClaw 实验分析报告")
    lines.append("")
    lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    
    lines.append("## 概览")
    lines.append("")
    if scenario:
        lines.append(f"**场景**: {scenario}")
    lines.append(f"**总实验数**: {stats['total_experiments']}")
    lines.append(f"**成功完成**: {stats['completed']} ({stats['success_rate']*100:.1f}%)")
    lines.append(f"**平均耗时**: {stats['avg_duration']:.2f}s")
    lines.append("")
    
    lines.append("## 变体对比")
    lines.append("")
    lines.append("| 排名 | 变体 | 平均得分 | 成功率 | 平均耗时 | 运行次数 |")
    lines.append("|------|------|----------|--------|----------|----------|")
    
    for i, v in enumerate(summary, 1):
        lines.append(f"| {i} | `{v['variant_id']}` | {v['avg_score']:.3f} | {v['success_rate']*100:.1f}% | {v['avg_duration']:.1f}s | {v['runs']} |")
    lines.append("")
    
    if summary:
        best = summary[0]
        lines.append("## 最佳变体")
        lines.append("")
        lines.append(f"**变体 ID**: `{best['variant_id']}`")
        lines.append(f"**综合得分**: {best['avg_score']:.3f}")
        lines.append(f"**成功率**: {best['success_rate']*100:.1f}%")
        lines.append("")
    
    return "\n".join(lines)

def main():
    args = parse_args()
    
    # 确定输入文件
    input_file = args.input
    if not Path(input_file).is_absolute():
        script_dir = Path(__file__).parent
        project_dir = script_dir.parent
        input_file = project_dir / input_file
    
    if not Path(input_file).exists():
        print(f"Error: Input file not found: {input_file}", file=sys.stderr)
        sys.exit(1)
    
    # 加载数据
    records = load_experiments(input_file)
    
    # 筛选
    if args.scenario:
        records = [r for r in records if r['scenario'] == args.scenario]
    
    if not records:
        print("No experiments found matching criteria.")
        sys.exit(0)
    
    # 计算统计
    stats = calculate_statistics(records)
    summary = compare_variants(records)
    
    # 生成报告
    if args.format == 'markdown':
        report = generate_markdown_report(records, args.scenario, stats, summary)
    else:
        report = json.dumps({'stats': stats, 'summary': summary}, indent=2)
    
    # 输出
    if args.output:
        with open(args.output, 'w') as f:
            f.write(report)
        print(f"Report saved to: {args.output}")
    else:
        print(report)

if __name__ == '__main__':
    main()