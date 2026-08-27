import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import en from "./en.json";
import tr from "./tr.json";
import ar from "./ar.json";

const saved = localStorage.getItem("zorro.lang") || "en";

void i18n.use(initReactI18next).init({
  resources: { en: { translation: en }, tr: { translation: tr }, ar: { translation: ar } },
  lng: saved,
  fallbackLng: "en",
  interpolation: { escapeValue: false },
});

export function applyDir(lng: string) {
  document.documentElement.lang = lng;
  document.documentElement.dir = lng === "ar" ? "rtl" : "ltr";
}

applyDir(saved);

export default i18n;
