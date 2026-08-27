from app.bots.safety import SafetyContext, check_bot_safety, promote_gate, promote_gate


def _ok(**over) -> SafetyContext:
    base = dict(
        kill_switch=False,
        feed_unreliable=False,
        news_blocked=False,
        session_blocked=False,
        spread_abnormal=False,
        alias_mapped=True,
        demo_required_unmet=False,
        rationale_ok=True,
        rationale_veto=False,
        min_interval_ok=True,
        lots_positive=True,
        sl_attached=True,
        vision_required_failed=False,
        exposure_cap_exceeded=False,
        account_bound=True,
        code_version_active=True,
    )
    base.update(over)
    return SafetyContext(**base)


def test_kill_switch_overrides_everything():
    v = check_bot_safety(_ok(kill_switch=True, rationale_ok=True))
    assert v.ok is False
    assert v.failed == ["kill_switch"]


def test_missing_rationale_no_order():
    v = check_bot_safety(_ok(rationale_ok=False))
    assert v.ok is False
    assert "rationale_ok" in v.failed


def test_veto_never_flips_just_blocks():
    v = check_bot_safety(_ok(rationale_veto=True))
    assert v.ok is False
    assert "rationale_veto" in v.failed


def test_unmapped_alias_blocks_bot_order():
    v = check_bot_safety(_ok(alias_mapped=False))
    assert "alias_mapped" in v.failed


def test_promote_without_demo_is_403():
    ok, code, _ = promote_gate(False, "XAU_USD", "XAU_USD", False)
    assert ok is False
    assert code == 403


def test_promote_without_pin_or_symbol_is_403():
    ok, code, _ = promote_gate(True, "", "XAU_USD", False)
    assert ok is False
    assert code == 403
    ok2, code2, _ = promote_gate(True, "wrong", "XAU_USD", False)
    assert code2 == 403
