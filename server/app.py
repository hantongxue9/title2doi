"""title2doi — Flask Web 应用

查收查引辅助工具：批量从文章标题检索 DOI。
提供单页向导式 Web 界面 + RESTful API。

路由:
    GET  /              — 主页面
    POST /api/parse     — 基础解析（正则引擎，文本/文件）
    POST /api/parse-llm — 智能解析（LLM 引擎）
    POST /api/lookup    — 批量查询 DOI
    POST /api/export/excel — 导出 Excel
"""

import io
import base64
import os
import time
from typing import Dict, Optional

from flask import Flask, render_template, request, jsonify
from werkzeug.exceptions import RequestEntityTooLarge

from src.env import load_dotenv, get_env
from src.logger import setup_logging, log_request, log_llm_call, get_logger
from src.parser import parse_text, parse_uploaded_file
from src.llm_parser import parse_via_llm
from src.lookup import batch_lookup
from src.config import (
    LLM_DEFAULT_API_BASE,
    LLM_DEFAULT_MODEL,
    MAX_UPLOAD_BYTES,
)

# ── 启动：加载配置和日志 ──────────────────────────────────
load_dotenv()
log = setup_logging()

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_BYTES

# 后端默认 LLM 配置（来自 .env 或 config.py）
BACKEND_LLM_CONFIG = {
    "api_base": get_env("LLM_API_BASE", LLM_DEFAULT_API_BASE),
    "api_key": get_env("LLM_API_KEY", ""),
    "model": get_env("LLM_MODEL", LLM_DEFAULT_MODEL),
}

app_log = get_logger("app")
app_log.info(
    "title2doi 启动 — backend api_base=%s model=%s key_configured=%s",
    BACKEND_LLM_CONFIG["api_base"],
    BACKEND_LLM_CONFIG["model"],
    "yes" if BACKEND_LLM_CONFIG["api_key"] else "no",
)


def _merge_llm_config(frontend: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """合并 LLM 配置：前端覆盖 > 后端 .env > config.py 默认。

    Args:
        frontend: 前端传过来的配置（api_base, api_key, model），均可选

    Returns:
        合并后的配置字典，至少包含 api_base, api_key, model
    """
    if frontend is None:
        frontend = {}

    return {
        "api_base": frontend.get("api_base") or BACKEND_LLM_CONFIG["api_base"],
        "api_key": frontend.get("api_key") or BACKEND_LLM_CONFIG["api_key"],
        "model": frontend.get("model") or BACKEND_LLM_CONFIG["model"],
    }


# ── 路由 ──────────────────────────────────────────────────

@app.route("/")
def index():
    """主页面"""
    return render_template("index.html")


@app.route("/api/parse", methods=["POST"])
@log_request
def api_parse():
    """基础解析 API（正则引擎）。

    接受:
        - mode=text + text=标题文本
        - mode=file + file=上传文件

    返回: {"ok": true, "titles": [...], "count": N, "source": "..."}
    """
    mode = request.form.get("mode", "text")

    try:
        if mode == "file":
            uploaded = request.files.get("file")
            if not uploaded:
                return jsonify({"ok": False, "error": "请选择文件"})

            filename = uploaded.filename or "unknown"
            file_bytes = uploaded.read()
            if not file_bytes:
                return jsonify({"ok": False, "error": "文件为空"})

            titles = parse_uploaded_file(file_bytes, filename)
            source = filename
        else:
            raw_text = request.form.get("text", "")
            if not raw_text.strip():
                return jsonify({"ok": False, "error": "请输入标题文本"})
            titles = parse_text(raw_text)
            source = "粘贴文本"

        if not titles:
            return jsonify({
                "ok": False,
                "error": "未能解析出有效标题，请检查输入格式（建议每行一个标题）"
            })

        return jsonify({"ok": True, "titles": titles, "count": len(titles), "source": source})

    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)})
    except Exception as e:
        get_logger("api").exception("parse error")
        return jsonify({"ok": False, "error": f"解析失败: {e}"})


@app.errorhandler(RequestEntityTooLarge)
def handle_request_too_large(_error):
    max_mb = MAX_UPLOAD_BYTES // (1024 * 1024)
    return jsonify({"ok": False, "error": f"文件过大，单个文件不能超过 {max_mb}MB"}), 413


@app.route("/api/parse-llm", methods=["POST"])
@log_request
def api_parse_llm():
    """LLM 智能解析 API。

    接受 JSON:
        {
            "text": "原始文本",
            "api_base": "可选，覆盖后端默认 API 地址",
            "api_key":  "可选，覆盖后端默认 API Key",
            "model":    "可选，覆盖后端默认模型"
        }

    返回: {"ok": true, "titles": [...], "count": N, "engine": "llm"}
    """
    data = request.get_json(silent=True)
    if not data or "text" not in data:
        return jsonify({"ok": False, "error": "请输入文本"})

    raw_text = data["text"]
    if not raw_text.strip():
        return jsonify({"ok": False, "error": "文本为空"})

    # 合并配置
    config = _merge_llm_config({
        k: data.get(k) for k in ("api_base", "api_key", "model") if data.get(k)
    })

    try:
        start = time.time()
        titles = parse_via_llm(
            raw_text=raw_text,
            api_base=config["api_base"],
            api_key=config["api_key"],
            model=config["model"],
        )
        elapsed = (time.time() - start) * 1000

        # 记录 LLM 调用日志（不记录内容）
        log_llm_call(
            model=config["model"],
            input_len=len(raw_text),
            output_len=sum(len(t) for t in titles),
            elapsed_ms=elapsed,
        )

        if not titles:
            return jsonify({
                "ok": False,
                "error": "LLM 未能提取出标题。请检查文本内容，或切换到「基础解析」重试。"
            })

        return jsonify({"ok": True, "titles": titles, "count": len(titles), "engine": "llm"})

    except ValueError as e:
        get_logger("llm").warning("config error: %s", e)
        return jsonify({"ok": False, "error": str(e)})
    except RuntimeError as e:
        get_logger("llm").error("api error: %s", e)
        return jsonify({"ok": False, "error": str(e)})
    except Exception as e:
        get_logger("llm").exception("unexpected error")
        return jsonify({"ok": False, "error": f"LLM 解析失败: {e}"})


@app.route("/api/lookup", methods=["POST"])
@log_request
def api_lookup():
    """批量查询 DOI API。

    接受 JSON: {"titles": ["Title A", "Title B", ...]}

    返回:
        {"ok": true, "results": [...], "summary": {"total": N, "found": N, ...}}
    """
    data = request.get_json(silent=True)
    if not data or "titles" not in data:
        return jsonify({"ok": False, "error": "请提供标题列表"})

    titles = data["titles"]
    if not isinstance(titles, list) or len(titles) == 0:
        return jsonify({"ok": False, "error": "标题列表为空"})

    if len(titles) > 200:
        return jsonify({"ok": False, "error": "单次最多查询 200 条标题"})

    try:
        results = batch_lookup(titles)
    except Exception as e:
        get_logger("api").exception("lookup error")
        return jsonify({"ok": False, "error": f"查询失败: {e}"})

    found = sum(1 for r in results if r.is_found)
    high = sum(1 for r in results if r.is_found and r.confidence >= 90)
    mid = sum(1 for r in results if r.is_found and 70 <= r.confidence < 90)
    low = sum(1 for r in results if r.is_found and r.confidence < 70)

    return jsonify({
        "ok": True,
        "results": [
            {
                "query_title": r.query_title,
                "doi": r.doi,
                "matched_title": r.matched_title,
                "confidence": r.confidence,
                "confidence_level": r.confidence_level,
                "error": r.error,
                "is_found": r.is_found,
            }
            for r in results
        ],
        "summary": {
            "total": len(results),
            "found": found,
            "high": high,
            "mid": mid,
            "low": low,
        }
    })


@app.route("/api/export/excel", methods=["POST"])
@log_request
def api_export_excel():
    """导出结果为 Excel 文件（返回 base64）。"""
    import pandas as pd

    data = request.get_json(silent=True)
    if not data or "results" not in data:
        return jsonify({"ok": False, "error": "无数据可导出"})

    rows = []
    for i, r in enumerate(data["results"], 1):
        rows.append({
            "序号": i,
            "原始标题": r["query_title"],
            "DOI": r["doi"] or "",
            "匹配标题": r["matched_title"] or "",
            "置信度": f"{r['confidence']:.0f}%" if r["confidence"] > 0 else "",
            "查询状态": "找到" if r["is_found"] else (r["error"] or "未找到"),
        })

    df = pd.DataFrame(rows)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="DOI查询结果")

    output.seek(0)
    b64 = base64.b64encode(output.read()).decode()

    return jsonify({"ok": True, "filename": "doi_results.xlsx", "data": b64})


if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "").lower() in ("1", "true", "yes")
    app.run(host="0.0.0.0", port=5000, debug=debug)
