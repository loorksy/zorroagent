"""B3.4 alias suffixes, EUR_USD → EURUSDm, unmapped live bot cannot order."""

from app.symbols.alias import apply_broker_suffix, resolve_alias, stem_canonical


def test_eur_usd_to_eurusdm():
    assert apply_broker_suffix("EUR_USD", "m") == "EURUSDm"


def test_suffix_cases():
    assert apply_broker_suffix("XAU_USD", "m") == "XAUUSDm"
    assert apply_broker_suffix("XAU_USD", "pro") == "XAUUSDpro"
    assert apply_broker_suffix("XAU_USD", ".m") == "XAUUSD.m"
    assert apply_broker_suffix("XAU_USD", ".pro") == "XAUUSD.pro"
    assert apply_broker_suffix("EUR_USD", "#") == "EURUSD#"


def test_stem():
    assert stem_canonical("EUR_USD") == "EURUSD"


def test_unmapped_live_bot_cannot_send_order():
    r = resolve_alias("XAU_USD", {}, set())
    assert r.can_execute is False
    assert "execute NEVER" in (r.error or "")
