import { useEffect, useRef, useState } from "react";
import { init, dispose } from "klinecharts";
import { api } from "../lib/api";
import { useTranslation } from "react-i18next";

const LAYOUT_KEY = "zorro.chart.layout";

/** KLineChart Pro surface — klinecharts engine, professional desk chrome. */
export function KLineChartPro({
  symbol,
  timeframe,
  overlays,
}: {
  symbol: string;
  timeframe: string;
  overlays?: { price: number; label: string; color: string }[];
}) {
  const { t } = useTranslation();
  const ref = useRef<HTMLDivElement>(null);
  const [drawn, setDrawn] = useState(overlays || []);

  useEffect(() => {
    const saved = localStorage.getItem(LAYOUT_KEY);
    if (saved) {
      try {
        const j = JSON.parse(saved);
        if (j.timeframe) {
          /* layout persist: timeframe remembered by desk store already */
        }
      } catch {
        /* ignore */
      }
    }
  }, []);

  useEffect(() => {
    localStorage.setItem(LAYOUT_KEY, JSON.stringify({ symbol, timeframe }));
  }, [symbol, timeframe]);

  useEffect(() => {
    setDrawn(overlays || []);
  }, [overlays]);

  useEffect(() => {
    if (!ref.current || !symbol) return;
    const chart = init(ref.current);
    let dead = false;
    void (async () => {
      const data = await api.candles(symbol, timeframe).catch(() => null);
      if (dead || !data?.ok) return;
      const bars = (data.candles || []).map((c: any) => {
        const mid = c.mid || c;
        return {
          timestamp: Date.parse(c.time),
          open: Number(mid.o ?? mid.open),
          high: Number(mid.h ?? mid.high),
          low: Number(mid.l ?? mid.low),
          close: Number(mid.c ?? mid.close),
          volume: Number(c.volume || 0),
        };
      });
      chart.applyNewData(bars);
    })();
    return () => {
      dead = true;
      dispose(ref.current!);
    };
  }, [symbol, timeframe]);

  if (!symbol)
    return (
      <div className="h-80 grid place-items-center text-muted-fg border border-line rounded-lg" role="status">
        {t("ask.pickSymbol")}
      </div>
    );
  return (
    <div className="space-y-2">
      <div className="flex justify-end">
        <button className="text-sm px-3 min-h-10 rounded bg-muted" onClick={() => setDrawn([])} data-testid="clear-drawings">
          {t("chart.clear")}
        </button>
      </div>
      <div ref={ref} className="h-80 w-full rounded-lg border border-line bg-card" role="img" aria-label={`Chart ${symbol} ${timeframe}`} />
      {drawn.length > 0 && (
        <ul className="text-xs text-muted-fg" data-testid="chart-overlays">
          {drawn.map((o) => (
            <li key={o.label} style={{ color: o.color }}>
              {o.label}: {o.price}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
