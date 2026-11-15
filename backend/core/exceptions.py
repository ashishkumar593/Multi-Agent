"""Application exception hierarchy."""

class AppException(Exception):
    """Base application exception."""

class ConfigurationError(AppException):
    """Configuration or environment variable error."""

class IngestionError(AppException):
    """Document parsing or ingestion failure."""

class RetrievalError(AppException):
    """Vector, BM25, or hybrid search failure."""

class AgentExecutionError(AppException):
    """Agent execution or LLM parsing error."""

class SecurityError(AppException):
    """Security guardrail violation (SSRF, path traversal, malicious input)."""
