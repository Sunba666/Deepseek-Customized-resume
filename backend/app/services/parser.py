"""简历文本提取：PDF / DOCX / TXT → 纯文本。

仅做文本提取，不做 OCR（扫描件 PDF 返回空文本并提示）。
"""
import io
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def extract_text(path: Path) -> str:
    """按扩展名提取文本，返回去空白后的文本。"""
    ext = path.suffix.lower()
    readers = {".pdf": _extract_pdf, ".docx": _extract_docx, ".txt": _extract_txt}
    if ext not in readers:
        raise ValueError(f"不支持的文件类型: {ext}")
    try:
        text = readers[ext](path).strip()
    except ValueError:
        raise
    except Exception as exc:
        logger.warning("resume parsing failed (%s): %s", ext, type(exc).__name__)
        raise ValueError("文件无法解析，请确认文件未损坏、未加密，并使用 PDF / DOCX / TXT 格式") from exc
    if not text:
        raise ValueError("简历中没有可提取的文本，请上传包含文字的文件")
    return text


def _extract_pdf(path: Path) -> str:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    parts = []
    for page in reader.pages:
        try:
            parts.append(page.extract_text() or "")
        except Exception as e:  # 单页失败不中断
            logger.warning("pdf page extract failed: %s", e)
    text = "\n".join(parts)
    if not text.strip():
        raise ValueError("未从 PDF 提取到文本，可能为扫描件/图片型 PDF（暂不支持 OCR）")
    return text


def _extract_docx(path: Path) -> str:
    import docx

    doc = docx.Document(str(path))
    parts = [p.text for p in doc.paragraphs if p.text.strip()]
    for table in doc.tables:
        for row in table.rows:
            cells = [c.text.strip() for c in row.cells if c.text.strip()]
            if cells:
                parts.append(" | ".join(cells))
    return "\n".join(parts)


def _extract_txt(path: Path) -> str:
    # 尝试常见编码，兜底 GBK
    raw = path.read_bytes()
    for enc in ("utf-8-sig", "gb18030", "big5"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")
