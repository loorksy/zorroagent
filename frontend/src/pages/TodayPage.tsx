import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { api } from "../lib/api";
import { RecCard } from "../components/RecCard";
import { useDesk } from "../store";

export function TodayPage() {
  const { t } = useTranslation();
  const [recs, setRecs] = useState<any[]>([]);
  useEffect(() => {
    void api.recs().then(setRecs).catch(() => setRecs([]));
    void api.health().then((h) => {
      if (h.feeds?.oanda?.status !== "connected") useDesk.getState().setBanner("Price data unreliable");
    }).catch(() => {});
  }, []);
  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">{t("nav.today")}</h1>
      {recs.length === 0 && <p className="text-slate-400">{t("empty.recs")}</p>}
      {recs.map((r) => (
        <RecCard key={r.id} rec={r} />
      ))}
    </div>
  );
}
