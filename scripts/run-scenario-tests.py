#!/usr/bin/env python3
"""
Phase 3: 场景化工具测试执行脚本
记录不同工具在不同场景下的使用效果
"""

import json
import time
import subprocess
from datetime import datetime
from pathlib import Path

OUTPUT_DIR = Path("/home/jerry/.openclaw/workspace/jerry/design/optimization-framework/experiments/scenario-based")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 测试URL清单 - Round 1
TEST_CASES = [
    # S1: 简单静态页
    {"id": "S1_001", "scenario": "static", "url": "https://dbreunig.com/2026/04/14/cybersecurity-is-proof-of-work-now.html", "expected_tool": "web_fetch"},
    {"id": "S1_002", "scenario": "static", "url": "https://theleo.zone/posts/pager/", "expected_tool": "web_fetch"},
    
    # S2: 反爬页面
    {"id": "S2_001", "scenario": "anti_scrape", "url": "https://medium.com/@anthropics/mythos-security-assessment", "expected_tool": "browser"},
    {"id": "S2_002", "scenario": "anti_scrape", "url": "https://www.reddit.com/r/MachineLearning/", "expected_tool": "browser"},
    
    # S3: 平台内容 - 使用正确的 opencli 命令
    {"id": "S3_001", "scenario": "platform", "url": "bilibili hot", "expected_tool": "opencli", "opencli_cmd": "opencli bilibili hot --limit 5 -f json"},
    {"id": "S3_002", "scenario": "platform", "url": "zhihu hot", "expected_tool": "opencli", "opencli_cmd": "opencli zhihu hot -f json"},
    
    # S4: JS渲染页
    {"id": "S4_001", "scenario": "spa", "url": "https://spa-react-example.netlify.app", "expected_tool": "browser"},
    
    # S5: 搜索场景
    {"id": "S5_001", "scenario": "search", "url": "search: AI agents", "expected_tool": "search", "search_query": "what are AI agents"},
    
    # S6: 实时数据
    {"id": "S6_001", "scenario": "realtime", "url": "https://wttr.in/Sydney?format=j1", "expected_tool": "web_fetch"},
    {"id": "S6_002", "scenario": "realtime", "url": "weibo hot", "expected_tool": "opencli", "opencli_cmd": "opencli weibo hot -f json"},
]

def test_web_fetch(url):
    """测试 web_fetch 工具"""
    start = time.time()
    try:
        import requests
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        duration = (time.time() - start) * 1000
        
        return {
            "success": resp.status_code == 200,
            "duration_ms": duration,
            "status_code": resp.status_code,
            "content_length": len(resp.text) if resp.status_code == 200 else 0,
            "notes": "HTTP直接抓取"
        }
    except Exception as e:
        return {"success": False, "duration_ms": (time.time() - start) * 1000, "error": str(e)}

def test_search(query):
    """测试 Search API 工具"""
    start = time.time()
    try:
        # 使用 search-suite 的 search.py
        result = subprocess.run(
            ["python3", "/home/jerry/.openclaw/workspace/skills/search-suite/scripts/search.py", query],
            capture_output=True,
            text=True,
            timeout=30
        )
        duration = (time.time() - start) * 1000
        
        try:
            data = json.loads(result.stdout)
            success = data.get("success", False)
            return {
                "success": success,
                "duration_ms": duration,
                "engine": data.get("engine", "unknown"),
                "results_count": len(data.get("results", [])),
                "has_answer": bool(data.get("answer")),
                "notes": f"Search API via {data.get('engine', 'unknown')}"
            }
        except:
            return {"success": False, "duration_ms": duration, "error": "Parse failed", "raw": result.stdout[:200]}
    except Exception as e:
        return {"success": False, "duration_ms": (time.time() - start) * 1000, "error": str(e)}

def test_browser(url):
    """测试 Browser 工具 - 标记需要手动执行"""
    return {
        "success": None,
        "duration_ms": 0,
        "notes": "Browser工具需手动执行: browser --url {url} --snapshot",
        "manual_command": f"browser --url {url} --snapshot"
    }

def test_opencli(cmd):
    """测试 opencli 工具"""
    start = time.time()
    try:
        result = subprocess.run(
            cmd.split(),
            capture_output=True,
            text=True,
            timeout=30
        )
        duration = (time.time() - start) * 1000
        
        success = result.returncode == 0 and len(result.stdout) > 100
        return {
            "success": success,
            "duration_ms": duration,
            "output_length": len(result.stdout),
            "error": result.stderr[:200] if result.stderr else None,
            "notes": "opencli CLI执行"
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "duration_ms": (time.time() - start) * 1000, "error": "Timeout"}
    except Exception as e:
        return {"success": False, "duration_ms": (time.time() - start) * 1000, "error": str(e)}

def run_test(test_case):
    """执行单个测试用例"""
    print(f"\n测试 {test_case['id']}: {test_case['url']}")
    print(f"预期工具: {test_case['expected_tool']}")
    
    result = {
        "test_id": test_case['id'],
        "scenario": test_case['scenario'],
        "url": test_case['url'],
        "timestamp": datetime.now().isoformat(),
        "expected_tool": test_case['expected_tool'],
        "tool_sequence": []
    }
    
    # 按优先级尝试工具
    tools_to_try = []
    
    if test_case['scenario'] == 'static':
        tools_to_try = [('web_fetch', test_web_fetch, test_case['url'])]
    elif test_case['scenario'] == 'anti_scrape':
        tools_to_try = [
            ('browser', test_browser, test_case['url']),
            ('web_fetch', test_web_fetch, test_case['url'])
        ]
    elif test_case['scenario'] == 'platform' and 'opencli_cmd' in test_case:
        tools_to_try = [
            ('opencli', test_opencli, test_case['opencli_cmd']),
            ('browser', test_browser, test_case['url'])
        ]
    elif test_case['scenario'] == 'spa':
        tools_to_try = [('browser', test_browser, test_case['url'])]
    elif test_case['scenario'] == 'search' and 'search_query' in test_case:
        tools_to_try = [('search', test_search, test_case['search_query'])]
    elif test_case['scenario'] == 'realtime' and 'opencli_cmd' in test_case:
        tools_to_try = [
            ('opencli', test_opencli, test_case['opencli_cmd']),
            ('web_fetch', test_web_fetch, test_case['url'])
        ]
    elif test_case['scenario'] == 'realtime':
        tools_to_try = [('web_fetch', test_web_fetch, test_case['url'])]
    
    # 执行工具链
    for tool_name, tool_func, tool_arg in tools_to_try:
        tool_result = tool_func(tool_arg)
        tool_result['tool'] = tool_name
        result['tool_sequence'].append(tool_result)
        
        if tool_result['success']:
            print(f"  ✓ {tool_name}: 成功 ({tool_result.get('duration_ms', 0):.0f}ms)")
            result['primary_tool_success'] = (tool_name == test_case['expected_tool'])
            result['fallback_triggered'] = len(result['tool_sequence']) > 1
            result['final_success'] = True
            break
        else:
            print(f"  ✗ {tool_name}: 失败 - {tool_result.get('error', tool_result.get('notes', 'Unknown'))}")
    else:
        result['final_success'] = False
        print(f"  ✗ 所有工具失败")
    
    return result

def run_all_tests():
    """执行所有测试"""
    print("=" * 60)
    print("Phase 3: 场景化工具测试")
    print("=" * 60)
    
    results = []
    for test_case in TEST_CASES:
        result = run_test(test_case)
        results.append(result)
        time.sleep(1)  # 避免过于频繁请求
    
    # 保存结果
    output_file = OUTPUT_DIR / f"round1_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'=' * 60}")
    print(f"测试完成！结果保存到: {output_file}")
    
    # 汇总统计
    total = len(results)
    success = sum(1 for r in results if r['final_success'])
    correct_tool = sum(1 for r in results if r.get('primary_tool_success', False))
    
    print(f"\n汇总:")
    print(f"  总测试数: {total}")
    print(f"  成功数: {success} ({success/total*100:.0f}%)")
    print(f"  首选工具正确: {correct_tool} ({correct_tool/total*100:.0f}%)")
    
    return results

if __name__ == "__main__":
    run_all_tests()