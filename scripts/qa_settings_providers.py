"""Capture Settings providers group (light + dark) for Appendix C evidence."""

from pathlib import Path

from playwright.sync_api import sync_playwright

from playwright.sync_api import sync_playwright

OUT = Path("/workspace/docs/qa-screenshots")
OUT.mkdir(parents=True, exist_ok=True)
BASE = "http://127.0.0.1:5173"

PROVIDERS = {
    "providers": {
        "oanda": {
            "status": "configured",
            "fields": {
                "OANDA_API_TOKEN": {"status": "configured", "last4": "42ab", "source": "settings"},
                "OANDA_ACCOUNT_ID": {"status": "configured", "last4": "0013", "source": "env"},
                "OANDA_ENV": {"status": "configured", "value": "practice", "source": "settings"},
            },
        },
        "twelve": {
            "status": "missing",
            "fields": {
                "TWELVE_DATA_API_KEY": {"status": "missing", "last4": ""},
                "PRICE_DIVERGENCE_BPS": {"status": "configured", "value": "15", "source": "env"},
            },
        },
        "finnhub": {"status": "missing", "fields": {"FINNHUB_API_KEY": {"status": "missing", "last4": ""}}},
        "metaapi": {"status": "missing", "fields": {"METAAPI_TOKEN": {"status": "missing", "last4": ""}}},
        "anthropic": {
            "status": "configured",
            "fields": {"ANTHROPIC_API_KEY": {"status": "configured", "last4": "k9z1", "source": "settings"}},
        },
        "telegram": {"status": "missing", "fields": {"TELEGRAM_BOT_TOKEN": {"status": "missing", "last4": ""}}},
        "optional": {"status": "missing", "fields": {}},
    },
    "system": {"postgres": "disconnected", "redis": "disconnected"},
    "audit": [{"key": "ANTHROPIC_API_KEY", "action": "set", "at": "2026-08-27T00:00:00+00:00"}],
    "hot_reload": {"api": True, "generation": 1, "workers": "reload overlay per job"},
}


def mock(route):
    url = route.request.url
    if "/api/settings/providers" in url:
        return route.fulfill(json=PROVIDERS)
    if "/api/" in url or "/health" in url:
        return route.fulfill(json={"ok": True, "feeds": {"oanda": {"status": "disconnected"}}})
    return route.continue_()


def capture(page, theme, name):
    page.goto(BASE + "/login", wait_until="domcontentloaded")
    page.evaluate(
        f"""() => {{
          localStorage.setItem('zorro.token', 'qa');
          localStorage.setItem('zorro.lang', 'en');
          localStorage.setItem('zorro.theme', '{theme}');
          localStorage.setItem('zorro-desk', JSON.stringify({{
            state: {{
              token: 'qa', language: 'en', theme: '{theme}',
              modelId: 'claude-sonnet-5', symbol: 'XAU_USD', timeframe: '15m',
              tier: 'deep', banner: null, modal: null, modalPayload: null, health: 'disconnected'
            }}, version: 0
          }}));
        }}"""
    )
    page.goto(BASE + "/settings", wait_until="domcontentloaded")
    page.wait_for_selector("[data-testid=settings-providers]", timeout=15000)
    page.evaluate(
        f"""() => {{
          document.documentElement.classList.toggle('dark', '{theme}' === 'dark');
          if ('{theme}' === 'light') document.documentElement.classList.remove('dark');
        }}"""
    )
    page.wait_for_timeout(400)
    path = OUT / f"{name}.png"
    page.screenshot(path=str(path), full_page=True, animations="disabled")
    print("wrote", path.name, path.stat().st_size)


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path="/usr/local/bin/google-chrome",
            args=["--headless=new", "--no-sandbox", "--disable-gpu", "--font-render-hinting=none"],
        )
        for theme, fname in (("dark", "settings-providers"), ("light", "settings-providers-light")):
            ctx = browser.new_context(viewport={"width": 1280, "height": 1600}, locale="en-US")
            page = ctx.new_page()
            page.route("**/*", mock)
            capture(page, theme, fname)
            ctx.close()
        browser.close()


if __name__ == "__main__":
    run()
