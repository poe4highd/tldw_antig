"""
统一日志配置：同时输出到 stdout 和滚动文件 logs/app.log
在 main.py 启动时调用 setup() 一次即可，其他模块直接 get_logger(__name__)。
"""
import logging
import logging.handlers
import os

LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
LOG_FILE = os.path.join(LOG_DIR, "app.log")
_initialized = False


def setup(level=logging.INFO):
    global _initialized
    if _initialized:
        return
    os.makedirs(LOG_DIR, exist_ok=True)

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 滚动文件：单文件最大 20MB，保留 5 个备份
    fh = logging.handlers.RotatingFileHandler(
        LOG_FILE, maxBytes=20 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    fh.setFormatter(fmt)

    sh = logging.StreamHandler()
    sh.setFormatter(fmt)

    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(fh)
    root.addHandler(sh)

    _initialized = True


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
