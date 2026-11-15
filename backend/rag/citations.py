"""Citation registry, validation, and deterministic bibliography generation."""
import re
from dataclasses import dataclass
from typing import Any

@dataclass
class CitationSource:
    index: int
    source_id: str
    title: str
    url_or_path: str
    page: int | None = None
    excerpt: str = ""

class CitationRegistry:
    """Manages verified source mappings and validates inline citation tags."""

    def __init__(self) -> None:
        self.sources: list[CitationSource] = []
        self._source_index_map: dict[str, int] = {}

    def register_source(
        self, source_id: str, title: str, url_or_path: str, page: int | None = None, excerpt: str = ""
    ) -> int:
        """Register a source passage and return its 1-based citation index."""
        if source_id in self._source_index_map:
            return self._source_index_map[source_id]

        idx = len(self.sources) + 1
        source = CitationSource(
            index=idx,
            source_id=source_id,
            title=title,
            url_or_path=url_or_path,
            page=page,
            excerpt=excerpt[:200],
        )
        self.sources.append(source)
        self._source_index_map[source_id] = idx
        return idx

    def validate_citations(self, text: str) -> tuple[bool, list[int], list[int]]:
        """Validate inline [N] citations. Returns (is_valid, valid_indices, invalid_indices)."""
        found_indices = [int(m) for m in re.findall(r"\[(\d+)\]", text)]
        max_idx = len(self.sources)

        valid = [i for i in found_indices if 1 <= i <= max_idx]
        invalid = [i for i in found_indices if i < 1 or i > max_idx]

        is_valid = len(invalid) == 0
        return is_valid, valid, invalid

    def render_references(self) -> str:
        """Generate structured Markdown bibliography."""
        if not self.sources:
            return ""

        lines = ["\n### References & Verified Sources"]
        for s in self.sources:
            page_info = f", Page {s.page}" if s.page else ""
            lines.append(f"[{s.index}] **{s.title}** ({s.url_or_path}{page_info})")
        return "\n".join(lines)
