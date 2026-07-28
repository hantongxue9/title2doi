# title2doi — 标题DOI批量检索工具

中国科学技术大学图书馆 · 查收查引辅助工具

批量从文章标题检索 DOI。支持粘贴文本和上传 Word/Excel 文件，内置 AI 智能解析和规则解析双引擎。

## 快速开始

访问 [GitHub Pages](https://hantongxue9.github.io/title2doi/) 直接使用，无需安装。

1. 粘贴标题或上传文件 → 解析标题（或 Ctrl+Enter）
2. 确认标题列表（可编辑增删）→ 批量查询 DOI
3. 复制高置信度结果或下载 Excel

快捷键：输入框中 **Ctrl+Enter** 快速解析。输入内容自动暂存，刷新不丢失。

## 解析模式

| 模式 | 适用场景 |
|------|---------|
| **智能解析 (AI)** | 作者、标题、期刊混排的杂乱引用文本。自动按换行切分条目，AI 提取标题。输入已是干净标题时自动跳过 AI，秒出结果 |
| **基础解析** | 每行一个标题的规范文本。上传 Word/Excel 使用此模式（自动识别标题列） |

## 置信度

DOI 匹配结果按置信度分为两档（基于 Crossref 返回标题与原始标题的文本相似度）：

| 等级 | 阈值 | 说明 |
|------|------|------|
| 高置信度 | ≥ 90% | 匹配准确，可直接使用 |
| 低置信度 | < 90% | 可能不准确，建议人工核实 |

导出功能仅包含高置信度结果。

## 管理员部署

### GitHub Pages（推荐）

仓库已配置 GitHub Actions 自动部署。在 Settings → Secrets and variables → Actions 中添加三个 Secret：

| Secret | 示例值 |
|--------|--------|
| `LLM_API_BASE` | `https://api.deepseek.com/v1/chat/completions` |
| `LLM_API_KEY` | `sk-...` |
| `LLM_MODEL` | `deepseek-chat` |

每次 push master 自动部署。用户可通过页面右上角「高级设置」覆盖默认 API 配置。

### 本地 Python 服务器（备选）

```bash
cd server
pip install -r requirements.txt
cp .env.example .env   # 编辑填入 API Key
python run.py
```

## 技术栈

- 纯静态 SPA（HTML + CSS + vanilla JS）
- LLM：OpenAI 兼容 API（默认 DeepSeek）
- DOI 查询：Crossref API（免费，无需 Key）
- 文档解析：SheetJS（Excel）+ Mammoth.js（Word）
