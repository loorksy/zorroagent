import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useDesk } from "../store";
import { api } from "../lib/api";
import { applyDir } from "../i18n";

const MODELS = ["claude-fable-5", "claude-opus-5", "claude-opus-4-8", "claude-sonnet-5", "claude-opus-4-7"];

export function SettingsPage() {
  const { t, i18n } = useTranslation();
  const desk = useDesk();
  return (
    <div className="max-w-md space-y-4">
      <h1 className="text-xl font-semibold">{t("nav.settings")}</h1>
      <label className="block text-sm">
        {t("settings.language")}
        <select
          className="w-full bg-muted rounded px-3 py-2"
          value={desk.language}
          onChange={(e) => {
            const l = e.target.value as "en" | "tr" | "ar";
            desk.setLang(l);
            void i18n.changeLanguage(l);
            applyDir(l);
            void api.settings({ language: l }).catch(() => {});
          }}
        >
          <option value="en">English</option>
          <option value="tr">Türkçe</option>
          <option value="ar">العربية</option>
        </select>
      </label>
      <label className="block text-sm">
        {t("settings.theme")}
        <select className="w-full bg-muted rounded px-3 py-2" value={desk.theme} onChange={(e) => desk.setTheme(e.target.value as any)}>
          <option value="dark">{t("settings.dark")}</option>
          <option value="light">{t("settings.light")}</option>
        </select>
      </label>
      <label className="block text-sm">
        {t("settings.quickDefault")}
        <select className="w-full bg-muted rounded px-3 py-2" defaultValue="claude-sonnet-5" onChange={(e) => api.settings({ quick_model: e.target.value })}>
          {MODELS.map((m) => (
            <option key={m} value={m}>
              {t(`models.${m}`)}
            </option>
          ))}
        </select>
      </label>
      <label className="block text-sm">
        {t("settings.deepDefault")}
        <select className="w-full bg-muted rounded px-3 py-2" defaultValue="claude-fable-5" onChange={(e) => api.settings({ deep_model: e.target.value })}>
          {MODELS.map((m) => (
            <option key={m} value={m}>
              {t(`models.${m}`)}
            </option>
          ))}
        </select>
      </label>
      <button className="rounded bg-muted px-3 py-2" onClick={() => desk.openModal("credentials")}>
        {t("modals.credentials")}
      </button>
      <button className="rounded bg-muted px-3 py-2" onClick={() => desk.openModal("disclaimer")}>
        {t("modals.disclaimer")}
      </button>
      <button className="rounded bg-muted px-3 py-2" onClick={() => desk.openModal("kill")}>
        {t("buttons.kill")}
      </button>
    </div>
  );
}

export function LoginPage() {
  const { t } = useTranslation();
  const desk = useDesk();
  const [email, setEmail] = useState("operator@local");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState("");
  return (
    <form
      className="max-w-sm mx-auto mt-24 space-y-3 px-4"
      onSubmit={async (e) => {
        e.preventDefault();
        try {
          const r = await api.login(email, password);
          desk.setToken(r.access_token);
          window.location.href = "/";
        } catch {
          setErr(t("auth.error"));
        }
      }}
    >
      <h1 className="text-xl font-semibold">{t("nav.login")}</h1>
      <label className="block text-sm">
        {t("auth.email")}
        <input className="w-full bg-muted rounded px-3 py-2" value={email} onChange={(e) => setEmail(e.target.value)} placeholder={t("auth.emailPlaceholder")} required />
      </label>
      <label className="block text-sm">
        {t("auth.password")}
        <input type="password" className="w-full bg-muted rounded px-3 py-2" value={password} onChange={(e) => setPassword(e.target.value)} placeholder={t("auth.passwordPlaceholder")} required />
      </label>
      {err && <p className="text-sell text-sm">{err}</p>}
      <button className="w-full rounded liquid-metal py-2">{t("auth.signIn")}</button>
      <p className="text-xs text-muted-fg">{t("app.disclaimer")}</p>
    </form>
  );
}
