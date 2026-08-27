import { create } from "zustand";
import { persist } from "zustand/middleware";

export type ModalName =
  | "execute"
  | "confirmRec"
  | "promote"
  | "kill"
  | "symbol"
  | "analysis"
  | "convert"
  | "draw"
  | "alias"
  | "pin"
  | "version"
  | "cap"
  | "credentials"
  | "disclaimer"
  | "stopAll"
  | null;

type State = {
  token: string | null;
  language: "en" | "tr" | "ar";
  theme: "dark" | "light";
  modelId: string;
  symbol: string | null;
  timeframe: string;
  tier: "quick" | "deep";
  banner: string | null;
  modal: ModalName;
  modalPayload: any;
  setToken: (t: string | null) => void;
  setLang: (l: "en" | "tr" | "ar") => void;
  setTheme: (t: "dark" | "light") => void;
  setModel: (m: string) => void;
  setSymbol: (s: string | null) => void;
  setTimeframe: (t: string) => void;
  setTier: (t: "quick" | "deep") => void;
  setBanner: (b: string | null) => void;
  openModal: (m: ModalName, payload?: any) => void;
  closeModal: () => void;
};

export const useDesk = create<State>()(
  persist(
    (set) => ({
      token: localStorage.getItem("zorro.token"),
      language: (localStorage.getItem("zorro.lang") as any) || "en",
      theme: (localStorage.getItem("zorro.theme") as any) || "dark",
      modelId: "claude-sonnet-5",
      symbol: null,
      timeframe: "15m",
      tier: "quick",
      banner: null,
      modal: null,
      modalPayload: null,
      setToken: (t) => {
        if (t) localStorage.setItem("zorro.token", t);
        else localStorage.removeItem("zorro.token");
        set({ token: t });
      },
      setLang: (l) => {
        localStorage.setItem("zorro.lang", l);
        set({ language: l });
      },
      setTheme: (t) => {
        localStorage.setItem("zorro.theme", t);
        set({ theme: t });
      },
      setModel: (m) => set({ modelId: m }),
      setSymbol: (s) => set({ symbol: s }),
      setTimeframe: (t) => set({ timeframe: t }),
      setTier: (t) => set({ tier: t }),
      setBanner: (b) => set({ banner: b }),
      openModal: (m, payload) => set({ modal: m, modalPayload: payload ?? null }),
      closeModal: () => set({ modal: null, modalPayload: null }),
    }),
    { name: "zorro-desk" },
  ),
);
