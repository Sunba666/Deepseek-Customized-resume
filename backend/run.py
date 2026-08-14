"""开发启动入口：python run.py 或 uvicorn app.main:app。"""
import uvicorn

from app.config import get_settings

if __name__ == "__main__":
    s = get_settings()
    uvicorn.run("app.main:app", host=s.host, port=s.port, reload=True)
