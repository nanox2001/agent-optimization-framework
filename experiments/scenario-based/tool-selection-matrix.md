# 工具选择决策矩阵

## 快速参考表

| 场景类型 | 示例 | 首选 | 备选 | 成功预期 | 关键限制 |
|----------|------|------|------|----------|----------|
| 📝 **Static** | 博客、文档 | `web_fetch` | `browser` | 95% | 无 |
| 🛡️ **Anti-Scrape** | Medium、Reddit | `browser` | - | 85% | 需socket目录 |
| 📱 **Platform** | B站、知乎 | `opencli` | `browser` | 80% | 需Node环境 |
| ⚛️ **SPA** | React/Vue应用 | `browser` | `web_fetch`* | 70% | *SSR检测 |
| 🔍 **Search** | AI搜索 | `search` | `browser` | 90% | API配额 |
| ⚡ **Realtime** | 天气、API | `web_fetch` | `opencli` | 90% | 无 |

## 决策流程图

```
                    ┌─────────────────┐
                    │   收到URL/查询   │
                    └────────┬────────┘
                             ▼
                    ┌─────────────────┐
                    │ 是否搜索关键词?  │
                    └────────┬────────┘
                         是/│\否
                           / │ \
                          ▼  │  ▼
                    ┌────────┴────────┐
                    │  是否已知平台?   │
                    └────────┬────────┘
                         是/│\否
                           / │ \
                          ▼  │  ▼
                    ┌────────┴────────┐
                    │ 是否反爬域名?    │
                    └────────┬────────┘
                         是/│\否
                           / │ \
                          ▼  │  ▼
                    ┌────────┴────────┐
                    │ 是否SPA特征?    │
                    └────────┬────────┘
                         是/│\否
                           / │ \
                          ▼  │  ▼
                       ┌─────┴─────┐
                       │ web_fetch │
                       └───────────┘
```

## 域名/平台快速匹配

### 必须使用 Browser
```
medium.com      → browser (反爬)
reddit.com      → browser (反爬)
linkedin.com    → browser (反爬)
twitter.com     → browser (JS渲染)
x.com           → browser (JS渲染)
instagram.com   → browser (反爬)
```

### 优先使用 opencli
```
bilibili.com    → opencli bilibili
zhihu.com       → opencli zhihu
weibo.com       → opencli weibo
xiaohongshu.com → opencli xiaohongshu
```

### web_fetch 即可
```
github.com      → web_fetch (服务端渲染)
docs.*          → web_fetch (文档站点)
*.md            → web_fetch (Markdown)
api.*           → web_fetch (API端点)
wttr.in         → web_fetch (天气API)
```

## 成功率对比

```
成功率
100% ┤
 90% ┤███████████ static (95%)
     │███████████ search (90%)
     │███████████ realtime (90%)
 80% ┤█████████   platform (80%)
 70% ┤███████     anti_scrape (85%)*
     │███████     spa (70%)*
 50% ┤
  0% ┼───────────────
        理论值  *非sandbox环境

Round 2 理论预期: 75%+
Round 2 实际(Sandbox): 36%
差距原因: 环境限制 (socket目录、Node缺失)
```

## 工具执行参数模板

### web_fetch
```python
{
  "timeout": 15,
  "headers": {"User-Agent": "Mozilla/5.0..."},
  "retry": 2
}
```

### browser
```bash
agent-browser --session {name} open {url} && \
  agent-browser --session {name} wait --load networkidle && \
  agent-browser --session {name} get text body && \
  agent-browser --session {name} close
```

### opencli
```bash
opencli {platform} {action} -f json
# 需要: Node.js >= 18
```

### search
```bash
python3 search.py "{query}"
# 需要: 配置Tavily/Serper API key
```

## 错误处理策略

| 错误类型 | 处理方式 | 重试 |
|----------|----------|------|
| Timeout | 切换备选工具 | 1次 |
| 403/429 | 标记为anti_scrape | 用browser |
| 404 | 失败 | 不重试 |
| JS渲染失败 | SSR检测 | web_fetch |
| Socket错误 | 环境检查 | 修复后重试 |

---

*基于 Phase 3 Round 2 实验结果生成*
*配置文件: configs/tool-scenario-mapping.json*
