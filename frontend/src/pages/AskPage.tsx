import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { CopilotKit } from "@copilotkit/react-core";
import { useDesk } from "../store";
import { api } from "../lib/api";
import { RecCard } from "../components/RecCard";
import { KLineChartPro } from "../components/Chart";

export function AskPage() {
  const { t } = useTranslation();
  const desk = useDesk();
  const [text, setText] = useState("");
  const [logOpen, setLogOpen] = useState(false);
  const [messages, setMessages] = useState<{ role: string; content: string; rec?: any }[]>([]);
  const [conv, setConv] = useState<string | null>(null);

  useEffect(() => {
    const seed = sessionStorage.getItem("zorro.qa.seed");
    if (seed) {
      try {
        setMessages(JSON.parse(seed));
      } catch {
        /* ignore */
      }
    }
  }, []);

  async function send() {
    if (!text.trim()) return;
    const user = text;
    setText("");
    setMessages((m) => [...m, { role: "user", content: user }]);
    const res = await api
      .chat({
        conversation_id: conv,
        message: user,
        language: desk.language,
        model_id: desk.modelId,
        canonical_id: desk.symbol,
        timeframe: desk.timeframe,
        tier: desk.tier,
      })
      .catch((e) => ({ reply: String(e), conversation_id: conv, recommendation: null }));
    setConv(res.conversation_id);
    setMessages((m) => [...m, { role: "assistant", content: res.reply, rec: res.recommendation }]);
  }

  const body = (
    <div className="grid lg:grid-cols-[1fr_360px] gap-4 min-h-[calc(100vh-8rem)]">
      <section className="flex flex-col min-h-[60vh]">
        <div className="flex flex-wrap gap-2 items-center mb-3">
          <button
            className={`px-3 min-h-11 rounded text-sm ${desk.tier === "quick" ? "bg-muted text-foreground" : "text-muted-fg"}`}
            onClick={() => desk.setTier("quick")}
            data-testid="tier-quick"
          >
            {t("ask.quick")}
          </button>
          <button
            className={`px-3 min-h-11 rounded text-sm ${desk.tier === "deep" ? "bg-muted text-foreground" : "text-muted-fg"}`}
            onClick={() => desk.setTier("deep")}
            data-testid="tier-deep"
          >
            {t("ask.deep")}
          </button>
          <button className="px-3 min-h-11 rounded bg-muted text-sm" onClick={() => desk.openModal("analysis")}>
            {t("buttons.newAnalysis")}
          </button>
        </div>
        <div className="flex-1 space-y-3 overflow-auto" data-testid="thread">
          {messages.length === 0 && <p className="text-sm text-muted-fg">{t("empty.ask")}</p>}
          {messages.map((m, i) => (
            <div key={i} className={m.role === "user" ? "text-end" : ""}>
              <p className="text-sm whitespace-pre-wrap">{m.content}</p>
              {m.rec && <RecCard rec={m.rec} surface="thread" />}
            </div>
          ))}
        </div>
        <details
          className="mt-2"
          open={logOpen}
          onToggle={(e) => setLogOpen((e.target as HTMLDetailsElement).open)}
          data-testid="agent-log"
        >
          <summary className="text-sm text-muted-fg cursor-pointer">{t("ask.agentLog")}</summary>
          <pre className="text-xs text-muted-fg whitespace-pre-wrap">{t("ask.agentLogBody")}</pre>
        </details>
        <form
          data-testid="chat-composer"
          className="composer-sheet mt-3 flex gap-2 p-2 sticky bottom-16 md:bottom-0"
          onSubmit={(e) => {
            e.preventDefault();
            void send();
          }}
        >
          <input
            className="flex-1 bg-transparent rounded px-3 py-3 touch-target"
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder={t("ask.placeholder")}
            aria-label={t("ask.placeholder")}
          />
          <button className="liquid-metal touch-target px-4 font-medium" type="submit">
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
