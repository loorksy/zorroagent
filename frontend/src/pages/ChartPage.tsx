import { useParams } from "react-router-dom";
import { useDesk } from "../store";
import { KLineChartPro } from "../components/Chart";
import { useTranslation } from "react-i18next";

export function ChartPage() {
  const { symbol } = useParams();
  const desk = useDesk();
  const { t } = useTranslation();
  const id = symbol || desk.symbol;
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2 items-center">
        <button className="px-3 py-2 min-h-11 rounded border border-line" onClick={() => desk.openModal("symbol")}>
          {id || t("ask.pickSymbol")}
        </button>
        {["1m", "5m", "15m", "1h", "4h", "1d"].map((tf) => (
          <button key={tf} className={`px-2 min-h-11 rounded text-sm ${desk.timeframe === tf ? "bg-muted text-foreground" : "text-muted-fg"}`} onClick={() => desk.setTimeframe(tf)}>
            {tf}
          </button>
        ))}
      </div>
      <KLineChartPro
        symbol={id || ""}
        timeframe={desk.timeframe}
        overlays={
          desk.modalPayload
            ? [
                { price: desk.modalPayload.preferred_entry, label: "entry", color: "var(--info)" },
                { price: desk.modalPayload.stop_loss, label: "sl", color: "var(--sell)" },
              ]
            : undefined
        }
      />
    </div>
  );
}
