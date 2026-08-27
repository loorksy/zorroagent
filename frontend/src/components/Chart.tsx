import { useEffect, useRef } from "react";
import { init, dispose } from "klinecharts";
import { api } from "../lib/api";

/** KLineChart Pro surface — klinecharts engine, professional desk chrome. */
export function KLineChartPro({ symbol, timeframe }: { symbol: string; timeframe: string }) {
  const ref = useRef<HTMLDivElement>(null);

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

  if (!symbol) return <div className="h-80 grid place-items-center text-slate-500">Select an instrument</div>;
  return <div ref={ref} className="h-80 w-full rounded-xl border border-line bg-card" role="img" aria-label={`Chart ${symbol} ${timeframe}`} />;
}
