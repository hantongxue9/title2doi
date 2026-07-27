"""LLM 智能标题解析模块

调用 OpenAI 兼容的 Chat Completions API，从杂乱文本中提取文章标题。
支持中英文混合、作者/标题混排、多篇文章粘连等场景。
"""

from typing import Dict, List, Optional

import requests

from src.config import (
    LLM_DEFAULT_API_BASE,
    LLM_DEFAULT_MODEL,
    LLM_TIMEOUT,
    LLM_MAX_TOKENS,
    LLM_TEMPERATURE,
)

SYSTEM_PROMPT = """你是一个学术文献信息提取助手。你的任务是从用户提供的文本中提取所有文章标题。

规则：
1. 只提取文章标题本身，去掉作者姓名、期刊名、年份、卷期页码、DOI、ISSN
2. 每篇文章输出一个标题，一行一个，不要空行
3. 如果原文中标题因换行被截断，请把它们合并成完整的一行
4. 中英文标题均提取，保持原标题语言
5. 不要编号，不要任何前缀后缀（如"标题："、"Title:"等）
6. 如果无法确定某段文字是否为标题，宁可跳过
7. 相同标题去重，只输出一次
8. 直接输出标题列表，不要任何解释、说明、或开头语"""


def _build_messages(raw_text: str) -> list:
    """构建 LLM API 请求的 messages。"""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"请从以下文本中提取所有文章标题：\n\n{raw_text}"},
    ]


def _parse_llm_response(content: str) -> List[str]:
    """解析 LLM 返回的文本，提取标题列表。

    处理 LLM 可能返回的各种格式：
    - 纯文本每行一个
    - Markdown 代码块包裹
    - 带编号的行
    """
    import re

    content = content.strip()

    # 去除可能的 markdown 代码块标记
    content = re.sub(r'^```[\w]*\s*\n?', '', content)
    content = re.sub(r'\n?```\s*$', '', content)

    titles = []
    seen = set()

    for line in content.split('\n'):
        line = line.strip()
        if not line:
            continue

        # 去除可能的编号前缀（如 "1. ", "1、", "- "）
        line = re.sub(r'^[\s]*[\d]+[\.\、\)）]\s*', '', line)
        line = re.sub(r'^[\s]*[-–—•·]\s*', '', line)

        # 去除首尾引号
        line = line.strip('"\'""''「」『』')

        if line and len(line) >= 3:  # 最短标题 3 字符
            normalized = line.lower().replace(' ', '')
            if normalized not in seen:
                seen.add(normalized)
                titles.append(line)

    return titles


def parse_via_llm(
    raw_text: str,
    api_base: Optional[str] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
) -> List[str]:
    """通过 LLM 从杂乱文本中提取文章标题。

    配置由调用方（app.py）负责合并完成后传入，
    本函数不再自行读取环境变量。

    Args:
        raw_text: 包含文章引用信息的原始文本
        api_base: API 端点 URL
        api_key: API 密钥（由调用方保证已合并 .env 和前端覆盖）
        model: 模型名称

    Returns:
        提取到的标题列表

    Raises:
        ValueError: API key 未配置
        RuntimeError: API 调用失败
    """
    if not raw_text.strip():
        return []

    base_url = api_base or LLM_DEFAULT_API_BASE
    key = api_key  # 由调用方（app.py）完成配置合并后传入
    model_name = model or LLM_DEFAULT_MODEL

    if not key:
        raise ValueError(
            "未配置 LLM API Key。请在 API 设置面板中填写，"
            "或设置环境变量 LLM_API_KEY。"
        )

    # 确保 URL 以 /chat/completions 结尾
    if not base_url.endswith('/chat/completions'):
        if base_url.endswith('/'):
            base_url = base_url + 'chat/completions'
        elif '/v1' in base_url and not base_url.endswith('/v1'):
            base_url = base_url + '/chat/completions'
        elif base_url.endswith('/v1'):
            base_url = base_url + '/chat/completions'

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {key}",
    }

    payload = {
        "model": model_name,
        "messages": _build_messages(raw_text),
        "max_tokens": LLM_MAX_TOKENS,
        "temperature": LLM_TEMPERATURE,
    }

    # 两次尝试（首次 + 1 次重试）
    last_error = None
    for attempt in range(2):
        try:
            resp = requests.post(
                base_url,
                json=payload,
                headers=headers,
                timeout=LLM_TIMEOUT,
            )

            if resp.status_code == 401 or resp.status_code == 403:
                raise ValueError(
                    f"API Key 无效或无权限（HTTP {resp.status_code}）。"
                    "请检查 API 设置面板中的 Key 是否正确。"
                )

            if resp.status_code == 404:
                raise ValueError(
                    f"API 端点不存在（HTTP 404）。请检查 API 地址配置：{base_url}"
                )

            if resp.status_code != 200:
                error_detail = resp.text[:500]
                # 尝试解析 JSON 错误消息
                try:
                    err_data = resp.json()
                    api_msg = err_data.get("message", "") or str(err_data)
                except Exception:
                    api_msg = error_detail

                if "model" in api_msg.lower() and ("not exist" in api_msg.lower() or "not found" in api_msg.lower()):
                    raise RuntimeError(
                        f"模型 '{model_name}' 不存在。"
                        "请在 API 设置面板中填入正确的模型 ID（可在硅基流动后台查看）。"
                    )

                raise RuntimeError(
                    f"API 返回错误（HTTP {resp.status_code}）: {error_detail}"
                )

            data = resp.json()
            content = (
                data.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
            )

            if not content:
                raise RuntimeError("LLM 返回了空内容，请重试")

            return _parse_llm_response(content)

        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            last_error = e
            if attempt == 0:
                continue  # 重试
            raise RuntimeError(
                f"连接 LLM API 失败（{LLM_TIMEOUT}秒超时）: {e}。"
                "请检查 API 地址是否正确、网络是否可达。"
            )

        except (ValueError, RuntimeError):
            raise  # 不重试已知错误

    raise RuntimeError(f"LLM 调用失败: {last_error}")
