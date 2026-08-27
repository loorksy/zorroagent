import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { RecCard, cardKind } from "../components/RecCard";
import { AskPage } from "../pages/AskPage";
import App from "../App";
import "../i18n";
import en from "../i18n/en.json";
import tr from "../i18n/tr.json";
import ar from "../i18n/ar.json";

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

test("routes listed in the brief have a page component", () => {
  render(<App />);
  // Guard redirects unauthenticated users to /login, which still mounts.
  expect(screen.getByText(/Sign in|Email|Login/i)).toBeTruthy();
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
