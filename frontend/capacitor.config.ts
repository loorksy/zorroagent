import type { CapacitorConfig } from "@capacitor/cli";

/** Production APK sets CAPACITOR_SERVER_URL=https://zorro.lork.cloud so the WebView talks to the live API. Local `cap sync` omits it. */
const productionUrl = process.env.CAPACITOR_SERVER_URL?.trim();

const config: CapacitorConfig = {
  appId: "com.zorro.trading",
  appName: "Zorro",
  webDir: "dist",
  server: {
    androidScheme: "https",
    ...(productionUrl
      ? {
          url: productionUrl,
          cleartext: false,
        }
      : {}),
  },
};

export default config;
