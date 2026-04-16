#!/usr/bin/env python3
"""
Phase 3 Round 2: 场景化工具测试 - 集成 Browser 工具
目标: 通过实际调用 browser 工具提升反爬/JS场景的成功率
"""

import json
import time
import subprocess
from datetime import datetime
from pathlib import Path

OUTPUT_DIR = Path("/home/jerry/.openclaw/workspace/jerry/design/optimization-framework/experiments/scenario-based")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Round 2 测试URL清单
TEST_CASES = [
    {"id": "S1_001", "scenario": "static", "url": "https://dbreunig.com/2026/04/14/cybersecurity-is-proof-of-work-now.html", "expected_tool": "web_fetch"},
    {"id": "S1_002", "scenario": "static", "url": "https://theleo.zone/posts/pager/", "expected_tool": "web_fetch"},
    {"id": "S2_001", "scenario": "anti_scrape", "url": "https://medium.com/@anthropics/mythos-security-assessment", "expected_tool": "browser"},
    {"id": "S2_002", "scenario": "anti_scrape", "url": "https://www.reddit.com/r/MachineLearning/", "expected_tool": "browser"},
    {"id": "S3_001", "scenario": "platform", "url": "bilibili hot", "expected_tool": "opencli", "opencli_cmd": "opencli bilibili hot --limit 5 -f json"},
    {"id": "S3_002", "scenario": "platform", "url": "zhihu hot", "expected_tool": "opencli", "opencli_cmd": "opencli zhihu hot -f json"},
    {"id": "S4_001", "scenario": "spa", "url": "https://spa-react-example.netlify.app", "expected_tool": "browser"},
    {"id": "S4_002", "scenario": "spa", "url": "https://react.dev", "expected_tool": "browser"},
    {"id": "S5_001", "scenario": "search", "url": "search: AI agents", "expected_tool": "search", "search_query": "what are AI agents"},
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
        result = subprocess.run(
            ["python3", "/home/jerry/.openclaw/workspace/skills/search-suite/scripts/search.py", query],
            capture_output=True,
            text=True,
            timeout=30
        )
        duration = (time.time() - start) * 1000
        has_content = len(result.stdout) > 50
        return {
            "success": has_content,
            "duration_ms": duration,
            "output_length": len(result.stdout),
            "notes": "Search API"
        }
    except Exception as e:
        return {"success": False, "duration_ms": (time.time() - start) * 1000, "error": str(e)}

def test_browser(url):
    """测试 Browser 工具 - 实际调用 agent-browser"""
    start = time.time()
    session_name = f"r2_{int(start)}"
    
    try:
        # 打开页面
        subprocess.run(
            ["agent-browser", "--session", session_name, "open", url],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # 等待加载
        subprocess.run(
            ["agent-browser", "--session", session_name, "wait", "--load", "networkidle"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # 获取内容
        get_result = subprocess.run(
            ["agent-browser", "--session", session_name, "get", "text", "body"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # 关闭会话
        subprocess.run(
            ["agent-browser", "--session", session_name, "close"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        duration = (time.time() - start) * 1000
        content = get_result.stdout
        success = len(content) > 200
        
        return {
            "success": success,
            "duration_ms": duration,
            "content_length": len(content),
            "content_preview": content[:300] if success else None,
            "notes": "Browser via agent-browser"
        }
    except Exception as e:
        try:
            subprocess.run(["agent-browser", "--session", session_name, "close"], capture_output=True, timeout=5)
        except:
            pass
        return {
            "success": False,
            "duration_ms": (time.time() - start) * 1000,
            "error": str(e),
            "notes": "Browser error"
        }

def test_opencli(cmd):
    """测试 opencli 工具"""
    start = time.time()
    try:
        result = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=30)
        duration = (time.time() - start) * 1000
        success = result.returncode == 0 and len(result.stdout) > 50
        return {
            "success": success,
            "duration_ms": duration,
            "output_length": len(result.stdout),
            "error": result.stderr[:200] if result.stderr else None,
            "notes": "opencli CLI"
        }
    except Exception as e:
        return {"success": False, "duration_ms": (time.time() - start) * 1000, "error": str(e)}

def run_test(test_case):
    """执行单个测试"""
    print(f"\n测试 {test_case['id']}: {test_case['url']}")
    print(f"场景: {test_case['scenario']} | 预期工具: {test_case['expected_tool']}")
    
    result = {
        "test_id": test_case['id'],
        "scenario": test_case['scenario'],
        "url": test_case['url'],
        "timestamp": datetime.now().isoformat(),
        "expected_tool": test_case['expected_tool'],
        "tool_sequence": []
    }
    
    # 根据场景选择工具链
    if test_case['scenario'] == 'static':
        tools = [('web_fetch', test_web_fetch, test_case['url'])]
    elif test_case['scenario'] == 'anti_scrape':
        tools = [
            ('browser', test_browser, test_case['url']),
            ('web_fetch', test_web_fetch, test_case['url'])
        ]
    elif test_case['scenario'] == 'platform' and 'opencli_cmd' in test_case:
        tools = [
            ('opencli', test_opencli, test_case['opencli_cmd']),
            ('browser', test_browser, test_case['url'])
        ]
    elif test_case['scenario'] == 'spa':
        tools = [
            ('browser', test_browser, test_case['url']),
            ('web_fetch', test_web_fetch, test_case['url'])
        ]
    elif test_case['scenario'] == 'search':
        tools = [
            ('search', test_search, test_case.get('search_query', '')),
            ('browser', test_browser, f"https://www.google.com/search?q={test_case.get('search_query', '').replace(' ', '+')}")
        ]
    elif test_case['scenario'] == 'realtime' and 'opencli_cmd' in test_case:
        tools = [('opencli', test_opencli, test_case['opencli_cmd'])]
    else:
        tools = [('web_fetch', test_web_fetch, test_case['url'])]
    
    # 执行工具链
    for tool_name, tool_func, tool_arg in tools:
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
            print(f"  ✗ {tool_name}: 失败 - {tool_result.get('error', 'Unknown')[:60]}")
    else:
        result['final_success'] = False
        print(f"  ✗ 所有工具失败")
    
    return result

def run_all_tests():
    """执行所有测试"""
    print("=" * 60)
    print("Phase 3 Round 2: 场景化工具测试 (集成 Browser)")
    print("=" * 60)
    
    results = []
    for test_case in TEST_CASES:
        result = run_test(test_case)
        results.append(result)
        time.sleep(2)
    
    # 保存结果
    output_file = OUTPUT_DIR / f"round2_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'=' * 60}")
    print(f"测试完成！结果保存到: {output_file}")
    
    # 统计
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