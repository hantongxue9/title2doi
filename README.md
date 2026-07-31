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

导出仅包含高置信度结果。中文匹配使用二元组算法，比英文更严格（封顶 50 分）。英文匹配忽略大小写及 a/an/the 停用词。

**DOI 修正规则**（命中时会在结果「来源」列标注）：
- 预印本（SSRN/arXiv/bioRxiv 等）自动跳过，优先正式发表版本
- 去除补充材料后缀（`.S001` 等）
- 德文版转国际版（`ange.xxx` → `anie.xxx`，Angewandte Chemie，年份 ≥1956）

## 部署

### GitHub Pages（当前）

仓库配置了 GitHub Actions，push master 自动部署。部署时会从 GitHub Actions Secrets 生成 `config.js`，作为页面默认 LLM 配置：

| Secret | 示例 |
|--------|------|
| `LLM_API_BASE` | `https://api.deepseek.com/v1/chat/completions` |
| `LLM_API_KEY` | `sk-...` |
| `LLM_MODEL` | `deepseek-v4-flash` |

如果需要更换线上默认 Key，请到 GitHub 仓库的 `Settings` → `Secrets and variables` → `Actions` 修改 `LLM_API_KEY`，然后重新触发 Pages 部署（push master 或手动运行 workflow）。

注意：GitHub Pages 是公开静态站点，部署产物中的 `config.js` 可以被访问者查看。当前方案的优点是打开即用；代价是默认 Key 属于前端公开配置。页面「高级设置」可覆盖默认配置，适合默认 Key 失效或用户希望使用自己的 Key 时使用。

### 本地 Python（备选）

```bash
cd server
pip install -r requirements.txt
cp .env.example .env
python run.py
```

本地后端可以在 `server/.env` 中配置：

| 变量 | 示例 |
|------|------|
| `LLM_API_BASE` | `https://api.deepseek.com/v1/chat/completions` |
| `LLM_API_KEY` | `sk-...` |
| `LLM_MODEL` | `deepseek-v4-flash` |

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
