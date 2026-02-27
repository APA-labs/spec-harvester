from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class DocumentMeta:
    url: str
    fetched_at: str
    status: int
    content_type: str
    sha256: str
    bytes: int
    headers: dict[str, str | None]
    final_url: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
