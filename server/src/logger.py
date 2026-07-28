"""结构化日志模块

输出到 logs/ 目录，按天切割。
记录请求、LLM 调用、错误，不记录敏感信息（API Key）。
"""

import logging
import os
import time
from datetime import datetime
from pathlib import Path
from functools import wraps


def _get_log_dir() -> Path:
    """获取日志目录（项目根/logs），自动创建。"""
    log_dir = Path(__file__).resolve().parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    return log_dir


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """初始化日志系统。

    配置两个 handler：
    - 文件 handler：logs/title2doi-YYYY-MM-DD.log
    - 控制台 handler：INFO 级别以上输出到 stderr

    Returns:
        根 logger
    """
    log_dir = _get_log_dir()
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = log_dir / f"title2doi-{today}.log"

    logger = logging.getLogger("title2doi")
    logger.setLevel(level)

    # 避免重复添加 handler
    if logger.handlers:
        return logger

    # 文件 handler
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(
        "[%(asctime)s] %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    logger.addHandler(fh)

    # 控制台 handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter(
        "[%(levelname)s] %(message)s"
    ))
    logger.addHandler(ch)

    return logger


def get_logger(name: str = None) -> logging.Logger:
    """获取子 logger。"""
    full_name = f"title2doi.{name}" if name else "title2doi"
    return logging.getLogger(full_name)


def log_request(f):
    """装饰器：记录请求日志（IP、端点、耗时）。"""
    log = get_logger("api")

    @wraps(f)
    def wrapper(*args, **kwargs):
        from flask import request
        start = time.time()
        try:
            resp = f(*args, **kwargs)
            elapsed = (time.time() - start) * 1000
            log.info(
                "request ip=%s method=%s path=%s status=%d elapsed=%.0fms",
                request.remote_addr or "-",
                request.method,
                request.path,
                resp.status_code if hasattr(resp, 'status_code') else 200,
                elapsed,
            )
            return resp
        except Exception:
            elapsed = (time.time() - start) * 1000
            log.exception(
                "error ip=%s method=%s path=%s elapsed=%.0fms",
                request.remote_addr or "-",
                request.method,
                request.path,
                elapsed,
            )
            raise

    return wrapper


def log_llm_call(model: str, input_len: int, output_len: int, elapsed_ms: float):
    """记录 LLM API 调用（不记录 Key 和内容）。"""
    log = get_logger("llm")
    log.info(
        "llm_call model=%s input_chars=%d output_chars=%d elapsed=%.0fms",
        model, input_len, output_len, elapsed_ms,
    )
