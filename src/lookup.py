"""DOI 查询模块

通过 Crossref API 根据标题查询 DOI。
支持单条查询和批量查询，含模糊匹配和置信度评估。
"""

import time
import logging
from difflib import SequenceMatcher
from typing import Dict, List, Optional
from dataclasses import dataclass, field

import requests

from src.config import (
    CROSSREF_API_URL,
    CROSSREF_TIMEOUT,
    CROSSREF_RETRIES,
    CROSSREF_MAX_RESULTS,
    REQUEST_INTERVAL,
)

logger = logging.getLogger(__name__)


@dataclass
class LookupResult:
    """单条 DOI 查询结果"""
    query_title: str           # 用户输入的原始标题
    doi: Optional[str] = None  # 匹配到的 DOI（None 表示未找到）
    matched_title: Optional[str] = None  # Crossref 返回的匹配标题
    confidence: float = 0.0    # 匹配置信度 0~100
    error: Optional[str] = None  # 错误信息（如有）
    candidates: List[Dict] = field(default_factory=list)  # 其他候选结果

    @property
    def is_found(self) -> bool:
        return self.doi is not None

    @property
    def confidence_level(self) -> str:
        """置信度等级"""
        if self.confidence >= 90:
            return "高"
        elif self.confidence >= 70:
            return "中"
        else:
            return "低"


def _clean_title_for_query(title: str) -> str:
    """为 API 查询清理标题。

    - 去除特殊字符（保留字母、数字、空格、基本标点）
    - Crossref API 对特殊字符敏感，部分字符会导致零结果
    """
    # 移除可能导致 API 查询失败的特殊字符
    # 保留: 字母、数字、空格、连字符、冒号、逗号、句号、引号
    cleaned = title.strip()
    # 把换行和多余空白合并
    cleaned = ' '.join(cleaned.split())
    return cleaned


def _extract_doi(item: dict) -> Optional[str]:
    """从 Crossref API 返回的 item 中提取 DOI。"""
    return item.get("DOI")


def _extract_title(item: dict) -> Optional[str]:
    """从 Crossref API 返回的 item 中提取标题。

    Crossref 的 title 字段是列表，取第一个。
    """
    title_list = item.get("title", [])
    if title_list:
        return title_list[0]
    # 备选：subtitle
    subtitle_list = item.get("subtitle", [])
    if subtitle_list:
        return subtitle_list[0]
    return None


def _extract_item_info(item: dict) -> dict:
    """从 API 返回的单个结果中提取关键信息。"""
    doi = _extract_doi(item)
    title = _extract_title(item)
    container = item.get("container-title", [])
    journal = container[0] if container else None
    issued = item.get("issued", {}).get("date-parts", [[None]])[0][0]
    item_type = item.get("type", "unknown")

    return {
        "doi": doi,
        "title": title,
        "journal": journal,
        "year": issued,
        "type": item_type,
    }


def _token_sort_ratio(a: str, b: str) -> float:
    """将字符串分词、排序后比较相似度（模拟 rapidfuzz token_sort_ratio）。"""
    a_tokens = sorted(a.split())
    b_tokens = sorted(b.split())
    return SequenceMatcher(None, " ".join(a_tokens), " ".join(b_tokens)).ratio() * 100


def _match_score(query: str, candidate_title: Optional[str]) -> float:
    """计算查询标题与候选标题的匹配分数 (0-100)。

    使用标准库 difflib.SequenceMatcher 实现模糊匹配，
    无需额外依赖。
    """
    if not candidate_title:
        return 0.0

    # 预处理：小写、去多余空格
    q = query.lower().strip()
    c = candidate_title.lower().strip()

    # 精确匹配（忽略大小写和空格）
    if q == c:
        return 100.0

    # 包含关系加分
    if q in c or c in q:
        base = 85.0
        len_ratio = min(len(q), len(c)) / max(len(q), len(c))
        bonus = len_ratio * 10
        return min(base + bonus, 98.0)

    # 模糊匹配（基于 difflib）
    sm = SequenceMatcher(None, q, c)
    ratio_score = sm.ratio() * 100  # 整体序列相似度
    token_score = _token_sort_ratio(q, c)  # 词序无关相似度

    # 查找最佳局部匹配（模拟 partial_ratio）
    if len(q) <= len(c):
        # q 较短：在 c 中找最佳匹配窗口
        blocks = sm.get_matching_blocks()
        best_block = max(blocks, key=lambda b: b.size) if blocks else None
        if best_block and best_block.size > 0:
            partial_score = (best_block.size / max(len(q), 1)) * 100
        else:
            partial_score = ratio_score
    else:
        partial_score = ratio_score

    # 加权综合
    combined = token_score * 0.4 + partial_score * 0.35 + ratio_score * 0.25
    return combined


def lookup_doi(title: str) -> LookupResult:
    """根据文章标题查询 DOI。

    查询 Crossref API，返回最佳匹配结果及其置信度。

    Args:
        title: 文章标题

    Returns:
        LookupResult 包含 DOI、匹配标题、置信度等信息
    """
    cleaned_title = _clean_title_for_query(title)
    result = LookupResult(query_title=title)

    if not cleaned_title:
        result.error = "标题为空"
        return result

    params = {
        "query.title": cleaned_title,
        "rows": CROSSREF_MAX_RESULTS,
        "sort": "relevance",
    }

    for attempt in range(CROSSREF_RETRIES + 1):
        try:
            resp = requests.get(
                CROSSREF_API_URL,
                params=params,
                timeout=CROSSREF_TIMEOUT,
                headers={"User-Agent": "title2doi/1.0 (mailto:ustc_library@example.com)"},
            )
            resp.raise_for_status()
            data = resp.json()
            break
        except requests.exceptions.Timeout:
            if attempt < CROSSREF_RETRIES:
                time.sleep(1)
                continue
            result.error = "API 请求超时"
            return result
        except requests.exceptions.HTTPError as e:
            if resp.status_code == 404:
                result.error = "未找到匹配记录"
                return result
            if attempt < CROSSREF_RETRIES:
                time.sleep(1)
                continue
            result.error = f"API 请求失败: HTTP {resp.status_code}"
            return result
        except requests.exceptions.RequestException as e:
            if attempt < CROSSREF_RETRIES:
                time.sleep(1)
                continue
            result.error = f"网络请求失败: {e}"
            return result
        except (ValueError, KeyError) as e:
            result.error = f"API 响应解析失败: {e}"
            return result

    # 解析结果
    items = data.get("message", {}).get("items", [])

    if not items:
        result.error = "未找到匹配记录"
        return result

    # 计算每个候选项的匹配分数
    candidates: List[Dict] = []
    best_score = 0.0
    best_item = None

    for item in items:
        info = _extract_item_info(item)
        if not info["title"]:
            continue
        score = _match_score(cleaned_title, info["title"])
        info["score"] = round(score, 1)
        candidates.append(info)

        if score > best_score:
            best_score = score
            best_item = info

    result.candidates = sorted(candidates, key=lambda x: x["score"], reverse=True)

    if best_item and best_score >= 50:  # 最低阈值 50 分
        result.doi = best_item["doi"]
        result.matched_title = best_item["title"]
        result.confidence = round(best_score, 1)
    else:
        result.error = f"无可靠匹配（最佳匹配分数: {round(best_score, 1)}/100）"
        # 即使低于阈值，仍然附加候选列表供人工判断
        if best_item:
            result.doi = None
            result.matched_title = best_item.get("title")
            result.confidence = round(best_score, 1)

    return result


def batch_lookup(
    titles: List[str],
    progress_callback=None,
) -> List[LookupResult]:
    """批量查询 DOI。

    Args:
        titles: 标题列表
        progress_callback: 可选的进度回调函数，签名为 callback(current: int, total: int, title: str)

    Returns:
        LookupResult 列表，与输入顺序一一对应
    """
    results: List[LookupResult] = []
    total = len(titles)

    for i, title in enumerate(titles):
        if progress_callback:
            progress_callback(i + 1, total, title)

        result = lookup_doi(title)
        results.append(result)

        # 请求间隔，避免触发限速
        if i < total - 1:
            time.sleep(REQUEST_INTERVAL)

    return results
