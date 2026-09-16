"""简历上传解析接口：POST /api/resume/parse。

流程：保存临时文件 → 提取文本 → 脱敏 → 返回文本 + 基本信息预览 + 画像建议。
"""
import logging

from starlette.concurrency import run_in_threadpool

from fastapi import APIRouter, File, HTTPException, UploadFile

from ..models.schemas import PortraitRequest, ResumeParseResult
from ..services import parser, portrait, redactor
from ..utils import file_handler

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/resume", tags=["resume"])


@router.post("/parse", response_model=ResumeParseResult)
async def parse_resume(file: UploadFile = File(...)):
    """上传简历（PDF/DOCX/TXT），返回脱敏文本与预览。"""
    try:
        data = await file_handler.read_upload(file)
        path = await run_in_threadpool(file_handler.save_upload, file.filename or "resume.txt", data)
    except file_handler.UploadTooLargeError as e:
        raise HTTPException(413, str(e)) from e
    except ValueError as e:
        raise HTTPException(400, str(e)) from e

    try:
        text = await run_in_threadpool(parser.extract_text, path)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    finally:
        file_handler.cleanup(path)

    redacted = redactor.redact(text)
    contacts = redactor.extract_contact(text)
    inferred = portrait.infer_portrait(text)

    preview = {
        "contact": contacts,
        "inferred_role": inferred.target_role,
        "skills": inferred.skills,
        "years_experience": inferred.years_experience,
    }
    logger.info("parsed resume %s (%d chars)", file.filename, len(text))
    return ResumeParseResult(
        filename=file.filename or "resume.txt",
        text=text,
        redacted_text=redacted,
        preview=preview,
    )
