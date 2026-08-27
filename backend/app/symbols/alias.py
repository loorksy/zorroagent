"""canonical_id → execution_symbol. Unmapped = analyze OK, execute NEVER."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AliasResolution:
    canonical_id: str
    execution_symbol: str | None
    mapped: bool
    test_ok: bool
    error: str | None = None

    @property
    def can_execute(self) -> bool:
        return self.mapped and self.test_ok and bool(self.execution_symbol)


def resolve_alias(canonical_id: str, mapping: dict[str, str], tested_ok: set[str]) -> AliasResolution:
    symbol = mapping.get(canonical_id)
    if not symbol:
        return AliasResolution(canonical_id, None, False, False, "Unmapped: analysis OK, execute NEVER.")
    if canonical_id not in tested_ok:
        return AliasResolution(canonical_id, symbol, True, False, "Alias not test-resolved against MetaApi.")
    return AliasResolution(canonical_id, symbol, True, True)


def validate_alias_payload(canonical_id: str, execution_symbol: str) -> str | None:
    if not canonical_id or not canonical_id.strip():
        return "canonical_id is required"
    if not execution_symbol or not execution_symbol.strip():
        return "execution_symbol is required"
    if " " in execution_symbol.strip():
        return "execution_symbol must not contain spaces"
    return None
