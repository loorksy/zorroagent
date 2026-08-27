import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { api } from "../lib/api";
import { useDesk } from "../store";

export function WatchlistPage() {
  const { t } = useTranslation();
  const [rows, setRows] = useState<any[]>([]);
  const open = useDesk((s) => s.openModal);
  const refresh = () => void api.watchlist().then(setRows).catch(() => setRows([]));
  useEffect(() => {
    refresh();
  }, []);
  return (
    <div className="space-y-3">
      <div className="flex justify-between">
        <h1 className="text-xl font-semibold">{t("nav.watchlist")}</h1>
        <button className="px-3 py-2 rounded bg-foreground text-primary-fg min-h-11" onClick={() => open("symbol")}>
          {t("buttons.addWatch")}
        </button>
      </div>
      {rows.length === 0 && <p className="text-muted-fg">{t("empty.watch")}</p>}
      <ul>
        {rows.map((r) => (
          <li key={r.id} className="flex justify-between py-2 border-b border-line">
            {r.canonical_id}
            <button onClick={() => api.delWatch(r.id).then(refresh)}>{t("buttons.remove")}</button>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function ExposurePage() {
  const { t } = useTranslation();
  const [data, setData] = useState<any>(null);
  const open = useDesk((s) => s.openModal);
  useEffect(() => {
    void api.exposure().then(setData).catch(() => setData(null));
  }, []);
  return (
    <div className="space-y-3">
      <h1 className="text-xl font-semibold">{t("nav.exposure")}</h1>
      <p>
        {t("exposure.totalR")}: {data?.total_r ?? t("card.notAvailable")}
      </p>
      {data?.correlation_warning && <p className="text-warning text-sm">{data.correlation_warning}</p>}
      <button className="rounded bg-muted px-3 py-2 min-h-11" onClick={() => open("cap")}>
        {t("modals.cap")}
      </button>
      <p className="text-xs text-muted-fg">{data?.disclaimer}</p>
    </div>
  );
}
