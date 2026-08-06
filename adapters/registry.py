from __future__ import annotations

from .base import AuditContext, Finding


class StaticAdapter:
    adapter_id = "local-static-scanner"

    def is_available(self) -> bool:
        return True

    def audit(self, text: str, context: AuditContext) -> list[Finding]:
        from scripts.audit import scan_text
        return scan_text(text, context)


class UpstreamReferenceAdapter:
    """Provenance-only adapter for the required Phase 1 upstream."""

    def __init__(self, adapter_id: str, enabled: bool = True):
        self.adapter_id = adapter_id
        self.enabled = enabled

    def is_available(self) -> bool:
        return self.enabled

    def audit(self, text: str, context: AuditContext) -> list[Finding]:
        return []


def default_adapters() -> list[object]:
    return [
        StaticAdapter(),
        UpstreamReferenceAdapter("conorbronsdon-avoid-ai-writing"),
        UpstreamReferenceAdapter("blader-humanizer"),
        UpstreamReferenceAdapter("harshaneel-humanize", enabled=False),
        UpstreamReferenceAdapter("aboudjem-humanizer-skill", enabled=False),
        UpstreamReferenceAdapter("gabelul-slopbuster", enabled=False),
    ]
