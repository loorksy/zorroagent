import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { vi } from "vitest";
import { SettingsPage } from "../pages/SettingsLogin";
import "../i18n";

const payload = {
  providers: {
    oanda: {
      status: "missing",
      fields: {
        OANDA_API_TOKEN: { status: "missing", last4: "" },
        OANDA_ACCOUNT_ID: { status: "missing", last4: "" },
        OANDA_ENV: { status: "configured", value: "practice", source: "env" },
      },
    },
    twelve: { status: "missing", fields: { TWELVE_DATA_API_KEY: { status: "missing", last4: "" }, PRICE_DIVERGENCE_BPS: { value: "15" } } },
    finnhub: { status: "missing", fields: { FINNHUB_API_KEY: { status: "missing", last4: "" } } },
    metaapi: { status: "missing", fields: { METAAPI_TOKEN: { status: "missing", last4: "" } } },
    anthropic: { status: "missing", fields: { ANTHROPIC_API_KEY: { status: "missing", last4: "" } } },
    telegram: { status: "missing", fields: { TELEGRAM_BOT_TOKEN: { status: "missing", last4: "" } } },
    optional: { status: "missing", fields: {} },
  },
  system: { postgres: "disconnected", redis: "disconnected" },
  audit: [],
};

beforeEach(() => {
  localStorage.setItem("zorro.token", "t");
  global.fetch = vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input);
    if (url.includes("/api/settings/providers") && !url.includes("/test")) {
      return { ok: true, status: 200, json: async () => payload, text: async () => JSON.stringify(payload) } as Response;
    }
    return { ok: true, status: 200, json: async () => ({}), text: async () => "{}" } as Response;
  }) as any;
});

test("settings providers groups exist and have no MCP", async () => {
  render(
    <MemoryRouter>
      <SettingsPage />
    </MemoryRouter>,
  );
  expect(await screen.findByTestId("settings-providers")).toBeInTheDocument();
  expect(screen.getByText("Market data")).toBeInTheDocument();
  expect(screen.getByText("News / calendar")).toBeInTheDocument();
  expect(screen.getByText("Execution")).toBeInTheDocument();
  expect(screen.getByText("Anthropic API key")).toBeInTheDocument();
  expect(screen.getAllByText(/Test connection/).length).toBeGreaterThan(0);
  const html = document.body.innerHTML.toLowerCase();
  expect(html).not.toContain("mcp"); // no MCP
  expect(html).not.toContain("sk-ant-");
});

test("secret inputs are masked", async () => {
  render(
    <MemoryRouter>
      <SettingsPage />
    </MemoryRouter>,
  );
  await screen.findByTestId("settings-providers");
  const secrets = document.querySelectorAll('input[type="password"]');
  expect(secrets.length).toBeGreaterThanOrEqual(5);
});
