"""轻量 .env 文件解析器

无需 python-dotenv 依赖，支持：
- KEY=value 格式
- 双引号/单引号包裹的值
- # 注释行
- 空行跳过
- 行尾注释（值不含 # 时）
"""

import os
from pathlib import Path
from typing import Dict


def load_dotenv(dotenv_path: str = None) -> Dict[str, str]:
    """加载 .env 文件，返回键值对字典。

    查找优先级：
    1. 指定的 dotenv_path
    2. 当前工作目录下的 .env
    3. 项目根目录下的 .env

    不会覆盖已有的环境变量（和 python-dotenv 行为一致）。

    Returns:
        解析到的键值对字典
    """
    # 确定 .env 文件路径
    if dotenv_path:
        paths = [Path(dotenv_path)]
    else:
        paths = [
            Path.cwd() / ".env",
            Path(__file__).resolve().parent.parent / ".env",
        ]

    env_file = None
    for p in paths:
        if p.is_file():
            env_file = p
            break

    if env_file is None:
        return {}

    result = {}
    try:
        with open(env_file, "r", encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()

                # 跳过空行和注释行
                if not line or line.startswith("#"):
                    continue

                # 解析 KEY=VALUE
                if "=" not in line:
                    continue

                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip()

                # 去除引号
                if len(value) >= 2:
                    if (value.startswith('"') and value.endswith('"')) or \
                       (value.startswith("'") and value.endswith("'")):
                        value = value[1:-1]

                # 去除行尾注释（简单处理：值中不含 # 时才去）
                if "#" in value and not value.startswith('"'):
                    hash_pos = value.find("#")
                    # 确保 # 前面是空格（避免 URL 中的 # 被误删）
                    if hash_pos > 0 and value[hash_pos - 1] == " ":
                        value = value[:hash_pos].rstrip()

                if key and value:
                    result[key] = value
                    # 不覆盖已存在的环境变量
                    if key not in os.environ:
                        os.environ[key] = value

    except Exception as e:
        print(f"[title2doi] 读取 .env 文件失败: {e}")

    return result


def get_env(key: str, default: str = "") -> str:
    """读取环境变量，带默认值。

    优先级：os.environ > .env 文件 > default
    """
    return os.environ.get(key, default)
