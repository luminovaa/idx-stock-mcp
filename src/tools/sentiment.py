"""MCP Tool: get_news_sentiment - Fetch and analyze news sentiment."""

import json
from ..data_sources.news_scraper import fetch_all_news
from ..utils.cache import news_cache, get_cache_key


async def get_news_sentiment(symbol: str, limit: int = 10) -> str:
    """Get latest news and sentiment data for a stock.
    
    Fetches news from Indonesian financial media (Bisnis.com, Kontan.co.id)
    and returns headlines with metadata for AI sentiment analysis.
    
    Args:
        symbol: IDX stock symbol (e.g., 'BBCA', 'TLKM')
        limit: Maximum number of news items per source (default: 10)
    
    Returns:
        JSON with news items (title, snippet, date, source, url)
    """
    cache_key = get_cache_key("news", symbol, limit)
    if cache_key in news_cache:
        return news_cache[cache_key]
    
    news_items = await fetch_all_news(symbol, limit=limit)
    
    result = {
        "symbol": symbol.upper(),
        "total_items": len(news_items),
        "sources": list(set(item.get("source", "") for item in news_items)),
        "news": news_items,
        "note": "Use these headlines and snippets to analyze sentiment. Consider: tone (positive/negative/neutral), catalysts (corporate actions, regulations, earnings), and red flags (investigations, downgrades).",
    }
    
    if not news_items:
        result["note"] = f"No recent news found for {symbol}. This could mean: (1) the stock is not in the news cycle, (2) scraping failed. Default to neutral sentiment."
    
    response = json.dumps(result, ensure_ascii=False)
    news_cache[cache_key] = response
    return response
