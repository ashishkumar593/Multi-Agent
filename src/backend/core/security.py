"""Security guardrails: SSRF protection, path traversal defenses, input sanitization."""
import ipaddress
import socket
from pathlib import Path
from urllib.parse import urlparse

from src.backend.core.exceptions import SecurityError

BLOCKED_IP_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),      # Loopback
    ipaddress.ip_network("10.0.0.0/8"),       # Private Class A
    ipaddress.ip_network("172.16.0.0/12"),    # Private Class B
    ipaddress.ip_network("192.168.0.0/16"),   # Private Class C
    ipaddress.ip_network("169.254.0.0/16"),   # Link-local & Cloud Metadata
    ipaddress.ip_network("::1/128"),          # IPv6 Loopback
    ipaddress.ip_network("fc00::/7"),         # IPv6 Private
]

def validate_safe_url(url: str, allow_offline_fallback: bool = True) -> bool:
    """Validate that target URL does not resolve to private or loopback IP (SSRF defense)."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise SecurityError(f"Unsupported URL scheme: {parsed.scheme}")

    hostname = parsed.hostname
    if not hostname:
        raise SecurityError("Invalid URL: missing hostname")

    try:
        # Check if hostname is already a valid IP
        try:
            target_ip = ipaddress.ip_address(hostname)
        except ValueError:
            ip_str = socket.gethostbyname(hostname)
            target_ip = ipaddress.ip_address(ip_str)

        for blocked_net in BLOCKED_IP_NETWORKS:
            if target_ip in blocked_net:
                raise SecurityError(f"SSRF blocked: {hostname} resolves to restricted IP {target_ip}")
    except socket.gaierror as err:
        if allow_offline_fallback and "." in hostname and not hostname.startswith("127.") and hostname != "localhost":
            return True
        raise SecurityError(f"DNS resolution failed for {hostname}: {err}") from err

    return True

def validate_safe_path(base_dir: Path, target_path: Path) -> Path:
    """Ensure target path is strictly within base directory (prevents path traversal)."""
    resolved_base = base_dir.resolve()
    resolved_target = target_path.resolve()
    if not str(resolved_target).startswith(str(resolved_base)):
        raise SecurityError(f"Path traversal detected: {target_path} is outside {base_dir}")
    return resolved_target

def wrap_untrusted_content(content: str, source_id: str) -> str:
    """Wrap untrusted document/web content in delimiter tags to mitigate indirect prompt injection."""
    return f'<untrusted_context source_id="{source_id}">\n{content}\n</untrusted_context>'
