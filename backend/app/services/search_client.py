"""搜索集成：Serper.dev / Tavily 网页搜索客户端。

- Serper.dev: POST https://google.serper.dev/search, header X-API-KEY
- Tavily:     POST https://api.tavily.com/search, body {api_key, query}

返回统一结构的文本片段列表，供 LLM 整合；任一失败返回空列表（不中断流水线）。
"""
import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

SERPER_URL = "https://google.serper.dev/search"
TAVILY_URL = "https://api.tavily.com/search"

TIMEOUT = 20.0
MAX_CHARS = 800  # 每条结果截断长度


def search(provider: str, api_key: str, query: str, max_results: int = 5) -> list[str]:
    """按 provider 调用搜索，返回截断后的文本片段列表。"""
    if not api_key:
        return []
    try:
        if provider == "serper":
            return _serper(api_key, query, max_results)
        if provider == "tavily":
            return _tavily(api_key, query, max_results)
    except Exception as e:  # 搜索失败不中断分析
        logger.warning("search failed (provider=%s): %s", provider, e)
    return []


def _serper(api_key: str, query: str, max_results: int) -> list[str]:
    resp = httpx.post(
        SERPER_URL,
        headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
        json={"q": query, "num": max_results},
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()
    snippets: list[str] = []
    for item in (data.get("organic") or [])[:max_results]:
        title = item.get("title") or ""
        link = item.get("link") or ""
        snippet = item.get("snippet") or ""
        text = f"{title} {snippet} [{link}]".strip()
        if text:
            snippets.append(text[:MAX_CHARS])
    return snippets


def _tavily(api_key: str, query: str, max_results: int) -> list[str]:
    resp = httpx.post(
        TAVILY_URL,
        json={"api_key": api_key, "query": query, "max_results": max_results},
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()
    snippets: list[str] = []
    for item in (data.get("results") or [])[:max_results]:
        title = item.get("title") or ""
        url = item.get("url") or ""
        content = item.get("content") or ""
        text = f"{title} {content} [{url}]".strip()
        if text:
            snippets.append(text[:MAX_CHARS])
    return snippets
