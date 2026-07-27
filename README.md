# title2doi — 标题DOI批量检索工具

中国科学技术大学图书馆 · 查收查引辅助工具

批量从文章标题检索 DOI。支持粘贴文本和上传 Word/Excel 文件，内置 AI 智能解析和规则解析双引擎。

## 快速开始（用户）

1. 打开浏览器访问服务器地址（如 `http://内网IP:5000`）
2. 粘贴标题或上传文件 → 点击「解析标题」
3. 确认标题列表 → 点击「批量查询 DOI」
4. 复制结果或下载 Excel

## 管理员部署

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API Key（启用 AI 智能解析）

```bash
cp .env.example .env
# 编辑 .env，填入硅基流动 API Key：
# LLM_API_KEY=sk-your-key-here
```

不配 API Key 也能用——基础解析和 DOI 查询不依赖 LLM。

### 3. 启动服务

**开发测试：**
```bash
python run.py
```

**生产环境：**
```bash
# Windows
deploy.bat

# Linux / Mac
bash deploy.sh
```

服务默认运行在 `http://0.0.0.0:5000`，同网段的其他电脑可通过 IP 访问。

### 4. 生产环境建议

- 安装 waitress：`pip install waitress`（纯 Python WSGI，Windows/Linux 通用）
- 配置 Windows 防火墙放行 5000 端口
- 长期运行可注册为 Windows 服务（用 nssm）

## API 配置说明

三层优先级（高→低）：

1. **前端高级设置**（用户自填）— 可选，覆盖服务器默认
2. **`.env` 文件**（管理员配置）— 所有用户共享
3. **`src/config.py`**（代码默认值）— 硅基流动 DeepSeek V3.2

## 支持的格式

| 输入方式 | 解析引擎 | 说明 |
|---------|---------|------|
| 粘贴文本 | 智能解析 (AI) | 支持作者/标题/期刊混排、中英混合 |
| 粘贴文本 | 基础解析 | 每行一个标题，去编号 |
| Word (.docx) | 基础解析 | 表格标题列识别 + 段落提取 |
| Excel (.xlsx) | 基础解析 | 自动识别标题列 |

## 技术栈

- Python 3.7+
- Flask · python-docx · openpyxl · requests
- LLM：OpenAI 兼容 API（默认 DeepSeek 官方 API，模型 deepseek-chat）
- DOI 查询：Crossref API

## 日志

运行日志保存在 `logs/` 目录，按天切割。
