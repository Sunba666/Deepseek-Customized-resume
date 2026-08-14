"""FastAPI 入口：装配路由、CORS、静态前端托管、优雅清理。

本地优先：服务仅监听 127.0.0.1；退出时按配置清理临时文件。
"""
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import get_settings
from .routers import analysis, analyze, companies, export, resume
from .services import risk_checker
from .utils import file_handler

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    file_handler.cleanup_old()
    logger.info("resume-advisor backend started (llm_enabled=%s)", get_settings().llm_enabled)
    yield
    file_handler.cleanup_dir_on_shutdown()


app = FastAPI(
    title="resume-advisor API",
    description="定制化求职方案生成器（本地优先）",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "tauri://localhost", "http://tauri.localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(resume.router)
app.include_router(analysis.router)
app.include_router(companies.router)
app.include_router(export.router)
app.include_router(analyze.router)


@app.get("/api/health")
def health():
    s = get_settings()
    return {
        "status": "ok",
        "llm_enabled": s.llm_enabled,
        "llm_base_url": s.llm_base_url,
        "llm_model": s.llm_model,
        "risk_sources": risk_checker.available_sources(),
    }


@app.get("/api/risk-sources")
def risk_sources():
    return {"sources": risk_checker.available_sources()}


# 托管前端构建产物（生产模式）；开发模式由 Vite dev server 代理
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")
