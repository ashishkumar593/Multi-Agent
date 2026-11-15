"""Secure webpage fetcher and clean text extraction."""
import re
from src.backend.core.exceptions import SecurityError
from src.backend.tools.source_validator import SourceValidator

class WebpageReader:
    """Fetches and sanitizes article content from web URLs."""

    def __init__(self, timeout_sec: float = 8.0, max_chars: int = 15000):
        self.timeout_sec = timeout_sec
        self.max_chars = max_chars

    def fetch_and_clean(self, url: str) -> str:
        """Fetch URL content safely and return cleaned text."""
        SourceValidator.validate_url(url)

        try:
            import httpx
            with httpx.Client(timeout=self.timeout_sec, follow_redirects=True) as client:
                resp = client.get(url, headers={"User-Agent": "AIResearchBot/1.0"})
                if resp.status_code != 200:
                    return ""
                html = resp.text
        except Exception:
            return ""

        return self._clean_html(html)

    def _clean_html(self, html: str) -> str:
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            for elem in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
                elem.decompose()
            text = soup.get_text(separator="\n")
        except ImportError:
            # shortcut: regex fallback if bs4 not installed
            text = re.sub(r"<[^>]+>", " ", html)

        # Normalize whitespace
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        clean = "\n".join(lines)
        return clean[: self.max_chars]
