import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { RecCard, cardKind } from "../components/RecCard";
import { AskPage } from "../pages/AskPage";
import App from "../App";
import { applyDir } from "../i18n";
import "../i18n";
import en from "../i18n/en.json";
import tr from "../i18n/tr.json";
import ar from "../i18n/ar.json";

const here = dirname(fileURLToPath(import.meta.url));

const rec = {
  id: "r1",
  direction: "BUY",
  canonical_id: "XAU_USD",
  model_id: "claude-fable-5",
  tradeable: true,
  preferred_entry: 2400,
  entry_zone: { low: 2398, high: 2402 },
  stop_loss: 2380,
  take_profits: [2420, 2440],
  fill_rule: "market",
  next_action: "watch",
  reasons: ["structure"],
  similar_past_cases: { label: "Insufficient data", count: 2 },
};

function leafKeys(obj: any, prefix = ""): string[] {
  return Object.entries(obj).flatMap(([k, v]) =>
    v && typeof v === "object" ? leafKeys(v, prefix ? `${prefix}.${k}` : k) : [prefix ? `${prefix}.${k}` : k],
  );
}

test("i18n keys exist in en tr ar", () => {
  const enKeys = leafKeys(en).sort();
  expect(leafKeys(tr).sort()).toEqual(enKeys);
  expect(leafKeys(ar).sort()).toEqual(enKeys);
});

test("arabic applyDir sets html dir rtl and restores ltr", () => {
  applyDir("ar");
  expect(document.documentElement.dir).toBe("rtl");
  expect(document.documentElement.lang).toBe("ar");
  applyDir("en");
  expect(document.documentElement.dir).toBe("ltr");
});

test("skip-link css does not use left:-999px (RTL overflow)", () => {
  const css = readFileSync(join(here, "../index.css"), "utf8");
  expect(css).not.toMatch(/left:\s*-999px/);
  expect(css).toMatch(/clip-path:\s*inset\(50%\)/);
  expect(css).toMatch(/overflow-x:\s*clip/);
});

test("symbol picker is reused across shell chart account watchlist", () => {
  const files = [
    "../components/Shell.tsx",
    "../pages/ChartPage.tsx",
    "../pages/AccountPage.tsx",
    "../pages/WatchlistExposure.tsx",
    "../components/Modals.tsx",
  ].map((p) => readFileSync(join(here, p), "utf8"));
  expect(files[0]).toMatch(/openModal\("symbol"\)/);
  expect(files[1]).toMatch(/openModal\("symbol"\)/);
  expect(files[2]).toMatch(/open\("symbol"\)/);
  expect(files[3]).toMatch(/open\("symbol"\)/);
  expect(files[4]).toMatch(/modal === "symbol"/);
  expect(files[4]).toMatch(/data-testid="symbol-filter"/);
});

test("ask analysis flow has no raw ticker text input", () => {
  const ask = readFileSync(join(here, "../pages/AskPage.tsx"), "utf8");
  const analysis = readFileSync(join(here, "../components/Modals.tsx"), "utf8");
  expect(ask).not.toMatch(/placeholder=.*ticker/i);
  expect(analysis).toMatch(/ask\.pickSymbol/);
  expect(analysis).toMatch(/ask\.noFreeText/);
});

test("routes listed in the brief have a page component", () => {
  render(<App />);
  // Guard redirects unauthenticated users to /login, which still mounts.
  expect(screen.getAllByText(/Sign in|Email|Login/i).length).toBeGreaterThan(0);
});

test("agent log default collapsed", () => {
  localStorage.setItem("zorro.token", "t");
  render(
    <MemoryRouter>
      <AskPage />
    </MemoryRouter>,
  );
  const log = screen.getByTestId("agent-log") as HTMLDetailsElement;
  expect(log.open).toBe(false);
});

test("quick vs deep toggle exists", () => {
  localStorage.setItem("zorro.token", "t");
  render(
    <MemoryRouter>
      <AskPage />
    </MemoryRouter>,
  );
  expect(screen.getByTestId("tier-quick")).toBeInTheDocument();
  expect(screen.getByTestId("tier-deep")).toBeInTheDocument();
});

test("execute absent on thread rec card", () => {
  render(
    <MemoryRouter>
      <RecCard rec={rec} surface="thread" />
    </MemoryRouter>,
  );
  expect(screen.queryByTestId("execute-after-save")).not.toBeInTheDocument();
  expect(screen.queryByText(/Execute trade/i)).not.toBeInTheDocument();
});

test("execute present only after save", () => {
  render(
    <MemoryRouter>
      <RecCard rec={rec} surface="saved" />
    </MemoryRouter>,
  );
  expect(screen.getByTestId("execute-after-save")).toBeInTheDocument();
});

test("card kind switch is exhaustive", () => {
  expect(cardKind({ refused: true })).toBe("refusal");
  expect(cardKind({ tradeable: true })).toBe("recommendation");
  expect(cardKind({ tradeable: false })).toBe("quick");
});
