import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { api } from "../lib/api";
import { useDesk } from "../store";

export function BotsPage() {
  const { t } = useTranslation();
  const [rows, setRows] = useState<any[]>([]);
  useEffect(() => {
    void api.bots().then(setRows).catch(() => setRows([]));
  }, []);
  return (
    <div className="space-y-3">
      <h1 className="text-xl font-semibold">{t("nav.bots")}</h1>
      {rows.length === 0 && <p className="text-slate-400">{t("empty.bots")}</p>}
      <ul>
        {rows.map((b) => (
          <li key={b.id}>
            <Link to={`/bots/${b.id}`}>
              {b.name} — {b.status}
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function BotDetailPage() {
  const { id } = useParams();
  const { t } = useTranslation();
  const nav = useNavigate();
  const open = useDesk((s) => s.openModal);
  const [bot, setBot] = useState<any>(null);
  useEffect(() => {
    if (id) void api.bot(id).then(setBot).catch(() => setBot(null));
  }, [id]);
  if (!bot) return <p>{t("card.notAvailable")}</p>;
  return (
    <div className="space-y-3">
      <h1 className="text-xl font-semibold">{bot.name}</h1>
      <p className="text-sm text-slate-400">{bot.performance_note}</p>
      <div className="flex flex-wrap gap-2">
        <button className="rounded bg-muted px-3 py-2" onClick={() => id && api.demoBot(id)}>
          {t("buttons.startDemo")}
        </button>
        <button className="rounded bg-accent text-primary px-3 py-2" onClick={() => nav(`/bots/${id}/live`)}>
          {t("buttons.promoteLive")}
        </button>
        <button className="rounded bg-muted px-3 py-2" onClick={() => open("version", bot)}>
          {t("buttons.rollback")}
        </button>
      </div>
    </div>
  );
}

export function BotLivePage() {
  const { id } = useParams();
  const { t } = useTranslation();
  const open = useDesk((s) => s.openModal);
  useEffect(() => {
    if (id) open("promote", { id, account_id: "" });
  }, [id, open]);
  return <p className="text-sm">{t("modals.promote")} — demo success + typed canonical symbol or PIN required.</p>;
}

export function DemoPage() {
  const { t } = useTranslation();
  const [d, setD] = useState<any>(null);
  useEffect(() => {
    void api.demo().then(setD).catch(() => setD(null));
  }, []);
  return (
    <div>
      <h1 className="text-xl font-semibold">{t("nav.demo")}</h1>
      <p>{d?.note}</p>
      <p className="text-xs mt-4">{d?.disclaimer}</p>
    </div>
  );
}

export function MemoryPage() {
  const { t } = useTranslation();
  const [d, setD] = useState<any>(null);
  useEffect(() => {
    void api.memory().then(setD).catch(() => setD(null));
  }, []);
  return (
    <div>
      <h1 className="text-xl font-semibold">{t("nav.memory")}</h1>
      <p className="text-sm text-slate-400">{d?.note}</p>
      <ul>
        {(d?.cases || []).map((c: any) => (
          <li key={c.id}>{c.canonical_id} {c.direction}</li>
        ))}
      </ul>
    </div>
  );
}

export function ReviewPage() {
  const { t } = useTranslation();
  const [d, setD] = useState<any>(null);
  useEffect(() => {
    void api.review().then(setD).catch(() => setD(null));
  }, []);
  return (
    <div>
      <h1 className="text-xl font-semibold">{t("nav.review")}</h1>
      <p>sample {d?.sample_size ?? 0}</p>
      <p>{d?.label === "Insufficient data" ? t("card.insufficient") : d?.label}</p>
      <p className="text-xs">{d?.disclaimer}</p>
    </div>
  );
}

export function HistoryPage() {
  const { t } = useTranslation();
  const [d, setD] = useState<any>(null);
  useEffect(() => {
    void api.history().then(setD).catch(() => setD(null));
  }, []);
  return (
    <div>
      <h1 className="text-xl font-semibold">{t("nav.history")}</h1>
      <p className="text-sm">{d?.note}</p>
      <ul>
        {(d?.recommendations || []).map((r: any) => (
          <li key={r.id}>
            {r.direction} {r.canonical_id}
          </li>
        ))}
      </ul>
    </div>
  );
}
