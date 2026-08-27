import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import {
  Bot,
  LayoutGrid,
  LineChart,
  MessageSquare,
  MoreHorizontal,
  ScanSearch,
  Settings,
  ShieldAlert,
} from "lucide-react";
import { useDesk } from "../store";
import { Modals } from "./Modals";
import { applyDir } from "../i18n";
import { useEffect } from "react";

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

export function Shell() {
  const { t, i18n } = useTranslation();
  const loc = useLocation();
  const nav = useNavigate();
  const banner = useDesk((s) => s.banner);
  const theme = useDesk((s) => s.theme);
  const language = useDesk((s) => s.language);
  const openModal = useDesk((s) => s.openModal);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
    document.documentElement.classList.toggle("light", theme === "light");
    if (theme === "light") document.documentElement.classList.remove("dark");
    void i18n.changeLanguage(language);
    applyDir(language);
  }, [theme, language, i18n]);

  return (
    <div className={`min-h-full ${theme === "light" ? "bg-slate-100 text-slate-900" : "bg-desk text-slate-100"}`}>
      {banner && (
        <div role="status" className="bg-red-600 text-white text-center text-sm py-2 px-3">
          {t("banner.unreliable")}
        </div>
      )}
      <header className="hidden md:flex items-center justify-between border-b border-line px-4 h-14">
        <div className="flex items-center gap-6">
          <span className="font-semibold tracking-tight">{t("app.name")}</span>
          {primary.map((p) => (
            <NavLink
              key={p.to}
              to={p.to}
              className={({ isActive }) =>
                `text-sm touch-target flex items-center ${isActive || loc.pathname === p.to ? "text-accent" : "text-slate-400 hover:text-white"}`
              }
            >
              {t(`nav.${p.key}`)}
            </NavLink>
          ))}
          <details className="relative">
            <summary className="text-sm text-slate-400 cursor-pointer list-none flex items-center gap-1">
              <MoreHorizontal size={16} aria-hidden /> {t("nav.more")}
            </summary>
            <div className="absolute z-20 mt-2 w-56 rounded-lg border border-line bg-card p-2 shadow-xl">
              {more.map((m) => (
                <NavLink key={m.to} to={m.to} className="block px-3 py-2 text-sm rounded hover:bg-muted">
                  {t(`nav.${m.key}`)}
                </NavLink>
              ))}
            </div>
          </details>
        </div>
        <div className="flex items-center gap-2">
          <button className="touch-target px-3 text-sm text-red-400" onClick={() => openModal("kill")} aria-label={t("buttons.kill")}>
            <ShieldAlert size={18} />
          </button>
          <button className="touch-target px-3" onClick={() => nav("/settings")} aria-label={t("nav.settings")}>
            <Settings size={18} />
          </button>
        </div>
      </header>
      <main className="pb-20 md:pb-6 max-w-6xl mx-auto px-4 py-4">
        <Outlet />
        <p className="mt-10 text-xs text-slate-500 leading-relaxed">{t("app.disclaimer")}</p>
      </main>
      <nav className="md:hidden fixed bottom-0 inset-x-0 border-t border-line bg-card/95 backdrop-blur flex justify-around py-1 pb-[env(safe-area-inset-bottom)]">
        {primary.map((p) => (
          <NavLink key={p.to} to={p.to} className="flex flex-col items-center text-[11px] py-2 px-3 touch-target">
            <p.icon size={20} />
            {t(`nav.${p.key}`)}
          </NavLink>
        ))}
        <details className="relative">
          <summary className="flex flex-col items-center text-[11px] py-2 px-3 list-none">
            <MoreHorizontal size={20} />
            {t("nav.more")}
          </summary>
          <div className="absolute bottom-14 right-0 w-56 rounded-lg border border-line bg-card p-2 max-h-80 overflow-auto">
            {more.map((m) => (
              <NavLink key={m.to} to={m.to} className="block px-3 py-2 text-sm">
                {t(`nav.${m.key}`)}
              </NavLink>
            ))}
          </div>
        </details>
      </nav>
      <Modals />
    </div>
  );
}
