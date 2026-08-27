import { useTranslation } from "react-i18next";
import { useDesk } from "../store";

export type CardKind = "recommendation" | "refusal" | "quick";

export function cardKind(rec: { refused?: boolean; tradeable?: boolean }): CardKind {
  if (rec.refused) return "refusal";
  if (rec.tradeable) return "recommendation";
  return "quick";
}

export function RecCard({ rec, surface = "thread" }: { rec: any; surface?: "thread" | "saved" }) {
  const { t } = useTranslation();
  const open = useDesk((s) => s.openModal);
  if (!rec) return null;
  const kind = cardKind(rec);
  switch (kind) {
    case "recommendation":
    case "refusal":
    case "quick":
      break;
    default: {
      const _exhaustive: never = kind;
      throw new Error(`Unknown card type: ${_exhaustive}`);
    }
  }
  const similar = rec.similar_past_cases || {};
  const dirLabel = rec.direction === "SELL" ? t("card.sell") : t("card.buy");
  return (
    <article className="rounded-lg border border-line bg-card p-4 space-y-3" data-testid="rec-card" data-kind={kind}>
      <header className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">
          <span className={rec.direction === "BUY" ? "text-buy" : "text-sell"}>{dirLabel}</span> {rec.canonical_id}
        </h2>
        <span className="text-xs text-muted-fg">{rec.model_id}</span>
      </header>
      {kind === "quick" && <p className="text-xs text-warning">{t("card.nonTradeable")}</p>}
      {kind === "refusal" && (
        <p className="text-sm text-sell">
          {t("card.refused")}: {rec.refused_gate} — {rec.refused_reason}
        </p>
      )}
      <p className="text-sm text-muted-fg">{(rec.reasons || []).slice(0, 3).join(" · ")}</p>
      <dl className="grid grid-cols-2 gap-2 text-sm">
        <div>
          <dt className="text-muted-fg">{t("card.entry")}</dt>
          <dd>
            {rec.preferred_entry} ({rec.entry_zone?.low}–{rec.entry_zone?.high})
          </dd>
        </div>
        <div>
          <dt className="text-muted-fg">{t("card.stop")}</dt>
          <dd>{rec.stop_loss}</dd>
        </div>
        <div>
          <dt className="text-muted-fg">{t("card.targets")}</dt>
          <dd>{(rec.take_profits || []).join(" / ")}</dd>
        </div>
        <div>
          <dt className="text-muted-fg">{t("card.fill")}</dt>
          <dd>{rec.fill_rule}</dd>
        </div>
      </dl>
      <p className="text-sm">
        {t("card.next")}: {rec.next_action || "—"}
      </p>
      <p className="text-xs text-muted-fg">
        {t("card.similar")}: {similar.label === "Insufficient data" ? t("card.insufficient") : similar.count ?? 0}
        {similar.win_rate == null ? "" : ` · ${similar.win_rate}`}
      </p>
      <div className="flex gap-2">
        <button className="touch-target px-3 py-2 rounded bg-muted text-sm" onClick={() => open("confirmRec", rec)}>
          {t("modals.confirmRec")}
        </button>
        {surface === "saved" && rec.tradeable && rec.id && (
          <button
            className="touch-target px-3 py-2 rounded bg-foreground text-primary-fg text-sm font-medium"
            onClick={() => open("execute", rec)}
            data-testid="execute-after-save"
          >
            {t("buttons.execute")}
          </button>
        )}
      </div>
    </article>
  );
}
