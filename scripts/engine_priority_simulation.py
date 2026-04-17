#!/usr/bin/env python3
"""
Phase 3: 搜索引擎优先级对比实验 (模拟模式)
对比 Control (Tavily优先) vs Treatment (Brave优先)

模拟引擎行为差异来验证策略效果
"""

import json
import time
import random
from datetime import datetime
from pathlib import Path

# 测试查询集 - 定义每个查询最适合的引擎
TEST_QUERIES = [
    {
        "id": "tech_1",
        "category": "technical",
        "query": "how to optimize asyncio performance python",
        "description": "技术问题",
        "best_engine": "tavily",
        "fallback_rate": {"tavily": 0.1, "brave": 0.2, "google": 0.05}
    },
    {
        "id": "news_1",
        "category": "news",
        "query": "latest AI regulation news 2026",
        "description": "新闻事件",
        "best_engine": "brave",
        "fallback_rate": {"tavily": 0.3, "brave": 0.1, "google": 0.15}
    },
    {
        "id": "realtime_1",
        "category": "realtime",
        "query": "Sydney weather forecast tomorrow",
        "description": "实时信息",
        "best_engine": "brave",
        "fallback_rate": {"tavily": 0.4, "brave": 0.15, "google": 0.1}
    },
    {
        "id": "academic_1",
        "category": "academic",
        "query": "LLM reasoning chain of thought papers",
        "description": "学术资料",
        "best_engine": "tavily",
        "fallback_rate": {"tavily": 0.15, "brave": 0.25, "google": 0.2}
    },
    {
        "id": "product_1",
        "category": "product",
        "query": "best noise cancelling headphones review",
        "description": "产品信息",
        "best_engine": "brave",
        "fallback_rate": {"tavily": 0.25, "brave": 0.1, "google": 0.15}
    }
]

def load_config(config_path: str) -> dict:
    """加载实验配置"""
    with open(config_path) as f:
        return json.load(f)

def simulate_search(query_config: dict, engine: str, attempt_num: int) -> dict:
    """
    模拟搜索引擎行为
    
    关键差异：
    - Tavily: 对技术/学术问题效果好，但新闻/实时信息稍慢
    - Brave: 对新闻/实时/产品效果好，速度较快
    - Google: 通用备选，免费但结果质量中等
    """
    # 基于查询类型和引擎计算成功率和响应时间
    fallback_rate = query_config["fallback_rate"].get(engine, 0.3)
    
    # 首次尝试成功率更高
    if attempt_num == 0:
        fallback_rate *= 0.8
    
    # 模拟成功率
    success = random.random() > fallback_rate
    
    # 模拟响应时间 (秒)
    base_latency = {
        "tavily": 0.8,
        "brave": 0.5,
        "google": 1.2
    }.get(engine, 1.0)
    
    # 查询类型影响响应时间
    category_factor = {
        "technical": 1.1,
        "news": 0.9,
        "realtime": 0.8,
        "academic": 1.2,
        "product": 0.9
    }.get(query_config["category"], 1.0)
    
    duration = base_latency * category_factor * (0.8 + random.random() * 0.4)
    
    # 模拟结果质量 (1-5)
    if engine == query_config["best_engine"]:
        quality = random.randint(4, 5)
    elif engine == "google":
        quality = random.randint(2, 4)
    else:
        quality = random.randint(3, 4)
    
    # 是否返回答案
    has_answer = engine == "tavily" and success
    
    return {
        "success": success,
        "engine": engine,
        "duration": round(duration, 3),
        "credits_used": 1 if engine != "google" else 0,
        "results_count": random.randint(3, 5) if success else 0,
        "quality": quality if success else 0,
        "has_answer": has_answer
    }

def search_with_engine_priority(query_config: dict, config: dict) -> dict:
    """
    根据配置执行搜索，按优先级尝试引擎
    """
    engines = sorted(config["engines"], key=lambda x: x.get("priority", 99))
    
    start_time = time.time()
    attempts = []
    
    for idx, engine_config in enumerate(engines):
        if not engine_config.get("enabled", True):
            continue
            
        engine_name = engine_config["name"]
        attempt_start = time.time()
        
        # 模拟搜索
        result = simulate_search(query_config, engine_name, idx)
        attempt_duration = time.time() - attempt_start
        
        attempt = {
            "engine": engine_name,
            "success": result["success"],
            "duration": round(attempt_duration + result["duration"], 3),
            "credits_used": result["credits_used"],
            "results_count": result["results_count"],
            "has_answer": result["has_answer"],
            "quality": result["quality"]
        }
        attempts.append(attempt)
        
        if result["success"]:
            total_duration = time.time() - start_time
            return {
                "success": True,
                "engine_used": engine_name,
                "fallback_count": len(attempts) - 1,
                "duration": round(total_duration + result["duration"], 3),
                "credits_used": sum(a["credits_used"] for a in attempts),
                "results_count": result["results_count"],
                "has_answer": result["has_answer"],
                "quality": result["quality"],
                "attempts": attempts
            }
    
    total_duration = time.time() - start_time
    return {
        "success": False,
        "error": "所有引擎失败",
        "fallback_count": len(attempts) - 1,
        "duration": round(total_duration, 3),
        "attempts": attempts
    }

def run_round(config_path: str, round_num: int, variant: str) -> dict:
    """执行一轮测试"""
    config = load_config(config_path)
    results = []
    
    print(f"\n{'='*60}")
    print(f"开始 {variant.upper()} 第 {round_num} 轮测试")
    print(f"策略: {config['description']}")
    print(f"{'='*60}")
    
    for test_query in TEST_QUERIES:
        print(f"\n[{test_query['id']}] {test_query['description']}")
        print(f"查询: {test_query['query']}")
        
        result = search_with_engine_priority(test_query, config)
        result["query_id"] = test_query['id']
        result["category"] = test_query['category']
        result["query"] = test_query['query']
        result["best_engine"] = test_query['best_engine']
        results.append(result)
        
        if result["success"]:
            print(f"  ✓ 成功 | 引擎: {result['engine_used']} | 耗时: {result['duration']:.2f}s | "
                  f"Fallback: {result['fallback_count']} | 质量: {result.get('quality', 0)}/5")
        else:
            print(f"  ✗ 失败 | 耗时: {result['duration']:.2f}s | 错误: {result.get('error', 'Unknown')}")
        
        time.sleep(0.1)  # 小间隔避免过于密集
    
    return {
        "variant": variant,
        "round": round_num,
        "timestamp": datetime.now().isoformat(),
        "config_name": config["name"],
        "results": results
    }

def analyze_results(results: list) -> dict:
    """分析结果"""
    total = len(results)
    successes = sum(1 for r in results if r["success"])
    
    durations = [r["duration"] for r in results if r["success"]]
    fallback_counts = [r.get("fallback_count", 0) for r in results]
    credits = [r.get("credits_used", 0) for r in results]
    qualities = [r.get("quality", 0) for r in results if r["success"]]
    
    # 按类别统计
    by_category = {}
    for r in results:
        cat = r.get("category", "unknown")
        if cat not in by_category:
            by_category[cat] = {"total": 0, "successes": 0, "fallbacks": [], "credits": []}
        by_category[cat]["total"] += 1
        if r["success"]:
            by_category[cat]["successes"] += 1
        by_category[cat]["fallbacks"].append(r.get("fallback_count", 0))
        by_category[cat]["credits"].append(r.get("credits_used", 0))
    
    # 按类别整理
    by_category_summary = {}
    for cat, data in by_category.items():
        by_category_summary[cat] = {
            "success_rate": round(data["successes"] / data["total"] * 100, 2),
            "avg_fallback": round(sum(data["fallbacks"]) / len(data["fallbacks"]), 2),
            "total_credits": sum(data["credits"])
        }
    
    # 引擎使用分布
    engine_usage = {}
    for r in results:
        if r["success"]:
            engine = r.get("engine_used", "unknown")
            engine_usage[engine] = engine_usage.get(engine, 0) + 1
    
    return {
        "total_queries": total,
        "successes": successes,
        "success_rate": round(successes / total * 100, 2) if total > 0 else 0,
        "avg_duration": round(sum(durations) / len(durations), 3) if durations else 0,
        "avg_fallback": round(sum(fallback_counts) / len(fallback_counts), 2) if fallback_counts else 0,
        "avg_quality": round(sum(qualities) / len(qualities), 2) if qualities else 0,
        "total_credits": sum(credits),
        "by_category": by_category_summary,
        "engine_usage": engine_usage
    }

def generate_report(control_data: list, treatment_data: list, output_dir: str):
    """生成实验报告"""
    control_analysis = analyze_results([r for rd in control_data for r in rd["results"]])
    treatment_analysis = analyze_results([r for rd in treatment_data for r in rd["results"]])
    
    report = {
        "experiment": "Phase 3: 搜索引擎优先级对比",
        "timestamp": datetime.now().isoformat(),
        "control": {
            "config": "Tavily优先 → Brave → Google",
            "rounds": len(control_data),
            "analysis": control_analysis
        },
        "treatment": {
            "config": "Brave优先 → Tavily → Google",
            "rounds": len(treatment_data),
            "analysis": treatment_analysis
        },
        "comparison": {
            "success_rate_diff": round(treatment_analysis["success_rate"] - control_analysis["success_rate"], 2),
            "duration_diff": round(treatment_analysis["avg_duration"] - control_analysis["avg_duration"], 3),
            "fallback_diff": round(treatment_analysis["avg_fallback"] - control_analysis["avg_fallback"], 2),
            "quality_diff": round(treatment_analysis["avg_quality"] - control_analysis["avg_quality"], 2),
            "credits_diff": treatment_analysis["total_credits"] - control_analysis["total_credits"]
        }
    }
    
    output_path = Path(output_dir) / "engine-priority-analysis.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📊 分析报告已保存: {output_path}")
    return report

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="搜索引擎优先级对比实验 (模拟)")
    parser.add_argument("--rounds", type=int, default=5, help="测试轮数")
    parser.add_argument("--output-dir", type=str, default="experiments/engine-priority", help="输出目录")
    parser.add_argument("--seed", type=int, default=42, help="随机种子")
    args = parser.parse_args()
    
    # 设置随机种子
    random.seed(args.seed)
    
    base_dir = Path(__file__).parent.parent
    configs_dir = base_dir / "configs"
    output_dir = base_dir / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    
    control_config = configs_dir / "engine-priority-control.json"
    treatment_config = configs_dir / "engine-priority-treatment.json"
    
    control_data = []
    treatment_data = []
    
    print("🚀 开始搜索引擎优先级对比实验 (模拟模式)")
    print(f"计划执行: {args.rounds} 轮 x 2 组 = {args.rounds * 2} 批次测试")
    print(f"随机种子: {args.seed}")
    
    for i in range(1, args.rounds + 1):
        # Control组
        control_result = run_round(control_config, i, "control")
        control_data.append(control_result)
        
        control_file = output_dir / f"round{i}-control.json"
        with open(control_file, "w") as f:
            json.dump(control_result, f, indent=2)
        print(f"  💾 已保存: {control_file}")
        
        time.sleep(0.5)
        
        # Treatment组
        treatment_result = run_round(treatment_config, i, "treatment")
        treatment_data.append(treatment_result)
        
        treatment_file = output_dir / f"round{i}-treatment.json"
        with open(treatment_file, "w") as f:
            json.dump(treatment_result, f, indent=2)
        print(f"  💾 已保存: {treatment_file}")
        
        if i < args.rounds:
            time.sleep(1)
    
    # 生成报告
    if control_data and treatment_data:
        report = generate_report(control_data, treatment_data, output_dir)
        
        print("\n" + "="*60)
        print("📈 实验结果汇总")
        print("="*60)
        print(f"\n对照组 (Tavily优先):")
        print(f"  成功率: {report['control']['analysis']['success_rate']:.2f}%")
        print(f"  平均耗时: {report['control']['analysis']['avg_duration']:.3f}s")
        print(f"  平均Fallback: {report['control']['analysis']['avg_fallback']:.2f}")
        print(f"  平均质量: {report['control']['analysis']['avg_quality']:.2f}/5")
        print(f"  总消耗: {report['control']['analysis']['total_credits']} credits")
        print(f"  引擎使用: {report['control']['analysis']['engine_usage']}")
        
        print(f"\n实验组 (Brave优先):")
        print(f"  成功率: {report['treatment']['analysis']['success_rate']:.2f}%")
        print(f"  平均耗时: {report['treatment']['analysis']['avg_duration']:.3f}s")
        print(f"  平均Fallback: {report['treatment']['analysis']['avg_fallback']:.2f}")
        print(f"  平均质量: {report['treatment']['analysis']['avg_quality']:.2f}/5")
        print(f"  总消耗: {report['treatment']['analysis']['total_credits']} credits")
        print(f"  引擎使用: {report['treatment']['analysis']['engine_usage']}")
        
        print(f"\n差异对比:")
        print(f"  成功率变化: {report['comparison']['success_rate_diff']:+.2f}%")
        print(f"  耗时变化: {report['comparison']['duration_diff']:+.3f}s")
        print(f"  Fallback变化: {report['comparison']['fallback_diff']:+.2f}")
        print(f"  质量变化: {report['comparison']['quality_diff']:+.2f}")
        print(f"  消耗变化: {report['comparison']['credits_diff']:+d} credits")
        
        # 推荐策略
        print("\n" + "="*60)
        print("🎯 推荐策略")
        print("="*60)
        
        ctrl = report['control']['analysis']
        treat = report['treatment']['analysis']
        
        recommendations = []
        if treat['success_rate'] > ctrl['success_rate']:
            recommendations.append("实验组(Brave优先)成功率更高")
        elif treat['success_rate'] < ctrl['success_rate']:
            recommendations.append("对照组(Tavily优先)成功率更高")
        else:
            recommendations.append("两组成功率相同")
            
        if treat['avg_fallback'] < ctrl['avg_fallback']:
            recommendations.append("实验组平均Fallback次数更少")
        elif treat['avg_fallback'] > ctrl['avg_fallback']:
            recommendations.append("对照组平均Fallback次数更少")
            
        if treat['avg_quality'] > ctrl['avg_quality']:
            recommendations.append("实验组结果质量更高")
        elif treat['avg_quality'] < ctrl['avg_quality']:
            recommendations.append("对照组结果质量更高")
        
        if treat['total_credits'] < ctrl['total_credits']:
            recommendations.append("实验组额度消耗更少")
        elif treat['total_credits'] > ctrl['total_credits']:
            recommendations.append("对照组额度消耗更少")
        
        for rec in recommendations:
            print(f"  • {rec}")
            
        # 最终建议
        print("\n最终建议:")
        score_treatment = 0
        score_control = 0
        
        if treat['success_rate'] > ctrl['success_rate']:
            score_treatment += 2
        elif treat['success_rate'] < ctrl['success_rate']:
            score_control += 2
            
        if treat['avg_fallback'] < ctrl['avg_fallback']:
            score_treatment += 1
        elif treat['avg_fallback'] > ctrl['avg_fallback']:
            score_control += 1
            
        if treat['avg_quality'] > ctrl['avg_quality']:
            score_treatment += 2
        elif treat['avg_quality'] < ctrl['avg_quality']:
            score_control += 2
        
        if score_treatment > score_control:
            print("  ✅ 建议采用实验组策略 (Brave优先)")
        elif score_control > score_treatment:
            print("  ✅ 建议保持对照组策略 (Tavily优先)")
        else:
            print("  ⚖️ 建议根据具体场景选择策略")
    else:
        print("⚠️ 没有足够的实验数据进行对比分析")

if __name__ == "__main__":
    main()
