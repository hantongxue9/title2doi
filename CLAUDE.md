# title2doi · 标题DOI批量检索

USTC Lib · Han · 查收查引辅助工具

纯静态 SPA，GitHub Pages 部署。输入文章标题（粘贴或上传文件）→ AI 提取标题 → Crossref 查 DOI → 复制导出。

## 项目结构

```
├── index.html             # 完整 SPA（唯一前端，Flask 也直接 serve 它）
├── config.example.js      # 部署时 Actions 从 Secrets 注入 config.js
├── .github/workflows/     # pages.yml 自动部署 + test.yml 自动测试
├── tests/                 # run.py 单元测试 + CHECKLIST.md 手动清单
└── server/                # Python Flask 备选版（serve 根目录 index.html）
```

## 核心功能

- **智能解析**：换行切分 → 短行合并 → 编号批量送 LLM → 按编号解析
- **智能检测**：≥70% 行为干净标题时跳过 LLM，零 token
- **基础解析**：正则 + Word/Excel（SheetJS + Mammoth.js）
- **DOI 查询**：Crossref API，词级匹配 + LCS 词序约束；会话级缓存；自动重试 1 次
- **DOI 修正规则**（命中时来源列标注）：预印本跳过、去 `.S001` 后缀、`ange→anie` 德文版转国际版（年份≥1956）
- **置信度**：完全一致 100，仅标点差异 98，去停用词 97，其他 ≤70（中文二元组 ≤50）

## 关键函数（index.html）

| 函数 | 用途 |
|------|------|
| `doParse()` | 解析入口，路由：文件提取→文本检测→LLM/正则 |
| `llmParse()` | 调 LLM API，groupEntries→buildNumberedPrompt→parseNumberedResponse |
| `lookupDOI()` | Crossref 查询，自动重试 1 次 |
| `matchScore()` | 中英文分治：中文二元组 Jaccard，英文词级 F1+LCS |
| `renderResults()` | 渲染统计卡片 + 表格 + DOI 输出 |
| `retrySingleQuery()` | 单条重试，≥90 自动入高置信度 |
| `batchRetry()` | 批量重试，逐行转圈动画 |

## 配置

三层优先级：前端高级设置 > GitHub Secrets > 代码默认

默认：`https://api.deepseek.com/v1/chat/completions` / `deepseek-v4-flash`

## 验证

```bash
python tests/run.py            # 单元测试（40 项，CI 自动跑）
cat tests/CHECKLIST.md         # 手动测试清单
python -m http.server 8080     # 本地预览
```

## 红线

- 前端是唯一来源，**不要**再建 server/templates 副本
- 改 DOI 匹配逻辑后必须跑 `tests/run.py` 并补断言
- GitHub Pages 公开站点：`config.js` 里的 LLM Key 会被访问者看到（已知问题，方案 B 暂缓）
