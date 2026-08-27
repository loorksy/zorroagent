"""Portfolio exposure in R. Informational unless operator set a cap. Agent read-only tool."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class OpenRisk:
    canonical_id: str
    direction: str
    r: float
    asset_class: str


@dataclass
class ExposureReport:
    total_r: float
    by_symbol: dict[str, float]
    correlation_warning: str | None
    cap_r: float | None
    cap_exceeded: bool


CORRELATED = {
    frozenset({"EUR_USD", "GBP_USD"}),
    frozenset({"AUD_USD", "NZD_USD"}),
    frozenset({"USD_JPY", "USD_CHF"}),
    frozenset({"XAU_USD", "XAG_USD"}),
    frozenset({"NAS100_USD", "SPX500_USD", "US30_USD"}),
}


def aggregate_exposure(positions: list[OpenRisk], cap_r: float | None) -> ExposureReport:
    by: dict[str, float] = {}
    for p in positions:
        by[p.canonical_id] = by.get(p.canonical_id, 0.0) + p.r
    total = sum(by.values())
    warning = None
    ids = set(by)
    for group in CORRELATED:
        overlap = ids & group
        if len(overlap) >= 2:
            same_side = {p.direction for p in positions if p.canonical_id in overlap}
            if len(same_side) == 1:
                warning = (
                    f"Correlation warning: {', '.join(sorted(overlap))} are typically correlated "
                    "and currently share direction. Informational unless an exposure cap is set."
                )
                break
    return ExposureReport(
        total_r=total,
        by_symbol=by,
        correlation_warning=warning,
        cap_r=cap_r,
        cap_exceeded=bool(cap_r is not None and total > cap_r),
    )
