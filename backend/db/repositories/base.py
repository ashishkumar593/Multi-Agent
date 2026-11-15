"""Base repository class."""
from typing import Any, Generic, TypeVar

T = TypeVar("T")

class BaseRepository(Generic[T]):
    """Generic repository providing basic CRUD persistence."""

    def __init__(self, session: Any = None):
        self.session = session
