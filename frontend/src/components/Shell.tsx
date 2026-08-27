import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import {
  LayoutGrid,
  Menu,
  MessageSquare,
  ScanSearch,
  Settings,
  ShieldAlert,
  X,
} from "lucide-react";
import { useDesk } from "../store";
import { Modals } from "./Modals";
import { applyDir } from "../i18n";
import { useEffect, useState } from "react";
import { api } from "../lib/api";

const primary = [
  { to: "/", key: "ask", icon: MessageSquare },
  { to: "/today", key: "today", icon: ScanSearch },
  { to: "/build", key: "build", icon: LayoutGrid },
];

const more = [
  { to: "/chart", key: "chart" },
  { to: "/recommendations", key: "recommendations" },
  { to: "/watchlist", key: "watchlist" },
  { to: "/exposure", key: "exposure" },
  { to: "/account", key: "account" },
  { to: "/strategies", key: "strategies" },
  { to: "/demo", key: "demo" },
  { to: "/bots", key: "bots" },
  { to: "/memory", key: "memory" },
  { to: "/review", key: "review" },
  { to: "/settings", key: "settings" },
  { to: "/history", key: "history" },
];

function ActiveMarker() {
  return <span aria-hidden className="active-marker" />;
}

function railLinkClass(active: boolean) {
  return `relative flex min-h-11 lg:min-h-10 items-center gap-3 rounded-lg px-3 text-sm font-medium ${
    active ? "bg-[var(--sidebar-active-bg)] text-foreground" : "text-muted-fg hover:bg-muted hover:text-foreground"
  }`;
}

export function Shell() {
  const { t, i18n } = useTranslation();
  const loc = useLocation();
  const nav = useNavigate();
  const banner = useDesk((s) => s.banner);
  const theme = useDesk((s) => s.theme);
  const language = useDesk((s) => s.language);
  const openModal = useDesk((s) => s.openModal);
  const symbol = useDesk((s) => s.symbol);
  const timeframe = useDesk((s) => s.timeframe);
  const setTimeframe = useDesk((s) => s.setTimeframe);
  const modelId = useDesk((s) => s.modelId);
  const setModel = useDesk((s) => s.setModel);
  const setTheme = useDesk((s) => s.setTheme);
  const setLang = useDesk((s) => s.setLang);
  const health = useDesk((s) => s.health);
  const setHealth = useDesk((s) => s.setHealth);
  const setBanner = useDesk((s) => s.setBanner);
  const [drawer, setDrawer] = useState(false);
  const [convs, setConvs] = useState<{ id: string; title: string }[]>([]);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
    if (theme === "light") document.documentElement.classList.remove("dark");
    void i18n.changeLanguage(language);
    applyDir(language);
  }, [theme, language, i18n]);

  useEffect(() => {
    void api
      .health()
      .then((h) => {
        const o = h.feeds?.oanda?.status;
        setHealth(o || "disconnected");
        if (o && o !== "connected") setBanner("unreliable");
      })
      .catch(() => {
        setHealth("disconnected");
      });
    void api.conversations().then(setConvs).catch(() => setConvs([]));
  }, [setHealth, setBanner]);

  const rail = (
    <aside className="flex h-full w-64 flex-col border-e border-line bg-sidebar" data-testid="rail">
      <div className="flex items-center justify-between px-4 h-14">
        <span className="font-semibold tracking-tight">{t("app.name")}</span>
        <button className="md:hidden touch-target" onClick={() => setDrawer(false)} aria-label={t("buttons.close")}>
          <X size={18} />
        </button>
      </div>
      <nav aria-label={t("nav.ask")} className="flex flex-col gap-0.5 px-2 py-2">
        {primary.map((p) => {
          const active = loc.pathname === p.to;
          return (
            <NavLink key={p.to} to={p.to} className={railLinkClass(active)} onClick={() => setDrawer(false)}>
              {active && <ActiveMarker />}
              <p.icon size={16} aria-hidden />
              {t(`nav.${p.key}`)}
            </NavLink>
          );
        })}
      </nav>
      <div className="px-4 pt-2 text-xs text-muted-fg">{t("ask.conversations")}</div>
      <ul className="flex-1 overflow-auto px-2 py-1">
        {convs.length === 0 && <li className="px-3 py-2 text-xs text-muted-fg">{t("empty.chats")}</li>}
        {convs.map((c) => (
          <li key={c.id}>
            <NavLink to="/" className="block rounded-lg px-3 py-2 text-sm text-muted-fg hover:bg-muted">
              {c.title || t("ask.newChat")}
            </NavLink>
          </li>
        ))}
      </ul>
      <nav className="border-t border-line px-2 py-2 max-h-48 overflow-auto">
        {more.map((m) => {
          const active = loc.pathname === m.to || loc.pathname.startsWith(m.to + "/");
          return (
            <NavLink key={m.to} to={m.to} className={railLinkClass(active)} onClick={() => setDrawer(false)}>
              {active && <ActiveMarker />}
              {t(`nav.${m.key}`)}
            </NavLink>
          );
        })}
      </nav>
    </aside>
  );

  return (
    <div className="min-h-full bg-background text-foreground">
      <a className="skip-link" href="#main">
        {t("a11y.skip")}
      </a>
      {banner && (
        <div role="status" className="banner-unreliable text-center text-sm py-2 px-3" data-testid="price-banner">
          {t("banner.unreliable")}
        </div>
      )}
      <div className="flex min-h-full">
        <div className="hidden md:block sticky top-0 h-screen">{rail}</div>
        {drawer && (
          <div className="md:hidden fixed inset-0 z-40 flex">
            <div className="absolute inset-0 bg-black/50" onClick={() => setDrawer(false)} />
            <div className="relative z-10 h-full">{rail}</div>
          </div>
        )}
        <div className="flex-1 flex flex-col min-w-0">
          <header className="flex items-center justify-between border-b border-line px-3 h-14 gap-2 overflow-hidden">
            <div className="flex items-center gap-2 min-w-0">
              <button className="md:hidden touch-target" onClick={() => setDrawer(true)} aria-label={t("nav.more")}>
                <Menu size={18} />
              </button>
              <button className="touch-target px-3 rounded-lg border border-line text-sm max-w-[7rem] sm:max-w-none truncate" onClick={() => openModal("symbol")}>
                {symbol || t("ask.pickSymbol")}
              </button>
              {["1m", "5m", "15m", "1h", "4h", "1d"].map((tf) => (
                <button
                  key={tf}
                  className={`hidden lg:inline-flex px-2 min-h-10 rounded text-sm ${timeframe === tf ? "bg-muted text-foreground" : "text-muted-fg"}`}
                  onClick={() => setTimeframe(tf)}
                >
                  {tf}
                </button>
              ))}
            </div>
            <div className="flex items-center gap-1 min-w-0 overflow-hidden">
              <span
                className={`shrink-0 w-2.5 h-2.5 rounded-full ${health === "connected" ? "bg-buy" : "bg-warning"}`}
                title={health}
                data-testid="health-chip"
                aria-label={health === "connected" ? t("health.connected") : t("health.degraded")}
              />
              <select
                className="hidden md:block bg-muted rounded px-2 min-h-10 text-sm max-w-[14rem]"
                value={modelId}
                onChange={(e) => setModel(e.target.value)}
                aria-label={t("ask.model")}
              >
                {["claude-fable-5", "claude-opus-5", "claude-opus-4-8", "claude-sonnet-5", "claude-opus-4-7"].map((m) => (
                  <option key={m} value={m}>
                    {t(`models.${m}`)}
                  </option>
                ))}
              </select>
              <select
                className="bg-muted rounded px-2 min-h-10 text-sm"
                value={language}
                onChange={(e) => setLang(e.target.value as "en" | "tr" | "ar")}
                aria-label={t("settings.language")}
              >
                <option value="en">EN</option>
                <option value="tr">TR</option>
                <option value="ar">AR</option>
              </select>
              <button className="touch-target px-2 text-sm" onClick={() => setTheme(theme === "dark" ? "light" : "dark")} aria-label={t("settings.theme")}>
                {theme === "dark" ? "☀" : "☾"}
              </button>
              <button className="touch-target px-2 text-sell" onClick={() => openModal("kill")} aria-label={t("buttons.kill")}>
                <ShieldAlert size={18} />
              </button>
              <button className="touch-target px-2" onClick={() => nav("/settings")} aria-label={t("nav.settings")}>
                <Settings size={18} />
              </button>
            </div>
          </header>
          <main id="main" className="flex-1 pb-20 md:pb-6 px-4 py-4 max-w-6xl w-full mx-auto">
            <Outlet />
            <p className="mt-10 text-xs text-muted-fg leading-relaxed">{t("app.disclaimer")}</p>
          </main>
        </div>
      </div>
      <nav className="md:hidden fixed bottom-0 inset-x-0 border-t border-line bg-card/95 backdrop-blur flex justify-around py-1 pb-[env(safe-area-inset-bottom)]">
        {primary.map((p) => (
          <NavLink key={p.to} to={p.to} className="flex flex-col items-center text-[11px] py-2 px-3 touch-target">
            <p.icon size={20} />
            {t(`nav.${p.key}`)}
          </NavLink>
        ))}
      </nav>
      <Modals />
    </div>
  );
}
