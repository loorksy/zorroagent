const TOKEN_KEY = "zorro.token";

export function token(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(t: string | null) {
  if (t) localStorage.setItem(TOKEN_KEY, t);
  else localStorage.removeItem(TOKEN_KEY);
}

async function req<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = { ...(init.headers as Record<string, string>) };
  if (!(init.body instanceof FormData)) headers["Content-Type"] = "application/json";
  const t = token();
  if (t) headers.Authorization = `Bearer ${t}`;
  const r = await fetch(path, { ...init, headers });
  if (r.status === 401) {
    setToken(null);
    if (!path.includes("/auth/login")) window.location.href = "/login";
  }
  if (!r.ok) {
    const text = await r.text();
    throw new Error(text || r.statusText);
  }
  return r.json() as Promise<T>;
}

/** List endpoints must never crash the desk if the payload is an object. */
export function asList(v: unknown): any[] {
  if (Array.isArray(v)) return v;
  if (v && typeof v === "object") {
    const o = v as Record<string, unknown>;
    for (const k of ["items", "instruments", "conversations", "recommendations", "bots", "accounts", "aliases"]) {
      if (Array.isArray(o[k])) return o[k] as any[];
    }
  }
  return [];
}

export const api = {
  health: () => req<any>("/health"),
  login: (email: string, password: string) =>
    req<{ access_token: string }>("/api/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }),
  me: () => req<any>("/api/me"),
  models: () => req<any>("/api/models"),
  settings: (body: any) => req("/api/settings", { method: "PUT", body: JSON.stringify(body) }),
  instruments: (q?: string) => req<{ instruments: Instrument[] }>(`/api/instruments${q ? `?q=${encodeURIComponent(q)}` : ""}`),
  candles: (id: string, tf = "15m") => req<any>(`/api/candles/${id}?timeframe=${tf}`),
  price: (id: string) => req<any>(`/api/price/${id}`),
  conversations: () => req<any>("/api/conversations").then(asList),
  createConversation: () => req<any>("/api/conversations", { method: "POST" }),
  chat: (body: any) => req<any>("/api/chat", { method: "POST", body: JSON.stringify(body) }),
  analyze: (body: any) => req<any>("/api/analyze", { method: "POST", body: JSON.stringify(body) }),
  recs: () => req<any>("/api/recommendations").then(asList),
  rec: (id: string) => req<any>(`/api/recommendations/${id}`),
  watchlist: () => req<any>("/api/watchlist").then(asList),
  addWatch: (canonical_id: string) => req("/api/watchlist", { method: "POST", body: JSON.stringify({ canonical_id }) }),
  delWatch: (id: string) => req(`/api/watchlist/${id}`, { method: "DELETE" }),
  exposure: () => req<any>("/api/exposure"),
  accounts: () => req<any>("/api/accounts").then(asList),
  addAccount: (body: any) => req("/api/accounts", { method: "POST", body: JSON.stringify(body) }),
  aliases: (id: string) => req<any>(`/api/accounts/${id}/aliases`).then(asList),
  saveAlias: (id: string, body: any) => req(`/api/accounts/${id}/aliases`, { method: "POST", body: JSON.stringify(body) }),
  strategies: () => req<any>("/api/strategies").then(asList),
  library: () => req<any>("/api/strategies/library"),
  createStrategy: (body: any) => req("/api/strategies", { method: "POST", body: JSON.stringify(body) }),
  versions: (id: string) => req<any>(`/api/strategies/${id}/versions`).then(asList),
  optimize: (id: string, body: any) => req(`/api/strategies/${id}/optimize`, { method: "POST", body: JSON.stringify(body) }),
  bots: () => req<any>("/api/bots").then(asList),
  bot: (id: string) => req<any>(`/api/bots/${id}`),
  createBot: (body: any) => req("/api/bots", { method: "POST", body: JSON.stringify(body) }),
  demoBot: (id: string) => req(`/api/bots/${id}/demo`, { method: "POST" }),
  liveBot: (id: string, body: any) => req(`/api/bots/${id}/live`, { method: "POST", body: JSON.stringify(body) }),
  rollback: (id: string, version_id: string) => req(`/api/bots/${id}/rollback`, { method: "POST", body: JSON.stringify({ version_id }) }),
  kill: (engaged: boolean, reason = "") => req("/api/kill-switch", { method: "POST", body: JSON.stringify({ engaged, reason }) }),
  getKill: () => req<any>("/api/kill-switch"),
  memory: () => req<any>("/api/memory"),
  review: () => req<any>("/api/review"),
  history: () => req<any>("/api/history"),
  demo: () => req<any>("/api/demo"),
  execute: (body: any) => req("/api/execute", { method: "POST", body: JSON.stringify(body) }),
};

export type Instrument = {
  canonical_id: string;
  display_symbol: string;
  asset_class: string;
  tradable: boolean;
};
