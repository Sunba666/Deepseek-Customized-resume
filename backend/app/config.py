"""应用配置：读取 .env，未配置项使用内置默认值（本地优先，零配置可运行）。"""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 服务
    host: str = "127.0.0.1"
    port: int = 8000

    # LLM (OpenAI 兼容格式)
    llm_base_url: str = "https://api.deepseek.com"
    llm_api_key: str = ""
    llm_model: str = "deepseek-chat"
    llm_temperature: float = 0.3

    # 公司本地库 (复用 Company-lookup 数据库；留空用 mock)
    company_db_path: str = r"E:\自己制作的项目\Company-lookup\company_data.db"

    # 数据源 API (预留企查查/天眼查)
    qcc_api_key: str = ""
    tianyancha_api_key: str = ""

    # 隐私
    auto_clean_temp: bool = True

    @property
    def llm_enabled(self) -> bool:
        return bool(self.llm_api_key.strip())

    @property
    def temp_dir(self) -> Path:
        d = BACKEND_DIR / "tmp"
        d.mkdir(parents=True, exist_ok=True)
        return d


@lru_cache
def get_settings() -> Settings:
    return Settings()
