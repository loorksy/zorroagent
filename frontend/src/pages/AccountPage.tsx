import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { api } from "../lib/api";
import { useDesk } from "../store";

export function AccountPage() {
  const { t } = useTranslation();
  const [accounts, setAccounts] = useState<any[]>([]);
  const [aliases, setAliases] = useState<any[]>([]);
  const [active, setActive] = useState<string | null>(null);
  const [name, setName] = useState("demo");
  const [accId, setAccId] = useState("");
  const [token, setToken] = useState("");
  const [canon, setCanon] = useState("");
  const [exec, setExec] = useState("");
  const [err, setErr] = useState("");
  const open = useDesk((s) => s.openModal);

  const load = () => void api.accounts().then(setAccounts).catch(() => setAccounts([]));
  useEffect(() => {
    load();
  }, []);
  useEffect(() => {
    if (active) void api.aliases(active).then(setAliases).catch(() => setAliases([]));
  }, [active]);

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">{t("nav.account")}</h1>
      <p className="text-sm text-slate-400">Analysis uses canonical OANDA ids. Orders use execution_symbol. Unmapped = analyze OK, execute NEVER.</p>
      <form
        className="grid gap-2 max-w-md"
        onSubmit={async (e) => {
          e.preventDefault();
          await api.addAccount({ name, metaapi_account_id: accId, token, is_demo: true });
          load();
        }}
      >
        <label className="text-sm">
          {t("forms.name")}
          <input className="w-full bg-muted rounded px-3 py-2" value={name} onChange={(e) => setName(e.target.value)} required />
        </label>
        <label className="text-sm">
          {t("forms.accountId")}
          <input className="w-full bg-muted rounded px-3 py-2" value={accId} onChange={(e) => setAccId(e.target.value)} required />
        </label>
        <label className="text-sm">
          {t("forms.token")}
          <input type="password" className="w-full bg-muted rounded px-3 py-2" value={token} onChange={(e) => setToken(e.target.value)} />
        </label>
        <button className="rounded bg-accent text-primary py-2">{t("buttons.save")}</button>
      </form>
      <ul>
        {accounts.map((a) => (
          <li key={a.id}>
            <button className="py-2" onClick={() => setActive(a.id)}>
              {a.name} {a.is_demo ? "(demo)" : "(live)"}
            </button>
          </li>
        ))}
      </ul>
      {active && (
        <form
          className="grid gap-2 max-w-md"
          onSubmit={async (e) => {
            e.preventDefault();
            setErr("");
            try {
              await api.saveAlias(active, { canonical_id: canon, execution_symbol: exec });
              setAliases(await api.aliases(active));
            } catch (ex: any) {
              setErr(ex.message);
            }
          }}
        >
          <h2 className="font-medium">{t("modals.alias")}</h2>
          <button type="button" className="text-start text-sm underline" onClick={() => open("symbol")}>
            {t("ask.pickSymbol")}
          </button>
          <input className="bg-muted rounded px-3 py-2" placeholder="canonical_id" value={canon} onChange={(e) => setCanon(e.target.value)} required />
          <input className="bg-muted rounded px-3 py-2" placeholder="execution_symbol" value={exec} onChange={(e) => setExec(e.target.value)} required />
          <button className="rounded bg-muted py-2">{t("buttons.testResolve")}</button>
          {err && <p className="text-red-400 text-sm">{err}</p>}
          <ul className="text-sm">
            {aliases.map((x) => (
              <li key={x.id}>
                {x.canonical_id} → {x.execution_symbol} {x.last_test_ok ? "ok" : x.last_test_error}
              </li>
            ))}
          </ul>
        </form>
      )}
    </div>
  );
}
