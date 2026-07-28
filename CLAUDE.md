# title2doi — 标题DOI批量检索工具

USTC Lib · Han · 查收查引辅助工具

## 项目概述

纯静态 SPA，GitHub Pages 部署。批量从文章标题检索 DOI。
输入：粘贴文本 / 上传 Word/Excel → 智能解析 → Crossref 查 DOI → 复制导出。

## 架构

```
根目录（GitHub Pages 部署）
├── index.html           # 完整 SPA（HTML + CSS + vanilla JS）
├── config.example.js    # 配置模板（部署时 Actions 从 Secrets 注入 config.js）
├── config.js            # 运行时配置（.gitignore，由 Actions 生成）
└── .github/workflows/
    └── pages.yml        # 自动部署到 GitHub Pages

server/                  # Python Flask 版（备选，本地/内网部署）
├── app.py · src/ · templates/ · requirements.txt
```

## 核心功能

- **智能解析 (LLM)**：换行切分 → 短行合并 → 编号批量送 LLM → 按编号解析返回
- **智能检测**：输入 ≥70% 行为干净标题时自动跳过 LLM，零 token 消耗
- **基础解析**：正则提取 + Word/Excel 文件解析（SheetJS + Mammoth.js）
- **DOI 查询**：Crossref API（免费），difflib 模糊匹配
- **置信度**：≥90% 高（可用），<90% 低（需核实），导出仅含高置信度
- **交互**：Ctrl+Enter 解析、输入暂存、统计点击筛选、单条 DOI 复制、取消查询

## LLM 配置

三层优先级：前端高级设置 > GitHub Secrets (config.js) > 代码默认值

| 配置项 | 默认值 |
|--------|--------|
| API 地址 | `https://api.deepseek.com/v1/chat/completions` |
| 模型 | `deepseek-chat` |

## 部署

GitHub Pages：配置三个 Repository Secrets (`LLM_API_BASE`, `LLM_API_KEY`, `LLM_MODEL`)，push 自动部署。

本地：`cd server && pip install -r requirements.txt && python run.py`

## 技术栈

- 纯静态 SPA（HTML + CSS + vanilla JS），零前端依赖
- CDN：SheetJS（Excel 解析/导出）、Mammoth.js（Word 解析）
- LLM：OpenAI 兼容 API · DOI：Crossref API

## 验证

```bash
node --check <(python -c "..." )  # 提取 JS 并检查语法
python -m http.server 8080        # 本地预览
```
