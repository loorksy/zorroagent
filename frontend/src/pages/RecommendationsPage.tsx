import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../lib/api";
import { RecCard } from "../components/RecCard";
import { useTranslation } from "react-i18next";

export function RecommendationsPage() {
  const { t } = useTranslation();
  const [rows, setRows] = useState<any[]>([]);
  useEffect(() => {
    void api.recs().then(setRows).catch(() => setRows([]));
  }, []);
  return (
    <div className="space-y-3">
      <h1 className="text-xl font-semibold">{t("nav.recommendations")}</h1>
      {rows.map((r) => (
        <Link key={r.id} to={`/recommendations/${r.id}`} className="block">
          <RecCard rec={r} />
        </Link>
      ))}
      {rows.length === 0 && <p className="text-muted-fg">{t("empty.recs")}</p>}
    </div>
  );
}

export function RecommendationDetailPage() {
  const { id } = useParams();
  const { t } = useTranslation();
  const [rec, setRec] = useState<any>(null);
  useEffect(() => {
    if (id) void api.rec(id).then(setRec).catch(() => setRec(null));
  }, [id]);
  if (!rec) return <p>{t("card.notAvailable")}</p>;
  return <RecCard rec={rec} surface="saved" />;
}
