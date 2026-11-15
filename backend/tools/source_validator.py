"""Source credibility and SSRF validation for web URLs."""
from urllib.parse import urlparse
from backend.core.security import validate_safe_url

HIGH_CREDIBILITY_DOMAINS = {".edu", ".gov", ".org", "arxiv.org", "nature.com", "reuters.com", "ieee.org"}

class SourceValidator:
    """Validates URL safety and computes baseline credibility scores."""

    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate safety against SSRF and private IP destinations."""
        return validate_safe_url(url)

    @staticmethod
    def calculate_credibility(url: str) -> float:
        """Score credibility from 0.0 to 1.0 based on domain authority heuristics."""
        parsed = urlparse(url)
        hostname = (parsed.hostname or "").lower()

        for high_domain in HIGH_CREDIBILITY_DOMAINS:
            if hostname.endswith(high_domain):
                return 0.95

        if parsed.scheme == "https":
            return 0.75
        return 0.50
