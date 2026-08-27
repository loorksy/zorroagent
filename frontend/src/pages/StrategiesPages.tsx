import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { api } from "../lib/api";

export function StrategiesPage() {
  const { t } = useTranslation();
  const [rows, setRows] = useState<any[]>([]);
  useEffect(() => {
    void api.strategies().then(setRows).catch(() => setRows([]));
  }, []);
  return (
    <div className="space-y-3">
      <div className="flex justify-between">
        <h1 className="text-xl font-semibold">{t("nav.strategies")}</h1>
        <Link to="/strategies/new" className="px-3 py-2 rounded bg-foreground text-primary-fg min-h-11 inline-flex items-center">
          {t("buttons.new")}
        </Link>
      </div>
      <ul>
        {rows.map((s) => (
          <li key={s.id} className="py-2 border-b border-line flex justify-between">
            {s.name}
            <span className="flex gap-3 text-sm">
              <Link to={`/strategies/${s.id}/optimize`}>{t("buttons.optimize")}</Link>
              <Link to={`/strategies/${s.id}/versions`}>{t("buttons.versions")}</Link>
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function StrategyNewPage() {
  const { t } = useTranslation();
  const nav = useNavigate();
  const [name, setName] = useState("");
  const [tpl, setTpl] = useState("session_breakout");
  return (
    <form
      className="max-w-md space-y-3"
      onSubmit={async (e) => {
        e.preventDefault();
        await api.createStrategy({ name, origin: "library", template: tpl });
        nav("/strategies");
      }}
    >
      <h1 className="text-xl font-semibold">{t("buttons.library")}</h1>
      <label className="block text-sm">
        {t("forms.name")}
        <input className="w-full bg-muted rounded px-3 py-2" value={name} onChange={(e) => setName(e.target.value)} required placeholder={t("forms.namePlaceholder")} />
      </label>
      <select className="w-full bg-muted rounded px-3 py-2" value={tpl} onChange={(e) => setTpl(e.target.value)}>
        <option value="session_breakout">session_breakout</option>
        <option value="zone_retest">zone_retest</option>
        <option value="structure_continuation">structure_continuation</option>
      </select>
      <button className="rounded bg-foreground text-primary-fg px-4 py-2 min-h-11">{t("buttons.save")}</button>
    </form>
  );
}

export function StrategyOptimizePage() {
  const { id } = useParams();
  const { t } = useTranslation();
  const [out, setOut] = useState<any>(null);
  return (
    <div className="space-y-3">
      <h1 className="text-xl font-semibold">{t("buttons.optimize")}</h1>
      <button
        className="rounded bg-foreground text-primary-fg px-3 py-2 min-h-11"
        onClick={async () => {
          if (!id) return;
          const r = await api.optimize(id, { candles: [], direction: "BUY", entry: 1, stop: 0.9, targets: [1.1, 1.2], spread: 0.0001, slippage: 0.0001, canonical_id: "EUR_USD" });
          setOut(r);
        }}
      >
        {t("buttons.run")}
      </button>
      {out && (
        <dl className="text-sm bg-card p-3 rounded border border-line space-y-1">
          <div>
            {t("review.sample")}: {out.sample_size}
          </div>
          <div>maxDD={out.max_dd ?? t("card.insufficient")}</div>
          <div>pf={out.profit_factor ?? t("card.insufficient")}</div>
          <div>{out.label}</div>
          {out.fragility_warning ? <div className="text-warning">{out.fragility_warning}</div> : null}
        </dl>
      )}
    </div>
  );
}

export function StrategyVersionsPage() {
  const { id } = useParams();
  const [rows, setRows] = useState<any[]>([]);
  useEffect(() => {
    if (id) void api.versions(id).then(setRows).catch(() => setRows([]));
  }, [id]);
  return (
    <ul>
      {rows.map((v) => (
        <li key={v.id} className="py-2 border-b border-line">
          v{v.version} {v.changelog}
        </li>
      ))}
    </ul>
  );
}
