import httpx
from typing import Optional


def fetch_url(url: str, timeout: float = 30.0) -> str:
    """Fetch remote content via HTTP GET."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    response = httpx.get(url, timeout=timeout, headers=headers, follow_redirects=True)
    response.raise_for_status()
    return response.text


def extract_text_from_url(url: str, timeout: float = 30.0) -> Optional[str]:
    """
    Extract main text content from a URL.
    Uses Jina Reader API first (cleanest), then falls back to trafilatura/BeautifulSoup.
    """
    # Try Jina Reader API first (cleanest - returns clean markdown/text)
    try:
        reader_url = f"https://r.jina.ai/{url}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/plain'
        }
        response = httpx.get(reader_url, timeout=timeout, headers=headers, follow_redirects=True)
        response.raise_for_status()
        
        text = response.text.strip()
        
        # Limit content length
        if len(text) > 3000:
            text = text[:3000] + "\n\n[Content truncated for brevity]"
        
        if text and len(text) > 50:
            return text
    except Exception:
        pass  # Fall through to fallback methods
    
    # Fallback: Try direct HTML scraping
    try:
        html_content = fetch_url(url, timeout)
    except Exception:
        return None
    
    # Try trafilatura
    try:
        import trafilatura
        extracted = trafilatura.extract(html_content, include_comments=False, include_tables=True)
        if extracted and len(extracted.strip()) > 100:
            return extracted.strip()
    except Exception:
        pass
    
    # Fallback to BeautifulSoup
    try:
        from bs4 import BeautifulSoup
        import re
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove problematic elements
        for element in soup(["script", "style", "noscript"]):
            element.decompose()
        
        # Find main content
        main_content = (
            soup.find('div', class_='mw-content-container') or
            soup.find('div', class_='mw-parser-output') or
            soup.find('main') or 
            soup.find('article') or 
            soup.find('div', id='content') or
            soup.find('body')
        )
        
        text = main_content.get_text(separator='\n', strip=True) if main_content else soup.get_text(separator='\n', strip=True)
        
        # Clean up
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        text = '\n\n'.join(lines)
        text = re.sub(r'\n{4,}', '\n\n\n', text)
        text = re.sub(r' {3,}', ' ', text)
        text = text.strip()
        
        if text and len(text) > 50:
            return text
        elif text and len(text) > 10:
            return text
    except Exception:
        pass
    
    return None
