/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        background: "var(--background)",
        foreground: "var(--foreground)",
        card: "var(--card)",
        muted: "var(--muted)",
        "muted-fg": "var(--muted-foreground)",
        line: "var(--border)",
        desk: "var(--background)",
        primary: "var(--primary)",
        "primary-fg": "var(--primary-foreground)",
        buy: "var(--buy)",
        sell: "var(--sell)",
        warning: "var(--warning)",
        info: "var(--info)",
        destructive: "var(--destructive)",
        sidebar: "var(--sidebar)",
        ring: "var(--ring)",
        // trading green only — never brand chrome
        accent: "var(--buy)",
      },
      borderRadius: {
        DEFAULT: "0.625rem",
        lg: "0.875rem",
      },
      fontFamily: {
        sans: ["Inter", "Cairo", "system-ui", "sans-serif"],
      },
      minHeight: {
        touch: "44px",
      },
    },
  },
  plugins: [],
};
