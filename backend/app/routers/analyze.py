"""分析接口：POST /api/analyze。

接收简历文件 + LLM/搜索配置（由前端传入，不落盘），返回真实分析结果 JSON。
"""
import logging

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from ..services import analyzer
from ..utils import file_handler

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["analyze"])


@router.post("/analyze")
async def analyze(
    file: UploadFile = File(...),
    llm_base_url: str = Form("https://api.openai.com/v1"),
    llm_api_key: str = Form(""),
    llm_model: str = Form("gpt-4o"),
    search_provider: str = Form(""),
    search_api_key: str = Form(""),
):
    """上传简历并返回结构化分析结果（职业画像 / 公司推荐 / STAR 建议）。"""
    data = await file.read()
    if not data:
        raise HTTPException(400, "上传文件为空")
    try:
        path = file_handler.save_upload(file.filename or "resume.txt", data)
    except ValueError as e:
        raise HTTPException(400, str(e))

    try:
        result = analyzer.analyze_resume(
            file_path=path,
            llm_base_url=llm_base_url.strip() or "https://api.openai.com/v1",
            llm_api_key=llm_api_key.strip(),
            llm_model=llm_model.strip() or "gpt-4o",
            search_provider=search_provider.strip(),
            search_api_key=search_api_key.strip(),
        )
        return result
    except analyzer.AnalyzeError as e:
        raise HTTPException(400, str(e))
    except Exception as e:  # LLM/网络等异常统一转为 502，避免泄漏细节
        logger.exception("analyze failed")
        raise HTTPException(502, f"分析失败：{e}")
    finally:
        file_handler.cleanup(path)
