#!/usr/bin/env python3
"""
Phase 3 Round 3 - Host Environment Test Execution
Run 70+ test cases on Host (mini) to collect real success rate data
"""

import json
import time
import subprocess
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

# Add search-suite scripts to path
SEARCH_SUITE_PATH = Path.home() / ".openclaw/workspace/skills/search-suite/scripts"
sys.path.insert(0, str(SEARCH_SUITE_PATH))

try:
    from scenario_detect import detect_scenario, select_tools_for_scenario, load_config
except ImportError as e:
    print(f"Warning: Could not import scenario_detect: {e}")
    detect_scenario = None

# Test configuration
TEST_DATA_PATH = Path("/home/jerry/.openclaw/workspace/jerry/design/optimization-framework/phase3-design/test-data/round3_test_set_70.json")
OUTPUT_DIR = Path("/home/jerry/.openclaw/workspace/jerry/design/optimization-framework/experiments/scenario-based")
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
OUTPUT_FILE = OUTPUT_DIR / f"round3_host_{TIMESTAMP}.json"

# Tool execution functions
def execute_web_fetch(url: str, timeout: int = 15) -> Dict[str, Any]:
    """Execute web_fetch tool"""
    start_time = time.time()
    try:
        result = subprocess.run(
            ["curl", "-s", "-L", "-A", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36", 
             "--max-time", str(timeout), url],
            capture_output=True,
            text=True,
            timeout=timeout + 5
        )
        duration_ms = (time.time() - start_time) * 1000
        
        success = result.returncode == 0 and len(result.stdout) > 100
        return {
            "tool": "web_fetch",
            "success": success,
            "duration_ms": duration_ms,
            "status_code": 200 if success else (result.returncode if result.returncode != 0 else 403),
            "content_length": len(result.stdout),
            "content_preview": result.stdout[:500] if success else None,
            "error": result.stderr[:200] if not success else None,
            "notes": "HTTP直接抓取"
        }
    except Exception as e:
        return {
            "tool": "web_fetch",
            "success": False,
            "duration_ms": (time.time() - start_time) * 1000,
            "error": str(e),
            "notes": "HTTP直接抓取失败"
        }


def execute_opencli(query: str, timeout: int = 15) -> Dict[str, Any]:
    """Execute opencli tool"""
    start_time = time.time()
    try:
        # Parse query for opencli
        parts = query.split()
        if len(parts) >= 2:
            platform = parts[0]
            action = parts[1] if len(parts) > 1 else "hot"
            cmd = ["opencli", platform, action, "-f", "json"]
        else:
            cmd = ["opencli"] + parts + ["-f", "json"]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        duration_ms = (time.time() - start_time) * 1000
        
        success = result.returncode == 0 and len(result.stdout) > 50
        return {
            "tool": "opencli",
            "success": success,
            "duration_ms": duration_ms,
            "output_length": len(result.stdout),
            "output_preview": result.stdout[:500] if success else None,
            "error": result.stderr[:200] if not success and result.stderr else None,
            "notes": "opencli CLI"
        }
    except Exception as e:
        return {
            "tool": "opencli",
            "success": False,
            "duration_ms": (time.time() - start_time) * 1000,
            "error": str(e)[:200],
            "notes": "opencli CLI"
        }


def execute_search(query: str, timeout: int = 30) -> Dict[str, Any]:
    """Execute search via search.py"""
    start_time = time.time()
    try:
        search_script = SEARCH_SUITE_PATH / "search.py"
        result = subprocess.run(
            ["python3", str(search_script), "smart", query],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(SEARCH_SUITE_PATH)
        )
        duration_ms = (time.time() - start_time) * 1000
        
        success = result.returncode == 0 and len(result.stdout) > 100
        return {
            "tool": "search",
            "success": success,
            "duration_ms": duration_ms,
            "output_length": len(result.stdout),
            "output_preview": result.stdout[:500] if success else None,
            "error": result.stderr[:200] if not success and result.stderr else None,
            "notes": "Search API"
        }
    except Exception as e:
        return {
            "tool": "search",
            "success": False,
            "duration_ms": (time.time() - start_time) * 1000,
            "error": str(e)[:200],
            "notes": "Search API"
        }


def execute_tool_for_scenario(scenario: str, input_data: str, expected_tool: str) -> List[Dict[str, Any]]:
    """Execute tool chain based on scenario"""
    tool_sequence = []
    
    # Define tool chains per scenario
    if scenario == "static":
        tools = ["web_fetch"]
    elif scenario == "anti_scrape":
        tools = ["web_fetch"]  # Fallback to web_fetch for anti-scrape in simple test
    elif scenario == "platform":
        tools = ["opencli", "web_fetch"]
    elif scenario == "spa":
        tools = ["web_fetch"]  # SPA falls back to web_fetch
    elif scenario == "search":
        tools = ["search", "web_fetch"]
    elif scenario == "realtime":
        if "wttr.in" in input_data or "天气" in input_data or "weather" in input_data.lower():
            tools = ["web_fetch", "opencli"]
        else:
            tools = ["opencli", "web_fetch"]
    else:
        tools = ["web_fetch"]
    
    for tool in tools:
        if tool == "web_fetch":
            result = execute_web_fetch(input_data)
        elif tool == "opencli":
            result = execute_opencli(input_data)
        elif tool == "search":
            result = execute_search(input_data)
        else:
            continue
            
        tool_sequence.append(result)
        
        # Stop if successful
        if result["success"]:
            break
    
    return tool_sequence


def run_test(test_case: Dict[str, Any]) -> Dict[str, Any]:
    """Run a single test case"""
    test_id = test_case["id"]
    scenario = test_case["scenario"]
    input_data = test_case["input"]
    expected_tool = test_case.get("expected_tool", "unknown")
    
    print(f"Running {test_id}: {scenario} - {input_data[:60]}...")
    
    # Execute tool chain
    tool_sequence = execute_tool_for_scenario(scenario, input_data, expected_tool)
    
    # Determine success
    primary_success = tool_sequence[0]["success"] if tool_sequence else False
    final_success = any(r["success"] for r in tool_sequence)
    fallback_triggered = len(tool_sequence) > 1 and not primary_success
    
    result = {
        "test_id": test_id,
        "scenario": scenario,
        "url": input_data,
        "timestamp": datetime.now().isoformat(),
        "expected_tool": expected_tool,
        "tool_sequence": tool_sequence,
        "primary_tool_success": primary_success,
        "fallback_triggered": fallback_triggered,
        "final_success": final_success
    }
    
    status = "✅" if final_success else "❌"
    print(f"  {status} Primary: {primary_success}, Fallback: {fallback_triggered}, Final: {final_success}")
    
    return result


def main():
    """Main execution function"""
    print("=" * 70)
    print("Phase 3 Round 3 - Host Environment Testing")
    print(f"Start Time: {datetime.now().isoformat()}")
    print("=" * 70)
    
    # Load test cases
    print(f"\nLoading test cases from: {TEST_DATA_PATH}")
    with open(TEST_DATA_PATH) as f:
        test_data = json.load(f)
    
    test_cases = test_data.get("test_cases", [])
    print(f"Total test cases: {len(test_cases)}")
    
    # Run tests
    results = []
    stats = {
        "total": len(test_cases),
        "by_scenario": {},
        "by_tool": {}
    }
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n[{i}/{len(test_cases)}] ", end="")
        result = run_test(test_case)
        results.append(result)
        
        # Update stats
        scenario = test_case["scenario"]
        if scenario not in stats["by_scenario"]:
            stats["by_scenario"][scenario] = {"total": 0, "success": 0, "fallbacks": 0}
        stats["by_scenario"][scenario]["total"] += 1
        if result["final_success"]:
            stats["by_scenario"][scenario]["success"] += 1
        if result["fallback_triggered"]:
            stats["by_scenario"][scenario]["fallbacks"] += 1
    
    # Calculate final statistics
    print("\n" + "=" * 70)
    print("FINAL STATISTICS")
    print("=" * 70)
    
    total_success = sum(1 for r in results if r["final_success"])
    total_fallbacks = sum(1 for r in results if r["fallback_triggered"])
    
    print(f"\nOverall:")
    print(f"  Total: {len(results)}")
    print(f"  Success: {total_success}")
    print(f"  Success Rate: {total_success/len(results)*100:.1f}%")
    print(f"  Fallbacks Triggered: {total_fallbacks}")
    
    print(f"\nBy Scenario:")
    for scenario, data in sorted(stats["by_scenario"].items()):
        rate = data["success"] / data["total"] * 100 if data["total"] > 0 else 0
        print(f"  {scenario:12s}: {data['success']:2d}/{data['total']:2d} ({rate:5.1f}%) - Fallbacks: {data['fallbacks']}")
    
    # Save results
    output = {
        "metadata": {
            "version": "3.0",
            "timestamp": TIMESTAMP,
            "total_tests": len(results),
            "successful": total_success,
            "success_rate": total_success / len(results) if results else 0,
            "fallbacks_triggered": total_fallbacks,
            "by_scenario": {
                scenario: {
                    "total": data["total"],
                    "success": data["success"],
                    "success_rate": data["success"] / data["total"] if data["total"] > 0 else 0
                }
                for scenario, data in stats["by_scenario"].items()
            }
        },
        "results": results
    }
    
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Results saved to: {OUTPUT_FILE}")
    print(f"End Time: {datetime.now().isoformat()}")
    
    return output


if __name__ == "__main__":
    main()