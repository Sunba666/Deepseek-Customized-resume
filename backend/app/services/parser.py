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
    if ext == ".pdf":
        return _extract_pdf(path)
    if ext == ".docx":
        return _extract_docx(path)
    if ext == ".txt":
        return _extract_txt(path)
    raise ValueError(f"不支持的文件类型: {ext}")


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
    for enc in ("utf-8", "utf-8-sig", "gbk", "gb18030", "big5"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")
