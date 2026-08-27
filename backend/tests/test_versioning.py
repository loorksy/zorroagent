from app.bots.versioning import activate_version, rollback_version
import pytest


def test_live_stays_on_old_version_until_activate():
    active, previous = activate_version("v1", "v2")
    assert active == "v2"
    assert previous == "v1"


def test_rollback_restores_previous_version():
    active, previous = rollback_version("v2", "v1")
    assert active == "v1"
    assert previous == "v2"


def test_rollback_without_previous_raises():
    with pytest.raises(ValueError, match="No previous"):
        rollback_version("v1", None)
