# title2doi · 标题DOI批量检索

USTC Lib · Han · 查收查引辅助工具

纯静态 SPA，GitHub Pages 部署。输入文章标题（粘贴或上传文件）→ AI 提取标题 → Crossref 查 DOI → 复制导出。

## 项目结构

```
├── index.html             # 完整 SPA（HTML + CSS + vanilla JS，约 1080 行）
├── config.example.js      # 部署时 Actions 从 Secrets 注入 config.js
├── .github/workflows/     # GitHub Actions 自动部署
└── server/                # Python Flask 备选版（本地/内网）
```

## 核心功能

- **智能解析**：换行切分 → 短行合并 → 编号批量送 LLM → 按编号解析
- **智能检测**：≥70% 行为干净标题时跳过 LLM，零 token
- **基础解析**：正则 + Word/Excel（SheetJS + Mammoth.js）
- **DOI 查询**：Crossref API，词级匹配 + LCS 词序约束
- **置信度**：完全一致 100，仅标点差异 98，其他 ≤70（中文二元组 ≤50）

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

默认：`https://api.deepseek.com/v1/chat/completions` / `deepseek-chat`

## 验证

```bash
node --check <extracted_js>    # JS 语法
python -m http.server 8080     # 本地预览
```
