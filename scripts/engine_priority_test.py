#!/usr/bin/env python3
"""
Phase 3: 搜索引擎优先级对比实验
对比 Control (Tavily优先) vs Treatment (Brave优先)
"""

import json
import time
import os
from datetime import datetime
from pathlib import Path
import requests

# 测试查询集
TEST_QUERIES = [
    {
        "id": "tech_1",
        "category": "technical",
        "query": "how to optimize asyncio performance python",
        "description": "技术问题"
    },
    {
        "id": "news_1",
        "category": "news",
        "query": "latest AI regulation news 2026",
        "description": "新闻事件"
    },
    {
        "id": "realtime_1",
        "category": "realtime",
        "query": "Sydney weather forecast tomorrow",
        "description": "实时信息"
    },
    {
        "id": "academic_1",
        "category": "academic",
        "query": "LLM reasoning chain of thought papers",
        "description": "学术资料"
    },
    {
        "id": "product_1",
        "category": "product",
        "query": "best noise cancelling headphones review",
        "description": "产品信息"
    }
]

def load_config(config_path: str) -> dict:
    """加载实验配置"""
    with open(config_path) as f:
        return json.load(f)

def search_with_engine_priority(query: str, config: dict) -> dict:
    """
    根据配置执行搜索，按优先级尝试引擎
    """
    engines = sorted(config["engines"], key=lambda x: x.get("priority", 99))
    
    start_time = time.time()
    attempts = []
    
    for engine_config in engines:
        if not engine_config.get("enabled", True):
            continue
            
        engine_name = engine_config["name"]
        attempt_start = time.time()
        
        try:
            result = execute_search(engine_name, query)
            attempt_duration = time.time() - attempt_start
            
            attempt = {
                "engine": engine_name,
                "success": result.get("success", False),
                "duration": round(attempt_duration, 3),
                "credits_used": result.get("credits_used", 0),
                "results_count": len(result.get("results", [])),
                "has_answer": result.get("answer") is not None
            }
            attempts.append(attempt)
            
            if result.get("success"):
                total_duration = time.time() - start_time
                return {
                    "success": True,
                    "engine_used": engine_name,
                    "fallback_count": len(attempts) - 1,
                    "duration": round(total_duration, 3),
                    "credits_used": sum(a["credits_used"] for a in attempts),
                    "results_count": len(result.get("results", [])),
                    "has_answer": result.get("answer") is not None,
                    "attempts": attempts
                }
                
        except Exception as e:
            attempt_duration = time.time() - attempt_start
            attempts.append({
                "engine": engine_name,
                "success": False,
                "duration": round(attempt_duration, 3),
                "error": str(e)
            })
            continue
    
    total_duration = time.time() - start_time
    return {
        "success": False,
        "error": "所有引擎失败",
        "fallback_count": len(attempts) - 1,
        "duration": round(total_duration, 3),
        "attempts": attempts
    }

def execute_search(engine: str, query: str) -> dict:
    """调用具体搜索引擎"""
    if engine == "tavily":
        return search_tavily(query)
    elif engine == "brave":
        return search_brave(query)
    elif engine == "google":
        return search_google(query)
    else:
        raise ValueError(f"未知引擎: {engine}")

def search_tavily(query: str) -> dict:
    """Tavily搜索"""
    api_key = os.environ.get("TAVILY_API_KEY", "")
    if not api_key:
        return {"success": False, "error": "TAVILY_API_KEY未设置"}
    
    try:
        response = requests.post(
            "https://api.tavily.com/search",
            json={
                "query": query,
                "api_key": api_key,
                "include_answer": True,
                "include_raw_content": False,
                "max_results": 5
            },
            timeout=30
        )
        data = response.json()
        
        return {
            "success": True,
            "answer": data.get("answer"),
            "results": data.get("results", []),
            "credits_used": 1
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def search_brave(query: str) -> dict:
    """Brave搜索"""
    api_key = os.environ.get("BRAVE_API_KEY", "")
    if not api_key:
        return {"success": False, "error": "BRAVE_API_KEY未设置"}
    
    try:
        response = requests.get(
            "https://api.search.brave.com/res/v1/web/search",
            params={"q": query, "count": 5},
            headers={
                "X-Subscription-Token": api_key,
                "Accept": "application/json"
            },
            timeout=30
        )
        data = response.json()
        web_results = data.get("web", {}).get("results", [])
        
        results = []
        for r in web_results[:5]:
            results.append({
                "title": r.get("title"),
                "url": r.get("url"),
                "content": r.get("description")
            })
        
        return {
            "success": True,
            "answer": None,  # Brave不直接返回答案
            "results": results,
            "credits_used": 1
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def search_google(query: str) -> dict:
    """Google搜索 - 使用OpenClaw web_search"""
    return {
        "success": True,
        "engine": "google",
        "answer": None,
        "results": [],
        "credits_used": 0,
        "note": "Placeholder - 需要OpenClaw web_search工具"
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
        
        result = search_with_engine_priority(test_query['query'], config)
        result["query_id"] = test_query['id']
        result["category"] = test_query['category']
        result["query"] = test_query['query']
        results.append(result)
        
        if result["success"]:
            print(f"  ✓ 成功 | 引擎: {result['engine_used']} | 耗时: {result['duration']}s | Fallback: {result['fallback_count']}")
        else:
            print(f"  ✗ 失败 | 耗时: {result['duration']}s | 错误: {result.get('error', 'Unknown')}")
        
        time.sleep(1)
    
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
    
    # 按类别统计
    by_category = {}
    for r in results:
        cat = r.get("category", "unknown")
        if cat not in by_category:
            by_category[cat] = {"total": 0, "successes": 0}
        by_category[cat]["total"] += 1
        if r["success"]:
            by_category[cat]["successes"] += 1
    
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
        "total_credits": sum(credits),
        "by_category": {k: {"success_rate": round(v["successes"]/v["total"]*100, 2), "count": v["total"]} for k, v in by_category.items()},
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
    
    parser = argparse.ArgumentParser(description="搜索引擎优先级对比实验")
    parser.add_argument("--rounds", type=int, default=5, help="测试轮数")
    parser.add_argument("--output-dir", type=str, default="../experiments/engine-priority", help="输出目录")
    parser.add_argument("--skip-tests", action="store_true", help="跳过测试，仅分析已有结果")
    args = parser.parse_args()
    
    base_dir = Path(__file__).parent.parent
    configs_dir = base_dir / "configs"
    output_dir = base_dir / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    
    control_config = configs_dir / "engine-priority-control.json"
    treatment_config = configs_dir / "engine-priority-treatment.json"
    
    control_data = []
    treatment_data = []
    
    if not args.skip_tests:
        print("🚀 开始搜索引擎优先级对比实验")
        print(f"计划执行: {args.rounds} 轮 x 2 组 = {args.rounds * 2} 批次测试")
        
        # 检查API Key
        if not os.environ.get("TAVILY_API_KEY"):
            print("⚠️ 警告: TAVILY_API_KEY 未设置")
        if not os.environ.get("BRAVE_API_KEY"):
            print("⚠️ 警告: BRAVE_API_KEY 未设置")
        
        for i in range(1, args.rounds + 1):
            # Control组
            control_result = run_round(control_config, i, "control")
            control_data.append(control_result)
            
            control_file = output_dir / f"round{i}-control.json"
            with open(control_file, "w") as f:
                json.dump(control_result, f, indent=2)
            print(f"  💾 已保存: {control_file}")
            
            time.sleep(2)  # 间隔避免限流
            
            # Treatment组
            treatment_result = run_round(treatment_config, i, "treatment")
            treatment_data.append(treatment_result)
            
            treatment_file = output_dir / f"round{i}-treatment.json"
            with open(treatment_file, "w") as f:
                json.dump(treatment_result, f, indent=2)
            print(f"  💾 已保存: {treatment_file}")
            
            if i < args.rounds:
                time.sleep(3)  # 轮间间隔
    else:
        # 加载已有结果
        print("📂 加载已有实验结果...")
        for i in range(1, args.rounds + 1):
            control_file = output_dir / f"round{i}-control.json"
            treatment_file = output_dir / f"round{i}-treatment.json"
            
            if control_file.exists():
                with open(control_file) as f:
                    control_data.append(json.load(f))
            if treatment_file.exists():
                with open(treatment_file) as f:
                    treatment_data.append(json.load(f))
    
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
        print(f"  总消耗: {report['control']['analysis']['total_credits']} credits")
        
        print(f"\n实验组 (Brave优先):")
        print(f"  成功率: {report['treatment']['analysis']['success_rate']:.2f}%")
        print(f"  平均耗时: {report['treatment']['analysis']['avg_duration']:.3f}s")
        print(f"  平均Fallback: {report['treatment']['analysis']['avg_fallback']:.2f}")
        print(f"  总消耗: {report['treatment']['analysis']['total_credits']} credits")
        
        print(f"\n差异对比:")
        print(f"  成功率变化: {report['comparison']['success_rate_diff']:+.2f}%")
        print(f"  耗时变化: {report['comparison']['duration_diff']:+.3f}s")
        print(f"  Fallback变化: {report['comparison']['fallback_diff']:+.2f}")
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
            
        if treat['total_credits'] < ctrl['total_credits']:
            recommendations.append("实验组额度消耗更少")
        elif treat['total_credits'] > ctrl['total_credits']:
            recommendations.append("对照组额度消耗更少")
        
        for rec in recommendations:
            print(f"  • {rec}")
            
        # 最终建议
        print("\n最终建议:")
        if treat['success_rate'] >= ctrl['success_rate'] and treat['avg_fallback'] <= ctrl['avg_fallback']:
            print("  ✅ 建议采用实验组策略 (Brave优先)")
        elif ctrl['success_rate'] > treat['success_rate'] or (ctrl['success_rate'] == treat['success_rate'] and ctrl['avg_fallback'] < treat['avg_fallback']):
            print("  ✅ 建议保持对照组策略 (Tavily优先)")
        else:
            print("  ⚖️ 建议根据具体场景选择策略")
            print(f"     - 困难/实时场景考虑: {'Brave优先' if treat['by_category'].get('hard', {}).get('success_rate', 0) > ctrl['by_category'].get('hard', {}).get('success_rate', 0) else 'Tavily优先'}")
    else:
        print("⚠️ 没有足够的实验数据进行对比分析")

if __name__ == "__main__":
    main()