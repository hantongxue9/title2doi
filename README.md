# title2doi — 标题DOI批量检索工具

中国科学技术大学图书馆 · 查收查引辅助工具

批量从文章标题检索 DOI。支持粘贴文本和上传 Word/Excel 文件，内置 AI 智能解析和规则解析双引擎。

## 快速开始（用户）

访问 GitHub Pages 地址即可使用，无需安装任何软件。

1. 粘贴标题或上传文件 → 点击「解析标题」
2. 确认标题列表 → 点击「批量查询 DOI」
3. 复制结果或下载 Excel

## 管理员部署

### GitHub Pages（推荐）

项目已配置 GitHub Actions 自动部署。管理员只需在仓库 Settings → Secrets and variables → Actions 中配置三个 Secret：

| Secret | 说明 | 示例值 |
|--------|------|--------|
| `LLM_API_BASE` | API 地址 | `https://api.deepseek.com/v1/chat/completions` |
| `LLM_API_KEY` | API Key | `sk-...` |
| `LLM_MODEL` | 模型名称 | `deepseek-chat` |

配置完成后，每次 push 到 master 分支会自动部署。用户页面上的「高级设置」可覆盖默认 API 配置。

### 本地 Python 服务器（备选）

Python Flask 版本位于 `server/` 目录，供本地或内网部署使用：

```bash
cd server
pip install -r requirements.txt
cp .env.example .env   # 编辑 .env 填入 API Key
python run.py          # 访问 http://localhost:5000
```

不配 API Key 也能用——基础解析和 DOI 查询不依赖 LLM。

## 技术栈

- 纯静态 SPA（HTML + CSS + vanilla JS）
- LLM：OpenAI 兼容 API（默认 DeepSeek）
- DOI 查询：Crossref API（免费，无需 Key）
- 文档解析：SheetJS（Excel）+ Mammoth.js（Word）

## 配置说明

三层优先级（高→低）：

1. **前端高级设置**（用户自填，存浏览器 localStorage）
2. **GitHub Secrets**（管理员配置，Actions 注入 `config.js`）
3. **代码默认值**（DeepSeek 官方 API）
