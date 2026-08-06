from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Optional


@dataclass(frozen=True)
class AuditContext:
    language: str
    mode: str
    profile_ids: tuple[str, ...]
    source_name: Optional[str] = None


@dataclass(frozen=True)
class Finding:
    rule_id: str
    source_adapter: str
    category: str
    severity: str
    confidence: str
    evidence: str
    start_offset: Optional[int]
    end_offset: Optional[int]
    diagnosis: str
    action: str
    repair_type: str
    upstream_sources: tuple[str, ...]
    protected: bool = False

    def to_dict(self) -> dict:
        return asdict(self)
