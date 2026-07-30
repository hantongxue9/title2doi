# title2doi · 标题DOI批量检索

USTC Lib · Han · 查收查引辅助工具

输入文章标题（粘贴或上传 Word/Excel），AI 自动提取标题并批量查询 DOI。

## 使用

访问 [GitHub Pages](https://hantongxue9.github.io/title2doi/)，无需安装。

1. 粘贴标题或上传文件 →「解析标题」（或 Ctrl+Enter）
2. 确认标题列表（可编辑增删）→「批量查询 DOI」
3. 查看结果，复制高置信度 DOI 或下载 Excel

## 解析模式

| 模式 | 适用场景 |
|------|---------|
| 智能解析 (AI) | 作者、标题、期刊混排的引用文本。自动按换行切分后送 LLM 提取标题 |
| 基础解析 | 每行一个标题的规范文本。上传 Word/Excel 使用此模式 |

输入已是干净标题时自动跳过 AI，零 token 消耗。

## 置信度

DOI 匹配按标题文本相似度分为两档：

| 等级 | 阈值 | 说明 |
|------|------|------|
| 高 | ≥ 90% | 标题完全一致或仅标点差异，可直接使用 |
| 低 | < 90% | 需人工核实。可点击 ↻ 单条重试或批量重试 |

导出仅包含高置信度结果。中文匹配使用二元组算法，比英文更严格（封顶 50 分）。英文匹配忽略大小写及 a/an/the 停用词。遇到预印本（SSRN/arXiv/bioRxiv 等）时自动跳过，优先用正式发表版本。

## 部署

### GitHub Pages（当前）

仓库配置了 GitHub Actions，push master 自动部署。需设置三个 Secrets：

| Secret | 示例 |
|--------|------|
| `LLM_API_BASE` | `https://api.deepseek.com/v1/chat/completions` |
| `LLM_API_KEY` | `sk-...` |
| `LLM_MODEL` | `deepseek-v4-flash` |

用户可在页面高级设置中覆盖默认配置。

### 本地 Python（备选）

```bash
cd server
pip install -r requirements.txt
cp .env.example .env
python run.py
```

## 测试

```bash
# 单元测试（30 项，覆盖核心函数）
python tests/run.py

# 手动测试清单
cat tests/CHECKLIST.md
```

CI 会在每次 push 时自动运行单元测试。

## 技术栈

纯静态 SPA · Crossref API · DeepSeek LLM · SheetJS · Mammoth.js
