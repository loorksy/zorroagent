import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { CopilotKit } from "@copilotkit/react-core";
import { useDesk } from "../store";
import { api } from "../lib/api";
import { RecCard } from "../components/RecCard";
import { KLineChartPro } from "../components/Chart";

const MODELS = [
  "claude-fable-5",
  "claude-opus-5",
  "claude-opus-4-8",
  "claude-sonnet-5",
  "claude-opus-4-7",
] as const;

export function AskPage() {
  const { t } = useTranslation();
  const desk = useDesk();
  const [text, setText] = useState("");
  const [logOpen, setLogOpen] = useState(false);
  const [messages, setMessages] = useState<{ role: string; content: string; rec?: any }[]>([]);
  const [conv, setConv] = useState<string | null>(null);

  useEffect(() => {
    void api.health().then((h) => {
      const o = h.feeds?.oanda?.status;
      if (o && o !== "connected") desk.setBanner("Price data unreliable");
    }).catch(() => {});
  }, [desk]);

  async function send() {
    if (!text.trim()) return;
    const user = text;
    setText("");
    setMessages((m) => [...m, { role: "user", content: user }]);
    const res = await api.chat({
      conversation_id: conv,
      message: user,
      language: desk.language,
      model_id: desk.modelId,
      canonical_id: desk.symbol,
      timeframe: desk.timeframe,
      tier: desk.tier,
    }).catch((e) => ({ reply: String(e), conversation_id: conv }));
    setConv(res.conversation_id);
    setMessages((m) => [...m, { role: "assistant", content: res.reply, rec: res.recommendation }]);
  }

  const body = (
      <div className="grid lg:grid-cols-[1fr_360px] gap-4">
        <section className="space-y-4">
          <div className="flex flex-wrap gap-2 items-center">
            <button className="touch-target px-3 py-2 rounded border border-line" onClick={() => desk.openModal("symbol")}>
              {desk.symbol || t("ask.pickSymbol")}
            </button>
            {["1m", "5m", "15m", "1h", "4h", "1d"].map((tf) => (
              <button key={tf} className={`px-2 py-1 rounded text-sm ${desk.timeframe === tf ? "bg-accent text-primary" : "bg-muted"}`} onClick={() => desk.setTimeframe(tf)}>
                {tf}
              </button>
            ))}
            <label className="text-sm">
              {t("ask.model")}
              <select
                className="ml-2 bg-muted rounded px-2 py-1"
                value={desk.modelId}
                onChange={(e) => desk.setModel(e.target.value)}
                aria-label={t("ask.model")}
              >
                {MODELS.map((m) => (
                  <option key={m} value={m}>
                    {t(`models.${m}`)}
                  </option>
                ))}
              </select>
            </label>
            <button className={`px-3 py-1 rounded text-sm ${desk.tier === "quick" ? "bg-accent text-primary" : "bg-muted"}`} onClick={() => desk.setTier("quick")}>
              {t("ask.quick")}
            </button>
            <button className={`px-3 py-1 rounded text-sm ${desk.tier === "deep" ? "bg-accent text-primary" : "bg-muted"}`} onClick={() => desk.setTier("deep")}>
              {t("ask.deep")}
            </button>
            <button className="px-3 py-1 rounded bg-muted text-sm" onClick={() => desk.openModal("analysis")}>
              {t("buttons.newAnalysis")}
            </button>
          </div>
          <div className="min-h-[40vh] space-y-3">
            {messages.map((m, i) => (
              <div key={i} className={m.role === "user" ? "text-end" : ""}>
                <p className="text-sm whitespace-pre-wrap">{m.content}</p>
                {m.rec && <RecCard rec={m.rec} />}
              </div>
            ))}
          </div>
          <details open={logOpen} onToggle={(e) => setLogOpen((e.target as HTMLDetailsElement).open)}>
            <summary className="text-sm text-slate-500 cursor-pointer">{t("ask.agentLog")}</summary>
            <pre className="text-xs text-slate-500 whitespace-pre-wrap">Hidden by default. Full transcript lives on the agent run.</pre>
          </details>
          <form
            className="flex gap-2"
            onSubmit={(e) => {
              e.preventDefault();
              void send();
            }}
          >
            <input
              className="flex-1 bg-muted rounded px-3 py-3 touch-target"
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder={t("ask.placeholder")}
              aria-label={t("ask.placeholder")}
            />
            <button className="touch-target px-4 rounded bg-accent text-primary font-medium" type="submit">
              {t("ask.send")}
            </button>
          </form>
        </section>
        <aside className="hidden lg:block">
          <KLineChartPro symbol={desk.symbol || ""} timeframe={desk.timeframe} />
        </aside>
      </div>
  );
  const key = import.meta.env.VITE_COPILOTKIT_KEY;
  if (!key) return body;
  return <CopilotKit publicApiKey={key}>{body}</CopilotKit>;
}
