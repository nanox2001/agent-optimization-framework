# OpenClaw 网页抓取功能架构分析

> 分析日期：2026-04-15  
> 文档版本：1.0  
> 分析范围：OpenClaw 网页抓取工具链、执行流程、性能特征

---

## 一、功能组件清单

### 1.1 核心抓取工具

| 工具名称 | 类型 | 功能描述 | 参数配置 | 适用场景 | 成功率（观察值） |
|---------|------|---------|---------|---------|----------------|
| **web_fetch** | 内置工具 | 基础HTTP抓取，支持静态页面获取 | `url`, `extractMode` ("markdown"/"html"/"text"), `maxChars` | 简单静态页面、GitHub等 | github.com: 92.1%, weixin.qq.com: 0% |
| **browser** | Chrome扩展Relay | 通过Chrome浏览器获取渲染后内容 | `action` ("snapshot"/"navigate"), `profile` ("chrome") | 动态内容、反爬站点、微信文章 | weixin.qq.com: 85.7% |
| **Jina Reader** | 外部API | 智能正文提取，LLM友好格式 | URL via `https://r.jina.ai/{url}` | 复杂布局、需要正文提取 | 观察约78.9% |
| **Scrapling** | Python库 | 动态渲染、StealthyFetcher | `Fetcher.get()`, `StealthyFetcher.fetch()` | JS渲染页面、需代理场景 | 依赖配置，反爬强 |

### 1.2 搜索工具（发现阶段）

| 工具名称 | 提供商 | 功能描述 | 配置位置 | 典型耗时 |
|---------|--------|---------|---------|---------|
| **web_search** | Tavily | 搜索+LLM总结 | `tools.web.search.provider: "tavily"` | ~500ms |
| **brave** | Brave Search | 隐私搜索 | plugins配置 | ~300ms |
| **google** | Google Search | 免费搜索 | plugins.google.config.webSearch | ~200ms |

### 1.3 平台访问工具

| 工具名称 | 功能描述 | 典型源 | 成功率（观察值） |
|---------|---------|--------|----------------|
| **OpenCLI** | 多平台热点数据获取 | HackerNews, Reddit, 微博 | 96.0% (120/125) |
| **info-collector** | 统一调度入口 | 多源聚合 | 场景依赖 |

### 1.4 相关 Skill 抓取能力

| Skill名称 | 抓取能力 | 依赖工具 | 触发条件 |
|---------|---------|---------|---------|
| **wechat-article-extractor** | 微信公众号文章提取 | web_fetch, web_search, exec, browser (可选) | mp.weixin.qq.com URL |
| **info-collector** | 信息收集统一调度 | 全工具链 | 关键词触发 |
| **search-suite** | 搜索执行 | web_search | 搜索相关 |

---

## 二、执行流程图

### 2.1 完整抓取执行流程

```
用户请求 (URL/关键词)
    │
    ▼
┌─────────────────────────────────────┐
│         场景识别 (Scene Detection)      │
│  ┌─────────────────────────────────┐  │
│  │ 探索 │ 热点 │ 阅读 │ 监控 │ 深研 │ 验证 │  │
│  └─────────────────────────────────┘  │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│      首选工具选择 (Primary Tool Selection) │
│   基于场景历史成功率优化选择              │
└─────────────────────────────────────┘
    │
    ├─── 路径1: 直接抓取 ───────────────────┐
    │                                         ▼
    │                              ┌──────────────────┐
    │                              │   web_fetch    │
    │                              │   (200-500ms)   │
    │                              └──────────────────┘
    │                                         │
    │                              success? ──┼──► 内容提取 ► 输出
    │                                         │ fail
    │                                         ▼
    ├─── 路径2: 智能抓取 ───────────────────┐
    │                                         ▼
    │                              ┌──────────────────┐
    │                              │   Jina Reader  │
    │                              │   (500-2000ms)  │
    │                              └──────────────────┘
    │                                         │
    │                              success? ──┼──► 内容提取 ► 输出
    │                                         │ fail
    │                                         ▼
    ├─── 路径3: 动态渲染 ───────────────────┐
    │                                         ▼
    │                              ┌──────────────────┐
    │                              │   Scrapling    │
    │                              │   (3000ms+)     │
    │                              │   (需Python环境) │
    │                              └──────────────────┘
    │                                         │
    │                              success? ──┼──► 内容提取 ► 输出
    │                                         │ fail
    │                                         ▼
    └─── 路径4: 浏览器兜底 (LAST TRY) ───────┐
                                              ▼
                                   ┌──────────────────┐
                                   │  browser Relay   │
                                   │  (4000-6000ms)   │
                                   │  (需Chrome扩展)   │
                                   └──────────────────┘
                                              │
                                   success? ──┼──► 内容提取 ► 输出
                                              │ fail
                                              ▼
                                   ┌──────────────────┐
                                   │   请求用户介入    │
                                   │  (手动验证后重试) │
                                   └──────────────────┘
```

### 2.2 微信文章特殊流程

```
mp.weixin.qq.com URL 输入
    │
    ▼
Step 1: web_fetch 直接尝试
    │
    ├── 成功 (rawLength > 500) ──► Step 4B 格式化输出
    │
    └── 失败 (403/空内容) ────────► Step 2
    │
    ▼
Step 2: 提取文章元数据 (标题/作者)
    │
    ▼
Step 3: web_search 搜索镜像站点
    │
    ├── 找到镜像 (53ai.com, ofweek.com等) ──► Step 4A
    │
    └── 无镜像 ─────────────────────────────► Step 5 (Browser Relay)
    │
    ▼
Step 4A: curl下载 + Python脚本提取
    │
    ▼
Step 4B: Markdown格式化
    │
    ▼
Step 5: 验证输出质量 (长度/内容完整性)
    │
    └── 质量不足 ──► 尝试下一镜像
```

### 2.3 错误处理与重试机制

```
┌────────────────────────────────────────────────────────────┐
│                    错误处理层级结构                          │
├────────────────────────────────────────────────────────────┤
│ Level 1: 同类型工具重试                                      │
│   - web_fetch 失败 → 换 Jina                                 │
│   - Tavily 失败 → 换 Brave → 换 Google                        │
│                                                            │
│ Level 2: 跨类型Fallback                                      │
│   - 抓取失败 → OpenCLI平台访问                                │
│   - 搜索失败 → 浏览器直接访问                                 │
│                                                            │
│ Level 3: LAST TRY (最终兜底)                                  │
│   - 尝试所有可用工具                                         │
│   - 记录所有失败原因                                         │
│   - browser作为最终fallback                                  │
│                                                            │
│ Level 4: 用户介入                                            │
│   - 请求用户手动验证                                         │
│   - browser snapshot读取验证后页面                             │
└────────────────────────────────────────────────────────────┘
```

---

## 三、数据流分析

### 3.1 输入数据结构

```json
{
  "input": {
    "type": "url|keywords|scenario",
    "url": "https://example.com/article",
    "keywords": ["AI", "Agent"],
    "scenario": "阅读|探索|热点|监控",
    "options": {
      "extractMode": "markdown|html|text",
      "maxChars": 50000,
      "fallbackEnabled": true,
      "timeout": 30000
    }
  }
}
```

### 3.2 处理阶段数据转换

| 阶段 | 输入 | 处理 | 输出 |
|-----|------|------|------|
| **抓取** | URL | HTTP请求/浏览器渲染 | Raw HTML/Content |
| **提取** | Raw HTML | HTML→Markdown转换 | Clean Markdown |
| **验证** | Markdown | 内容质量检查 (长度/结构) | 质量评分 |
| **Fallback** | 失败记录 | 工具切换决策 | 下一个工具 |
| **输出** | 合格内容 | 格式化/元数据添加 | 最终结果 |

### 3.3 输出数据结构

```json
{
  "output": {
    "content": "# Article Title\n\nFull markdown content...",
    "metadata": {
      "source": "web_fetch|jina|browser",
      "title": "Article Title",
      "url": "https://example.com/article",
      "fetchTime": "2026-04-15T08:01:00Z",
      "charCount": 15234,
      "imageCount": 5
    },
    "stats": {
      "fallbackCount": 2,
      "failedTools": ["web_fetch", "jina"],
      "successTool": "browser",
      "durationMs": 5200
    }
  }
}
```

### 3.4 统计记录数据流

```json
{
  "record": {
    "timestamp": "2026-03-29T18:11:46",
    "scenario": "阅读",
    "target": "https://weixin.qq.com/xxx",
    "domain": "weixin.qq.com",
    "tool": "browser",
    "success": true,
    "duration_ms": 5200,
    "error": null,
    "fallback_count": 2,
    "failed_tools": ["web_fetch", "jina"]
  }
}
```

统计聚合数据：

```json
{
  "stats": {
    "by_domain": {
      "weixin.qq.com": {
        "attempts": 4,
        "success_by_tool": {"browser": 2}
      },
      "github.com": {
        "attempts": 3,
        "success_by_tool": {"web_fetch": 2, "jina": 1}
      }
    },
    "by_tool": {
      "browser": {"success": 2, "failure": 0, "avg_time_ms": 5000},
      "web_fetch": {"success": 2, "failure": 1, "avg_time_ms": 260},
      "jina": {"success": 1, "failure": 1, "avg_time_ms": 2750},
      "opencli": {"success": 4, "failure": 1, "avg_time_ms": 142}
    }
  }
}
```

---

## 四、性能特征总结

### 4.1 抓取速度（观察值）

| 工具 | 平均耗时 | 场景特点 |
|------|---------|---------|
| **opencli** | 142ms | 平台直连，最快 |
| **web_fetch** | 260ms | 简单HTTP请求 |
| **jina** | 800-2750ms | 外部API+内容提取 |
| **browser** | 4000-5200ms | 浏览器渲染+通信 |

### 4.2 成功率统计（观察数据）

基于 `info-collector-stats.json` 的统计：

| 工具 | 成功次数 | 失败次数 | 成功率 |
|------|---------|---------|-------|
| opencli | 120 | 5 | **96.0%** |
| jina | 38 | 8 | **78.9%** |
| web_fetch | 38 | 25 | **60.3%** |
| browser | 4 | 0 | **100%** (作为兜底) |

**按域名分析：**

| 域名 | 最佳工具 | 成功率 | 备注 |
|------|---------|--------|------|
| weixin.qq.com | browser | 85.7% | 微信限制严格 |
| github.com | web_fetch | 92.1% | 静态页面友好 |
| hackernews | opencli | 98.2% | 平台API稳定 |

### 4.3 常见失败原因

| 失败类型 | 典型错误 | 触发场景 | 解决方案 |
|---------|---------|---------|---------|
| **403 Forbidden** | 反爬拦截 | 微信/付费内容 | 换镜像/Browser |
| **timeout** | 请求超时 | Jina/Scrapling | 增加超时/换工具 |
| **rate limit** | API配额 | 搜索/开放平台 | 等待/换平台 |
| **空内容** | JS渲染未执行 | 动态页面 | browser/Scrapling |
| **环境异常** | 验证码拦截 | 微信/反爬站点 | Browser Relay |

### 4.4 Fallback频率

根据观察：
- 大约 **30-40%** 的请求需要至少一次Fallback
- 微信文章场景：80%+ 需要Browser兜底
- 普通网页：15-20% 需要Fallback

---

## 五、优化机会分析

### 5.1 潜在优化点（至少3个）

#### 优化点 1：智能域名预选择

**现状**：所有请求按固定顺序尝试工具
**优化方向**：
- 基于历史数据自动学习每个域名的最佳工具
- 实现域名特征识别（反爬强度、动态内容检测）
- 预期提升：减少30%的Fallback次数

#### 优化点 2：并行预抓取策略

**现状**：串行尝试工具，失败才换下一个
**优化方向**：
- 对高风险URL（已知的反爬站点）并行发送多个请求
- web_fetch + Jina + Scrapling 同时发起
- 优先返回最快成功的完整结果
- 预期提升：关键场景降低50%延迟

#### 优化点 3：缓存与镜像发现自动化

**现状**：微信等站点依赖手动搜索镜像
**优化方向**：
- 建立热门站点的镜像URL缓存池
- 预抓取并索引可能需要镜像的文章
- 自动化镜像发现和验证流程
- 预期提升：微信等困难场景80%自动化

#### 优化点 4：浏览器实例池复用

**现状**：每次browser请求可能新建浏览器实例
**优化方向**：
- 维护浏览器实例池（预热N个实例）
- 复用已登录/已验证的会话状态
- 预期提升：browser工具降低60%延迟

#### 优化点 5：增量抓取与智能分页

**现状**：长文章一次性获取
**优化方向**：
- 对超长页面智能分块抓取
- 实现增量内容检测（只抓取变化部分）
- 预期提升：大文件场景降低50%带宽和时间

### 5.2 优化优先级建议

| 优先级 | 优化项 | 预期收益 | 实现难度 |
|-------|-------|---------|---------|
| **高** | 智能域名预选择 | ★★★★☆ | 中 |
| **高** | 浏览器实例池 | ★★★★☆ | 高 |
| **中** | 并行预抓取 | ★★★☆☆ | 中 |
| **中** | 缓存与镜像自动化 | ★★★☆☆ | 低 |
| **低** | 增量抓取 | ★★☆☆☆ | 高 |

### 5.3 测试设计建议

基于以上分析，建议优化测试覆盖以下场景：

1. **基础场景**（覆盖率目标：95%）
   - 静态HTML页面
   - GitHub仓库页面
   - 常见新闻网站

2. **困难场景**（覆盖率目标：80%）
   - 微信公众号文章
   - 需要登录的内容
   - 验证码保护页面

3. **边界场景**（覆盖率目标：60%）
   - 超大页面（>1MB）
   - 重定向链
   - 二进制内容

---

## 附录：相关文件路径

| 文件 | 路径 |
|------|------|
| 抓取策略文档 | `/home/jerry/.openclaw/workspace/docs/web-scraping-strategy.md` |
| 信息收集Skill | `/home/jerry/.openclaw/workspace/skills/info-collector/SKILL.md` |
| 微信文章提取Skill | `/home/jerry/.openclaw/skills/openclaw-skills-wechat-article-extractor/SKILL.md` |
| 性能统计 | `/home/jerry/.openclaw/workspace/jerry/logs/info-collector-stats.json` |
| 每日抓取数据 | `/home/jerry/.openclaw/workspace/jerry/inbox/daily-fetch/` |
| OpenClaw配置 | `/home/jerry/.openclaw/openclaw.json` |

---

*文档结束*
    "