"""Playwright visual pack: EN/TR/AR × light/dark × 390/768/1280.

Method: Google Chrome headless against Vite with API routes mocked.
Real DOM screenshots, not generated mockups.
RTL skip-link uses clip (not left:-999px) so Arabic viewports paint the desk.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path("/workspace/docs/qa-screenshots")
OUT.mkdir(parents=True, exist_ok=True)
BASE = "http://127.0.0.1:5173"
MIN_BYTES = 8000

REC = {
    "id": "rec-qa-1",
    "direction": "BUY",
    "canonical_id": "XAU_USD",
    "model_id": "claude-fable-5",
    "tradeable": True,
    "preferred_entry": 2400,
    "entry_zone": {"low": 2398, "high": 2402},
    "stop_loss": 2380,
    "take_profits": [2420, 2440],
    "fill_rule": "confirming_close",
    "next_action": "watch close",
    "reasons": ["HTF structure", "demand zone", "ATR buffer"],
    "similar_past_cases": {"label": "Insufficient data", "count": 4, "win_rate": None},
    "gates": [{"gate_id": "G1", "name": "news", "status": "pass", "reason": ""}],
}

CONFIRM_LABELS = ("Recommendation confirmation", "Tavsiye onayı", "تأكيد التوصية")


def mock(route):
    url = route.request.url
    if "/api/" in url or "/health" in url:
        if "/instruments" in url:
            return route.fulfill(
                json={
                    "instruments": [
                        {
                            "canonical_id": "XAU_USD",
                            "display_symbol": "XAU/USD",
                            "asset_class": "metal",
                            "tradable": True,
                        }
                    ],
                    "source": "OANDA",
                }
            )
        if "/api/settings/providers" in url:
            return route.fulfill(
                json={
                    "providers": {
                        "oanda": {
                            "status": "missing",
                            "fields": {
                                "OANDA_API_TOKEN": {"status": "missing", "last4": ""},
                                "OANDA_ACCOUNT_ID": {"status": "missing", "last4": ""},
                                "OANDA_ENV": {"status": "configured", "value": "practice", "source": "env"},
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
                        "anthropic": {"status": "missing", "fields": {"ANTHROPIC_API_KEY": {"status": "missing", "last4": ""}}},
                        "telegram": {"status": "missing", "fields": {"TELEGRAM_BOT_TOKEN": {"status": "missing", "last4": ""}}},
                        "optional": {"status": "missing", "fields": {}},
                    },
                    "system": {"postgres": "disconnected", "redis": "disconnected"},
                    "audit": [],
                    "hot_reload": {"api": True, "workers": "reload overlay per job"},
                }
            )
        if "/conversations" in url:
            return route.fulfill(json=[{"id": "c1", "title": "XAU_USD"}])
        if "/recommendations" in url:
            return route.fulfill(json=[REC])
        if "/bots" in url:
            return route.fulfill(json=[{"id": "b1", "name": "demo-bot", "status": "demo_running", "mode": "demo"}])
        if "/candles" in url:
            return route.fulfill(json={"ok": True, "candles": [], "source": "OANDA"})
        if url.rstrip("/").endswith("/health") or "/healthz" in url:
            return route.fulfill(
                json={
                    "ok": True,
                    "disclaimer": "Personal analysis",
                    "feeds": {
                        "oanda": {"status": "disconnected", "detail": "no key"},
                        "twelve_data": {"status": "disconnected"},
                        "metaapi": {"status": "disconnected"},
                    },
                }
            )
        return route.fulfill(json={})
    return route.continue_()


def apply_state(page, lang, theme, banner, rec):
    rec_json = json.dumps([{"role": "assistant", "content": "Deep Analysis", "rec": REC}]) if rec else "[]"
    banner_js = '"unreliable"' if banner else "null"
    page.evaluate(
        f"""() => {{
          localStorage.setItem('zorro.token', 'qa');
          localStorage.setItem('zorro.lang', '{lang}');
          localStorage.setItem('zorro.theme', '{theme}');
          sessionStorage.setItem('zorro.qa.seed', {json.dumps(rec_json)});
          localStorage.setItem('zorro-desk', JSON.stringify({{
            state: {{
              token: 'qa', language: '{lang}', theme: '{theme}',
              modelId: 'claude-sonnet-5', symbol: 'XAU_USD', timeframe: '15m',
              tier: 'deep', banner: {banner_js}, modal: null, modalPayload: null, health: 'disconnected'
            }}, version: 0
          }}));
        }}"""
    )


def reset_scroll(page):
    page.evaluate(
        """() => {
          document.documentElement.scrollTop = 0;
          document.body.scrollTop = 0;
          document.documentElement.scrollLeft = 0;
          document.body.scrollLeft = 0;
        }"""
    )


def shot(page, name):
    reset_scroll(page)
    page.wait_for_timeout(120)
    path = OUT / f"{name}.png"
    page.screenshot(path=str(path), full_page=False, animations="disabled")
    size = path.stat().st_size
    print("wrote", path.name, size)
    if size < MIN_BYTES:
        print("WARN small screenshot", path.name, size, file=sys.stderr)
    return size


def open_desk(page, lang, theme, banner, rec, path="/"):
    page.goto(BASE + "/login", wait_until="domcontentloaded")
    apply_state(page, lang, theme, banner, rec)
    page.goto(BASE + path, wait_until="domcontentloaded")
    page.wait_for_function("() => document.getElementById('main') || document.querySelector('form')")
    page.evaluate("() => document.fonts && document.fonts.ready")
    page.wait_for_timeout(450)
    if rec and path == "/":
        page.wait_for_selector("[data-testid=rec-card]", timeout=8000)


def run():
    langs = ["en", "tr", "ar"]
    themes = ["light", "dark"]
    viewports = [(390, 844), (768, 1024), (1280, 800)]
    too_small = []
    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path="/usr/local/bin/google-chrome",
            args=["--headless=new", "--no-sandbox", "--disable-gpu", "--font-render-hinting=none"],
        )
        for lang in langs:
            for theme in themes:
                for w, h in viewports:
                    tag = f"{lang}-{theme}-{w}"
                    ctx = browser.new_context(
                        viewport={"width": w, "height": h},
                        locale="ar" if lang == "ar" else ("tr-TR" if lang == "tr" else "en-US"),
                    )
                    page = ctx.new_page()
                    page.route("**/*", mock)

                    open_desk(page, lang, theme, True, False, "/")
                    if shot(page, f"{tag}-ask-empty") < MIN_BYTES:
                        too_small.append(f"{tag}-ask-empty")
                    if shot(page, f"{tag}-banner") < MIN_BYTES:
                        too_small.append(f"{tag}-banner")

                    open_desk(page, lang, theme, False, True, "/")
                    if shot(page, f"{tag}-ask-rec") < MIN_BYTES:
                        too_small.append(f"{tag}-ask-rec")
                    for label in CONFIRM_LABELS:
                        loc = page.get_by_text(label, exact=False)
                        if loc.count():
                            loc.first.click()
                            break
                    page.wait_for_timeout(250)
                    if shot(page, f"{tag}-confirm-rec") < MIN_BYTES:
                        too_small.append(f"{tag}-confirm-rec")
                    exe = page.locator("[data-testid=execute-after-save]")
                    if exe.count():
                        exe.first.click()
                        page.wait_for_timeout(250)
                    if shot(page, f"{tag}-execute") < MIN_BYTES:
                        too_small.append(f"{tag}-execute")

                    open_desk(page, lang, theme, False, False, "/today")
                    if shot(page, f"{tag}-today") < MIN_BYTES:
                        too_small.append(f"{tag}-today")
                    open_desk(page, lang, theme, False, False, "/chart/XAU_USD")
                    if shot(page, f"{tag}-chart") < MIN_BYTES:
                        too_small.append(f"{tag}-chart")
                    open_desk(page, lang, theme, False, False, "/bots")
                    if shot(page, f"{tag}-bots") < MIN_BYTES:
                        too_small.append(f"{tag}-bots")
                    open_desk(page, lang, theme, False, False, "/settings")
                    if shot(page, f"{tag}-settings") < MIN_BYTES:
                        too_small.append(f"{tag}-settings")
                    open_desk(page, lang, theme, False, False, "/")
                    page.locator("button.text-sell").first.click()
                    page.wait_for_timeout(250)
                    if shot(page, f"{tag}-kill") < MIN_BYTES:
                        too_small.append(f"{tag}-kill")
                    ctx.close()
        browser.close()
    if too_small:
        print("SMALL_SCREENSHOTS", ",".join(too_small), file=sys.stderr)
        raise SystemExit(2)


if __name__ == "__main__":
    run()
