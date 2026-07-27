# title2doi — 标题DOI批量检索工具

## 项目概述

批量从文章标题检索 DOI，服务于图书馆查收查引工作流。
输入：粘贴标题文本 / 上传 Word(.docx) / 上传 Excel(.xlsx)
输出：标题→DOI 对照表，支持一键复制和 Excel 导出。

## 技术栈

- Python 3.7+ · Flask · python-docx · openpyxl · requests
- LLM：OpenAI 兼容 API（默认 DeepSeek 官方 API，模型 deepseek-chat）
- DOI 查询：Crossref API
- 无额外前端依赖（vanilla HTML/CSS/JS）
- 无 python-dotenv 依赖（自实现 .env 解析）

## 目录结构

```
title2doi/
├── CLAUDE.md           # 本文件
├── README.md           # 用户 + 管理员文档
├── requirements.txt    # Python 依赖
├── .env.example        # API Key 配置模板
├── run.py / run.bat    # 开发启动
├── deploy.sh / deploy.bat  # 生产部署
├── app.py              # Flask 应用入口（路由 + 配置合并 + 日志初始化）
├── templates/
│   └── index.html      # 单页向导 UI（三步覆盖式）
└── src/
    ├── __init__.py
    ├── config.py       # 全局常量（Crossref + LLM 默认值）
    ├── env.py          # 轻量 .env 解析器
    ├── logger.py       # 结构化日志（请求/LLM/错误，按天切割）
    ├── parser.py       # 基础标题解析（正则 + Word/Excel）
    ├── llm_parser.py   # LLM 智能解析（OpenAI 兼容 API）
    └── lookup.py       # DOI 查询（Crossref API + difflib 匹配）
```

## API 路由

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 主页面 |
| POST | `/api/parse` | 基础解析 (form: mode + text/file) |
| POST | `/api/parse-llm` | LLM 智能解析 (json: {text, api_base?, api_key?, model?}) |
| POST | `/api/lookup` | 批量查询 DOI (json: {titles: [...]}) |
| POST | `/api/export/excel` | 导出 Excel (json: {results: [...]}) |

## 配置优先级

```
前端高级设置  >  .env 文件  >  config.py 硬编码默认
   (可选覆盖)     (管理员配)      (兜底值)
```

- `app.py` 启动时通过 `src/env.py` 加载 `.env`，合并为 `BACKEND_LLM_CONFIG`
- 每次 LLM 请求时，`_merge_llm_config()` 将前端传值覆盖到后端配置上
- `llm_parser.py` 不再自行读取环境变量，配置全部由调用方传入

## 日志

- 请求日志：IP、方法、路径、状态码、耗时（`@log_request` 装饰器）
- LLM 日志：模型名、输入/输出长度、耗时（不记录 Key 和内容）
- 错误日志：完整 traceback
- 位置：`logs/title2doi-YYYY-MM-DD.log`

## 开发约定

- type hints 使用 typing 模块（兼容 Python 3.7）
- docstring 用中文
- API 调用必须有超时和重试
- LLM API 使用 OpenAI 兼容格式，不绑定特定厂商

## 运行

```bash
pip install -r requirements.txt
python run.py          # 开发
bash deploy.sh         # Linux 生产
deploy.bat             # Windows 生产
```

## 验证

```bash
python -c "
from src.env import load_dotenv
from src.parser import parse_text
from src.llm_parser import _parse_llm_response
from src.lookup import lookup_doi

# .env 解析
load_dotenv()

# 基础解析
assert len(parse_text('Title A\nTitle B')) == 2

# LLM 响应解析
assert len(_parse_llm_response('1. Paper\n2. Paper')) == 2

# DOI 查询
assert lookup_doi('Attention Is All You Need').is_found
print('All checks passed')
"
```
