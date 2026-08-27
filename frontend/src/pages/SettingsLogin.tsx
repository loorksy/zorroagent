import { useEffect, useState, type ClipboardEvent, type ReactNode } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useDesk } from "../store";
import { api } from "../lib/api";
import { applyDir } from "../i18n";

const MODELS = ["claude-fable-5", "claude-opus-5", "claude-opus-4-8", "claude-sonnet-5", "claude-opus-4-7"];

type FieldStatus = {
  status?: string;
  last4?: string;
  value?: string;
  source?: string;
};

type ProvidersPayload = {
  providers?: Record<string, { status?: string; fields?: Record<string, FieldStatus> }>;
  system?: { postgres?: string; redis?: string };
};

function forbidCopy(e: ClipboardEvent) {
  e.preventDefault();
}

function SecretField({
  label,
  envName,
  field,
  value,
  onChange,
  onClear,
}: {
  label: string;
  envName: string;
  field?: FieldStatus;
  value: string;
  onChange: (v: string) => void;
  onClear: () => void;
}) {
  const { t } = useTranslation();
  const [reveal, setReveal] = useState(false);
  const configured = field?.status === "configured" && Boolean(field?.last4);
  const placeholder = configured ? `••••${field?.last4}` : t("settings.missing");
  return (
    <label className="block text-sm space-y-1">
      <span className="flex items-baseline justify-between gap-2">
        <span>{label}</span>
        <span className="text-[11px] text-muted-fg font-mono">{envName}</span>
      </span>
      <div className="flex gap-2">
        <input
          className="w-full bg-muted rounded px-3 py-2 min-h-11 select-none"
          type={reveal ? "text" : "password"}
          value={value}
          autoComplete="off"
          autoCorrect="off"
          spellCheck={false}
          placeholder={placeholder}
          onChange={(e) => onChange(e.target.value)}
          onCopy={forbidCopy}
          onCut={forbidCopy}
          aria-label={label}
        />
        <button type="button" className="rounded bg-muted px-2 text-xs min-h-11" onClick={() => setReveal((v) => !v)}>
          {reveal ? t("settings.hide") : t("settings.reveal")}
        </button>
        <button type="button" className="rounded bg-muted px-2 text-xs min-h-11" onClick={onClear}>
          {t("settings.clearField")}
        </button>
      </div>
      <p className="text-[11px] text-muted-fg">
        {configured ? `${t("settings.configured")} · ${t("settings.last4")} ${field?.last4}` : t("settings.missing")}
        {field?.source === "env" ? ` · ${t("settings.sourceEnv")}` : field?.source === "settings" ? ` · ${t("settings.sourceSettings")}` : ""}
      </p>
    </label>
  );
}

function Group({ title, help, children }: { title: string; help?: string; children: ReactNode }) {
  return (
    <section className="rounded-[var(--radius)] border border-border bg-card p-4 space-y-3">
      <div>
        <h2 className="text-sm font-semibold">{title}</h2>
        {help ? <p className="text-xs text-muted-fg mt-1">{help}</p> : null}
      </div>
      {children}
    </section>
  );
}

export function SettingsPage() {
  const { t, i18n } = useTranslation();
  const desk = useDesk();
  const [data, setData] = useState<ProvidersPayload | null>(null);
  const [draft, setDraft] = useState<Record<string, string>>({});
  const [msg, setMsg] = useState("");
  const [testMsg, setTestMsg] = useState<Record<string, { ok: boolean; detail: string }>>({});
  const [linkOnce, setLinkOnce] = useState("");
  const [busy, setBusy] = useState(false);

  const load = () =>
    api
      .providers()
      .then((r) => setData(r))
      .catch(() => setData({ providers: {}, system: { postgres: "disconnected", redis: "disconnected" } }));

  useEffect(() => {
    void load();
  }, []);

  const field = (provider: string, key: string) => data?.providers?.[provider]?.fields?.[key];

  const setKey = (key: string, value: string) => setDraft((d) => ({ ...d, [key]: value }));

  async function save(keys: string[]) {
    setBusy(true);
    setMsg("");
    try {
      const body: Record<string, string> = {};
      for (const k of keys) {
        if (k in draft) body[k] = draft[k];
      }
      if (Object.keys(body).length === 0) {
        setMsg(t("settings.saved"));
        return;
      }
      await api.saveProviders(body);
      setDraft((d) => {
        const next = { ...d };
        for (const k of keys) delete next[k];
        return next;
      });
      await load();
      setMsg(t("settings.saved"));
    } catch (e: any) {
      setMsg(e?.message || t("settings.testFail"));
    } finally {
      setBusy(false);
    }
  }

  async function clearKey(key: string) {
    setBusy(true);
    try {
      await api.saveProviders({ [key]: "" });
      setDraft((d) => {
        const next = { ...d };
        delete next[key];
        return next;
      });
      await load();
      setMsg(t("settings.cleared"));
    } finally {
      setBusy(false);
    }
  }

  async function test(provider: string, keys: string[]) {
    setBusy(true);
    try {
      const body: Record<string, string> = {};
      for (const k of keys) {
        if (draft[k]) body[k] = draft[k];
      }
      const r = await api.testProvider(provider, body);
      setTestMsg((m) => ({ ...m, [provider]: { ok: Boolean(r.ok), detail: r.detail || "" } }));
    } catch (e: any) {
      setTestMsg((m) => ({ ...m, [provider]: { ok: false, detail: e?.message || t("settings.testFail") } }));
    } finally {
      setBusy(false);
    }
  }

  const TestLine = ({ provider }: { provider: string }) => {
    const row = testMsg[provider];
    if (!row) return null;
    return (
      <p className={`text-sm ${row.ok ? "text-buy" : "text-sell"}`} data-testid={`test-${provider}`}>
        {row.ok ? t("settings.testPass") : t("settings.testFail")}: {row.detail}
      </p>
    );
  };

  return (
    <div className="max-w-2xl space-y-4 pb-16" data-testid="settings-providers">
      <h1 className="text-xl font-semibold">{t("nav.settings")}</h1>
      <p className="text-xs text-muted-fg">{t("settings.bootstrapNote")}</p>
      {msg && <p className="text-sm">{msg}</p>}

      <Group title={t("settings.desk")}>
        <label className="block text-sm">
          {t("settings.language")}
          <select
            className="w-full bg-muted rounded px-3 py-2 min-h-11"
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
          <select className="w-full bg-muted rounded px-3 py-2 min-h-11" value={desk.theme} onChange={(e) => desk.setTheme(e.target.value as any)}>
            <option value="dark">{t("settings.dark")}</option>
            <option value="light">{t("settings.light")}</option>
          </select>
        </label>
      </Group>

      <Group title={t("settings.market")} help={t("settings.marketHelp")}>
        <SecretField
          label={t("settings.oandaToken")}
          envName="OANDA_API_TOKEN"
          field={field("oanda", "OANDA_API_TOKEN")}
          value={draft.OANDA_API_TOKEN || ""}
          onChange={(v) => setKey("OANDA_API_TOKEN", v)}
          onClear={() => void clearKey("OANDA_API_TOKEN")}
        />
        <SecretField
          label={t("settings.oandaAccount")}
          envName="OANDA_ACCOUNT_ID"
          field={field("oanda", "OANDA_ACCOUNT_ID")}
          value={draft.OANDA_ACCOUNT_ID || ""}
          onChange={(v) => setKey("OANDA_ACCOUNT_ID", v)}
          onClear={() => void clearKey("OANDA_ACCOUNT_ID")}
        />
        <label className="block text-sm">
          {t("settings.oandaEnv")}
          <span className="ms-2 text-[11px] text-muted-fg font-mono">OANDA_ENV</span>
          <select
            className="w-full bg-muted rounded px-3 py-2 min-h-11"
            value={draft.OANDA_ENV ?? field("oanda", "OANDA_ENV")?.value ?? "practice"}
            onChange={(e) => setKey("OANDA_ENV", e.target.value)}
          >
            <option value="practice">{t("settings.oandaPractice")}</option>
            <option value="live">{t("settings.oandaLive")}</option>
          </select>
        </label>
        <SecretField
          label={t("settings.twelveKey")}
          envName="TWELVE_DATA_API_KEY"
          field={field("twelve", "TWELVE_DATA_API_KEY")}
          value={draft.TWELVE_DATA_API_KEY || ""}
          onChange={(v) => setKey("TWELVE_DATA_API_KEY", v)}
          onClear={() => void clearKey("TWELVE_DATA_API_KEY")}
        />
        <label className="block text-sm">
          {t("settings.divergence")}
          <span className="ms-2 text-[11px] text-muted-fg font-mono">PRICE_DIVERGENCE_BPS</span>
          <input
            className="w-full bg-muted rounded px-3 py-2 min-h-11"
            type="number"
            min={1}
            step={0.5}
            value={draft.PRICE_DIVERGENCE_BPS ?? field("twelve", "PRICE_DIVERGENCE_BPS")?.value ?? "15"}
            onChange={(e) => setKey("PRICE_DIVERGENCE_BPS", e.target.value)}
          />
        </label>
        <div className="flex flex-wrap gap-2">
          <button type="button" className="rounded bg-muted px-3 py-2 min-h-11" disabled={busy} onClick={() => void test("oanda", ["OANDA_API_TOKEN", "OANDA_ACCOUNT_ID", "OANDA_ENV"])}>
            {t("settings.testConnection")} · OANDA
          </button>
          <button type="button" className="rounded bg-muted px-3 py-2 min-h-11" disabled={busy} onClick={() => void test("twelve", ["TWELVE_DATA_API_KEY"])}>
            {t("settings.testConnection")} · Twelve
          </button>
          <button
            type="button"
            className="rounded liquid-metal px-3 py-2 min-h-11"
            disabled={busy}
            onClick={() => void save(["OANDA_API_TOKEN", "OANDA_ACCOUNT_ID", "OANDA_ENV", "TWELVE_DATA_API_KEY", "PRICE_DIVERGENCE_BPS"])}
          >
            {t("settings.saveGroup")}
          </button>
        </div>
        <TestLine provider="oanda" />
        <TestLine provider="twelve" />
      </Group>

      <Group title={t("settings.news")} help={t("settings.newsHelp")}>
        <SecretField
          label={t("settings.finnhubKey")}
          envName="FINNHUB_API_KEY"
          field={field("finnhub", "FINNHUB_API_KEY")}
          value={draft.FINNHUB_API_KEY || ""}
          onChange={(v) => setKey("FINNHUB_API_KEY", v)}
          onClear={() => void clearKey("FINNHUB_API_KEY")}
        />
        <div className="flex flex-wrap gap-2">
          <button type="button" className="rounded bg-muted px-3 py-2 min-h-11" disabled={busy} onClick={() => void test("finnhub", ["FINNHUB_API_KEY"])}>
            {t("settings.testConnection")}
          </button>
          <button type="button" className="rounded liquid-metal px-3 py-2 min-h-11" disabled={busy} onClick={() => void save(["FINNHUB_API_KEY"])}>
            {t("settings.saveGroup")}
          </button>
        </div>
        <TestLine provider="finnhub" />
      </Group>

      <Group title={t("settings.execution")} help={t("settings.executionHelp")}>
        <SecretField
          label={t("settings.metaapiToken")}
          envName="METAAPI_TOKEN"
          field={field("metaapi", "METAAPI_TOKEN")}
          value={draft.METAAPI_TOKEN || ""}
          onChange={(v) => setKey("METAAPI_TOKEN", v)}
          onClear={() => void clearKey("METAAPI_TOKEN")}
        />
        <SecretField
          label={t("settings.metaapiAccount")}
          envName="METAAPI_ACCOUNT_ID"
          field={field("metaapi", "METAAPI_ACCOUNT_ID")}
          value={draft.METAAPI_ACCOUNT_ID || ""}
          onChange={(v) => setKey("METAAPI_ACCOUNT_ID", v)}
          onClear={() => void clearKey("METAAPI_ACCOUNT_ID")}
        />
        <label className="block text-sm">
          {t("settings.brokerServer")}
          <span className="ms-2 text-[11px] text-muted-fg font-mono">METAAPI_BROKER_SERVER</span>
          <input
            className="w-full bg-muted rounded px-3 py-2 min-h-11"
            value={draft.METAAPI_BROKER_SERVER ?? field("metaapi", "METAAPI_BROKER_SERVER")?.value ?? ""}
            onChange={(e) => setKey("METAAPI_BROKER_SERVER", e.target.value)}
            placeholder="Broker-Server"
          />
        </label>
        <label className="block text-sm">
          {t("settings.accountType")}
          <span className="ms-2 text-[11px] text-muted-fg font-mono">METAAPI_ACCOUNT_TYPE</span>
          <select
            className="w-full bg-muted rounded px-3 py-2 min-h-11"
            value={draft.METAAPI_ACCOUNT_TYPE ?? field("metaapi", "METAAPI_ACCOUNT_TYPE")?.value ?? "demo"}
            onChange={(e) => setKey("METAAPI_ACCOUNT_TYPE", e.target.value)}
          >
            <option value="demo">{t("settings.accountDemo")}</option>
            <option value="live">{t("settings.accountLive")}</option>
          </select>
        </label>
        <Link to="/account" className="text-sm underline min-h-11 inline-flex items-center">
          {t("settings.aliasLink")}
        </Link>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            className="rounded bg-muted px-3 py-2 min-h-11"
            disabled={busy}
            onClick={() => void test("metaapi", ["METAAPI_TOKEN", "METAAPI_ACCOUNT_ID", "METAAPI_REGION"])}
          >
            {t("settings.testConnection")}
          </button>
          <button
            type="button"
            className="rounded liquid-metal px-3 py-2 min-h-11"
            disabled={busy}
            onClick={() => void save(["METAAPI_TOKEN", "METAAPI_ACCOUNT_ID", "METAAPI_BROKER_SERVER", "METAAPI_ACCOUNT_TYPE"])}
          >
            {t("settings.saveGroup")}
          </button>
        </div>
        <TestLine provider="metaapi" />
      </Group>

      <Group title={t("settings.modelsGroup")} help={t("settings.modelsHelp")}>
        <SecretField
          label={t("settings.anthropicKey")}
          envName="ANTHROPIC_API_KEY"
          field={field("anthropic", "ANTHROPIC_API_KEY")}
          value={draft.ANTHROPIC_API_KEY || ""}
          onChange={(v) => setKey("ANTHROPIC_API_KEY", v)}
          onClear={() => void clearKey("ANTHROPIC_API_KEY")}
        />
        <label className="block text-sm">
          {t("settings.quickDefault")}
          <select
            className="w-full bg-muted rounded px-3 py-2 min-h-11"
            value={draft.QUICK_MODEL ?? field("anthropic", "QUICK_MODEL")?.value ?? "claude-sonnet-5"}
            onChange={(e) => {
              setKey("QUICK_MODEL", e.target.value);
              void api.settings({ quick_model: e.target.value });
            }}
          >
            {MODELS.map((m) => (
              <option key={m} value={m}>
                {t(`models.${m}`)}
              </option>
            ))}
          </select>
        </label>
        <label className="block text-sm">
          {t("settings.deepDefault")}
          <select
            className="w-full bg-muted rounded px-3 py-2 min-h-11"
            value={draft.DEEP_MODEL ?? field("anthropic", "DEEP_MODEL")?.value ?? "claude-fable-5"}
            onChange={(e) => {
              setKey("DEEP_MODEL", e.target.value);
              void api.settings({ deep_model: e.target.value });
            }}
          >
            {MODELS.map((m) => (
              <option key={m} value={m}>
                {t(`models.${m}`)}
              </option>
            ))}
          </select>
        </label>
        <div className="flex flex-wrap gap-2">
          <button type="button" className="rounded bg-muted px-3 py-2 min-h-11" disabled={busy} onClick={() => void test("anthropic", ["ANTHROPIC_API_KEY"])}>
            {t("settings.testConnection")}
          </button>
          <button type="button" className="rounded liquid-metal px-3 py-2 min-h-11" disabled={busy} onClick={() => void save(["ANTHROPIC_API_KEY", "QUICK_MODEL", "DEEP_MODEL"])}>
            {t("settings.saveGroup")}
          </button>
        </div>
        <TestLine provider="anthropic" />
      </Group>

      <Group title={t("settings.telegramGroup")} help={t("settings.telegramHelp")}>
        <SecretField
          label={t("settings.telegramToken")}
          envName="TELEGRAM_BOT_TOKEN"
          field={field("telegram", "TELEGRAM_BOT_TOKEN")}
          value={draft.TELEGRAM_BOT_TOKEN || ""}
          onChange={(v) => setKey("TELEGRAM_BOT_TOKEN", v)}
          onClear={() => void clearKey("TELEGRAM_BOT_TOKEN")}
        />
        <div className="space-y-2">
          <p className="text-sm">{t("settings.linkCode")}</p>
          <p className="text-xs text-muted-fg">{t("settings.linkHint")}</p>
          <p className="text-[11px] text-muted-fg">
            {field("telegram", "TELEGRAM_LINK_CODE")?.status === "configured"
              ? `${t("settings.configured")} · ${t("settings.last4")} ${field("telegram", "TELEGRAM_LINK_CODE")?.last4}`
              : t("settings.missing")}
          </p>
          {linkOnce && (
            <p className="text-sm font-mono bg-muted rounded px-3 py-2" data-testid="telegram-link-once">
              {linkOnce}
              <span className="block text-[11px] text-muted-fg mt-1">{t("settings.codeOnce")}</span>
            </p>
          )}
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              className="rounded bg-muted px-3 py-2 min-h-11"
              disabled={busy}
              onClick={async () => {
                const r = await api.telegramLink("generate");
                setLinkOnce(r.code || "");
                await load();
              }}
            >
              {t("settings.generateCode")}
            </button>
            <button
              type="button"
              className="rounded bg-muted px-3 py-2 min-h-11"
              disabled={busy}
              onClick={async () => {
                await api.telegramLink("revoke");
                setLinkOnce("");
                await load();
                setMsg(t("settings.cleared"));
              }}
            >
              {t("settings.revokeCode")}
            </button>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <button type="button" className="rounded bg-muted px-3 py-2 min-h-11" disabled={busy} onClick={() => void test("telegram", ["TELEGRAM_BOT_TOKEN"])}>
            {t("settings.testConnection")}
          </button>
          <button type="button" className="rounded liquid-metal px-3 py-2 min-h-11" disabled={busy} onClick={() => void save(["TELEGRAM_BOT_TOKEN"])}>
            {t("settings.saveGroup")}
          </button>
        </div>
        <TestLine provider="telegram" />
      </Group>

      <Group title={t("settings.system")} help={t("settings.systemHelp")}>
        <ul className="text-sm space-y-1">
          <li>
            {t("settings.postgres")}: {data?.system?.postgres === "connected" ? t("settings.connected") : t("settings.disconnected")}
          </li>
          <li>
            {t("settings.redis")}: {data?.system?.redis === "connected" ? t("settings.connected") : t("settings.disconnected")}
          </li>
        </ul>
        <p className="text-xs font-medium">{t("settings.optional")}</p>
        <SecretField
          label={t("settings.sentryDsn")}
          envName="SENTRY_DSN"
          field={field("optional", "SENTRY_DSN")}
          value={draft.SENTRY_DSN || ""}
          onChange={(v) => setKey("SENTRY_DSN", v)}
          onClear={() => void clearKey("SENTRY_DSN")}
        />
        <label className="block text-sm">
          {t("settings.publicUrl")}
          <span className="ms-2 text-[11px] text-muted-fg font-mono">PUBLIC_APP_URL</span>
          <input
            className="w-full bg-muted rounded px-3 py-2 min-h-11"
            value={draft.PUBLIC_APP_URL ?? field("optional", "PUBLIC_APP_URL")?.value ?? ""}
            onChange={(e) => setKey("PUBLIC_APP_URL", e.target.value)}
            placeholder="https://"
          />
        </label>
        <label className="block text-sm">
          {t("settings.webhookUrl")}
          <span className="ms-2 text-[11px] text-muted-fg font-mono">WEBHOOK_BASE_URL</span>
          <input
            className="w-full bg-muted rounded px-3 py-2 min-h-11"
            value={draft.WEBHOOK_BASE_URL ?? field("optional", "WEBHOOK_BASE_URL")?.value ?? ""}
            onChange={(e) => setKey("WEBHOOK_BASE_URL", e.target.value)}
            placeholder="https://"
          />
        </label>
        <button type="button" className="rounded liquid-metal px-3 py-2 min-h-11" disabled={busy} onClick={() => void save(["SENTRY_DSN", "PUBLIC_APP_URL", "WEBHOOK_BASE_URL"])}>
          {t("settings.saveGroup")}
        </button>
        <p className="text-[11px] text-muted-fg">{t("settings.workerNote")}</p>
      </Group>

      <div className="flex flex-wrap gap-2">
        <button className="rounded bg-muted px-3 py-2 min-h-11" onClick={() => desk.openModal("credentials")}>
          {t("modals.credentials")}
        </button>
        <button className="rounded bg-muted px-3 py-2 min-h-11" onClick={() => desk.openModal("disclaimer")}>
          {t("modals.disclaimer")}
        </button>
        <button className="rounded bg-muted px-3 py-2 min-h-11" onClick={() => desk.openModal("kill")}>
          {t("buttons.kill")}
        </button>
      </div>
    </div>
  );
}

export function LangSwitch() {
  const { i18n } = useTranslation();
  return (
    <div className="flex gap-2 text-xs">
      {(["ar", "en", "tr"] as const).map((lng) => (
        <button
          key={lng}
          type="button"
          className={`rounded px-2 py-1 min-h-11 ${i18n.language.startsWith(lng) ? "bg-muted" : "text-muted-fg"}`}
          onClick={() => {
            void i18n.changeLanguage(lng);
            applyDir(lng);
            localStorage.setItem("zorro.lang", lng);
          }}
        >
          {lng.toUpperCase()}
        </button>
      ))}
    </div>
  );
}

export function LoginPage() {
  const { t } = useTranslation();
  const desk = useDesk();
  const [email, setEmail] = useState("loorksy@gmail.com");
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
      <div className="flex items-center justify-between gap-2">
        <h1 className="text-xl font-semibold">{t("nav.login")}</h1>
        <LangSwitch />
      </div>
      <label className="block text-sm">
        {t("auth.email")}
        <input className="w-full bg-muted rounded px-3 py-2" value={email} onChange={(e) => setEmail(e.target.value)} placeholder={t("auth.emailPlaceholder")} autoComplete="username" required />
      </label>
      <label className="block text-sm">
        {t("auth.password")}
        <input type="password" className="w-full bg-muted rounded px-3 py-2" value={password} onChange={(e) => setPassword(e.target.value)} placeholder={t("auth.passwordPlaceholder")} autoComplete="current-password" required />
      </label>
      {err && <p className="text-sell text-sm">{err}</p>}
      <button className="w-full rounded liquid-metal py-2">{t("auth.signIn")}</button>
      <p className="text-sm">
        <Link className="underline" to="/download">
          {t("download.nav")}
        </Link>
      </p>
      <p className="text-xs text-muted-fg">{t("app.disclaimer")}</p>
    </form>
  );
}
