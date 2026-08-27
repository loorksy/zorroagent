import type { CapacitorConfig } from "@capacitor/cli";

const config: CapacitorConfig = {
  appId: "com.zorro.trading",
  appName: "Zorro",
  webDir: "dist",
  server: { androidScheme: "https" },
};

export default config;
