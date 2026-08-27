"""Bot version pointer: live stays on the old version until activate; rollback restores previous."""


def activate_version(current_active: str | None, new_id: str) -> tuple[str, str | None]:
    """Return (active_version_id, previous_version_id). Does not auto-cut over."""
    return new_id, current_active


def rollback_version(
    current_active: str | None,
    previous: str | None,
    requested: str | None = None,
) -> tuple[str, str | None]:
    restore = requested or previous
    if not restore:
        raise ValueError("No previous version to restore")
    return restore, current_active
