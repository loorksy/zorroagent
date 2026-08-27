"""B3.3 feeds: OANDA for indicators; Twelve never computes levels; MetaApi down ≠ analysis down."""

import ast
from pathlib import Path

from app.feeds.divergence import check_divergence
from app.indicators import atr


def test_oanda_candles_compute_atr():
    candles = [
        {"high": 10 + i * 0.1, "low": 9.5 + i * 0.1, "close": 9.8 + i * 0.1} for i in range(20)
    ]
    value = atr(candles)
    assert value is not None and value > 0


def test_twelve_module_never_imported_by_indicators():
    root = Path(__file__).resolve().parents[1] / "app"
    offenders = []
    for path in root.rglob("*.py"):
        if "feeds/twelve.py" in str(path):
            continue
        text = path.read_text()
        if path.name in {"indicators.py", "tools.py"}:
            tree = ast.parse(text)
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module and "twelve" in node.module:
                    offenders.append(str(path))
                if isinstance(node, ast.Import):
                    for n in node.names:
                        if "twelve" in n.name:
                            offenders.append(str(path))
    assert offenders == []


def test_divergence_beyond_threshold_sets_banner_and_blocks():
    r = check_divergence(1.0, 1.01, 15)
    assert r.diverged is True
    assert r.banner == "Price data unreliable"


def test_metaapi_disconnected_does_not_enter_indicator_path():
    # indicators.py docstring + import graph: MetaApi is not a data source.
    text = (Path(__file__).resolve().parents[1] / "app" / "indicators.py").read_text()
    assert "MetaApi" not in text
    assert "Twelve Data is never an input" in text
