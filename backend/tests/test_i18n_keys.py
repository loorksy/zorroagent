"""Fail if EN/TR/AR JSON keys diverge."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "frontend" / "src" / "i18n"


def leaves(obj, prefix=""):
    out = []
    for k, v in obj.items():
        key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            out.extend(leaves(v, key))
        else:
            out.append(key)
    return sorted(out)


def test_i18n_keys_match():
    en = json.loads((ROOT / "en.json").read_text())
    tr = json.loads((ROOT / "tr.json").read_text())
    ar = json.loads((ROOT / "ar.json").read_text())
    assert leaves(en) == leaves(tr) == leaves(ar)


def test_tr_ar_not_raw_english_on_banner():
    tr = json.loads((ROOT / "tr.json").read_text())
    ar = json.loads((ROOT / "ar.json").read_text())
    assert tr["banner"]["unreliable"] != "Price data unreliable"
    assert ar["banner"]["unreliable"] != "Price data unreliable"
    assert tr["card"]["insufficient"] != "Insufficient data"
    assert ar["card"]["insufficient"] != "Insufficient data"
