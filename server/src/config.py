"""配置常量"""

# Crossref API
CROSSREF_API_URL = "https://api.crossref.org/works"
CROSSREF_TIMEOUT = 15  # 请求超时（秒）
CROSSREF_RETRIES = 2   # 重试次数
CROSSREF_MAX_RESULTS = 3  # 每次查询返回的最多候选结果数

# 请求间隔（秒），避免触发限速
REQUEST_INTERVAL = 0.3

# 标题解析
MIN_TITLE_LENGTH = 5       # 标题最短字符数（短于此的不是标题）
MAX_TITLE_LENGTH = 600     # 标题最长字符数
SKIP_PATTERNS = [          # 明显不是标题的行（忽略大小写）
    "参考文献", "references", "附录", "appendix",
    "致谢", "acknowledgments", "acknowledgements",
]

# Excel/Word 表格中可能的标题列名
TITLE_COLUMN_KEYWORDS = [
    "题名", "标题", "篇名", "论文标题", "文章标题", "论文题目",
    "title", "article title", "paper title", "publication title",
]

# ── LLM 智能解析 ──────────────────────────────────────────
# 以下为后端默认值，可被前端 API 设置面板或环境变量覆盖

# OpenAI 兼容 API 地址（DeepSeek 官方 API）
LLM_DEFAULT_API_BASE = "https://api.deepseek.com/v1/chat/completions"

# 默认模型（DeepSeek 官方：deepseek-v4-flash，速度快成本低）
LLM_DEFAULT_MODEL = "deepseek-v4-flash"

# LLM 请求配置
LLM_TIMEOUT = 30       # 请求超时（秒）
LLM_MAX_TOKENS = 2000  # 最大输出 token 数
LLM_TEMPERATURE = 0.1  # 低温度，提高输出稳定性
