# Phase 3: 场景化工具组合优化实验

## 目标

通过场景化测试，建立"场景→工具"映射表和 Fallback 策略，优化通用搜索抓取效率。

---

## 工具全景

| 工具 | 能力 | 适用场景 | 额度/成本 |
|------|------|---------|----------|
| **Search API (Tavily)** | 搜索+LLM总结 | 通用搜索、技术问题 | 1 credit/次 |
| **Search API (Brave)** | 搜索结果 | 新闻、实时信息 | 1 credit/次 |
| **Search API (Google)** | 搜索结果 | 备用 | 免费 |
| **opencli** | 平台CLI | B站/知乎/微博/Twitter等 | 免费 |
| **Browser (Playwright)** | 浏览器控制 | 反爬、JS渲染、登录页面 | 资源密集 |
| **web_fetch** | HTTP抓取 | 简单静态页面 | 免费 |
| **web_search** | Gemini+搜索 | AI总结搜索 | 模型成本 |

---

## 测试场景

### S1: 简单静态页
- **典型**: 博客文章、新闻网站
- **测试URL**: 
  - https://example.com (简单)
  - https://news.ycombinator.com/item?id=123 (HN评论)
- **预期工具**: web_fetch → Search API fallback
- **评估**: 成功率、内容完整度

### S2: 反爬页面
- **典型**: Medium、Reddit、某些论坛
- **测试URL**:
  - https://medium.com/@user/article
  - https://www.reddit.com/r/programming/comments/xxx
- **预期工具**: Browser → web_fetch fallback
- **评估**: 403比例、Browser成功率

### S3: 平台专属内容
- **典型**: B站、知乎、微博、小红书
- **测试URL**:
  - B站视频: https://bilibili.com/video/BVxxx
  - 知乎问题: https://zhihu.com/question/xxx
  - 微博用户: https://weibo.com/u/xxx
- **预期工具**: opencli → Browser fallback
- **评估**: opencli命令覆盖、数据结构化程度

### S4: JS渲染页面 (SPA)
- **典型**: React/Vue应用、动态加载内容
- **测试URL**:
  - https://spa-example.com
  - 动态行情页
- **预期工具**: Browser (等待渲染)
- **评估**: 等待时间、内容完整度

### S5: 登录内容
- **典型**: 知乎私信、微博私信、论坛消息
- **测试URL**:
  - https://zhihu.com/messages
  - https://weibo.com/messages
- **预期工具**: opencli (复用登录) → Browser
- **评估**: 登录态复用成功率

### S6: 实时数据
- **典型**: 股价、天气、热搜
- **测试URL**:
  - 天气: wttr.in/Sydney
  - B站热搜: opencli bilibili hot
  - 知乎热搜: opencli zhihu hot
- **预期工具**: Search API → opencli
- **评估**: 时效性、数据准确度

---

## 数据记录格式

### 单次抓取记录
```json
{
  "test_id": "S3_001",
  "scenario": "platform_content",
  "url": "https://bilibili.com/video/BVxxx",
  "timestamp": "2026-04-17T12:00:00Z",
  "tool_sequence": [
    {
      "tool": "opencli",
      "command": "opencli bilibili video --url xxx",
      "success": true,
      "duration_ms": 850,
      "content_quality": 5,
      "notes": "直接获取视频信息，无需渲染"
    }
  ],
  "primary_tool_success": true,
  "fallback_triggered": false,
  "final_success": true,
  "content_extracted": {
    "title": "视频标题",
    "author": "作者",
    "views": 12345,
    "likes": 500
  },
  "issues": [],
  "recommendation": "opencli 为首选，速度快数据结构化"
}
```

### 场景汇总统计
```json
{
  "scenario": "platform_content",
  "total_tests": 50,
  "by_tool": {
    "opencli": {
      "attempts": 40,
      "successes": 38,
      "success_rate": 0.95,
      "avg_duration_ms": 920,
      "avg_quality": 4.8
    },
    "browser": {
      "attempts": 10,
      "successes": 8,
      "success_rate": 0.80,
      "avg_duration_ms": 3500,
      "avg_quality": 4.2
    }
  },
  "primary_tool_correct_rate": 0.85,
  "recommendation": {
    "primary": "opencli",
    "fallback": "browser",
    "notes": "opencli覆盖主流平台，浏览器补充特殊页面"
  }
}
```

---

## 实验执行计划

### Round 1: 基础场景验证
- 每个场景 5 个测试URL
- 记录首选工具成功率
- 标记失败原因

### Round 2-5: 扩展测试
- 增加更多URL变体
- 测试 Fallback 效果
- 收集异常情况

### 最终输出

1. **场景→工具映射表**: `scenario-tool-mapping.json`
2. **工具效果统计**: `tool-effectiveness-stats.json`
3. **Fallback策略**: `fallback-strategy.json`
4. **决策树**: 自动选择工具的逻辑

---

## 文件结构

```
experiments/
├── scenario-based/
│   ├── round1/
│   │   ├── S1-static-pages.json
│   │   ├── S2-anti-scrape.json
│   │   ├── S3-platform.json
│   │   ├── S4-spa.json
│   │   ├── S5-login.json
│   │   └── S6-realtime.json
│   ├── round2-5/
│   ├── aggregated-stats.json
│   └── scenario-tool-mapping.json
```

---

## 下一步

1. 创建测试执行脚本
2. 定义具体测试URL清单
3. 开始 Round 1 执行
4. 收集数据并分析

---

*Created: 2026-04-16*
*Status: 设计完成，待执行*