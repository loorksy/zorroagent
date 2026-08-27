from app.feeds.divergence import check_divergence


def test_missing_oanda_is_unreliable():
    r = check_divergence(None, 1.1, 15)
    assert r.diverged is True
    assert r.banner == "Price data unreliable"


def test_within_limit_ok():
    r = check_divergence(1.1000, 1.1001, 15)
    assert r.diverged is False


def test_beyond_limit_banner():
    r = check_divergence(1.0, 1.01, 15)  # 100 bps
    assert r.diverged is True
    assert r.banner == "Price data unreliable"
