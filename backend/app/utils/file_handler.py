"""文件读写与临时存储：保存上传文件到临时目录，按配置自动清理。

本地优先：文件只存临时目录，处理完即删，不上传任何服务器。
"""
import logging
import os
import tempfile
import time
import uuid
from pathlib import Path

from ..config import get_settings

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}

_tmp_root = Path(tempfile.gettempdir()) / "resume-advisor"


def _settings():
    return get_settings()


def save_upload(filename: str, data: bytes) -> Path:
    """保存上传文件到临时目录，返回路径。校验扩展名白名单。"""
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"不支持的文件类型: {ext or '(无扩展名)'}，仅支持 PDF / DOCX / TXT")

    _tmp_root.mkdir(parents=True, exist_ok=True)
    safe_name = f"{uuid.uuid4().hex}{ext}"
    path = _tmp_root / safe_name
    path.write_bytes(data)
    logger.info("saved upload %s -> %s", filename, path)
    return path


def cleanup(path: Path) -> None:
    """删除单个临时文件，失败仅告警。"""
    try:
        if path.exists():
            path.unlink()
            logger.info("cleaned temp file %s", path)
    except OSError as e:  # pragma: no cover
        logger.warning("cleanup failed for %s: %s", path, e)


def cleanup_old(max_age_seconds: int = 3600) -> int:
    """清理超龄临时文件（兜底，防止崩溃残留）。返回删除数量。"""
    if not _tmp_root.exists():
        return 0
    now = time.time()
    removed = 0
    for f in _tmp_root.iterdir():
        try:
            if f.is_file() and now - f.stat().st_mtime > max_age_seconds:
                f.unlink()
                removed += 1
        except OSError:
            continue
    if removed:
        logger.info("auto-cleaned %d stale temp files", removed)
    return removed


def cleanup_dir_on_shutdown() -> None:
    """退出时按配置清理临时目录全部文件。"""
    if not get_settings().auto_clean_temp:
        return
    try:
        if _tmp_root.exists():
            for f in _tmp_root.iterdir():
                if f.is_file():
                    f.unlink()
            logger.info("temp dir cleaned on shutdown")
    except OSError as e:  # pragma: no cover
        logger.warning("shutdown cleanup failed: %s", e)


# 兼容 os.environ 使用方
TEMP_DIR = str(_tmp_root)
