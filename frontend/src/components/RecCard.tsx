import { useTranslation } from "react-i18next";
import { useDesk } from "../store";

export function RecCard({ rec }: { rec: any }) {
  const { t } = useTranslation();
  const open = useDesk((s) => s.openModal);
  if (!rec) return null;
  const similar = rec.similar_past_cases || {};
  return (
    <article className="rounded-xl border border-line bg-card p-4 space-y-3">
      <header className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">
          <span className={rec.direction === "BUY" ? "text-accent" : "text-red-400"}>{rec.direction}</span>{" "}
          {rec.canonical_id}
        </h2>
        <span className="text-xs text-slate-400">{rec.model_id}</span>
      </header>
      {rec.tradeable === false && <p className="text-xs text-amber-400">{t("card.nonTradeable")}</p>}
      {rec.refused && (
        <p className="text-sm text-red-400">
          {t("card.refused")}: {rec.refused_gate} — {rec.refused_reason}
        </p>
      )}
      <p className="text-sm text-slate-300">{(rec.reasons || []).slice(0, 3).join(" · ")}</p>
      <dl className="grid grid-cols-2 gap-2 text-sm">
        <div>
          <dt className="text-slate-500">{t("card.entry")}</dt>
          <dd>
            {rec.preferred_entry} ({rec.entry_zone?.low}–{rec.entry_zone?.high})
          </dd>
        </div>
        <div>
          <dt className="text-slate-500">{t("card.stop")}</dt>
          <dd>{rec.stop_loss}</dd>
        </div>
        <div>
          <dt className="text-slate-500">{t("card.targets")}</dt>
          <dd>{(rec.take_profits || []).join(" / ")}</dd>
        </div>
        <div>
          <dt className="text-slate-500">{t("card.fill")}</dt>
          <dd>{rec.fill_rule}</dd>
        </div>
      </dl>
      <p className="text-sm">
        {t("card.next")}: {rec.next_action || "—"}
      </p>
      <p className="text-xs text-slate-500">
        {t("card.similar")}: {similar.label === "Insufficient data" ? t("card.insufficient") : similar.count ?? 0}
        {similar.win_rate == null ? "" : ` · ${similar.win_rate}`}
      </p>
      <div className="flex gap-2">
        <button className="touch-target px-3 py-2 rounded bg-muted text-sm" onClick={() => open("confirmRec", rec)}>
          {t("modals.confirmRec")}
        </button>
        {rec.tradeable && (
          <button className="touch-target px-3 py-2 rounded bg-accent text-primary text-sm font-medium" onClick={() => open("execute", rec)}>
            {t("buttons.execute")}
          </button>
        )}
      </div>
    </article>
  );
}
