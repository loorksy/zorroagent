from app.symbols.alias import resolve_alias, validate_alias_payload


def test_unmapped_analyze_ok_execute_never():
    r = resolve_alias("EUR_USD", {}, set())
    assert r.mapped is False
    assert r.can_execute is False
    assert "execute NEVER" in (r.error or "")


def test_mapped_but_untested_cannot_execute():
    r = resolve_alias("EUR_USD", {"EUR_USD": "EURUSD"}, set())
    assert r.mapped is True
    assert r.can_execute is False


def test_mapped_and_tested_can_execute():
    r = resolve_alias("EUR_USD", {"EUR_USD": "EURUSD"}, {"EUR_USD"})
    assert r.can_execute is True
    assert r.execution_symbol == "EURUSD"


def test_payload_validation():
    assert validate_alias_payload("", "EURUSD")
    assert validate_alias_payload("EUR_USD", "EUR USD")
    assert validate_alias_payload("EUR_USD", "EURUSD") is None
