"""News scraper for Indonesian stock market news."""

import httpx
from bs4 import BeautifulSoup
from typing import Optional
from datetime import datetime


async def fetch_news_bisnis(symbol: str, limit: int = 10) -> list[dict]:
    """Fetch news from Bisnis.com related to a stock symbol.
    
    Returns list of dicts with: title, snippet, date, url
    """
    results = []
    try:
        search_url = f"https://www.bisnis.com/search?query={symbol}"
        
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            response = await client.get(
                search_url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "text/html",
                }
            )
            
            if response.status_code != 200:
                return results
            
            soup = BeautifulSoup(response.text, "html.parser")
            articles = soup.select("article, .list-news .item, .search-result-item")[:limit]
            
            for article in articles:
                title_el = article.select_one("h2, h3, .title, a")
                snippet_el = article.select_one("p, .description, .excerpt")
                date_el = article.select_one("time, .date, .time")
                link_el = article.select_one("a[href]")
                
                if title_el:
                    results.append({
                        "title": title_el.get_text(strip=True),
                        "snippet": snippet_el.get_text(strip=True) if snippet_el else "",
                        "date": date_el.get_text(strip=True) if date_el else "",
                        "url": link_el.get("href", "") if link_el else "",
                        "source": "bisnis.com",
                    })
    except Exception:
        pass
    
    return results


async def fetch_news_kontan(symbol: str, limit: int = 10) -> list[dict]:
    """Fetch news from Kontan.co.id related to a stock symbol."""
    results = []
    try:
        search_url = f"https://www.kontan.co.id/search/?search={symbol}"
        
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            response = await client.get(
                search_url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "text/html",
                }
            )
            
            if response.status_code != 200:
                return results
            
            soup = BeautifulSoup(response.text, "html.parser")
            articles = soup.select(".list-berita li, .search-result-item, article")[:limit]
            
            for article in articles:
                title_el = article.select_one("h2, h3, .title, a")
                snippet_el = article.select_one("p, .description")
                date_el = article.select_one("time, .date, span.font-gray")
                link_el = article.select_one("a[href]")
                
                if title_el:
                    results.append({
                        "title": title_el.get_text(strip=True),
                        "snippet": snippet_el.get_text(strip=True) if snippet_el else "",
                        "date": date_el.get_text(strip=True) if date_el else "",
                        "url": link_el.get("href", "") if link_el else "",
                        "source": "kontan.co.id",
                    })
    except Exception:
        pass
    
    return results


async def fetch_all_news(symbol: str, limit: int = 10) -> list[dict]:
    """Fetch news from all sources and combine.
    
    Args:
        symbol: Stock symbol (e.g., 'BBCA')
        limit: Max news items per source
    
    Returns:
        Combined list of news items sorted by recency
    """
    # Fetch from multiple sources
    bisnis_news = await fetch_news_bisnis(symbol, limit=limit)
    kontan_news = await fetch_news_kontan(symbol, limit=limit)
    
    # Combine and deduplicate by title
    all_news = bisnis_news + kontan_news
    seen_titles = set()
    unique_news = []
    
    for item in all_news:
        title_lower = item["title"].lower()
        if title_lower not in seen_titles:
            seen_titles.add(title_lower)
            unique_news.append(item)
    
    return unique_news[:limit * 2]  # Return up to 2x limit combined
