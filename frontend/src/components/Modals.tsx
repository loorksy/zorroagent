import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useDesk } from "../store";
import { api, Instrument } from "../lib/api";
import { RecCard } from "./RecCard";

function Overlay({ title, children }: { title: string; children: React.ReactNode }) {
  const close = useDesk((s) => s.closeModal);
  const { t } = useTranslation();
  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/60 p-4" role="dialog" aria-modal="true" aria-label={title}>
      <div className="w-full max-w-lg max-h-[90vh] overflow-auto rounded-xl border border-line bg-card p-5 space-y-4">
        <header className="flex justify-between items-center">
          <h2 className="font-semibold">{title}</h2>
          <button className="touch-target text-sm" onClick={close} aria-label={t("buttons.close")}>
            {t("buttons.close")}
          </button>
        </header>
        {children}
      </div>
    </div>
  );
}

function Field({ label, error, children }: { label: string; error?: string; children: React.ReactNode }) {
  return (
    <label className="block text-sm space-y-1">
      <span>{label}</span>
      {children}
      {error && <span className="text-red-400 text-xs">{error}</span>}
    </label>
  );
}

export function Modals() {
  const { t } = useTranslation();
  const modal = useDesk((s) => s.modal);
  const payload = useDesk((s) => s.modalPayload);
  const close = useDesk((s) => s.closeModal);
  const setSymbol = useDesk((s) => s.setSymbol);
  const [q, setQ] = useState("");
  const [items, setItems] = useState<Instrument[]>([]);
  const [lots, setLots] = useState("");
  const [confirm, setConfirm] = useState("");
  const [err, setErr] = useState("");

  useEffect(() => {
    if (modal === "symbol") {
      void api.instruments(q).then((r) => setItems(r.instruments)).catch(() => setItems([]));
    }
  }, [modal, q]);

  if (!modal) return null;

  if (modal === "symbol") {
    return (
      <Overlay title={t("modals.symbol")}>
        <p className="text-xs text-slate-400">{t("ask.noFreeText")}</p>
        <input className="w-full bg-muted rounded px-3 py-2" value={q} onChange={(e) => setQ(e.target.value)} placeholder={t("ask.pickSymbol")} />
        <ul className="max-h-64 overflow-auto divide-y divide-line">
          {items.map((i) => (
            <li key={i.canonical_id}>
              <button
                className="w-full text-start py-2 touch-target"
                onClick={() => {
                  setSymbol(i.canonical_id);
                  close();
                }}
              >
                {i.display_symbol} <span className="text-slate-500 text-xs">{i.canonical_id}</span>
              </button>
            </li>
          ))}
        </ul>
      </Overlay>
    );
  }

  if (modal === "execute") {
    return (
      <Overlay title={t("modals.execute")}>
        <p className="text-xs">{t("app.disclaimer")}</p>
        <Field label={t("forms.lots")} error={!lots ? t("forms.required") : ""}>
          <input className="w-full bg-muted rounded px-3 py-2" value={lots} onChange={(e) => setLots(e.target.value)} placeholder={t("forms.lotsPlaceholder")} />
        </Field>
        <Field label={t("forms.canonicalConfirm")}>
          <input className="w-full bg-muted rounded px-3 py-2" value={confirm} onChange={(e) => setConfirm(e.target.value)} placeholder={t("forms.pinPlaceholder")} />
        </Field>
        <button
          className="w-full touch-target rounded bg-accent text-primary font-medium py-2"
          onClick={async () => {
            if (!lots) return;
            try {
              await api.execute({
                source: "recommendation",
                source_id: payload?.id,
                source_name: payload?.name,
                account_id: payload?.account_id || "",
                lots: Number(lots),
                confirmation: confirm,
              });
              close();
            } catch (e: any) {
              setErr(e.message);
            }
          }}
        >
          {t("buttons.confirm")}
        </button>
        {err && <p className="text-red-400 text-sm">{err}</p>}
      </Overlay>
    );
  }

  if (modal === "confirmRec") {
    const g = payload?.gates || [];
    return (
      <Overlay title={t("modals.confirmRec")}>
        <RecCard rec={payload} />
        <ul className="text-sm space-y-1">
          {g.map((x: any) => (
            <li key={x.gate_id}>
              {x.gate_id} {x.name}: {x.status} {x.reason || ""}
            </li>
          ))}
        </ul>
      </Overlay>
    );
  }

  if (modal === "kill" || modal === "stopAll") {
    return (
      <Overlay title={t("modals.kill")}>
        <p>{t("modals.stopAll")}</p>
        <button
          className="w-full touch-target rounded bg-red-600 py-2"
          onClick={async () => {
            await api.kill(true, "ui");
            close();
          }}
        >
          {t("buttons.stopAll")}
        </button>
      </Overlay>
    );
  }

  if (modal === "promote") {
    return (
      <Overlay title={t("modals.promote")}>
        <Field label={t("forms.canonicalConfirm")}>
          <input className="w-full bg-muted rounded px-3 py-2" value={confirm} onChange={(e) => setConfirm(e.target.value)} />
        </Field>
        <button
          className="w-full rounded bg-accent text-primary py-2 touch-target"
          onClick={async () => {
            await api.liveBot(payload.id, { confirmation: confirm, account_id: payload.account_id });
            close();
          }}
        >
          {t("buttons.promoteLive")}
        </button>
      </Overlay>
    );
  }

  if (modal === "analysis") {
    return (
      <Overlay title={t("modals.analysis")}>
        <p className="text-sm text-slate-400">{t("ask.noFreeText")}</p>
        <button className="rounded bg-muted px-3 py-2" onClick={() => useDesk.getState().openModal("symbol")}>
          {t("ask.pickSymbol")}
        </button>
      </Overlay>
    );
  }

  if (modal === "convert") {
    return (
      <Overlay title={t("modals.convert")}>
        <p className="text-sm">Exact levels will be locked — no new rules.</p>
        <button className="rounded bg-accent text-primary px-3 py-2" onClick={close}>
          {t("buttons.convertBot")}
        </button>
      </Overlay>
    );
  }

  if (modal === "draw") {
    return (
      <Overlay title={t("modals.draw")}>
        <textarea className="w-full bg-muted rounded p-2 min-h-32" placeholder={t("ask.placeholder")} />
        <button className="rounded bg-accent text-primary px-3 py-2" onClick={close}>
          {t("buttons.save")}
        </button>
      </Overlay>
    );
  }

  if (modal === "alias") {
    return (
      <Overlay title={t("modals.alias")}>
        <Field label="canonical_id">
          <input className="w-full bg-muted rounded px-3 py-2" defaultValue={payload?.canonical_id} readOnly />
        </Field>
        <Field label="execution_symbol">
          <input className="w-full bg-muted rounded px-3 py-2" id="exec-sym" />
        </Field>
        <button className="rounded bg-accent text-primary px-3 py-2">{t("buttons.testResolve")}</button>
      </Overlay>
    );
  }

  if (modal === "pin") {
    return (
      <Overlay title={t("modals.pin")}>
        <Field label={t("forms.pin")}>
          <input type="password" className="w-full bg-muted rounded px-3 py-2" />
        </Field>
        <button className="rounded bg-accent text-primary px-3 py-2" onClick={close}>
          {t("buttons.confirm")}
        </button>
      </Overlay>
    );
  }

  if (modal === "version") {
    return (
      <Overlay title={t("modals.version")}>
        <p className="text-sm">Live bot keeps current until explicit activate. One-click rollback.</p>
        <button className="rounded bg-muted px-3 py-2">{t("buttons.rollback")}</button>
      </Overlay>
    );
  }

  if (modal === "cap") {
    return (
      <Overlay title={t("modals.cap")}>
        <input type="number" className="w-full bg-muted rounded px-3 py-2" placeholder="R" />
        <button className="rounded bg-accent text-primary px-3 py-2" onClick={close}>
          {t("buttons.save")}
        </button>
      </Overlay>
    );
  }

  if (modal === "credentials") {
    return (
      <Overlay title={t("modals.credentials")}>
        <Field label={t("forms.token")}>
          <input type="password" className="w-full bg-muted rounded px-3 py-2" />
        </Field>
        <p className="text-xs text-slate-500">Encrypted at rest. Never stored in the frontend.</p>
        <button className="rounded bg-accent text-primary px-3 py-2" onClick={close}>
          {t("buttons.save")}
        </button>
      </Overlay>
    );
  }

  if (modal === "disclaimer") {
    return (
      <Overlay title={t("modals.disclaimer")}>
        <p>{t("app.disclaimer")}</p>
        <button className="rounded bg-muted px-3 py-2" onClick={close}>
          {t("buttons.close")}
        </button>
      </Overlay>
    );
  }

  return null;
}
