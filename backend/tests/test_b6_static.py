"""B6 static forbidden list against app code (not this brief, not lockfiles)."""

from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1] / "app"
FRONTEND = Path(__file__).resolve().parents[2] / "frontend" / "src"

EXCLUSION_HINTS = (
    "no mcp",
    "not mcp",
    "exclusion",
    "wait is forbidden",
    "wait is not",
    "never a monthly return",
    "does not promise monthly",
    "never monthly return",
)


def _iter_src():
    for root in (BACKEND, FRONTEND):
        for path in root.rglob("*"):
            if path.suffix in {".py", ".ts", ".tsx", ".json"} and "node_modules" not in path.parts:
                yield path


def test_model_picker_has_no_openai_gpt_gemini_grok():
    picker = (FRONTEND / "components" / "Shell.tsx").read_text()
    settings = (FRONTEND / "pages" / "SettingsLogin.tsx").read_text()
    blob = picker + settings
    for token in ("openai", "gpt-4", "gemini", "grok"):
        assert token not in blob.lower()
    for model in (
        "claude-fable-5",
        "claude-opus-5",
        "claude-opus-4-8",
        "claude-sonnet-5",
        "claude-opus-4-7",
    ):
        assert model in picker
        assert model in settings


def test_no_celery_redux_in_app_code():
    hits = []
    for path in _iter_src():
        text = path.read_text(errors="ignore").lower()
        if "celery" in text or " from 'redux" in text or "from redux" in text or "react-redux" in text:
            hits.append(str(path))
    assert hits == []


def test_no_mcp_server_dependency_in_app():
    hits = []
    for path in _iter_src():
        text = path.read_text(errors="ignore")
        lower = text.lower()
        if "@modelcontextprotocol" in lower or "mcp.true-north" in lower:
            hits.append(str(path))
        if "mcp" in lower:
            if path.suffix == ".json":
                continue
            # comments / exclusion documentation are allowed
            for line in text.splitlines():
                l = line.lower()
                if "mcp" in l and not l.strip().startswith(("#", "//", "*", "/*")):
                    if any(h in l for h in EXCLUSION_HINTS) or '"mcp": false' in l or "'mcp': false" in l:
                        continue
                    if "no mcp" in l or "not mcp" in l or "without mcp" in l:
                        continue
                    if "mcp key" in l:
                        continue
                    hits.append(f"{path}:{line.strip()}")
    assert hits == []


def test_no_crypto_venues_or_whale_radar():
    hits = []
    for path in _iter_src():
        text = path.read_text(errors="ignore").lower()
        for token in ("whale", "polymarket", "okx", "bitget", "bingx"):
            if token in text:
                hits.append(f"{path}:{token}")
    assert hits == []


def test_telegram_stopall_imports_shared_kill():
    text = (BACKEND / "telegram" / "bot.py").read_text()
    assert "from app.bots.kill import apply_kill_switch" in text
    assert "KillSwitch(" not in text


def test_indicators_do_not_use_metaapi():
    text = (BACKEND / "indicators.py").read_text()
    assert "metaapi" not in text.lower()
